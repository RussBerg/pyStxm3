'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import QtCore, QtGui
from PyQt5 import uic
import os
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.applications.pyStxm.scan_plugins import plugin_dir
from cls.applications.pyStxm.scan_plugins.LineSpecScan import LineSpecScanClass
#from cls.applications.pyStxm.scan_plugins.LineSpecSSCANWithE712Wavegen import LineSpecSSCAN
from cls.applications.pyStxm.scan_plugins.LineSpecSSCANWithE712WavegenScan import LineSpecScanWithE712WavegenClass
from bcm.devices.device_names import *
from cls.data_io.stxm_data_io import STXMDataIo

from cls.types.stxmTypes import scan_types, scan_sub_types, scan_panel_order, spatial_type_prefix, sample_positioning_modes, scan_image_types
#from cls.scanning.ScanTableView import MultiRegionWidget
from cls.applications.pyStxm.widgets.scan_table_view.multiRegionWidget import MultiRegionWidget
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types, get_unique_roi_id, \
                on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
                                on_center_changed, recalc_setpoints, get_first_sp_db_from_wdg_com, get_base_start_stop_roi, get_base_roi
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
MAX_SCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_X')
MAX_SCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_Y')
USE_E712_HDW_ACCEL = MAIN_OBJ.get_preset_as_int('USE_E712_HDW_ACCEL')

class LineScansParam(ScanParamWidget):

    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        #uic.loadUi(plugin_dir + '\\image_lxl_scan.ui', self)
        uic.loadUi( os.path.join(plugin_dir, 'line_scan.ui'), self)
        self.epu_supported = False
        self.goni_supported = False

        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.goni_supported = True
            x_cntr = self.main_obj.device(DNM_GONI_X).get_position()
            y_cntr = self.main_obj.device(DNM_GONI_Y).get_position()
        else:
            x_cntr = self.main_obj.device(DNM_SAMPLE_X).get_position()
            y_cntr = self.main_obj.device(DNM_SAMPLE_Y).get_position()

        #self.multi_region_widget = MultiRegionWidget(use_center=False, is_arb_line=True, enable_multi_spatial=self.enable_multi_region, max_range=MAX_SCAN_RANGE_FINEX) #instead of using centerx etc use startX
        self.multi_region_widget = MultiRegionWidget(use_center=False, is_arb_line=True,
                                                     enable_multi_spatial=self.enable_multi_region, \
                                                     max_range=MAX_SCAN_RANGE_FINEX, use_hdw_accel=False, min_sp_rois=1,
                                                     x_cntr=x_cntr,
                                                     y_cntr=y_cntr, main_obj=self.main_obj)  # instead of using centerx etc use startX
        self.epu_supported = False

        if(not self.main_obj.is_device_supported(DNM_EPU_POLARIZATION)):

            self.multi_region_widget.deslect_all_polarizations()
            self.multi_region_widget.disable_polarization_table(True)
            self.multi_region_widget.set_polarization_table_visible(False)
        else:
            self.epu_supported = True
            self.multi_region_widget.deslect_all_polarizations()
            self.multi_region_widget.disable_polarization_table(False)
            self.multi_region_widget.set_polarization_table_visible(True)

        self.multi_region_widget.spatial_row_selected.connect(self.on_spatial_row_selected)
        self.multi_region_widget.spatial_row_changed.connect(self.on_spatial_row_changed)
        self.multi_region_widget.spatial_row_deleted.connect(self.on_spatial_row_deleted)
        
        self.evGrpBox.layout().addWidget(self.multi_region_widget)
        #self.scanTypeSelComboBox.currentIndexChanged.connect(self.scan_subtype_changed)

        self.loadScanBtn.clicked.connect(self.load_scan)
        #self.singleEVChkBx.clicked.connect(self.on_single_energy)
        if(USE_E712_HDW_ACCEL):
            self.scan_class = LineSpecScanWithE712WavegenClass(main_obj=self.main_obj)
        else:
            self.scan_class = LineSpecScanClass(main_obj=self.main_obj)

        self.sub_type_override = self.sub_type
        
        self.wdg_com = None
        self.load_from_defaults()
        #self.on_plugin_focus()
        self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Line Scan"
        self.idx = scan_panel_order.LINE_SCAN  # by default
        self.type = scan_types.SAMPLE_LINE_SPECTRA
        self.data = {}
        self.section_id = 'LINE'
        self.axis_strings = ['XY microns', 'Energy eV', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.SEG
        #self.enable_multi_region = self.main_obj.get_is_multi_region_enabled()
        self.enable_multi_region = False
        self.multi_ev = True
        self.sp_db = None

    def on_plugin_focus(self):
        '''
        this is called when this scan param receives focus on the GUI
        - basically get the current EPU values and assign them to the multiregion widget
        :return:
        '''
        if (self.isEnabled()):
            # call the standard init_base_values function for scan param widgets that contain a multiRegionWidget
            self.on_multiregion_widget_focus_init_base_values()
        super(LineScansParam, self).on_plugin_focus()

    def on_plugin_defocus(self):
        '''
            this is called when this scan param loses focus on the GUI

        :return:
        '''
        super(LineScansParam, self).on_plugin_defocus()


    def clear_params(self):
        """ meant to clear all params from table """
        self.multi_region_widget.clear_spatial_table()
    
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
            
            bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
            warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95) #%95 of max
            alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 1.0) #%100 of max
                    
            bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond SampleXY Capabilities', get_alarm_fill_pattern())        
            normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Line Scan (Fine)', get_normal_fill_pattern())
            warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Line Scan (Coarse)', get_warn_fill_pattern())
            alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample X/Y', get_alarm_fill_pattern())
            
            self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
    
    def scan_subtype_changed(self, idx):
        if(idx == 0):
            #line unidir
            self.sub_type = scan_sub_types.LINE_UNIDIR
        else:
            #point by point
            self.sub_type = scan_sub_types.POINT_BY_POINT
            
    def set_roi(self, roi):
        (sx, sy, sz, s0) = roi[START]
        (stpx, stpy, stpz, stp0) = roi[STOP]
        (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (stepx, stepy, stepz, step0) = roi[STEP]
        
        dwell = roi[DWELL]

        scan = self.multi_region_widget.get_spatial_row_data(0)

        dct_put(scan, SPDB_XSTART, sx)
        dct_put(scan, SPDB_XSTOP, stpx)
        dct_put(scan, SPDB_XRANGE, rx)
        dct_put(scan, SPDB_XNPOINTS, nx)
        dct_put(scan, SPDB_XSTEP, stepx)

        dct_put(scan, SPDB_YSTART, sy)
        dct_put(scan, SPDB_YSTOP, stpy)
        dct_put(scan, SPDB_YRANGE, ry)
        dct_put(scan, SPDB_YNPOINTS, ny)
        dct_put(scan, SPDB_YSTEP, stepy)

        
    def mod_roi(self, sp_db, do_recalc=True, ev_only=False, sp_only=False):
        """
        wdg_com is a widget_com dict
        The purpose of the mod_roi() function is to update the fields in the GUI with the correct values
        it can be called by either a signal from one of the edit fields (ex: self.centerXFld) or
        by a signal from a plotter (via the main gui that is connected to the plotter) so that as a user
        grabs a region of interest marker in the plot and either moves or resizes it, those new center and size
        values will be delivered here and,  if required, the stepsizes will be recalculated
        
        
        :param wdg_com: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type wdg_com: dict.

        :param do_recalc: selectively the STEP of the ROI's for X and Y can be recalculated if the number of points or range have changed
        :type do_recalc: flag.
    
        :returns: None
      
        """
        item_id = dct_get(sp_db, SPDB_ID_VAL)
        dct_put(sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)

        if(sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)
            if(cur_scan != None):
                #change the command to add this ROI
                sp_db[CMND] = widget_com_cmnd_types.ROI_CHANGED
        
        if(sp_db[CMND] == widget_com_cmnd_types.ROI_CHANGED):
            #we are being modified by the plotter
            x_roi = sp_db[SPDB_X]
            y_roi = sp_db[SPDB_Y]
            scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)
            if(cur_scan is None):
                scan[SPDB_ID_VAL] = item_id
                on_npoints_changed(scan[SPDB_X])
                on_npoints_changed(scan[SPDB_Y])
                #self.multi_region_widget.sp_widg.table_view.add_scan(scan, wdg_com['CURRENT']['PLOT']['ITEM']['ID'])
                self.multi_region_widget.sp_widg.on_new_region(scan)
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                
            else:
                #cur_scan = self.multi_region_widget.sp_widg.table_view.get_scan(item_id)
                #update the center and range fields that have come from the plotter
                #first call center recalc, then range
                cur_scan[SPDB_X][START] = scan[SPDB_X][START]
                on_start_changed(cur_scan[SPDB_X])
                
                cur_scan[SPDB_X][STOP] = scan[SPDB_X][STOP]
                on_stop_changed(cur_scan[SPDB_X])
                
                cur_scan[SPDB_Y][START] = scan[SPDB_Y][START]
                on_start_changed(cur_scan[SPDB_Y])
                
                cur_scan[SPDB_Y][STOP] = scan[SPDB_Y][STOP]
                on_stop_changed(cur_scan[SPDB_Y])
                
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                self.multi_region_widget.sp_widg.modify_row_data(item_id, cur_scan)

        elif(sp_db[CMND] == widget_com_cmnd_types.DEL_ROI):
            #remove this roi from the multi region spatial table
            self.multi_region_widget.sp_widg.delete_row(item_id)            
        
        elif (sp_db[CMND] == widget_com_cmnd_types.DESELECT_ROI):
            # _logger.debug('mod_roi: calling deselect_all() ')
            self.multi_region_widget.sp_widg.deselect_all()
            
        else:
             
            _logger.error('image_scan: mod_roi: unsupported widget_com CMND [%d]' % sp_db[CMND])
            return    
    
    def load_roi(self, wdg_com, append=False, ev_only=False, sp_only=False):
        """
        take a widget communications dict and load the plugin GUI with the spatial region, also
        set the scan subtype selection pulldown for point by point or line
        """
        #wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        if(wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            sp_roi_dct = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
            sp_ids = list(sp_roi_dct.keys())
            sp_id = sp_ids[0]
            sp_db = sp_roi_dct[sp_id]

            if(not ev_only and (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != scan_types.SAMPLE_LINE_SPECTRA)):
                return

            # if(not ev_only):
            #     if(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE) == scan_sub_types.LINE_UNIDIR):
            #         #image Line Unidir
            #         self.scanTypeSelComboBox.setCurrentIndex(1)
            #     else:
            #         #line Point by Point
            #         self.scanTypeSelComboBox.setCurrentIndex(0)
            #
            self.multi_region_widget.load_scan(wdg_com, ev_only=ev_only)
            #emit roi_changed so that the plotter can be signalled to create the ROI shape items
            if (not self.multi_region_widget.is_spatial_list_empty()):
                self.roi_changed.emit(wdg_com)
    
    def on_single_energy(self, val):
        self.single_energy = val
#         if(not val):
#             pass
#         else:
#             self.ev_select_widget.on_single_ev()
#        self.update_data()
    
    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.wdg_com = self.GONI_SCAN_update_data()
        else:
            self.wdg_com = self.update_multi_spatial_wdg_com()
        
        sp_db = get_first_sp_db_from_wdg_com(self.wdg_com)

        y_roi = dct_get(sp_db, SPDB_Y)
        if(y_roi):
            #self.sub_type_override = self.scanTypeSelComboBox.currentIndex()
            if(y_roi[START] == y_roi[STOP]):
                self.sub_type = scan_sub_types.LINE_UNIDIR
            else:
                self.sub_type = scan_sub_types.POINT_BY_POINT
            
            # #allow the user to override the subtype
            # if(self.sub_type == scan_sub_types.LINE_UNIDIR):
            #     if(self.sub_type_override == scan_sub_types.POINT_BY_POINT):
            #         self.sub_type = scan_sub_types.POINT_BY_POINT
        
        dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
        self.sp_db = sp_db
        self.update_last_settings()

        self.roi_changed.emit(self.wdg_com)
        return(self.wdg_com)
    
    #########################################################################
    #  Goniometer specific routines
    #########################################################################
    
    
    def add_goni_rois(self, wdg_com):
        
        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)
        
        self.sp_db = get_first_sp_db_from_wdg_com(wdg_com)
        gx_roi = dct_get(self.sp_db, SPDB_X)
        gy_roi = dct_get(self.sp_db, SPDB_Y)
        
        nx = gx_roi[NPOINTS]
        # here we need to turn the absolute scan region (goni XY) that the user selected
        # into one that is centered around 0 as our ZP XY is
        scan_rect = QtCore.QRectF(QtCore.QPointF(gx_roi[START], gy_roi[START]), QtCore.QPointF(gx_roi[STOP], gy_roi[STOP]))
        dx = scan_rect.center().x() - mtr_gx.get_position() 
        dy = scan_rect.center().y() - mtr_gy.get_position() 
            
        if((abs(dx) > 30.0) or (abs(dy) > 30.0)):
            scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
        else:    
            scan_rect.moveCenter(QtCore.QPointF(dx, dy))
            
        #now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
        zx_roi = get_base_start_stop_roi(SPDB_ZX, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), nx, enable=True)
        zy_roi = get_base_start_stop_roi(SPDB_ZY, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), nx, enable=True)
        
        #now create the model that this pluggin will use to record its params
        gx_roi = get_base_start_stop_roi(SPDB_GX, DNM_GONI_X, gx_roi[START], gx_roi[STOP], nx)
        gy_roi = get_base_start_stop_roi(SPDB_GY, DNM_GONI_Y, gy_roi[START], gy_roi[STOP], nx)
        
        #x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
        dct_put(self.sp_db, SPDB_X, gx_roi)
        dct_put(self.sp_db, SPDB_Y, gy_roi)
            
        dct_put(self.sp_db, SPDB_ZX, zx_roi)
        dct_put(self.sp_db, SPDB_ZY, zy_roi)
            
#         #it is fine the way it is
        dct_put(self.sp_db, SPDB_GX, gx_roi)
        dct_put(self.sp_db, SPDB_GY, gy_roi)
        
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
    #     xhlm = gx_pos + (MAX_SCAN_RANGE_FINEX * 0.5)
    #     yllm = gy_pos - (MAX_SCAN_RANGE_FINEY * 0.5)
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

    def gen_GONI_SCAN_max_scan_range_limit_def(self):
        '''
        this function creates the boundaries for the plotter to use when selecting new scan areas based on :
         - the line scan is only allowed within the range of the current zoneplate position and zoneplate range, no
          lines requiring a move by the goniometer are allowed as the repeatability of hte poistioning is not good enough
         so: find the current center and range and setup boundaries
        :return:
        '''
        """ to be overridden by inheriting class
                """
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
        xhlm = gx_pos + (MAX_SCAN_RANGE_FINEX * 0.5)
        yllm = gy_pos - (MAX_SCAN_RANGE_FINEY * 0.5)
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
        #
        # mtr_zpx = self.main_obj.device(DNM_ZONEPLATE_X)
        # mtr_zpy = self.main_obj.device(DNM_ZONEPLATE_Y)
        # # mtr_osax = self.main_obj.device('OSAX.X')
        # # mtr_osay = self.main_obj.device('OSAY.Y')
        # mtr_gx = self.main_obj.device(DNM_GONI_X)
        # mtr_gy = self.main_obj.device(DNM_GONI_Y)
        #
        # gx_pos = mtr_gx.get_position()
        # gy_pos = mtr_gy.get_position()
        #
        # # these are all added because the sign is in the LLIM
        # xllm = gx_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
        # xhlm = gx_pos + (MAX_SCAN_RANGE_FINEX * 0.5)
        # yllm = gy_pos - (MAX_SCAN_RANGE_FINEY * 0.5)
        # yhlm = gy_pos + (MAX_SCAN_RANGE_FINEY * 0.5)
        #
        # # gxllm = mtr_gx.get_low_limit()
        # # gxhlm = mtr_gx.get_high_limit()
        # # gyllm = mtr_gy.get_low_limit()
        # # gyhlm = mtr_gy.get_high_limit()
        # #
        # # zxllm = mtr_zpx.get_low_limit()
        # # zxhlm = mtr_zpx.get_high_limit()
        # # zyllm = mtr_zpy.get_low_limit()
        # # zyhlm = mtr_zpy.get_high_limit()
        #
        #
        # bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        # # warn_qrect = self.get_percentage_of_qrect(bounding, 0.90) #%80 of max
        # # alarm_qrect = self.get_percentage_of_qrect(bounding, 0.95) #%95 of max
        # normal_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        # warn_qrect = self.get_percentage_of_qrect(normal_qrect, 1.01)  # %95 of max
        # alarm_qrect = self.get_percentage_of_qrect(normal_qrect, 1.0)  # %95 of max
        #
        # bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Goniometer Capabilities',
        #                        get_alarm_fill_pattern())
        # normal = ROILimitObj(normal_qrect, get_normal_clr(45), 'SEG', get_normal_fill_pattern())
        # warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Goniometer will be required to move',
        #                    get_warn_fill_pattern())
        # alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Range is beyond ZP Capabilities',
        #                     get_alarm_fill_pattern())
        #
        # self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)

    def create_sub_spatial_dbs(self, wdg_com):
        """
        Given a set of spatial region dbs, subdivide them into spatial regions that are within the scan range of the 
        Zoneplate X and Y, each sub spatial region represents the area that can be scanned when the OSA XY is positioned at the regions center.
        If the desired scan area is smaller than the max subscan range then just return the original spatial region 
        
        This function creates a dict of sub spatial regions as well, the OSA XY position for each sub spatial region can be 
        taken from (x_roi[CENTER], y_roi[CENTER])
        
        :returns: None
     
        """
        sub_spatials = {}
        sp_dbs = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
        
        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)
        mtr_gz = self.main_obj.device(DNM_GONI_Z)
        mtr_gt = self.main_obj.device(DNM_GONI_THETA)
        mtr_oz = self.main_obj.device(DNM_OSA_Z)
        
        for sp_id in sp_dbs:
            sp_db = sp_dbs[sp_id]
            gt_roi = get_base_start_stop_roi(SPDB_GT, DNM_GONI_THETA, mtr_gt.get_position(), mtr_gt.get_position(), 1, enable=True)
            gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, dct_get(sp_db, SPDB_XCENTER), dct_get(sp_db, SPDB_XRANGE), dct_get(sp_db, SPDB_XNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
            gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, dct_get(sp_db, SPDB_YCENTER), dct_get(sp_db, SPDB_YRANGE), dct_get(sp_db, SPDB_YNPOINTS), stepSize=None, max_scan_range=None, enable=True, is_point=False)
            gz_roi = get_base_roi(SPDB_GZ, DNM_GONI_Z, mtr_gz.get_position(), 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=True)
            
            self.apply_correction_model(gx_roi, gy_roi, gz_roi, gt_roi)
            
            #here use only a single OSA XY, when subdividing then this will need to be a set of setpoints = #subdivisions * # Y points
            osax_center = 0
            osay_center = 0
            ox_roi = get_base_roi(SPDB_GX, DNM_OSA_X, osax_center, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=False)
            oy_roi = get_base_roi(SPDB_GY, DNM_OSA_Y, osay_center, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=False)
            #Xdisabled for now
            oz_roi = get_base_roi(SPDB_GZ, DNM_OSA_Z, mtr_oz.get_position(), 0, 1, stepSize=None, max_scan_range=None, enable=False, is_point=False)
            
            #this needs to be handled properly for multi subspatial
            ox_roi[SETPOINTS] = [ox_roi[START]]
            oy_roi[SETPOINTS] = [oy_roi[START]]
            oz_roi[SETPOINTS] = [oz_roi[START]]
            
            goni_rois = {}
            osa_rois = {}
            goni_rois = {}
            
            # here we need to turn the absolute scan region (goni XY) that the user selected
            # into one that is centered around 0 as our ZP XY is
            rect  = sp_db[SPDB_RECT]
            scan_rect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[1]), QtCore.QPointF(rect[2], rect[3]))
            dx = scan_rect.center().x() - mtr_gx.get_position() 
            dy = scan_rect.center().y() - mtr_gy.get_position() 
                
            if((abs(dx) > 30.0) or (abs(dy) > 30.0)):
                scan_rect.moveCenter(QtCore.QPointF(0.0, 0.0))
            else:    
                scan_rect.moveCenter(QtCore.QPointF(dx, dy))
            
            #now set X and Y to new start/stop/ values, note using X and Y NPOINTS though
            zxnpts = dct_get(sp_db, SPDB_XNPOINTS)
            zx_roi = get_base_start_stop_roi(SPDB_X, DNM_ZONEPLATE_X, scan_rect.left(), scan_rect.right(), zxnpts, enable=True)
            
            zynpts = dct_get(sp_db, SPDB_YNPOINTS)
            zy_roi = get_base_start_stop_roi(SPDB_Y, DNM_ZONEPLATE_Y, scan_rect.bottom(), scan_rect.top(), zynpts, enable=True)
            
            dct_put(sp_db, SPDB_ZX, zx_roi)
            dct_put(sp_db, SPDB_ZY, zy_roi)
            
            #x_roi and y_roi have to be the absolute coordinates because they are used later on to setup the image plot boundaries
            dct_put(sp_db, SPDB_X, gx_roi)
            dct_put(sp_db, SPDB_Y, gy_roi)
            
            #it is fine the way it is
            dct_put(sp_db, SPDB_GX, gx_roi)
            dct_put(sp_db, SPDB_GY, gy_roi)
            dct_put(sp_db, SPDB_GZ, gz_roi)
            dct_put(sp_db, SPDB_GT, gt_roi)
                
            dct_put(sp_db, SPDB_OX, ox_roi)
            dct_put(sp_db, SPDB_OY, oy_roi)
            dct_put(sp_db, SPDB_OZ, oz_roi)
                
            return(None)
    
    def GONI_SCAN_update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        wdg_com = self.update_multi_spatial_wdg_com()
        sub_spatials = self.create_sub_spatial_dbs(wdg_com)
        if(sub_spatials):
            #for now only support single spatial with multi sub spatial
            sp_id = list(sub_spatials.keys())[0]
            sp_db = dct_get(wdg_com, SPDB_SPATIAL_ROIS)[sp_id]
            dct_put(sp_db, SPDB_SUB_SPATIAL_ROIS, sub_spatials[sp_id])
        self.roi_changed.emit(wdg_com)
        return(wdg_com)    

    def update_last_settings(self):
        '''
        these only update the spatial region values not the energy or EPU
        example:
            update the 'default' settings that will be reloaded when this scan pluggin is selected again
        :return:
        '''
        sp_db = get_first_sp_db_from_wdg_com(self.wdg_com)
        x_roi = sp_db[SPDB_X]
        y_roi = sp_db[SPDB_Y]

        DEFAULTS.set('SCAN.LINE.START', (x_roi[START], y_roi[START], 0, 0))
        DEFAULTS.set('SCAN.LINE.STOP', (x_roi[STOP], y_roi[STOP], 0, 0))
        DEFAULTS.set('SCAN.LINE.CENTER', (x_roi[CENTER], y_roi[CENTER], 0, 0))
        DEFAULTS.set('SCAN.LINE.RANGE', (x_roi[RANGE], y_roi[RANGE], 0, 0))
        DEFAULTS.set('SCAN.LINE.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], 0, 0))
        DEFAULTS.set('SCAN.LINE.STEP', (x_roi[STEP], y_roi[STEP], 0, 0))
        DEFAULTS.update()