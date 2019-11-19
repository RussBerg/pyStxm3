'''
Created on Aug 25, 2014

@author: bergr
'''
from PyQt5 import QtCore, QtGui
from PyQt5 import uic

import copy
import os
import numpy as np
from cls.app_data.defaults import get_style

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS
from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from cls.applications.pyStxm.scan_plugins import plugin_dir
#from cls.applications.pyStxm.scan_plugins.SampleImageWithEnergySSCAN import SampleImageWithEnergySSCAN
#from cls.applications.pyStxm.scan_plugins.SampleImageWithE712Wavegen import SampleImageWithE712Wavegen
#from cls.applications.pyStxm.scan_plugins.SampleFineImageWithE712WavegenScanClass import SampleFineImageWithE712WavegenScanClass
#from cls.applications.pyStxm.scan_plugins.TomographyWithE712Wavegen import TomographyWithE712Wavegen
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

PREC = 3

class TomographyScansParam(ScanParamWidget):

    
    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent

        if (self.sample_positioning_mode != sample_positioning_modes.GONIOMETER):
            self.name = "Tomography Scan ---- [DISABLED by scanning mode] "
            self.setEnabled(False)
            self.setToolTip('TomographyScansParam: Scan plugin is disabled while in Goniometer sample positioning mode')
        else:

            self.positioners = {'ZX':DNM_ZONEPLATE_X, 'ZY':DNM_ZONEPLATE_Y, 'ZZ':DNM_ZONEPLATE_Z, 'OX':DNM_OSA_X,
                                'OY':DNM_OSA_Y, 'OZ':DNM_OSA_Z, 'GX':DNM_GONI_X, 'GY':DNM_GONI_Y, 'GZ':DNM_GONI_Z,
                                'GT':DNM_GONI_THETA}

            # more
            DNM_EPU_POLARIZATION = DNM_EPU_POLARIZATION
            DNM_EPU_OFFSET = DNM_EPU_OFFSET
            DNM_EPU_ANGLE = DNM_EPU_ANGLE

            uic.loadUi( os.path.join(plugin_dir, 'tomography_scan.ui'), self)
            self.tomo_zpz_adjust_wdg = uic.loadUi(os.path.join(plugin_dir, 'tomo_zpz_adjust.ui'))
            self.tomo_zpz_adjust_wdg.setModal(True)
            self.connect_zpz_adjust_paramfield_signals(self.tomo_zpz_adjust_wdg)

            self.multi_region_widget = MultiRegionWidget(enable_multi_spatial=False, max_range=MAX_SCAN_RANGE_FINEX)
            self.multi_region_widget.spatial_row_selected.connect(self.on_spatial_row_selected)
            self.multi_region_widget.spatial_row_changed.connect(self.on_spatial_row_changed)
            self.multi_region_widget.spatial_row_deleted.connect(self.on_spatial_row_deleted)

            self.evGrpBox.layout().addWidget(self.multi_region_widget)
            self.scanTypeSelComboBox.currentIndexChanged.connect(self.scan_type_changed)

            self.loadScanBtn.clicked.connect(self.load_scan)
            self.defineZPZFocusAdjBtn.clicked.connect(self.on_zpz_focus_adjust)
            self.tomo_zpz_adjust_wdg.zpzEnableAdjustChkBox.clicked.connect(self.on_zpz_enable_chkbox)
            #self.useE712WavegenBtn.clicked.connect(self.on_E712WavegenBtn)

            #self.sscan_class = TomographyWithE712Wavegen()

            #self.singleEVChkBx.clicked.connect(self.on_single_energy)
            self.hdwAccelDetailsBtn.clicked.connect(self.show_hdw_accel_details)
            self.hdwAccelDetailsBtn.setToolTip('E712 Wavgen details')
            self.wdg_com = None
            self.sp_db = None
            self.load_from_defaults()
            self.init_sp_db()
            self.connect_paramfield_signals()
            self.on_plugin_focus()
            self.init_loadscan_menu()

    def connect_zpz_adjust_paramfield_signals(self, zz_adj_wdg):
        '''
        connect the 3 zpz in focus fields to double validators
        :param zz_adj_wdg: the ui that contains the zpz adjust widgets
        :return:
        '''

        mtr_zz = MAIN_OBJ.device(DNM_ZONEPLATE_Z)
        zzllm = mtr_zz.get_low_limit()
        zzhlm = mtr_zz.get_high_limit()

        fld = zz_adj_wdg.zpzStartInFocusFld
        fld.dpo = dblLineEditParamObj('zpz_start_infocus', zzllm, zzhlm, PREC, parent=fld)
        #fld.dpo.valid_returnPressed.connect(self.update_data)

        fld = zz_adj_wdg.zpzCenterInFocusFld
        fld.dpo = dblLineEditParamObj('zpz_center_infocus', zzllm, zzhlm, PREC, parent=fld)
        #fld.dpo.valid_returnPressed.connect(self.update_data)

        fld = zz_adj_wdg.zpzStopInFocusFld
        fld.dpo = dblLineEditParamObj('zpz_stop_infocus', zzllm, zzhlm, PREC, parent=fld)
        #fld.dpo.valid_returnPressed.connect(self.update_data)



    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Tomography Scan"
        self.idx = scan_panel_order.TOMOGRAPHY_SCAN  # by default
        self.type = scan_types.TOMOGRAPHY_SCAN
        self.sub_type = scan_sub_types.LINE_UNIDIR
        self.data = {}
        self.section_id = image_scan_secids[image_scan_secids.TOMO]  # by default
        self.axis_strings = ['Goniometer Y microns', 'Goniometer X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        # data_file_pfx = 'i'
        self.data_file_pfx = MAIN_OBJ.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.ROI
        self.enable_multi_region = False
        self.multi_ev = True

    def is_spatial_list_empty(self):
        '''
        overide the base implementation by checking the table to see if it is empty
        :return:
        '''
        return (self.multi_region_widget.is_spatial_list_empty())

    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()

        :returns: None

        """
        sgt = float(str(self.startGTFld.text()))
        egt = float(str(self.endGTFld.text()))

        cgt = float(sgt + egt) / 2.0
        rgt = float(egt - sgt)
        ngt = int(str(self.npointsGTFld.text()))
        stgt = float(str(self.stepGTFld.text()))

        # now create the model that this pluggin will use to record its params
        gt_roi = get_base_roi(SPDB_GT, DNM_GONI_THETA, cgt, rgt, ngt, stgt)
        goni_rois = {SPDB_GT: gt_roi}
        self.sp_db = make_spatial_db_dict(goni_rois=goni_rois)

    def on_zpz_enable_chkbox(self, chkd):
        if(chkd):
            self.tomo_zpz_adjust_wdg.zpzAdjustGrpBox.setEnabled(True)
        else:
            self.tomo_zpz_adjust_wdg.zpzAdjustGrpBox.setEnabled(False)

    def on_zpz_focus_adjust(self):

        (zpz_start, zpz_center, zpz_stop, dud) = DEFAULTS.get('SCAN.TOMO.ZPZ_ADJUST')
        #copy angles from tomo scan pluggin screen
        start = float(self.startGTFld.text())
        stop = float(self.endGTFld.text())
        center = float((start + stop) / 2.0)

        self.tomo_zpz_adjust_wdg.zpzEnableAdjustChkBox.setChecked(False)
        self.tomo_zpz_adjust_wdg.zpzAdjustGrpBox.setEnabled(False)

        self.tomo_zpz_adjust_wdg.startGTFld.setText('%.2f' % start)
        self.tomo_zpz_adjust_wdg.centerGTFld.setText('%.2f' % center)
        self.tomo_zpz_adjust_wdg.endGTFld.setText('%.2f' % stop)

        self.tomo_zpz_adjust_wdg.zpzStartInFocusFld.setText('%s' % zpz_start)
        self.tomo_zpz_adjust_wdg.zpzCenterInFocusFld.setText('%s' % zpz_center)
        self.tomo_zpz_adjust_wdg.zpzStopInFocusFld.setText('%s' % zpz_stop)

        self.tomo_zpz_adjust_wdg.okBtn.clicked.connect(self.on_close_tomo_zpz_adj)
        self.tomo_zpz_adjust_wdg.okBtn.setDefault(False)
        self.tomo_zpz_adjust_wdg.okBtn.setAutoDefault(False)
        dark = get_style('dark')
        self.tomo_zpz_adjust_wdg.setStyleSheet(dark)
        self.tomo_zpz_adjust_wdg.startGTFld.setFocus()
        self.tomo_zpz_adjust_wdg.show()


    def on_plugin_focus(self):
        '''
        this is called when this scan param receives focus on the GUI
        - basically get the current EPU values and assign them to the multiregion widget
        :return:
        '''
        #call the standard init_base_values function for scan param widgets that contain a multiRegionWidget
        if(self.isEnabled()):
            self.on_multiregion_widget_focus_init_base_values()

    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        Here we are leaving hte tomo scan so reset the zpz_adjust pv (which is used to adjust zpz focus over the angles
        of the tomo scan, back to 0.0
        :return:
        '''
        # print 'ScanParamWidget[%s] has lost focus' % self.name
        if (self.isEnabled()):
            zpz_adjust = self.main_obj.device(DNM_ZPZ_ADJUST)
            zpz_adjust.put(0.0)

        # call the base class defocus
        super(TomographyScansParam, self).on_plugin_defocus()

    def on_close_tomo_zpz_adj(self):
        self.tomo_zpz_adjust_wdg.close()
        if (self.tomo_zpz_adjust_wdg.zpzEnableAdjustChkBox.isChecked()):

            start = float(self.tomo_zpz_adjust_wdg.zpzStartInFocusFld.text())
            center = float(self.tomo_zpz_adjust_wdg.zpzCenterInFocusFld.text())
            stop = float(self.tomo_zpz_adjust_wdg.zpzStopInFocusFld.text())

            delta_start = center - start
            delta_stop = center - stop
            delta_center = float((delta_start + delta_stop)/2.0)
            delta_rng =  delta_start - delta_stop
            ngt = int(str(self.npointsGTFld.text()))
            defocus_pnts = np.linspace(delta_start, delta_stop, ngt)
            zpz_adjust_roi = get_base_roi(SPDB_G_ZPZ_ADJUST, 'NONE', delta_center, delta_rng, ngt, stepSize=None, max_scan_range=None,
                                  enable=False)
            #reverse order of setpoints
            zpz_adjust_roi[SETPOINTS] = defocus_pnts
            dct_put(self.sp_db, SPDB_G_ZPZ_ADJUST, zpz_adjust_roi)
            self.update_last_settings()

        else:
            #it has been disabled so create a table of zero's for zpz_adjust values
            ngt = int(str(self.npointsGTFld.text()))
            defocus_pnts = np.zeros(ngt)
            zpz_adjust_roi = get_base_roi(SPDB_G_ZPZ_ADJUST, 'NONE', 0, 0, ngt, stepSize=None,
                                          max_scan_range=None,
                                          enable=False)
            # reverse order of setpoints
            zpz_adjust_roi[SETPOINTS] = defocus_pnts
            dct_put(self.sp_db, SPDB_G_ZPZ_ADJUST, zpz_adjust_roi)

    def connect_paramfield_signals(self):

        mtr_t = self.main_obj.device(DNM_GONI_THETA)
        gtllm = mtr_t.get_low_limit()
        gthlm = mtr_t.get_high_limit()
        rgt = gthlm - gtllm
        lim_dct = {}
        lim_dct['GT'] = {'llm': gtllm, 'hlm': gthlm, 'rng': rgt}
        # call standard function to check the fields of the scan param and assign limits
        self.connect_param_flds_to_validator(lim_dct)


    def show_hdw_accel_details(self):
        dark = get_style('dark')
        self.sscan_class.e712_wg.setStyleSheet(dark)
        self.sscan_class.e712_wg.show()

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

        #if(self.useE712WavegenBtn.isChecked()):
        if (True):
            self.sscan_class.e712_wg.set_mode(mode)
            hline_time = self.sscan_class.e712_wg.calc_hline_time( dwell_in_sec, x_roi[NPOINTS], pxp=pxp)
            total_time_sec = float(y_roi[NPOINTS]) * (float(hline_time))
            s = 'Estimated time: %s' % secondsToStr(total_time_sec)

        else:
            if(pxp):
                hline_time = dwell_in_sec * x_roi[NPOINTS]
            else:
                hline_time = dwell_in_sec * x_roi[NPOINTS]

            total_time_sec = float(y_roi[NPOINTS]) * float(hline_time)
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
            mtr_sx = MAIN_OBJ.device(DNM_SAMPLE_X)
            mtr_sy = MAIN_OBJ.device(DNM_SAMPLE_Y)
            mtr_sfx = MAIN_OBJ.device(DNM_SAMPLE_FINE_X)
            mtr_sfy = MAIN_OBJ.device(DNM_SAMPLE_FINE_Y)
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
            #             self.idx = scan_types.SAMPLE_IMAGE #*POINT*
            #             self.type = scan_types.SAMPLE_IMAGE

            self.sub_type = scan_sub_types.POINT_BY_POINT

        else:
            # line by line
            #             self.idx = scan_types.SAMPLE_IMAGE #by default
            #             self.type = scan_types.SAMPLE_IMAGE
            self.sub_type = scan_sub_types.LINE_UNIDIR

        
    def scan_type_changed(self, idx):
        if(idx == 0):
            #line by line
#             self.idx = scan_types.SAMPLE_IMAGE #by default
#             self.type = scan_types.SAMPLE_IMAGE
            self.sub_type = scan_sub_types.LINE_UNIDIR
            
        else:
            #point by point
#             self.idx = scan_types.SAMPLE_IMAGE #*POINT*
#             self.type = scan_types.SAMPLE_IMAGE
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
        """
        set_roi standard function supported by all scan pluggins to initialize the GUI for this scan with values
        stored in the defaults library

        :param roi: is a standard dict returned from the call to DEFAULTS.get_defaults()
        :type roi: dict.

        :returns: None

        """
        # print 'det_scan: set_roi: ' , roi
        (cx, cy, cz, gt_c) = roi[CENTER]
        (rx, ry, rz, gt_rng) = roi[RANGE]
        (nx, ny, nz, gt_npts) = roi[NPOINTS]
        (sx, sy, sz, gt_step) = roi[STEP]

        gt_start = gt_c - (gt_rng*0.5)
        gt_stop = gt_c + (gt_rng * 0.5)
        self.set_parm(self.startGTFld, gt_start)
        self.set_parm(self.endGTFld, gt_stop)

        if (gt_npts != None):
            self.set_parm(self.npointsGTFld, gt_npts, type='int', floor=1)

        if (gt_step != None):
            self.set_parm(self.stepGTFld, gt_step, type='float', floor=0)


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
        if (not self.isEnabled()):
            # if this plugin is disabled because of the scanning mode then just return without oing anything
            return

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
            #print 'image_scan: mod_roi: unsupported widget_com CMND [%d]' % wdg_com[CMND]
            #return
            gt_roi = dct_get(wdg_com, SPDB_GT)
            if (gt_roi[START] != None):
                self.set_parm(self.startGTFld, gt_roi[START], type='float')

            if (gt_roi[STOP] != None):
                self.set_parm(self.endGTFld, gt_roi[STOP], type='float')

            if (gt_roi[NPOINTS] != None):
                self.set_parm(self.npointsGTFld, gt_roi[NPOINTS], type='int', floor=1)

            if (gt_roi[STEP] != None):
                self.set_parm(self.stepGTFld, gt_roi[STEP], type='float', floor=0)

        if (wdg_com[CMND] == widget_com_cmnd_types.SELECT_ROI):
            self.update_last_settings()

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

            #allow the loading of fine image scans into the tomo scan so that spatial values can easily be reused
            image_scans = [scan_types.SAMPLE_IMAGE, scan_types.TOMOGRAPHY_SCAN]
            if((not ev_only) and (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in image_scans)):
                _logger.error('Wrong scan type, scan not loaded')
                return

            if(not ev_only):
                if(dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE) == scan_sub_types.LINE_UNIDIR):
                    #image Line by Line
                    self.scanTypeSelComboBox.setCurrentIndex(1)
                else:
                    #image Point by Point
                    self.scanTypeSelComboBox.setCurrentIndex(0)

                # if(dct_get(sp_db, SPDB_HDW_ACCEL_USE)):
                #     self.useE712WavegenBtn.setChecked(True)
                # else:
                #     self.useE712WavegenBtn.setChecked(False)

                if (dct_get(sp_db, SPDB_HDW_ACCEL_AUTO_DDL)):
                    self.autoDDLRadBtn.setChecked(True)
                else:
                    self.autoDDLRadBtn.setChecked(False)

                if (dct_get(sp_db, SPDB_HDW_ACCEL_REINIT_DDL)):
                    self.reinitDDLRadBtn.setChecked(True)
                else:
                    self.reinitDDLRadBtn.setChecked(False)

            # load GT fields
            gt_roi = dct_get(sp_db, SPDB_GT)

            # if do_recalc then it is because mod_roi() has been called by a signal that the
            # plotWidgetter has resized/moved the ROI, the recalc of x/y when the number of points
            # is changed is handled above in the signal for the npointsFld
            on_range_changed(gt_roi)

            self.set_parm(self.startGTFld, gt_roi[START])
            self.set_parm(self.endGTFld, gt_roi[STOP])

            if (gt_roi[NPOINTS] != None):
                self.set_parm(self.npointsGTFld, gt_roi[NPOINTS], type='int', floor=1)

            if (gt_roi[STEP] != None):
                self.set_parm(self.stepGTFld, gt_roi[STEP], type='float', floor=0)
            #end load GT fields

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

                if(dct_get(sp_db, SPDB_EV_NPOINTS) > 1):
                    self.type = scan_types.TOMOGRAPHY_SCAN
                    dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, scan_types.TOMOGRAPHY_SCAN)     #the scan type: scan_types-> Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')
                    #dct_put(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, None)
                else:
                    dct_put(sp_db, SPDB_SCAN_PLUGIN_TYPE, scan_types.TOMOGRAPHY_SCAN)
    
    
    
    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to 
        get the data from the pluggins UI widgets and write them into a dict returned by 
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
        the scan classes configure() functions
    
        :returns: None
     
        """
        
        self.update_type()
        self.update_last_settings(incl_zpz_adjust=False)
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.wdg_com = self.GONI_SCAN_update_data()
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
        mtr_zpx = MAIN_OBJ.device(DNM_ZONEPLATE_X)
        mtr_zpy = MAIN_OBJ.device(DNM_ZONEPLATE_Y)
        #mtr_osax = MAIN_OBJ.device('OSAX.X')
        #mtr_osay = MAIN_OBJ.device('OSAY.Y')
        mtr_gx = MAIN_OBJ.device(DNM_GONI_X)
        mtr_gy = MAIN_OBJ.device(DNM_GONI_Y)
        
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
        if('SX' in list(self.positioners.keys())):
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
        elif('GX' in list(self.positioners.keys())):    
            mtr_x = self.main_obj.device(DNM_GONI_X)
            mtr_y = self.main_obj.device(DNM_GONI_Y)
        else:
            return((0.0, 0.0))    
        return((mtr_x.get_position(), mtr_y.get_position()))
    
    def get_theta_fld_vals(self):
        roi = {}
        self.assign_flds(roi, 'Theta')
        return(roi)

    def update_last_settings(self, incl_zpz_adjust=True):
        """ update the 'default' settings that will be reloaded when this scan pluggin is selected again
        """
        gt_roi = dct_get(self.sp_db, SPDB_GT)

        DEFAULTS.set('SCAN.TOMO.CENTER', (0, 0, 0, gt_roi[CENTER]))
        DEFAULTS.set('SCAN.TOMO.RANGE', (0, 0, 0, gt_roi[RANGE]))
        DEFAULTS.set('SCAN.TOMO.NPOINTS', (0, 0, 0, gt_roi[NPOINTS]))
        DEFAULTS.set('SCAN.TOMO.STEP', (0, 0, 0, gt_roi[STEP]))

        if(incl_zpz_adjust):
            # self.tomo_zpz_adjust_wdg.zpzEnableAdjustChkBox.setChecked(False)
            zpz_start = self.tomo_zpz_adjust_wdg.zpzStartInFocusFld.text()
            zpz_center = self.tomo_zpz_adjust_wdg.zpzCenterInFocusFld.text()
            zpz_stop = self.tomo_zpz_adjust_wdg.zpzStopInFocusFld.text()
            DEFAULTS.set('SCAN.TOMO.ZPZ_ADJUST', (zpz_start, zpz_center, zpz_stop, 0))

        DEFAULTS.update()

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
        #sp_db = copy.deepcopy(self.sp_db)
        if(len(sp_dbs) == 1):
            #single spatial, check for multi goni theta
            gt_npoints = dct_get(self.sp_db, SPDB_GTNPOINTS)
            gt_setpoints = dct_get(self.sp_db, SPDB_GTSETPOINTS)
            if(gt_npoints > 1):
                new_sp_dbs = {}
                #it is multi goni theta so create a sp_db for each angle
                sp_id = list(sp_dbs.keys())[0]
                sp_db = sp_dbs[sp_id]
                for i in range(gt_npoints):
                    #_sp_db = copy.deepcopy(sp_db)
                    #new_sp_dbs[i] = _sp_db
                    new_sp_dbs[i] = sp_db
                sp_dbs = new_sp_dbs

        for sp_id in sp_dbs:
            sp_db = sp_dbs[sp_id]
            sp_db = self.modify_sp_db_for_goni(sp_db)

        dct_put(wdg_com, WDGCOM_SPATIAL_ROIS, sp_dbs)

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
    
    
    