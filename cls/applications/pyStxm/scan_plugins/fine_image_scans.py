'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import QtCore, QtGui
from PyQt5 import uic

import os
from cls.app_data.defaults import get_style

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.applications.pyStxm.scan_plugins import plugin_dir
# from cls.applications.pyStxm.scan_plugins.SampleImageWithEnergySSCAN import SampleImageWithEnergySSCAN
# from cls.applications.pyStxm.scan_plugins.SampleImageWithE712Wavegen import SampleImageWithE712Wavegen
from cls.applications.pyStxm.scan_plugins.SampleFineImageWithE712WavegenScan import SampleFineImageWithE712WavegenScanClass
from cls.applications.pyStxm.widgets.scan_table_view.multiRegionWidget import MultiRegionWidget
from bcm.devices.device_names import *

from cls.data_io.stxm_data_io import STXMDataIo

from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types, get_unique_roi_id, \
                    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
                    on_center_changed, recalc_setpoints, get_base_start_stop_roi, get_base_roi, get_first_sp_db_from_wdg_com
from cls.types.stxmTypes import scan_types, scan_sub_types, scan_panel_order, image_scan_secids, spatial_type_prefix, sample_positioning_modes, sample_fine_positioning_modes, scan_image_types

from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.time_utils import secondsToStr
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
MAX_SCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_X')
MAX_SCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_Y')
USE_E712_HDW_ACCEL = MAIN_OBJ.get_preset_as_int('USE_E712_HDW_ACCEL')

class FineImageScansParam(ScanParamWidget):

    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi( os.path.join(plugin_dir, 'fine_image_scans.ui'), self)

        self.epu_supported = False
        self.goni_supported = False

        if(self.main_obj.is_device_supported(DNM_GONI_X)):
            self.goni_supported = True

        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            x_cntr = self.main_obj.device(DNM_GONI_X).get_position()
            y_cntr = self.main_obj.device(DNM_GONI_Y).get_position()
        else:
            x_cntr = self.main_obj.device(DNM_SAMPLE_X).get_position()
            y_cntr = self.main_obj.device(DNM_SAMPLE_Y).get_position()

        self.multi_region_widget = MultiRegionWidget(enable_multi_spatial=self.enable_multi_region,
                                                      single_ev_model=True, max_range=MAX_SCAN_RANGE_FINEX, min_sp_rois=1,
                                                     x_cntr=x_cntr, y_cntr=y_cntr, main_obj=self.main_obj)

        if (not self.main_obj.is_device_supported(DNM_EPU_POLARIZATION)):
            self.multi_region_widget.deslect_all_polarizations()
            self.multi_region_widget.disable_polarization_table(True)
            self.multi_region_widget.set_polarization_table_visible(False)
        else:
            # more
            self.epu_supported = True
            self.multi_region_widget.deslect_all_polarizations()
            self.multi_region_widget.disable_polarization_table(False)
            self.multi_region_widget.set_polarization_table_visible(True)

        #self.multi_region_widget = MultiRegionWidget(enable_multi_spatial=self.enable_multi_region, max_range=MAX_SCAN_RANGE_FINEX)
        self.multi_region_widget.spatial_row_selected.connect(self.on_spatial_row_selected)
        self.multi_region_widget.spatial_row_changed.connect(self.on_spatial_row_changed)
        self.multi_region_widget.spatial_row_deleted.connect(self.on_spatial_row_deleted)
        self.multi_region_widget.spatial_row_added.connect(self.on_spatial_row_changed)

        self.center_plot_on_focus = True

        self.evGrpBox.layout().addWidget(self.multi_region_widget)
        self.scanTypeSelComboBox.currentIndexChanged.connect(self.scan_type_changed)

        self.loadScanBtn.clicked.connect(self.load_scan)
        self.hdwAccelDetailsBtn.setToolTip('E712 Wavgen details')
        #self.scan_class = SampleImageWithEnergySSCAN()
        #self.scan_class = SampleFineImageWithE712WavegenScanClass()
        if(USE_E712_HDW_ACCEL):
            self.scan_class = SampleFineImageWithE712WavegenScanClass(main_obj=self.main_obj)
        else:
            self.scan_class = SampleFineImageWithE712WavegenScanClass(main_obj=self.main_obj)

        #self.singleEVChkBx.clicked.connect(self.on_single_energy)
        self.hdwAccelDetailsBtn.clicked.connect(self.show_hdw_accel_details)
        self.wdg_com = None
        self.load_from_defaults()
        self.on_plugin_focus()
        self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Fine Image Scan"
        self.idx = scan_panel_order.IMAGE_SCAN  # by default
        self.type = scan_types.SAMPLE_IMAGE
        self.sub_type = scan_sub_types.LINE_UNIDIR
        self.data = {}
        self.section_id = image_scan_secids[image_scan_secids.SAMPLE_LXL]  # by default
        self.axis_strings = ['Sample Y microns', 'Sample X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        # data_file_pfx = 'i'
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.ROI
        self.enable_multi_region = self.main_obj.get_is_multi_region_enabled()
        self.multi_ev = True
        self._help_ttip = 'Sample Fine scan documentation and instructions'

    def on_plugin_focus(self):
        '''
        this is called when this scan param receives focus on the GUI
        - basically get the current EPU values and assign them to the multiregion widget
        :return:
        '''
        if(self.isEnabled()):
            #call the standard init_base_values function for scan param widgets that contain a multiRegionWidget
            self.on_multiregion_widget_focus_init_base_values()

    def show_hdw_accel_details(self):
        dark = get_style('dark')
        self.scan_class.e712_wg.setStyleSheet(dark)
        self.scan_class.e712_wg.show()

    def calc_new_scan_time_estemate(self, is_pxp, x_roi, y_roi, dwell_in_sec):
        '''
        changes id using hdw acceleration or not
        when done it must emit the signal:
            new_est_scan_time

        :return: tuple(seconds, time_string)
        '''

        dwell = dwell_in_sec * 0.001
        mode = self.scanTypeSelComboBox.currentIndex()
        if(mode is 0):
            pxp = True
        else:
            pxp = False


        self.scan_class.e712_wg.set_mode(mode)
        hline_time = self.scan_class.e712_wg.calc_hline_time( dwell_in_sec, x_roi[NPOINTS], pxp=pxp)
        total_time_sec = float(y_roi[NPOINTS]) * (float(hline_time))
        s = 'Estimated time: %s' % secondsToStr(total_time_sec)

        self.new_est_scan_time.emit((total_time_sec, s))
        return((total_time_sec, s))


    def on_E712WavegenBtn(self, chkd):
        if(chkd):
            #set the wave generator radio box's to enabled
            self.autoDDLRadBtn.setEnabled(True)
            self.reinitDDLRadBtn.setEnabled(True)
        else:
            # set the wave generator radio box's to disabled
            self.autoDDLRadBtn.setEnabled(False)
            self.reinitDDLRadBtn.setEnabled(False)


    def clear_params(self):
        """ meant to clear all params from table """
        self.multi_region_widget.clear_spatial_table()
                            
    def gen_max_scan_range_limit_def(self):
        """ this function only currently centers around 0,0, this is a problem because in order
        to indicate when the range of the scan is larger than the fine ranges it must be valid around 
        whereever o,o is on the fine physical stage is, as this is nly generated and sent to teh plot 
        widget at startup it doesnt work properly when the scan is not around 0,0. 
        leaving this for future
        """

        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.gen_GONI_SCAN_max_scan_range_limit_def()
        else:
            mtr_sx = self.main_obj.device(DNM_SAMPLE_X)
            mtr_sy = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_sfx = self.main_obj.device(DNM_SAMPLE_FINE_X)
            mtr_sfy = self.main_obj.device(DNM_SAMPLE_FINE_Y)
            center_x = mtr_sx.get_position()
            center_y = mtr_sy.get_position()

            xllm = mtr_sx.get_low_limit()
            xhlm = mtr_sx.get_high_limit()
            yllm = mtr_sy.get_low_limit()
            yhlm = mtr_sy.get_high_limit()
            
            fxllm = center_x - (MAX_SCAN_RANGE_FINEX * 0.5)
            fxhlm = center_x + (MAX_SCAN_RANGE_FINEX * 0.5)
            fyllm = center_y - (MAX_SCAN_RANGE_FINEY * 0.5)
            fyhlm = center_y + (MAX_SCAN_RANGE_FINEY * 0.5)
            
            bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))

            #adjust the warn qrect by 0.1 in all directions so that a scan range of the exact size of the limit is still allowed
            warn_qrect = QtCore.QRectF(QtCore.QPointF(fxllm - 0.1, fyhlm + 0.1), QtCore.QPointF(fxhlm + 0.1, fyllm - 0.1))
            alarm_qrect = self.get_percentage_of_qrect(warn_qrect, 0.99999)  # %99 of max
                    
            bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond SampleXY Capabilities', get_warn_fill_pattern())        
            normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Sample Image Fine Scan', get_normal_fill_pattern())
            #warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Sample Image Coarse Scan', get_warn_fill_pattern())
            #warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Nearing Range Limit for Sample Image Scan', get_warn_fill_pattern())
            warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Coarse X/Y will have to be moved in order to perform scan',
                               get_warn_fill_pattern())
            alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample Fine X/Y', get_alarm_fill_pattern())
            
            self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
    

    def update_sub_type(self):
        idx = self.scanTypeSelComboBox.currentIndex()
        if (idx == scan_sub_types.POINT_BY_POINT):
            # point by point
            self.sub_type = scan_sub_types.POINT_BY_POINT
        else:
            # line by line
            self.sub_type = scan_sub_types.LINE_UNIDIR

        
    def scan_type_changed(self, idx):
        if(idx == 0):
            #line by line
            self.sub_type = scan_sub_types.LINE_UNIDIR
        else:
            #point by point
            self.sub_type = scan_sub_types.POINT_BY_POINT

        sp_db = get_first_sp_db_from_wdg_com(self.wdg_com)
        x_roi = sp_db[SPDB_X]
        y_roi = sp_db[SPDB_Y]
        dwell = sp_db[SPDB_EV_ROIS][0][DWELL]
        if (self.sub_type == scan_sub_types.POINT_BY_POINT):
            self.calc_new_scan_time_estemate(True, x_roi, y_roi, dwell)
        else:
            self.calc_new_scan_time_estemate(False, x_roi, y_roi, dwell)


    
    def set_roi(self, roi):
        '''
        This standard function is typically used to set QtLineEdit fields but because this plugin uses the multispatialwidget
        there are no fields so it is basically unused
        :param roi:
        :return:
        '''
        # (cx, cy, cz, c0) = roi[CENTER]
        # (rx, ry, rz, s0) = roi[RANGE]
        # (nx, ny, nz, n0) = roi[NPOINTS]
        # (sx, sy, sz, s0) = roi[STEP]
        #
        # dwell = roi[DWELL]
        pass
        


    def mod_roi(self, wdg_com, do_recalc=True, ev_only=False, sp_only=False):
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
        item_id = dct_get(wdg_com, SPDB_ID_VAL)
        dct_put(wdg_com, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
        
        
        if(wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            self.load_roi(wdg_com)
            return
        
        #if((wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI) or (wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN)):
        if(wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI):
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)
            if(cur_scan != None):
                #change the command to add this ROI
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                return
                #wdg_com[CMND] = widget_com_cmnd_types.ROI_CHANGED
            else:
                x_roi = wdg_com[SPDB_X]
                y_roi = wdg_com[SPDB_Y]
                #x_roi[NPOINTS] = 20
                #y_roi[NPOINTS] = 20
                scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
                on_npoints_changed(scan[SPDB_X])
                on_npoints_changed(scan[SPDB_Y])
                scan[SPDB_ID_VAL] = item_id
                self.multi_region_widget.sp_widg.on_new_region(scan)
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)    
                return
        
        if(wdg_com[CMND] == widget_com_cmnd_types.ROI_CHANGED):
            #print 'image_scans.mod_roi: item_id = %d' % item_id
            #we are being modified by the plotter
            x_roi = wdg_com[SPDB_X]
            y_roi = wdg_com[SPDB_Y]
            scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)

            if(cur_scan is None):
                scan[SPDB_ID_VAL] = item_id
                on_npoints_changed(scan[SPDB_X])
                on_npoints_changed(scan[SPDB_Y])

                _dwell = scan[SPDB_EV_ROIS][0][DWELL]
                _x = scan[SPDB_X]
                _y = scan[SPDB_Y]


                #self.multi_region_widget.sp_widg.table_view.add_scan(scan, wdg_com['CURRENT']['PLOT']['ITEM']['ID'])
                self.multi_region_widget.sp_widg.on_new_region(scan, ev_only=ev_only)
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                #return
            else:
                #cur_scan = self.multi_region_widget.sp_widg.table_view.get_scan(item_id)
                #update the center and range fields that have come from the plotter
                #first call center recalc, then range
                cur_scan[SPDB_X][CENTER] = scan[SPDB_X][CENTER]
                on_center_changed(cur_scan[SPDB_X])
                
                cur_scan[SPDB_X][RANGE] = scan[SPDB_X][RANGE]
                on_range_changed(cur_scan[SPDB_X])
                
                cur_scan[SPDB_Y][CENTER] = scan[SPDB_Y][CENTER]
                on_center_changed(cur_scan[SPDB_Y])
                
                cur_scan[SPDB_Y][RANGE] = scan[SPDB_Y][RANGE]
                on_range_changed(cur_scan[SPDB_Y])

                _dwell = cur_scan[SPDB_EV_ROIS][0][DWELL]
                _x = cur_scan[SPDB_X]
                _y = cur_scan[SPDB_Y]
                
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                self.multi_region_widget.sp_widg.modify_row_data(item_id, cur_scan)

                #return

            if (self.sub_type == scan_sub_types.POINT_BY_POINT):
                self.calc_new_scan_time_estemate(True, _x, _y, _dwell)
            else:
                self.calc_new_scan_time_estemate(False, _x, _y, _dwell)
            return


        elif(wdg_com[CMND] == widget_com_cmnd_types.DEL_ROI):
            #remove this roi from the multi region spatial table
            self.multi_region_widget.sp_widg.delete_row(item_id)

            return
        
        #elif(wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI):
        #    self.multi_region_widget.select_spatial_row(item_id)
        #    return
        elif(wdg_com[CMND] == widget_com_cmnd_types.DESELECT_ROI):
            #_logger.debug('mod_roi: calling deselect_all() ')
            self.multi_region_widget.sp_widg.deselect_all()
                
        else:
            #we are 
            print('image_scan: mod_roi: unsupported widget_com CMND [%d]' % wdg_com[CMND])
            return    

    def clear_params(self):
        #this should cascade through and delete all tables
        self.multi_region_widget.clear_spatial_table()


    def load_roi(self, wdg_com, append=False, ev_only=False, sp_only=False):
        """
        take a widget communications dict and load the plugin GUI with the spatial region, also
        set the scan subtype selection pulldown for point by point or line
        """
        #self.wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        self.wdg_com = wdg_com
        if(self.wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            sp_db_dct = dct_get(self.wdg_com, WDGCOM_SPATIAL_ROIS)
            sp_ids = list(sp_db_dct.keys())
            sp_id = sp_ids[0]
            sp_db = sp_db_dct[sp_id]

            image_scans = [scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK ]
            if((not ev_only) and (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in image_scans)):
                return

            if(not ev_only):
                if(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE) == scan_sub_types.LINE_UNIDIR):
                    #image Line by Line
                    self.scanTypeSelComboBox.setCurrentIndex(1)
                else:
                    #image Point by Point
                    self.scanTypeSelComboBox.setCurrentIndex(0)

                if (dct_get(sp_db, SPDB_HDW_ACCEL_AUTO_DDL)):
                    self.autoDDLRadBtn.setChecked(True)
                else:
                    self.autoDDLRadBtn.setChecked(False)

                if (dct_get(sp_db, SPDB_HDW_ACCEL_REINIT_DDL)):
                    self.reinitDDLRadBtn.setChecked(True)
                else:
                    self.reinitDDLRadBtn.setChecked(False)

            self.multi_region_widget.load_scan(self.wdg_com, ev_only=ev_only, sp_only=sp_only)
            self.enable_multi_region = self.multi_region_widget.is_multi_region_enabled()
            #emit roi_changed so that the plotter can be signalled to create the ROI shap items
            if(not self.multi_region_widget.is_spatial_list_empty()):
                self.roi_changed.emit(self.wdg_com)
    
    def on_single_energy(self, val):
        self.single_energy = val
#         if(not val):
#             pass
#         else:
#             self.ev_select_widget.on_single_ev()
#        self.update_data()
    
    def update_type(self):

        self.update_sub_type()
        if(self.wdg_com is not None):
            sp_rois = dct_get(self.wdg_com, WDGCOM_SPATIAL_ROIS)
            sp_ids = list(sp_rois.keys())
            for sp_id in sp_ids:
                sp_db = sp_rois[sp_id]

                if(USE_E712_HDW_ACCEL):
                    #added E712 waveform generator support
                    dct_put(sp_db, SPDB_HDW_ACCEL_USE, True)
                    dct_put(sp_db, SPDB_HDW_ACCEL_AUTO_DDL, self.autoDDLRadBtn.isChecked())
                    dct_put(sp_db, SPDB_HDW_ACCEL_REINIT_DDL, self.reinitDDLRadBtn.isChecked())

                dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)
                x_roi = dct_get(sp_db, SPDB_X)
                if(dct_get(sp_db, SPDB_XRANGE) > MAX_SCAN_RANGE_FINEX):
                    x_roi[SCAN_RES] = COARSE
                else:
                    x_roi[SCAN_RES] = FINE

                #if(dct_get(sp_db, SPDB_EV_NPOINTS) > 1):
                if ((len(sp_ids) > 1) or (dct_get(sp_db, SPDB_EV_NPOINTS) > 1)):
                    self.type = scan_types.SAMPLE_IMAGE_STACK
                    dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, scan_types.SAMPLE_IMAGE_STACK)     #the scan type: scan_types-> Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')    
                    #dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, None)
                else:
                    self.type = scan_types.SAMPLE_IMAGE
                    dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, scan_types.SAMPLE_IMAGE)
    
    
    
    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        
        self.update_type()
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            #goniometer_zoneplate mode
            self.wdg_com = self.GONI_SCAN_update_data()
        # elif(self.sample_positioning_mode == sample_positioning_modes.COARSE):
        #     if (self.main_obj.get_fine_sample_positioning_mode() == sample_fine_positioning_modes.ZONEPLATE):
        #         #coarse_zoneplate mode
        #         self.wdg_com = self.ZONEPLATE_SCAN_update_data()
        #     else:
        #         #coarse_samplefine mode
        #         self.wdg_com = self.update_multi_spatial_wdg_com()
        else:
           self.wdg_com = self.update_multi_spatial_wdg_com()

        self.roi_changed.emit(self.wdg_com)    
        return(self.wdg_com)
    
    
    #########################################################################
    #  Goniometer specific routines
    #########################################################################
    
    def gen_GONI_SCAN_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """    
        mtr_zpx = self.main_obj.device(DNM_ZONEPLATE_X)
        mtr_zpy = self.main_obj.device(DNM_ZONEPLATE_Y)
        #mtr_osax = self.main_obj.device('OSAX.X')
        #mtr_osay = self.main_obj.device('OSAY.Y')
        mtr_gx = self.main_obj.device(DNM_GONI_X)
        mtr_gy = self.main_obj.device(DNM_GONI_Y)
        
        gx_pos = mtr_gx.get_position()
        gy_pos = mtr_gy.get_position()
        
        #these are all added because the sign is in the LLIM
        xllm = gx_pos - (MAX_SCAN_RANGE_FINEX * 0.5)
        xhlm = gx_pos + (MAX_SCAN_RANGE_FINEX * 0.5)
        yllm = gy_pos - (MAX_SCAN_RANGE_FINEY * 0.5)
        yhlm = gy_pos + (MAX_SCAN_RANGE_FINEY * 0.5)
        
        gxllm = mtr_gx.get_low_limit()
        gxhlm = mtr_gx.get_high_limit()
        gyllm = mtr_gy.get_low_limit()
        gyhlm = mtr_gy.get_high_limit()
        
        bounding_qrect = QtCore.QRectF(QtCore.QPointF(gxllm, gyhlm), QtCore.QPointF(gxhlm, gyllm))
        #warn_qrect = self.get_percentage_of_qrect(bounding, 0.90) #%80 of max
        #alarm_qrect = self.get_percentage_of_qrect(bounding, 0.95) #%95 of max
        normal_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(normal_qrect, 1.01) #%95 of max
        alarm_qrect = self.get_percentage_of_qrect(normal_qrect, 1.0) #%95 of max
        
        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Goniometer Capabilities', get_alarm_fill_pattern())
        normal = ROILimitObj(normal_qrect, get_normal_clr(45), 'Fine ZP Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Goniometer will be required to move', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Range is beyond ZP Capabilities', get_alarm_fill_pattern())
        
        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)    
        
        self.multi_region_widget.set_roi_limits(self.roi_limit_def)
        
    def get_saved_center(self):
        '''
        override the get_saved_center() in base and return the current Gx Gy values as "THE CENTER"
        this call is typical used by the main gui when the user selects the zp image scan so that the plot can
        display coordinates around the current goni center
        '''
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            mtr_x = self.main_obj.device(DNM_GONI_X)
            mtr_y = self.main_obj.device(DNM_GONI_Y)
        else:
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)

        return((mtr_x.get_position(), mtr_y.get_position()))
    
    def get_theta_fld_vals(self):
        roi = {}
        self.assign_flds(roi, 'Theta')
        return(roi)
    
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
        
        for sp_id in sp_dbs:
            sp_db = sp_dbs[sp_id]
            sp_db = self.modify_sp_db_for_goni(sp_db)

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
        
        return(wdg_com)

