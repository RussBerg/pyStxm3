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
import traceback
import time
import datetime
from time import mktime, strftime, strptime, gmtime
import sys, os
import glob
import numpy as np
import queue
import atexit
import copy

from PyQt5 import QtCore, QtGui, uic, QtWidgets
from guiqwt.config import _
from threading import Lock
import copy

from yapsy.PluginManager import PluginManager

import cls.applications.bioXasIM.setup_env


from cls.applications.bioXasIM import abs_path_to_ini_file
from cls.applications.bioXasIM.bioxas_user import usr_acct_manager

from cls.appWidgets.thumbnailViewer import ContactSheet

from cls.data_io.bioxas_im_data_io import BioxasDataIo

from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.cfgparser import ConfigClass
from cls.utils.roi_utils import widget_com_cmnd_types, get_first_sp_db_from_wdg_com, reset_unique_roi_id
from cls.utils.file_system_tools import master_get_seq_names, get_thumb_file_name_list

from cls.plotWidgets.imageWidget import ImageWidget
from cls.plotWidgets.striptool.stripToolWidget import StripToolWidget
from cls.plotWidgets.curveWidget import CurveViewerWidget, get_next_color, get_basic_line_style
from cls.plotWidgets.utils import *


from cls.scanning.BaseScan import LOAD_ALL
from cls.scanning.dataRecorder import HdrData
from cls.scanning.types import image_types, scan_types, scan_panel_order, scan_sub_types, \
                                        spatial_type_prefix, energy_scan_order_types, sample_fine_positioning_modes,\
                                        sample_positioning_modes, scan_status_types, endstation_id_types
from cls.scanning.base import ScanParamWidget
from cls.caWidgets.caLabelWidget import ca_aiLabelWidget, ca_mbbiLabelWidget, ca_strLabel, ca_biLabelWidget

from cls.appWidgets.user_account.login import loginWidget
#from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
from cls.app_data.defaults import  master_colors, get_style, rgb_as_hex

from cls.applications.bioXasIM.widgets.motorPanel import PositionersPanel
from cls.applications.bioXasIM.widgets.pvDisplayPanel import PVsPanel
from cls.applications.bioXasIM.widgets.detectorsPanel import DetectorsPanel

from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES
from cls.applications.bioXasIM.widgets.scan_queue_table import ScanQueueTableWidget

from cls.applications.bioXasIM.device_names import *

#from bcm.epics.devices import scan
from bcm.devices.base import BaseDevice
from bcm.epics_devices_MOVED.scan import Scan



#read the ini file and load the default directories
appConfig = ConfigClass(abs_path_to_ini_file)
scanPluginDir = appConfig.get_value('DEFAULT', 'scanPluginDir')
major_version = appConfig.get_value('DEFAULT', 'major_version')
minor_version = appConfig.get_value('DEFAULT', 'minor_version')
uiDir = appConfig.get_value('DEFAULT', 'uiDir')

sample_pos_mode = appConfig.get_value('DEFAULT', 'sample_positioning_mode')
sample_finepos_mode = appConfig.get_value('DEFAULT', 'fine_sample_positioning_mode')

if(sample_pos_mode.find('COARSEXY') > -1):
    sample_pos_mode = sample_positioning_modes.COARSE
elif(sample_pos_mode.find('GONIOMETER') > -1):
    sample_pos_mode = sample_positioning_modes.GONIOMETER
else:
    sample_pos_mode = sample_positioning_modes.COARSE

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

active_user = None

PLOTTER_IMAGES_TAB = 0
PLOTTER_SPECTRA_TAB = 1

NUM_POINTS_LOST_AFTER_EDIFF = 2
DATA_OFFSET = 1


hostname = os.getenv('COMPUTERNAME')
if(hostname == 'WKS-W001465'):
    #the new test computer in old magnet mapping room
    FAKE_MARKER=False
    UNIT_SCALAR = 0.001
    #VELO_SCALAR = 1
    #VELO_SCALAR = 0.001
    VELO_SCALAR = 1000.0
    USE_PIEZO = True
elif(hostname == 'NBK-W001021'):
    #my notebook computer
    FAKE_MARKER=True
    UNIT_SCALAR = 1.0
    USE_PIEZO = False
else:
    #the old stxm_control conmputer
    FAKE_MARKER = False
    UNIT_SCALAR = 0.001
    VELO_SCALAR = 0.001
    USE_PIEZO = True


##############################################################################################################
##############################################################################################################
class bioxasMWindow(QtWidgets.QMainWindow):
    '''
    classdocs
    '''
    _set_scan_btns = QtCore.pyqtSignal(object)
    #_check_for_another_scan = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        """
        __init__(): description

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        super(bioxasMWindow, self).__init__(parent)
        uic.loadUi(uiDir + '/scanDetails-mainWindow-plugins-dark.ui', self)
        self.setWindowTitle('pyBioXas %s.%s Canadian Light Source Inc. %s' % (MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'),  MAIN_OBJ.get('APP.DATE')))

        atexit.register(self.on_exit)
        self.setGeometry(10,100,1900,1300)
        self.qssheet = get_style('dark')
        #self.setStyleSheet(self.qssheet)
        #self.apply_stylesheet(self.centralwidget, self.qssheet)

        auto_login = True
        self.loginWdgt = loginWidget(usr_acct_manager, auto_login=auto_login)
        if(auto_login):
            self.active_user = self.loginWdgt.get_user_obj()
            print('%s succesful logged in' % self.active_user.get_username())
            print('Active user data dir : %s' % self.active_user.get_data_dir())

        MAIN_OBJ.set('APP.USER', self.active_user)

        try:
            self.log = log_to_qt()
            #connect logger
            self.log.new_msg.connect(self.add_to_log)

            self.updateStyleBtn.clicked.connect(self.on_update_style)
            #self.scanTypeToolBox.currentChanged.connect(self.on_toolbox_changed)

            self._set_scan_btns.connect(self.on_set_scan_btns)
            #self._check_for_another_scan.connect(self.check_for_more_ev_regions)
            self.single_energy = True

            self.data = []
            self.rvrsddata = []
            self.scan_tbox_widgets = []

            self.scan_in_progress = False
            self.image_started = False

            self.setup_main_gui()
            self.setup_image_plot()
            self.setup_spectra_plot()

            #self.shutterFbkLbl = ca_biLabelWidget(MAIN_OBJ.device(DNM_SHUTTER).get_name(), labelWidget=self.shutterFbkLbl , hdrText=DNM_SHUTTER,title_color='white', options= dict(state_clrs=['black','blue']))
            self.status_dict = {}

            if(LOAD_ALL):
                self.init_statusbar()

            self.scan = None
            self.dwell = 0

            # a variable to hold the list of ev_rois for current scan
            self.ev_rois = None
            self.cur_ev_idx = 0
            self.cur_sp_rois = {}
            #self.e_roi_queue = Queue.Queue()

            self.ySetpoints = None
            self.xSetpoints = None
            self.npointsX = 0
            self.npointsY = 0

            self.accRange = 0
            self.dccRange = 0
            self.executingScan = None

            self.stopping = False

            self.init_all_scans()

            self.set_buttons_for_starting()

            self.previousScanType = None

            self.setup_scan_toolbox()
            self.scan_panel_idx = self.scanTypeToolBox.currentIndex()
            #self.scan_tbox_widgets[self.scan_panel_idx].set_zp_focus_mode()
            self._scan_type = self.scan_tbox_widgets[self.scan_panel_idx].type
            self._scan_sub_type = self.scan_tbox_widgets[self.scan_panel_idx].sub_type

            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.on_update_style)
            self.timer.start(100)

            #self.start_epics_tasks()
            #self.setup_info_dock()
            self.loadImageDataBtn.clicked.connect(self.load_simulated_image_data)
        except:
            traceback.print_exc()

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
        MAIN_OBJ.device(DNM_SHUTTERTASKRUN).put(1)


    def on_update_style(self):
        """
        on_update_style(): description

        :returns: None
        """
        """ handler for interactive button """
        self.timer.stop()
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)
        self.apply_stylesheet(self.centralwidget, self.qssheet)
        self.update_plot_colors()


    def update_plot_colors(self):
        """
        update_plot_colors(): description

        :returns: None
        """
        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

        self.evScanplot.set_grid_parameters(bg_clr, min_clr, maj_clr)
        self.lineByLineImageDataWidget.set_grid_parameters(bg_clr, min_clr, maj_clr)
        self.lineByLineImageDataWidget.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)
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
        #for some reason the stysheet isnt picked up by the central widget and centralFrame so force it here
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
        if(clr is not None):
            self.logWindow.setTextColor(clr)
        self.logWindow.append(msg)


    def load_dir_view(self):
        """
        load_dir_view(): description

        :returns: None
        """
        self.dir_model = QtWidgets.QFileSystemModel()
        self.dir_model.setRootPath( QtCore.QDir.currentPath() )

        #self.dir_model.setRootPath( QtCore.QString(MAIN_OBJ.get_session_info().get_data_dir()) )
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
        if(do_what == 'SET_FOR_SCANNING'):
            self.set_buttons_for_scanning()
        elif(do_what == 'SET_FOR_STARTING'):
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
        #self.stopBtn.setEnabled(True)
        self.pauseBtn.setEnabled(True)
        self.scansFrame.setEnabled(False)
        #self.scan_tbox_widgets[self.scan_panel_idx].set_read_only()
        self.lineByLineImageDataWidget.set_enable_drop_events(False)

    def set_buttons_for_starting(self):
        """
        set_buttons_for_starting(): description

        :returns: None
        """
        self.scan_in_progress = False
        self.startBtn.setEnabled(True)
        #self.stopBtn.setEnabled(False)
        self.pauseBtn.setEnabled(False)
        self.scansFrame.setEnabled(True)
        #self.scan_tbox_widgets[self.scan_panel_idx].set_editable()
        self.lineByLineImageDataWidget.set_enable_drop_events(True)

    def init_all_scans(self):
        """
        init_all_scans(): description

        """
        #ensure a connection to dcs values so that the forst data collection goes smooth
        _logger.info('intializing DCS connections')
        devices = MAIN_OBJ.get_devices()
        d = MAIN_OBJ.take_positioner_snapshot(devices['POSITIONERS'])
        d = MAIN_OBJ.take_detectors_snapshot(devices['DETECTORS'])
        d = MAIN_OBJ.take_pvs_snapshot(devices['PVS'])
        _logger.info('intializing DCS connections: Done')

    def closeEvent(self,event):
        """
        closeEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            event.accept()

    def on_edit_zp_params(self):
        """
        on_edit_zp_params(): description

        :returns: None
        """

        self.fpForm.show()

    def setup_main_gui(self):
        """
        setup_main_gui(): description

        :returns: None
        """
        #self.statusBar = QtWidgets.QStatusBar()
        #self.layout().addWidget(self.statusBar)
        self.setMinimumSize(1000,1000)
        self.setMaximumSize(2000,2000)

        #self.connect(self.actionExit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        self.actionExit.triggered.connect(self.close)
        self.actionZP_Params.triggered.connect(self.on_edit_zp_params)

        self.startBtn.clicked.connect(self.on_start_sscan)
        self.pauseBtn.clicked.connect(self.on_pause)
        self.stopBtn.clicked.connect(self.on_stop)

        # remember that the striptToolWidget uses the pv specified in counters.ini
        self.evScanplot = StripToolWidget(1, pvList=[MAIN_OBJ.device(DNM_TICKER).get_name()])

        self.enable_detfbk = False
        self.enable_osafbk = False

        if(LOAD_ALL):

            vbox2 = QtWidgets.QVBoxLayout()
            vbox2.addWidget(self.evScanplot)
            vbox2.setContentsMargins(1,1,1,1)
            self.counterPlotFrame.setLayout(vbox2)

            #endstation positioners panel
            #this exclude list is a hack for now, this needs to refer back to something in the BL config file
            exclude_list = ['_ZonePlateZ_base', 'SampleFineX', 'SampleFineY', 'CoarseX.X', 'CoarseY.Y', 'AUX1','AUX2','Cff','PeemM3Trans']
            self.esPosPanel = PositionersPanel(POS_TYPE_ES, exclude_list)
            spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
            vbox3 = QtWidgets.QVBoxLayout()
            vbox3.addWidget(self.esPosPanel)
            vbox3.addItem(spacer)
            self.endstationPositionersFrame.setLayout(vbox3)

            #beamline positioners panel
            self.blPosPanel = PositionersPanel(POS_TYPE_BL)
            spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
            vbox4 = QtWidgets.QVBoxLayout()
            vbox4.addWidget(self.blPosPanel)
            vbox4.addItem(spacer)
            self.beamlinePositionersFrame.setLayout(vbox4)

            #temperatures panel
            dev_obj = MAIN_OBJ.get_device_obj()
            temps = dev_obj.get_all_temperatures(POS_TYPE_ES)
            self.esTempPanel = PVsPanel(temps, egu='deg C')
            #self.esTempPanel = TemperaturesPanel(POS_TYPE_ES)
            spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
            vbox5 = QtWidgets.QVBoxLayout()
            vbox5.addWidget(self.esTempPanel)
            vbox5.addItem(spacer)
            self.esTempsFrame.setLayout(vbox5)

            #pressures panel
            dev_obj = MAIN_OBJ.get_device_obj()
            presrs = dev_obj.get_all_pressures(POS_TYPE_ES)
            self.esPressPanel = PVsPanel(presrs, egu='Torr', engineering_notation=True)
            #self.esTempPanel = TemperaturesPanel(POS_TYPE_ES)
            spacer = QtWidgets.QSpacerItem(20,40,QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
            vbox6 = QtWidgets.QVBoxLayout()
            vbox6.addWidget(self.esPressPanel)
            vbox6.addItem(spacer)
            self.esPressuresFrame.setLayout(vbox6)

            self.detectorsPanel = DetectorsPanel()
            spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            vbox5 = QtWidgets.QVBoxLayout()
            vbox5.addWidget(self.detectorsPanel)
            vbox5.addItem(spacer)
            self.detectorsFrame.setLayout(vbox5)


        self.load_dir_view()
        self.pythonshell = None

        self.shutterCntrlComboBox.currentIndexChanged.connect(self.on_shutterCntrlComboBox)
        idx = self.shutterCntrlComboBox.currentIndex()
        self.on_shutterCntrlComboBox(0) #Auto

        self.scan_progress_table =ScanQueueTableWidget()
        self.scan_q_layout.addWidget(self.scan_progress_table)
        self.init_images_frame()

    def init_images_frame(self):

        self.images_window = ContactSheet(self.active_user.get_data_dir(), BioxasDataIo)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.images_window)
        self.imagesFrame.setLayout(vbox)

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
        #idx = self.shutterCntrlComboBox.currentIndex()
        return
#         if(idx == 0):
#             print 'setting shutter mode to AUTO'
#             MAIN_OBJ.device(DNM_SHUTTER).close()
#             MAIN_OBJ.device(DNM_SHUTTER).set_to_auto()
#
#         elif(idx == 1):
#             print 'setting shutter mode to MANUAL'
#             MAIN_OBJ.device(DNM_SHUTTER).set_to_manual()
#             MAIN_OBJ.device(DNM_SHUTTER).open()
#         else:
#             print 'setting shutter mode to MANUAL'
#             MAIN_OBJ.device(DNM_SHUTTER).set_to_manual()
#             MAIN_OBJ.device(DNM_SHUTTER).close()

    def setup_scan_toolbox(self):
        """
        setup_scan_toolbox(): description

        :returns: None
        """
        # Create plugin manager
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.scanTypeToolBox = QtWidgets.QToolBox()
        self.scanTypeToolBox.layout().setContentsMargins(0,0,0,0)
        self.scanTypeToolBox.layout().setSpacing(0)
        #self.scanTypeToolBox.setStyleSheet(" QToolBox::tab {padding-left: 100px;} ")
        self.manager = PluginManager(categories_filter={ "Scans": ScanParamWidget})
        self.manager.setPluginPlaces(['scan_plugins'])
        # Load plugins
        self.manager.locatePlugins()
        self.manager.loadPlugins()

        pages = 0
        num_scans = 0
        scans = {}

        #walk the plugin directory looking for plugins of category ScanParamWidget
        for plugin in self.manager.getPluginsOfCategory("Scans"):
            print("Found SCAN plugin [%s]" % plugin.plugin_object.name)
            scans[plugin.plugin_object.idx] = plugin.plugin_object
            num_scans += 1

        #now insert then in the order the plugins idx value says
        for idx in range(num_scans):
            # plugin.plugin_object is an instance of the plugin
            #self.dataformattersCombo.addItem(plugin.plugin_object.name)
            #self.dataformatters[plugin.plugin_object.name] = plugin.plugin_object
            self.scanTypeToolBox.insertItem(pages, scans[idx], scans[idx].name)
            scans[idx].roi_changed.connect(self.on_scanpluggin_roi_changed)
            scans[idx].roi_deleted.connect(self.on_scantable_roi_deleted)
            scans[idx].plot_data.connect(self.on_plot_data_loaded)
            scans[idx].selected.connect(self.set_current_scan_pluggin)
            scans[idx].clear_all_sig.connect(self.on_clear_all)

            self.scan_tbox_widgets.append(scans[idx])
            pages += 1

        layout.addWidget(self.scanTypeToolBox)
        self.scansFrame.setLayout(layout)

        #####
        limit_def = self.scan_tbox_widgets[0].get_max_scan_range_limit_def()
        plot_item_type = self.scan_tbox_widgets[0].plot_item_type
        if(self.scan_tbox_widgets[0].is_multi_region()):
            self.lineByLineImageDataWidget.set_enable_multi_region(True)
        else:
            self.lineByLineImageDataWidget.set_enable_multi_region(False)

        self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)
        self.plotTabWidget.setCurrentIndex(PLOTTER_IMAGES_TAB)
        ######
        dx = MAIN_OBJ.device(DNM_DETECTOR_X)
        dy = MAIN_OBJ.device(DNM_DETECTOR_Y)
        centers = (dx.get_position(), dy.get_position())
        self.lineByLineImageDataWidget.set_center_at_XY(centers, (500,500))
        self.scanTypeToolBox.currentChanged.connect(self.on_toolbox_changed)

        wdg_com = self.scan_tbox_widgets[0].update_data()
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
        #item_id = dct_get(wdg_com, SPDB_SCAN_PLUGIN_ITEM_ID)
        item_id = dct_get(wdg_com, SPDB_ID_VAL)
        plot_item_type = dct_get(wdg_com, SPDB_PLOT_SHAPE_TYPE)

        item = self.lineByLineImageDataWidget.getShapePlotItem(item_id, item_type=plot_item_type)
        if(item):
            self.lineByLineImageDataWidget.blockSignals(True)
            self.lineByLineImageDataWidget.delPlotItem(item, replot=True)
            self.lineByLineImageDataWidget.blockSignals(False)


    def set_current_scan_pluggin(self, idx):
        #self.scanTypeToolBox.blockSignals(True)
        _logger.debug('set_current_scan_pluggin: [%d]' % idx)
        self.scan_panel_idx = idx
        self.scanTypeToolBox.setCurrentIndex(self.scan_panel_idx)
        #self.scanTypeToolBox.blockSignals(False)

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
        #if(self.scan_panel_idx > 100):
        #    self.scan_panel_idx = scan_panel_order.IMAGE_SCAN

        self.scanTypeToolBox.setCurrentIndex(self.scan_panel_idx)
        self.scan_tbox_widgets[self.scan_panel_idx].set_zp_focus_mode()
        time.sleep(0.15)
        #self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        #self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(sp_db, do_recalc=False)
        if(dct_get(sp_db, SPDB_PLOT_IMAGE_TYPE) in [image_types.FOCUS, image_types.OSAFOCUS]):
            #dont allow signals that would cause a plot segment to be created
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
            self.scan_tbox_widgets[self.scan_panel_idx].load_roi(wdg_com)
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)
        else:
            self.scan_tbox_widgets[self.scan_panel_idx].load_roi(wdg_com)
        #self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)

    def on_scanpluggin_roi_changed(self, wdg_com):
        """
        on_scanpluggin_roi_changed(): description

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type

        :returns: None
        """
        #_logger.debug('on_scanpluggin_roi_changed: called')
        if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
            #self.scan_progress_table.set_directory_label(self.active_user.get_data_dir())
            #self.scan_progress_table.load_wdg_com(wdg_com)

#             #for each spatial region create a plotitem
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
            #if(sp_rois is None):
            #    return
            if((sp_rois is None) or (len(list(sp_rois.keys())) < 1)):
                return
            for sp_id in list(sp_rois.keys()):
                #sp_id = sp_rois.keys()[0]
                sp_db = sp_rois[sp_id]
                scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
                plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
                item_id = int(dct_get(sp_db, SPDB_ID_VAL))

                if(plot_item_type == spatial_type_prefix.PNT):
                    x1 = x2 = float(dct_get(sp_db, SPDB_XCENTER))
                    y1 = y2 = float(dct_get(sp_db, SPDB_YCENTER))

                else:
                    x1 = float(dct_get(sp_db, SPDB_XSTART))
                    y1 = float(dct_get(sp_db, SPDB_YSTART))
                    x2 = float(dct_get(sp_db, SPDB_XSTOP))
                    y2 = float(dct_get(sp_db, SPDB_YSTOP))

                #print 'on_scanpluggin_roi_changed: item_id = %d' % item_id
                item = self.lineByLineImageDataWidget.getShapePlotItem(item_id, plot_item_type)
                #self.lineByLineImageDataWidget.set_shape_item_max_range(item, dct_get(sp_db, SPDB_SCAN_PLUGIN_MAX_SCANRANGE))

                rect =     (x1, y1, x2, y2)

                #print 'on_scanpluggin_roi_changed: rect=' , (rect)
                skip_list = [scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]
                if(item is None):
                    if(scan_item_type not in skip_list):
                        self.lineByLineImageDataWidget.addShapePlotItem(item_id, rect, item_type=plot_item_type)
                else:
                    self.lineByLineImageDataWidget.blockSignals(True)
                    if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.SELECT_ROI):
                        self.lineByLineImageDataWidget.selectShapePlotItem(item_id, select=True, item=item, item_type=plot_item_type)

                    elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ROI_CHANGED):
                        self.lineByLineImageDataWidget.resizeShapePlotItem(item_id, rect, item=item, item_type=plot_item_type)

                    self.lineByLineImageDataWidget.blockSignals(False)

        self.scan_progress_table.load_wdg_com(wdg_com)

    def on_plotitem_roi_changed(self, wdg_com):
        """
        on_plotitem_roi_changed(): description

        :param wdg_com: wdg_com description
        :type wdg_com: wdg_com type

        :returns: None
        """
        """ make call to update the scans params defined in the plugin """
        #print 'on_plotitem_roi_changed: ', dct
        if(self.scan_in_progress):
            return

        non_interactive_plots = [scan_panel_order.POSITIONER_SCAN]

        skip_scan_q_table_plots = [scan_panel_order.OSA_FOCUS_SCAN, scan_panel_order.FOCUS_SCAN]

        x1 = dct_get(wdg_com, SPDB_XSTART)
        y1 = dct_get(wdg_com, SPDB_YSTART)
        x2 = dct_get(wdg_com, SPDB_XSTOP)
        y2 = dct_get(wdg_com, SPDB_YSTOP)
        rect =     (x1, y1, x2, y2)
        #print 'on_plotitem_roi_changed: rect', rect

        if(self.scan_panel_idx in non_interactive_plots):
            return

        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ROI_CHANGED):

            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)
            wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].update_data()

            if(self.scan_panel_idx in skip_scan_q_table_plots):
                # just skip because this produces a lot of changes to the scan_q_table whcih currently are very slow when firing a lot of
                # signals to say the plot roi has chnaged
                pass
            else:
                self.scan_progress_table.load_wdg_com(wdg_com)

        elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.ADD_ROI):
            #pass on this addition request
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.DEL_ROI):
            #pass on this deletion request
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.SELECT_ROI):
            self.scan_tbox_widgets[self.scan_panel_idx].mod_roi(wdg_com)

        elif(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.DESELECT_ROI):
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
        #(fname, ado_obj) = tpl
        #wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
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
        if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.SAMPLE_POINT_SPECTRA, scan_types.GENERIC_SCAN]):
            self.lineByLineImageDataWidget.blockSignals(True)
            self.lineByLineImageDataWidget.delShapePlotItems()
            self.lineByLineImageDataWidget.load_image_data(fname, wdg_com, data)

            #only allow the scan param shapes to be created if NOT a focus type scan image
            if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS]):
                rect = sp_db[SPDB_RECT]
                sp_id = int(dct_get(sp_db, SPDB_ID_VAL))
                #scan_item_type = int(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
                plot_item_type = int(dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))
                self.lineByLineImageDataWidget.addShapePlotItem(int(sp_id), rect, item_type=plot_item_type)

            #make sure plotter is aware if it is supposed to allow more than one ShpeItem
            #if(self.scan_tbox_widgets[self.scan_panel_idx].is_multi_region()):
            #    self.lineByLineImageDataWidget.set_enable_multi_region(True)
            #else:
            #    self.lineByLineImageDataWidget.set_enable_multi_region(False)

            self.lineByLineImageDataWidget.blockSignals(False)

    def setup_image_plot(self):
        """
        setup_image_plot(): description

        :returns: None
        """
        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

        #gridparam = {'fg_clr':fg_clr, 'bg_clr':bg_clr, 'min_clr':min_clr, 'maj_clr':maj_clr}

        #self.lineByLineImageDataWidget = ImageWidget(self, filtStr = "*.hdf5", type='analyze', sample_pos_mode=sample_pos_mode,
        self.lineByLineImageDataWidget = ImageWidget(parent=None, filtStr = "*.hdf5", type=None,
                            options=dict(lock_aspect_ratio=True, show_contrast=True, show_xsection=True, show_ysection=True,
                            xlabel=("microns", ""), ylabel=("microns", ""), colormap="gist_gray"))
        self.lineByLineImageDataWidget.setObjectName("lineByLineImageDataWidget")
        self.lineByLineImageDataWidget.register_osa_and_samplehldr_tool(sample_pos_mode)
        #self.lineByLineImageDataWidget.set_transform_factors(0.333, 0.333, 0.333, 'um')
        self.lineByLineImageDataWidget.setMinimumSize(600,600)
        self.lineByLineImageDataWidget.setMaximumSize(1000,1000)
        self.lineByLineImageDataWidget.enable_tool_by_name('StxmOpenFileTool', False)
        #self.lineByLineImageDataWidget.set_sample_positioning_mode(sample_pos_mode)
        self.lineByLineImageDataWidget.set_dataIO(BioxasDataIo)

        #self.lineByLineImageDataWidget.addTool('HLineSegmentTool')

        self.lineByLineImageDataWidget.set_grid_parameters(bg_clr, min_clr, maj_clr)
        self.lineByLineImageDataWidget.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)

        self.lineByLineImageDataWidget.new_roi_center.connect(self.on_plotitem_roi_changed)
        self.lineByLineImageDataWidget.scan_loaded.connect(self.on_scan_loaded)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.lineByLineImageDataWidget)
        self.imagePlotFrame.setLayout(vbox)

        #self.lineByLineImageDataWidget.create_sample_holder()

        self.lineByLineImageDataWidget.set_data_dir(self.active_user.get_data_dir())
        MAIN_OBJ.set('IMAGE_WIDGET', self.lineByLineImageDataWidget)


    def setup_spectra_plot(self):
        """
        setup_spectra_plot(): description

        :returns: None
        """
        vbox = QtWidgets.QVBoxLayout()
        #self.spectraWidget = CurveViewerWidget(parent = self, winTitleStr = "Spectra Data Viewer")
        self.spectraWidget = CurveViewerWidget()
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
        from cls.applications.bioXasIM.widgets.camera_ruler import CameraRuler, camruler_mode
        vbox = QtWidgets.QVBoxLayout()
        #self.spectraWidget = CurveViewerWidget(parent = self, winTitleStr = "Spectra Data Viewer")
        self.calibCamWidget = CameraRuler(mode=camruler_mode.CLIENT)
        self.calibCamWidget.setObjectName("calibCamWidget")


        vbox.addWidget(self.calibCamWidget)
        self.calibCamPlotFrame.setLayout(vbox)

    def setup_info_dock(self):
        """
        setup_info_dock(): description

        :returns: None
        """
        #ns = {'main': self, 'widget': self, 'det_scan' : scans[1]}
        ns = {'main': self, 'pythonShell': self.pythonshell, 'g':globals() }
        #msg = "Try for example: widget.set_text('foobar') or win.close()"
        self.pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
        self.pyconsole_layout.addWidget(self.pythonshell)
        #self.apply_stylesheet(self.pythonshell, self.qssheet)

    def on_toolbox_changed(self, idx):
        """
        on_toolbox_changed(): description

        :param idx: idx description
        :type idx: idx type

        :returns: None
        """
        reset_unique_roi_id()
        ranges = (None, None)
        #print 'on_toolbox_changed: %d' % idx
        spectra_plot_types = [scan_panel_order.POINT_SCAN]
        non_interactive_plots = [scan_panel_order.POSITIONER_SCAN]
        multi_spatial_scan_types = [scan_types.SAMPLE_POINT_SPECTRA, scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_IMAGE, \
                                    scan_types.SAMPLE_IMAGE_STACK]

        skip_list = [scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]

        self.scan_panel_idx = idx

        if(len(self.scan_tbox_widgets) > 0):
            self.scan_progress_table.clear_table()
            sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()

            scan_pluggin = self.scan_tbox_widgets[self.scan_panel_idx]
            ranges = scan_pluggin.get_saved_range()
            centers = scan_pluggin.get_saved_center()
            axis_strs = scan_pluggin.get_axis_strs()
            max_scan_range = scan_pluggin.get_spatial_scan_range()
            limit_def = scan_pluggin.get_max_scan_range_limit_def()
            plot_item_type = scan_pluggin.plot_item_type
            enable_multi_region = scan_pluggin.is_multi_region()
            scan_type = scan_pluggin.get_scan_type()
            #wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].update_data()
            #self.scan_progress_table.load_wdg_com(wdg_com)

        self.lineByLineImageDataWidget.delShapePlotItems()
        if(idx in spectra_plot_types):
            #self.plotTabWidget.setCurrentIndex(0)
            self.spectraWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])
        else:
            self.plotTabWidget.setCurrentIndex(PLOTTER_IMAGES_TAB)

            if((ranges[0] is not None) and (ranges[1] is not None)):

                if((self.scan_panel_idx == scan_panel_order.IMAGE_SCAN) and (sample_positioning_mode == sample_positioning_modes.GONIOMETER)):
                    self.lineByLineImageDataWidget.set_center_at_XY(centers, ranges)
                else:
                    pass
                    #sx = MAIN_OBJ.device(DNM_SAMPLE_X)
                    #sy = MAIN_OBJ.device(DNM_SAMPLE_Y)
                    #centers = (sx.get_position(), sy.get_position())
                    #self.lineByLineImageDataWidget.set_center_at_XY(centers, ranges)


                #self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)
                self.lineByLineImageDataWidget.setPlotAxisStrs(axis_strs[0], axis_strs[1])

        self.lineByLineImageDataWidget.set_max_shape_sizes(max_scan_range)
        self.lineByLineImageDataWidget.set_enable_multi_region(enable_multi_region)

        if(self.scan_panel_idx in non_interactive_plots):
            #disable all roi selection tools
            self.lineByLineImageDataWidget.set_shape_limits(shape=None, limit_def=None)
        else:
            self.lineByLineImageDataWidget.set_shape_limits(shape=plot_item_type, limit_def=limit_def)


        if(len(self.scan_tbox_widgets) > 0):
            #some of the params on a particular tool box read pv's so make sure the
            #focus calc mode is set correctly and has time to process
            scan_pluggin.set_zp_focus_mode()
            time.sleep(0.15)
            scan_pluggin.load_from_defaults()

        #if(scan_type in multi_spatial_scan_types):
        wdg_com = scan_pluggin.update_data()

        #if(wdg_com):
        #    if(len(wdg_com['SPATIAL_ROIS']) > 0):
        #        self.scan_progress_table.load_wdg_com(wdg_com)


    def init_statusbar(self):
        """
        init_statusbar(): description

        :returns: None
        """
        self.status_list = []
        title_color= master_colors['app_blue']
        fbk_color = 'white'
        msg_color = master_colors['msg_color']
        ma_color = master_colors['app_yellow']


#         self.status_list.append(ca_strLabel(MAIN_OBJ.device('SRStatus_msgL1'),  hdrText='SR Status', title_color=title_color, var_clr=fbk_color))
#         self.status_list.append(ca_strLabel(MAIN_OBJ.device('SRStatus_msgL2'), title_color=title_color, var_clr=fbk_color))
#         self.status_list.append(ca_strLabel(MAIN_OBJ.device('SRStatus_msgL3'), title_color=title_color, var_clr=fbk_color))

        #self.status_list.append(ca_aiLabelWidget(MAIN_OBJ.device(DNM_MONO_EV_FBK), hdrText='Energy', egu='eV', title_color=title_color, var_clr=fbk_color))
        #self.status_list.append(ca_aiLabelWidget(MAIN_OBJ.device(DNM_TICKER), hdrText='I0', title_color=title_color, var_clr=fbk_color))
        self.status_list.append(ca_mbbiLabelWidget(MAIN_OBJ.device(DNM_SYSTEM_MODE_FBK).get_name(), hdrText='SR Mode', title_color=title_color, var_clr=fbk_color))
        self.status_list.append(ca_aiLabelWidget(MAIN_OBJ.device('StorageRingCurrent'), hdrText='Ring', egu='mA', title_color=title_color, var_clr=fbk_color, alarm=5, warn=20))
        self.status_list.append(QtWidgets.QLabel('Beamline: ' + MAIN_OBJ.get_beamline_name()))
        self.status_list.append(QtWidgets.QLabel('EndStation: ' + MAIN_OBJ.get_endstation_name()))

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
        #print 'add_line_to_plot: row=%d' % row
        #print counter_to_plotter_com_dct
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        col = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        line_data = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        img_cntr = counter_to_plotter_com_dct[CNTR2PLOT_IMG_CNTR]
        is_line = counter_to_plotter_com_dct[ CNTR2PLOT_IS_LINE ]
        is_point = counter_to_plotter_com_dct[ CNTR2PLOT_IS_POINT ]
        #self.cur_image_idx = _dct['img_idx']

        if(self.get_cur_scan_type() == scan_types.SAMPLE_LINE_SPECTRA):
            #if(not self.image_started and (col == 0)):
            #if(not self.executingScan.image_started and (col == 0)):
            if(is_point):
                if(not self.executingScan.image_started and (col == 0) and (row == 0)):
                    self.on_image_start()
            if(is_line):
                if(not self.executingScan.image_started and (col == 0)):
                    self.on_image_start()


            if(col > 0):
                #self.image_started = False
                self.executingScan.image_started = False

            self.lineByLineImageDataWidget.addVerticalLine(col, line_data, True)
        else:
            #if(not self.image_started and (row == 0)):
            #if(not self.executingScan.image_started and (row == 0)):
            if(is_point):
                if(not self.executingScan.image_started and (col == 0) and (row == 0)):
                    self.on_image_start()

            if(is_line):
                if(not self.executingScan.image_started and (row == 0)):
                    self.on_image_start()


            if(row > 0):
                #self.image_started = False
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

        :param row: row description
        :type row: row type

        :param tpl: tpl description
        :type tpl: tpl type

        :returns: None
        """
        """ a function to take data (a full line) and add it to the configured plotters
        Need a flag to monitor when to start a new image
        """

        #print counter_to_plotter_com_dct
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        col = point = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        val = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        img_cntr = counter_to_plotter_com_dct[CNTR2PLOT_IMG_CNTR]
        ev_cntr = counter_to_plotter_com_dct[CNTR2PLOT_EV_CNTR]

        if(self.get_cur_scan_type() == scan_types.SAMPLE_LINE_SPECTRA):
            if(not self.executingScan.image_started and (ev_cntr == 0) and ((col == 0) and (row == 0))):
                self.on_image_start()

            if(col > 0):
                self.executingScan.image_started = False

            self.lineByLineImageDataWidget.addPoint(row, point, val, True)

        else:
            if(not self.executingScan.image_started and (row == 0)):
                self.on_image_start()

            #print 'add_point_to_plot: row=%d, point=%d, val=%d' % (row, point, val)
            self.lineByLineImageDataWidget.addPoint(row, point, val, True)

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
        #_logger.debug('add_point_to_spectra: called with row=%d, tpl=')
        sp_id = counter_to_plotter_com_dct[CNTR2PLOT_SP_ID]
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        point = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        val = counter_to_plotter_com_dct[CNTR2PLOT_VAL]


        #print 'add_point_to_spectra: sp_id=%d row=%d, point=%d, val=%d' % (sp_id, row, point, val)
        self.spectraWidget.addXYPoint('sp_id_%d'%sp_id, point, val, update=True)

    def reset_image_plot(self):
        self.image_started == False
        self.lineByLineImageDataWidget.delImagePlotItems()
        self.lineByLineImageDataWidget.delShapePlotItems()
        self.lineByLineImageDataWidget.set_auto_contrast(True)

    def assign_datafile_names_to_sp_db(self, sp_db, d, image_idx=0):
        ''' d keys ['thumb_name', 'prefix', 'data_ext', 'stack_dir', 'data_name', 'thumb_ext']
        '''
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
        if((val is None) or (type(val) != typ)):
            return(False)
        else:
            return(True)

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
                if( not v):
                    return(False)

        return(True)


    def determine_num_thumbnail_images_required(self, wdg_com):
        """
        determine_num_thumbnail_images_required(): take a list of spatial regions and check the scan type and retrun
        the number of images that will be needed

        :param sp_rois: sp_rois description
        :type sp_rois: sp_rois type

        :returns: integer number of images required for the scans
        """
        single_image_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_FOCUS, scan_types.OSA_IMAGE, scan_types.SAMPLE_FOCUS, \
                              scan_types.SAMPLE_IMAGE, scan_types.GENERIC_SCAN, scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_POINT_SPECTRA]
        sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = sorted(sp_rois.keys())
        n_imgs = []
        _imgs = 0
        for sp_id in sp_ids:
            sp_db = sp_rois[sp_id]
            scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
            if(scan_type in single_image_scans):
                #n_imgs.append(1)
                _imgs = 1
            else:
                #n_imgs.append(self.get_num_ev_points(sp_db[SPDB_EV_ROIS]))
                _imgs = self.get_num_ev_points(sp_db[SPDB_EV_ROIS])
                #n_imgs = sp_db[SPDB_EV_NPOINTS] * sp_db[SPDB_POL_NPOINTS]
            n_imgs.append(_imgs)
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
        return(int(n_ev))

    def apply_user_settings_to_scan(self, scan):
        """
        apply_user_settings_to_scan: query the appConfig settings file andset any flags of the executing scan here

        :param scan: This is the currently configured executing scan
        :type scan: this is a scan plugin that has ScanParamWiget as its parent class

        """
        appConfig.update()
        #set the save all data flag
        val = appConfig.get_bool_value('DATA', 'save_all_data')
        if(val is not None):
            scan.set_save_all_data(val)

        val = appConfig.get_bool_value('DATA', 'save_jpg_thumbnails')
        if(val is not None):
            scan.set_save_jpgs(val)


        #set others below



    def on_start_sscan(self):
        """
        on_start_sscan(): description

        :returns: None
        """
        #make sure the data dir is up to date in case the 24 hour time has rolled over
        self.active_user.create_data_dir()

        #keep the scan plugin from firing any signals that would cause other widgets to respond
        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(True)
        self.cur_wdg_com = self.scan_tbox_widgets[self.scan_panel_idx].get_roi()
        if(self.cur_wdg_com is None):
            self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)
            return

        #set main gui widgets up for running a scan
        self.set_buttons_for_scanning()

        #init some variables
        self.data = []
        MAIN_OBJ.clear_scans()
        self.reset_image_plot()
        self.cur_ev_idx = 0
        new_stack_dir = False

        #ok allow the scan plugin to fire signals again
        self.scan_tbox_widgets[self.scan_panel_idx].blockSignals(False)

        #assign these values that are used to decide which GUI signals to connect and disconnect
        self.set_cur_scan_type(self.scan_tbox_widgets[self.scan_panel_idx].type)
        self.set_cur_scan_sub_type(self.scan_tbox_widgets[self.scan_panel_idx].sub_type)

        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()

        #get an instance of the actual scan class
        sscan = self.scan_tbox_widgets[self.scan_panel_idx].get_sscan_instance()
        sscan.set_active_user(self.active_user)
        sscan.scan_type = scan_type

        self.apply_user_settings_to_scan(sscan)
        self.executingScan = sscan

        #grab some information used by all scans below
        sp_rois = dct_get(self.cur_wdg_com, WDGCOM_SPATIAL_ROIS)
        sp_ids = sorted(sp_rois.keys())
        self.cur_sp_rois = copy.copy(sp_rois)

        # a list of basic scans that use the same configuration block below
        _simple_types = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.GENERIC_SCAN, scan_types.SAMPLE_FOCUS]
        _multispatial_types = [scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_POINT_SPECTRA]

        if(scan_type in _simple_types):
            sp_id = sp_ids[0]
            sp_db = sp_rois[sp_id]
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False, num_desired_datafiles=1)
            self.assign_datafile_names_to_sp_db(sp_db, d[0])
            sscan.set_spatial_id(sp_id)
            sscan.set_datafile_names_dict(d)
            sscan.set_spatial_id_list(sp_ids)
            sscan.configure(self.cur_wdg_com, sp_id=sp_id, line=False)
            if(scan_type == scan_types.GENERIC_SCAN):
                self.init_point_spectra(num_curves=1)

        elif(scan_type in _multispatial_types):
            line=True
            num_images_lst = self.determine_num_thumbnail_images_required(self.cur_wdg_com)
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False, num_desired_datafiles=len(sp_ids))
            idx = 0
            for sp_id in sp_ids:
                sp_db = sp_rois[sp_id]
                if(scan_type == scan_types.SAMPLE_POINT_SPECTRA):
                    #for point spec all spatial regions use same datafile but different entrys
                    self.assign_datafile_names_to_sp_db(sp_db, d[0], image_idx=0)
                else:
                    self.assign_datafile_names_to_sp_db(sp_db, d[idx], image_idx=idx)
                idx += 1

            if(scan_type == scan_types.SAMPLE_POINT_SPECTRA):
                #here I need to init it with the number of sp_ids (spatial points)
                self.init_point_spectra(num_curves=len(sp_ids))
                line = False

            self.set_cur_scan_sub_type(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE))
            #sscan.set_datafile_names_dict(d)
            sscan.set_spatial_id_list(sp_ids)
            sp_id = sscan.get_next_spatial_id()
            sscan.configure(self.cur_wdg_com, sp_id=sp_id  , ev_idx=0, line=line)

        elif(scan_type == scan_types.SAMPLE_IMAGE_STACK):
            #use first sp_DB to determine if point by point or line unidir
            sp_db = sp_rois[sp_ids[0]]
            #num_images = int(sp_db[SPDB_EV_NPOINTS] * sp_db[SPDB_POL_NPOINTS] * len(sp_ids))
            num_images = self.determine_num_thumbnail_images_required(self.cur_wdg_com)[0]
            d = master_get_seq_names(self.active_user.get_data_dir(), prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', num_desired_datafiles=num_images, new_stack_dir=True)
            if(len(sp_ids) > 1):
                #each spatial roi needs a filename dict
                for i in range(num_images):
                    self.assign_datafile_names_to_sp_db(sp_rois[sp_ids[i]], d[i], image_idx=idx)
            else:
                self.assign_datafile_names_to_sp_db(sp_rois[sp_ids[0]], d[0])

            self.set_cur_scan_sub_type(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE))
            sscan.set_datafile_names_dict(d)
            sscan.set_spatial_id_list(sp_ids)
            sp_id = sscan.get_next_spatial_id()
            sscan.configure(self.cur_wdg_com, sp_id=sp_id  , ev_idx=0, line=True)


        else:
            _logger.error('start_scan: unsupported scan type [%d]' % scan_type)
            self.set_buttons_for_starting()
            return

        MAIN_OBJ.set('SCAN.CFG.WDG_COM', self.cur_wdg_com)

        #make sure all scans have set the data file names to their respective active data objects before allowing scan
        #to start
        if(not self.test_assign_datafile_names_to_sp_db(self.cur_wdg_com)):
            _logger.error('start_scan: incorrectly configured scan: data file names not assigned to active data object')
            self.set_buttons_for_starting()
            return

        #ok all good lets run the scan
        self.scan_progress_table.set_queue_file_list(get_thumb_file_name_list(d))
        self.scan_progress_table.load_wdg_com(self.cur_wdg_com)
        self.connect_executingScan_signals()
        self.executingScan.image_started = False
        self.executingScan.reset_consecutive_scan_idx()
        self.executingScan.start()
        self.start_time = time.time()

    def init_point_spectra(self, sp_id=-1, num_curves=1):
        """
        init_point_spectra(): description

        :param sp_id=-1: sp_id=-1 description
        :type sp_id=-1: sp_id=-1 type

        :returns: None
        """

        self.spectraWidget.clear_plot()

        sp_ids = list(self.cur_sp_rois.keys())

        for sp_id in sp_ids:
            #self.spectraWidget.create_curve('point_spectra_%d' % i,curve_style='Lines')
            clr = get_next_color(use_dflt=False)
            style = get_basic_line_style(clr)
            self.spectraWidget.create_curve('sp_id_%d' % sp_id, curve_style=style)

    def connect_executingScan_signals(self):
        """
        connect_executingScan_signals(): description

        :returns: None
        """
        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()
        #_logger.info('GUI: connect_executingScan_signals')
        if((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
            (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
            (scan_type == scan_types.SAMPLE_LINE_SPECTRA) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
            (scan_type == scan_types.SAMPLE_FOCUS) and (scan_sub_type == scan_sub_types.LINE_UNIDIR)):
            self.executingScan.sigs.changed.connect(self.add_line_to_plot)

            if(not (scan_type == scan_types.SAMPLE_LINE_SPECTRA)):
                #dont connect this for line_spec scans because the data level is energy which would cause a
                # new image for each energy line which is not what we want
                self.executingScan.data_start.connect(self.on_image_start)

        elif(((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (scan_sub_type == scan_sub_types.POINT_BY_POINT) or \
                (scan_type == scan_types.DETECTOR_IMAGE)  or \
                (scan_type == scan_types.OSA_IMAGE) or \
                (scan_type == scan_types.OSA_FOCUS) or \
                ((scan_type == scan_types.SAMPLE_LINE_SPECTRA) and (scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                (scan_type == scan_types.SAMPLE_FOCUS) or \
                (scan_type == scan_types.ZP_IMAGE_SCAN) ):
            self.executingScan.sigs.changed.connect(self.add_point_to_plot)

            if(not (scan_type == scan_types.SAMPLE_LINE_SPECTRA)):
                #dont connect this for line_spec scans because the data level is energy which would cause a
                # new image for each energy line which is not what we want
                self.executingScan.data_start.connect(self.on_image_start)


        elif((scan_type == scan_types.SAMPLE_POINT_SPECTRA) or \
            (scan_type == scan_types.GENERIC_SCAN)):
            self.executingScan.sigs.changed.connect(self.add_point_to_spectra)
            #self.executingScan.new_spatial_start.connect(self.init_point_spectra)

        else:
            _logger.error('connect_executingScan_signals: executingScan type [%d] not supported', scan_type)

        self.executingScan.sigs.status.connect(self.on_scan_status)
        #self.executingScan.sigs.progress.connect(self.on_scan_progress)
        self.executingScan.top_level_progress.connect(self.on_total_scan_progress)
        self.executingScan.low_level_progress.connect(self.on_scan_progress)
        self.executingScan.sigs_disconnected.connect(self.on_executing_scan_sigs_discon)
        self.executingScan.sigs.aborted.connect(self.on_scan_done)
        self.executingScan.all_done.connect(self.on_scan_done)

        self.executingScan.saving_data.connect(self.on_saving_data)

        #_logger.debug('executingScan signals connected')

    def disconnect_executingScan_signals(self):
        """
        disconnect_executingScan_signals(): description

        :returns: None
        """
        scan_type = self.get_cur_scan_type()
        scan_sub_type = self.get_cur_scan_sub_type()

        #_logger.debug('disconnect_executingScan_signals: TOP')
        if((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
           (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
            (scan_type == scan_types.SAMPLE_LINE_SPECTRA) and (scan_sub_type == scan_sub_types.LINE_UNIDIR) or \
            (scan_type == scan_types.SAMPLE_FOCUS) and (scan_sub_type == scan_sub_types.LINE_UNIDIR)):
            self.executingScan.sigs.changed.disconnect(self.add_line_to_plot)

            if(not (scan_type == scan_types.SAMPLE_LINE_SPECTRA)):
                self.executingScan.data_start.disconnect(self.on_image_start)

        elif(((scan_type == scan_types.SAMPLE_IMAGE) and (scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                (scan_type == scan_types.SAMPLE_IMAGE_STACK) and (scan_sub_type == scan_sub_types.POINT_BY_POINT) or \
                (scan_type == scan_types.DETECTOR_IMAGE)  or \
                (scan_type == scan_types.OSA_IMAGE) or \
                (scan_type == scan_types.OSA_FOCUS) or \
                ((scan_type == scan_types.SAMPLE_LINE_SPECTRA) and (scan_sub_type == scan_sub_types.POINT_BY_POINT)) or \
                (scan_type == scan_types.SAMPLE_FOCUS) or \
                (scan_type == scan_types.ZP_IMAGE_SCAN) ):
            self.executingScan.sigs.changed.disconnect(self.add_point_to_plot)

            if(not (scan_type == scan_types.SAMPLE_LINE_SPECTRA)):
                self.executingScan.data_start.disconnect(self.on_image_start)

        elif((scan_type == scan_types.SAMPLE_POINT_SPECTRA) or \
            (scan_type == scan_types.GENERIC_SCAN)):
            self.executingScan.sigs.changed.disconnect(self.add_point_to_spectra)
            #self.executingScan.new_spatial_start.disconnect(self.init_point_spectra)

        else:
            _logger.error('disconnect_executingScan_signals: executingScan type [%d] not supported', scan_type)

        self.executingScan.sigs.status.disconnect(self.on_scan_status)
        #self.executingScan.sigs.progress.disconnect(self.on_scan_progress)
        self.executingScan.top_level_progress.disconnect(self.on_total_scan_progress)
        self.executingScan.low_level_progress.disconnect(self.on_scan_progress)
        self.executingScan.sigs_disconnected.disconnect(self.on_executing_scan_sigs_discon)
        self.executingScan.sigs.aborted.disconnect(self.on_scan_done)
        self.executingScan.all_done.disconnect(self.on_scan_done)

        self.executingScan.saving_data.disconnect(self.on_saving_data)


        self._set_scan_btns.emit('SET_FOR_STARTING')
        self.on_scan_status('Idle')

    def on_saving_data(self, msg):
        self.scanActionLbl.setText(msg)
        _logger.info('%s ...' % msg)

    def on_image_start(self, wdg_com=None):
        """
        on_image_start(): called when a new image  starts

        :param wdg_com=None: wdg_com=None description
        :type wdg_com=None: wdg_com=None type

        :returns: None
        """
        #on_image_start can be called by singal passed from scan with the wdg_com as the arg
        #_logger.debug('on_image_start called')
        if(wdg_com is None):
            #use current
            wdg_com = self.cur_wdg_com

        sp_id = self.executingScan.get_spatial_id()
        if(sp_id not in list(wdg_com[WDGCOM_SPATIAL_ROIS].keys())):
            _logger.error('Spatial ID does not exist in widget communication dict')
            return

        sp_db = wdg_com[WDGCOM_SPATIAL_ROIS][sp_id]
        scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)

        #hack
        if(self.executingScan.image_started == True):
            self.executingScan.image_started = False

        if(self.executingScan.image_started == False):

            numX = dct_get(sp_db, SPDB_XNPOINTS)
            numY = dct_get(sp_db, SPDB_YNPOINTS)
            numZ = dct_get(sp_db, SPDB_ZNPOINTS)
            #img_parms = dct_get(wdg_com, 'CURRENT.SCAN.IMAGE_PARMS')
            rect = dct_get(sp_db, SPDB_RECT)
            numE = dct_get(sp_db, SPDB_EV_NPOINTS)

            x_roi = sp_db['X']
            y_roi = sp_db['Y']

            #_logger.info('on_image_start: rect = (%.2f, %.2f, %.2f, %.2f)' % (rect[0], rect[1], rect[2], rect[3]))
            #_logger.info('on_image_start: rois (%.2f, %.2f, %.2f, %.2f)' % (x_roi[START], y_roi[START], x_roi[STOP], y_roi[STOP]))
            #_logger.debug('GUI: on_image_start')
            if(scan_type == scan_types.SAMPLE_FOCUS):
                self.lineByLineImageDataWidget.initData(image_types.FOCUS, numZ ,  numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)

            elif(scan_type == scan_types.OSA_FOCUS):
                #osa focus scan only sits at a single Y position and so will be a square (equal to num x points)
                self.lineByLineImageDataWidget.initData(image_types.OSAFOCUS, numZ ,  numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)

            elif(scan_type == scan_types.SAMPLE_LINE_SPECTRA):
                self.lineByLineImageDataWidget.initData(image_types.LINE_PLOT, numX ,  numE, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=True)

            else:
                self.lineByLineImageDataWidget.initData(image_types.IMAGE, numY ,  numX, {SPDB_RECT: rect})
                self.lineByLineImageDataWidget.set_autoscale(fill_plot_window=False)

            self.executingScan.image_started = True
            self.on_scan_start()



    def on_spectra_start(self):
        """
        on_spectra_start(): description

        :returns: None
        """
        print('on_spectra_start')
        self.spectraWidget.clear_plot()


    def on_scan_start(self):
        """
        on_scan_start(): description

        :returns: None
        """
        #self.scan_progress_table.set_pixmap(0, scan_status_types.RUNNING)
        pass

    def on_scan_done(self):
        """
        on_scan_done(): description

        :returns: None
        """
        #idx = self.executingScan.get_imgidx()
        #_logger.info('GUI: scan completed')
        #self.scan_progress_table.set_pixmap(self.cur_image_idx, scan_status_types.DONE)
        pass

    def on_executing_scan_sigs_discon(self):
        """
        on_executing_scan_sigs_discon(): description

        :returns: None
        """
        #_logger.info('GUI: on_executing_scan_sigs_discon')
#        if(MAIN_OBJ.device(DNM_SHUTTER).is_auto()):
#            MAIN_OBJ.device(DNM_SHUTTER).close()
        #_logger.info('scan completed')
        #self.curImgProgBar.setValue(0.0)
        self.totalProgBar.setValue(0.0)

        self.lineByLineImageDataWidget.set_lock_aspect_ratio(True)
        if(self.executingScan is not None):
            self.disconnect_executingScan_signals()

    def secondsToStr(self, t):
        """
        secondsToStr(): description

        :param t: t description
        :type t: t type

        :returns: None
        """
        #rediv = lambda ll,b : list(divmod(ll[0],b)) + ll[1:]
        #return "%d:%02d:%02d" % tuple(reduce(rediv,[[t*1000,], 1000,60]))
        #return "%d:%02d:%02d" % tuple(reduce(rediv,[[t*1000,], 1000,60]))
        #elapsed_sec = end_time - begin_time
        return(strftime("%H:%M:%S", gmtime(t)))


    def  check_time(self, cur_scan_progress):
        """
         check_time(): description

        :param cur_scan_progress: cur_scan_progress description
        :type cur_scan_progress: cur_scan_progress type

        :returns: None
        """
        if(cur_scan_progress < 1.0):
            cur_scan_progress = 1
        if(self.start_time is None):
            self.start_time = time.time()
        self.elapsed_time = time.time() - self.start_time
        time_left = ((100.0 / cur_scan_progress) * self.elapsed_time) - self.elapsed_time
        #cs_sts['elapsed_time'] = self.secondsToStr(self.elapsed_time)
        self.elapsedTimeLbl.setText(self.secondsToStr(self.elapsed_time))
        #cs_sts['time_left'] = self.secondsToStr(time_left)
        self.timeLeftLbl.setText(self.secondsToStr(time_left))

    def on_scan_status(self, msg):
        """
        on_scan_status(): description

        :param msg: msg description
        :type msg: msg type

        :returns: None
        """
        self.scanActionLbl.setText(msg)

    def set_cur_scan_type(self, type):
        self._scan_type = type

    def set_cur_scan_sub_type(self, type):
        self._scan_sub_type = type

    def get_cur_scan_type(self):
        return(self._scan_type)

    def get_cur_scan_sub_type(self):
        return(self._scan_sub_type)

    def on_scan_progress(self, percent):
        """
        on_scan_progress(): a signal handler that fires when the progress pv's have been updated, here clip the top of the scan
        percentage at >= 90.0, if >= 90.0 just set it to %100

        :param percent: percent description
        :type percent: percent type

        :returns: None
        """
        idx = self.executingScan.get_consecutive_scan_idx()
        sp_id = self.executingScan.get_spatial_id()

        if(self.get_cur_scan_type() is not scan_types.SAMPLE_IMAGE_STACK):
            set_pixmap = self.scan_progress_table.set_pixmap_by_spid
            set_progress = self.scan_progress_table.set_progress_by_spid
            id = sp_id
        else:
            #its a stack
            set_pixmap = self.scan_progress_table.set_pixmap
            set_progress = self.scan_progress_table.set_progress
            id = idx

        if(percent >= 90.0):
            percent = 100.0
        #print 'on_scan_progress: sp_id [%d] at %.2f  done' % (idx, percent)

        set_progress(id, percent)

        if(percent >= 100.0):
            set_pixmap(id, scan_status_types.DONE)
        elif(percent < 100.0):
            set_pixmap(id, scan_status_types.RUNNING)
        else:
            set_pixmap(id, scan_status_types.STOPPED)
        #self.curImgProgBar.setValue(percent)
        self.check_time(percent)

    def on_total_scan_progress(self, percent):
        """
        on_total_scan_progress(): description

        :param percent: percent description
        :type percent: percent type

        :returns: None
        """
        #print 'on_total_scan_progress: %.2f' % percent
        #self.totalProgBar.setValue(percent)
        #self.scan_progress_table.set_progress(self.cur_image_idx, percent)
        self.totalProgBar.setValue(percent)

    def on_pause(self, chkd):
        """
        on_pause(): description

        :param chkd: chkd description
        :type chkd: chkd type

        :returns: None
        """

        if(self.executingScan):
            #idx = self.executingScan.get_imgidx()
            idx = self.executingScan.get_consecutive_scan_idx()
            if(chkd):
                self.executingScan.pause()
                self.scan_progress_table.set_pixmap(idx, scan_status_types.PAUSED)
            else:
                self.executingScan.resume()
                self.scan_progress_table.set_pixmap(idx, scan_status_types.RUNNING)

    def on_stop(self):
        """
        on_stop(): description

        :returns: None

        """
        if(self.executingScan):
            #idx = self.executingScan.get_imgidx()
            idx = self.executingScan.get_consecutive_scan_idx()
            self.executingScan.stop()
            self.scan_progress_table.set_pixmap(idx, scan_status_types.ABORTED)
            self.stopping = True
        self.set_buttons_for_starting()

    def on_exit(self):
        """
        on_exit(): description

        :returns: None
        """
        pass
        #_logger.info('Main GUI: on_exit')

def go():
    """
        go(): description

        :param go(: go( description
        :type go(: go( type

        :returns: None
    """


    #ca.threads_init()
    app = QtWidgets.QApplication(sys.argv)
    pystxm_win = bioxasMWindow()
    pystxm_win.show()
    app.exec_()


# if __name__ == '__main__':
#     import profile
#     import pstats
#
#     ca.threads_init()
#     #motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
#     app = QtWidgets.QApplication(sys.argv)
#
#     #log_to_qt()
#     absMtr = bioxasMWindow()
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
    print('bias val = ' , bval)
    profile.Profile.bias = bval
    return bval

def profile_it():
    """
        profile_it(): description

        :param profile_it(: profile_it( description
        :type profile_it(: profile_it( type

        :returns: None
    """

    #determine_profile_bias_val()

    profile.Profile.bias = 1.36987840635e-05


    profile.run('go()', 'testprof.dat')

    p = pstats.Stats('testprof.dat')
    p.sort_stats('cumulative').print_stats(100)


if __name__ == '__main__':
    import profile
    import pstats


    #motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
    #app = QtWidgets.QApplication(sys.argv)
    go()
    #profile_it()

    #test()









