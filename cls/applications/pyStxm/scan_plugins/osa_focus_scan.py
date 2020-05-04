'''
Created on Aug 25, 2014

@author: bergr
'''
'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import uic, QtCore

import os
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.applications.pyStxm.scan_plugins import plugin_dir
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, DEFAULTS
from cls.applications.pyStxm.scan_plugins.OsaFocusScan import OsaFocusScanClass
from bcm.devices.device_names import *
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from cls.data_io.stxm_data_io import STXMDataIo

from cls.utils.roi_utils import get_base_roi, get_base_start_stop_roi, get_base_energy_roi, make_spatial_db_dict
from cls.types.stxmTypes import scan_types, scan_panel_order, spatial_type_prefix
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)


class OsaFocusScanParam(ScanParamWidget):

    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi(os.path.join(plugin_dir, 'osa_focus_scan.ui'), self)

        self.setCenterBtn.clicked.connect(self.on_center_btn)
        self.loadScanBtn.clicked.connect(self.load_scan)

        self.scan_class = OsaFocusScanClass()
        
        self.sp_db = None
        self.load_from_defaults()
        self.init_sp_db()
        self.connect_paramfield_signals()
        self.on_focus_scan_single_spatial_npoints_changed()
        self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "OSA Focus Scan"
        self.idx = scan_panel_order.OSA_FOCUS_SCAN
        self.type = scan_types.OSA_FOCUS
        self.data = {}
        self.section_id = 'OSA_FOCUS'
        # override base parameter idxs for the get center and range calls, params are in a list [X, Y, Z, ?]
        self.p0_idx = 0
        self.p1_idx = 2
        # data_file_pfx = 'of'
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        # axis_strings = [<left>, <bottom>, <top>, <right>]
        self.axis_strings = ['ZP Z microns', 'OSA X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.FL
        self.plot_item_type = spatial_type_prefix.SEG
        self._help_ttip = 'OSA Focus scan documentation and instructions'

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            if (self.main_obj.device(DNM_OSAY_TRACKING, do_warn=False)):
                #make sure that the OSA vertical tracking is off if it is on
                self.osay_trcking_was = self.main_obj.device(DNM_OSAY_TRACKING).get_position()
                self.main_obj.device(DNM_OSAY_TRACKING).put(0) #off


    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            if (self.main_obj.device(DNM_OSAY_TRACKING, do_warn=False)):
                #put the OSA vertical tracking back to its previous state
                self.main_obj.device(DNM_OSAY_TRACKING).put(self.osay_trcking_was)

        # call the base class defocus
        super(OsaFocusScanParam, self).on_plugin_defocus()

    def connect_paramfield_signals(self):

        mtr_x = self.main_obj.device(DNM_OSA_X)
        mtr_y = self.main_obj.device(DNM_OSA_Y)
        mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z)
        
        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()
        zllm = mtr_z.get_low_limit()
        zhlm = mtr_z.get_high_limit()
                
        rx = xhlm - xllm
        ry = yhlm - yllm
        rz = zhlm - zllm
        
        lim_dct = {}
        lim_dct['X'] = {'llm':xllm, 'hlm': xhlm, 'rng':rx}
        lim_dct['Y'] = {'llm':yllm, 'hlm': yhlm, 'rng':ry}
        lim_dct['ZP'] = {'llm':zllm, 'hlm': zhlm, 'rng':rz}
        
        self.connect_param_flds_to_validator(lim_dct)
        
    def gen_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """    
        mtr_zpx = self.main_obj.device(DNM_OSA_X)
        mtr_zpy = self.main_obj.device(DNM_OSA_Y)
        
        xllm = mtr_zpx.get_low_limit()
        xhlm = mtr_zpx.get_high_limit()
        yllm = mtr_zpy.get_low_limit()
        yhlm = mtr_zpy.get_high_limit()
        
        bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.80) #%80 of max
        alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95) #%95 of max
                
        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond OSA Capabilities', get_alarm_fill_pattern())        
        normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'OSA Focus Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Nearing max Range of OSA X/Y', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of OSA X/Y', get_alarm_fill_pattern())
        
        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
        
    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the 
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()
        
        :returns: None
      
        """
        sx = float(str(self.startXFld.text())) 
        ex = float(str(self.endXFld.text()))
        sy = float(str(self.startYFld.text()))
        ey = float(str(self.endYFld.text()))
        
        dwell = float(str(self.dwellFld.text()))
        nx = int(str(self.npointsXFld.text())) #+ NUM_POINTS_LOST_AFTER_EDIFF  #+1 for the first data point being the row
        if(nx == 0):
            nx = 1
        ny = nx
        
        cz = float(str(self.centerZPFld.text())) 
        rz = float(str(self.rangeZPFld.text()))
        nz = int(str(self.npointsZPFld.text())) 
        
        #now create the model that this pluggin will use to record its params
        x_roi = get_base_start_stop_roi(SPDB_X, DNM_OSA_X, sx, ex, nx, src=self.main_obj.device(DNM_OSA_X).get_name())
        y_roi = get_base_start_stop_roi(SPDB_Y, DNM_OSA_Y, sy, ey, ny, src=self.main_obj.device(DNM_OSA_Y).get_name())
        zz_roi = get_base_roi(SPDB_ZZ, DNM_ZONEPLATE_Z_BASE, cz, rz, nz, enable=False, src=self.main_obj.device(DNM_ZONEPLATE_Z_BASE).get_name())

        energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi('EV', DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False )

        zp_rois = {}
        dct_put(zp_rois, SPDB_ZZ, zz_roi)

        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, zp_rois=zp_rois)


        
    
    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the 
        positioners, if all is well return true else false
        
        '''
        retxy = self.check_start_stop_xy_scan_limits(DNM_OSA_X, DNM_OSA_Y)
        retz = self.check_center_range_z_scan_limits(DNM_ZONEPLATE_Z)
        
        if(retxy and retz):
            return(True)
        else:
            return(False)
            
    def on_center_btn(self):
        sflag = self.main_obj.device('Zpz_scanModeFlag')
        a0 = self.main_obj.device('A0')
        #1 for OSA focus scan 0 for anything else
        sflag.put('user_setpoint', 0)
        
        zp_cent = float(str(self.centerZPFld.text()))
        #mtrz = self.main_obj.device(DNM_ZONEPLATE_Z)
        mtrz = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
        mtrx = self.main_obj.device(DNM_OSA_X)
        mtry = self.main_obj.device(DNM_OSA_Y)
        oz = self.main_obj.device(DNM_OSA_Z)
        
        mtrz.move(zp_cent)
        mtrz.confirm_stopped()
        
        fl = self.main_obj.device(DNM_FOCAL_LEN).get_position()
        mtrz.set_position(fl)
        mtrx.move(0.0)
        mtry.move(0.0)
    
    def set_roi(self, roi):
        """
        set_roi standard function supported by all scan pluggins to initialize the GUI for this scan with values
        stored in the defaults library
        
        :param roi: is a standard dict returned from the call to DEFAULTS.get_defaults()
        :type roi: dict.
    
        :returns: None
      
        """
        sx = sy = ex = ey = None
        (sx, sy, sz, s0) = roi[START]
        (ex, ey, ez, e0) = roi[STOP]

        (cx, cy, cz, c0) = roi[CENTER]
        (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (stpx, stpy, stpz, stp0) = roi[STEP]
        
        if('DWELL' in roi):
            self.set_parm(self.dwellFld, roi[DWELL])

        self.set_parm(self.startXFld, sx)
        self.set_parm(self.startYFld, sy)
        
        #we want the ZP center to always be the current Zpz pozition
        zpz_pos = self.main_obj.device(DNM_ZONEPLATE_Z).get_position()
        self.set_parm(self.centerZPFld, zpz_pos)
        
        if(ex != None):
            self.set_parm(self.endXFld, ex)
        
        if(ey != None):
            self.set_parm(self.endYFld, ey)
        
        if(rz != None):
            self.set_parm(self.rangeZPFld, rz)    
        
        if(nx != None):
            self.set_parm(self.npointsXFld, nx, type='int', floor=0)
        
        if(nz != None):
            self.set_parm(self.npointsZPFld, nz, type='int', floor=0)


    
    def mod_roi(self, sp_db, do_recalc=True, sp_only=False):
        """
        sp_db is a widget_com dict
        The purpose of the mod_roi() function is to update the fields in the GUI with the correct values
        it can be called by either a signal from one of the edit fields (ex: self.startXFld) or
        by a signal from a plotter (via the main gui that is connected to the plotter) so that as a user
        grabs a region of interest marker in the plot and either moves or resizes it, those new center and size
R        values will be delivered here and,  if required, the stepsizes will be recalculated
        
        
        :param sp_db: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type sp_db: dict.

        :param do_recalc: selectively the STEP of the ROI's for X and Y can be recalculated if the number of points or range have changed
        :type do_recalc: flag.
    
        :returns: None
      
        """
        self.focus_scan_mod_roi(sp_db, do_recalc)


    def update_last_settings(self):
        '''
        to be implemented by inheriting class
        example:
            update the 'default' settings that will be reloaded when this scan pluggin is selected again



        :return:
        '''
        x_roi = dct_get(self.sp_db, SPDB_X)
        y_roi = dct_get(self.sp_db, SPDB_Y)
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)
        #e_rois = self.sp_db[SPDB_EV_ROIS]
        e_rois = dct_get(self.sp_db, SPDB_EV_ROIS)

        DEFAULTS.set('SCAN.OSA_FOCUS.START', (x_roi[START], y_roi[START], zz_roi[START], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.STOP', (x_roi[STOP], y_roi[STOP], zz_roi[STOP], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.CENTER', (x_roi[CENTER], y_roi[CENTER], zz_roi[CENTER], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.RANGE', (x_roi[RANGE], y_roi[RANGE], zz_roi[RANGE], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], zz_roi[NPOINTS], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.STEP', (x_roi[STEP], y_roi[STEP], zz_roi[STEP], 0))
        DEFAULTS.set('SCAN.OSA_FOCUS.DWELL', e_rois[0][DWELL])
        DEFAULTS.update()

    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
        
        :param allow_signals: selectively allow the updating of the params to fire signals, this way we can prevent a change 
                                of a ZP param from updating the plot window
        :type allow_signals: flag.
        
        :returns: None
     
        """
        #force the subtype to be a PXP
        wdg_com = self.focus_scan_update_data(force_pxp=True)
        self.roi_changed.emit(wdg_com)
        return(wdg_com)
