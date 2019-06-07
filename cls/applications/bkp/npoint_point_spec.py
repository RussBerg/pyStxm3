
'''
Created on Nov 16, 2016

@author: bergr
'''

from PyQt5 import QtCore
from PyQt5 import uic
from cls.scanning.ScanTableView import MultiRegionWidget
from cls.scanning.plugins import plugin_dir
from cls.scanning.plugins.SampleImageWithEnergySSCAN import SampleImageWithEnergySSCAN
from cls.scanning.plugins.base import ScanParamWidget, zp_focus_modes
from sm.stxm_control.plotters.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, \
    get_warn_fill_pattern, get_alarm_fill_pattern
from sm.stxm_control.plotters.shape_restrictions import ROILimitObj, ROILimitDef

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.types.stxmTypes import scan_types, scan_panel_order, spatial_type_prefix
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *
from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types, \
    on_start_changed, on_stop_changed, \
    get_base_start_stop_roi, get_first_sp_db_from_wdg_com

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset('MAX_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset('MAX_SCAN_RANGE_Y')

_logger = get_module_logger(__name__)

class PointScanParam(ScanParamWidget):
    name = "Point Scan"
    idx = scan_panel_order.POINT_SCAN
    type = scan_types.SAMPLE_POINT_SPECTRUM
    data = {}
    section_id = 'POINT'
    axis_strings = ['counts', 'eV', '', '']
    zp_focus_mode = zp_focus_modes.A0MOD
    #data_file_pfx = 'p'
    data_file_pfx = MAIN_OBJ.get_datafile_prefix()
    plot_item_type = spatial_type_prefix.PNT
    enable_multi_region = MAIN_OBJ.get_is_multi_region_enabled()
    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self)
        self._parent = parent
        uic.loadUi(    plugin_dir + '\\point_scan.ui', self) 
        
        #self.multi_region_widget = MultiRegionWidget()
        self.multi_region_widget = MultiRegionWidget(use_center=False, is_point=True, enable_multi_spatial=self.enable_multi_region) #instead of using centerx etc use startX
        self.multi_region_widget.spatial_row_selected.connect(self.on_spatial_row_selected)
        self.multi_region_widget.spatial_row_changed.connect(self.on_spatial_row_changed)
        self.multi_region_widget.spatial_row_deleted.connect(self.on_spatial_row_deleted)
        
        self.evGrpBox.layout().addWidget(self.multi_region_widget)
        
        self.loadScanBtn.clicked.connect(self.load_scan)
        #self.singleEVChkBx.clicked.connect(self.on_single_energy)
        self.sscan_class = SampleImageWithEnergySSCAN()
        
        self.wdg_com = None
        self.load_from_defaults()
    
    def gen_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """    
        mtr_sx = MAIN_OBJ.device('SampleX')
        mtr_sy = MAIN_OBJ.device('SampleY')
        
        xllm = mtr_sx.get_low_limit()
        xhlm = mtr_sx.get_high_limit()
        yllm = mtr_sy.get_low_limit()
        yhlm = mtr_sy.get_high_limit()
        
        fxllm = 0.0 - (MAX_SCAN_RANGE_FINEX * 0.5)
        fxhlm = 0.0 + (MAX_SCAN_RANGE_FINEX * 0.5)
        fyllm = 0.0 - (MAX_SCAN_RANGE_FINEY * 0.5)
        fyhlm = 0.0 + (MAX_SCAN_RANGE_FINEY * 0.5)
        
        bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95) #%95 of max
        alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 1.0) #%100 of max
                
        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Point is beyond SampleXY Range', get_alarm_fill_pattern())        
        normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Point Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Point Scan, Nearing Limit of Sample X/Y Range', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond Range of Sample X/Y', get_alarm_fill_pattern())
        
        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
        
    def set_roi(self, roi):
        """
        set_roi standard function supported by all scan pluggins to initialize the GUI for this scan with values
        stored in the defaults library
        
        :param roi: is a standard dict returned from the call to DEFAULTS.get_defaults()
        :type roi: dict.
    
        :returns: None
      
        """
        (cx, cy, cz, c0) = roi[CENTER]
        (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (sx, sy, sz, s0) = roi[STEP]
        #dwell = roi[DWELL]
        
        #self.centerXFld.setText(str('%.2f' % cx))
        #self.centerYFld.setText(str('%.2f' % cy))
        
    
    def mod_roi(self, wdg_com, do_recalc=True, sp_only=False):
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
        #if(self.wdg_com is None):
        #    import copy
        #    self.wdg_com = copy(wdg_com)
        
        if(wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            self.load_roi(wdg_com)
            return
        
        if(wdg_com[CMND] == widget_com_cmnd_types.ROI_CHANGED):
            #we are being modified by the plotter
            item_id = dct_get(wdg_com,SPDB_PLOT_ITEM_ID)
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)
            sx = wdg_com[SPDB_X][START]
            sy = wdg_com[SPDB_Y][START]
            ex = wdg_com[SPDB_X][STOP]
            ey = wdg_com[SPDB_Y][STOP]
            nx = wdg_com[SPDB_X][NPOINTS]
            ny = wdg_com[SPDB_Y][NPOINTS]
            if(cur_scan is None):
                #ADD_ROI
                #x_roi = get_base_roi(SPDB_X, 'SampleX', cx, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=True)
                #y_roi = get_base_roi(SPDB_Y, 'SampleY', cy, 0, 1, stepSize=None, max_scan_range=None, enable=True, is_point=True)
                
                x_roi = get_base_start_stop_roi(SPDB_X, DNM_SAMPLE_X, sx, ex, 1, is_point=True)
                y_roi = get_base_start_stop_roi(SPDB_Y, DNM_SAMPLE_Y, sy, ey, 1, is_point=True)
                
                scan = make_spatial_db_dict(sp_id=item_id, x_roi=x_roi, y_roi=y_roi)
                scan[SPDB_ID_VAL] = item_id
                self.multi_region_widget.sp_widg.on_new_region(scan)
                #self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                
            else:
                #update the center and range fields that have come from the plotter
                cur_scan[SPDB_X][START] = sx
                on_start_changed(cur_scan[SPDB_X])
                cur_scan[SPDB_X][STOP] = ex
                on_stop_changed(cur_scan[SPDB_X])
                
                
                cur_scan[SPDB_Y][START] = sy
                on_start_changed(cur_scan[SPDB_Y])
                cur_scan[SPDB_Y][STOP] = ey
                on_stop_changed(cur_scan[SPDB_Y])
                
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                self.multi_region_widget.sp_widg.modify_row_data(item_id, cur_scan)
                

        elif(wdg_com[CMND] == widget_com_cmnd_types.DEL_ROI):
            #remove this roi from the multi region spatial table
            item_id = dct_get(wdg_com,SPDB_PLOT_ITEM_ID)
            self.multi_region_widget.sp_widg.delete_row(item_id)            
        
        elif(wdg_com[CMND] == widget_com_cmnd_types.ADD_ROI):
            pass    
        elif(wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI):
            item_id = dct_get(wdg_com, SPDB_PLOT_ITEM_ID)
            self.multi_region_widget.select_spatial_row(item_id)
            
        elif(wdg_com[CMND] == widget_com_cmnd_types.DESELECT_ROI):
            self.multi_region_widget.sp_widg.deselect_all()
            
        else:
            #we are 
            print('point_scan: mod_roi: unsupported widget_com CMND [%d]' % wdg_com[CMND])
            return
        
    def load_roi(self, ado_obj):
        """
        take a widget communications dict and load the plugin GUI with the spatial region, also
        set the scan subtype selection pulldown for point by point or line
        """
        wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        if(wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            sp_db = sp_db = get_first_sp_db_from_wdg_com(wdg_com)

            if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != scan_types.SAMPLE_POINT_SPECTRUM):
                return
                
            self.multi_region_widget.load_scan(wdg_com)
            #emit roi_changed so that the plotter can be signalled to create the ROI shape items
            self.roi_changed.emit(wdg_com)        
            
    def on_spatial_row_selected(self, wdg_com):
        """
        :param wdg_com: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type wdg_com: dict.
    
        :returns: None
      
        """
        wdg_com[CMND] = widget_com_cmnd_types.SELECT_ROI
        dct_put(wdg_com,SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
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
        wdg_com = self.update_multi_spatial_wdg_com()
        self.roi_changed.emit(wdg_com)
        return(wdg_com)
    
    
    
