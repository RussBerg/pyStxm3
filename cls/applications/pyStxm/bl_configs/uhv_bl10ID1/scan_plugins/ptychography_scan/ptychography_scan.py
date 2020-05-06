"""
Created on Aug 25, 2014

@author: bergr
"""
'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import QtCore, QtGui
from PyQt5 import uic

import copy
import os
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, DEFAULTS
from cls.scanning.base import ScanParamWidget, zp_focus_modes

from bcm.devices.device_names import *
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from cls.data_io.stxm_data_io import STXMDataIo
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, get_axis_setpoints_from_sp_db
from cls.applications.pyStxm.widgets.scan_table_view.multiRegionWidget import MultiRegionWidget
from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, widget_com_cmnd_types, on_range_changed, on_center_changed
from cls.types.stxmTypes import scan_types, scan_sub_types, spatial_type_prefix, image_types, sample_positioning_modes, sample_fine_positioning_modes
from cls.utils.roi_utils import make_spatial_db_dict, widget_com_cmnd_types, get_unique_roi_id, \
                    on_range_changed, on_npoints_changed, on_step_size_changed, on_start_changed, on_stop_changed, \
                    on_center_changed, recalc_setpoints, get_base_start_stop_roi, get_base_roi, get_first_sp_db_from_wdg_com
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

from cls.applications.pyStxm.bl_configs.basic.scan_plugins.ptychography_scan.PtychographyScan import PtychographyScanClass

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('max_fine_x')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('max_fine_y')
MAX_SCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('max_coarse_x')
MAX_SCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('max_coarse_y')
USE_E712_HDW_ACCEL = MAIN_OBJ.get_preset_as_bool('USE_E712_HDW_ACCEL', 'BL_CFG_MAIN')
PTYCHOGRAPHY_ENABLED = MAIN_OBJ.get_preset_as_bool('PTYCHOGRAPHY_ENABLED')

_logger = get_module_logger(__name__)
    
class PtychographyScanParam(ScanParamWidget):

    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent

        if ((self.sample_fine_positioning_mode != sample_fine_positioning_modes.ZONEPLATE) or (
                PTYCHOGRAPHY_ENABLED == False)):
            if (not PTYCHOGRAPHY_ENABLED):
                self.name = "Ptychography Scan ---- [DISABLED in app.ini] "
            else:
                self.name = "Ptychography Scan ---- [DISABLED by scanning mode] "
            self.setEnabled(False)
            self.setToolTip(
                'PtychographyScanParam: Scan plugin is disabled while in none Zoneplate sample fine positioning mode')
        else:

            uic.loadUi( os.path.join(os.path.dirname(__file__), 'ptychography_scan.ui'), self)

            x_cntr = self.main_obj.device(DNM_SAMPLE_FINE_X).get_position()
            y_cntr = self.main_obj.device(DNM_SAMPLE_FINE_Y).get_position()

            self.multi_region_widget = MultiRegionWidget(enable_multi_spatial=False, max_range=MAX_SCAN_RANGE_FINEX,
                                                         min_sp_rois=1, x_cntr=x_cntr, y_cntr=y_cntr, main_obj=self.main_obj)

            if (not self.main_obj.is_device_supported(DNM_EPU_POLARIZATION)):

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
            self.loadScanBtn.clicked.connect(self.load_scan)

            self.scan_class = PtychographyScanClass(main_obj=self.main_obj)
            self.on_ev_pol_sel(0)
            self.evpol_flg_comboBox.currentIndexChanged.connect(self.on_ev_pol_sel)
            self.wdg_com = None
            self.sp_db = None
            self.osay_trcking_was = self.main_obj.device(DNM_OSAY_TRACKING).get_position()
            self.load_from_defaults()
            self.init_sp_db()
            #self.connect_paramfield_signals()
            self.on_plugin_focus()
            self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Ptychography Scan"
        self.idx = self.main_obj.get_scan_panel_order(__file__)
        self.type = scan_types.PTYCHOGRAPHY
        self.data = {}
        self.section_id = 'PTYCHOGRAPHY'
        self.axis_strings = ['Sample Y microns', 'Sample X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.DO_NOTHING
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.ROI

        self._type_interactive_plot = True  # [scan_panel_order.POSITIONER_SCAN]
        self._type_skip_scan_q_table_plots = False  # [scan_panel_order.OSA_FOCUS_SCAN, scan_panel_order.FOCUS_SCAN]
        self._type_spectra_plot_type = False  # [scan_panel_order.POINT_SCAN, scan_panel_order.POSITIONER_SCAN]
        self._type_skip_centering_scans = False  # [scan_panel_order.FOCUS_SCAN, scan_panel_order.TOMOGRAPHY,
        # scan_panel_order.LINE_SCAN, scan_panel_order.POINT_SCAN, scan_panel_order.IMAGE_SCAN]
        self._type_do_recenter = False  # [scan_panel_order.IMAGE_SCAN, scan_panel_order.TOMOGRAPHY, scan_panel_order.LINE_SCAN]

        # self._help_html_fpath = os.path.join('interface', 'window_system', 'scan_plugins', 'detector.html')
        self._help_ttip = 'Ptychography documentation and instructions'

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            #make sure that the OSA vertical tracking is off if it is on
            self.osay_trcking_was = self.main_obj.device(DNM_OSAY_TRACKING).get_position()
            self.main_obj.device(DNM_OSAY_TRACKING).put(0) #off
            self.on_multiregion_widget_focus_init_base_values()

    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        :return:
        '''

        if (self.isEnabled()):
            # put the OSA vertical tracking back to its previous state
            self.main_obj.device(DNM_OSAY_TRACKING).put(self.osay_trcking_was)

        # call the base class defocus
        super(PtychographyScanParam, self).on_plugin_defocus()

    def on_ev_pol_sel(self, idx):
        '''
        set the flag, 0 == EV then Pol, 1 == Pol then EV
        :param idx: 
        :return: 
        '''
        self.scan_class.set_ev_first_flg(idx)
        
        
    def connect_paramfield_signals(self):

        mtr_x = self.main_obj.device(DNM_SAMPLE_FINE_X)
        mtr_y = self.main_obj.device(DNM_SAMPLE_FINE_Y)
        
        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()
        
        rx = xhlm - xllm
        ry = yhlm - yllm
        
        lim_dct = {}
        lim_dct['X'] = {'llm':xllm, 'hlm': xhlm, 'rng':rx}
        lim_dct['Y'] = {'llm':yllm, 'hlm': yhlm, 'rng':ry}
        
        self.connect_param_flds_to_validator(lim_dct)

    def update_min_max(self):

        mtr_x = self.main_obj.device(DNM_SAMPLE_FINE_X)
        mtr_y = self.main_obj.device(DNM_SAMPLE_FINE_Y)

        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()
        rx = xhlm - xllm
        ry = yhlm - yllm

        dpo = self.centerXFld.dpo
        self.update_dpo_min_max(dpo, xllm, xhlm)

        dpo = self.centerYFld.dpo
        self.update_dpo_min_max(dpo, yllm, yhlm)

        dpo = self.rangeXFld.dpo
        self.update_dpo_min_max(dpo, rx, rx)

        dpo = self.rangeYFld.dpo
        self.update_dpo_min_max(dpo, ry, ry)

    def gen_max_scan_range_limit_def(self):
        """ this function only currently centers around 0,0, this is a problem because in order
        to indicate when the range of the scan is larger than the fine ranges it must be valid around
        whereever o,o is on the fine physical stage is, as this is nly generated and sent to teh plot
        widget at startup it doesnt work properly when the scan is not around 0,0.
        leaving this for future
        """

        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
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

            # adjust the warn qrect by 0.1 in all directions so that a scan range of the exact size of the limit is still allowed
            warn_qrect = QtCore.QRectF(QtCore.QPointF(fxllm - 0.1, fyhlm + 0.1),
                                       QtCore.QPointF(fxhlm + 0.1, fyllm - 0.1))
            alarm_qrect = self.get_percentage_of_qrect(warn_qrect, 0.99999)  # %99 of max

            bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond SampleXY Capabilities',
                                   get_warn_fill_pattern())
            normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Sample Image Fine Scan',
                                 get_normal_fill_pattern())
            # warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Sample Image Coarse Scan', get_warn_fill_pattern())
            # warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Nearing Range Limit for Sample Image Scan', get_warn_fill_pattern())
            warn = ROILimitObj(warn_qrect, get_warn_clr(150),
                               'Coarse X/Y will have to be moved in order to perform scan',
                               get_warn_fill_pattern())
            alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample Fine X/Y',
                                get_alarm_fill_pattern())

            self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)

    def gen_GONI_SCAN_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """
        mtr_zpx = self.main_obj.device(DNM_SAMPLE_FINE_X)
        mtr_zpy = self.main_obj.device(DNM_SAMPLE_FINE_Y)

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

    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()

        :returns: None

        """
        self.sp_db = self.multi_region_widget.sp_widg.get_row_data_by_item_id(0)

        # sgt = float(str(self.startGTFld.text()))
        # egt = float(str(self.endGTFld.text()))
        #
        # cgt = float(sgt + egt) / 2.0
        # rgt = float(egt - sgt)
        # ngt = int(str(self.npointsGTFld.text()))
        # stgt = float(str(self.stepGTFld.text()))
        #
        # # now create the model that this pluggin will use to record its params
        # gt_roi = get_base_roi(SPDB_GT, DNM_GONI_THETA, cgt, rgt, ngt, stgt)
        # goni_rois = {SPDB_GT: gt_roi}
        # self.sp_db = make_spatial_db_dict(goni_rois=goni_rois)
    
    # def check_scan_limits(self):
    #     ''' a function to be implemented by the scan pluggin that
    #     checks the scan parameters against the soft limits of the
    #     positioners, if all is well return true else false
    #
    #     This function should provide an explicit error log msg to aide the user
    #     '''
    #     ret = self.check_center_range_xy_scan_limits(DNM_SAMPLE_X, DNM_SAMPLE_Y)
    #     return(ret)
    

    def set_roi(self, roi):
        """
        set_roi standard function supported by all scan pluggins to initialize the GUI for this scan with values
        stored in the defaults library
        
        :param roi: is a standard dict returned from the call to DEFAULTS.get_defaults()
        :type roi: dict.
    
        :returns: None
      
        """
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

        if (wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            self.load_roi(wdg_com)
            return

        # if((wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI) or (wdg_com[CMND] == widget_com_cmnd_types.LOAD_SCAN)):
        if (wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI):
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)
            if (cur_scan != None):
                # change the command to add this ROI
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                return
                # wdg_com[CMND] = widget_com_cmnd_types.ROI_CHANGED
            else:
                x_roi = wdg_com[SPDB_X]
                y_roi = wdg_com[SPDB_Y]
                # x_roi[NPOINTS] = 20
                # y_roi[NPOINTS] = 20
                scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
                on_npoints_changed(scan[SPDB_X])
                on_npoints_changed(scan[SPDB_Y])
                scan[SPDB_ID_VAL] = item_id
                self.multi_region_widget.sp_widg.on_new_region(scan)
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                return

        if (wdg_com[CMND] == widget_com_cmnd_types.ROI_CHANGED):
            # print 'image_scans.mod_roi: item_id = %d' % item_id
            # we are being modified by the plotter
            x_roi = wdg_com[SPDB_X]
            y_roi = wdg_com[SPDB_Y]
            scan = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi)
            cur_scan = self.multi_region_widget.sp_widg.get_row_data_by_item_id(item_id)

            if (cur_scan is None):
                scan[SPDB_ID_VAL] = item_id
                on_npoints_changed(scan[SPDB_X])
                on_npoints_changed(scan[SPDB_Y])

                _dwell = scan[SPDB_EV_ROIS][0][DWELL]
                _x = scan[SPDB_X]
                _y = scan[SPDB_Y]

                # self.multi_region_widget.sp_widg.table_view.add_scan(scan, wdg_com['CURRENT']['PLOT']['ITEM']['ID'])
                self.multi_region_widget.sp_widg.on_new_region(scan, ev_only=ev_only)
                self.multi_region_widget.sp_widg.select_row(item_id=item_id)
                # return
            else:
                # cur_scan = self.multi_region_widget.sp_widg.table_view.get_scan(item_id)
                # update the center and range fields that have come from the plotter
                # first call center recalc, then range
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

                # return

            if (self.sub_type == scan_sub_types.POINT_BY_POINT):
                self.calc_new_scan_time_estemate(True, _x, _y, _dwell)
            else:
                self.calc_new_scan_time_estemate(False, _x, _y, _dwell)
            return


    def update_last_settings(self):
        """ update the 'default' settings that will be reloaded when this scan pluggin is selected again
        """
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        e_rois = self.sp_db[SPDB_EV_ROIS]
        
        DEFAULTS.set('SCAN.PTYCHOGRAPHY.CENTER',  (x_roi[CENTER], y_roi[CENTER], 0, 0))
        DEFAULTS.set('SCAN.PTYCHOGRAPHY.RANGE', (x_roi[RANGE], y_roi[RANGE], 0, 0))
        DEFAULTS.set('SCAN.PTYCHOGRAPHY.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], 0, 0))
        DEFAULTS.set('SCAN.PTYCHOGRAPHY.STEP', (x_roi[STEP], y_roi[STEP], 0, 0))
        DEFAULTS.set('SCAN.PTYCHOGRAPHY.DWELL', e_rois[0][DWELL])
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

        #wdg_com = self.update_single_spatial_wdg_com()
        wdg_com = self.update_multi_spatial_wdg_com()
                
        self.roi_changed.emit(wdg_com)
        return(wdg_com)
    