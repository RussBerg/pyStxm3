'''
Created on Aug 25, 2014

@author: bergr
'''
import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import simplejson as json
import copy
import math
import time
from importlib import import_module
import webbrowser
from bcm.devices.device_names import *

from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj

from cls.appWidgets.dialogs import getOpenFileName, getSaveFileName

from cls.scanning.dataRecorder import NumpyAwareJSONEncoder
from cls.utils.roi_utils import make_active_data_dict, make_base_wdg_com
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, get_axis_setpoints_from_sp_db
from cls.utils.file_system_tools import master_get_seq_names
from cls.utils.excepthook import exception
from cls.types.beamline import BEAMLINE_IDS

from cls.utils.json_threadsave import ThreadJsonSave, loadJson
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, get_unique_roi_id, \
    get_epu_pol_dct, make_spatial_db_dict, widget_com_cmnd_types, \
    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
    on_center_changed, recalc_setpoints, get_sp_ids_from_wdg_com, get_first_sp_db_from_wdg_com, \
    get_base_start_stop_roi
from cls.utils.roi_dict_defs import *
from cls.utils.json_threadsave import mime_to_dct
from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types, get_unique_roi_id, \
    add_to_unique_roi_id_list, reset_unique_roi_id

from cls.plotWidgets.color_def import *
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef

from cls.types.stxmTypes import scan_sub_types, scan_types, image_types, positioner_sub_types, scan_image_types
# from cls.data_io.stxm_data_io import STXMDataIo

from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.enum_utils import Enum
from cls.utils.fileUtils import get_file_path_as_parts, creation_date
from cls.applications.pyStxm import abs_path_to_ini_file, abs_path_to_top, abs_path_to_docs, abs_path_of_ddl_file
from cls.utils.cfgparser import ConfigClass

_logger = get_module_logger(__name__)

PREC = 3
d_fmt = '%.' + '%df' % (PREC)
# the following modes are:
# 0 = fl     calc the focus (or zoneplate z and coarse z positions) such that Cz doesnt move, and Zpz is set to the full focal length 
# 1 = a0mod  calc the focus such that Cz doesnt move, and A0 is modified so that zpz is moved only
# 2 = cz     calc the focus such that Cz moves to put image in focus, and Zpz is set to the calculated pos of (fl - A0)
zp_focus_modes = Enum('fl', 'a0mod', 'cz', 'DO_NOTHING', 'CHECK_LOCAL_SETTING')

NORMAL_BKGRND_COLOR = 'white'
WARN_BKGRND_COLOR = 'yellow'


# appConfig = ConfigClass(abs_path_to_ini_file)
# scanDefs_dir = appConfig.get_value('DEFAULT', 'scanDefsDir')


class Formatter(object):
    """Plugins of this class convert plain text to HTML"""

    name = "No Format"

    def formatText(self, text):
        """Takes plain text, returns HTML"""
        return text


class DataFormatter(QtWidgets.QWidget):
    """Plugins of this class convert a scan data dict to an output file of a given type"""

    name = "No Format"

    def formatData(self, data):
        """Takes a scan data dict, returns it formatted as type"""
        return data


plugin_change_roles = Enum('ALL', 'PARAM')


class ScanParamEventFilter(QtCore.QObject):
    focus_in = QtCore.pyqtSignal()
    focus_out = QtCore.pyqtSignal()
    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QtCore.QEvent.FocusOut:
            print('focus out')
            # return False so that the widget will also handle the event
            # otherwise it won't focus out
            self.focus_in.emit()
            return False
        elif event.type() == QtCore.QEvent.FocusIn:
            print('focus in')
            # return False so that the widget will also handle the event
            # otherwise it won't focus out
            self.focus_out.emit()
            return False
        else:
            # we don't care about other events
            return False

class ScanParamWidget(QtWidgets.QFrame):
    """Plugins of this class define the params for scans"""
    roi_changed = QtCore.pyqtSignal(object)
    roi_deleted = QtCore.pyqtSignal(object)
    plot_data = QtCore.pyqtSignal(object)
    update_plot_strs = QtCore.pyqtSignal(object)
    plugin_tool_clicked = QtCore.pyqtSignal(
        object)  # object is a dict containing the widget that was clicked and any arguments is comes with
    changed = QtCore.pyqtSignal(object, int)  # try a signal similar to model view with (data, role)
    dropped = QtCore.pyqtSignal(QtCore.QMimeData)
    selected = QtCore.pyqtSignal(int)  # a signal to set the =
    clear_all_sig = QtCore.pyqtSignal()  # a signal to tell the parent to clear all previous params, used mainly to signal that the plot should be cleared
    new_est_scan_time = QtCore.pyqtSignal(
        object)  # when a scan parameter has changed a new estemate is recalc'd and emitted with this signal
    test_scan = QtCore.pyqtSignal(int)
    update_shape_limits = QtCore.pyqtSignal(object)
    call_main_func = QtCore.pyqtSignal(str, object) # function name, **kwargs

    def __init__(self, main_obj=None, data_io=None, dflts=None):
        #QtWidgets.QFrame.__init__(self)
        super(ScanParamWidget, self).__init__()
        self.setAcceptDrops(True)
        if (main_obj is None):
            _logger.error('main_obj must be an instance of a MAIN_OBJ module, cannot be None')
            exit()

        if (data_io is None):
            _logger.error('data_io must be an instance of a Data_IO module, cannot be None')
            exit()

        if (dflts is None):
            _logger.error('defaults must be an instance of a DEFAULTS module, cannot be None')
            exit()

        self.name = "No Scan Name"
        self.idx = 0
        self.data = {}
        self.axis_strings = []
        self.scan_sec = 'SCAN.'
        self.preset_sec = 'PRESETS.'
        self.zp_focus_mode = zp_focus_modes.FL
        self.data_file_pfx = 'i'
        self.data_dir = ''
        self.p0_idx = 0
        self.p1_idx = 1
        self.p2_idx = 2
        self.p3_idx = 3
        self.max_scan_range = (None, None)
        self.roi_limit_def = None
        self.enable_edits = True
        self.enable_multi_region = False
        self.center_plot_on_focus = False
        self.scan_class = None
        # used mainly by SAMPLE_IMAGE scans to differentiat a LXL or PXP scan
        self.sub_type = scan_sub_types.POINT_BY_POINT  # default
        self.positioner_type = positioner_sub_types.SAMPLEXY  # default
        self.multi_ev = False
        self.scan_mod_name = 'UNKNOWN'
        self.test_sp_db = None
        self.test_mod = None
        self._selection_is_oversized = False

        self._help_html_fpath = 'place path to plugin help html link here'
        self._help_ttip = '[PLACE SCAN NAME HERE] Scan documentation and instructions'

        self.main_obj = main_obj
        self.data_io_class = data_io
        self._defaults = dflts
        self.sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        self.sample_fine_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()

        self.upd_timer = QtCore.QTimer()
        self.upd_timer.setSingleShot(True)
        self.upd_timer.timeout.connect(self.update_min_max)

        #self.setToolTip('A whole bunch of info here')
        # set button context menu policy
        # _filter = ScanParamEventFilter()
        # _filter.focus_in.connect(self.on_plugin_focus)
        # _filter.focus_out.connect(self.on_plugin_defocus)
        # self.installEventFilter(_filter)

        self.init_plugin()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        to be implemented by inheriting class
        :return:
        '''
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def init_loadscan_menu(self):
        '''
        a function that is called by the pluggin constructor AFTER the ui file has been loaded, it sets up
        a right click context menu to load different scan options
        :return:
        '''
        if (hasattr(self, 'loadscan_frame')):
            self.rtclkpic.setToolTip('Right click for more loading/saving options')
            self.loadscan_frame.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.loadscan_frame.customContextMenuRequested.connect(self.on_context_menu)

        if (hasattr(self, 'ddlFrame')):
            self.ddlFrame.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.ddlFrame.customContextMenuRequested.connect(self.on_ddl_menu)

        if(hasattr(self, 'helpBtn')):
            self.helpBtn.clicked.connect(self.on_help_btn_clicked)
            self._help_html_fpath = os.path.join(abs_path_to_docs, self._help_html_fpath)
            self.helpBtn.setToolTip(self._help_ttip)

    def format_info_text(self, title, msg, title_clr='blue', newline=True, start_preformat=False, end_preformat=False):
        '''
        take arguments and create an html string used for tooltips
        :param title: The title will be bolded
        :param msg: The message will be simple black text
        :param title_clr: The Title will use this color
        :param newline: A flag to add a newline at the end of the string or not
        :param start_preformat: If this is the first string we need to start the PREformat tag
        :param end_preformat: If this is the last string we need to stop the PREformat tag
        :return:
        '''
        s = ''
        if (start_preformat):
            s += '<pre>'

        if (newline):
            s += '<font size="3" color="%s"><b>%s</b></font> %s<br>' % (title_clr, title, msg)
        else:
            s += '<font size="3" color="%s"><b>%s</b></font> %s' % (title_clr, title, msg)

        if (end_preformat):
            s += '</pre>'
        return (s)

    def get_selection_is_oversized(self):
            return(self._selection_is_oversized)

    def on_help_btn_clicked(self):
        webbrowser.open(self._help_html_fpath)

    def get_do_center_plot_on_focus(self):
        return (self.center_plot_on_focus)

    def get_scan_class(self):
        '''
                This is a function that is called when the scan is about to be executed
                to be implemented by inheriting class
                :return:
                '''
        return (self.scan_class)

    def is_spatial_list_empty(self):
        '''
        to be implemented by inheriting class
        by default return False because all single spatial scan plugins will always have a spatial defined, only
        the multi spatials will have a table that could possibly be empty
        :return bool:
        '''
        return(False)

    def on_plugin_scan_start(self):
        '''
        This is a function that is called when the scan starts from the main GUI
        to be implemented by inheriting class
        :param self:
        :return:
        '''
        pass

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        to be implemented by inheriting class
        :return:
        '''
        #print 'ScanParamWidget[%s] has received focus' % self.name
        if (self.isEnabled()):
            # if this plugin has not been disabled because of the scanning mode then execute update_last_settings()
            pass

    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        to be implemented by inheriting class
        :return:
        '''
        #print 'ScanParamWidget[%s] has lost focus' % self.name
        if(self.isEnabled()):
            # if this plugin has not been disabled because of the scanning mode then execute update_last_settings()
            self.update_last_settings()

    # def focusInEvent(self, event):
    #     print('focusInEvent: ')
    #     self.on_plugin_focus()
    #     # do custom stuff
    #     #super(ScanParamWidget, self).focusInEvent(event)
    #
    #
    # def focusOutEvent(self, event):
    #     print('focusOutEvent:')
    #     self.on_plugin_defocus()
    #     # do custom stuff
    #     #super(ScanParamWidget, self).focusOutEvent(event)

    def gen_GONI_SCAN_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """
        MAX_SCAN_RANGE_FINEX = self.main_obj.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
        MAX_SCAN_RANGE_FINEY = self.main_obj.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
        MAX_SCAN_RANGE_X = self.main_obj.get_preset_as_float('MAX_SCAN_RANGE_X')
        MAX_SCAN_RANGE_Y = self.main_obj.get_preset_as_float('MAX_SCAN_RANGE_Y')
        mtr_zpx = self.main_obj.device(DNM_ZONEPLATE_X)
        mtr_zpy = self.main_obj.device(DNM_ZONEPLATE_Y)
        # mtr_osax = self.main_obj.device('OSAX.X')
        # mtr_osay = self.main_obj.device('OSAY.Y')
        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)

        gx_pos = mtr_gx.get_position()
        gy_pos = mtr_gy.get_position()

        # these are all added because the sign is in the LLIM
        xllm = gx_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
        xhlm = gx_pos + (MAX_SCAN_RANGE_FINEY * 0.5)
        yllm = gy_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
        yhlm = gy_pos + (MAX_SCAN_RANGE_FINEY * 0.5)

        gxllm = mtr_gx.get_low_limit()
        gxhlm = mtr_gx.get_high_limit()
        gyllm = mtr_gy.get_low_limit()
        gyhlm = mtr_gy.get_high_limit()

        bounding_qrect = QtCore.QRectF(QtCore.QPointF(gxllm, gyhlm), QtCore.QPointF(gxhlm, gyllm))
        # warn_qrect = self.get_percentage_of_qrect(bounding, 0.90) #%80 of max
        # alarm_qrect = self.get_percentage_of_qrect(bounding, 0.95) #%95 of max
        normal_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(normal_qrect, 1.01)  # %95 of max
        alarm_qrect = self.get_percentage_of_qrect(normal_qrect, 1.0)  # %95 of max

        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Goniometer Capabilities',
                               get_alarm_fill_pattern())
        normal = ROILimitObj(normal_qrect, get_normal_clr(45), 'Fine ZP Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Goniometer will be required to move',
                           get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Range is beyond ZP Capabilities',
                            get_alarm_fill_pattern())

        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)

    def update_last_settings(self):
        '''
        to be implemented by inheriting class
        example:
            update the 'default' settings that will be reloaded when this scan pluggin is selected again

            x_roi = self.sp_db[SPDB_X]
            y_roi = self.sp_db[SPDB_Y]
            e_rois = self.sp_db[SPDB_EV_ROIS]

            DEFAULTS.set('SCAN.DETECTOR.CENTER', (x_roi[CENTER], y_roi[CENTER], 0, 0))
            DEFAULTS.set('SCAN.DETECTOR.RANGE', (x_roi[RANGE], y_roi[RANGE], 0, 0))
            DEFAULTS.set('SCAN.DETECTOR.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], 0, 0))
            DEFAULTS.set('SCAN.DETECTOR.STEP', (x_roi[STEP], y_roi[STEP], 0, 0))
            DEFAULTS.set('SCAN.DETECTOR.DWELL', e_rois[0][DWELL])
            DEFAULTS.update()

        :return:
        '''
        pass

    def get_last_settings(self):
        '''
        A convienience function to get the pluggins last settings, may not be implemented by all plugins. I created this
        to facilitate how torange the plotter when the user clicks from Focus scan where Y scale is Zoneplate Z (all negative)
        to an image scan like the fine image scan where the Y axis is mostly all positive, by being able to
        retrieve the coarse image scans last scan settings I can more accurately place the plotting range in an
        area that makes sense.
        :return:
        '''
        dct = {}
        dct['cntr'] = self._defaults.get('SCAN.%s.CENTER' % self.section_id)
        dct['rng'] = self._defaults.get('SCAN.%s.RANGE' % self.section_id)
        dct['npoints'] = self._defaults.get('SCAN.%s.NPOINTS' % self.section_id)
        dct['step'] = self._defaults.get('SCAN.%s.STEP' % self.section_id)
        dct['dwell'] = self._defaults.get('SCAN.%s.DWELL' % self.section_id)
        return(dct)

    def call_to_reset_image_plot(self):
        p = self.parent()
        while p is not None:
            if(hasattr(p, 'reset_image_plot')):
                p.reset_image_plot()
                break
            else:
                p = p.parent()


    def set_fld_with_val(self, fld, val_str):
        '''
        used in do_test() functions
        :param fld:
        :param val_str:
        :return:
        '''
        fld.setText(val_str)
        fld.returnPressed.emit()
        time.sleep(0.1)

    def init_test_module(self):
        test_modname = os.path.join(self.scan_mod_path, 'test', self.scan_mod_name + '_tester.py')
        if (os.path.exists(test_modname)):
            idx = test_modname.find('cls\\')
            s2 = test_modname[idx:]
            s3 = s2.replace('\\', '.')
            s4 = s3.replace('_tester.py', '_tester')
            #import test_sp_db from there
            self.test_mod = import_module(s4)

        else:
            self.test_mod = None


    def do_test(self):
        if(self.test_mod):
            self.test_sp_db = self.test_mod.init_test_sp_db()
            self.test_mod.do_test(self, self.test_sp_db)

    def derive_scan_mod_name(self, f_name):
        _modname = f_name.split('\\')[-1]
        _modpath = f_name.replace(_modname, '')

        if(_modname.find('.pyc')> 0):
            _modname = _modname.replace('.pyc','')
        else:
            _modname = _modname.replace('.py', '')
        return(_modpath, _modname)


    def get_post_test_data_entries(self, dct):
        options = {'standard': 'nexus', 'def': 'nxstxm'}
        sp_id = list(dct.keys())[0]
        datanames_dct = dct[sp_id]
        data_io = self.data_io_class(datanames_dct['data_dir'], datanames_dct['thumb_name'], options=options)
        entry_dct = data_io.load()
        idx = 0
        # need to give some time for the file to be saved in it's entirety
        while ((entry_dct is None) and (idx < 5)):
            print('%s.py: entry_dct is None, waiting and trying again[%d]' % (self.scan_mod_name, idx))
            time.sleep(0.25)
            entry_dct = data_io.load()
            idx += 1
        return(entry_dct)

    # def do_post_test(self, dct={}):
    #     '''
    #
    #     :param dct:
    #     :return:
    #     '''
    #     print 'base.py: running post test'
    #     print dct

    def do_post_test(self, dct={}):
        '''
        example:
            {0:
                {'thumb_name': 'C180108007',
                'stack_flbl': 'C180108007.hdf5 img/0',
                'data_dir': 'S:\\STXM-data\\Cryo-STXM\\2018\\guest\\0108',
                'stack_dir': 'S:\\STXM-data\\Cryo-STXM\\2018\\guest\\0108\\C180108007',
                'data_name': 'C180108007.hdf5',
                'thumb_ext': 'jpg',
                'prefix': 'C180108007',
                'data_ext': 'hdf5'}
            }
        :param dct:
        :return:
        '''
        test_sp_db = self.test_sp_db
        entry_dct = self.get_post_test_data_entries(dct)

        if (entry_dct is None):
            _logger.error('%s.py: there seems to be a problem loading hte data file[%s]' % (self.scan_mod_name, dct['data_name']))
            return (False)

        _logger.info(list(entry_dct.keys()))

        ekey = list(entry_dct.keys())[0]
        entry_dct = entry_dct[ekey]
        sp_db = get_first_sp_db_from_entry(entry_dct)
        # xdata = get_axis_setpoints_from_sp_db(sp_db, axis='X')
        # ydatas = get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER)

        #
        res = True
        skip_list = [SPDB_RECT]
        do_list = [SPDB_X, SPDB_Y, SPDB_Z, SPDB_GONI]

        for k in do_list:
            _logger.info('checking [%s]' % k)
            res = check_roi_for_match(dct_get(test_sp_db, k), dct_get(sp_db, k), skip_list=skip_list, verbose=True)

        # check that shape of data matches do_test()

        # check that the data is non zero

        # check that the datafile is a base level proper nexus file
        return (res)

    def update_min_max(self):
        '''to be implemented by inheriting class
        '''
        pass

    # def on_plugin_focus(self):
    #     '''
    #     This function is a placeholder to be implemented by inheriting class.
    #     This function is called whenever the widget comes into focus which
    #     allows a spot to populate variables with intial values that are relevant
    #     to the scan
    #     :return:
    #     '''
    #     print 'on_focus_init_base_values: ', self
    #     pass

    def on_multiregion_widget_focus_init_base_values(self):
        '''
        this is called when this scan param receives focus on the GUI
        - basically get the current EPU values and assign them to the multiregion widget
        :return:
        '''
        # set the polarization selection widgets default values
        if (self.main_obj.is_device_supported(DNM_EPU_POLARIZATION)):
            pol = self.main_obj.device(DNM_EPU_POLARIZATION).get_position()
            offset = self.main_obj.device(DNM_EPU_OFFSET).get_position()
            angle = self.main_obj.device(DNM_EPU_ANGLE).get_position()
            self.multi_region_widget.init_polarization_values(pol, offset, angle)

    def calc_new_scan_time_estemate(self, is_pxp, x_roi, y_roi, dwell):
        '''
        to be implemented by inheriting class
        when done it must emit the signal:
            new_est_scan_time

        :return: tuple(seconds, time_string)
        '''
        self.new_est_scan_time.emit((0, '00:00:00'))
        return ((0, '00:00:00'))

    def on_context_menu(self, point):
        '''
                setup a context menu when the user right clicks on a scan pluggin
                to show:
                    - Save scan configuration
                    - Load energy scan definition
                    loading an energy scn def is only enabled if the pluggin's multi_ev member variable is True
                :param point:
                :return:
                '''
        menu = QtWidgets.QMenu(self)
        saveAction = menu.addAction("Save scan configuration")
        loadSpAction = menu.addAction("Load spatial scan definition")
        loadEvAction = menu.addAction("Load energy scan definition")

        # set it to False instead of None because the user may not select any action (which would equal None)
        dumpdbgEvAction = False
        debugger = sys.gettrace()
        if (debugger):
            # only offer this menu if user is debugging
            dumpdbgEvAction = menu.addAction("dump debug info")

        # do a check here to see if I want to enable loading ev scan def
        if (self.multi_ev):
            loadEvAction.setEnabled(True)
        else:
            loadEvAction.setEnabled(False)

        action = menu.exec_(self.mapToGlobal(point))
        if action == saveAction:
            # print 'OK saving scan cfg'
            cfg = self.update_data()
            self.save_config(cfg)
        elif action == loadEvAction:
            # print 'OK loading Ev scan def'
            # cfg = self.update_data()
            self.load_scan_definition(ev_only=True)
            pass
        elif action == loadSpAction:
            self.load_scan_definition(sp_only=True)
        elif action == dumpdbgEvAction:
            self.show_debug_info()

    def on_ddl_menu(self, point):
        '''
                setup a ddl menu when the user right clicks on a scan pluggin
                to show:
                    - Clear DDL cache: last cleared Dec 23, 2019
                    - E712 Details
                :param point:
                :return:
                '''
        if (os.path.exists(abs_path_of_ddl_file)):
            # get the data of the last modification of the file
            t_str = creation_date(abs_path_of_ddl_file)
            msg = 'clear DDL cache: last cleared %s' % t_str
            #msg = '%s' % self.format_info_text('clear DDL cache:', 'last cleared [%s]' % t_str, newline=False,
            #                                  end_preformat=True)
        else:
            msg = 'clear DDL cache:'

        menu = QtWidgets.QMenu(self)
        clearCacheAction = menu.addAction(msg)
        #loadSpAction = menu.addAction("Load spatial scan definition")
        #loadEvAction = menu.addAction("Load energy scan definition")

        # # set it to False instead of None because the user may not select any action (which would equal None)
        # dumpdbgEvAction = False
        # debugger = sys.gettrace()
        # if (debugger):
        #     # only offer this menu if user is debugging
        #     dumpdbgEvAction = menu.addAction("dump debug info")
        #
        # # do a check here to see if I want to enable loading ev scan def
        # if (self.multi_ev):
        #     loadEvAction.setEnabled(True)
        # else:
        #     loadEvAction.setEnabled(False)
        point = QtCore.QPoint(point.x() + 120, point.y() + 60)
        action = menu.exec_(self.mapToGlobal(point))
        if action == clearCacheAction:
            # print 'OK saving scan cfg'
            #cfg = self.update_data()
            #self.save_config(cfg)
            if (os.path.exists(abs_path_of_ddl_file)):
                os.remove(abs_path_of_ddl_file)

        # elif action == loadEvAction:
        #     # print 'OK loading Ev scan def'
        #     # cfg = self.update_data()
        #     self.load_scan_definition(ev_only=True)
        #     pass
        # elif action == loadSpAction:
        #     self.load_scan_definition(sp_only=True)
        # elif action == dumpdbgEvAction:
        #     self.show_debug_info()

    def show_debug_info(self):
        print('debug dump of [%s]' % self.name)
        for k in list(self.__dict__.keys()):
            print((k, self.__dict__[k]))


    def save_config(self, dct):
        scanDefs_dir = self.main_obj.get('APP.USER').get_scan_defs_dir()
        fname = getSaveFileName("Save Scan Definition", '*.json', filter_str="Json Files(*.json)",
                                search_path=scanDefs_dir)
        if (len(fname) < 1):
            return
        prfx = self.main_obj.get_datafile_prefix()
        # d = master_get_seq_names(datadir, prefix_char=prfx, thumb_ext='jpg', dat_ext='json', stack_dir=False, num_desired_datafiles=1)[0]
        wdg_com = make_active_data_dict()
        dct_put(wdg_com, ADO_CFG_WDG_COM, dct)
        dct_put(wdg_com, ADO_CFG_SCAN_TYPE, self.type)
        j = json.dumps(wdg_com, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
        f = open(fname, "w")
        f.write(j)
        f.close()
        _logger.info('save_config: [%s] saved configuration in [%s]' % (self.name, fname))

    def get_sscan_instance(self):
        return (self.sscan_class)

    def clear_params(self):
        '''
        to be implemented by inheriting class
        :return:
        '''
        pass

    def register(self):
        '''
        a function to register the scan plugin with the scan manager so that scans can be loaded unloaded
        dynamically by an addon toggle or something

        To be implemented by the inheriting class
        '''
        # bpy.utils.register_class(SimpleOperator)
        pass

    def unregister(self):
        '''
        a function to register the scan plugin with the scan manager so that scans can be loaded unloaded
        dynamically by an addon toggle or something

        To be implemented by the inheriting class
        '''
        # bpy.utils.unregister_class(SimpleOperator)
        pass

    def dragEnterEvent(self, event):
        dct = mime_to_dct(event.mimeData())
        _logger.debug('dragEnterEvent: [%d]' % dct['scan_panel_idx'])
        event.acceptProposedAction()
        # self.dropped.emit(event.mimeData())
        self.selected.emit(dct['scan_panel_idx'])

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    @exception
    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasImage():
            # self.setPixmap(QtGui.QPixmap(mimeData.imageData()))
            print('dropEvent: mime data has an IMAGE')
        elif mimeData.hasHtml():
            # self.setText(mimeData.html())
            # self.setTextFormat(QtCore.Qt.RichText)
            print('dropEvent: mime data has HTML')
        elif mimeData.hasText():
            # self.setText(mimeData.text())
            # self.setTextFormat(QtCore.Qt.PlainText)
            # print 'dropEvent: mime data has an TEXT = \n[%s]' % mimeData.text()
            dct = mime_to_dct(mimeData)
            print('dropped file is : %s' % dct['file'])
            self.openfile(dct['file'])
        elif mimeData.hasUrls():
            # self.setText("\n".join([url.path() for url in mimeData.urls()]))
            print('dropEvent: mime data has URLs')
        else:
            # self.setText("Cannot display data")
            print('dropEvent: mime data Cannot display data')

        # self.setBackgroundRole(QtGui.QPalette.Dark)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        event.accept()

    def is_multi_region(self):
        return (self.enable_multi_region)

    def get_spatial_scan_range(self):
        return (self.max_scan_range)

    def set_spatial_scan_range(self, rng_tpl):
        '''
        rng_tpl is a tuple that represents the max range for x and y respectively
        :param rng_tpl:
        :return:
        '''
        self.max_scan_range = rng_tpl

    def get_scan_type(self):
        return (self.type)

    def set_editable(self):
        """To be implemented by inheriting class:
         this is to set all of the widgets in the scans params to enable/disable edits (like during a scan)
         """
        flds = self.findChildren(QtWidgets.QLineEdit)
        btns = self.findChildren(QtWidgets.QPushButton)

        for f in flds:
            f.setEnabled(True)

        for b in btns:
            b.setEnabled(True)

    def set_read_only(self):
        """To be implemented by inheriting class:
         this is to set all of the widgets in the scans params back to enabled
        """
        flds = self.findChildren(QtWidgets.QLineEdit)
        btns = self.findChildren(QtWidgets.QPushButton)

        for f in flds:
            f.setEnabled(False)

        for b in btns:
            b.setEnabled(False)

    def update_data(self):
        """To be implemented by inheriting class:
         will get all params for its scan and call or emit the scan to execute
         """
        pass

    def set_roi(self, roi):
        """ To be implemented by inheriting class:
        a method so that the UI can update the parm fields text with data driven by interactive GUI
        """
        pass

    def set_parm(self, fld, val, type='float', floor=None):
        # pval = float(str(fld.text()))
        if (val is None):
            return
        pval = val
        if (floor is not None):
            if (pval < floor):
                pval = floor
        if (type == 'float'):
            fld.setText('%.2f' % pval)
        else:
            fld.setText('%d' % pval)

    def mod_parm(self, fld, val, type='float', floor=None):
        pval = float(str(fld.text()))
        pval += val
        if (floor is not None):
            if (pval < floor):
                pval = floor
        if (type == 'float'):
            fld.setText('%.2f' % pval)
        else:
            fld.setText('%d' % pval)

    def center_parm_in_range(self, center, rng, llm, hlm):
        '''a standard function for pluggins to use to check given center and range check to see if the low end of the range
        is still greater than the low limit and if the high end of the range is less
        than the high limit
        '''
        low = center - (0.5 * rng)
        hi = center + (0.5 * rng)
        if (low < llm):
            return (False)
        if (hi > hlm):
            return (False)

        return (True)

    def startstop_parm_in_range(self, start, stop, llm, hlm):
        '''a standard function for pluggins to use to check given start and stop and check to see if if violates teh
        soft limits of the positioner
        '''
        if (start < llm):
            return (False)
        if (start > hlm):
            return (False)
        if (stop < llm):
            return (False)
        if (stop > hlm):
            return (False)

        return (True)

    def check_center_range_xy_scan_limits(self, mtrx_name, mtry_name):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        cx = float(str(self.centerXFld.text()))
        rx = float(str(self.rangeXFld.text()))
        cy = float(str(self.centerYFld.text()))
        ry = float(str(self.rangeYFld.text()))
        mtrx = self.main_obj.device(mtrx_name)
        mtry = self.main_obj.device(mtry_name)

        x_bkgrnd = NORMAL_BKGRND_COLOR
        y_bkgrnd = NORMAL_BKGRND_COLOR
        ret = True

        if (not self.center_parm_in_range(cx, rx, mtrx.get_low_limit(), mtrx.get_high_limit())):
            _logger.warning('check_center_range_xy_scan_limits: scan parameters for %s violate soft limits' % mtrx_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtrx.get_low_limit(), mtrx.get_high_limit()))
            x_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        if (not self.center_parm_in_range(cy, ry, mtry.get_low_limit(), mtry.get_high_limit())):
            _logger.warning('check_center_range_xy_scan_limits: scan parameters for %s violate soft limits' % mtry_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtry.get_low_limit(), mtry.get_high_limit()))
            y_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        self.centerXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)
        self.rangeXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)
        self.centerYFld.setStyleSheet("QLineEdit { background: %s; }" % y_bkgrnd)
        self.rangeYFld.setStyleSheet("QLineEdit { background: %s; }" % y_bkgrnd)

        if (ret):
            _logger.debug('check_center_range_xy_scan_limits: all scan parameters within soft limits')
        return (ret)

    def check_start_stop_xy_scan_limits(self, mtrx_name, mtry_name):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        sx = float(str(self.startXFld.text()))
        ex = float(str(self.endXFld.text()))
        sy = float(str(self.startYFld.text()))
        ey = float(str(self.endYFld.text()))
        mtrx = self.main_obj.device(mtrx_name)
        mtry = self.main_obj.device(mtry_name)
        x_bkgrnd = NORMAL_BKGRND_COLOR
        y_bkgrnd = NORMAL_BKGRND_COLOR
        ret = True

        if (not self.startstop_parm_in_range(sx, ex, mtrx.get_low_limit(), mtrx.get_high_limit())):
            _logger.warning('check_start_stop_xy_scan_limits: scan parameters for %s violate soft limits' % mtrx_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtrx.get_low_limit(), mtrx.get_high_limit()))
            x_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        if (not self.startstop_parm_in_range(sy, ey, mtry.get_low_limit(), mtry.get_high_limit())):
            _logger.warning('check_start_stop_xy_scan_limits: scan parameters for %s violate soft limits' % mtry_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtry.get_low_limit(), mtry.get_high_limit()))
            y_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        self.startXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)
        self.endXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)
        self.startYFld.setStyleSheet("QLineEdit { background: %s; }" % y_bkgrnd)
        self.endYFld.setStyleSheet("QLineEdit { background: %s; }" % y_bkgrnd)

        if (ret):
            _logger.debug('check_start_stop_xy_scan_limits: all scan parameters within soft limits')
        return (ret)

    def check_start_stop_x_scan_limits(self, mtr_name):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        sx = float(str(self.startXFld.text()))
        ex = float(str(self.endXFld.text()))
        mtr = self.main_obj.device(mtr_name)
        x_bkgrnd = NORMAL_BKGRND_COLOR
        ret = True

        if (not self.startstop_parm_in_range(sx, ex, mtr.get_low_limit(), mtr.get_high_limit())):
            _logger.warning('check_start_stop_scan_limits: scan parameters for %s violate soft limits' % mtr_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtr.get_low_limit(), mtr.get_high_limit()))
            x_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        self.startXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)
        self.endXFld.setStyleSheet("QLineEdit { background: %s; }" % x_bkgrnd)

        if (ret):
            _logger.debug('check_start_stop_xy_scan_limits: all scan parameters within soft limits')
        return (ret)

    def check_center_range_z_scan_limits(self, mtrz_name):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        cz = float(str(self.centerZPFld.text()))
        rz = float(str(self.rangeZPFld.text()))
        mtrz = self.main_obj.device(mtrz_name)
        z_bkgrnd = NORMAL_BKGRND_COLOR
        ret = True

        if (not self.center_parm_in_range(cz, rz, mtrz.get_low_limit(), mtrz.get_high_limit())):
            _logger.warning('check_center_range_z_scan_limits: scan parameters for %s violate soft limits' % mtrz_name)
            _logger.warning('valid absolute range from %.2f to %.2f' % (mtrz.get_low_limit(), mtrz.get_high_limit()))
            z_bkgrnd = WARN_BKGRND_COLOR
            ret = False

        self.centerZPFld.setStyleSheet("QLineEdit { background: %s; }" % z_bkgrnd)
        self.rangeZPFld.setStyleSheet("QLineEdit { background: %s; }" % z_bkgrnd)

        if (ret):
            _logger.debug('check_center_range_z_scan_limits: all scan parameters within soft limits')
        return (ret)

    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        return (True)

    def get_roi(self):

        # check first if the params for scan violate any soft limits
        if (not self.check_scan_limits()):
            _logger.error('Scan parameters violate soft limits of a positioner, scan not attempted')
            return (None)

        roi = self.update_data()
        return (roi)

    def load_from_defaults(self):
        s_id = self.scan_sec + self.section_id
        roi = self._defaults.get_scan_def(s_id)
        self.set_roi(roi)

        self.gen_max_scan_range_limit_def()

    def get_max_scan_range_limit_def(self):
        # need to update the limit def here before returning it
        #self.gen_max_scan_range_limit_def()
        return (self.roi_limit_def)

    def connect_paramfield_signals(self):
        """ to be overridden by inheriting class
        """
        pass

    def gen_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """
        # norm_qrect = QtCore.QRect(0, 0, 50, -50)
        # warn_qrect = QtCore.QRect(0, 0, 100, -300)
        # alarm_qrect = QtCore.QRect(0, 0, 700, -100)

        bounding = QtCore.QRectF(QtCore.QPointF(-5000, 5000), QtCore.QPointF(10000, -10000))

        warn_qrect = self.get_percentage_of_qrect(bounding, 0.80)  # %80 of max
        alarm_qrect = self.get_percentage_of_qrect(bounding, 0.95)  # %95 of max

        normal = ROILimitObj(bounding, get_normal_clr(25), 'All is Normal', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Warning', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Oh Crap!', get_alarm_fill_pattern())

        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)

    def get_percentage_of_qrect(self, qrect, p):
        '''
        take a qrect and return another qrect that is only a percentage of the passed in qrect. This
        is used mainly to produce warning qrects for a limit_def

        :param qrect: QRectF object
        :type qrect: QRectF

        :param p: The percentage of qrect to return, value is given as a decimal where 0.5 = %50
        :type p: double

        :returns: QRectF

        '''
        (x1, y1, x2, y2) = qrect.getCoords()
        return (QtCore.QRectF(QtCore.QPointF(x1 * p, y1 * p), QtCore.QPointF(x2 * p, y2 * p)))

    def get_saved_range(self):
        s_id = self.scan_sec + self.section_id
        # roi = self._defaults.get_scan_def(s_id)
        roi = self._defaults.get(s_id)
        return ((roi[RANGE][self.p0_idx], roi[RANGE][self.p1_idx]))

    def get_saved_center(self):
        s_id = self.scan_sec + self.section_id
        # roi = self._defaults.get_scan_def(s_id)
        roi = self._defaults.get(s_id)
        return ((roi[CENTER][self.p0_idx], roi[CENTER][self.p1_idx]))

    def get_axis_strs(self):
        return (self.axis_strings)

    # def load_roi(self, ado_obj):
    def load_roi(self, wdg_com, append=False, ev_only=False, sp_only=False):
        """
        take a widget communications dict and load the plugin GUI with the spatial region, also
        set the scan subtype selection pulldown for point by point or line
        """

        # wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)

        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
            sp_db = get_first_sp_db_from_wdg_com(wdg_com)

            if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != self.type):
                return

            if (self.multi_ev):
                self.mod_roi(sp_db, do_recalc=False, ev_only=ev_only, sp_only=sp_only)
            else:
                self.mod_roi(sp_db, do_recalc=False, sp_only=sp_only)
            # THIS CALL IS VERY IMPORTANT IN ORDER TO KEEP TEHPLOT AND TABLES IN SYNC
            add_to_unique_roi_id_list(sp_db[SPDB_ID_VAL])

            # emit roi_changed so that the plotter can be signalled to create the ROI shap items
            self.roi_changed.emit(wdg_com)

    def load_scan(self):
        datadir = self.main_obj.get('APP.USER').get_data_dir()
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        fname = getOpenFileName("Load Scan", filter_str="Scan Files (%s*.hdf5; *.json)" % self.data_file_pfx,
                                search_path=datadir)
        self.openfile(fname)

    def load_scan_definition(self, ev_only=False, sp_only=False):
        scanDefs_dir = self.main_obj.get('APP.USER').get_scan_defs_dir()
        # self.data_file_pfx = self.main_obj.get_datafile_prefix()
        fname = getOpenFileName("Load Scan Definition", filter_str="Scan Def Files (*.hdf5;*.json)",
                                search_path=scanDefs_dir)
        self.openfile(fname, ev_only, sp_only)

    def clear_params(self):
        """ meant to clear all params from table , to be implemented by inheriting class"""
        pass

    def replace_roi_ids_with_current_ones(self, ado_obj):
        wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        sp_ids = get_sp_ids_from_wdg_com(wdg_com)
        sp_roi_dct = dct_get(wdg_com, SPDB_SPATIAL_ROIS)
        sp_rois = {}
        for sp_id in sp_ids:
            u_id = get_unique_roi_id()
            sp_db = sp_roi_dct[sp_id]
            dct_put(sp_db, SPDB_ID_VAL, u_id)
            sp_rois[u_id] = copy.deepcopy(sp_db)
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois)

    @exception
    def openfile(self, fname, ev_only=False, sp_only=False, counter_name='counter0'):
        """
        check_for_cur_scan_tab: this call was originally used by the load_scan buttons on each scan pluggin
        tab which would only load a scan that matched the scan pluggin you were loading from, but to
        support drag and drop operations we will allow the skipping of this check so that the main app
        can automatically make the dropped scan the curent scan pluggin tab
        """

        #group the section id's of scans to allow when loading in teh tomography scan
        allow_load_in_tomo_type  = ['SAMPLE_LXL', 'SAMPLE_PXP', 'TOMO']


        if (fname is None):
            return
        if (not ev_only):
            self.clear_params()
            # tell the parent to clear the slate (plotteer)
            self.clear_all_sig.emit()
            reset_unique_roi_id()

        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        load_image_data = True
        if (fsuffix.find('.json') > -1):
            options = {'standard': 'json', 'def': 'nxstxm'}
            load_image_data = False
        else:
            options = {'standard': 'nexus', 'def': 'nxstxm'}
            if (sp_only or ev_only):
                load_image_data = False

        data_io = self.data_io_class(data_dir, fprefix, options)

        # if(not ev_only):
        #     #tell the parent to clear the slate (plotteer)
        #     self.clear_all_sig.emit()

        entry_dct = data_io.load()
        if (entry_dct is None):
            return
        # use this counter to control if to append or not when loading entries
        i = 0
        ekeys = list(entry_dct.keys())
        ekeys.sort()
        for ekey in ekeys:
            # ekey = entry_dct.keys()[0]
            if (load_image_data):
                nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
                # currently only support 1 counter
                data = data_io.get_signal_data_from_NXdata(nx_datas, counter_name)
            wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
            sp_db = get_first_sp_db_from_wdg_com(wdg_com)

            loaded_scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_SECTION_ID)

            if (ev_only or (loaded_scan_type == self.section_id) or
                    ((self.section_id == 'TOMO') and (loaded_scan_type in allow_load_in_tomo_type))):

                dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.LOAD_SCAN)
                dct_put(sp_db, WDGCOM_CMND, widget_com_cmnd_types.LOAD_SCAN)
                if (i == 0):
                    self.load_roi(wdg_com, append=False, ev_only=ev_only, sp_only=sp_only)
                else:
                    self.load_roi(wdg_com, append=True, ev_only=ev_only, sp_only=sp_only)
                i += 1

                if (not ev_only):
                    # THIS CALL IS VERY IMPORTANT IN ORDER TO KEEP TEHPLOT AND TABLES IN SYNC
                    add_to_unique_roi_id_list(sp_db[SPDB_ID_VAL])

                if (not load_image_data):
                    return

                if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) == scan_types.SAMPLE_POINT_SPECTRA):
                    valid_data_dim = 1

                elif (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) == scan_types.SAMPLE_IMAGE):
                    valid_data_dim = 2

                elif (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) == scan_types.SAMPLE_IMAGE_STACK):
                    valid_data_dim = 3
                else:
                    valid_data_dim = 2

                if ((data.ndim is 3)):
                    data = data[0]

                if ((data.ndim is not valid_data_dim)):
                    _logger.error('Data in file [%s] is of wrong dimension, is [%d] should be [%d]' % (
                    fname, data.ndim, valid_data_dim))
                    print('Data in file [%s] is of wrong dimension, is [%d] should be [%d]' % (
                    fname, data.ndim, valid_data_dim))
                    return
                # signal the main GUI that there is data to plot but only if is is a single image, ignore stack or point spectra scans
                if (len(list(entry_dct.keys())) == 1):
                    if (data is not None):
                        self.plot_data.emit((fname, wdg_com, data))
                    _logger.debug('[%s] scan loaded' % self.section_id)
            else:
                _logger.error('unable to load scan, wrong scan type')
                break

    def on_spatial_row_deleted(self, sp_db):
        """ the table has been changed by keying in new values"""
        wdg_com = make_base_wdg_com()
        sp_rois_dct = {}
        sp_rois_dct[sp_db[SPDB_ID_VAL]] = sp_db
        dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.DEL_ROI)
        dct_put(sp_db, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)
        dct_put(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX, self.data_file_pfx)
        dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
        dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
        dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)

        self.roi_deleted.emit(wdg_com)

    def on_spatial_row_changed(self, sp_rois_dct):
        """ the table has been changed by keying in new values"""
        sp_ids = list(sp_rois_dct.keys())
        # set types for each spatial region
        for sp_id in sp_ids:
            sp_db = sp_rois_dct[sp_id]
            dct_put(sp_db, SPDB_PLOT_IMAGE_TYPE, scan_image_types[self.type])
            dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_PANEL_IDX, self.idx)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX, self.data_file_pfx)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_MAX_SCANRANGE, self.max_scan_range)

            dwell = sp_db[SPDB_EV_ROIS][0][DWELL]
            sec, t_str = self.calc_new_scan_time_estemate(self.sub_type, sp_db[SPDB_X], sp_db[SPDB_Y], dwell)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_EST_SCAN_TIME_SEC, sec)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_EST_SCAN_TIME_SEC, t_str)

        # now set the wdg_com
        wdg_com = make_base_wdg_com()
        dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.ROI_CHANGED)
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)

        self.roi_changed.emit(wdg_com)

    def on_spatial_row_selected(self, sp_db):
        """
        :param wdg_com: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type wdg_com: dict.

        :returns: None

        """
        wdg_com = make_base_wdg_com()
        sp_rois_dct = {}
        sp_rois_dct[sp_db[SPDB_ID_VAL]] = sp_db
        dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.SELECT_ROI)
        dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
        ### Jun 23 2017
        dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)
        ###
        self.roi_changed.emit(wdg_com)

    def check_local_zp_focus_mode(self):
        ''' to be implemented by inheriting class

        :return:
        '''
        pass

    def set_zp_focus_mode(self, mode=None):
        """
        this function sets the mode that controls how the positions for Zpz and Cz are calculated.
        this function is called when the user switches to a new scan in the scans toolbox
        """
        if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
            zpz_scanflag = self.main_obj.device(DNM_ZONEPLATE_SCAN_MODE)
            if (mode is None):
                if (self.zp_focus_mode is zp_focus_modes.DO_NOTHING):
                    pass
                elif (self.zp_focus_mode is zp_focus_modes.CHECK_LOCAL_SETTING):
                    self.check_local_zp_focus_mode()
                else:
                    #zpz_scanflag.put('user_setpoint', self.zp_focus_mode)
                    zpz_scanflag.put(self.zp_focus_mode)
            else:
                #zpz_scanflag.put('user_setpoint', mode)
                zpz_scanflag.put(mode)

    def update_roi_from_flds(self, roi, fld_key):

        if (hasattr(self, 'start%sFld' % fld_key)):
            fld = getattr(self, 'start%sFld' % fld_key)
            roi[START] = float(str(fld.text()))

        if (hasattr(self, 'end%sFld' % fld_key)):
            fld = getattr(self, 'end%sFld' % fld_key)
            roi[STOP] = float(str(fld.text()))

        if (hasattr(self, 'center%sFld' % fld_key)):
            fld = getattr(self, 'center%sFld' % fld_key)
            roi[CENTER] = float(str(fld.text()))

        if (hasattr(self, 'range%sFld' % fld_key)):
            fld = getattr(self, 'range%sFld' % fld_key)
            roi[RANGE] = float(str(fld.text()))

        if (hasattr(self, 'npoints%sFld' % fld_key)):
            fld = getattr(self, 'npoints%sFld' % fld_key)
            roi[NPOINTS] = int(str(fld.text()))

        if (hasattr(self, 'step%sFld' % fld_key)):
            fld = getattr(self, 'step%sFld' % fld_key)
            roi[STEP] = float(str(fld.text()))

    def update_flds_from_roi(self, roi, fld_key):

        if (hasattr(self, 'start%sFld' % fld_key)):
            fld = getattr(self, 'start%sFld' % fld_key)
            fld.setText(d_fmt % roi[START])

        if (hasattr(self, 'end%sFld' % fld_key)):
            fld = getattr(self, 'end%sFld' % fld_key)
            fld.setText(d_fmt % roi[STOP])

        if (hasattr(self, 'center%sFld' % fld_key)):
            fld = getattr(self, 'center%sFld' % fld_key)
            fld.setText(d_fmt % roi[CENTER])

        if (hasattr(self, 'range%sFld' % fld_key)):
            fld = getattr(self, 'range%sFld' % fld_key)
            fld.setText(d_fmt % roi[RANGE])

        if (hasattr(self, 'npoints%sFld' % fld_key)):
            fld = getattr(self, 'npoints%sFld' % fld_key)
            fld.setText('%d' % roi[NPOINTS])

        if (hasattr(self, 'step%sFld' % fld_key)):
            fld = getattr(self, 'step%sFld' % fld_key)
            fld.setText(d_fmt % roi[STEP])

    def update_dpo_min_max(self, dpo, _min, _max):
        dpo._min = _min
        dpo._max = _max

    def connect_param_flds_to_validator(self, lim_dct, respect_lwr_lim=False, respect_hghr_lim=False):
        """
        connect_param_flds_to_validator(): This functions purpose is to take all of the
        QLineEdit fields of a scan param plugin and add to them an object that connects
        the field to an appropriate QValidator that will manage that the values entered
        into each field abide by certain rules, they are limited to a value between the
        llm and hlm values, as well the object handles changeing the background color of each field
        as it is being edited and after a valid value has been recorded when teh enter key
        is pressed. If a valid value has been entered and the return key has been pressed
        the object emits the 'valid_returnPressed' signal which in turn will call the associated
        callback that will recalc all of the other fields in the roi

        :param lim_dct: dictionary of a dictionary of the limits to use
        :type lim_dct: a dict of field keys each containing a dict of limits,
                valid field key values are: ['X', Y, 'ZP]
                each contains values for: ['llm', 'hlm', 'rng']
        :respect_lwr_lim bool: a flag to adjust the validator to respect the lower lim that has been passed as the
                very lowest value allowed, then the highest value allowed becomes [llm + rng]
        :respect_hghr_lim bool: a flag to adjust the validator to respect the higher lim that has been passed as the
                very highest value allowed, then the lowest value allowed becomes [hlm - rng]

        :returns: None
        """

        if (hasattr(self, 'dwellFld')):
            fld = getattr(self, 'dwellFld')
            fld.dpo = dblLineEditParamObj('dwellFld', 0.0, 10000.0, PREC, parent=fld)
            fld.dpo.valid_returnPressed.connect(self.update_data)

        for fld_key in list(lim_dct.keys()):

            llm = lim_dct[fld_key]['llm']
            hlm = lim_dct[fld_key]['hlm']
            rng = lim_dct[fld_key]['rng']
            if(fld_key is 'X'):
                #check to see if the call passed in rngX_llm because if so we will need it to respect the X lower lim
                if('rngX_llm' in list(lim_dct[fld_key].keys())):
                    rngKEY_llm = lim_dct[fld_key]['rngX_llm']
                else:
                    rngKEY_llm = -0.5 * rng
                # check to see if the call passed in rngX_hlm because if so we will need it to respect the X higher lim
                if ('rngX_hlm' in list(lim_dct[fld_key].keys())):
                    rngKEY_hlm = lim_dct[fld_key]['rngX_hlm']
                else:
                    rngKEY_hlm = 0.5 * rng

            if (fld_key is 'Y'):
                # check to see if the call passed in rngY_llm because if so we will need it to respect the Y lower lim
                if ('rngY_llm' in list(lim_dct[fld_key].keys())):
                    rngKEY_llm = lim_dct[fld_key]['rngY_llm']
                else:
                    rngKEY_llm = -0.5 * rng
                # check to see if the call passed in rngY_hlm because if so we will need it to respect the Y higher lim
                if ('rngY_hlm' in list(lim_dct[fld_key].keys())):
                    rngKEY_hlm = lim_dct[fld_key]['rngY_hlm']
                else:
                    rngKEY_hlm = 0.5 * rng

            if (hasattr(self, 'start%sFld' % fld_key)):
                fld_name = 'start%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, llm, hlm, PREC, parent=fld)
                # fld.dpo.valid_returnPressed.connect(self.update_data)
                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_start_changed)

            if (hasattr(self, 'end%sFld' % fld_key)):
                fld_name = 'end%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, llm, hlm, PREC, parent=fld)
                # fld.dpo.valid_returnPressed.connect(self.update_data)
                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_stop_changed)

            if (hasattr(self, 'center%sFld' % fld_key)):
                fld_name = 'center%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, llm, hlm, PREC, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_center_changed)

            if (hasattr(self, 'range%sFld' % fld_key)):
                fld_name = 'range%sFld' % fld_key
                fld = getattr(self, fld_name)
                if(respect_lwr_lim):
                    fld.dpo = dblLineEditParamObj(fld_name, rngKEY_llm, rngKEY_llm + rng, PREC, parent=fld)
                elif(respect_hghr_lim):
                    fld.dpo = dblLineEditParamObj(fld_name, hlm - rng, hlm, PREC, parent=fld)
                else:
                    fld.dpo = dblLineEditParamObj(fld_name, -0.5 * rng, 0.5 * rng, PREC, parent=fld)

                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_range_changed)

            if (hasattr(self, 'npoints%sFld' % fld_key)):
                fld_name = 'npoints%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = intLineEditParamObj(fld_name, 0, 10000, 0, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_npoints_changed)

            if (hasattr(self, 'step%sFld' % fld_key)):
                fld_name = 'step%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, 0.0, 10000.0, PREC, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_spatial_stepsize_changed)

        if ('ZP' in list(lim_dct.keys())):
            fld_key = 'ZP'
            llm = lim_dct[fld_key]['llm']
            hlm = lim_dct[fld_key]['hlm']
            rng = lim_dct[fld_key]['rng']

            if (hasattr(self, 'center%sFld' % fld_key)):
                fld_name = 'center%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, llm, hlm, PREC, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.update_zp_data)

            if (hasattr(self, 'range%sFld' % fld_key)):
                fld_name = 'range%sFld' % fld_key
                fld = getattr(self, fld_name)
                #         self.rangeZPFld.returnPressed.connect(self.on_single_zp_spatial_range_changed)
                fld.dpo = dblLineEditParamObj(fld_name, -0.5 * rng, 0.5 * rng, PREC, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_zp_spatial_range_changed)

            if (hasattr(self, 'npoints%sFld' % fld_key)):
                fld_name = 'npoints%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = intLineEditParamObj(fld_name, 0, 10000, 0, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_zp_spatial_npoints_changed)

            if (hasattr(self, 'step%sFld' % fld_key)):
                fld_name = 'step%sFld' % fld_key
                fld = getattr(self, fld_name)
                fld.dpo = dblLineEditParamObj(fld_name, 0.0, 10000.0, PREC, parent=fld)
                fld.dpo.valid_returnPressed.connect(self.on_single_zp_spatial_stepsize_changed)

    def update_single_spatial_wdg_com(self, is_focus=False, positioner=None):
        """
        This function takes the current local spatial roi for a single spatial
        scan and updates its fields in teh scan plugin GUI, then builds a
        wdg_com dict that is returned to the calling function

        """
        x_roi = dct_get(self.sp_db, SPDB_X)
        y_roi = dct_get(self.sp_db, SPDB_Y)
        e_rois = dct_get(self.sp_db, SPDB_EV_ROIS)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (positioner is not None):
            # the call to update_single_spatial_wdg_com() is coming from a scan pluggin that
            # can select from different positioners to scan, so it plasses in the one
            # to use for the scan.
            # NOTE: we use the x axis for positioner scans
            x_roi[POSITIONER] = positioner

        #         self.update_roi_from_flds(x_roi, SPDB_X)
        #         self.update_roi_from_flds(y_roi, SPDB_Y)
        #         self.update_roi_from_flds(z_roi, 'ZP')

        self.update_flds_from_roi(x_roi, SPDB_X)
        self.update_flds_from_roi(y_roi, SPDB_Y)
        self.update_flds_from_roi(zz_roi, SPDB_ZP)

        if (hasattr(self, 'dwellFld')):
            e_rois[0][DWELL] = float(str(self.dwellFld.text()))
            energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
            e_rois[0][START] = energy_pos
            e_rois[0][STOP] = energy_pos
            e_rois[0][CENTER] = energy_pos

        # image_parms={}

        # is teh following necessary?
        if (y_roi[RANGE] == 0.0):
            x1 = x_roi[START]
            x2 = x_roi[STOP]
            y1 = y_roi[START] - (0.5 * y_roi[NPOINTS])
            y2 = y_roi[STOP] + (0.5 * y_roi[NPOINTS])
        else:
            x1 = x_roi[START]
            x2 = x_roi[STOP]
            y1 = y_roi[START]
            y2 = y_roi[STOP]

        if (dct_get(self.sp_db, SPDB_ID_VAL) is None):
            sp_id = get_unique_roi_id()
        else:
            sp_id = dct_get(self.sp_db, SPDB_ID_VAL)

        dct_put(self.sp_db, SPDB_ID_VAL, sp_id)

        dct_put(self.sp_db, WDGCOM_CMND, widget_com_cmnd_types.ROI_CHANGED)
        dct_put(self.sp_db, SPDB_EV_NPOINTS, 1)
        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
        dct_put(self.sp_db, SPDB_PLOT_IMAGE_TYPE, scan_image_types[self.type])
        dct_put(self.sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
        if (is_focus):
            dct_put(self.sp_db, SPDB_RECT, (x1, zz_roi[START], x2, zz_roi[STOP]))
        else:
            dct_put(self.sp_db, SPDB_RECT, (x1, y1, x2, y2))

        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)
        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX, self.data_file_pfx)

        # assume only 1 ROI
        dct_put(self.sp_db, SPDB_PLOT_ITEM_ID, '%s %d' % (self.plot_item_type, 1))
        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_PANEL_IDX, self.idx)
        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)

        wdg_com = make_base_wdg_com()
        wdg_com[WDGCOM_CMND] = widget_com_cmnd_types.ROI_CHANGED
        wdg_com[WDGCOM_SPATIAL_ROIS] = {sp_id: self.sp_db}

        return (wdg_com)

    def disable_z_roi(self, sp_db):
        '''
        z_roi has no meaning for multi spatial region scans so make them disabled
        :param z_roi:
        :return:
        '''
        #z_roi
        dct_put(sp_db, SPDB_ZENABLED, False)
        dct_put(sp_db, SPDB_ZNPOINTS, 0)
        #zoneplate Z
        dct_put(sp_db, SPDB_ZZENABLED, False)
        dct_put(sp_db, SPDB_ZZNPOINTS, 0)

    def update_multi_spatial_wdg_com(self):
        """
        This is a standard function that all scan pluggins have that is called to
        get the data from the pluggins UI widgets and write them into a dict returned by
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by
        the scan classes configure() functions

        :returns: None

        """
        sp_rois_dct = self.multi_region_widget.get_sp_regions()

        sp_rois = self.multi_region_widget.get_just_sp_regions()
        ev_setpoints = self.multi_region_widget.get_just_ev_setpoints()
        ev_rois = self.multi_region_widget.get_just_ev_regions()
        pol_rois = self.multi_region_widget.get_just_pol_regions()
        dwells = self.multi_region_widget.get_just_dwells()

        sp_ids = list(sp_rois_dct.keys())

        # set types for each spatial region
        for sp_id in sp_ids:
            sp_db = sp_rois_dct[sp_id]
            self.disable_z_roi(sp_db)

            dct_put(sp_db, SPDB_PLOT_IMAGE_TYPE, scan_image_types[self.type])
            dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_PANEL_IDX, self.idx)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_DATAFILE_PFX, self.data_file_pfx)
            dct_put(sp_db, SPDB_SCAN_PLUGIN_MAX_SCANRANGE, self.max_scan_range)
            #Jan 10 2018
            dct_put(sp_db, SPDB_EV_NPOINTS, len(ev_setpoints))
            dct_put(sp_db, SPDB_EV_ROIS, ev_rois)


            # added E712 waveform generator support
            if (hasattr(self, 'useE712WavegenBtn')):
                dct_put(sp_db, SPDB_HDW_ACCEL_USE, self.useE712WavegenBtn.isChecked())
                dct_put(sp_db, SPDB_HDW_ACCEL_AUTO_DDL, self.autoDDLRadBtn.isChecked())
                dct_put(sp_db, SPDB_HDW_ACCEL_REINIT_DDL, self.reinitDDLRadBtn.isChecked())

        # now set the wdg_com
        wdg_com = make_base_wdg_com()
        dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.ROI_CHANGED)
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)

        dct_put(wdg_com, SPDB_SINGLE_LST_SP_ROIS, sp_rois)
        dct_put(wdg_com, SPDB_SINGLE_LST_POL_ROIS, pol_rois)
        dct_put(wdg_com, SPDB_SINGLE_LST_DWELLS, dwells)
        # remove any nans left over from a buggy delete
        i = 0
        for e_roi in ev_setpoints:
            if (math.isnan(e_roi)):
                del (ev_setpoints[i])
            i += 1
        dct_put(wdg_com, SPDB_SINGLE_LST_EV_ROIS, ev_setpoints)

        return (wdg_com)

    def on_single_spatial_start_changed(self):
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (hasattr(self, 'startXFld')):
            x_roi[START] = float(str(self.startXFld.text()))
            on_start_changed(x_roi)

        if (hasattr(self, 'startYFld')):
            y_roi[START] = float(str(self.startYFld.text()))
            on_start_changed(y_roi)

        if (hasattr(self, 'startZFld')):
            z_roi[START] = float(str(self.startZFld.text()))
            on_start_changed(z_roi)

        if (hasattr(self, 'startZPFld')):
            zz_roi[START] = float(str(self.startZPFld.text()))
            on_start_changed(zz_roi)

        if (hasattr(self, 'startGTFld')):
            gt_roi[START] = float(str(self.startGTFld.text()))
            on_start_changed(gt_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_single_spatial_stop_changed(self):
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (hasattr(self, 'endXFld')):
            x_roi[STOP] = float(str(self.endXFld.text()))
            on_stop_changed(x_roi)

        if (hasattr(self, 'endYFld')):
            y_roi[STOP] = float(str(self.endYFld.text()))
            on_stop_changed(y_roi)

        if (hasattr(self, 'endZFld')):
            z_roi[STOP] = float(str(self.endZFld.text()))
            on_stop_changed(z_roi)

        if (hasattr(self, 'endZPFld')):
            zz_roi[STOP] = float(str(self.endZPFld.text()))
            on_stop_changed(zz_roi)

        if (hasattr(self, 'endGTFld')):
            gt_roi[STOP] = float(str(self.endGTFld.text()))
            on_stop_changed(gt_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_single_spatial_center_changed(self):
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (hasattr(self, 'centerXFld')):
            x_roi[CENTER] = float(str(self.centerXFld.text()))
            on_center_changed(x_roi)

        if (hasattr(self, 'centerYFld')):
            y_roi[CENTER] = float(str(self.centerYFld.text()))
            on_center_changed(y_roi)

        if (hasattr(self, 'centerZFld')):
            z_roi[CENTER] = float(str(self.centerZFld.text()))
            on_center_changed(z_roi)

        if (hasattr(self, 'centerZPFld')):
            zz_roi[CENTER] = float(str(self.centerZPFld.text()))
            on_center_changed(zz_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_single_spatial_range_changed(self):
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (x_roi[CENTER] is None):
            if (hasattr(self, 'centerXFld')):
                x_roi[CENTER] = float(str(self.centerXFld.text()))
                on_center_changed(x_roi)
        if (y_roi[CENTER] is None):
            if (hasattr(self, 'centerYFld')):
                y_roi[CENTER] = float(str(self.centerYFld.text()))
                on_center_changed(y_roi)

        if (z_roi[CENTER] is None):
            if (hasattr(self, 'centerZFld')):
                z_roi[CENTER] = float(str(self.centerZFld.text()))
                on_center_changed(z_roi)

        if (zz_roi[CENTER] is None):
            if (hasattr(self, 'centerZPFld')):
                zz_roi[CENTER] = float(str(self.centerZPFld.text()))
                on_center_changed(zz_roi)

        if (hasattr(self, 'rangeXFld')):
            x_roi[RANGE] = float(str(self.rangeXFld.text()))
            on_range_changed(x_roi)

        if (hasattr(self, 'rangeYFld')):
            y_roi[RANGE] = float(str(self.rangeYFld.text()))
            on_range_changed(y_roi)

        if (hasattr(self, 'rangeZFld')):
            z_roi[RANGE] = float(str(self.rangeZFld.text()))
            on_range_changed(z_roi)

        if (hasattr(self, 'rangeZPFld')):
            zz_roi[RANGE] = float(str(self.rangeZPFld.text()))
            on_range_changed(zz_roi)

        #support the pattern generators pad size field which sets the xy range
        if (hasattr(self, 'padSizeFld')):
            x_roi[RANGE] = float(str(self.padSizeFld.text()))
            y_roi[RANGE] = float(str(self.padSizeFld.text()))
            on_range_changed(x_roi)
            on_range_changed(y_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_single_spatial_stepsize_changed(self):

        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)


        #         if(hasattr(self,'centerXFld')):
        #             x_roi[CENTER] = float(str(self.centerXFld.text()))
        #             on_center_changed(x_roi)
        #
        #         if(hasattr(self,'centerYFld')):
        #             y_roi[CENTER] = float(str(self.centerYFld.text()))
        #             on_center_changed(y_roi)
        #
        #         if(hasattr(self,'centerZPFld')):
        #             z_roi[CENTER] = float(str(self.centerZPFld.text()))
        #             on_center_changed(z_roi)

        if (hasattr(self, 'stepXFld')):
            x_roi[STEP] = float(str(self.stepXFld.text()))
            on_step_size_changed(x_roi)

        if (hasattr(self, 'stepYFld')):
            y_roi[STEP] = float(str(self.stepYFld.text()))
            on_step_size_changed(y_roi)

        if (hasattr(self, 'stepZFld')):
            z_roi[STEP] = float(str(self.stepZFld.text()))
            on_step_size_changed(z_roi)

        if (hasattr(self, 'stepZPFld')):
            zz_roi[STEP] = float(str(self.stepZPFld.text()))
            on_step_size_changed(zz_roi)

        if (hasattr(self, 'stepGTFld')):
            gt_roi[STEP] = float(str(self.stepGTFld.text()))
            on_step_size_changed(gt_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_single_spatial_npoints_changed(self):
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        z_roi = self.sp_db[SPDB_Z]
        gt_roi = dct_get(self.sp_db, SPDB_GT)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (hasattr(self, 'startXFld')):
            x_roi[START] = float(str(self.startXFld.text()))
            on_start_changed(x_roi)

        if (hasattr(self, 'endXFld')):
            x_roi[STOP] = float(str(self.endXFld.text()))
            on_stop_changed(x_roi)

        if (hasattr(self, 'centerXFld')):
            x_roi[CENTER] = float(str(self.centerXFld.text()))
            on_center_changed(x_roi)

        if (hasattr(self, 'startYFld')):
            y_roi[START] = float(str(self.startYFld.text()))
            on_start_changed(y_roi)

        if (hasattr(self, 'endYFld')):
            y_roi[STOP] = float(str(self.endYFld.text()))
            on_stop_changed(y_roi)

        if (hasattr(self, 'centerYFld')):
            y_roi[CENTER] = float(str(self.centerYFld.text()))
            on_center_changed(y_roi)

        if (hasattr(self, 'centerZFld')):
            z_roi[CENTER] = float(str(self.centerZFld.text()))
            on_center_changed(z_roi)

        if (hasattr(self, 'centerZPFld')):
            zz_roi[CENTER] = float(str(self.centerZPFld.text()))
            on_center_changed(zz_roi)

        if (hasattr(self, 'npointsXFld')):
            x_roi[NPOINTS] = int(str(self.npointsXFld.text()))
            on_npoints_changed(x_roi)

        if (hasattr(self, 'npointsYFld')):
            y_roi[NPOINTS] = int(str(self.npointsYFld.text()))
            on_npoints_changed(y_roi)

        if (hasattr(self, 'npointsZFld')):
            z_roi[NPOINTS] = int(str(self.npointsZFld.text()))
            on_npoints_changed(z_roi)

        if (hasattr(self, 'npointsZPFld')):
            zz_roi[NPOINTS] = int(str(self.npointsZPFld.text()))
            on_npoints_changed(zz_roi)

        if (hasattr(self, 'npointsGTFld')):
            gt_roi[NPOINTS] = int(str(self.npointsGTFld.text()))
            on_npoints_changed(gt_roi)

        self.mod_roi(self.sp_db, do_recalc=False)

        self.update_data()

    def on_focus_scan_single_spatial_npoints_changed(self):
        """ focus scans use the same number of points for Y as they do for X
        focus scans are a line between two arbitrary points (x1, y1, x2, y2)
        therefore we use the same number of points for both but only the npointsXFld
        exists on focus scans, so copy the number of points to Y so that the [SETPOINTS]
        for Y will be calculated correctly
        """
        npointsX = int(str(self.npointsXFld.text()))
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]

        y_roi[NPOINTS] = npointsX
        on_npoints_changed(y_roi)

        x_roi[NPOINTS] = npointsX
        on_npoints_changed(x_roi)

        # call the main on_single_spatial_npoints_changed()
        self.on_single_spatial_npoints_changed()

    def on_focus_on_single_spatial_stepsize_changed(self):
        pass

    def on_focus_scan_load(self, sp_db):
        """
        wdg_com is a widget_com dict
        The purpose of the on_focus_scan_load() function is to update the fields in the GUI with the values
        passed in from teh loaded scan

        :param wdg_com: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type wdg_com: dict.

        :returns: None

        """
        # dct_put(self.wdg_com,SPDB_SCAN_PLUGIN_ITEM_ID, dct_get(wdg_com,SPDB_SCAN_PLUGIN_ITEM_ID))
        dct_put(self.sp_db, SPDB_PLOT_ITEM_ID, dct_get(sp_db, SPDB_PLOT_ITEM_ID))

        # the rois that exist in the loaded file dict do not have the functions for 'on_center_changed' etc
        # so the ROIS must be rebuilt
        x_roi = sp_db[SPDB_X]
        y_roi = sp_db[SPDB_Y]

        #z_roi = sp_db[SPDB_Z]
        zz_roi = dct_get(sp_db, SPDB_ZZ)

        #hack until files saved properly
        if(zz_roi[START] is None):
            zz_roi = sp_db[SPDB_Z]
        else:
            zz_roi = dct_get(sp_db, SPDB_ZZ)

        zp_rois = {}
        dct_put(zp_rois, SPDB_ZZ, zz_roi)

        e_rois = sp_db[SPDB_EV_ROIS]
        e_roi = get_base_energy_roi('EV', DNM_ENERGY, 395, 395, 0, 1, e_rois[0][DWELL], None, enable=False)
        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, zp_rois=zp_rois)

        # now that everything has been updated go ahead and use them
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        #z_roi = self.sp_db[SPDB_Z]
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)
        e_rois = self.sp_db[SPDB_EV_ROIS]

        self.set_parm(self.startXFld, x_roi[START])
        self.set_parm(self.startYFld, y_roi[START])
        self.set_parm(self.endXFld, x_roi[STOP])
        self.set_parm(self.endYFld, y_roi[STOP])

        self.set_parm(self.centerZPFld, zz_roi[CENTER])

        if (e_rois[0][DWELL] is not None):
            self.set_parm(self.dwellFld, e_rois[0][DWELL])

        if (x_roi[NPOINTS] is not None):
            self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=1)
        if (zz_roi[NPOINTS] is not None):
            self.set_parm(self.npointsZPFld, zz_roi[NPOINTS], type='int', floor=1)

        if (x_roi[STEP] is not None):
            self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)
        if (zz_roi[STEP] is not None):
            self.set_parm(self.stepZPFld, zz_roi[STEP], type='float', floor=0)

    def focus_scan_mod_roi(self, wdg_com, do_recalc=True):
        """
        wdg_com is a widget_com dict
        The purpose of the mod_roi() function is to update the fields in the GUI with the correct values
        it can be called by either a signal from one of the edit fields (ex: self.startXFld) or
        by a signal from a plotter (via the main gui that is connected to the plotter) so that as a user
        grabs a region of interest marker in the plot and either moves or resizes it, those new center and size
        values will be delivered here and,  if required, the stepsizes will be recalculated

        There are several reasons why this routiune gets called:

        if dct_get(wdg_com, SPDB_PLOT_SHAPE_TYPE is None then called by a plot signal used to update the parameters for ZpZ, here the plot
                is not creating a ShapeItem it is merely choosing a new ZPZ center, here X and Y do NOT change

        if dct_get(wdg_com, SPDB_PLOT_SHAPE_TYPE == an integer
            - called by a plot signal that is creating a new ROI, here only X and Y to change

        :param wdg_com: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type wdg_com: dict.

        :param do_recalc: selectively the STEP of the ROI's for X and Y can be recalculated if the number of points or range have changed
        :type do_recalc: flag.

        :returns: None

        """
        keys_pressed_dct = dct_get(wdg_com, SPDB_PLOT_KEY_PRESSED)
        if(keys_pressed_dct is not None):
            if(keys_pressed_dct[QtCore.Qt.Key_Control] and keys_pressed_dct[QtCore.Qt.Key_C]):
                #the user is trying to set the center but for focus scans but we want to not allow this
                #because sometimes it fails causing the the value of zpz to be applied to the spatial Y field
                zz_roi = dct_get(self.sp_db, SPDB_ZZ)
                zz_roi[CENTER] = dct_get(wdg_com, SPDB_Y)[CENTER]

                # for some reason when the focus line to scan is selected or deselected
                # the zz_roi has None for a CENTER, sort this out in the future, for now just dont bother recalculating
                if (zz_roi[CENTER] is not None):
                    on_center_changed(zz_roi)
                    self.set_parm(self.centerZPFld, zz_roi[CENTER])
                return

        # single spatial scan pluggins have nothing to delete, so just leave the params where they are
        # even though the plotter has issued this DEL_ROI
        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.DEL_ROI):
            return

        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
            self.on_focus_scan_load(wdg_com)
            return

        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.SELECT_ROI):
            # dct_put(self.wdg_com,SPDB_SCAN_PLUGIN_ITEM_ID, dct_get(wdg_com,SPDB_PLOT_ITEM_ID))
            dct_put(self.sp_db, SPDB_ID_VAL, dct_get(wdg_com, SPDB_PLOT_ITEM_ID))

        # dct_put(self.wdg_com,SPDB_SCAN_PLUGIN_ITEM_ID, dct_get(wdg_com,SPDB_SCAN_PLUGIN_ITEM_ID))
        dct_put(self.sp_db, SPDB_PLOT_ITEM_ID, dct_get(wdg_com, SPDB_PLOT_ITEM_ID))
        dct_put(self.sp_db, SPDB_PLOT_IMAGE_TYPE, dct_get(wdg_com, SPDB_PLOT_IMAGE_TYPE))

        # depending on what image is curreently loaded Y and Z mean different things
        if ((dct_get(wdg_com, SPDB_PLOT_IMAGE_TYPE) == image_types.OSAFOCUS) or \
                    (dct_get(wdg_com, SPDB_PLOT_IMAGE_TYPE) == image_types.FOCUS) or \
                    (dct_get(wdg_com, SPDB_PLOT_IMAGE_TYPE) is None)):
            # Y means Z because the plot is using the coordinates of an osa_focus scan (the Y axis is ZpZ)
            # set Y to see no change in current params
            if (dct_get(wdg_com, SPDB_PLOT_SHAPE_TYPE) is None):
                cur_y_roi = self.sp_db[SPDB_Y]
                y_roi = cur_y_roi

                cur_x_roi = self.sp_db[SPDB_X]
                x_roi = cur_x_roi

                # set Z using passed in Y axis values
                #z_roi = self.sp_db[SPDB_Z]
                zz_roi = dct_get(self.sp_db, SPDB_ZZ)
                #zz_roi[CENTER] = sp_db[SPDB_Y][CENTER]
                zz_roi[CENTER] = dct_get(wdg_com, SPDB_ZZ)[CENTER]

                #for some reason when the focus line to scan is selected or deselected
                #the zz_roi has None for a CENTER, sort this out in the future, for now just dont bother recalculating
                if(zz_roi[CENTER] is not None):
                    on_center_changed(zz_roi)
                    self.set_parm(self.centerZPFld, zz_roi[CENTER])
            else:

                cur_x_roi = self.sp_db[SPDB_X]
                x_roi = wdg_com[SPDB_X]

                cur_y_roi = self.sp_db[SPDB_Y]
                y_roi = wdg_com[SPDB_Y]

                cur_x_roi[START] = x_roi[START]
                on_start_changed(cur_x_roi)

                cur_x_roi[STOP] = x_roi[STOP]
                on_stop_changed(cur_x_roi)

                cur_y_roi[START] = y_roi[START]
                on_start_changed(cur_y_roi)

                cur_y_roi[STOP] = y_roi[STOP]
                on_stop_changed(cur_y_roi)
        else:

            cur_x_roi = self.sp_db[SPDB_X]
            x_roi = wdg_com[SPDB_X]

            cur_y_roi = self.sp_db[SPDB_Y]
            y_roi = wdg_com[SPDB_Y]

            cur_x_roi[START] = x_roi[START]
            on_start_changed(cur_x_roi)

            cur_x_roi[STOP] = x_roi[STOP]
            on_stop_changed(cur_x_roi)

            cur_y_roi[START] = y_roi[START]
            on_start_changed(cur_y_roi)

            cur_y_roi[STOP] = y_roi[STOP]
            on_stop_changed(cur_y_roi)

        # now that everything has been updated go ahead and use them
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        #z_roi = self.sp_db[SPDB_Z]
        e_rois = self.sp_db[SPDB_EV_ROIS]
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        if (y_roi[START] == y_roi[STOP]):
            self.sub_type = scan_sub_types.LINE_UNIDIR
        else:
            self.sub_type = scan_sub_types.POINT_BY_POINT

        self.set_parm(self.startXFld, x_roi[START])
        self.set_parm(self.startYFld, y_roi[START])
        self.set_parm(self.endXFld, x_roi[STOP])
        self.set_parm(self.endYFld, y_roi[STOP])

        # self.set_parm(self.centerZPFld, z_roi[CENTER])

        if (e_rois[0][DWELL] is not None):
            self.set_parm(self.dwellFld, e_rois[0][DWELL])

        if (x_roi[NPOINTS] is not None):
            self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=1)
        if (zz_roi[NPOINTS] is not None):
            self.set_parm(self.npointsZPFld, zz_roi[NPOINTS], type='int', floor=1)

        if (x_roi[STEP] is not None):
            self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)
        if (zz_roi[STEP] is not None):
            self.set_parm(self.stepZPFld, zz_roi[STEP], type='float', floor=0)

    def get_max_fine_scan_range(self):
        ''' to be implemented by inheriting class'''
        return(0.0)

    def focus_scan_update_data(self, force_pxp=False):
        """
        This is a standard function that all scan pluggins have that is called to
        get the data from the pluggins UI widgets and write them into a dict returned by
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by
        the scan classes configure() functions

        :param force_pxp: the caller can force a pxp sub type (like for OSA focus scans)
        :type wdg_com: bool.

        :returns: None

        """

        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        #z_roi = self.sp_db[SPDB_Z]
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)

        startX = float(str(self.startXFld.text()))
        endX = float(str(self.endXFld.text()))
        npointsX = int(
            str(self.npointsXFld.text()))  # + NUM_POINTS_LOST_AFTER_EDIFF  #+1 for the first data point being the row
        x_roi[START] = startX
        x_roi[STOP] = endX
        x_roi[NPOINTS] = npointsX

        on_start_changed(x_roi)
        on_stop_changed(x_roi)
        on_npoints_changed(x_roi)

        startY = float(str(self.startYFld.text()))
        endY = float(str(self.endYFld.text()))
        npointsY = npointsX  # make sure same as X
        y_roi[START] = startY
        y_roi[STOP] = endY
        y_roi[NPOINTS] = npointsY

        on_start_changed(y_roi)
        on_stop_changed(y_roi)
        on_npoints_changed(y_roi)

        dwell = float(str(self.dwellFld.text()))

        zp_startY = float(str(self.centerZPFld.text()))
        zp_rngY = float(str(self.rangeZPFld.text()))
        zp_npointsY = int(str(self.npointsZPFld.text()))
        zz_roi[CENTER] = zp_startY
        zz_roi[RANGE] = zp_rngY
        zz_roi[NPOINTS] = zp_npointsY

        if(force_pxp):
            self.sub_type = scan_sub_types.POINT_BY_POINT
        else:
            if (y_roi[START] == y_roi[STOP]):
                self.sub_type = scan_sub_types.LINE_UNIDIR
            else:
                self.sub_type = scan_sub_types.POINT_BY_POINT

        on_center_changed(zz_roi)
        on_range_changed(zz_roi)
        on_npoints_changed(zz_roi)

        recalc_setpoints(x_roi)
        recalc_setpoints(y_roi)
        # already done by 'on_center_changed' z_roi['recalc_setpoints'](z_roi)

        # update local widget_com dict
        wdg_com = self.update_single_spatial_wdg_com(is_focus=True)

        self._defaults.set('SCAN.%s.CENTER' % self.section_id, (startX, startY, zp_startY, 0))
        self._defaults.set('SCAN.%s.RANGE' % self.section_id, (endX, endY, zp_rngY, 0))
        self._defaults.set('SCAN.%s.NPOINTS' % self.section_id, (npointsX, npointsY, zp_npointsY, 0))
        self._defaults.set('SCAN.%s.DWELL' % self.section_id, dwell)
        self._defaults.update()

        #         dct_put(self.wdg_com, WDGCOM_CMND, widget_com_cmnd_types.ROI_CHANGED)
        #         dct_put(self.wdg_com, SPDB_EV_NPOINTS, 1)
        #
        #         dct_put(self.wdg_com, SPDB_PLOT_IMAGE_TYPE, scan_image_types[self.type])
        #         dct_put(self.wdg_com, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
        #         dct_put(self.wdg_com, SPDB_PLOT_ITEM_ID, '%s %d' % (self.plot_item_type, 1))
        #         dct_put(self.wdg_com, SPDB_RECT, (x_roi[START], z_roi[START], x_roi[STOP], z_roi[STOP]))
        #         #dct_put(self.wdg_com, 'CURRENT.SCAN.IMAGE_PARMS', image_parms)
        #         dct_put(self.wdg_com, SPDB_SCAN_PLUGIN_TYPE, self.type)
        #         dct_put(self.wdg_com, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
        #         dct_put(self.wdg_com, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)
        #         dct_put(self.wdg_com, SPDB_SCAN_PLUGIN_DATAFILE_PFX, self.data_file_pfx)
        #
        #         if(dct_get(self.wdg_com, SPDB_ID_VAL) is None):
        #             dct_put(self.wdg_com, SPDB_ID_VAL, get_unique_roi_id())

        # self.roi_changed.emit(wdg_com)
        return (wdg_com)

    def on_single_zp_spatial_range_changed(self):
        self.blockSignals(True)
        self.on_single_spatial_range_changed()
        self.blockSignals(False)

    def on_single_zp_spatial_npoints_changed(self):
        self.blockSignals(True)
        self.on_single_spatial_npoints_changed()
        self.blockSignals(False)

    def on_single_zp_spatial_stepsize_changed(self):
        self.blockSignals(True)
        self.on_single_spatial_stepsize_changed()
        self.blockSignals(False)

    def update_zp_data(self):
        self.blockSignals(True)
        self.update_data()
        self.blockSignals(False)

    def calc_correction(self, x, y, z, t):
        '''
        here it is hoped that the mathematical model will go to calculate the corrections required to reposition the sample correctly
        based on a new theta value
        for now the model is only to offset the value by %10 of theta
        '''
        #         new_x = x + (0.1 * t)
        #         new_y = y + (0.1 * t)
        #         new_z = z + (0.1 * t)
        #         return(new_x, new_y, new_z)
        #
        new_x = x
        new_y = y
        new_z = z
        return (new_x, new_y, new_z)

    def apply_correction_model(self, gx_roi, gy_roi, gz_roi, gt_roi):
        x = gx_roi[SETPOINTS][0]
        y = gy_roi[SETPOINTS][0]
        z = gz_roi[SETPOINTS][0]
        idx = 0
        for t in gt_roi[SETPOINTS]:
            gx_roi[idx], gy_roi[idx], gz_roi[idx] = self.calc_correction(x, y, z, t)
            idx += 1

    def dump_qrectf(self, qrectf):
        '''
        used during debugging
        :param qrectf:
        :return:
        '''
        print('\tleft: %.3f' % qrectf.left())
        print('\ttop: %.3f' % qrectf.top())
        print('\tright: %.3f' % qrectf.right())
        print('\tbottom: %.3f' % qrectf.bottom())
        _cntr = qrectf.center()
        _rng = (qrectf.width(), qrectf.height())
        print('center: (%.3f, %.3f)' % (_cntr.x(), _cntr.y()))
        print('range: (%.3f, %.3f)' % (_rng[0], _rng[1]))

    def modify_sp_db_for_goni(self, sp_db, multi_sp_goni_center=-99.99, is_focus=False):
        '''
        goni_center will be set to the center of all of the sp_dbs
        :param sp_db:
        :param goni_center:
        :param is_focus:
        :return:
        '''

        MAX_SCAN_RANGE_FINEX = self.main_obj.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
        MAX_SCAN_RANGE_FINEY = self.main_obj.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
        MAX_SCAN_RANGE_X = self.main_obj.get_preset_as_float('MAX_SCAN_RANGE_X')
        MAX_SCAN_RANGE_Y = self.main_obj.get_preset_as_float('MAX_SCAN_RANGE_Y')

        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)
        mtr_gz = self.main_obj.device(DNM_GONI_Z)
        mtr_gt = self.main_obj.device(DNM_GONI_THETA)
        mtr_oz = self.main_obj.device(DNM_OSA_Z)

        # here we need to turn the absolute scan region (goni XY) that the user selected
        # into one that is centered around 0 as our ZP XY is
        if (is_focus):
            rect = (sp_db['X'][START], sp_db['Y'][START], sp_db['X'][STOP], sp_db['Y'][STOP])
        else:
            # SPDB_RECT is (left, top, right, bottom)
            rect = sp_db[SPDB_RECT]

        #scan_rect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[1]), QtCore.QPointF(rect[2], rect[3]))
        #NOTE: Y is flipped here to rectify the rect for plotting when making its decision on wether or not the desired
        # scan fits in range of the current positions of the goniometer
        scan_rect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[3]), QtCore.QPointF(rect[2], rect[1]))

        dx = scan_rect.center().x() - mtr_gx.get_position()
        dy = scan_rect.center().y() - mtr_gy.get_position()

        dx = scan_rect.center().x() - mtr_gx.get_position()
        dy = scan_rect.center().y() - mtr_gy.get_position()

        max_fxrng = mtr_gx.get_position() + (MAX_SCAN_RANGE_FINEX * 0.5)
        min_fxrng = mtr_gx.get_position() - (MAX_SCAN_RANGE_FINEX * 0.5)
        max_fyrng = mtr_gy.get_position() + (MAX_SCAN_RANGE_FINEY * 0.5)
        min_fyrng = mtr_gy.get_position() - (MAX_SCAN_RANGE_FINEY * 0.5)

        # _cntr = scan_rect.center()
        # _rng = (scan_rect.width(), scan_rect.height())
        # #print 'scan_rect center=(%.3f, %.3f)  range=(%.3f, %.3f)' % (_cntr.x(), _cntr.y(), _rng[0], _rng[1])

        # current valid scan rectangle
        cur_valid_rect = QtCore.QRectF(QtCore.QPointF(min_fxrng, max_fyrng), QtCore.QPointF(max_fxrng, min_fyrng))
        # print 'cur_valid_rect:'
        # self.dump_qrectf(cur_valid_rect)
        # print 'scan_rect:'
        # self.dump_qrectf(scan_rect)

        new_center = False

        # if((abs(dx) > 30.0) or (abs(dy) > 30.0)):
        #if ((abs(dx) > (MAX_SCAN_RANGE_FINEX * 0.5)) or (abs(dy) > (MAX_SCAN_RANGE_FINEY * 0.5))):
        if(not cur_valid_rect.contains(scan_rect)):
            new_center = True
            #print 'modify_sp_db_for_goni: NEW GONI CENTER NEEDED'
        else:
            #print 'modify_sp_db_for_goni: goni center stays where it is'
            pass

        if (new_center):
            # scan is larger than the zoneplate can handle so we will be moving the goni X/Y to center of scan thus it
            # will be centered around 0,0
            scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
            osax_center = 0.0
            osay_center = 0.0

            gonix_center = dct_get(sp_db, SPDB_XCENTER)
            goniy_center = dct_get(sp_db, SPDB_YCENTER)

        else:
            scan_rect.moveCenter(QtCore.QPointF(dx, dy))
            # only need to offset OSA X by %50 of the total dx to achieve even illumination
            # we change the sign of dx because the setpoint must reflect what needs to happen to OSA X to put THE BEAM in the center of the OSA
            osax_center = dx * -1.0  # * 2.0
            osay_center = dy * -1.0  # * 2.0
            # leave at current position
            gonix_center = mtr_gx.get_position()
            goniy_center = mtr_gy.get_position()

        x_roi = get_base_roi(SPDB_GX, DNM_GONI_X, dct_get(sp_db, SPDB_XCENTER), dct_get(sp_db, SPDB_XRANGE),
                             dct_get(sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        y_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, dct_get(sp_db, SPDB_YCENTER), dct_get(sp_db, SPDB_YRANGE),
                             dct_get(sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)



        #gt_roi = get_base_start_stop_roi(SPDB_GT, DNM_GONI_THETA, mtr_gt.get_position(), mtr_gt.get_position(), 1, enable=True)
        if(hasattr(self,'sp_db')):
            gt_start = dct_get(self.sp_db, SPDB_GTSTART)
            gt_stop = dct_get(self.sp_db, SPDB_GTSTOP)
            gt_npoints = dct_get(self.sp_db, SPDB_GTNPOINTS)
            gt_roi = get_base_start_stop_roi(SPDB_GT, DNM_GONI_THETA, gt_start, gt_stop, gt_npoints,
                                             enable=True)
            zpz_adjust_roi = dct_get(self.sp_db, SPDB_G_ZPZ_ADJUST)
        else:
            gt_roi = get_base_start_stop_roi(SPDB_GT, DNM_GONI_THETA, mtr_gt.get_position(),
                                             mtr_gt.get_position(), 1, enable=True)
            zpz_adjust_roi = get_base_roi(SPDB_G_ZPZ_ADJUST, 'NONE', 0.0, 0.0, 1, stepSize=None,
                                          max_scan_range=None,
                                          enable=False)

        gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, gonix_center, dct_get(sp_db, SPDB_XRANGE),
                              dct_get(sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True,
                              is_point=False)
        gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, goniy_center, dct_get(sp_db, SPDB_YRANGE),
                              dct_get(sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        gz_roi = get_base_roi(SPDB_GZ, DNM_GONI_Z, mtr_gz.get_position(), 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=True)

        self.apply_correction_model(gx_roi, gy_roi, gz_roi, gt_roi)

        # here use only a single OSA XY, when subdividing then this will need to be a set of setpoints = #subdivisions * # Y points
        ox_roi = get_base_roi(SPDB_OX, DNM_OSA_X, osax_center, 0, 1, stepSize=None, max_scan_range=None,
                              enable=True, is_point=False)
        oy_roi = get_base_roi(SPDB_OY, DNM_OSA_Y, osay_center, 0, 1, stepSize=None, max_scan_range=None,
                              enable=True, is_point=False)
        # Z disabled for now
        oz_roi = get_base_roi(SPDB_OZ, DNM_OSA_Z, mtr_oz.get_position(), 0, 1, stepSize=None,
                              max_scan_range=None, enable=False, is_point=False)

        # this needs to be handled properly for multi subspatial
        ox_roi[SETPOINTS] = [ox_roi[CENTER]]
        oy_roi[SETPOINTS] = [oy_roi[CENTER]]
        oz_roi[SETPOINTS] = [oz_roi[CENTER]]

        # now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
        zxnpts = dct_get(sp_db, SPDB_XNPOINTS)
        zx_roi = get_base_start_stop_roi(SPDB_X, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), zxnpts,
                                         enable=True)

        zynpts = dct_get(sp_db, SPDB_YNPOINTS)
        zy_roi = get_base_start_stop_roi(SPDB_Y, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), zynpts,
                                         enable=True)

        #because this is strictly for modiifications FOR THE GONIOMETER that means that x_roi and y_roi contain the scan
        # params and zx_roi zy_roi do not contain scan param info, so copy x_roi to zx_roi and same for y/zy
        dct_put(sp_db, SPDB_ZX, zx_roi)
        dct_put(sp_db, SPDB_ZY, zy_roi)
        #dct_put(sp_db, SPDB_ZX, x_roi)
        #dct_put(sp_db, SPDB_ZY, y_roi)

        # x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
        dct_put(sp_db, SPDB_X, x_roi)
        dct_put(sp_db, SPDB_Y, y_roi)
        dct_put(sp_db, SPDB_SPATIAL_ROIS_CENTER, multi_sp_goni_center)

        # it is fine the way it is
        dct_put(sp_db, SPDB_GX, gx_roi)
        dct_put(sp_db, SPDB_GY, gy_roi)
        dct_put(sp_db, SPDB_GZ, gz_roi)
        dct_put(sp_db, SPDB_GT, gt_roi)
        dct_put(sp_db, SPDB_G_ZPZ_ADJUST, zpz_adjust_roi)

        dct_put(sp_db, SPDB_OX, ox_roi)
        dct_put(sp_db, SPDB_OY, oy_roi)
        dct_put(sp_db, SPDB_OZ, oz_roi)

        # added E712 waveform generator support
        if(hasattr(self, 'useE712WavegenBtn')):
            dct_put(sp_db, SPDB_HDW_ACCEL_USE, self.useE712WavegenBtn.isChecked())
        else:
            dct_put(sp_db, SPDB_HDW_ACCEL_USE, False)

        if (hasattr(self, 'autoDDLRadBtn')):
            dct_put(sp_db, SPDB_HDW_ACCEL_AUTO_DDL, self.autoDDLRadBtn.isChecked())
            #make sure this is set in case teh plugin ui widget had its useE712WavegenBtn removed for space
            dct_put(sp_db, SPDB_HDW_ACCEL_USE, True)
        else:
            dct_put(sp_db, SPDB_HDW_ACCEL_AUTO_DDL, False)

        if (hasattr(self, 'reinitDDLRadBtn')):
            dct_put(sp_db, SPDB_HDW_ACCEL_REINIT_DDL, self.reinitDDLRadBtn.isChecked())
            # make sure this is set in case teh plugin ui widget had its useE712WavegenBtn removed for space
            dct_put(sp_db, SPDB_HDW_ACCEL_USE, True)
        else:
            dct_put(sp_db, SPDB_HDW_ACCEL_REINIT_DDL, False)

        return (sp_db)
