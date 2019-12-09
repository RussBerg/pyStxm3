'''
Created on June 28, 2019

@author: bergr
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

import time
import os

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, DEFAULTS
from cls.applications.pyStxm.scan_plugins import plugin_dir
# from cls.applications.pyStxm.scan_plugins.PatternGenWithE712WavegenScan import PatternGenWithE712WavegenScanClass
from cls.applications.pyStxm.scan_plugins.PatternGenScan import PatternGenScanClass
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from bcm.devices.device_names import *

from cls.data_io.stxm_data_io import STXMDataIo
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, \
    get_axis_setpoints_from_sp_db

from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, widget_com_cmnd_types, \
    on_range_changed, on_center_changed

from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.types.stxmTypes import scan_types, scan_sub_types, scan_panel_order, spatial_type_prefix, \
    sample_positioning_modes, sample_fine_positioning_modes

# from cls.plotWidgets.shapes.pattern_gen import PAD_SIZE
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, \
    get_warn_fill_pattern, get_alarm_fill_pattern

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

MAX_SCAN_RANGE_FINEX = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_X')
MAX_SCAN_RANGE_FINEY = MAIN_OBJ.get_preset_as_float('MAX_FINE_SCAN_RANGE_Y')
USE_E712_HDW_ACCEL = MAIN_OBJ.get_preset_as_int('USE_E712_HDW_ACCEL')

_logger = get_module_logger(__name__)


class PatternGeneratorScanParam(ScanParamWidget):
    data = {}

    def __init__(self, parent=None):
        ScanParamWidget.__init__(self, main_obj=MAIN_OBJ, data_io=STXMDataIo, dflts=DEFAULTS)
        self._parent = parent
        uic.loadUi(os.path.join(plugin_dir, 'pattern_gen_scan.ui'), self)
        self.scan_mod_path, self.scan_mod_name = self.derive_scan_mod_name(__file__)

        # if(not USE_E712_HDW_ACCEL):
        # 	self.name = "Pattern Generator Scan ---- [DISABLED, non hardware acclerated version is currently not supported] "
        # 	self.setEnabled(False)
        # 	self.setToolTip('PatternGeneratorScanParam: Scan plugin is disabled, non hardware acclerated version is currently not supported ')
        # else:

        # self.scan_class = PatternGenWithE712WavegenScanClass(main_obj=self.main_obj)
        self.scan_class = PatternGenScanClass(main_obj=self.main_obj)
        self.sp_db = None
        self.load_from_defaults()
        self.init_sp_db()
        self.connect_paramfield_signals()
        self.on_single_spatial_npoints_changed()

        self.loadScanBtn.clicked.connect(self.load_scan)
        self.showPatternBtn.clicked.connect(self.on_show_pattern_btn_clicked)
        self.defaultBtn.clicked.connect(self.on_default_btn_clicked)

        # self.init_test_module()
        self.init_loadscan_menu()

    def init_plugin(self):
        '''
        set the plugin specific details to common attributes
        :return:
        '''
        self.name = "Pattern Generator"
        self.idx = scan_panel_order.PATTERN_GEN_SCAN
        self.type = scan_types.PATTERN_GEN_SCAN
        self.section_id = 'PATTERN_GEN'
        self.axis_strings = ['Sample Y microns', 'Sample X microns', '', '']
        self.zp_focus_mode = zp_focus_modes.A0MOD
        self.data_file_pfx = self.main_obj.get_datafile_prefix()
        self.plot_item_type = spatial_type_prefix.ROI
        self._help_html_fpath = os.path.join('interface', 'window_system', 'scan_plugins', 'pattern_generator.html')
        self._help_ttip = 'Pattern Generator documentation and instructions'

    def on_plugin_focus(self):
        '''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            # ask the plotter to show the pattern if show_pattern button is checked
            if (self.showPatternBtn.isChecked()):
                self.on_show_pattern_btn_clicked(True)
            else:
                self.on_show_pattern_btn_clicked(False)

    def on_plugin_scan_start(self):
        '''
        This function overrids the base implementation so that we can uncheck the show pattern button when the scan starts
        :param self:
        :return:
        '''
        self.showPatternBtn.setChecked(False)

    def on_plugin_defocus(self):
        '''
        This is a function that is called when the plugin leaves focus from the main GUI
        :return:
        '''
        if (self.isEnabled()):
            self.update_last_settings()

        # if(USE_E712_HDW_ACCEL):
        # 	#reset the wavetable rate
        # 	self.scan_class.e712_wg.set_forced_rate(1)
        # call the base class defocus
        super(PatternGeneratorScanParam, self).on_plugin_defocus()

    def on_show_pattern_btn_clicked(self, chkd):
        '''
        here we emit a signal that allows us to call a function back in stxmMain that will draw the pattern,
        only the main app knows about the polotter so that is why it was done this way
        :param chkd:
        :return:
        '''
        # emit a signal that stxmMain is listening for and call show_pattern_generator_pattern in stxmMain
        xc = float(self.centerXFld.text())
        yc = float(self.centerYFld.text())
        # mtr_x = self.main_obj.get_sample_positioner('X')
        # mtr_y = self.main_obj.get_sample_positioner('Y')
        # xc = mtr_x.get_position()
        # yc = mtr_y.get_position()
        # self.set_parm(self.centerXFld, xc)
        # self.set_parm(self.centerYFld, yc)
        pad_size = float(self.padSizeFld.text())
        self.call_main_func.emit('show_pattern_generator_pattern', (chkd, xc, yc, pad_size))

    def connect_paramfield_signals(self):

        # mtr_x = self.main_obj.device(DNM_SAMPLE_X)
        # mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
        mtr_x = self.main_obj.get_sample_positioner('X')
        mtr_y = self.main_obj.get_sample_positioner('Y')

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
        # set dwell time limits from 0 to 100,000 ms
        self.padFld_1.dpo = dblLineEditParamObj('padFld_1', 0.0, 100000.0, 2, parent=self.padFld_1)
        self.padFld_2.dpo = dblLineEditParamObj('padFld_2', 0.0, 100000.0, 2, parent=self.padFld_2)
        self.padFld_3.dpo = dblLineEditParamObj('padFld_3', 0.0, 100000.0, 2, parent=self.padFld_3)

        self.padFld_4.dpo = dblLineEditParamObj('padFld_4', 0.0, 100000.0, 2, parent=self.padFld_4)
        self.padFld_5.dpo = dblLineEditParamObj('padFld_5', 0.0, 100000.0, 2, parent=self.padFld_5)
        self.padFld_6.dpo = dblLineEditParamObj('padFld_6', 0.0, 100000.0, 2, parent=self.padFld_6)

        self.padFld_7.dpo = dblLineEditParamObj('padFld_7', 0.0, 100000.0, 2, parent=self.padFld_7)
        self.padFld_8.dpo = dblLineEditParamObj('padFld_8', 0.0, 100000.0, 2, parent=self.padFld_8)
        self.padFld_9.dpo = dblLineEditParamObj('padFld_9', 0.0, 100000.0, 2, parent=self.padFld_9)

        # set max range to the smallest of X or Y ranges (may not be the same)
        # it is divided by 5 because each of the 3 pads is separated by same pad sized distance so...
        #     1   2   3   4   5
        #  [pad1]  [pad2]  [pad3]

        if (MAX_SCAN_RANGE_FINEX > MAX_SCAN_RANGE_FINEY):
            max_pad_size = float(MAX_SCAN_RANGE_FINEY) / 5.0
        else:
            max_pad_size = float(MAX_SCAN_RANGE_FINEX) / 5.0

        self.padSizeFld.dpo = dblLineEditParamObj('padSizeFld', 0.5, max_pad_size, 2, parent=self.padSizeFld)
        # when the pad size has changed make sure to recalc the roi (step etc)
        self.padSizeFld.dpo.valid_returnPressed.connect(self.on_single_spatial_range_changed)
        self.padSizeFld.setToolTip(
            'The range allowed by the fine stage is min %.2f to a max of %.2f um' % (0.5, max_pad_size))

    def update_min_max(self):
        # mtr_x = self.main_obj.device(DNM_SAMPLE_X)
        # mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
        mtr_x = self.main_obj.get_sample_positioner('X')
        mtr_y = self.main_obj.get_sample_positioner('Y')

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

    # dpo = self.rangeXFld.dpo
    # self.update_dpo_min_max(dpo, rx, rx)
    #
    # dpo = self.rangeYFld.dpo
    # self.update_dpo_min_max(dpo, ry, ry)

    def gen_max_scan_range_limit_def(self):
        """ to be overridden by inheriting class
        """
        # mtr_x = self.main_obj.device(DNM_SAMPLE_X)
        # mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
        mtr_x = self.main_obj.get_sample_positioner('X')
        mtr_y = self.main_obj.get_sample_positioner('Y')

        xllm = mtr_x.get_low_limit()
        xhlm = mtr_x.get_high_limit()
        yllm = mtr_y.get_low_limit()
        yhlm = mtr_y.get_high_limit()

        bounding_qrect = QtCore.QRectF(QtCore.QPointF(xllm, yhlm), QtCore.QPointF(xhlm, yllm))
        warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.80)  # %80 of max
        alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95)  # %95 of max

        bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Sample X/Y Capabilities',
                               get_alarm_fill_pattern())
        normal = ROILimitObj(bounding_qrect, get_normal_clr(45), 'Pattern Gen Scan', get_normal_fill_pattern())
        warn = ROILimitObj(warn_qrect, get_warn_clr(150), 'Nearing max Range of Sample X/Y', get_warn_fill_pattern())
        alarm = ROILimitObj(alarm_qrect, get_alarm_clr(255), 'Beyond range of Sample X/Y', get_alarm_fill_pattern())

        self.roi_limit_def = ROILimitDef(bounding, normal, warn, alarm)

    def init_sp_db(self):
        """
        init_sp_db standard function supported by all scan pluggins to initialize the local widget_com dict to whatever the
        GUI is currently displaying, this is usually called after the call to self.load_from_defaults()

        :returns: None

        """
        # get current sample position
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            x_pos = self.main_obj.device(DNM_GONI_X).get_position()
            y_pos = self.main_obj.device(DNM_GONI_Y).get_position()
        else:
            x_pos = self.main_obj.device(DNM_SAMPLE_X).get_position()
            y_pos = self.main_obj.device(DNM_SAMPLE_Y).get_position()

        self.set_parm(self.centerXFld, x_pos)
        self.set_parm(self.centerYFld, y_pos)

        cx = float(str(self.centerXFld.text()))
        # rx = float(str(self.rangeXFld.text()))
        rx = 5.0
        cy = float(str(self.centerYFld.text()))
        # ry = float(str(self.rangeYFld.text()))
        ry = 5.0
        dwell = 1.0
        nx = int(str(self.npointsXFld.text()))
        ny = int(str(self.npointsYFld.text()))
        sx = float(str(self.stepXFld.text()))
        sy = float(str(self.stepYFld.text()))
        # now create the model that this pluggin will use to record its params
        x_src = self.main_obj.device(DNM_SAMPLE_X).get_name()
        y_src = self.main_obj.device(DNM_SAMPLE_Y).get_name()

        x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, cx, rx, nx, sx, src=x_src)
        y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, cy, ry, ny, sy, src=y_src)

        energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
        e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)

        self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi)

    def check_scan_limits(self):
        ''' a function to be implemented by the scan pluggin that
        checks the scan parameters against the soft limits of the
        positioners, if all is well return true else false

        This function should provide an explicit error log msg to aide the user
        '''
        # ret = self.check_center_range_xy_scan_limits(DNM_SAMPLE_X, DNM_SAMPLE_Y)
        ret = True
        return (ret)

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
        # (rx, ry, rz, s0) = roi[RANGE]
        (nx, ny, nz, n0) = roi[NPOINTS]
        (sx, sy, sz, s0) = roi[STEP]
        pad_size = float(roi['PAD_SIZE'])

        self.set_parm(self.padSizeFld, pad_size, type='float', floor=0.05)
        self.set_parm(self.centerXFld, cx)
        self.set_parm(self.centerYFld, cy)

        if (nx != None):
            self.set_parm(self.npointsXFld, nx, type='int', floor=2)

        if (ny != None):
            self.set_parm(self.npointsYFld, ny, type='int', floor=2)

        if (sx != None):
            self.set_parm(self.stepXFld, sx, type='float', floor=0)

        if (sy != None):
            self.set_parm(self.stepYFld, sy, type='float', floor=0)

    def mod_roi(self, sp_db, do_recalc=True, sp_only=False):
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
            self.sp_db[SPDB_Y][CENTER] = sp_db[SPDB_Y][CENTER]

        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]

        # rng = float(self.padSizeFld.text())

        # x_roi[RANGE] = rng
        # y_roi[RANGE] = rng
        # e_rois = self.sp_db[SPDB_EV_ROIS]
        #
        # #if do_recalc then it is because mod_roi() has been called by a signal that the
        # #plotWidgetter has resized/moved the ROI, the recalc of x/y when the number of points
        # #is changed is handled above in the signal for the npointsFld
        # if(do_recalc):
        # make sure that the pad size has been factored into the step size calc
        on_range_changed(x_roi)
        on_range_changed(y_roi)

        x_cntr, y_cntr = dct_get(self.sp_db, SPDB_SPATIAL_ROIS_CENTER)
        # skip setting the center position because it most likely will not make sense to reload it
        # self.set_parm(self.centerXFld, x_cntr)
        # self.set_parm(self.centerYFld, y_cntr)

        if (x_roi[NPOINTS] != None):
            self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=2)

        if (y_roi[NPOINTS] != None):
            self.set_parm(self.npointsYFld, y_roi[NPOINTS], type='int', floor=2)

        if (x_roi[STEP] != None):
            self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)

        if (y_roi[STEP] != None):
            self.set_parm(self.stepYFld, y_roi[STEP], type='float', floor=0)

    # use the range specified in the x_roi to set the pad size
    # if (x_roi[RANGE] != None):
    #	self.set_parm(self.padSizeFld, x_roi[RANGE], type='float', floor=0.5)

    # if(sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
    # 	self.update_last_settings()

    def load_roi(self, wdg_com, append=False, ev_only=False, sp_only=False):
        """
        Override the base level load_roi()
        take a widget communications dict and load the plugin GUI with the spatial region, also
        set the scan subtype selection pulldown for point by point or line
        """

        # wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)

        if (wdg_com[WDGCOM_CMND] == widget_com_cmnd_types.LOAD_SCAN):
            # load the dwells for each pad
            sp_rois = dct_get(wdg_com, WDGCOM_SPATIAL_ROIS)
            i = 1
            for sp_id in sp_rois.keys():
                _sp_db = sp_rois[sp_id]
                dwell = _sp_db[EV_ROIS][0][DWELL]
                fld = getattr(self, 'padFld_%d' % i)
                fld.setText(str('%.2f' % dwell))
                if (i == 5):
                    sp_db = _sp_db
                i += 1

            if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != self.type):
                return

            # make sure the LOAD_SCAN command is set
            dct_put(sp_db, CMND, widget_com_cmnd_types.LOAD_SCAN)

            self.mod_roi(sp_db, do_recalc=False, sp_only=sp_only)
        # THIS CALL IS VERY IMPORTANT IN ORDER TO KEEP TEHPLOT AND TABLES IN SYNC

    # add_to_unique_roi_id_list(sp_db[SPDB_ID_VAL])

    # emit roi_changed so that the plotter can be signalled to create the ROI shap items
    # self.roi_changed.emit(wdg_com)

    def update_last_settings(self):
        """ update the 'default' settings that will be reloaded when this scan pluggin is selected again
        """
        x_roi = self.sp_db[SPDB_X]
        y_roi = self.sp_db[SPDB_Y]
        e_rois = self.sp_db[SPDB_EV_ROIS]

        DEFAULTS.set('SCAN.PATTERN_GEN.CENTER', (x_roi[CENTER], y_roi[CENTER], 0, 0))
        DEFAULTS.set('SCAN.PATTERN_GEN.RANGE', (x_roi[RANGE], y_roi[RANGE], 0, 0))
        DEFAULTS.set('SCAN.PATTERN_GEN.NPOINTS', (x_roi[NPOINTS], y_roi[NPOINTS], 0, 0))
        DEFAULTS.set('SCAN.PATTERN_GEN.STEP', (x_roi[STEP], y_roi[STEP], 0, 0))
        DEFAULTS.set('SCAN.PATTERN_GEN.DWELL', e_rois[0][DWELL])

        DEFAULTS.set('SCAN.PATTERN_GEN.PAD1', str(self.padFld_1.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD2', str(self.padFld_2.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD3', str(self.padFld_3.text()))

        DEFAULTS.set('SCAN.PATTERN_GEN.PAD4', str(self.padFld_4.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD5', str(self.padFld_5.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD6', str(self.padFld_6.text()))

        DEFAULTS.set('SCAN.PATTERN_GEN.PAD7', str(self.padFld_7.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD8', str(self.padFld_8.text()))
        DEFAULTS.set('SCAN.PATTERN_GEN.PAD9', str(self.padFld_9.text()))

        DEFAULTS.set('SCAN.PATTERN_GEN.PAD_SIZE', float(self.padSizeFld.text()))

        DEFAULTS.update()

    def gen_pad(self, xc, yc, pad_width, dwell):
        '''
        convienience function that takes a center and creates a pad tuple
            pad = ((xc, yc), dwell, rect)
        :param xc:
        :param yc:
        :param pad_centers_width:
        :param dwell:
        :return:
        '''
        half_pad = (pad_width * 0.5)
        top = yc - half_pad
        left = xc - half_pad
        btm = yc + half_pad
        right = xc + half_pad
        rect = (left, top, right, btm)
        pad = {'centers': (xc, yc), 'dwell': dwell, 'rect': rect}
        return (pad)

    def on_default_btn_clicked(self):
        '''
        handler for default button clicked, just load the standard dwell times for the 9 pads
        pad layout
            1	2	3
            4	5	6
            7	8	9
        :return:
        '''
        self.padFld_1.setText(str(12.5))
        self.padFld_2.setText(str(25.0))
        self.padFld_3.setText(str(50.0))

        self.padFld_4.setText(str(100.0))
        self.padFld_5.setText(str(250.0))
        self.padFld_6.setText(str(375.0))

        self.padFld_7.setText(str(500.0))
        self.padFld_8.setText(str(750.0))
        self.padFld_9.setText(str(1000.0))

    def get_pattern_pads(self, xc, yc, pad_width):
        '''
        convienience function that takes a center and creates 9 square pads centers,
        Pad layout

                1	2	3
                4	5	6
                7	8	9

        :param xc:
        :param yc:
        :param pad_centers_width:
        :return:
        '''
        pad_centers_width = pad_width + pad_width
        pad1 = self.gen_pad(xc - pad_centers_width, yc + pad_centers_width, pad_width, float(self.padFld_1.text()))
        pad2 = self.gen_pad(xc, yc + pad_centers_width, pad_width, float(self.padFld_2.text()))
        pad3 = self.gen_pad(xc + pad_centers_width, yc + pad_centers_width, pad_width, float(self.padFld_3.text()))

        pad4 = self.gen_pad(xc - pad_centers_width, yc, pad_width, float(self.padFld_4.text()))
        pad5 = self.gen_pad(xc, yc, pad_width, float(self.padFld_5.text()))
        pad6 = self.gen_pad(xc + pad_centers_width, yc, pad_width, float(self.padFld_6.text()))

        pad7 = self.gen_pad(xc - pad_centers_width, yc - pad_centers_width, pad_width, float(self.padFld_7.text()))
        pad8 = self.gen_pad(xc, yc - pad_centers_width, pad_width, float(self.padFld_8.text()))
        pad9 = self.gen_pad(xc + pad_centers_width, yc - pad_centers_width, pad_width, float(self.padFld_9.text()))

        pads = [pad1, pad2, pad3, pad4, pad5, pad6, pad7, pad8, pad9]
        return (pads)

    def update_data(self):
        """
        This is a standard function that all scan pluggins have that is called to
        get the data from the pluggins UI widgets and write them into a dict returned by
        get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by
        the scan classes configure() functions

        :returns: None

        """
        # self.update_last_settings()
        # update local widget_com dict
        pad_size = float(self.padSizeFld.text())
        rx = ry = pad_size  # pad_size um pads
        pad_centers_width = rx + ry
        wdg_com = self.update_single_spatial_wdg_com()
        sp_id = list(wdg_com['SPATIAL_ROIS'].keys())[0]

        # get the centers
        xc, yc = (wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_X][CENTER], wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_Y][CENTER])
        absolute_coord_pads = self.get_pattern_pads(xc, yc, rx)
        nx, ny = (
        wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_X][NPOINTS], wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_Y][NPOINTS])
        # create the 9 1.2x1.2 um spatial rois, each with increasing dwells of 12.5, 25, 50, 100, 250, 375, 500, 750, 1000 ms

        # nx = ny = 20  # 20pnts per
        # x_src = self.main_obj.device(DNM_SAMPLE_X).get_name()
        # y_src = self.main_obj.device(DNM_SAMPLE_Y).get_name()

        # get current sample position
        x_posner = self.main_obj.get_sample_positioner('X')
        y_posner = self.main_obj.get_sample_positioner('Y')
        x_pos = x_posner.get_position()
        y_pos = y_posner.get_position()
        x_src = x_posner.get_name()
        y_src = y_posner.get_name()

        # if zoneplate scan, recalc the xc, yc to be relative to 0,0
        if (self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
            xc = xc - x_pos
            yc = yc - y_pos
            pads = self.get_pattern_pads(xc, yc, rx)
            # modify the pad rects to be absolute coords so that the plotter puts them in the correct location
            for (p, ap) in zip(pads, absolute_coord_pads):
                p['rect'] = ap['rect']
        else:
            pads = self.get_pattern_pads(xc, yc, rx)

        sp_rois_dct = {}
        id = 0
        for pad_dct in pads:
            (cx, cy) = pad_dct['centers']
            dwell = pad_dct['dwell']
            rect = pad_dct['rect']
            x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, cx, rx, nx, src=x_src, max_scan_range=MAX_SCAN_RANGE_FINEX)
            y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, cy, ry, ny, src=y_src, max_scan_range=MAX_SCAN_RANGE_FINEY)
            energy_pos = self.main_obj.device(DNM_ENERGY).get_position()
            e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)
            zp_rois = {}

            # if this is a zoneplate scan then copy the x/y rois to the zoneplate rois
            if (self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
                dct_put(zp_rois, SPDB_ZX, x_roi)
                dct_put(zp_rois, SPDB_ZY, y_roi)

            _sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, sp_id=id, zp_rois=zp_rois)
            dct_put(_sp_db, SPDB_RECT, rect)
            dct_put(_sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
            dct_put(_sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, scan_sub_types.POINT_BY_POINT)
            dct_put(_sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
            dct_put(_sp_db, SPDB_HDW_ACCEL_USE, False)
            dct_put(_sp_db, SPDB_SPATIAL_ROIS_CENTER, (xc, yc))
            dct_put(_sp_db, SPDB_SCAN_PLUGIN_SECTION_ID, self.section_id)

            sp_rois_dct[id] = _sp_db
            id += 1

        # wdg_com[SPDB_SPATIAL_ROIS] = sp_rois

        # replace the sp_dbs with the new ones that have been centered at the user specified location
        del (wdg_com[SPDB_SPATIAL_ROIS][sp_id])
        wdg_com[SPDB_SPATIAL_ROIS] = {}
        dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)

        self.roi_changed.emit(wdg_com)
        return (wdg_com)
