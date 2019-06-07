'''
Created on Nov 15, 2017

@author: bergr
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtTest import QSignalSpy

from PyQt5 import uic

import os
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS
from cls.applications.pyStxm.scan_plugins import plugin_dir
from cls.applications.pyStxm.scan_plugins.CoarseSampleImageScan import CoarseSampleImageScanClass
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from bcm.devices.device_names import *

from cls.data_io.stxm_data_io import STXMDataIo

from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, widget_com_cmnd_types, \
    on_range_changed, on_center_changed, get_first_sp_db_from_wdg_com

from cls.types.stxmTypes import scan_types, scan_sub_types, \
    energy_scan_order_types, sample_positioning_modes, sample_fine_positioning_modes,scan_types, scan_panel_order, spatial_type_prefix, image_types
from cls.scanning.base import ScanParamWidget, zp_focus_modes

from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, \
    get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
MAX_SCAN_RANGE_X = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_X')
MAX_SCAN_RANGE_Y = MAIN_OBJ.get_preset_as_float('MAX_SCAN_RANGE_Y')

class CoarseImageScanParam(ScanParamWidget):

    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi(os.path.join(plugin_dir, 'coarse_image_scan.ui'), self)

        #disable this pluggin if we are in GONIOMETER mode (because coarse scans make no sense)
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.name = "Coarse Image Scan ---- [DISABLED by scanning mode] "
            self.setEnabled(False)
            self.setToolTip('CoarseImageScanParam: Scan plugin is disabled while in Goniometer sample positioning mode')
        else:

            self.plotWidget = None
            self.loadScanBtn.clicked.connect(self.load_scan)

            self.scan_class = CoarseSampleImageScanClass(main_obj=self.main_obj)

            self.scanTypeSelComboBox.currentIndexChanged.connect(self.scan_type_changed)

            self.data = {}
            self.sp_db = None
            self.load_from_defaults()
            self.init_sp_db()
            self.connect_paramfield_signals()
            self.on_single_spatial_npoints_changed()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Coarse Image Scan"
        self.idx = scan_panel_order.COARSE_IMAGE_SCAN
        self.type = scan_types.COARSE_IMAGE_SCAN
        self.sub_type = scan_sub_types.LINE_UNIDIR
        self.section_id = 'COARSE_IMAGE'
        self.axis_strings = ['Sample Y microns', 'Sample X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        # data_file_pfx = 'd'
        self.data_file_pfx = MAIN_OBJ.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.ROI

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
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
        super(CoarseImageScanParam, self).on_plugin_defocus()

    def scan_type_changed(self, idx):
        if (idx == 0):
            # line by line
            #             self.idx = scan_types.SAMPLE_IMAGE #by default
            #             self.type = scan_types.SAMPLE_IMAGE
            self.sub_type = scan_sub_types.LINE_UNIDIR

        else:
            # point by point
            #             self.idx = scan_types.SAMPLE_IMAGE #*POINT*
            #             self.type = scan_types.SAMPLE_IMAGE
            self.sub_type = scan_sub_types.POINT_BY_POINT


        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        dwell = self.sp_db[SPDB_EV_ROIS][0][DWELL]
        if (self.sub_type == scan_sub_types.POINT_BY_POINT):
            self.calc_new_scan_time_estemate(True, x_roi, y_roi, dwell)
        else:
              self.calc_new_scan_time_estemate(False, x_roi, y_roi, dwell)


    def connect_paramfield_signals(self):

        mtr_x = MAIN_OBJ.device(DNM_SAMPLE_X)
        mtr_y = MAIN_OBJ.device(DNM_SAMPLE_Y)

        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()

        rx = xhlm - xllm
        ry = yhlm - yllm

        lim_dct = {}
        lim_dct['X'] = {'llm': xllm, 'hlm': xhlm, 'rng': rx}
        lim_dct['Y'] = {'llm': yllm, 'hlm': yhlm, 'rng': ry}

        # call standard function to check the fields of the scan param and assign limits
        self.connect_param_flds_to_validator(lim_dct)

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

        dct_put(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, self.sub_type)

    def update_min_max(self):

        mtr_x = MAIN_OBJ.device(DNM_SAMPLE_X)
        mtr_y = MAIN_OBJ.device(DNM_SAMPLE_Y)

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
        """ to be overridden by inheriting class
        """
        mtr_x = MAIN_OBJ.device(DNM_SAMPLE_X)
        mtr_y = MAIN_OBJ.device(DNM_SAMPLE_Y)

        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()

        bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.80)  # %80 of max
        alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95)  # %95 of max

        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Sample Coarse Capabilities',
                               get_alarm_fill_pattern())
        normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Sample Coarse Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Nearing max Range of Sample Coarse X/Y', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample Coarse X/Y', get_alarm_fill_pattern())

        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)
        self.max_scan_range = ((xhlm - xllm), (yhlm - yllm))

    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()

        :returns: None

        """
        cx = float(str(self.centerXFld.text()))
        rx = float(str(self.rangeXFld.text()))
        cy = float(str(self.centerYFld.text()))
        ry = float(str(self.rangeYFld.text()))
        dwell = float(str(self.dwellFld.text()))
        nx = int(str(self.npointsXFld.text()))
        ny = int(str(self.npointsYFld.text()))
        sx = float(str(self.stepXFld.text()))
        sy = float(str(self.stepYFld.text()))
        # now create the model that this pluggin will use to record its params
        x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, cx, rx, nx, sx)
        y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, cy, ry, ny, sy)
        z_roi = get_base_roi(SPDB_Z, DNM_DETECTOR_Z, 0, 0, 0, enable=False)

        energy_pos = MAIN_OBJ.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)

        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, z_roi=z_roi, e_roi=e_roi)

    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        ret = self.check_center_range_xy_scan_limits(DNM_SAMPLE_X, DNM_SAMPLE_Y)
        return (ret)

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
        # print 'det_scan: set_roi: ' , roi
        (cx, cy, cz, c0) = roi[CENTER]
        (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (sx, sy, sz, s0) = roi[STEP]

        if ('DWELL' in roi):
            self.set_parm(self.dwellFld, roi[DWELL])

        self.set_parm(self.centerXFld, cx)
        self.set_parm(self.centerYFld, cy)

        if (rx != None):
            self.set_parm(self.rangeXFld, rx)
        if (ry != None):
            self.set_parm(self.rangeYFld, ry)

        if (nx != None):
            self.set_parm(self.npointsXFld, nx, type='int', floor=2)

        if (ny != None):
            self.set_parm(self.npointsYFld, ny, type='int', floor=2)

        if (sx != None):
            self.set_parm(self.stepXFld, sx, type='float', floor=0)

        if (sy != None):
            self.set_parm(self.stepYFld, sy, type='float', floor=0)

    def mod_roi(self, sp_db, do_recalc=True, sp_only=True):
        """
        sp_db is a widget_com dict
        The purpose of the mod_roi() function is to update the fields in the GUI with the correct values
        it can be called by either a signal from one of the edit fields (ex: self.centerXFld) or
        by a signal from a plotter (via the main gui that is connected to the plotter) so that as a user
        grabs a region of interest marker in the plot and either moves or resizes it, those new center and size
        values will be delivered here and,  if required, the stepsizes will be recalculated


        :param sp_db: is a standard dict returned from the call to sm.stxm_control.stxm_utils.roi_utils.make_spatial_db_dict()
        :type sp_db: dict.

        :param do_recalc: selectively the STEP of the ROI's for X and Y can be recalculated if the number of points or range have changed
        :type do_recalc: flag.

        :returns: None

        """
        if (sp_db[CMND] == widget_com_cmnd_types.DEL_ROI):
            return

        if (sp_db[CMND] == widget_com_cmnd_types.LOAD_SCAN):
            self.sp_db = sp_db
        else:
            if (sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
                # dct_put(self.sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, dct_get(sp_db, SPDB_PLOT_ITEM_ID))
                dct_put(self.sp_db, SPDB_ID_VAL, dct_get(sp_db, SPDB_PLOT_ITEM_ID))

            self.sp_db[SPDB_X][CENTER] = sp_db[SPDB_X][CENTER]

            if (sp_db[SPDB_X][RANGE] != 0):
                #only modify if larger than fine scans
                if( sp_db[SPDB_X][RANGE] > MAX_SCAN_RANGE_FINEX):
                    self.sp_db[SPDB_X][RANGE] = sp_db[SPDB_X][RANGE]

            self.sp_db[SPDB_Y][CENTER] = sp_db[SPDB_Y][CENTER]

            if (sp_db[SPDB_Y][RANGE] != 0):
                # only modify if larger than fine scans
                if (sp_db[SPDB_Y][RANGE] > MAX_SCAN_RANGE_FINEY):
                    self.sp_db[SPDB_Y][RANGE] = sp_db[SPDB_Y][RANGE]

        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        e_rois = self.sp_db[SPDB_EV_ROIS]

        # if do_recalc then it is because mod_roi() has been called by a signal that the
        # plotWidgetter has resized/moved the ROI, the recalc of x/y when the number of points
        # is changed is handled above in the signal for the npointsFld
        if (do_recalc):
            on_range_changed(x_roi)
            on_range_changed(y_roi)

        self.set_parm(self.centerXFld, x_roi[CENTER])
        self.set_parm(self.centerYFld, y_roi[CENTER])

        if (e_rois[0][DWELL] != None):
            self.set_parm(self.dwellFld, e_rois[0][DWELL])

        if (x_roi[RANGE] != None):
            self.set_parm(self.rangeXFld, x_roi[RANGE])
        if (y_roi[RANGE] != None):
            self.set_parm(self.rangeYFld, y_roi[RANGE])

        if (x_roi[NPOINTS] != None):
            self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=2)

        if (y_roi[NPOINTS] != None):
            self.set_parm(self.npointsYFld, y_roi[NPOINTS], type='int', floor=2)

        if (x_roi[STEP] != None):
            self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)

        if (y_roi[STEP] != None):
            self.set_parm(self.stepYFld, y_roi[STEP], type='float', floor=0)

        # if (sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
        #     self.update_last_settings()

    def update_last_settings(self):
        """ update the 'default' settings that will be reloaded when this scan pluggin is selected again
        """
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        e_rois = self.sp_db[SPDB_EV_ROIS]

        DEFAULTS.set('SCAN.%s.CENTER' % self.section_id, (x_roi[CENTER], y_roi[CENTER], 0, 0))
        DEFAULTS.set('SCAN.%s.RANGE' % self.section_id, (x_roi[RANGE], y_roi[RANGE], 0, 0))
        DEFAULTS.set('SCAN.%s.NPOINTS' % self.section_id, (x_roi[NPOINTS], y_roi[NPOINTS], 0, 0))
        DEFAULTS.set('SCAN.%s.STEP' % self.section_id, (x_roi[STEP], y_roi[STEP], 0, 0))
        DEFAULTS.set('SCAN.%s.DWELL' % self.section_id, e_rois[0][DWELL])
        DEFAULTS.update()

    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to
        get the data from the pluggins UI widgets and write them into a dict returned by
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by
        the scan classes configure() functions

        :returns: None

        """
        # update local widget_com dict
        self.update_sub_type()
        wdg_com = self.update_single_spatial_wdg_com()

        self.roi_changed.emit(wdg_com)
        return (wdg_com)
