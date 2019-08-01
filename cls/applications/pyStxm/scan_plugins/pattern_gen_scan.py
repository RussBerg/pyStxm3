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
from cls.applications.pyStxm.scan_plugins.PatternGenWithE712WavegenScan import PatternGenWithE712WavegenScanClass
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj
from bcm.devices.device_names import *

from cls.data_io.stxm_data_io import STXMDataIo
from cls.data_io.utils import test_eq, check_roi_for_match, get_first_entry_key, get_first_sp_db_from_entry, get_axis_setpoints_from_sp_db

from cls.utils.roi_utils import get_base_roi, get_base_energy_roi, make_spatial_db_dict, widget_com_cmnd_types, on_range_changed, on_center_changed

from cls.scanning.base import ScanParamWidget, zp_focus_modes
from cls.types.stxmTypes import scan_types, scan_sub_types, scan_panel_order, spatial_type_prefix, sample_positioning_modes, sample_fine_positioning_modes

from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef
from cls.plotWidgets.color_def import get_normal_clr, get_warn_clr, get_alarm_clr, get_normal_fill_pattern, get_warn_fill_pattern, get_alarm_fill_pattern

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

		if(not USE_E712_HDW_ACCEL):
			self.name = "Pattern Generator Scan ---- [DISABLED, non hardware acclerated version is currently not supported] "
			self.setEnabled(False)
			self.setToolTip('PatternGeneratorScanParam: Scan plugin is disabled, non hardware acclerated version is currently not supported ')
		else:
			self.positioners = {'ZX': DNM_ZONEPLATE_X, 'ZY': DNM_ZONEPLATE_Y,
								'OX': DNM_OSA_X, 'OY': DNM_OSA_Y, 'OZ': DNM_OSA_Z,
								'GX': DNM_GONI_X, 'GY': DNM_GONI_Y, 'GZ': DNM_GONI_Z, 'GT': DNM_GONI_THETA,
								'SX': DNM_SAMPLE_X, 'SY': DNM_SAMPLE_Y, 'SFX': DNM_SAMPLE_FINE_X,
								'SFY': DNM_SAMPLE_FINE_Y,
								'CX': DNM_COARSE_X, 'CY': DNM_COARSE_Y,
								'POL': DNM_EPU_POLARIZATION, 'OFF': DNM_EPU_OFFSET, 'ANG': DNM_EPU_ANGLE}
			self.scan_class = PatternGenWithE712WavegenScanClass(main_obj=self.main_obj)
			self.sp_db = None
			self.load_from_defaults()
			self.init_sp_db()
			self.connect_paramfield_signals()
			self.on_single_spatial_npoints_changed()
			self.showPatternBtn.clicked.connect(self.on_show_pattern_btn_clicked)



	def init_plugin(self):
		'''
		set the plugin specific details to common attributes
		:return:
		'''
		self.name = "Pattern Generator Scan"
		self.idx = scan_panel_order.PATTERN_GEN_SCAN
		self.type = scan_types.PATTERN_GEN_SCAN
		self.section_id = 'PatternGen'
		self.axis_strings = ['Sample Y microns', 'Sample X microns', '', '']
		self.zp_focus_mode = zp_focus_modes.FL
		self.data_file_pfx = MAIN_OBJ.get_datafile_prefix()
		self.plot_item_type = spatial_type_prefix.ROI
		self._help_html_fpath = os.path.join('interface', 'window_system', 'scan_plugins', 'pattern_generator.html')
		self._help_ttip = 'Pattern Generator documentation and instructions'

	def on_plugin_focus(self):
		'''
        This is a function that is called when the plugin first receives focus from the main GUI
        :return:
        '''
		# make sure that the OSA vertical tracking is off if it is on
		if (self.isEnabled()):
			# ask the plotter to show the pattern

			pass

	def on_plugin_defocus(self):
		'''
        This is a function that is called when the plugin leaves focus from the main GUI
        :return:
        '''
		if (self.isEnabled()):
			# # put the OSA vertical tracking back to its previous state
			# self.main_obj.device(DNM_OSAY_TRACKING).put(self.osay_trcking_was)
			pass

		# call the base class defocus
		#reset the wavetable rate
		self.scan_class.e712_wg.set_forced_rate(1)
		super(PatternGeneratorScanParam, self).on_plugin_defocus()


	def on_show_pattern_btn_clicked(self, chkd):
		#emit a signal that stxmMain is listening for and call show_pattern_generator_pattern in stxmMain
		self.call_main_func.emit('show_pattern_generator_pattern', chkd)

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
		lim_dct['X'] = {'llm':xllm, 'hlm': xhlm, 'rng':rx}
		lim_dct['Y'] = {'llm':yllm, 'hlm': yhlm, 'rng':ry}

		#call standard function to check the fields of the scan param and assign limits
		self.connect_param_flds_to_validator(lim_dct)

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
		self.update_dpo_min_max(dpo, yllm,yhlm)

		# dpo = self.rangeXFld.dpo
		# self.update_dpo_min_max(dpo, rx, rx)
		#
		# dpo = self.rangeYFld.dpo
		# self.update_dpo_min_max(dpo, ry, ry)


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
		warn_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.80) #%80 of max
		alarm_qrect = self.get_percentage_of_qrect(bounding_qrect, 0.95) #%95 of max
				
		bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Range is beyond Sample X/Y Capabilities', get_alarm_fill_pattern())
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
		#rx = float(str(self.rangeXFld.text()))
		rx = 5.0
		cy = float(str(self.centerYFld.text()))
		#ry = float(str(self.rangeYFld.text()))
		ry = 5.0
		dwell = 1.0
		nx = int(str(self.npointsXFld.text())) 
		ny = int(str(self.npointsYFld.text())) 
		sx = float(str(self.stepXFld.text()))
		sy = float(str(self.stepYFld.text()))
		#now create the model that this pluggin will use to record its params
		x_src = self.main_obj.device(DNM_SAMPLE_X).get_name()
		y_src = self.main_obj.device(DNM_SAMPLE_Y).get_name()

		x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, cx, rx, nx, sx, src=x_src)
		y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, cy, ry, ny, sy, src=y_src)

		energy_pos = MAIN_OBJ.device(DNM_ENERGY).get_position()
		e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False )

		self.sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi)

	def check_scan_limits(self):
		''' a function to be implemented by the scan pluggin that
		checks the scan parameters against the soft limits of the 
		positioners, if all is well return true else false
		
		This function should provide an explicit error log msg to aide the user
		'''
		#ret = self.check_center_range_xy_scan_limits(DNM_SAMPLE_X, DNM_SAMPLE_Y)
		ret = True
		return(ret)
	
	# def on_set_center(self):
	#
	# 	mtr_x = MAIN_OBJ.device(DNM_SAMPLE_X)
	# 	mtr_y = MAIN_OBJ.device(DNM_SAMPLE_Y)
	#
	# 	centX = float(str(self.centerXFld.text()))
	# 	centY = float(str(self.centerYFld.text()))
	#
	# 	#DRBV + CENTX
	# 	#pcalX = mtrx.get('calibPosn')
	# 	#pcalY = mtry.get('calibPosn')
	#
	# 	#mtrx.set_calibrated_position(centX + pcalX)
	# 	#mtry.set_calibrated_position(centY + pcalY)
	#
	# 	self.sp_db[SPDB_X][CENTER] = 0.0
	# 	on_center_changed(self.sp_db[SPDB_X])
	# 	self.sp_db[SPDB_Y][CENTER] = 0.0
	# 	on_center_changed(self.sp_db[SPDB_Y])
	#
	# 	mtr_x.move(centX)
	# 	mtr_y.move(centY)
	#
	# 	mtr_x.wait_for_stopped_and_zero()
	# 	mtr_y.wait_for_stopped_and_zero()
	#
	# 	roi = {}
	# 	roi[CENTER] = (0.0, 0.0, 0.0, 0.0)
	# 	roi[RANGE] = (None, None, None, None)
	# 	roi[NPOINTS] = (None, None, None, None)
	# 	roi[STEP] = (None, None, None, None)
	# 	self.set_roi(roi)
	#
	# 	DEFAULTS.set('PRESETS.DETECTOR.CALIBPOSN', (centX, centY))
	# 	DEFAULTS.set('PRESETS.DETECTOR.CENTER', (0.0, 0.0))
	# 	DEFAULTS.update()
	#
	# 	self.upd_timer.start(250)

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
		

		self.set_parm(self.centerXFld, cx)
		self.set_parm(self.centerYFld, cy)
		
		# if(rx != None):
		# 	self.set_parm(self.rangeXFld, rx)
		# if(ry != None):
		# 	self.set_parm(self.rangeYFld, ry)

		if(nx != None):
			self.set_parm(self.npointsXFld, nx, type='int', floor=2)
			
		if(ny != None):
			self.set_parm(self.npointsYFld, ny, type='int', floor=2)
		
		if(sx != None):
			self.set_parm(self.stepXFld, sx, type='float', floor=0)
			
		if(sy != None):
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
		if(sp_db[CMND] == widget_com_cmnd_types.DEL_ROI):
			return
		
		if(sp_db[CMND] == widget_com_cmnd_types.LOAD_SCAN):
			self.sp_db = sp_db
		else:
			if(sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
				#dct_put(self.sp_db, SPDB_SCAN_PLUGIN_ITEM_ID, dct_get(sp_db, SPDB_PLOT_ITEM_ID))
				dct_put(self.sp_db, SPDB_ID_VAL, dct_get(sp_db, SPDB_PLOT_ITEM_ID))
				 	
			self.sp_db[SPDB_X][CENTER] = sp_db[SPDB_X][CENTER]

			if(sp_db[SPDB_X][RANGE] != 0):
				self.sp_db[SPDB_X][RANGE] = sp_db[SPDB_X][RANGE]

			self.sp_db[SPDB_Y][CENTER] = sp_db[SPDB_Y][CENTER]

			if(sp_db[SPDB_Y][RANGE] != 0):
				self.sp_db[SPDB_Y][RANGE] = sp_db[SPDB_Y][RANGE]

		x_roi = self.sp_db[SPDB_X]
		y_roi = self.sp_db[SPDB_Y]
		e_rois = self.sp_db[SPDB_EV_ROIS]

		#if do_recalc then it is because mod_roi() has been called by a signal that the
		#plotWidgetter has resized/moved the ROI, the recalc of x/y when the number of points
		#is changed is handled above in the signal for the npointsFld
		if(do_recalc):
			on_range_changed(x_roi)
			on_range_changed(y_roi)

		self.set_parm(self.centerXFld, x_roi[CENTER])
		self.set_parm(self.centerYFld, y_roi[CENTER])
		
		# if(x_roi[RANGE] != None):
		# 	self.set_parm(self.rangeXFld, x_roi[RANGE])
		# if(y_roi[RANGE] != None):
		# 	self.set_parm(self.rangeYFld, y_roi[RANGE])

		if(x_roi[NPOINTS] != None):
			self.set_parm(self.npointsXFld, x_roi[NPOINTS], type='int', floor=2)
			
		if(y_roi[NPOINTS] != None):
			self.set_parm(self.npointsYFld, y_roi[NPOINTS], type='int', floor=2)
			
		if(x_roi[STEP] != None):
			self.set_parm(self.stepXFld, x_roi[STEP], type='float', floor=0)
		
		if(y_roi[STEP] != None):
			self.set_parm(self.stepYFld, y_roi[STEP], type='float', floor=0)
		
		# if(sp_db[CMND] == widget_com_cmnd_types.SELECT_ROI):
		# 	self.update_last_settings()



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
		pad = {'centers':(xc, yc), 'dwell': dwell, 'rect': rect}
		return(pad)


	def get_pattern_pads(self, xc, yc, pad_width):
		'''
		convienience function that takes a center and creates 9 square pads centers,
		:param xc:
		:param yc:
		:param pad_centers_width:
		:return:
		'''
		pad_centers_width = pad_width + pad_width
		pad1 = self.gen_pad(xc - pad_centers_width, yc + pad_centers_width, pad_width, 12.5)
		pad2 = self.gen_pad(xc, yc + pad_centers_width, pad_width, 25.0)
		pad3 = self.gen_pad(xc + pad_centers_width, yc + pad_centers_width, pad_width, 50.0)

		pad4 = self.gen_pad(xc - pad_centers_width, yc, pad_width, 100.0)
		pad5 = self.gen_pad(xc, yc, pad_centers_width, 250.0)
		pad6 = self.gen_pad(xc + pad_centers_width, yc, pad_width, 375.0)

		pad7 = self.gen_pad(xc - pad_centers_width, yc - pad_centers_width, pad_width, 500.0)
		pad8 = self.gen_pad(xc, yc - pad_centers_width, pad_width, 750.0)
		pad9 = self.gen_pad(xc + pad_centers_width, yc - pad_centers_width, pad_width, 1000.0)

		pads = [pad1, pad2, pad3, pad4, pad5, pad6, pad7, pad8, pad9]
		return(pads)

	def update_data(self):
		"""
		This is a standard function that all scan pluggins have that is called to 
		get the data from the pluggins UI widgets and write them into a dict returned by 
		get_base_scanparam_roi(), this dict is emitted by all scan pluggins to be used by 
		the scan classes configure() functions
	
		:returns: None
	 
		"""
		#update local widget_com dict
		rx = ry = 1.2  # 1.2 um pads
		pad_centers_width = rx + ry
		wdg_com = self.update_single_spatial_wdg_com()
		sp_id = list(wdg_com['SPATIAL_ROIS'].keys())[0]

		#get the centers
		xc, yc = (wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_X][CENTER], wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_Y][CENTER])
		absolute_coord_pads = self.get_pattern_pads(xc, yc, rx)
		nx, ny = (wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_X][NPOINTS], wdg_com[SPDB_SPATIAL_ROIS][sp_id][SPDB_Y][NPOINTS])
		#create the 9 1.2x1.2 um spatial rois, each with increasing dwells of 12.5, 25, 50, 100, 250, 375, 500, 750, 1000 ms

		#nx = ny = 20  # 20pnts per
		# x_src = self.main_obj.device(DNM_SAMPLE_X).get_name()
		# y_src = self.main_obj.device(DNM_SAMPLE_Y).get_name()

		#get current sample position
		x_posner = self.main_obj.get_sample_positioner('X')
		y_posner = self.main_obj.get_sample_positioner('Y')
		x_pos = x_posner.get_position()
		y_pos = y_posner.get_position()
		x_src = x_posner.get_name()
		y_src = y_posner.get_name()

		#if zoneplate scan, recalc the xc, yc to be relative to 0,0
		if (self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
			xc = xc - x_pos
			yc = yc - y_pos
			pads = self.get_pattern_pads(xc, yc, rx)
			#modify the pad rects to be absolute coords so that the plotter puts them in the correct location
			for (p, ap) in zip(pads, absolute_coord_pads):
				p['rect'] = ap['rect']
		else:
			pads = self.get_pattern_pads(xc, yc, rx)



		# # dwells in order from btm left to top right
		# # dwells = [500, 750, 1000, 100, 250, 375, 12.5, 25, 50.0]
		# # pads in order from top left to btm right, ((xc, yc), dwell)
		# pad1 = ((xc - pad_centers_width, yc + pad_centers_width), 12.5)
		# pad2 = ((xc, yc + pad_centers_width), 25.0)
		# pad3 = ((xc + pad_centers_width, yc + pad_centers_width), 50.0)
		#
		# pad4 = ((xc - pad_centers_width, yc), 100.0)
		# pad5 = ((xc, yc), 250.0)
		# pad6 = ((xc + pad_centers_width, yc), 375.0)
		#
		# pad7 = ((xc - pad_centers_width, yc - pad_centers_width ), 500.0)
		# pad8 = ((xc, yc - pad_centers_width), 750.0)
		# pad9 = ((xc + pad_centers_width, yc - pad_centers_width), 1000.0)
		#
		# pads = [pad1, pad2, pad3, pad4, pad5, pad6, pad7, pad8, pad9]

		sp_rois_dct = {}
		id = 0
		for pad_dct in pads:
			(cx, cy) = pad_dct['centers']
			dwell = pad_dct['dwell']
			rect = pad_dct['rect']
			x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, cx, rx, nx, src=x_src, max_scan_range=MAX_SCAN_RANGE_FINEX)
			y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, cy, ry, ny, src=y_src, max_scan_range=MAX_SCAN_RANGE_FINEY)
			energy_pos = MAIN_OBJ.device(DNM_ENERGY).get_position()
			e_roi = get_base_energy_roi(SPDB_EV, DNM_ENERGY, energy_pos, energy_pos, 0, 1, dwell, None, enable=False)
			# if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
			# 	zp_rois = {}
			# 	dct_put(zp_rois, SPDB_ZX, x_roi)
			# 	dct_put(zp_rois, SPDB_ZY, y_roi)
			# 	_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, zp_rois=zp_rois, e_roi=e_roi, sp_id=id)
			# 	#_sp_db = self.modify_sp_db_for_goni(_sp_db)
			# else:
			# 	_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, sp_id=id)
			#
			zp_rois = {}

			#if this is a zoneplate scan then copy the x/y rois to the zoneplate rois
			if (self.sample_fine_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
				dct_put(zp_rois, SPDB_ZX, x_roi)
				dct_put(zp_rois, SPDB_ZY, y_roi)

			_sp_db = make_spatial_db_dict(x_roi=x_roi, y_roi=y_roi, e_roi=e_roi, sp_id=id, zp_rois=zp_rois)
			dct_put(_sp_db, SPDB_RECT, rect)
			dct_put(_sp_db, SPDB_SCAN_PLUGIN_TYPE, self.type)
			dct_put(_sp_db, SPDB_SCAN_PLUGIN_SUBTYPE, scan_sub_types.POINT_BY_POINT)
			dct_put(_sp_db, SPDB_PLOT_SHAPE_TYPE, self.plot_item_type)
			dct_put(_sp_db, SPDB_HDW_ACCEL_USE, False)

			sp_rois_dct[id] = _sp_db
			id += 1

		#wdg_com[SPDB_SPATIAL_ROIS] = sp_rois
		del (wdg_com[SPDB_SPATIAL_ROIS][sp_id])
		wdg_com[SPDB_SPATIAL_ROIS] = {}
		dct_put(wdg_com, SPDB_SPATIAL_ROIS, sp_rois_dct)

		self.roi_changed.emit(wdg_com)
		return(wdg_com)

	
	