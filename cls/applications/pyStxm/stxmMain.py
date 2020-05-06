'''
Created on 2014-06-23

@author: bergr
'''

"""
.. module:: septScanMainWindow
    :platform: Windows
    :synopsis: The main module for pySTXM
.. moduleauthor:: Russ Berg <russ.berg@lightsource.ca>

"""
import os
import time
from importlib.machinery import SourceFileLoader
from time import mktime, strftime, strptime, gmtime
import sys, os
import atexit

import logging
import numpy as np
import simplejson as json
import webbrowser
import copy
from PyQt5 import QtCore, QtGui, uic, QtWidgets

from cls.appWidgets.splashScreen import get_splash
from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.sm_user import usr_acct_manager

from cls.utils.log import get_module_logger, log_to_qt, log_to_console, log_to_qt_and_to_file
from cls.utils.roi_dict_defs import *
from cls.utils.list_utils import sum_lst
from cls.utils.cfgparser import ConfigClass
from cls.utils.roi_utils import widget_com_cmnd_types, get_first_sp_db_from_wdg_com, reset_unique_roi_id, \
    add_to_unique_roi_id_list
from cls.utils.file_system_tools import master_get_seq_names, get_thumb_file_name_list
from cls.utils.prog_dict_utils import *
from cls.utils.sig_utils import reconnect_signal, disconnect_signal

from cls.plotWidgets.imageWidget import ImageWidget
from cls.plotWidgets.zmq_imageWidget import ZMQImageWidget as ImgPlotWindow
from cls.plotWidgets.striptool.stripToolWidget import StripToolWidget
from cls.plotWidgets.curveWidget import CurveViewerWidget, get_next_color, get_basic_line_style
from cls.plotWidgets.utils import *

from cls.data_io.stxm_data_io import STXMDataIo
from cls.scanning.BaseScan import LOAD_ALL
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
# from cls.scanning.dataRecorder import HdrData
from cls.types.stxmTypes import image_types, scan_types, scan_sub_types, spectra_type_scans, \
    spatial_type_prefix, energy_scan_order_types, sample_fine_positioning_modes, \
    sample_positioning_modes, scan_status_types, endstation_id_types

from cls.scanning.widgets.sscan_status import SScanStatusWidget
from cls.scanning.base import ScanParamWidget

from cls.devWidgets.ophydLabelWidget import ophyd_aiLabelWidget, ophyd_mbbiLabelWidget, ophyd_strLabel, ophyd_biLabelWidget, format_text
from cls.devWidgets.ophydPushBtn import ophydPushBtn
from cls.appWidgets.user_account.login import loginWidget
#from cls.applications.pyStxm.widgets.thumbnailViewer_wip import ContactSheet
from cls.applications.pyStxm.widgets.thumbnailViewer import ContactSheet
from cls.appWidgets.dialogs import excepthook
from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
from cls.appWidgets.thread_worker import Worker
from cls.app_data.defaults import master_colors, get_style, rgb_as_hex, master_q_colors

#from cls.applications.pyStxm.widgets.sampleSelector import SampleSelectorWidget
from cls.applications.pyStxm.widgets.motorPanel import PositionersPanel
from cls.applications.pyStxm.widgets.beam_spot_fbk import BeamSpotFeedbackObj
#from cls.applications.pyStxm.widgets.toolsPanel import ToolsPanel
from cls.applications.pyStxm.widgets.devDisplayPanel import DevsPanel
#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES

from cls.appWidgets.main_object import  POS_TYPE_BL, POS_TYPE_ES
from cls.applications.pyStxm.widgets.scan_queue_table import ScanQueueTableWidget
from cls.applications.pyStxm.widgets.ioc_apps_panel import IOCAppsPanel
from cls.applications.pyStxm.widgets.ccd_viewer import CCDViewerPanel

from cls.types.beamline import BEAMLINE_IDS
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ

import suitcase.nxstxm as suit_nxstxm
import suitcase.nxptycho as suit_nxptycho

#from bcm.devices.device_names import *
from bcm.devices.device_names import *


# from event_model import RunRouter
# from suitcase.nxstxm import Serializer
#
# def factory(name, start_doc):
#
#     serializer = Serializer(data_dir)
#     serializer('start', start_doc)
#
#     return [serializer], []
#
#
# #connect outr data
# rr = RunRouter([factory])
# RE.subscribe(rr)

# read the ini file and load the default directories
appConfig = ConfigClass(abs_path_to_ini_file)
scanPluginDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'scan_plugins')
uiDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'ui')
prefsDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'preferences')
docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','docs','_build','html','index.html')

sample_pos_mode = MAIN_OBJ.get_sample_positioning_mode()
sample_finepos_mode = MAIN_OBJ.get_fine_sample_positioning_mode()

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

active_user = None

PLOTTER_IMAGES_TAB = 0
PLOTTER_SPECTRA_TAB = 1

NUM_POINTS_LOST_AFTER_EDIFF = 2
DATA_OFFSET = 1

hostname = os.getenv('COMPUTERNAME')
if (hostname == 'WKS-W001465'):
    # the new test computer in old magnet mapping room
    FAKE_MARKER = False
    UNIT_SCALAR = 0.001
    # VELO_SCALAR = 1
    # VELO_SCALAR = 0.001
    VELO_SCALAR = 1000.0
    USE_PIEZO = True
elif (hostname == 'NBK-W001021'):
    # my notebook computer
    FAKE_MARKER = True
    UNIT_SCALAR = 1.0
    USE_PIEZO = False
else:
    # the old stxm_control conmputer
    FAKE_MARKER = False
    UNIT_SCALAR = 0.001
    VELO_SCALAR = 0.001
    USE_PIEZO = True

class EngineLabel(QtWidgets.QLabel):
    """
    QLabel to display the RunEngine Status
    Attributes
    ----------
    color_map : dict
        Mapping of Engine states to color displays
    """
    changed = QtCore.pyqtSignal(object, str)

    # color_map = {name: (font color, background color)
    # color_map = {'running': (master_colors['white'], master_colors['scan_sts_blue'], master_colors['app_ltblue'], master_colors['app_drkblue']),
    #              'paused': (master_colors['black'], master_colors['app_yellow'], master_colors['app_ltblue'], master_colors['app_blue']),
    #              'idle': (master_colors['white'], master_colors['app_drkgray'], master_colors['app_ltblue'], master_colors['app_blue'])}
    color_map = {'running': (master_colors['black'], master_colors['app_ltblue'], master_colors['fbk_moving_ylw'], master_colors['app_red']),
                 'paused': (master_colors['black'], master_colors['app_yellow'], master_colors['app_ltblue'],
                            master_colors['app_blue']),
                 'idle': (master_colors['white'], master_colors['app_drkgray'], master_colors['app_ltblue'],
                          master_colors['app_blue'])}

    def __init__(self, txt):
        super(EngineLabel, self).__init__(txt)
        self._blink_timer = QtCore.QTimer()
        self._blink_timer.timeout.connect(self.on_timeout)
        self._tmr_en = False
        self._blink_timer.start(500)
        self._cur_color = None
        self._state_str = None

    def on_timeout(self):
        if(self._tmr_en):
            if(self.isEnabled()):
                self.setEnabled(False)
            else:
                self.setEnabled(True)
        else:
            if(not self.isEnabled()):
                self.setEnabled(True)
        self._set_colors()

    @QtCore.pyqtSlot('QString', 'QString')
    def on_state_change(self, state, old_state):
        self._state_str = state.capitalize()
        # Update the label
        if(state.find('running') > -1):
            self._tmr_en = True
        else:
            self._tmr_en = False

        self.setText(self._state_str)
        # Update the font and background color
        self._cur_color = self.color_map[state]
        # ss = 'QLabel {color: %s; background-color: %s}' % (self._cur_color[0], self._cur_color[1])
        # self.changed.emit(state.capitalize(), ss)
        #self._set_colors()

    def _set_colors(self):
        if(self._tmr_en):
            if (self.isEnabled()):
                clr1, clr2, clr3, cl4 = self._cur_color
            else:
                clr1, clr3, clr2, clr4 = self._cur_color
        else:
            clr1, clr2, clr3, cl4 = self._cur_color

        ss = 'QLabel {color: %s; background-color: %s}' % (clr1, clr2)
        self.changed.emit(self._state_str, ss)

    def connect(self, engine):
        """Connect an existing QRunEngine"""
        engine.state_changed.connect(self.on_state_change)
        self.on_state_change(engine.state, None)

##############################################################################################################
##############################################################################################################
class pySTXMWindow(QtWidgets.QMainWindow):
    '''
    classdocs
    '''
    _set_scan_btns = QtCore.pyqtSignal(object)

    # _check_for_another_scan = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, exec_in_debugger=False, log=None):
        """
        __init__(): description

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        super(pySTXMWindow, self).__init__(parent)
        uic.loadUi(os.path.join(os.getcwd(), 'ui', 'pyStxm.ui'), self)
        atexit.register(self.on_exit)

        # connect logger
        #self.log = log_to_qt()
        # logdir = os.path.dirname(os.path.abspath(__file__))
        # logfile = os.path.join(logdir, 'logs', time.strftime("%Y%m%d-%H%M%S") + '.log')
        # self.log = log_to_qt_and_to_file(logfile, level=logging.DEBUG)
        if(log is None):
            logdir = os.path.dirname(os.path.abspath(__file__))
            logfile = os.path.join(logdir, 'logs', time.strftime("%Y%m%d-%H%M%S") + '.log')
            log = log_to_qt_and_to_file(logfile, level=logging.DEBUG)

        self.log = log
        self.log.new_msg.connect(self.add_to_log)
        # self.log = log_to_console()
        self.splash = get_splash()
        self.exec_in_debugger = exec_in_debugger

        _logger.info('####################### Starting pystxm ####################### ')
        # self.setWindowTitle('pyStxm %s.%s Canadian Light Source Inc. ' % (major_version, minor_version))
        #self.setWindowTitle('pyStxm %s.%s Canadian Light Source Inc. %s [%s]' % (
        #MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'), MAIN_OBJ.get('APP.DATE'), os.path.dirname(os.path.abspath(__file__))))
        self.setWindowTitle('pyStxm %s.%s Canadian Light Source Inc. [%s] [%s] [%s]' % (
            MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'), os.path.dirname(os.path.abspath(__file__)), MAIN_OBJ.get('APP.COMMIT'), MAIN_OBJ.get('APP.DATE')))

        self.setGeometry(10, 100, 2000, 1300)
        self.qssheet = get_style('dark')
        # self.setStyleSheet(self.qssheet)
        # self.apply_stylesheet(self.centralwidget, self.qssheet)

        auto_login = True
        self.loginWdgt = loginWidget(usr_acct_manager, auto_login=auto_login, parent=self)
        if (auto_login):
            self.active_user = self.loginWdgt.get_user_obj()
            _logger.info('%s succesful logged in' % self.active_user.get_username())
            _logger.info('Active user data dir : %s' % self.active_user.get_data_dir())

        MAIN_OBJ.set('APP.USER', self.active_user)
        # self.scanTypeToolBox.currentChanged.connect(self.on_toolbox_changed)

        self._set_scan_btns.connect(self.on_set_scan_btns)
        # self._check_for_another_scan.connect(self.check_for_more_ev_regions)
        self.single_energy = True

        self.data = []
        self.rvrsddata = []
        self.shorcuts = self._define_global_shortcuts()
        self.scan_tbox_widgets = []
        self.scan_pluggin = None

        self._pref_panels = {}

        self.scan_in_progress = False
        self.image_started = False

        self.ring_ma = MAIN_OBJ.device(DNM_RING_CURRENT).get_ophyd_device()
        self.point_det = MAIN_OBJ.device(DNM_POINT_DET)
        self.line_det = MAIN_OBJ.device(DNM_LINE_DET)
        self.line_det_flyer = MAIN_OBJ.device(DNM_LINE_DET_FLYER)
        self.gate = MAIN_OBJ.device(DNM_POINT_GATE)

        # self.vidTimer = QtCore.QTimer()
        # self.vidTimer.timeout.connect(self.on_video_timer)

        self.setup_main_gui()
        self.setup_image_plot()
        self.setup_spectra_plot()



        #beam spot feedback dispatcher
        #self.bmspot_fbk_obj = BeamSpotFeedbackObj(MAIN_OBJ)
        #self.bmspot_fbk_obj.new_beam_pos.connect(self.on_new_beamspot_fbk)
        _cam_en = MAIN_OBJ.get_preset_as_bool('enabled', 'CAMERA')
        if(_cam_en):
            if (int(_cam_en) == 1):
                self.setup_calib_camera()

        if(LOAD_ALL):
            self.setup_video_panel()

        if(LOAD_ALL):
            self.setup_preferences_panel()

        self.shutterFbkLbl = ophyd_biLabelWidget(MAIN_OBJ.device(DNM_SHUTTER), labelWidget=self.shutterFbkLbl,
                                              hdrText=DNM_SHUTTER, title_color='white',
                                              options=dict(state_clrs=['black', 'blue']))
        self.status_dict = {}

        if (LOAD_ALL):
            self.splash.show_msg('Initializing status bar')
            self.init_statusbar()

        self.scan = None
        self.dwell = 0

        # a variable to hold the list of ev_rois for current scan
        self.ev_rois = None
        self.cur_ev_idx = 0
        self.cur_sp_rois = {}
        # self.e_roi_queue = Queue.Queue()

        self.ySetpoints = None
        self.xSetpoints = None
        self.npointsX = 0
        self.npointsY = 0

        self.accRange = 0
        self.dccRange = 0
        self.executingScan = None

        self.stopping = False

        self.init_all_scans()
        self.previousScanType = None

        self._threadpool = QtCore.QThreadPool()

        self.splash.show_msg('Loading scan plugins')
        self.setup_scan_toolbox()
        self.scan_panel_idx = self.scanTypeToolBox.currentIndex()
        self.scan_tbox_widgets[self.scan_panel_idx].set_zp_focus_mode()
        self._scan_type = self.scan_tbox_widgets[self.scan_panel_idx].type
        self._scan_sub_type = self.scan_tbox_widgets[self.scan_panel_idx].sub_type
        self.on_update_style()

        self.set_style_timer = QtCore.QTimer(self)
        self.set_style_timer.timeout.connect(self.on_update_style)
        self.set_style_timer.setSingleShot(True)
        self.set_style_timer.start(100)

        # if(not self.exec_in_debugger):
        #     # pass on this for now, this causes the exiting of the app to hang waiting for something, not sure why
        #     self.setup_info_dock()
        #     #pass


        self.set_buttons_for_starting()
        #self.loadImageDataBtn.clicked.connect(self.load_simulated_image_data)
        # except:
        #    traceback.print_exc()

        # self.enable_fbk_timer = QtCore.QTimer()
        # self.enable_fbk_timer.timeout.connect(self.allow_feedback)
        # self.enable_fbk_timer.setSingleShot(True)
        # self.enable_fbk_timer.start(5000)
        self.splash.show_msg('initialization done')
        self.enable_energy_change(True)

        MAIN_OBJ.engine_widget.engine.exec_result.connect(self.on_execution_completed)
        MAIN_OBJ.engine_widget.engine.prog_changed.connect(self.on_run_engine_progress)
        #MAIN_OBJ.engine_subscribe(self.bsImagePlotWidget.doc_callback)
        self.status_label = EngineLabel('Engine Status')
        self.status_label.changed.connect(self.on_status_changed)
        self.status_label.connect(MAIN_OBJ.engine_widget.engine)

    def setup_preferences_panel(self):
        '''
        walk a directory where the preferences are kept and load the combobox and stacked widget
        :return:
        '''

        self._pref_panels = {}
        #import importlib
        import imp
        from cls.utils.dirlist import dirlist
        _dirs = os.listdir(prefsDir)

        idx = 0
        for dir in _dirs:
            if(dir.find('.py') < 0):
                #get files in pref dir
                _files = os.listdir(os.path.join(prefsDir, dir))
                if('loader.py' in _files):
                    _filepath = os.path.join(prefsDir, dir, 'loader.py')
                    if(os.path.exists(_filepath)):
                        #_mod = importlib.load_source('mod_classname', _filepath)
                        _mod = SourceFileLoader('mod_classname', _filepath).load_module()
                        _mod_filepath = os.path.join(prefsDir, dir, _mod.mod_file)
                        #_cls = importlib.load_source(_mod.mod_classname, _mod_filepath)
                        _cls = SourceFileLoader('mod_classname', _mod_filepath).load_module()
                        #create an instance of the class
                        _inst = eval('_cls.%s()' % _mod.mod_classname)
                        wdg = QtWidgets.QWidget()
                        _lyt = QtWidgets.QVBoxLayout()
                        _lyt.addWidget(_inst)
                        wdg.setLayout(_lyt)
                        self.apply_stylesheet(wdg, self.qssheet)
                        self.prefsStackedWidget.insertWidget(idx, wdg)
                        self.splash.show_msg('Loading %s preferences widget' % _mod.mod_file)

                        self.prefsComboBox.addItem(_mod.mod_hdr_name, idx)
                        self.prefsComboBox.currentIndexChanged.connect(self.on_preference_changed)

                        self._pref_panels[_cls.mod_classname] = _inst
                        idx += 1

    def get_pref_panel(self, pref_nm):
        if(pref_nm in self._pref_panels.keys()):
            return(self._pref_panels[pref_nm])
        else:
            _logger.error('Pref panel [%s] does not exist' % pref_nm)

    def on_preference_changed(self, idx):
        self.prefsStackedWidget.setCurrentIndex(idx)

    def on_new_beamspot_fbk(self, cx, cy):
        '''
        the beam spot object has emitted a new center x/y so let the plotter know
        :param cx:
        :param cy:
        :return:
        '''

        #todo:: need to skip this if the tool is not visible
        #print('on_new_beamspot_fbk: (%.2f, %.2f)' % (cx, cy))
        #self.lineByLineImageDataWidget.move_beam_spot(cx, cy)
        pass

    def set_zp_focus_mode(self, mode=None):
        """
        this function sets the mode that controls how the positions for Zpz and Cz are calculated.
        this function is called when the user switches to a new scan in the scans toolbox
        """
        if(MAIN_OBJ.get_beamline_id() is BEAMLINE_IDS.STXM):
            zpz_scanflag = MAIN_OBJ.device(DNM_ZONEPLATE_SCAN_MODE)
            zpz_scanflag.put('user_setpoint', mode)


    def allow_feedback(self):
        if (hasattr(self, 'esPosPanel')):
            self.esPosPanel.enable_feedback()
        if (hasattr(self, 'blPosPanel')):
            self.blPosPanel.enable_feedback()

    def load_simulated_image_data(self):
        global SIMULATE_IMAGE_DATA, SIM_DATA

        SIMULATE_IMAGE_DATA = True
        SIM_DATA = self.lineByLineImageDataWidget.get_current_data()
        _logger.info('Loaded Simulated data')

    def start_epics_tasks(self):
        """
        start_epics_tasks(): description

        :returns: None
        """
        MAIN_OBJ.device('ShutterTaskRun').put(1)

    def on_update_style(self):
        """
        on_update_style(): description

        :returns: None
        """
        """ handler for interactive button """
        # self.set_style_timer.stop()
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)
        self.apply_stylesheet(self.centralwidget, self.qssheet)
        self.update_plot_colors()
        self.allow_feedback()

    def update_plot_colors(self):
        """
        update_plot_colors(): description

        :returns: None
        """
        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

        if (hasattr(self, 'stripToolPlot')):
            self.stripToolPlot.set_grid_parameters(bg_clr, min_clr, maj_clr)

        if (hasattr(self, 'lineByLineImageDataWidget')):
            self.lineByLineImageDataWidget.set_grid_parameters(bg_clr, min_clr, maj_clr)
            self.lineByLineImageDataWidget.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)

        if (hasattr(self, 'spectraWidget')):
            self.spectraWidget.set_grid_parameters(bg_clr, min_clr, maj_clr)

    def apply_stylesheet(self, widget, ssheet):
        """
        apply_stylesheet(): description

        :param widget: widget description
        :type widget: widget type

        :param ssheet: ssheet description
        :type ssheet: ssheet type

        :returns: None
        """
        # for some reason the stysheet isnt picked up by the central widget and centralFrame so force it here
        widget.setStyleSheet(ssheet)

    def add_to_log(self, clr, msg):
        """
        add_to_log(): description

        :param clr: clr description
        :type clr: clr type

        :param msg: msg description
        :type msg: msg type

        :returns: None
        """
        """
            This is a signal handler that is connected to the logger so that
            messages sent to the logger are  then displayed by this apps loggin
            widget, color is supported for the varying levels of message logged
        """
        if (clr is not None):
            self.logWindow.setTextColor(clr)
        self.logWindow.append(msg)

    def load_dir_view(self):
        """
        load_dir_view(): description

        :returns: None
        """
        self.dir_model = QtWidgets.QFileSystemModel()
        self.dir_model.setRootPath(QtCore.QDir.currentPath())

        # self.dir_model.setRootPath( QtCore.QString(MAIN_OBJ.get_session_info().get_data_dir()) )
        self.dirTreeView.setModel(self.dir_model)
        self.dirTreeView.clicked.connect(self.on_treeView_clicked)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_treeView_clicked(self, index):
        """
        on_treeView_clicked(): description

        :param index: index description
        :type index: index type

        :returns: None
        """
        indexItem = self.dir_model.index(index.row(), 0, index.parent())
        fileName = self.dir_model.fileName(indexItem)
        filePath = self.dir_model.filePath(indexItem)
        print('selected [%s]' % (filePath))

    def on_set_scan_btns(self, do_what):
        """
        on_set_scan_btns(): description

        :param do_what: do_what description
        :type do_what: do_what type

        :returns: None
        """
        if (do_what == 'SET_FOR_SCANNING'):
            self.set_buttons_for_scanning()
        elif (do_what == 'SET_FOR_STARTING'):
            self.set_buttons_for_starting()
        else:
            pass

    def set_buttons_for_scanning(self):
        """
        set_buttons_for_scanning(): description

        :returns: None
        """

        self.scan_in_progress = True
        self.startBtn.setEnabled(False)
        # self.stopBtn.setEnabled(True)
        self.pauseBtn.setEnabled(True)
        self.scansFrame.setEnabled(False)

        #self.contact_sheet.set_drag_enabled(False)

        if (hasattr(self, 'lineByLineImageDataWidget')):
            # self.scan_tbox_widgets[self.scan_panel_idx].set_read_only()
            self.lineByLineImageDataWidget.set_enable_drop_events(False)
            # do not allow user to delete currently acquiring image
            self.lineByLineImageDataWidget.enable_menu_action('Clear Plot', False)


    def set_buttons_for_starting(self):
        """
        set_buttons_for_starting(): description

        :returns: None
        """

        self.scan_in_progress = False
        self.startBtn.setEnabled(True)
        # self.stopBtn.setEnabled(False)
        self.pauseBtn.setEnabled(False)
        self.pauseBtn.setChecked(False)
        self.scansFrame.setEnabled(True)
        # self.scan_tbox_widgets[self.scan_panel_idx].set_editable()
        if (hasattr(self, 'contact_sheet')):
            self.contact_sheet.set_drag_enabled(True)
        if (hasattr(self, 'lineByLineImageDataWidget')):
            self.lineByLineImageDataWidget.set_enable_drop_events(True)
            # allow user to delete currently acquiring and any other images
            self.lineByLineImageDataWidget.enable_menu_action('Clear Plot', True)



    def init_all_scans(self):
        """
        init_all_scans(): description

        """
        # ensure a connection to dcs values so that the forst data collection goes smooth
        _logger.debug('intializing DCS connections')
        devices = MAIN_OBJ.get_devices()
        d = MAIN_OBJ.take_positioner_snapshot(devices['POSITIONERS'])
        d = MAIN_OBJ.take_detectors_snapshot(devices['DETECTORS'])
        d = MAIN_OBJ.take_pvs_snapshot(devices['PVS'])
        _logger.debug('intializing DCS connections: Done')

        # self.imageSCAN.stop()
        # self.pointSCAN.stop()
        # self.focusSCAN.stop()

    def closeEvent(self, event):
        """
        closeEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        result = QtWidgets.QMessageBox.question(self,
                                                "Confirm Exit...",
                                                "Are you sure you want to exit ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            self.enable_energy_change(False)
            event.accept()

    def enable_energy_change(self, en):
        devices = MAIN_OBJ.get_devices()
        #ev_en = devices['PVS'][DNM_ENERGY_ENABLE]
        ev_en = MAIN_OBJ.device(DNM_ENERGY_ENABLE)
        zpz = MAIN_OBJ.device(DNM_ZONEPLATE_Z_BASE)

        if(en):
            ev_en.put(1)
            # enable Zoneplate Z servo
            zpz.put('use_torque', 1)
            zpz.put('disabled', 0) # GO
        else:
            # park energy change enabled
            ev_en.put(0)
            #disable Zoneplate Z servo
            zpz.put('use_torque', 0)
            zpz.put('disabled', 1)  # STOP



    # def on_edit_zp_params(self):
    #     """
    #     on_edit_zp_params(): description
    #
    #     :returns: None
    #     """
    #
    #     #self.fpForm.show()
    #     self.fpForm = FocusParams(self)
    #     self.apply_stylesheet(self.fpForm, self.qssheet)
    #     self.fpForm.show()

    def on_about_pystxm(self):
        self.aboutForm =  uic.loadUi(os.path.join(uiDir, 'pyStxm_about.ui'))
        self.aboutForm.okBtn.clicked.connect(self.aboutForm.close)
        ver_str = 'version %s.%s %s' % ( MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'), MAIN_OBJ.get('APP.DATE'))
        self.aboutForm.versionLbl.setText(ver_str)
        #self.apply_stylesheet(self.aboutForm, self.qssheet)
        self.apply_stylesheet(self.aboutForm, 'QDialog{ background-color: %s ;}' % master_colors["master_background_color"])
        self.aboutForm.show()

    def on_pystxm_help(self):
        webbrowser.open(docs_path)

    def on_switch_user(self):
        pass

    def _define_global_shortcuts(self):

        shortcuts = []

        # sequence = {
        #     'Ctrl+Shift+Left': self.on_action_previous_comic_triggered,
        #     'Ctrl+Left': self.on_action_first_page_triggered,
        #     'Left': self.on_action_previous_page_triggered,
        #     'Right': self.on_action_next_page_triggered,
        #     'Ctrl+Right': self.on_action_last_page_triggered,
        #     'Ctrl+Shift+Right': self.on_action_next_comic_triggered,
        #     'Ctrl+R': self.on_action_rotate_left_triggered,
        #     'Ctrl+Shift+R': self.on_action_rotate_right_triggered,
        # }

        sequence = {
            'Ctrl+U': self.on_update_style,
        }

        for key, value in list(sequence.items()):
            s = QtWidgets.QShortcut(QtGui.QKeySequence(key),
                                    self, value)
            s.setEnabled(True)
            shortcuts.append(s)

        return shortcuts

    def setup_main_gui(self):
        """
        setup_main_gui(): description

        :returns: None
        """
        self.mainTabWidget.currentChanged.connect(self.on_main_tab_changed)
        self.mainTabWidget.tabBarClicked.connect(self.on_main_tab_changed)
        # self.statusBar = QtWidgets.QStatusBar()
        # self.layout().addWidget(self.statusBar)
        self.setMinimumSize(1000, 1000)
        self.setMaximumSize(2000, 2000)

        self.actionExit.triggered.connect(self.close)
        #self.actionZP_Params.triggered.connect(self.on_edit_zp_params)
        self.actionAbout_pyStxm.triggered.connect(self.on_about_pystxm)
        self.actionpyStxm_help.triggered.connect(self.on_pystxm_help)
        self.actionSwitch_User.triggered.connect(self.on_switch_user)

        self.startBtn.clicked.connect(self.on_start_scan)
        self.pauseBtn.clicked.connect(self.on_pause)
        self.stopBtn.clicked.connect(self.on_stop)

        # remember that the striptToolWidget uses the pv specified in counters.ini
        self.stripToolPlot = StripToolWidget(1, sigList=[MAIN_OBJ.device(DNM_PMT)], parent=self)

        self.enable_detfbk = False
        self.enable_osafbk = False

        if (LOAD_ALL):
            # self.sample_selector = SampleSelectorWidget(scaler=0.80, parent=self)
            #
            # hbox = QtWidgets.QHBoxLayout()
            # hbox.addWidget(self.sample_selector)
            # hbox.setContentsMargins(0, 0, 0, 0)
            # hbox.addStretch()
            # self.sampleSelFrame.setLayout(hbox)

            if (hasattr(self, 'stripToolPlot')):
                vbox2 = QtWidgets.QVBoxLayout()
                vbox2.addWidget(self.stripToolPlot)
                vbox2.setContentsMargins(1, 1, 1, 1)
                self.counterPlotFrame.setLayout(vbox2)

            # endstation positioners panel
            dev_obj = MAIN_OBJ.get_device_obj()
            exclude_list = dev_obj.get_exclude_positioners_list()
            self.esPosPanel = PositionersPanel(POS_TYPE_ES, exclude_list, main_obj=MAIN_OBJ, parent=self)
            self.esPosPanel.setObjectName('esPosPanel')
            # spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox3 = QtWidgets.QVBoxLayout()
            vbox3.addWidget(self.esPosPanel)
            vbox3.addItem(spacer)

            #horizontal line
            hline = QtWidgets.QFrame()
            hline.setFrameShape(QtWidgets.QFrame.HLine)
            hline.setFrameShadow(QtWidgets.QFrame.Sunken)
            #add the line twice
            self.esPosPanel.append_widget_to_positioner_layout(hline)
            self.esPosPanel.append_widget_to_positioner_layout(hline)

            #add Zpz change on energy button
            ev_en_dev = dev_obj.device('Energy_enable')
            if(ev_en_dev):
                self.esPosPanel.append_toggle_btn_device('  FL change with Energy  ',
                                                   'Enable the Focal Length (FL==Zpz stage) to move to new focal length based on Energy',
                                                   ev_en_dev, off_val=0, on_val=1, fbk_dev=ev_en_dev,
                                                   off_str='Disabled', on_str='Enabled')

            #add the beam defocus device
            defoc_dev = dev_obj.device(DNM_BEAM_DEFOCUS)
            if(defoc_dev):
                _min = 0.0
                _max = 5000
                self.esPosPanel.append_setpoint_device('  Defocus spot size by  ',
                                                   'Defocus the beam as a function of beamspot size (um)', 'um',
                                                   defoc_dev, _min, _max)

            # add the OSA vertical tracking device
            osay_track_dev = dev_obj.device(DNM_OSAY_TRACKING)
            if(osay_track_dev):
                self.esPosPanel.append_toggle_btn_device('  OSA vertical tracking  ',
                                                   'Toggle the OSA vertical tracking during zoneplate scanning',
                                                     osay_track_dev, off_val=0, on_val=1, fbk_dev=osay_track_dev,
                                                     off_str='Off', on_str='On')

            # add the Focusing Mode
            foc_mode_dev = dev_obj.device(DNM_ZONEPLATE_SCAN_MODE)
            if(foc_mode_dev):
                self.esPosPanel.append_toggle_btn_device('  Focal length mode  ',
                                                     'Toggle the focal length mode from Sample to OSA focused',
                                                     foc_mode_dev, off_val=1, on_val=0,
                                                     off_str='Sample Focused', on_str='OSA Focused',toggle=True )
            #add zonplate in/out

            zp_inout_dev = dev_obj.device(DNM_ZONEPLATE_INOUT)
            if(zp_inout_dev):
                zp_inout_dev_fbk = dev_obj.device(DNM_ZONEPLATE_INOUT_FBK)
                self.esPosPanel.append_toggle_btn_device(' Zoneplate In/Out',
                                'Move the zonplate Z stage all the way upstream out of the way',
                                zp_inout_dev, off_val=0, on_val=1,
                                off_str='Out', on_str='In', fbk_dev=zp_inout_dev_fbk, toggle=False)

            self.endstationPositionersFrame.setLayout(vbox3)

            # #beamline positioners panel
            self.blPosPanel = PositionersPanel(POS_TYPE_BL, main_obj=MAIN_OBJ, parent=self)
            self.blPosPanel.setObjectName('blPosPanel')
            #spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox4 = QtWidgets.QVBoxLayout()
            vbox4.addWidget(self.blPosPanel)
            vbox4.addItem(spacer)
            self.beamlinePositionersFrame.setLayout(vbox4)

            # temperatures panel
            dev_obj = MAIN_OBJ.get_device_obj()
            temps = dev_obj.get_all_temperatures(POS_TYPE_ES)
            self.esTempPanel = DevsPanel(temps, egu='deg C', parent=None)
            self.esTempPanel.setObjectName('esTempPanel')
            # self.esTempPanel = TemperaturesPanel(POS_TYPE_ES)
            #spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox5 = QtWidgets.QVBoxLayout()
            vbox5.addWidget(self.esTempPanel)
            vbox5.addItem(spacer)
            self.esTempsFrame.setLayout(vbox5)
            #
            # ES pressures panel
            dev_obj = MAIN_OBJ.get_device_obj()
            presrs = dev_obj.get_all_pressures(POS_TYPE_ES)

            self.esPressPanel = DevsPanel(presrs, egu='Torr', engineering_notation=True, parent=None)
            self.esPressPanel.setObjectName('esPressPanel')
            # self.esTempPanel = TemperaturesPanel(POS_TYPE_ES)
            #spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox6 = QtWidgets.QVBoxLayout()
            vbox6.addWidget(self.esPressPanel)
            vbox6.addItem(spacer)
            self.esPressuresFrame.setLayout(vbox6)

            # BL pressures panel
            bl_presrs = dev_obj.get_all_pressures(POS_TYPE_BL)
            bl_presrs = self.sort_by_desc(bl_presrs)
            self.blPressPanel = DevsPanel(bl_presrs, egu='Torr', engineering_notation=True, parent=None)
            self.blPressPanel.setObjectName('blPressPanel')
            spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox7 = QtWidgets.QVBoxLayout()
            vbox7.addWidget(self.blPressPanel)
            vbox7.addItem(spacer)
            self.blPressuresFrame.setLayout(vbox7)

            # tools panel
            #             self.toolsPanel = ToolsPanel()
            #             spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            #             vbox4 = QtWidgets.QVBoxLayout()
            #             vbox4.addWidget(self.toolsPanel)
            #             vbox4.addItem(spacer)
            #             self.toolsPositionersFrame.setLayout(vbox4)

            # self.detectorsPanel = DetectorsPanel(self)
            # spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            # vbox5 = QtWidgets.QVBoxLayout()
            # vbox5.addWidget(self.detectorsPanel)
            # vbox5.addItem(spacer)
            # self.detectorsFrame.setLayout(vbox5)

        #self.load_dir_view()
        self.pythonshell = None

        self.shutterCntrlComboBox.currentIndexChanged.connect(self.on_shutterCntrlComboBox)
        idx = self.shutterCntrlComboBox.currentIndex()
        self.on_shutterCntrlComboBox(0)  # Auto

        self.scan_progress_table = ScanQueueTableWidget(parent=self)
        self.scanQFrame.layout().addWidget(self.scan_progress_table)

        #initialize the thumbnail viewer
        self.init_images_frame()

        self.init_ccd_viewer_frame()

        #load the app status panel
        self.setup_ioc_software_status()

        #load the sscan status panel
        #self.setup_sscan_status()

        #self.check_if_pv_exists()

    def check_if_pv_exists(self):
        dev_obj = MAIN_OBJ.get_device_obj()
        psner_dct = dev_obj.devices['POSITIONERS']
        posner_names = list(psner_dct.keys())

        print('checking for existance of pvs:')
        from epics import caget, caput, cainfo
        for k in posner_names:
            pv = psner_dct[k]
            pv_name = pv.get_name()
            print('checking [%s]: <%s>' % (pv_name, cainfo(pv_name)))

    def sort_by_desc(self, devs):
        '''
        sort the device dictionary by description and return the devices as a list sorted by description
        :param devs:
        :return:
        '''
        from cls.utils.dict_utils import sort_str_list
        desc_lst = []
        dev_dct = {}
        sorted_dev_lst = []
        for d_k in list(devs.keys()):
            desc = devs[d_k].get_desc()
            desc_lst.append(desc)
            dev_dct[desc] = devs[d_k]

        sorted_desc_lst = sort_str_list(desc_lst)

        for s_d in sorted_desc_lst:
            sorted_dev_lst.append(dev_dct[s_d])
        return(sorted_dev_lst)


    def on_main_tab_changed(self, tab_idx):
        pass


    def setup_ioc_software_status(self):
        '''
        add a list of IOC application heart beat pv's to the 'Status' tab of the main application. The status
        of each heart beat will update based on wether the app is running or not
        :return:
        '''
        ioc_apps_wdg = IOCAppsPanel(MAIN_OBJ)
        ioc_apps_wdg.setProperty('alertField', True)
        ioc_apps_wdg.alert.connect(self.on_panel_alert)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(ioc_apps_wdg)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        vlayout.addItem(spacer)

        self.IOCSwStatusGrpBx.setLayout(vlayout)
        #tb = self.mainTabWidget.tabBar()
        #tb.paintEvent = self.ioc_apps_paintEvent


    def on_panel_alert(self, alert_dct):
        from cls.appWidgets.base_content_panel import alert_lvls
        change_it = False
        alert_lvl = alert_dct['lvl']
        tab_idx = alert_dct['tab_idx']
        obj_name = alert_dct['obj_name']

        if(alert_lvl == alert_lvls.NORMAL):
            #no change
            pass
        elif(alert_lvl == alert_lvls.WARNING):
            bg_clr = 'rgb(255,255,0);'
            change_it = True
        elif (alert_lvl == alert_lvls.ERROR):
            bg_clr = 'rgb(255,0,0);'
            change_it = True
        else:
            _logger.error('alert level is out of range')
            bg_clr = 'rgb(0,0,255);'
            change_it = True

        # if(change_it):
        #     #self.mainTabWidget.tabBar().setStyleSheet("QTabBar::tab:selected { color: #00ff00; background-color: %s}" % bg_clr)
        #     #self.mainTabWidget.tabBar().setStyleSheet("QTabBar::tab:selected { background-color: %s}" % bg_clr)
        #     self.mainTabWidget.tabBar().setStyleSheet("QTabBar::tab[currentIndex = 2] { background-color: %s}" % (bg_clr))


    def ioc_apps_paintEvent(self, event):
        p = QtWidgets.QStylePainter(self)
        painter = QtGui.QPainter(self)
        painter.save()
        for index in range(self.count()):  # for all tabs

            tabRect = self.tabRect(index)
            tabRect.adjust(-1, 3, -1, -1)  # ajust size of every tab (make it smaller)
            if index == 0:  # make first tab red
                color = QtGui.QColor(255, 0, 0)
            elif index == 1:  # make second tab yellow
                color = QtGui.QColor(255, 255, 0)
            else:  # make all other tabs blue
                color = QtGui.QColor(0, 0, 255)
            if index == self.currentIndex():  # if it's the selected tab
                color = color.lighter(130)  # highlight the selected tab with a 30% lighter color
                tabRect.adjust(0, -3, 0, 1)  # increase height of selected tab and remove bottom border
            brush = QtGui.QBrush(color)
            painter.fillRect(tabRect, brush)

            painter.setPen(QtGui.QPen(QtGui.QColor(QtCore.Qt.black)))  # black pen (for drawing the text)
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                                 self.tabText(index))

            painter.setPen(QtGui.QPen(QtGui.QColor(QtCore.Qt.gray)))  # gray pen (for drawing the border)
            painter.drawRect(tabRect)
        painter.restore()

    def setup_sscan_status(self):
        '''
        A widget that connects to SMSG, CPT and FAZE of all 8 sscan records in order to show their values during a scan
        :return:
        '''
        vlayout = QtWidgets.QVBoxLayout()
        devs = MAIN_OBJ.get_devices()
        sscan_status = SScanStatusWidget(devs['SSCANS'])
        vlayout.addWidget(sscan_status)

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        vlayout.addItem(spacer)

        self.sscanStatusFrame.setLayout(vlayout)

    def init_images_frame(self):
        self.contact_sheet = ContactSheet(self.active_user.get_data_dir(), STXMDataIo, parent=self)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.contact_sheet)
        self.imagesFrame.setLayout(vbox)

    def init_ccd_viewer_frame(self):
        ccd_dev = MAIN_OBJ.device(DNM_GREATEYES_CCD, do_warn=False)
        if(ccd_dev):
            self.ccd_w = CCDViewerPanel(MAIN_OBJ.device(DNM_GREATEYES_CCD), parent=self)

            vbox = QtWidgets.QVBoxLayout()
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(self.ccd_w)
            self.ccdFrame.setLayout(vbox)
        else:
            _logger.info('Great Eyes CCD not detected so not loading CCD viewer panel')



    def on_shutterCntrlComboBox(self, idx):
        """
        on_shutterCntrlComboBox(): description

        :param idx: idx description
        :type idx: idx type

        :returns: None
        """
        """ in order 
        0 = Auto
        1 = Open
        2 = Close
        """
        # idx = self.shutterCntrlComboBox.currentIndex()
        if (idx == 0):
            # print 'setting shutter mode to AUTO'
            MAIN_OBJ.device(DNM_SHUTTER).close()
            MAIN_OBJ.device(DNM_SHUTTER).set_to_auto()

        elif (idx == 1):
            # print 'setting shutter mode to MANUAL'
            MAIN_OBJ.device(DNM_SHUTTER).set_to_manual()
            MAIN_OBJ.device(DNM_SHUTTER).open()
        else:
            # print 'setting shutter mode to MANUAL'
            MAIN_OBJ.device(DNM_SHUTTER).set_to_manual()
            MAIN_OBJ.device(DNM_SHUTTER).close()

    def setup_scan_toolbox(self):

        '''
        walk a directory where the preferences are kept and load the combobox and stacked widget
        :return:
        '''

        # Create plugin manager
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scanTypeToolBox = QtWidgets.QToolBox()
        self.scanTypeToolBox.layout().setContentsMargins(0, 0, 0, 0)
        self.scanTypeToolBox.layout().setSpacing(0)

        #get the beamline config directory from teh presets loaded at startup
        plugin_dir = MAIN_OBJ.get_preset('bl_config_dir', 'MAIN')
        _dirs = os.listdir(plugin_dir)

        idx = 0
        pages = 0
        num_scans = 0
        scans = {}
        # walk the subdirs of the beamline config directory looking for scan plugins
        for dir in _dirs:
            if(os.path.isdir(os.path.join(plugin_dir, dir))):
                # get files in dir
                _files = os.listdir(os.path.join(plugin_dir, dir))
                if ('loader.py' in _files):
                    _filepath = os.path.join(plugin_dir, dir, 'loader.py')
                    if (os.path.exists(_filepath)):
                        _mod = SourceFileLoader('mod_classname', _filepath).load_module()
                        _mod_filepath = os.path.join(plugin_dir, dir, _mod.mod_file)
                        _cls = SourceFileLoader('mod_classname', _mod_filepath).load_module()
                        # create an instance of the class
                        plugin = eval('_cls.%s()' % _mod.mod_classname)
                        _logger.debug("Found SCAN plugin [%s]" % plugin.name)
                        print("Found SCAN plugin [%d][%s]" % (plugin.idx, plugin.name))
                        self.splash.show_msg(
                            "Found SCAN plugin [%d][%s]" % (plugin.idx, plugin.name))
                        scans[plugin.idx] = plugin
                        num_scans += 1

        # now insert then in the order the plugins idx value says
        for idx in range(num_scans):
            # plugin.plugin_object is an instance of the plugin
            # self.dataformattersCombo.addItem(plugin.plugin_object.name)
            # self.dataformatters[plugin.plugin_object.name] = plugin.plugin_object
            self.scanTypeToolBox.insertItem(pages, scans[idx], scans[idx].name)
            scans[idx].roi_changed.connect(self.on_scanpluggin_roi_changed)
            scans[idx].roi_deleted.connect(self.on_scantable_roi_deleted)
            scans[idx].plot_data.connect(self.on_plot_data_loaded)
            scans[idx].selected.connect(self.set_current_scan_pluggin)
            scans[idx].clear_all_sig.connect(self.on_clear_all)
            scans[idx].new_est_scan_time.connect(self.on_new_est_scan_time)
            scans[idx].call_main_func.connect(self.scan_plugin_func_call)

            scans[idx].test_scan.connect(self.on_test_scan)
            scans[idx].update_plot_strs.connect(self.on_update_plot_strs)

            self.scan_tbox_widgets.append(scans[idx])
            pages += 1

        layout.addWidget(self.scanTypeToolBox)
        self.scansFrame.setLayout(layout)

        if (len(self.scan_tbox_widgets) <= 0):
            raise sys

        #####
        limit_def = self.scan_tbox_widgets[0].get_max_scan_range_limit_def()
        plot_item_type = self.scan_tbox_widgets[0].plot_item_type

        if (hasattr(self, 'lineByLineImageDataWidget')):
            if (self.scan_tbox_widgets[0].is_multi_region()):
                self.lineByLineImageDataWidget.set_enable_multi_region(True)
            else:
                self.lineByLineImageDataWidget.set_enable_multi_region(False)

            self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)
        self.plotTabWidget.setCurrentIndex(PLOTTER_IMAGES_TAB)
        ######
        dx = MAIN_OBJ.device(DNM_DETECTOR_X)
        dy = MAIN_OBJ.device(DNM_DETECTOR_Y)
        centers = (dx.get_position(), dy.get_position())

        if (hasattr(self, 'lineByLineImageDataWidget')):
            self.lineByLineImageDataWidget.set_center_at_XY(centers, (500, 500))

        self.scanTypeToolBox.currentChanged.connect(self.on_toolbox_changed)

        wdg_com = self.scan_tbox_widgets[0].update_data()
        if (hasattr(self, 'scan_progress_table')):
            self.scan_progress_table.load_wdg_com(wdg_com)

    def on_scantable_roi_deleted(self, wdg_com):
        """
        on_scantable_roi_deleted(): description

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type

        :returns: None
        """
        """
        the ScanTableView widget has deleted a spatial row, pass info on to plotter
        so that the shapeItem can also be deleted  
        """
        # item_id = dct_get(wdg_com, SPDB_SCAN_PLUGIN_ITEM_ID)
        sp_rois_dct = dct_get(wdg_com, SPDB_SPATIAL_ROIS)
        #there will only be one selection
        item_id = list(sp_rois_dct.keys())[0]
        sp_db = sp_rois_dct[item_id]

        #item_id = dct_get(wdg_com, SPDB_ID_VAL)
        plot_item_type = dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE)

        item = self.lineByLineImageDataWidget.getShapePlotItem(item_id, item_type=plot_item_type)
        if (item):
            self.lineByLineImageDataWidget.blockSignals(True)
            self.lineByLineImageDataWidget.delPlotItem(item, replot=True)
            self.lineByLineImageDataWidget.blockSignals(False)

    def set_current_scan_pluggin(self, idx):
        # self.scanTypeToolBox.blockSignals(True)
        #_logger.debug('set_current_scan_pluggin: [%d]' % idx)
        self.scan_panel_idx = idx
        self.scanTypeToolBox.setCurrentIndex(self.scan_panel_idx)
        # self.scanTypeToolBox.blockSignals(False)

    def on_new_directed_beam_pos(self, newx, newy):
        '''
        The plotter has emitted a new_beam_position signal, so move the beam
        :param cx:
        :param cy:
        :return:
        scanning_mode_strings
            'GONI_ZONEPLATE'
            'COARSE_SAMPLEFINE'
            'COARSE_ZONEPLATE'
        '''
        scanning_mode_str = MAIN_OBJ.get_sample_scanning_mode_string()
        if(scanning_mode_str.find('GONI_ZONEPLATE') > -1):
            cx_pos = MAIN_OBJ.device(DNM_GONI_X).get_position()
            cy_pos = MAIN_OBJ.device(DNM_GONI_Y).get_position()
            x_mtr = MAIN_OBJ.device(DNM_ZONEPLATE_X)
            y_mtr = MAIN_OBJ.device(DNM_ZONEPLATE_Y)

            # make zero based for zoneplate scan
            x_pos = newx - cx_pos
            y_pos = newy - cy_pos

        elif (scanning_mode_str.find('COARSE_ZONEPLATE') > -1):
            cx_pos = MAIN_OBJ.device(DNM_COARSE_X).get_position()
            cy_pos = MAIN_OBJ.device(DNM_COARSE_Y).get_position()
            x_mtr = MAIN_OBJ.device(DNM_SAMPLE_X)
            y_mtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
            # make zero based for zoneplate scan
            x_pos = newx
            y_pos = newy


        elif(scanning_mode_str.find('COARSE_SAMPLEFINE') > -1):
            cx_pos = MAIN_OBJ.device(DNM_SAMPLE_X).get_position()
            cy_pos = MAIN_OBJ.device(DNM_SAMPLE_Y).get_position()
            x_mtr = MAIN_OBJ.device(DNM_SAMPLE_X)
            y_mtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
            # using absolute x/y from interferometer
            x_pos = newx
            y_pos = newy

        x_mtr.move(x_pos, wait=False)
        y_mtr.move(y_pos, wait=False)




    def on_scan_loaded(self, wdg_com):
        """
        on_scan_loaded(): This is a slot to service a signal emmitted from the PLOTTER only

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type
        self.delShapePlotItems()
        :returns: None
        """
        """ make call to update the scans params defined in the plugin """

        sp_db = get_first_sp_db_from_wdg_com(wdg_com)

        self.scan_panel_idx = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_PANEL_IDX))
        # if(self.scan_panel_idx > 100):
        #    self.scan_panel_idx = scan_panel_order.IMAGE_SCAN

        self.scanTypeToolBox.setCurrentIndex(self.scan_panel_idx)
        self.scan_tbox_widgets[self.scan_panel_idx].set_zp_focus_mode()
        time.sleep(0.15)
        # self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        # self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(sp_db, do_recalc=False)
        if (dct_get(sp_db, SPDB_PLOT_IMAGE_TYPE) in [image_types.FOCUS, image_types.OSAFOCUS]):
            # dont allow signals that would cause a plot segment to be created
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
            self.scan_tbox_widgets[self.scan_panel_idx].load_roi(wdg_com)
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)
        else:
            self.scan_tbox_widgets[self.scan_panel_idx].load_roi(wdg_com)
            # self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)

    def on_scanpluggin_roi_changed(self, wdg_com):
        """
        on_scanpluggin_roi_changed(): description

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type

        :returns: None
        """
        # _logger.debug('on_scanpluggin_roi_changed: called')
        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
            # self.scan_progress_table.set_directory_label(self.active_user.get_data_dir())
            # self.scan_progress_table.load_wdg_com(wdg_com)

            #          #for each spatial region create a plotitem
            #             sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
            #             for sp_id in sp_rois.keys():
            #                 sp_db = sp_rois[sp_id]
            #                 rect = sp_db[SPDB_RECT]
            #                 scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
            #                 plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
            #                 self.lineByLineImageDataWidget.addShapePlotItem(int(sp_id), rect, item_type=plot_item_type)
            pass
        else:

            sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
            # if(sp_rois is None):
            #    return
            if ((sp_rois is None) or (len(list(sp_rois.keys())) < 1)):
                #no spatial ids so clear unique id list
                reset_unique_roi_id()
                return
            for sp_id in list(sp_rois.keys()):
                add_to_unique_roi_id_list(sp_id)
                # sp_id = sp_rois.keys()[0]
                sp_db = sp_rois[sp_id]
                scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
                plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
                item_id = int(dct_get(sp_db, SPDB_ID_VAL))

                if (plot_item_type == spatial_type_prefix.PNT):
                    x1 = x2 = float(dct_get(sp_db, SPDB_XCENTER))
                    y1 = y2 = float(dct_get(sp_db, SPDB_YCENTER))

                else:
                    x1 = float(dct_get(sp_db, SPDB_XSTART))
                    y1 = float(dct_get(sp_db, SPDB_YSTART))
                    x2 = float(dct_get(sp_db, SPDB_XSTOP))
                    y2 = float(dct_get(sp_db, SPDB_YSTOP))

                xc = float(dct_get(sp_db, SPDB_XCENTER))
                yc = float(dct_get(sp_db, SPDB_YCENTER))

                # print 'on_scanpluggin_roi_changed: item_id = %d' % item_id
                if (hasattr(self, 'lineByLineImageDataWidget')):
                    item = self.lineByLineImageDataWidget.getShapePlotItem(item_id, plot_item_type)
                    #self.lineByLineImageDataWidget.set_shape_item_max_range(item, dct_get(sp_db, SPDB_SCAN_PLUGIN_MAX_SCANRANGE))

                    rect = (x1, y1, x2, y2)

                    #print 'on_scanpluggin_roi_changed: rect=' , (rect)
                    skip_list = [scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]
                    if((item is None) and not(scan_item_type is scan_types.PATTERN_GEN)):
                        if(scan_item_type not in skip_list):
                            self.lineByLineImageDataWidget.addShapePlotItem(item_id, rect, item_type=plot_item_type, re_center=True)
                    elif(scan_item_type is scan_types.PATTERN_GEN):
                        xc, yc = self.scan_pluggin.get_saved_center()
                        #self.lineByLineImageDataWidget.move_shape_to_new_center('pattern', xc, yc)

                    else:
                        self.lineByLineImageDataWidget.blockSignals(True)
                        if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.SELECT_ROI):
                            self.lineByLineImageDataWidget.selectShapePlotItem(item_id, select=True, item=item, item_type=plot_item_type)

                        elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ROI_CHANGED):
                            self.lineByLineImageDataWidget.resizeShapePlotItem(item_id, rect, item=item, item_type=plot_item_type)

                        self.lineByLineImageDataWidget.blockSignals(False)

        #self.lineByLineImageDataWidget.recenter_plot_to_all_items()
        if (hasattr(self, 'scan_progress_table')):
            self.scan_progress_table.load_wdg_com(wdg_com)

    def on_plotitem_roi_changed(self, wdg_com):
        """
        on_plotitem_roi_changed(): description

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type

        :returns: None
        """
        """ make call to update the scans params defined in the plugin """
        #print('on_plotitem_roi_changed: ', wdg_com)
        if (self.scan_in_progress):
            return

        #non_interactive_plots = [scan_panel_order.POSITIONER_SCAN]

        #skip_scan_q_table_plots = [scan_panel_order.OSA_FOCUS_SCAN, scan_panel_order.FOCUS_SCAN]

        x1 = dct_get(wdg_com, SPDB_XSTART)
        y1 = dct_get(wdg_com, SPDB_YSTART)
        x2 = dct_get(wdg_com, SPDB_XSTOP)
        y2 = dct_get(wdg_com, SPDB_YSTOP)
        rect = (x1, y1, x2, y2)
        # print 'on_plotitem_roi_changed: rect', rect

        #if (self.scan_panel_idx in non_interactive_plots):
        if(not self.scan_tbox_widgets[self.scan_panel_idx].is_interactive_plot()):
            return

        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ROI_CHANGED):

            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)
            wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].update_data()

            #if (self.scan_panel_idx in skip_scan_q_table_plots):
            if(self.scan_tbox_widgets[self.scan_panel_idx].is_skip_scan_queue_table_plot()):
                # just skip because this produces a lot of changes to the scan_q_table whcih currently are very slow when firing a lot of
                # signals to say the plot roi has chnaged
                pass
            else:
                if (hasattr(self, 'scan_progress_table')):
                    self.scan_progress_table.load_wdg_com(wdg_com)

        elif (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ADD_ROI):
            # pass on this addition request
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.DEL_ROI):
            # pass on this deletion request
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.SELECT_ROI):
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.DESELECT_ROI):
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        else:
            _logger.error('on_plotitem_roi_changed: unsupported widget_com command type' % wdg_com[WDGCOM_CMND])
        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)

    def on_clear_all(self):
        """ the scan plugin is asking us to clear the plot """
        self.lineByLineImageDataWidget.blockSignals(True)
        self.lineByLineImageDataWidget.delShapePlotItems()
        self.lineByLineImageDataWidget.blockSignals(False)

    def on_plot_data_loaded(self, tpl):
        """
        on_plot_data_loaded(): description

        :param data_dct: data_dct description
        :type data_dct: data_dct type

        :returns: None
        """
        # (fname, ado_obj) = tpl
        # wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        (fname, wdg_com, data) = tpl
        sp_db = get_first_sp_db_from_wdg_com(wdg_com)

        #         #for each spatial region create a plotitem
        #             sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        #             for sp_id in sp_rois.keys():
        #                 sp_db = sp_rois[sp_id]
        #                 rect = sp_db[SPDB_RECT]
        #                 scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
        #                 plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
        #                 self.lineByLineImageDataWidget.addShapePlotItem(int(sp_id), rect, item_type=plot_item_type)
        #
        if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) is scan_types.SAMPLE_LINE_SPECTRUM):
            self.lineByLineImageDataWidget.do_load_linespec_file(fname, wdg_com, data, dropped=False)
            self.lineByLineImageDataWidget.on_set_aspect_ratio(force=True)

        elif (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.GENERIC_SCAN]):
            self.lineByLineImageDataWidget.blockSignals(True)
            self.lineByLineImageDataWidget.delShapePlotItems()
            self.lineByLineImageDataWidget.load_image_data(fname, wdg_com, data)

            # only allow the scan param shapes to be created if NOT a focus type scan image
            if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS]):
                rect = sp_db[SPDB_RECT]
                sp_id = int(dct_get(sp_db, SPDB_ID_VAL))
                # scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
                plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
                self.lineByLineImageDataWidget.addShapePlotItem(int(sp_id), rect, item_type=plot_item_type)

            # make sure plotter is aware if it is supposed to allow more than one ShpeItem
            if(self.scan_tbox_widgets[self.scan_panel_idx].is_multi_region()):
               self.lineByLineImageDataWidget.set_enable_multi_region(True)
            else:
               self.lineByLineImageDataWidget.set_enable_multi_region(False)

            self.lineByLineImageDataWidget.blockSignals(False)

    def show_pattern_generator_pattern(self, tple):
        '''
        called by the pattern generator scan plugin
        :return:
        '''
        chkd, xc, yc, pad_size = tple
        if(chkd):
            #check to see if it is currently visible if so hide it if not show it

            self.lineByLineImageDataWidget.show_pattern( xc, yc, pad_size, do_show=True)
        else:
            self.lineByLineImageDataWidget.show_pattern(xc, yc, pad_size, do_show=False)

    def setup_image_plot(self):
        """
        setup_image_plot(): description

        :returns: None
        """
        #        from guiqwt.plot import ImageDialog
        #        self.lineByLineImageDataWidget = ImageDialog(edit=False, toolbar=True, wintitle="Contrast test",


        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

        # gridparam = {'fg_clr':fg_clr, 'bg_clr':bg_clr, 'min_clr':min_clr, 'maj_clr':maj_clr}

        # self.lineByLineImageDataWidget = ImageWidget(parent=None, filtStr="*.hdf5", type=None,
        #         options = dict(lock_aspect_ratio=True, show_contrast=True, show_xsection=True, show_ysection=True,
        #         xlabel=("microns", ""), ylabel=("microns", ""), colormap="gist_gray"))


        self.lineByLineImageDataWidget = ImageWidget(parent=None, type='analyze', settings_fname='%s_settings.json' % MAIN_OBJ.get_endstation_prefix())
        self.lineByLineImageDataWidget.set_lock_aspect_ratio(True)
        #self.bsImagePlotWidget = ImgPlotWindow()
        #vb = QtWidgets.QVBoxLayout()
        #vb.addWidget(self.bsImagePlotWidget)
        #self.bsImagePlotFrame.setLayout(vb)

        self.lineByLineImageDataWidget.setObjectName("lineByLineImageDataWidget")
        self.lineByLineImageDataWidget.register_osa_and_samplehldr_tool(sample_pos_mode)
        #        self.lineByLineImageDataWidget.register_osa_and_samplehldr_tool(sample_pos_mode)
        # self.lineByLineImageDataWidget.set_transform_factors(0.333, 0.333, 0.333, 'um')
        self.lineByLineImageDataWidget.setMinimumSize(600, 600)
        self.lineByLineImageDataWidget.setMaximumSize(1000, 1000)
        self.lineByLineImageDataWidget.enable_tool_by_name('tools.clsOpenFileTool', False)
        #   self.lineByLineImageDataWidget.set_sample_positioning_mode(sample_pos_mode)
        self.lineByLineImageDataWidget.set_dataIO(STXMDataIo)

        self.lineByLineImageDataWidget.addTool('DummySeparatorTool')
        self.lineByLineImageDataWidget.addTool('tools.BeamSpotTool')
        self.lineByLineImageDataWidget.addTool('tools.StxmControlBeamTool')
        self.lineByLineImageDataWidget.addTool('DummySeparatorTool')

        self.lineByLineImageDataWidget.set_grid_parameters(bg_clr, min_clr, maj_clr)
        self.lineByLineImageDataWidget.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)

        self.lineByLineImageDataWidget.new_roi_center.connect(self.on_plotitem_roi_changed)
        self.lineByLineImageDataWidget.scan_loaded.connect(self.on_scan_loaded)
        self.lineByLineImageDataWidget.install_beam_fbk_devs(MAIN_OBJ)
        self.lineByLineImageDataWidget.new_beam_position.connect(self.on_new_directed_beam_pos)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.lineByLineImageDataWidget)
        self.imagePlotFrame.setLayout(vbox)

        # self.lineByLineImageDataWidget.create_sample_holder()

        self.lineByLineImageDataWidget.set_data_dir(self.active_user.get_data_dir())
        MAIN_OBJ.set('IMAGE_WIDGET', self.lineByLineImageDataWidget)

    def setup_spectra_plot(self):

        """
        setup_spectra_plot(): description

        :returns: None
        """
        vbox = QtWidgets.QVBoxLayout()
        # self.spectraWidget = CurveViewerWidget(parent = self, winTitleStr = "Spectra Data Viewer")
        self.spectraWidget = CurveViewerWidget(parent=self)
        self.spectraWidget.set_dataIO(STXMDataIo)
        self.spectraWidget.setObjectName("spectraWidget")
        self.spectraWidget.add_legend("TL")

        vbox.addWidget(self.spectraWidget)
        self.spectraPlotFrame.setLayout(vbox)


    def setup_calib_camera(self):
        """
        setup_video_panel(): description

        :returns: None
        plotTabWidget
        tab3
        """
        from cls.applications.pyStxm.widgets.camera_ruler import CameraRuler, camruler_mode
        vbox = QtWidgets.QVBoxLayout()
        # self.spectraWidget = CurveViewerWidget(parent = self, winTitleStr = "Spectra Data Viewer")
        #self.splash.show_msg('Loading Calibration Camera in Client Mode')
        self.calibCamWidget = CameraRuler(mode=camruler_mode.CLIENT, main_obj=MAIN_OBJ, parent=self)
        self.calibCamWidget.setObjectName("calibCamWidget")

        vbox.addWidget(self.calibCamWidget)
        self.calibCamPlotFrame.setLayout(vbox)


    #     def add_to_plot_tab_widget(self, tab_num, tab_title, widg):
    #         tw = self._get_base_tab_widget()
    #         self.plotTabWidget.setTabPosition(tab_num)
    #         self.plotTabWidget.setTabText(tab_title)
    #         self.plotTabWidget.
    #
    #     def _get_base_tab_widget(self):
    #         tw = QtWidgets.QWidget()
    #         tf = QtWidgets.QFrame()
    #         vbox = QtWidgets.QVBoxLayout()
    #         vbox.addWidget(tf)
    #         tw.setLayout(vbox)
    #         return(tw)


    def setup_video_panel(self):
        """
        setup_video_panel(): description

        :returns: None
        """
        pass
        # QWebSettings.globalSettings().setAttribute(QWebSettings.PluginsEnabled, True)
        # QWebSettings.globalSettings().setAttribute(QWebSettings.AutoLoadImages, True)
        # self.videoWebView.setUrl(QtCore.QUrl("http://ccd1608-500.clsi.ca/jpg/image.jpg"))
        # self.videoWebView.load(QtCore.QUrl("http://ccd1608-500.clsi.ca/jpg/image.jpg"))

        # self.videoWebView.setUrl(QtCore.QUrl("http://v2e1602-101/axis-cgi/mjpg/video.cgi?camera=1"))
        # self.videoWebView.load(QtCore.QUrl("http://v2e1602-101/axis-cgi/mjpg/video.cgi?camera=1"))

        # self.vidTimer.start(250)

        # self.videoPlayer.load(Phonon.MediaSource('http://ccd1608-500.clsi.ca/view/index.shtml'))
        # self.videoPlayer.play()


    def on_video_timer(self):
        """
        on_video_timer(): description

        :returns: None
        """
        self.videoWebView.load(QtCore.QUrl("http://ccd1608-500.clsi.ca/jpg/image.jpg"))
        # self.videoWebView.reload()

    def sscan_faze_cb_report(self, sscans):
        '''
        a convienience function to get the current state of all scan callbacks for FAZE field of SSCAN record
        :param sscans:
        :return:
        '''
        skeys = sorted(sscans.keys())
        for k in skeys:
            sscan = sscans[k]
            ss = sscan['sscan']
            cbs = ss._pvs['FAZE'].callbacks
            num_cbs = len(list(cbs.keys()))
            cb_ids = list(cbs.keys())
            id_str = ''
            for _id in cb_ids:
                id_str += '%d ' % _id

            print('[%s] has [%d] cbs for FAZE with Ids [%s]' % (ss.NAME, num_cbs, id_str))

    def init_sscans_for_console(self):
        # devs = MAIN_OBJ.get_devices()
        # sscans = devs['SSCANS']
        # sscan1 = sscans['uhvstxm:scan1']
        # sscan2 = sscans['uhvstxm:scan2']
        # sscan3 = sscans['uhvstxm:scan3']
        # sscan4 = sscans['uhvstxm:scan4']
        # sscan5 = sscans['uhvstxm:scan5']
        # sscan6 = sscans['uhvstxm:scan6']
        # sscan7 = sscans['uhvstxm:scan7']
        # sscan8 = sscans['uhvstxm:scan8']
        #
        # sscan1_fazecbs = sscan1._pvs['FAZE'].callbacks
        # sscan2_fazecbs = sscan2._pvs['FAZE'].callbacks
        # sscan3_fazecbs = sscan3._pvs['FAZE'].callbacks
        # sscan4_fazecbs = sscan4._pvs['FAZE'].callbacks
        # sscan5_fazecbs = sscan5._pvs['FAZE'].callbacks
        # sscan6_fazecbs = sscan6._pvs['FAZE'].callbacks
        # sscan7_fazecbs = sscan7._pvs['FAZE'].callbacks
        # sscan8_fazecbs = sscan8._pvs['FAZE'].callbacks
        #
        # sscans = {}
        # sscans['sscan1'] = {'sscan': sscan1, 'cbs': sscan1_fazecbs}
        # sscans['sscan2'] = {'sscan': sscan2, 'cbs': sscan2_fazecbs}
        # sscans['sscan3'] = {'sscan': sscan3, 'cbs': sscan3_fazecbs}
        # sscans['sscan4'] = {'sscan': sscan4, 'cbs': sscan4_fazecbs}
        # sscans['sscan5'] = {'sscan': sscan5, 'cbs': sscan5_fazecbs}
        # sscans['sscan6'] = {'sscan': sscan6, 'cbs': sscan6_fazecbs}
        # sscans['sscan7'] = {'sscan': sscan7, 'cbs': sscan7_fazecbs}
        # sscans['sscan8'] = {'sscan': sscan8, 'cbs': sscan8_fazecbs}
        #
        # #self.sscan_faze_cb_report(sscans)
        #
        # return(sscans)
        pass

    def setup_info_dock(self):
        """
        setup_info_dock(): description

        :returns: None
        """
        # ns = {'main': self, 'widget': self, 'det_scan' : scans[1]}
        #sscans = self.init_sscans_for_console()
        ns = {'main': self, 'pythonShell': self.pythonshell, 'g': globals(), 'MAIN_OBJ': MAIN_OBJ, 'scans_plgins': self.scan_tbox_widgets}
        # msg = "Try for example: widget.set_text('foobar') or win.close()"
        #self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True, exitfunc=exit)
        self.pythonshell = ShellWidget(parent=None, namespace=ns, commands=[], multithreaded=True)
        self.pyconsole_layout.addWidget(self.pythonshell)
        # self.apply_stylesheet(self.pythonshell, self.qssheet)


    def on_toolbox_changed(self, idx):
        """
        on_toolbox_changed(): description

        :param idx: idx description
        :type idx: idx type

        :returns: None
        """
        reset_unique_roi_id()
        ranges = (None, None)
        # print 'on_toolbox_changed: %d' % idx
        #spectra_plot_types = [scan_panel_order.POINT_SCAN, scan_panel_order.POSITIONER_SCAN]
        #non_interactive_plots = [scan_panel_order.POSITIONER_SCAN]
        # multi_spatial_scan_types = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM,
        #                             scan_types.SAMPLE_IMAGE, \
        #                             scan_types.SAMPLE_IMAGE_STACK]
        # skip_list = [scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]

        #Note: these are scan panel order NOT scan types
        #skip_centering_scans = [scan_panel_order.FOCUS_SCAN, scan_panel_order.TOMOGRAPHY,
        #                        scan_panel_order.LINE_SCAN, scan_panel_order.POINT_SCAN, scan_panel_order.IMAGE_SCAN]

        self.scan_panel_idx = idx

        if (len(self.scan_tbox_widgets) > 0):

            self.lineByLineImageDataWidget.delShapePlotItems()

            if (hasattr(self, 'scan_progress_table')):
                self.scan_progress_table.clear_table()
            sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()

            if(self.scan_pluggin is not None):
                self.scan_pluggin.on_plugin_defocus()

            scan_pluggin = self.scan_tbox_widgets[self.scan_panel_idx]
            self.scan_pluggin = scan_pluggin

            scan_pluggin.on_plugin_focus()

            if(not scan_pluggin.isEnabled()):
                #pluggin is disabled so ignore it
                return

            ranges = scan_pluggin.get_saved_range()
            centers = scan_pluggin.get_saved_center()
            axis_strs = scan_pluggin.get_axis_strs()
            max_scan_range = scan_pluggin.get_spatial_scan_range()
            limit_def = scan_pluggin.get_max_scan_range_limit_def()
            plot_item_type = scan_pluggin.plot_item_type
            enable_multi_region = scan_pluggin.is_multi_region()
            scan_type = scan_pluggin.get_scan_type()
            do_center_plot = scan_pluggin.get_do_center_plot_on_focus()
            # wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].update_data()
            # self.scan_progress_table.load_wdg_com(wdg_com)

        #self.lineByLineImageDataWidget.delShapePlotItems()

        #if (idx in spectra_plot_types):
        if (scan_pluggin.is_spectra_plot_type()):
            #but only switch if it is not a point scan as the selection for a point scan is done on a 2D image
            #if(idx is scan_panel_order.POINT_SCAN):
            if(scan_pluggin.type is scan_types.SAMPLE_POINT_SPECTRUM):
                # it is a point scan so zoom the plot to a valid range
                #sx = MAIN_OBJ.device(DNM_SAMPLE_X)
                #sy = MAIN_OBJ.device(DNM_SAMPLE_Y)
                sx = MAIN_OBJ.get_sample_positioner('X')
                sy = MAIN_OBJ.get_sample_positioner('Y')

                centers = (sx.get_position(), sy.get_position())
                self.lineByLineImageDataWidget.set_center_at_XY(centers, max_scan_range)
            else:
                self.plotTabWidget.setCurrentIndex(PLOTTER_SPECTRA_TAB)
                self.spectraWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])
        else:
            self.plotTabWidget.setCurrentIndex(PLOTTER_IMAGES_TAB)

            if ((ranges[0] is not None) and (ranges[1] is not None)):

                #do_recenter_lst = [scan_panel_order.IMAGE_SCAN, scan_panel_order.TOMOGRAPHY, scan_panel_order.LINE_SCAN]

                #if ((self.scan_panel_idx == scan_panel_order.IMAGE_SCAN) and (sample_positioning_mode == sample_positioning_modes.GONIOMETER)):
                #if ((self.scan_panel_idx in  do_recenter_lst) and (sample_positioning_mode == sample_positioning_modes.GONIOMETER)):
                if ((scan_pluggin.is_do_recenter_type()) and (
                        sample_positioning_mode == sample_positioning_modes.GONIOMETER)):
                    self.lineByLineImageDataWidget.set_center_at_XY(centers, ranges)
                else:

                    #if(self.scan_panel_idx in skip_centering_scans):
                    if (scan_pluggin.is_skip_center_type()):
                        #we are likely already where we want to be on the plotter if the user switched to one of these scans
                        pass
                    else:
                        #sx = MAIN_OBJ.device(DNM_SAMPLE_X)
                        #sy = MAIN_OBJ.device(DNM_SAMPLE_Y)
                        sx = MAIN_OBJ.get_sample_positioner('X')
                        sy = MAIN_OBJ.get_sample_positioner('Y')
                        centers = (sx.get_position(), sy.get_position())
                        if (scan_type is scan_types.PATTERN_GEN):
                            self.lineByLineImageDataWidget.set_center_at_XY(centers, (ranges[0]*10, ranges[1]*10))
                        else:
                            self.lineByLineImageDataWidget.set_center_at_XY(centers, ranges)

                # self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)
                self.lineByLineImageDataWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])

        self.lineByLineImageDataWidget.set_max_shape_sizes(max_scan_range)
        self.lineByLineImageDataWidget.set_enable_multi_region(enable_multi_region)

        #if (self.scan_panel_idx in non_interactive_plots):
        if(not scan_pluggin.is_interactive_plot()):
            # disable all roi selection tools
            self.lineByLineImageDataWidget.set_shape_limits(shape=None, limit_def=None)
        else:
            self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)

        if (len(self.scan_tbox_widgets) > 0):
            # some of the params on a particular tool box read pv's so make sure the
            # focus calc mode is set correctly and has time to process
            scan_pluggin.set_zp_focus_mode()
            time.sleep(0.15)
            scan_pluggin.load_from_defaults()

        # if(scan_type in multi_spatial_scan_types):
        #scan_pluggin.on_focus_init_base_values()

        wdg_com = scan_pluggin.update_data()

        #if(scan_type is scan_types.PATTERN_GEN):
        #    self.show_pattern_generator_pattern()

        # if(wdg_com):
        #    if(len(wdg_com['SPATIAL_ROIS']) > 0):
        #        self.scan_progress_table.load_wdg_com(wdg_com)


    #def scan_plugin_func_call(self, func_nm, chkd):
    def scan_plugin_func_call(self, func_nm, tuple):
        #allow the scan pluggins to (if they know about a function here in stxmMain) to call it by name
        if(hasattr(self, func_nm)):
            func = getattr(self, func_nm)
            func(tuple)
        else:
            _logger.info('Scan plugin called a function in stxmMain that doesnt exist: [%s]' % func_nm)


    def on_update_plot_strs(self, axis_strs):
        #spectra_plot_types = [scan_panel_order.POINT_SCAN, scan_panel_order.POSITIONER_SCAN]
        #scan_pluggin = self.scan_tbox_widgets[self.scan_panel_idx]
        #plot_item_type = scan_pluggin.plot_item_type
        #if(self.scan_panel_idx in spectra_plot_types):
        if (self.scan_tbox_widgets[self.scan_panel_idx].is_spectra_plot_type()):
            self.spectraWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])
        else:
            self.lineByLineImageDataWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])

    def init_statusbar(self):
        """
        init_statusbar(): description

        :returns: None
        """

        self.status_list = []
        title_color = master_colors['app_blue']
        fbk_color = 'white'
        msg_color = master_colors['msg_color']
        ma_color = master_colors['app_yellow']

        # separator = QtWidgets.QLabel()
        # separator.setMaximumWidth(5000)
        # separator.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.status_list.append(separator)

        #         self.status_list.append(ophyd_strLabel(MAIN_OBJ.device('SRStatus_msgL1'),  hdrText='SR Status', title_color=title_color, var_clr=fbk_color))
        #         self.status_list.append(ophyd_strLabel(MAIN_OBJ.device('SRStatus_msgL2'), title_color=title_color, var_clr=fbk_color))
        #         self.status_list.append(ophyd_strLabel(MAIN_OBJ.device('SRStatus_msgL3'), title_color=title_color, var_clr=fbk_color))

        self.status_list.append(
            ophyd_aiLabelWidget(MAIN_OBJ.device(DNM_AX1_INTERFER_VOLTS), hdrText='Ax1 Interferometer', egu='volts', title_color=title_color,
                             var_clr=fbk_color, alarm=0.2, warn=0.29))

        self.status_list.append(
            ophyd_aiLabelWidget(MAIN_OBJ.device(DNM_AX2_INTERFER_VOLTS), hdrText='Ax2 Interferometer', egu='volts',
                             title_color=title_color,
                             var_clr=fbk_color, alarm=0.2, warn=0.29))

        self.status_list.append(
            ophyd_aiLabelWidget(MAIN_OBJ.device(DNM_MONO_EV_FBK), hdrText='Energy', egu='eV', title_color=title_color,
                             var_clr=fbk_color))
        # self.status_list.append(ophyd_aiLabelWidget(MAIN_OBJ.device('ticker'), hdrText='I0', title_color=title_color, var_clr=fbk_color))
        self.status_list.append(
            ophyd_mbbiLabelWidget(MAIN_OBJ.device(DNM_SYSTEM_MODE_FBK), hdrText='SR Mode', title_color=title_color,
                               var_clr=fbk_color))
        self.status_list.append(
            ophyd_aiLabelWidget(MAIN_OBJ.device(DNM_RING_CURRENT), hdrText='Ring', egu='mA', title_color=title_color,
                             var_clr=fbk_color, alarm=5, warn=20))
        bl_txt = format_text('Beamline:', MAIN_OBJ.get_beamline_name(), title_color=title_color, var_color=fbk_color)
        self.status_list.append(QtWidgets.QLabel(bl_txt))

        es_txt = format_text('EndStation:', MAIN_OBJ.get_endstation_name(), title_color=title_color, var_color=fbk_color)
        self.status_list.append(QtWidgets.QLabel(es_txt))

        sm_txt = format_text('Scanning Mode:', MAIN_OBJ.get_sample_scanning_mode_string(), title_color=title_color,
                             var_color=fbk_color)
        self.status_list.append(QtWidgets.QLabel(sm_txt))

        for sts in self.status_list:
            self.statusBar().addPermanentWidget(sts)
            # add a separator
            self.statusBar().addPermanentWidget(QtWidgets.QLabel('|'))


    def add_line_to_plot(self, counter_to_plotter_com_dct):
        """
        add_line_to_plot(): description

        :param row: row description
        :type row: row type

        :param scan_data: scan_data description
        :type scan_data: scan_data type

        :returns: None
        """
        """ a function to take data (a full line) and add it to the configured plotters
        Needed a flag to monitor when to start a new image

        CNTR2PLOT_TYPE_ID = 'type_id'   #to be used to indicate what kind of counter/scan is sending this info
        CNTR2PLOT_ROW = 'row'           #a y position
        CNTR2PLOT_COL = 'col'           #an x position
        CNTR2PLOT_VAL = 'val'           #the point or array of data
        CNTR2PLOT_IMG_CNTR = 'img_cntr' #current image counter
        CNTR2PLOT_EV_CNTR = 'ev_idx'    #current energy counter
        CNTR2PLOT_SP_ID = 'sp_id'       #spatial id this data belongs to
        CNTR2PLOT_IS_POINT = 'is_pxp'   #data is from a point by point scan
        CNTR2PLOT_IS_LINE = 'is_lxl'    #data isfrom a line by line scan
        """

        #print 'add_line_to_plot: rcvd update from sp_id[%d]' % counter_to_plotter_com_dct[CNTR2PLOT_SP_ID]

        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        col = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        line_data = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        img_cntr = counter_to_plotter_com_dct[CNTR2PLOT_IMG_CNTR]
        is_line = counter_to_plotter_com_dct[CNTR2PLOT_IS_LINE]
        is_point = counter_to_plotter_com_dct[CNTR2PLOT_IS_POINT]
        sp_id = counter_to_plotter_com_dct[CNTR2PLOT_SP_ID]
        # self.cur_image_idx = _dct['img_idx']

        #print('add_line_to_plot: row[%d]' % row)
        #print('add_line_to_plot: ', (row, line_data))

        if (self.executingScan.scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            # if(not self.image_started and (col == 0)):
            # if(not self.executingScan.image_started and (col == 0)):
            if (is_point):
                if (not self.executingScan.image_started and (col == 0) and (row == 0)):
                    self.on_image_start(sp_id=sp_id)
            if (is_line):
                if (not self.executingScan.image_started and (col == 0)):
                    self.on_image_start(sp_id=sp_id)

            if (col > 0):
                # self.image_started = False
                self.executingScan.image_started = False

            #print('add_line_to_plot: col=%d' % self.executingScan.linescan_dct['col_idxs'][col])
            self.lineByLineImageDataWidget.addVerticalLine(self.executingScan.linescan_dct['map'][col],
                                                   self.executingScan.linescan_dct['col_idxs'][col], line_data, True)
        else:
            if (is_point):
                if (not self.executingScan.image_started and (col == 0) and (row == 0)):
                    #print 'calling on_image_start: not self.executingScan.image_started and (col == 0) and (row == 0)'
                    self.on_image_start(sp_id=sp_id)

            if (is_line):
                if (not self.executingScan.image_started and (row == 0)):
                    #print('calling on_image_start: not self.executingScan.image_started and (row == 0)')
                    self.on_image_start(sp_id=sp_id)

            if (row > 0):
                # self.image_started = False
                self.executingScan.image_started = False

            self.lineByLineImageDataWidget.addLine(0, row, line_data, True)


    def add_point_to_plot(self, counter_to_plotter_com_dct):
        """
        add_point_to_plot(): description
        CNTR2PLOT_TYPE_ID = 'type_id'   #to be used to indicate what kind of counter/scan is sending this info
        CNTR2PLOT_ROW = 'row'           #a y position
        CNTR2PLOT_COL = 'col'           #an x position
        CNTR2PLOT_VAL = 'val'           #the point or array of data
        CNTR2PLOT_IMG_CNTR = 'img_cntr' #current image counter
        CNTR2PLOT_EV_CNTR = 'ev_idx'    #current energy counter
        CNTR2PLOT_SP_ID = 'sp_id'       #spatial id this data belongs to
        CNTR2PLOT_IS_POINT = 'is_pxp'   #data is from a point by point scan
        CNTR2PLOT_IS_LINE = 'is_lxl'    #data isfrom a line by line scan
        CNTR2PLOT_SCAN_TYPE = 'scan_type' # the scan_type from types enum of this scan

        :param row: row description
        :type row: row type

        :param tpl: tpl description
        :type tpl: tpl type

        :returns: None
        """
        """ a function to take data (a full line) and add it to the configured plotters
        Need a flag to monitor when to start a new image
        """

        # print counter_to_plotter_com_dct
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        col = point = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        val = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        img_cntr = counter_to_plotter_com_dct[CNTR2PLOT_IMG_CNTR]
        ev_cntr = counter_to_plotter_com_dct[CNTR2PLOT_EV_CNTR]
        cur_scan_type = counter_to_plotter_com_dct[CNTR2PLOT_SCAN_TYPE]
        sp_id = self.executingScan._current_sp_id

        #print('add_point_to_plot:',sp_id, counter_to_plotter_com_dct)

        #if (self.get_cur_scan_type() == scan_types.SAMPLE_LINE_SPECTRUM):
        if (cur_scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            if (not self.executingScan.image_started and (ev_cntr == 0) and ((col == 0) and (row == 0))):
                self.on_image_start(sp_id=sp_id)

            if (col > 0):
                self.executingScan.image_started = False
            #img_idx, y, x, val
            if(img_cntr is None):
                img_cntr = 0

            #self.lineByLineImageDataWidget.addPoint(img_idx, y, x, val, show)
            self.lineByLineImageDataWidget.addPoint(img_cntr, row, col, val, True)

        else:
            if (not self.executingScan.image_started and (row == 0)):
                self.on_image_start(sp_id=sp_id)
            elif( self.executingScan.image_started and ((col == 0) and (row == 0))):
                self.on_image_start(sp_id=sp_id)

            #print('add_point_to_plot: row=%d, point=%d, val=%d' % (row, point, val))
            img_idx = 0
            self.lineByLineImageDataWidget.addPoint(img_idx, row, col, val, True)


    def add_point_to_spectra(self, counter_to_plotter_com_dct):
        """
        add_point_to_spectra():
        CNTR2PLOT_TYPE_ID = 'type_id'   #to be used to indicate what kind of counter/scan is sending this info
        CNTR2PLOT_ROW = 'row'           #a y position
        CNTR2PLOT_COL = 'col'           #an x position
        CNTR2PLOT_VAL = 'val'           #the point or array of data
        CNTR2PLOT_IMG_CNTR = 'img_cntr' #current image counter
        CNTR2PLOT_EV_CNTR = 'ev_idx'    #current energy counter
        CNTR2PLOT_SP_ID = 'sp_id'       #spatial id this data belongs to
        CNTR2PLOT_IS_POINT = 'is_pxp'   #data is from a point by point scan
        CNTR2PLOT_IS_LINE = 'is_lxl'    #data isfrom a line by line scan

        :param row: row description
        :type row: row type

        :param tpl: tpl description
        :type tpl: tpl type

        :returns: None
        """
        """ a function to take data (a full line) and add it to the configured plotters """
        # _logger.debug('add_point_to_spectra: called with row=%d, tpl=')
        sp_id = counter_to_plotter_com_dct[CNTR2PLOT_SP_ID]
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        point = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        val = counter_to_plotter_com_dct[CNTR2PLOT_VAL]

        # print 'add_point_to_spectra: sp_id=%d row=%d, point=%d, val=%d' % (sp_id, row, point, val)
        self.spectraWidget.addXYPoint('sp_id_%d' % sp_id, point, val, update=True)


    def reset_image_plot(self):
        self.image_started == False
        #if I want to experiment with adding image after image start by commenting this next line out
        self.lineByLineImageDataWidget.delImagePlotItems()
        self.lineByLineImageDataWidget.delShapePlotItems()
        self.lineByLineImageDataWidget.set_auto_contrast(True)


    def assign_datafile_names_to_sp_db(self, sp_db, d, image_idx=0):
        ''' d keys ['thumb_name', 'prefix', 'data_ext', 'stack_dir', 'data_name', 'thumb_ext']
        '''
        #print 'image_idx=%d' % image_idx
        #print 'd[data_dir]=%s' % d['data_dir']
        #print 'd[data_name]=%s' % d['data_name']

        ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
        dct_put(ado_obj, ADO_CFG_DATA_DIR, d['data_dir'])
        dct_put(ado_obj, ADO_CFG_DATA_FILE_NAME, d['data_name'])
        dct_put(ado_obj, ADO_CFG_DATA_THUMB_NAME, d['thumb_name'])
        dct_put(ado_obj, ADO_CFG_PREFIX, d['prefix'])
        dct_put(ado_obj, ADO_CFG_DATA_EXT, d['data_ext'])
        dct_put(ado_obj, ADO_CFG_STACK_DIR, d['stack_dir'])
        dct_put(ado_obj, ADO_CFG_THUMB_EXT, d['thumb_ext'])
        dct_put(ado_obj, ADO_CFG_DATA_IMG_IDX, image_idx)


    def test_type(self, val, typ):
        if ((val is None) or (type(val) != typ)):
            return (False)
        else:
            return (True)


    def test_assign_datafile_names_to_sp_db(self, wdg_com):
        ''' a test to make sure that the required data items have been set before allowing them
        to continue on to the scan lass
        d keys ['thumb_name', 'prefix', 'data_ext', 'stack_dir', 'data_name', 'thumb_ext']
        '''
        _lst = []
        sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = sorted(sp_rois.keys())
        for sp_id in sp_ids:
            sp_db = sp_rois[sp_id]
            ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_DATA_DIR), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_DATA_THUMB_NAME), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_PREFIX), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_DATA_EXT), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_STACK_DIR), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_THUMB_EXT), str))
            _lst.append(self.test_type(dct_get(ado_obj, ADO_CFG_DATA_IMG_IDX), int))

            for v in _lst:
                if (not v):
                    return (False)

        return (True)


    def determine_num_thumbnail_images_required(self, wdg_com, as_num=False):
        """
        determine_num_thumbnail_images_required(): take a list of spatial regions and check the scan type and retrun
        the number of images that will be needed

        :param sp_rois: sp_rois description
        :type sp_rois: sp_rois type

        :returns: integer number of images required for the scans
        """
        single_image_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_FOCUS, scan_types.OSA_IMAGE,
                              scan_types.SAMPLE_FOCUS, \
                              scan_types.SAMPLE_IMAGE, scan_types.GENERIC_SCAN, scan_types.SAMPLE_LINE_SPECTRUM,
                              scan_types.SAMPLE_POINT_SPECTRUM]
        sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = sorted(sp_rois.keys())
        n_imgs = []
        _imgs = 0
        for sp_id in sp_ids:
            sp_db = sp_rois[sp_id]
            scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
            if (scan_type in single_image_scans):
                # n_imgs.append(1)
                _imgs = 1
            else:
                # n_imgs.append(self.get_num_ev_points(sp_db[SPDB_EV_ROIS]))
                _imgs = self.get_num_ev_points(sp_db[SPDB_EV_ROIS])
                # n_imgs = sp_db[SPDB_EV_NPOINTS] * sp_db[SPDB_POL_NPOINTS]
            n_imgs.append(_imgs)
        if(as_num):
            return(sum_lst(n_imgs))
        else:
            return n_imgs


    def get_num_ev_points(self, ev_rois):
        """
        make sure to return an int
        """
        n_ev = 0
        _pol = 0
        _ev = 0

        for ev_roi in ev_rois:
            _ev = ev_roi[NPOINTS]
            _pol = len(ev_roi['EPU_POL_PNTS'])
            n_ev += _ev * _pol
        return (int(n_ev))


    def apply_user_settings_to_scan(self, scan):
        """
        apply_user_settings_to_scan: query the appConfig settings file andset any flags of the executing scan here

        :param scan: This is the currently configured executing scan
        :type scan: this is a scan plugin that has ScanParamWiget as its parent class

        """
        appConfig.update()
        # set the save all data flag
        val = appConfig.get_bool_value('DATA', 'save_all_data')
        if (val is not None):
            scan.set_save_all_data(val)

        val = appConfig.get_bool_value('DATA', 'save_jpg_thumbnails')
        if (val is not None):
            scan.set_save_jpgs(val)


            # set others below

    def set_user_selected_counters(self, sscan):
        '''
        get the current user sleected counters and populate the counter_dct and set that dict to the sscan
        :param sscan:
        :return:
        '''

        # here get the counters that the user has selected and populate the counter dict

        #for now just populate it with APD
        cntr_dct = {}
        cntr_dct[DNM_DEFAULT_COUNTER] = {'devname': DNM_COUNTER_APD, 'dev': MAIN_OBJ.device(DNM_COUNTER_APD)}
        #cntr_dct['axis1InterferVolts'] = {'devname': DNM_AX1_INTERFER_VOLTS, 'dev': MAIN_OBJ.device(DNM_AX1_INTERFER_VOLTS)}
        #cntr_dct['axis2InterferVolts'] = {'devname': DNM_AX2_INTERFER_VOLTS, 'dev': MAIN_OBJ.device(DNM_AX2_INTERFER_VOLTS)}
        #cntr_dct['ring_current'] = {'devname': DNM_RING_CURRENT,'dev': MAIN_OBJ.device(DNM_RING_CURRENT)}

        sscan.set_counter_dct(cntr_dct)


    def on_test_scan(self, scan_panel_id):
        _logger.info('ok testing scan plugin [%d]' % scan_panel_id)
        self.set_current_scan_pluggin(scan_panel_id)
        self.on_start_scan(testing=True)


    def on_start_scan(self, testing=False):
        """
        on_start_scan(): description

        :returns: None
        """
        #force shutter control back to Auto
        self.on_shutterCntrlComboBox(0)  # Auto

        self.executingScan = None
        # make sure the data dir is up to date in case the 24 hour time has rolled over
        self.active_user.create_data_dir()
        #default to locked aspect ratio

        # keep the scan plugin from firing any signals that would cause other widgets to respond
        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        # make sure that the current scan parameters are recorded
        self.scan_tbox_widgets[self.scan_panel_idx].update_last_settings()

        self.cur_wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].get_roi()

        if ((self.cur_wdg_com is None) or (len(self.cur_wdg_com[SPDB_SPATIAL_ROIS]) is 0)):
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)
            _logger.info('there was a problem retrieving the data from the scan pluggin via get_roi()')
            return

            # quick check to see if there is gong to be a problem saving the data
        # if(not self.check_data_export_good_to_go()):
        #     _logger.info('there was a problem test creating the tmp data file' )
        #     return
        #self.check_data_export_good_to_go()

        # init some variables
        self.data = []
        MAIN_OBJ.clear_scans()

        self.reset_image_plot()

        self.cur_ev_idx = 0
        new_stack_dir = False

        # ok allow the scan plugin to fire signals again
        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)

        # assign these values that are used to decide which GUI signals to connect and disconnect
        self.set_cur_scan_type(self.scan_tbox_widgets[self.scan_panel_idx].type)
        self.set_cur_scan_sub_type(self.scan_tbox_widgets[self.scan_panel_idx].sub_type)

        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()

        # get an instance of the actual scan class that is used to configure and connect to the sscan records
        #sscan = self.scan_tbox_widgets[self.scan_panel_idx].get_sscan_instance()
        #scan_plan = self.scan_tbox_widgets[self.scan_panel_idx].get_scan_plan(detectors=[MAIN_OBJ.device('POINT_DET')])
        self.scan_tbox_widgets[self.scan_panel_idx].on_plugin_scan_start()
        scan_class = self.scan_tbox_widgets[self.scan_panel_idx].get_scan_class()
        scan_class.set_active_user(self.active_user)
        scan_class.scan_type = scan_type
        #MAIN_OBJ.engine_widget.engine.plan_creator = lambda: scan_plan

        if(testing and (self.scan_tbox_widgets[self.scan_panel_idx].test_sp_db is None)):
            #the plugin doesnt have the support required for testing so turn testing off
            testing = False
            _logger.error('User requested TESTING but the scan plugin does not have a test_sp_db configured, so turning testing off')
            return

        self.apply_user_settings_to_scan(scan_class)
        self.executingScan = scan_class
        self.executingScan.disconnect_signals()

        # set main gui widgets up for running a scan
        self.set_buttons_for_scanning()

        # make sure that all data required by scan metadata is loaded into scan
        fprms_pnl = self.get_pref_panel('FocusParams')
        cur_zp_def = fprms_pnl.get_cur_zp_def()
        self.executingScan.set_zoneplate_info_dct(cur_zp_def)

        #assign the detectos to use
        self.set_user_selected_counters(self.executingScan)

        # grab some information used by all scans below
        sp_rois = dct_get(self.cur_wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = sorted(sp_rois.keys())
        self.cur_sp_rois = copy.copy(sp_rois)

        scan_class.set_spatial_id_list(sp_ids)

        # a list of basic scans that use the same configuration block below
        _simple_types = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.GENERIC_SCAN,
                         scan_types.SAMPLE_FOCUS, scan_types.COARSE_IMAGE, scan_types.COARSE_GONI]
        _multispatial_types = [scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_POINT_SPECTRUM]#, scan_types.TOMOGRAPHY]
        _stack_types = [scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY ]

        if (scan_type in _simple_types):
            sp_id = sp_ids[0]
            sp_db = sp_rois[sp_id]
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5',
                                     stack_dir=False, num_desired_datafiles=1)
            self.assign_datafile_names_to_sp_db(sp_db, d[0])
            #scan_class.set_spatial_id(sp_id)
            #scan_class.set_datafile_names_dict(d)
            #sept 1 sscan.set_spatial_id_list(sp_ids)
            scan_class.configure(self.cur_wdg_com, sp_id=sp_id, line=False)

            if(scan_sub_type is scan_sub_types.POINT_BY_POINT):
                self.point_det.set_scan_type(scan_type)
                scan_plan = scan_class.generate_scan_plan(detectors=[self.point_det, self.ring_ma], gate=self.gate)
            else:
                scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det_flyer], gate=self.gate)
            # scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)

            if (scan_type == scan_types.GENERIC_SCAN):
                self.init_point_spectra(num_curves=1)
                scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_spectra)
            else:
                scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)

        elif (scan_type in _multispatial_types):
            line = True
            num_images_lst = self.determine_num_thumbnail_images_required(self.cur_wdg_com)
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5',
                                     stack_dir=False, num_desired_datafiles=len(sp_ids))
            idx = 0
            for sp_id in sp_ids:
                sp_db = sp_rois[sp_id]
                if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
                    # for point spec all spatial regions use same datafile but different entrys
                    self.assign_datafile_names_to_sp_db(sp_db, d[0], image_idx=0)
                else:
                    self.assign_datafile_names_to_sp_db(sp_db, d[idx], image_idx=idx)
                idx += 1

            #if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            if(scan_type in spectra_type_scans):
                # here I need to init it with the number of sp_ids (spatial points)
                self.init_point_spectra(num_curves=len(sp_ids))
                line = False

            self.set_cur_scan_sub_type(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE))
            scan_class.set_datafile_names_dict(d)
            #sept 1 sscan.set_spatial_id_list(sp_ids)
            sp_id = scan_class.get_next_spatial_id()
            scan_class.configure(self.cur_wdg_com, sp_id=sp_id, ev_idx=0, line=line)
            self.line_det.set_scan_type(scan_type)
            #scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det, self.ring_ma], gate=self.gate)
            if (scan_sub_type is scan_sub_types.POINT_BY_POINT):
                self.point_det.set_scan_type(scan_type)
                if(scan_class.e712_enabled):
                    if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
                        # use point detector
                        scan_plan = scan_class.generate_scan_plan(detectors=[self.point_det, self.ring_ma],
                                                                  gate=self.gate)
                    else:
                        #use the flyer scan because we are using the E712 wavegenerator
                        scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det_flyer], gate=self.gate)
                else:
                    #use point detector
                    scan_plan = scan_class.generate_scan_plan(detectors=[self.point_det, self.ring_ma], gate=self.gate)
            else:
                scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det_flyer], gate=self.gate)
            # scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)

            #if (scan_type == scan_types.GENERIC_SCAN):
            if (scan_type in spectra_type_scans):
                #self.init_point_spectra(num_curves=1)
                self.init_point_spectra(num_curves=len(sp_ids))
                scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_spectra)
            else:
                scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)

            if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
                self.lineByLineImageDataWidget.set_lock_aspect_ratio(False)

        elif (scan_type == scan_types.SAMPLE_IMAGE_STACK or scan_type == scan_types.TOMOGRAPHY or scan_type == scan_types.PATTERN_GEN):
            # use first sp_DB to determine if point by point or line unidir
            idx = 0
            img_idx_fname_dct = {}
            sp_db_seq_names = []
            for sp_id in sp_ids:
                sp_db = sp_rois[sp_id]
                #get num images for this sp_id
                num_images = self.determine_num_thumbnail_images_required(self.cur_wdg_com)[idx]
                d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5',
                                         num_desired_datafiles=num_images, new_stack_dir=True)
                sp_db_seq_names.append(d)
                d_keys = list(d.keys())
                if (len(sp_ids) > 1):
                    # each spatial roi needs a filename dict
                    for i in range(num_images):
                        k = d_keys[i]
                        self.assign_datafile_names_to_sp_db(sp_db, d[k], image_idx=i)
                else:
                    self.assign_datafile_names_to_sp_db(sp_rois[sp_ids[0]], d[0])
                #idx += 1

            self.set_cur_scan_sub_type(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE))
            scan_class.set_datafile_names_dict(d)
            sp_id = scan_class.get_next_spatial_id()
            scan_class.configure(self.cur_wdg_com, sp_id=sp_id, ev_idx=0, line=True)
            self.line_det.set_scan_type(scan_type)
            # scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det, self.ring_ma], gate=self.gate)
            if (scan_sub_type is scan_sub_types.POINT_BY_POINT):
                self.point_det.set_scan_type(scan_type)
                if (scan_class.e712_enabled):
                    # use the flyer scan because we are using the E712 wavegenerator
                    scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det_flyer], gate=self.gate)
                else:
                    # use point detector
                    scan_plan = scan_class.generate_scan_plan(detectors=[self.point_det], gate=self.gate)
            else:
                scan_plan = scan_class.generate_scan_plan(detectors=[self.line_det_flyer], gate=self.gate)

            if (scan_type == scan_types.PATTERN_GEN):
                scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)
            #now create a sequential list of image names in spatial id order
            cntr = 0
            for i in range(num_images):
                for j in range(len(sp_db_seq_names)):
                    stack_flbl = '%s img/%d' % (sp_db_seq_names[j][i]['data_name'], cntr)
                    sp_db_seq_names[j][i]['stack_flbl'] = stack_flbl
                    img_idx_fname_dct[cntr] = sp_db_seq_names[j][i]
                    cntr += 1

            d = img_idx_fname_dct

        elif (scan_type == scan_types.PTYCHOGRAPHY):
            sp_id = sp_ids[0]
            sp_db = sp_rois[sp_id]
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5',
                                     stack_dir=False, num_desired_datafiles=1)
            self.assign_datafile_names_to_sp_db(sp_db, d[0])
            # scan_class.set_spatial_id(sp_id)
            # scan_class.set_datafile_names_dict(d)
            # sept 1 sscan.set_spatial_id_list(sp_ids)
            scan_class.configure(self.cur_wdg_com, sp_id=sp_id, line=False)

            self.point_det.set_scan_type(scan_type)
            scan_plan = scan_class.generate_scan_plan(detectors=[self.point_det, self.ring_ma], gate=self.gate)
            # this should be something else here
            scan_class.init_subscriptions(MAIN_OBJ.engine_widget, self.add_point_to_plot)
        else:
            _logger.error('start_scan: unsupported scan type [%d]' % scan_type)
            self.set_buttons_for_starting()
            return

        #assign the scan plan to the engine
        MAIN_OBJ.engine_widget.engine.plan_creator = lambda: scan_plan
        #self.status_label = EngineLabel('Engine Status')
        #self.status_label.connect(MAIN_OBJ.engine_widget.engine)

        # MAIN_OBJ.engine_widget.engine.exec_result.connect(self.on_execution_completed)

        MAIN_OBJ.set('SCAN.CFG.WDG_COM', self.cur_wdg_com)

        # make sure all scans have set the data file names to their respective active data objects before allowing scan
        # to start
        if (not self.test_assign_datafile_names_to_sp_db(self.cur_wdg_com)):
            _logger.error('start_scan: incorrectly configured scan: data file names not assigned to active data object')
            self.set_buttons_for_starting()
            return

        # ok all good lets run the scan
        if (hasattr(self, 'scan_progress_table')):
            self.scan_progress_table.set_queue_file_list(get_thumb_file_name_list(d))
            #self.scan_progress_table.load_wdg_com(self.cur_wdg_com, sp_id)
            if (scan_type == scan_types.TOMOGRAPHY):
                #tomo only has one spatial ID yet there is one defined per angle, anly send one though
                self.scan_progress_table.load_wdg_com(self.cur_wdg_com, sorted([list(sp_rois.keys())[0]]))
            else:
                self.scan_progress_table.load_wdg_com(self.cur_wdg_com, sorted(list(sp_rois.keys())))

            if (scan_type == scan_types.SAMPLE_IMAGE_STACK):
                self.scan_progress_table.set_directory_label(d[list(d.keys())[0]]['stack_dir'])
            else:
                self.scan_progress_table.set_directory_label(d[list(d.keys())[0]]['data_dir'])

        self.connect_executingScan_signals(testing=testing)

        if(testing):
            self.executingScan.set_save_all_data(True)

        self.executingScan.image_started = False

        #testing starting new image from here instead of from the call to add_line/point_to_plot
        #self.on_image_start(self, wdg_com=None, sp_id=None):
        self.on_image_start(self.cur_wdg_com, sp_id=sp_id)

        self.start_time = time.time()

        # Start the RunEngine
        MAIN_OBJ.engine_widget.engine.md['user'] = 'bergr'
        MAIN_OBJ.engine_widget.engine.md['host'] = 'myNotebook'
        MAIN_OBJ.engine_widget.control.state_widgets['start'].clicked.emit()

    def get_data_as_array(self, hdr, strm_nm, det_nm, final_shape):
        '''

        :param hdr:
        :param strm_nm:
        :param final_shape:
        :return:
        '''
        strm_data = hdr.table(strm_nm)
        d = strm_data[det_nm]
        _1d_arr = np.array(d.get_values())
        num_vals, = _1d_arr.shape
        num_final_shape = final_shape[0] * final_shape[1]
        if(num_vals != num_final_shape):
            #aborted scan so needs to be padded
            _1d_arr.resize(num_final_shape, refcheck=False)
            final_arr = _1d_arr.reshape(final_shape)
        else:
            final_arr = _1d_arr.reshape(final_shape)
        return(final_arr)

    def on_run_engine_progress(self, re_prog_dct):
        #print(re_prog_dct)
        dct = make_progress_dict(sp_id=0, percent=re_prog_dct['prog'], cur_img_idx=re_prog_dct['scan_idx'])
        self.on_scan_progress(dct)

    def on_execution_completed(self, run_uids):
        print('on_execution_completed: ', run_uids)
        self.on_state_changed(MAIN_OBJ.engine_widget.engine.state, run_uids)

    def on_status_changed(self, state_str, style_sheet):
        self.scanActionLbl.setText(state_str)
        self.scanActionLbl.setStyleSheet(style_sheet)

    def on_state_changed(self, state_str, run_uids):
        '''
        fires when the RunEngine is done
        :param state_str:
        :return:
        '''
        print('on_state_changed: [%s]' % state_str)
        if (state_str.find('paused') > -1):
            pass
        elif(state_str.find('idle') > -1):
            self.executingScan.on_scan_done()
            self.executingScan.clear_subscriptions(MAIN_OBJ.engine_widget)
            self.disconnect_executingScan_signals()
            self.set_buttons_for_starting()

            # if(self.executingScan.scan_type is not scan_types.PATTERN_GEN):
            #     #fireoff a thread to handle saving data to an nxstxm file
            #     worker = Worker(self.do_data_export, run_uids, 'datadir', False)  # Any other args, kwargs are passed to the run function
            #     #worker.signals.result.connect(self.load_thumbs)
            #     #worker.signals.progress.connect(self.progress_fn)
            #     #worker.signals.finished.connect(self.thread_complete)
            #
            #     # Execute
            #     self._threadpool.start(worker)

            # fireoff a thread to handle saving data to an nxstxm file
            worker = Worker(self.do_data_export, run_uids, 'datadir', False)  # Any other args, kwargs are passed to the run function
            # Execute
            self._threadpool.start(worker)


    def check_data_export_good_to_go(self):
        '''
        check to see if we are going to have trouble saving when scan is done
        :return:
        '''
        from cls.utils.file_system_tools import get_next_file_num_in_seq
        data_dir = self.active_user.get_data_dir()
        fprefix = 'C' + str(get_next_file_num_in_seq(data_dir, extension='hdf5.tmp'))
        return(suit_nxstxm.test_can_do_tmp_file(data_dir, fprefix))

    def do_data_export(self, run_uids, datadir, is_stack_dir=False, progress_callback=None):
        '''
        executes inside a threadpool so it doesnt bog down the main event loop
        :return:CCDViewerPanel
        '''

        _logger.info('do_data_export: ok starting export')
        from cls.utils.file_system_tools import get_next_file_num_in_seq
        data_dir = self.active_user.get_data_dir()
        fprefix = 'C' + str(get_next_file_num_in_seq(data_dir, extension='hdf5'))

        scan_type = self.get_cur_scan_type()
        first_uid = run_uids[0]
        is_stack = False

        if (scan_type is scan_types.PATTERN_GEN):
            #we only want the information in the main
            first_uid = run_uids[4]
            run_uids = [first_uid]

        if(scan_type in [scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY]):
            #could also just be multiple rois on a single energy
            data_dir = os.path.join(data_dir, fprefix)
            is_stack = True
            self.do_multi_entry_export(run_uids, data_dir, fprefix)

        elif(scan_type in [scan_types.PTYCHOGRAPHY]):
        #could also just be multiple rois on a single energy
            data_dir = os.path.join(data_dir, fprefix)
            is_stack = True
            self.do_ptychography_export(run_uids, data_dir, fprefix)
            suit_nxptycho.finish_export(data_dir, fprefix, first_uid)
            return

        #elif(scan_type is scan_types.SAMPLE_POINT_SPECTRUM):
        elif (scan_type in spectra_type_scans):
            self.do_point_spec_export(run_uids, data_dir, fprefix)

        else:
            img_idx_map = {}
            idx = 0
            for _uid in run_uids:
                print('starting basic export [%s]' % first_uid)
                header = MAIN_OBJ.engine_widget.db[first_uid]
                md = json.loads(header['start']['metadata'])
                _img_idx_map = json.loads(md['img_idx_map'])
                #img_idx_map[uid] = copy.copy(_img_idx_map['%d' % 0])
                primary_docs = header.documents(fill=True)
                # suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0, rev_lu_dct=MAIN_OBJ.get_device_reverse_lu_dct(), \
                #                 img_idx_map=_img_idx_map['0'], first_uid=uid, last_uid=_uid)
                #suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, first_uid=first_uid)
                suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, first_uid=first_uid)
        #suit_nxstxm.finish_export(data_dir, fprefix, first_uid, is_stack_dir=is_stack)
        suit_nxstxm.finish_export(data_dir, fprefix, first_uid)

    def get_counter_from_table(self, tbl, prime_cntr):
        for k in list(tbl.keys()):
            if(k.find(prime_cntr) > -1):
                return(k)
        return(None)


    def do_point_spec_export(self, run_uids, data_dir, fprefix):
        '''
        Point spec data is executed as a single run_uid, export is as an nxstxm entry
        :param run_uids:
        :param data_dir:
        :param fprefix:
        :return:
        '''
        #grab metadata from last run
        header = MAIN_OBJ.engine_widget.db[-1]
        md = json.loads(header['start']['metadata'])
        _img_idx_map = json.loads(md['img_idx_map'])
        img_idx_map = {}
        idx = 0
        first_uid = run_uids[0]
        print('starting point_spec export [%s]' % first_uid)
        header = MAIN_OBJ.engine_widget.db[first_uid]
        primary_docs = header.documents(fill=True)
        # suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0,
        #                        rev_lu_dct=MAIN_OBJ.get_device_reverse_lu_dct(), img_idx_map=_img_idx_map, \
        #                        first_uid=first_uid, last_uid=uid)
        suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, first_uid=first_uid)


    def do_multi_entry_export(self, run_uids, data_dir, fprefix):
        '''
        walk through a list of run_uids and export them as nxstxm entry's
        :param run_uids:
        :param data_dir:
        :param fprefix:
        :return:
        '''
        #grab metadata from last run
        header = MAIN_OBJ.engine_widget.db[-1]
        md = json.loads(header['start']['metadata'])
        _img_idx_map = json.loads(md['img_idx_map'])
        img_idx_map = {}
        idx = 0
        for uid in run_uids:
            if(idx is 0):
                first_uid = uid
            #img_idx_map['%d'%idx]['uid'] = uid
            #img_idx_map[uid] = copy.copy(_img_idx_map['%d'%idx])
            idx += 1
        last_uid = uid
        idx = 0
        print('starting multi_entry export [%s]' % uid)
        for uid in run_uids:
            #export each uid as an nxstxm entry
            header = MAIN_OBJ.engine_widget.db[uid]
            primary_docs = header.documents(fill=True)
            # #suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0,
            #                    rev_lu_dct=MAIN_OBJ.get_device_reverse_lu_dct(), img_idx_map=_img_idx_map['%d'%idx], \
            #                    first_uid=first_uid, last_uid=last_uid)
            if(not os.path.exists(data_dir)):
                os.makedirs(data_dir)
            suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, first_uid=first_uid)
            idx += 1

    def do_ptychography_export(self, run_uids, data_dir, fprefix):
        '''
        walk through a list of run_uids and export them as nxstxm entry's
        :param run_uids:
        :param data_dir:
        :param fprefix:
        :return:
        '''
        #grab metadata from last run
        header = MAIN_OBJ.engine_widget.db[-1]
        md = json.loads(header['start']['metadata'])
        _img_idx_map = json.loads(md['img_idx_map'])
        img_idx_map = {}
        idx = 0
        for uid in run_uids:
            if(idx is 0):
                first_uid = uid
            #img_idx_map['%d'%idx]['uid'] = uid
            #img_idx_map[uid] = copy.copy(_img_idx_map['%d'%idx])
            idx += 1
        last_uid = uid
        idx = 0
        print('starting multi_entry export [%s]' % uid)
        for uid in run_uids:
            #export each uid as an nxstxm entry
            header = MAIN_OBJ.engine_widget.db[uid]
            primary_docs = header.documents(fill=True)

            if(not os.path.exists(data_dir)):
                os.makedirs(data_dir)
            suit_nxptycho.export(primary_docs, data_dir, file_prefix=fprefix, first_uid=first_uid)
            idx += 1

    def call_do_post_test(self):
        '''
        create a dict of hte data to check
        :return:
        '''
        time.sleep(0.5)
        dct = {}
        data_dnames_dct = self.executingScan.get_datafile_names_dict()
        scan_pluggin = self.scan_tbox_widgets[self.scan_panel_idx]
        res = scan_pluggin.do_post_test(data_dnames_dct)

        if(res):
            _logger.info('Test succeeded')
        else:
            _logger.info('Test Failed')

    def init_point_spectra(self, sp_id=-1, num_curves=1):
        """
        init_point_spectra(): description

        :param sp_id=-1: sp_id=-1 description
        :type sp_id=-1: sp_id=-1 type

        :returns: None
        """

        self.spectraWidget.clear_plot()

        sp_ids = list(self.cur_sp_rois.keys())

        if(len(sp_ids) == 1):
            use_dflt = True
        else:
            use_dflt = False

        for sp_id in sp_ids:
            # self.spectraWidget.create_curve('point_spectra_%d' % i,curve_style='Lines')
            clr = get_next_color(use_dflt=use_dflt)
            style = get_basic_line_style(clr, marker='Star1')
            self.spectraWidget.create_curve('sp_id_%d' % sp_id, curve_style=style)


    def is_add_line_to_plot_type(self, scan_type, scan_sub_type, use_hdw_accel):
        '''
        a single function to decide if the scan type is the kind that adds a line to a plot
        :param scan_type:
        :param scan_sub_type:
        :param use_hdw_accel:
        :return:
        '''

        if ((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
                    ((scan_type == scan_types.SAMPLE_IMAGE) and (
                        scan_sub_type == scan_sub_types.POINT_BY_POINT) and use_hdw_accel) or \
                        (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (
                        scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
                        (scan_type == scan_types.TOMOGRAPHY) and (
                                scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
                    (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (
                        scan_sub_type == scan_sub_types.POINT_BY_POINT) or \
                        (scan_type == scan_types.SAMPLE_LINE_SPECTRUM) and (
                        scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
                        ((scan_type == scan_types.SAMPLE_LINE_SPECTRUM) and (
                                    scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                        (scan_type == scan_types.SAMPLE_FOCUS) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) ):
            return(True)
        elif(scan_type == scan_types.COARSE_IMAGE):
            return (True)
        else:
            return(False)


    def is_add_point_to_plot_type(self, scan_type, scan_sub_type, use_hdw_accel):
        '''
        a single function to decide if the scan type is the kind that adds a point to a 2d plot
        :param scan_type:
        :param scan_sub_type:
        :param use_hdw_accel:
        :return:
        '''
        if ((scan_type == scan_types.DETECTOR_IMAGE) or \
                    ((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.POINT_BY_POINT) and (
                    not use_hdw_accel)) or \
                    (scan_type == scan_types.OSA_IMAGE) or \
                    (scan_type == scan_types.OSA_FOCUS) or \
                    #((scan_type == scan_types.SAMPLE_LINE_SPECTRUM) and (
                    #            scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                    (scan_type == scan_types.SAMPLE_FOCUS) or \
                    (scan_type == scan_types.COARSE_IMAGE) or \
                    (scan_type == scan_types.COARSE_GONI) or \
                    (scan_type == scan_types.PATTERN_GEN)):
            return(True)
        else:
            return(False)

    def is_add_point_to_spectra_type(self, scan_type, scan_sub_type, use_hdw_accel):
        '''
        a single function to decide if the scan type is the kind that adds a point to a line  plot
        :param scan_type:
        :param scan_sub_type:
        :param use_hdw_accel:
        :return:
        '''
        if ((scan_type == scan_types.SAMPLE_POINT_SPECTRUM) or \
                    (scan_type == scan_types.GENERIC_SCAN)):
            return(True)
        else:
            return(False)


    def connect_executingScan_signals(self, testing=False):
        """
        connect_executingScan_signals(): description

        :returns: None
        """
        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()
        sp_db = self.executingScan.sp_db
        use_hdw_accel = dct_get(sp_db, SPDB_HDW_ACCEL_USE)

        _logger.debug('GUI: connect_executingScan_signals')
        if (self.is_add_line_to_plot_type(scan_type, scan_sub_type, use_hdw_accel)):
            reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed, self.add_line_to_plot)
            reconnect_signal(self.line_det.sigs, self.line_det.sigs.changed, self.add_line_to_plot)

            if (not (scan_type == scan_types.SAMPLE_LINE_SPECTRUM)):
                # dont connect this for line_spec scans because the data level is energy which would cause a
                # new image for each energy line which is not what we want
                if(not use_hdw_accel):
                    reconnect_signal(self.executingScan, self.executingScan.data_start,
                                          self.on_image_start)
                #just skip this signal if using hdw_accel because the on_image_start() will be called when the plotter updates

        elif(self.is_add_point_to_plot_type(scan_type, scan_sub_type, use_hdw_accel)):
            reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed, self.add_point_to_plot)

            if (not (scan_type == scan_types.SAMPLE_LINE_SPECTRUM)):
                # dont connect this for line_spec scans because the data level is energy which would cause a
                # new image for each energy line which is not what we want
                reconnect_signal(self.executingScan, self.executingScan.data_start, self.on_image_start)


        elif (self.is_add_point_to_spectra_type(scan_type, scan_sub_type, use_hdw_accel)):
            reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed, self.add_point_to_spectra)
        else:
            _logger.error('connect_executingScan_signals: executingScan type [%d] not supported', scan_type)

        reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.status, self.on_scan_status)
        reconnect_signal(self.scan_progress_table, self.scan_progress_table.total_prog, self.on_total_scan_progress)
        reconnect_signal(self.executingScan, self.executingScan.low_level_progress, self.on_scan_progress)
        reconnect_signal(self.executingScan, self.executingScan.sigs_disconnected, self.on_executing_scan_sigs_discon)
        reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.aborted, self.on_scan_done)
        reconnect_signal(self.executingScan, self.executingScan.all_done, self.on_scan_done)

        if (testing):
            _logger.debug('connecting self.call_do_post_test to self.executingScan.all_done')
            reconnect_signal(self.executingScan, self.executingScan.all_done, self.call_do_post_test)

        reconnect_signal(self.executingScan, self.executingScan.saving_data, self.on_saving_data)

        # _logger.debug('executingScan signals connected')

    def disconnect_executingScan_signals(self):
        """
        disconnect_executingScan_signals(): description

        :returns: None
        """
        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()
        sp_db = self.executingScan.sp_db
        use_hdw_accel = dct_get(sp_db, SPDB_HDW_ACCEL_USE)
        _logger.debug('disconnect_executingScan_signals: TOP')
        if (self.is_add_line_to_plot_type(scan_type, scan_sub_type, use_hdw_accel)):
            disconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed)

            if (not (scan_type == scan_types.SAMPLE_LINE_SPECTRUM)):
                if(not use_hdw_accel):
                    disconnect_signal(self.executingScan, self.executingScan.data_start)

        elif (self.is_add_point_to_plot_type(scan_type, scan_sub_type, use_hdw_accel)):
            disconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed)

            if (not (scan_type == scan_types.SAMPLE_LINE_SPECTRUM)):
                disconnect_signal(self.executingScan, self.executingScan.data_start)

        elif (self.is_add_point_to_spectra_type(scan_type, scan_sub_type, use_hdw_accel)):
            disconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed)

        else:
            _logger.error('disconnect_executingScan_signals: executingScan type [%d] not supported', scan_type)

        disconnect_signal(self.executingScan.sigs, self.executingScan.sigs.progress)
        disconnect_signal(self.executingScan, self.executingScan.top_level_progress)
        disconnect_signal(self.executingScan, self.executingScan.low_level_progress)
        disconnect_signal(self.executingScan, self.executingScan.sigs_disconnected)
        disconnect_signal(self.executingScan.sigs, self.executingScan.sigs.aborted)
        disconnect_signal(self.executingScan, self.executingScan.all_done)
        disconnect_signal(self.executingScan, self.executingScan.saving_data)
        disconnect_signal(self.executingScan, self.executingScan.all_done)

        self._set_scan_btns.emit('SET_FOR_STARTING')
        self.on_scan_status('idle')

    def on_saving_data(self, msg):
        self.scanActionLbl.setText(msg)
        #_logger.info('%s' % msg)

    def on_image_start(self, wdg_com=None, sp_id=None):
        """
        on_image_start(): called when a new image  starts

        :param wdg_com=None: wdg_com=None description
        :type wdg_com=None: wdg_com=None type

        :returns: None
        """
        # on_image_start can be called by singal passed from scan with the wdg_com as the arg
        #print 'on_image_start called'
        #_logger.debug('on_image_start called')
        #set these as defaults
        self.reset_image_plot()
        self.lineByLineImageDataWidget.set_lock_aspect_ratio(True)
        self.lineByLineImageDataWidget.set_fill_plot_window(False)
        # default img_idx is 0
        img_idx = 0
        if (wdg_com is None):
            # use current
            wdg_com = self.cur_wdg_com

        if(sp_id is None):
            #print 'on_image_start: sp_id is NONE'
            sp_id = self.executingScan.get_spatial_id()

        #print 'on_image_start: using sp_id=%d' % sp_id

        if (sp_id not in list(wdg_com[WDGCOM_SPATIAL_ROIS].keys())):
            _logger.error('Spatial ID [%d] does not exist in widget communication dict, using wdg_com from executingScan' % sp_id)
            wdg_com = self.executingScan.wdg_com
            if(wdg_com is not None):
                sp_id = self.executingScan.get_spatial_id()

        sp_db = wdg_com[WDGCOM_SPATIAL_ROIS][sp_id]
        scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)

        # hack
        if (self.executingScan.image_started == True):
            self.executingScan.image_started = False

        if (self.executingScan.image_started == False):

            numX = dct_get(sp_db, SPDB_XNPOINTS)
            numY = dct_get(sp_db, SPDB_YNPOINTS)
            numZ = dct_get(sp_db, SPDB_ZNPOINTS)
            numZ = dct_get(sp_db, SPDB_ZZNPOINTS)
            # img_parms = dct_get(wdg_com, 'CURRENT.SCAN.IMAGE_PARMS')
            rect = dct_get(sp_db, SPDB_RECT)
            numE = dct_get(sp_db, SPDB_EV_NPOINTS)
            x_roi = sp_db['X']
            y_roi = sp_db['Y']

            # _logger.info('on_image_start: rois (%.2f, %.2f, %.2f, %.2f)' % (x_roi[START], y_roi[START], x_roi[STOP], y_roi[STOP]))
            # _logger.debug('GUI: on_image_start')
            if (scan_type == scan_types.SAMPLE_FOCUS):
                self.lineByLineImageDataWidget.initData(img_idx, image_types.FOCUS, numZ, numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)

            elif (scan_type == scan_types.OSA_FOCUS):
                # osa focus scan only sits at a single Y position and so will be a square (equal to num x points)
                self.lineByLineImageDataWidget.initData(img_idx, image_types.OSAFOCUS, numZ, numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)

            elif (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
                setpoints = []
                ev_npts_stpts_lst = []
                for i in range(len(self.executingScan.e_rois)):
                    num_e_rois = len(self.executingScan.e_rois)
                    e_roi = self.executingScan.e_rois[i]
                    xpnts = self.executingScan.x_roi[NPOINTS]
                    ypnts = self.executingScan.y_roi[NPOINTS]
                    enpts = int(e_roi[NPOINTS])
                    stpts = e_roi[SETPOINTS]
                    #create a list entry of (npts, start, stop)
                    ev_npts_stpts_lst.append((enpts,stpts[0], stpts[-1]))
                    setpoints += list(stpts)
                    self.lineByLineImageDataWidget.initData(i, image_types.LINE_PLOT, xpnts, enpts)
                    self.lineByLineImageDataWidget.set_image_parameters(i, stpts[0], 0, stpts[-1], xpnts)

                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)
                self.lineByLineImageDataWidget.set_fill_plot_window(True)
                #dct = self.lineByLineImageDataWidget.determine_num_images(ev_npts_stpts_lst, xpnts)
                #self.executingScan.linescan_seq_map_dct = dct

            else:
                #_logger.info('on_image_start: calling initData()')

                self.lineByLineImageDataWidget.initData(img_idx, image_types.IMAGE, numY, numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=False)

            self.executingScan.image_started = True

    def on_spectra_start(self):
        """
        on_spectra_start(): description

        :returns: None
        """
        _logger.debug('on_spectra_start')
        self.spectraWidget.clear_plot()


    def on_scan_done(self):
        """
        on_scan_done(): description

        :returns: None
        """
        # idx = self.executingScan.get_imgidx()
        _logger.debug('GUI: scan completed')

        self.set_buttons_for_starting()
        # self.scan_progress_table.set_pixmap(self.cur_image_idx, scan_status_types.DONE)

    def on_executing_scan_sigs_discon(self):
        """
        on_executing_scan_sigs_discon(): description

        :returns: None
        """
        _logger.debug('GUI: on_executing_scan_sigs_discon')
        if (MAIN_OBJ.device(DNM_SHUTTER).is_auto()):
            MAIN_OBJ.device(DNM_SHUTTER).close()
        # _logger.info('scan completed')
        # self.curImgProgBar.setValue(0.0)
        self.totalProgBar.setValue(0.0)

        self.lineByLineImageDataWidget.set_lock_aspect_ratio(True)
        if (self.executingScan is not None):
            self.disconnect_executingScan_signals()

    def secondsToStr(self, t):
        """
        secondsToStr(): description

        :param t: t description
        :type t: t type

        :returns: None
        """
        # rediv = lambda ll,b : list(divmod(ll[0],b)) + ll[1:]
        # return "%d:%02d:%02d" % tuple(reduce(rediv,[[t*1000,], 1000,60]))
        # return "%d:%02d:%02d" % tuple(reduce(rediv,[[t*1000,], 1000,60]))
        # elapsed_sec = end_time - begin_time
        return (strftime("%H:%M:%S", gmtime(t)))


    def check_time(self, cur_scan_progress):
        """
         check_time(): description

        :param cur_scan_progress: cur_scan_progress description
        :type cur_scan_progress: cur_scan_progress type

        :returns: None
        """
        return
        # if (cur_scan_progress < 1.0):
        #     cur_scan_progress = 1
        # if (self.start_time is None):
        #     self.start_time = time.time()
        # self.elapsed_time = time.time() - self.start_time
        # time_left = ((100.0 / cur_scan_progress) * self.elapsed_time) - self.elapsed_time
        # # cs_sts['elapsed_time'] = self.secondsToStr(self.elapsed_time)
        # self.elapsedTimeLbl.setText(self.secondsToStr(self.elapsed_time))
        # # cs_sts['time_left'] = self.secondsToStr(time_left)
        # self.timeLeftLbl.setText(self.secondsToStr(time_left))


    def on_new_est_scan_time(self, xxx_todo_changeme):
        (sec, est_time_str) = xxx_todo_changeme
        self.timeLeftLbl.setText(est_time_str)

    def on_scan_status(self, msg):
        """
        on_scan_status(): description

        :param msg: msg description
        :type msg: msg type

        :returns: None
        """
        s = copy.copy(msg)
        _logger.debug('scanActionLbl: %s' % msg)
        self.scanActionLbl.setText(msg)
        scanning_ss = '#scanActionLbl {	font: 75 8pt "MS Shell Dlg 2"; font-weight: bold; color: black; background-color: rgb(235, 235, 0);}'
        idle_ss = '#scanActionLbl { font: 75 8pt "MS Shell Dlg 2"; font-weight: bold; color: white; background-color: transparent; }'

        if((s.find('Complete') > -1) or (s.find('Idle') > -1) or (s.find('idle') > -1)):
            self.scanActionLbl.setStyleSheet(idle_ss)
        else:
            self.scanActionLbl.setStyleSheet(scanning_ss)


    def set_cur_scan_type(self, type):
        self._scan_type = type


    def set_cur_scan_sub_type(self, type):
        self._scan_sub_type = type


    def get_cur_scan_type(self):
        return (self._scan_type)


    def get_cur_scan_sub_type(self):
        return (self._scan_sub_type)


    def on_scan_progress(self, prog_dct):
        """
        on_scan_progress(): a signal handler that fires when the progress pv's have been updated, here clip the top of the scan
        percentage at >= 90.0, if >= 90.0 just set it to %100

        :param percent: percent description
        :type percent: percent type

        :returns: None
        """
        sp_id = int(dct_get(prog_dct, PROG_DCT_SPID))
        percent = dct_get(prog_dct, PROG_DCT_PERCENT)
        cur_img_idx = int(dct_get(prog_dct, PROG_CUR_IMG_IDX))
        prog_state = dct_get(prog_dct, PROG_DCT_STATE)

        if (self.get_cur_scan_type() is not scan_types.SAMPLE_IMAGE_STACK):
            # set_pixmap = self.scan_progress_table.set_pixmap_by_spid
            # set_progress = self.scan_progress_table.set_progress_by_spid
            set_pixmap = self.scan_progress_table.set_pixmap
            set_progress = self.scan_progress_table.set_progress
            id = sp_id
        else:
            # its a stack
            set_pixmap = self.scan_progress_table.set_pixmap
            set_progress = self.scan_progress_table.set_progress
            id = sp_id

        if (percent >= 98.0):
            percent = 100.0

        set_progress(cur_img_idx, percent)

        if (percent >= 100.0):
            #set_pixmap(id, scan_status_types.DONE)
            set_pixmap(cur_img_idx, scan_status_types.DONE)
        elif (percent < 100.0):
            #set_pixmap(id, scan_status_types.RUNNING)
            set_pixmap(cur_img_idx, scan_status_types.RUNNING)
        else:
            #set_pixmap(id, scan_status_types.STOPPED)
            set_pixmap(cur_img_idx, scan_status_types.STOPPED)

        self.check_time(percent)
        #print 'on_scan_progress DONE:'


    def on_total_scan_progress(self, percent):
        """
        on_total_scan_progress(): description

        :param percent: percent description
        :type percent: percent type

        :returns: None
        """
        return
        # print 'on_total_scan_progress: %.2f' % percent
        # self.totalProgBar.setValue(percent)
        # self.scan_progress_table.set_progress(self.cur_image_idx, percent)
        self.totalProgBar.setValue(percent)


    def on_pause(self, chkd):
        """
        on_pause(): description

        :param chkd: chkd description
        :type chkd: chkd type

        :returns: None
        """

        if (self.executingScan):
            # idx = self.executingScan.get_imgidx()
            idx = self.executingScan.get_consecutive_scan_idx()
            if (chkd):
                #self.executingScan.pause()
                if (hasattr(self, 'scan_progress_table')):
                    self.scan_progress_table.set_pixmap(idx, scan_status_types.PAUSED)
                # request a pause
                MAIN_OBJ.engine_widget.control.state_widgets['pause'].clicked.emit()
            else:
                #self.executingScan.resume()
                # request a pause
                if (hasattr(self, 'scan_progress_table')):
                    self.scan_progress_table.set_pixmap(idx, scan_status_types.RUNNING)
                MAIN_OBJ.engine_widget.control.state_widgets['resume'].clicked.emit()

    def on_stop(self):
        """
        on_stop(): description

        :returns: None

        """
        self.on_shutterCntrlComboBox(0)  # Auto
        self.set_buttons_for_starting()
        if (self.executingScan):
            # idx = self.executingScan.get_imgidx()
            idx = self.executingScan.get_consecutive_scan_idx()
            self.executingScan.stop()
            if (hasattr(self, 'scan_progress_table')):
                self.scan_progress_table.set_pixmap(idx, scan_status_types.ABORTED)
            self.stopping = True
            #self.executingScan.disconnect_signals()

            # stop
            #MAIN_OBJ.engine_widget.control.state_widgets['stop'].clicked.emit()
            MAIN_OBJ.engine_widget.control.on_stop_clicked()

    def on_exit(self):
        """
        on_exit(): description

        :returns: None
        """
        #print 'on_exit: called'
        _logger.debug('Main GUI: on_exit')
        MAIN_OBJ.cleanup()



def import_devices():
    from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES

def go():
    """
        go(): description

        :param go(: go( description
        :type go(: go( type

        :returns: None
    """
    app = QtWidgets.QApplication(sys.argv)
    from cls.appWidgets.splashScreen import get_splash, del_splash

    def clean_up():
        MAIN_OBJ.cleanup()

    # ca.threads_init()
    #from cls.appWidgets.splashScreen import SplashScreen

    debugger = sys.gettrace()

    splash = get_splash()
    sys.excepthook = excepthook
    if(debugger is None):
        pystxm_win = pySTXMWindow(exec_in_debugger=False)
    else:
        pystxm_win = pySTXMWindow(exec_in_debugger=True)

    didit = splash.close()
    del_splash()

    app.aboutToQuit.connect(clean_up)
    pystxm_win.show()

    try:
        #starts event loop
        try:
            sys.exit(app.exec_())
        except:
            print("Exiting")
            exit()
    except:
        print("Exiting")


# app.exec_()


# if __name__ == '__main__':
#     import profile
#     import pstats
#     
#     ca.threads_init()
#     #motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
#     app = QtWidgets.QApplication(sys.argv)
#     
#     #log_to_qt()
#     absMtr = pySTXMWindow()
#     absMtr.show()
#     sys.exit(app.exec_())

def determine_profile_bias_val():
    """
        determine_profile_bias_val(): description

        :param determine_profile_bias_val(: determine_profile_bias_val( description
        :type determine_profile_bias_val(: determine_profile_bias_val( type

        :returns: None
    """
    pr = profile.Profile()
    v = 0
    v_t = 0
    for i in range(5):
        v_t = pr.calibrate(100000)
        v += v_t
        print(v_t)

    bval = v / 5.0
    print('bias val = ', bval)
    profile.Profile.bias = bval
    return bval


def profile_it():
    """
        profile_it(): description

        :param profile_it(: profile_it( description
        :type profile_it(: profile_it( type

        :returns: None
    """

    bval = determine_profile_bias_val()

    profile.Profile.bias = 1.36987840635e-05

    profile.run('go()', 'testprof.dat')

    p = pstats.Stats('testprof.dat')
    p.sort_stats('cumulative').print_stats(100)


if __name__ == '__main__':
    import profile
    import pstats

    # motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
    # app = QtWidgets.QApplication(sys.argv)
    go()
    #profile_it()

    # test()
    # app = QtWidgets.QApplication(sys.argv)

    # pystxm_win = pySTXMWindow()
    # sys.excepthook = excepthook
    # pystxm_win.show()

    # try:
    # sys.exit(app.exec_())
    # except:
    #    sys.excepthook(*sys.exc_info())
