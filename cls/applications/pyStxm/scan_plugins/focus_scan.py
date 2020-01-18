'''
Created on Aug 25, 2014

@author: bergr
'''
'''
Created on Aug 25, 2014

@author: bergr
'''

from PyQt5 import QtCore, uic


import os
from bcm.devices.device_names import *
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.applications.pyStxm.scan_plugins import plugin_dir

from cls.devWidgets.ophydLabelWidget import assign_aiLabelWidget

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS

#from cls.applications.pyStxm.scan_plugins.FocusSSCAN import FocusSSCAN
from cls.applications.pyStxm.scan_plugins.FocusScan import FocusScanClass
from cls.applications.pyStxm.scan_plugins.FocusE712Scan import FocusE712ScanClass

from bcm.devices.device_names import *
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from cls.data_io.stxm_data_io import STXMDataIo

from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.roi_utils import get_base_roi, get_base_start_stop_roi, get_base_energy_roi, make_spatial_db_dict, get_first_sp_db_from_wdg_com
from cls.utils.log import get_module_logger

from cls.types.stxmTypes import scan_types, scan_panel_order, spatial_type_prefix, sample_positioning_modes


MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
MAX_SCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_X')
MAX_SCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_Y')
#MAX_ZP_SUBSCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('MAX_ZP_SUBSCAN_RANGE_X')
#MAX_ZP_SUBSCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('MAX_ZP_SUBSCAN_RANGE_Y')



_logger = get_module_logger(__name__)

class FocusScanParam(ScanParamWidget):


    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi(  os.path.join( plugin_dir, 'focus_scan.ui'), self)

        self.scan_mod_path, self.scan_mod_name = self.derive_scan_mod_name(__file__)

        self.deltaA0FbkLbl = assign_aiLabelWidget(self.deltaA0FbkLbl, self.main_obj.device(DNM_DELTA_A0),
                                                  hdrText='Delta A0', egu='um',
                                                  title_color='white', var_clr='black')
        self.zpzFbkLbl = assign_aiLabelWidget(self.zpzFbkLbl, self.main_obj.device(DNM_ZPZ_RBV), hdrText='Zoneplate Z',
                                              egu='um',
                                              title_color='white', var_clr='black')
        self.flFbkLbl = assign_aiLabelWidget(self.flFbkLbl, self.main_obj.device(DNM_FOCAL_LENGTH),
                                             hdrText='Focal Length', egu='um',
                                             title_color='white', var_clr='black')

        self.setZPtoFocusBtn.clicked.connect(self.on_focus_zpz)
        self.setA0toFocusBtn.clicked.connect(self.on_focus_a0)
        self.loadScanBtn.clicked.connect(self.load_scan)
        self.testBtn.clicked.connect(self.do_test)
        self.resetDeltaA0Btn.clicked.connect(self.on_reset_delta_a0)

        #instanciate both because the non-E712 version is used for coarse scans
        self.scan_class_coarse = FocusScanClass(main_obj=self.main_obj)
        self.scan_class_e712 = FocusE712ScanClass(main_obj=self.main_obj)

        self.scan_class = self.scan_class_e712
        
        self.sp_db = None
        self.load_from_defaults()
        self.init_sp_db()
        self.connect_paramfield_signals()
        self.on_single_spatial_npoints_changed()
        self.init_loadscan_menu()

        #self.init_test_module()

        def on_plugin_focus(self):
            '''
            This is a function that is called when the plugin first receives focus from the main GUI
            :return:
            '''
            # make sure that the OSA vertical tracking is off if it is on
            if (self.isEnabled()):
                pass

        def on_plugin_defocus(self):
            '''
            This is a function that is called when the plugin leaves focus from the main GUI
            :return:
            '''
            if (self.isEnabled()):
                pass

            # call the base class defocus
            super(FocusScanParam, self).on_plugin_defocus()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Focus Scan"
        self.idx = scan_panel_order.FOCUS_SCAN
        self.type = scan_types.SAMPLE_FOCUS
        self.data = {}
        self.section_id = 'FOCUS'
        self.axis_strings = ['ZP Z microns', 'Sample X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        # data_file_pfx = 'f'
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.SEG
        self._help_ttip = 'Sample Focus scan documentation and instructions'

    def connect_paramfield_signals(self):
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            mtr_x = self.main_obj.device(DNM_GONI_X)
            mtr_y = self.main_obj.device(DNM_GONI_Y)
        else:
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
        
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

    def on_reset_delta_a0(self):
        a0 = self.main_obj.device(DNM_DELTA_A0)
        a0.put(0.0)

    def get_max_fine_scan_range(self):
        ''' to be implemented by inheriting class'''
        return(MAX_SCAN_RANGE_FINEX)
        
    def gen_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """    
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.gen_GONI_SCAN_max_scan_range_limit_def()
        else:
            mtr_sx = self.main_obj.device(DNM_SAMPLE_X)
            mtr_sy = self.main_obj.device(DNM_SAMPLE_Y)
        
            xllm = mtr_sx.get_low_limit()
            xhlm = mtr_sx.get_high_limit()
            yllm = mtr_sy.get_low_limit()
            yhlm = mtr_sy.get_high_limit()
            
            fxllm = 0.0 - (MAX_SCAN_RANGE_FINEX * 0.5)
            fxhlm = 0.0 + (MAX_SCAN_RANGE_FINEX * 0.5)
            fyllm = 0.0 - (MAX_SCAN_RANGE_FINEY * 0.5)
            fyhlm = 0.0 + (MAX_SCAN_RANGE_FINEY * 0.5)
            bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
            warn_qrect = QtCore.QRectF(QtCore.QPointF(fxllm, fyllm), QtCore.QPointF(fxhlm, fyhlm))
            alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.99) #%99 of max
                    
            bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond SampleXY Capabilities', get_alarm_fill_pattern())        
            normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Focus Fine Scan', get_normal_fill_pattern())
            warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Focus Coarse Scan', get_warn_fill_pattern())
            alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample X/Y', get_alarm_fill_pattern())
            
            self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
        
        
    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the 
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()
        
        :returns: None
      
        """
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.init_goniometer_sp_db()
        else:
            self.init_samplexy_sp_db()
                

    def init_samplexy_sp_db(self):
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
        x_roi = get_base_start_stop_roi(SPDB_X, DNM_SAMPLE_X, sx, ex, nx)
        y_roi = get_base_start_stop_roi(SPDB_Y, DNM_SAMPLE_Y, sy, ey, ny)
        zz_roi = get_base_roi(SPDB_ZZ, DNM_ZONEPLATE_Z, cz, rz, nz, enable=False)

        #zz_roi = get_base_roi(SPDB_ZZ, DNM_ZONEPLATE_Z, cz, rz, nz, enable=False)
        #zp_rois = {SPDB_ZZ: zz_roi}
        zp_rois = {}
        dct_put(zp_rois, SPDB_ZZ, zz_roi)

        energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi('EV', DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False )
        
        #self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)
        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, zp_rois=zp_rois)

    
    def init_goniometer_sp_db(self):
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
                
        # here we need to turn the absolute scan region (goni XY) that the user selected
        # into one that is centered around 0 as our ZP XY is
        scan_rect = QtCore.QRectF(QtCore.QPointF(sx, sy), QtCore.QPointF(ex, ey))
        scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
            
        #now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
        zx_roi = get_base_start_stop_roi(SPDB_ZX, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), nx, enable=True)
        zy_roi = get_base_start_stop_roi(SPDB_ZY, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), nx, enable=True)
        
        #now create the model that this pluggin will use to record its params
        gx_roi = get_base_start_stop_roi(SPDB_GX, DNM_GONI_X, sx, ex, nx)
        gy_roi = get_base_start_stop_roi(SPDB_GY, DNM_GONI_Y, sy, ey, ny)
        
        zz_roi = get_base_roi(SPDB_ZZ, DNM_ZONEPLATE_Z, cz, rz, nz, enable=False)
        
        energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi('EV', DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False )

        goni_rois = {}
        zp_rois = {}
        dct_put(goni_rois, SPDB_GX,  gx_roi)
        dct_put(goni_rois, SPDB_GY, gy_roi)

        dct_put(zp_rois, SPDB_ZX, zx_roi)
        dct_put(zp_rois, SPDB_ZY, zy_roi)
        dct_put(zp_rois, SPDB_ZZ, zz_roi)

        #self.sp_db = make_spatial_db_dict(z_roi = z_roi, e_roi=e_roi, goni_rois = goni_rois, zp_rois = zp_rois)
        #self.sp_db = make_spatial_db_dict(e_roi=e_roi)
        # x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
        self.sp_db = make_spatial_db_dict(x_roi=gx_roi, y_roi=gy_roi, e_roi=e_roi, goni_rois=goni_rois, zp_rois=zp_rois)

        
        #x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
#        dct_put(self.sp_db, SPDB_X, gx_roi)
#        dct_put(self.sp_db, SPDB_Y, gy_roi)
            
#         dct_put(self.sp_db, SPDB_ZX, zx_roi)
#         dct_put(self.sp_db, SPDB_ZY, zy_roi)
#         dct_put(self.sp_db, SPDB_ZZ, zz_roi)
#
# #         #it is fine the way it is
#         dct_put(self.sp_db, SPDB_GX, gx_roi)
#         dct_put(self.sp_db, SPDB_GY, gy_roi)
            
        
    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the 
        positioners, if all is well return true else false
        
        
        '''
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            return(self.check_goniometer_scan_limits())
        else:
            return(self.check_samplexy_scan_limits())
#         retxy = self.check_start_stop_xy_scan_limits('SampleX', 'SampleY')
#         retz = self.check_center_range_z_scan_limits('ZonePlateZ.Z')
#         
#         if(retxy and retz):
#             return(True)
#         else:
#             return(False)
    
    def check_samplexy_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the 
        positioners, if all is well return true else false
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        
        '''
        retxy = self.check_start_stop_xy_scan_limits(DNM_SAMPLE_X, DNM_SAMPLE_Y)
        retz = self.check_center_range_z_scan_limits(DNM_ZONEPLATE_Z)
        
        if(retxy and retz):
            return(True)
        else:
            return(False)
        
    def check_goniometer_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the 
        positioners, if all is well return true else false
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        
        '''
        retxy = self.check_start_stop_xy_scan_limits(DNM_GONI_X, DNM_GONI_Y)
        retz = self.check_center_range_z_scan_limits(DNM_ZONEPLATE_Z)
        
        if(retxy and retz):
            return(True)
        else:
            return(False)
        
    def on_select_focus(self, checked):
        if(checked):
            print('Focus_Scan: selection armed')
        else:
            print('Focus_Scan: selection disabled')
        
#     def dudon_focus_cz_btn(self):
#         """
#         From documsnt: Focusing procedures for CLS STXM
#             Auth: Adam Leontowich
#             Date: Nov 13, 2014    
#         
#         section 3.2.2.1 Focus to Cursor + set A0 for Autofocus
#         
#         """
#         #dat = self.get_local_params()
#         #(calcd_zpz, new_Cz) = focus_to_cursor_set_Cz(dat['fl'], dat['A0'], dat['idealA0'], dat['new_zpz'])
#         
#         sflag = self.main_obj.device('Zpz_scanFlag')
#         sflag.put(0)
#         #1 for OSA focus scan 0 for anything else
#         #mtrz = self.main_obj.device('ZonePlateZ.Z')
#         mtrz = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
#         fl = self.main_obj.device('Focal_Length').get_position()
#         theo_sample_in_focus = self.main_obj.device('Calcd_Zpz').get_position()
#         A0 = self.main_obj.device('A0').get_position()
#         idealA0 = self.main_obj.device('Ideal_A0').get_position()
#         new_zpz = float(str(self.centerZPFld.text())) 
#         
#         (calcd_zpz, A0updated) = focus_to_cursor_set_A0(fl, A0, idealA0, new_zpz)
#         self.main_obj.device('A0').put(A0updated)
#         mtrz.move(theo_sample_in_focus)
#         #move zpz to correct
#         #self.main_obj.device('Zpz_calcsetter').put(1)
    
    
    def on_focus_zpz(self):
        #sflag = self.main_obj.device('Zpz_scanModeFlag')
        #1 for OSA focus scan 0 for anything else
        #sflag.put('user_setpoint', 0)
        a0 = self.main_obj.device('A0')
        
        zp_cent = float(str(self.centerZPFld.text()))
        #mtrz = self.main_obj.device('ZonePlateZ.Z')
        mtrz = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
        mtrz.move(zp_cent)
        mtrz.confirm_stopped()
        
        fl = self.main_obj.device('Focal_Length').get_position()
        mtrz.set_position(fl)

        #added Jan 18 2018, if this btn is pressed need to reset delta to 0
        self.main_obj.device('Delta_A0').put(0.0)
    
    
#     def on_focus_zpz_new(self):
#         """
#         From document: Focusing procedures for CLS SM CryoStxm 
#             Auth: Adam Leontowich et al
#             Date: Jan , 2016    
#         
#            ...ZPz is moved to the value defined by the last cursor click
#            then OSAz 
#            A0 is updated, OSAz will not move and remain to be 0
#         
#         """
#         
#         zp_cent = float(str(self.centerZPFld.text()))
#         #mtrz = self.main_obj.device('ZonePlateZ.Z')
#         mtrz = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
#         mtrz.move(zp_cent)
#         mtrz.confirm_stopped()
#         
#         fl = self.main_obj.device('Focal_Length').get_position()
#         mtrz.set_position(fl)
    
    def on_focus_a0(self):
        """
        From document: Focusing procedures for CLS SM CryoStxm 
            Auth: Adam Leontowich et al
            Date: Jan , 2016    
        
           ...ZPz is moved to the value defined by the last cursor click
           then A0 is updated, OSAz will not move and remain to be 0
        
        """
        
        zp_cent = float(str(self.centerZPFld.text())) 
        theo_sample_in_focus = self.main_obj.device('Calcd_Zpz').get_position()
        #zpz_pos = self.main_obj.device(DNM_OSA_Z_BASE).get_position()
        delta = zp_cent - theo_sample_in_focus
        self.main_obj.device('Delta_A0').put(delta)
        #self.main_obj.device('A0ForCalc').put(zpz_pos - delta)

        #sflag = self.main_obj.device('Zpz_scanModeFlag')
        #sflag.put('user_setpoint', zp_focus_modes.A0MOD)
    
    
        
#     def on_focus_cz_btn(self):
#         """
#         From documsnt: Focusing procedures for CLS STXM
#             Auth: Adam Leontowich
#             Date: Nov 13, 2014    
#         
#         section 3.2.2.1 Focus to Cursor + set A0 for Autofocus
#         
#         Calculates a new Course Z position based on current A0 and theoretical
#         in focus distance
#         
#         """
#         zp_cent = float(str(self.centerZPFld.text())) 
#         theo_sample_in_focus = self.main_obj.device('Calcd_Zpz').get_position()
#         delta = zp_cent - theo_sample_in_focus
#         self.main_obj.device('delta_zpz').put(delta)
#         
#         sflag = self.main_obj.device('Zpz_scanFlag')
#         sflag.put(zp_scantype_flags.CZ)
        
    
#     def on_set_a0_for_auto_focus(self):
#         """
#         From document: Focusing procedures for CLS STXM
#             Auth: Adam Leontowich
#             Date: Nov 13, 2014    
#         
#         section 3.2.2.2 Focus to Cursor + set A0 for Autofocus
#         
#         """
#         
#         zp_cent = float(str(self.centerZPFld.text())) 
#         theo_sample_in_focus = self.main_obj.device('Calcd_Zpz').get_position()
#         delta = zp_cent - theo_sample_in_focus
#         self.main_obj.device('Delta_A0').put(delta)
#         
#         sflag = self.main_obj.device('Zpz_scanModeFlag')
#         sflag.put('user_setpoint', zp_focus_modes.A0MOD)
#         
        
#     def on_aaaafocus_a0_btn(self):
#         sflag = self.main_obj.device('Zpz_scanFlag')
#         sflag.put(0)
#         #1 for OSA focus scan 0 for anything else
#         mtrz = self.main_obj.device('ZonePlateZ.Z')
#         fl = self.main_obj.device('Focal_Length').get_position()
#         A0 = self.main_obj.device('A0').get_position()
#         idealA0 = self.main_obj.device('Ideal_A0').get_position()
#         new_zpz = float(str(self.centerZPFld.text())) 
#         
#         (calcd_zpz, A0updated) = focus_to_cursor_set_A0(fl, A0, idealA0, new_zpz)
#         self.main_obj.device('A0').put(A0updated)
#         mtrz.move(new_zpz)
                    
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
        # self.set_parm(self.startXFld, cx)
        # self.set_parm(self.startYFld, cy)
        #we want the ZP center to always be the current Zpz pozition
        zpz_pos = self.main_obj.device(DNM_ZONEPLATE_Z).get_position()
        self.set_parm(self.centerZPFld, zpz_pos)

        if (ex != None):
            self.set_parm(self.endXFld, ex)

        if (ey != None):
            self.set_parm(self.endYFld, ey)

        if (rz != None):
            self.set_parm(self.rangeZPFld, rz)

        if (nx != None):
            self.set_parm(self.npointsXFld, nx, type='int', floor=0)

        if (nz != None):
            self.set_parm(self.npointsZPFld, nz, type='int', floor=0)

    def mod_roi(self, sp_db, do_recalc=True, sp_only=False):
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
        self.focus_scan_mod_roi(sp_db, do_recalc)


    def determine_scan_class(self):
        '''
        check the scan range and set the sscan class to use, if its a fine scan then use the E712 for the piezo's else
        it is a coarse scan so use the coarse (original) version
        :return:
        '''

        xrng = dct_get(self.sp_db, SPDB_XRANGE)
        if(xrng > MAX_SCAN_RANGE_FINEX):
            #use coarse
            self.scan_class = self.scan_class_coarse
            _logger.info('focus scan range is larger than MAX_SCAN_RANGE_FINEX, using FocusSSCAN')
        else:
            #use fine
            self.scan_class = self.scan_class_e712
            #_logger.info('focus scan range is within MAX_SCAN_RANGE_FINEX, using FocusSSCAN_E712')

    def update_last_settings(self):
        '''
        to be implemented by inheriting class
        example:
            update the 'default' settings that will be reloaded when this scan pluggin is selected again
        :return:
        '''
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        zz_roi = dct_get(self.sp_db, SPDB_ZZ)
        e_rois = self.sp_db[SPDB_EV_ROIS]

        DEFAULTS.set('SCAN.FOCUS.START', (x_roi[START], y_roi[START], zz_roi[START], 0))
        DEFAULTS.set('SCAN.FOCUS.STOP', (x_roi[STOP], y_roi[STOP], zz_roi[STOP], 0))
        DEFAULTS.set('SCAN.FOCUS.CENTER', (x_roi[CENTER], y_roi[CENTER], zz_roi[CENTER], 0))
        DEFAULTS.set('SCAN.FOCUS.RANGE', (x_roi[RANGE], y_roi[RANGE], zz_roi[RANGE], 0))
        DEFAULTS.set('SCAN.FOCUS.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], zz_roi[NPOINTS], 0))
        DEFAULTS.set('SCAN.FOCUS.STEP', (x_roi[STEP], y_roi[STEP], zz_roi[STEP], 0))
        DEFAULTS.set('SCAN.FOCUS.DWELL', e_rois[0][DWELL])
        DEFAULTS.update()

    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """

        # need to set which instance of the sscan class to use
        #self.determine_scan_class()

        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            wdg_com = self.focus_scan_update_data()
            wdg_com = self.add_goni_rois(wdg_com) 
        else:
            wdg_com = self.focus_scan_update_data()
        
        self.roi_changed.emit(wdg_com)    
        return(wdg_com)
    
    
    #########################################################################
    #  Goniometer specific routines
    #########################################################################
    
    
    def add_goni_rois(self, wdg_com):
        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)
        mtr_gz = self.main_obj.device(DNM_GONI_Z)
        mtr_gt = self.main_obj.device(DNM_GONI_THETA)
        mtr_oz = self.main_obj.device(DNM_OSA_Z)
        
        self.sp_db = get_first_sp_db_from_wdg_com(wdg_com)
        gx_roi = dct_get(self.sp_db, SPDB_X)
        gy_roi = dct_get(self.sp_db, SPDB_Y)
        
        nx = gx_roi[NPOINTS]
        rect  = self.sp_db[SPDB_RECT]
        scan_rect = QtCore.QRectF(QtCore.QPointF(gx_roi[START], gy_roi[START]), QtCore.QPointF(gx_roi[STOP], gy_roi[STOP]))
        
        dx = scan_rect.center().x() - mtr_gx.get_position()  
        dy = scan_rect.center().y() - mtr_gy.get_position() 
        
        if((abs(dx) > 30.0) or (abs(dy) > 30.0)):
            #scan is larger than the zoneplate can handle so we will be moving the goni X/Y to center of scan thus it
            #will be centered around 0,0
            scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
            osax_center = 0.0
            osay_center = 0.0
            
            gonix_center = dct_get(self.sp_db, SPDB_XCENTER)
            goniy_center = dct_get(self.sp_db, SPDB_YCENTER)
            
        else:    
            scan_rect.moveCenter(QtCore.QPointF(dx, dy))
            #only need to offset OSA X by %50 of the total dx to achieve even illumination
            osax_center = dx #* 2.0
            osay_center = dy #* 2.0
            #leave at current position
            gonix_center = mtr_gx.get_position()
            goniy_center = mtr_gy.get_position()
        
        x_roi = get_base_roi(SPDB_GX, DNM_GONI_X, dct_get(self.sp_db, SPDB_XCENTER), dct_get(self.sp_db, SPDB_XRANGE), dct_get(self.sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        y_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, dct_get(self.sp_db, SPDB_YCENTER), dct_get(self.sp_db, SPDB_YRANGE), dct_get(self.sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        
        #now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
        zx_roi = get_base_start_stop_roi(SPDB_ZX, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), nx, enable=True)
        zy_roi = get_base_start_stop_roi(SPDB_ZY, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), nx, enable=True)
        
        #now create the model that this pluggin will use to record its params
        gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, gonix_center, dct_get(self.sp_db, SPDB_XRANGE), dct_get(self.sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, goniy_center, dct_get(self.sp_db, SPDB_YRANGE), dct_get(self.sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        
        gt_roi = get_base_start_stop_roi(SPDB_GT, DNM_GONI_THETA, mtr_gt.get_position(), mtr_gt.get_position(), 1, enable=True)
        gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, gonix_center, dct_get(self.sp_db, SPDB_XRANGE), dct_get(self.sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, goniy_center, dct_get(self.sp_db, SPDB_YRANGE), dct_get(self.sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
        gz_roi = get_base_roi(SPDB_GZ, DNM_GONI_Z, mtr_gz.get_position(), 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=True)
        
        self.apply_correction_model(gx_roi, gy_roi, gz_roi, gt_roi)
        
        ox_roi = get_base_roi(SPDB_OX, DNM_OSA_X, osax_center, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=False)
        oy_roi = get_base_roi(SPDB_OY, DNM_OSA_Y, osay_center, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=False)
        #Z disabled for now
        oz_roi = get_base_roi(SPDB_OZ, DNM_OSA_Z, mtr_oz.get_position(), 0, 1, stepSize=None, max_scan_range=None, enable=False, is_point=False)
        
        #this needs to be handled properly for multi subspatial
        ox_roi[SETPOINTS] = [ox_roi[CENTER]]
        oy_roi[SETPOINTS] = [oy_roi[CENTER]]
        oz_roi[SETPOINTS] = [oz_roi[CENTER]]    
        
        #x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
        dct_put(self.sp_db, SPDB_X, x_roi)
        dct_put(self.sp_db, SPDB_Y, y_roi)
             
        dct_put(self.sp_db, SPDB_ZX, zx_roi)
        dct_put(self.sp_db, SPDB_ZY, zy_roi)
             
#         #it is fine the way it is
        dct_put(self.sp_db, SPDB_GX, gx_roi)
        dct_put(self.sp_db, SPDB_GY, gy_roi)
        
        dct_put(self.sp_db, SPDB_OX, ox_roi)
        dct_put(self.sp_db, SPDB_OY, oy_roi)
        dct_put(self.sp_db, SPDB_OZ, oz_roi)
        
#         mtr_gx = self.main_obj.device(DNM_GONI_X)
#         mtr_gy = self.main_obj.device(DNM_GONI_Y)
#          
#         self.sp_db = get_first_sp_db_from_wdg_com(wdg_com)
#         gx_roi = dct_get(self.sp_db, SPDB_X)
#         gy_roi = dct_get(self.sp_db, SPDB_Y)
#          
#         nx = gx_roi[NPOINTS]
#         # here we need to turn the absolute scan region (goni XY) that the user selected
#         # into one that is centered around 0 as our ZP XY is
#         scan_rect = QtCore.QRectF(QtCore.QPointF(gx_roi[START], gy_roi[START]), QtCore.QPointF(gx_roi[STOP], gy_roi[STOP]))
#         dx = scan_rect.center().x() - mtr_gx.get_position() 
#         dy = scan_rect.center().y() - mtr_gy.get_position() 
#              
#         if((abs(dx) > 30.0) or (abs(dy) > 30.0)):
#             scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
#         else:    
#             scan_rect.moveCenter(QtCore.QPointF(dx, dy))
#              
#         #now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
#         zx_roi = get_base_start_stop_roi(SPDB_ZX, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), nx, enable=True)
#         zy_roi = get_base_start_stop_roi(SPDB_ZY, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), nx, enable=True)
#          
#         #now create the model that this pluggin will use to record its params
#         gx_roi = get_base_start_stop_roi(SPDB_GX, DNM_GONI_X, gx_roi[START], gx_roi[STOP], nx)
#         gy_roi = get_base_start_stop_roi(SPDB_GY, DNM_GONI_Y, gy_roi[START], gy_roi[STOP], nx)
#          
#         #x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
#         dct_put(self.sp_db, SPDB_X, gx_roi)
#         dct_put(self.sp_db, SPDB_Y, gy_roi)
#              
#         dct_put(self.sp_db, SPDB_ZX, zx_roi)
#         dct_put(self.sp_db, SPDB_ZY, zy_roi)
#              
# #         #it is fine the way it is
#         dct_put(self.sp_db, SPDB_GX, gx_roi)
#         dct_put(self.sp_db, SPDB_GY, gy_roi)

        #self.sp_db = get_first_sp_db_from_wdg_com(wdg_com)
        #self.sp_db = self.modify_sp_db_for_goni(get_first_sp_db_from_wdg_com(wdg_com), is_focus=True)

        return(wdg_com)
    
    
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
        return(new_x, new_y, new_z)     
    
    def apply_correction_model(self, gx_roi, gy_roi, gz_roi, gt_roi):
        x = gx_roi[SETPOINTS][0]
        y = gy_roi[SETPOINTS][0]
        z = gz_roi[SETPOINTS][0]
        idx = 0
        for t in gt_roi[SETPOINTS]:
            gx_roi[idx], gy_roi[idx], gz_roi[idx] = self.calc_correction(x, y, z, t) 
            idx += 1
    
    # def gen_GONI_SCAN_max_scan_range_limit_def(self):
    #     """ to be overridden by inheriting class
    #     """
    #     mtr_zpx = self.main_obj.device(DNM_ZONEPLATE_X)
    #     mtr_zpy = self.main_obj.device(DNM_ZONEPLATE_Y)
    #     #mtr_osax = self.main_obj.device('OSAX.X')
    #     #mtr_osay = self.main_obj.device('OSAY.Y')
    #     mtr_gx = self.main_obj.device(DNM_GONI_X)
    #     mtr_gy = self.main_obj.device(DNM_GONI_Y)
    #
    #     gx_pos = mtr_gx.get_position()
    #     gy_pos = mtr_gy.get_position()
    #
    #     #these are all added because the sign is in the LLIM
    #     xllm = gx_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
    #     xhlm = gx_pos + (MAX_SCAN_RANGE_FINEY * 0.5)
    #     yllm = gy_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
    #     yhlm = gy_pos + (MAX_SCAN_RANGE_FINEY * 0.5)
    #
    #     gxllm = mtr_gx.get_low_limit()
    #     gxhlm = mtr_gx.get_high_limit()
    #     gyllm = mtr_gy.get_low_limit()
    #     gyhlm = mtr_gy.get_high_limit()
    #
    #     bounding_qrect = QtCore.QRectF(QtCore.QPointF(gxllm, gyhlm), QtCore.QPointF(gxhlm, gyllm))
    #     #warn_qrect = self.get_percentage_of_qrect(bounding, 0.90) #%80 of max
    #     #alarm_qrect = self.get_percentage_of_qrect(bounding, 0.95) #%95 of max
    #     normal_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
    #     warn_qrect = self.get_percentage_of_qrect(normal_qrect, 1.01) #%95 of max
    #     alarm_qrect = self.get_percentage_of_qrect(normal_qrect, 1.0) #%95 of max
    #
    #     bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Goniometer Capabilities', get_alarm_fill_pattern())
    #     normal = ROILimitObj(normal_qrect, get_normal_clr(45), 'Fine ZP Scan', get_normal_fill_pattern())
    #     warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Goniometer will be required to move', get_warn_fill_pattern())
    #     alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Range is beyond ZP Capabilities', get_alarm_fill_pattern())
    #
    #     self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)
        
        
