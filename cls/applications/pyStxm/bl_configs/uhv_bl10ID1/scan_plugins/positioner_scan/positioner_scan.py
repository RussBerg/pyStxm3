'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import uic
import os
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, DEFAULTS
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from bcm.devices.device_names import *
from cls.data_io.stxm_data_io import STXMDataIo

from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, get_unique_roi_id, \
                    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
                    get_first_sp_db_from_wdg_com, on_center_changed, recalc_setpoints, widget_com_cmnd_types
from cls.types.stxmTypes import scan_types, spatial_type_prefix
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger

from cls.applications.pyStxm.bl_configs.uhv_bl10ID1.scan_plugins.positioner_scan.PositionerScan import PositionerScanClass

_logger = get_module_logger(__name__)

class PositionerScanParam(ScanParamWidget):

    
    data = {}
    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'positioner_scan.ui'), self)
        self.posner_dct = {}
        self.populate_positioner_cbox()
        
        self.loadScanBtn.clicked.connect(self.load_scan)
        self.posnerComboBox.currentIndexChanged.connect(self.positioner_changed)
        
        self.scan_class = PositionerScanClass(main_obj=self.main_obj)
        self.positioner = None

        self.sp_db = None
        self.load_from_defaults()
        self.init_sp_db()
        self.connect_paramfield_signals()
        self.on_single_spatial_npoints_changed()
        self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Positioner Scan"
        self.idx = self.main_obj.get_scan_panel_order(__file__)
        self.type = scan_types.GENERIC_SCAN
        self.section_id = 'POSITIONER'
        devices = self.main_obj.get_devices()
        posner_keys = list(devices['POSITIONERS'].keys())
        posner_keys.sort()
        self.axis_strings = ['Detector Counts', '%s microns' % posner_keys[0], '', '']
        # use the mode that adjusts the zoneplate by calculating the zpz using the A0 mod
        self.zp_focus_mode = zp_focus_modes.A0MOD
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.SEG

        self._type_interactive_plot = False  # [scan_panel_order.POSITIONER_SCAN]
        self._type_skip_scan_q_table_plots = False  # [scan_panel_order.OSA_FOCUS_SCAN, scan_panel_order.FOCUS_SCAN]
        self._type_spectra_plot_type = True  # [scan_panel_order.POINT_SCAN, scan_panel_order.POSITIONER_SCAN]
        self._type_skip_centering_scans = False  # [scan_panel_order.FOCUS_SCAN, scan_panel_order.TOMOGRAPHY,
        # scan_panel_order.LINE_SCAN, scan_panel_order.POINT_SCAN, scan_panel_order.IMAGE_SCAN]
        self._type_do_recenter = False  # [scan_panel_order.IMAGE_SCAN, scan_panel_order.TOMOGRAPHY, scan_panel_order.LINE_SCAN]

        self._help_ttip = 'Positioner scan documentation and instructions'

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            if(self.main_obj.device(DNM_OSAY_TRACKING)):
                #make sure that the OSA vertical tracking is off if it is on
                self.osay_trcking_was = self.main_obj.device(DNM_OSAY_TRACKING).get_position()
                self.main_obj.device(DNM_OSAY_TRACKING).put(0) #off


    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            if(self.main_obj.device(DNM_OSAY_TRACKING)):
                #put the OSA vertical tracking back to its previous state
                self.main_obj.device(DNM_OSAY_TRACKING).put(self.osay_trcking_was)

        # call the base class defocus
        super(PositionerScanParam, self).on_plugin_defocus()

    def connect_paramfield_signals(self):

        mtr_x = self.main_obj.device(self.positioner)
        self.axis_strings = ['Detector Counts', '%s microns' % self.positioner, '', '']
        self.update_plot_strs.emit(self.axis_strings)
        
        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        
        rx = xhlm - xllm
        
        lim_dct = {}
        lim_dct['X'] = {'llm':xllm, 'hlm': xhlm, 'rng':rx}
        
        self.connect_param_flds_to_validator(lim_dct)
        
    def populate_positioner_cbox(self):
        devices = self.main_obj.get_devices()
        idx = 0
        keys = list(devices['POSITIONERS'].keys())
        keys.sort()
        for posner in keys:
            self.posnerComboBox.addItem(posner)
            self.posner_dct[posner] = idx
            idx += 1
        
    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the 
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()
        
        :returns: None
      
        """
        self.positioner = str(self.posnerComboBox.itemText(0)) 
        startx = float(str(self.startXFld.text())) 
        stopx = float(str(self.endXFld.text()))
        dwell = float(str(self.dwellFld.text()))
        nx = int(str(self.npointsXFld.text())) 
        sx = float(str(self.stepXFld.text()))
        #now create the model that this pluggin will use to record its params
        cx = (startx + stopx) * 0.5
        rx = stopx - startx
        x_roi = get_base_roi(SPDB_X, 'None', cx, rx, nx, sx)
        y_roi = get_base_roi(SPDB_Y, 'None', 0, 0, 0, enable=False)
        z_roi = get_base_roi(SPDB_Z, 'None', 0, 0, 0, enable=False)
                
        energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi('EV', DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False )
        
        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)    
    
    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the 
        positioners, if all is well return true else false
        
        This function should provide an explicit error log msg to aide the user
        '''
        ret = False
        if(len(self.positioner) > 0):
            ret = self.check_start_stop_x_scan_limits(self.positioner)
        return(ret)
    
    
    def positioner_changed(self, idx):
        posner = str(self.posnerComboBox.currentText())
        #print '%s selected' % posner
        self.positioner = posner
        self.connect_paramfield_signals()
    
    def set_dwell(self, dwell):
        self.set_parm(self.dwellFld, dwell)
        self.update_data()
    
    def set_roi(self, roi):
        """
        set_roi standard function supported by all scan pluggins to initialize the GUI for this scan with values
        stored in the defaults library
        
        :param roi: is a standard dict returned from the call to DEFAULTS.get_defaults()
        :type roi: dict.
    
        :returns: None
      
        """
        #print 'det_scan: set_roi: ' , roi
        (cx, cy, cz, c0) = roi[CENTER]
        (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (sx, sy, sz, s0) = roi[STEP]
        
        if('DWELL' in roi):
            self.set_parm(self.dwellFld, roi[DWELL])
        
        self.set_parm(self.startXFld, cx)
        self.set_parm(self.endXFld, rx)
        
        if(nx != None):
            self.set_parm(self.npointsXFld, nx, type='int', floor=2)
            
        if(sx != None):
            self.set_parm(self.stepXFld, sx, type='float', floor=0)
            
    
    def mod_roi(self, sp_db, do_recalc=True, sp_only=True):
        """
        sp_db is a widget_com dict
        The purpose of the mod_roi() function is to update the fields in the GUI with the correct values
        it can be called by either a signal from one of the edit fields (ex: self.startXFld) or
        by a signal from a plotter (via the main gui that is connected to the plotter) so that as a user
        grabs a region of interest marker in the plot and either moves or resizes it, those new center and size
        values will be delivered here and,  if required, the stepsizes will be recalculated
        
        
        :param sp_db: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type sp_db: dict.

        :param do_recalc: selectively the STEP of the ROI's for X and Y can be recalculated if the number of points or range have changed
        :type do_recalc: flag.
    
        :returns: None
      
        """
        self.sp_db[SPDB_X][START] = sp_db[SPDB_X][START]
        self.sp_db[SPDB_X][STOP] = sp_db[SPDB_X][STOP]
        
        x_roi = self.sp_db[SPDB_X]
        e_rois = self.sp_db[SPDB_EV_ROIS]
        
        if(do_recalc):
            on_range_changed(x_roi)
        
        self.set_parm(self.startXFld, x_roi[START])
        self.set_parm(self.endXFld, x_roi[STOP])
        
        if(e_rois[0][DWELL] != None):
            self.set_parm(self.dwellFld, e_rois[0][DWELL])
        
        if(x_roi[NPOINTS] != None):
            self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=2)
            
        if(x_roi[STEP] != None):
            self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)
    
    
    def load_roi(self, wdg_com, append=False, sp_only=False):
            """
            take a widget communications dict and load the plugin GUI with the spatial region, also
            set the scan subtype selection pulldown for point by point or line
            """
            
            #wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
            
            if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
                sp_db = get_first_sp_db_from_wdg_com(wdg_com)
                positioner = sp_db[SPDB_X][POSITIONER]
    
                if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != self.type):
                    return
                
                self.mod_roi(sp_db, do_recalc=False)
                
                idx = self.posner_dct[positioner]
                self.posnerComboBox.setCurrentIndex(idx)
                
            #emit roi_changed so that the plotter can be signalled to create the ROI shap items
            #self.roi_changed.emit(wdg_com)

#     def load_roi(self, wdg_com):
#         """
#         take a widget communications dict and load the plugin GUI with the spatial region, also
#         set the scan subtype selection pulldown for point by point or line
#         """
#             
#         if(wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
#             sp_db = get_first_sp_db_from_wdg_com(wdg_com)
#             positioner = sp_db[SPDB_X][POSITIONER]
#             if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != scan_types.GENERIC_SCAN):
#                 return
#             
#             idx = self.posner_dct[positioner]
#             self.posnerComboBox.setCurrentIndex(idx)
                
    def update_last_settings(self):
        """ update the 'default' settings that will be reloaded when this scan pluggin is selected again
        """
        x_roi = self.sp_db[SPDB_X]
        e_rois = self.sp_db[SPDB_EV_ROIS]
        
        DEFAULTS.set('SCAN.POSITIONER.CENTER', (x_roi[START], 0, 0, 0))
        DEFAULTS.set('SCAN.POSITIONER.RANGE', (x_roi[STOP], 0, 0, 0))
        DEFAULTS.set('SCAN.POSITIONER.NPOINTS', (x_roi[NPOINTS], 0, 0, 0))
        DEFAULTS.set('SCAN.POSITIONER.STEP', (x_roi[STEP], 0, 0, 0))
        DEFAULTS.set('SCAN.POSITIONER.DWELL', e_rois[0][DWELL])
        DEFAULTS.update()
    
    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        #update local widget_com dict
        y_roi = dct_get(self.sp_db, SPDB_Y)
        #make sure Y has 1 point
        y_roi["NPOINTS"] = 1
        wdg_com = self.update_single_spatial_wdg_com(positioner=self.positioner)
        self.update_last_settings()
        
        return(wdg_com)
    
    