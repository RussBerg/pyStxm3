'''
Created on Aug 25, 2014

@author: bergr
'''
import math

import numpy as np

from bcm.devices.device_names import *
from cls.types.stxmTypes import energy_scan_order_types
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.enum_utils import Enum
from cls.utils.roi_dict_defs import *
from cls.utils.time_utils import make_timestamp_now

#BASE_EV = 395.0
BASE_EV = 1100.0 #pick a value that places the zoneplate Z a safe distance from the OSA and Sample for most Zoneplates
BASE_NPOINTS = 50
MIN_STEP_SIZE = 0.001
MAX_NPOINTS = 100000

unum = None
uid_list = []

def reset_unique_roi_id():
	"""
	This function is used as a common way to get unique ids that are assigned to the scan pluggin and plotter
	Regions of Interest
	"""
	global unum, uid_list
	#unum = 0
	unum = None
	#print 'reset_unique_roi_id()'
	uid_list = []

def get_current_unique_id():
	global uid_list
	if(len(uid_list) is 0):
		id = get_unique_roi_id()
	else:
		#id = uid_list[-1]
		id = unum
	#print 'get_current_unique_id=>%d' % id
	return(id)

def is_unique_roi_id_in_list(id):
	global uid_list
	if(id in uid_list):
		return(True)
	else:
		return(False)

def add_to_unique_roi_id_list(id):
	global unum, uid_list
	uid_list.append(id)
	#ensure no duplicates
	uid_list = list(set(uid_list))
	unum = id
	#print 'add_to_unique_roi_id_list(%d)' % id
	#print uid_list

def set_current_unique_id(id):
	global unum, uid_list
	if(id in uid_list):
		unum = id


def delete_unique_id(id):
	global unum, uid_list
	if(id in uid_list):
		if(unum ==  id):
			unum = None
		del(uid_list[id])

def get_unique_roi_id():
	"""
	This function is used as a common way to get unique ids that are assigned to the scan pluggin and plotter
	Regions of Interest
	"""
	global unum, uid_list
	#return(int(round(time.time() * 1000)))
	#unum += 1
	if(len(uid_list) == 0):
		add_to_unique_roi_id_list(0)
		return(0)
	ids = list(set(sorted(uid_list)))
	new_uid = ids[-1] + 1
	add_to_unique_roi_id_list(new_uid)
	return(new_uid)
	
	#return(unum)


def get_next_model_id(self):
        #m_keys = sorted(self.models.keys())
        #return(m_keys[-1] + 1)
        id_lst = []
        for scan in self.tablemodel.scanListData:
            id_lst.append(scan[SPDB_ID_VAL])
        ids = sorted(id_lst)
        return(ids[-1] + 1)

def decide_scan_resolution(rnge, max_range):
	if(max_range == None):
		return(COARSE)
	if(rnge > max_range):
		return(COARSE)
	else:
		return(FINE)

def get_base_roi(name, positionerName, center, rng, npoints, stepSize=None, max_scan_range=None, enable=True, is_point=False, src=None):
	""" define a base Region of Interest def that is passed around
	'center':
	'range':
	'npoints':
	'stepSize':
	"""
	roi_def = {}
	roi_def[NAME] = name
	roi_def[ID] = BASE_ROI
	roi_def[ID_VAL] = -1	
	roi_def[CENTER] = center
	roi_def[RANGE] = rng
	roi_def[NPOINTS] = int(npoints)
	roi_def[ENABLED] = enable
	roi_def[IS_POINT] = is_point
	#the following specifies an offset to the START and STOP values
	#allowing the user to apply a correction if need be, this was added
	#for zoneplate scanning where the Goniometer will need to be corrected as the
	#sample rotates to account for mechanical misalignment
	roi_def[OFFSET] = 0.0
	
	
	if(rng == None):
		roi_def[ROI_STEP] = None
		roi_def[START] = center
		roi_def[STOP] = center
	elif(rng == 0.0):
		roi_def[ROI_STEP] = 0
		roi_def[START] = center
		roi_def[STOP] = center
	else:
		roi_def[ROI_STEP] = rng/npoints
		roi_def[START] = center - (.5 * rng)
		roi_def[STOP] = center + (.5 * rng)

	if((roi_def[START] is not None) and (roi_def[STOP] is not None)):
		#make sure always left to right is less to more
		if(roi_def[START] > roi_def[STOP]):
			t = roi_def[STOP]
			roi_def[STOP] = roi_def[START]
			roi_def[START] = t

		determine_setpoints(roi_def, stepSize)
	
	roi_def[POSITIONER] = positionerName
	roi_def[SRC] = src
	roi_def[TOP_LEVEL] = False
	roi_def[DATA_LEVEL] = False
	if((rng or max_scan_range) is None):
		#skip
		roi_def[SCAN_RES] = None
	else:
		roi_def[SCAN_RES] =  decide_scan_resolution(rng, max_scan_range)
	
	return(roi_def)

def determine_setpoints(roi_def, stepSize=None):
	if(roi_def[NPOINTS] == 1):
		roi_def[SETPOINTS] = np.linspace(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET], roi_def[NPOINTS], endpoint=True, retstep=False)
		roi_def[ROI_STEP] = 0.0
	elif((roi_def[RANGE] == 0) and ( not roi_def[IS_POINT])):
		roi_def[SETPOINTS] = np.linspace(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET], roi_def[NPOINTS], endpoint=True, retstep=False)
		
	elif((roi_def[START] == None) or (roi_def[NPOINTS] == 0)):
		roi_def[SETPOINTS] = []
	else:
		if(stepSize):
			#NOTE this produces NPOINTS + 1 points 
			#use arange
			roi_def[ROI_STEP] = stepSize
			roi_def[SETPOINTS] = np.arange(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET] + stepSize, stepSize)
		else:	
			roi_def[SETPOINTS], roi_def[ROI_STEP] = np.linspace(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET], roi_def[NPOINTS], endpoint=True, retstep=True)


def get_base_start_stop_roi(name, positionerName, start, stop, npoints, stepSize=None, max_scan_range=111, enable=True, is_point=False, src=None):
	""" define a base Region of Interest def that is passed around
	'center':
	'range':
	'npoints':
	'stepSize':
	"""
	#ensure left to right is small to larger
	if(start > stop):
		t = stop
		stop = start
		start = t
		
	roi_def = {}
	roi_def[NAME] = name
	roi_def[ID] = BASE_START_STOP_ROI
	roi_def[ID_VAL] = -1
	roi_def[CENTER] = (start + stop) * 0.5
	roi_def[RANGE] = (stop - start)
	roi_def[NPOINTS] = int(npoints)
	roi_def[ENABLED] = enable
	roi_def[IS_POINT] = is_point
	#the following specifies an offset to the START and STOP values
	#allowing the user to apply a correction if need be, this was added
	#for zoneplate scanning where the Goniometer will need to be corrected as the
	#sample rotates to account for mechanical misalignment
	roi_def[OFFSET] = 0.0
	
	if((roi_def[RANGE] == 0.0) or (not enable)):
		roi_def[ROI_STEP] = 0
		roi_def[START] = start
		roi_def[STOP] = start
	else:
		roi_def[ROI_STEP] = roi_def[RANGE]/npoints
		roi_def[START] = start
		roi_def[STOP] = stop
	
	determine_setpoints(roi_def, stepSize)
	
	roi_def[POSITIONER] = positionerName
	roi_def[SRC] = src
	roi_def[TOP_LEVEL] = False
	roi_def[DATA_LEVEL] = False
	roi_def[SCAN_RES] =  decide_scan_resolution(roi_def[RANGE], max_scan_range)

	#added to support E712 waveform generator
	roi_def[SPDB_HDW_ACCEL_USE] = False
	roi_def[SPDB_HDW_ACCEL_AUTO_DDL] = True
	roi_def[SPDB_HDW_ACCEL_REINIT_DDL] = False
		
	return(roi_def)

#some ROI convienience functions that are useful when updating the scan params in a tableview widget
def on_start_changed(roi):
	check_if_single_point(roi, True)
	recalc_range(roi)
	recalc_step_size(roi)
	recalc_center(roi)
	recalc_setpoints(roi)

def on_stepsize_changed_with_fixed_step(roi, step):
	roi[START] = roi[START] + step
	recalc_npoints(roi)
	check_if_single_point(roi, True)
	recalc_range(roi)
	#recalc_step_size(roi)
	recalc_center(roi)
	recalc_setpoints(roi)

def on_stop_changed(roi):
	check_if_single_point(roi, False)
	recalc_range(roi)
	recalc_step_size(roi)
	recalc_center(roi)
	recalc_setpoints(roi)

def on_range_changed(roi):
	recalc_stop(roi)
	recalc_step_size(roi)
	recalc_center(roi)
	recalc_setpoints(roi)

def on_npoints_changed(roi):
	check_if_single_point(roi, True)
	recalc_step_size(roi)
	recalc_setpoints(roi)

def on_step_size_changed(roi):
	recalc_npoints(roi)
	recalc_setpoints(roi)

def on_centerxy_changed(roi):
	on_center_changed(roi)
	recalc_setpoints(roi)


def check_if_single_point(roi, start=True):
	'''
	check if roi is a single point, if yes then:
		if start is True
			that means that the user has just changed start so make stop match start
		else:
			do the opposite
	:param roi:
	:param start:
	:return:
	'''
	if(roi[NPOINTS] == 1):
		if(start):
			roi[STOP] = roi[START]
		else:
			roi[START] = roi[STOP]
		roi[RANGE] = 0.0


def recalc_center(roi):
	if(roi[IS_POINT]):
		roi[CENTER] = roi[START]
		roi[STOP] = roi[START]
		
	else:	
		roi[CENTER] = float(roi[START] + roi[STOP]) * 0.5
	
def recalc_npoints(roi):
	'''
	recalc the number of points but make sure that the values stay within 
	the MIN_STEP_SIZE and MAX_NPOINTS
	'''
	if(roi[IS_POINT]):
		roi[NPOINTS] = int(1)
	else:
		if(roi[ROI_STEP] < MIN_STEP_SIZE):
			roi[ROI_STEP] = MIN_STEP_SIZE

		if(roi[RANGE] is None):
			return
		if (roi[ROI_STEP] is None):
			return
		#make sure npts rounds up if .1 or higher
		npts = int( math.ceil(roi[RANGE]/roi[ROI_STEP]))
		if(npts < 1):
			roi[NPOINTS] = int(1)
			recalc_step_size(roi)
		elif(npts > MAX_NPOINTS):
			roi[NPOINTS] = int(MAX_NPOINTS)
		else:	
			roi[NPOINTS] = int(npts)

def recalc_step_size(roi):
	if(roi[IS_POINT]):
		roi[ROI_STEP] = 0.0
		
	else:
		if(roi[NPOINTS] == 0):
			roi[NPOINTS] = int(1)
		if(roi[NPOINTS] > 1):	
			#reduce the NPOINTS by 1 so that the stepsize will be correct for including the STOP value
			#step = float(roi[RANGE]/float(roi[NPOINTS] - 1))
			step = float(roi[RANGE] / float(roi[NPOINTS]))
			if(step < MIN_STEP_SIZE):
				roi[ROI_STEP] = MIN_STEP_SIZE	
			else:	
				#reduce the NPOINTS by 1 so that the stepsize will be correct for including the STOP value
				#roi[ROI_STEP] = float(roi[RANGE]/float(roi[NPOINTS] - 1))
				roi[ROI_STEP] = float(roi[RANGE] / float(roi[NPOINTS]))
		else:
			step = float(roi[RANGE]/float(roi[NPOINTS]))
	
def recalc_range(roi):
	if(roi[IS_POINT]):
		roi[RANGE] = 0.0
	
	elif(roi[STOP] < roi[START]):
		if(roi[ID] == EV_ROI):
			roi[STOP] = roi[START] + roi[RANGE]
		else:	
			roi[RANGE] = float(roi[START]) - float(roi[STOP])
		#roi[STOP] = roi[START] + roi[RANGE]
	#elif(roi[STOP] == roi[START]):
	#	roi[STOP] = float(roi[START]) + float(roi[RANGE])
	else:
		roi[RANGE] = float(roi[STOP]) - float(roi[START])
	recalc_setpoints(roi)	


def recalc_stop(roi):
	if(roi[IS_POINT]):
		roi[STOP] = roi[CENTER]
		roi[START] = roi[CENTER]
		 
	else:#if(roi[START] == None):
		roi[START] = roi[CENTER] - (0.5 * roi[RANGE])
		roi[STOP] = roi[CENTER] + (0.5 * roi[RANGE])

def recalc_setpoints(roi):
	if(roi[START] == None):
		recalc_stop(roi)
	#roi[SETPOINTS] = np.linspace(roi[START], roi[STOP], roi[NPOINTS])
	#roi[SETPOINTS] = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=False)
	if(roi[NPOINTS] == 1):
		roi[ROI_STEP] = roi[STOP] - roi[START]
		if(roi[ROI_STEP] != 0.0):
			roi[SETPOINTS], STEP = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=True, retstep=True)
		else:
			roi[SETPOINTS] = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=True, retstep=False)
	else:	
		#roi[SETPOINTS], roi[ROI_STEP] = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=True, retstep=True)
		#roi[SETPOINTS], STEP = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=True, retstep=True)
		roi[SETPOINTS], roi[ROI_STEP] = np.linspace(roi[START], roi[STOP], roi[NPOINTS], endpoint=True, retstep=True)
	roi['RECT'] = (roi[START], roi[STOP] - roi[RANGE], roi[STOP], roi[START] + roi[RANGE])
	
def on_center_changed(roi):
	roi[START] = roi[CENTER] - (0.5 * roi[RANGE])
	roi[STOP] = roi[CENTER] + (0.5 * roi[RANGE])
	recalc_setpoints(roi)
		
def roi_error():
	print('Error: dct not of type BASE_ROI')
	return(None)

def get_center(base_roi_dct):
	if(base_roi_dct[ID] == BASE_ROI):
		return(base_roi_dct[CENTER])
	else:
		return(roi_error())

def get_range(base_roi_dct):
	if(base_roi_dct[ID] == BASE_ROI):
		return(base_roi_dct[RANGE])
	else:
		return(roi_error())

def get_npoints(base_roi_dct):
	if(base_roi_dct[ID] == BASE_ROI):
		return(base_roi_dct[NPOINTS])
	else:
		return(roi_error())	

def get_stepsize(base_roi_dct):
	if(base_roi_dct[ID] == BASE_ROI):
		return(base_roi_dct[ROI_STEP])
	else:
		return(roi_error())	
	
def get_positioner(base_roi_dct):
	if(base_roi_dct[ID] == BASE_ROI):
		return(base_roi_dct[POSITIONER])
	else:
		return(roi_error())	


def get_epu_pol_dct(pol, offset, angle=0.0):
	""" define a base Region of Interest def that is passed around
	The parameters passed are base_roi dicts
		pol: 	one of, circ left, circ right, linear
		offset: is a list with npoint number of offset values for the
		angle:  if pol==linear, this is the angle used, else it is 0.0 (meaningless)
	
	"""
	roi_def = {}
	roi_def[NAME] = ''
	roi_def[ID] = EPU_POL
	roi_def[ID_VAL] = -1
	roi_def[POL] = int(pol)
	roi_def[POL_POSITIONER] = DNM_EPU_POLARIZATION
	roi_def[OFF] = offset
	roi_def[OFF_POSITIONER] = DNM_EPU_OFFSET
	roi_def[ANGLE] = angle
	return(roi_def)


#def new_get_base_energy_roi(name, positionerName, start, stop, rng, npoints, dwell, pol_roi, off_roi, stepSize=None, enable=False):
def get_base_energy_roi(name, positionerName, start, stop, rng, npoints, dwell, pol_rois=None, stepSize=None, enable=False, energy_scan_order=energy_scan_order_types.EV_THEN_POL):
	""" define a base Region of Interest def that is passed around
	'EV''start':
	'EV''stop':
	'EV''range':
	'EV''npoints':
	'EV''stepSize':
	'dwell'
	pol_rois: is a list of polarity dicts
	"""
	roi_def = get_base_start_stop_roi(name, positionerName, start, stop, npoints, stepSize)
	roi_def[ID] = EV_ROI
	roi_def[ID_VAL] = -1
	roi_def[SCAN_IDX] = None
	#roi_def['EV_IDX'] = None
# 	roi_def[SCAN_RES] =  None
	#roi_def[NPOINTS] =  npoints
	#keep a copy of original start to be used when computing the start of an adjacent ev roi for a multi ev scan
	roi_def[EV_BOUNDARY_ROI_START] = roi_def[START]
	if(pol_rois == None):
		pol_rois = [get_epu_pol_dct(-1, 0.0, angle=0.0)]
	#roi_def[POL_ID] = pol_rois
	roi_def[POL_ID] = len(pol_rois)
	roi_def[POL_ROIS] = pol_rois
	roi_def[XMCD_EN] = False
	roi_def[EV_POL_ORDER] = energy_scan_order
	roi_def[DWELL] = dwell
	roi_def[ENABLED] = enable
	roi_def[TOP_LEVEL] = False
	roi_def[DATA_LEVEL] = False
	
	roi_def[EPU_POL_PNTS] = []
	roi_def[EPU_OFF_PNTS] = []
	roi_def[EPU_ANG_PNTS] = []
	
	for pol_roi in pol_rois:
		roi_def[EPU_POL_PNTS].append(pol_roi[POL])
		roi_def[EPU_OFF_PNTS].append(pol_roi[OFF])
		roi_def[EPU_ANG_PNTS].append(pol_roi[ANGLE])
	
	return(roi_def)

def ensure_left_to_right(roi_def):
	if((roi_def[START] is not None) and (roi_def[STOP] is not None)):
		if(roi_def[START] > roi_def[STOP]):
			t = roi_def[STOP]
			roi_def[STOP] = roi_def[START]
			roi_def[START] = t
			
widget_com_cmnd_types = Enum('ROI_CHANGED','LOAD_SCAN','ADD_ROI','DEL_ROI','SELECT_ROI', 'DESELECT_ROI')
"""
	ROI_CHANGED:	a plot or table is sending the msg that a roi has moved/resized
	LOAD_SCAN:			the scan params contained within should be loaded by the receiver
	ADD_ROI:			the scan params contained within should be added by the receiver
	DEL_ROI:			the scan params contained within should be deleted by the receiver
	SELECT_ROI:			the item id contained within has been selected on, do not change any parms
"""
def make_spatial_db_dict(x_roi=None, y_roi=None, z_roi=None, e_roi=None, goni_rois={}, osa_rois={}, zp_rois={},sp_id=None):
	"""
	A standard dict that is used to store an instance of all info required to scan and record a spatial region
	
	One issue is that the parameters may require a recalculation such as the range changed (requiring recalc of stepsize etc)
	The goal is that the parameters will be recalculated BEFORE this dict is emitted, that way the widget that receives this 
	dict can assume all the values are as they should be. This may be difficult with the MultiRegionWidget because the "model" can 
	be changed:
	"""
	dct = {}
	dct_put(dct, 'ID', SPATIAL_DB_DICT)	#the id of this dict type

	gx_roi = None
	gy_roi = None
	gz_roi = None
	gt_roi = None
	
	ox_roi = None
	oy_roi = None
	oz_roi = None
	
	zpx_roi = None
	zpy_roi = None
	zpz_roi = None
	
	
	dct_put(dct, WDGCOM_CMND, None)	#The caller sets this field to a widget_com_cmnd_type
	
	if(x_roi == None):
		x_roi = get_base_roi(SPDB_X, DNM_SAMPLE_X, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=True)
	
	if(y_roi == None):
		y_roi = get_base_roi(SPDB_Y, DNM_SAMPLE_Y, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=True)
	
	if(z_roi == None):
		z_roi = get_base_roi(SPDB_Z, DNM_ZONEPLATE_Z, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=True)
	
	if(e_roi == None):
		pol_rois = get_epu_pol_dct(-1, 0.0, angle=0.0)
		e_rois = [get_base_energy_roi(SPDB_EV, DNM_ENERGY, BASE_EV, BASE_EV, 0, BASE_NPOINTS, 1.0, [pol_rois], stepSize=None, enable=False)]
	else:
		e_rois = [e_roi]

	if(goni_rois):
		if(SPDB_GX in list(goni_rois.keys())):
			gx_roi = goni_rois[SPDB_GX]
		else:
			gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)
		if(SPDB_GY in list(goni_rois.keys())):
			gy_roi = goni_rois[SPDB_GY]
		else:
			gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)
		if(SPDB_GZ in list(goni_rois.keys())):
			gz_roi = goni_rois[SPDB_GZ]
		else:
			gz_roi = get_base_roi(SPDB_GZ, DNM_GONI_Z, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)
		if(SPDB_GT in list(goni_rois.keys())):
			gt_roi = goni_rois[SPDB_GT]
		else:
			gt_roi = get_base_roi(SPDB_GT, DNM_GONI_THETA, None, None, 0, stepSize=None, max_scan_range=None,
								  enable=False)

		if (SPDB_G_ZPZ_ADJUST in list(goni_rois.keys())):
			g_zpz_adjust_roi = goni_rois[SPDB_G_ZPZ_ADJUST]
		else:
			g_zpz_adjust_roi = get_base_roi(SPDB_G_ZPZ_ADJUST, '', None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)
			
	else:	
		gx_roi = get_base_roi(SPDB_GX, DNM_GONI_X, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
		gy_roi = get_base_roi(SPDB_GY, DNM_GONI_Y, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
		gz_roi = get_base_roi(SPDB_GZ, DNM_GONI_Z, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
		gt_roi = get_base_roi(SPDB_GT, DNM_GONI_THETA, None, None, 0, stepSize=None, max_scan_range=None, enable=False)
		g_zpz_adjust_roi = get_base_roi(SPDB_G_ZPZ_ADJUST, '', None, None, 0, stepSize=None, max_scan_range=None, enable=False)
	
	if(osa_rois):
		if(SPDB_OX in list(osa_rois.keys())):
			ox_roi = dct_get(osa_rois, SPDB_OX)
		else:
			ox_roi = get_base_roi(SPDB_OX, DNM_OSA_X, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)
		if(SPDB_OY in list(osa_rois.keys())):
			oy_roi = dct_get(osa_rois, SPDB_OY)
		else:
			oy_roi = get_base_roi(SPDB_OY, DNM_OSA_Y, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)

		if(SPDB_OZ in list(osa_rois.keys())):
			oz_roi = dct_get(osa_rois, SPDB_OZ)
		else:
			oz_roi = get_base_roi(SPDB_OZ, DNM_OSA_Z, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None,
								  enable=False)


	else:
		ox_roi = get_base_roi(SPDB_OX, DNM_OSA_X, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
		oy_roi = get_base_roi(SPDB_OY, DNM_OSA_Y, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
		oz_roi = get_base_roi(SPDB_OZ, DNM_OSA_Z, None, None, BASE_NPOINTS, stepSize=None, max_scan_range=None, enable=False)
	
	
	if(zp_rois):
		zp_rois_keys = list(zp_rois[SPDB_ZP].keys())
		if(SPDB_X in zp_rois_keys):
			zpx_roi = dct_get(zp_rois, SPDB_ZX)
		else:
			zpx_roi = get_base_roi(SPDB_ZX, DNM_ZONEPLATE_X, None, None, 0, stepSize=None,
								   max_scan_range=None, enable=False)

		if(SPDB_Y in zp_rois_keys):
			zpy_roi = dct_get(zp_rois, SPDB_ZY)
		else:
			zpy_roi = get_base_roi(SPDB_GY, DNM_ZONEPLATE_Y, None, None, 0, stepSize=None,
								   max_scan_range=None, enable=False)

		if(SPDB_Z in zp_rois_keys):
			zpz_roi = dct_get(zp_rois, SPDB_ZZ)
		else:
			zpz_roi = get_base_roi(SPDB_GZ, DNM_ZONEPLATE_Z, None, None, 0, stepSize=None,
								   max_scan_range=None, enable=False)
				
	else:	
		zpx_roi = get_base_roi(SPDB_ZX, DNM_ZONEPLATE_X, None, None, 0, stepSize=None, max_scan_range=None, enable=False)
		zpy_roi = get_base_roi(SPDB_GY, DNM_ZONEPLATE_Y, None, None, 0, stepSize=None, max_scan_range=None, enable=False)
		zpz_roi = get_base_roi(SPDB_GZ, DNM_ZONEPLATE_Z, None, None, 0, stepSize=None, max_scan_range=None, enable=False)
			
	dct_put(dct, 'ID_VAL', sp_id)
	
	ensure_left_to_right(x_roi)
	ensure_left_to_right(y_roi)
	
	#single spatial, used for the scans: Det, Osa, Osa Focus, Focus
	dct_put(dct, SPDB_X, x_roi)
	dct_put(dct, SPDB_Y, y_roi)
	dct_put(dct, SPDB_Z, z_roi)
	
	dct_put(dct, SPDB_GX, gx_roi)
	dct_put(dct, SPDB_GY, gy_roi)
	dct_put(dct, SPDB_GZ, gz_roi)
	dct_put(dct, SPDB_GT, gt_roi)
	dct_put(dct, SPDB_G_ZPZ_ADJUST, g_zpz_adjust_roi)
	
	dct_put(dct, SPDB_OX, ox_roi)
	dct_put(dct, SPDB_OY, oy_roi)
	dct_put(dct, SPDB_OZ, oz_roi)

	dct_put(dct, SPDB_ZX, zpx_roi)
	dct_put(dct, SPDB_ZY, zpy_roi)
	dct_put(dct, SPDB_ZZ, zpz_roi)
		
	dct_put(dct, SPDB_EV_ROIS, e_rois)
	dct_put(dct, SPDB_SUB_SPATIAL_ROIS, None)
	
	dct_put(dct, SPDB_EV_NPOINTS, 1)	#holds total number of EV points
	dct_put(dct, SPDB_RECT, (x_roi[START], y_roi[START], x_roi[STOP], y_roi[STOP]))	#holds total number of EV points
	
	dct_put(dct, SPDB_PLOT_ITEM_ID, None)	#the plotItem id, to be set by caller
	dct_put(dct, SPDB_PLOT_ITEM_TITLE, None)	#the plotItem title, to be set by caller
	dct_put(dct, SPDB_PLOT_KEY_PRESSED, None)	#the plotItem id, to be set by caller
	dct_put(dct, SPDB_PLOT_IMAGE_TYPE, None)	#used to help determine what to plot when a scan is loaded. image_types-> Enum('focus', 'osafocus','image', 'line_plot')
	dct_put(dct, SPDB_PLOT_SHAPE_TYPE, None) 	#the plot shape item type: spatial_type_prefix-> ROI, SEG, PNT

	dct_put(dct, SPDB_SCAN_PLUGIN_TYPE, None) 	#the scan type: scan_types-> Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Image_Stack', 'Generic_Scan')	
	dct_put(dct, SPDB_SCAN_PLUGIN_SUBTYPE, None) 	#the scan sub type: scan_sub_types = Enum('Point_by_Point', 'Line_Unidir')
	#dct_put(dct, SPDB_SCAN_PLUGIN_ITEM_ID, None)		#the id of the currently selected scan, set in a scan pluggin widget
	dct_put(dct, SPDB_SCAN_PLUGIN_SECTION_ID, None)	#a string saying with the scan section ID is, used for determining 
	dct_put(dct, SPDB_SCAN_PLUGIN_DATAFILE_PFX, None)	#a one character prefix for the scan type, using this to save files with a
	dct_put(dct, SPDB_SCAN_PLUGIN_MAX_SCANRANGE, (None, None))	#scans like zp_image_scan have a limited range, so have pluggin define the range so that plot etc can make use of this info
	dct_put(dct, SPDB_SPATIAL_ROIS_CENTER, (None, None)) # if there is a multi spatial roi scan this will contain the center of all of those scans
	dct_put(dct, SPDB_ACTIVE_DATA_OBJECT, make_active_data_dict())	#this will contain the Active data odject used by scan for populating data

	return(dct)

def make_active_data_dict():
	"""
	a standard dict used during data collection, all recorded data during a scan must use this dict
	then pass it to the dataIO module for export into the desired format on disk
	"""
	dct = {}
	dct_put(dct, ADO_START_TIME, None)
	dct_put(dct, ADO_END_TIME, None)
	dct_put(dct, ADO_DEVICES, None)
	dct_put(dct, ADO_VERSION, None)
	
	dct_put(dct, ADO_DATA_SSCANS, {})
	dct_put(dct, ADO_DATA_POINTS, None)
	
	dct_put(dct, ADO_CFG_WDG_COM, None)
	dct_put(dct, ADO_CFG_SCAN_TYPE, None) 
	dct_put(dct, ADO_CFG_ROI, None)
	dct_put(dct, ADO_CFG_CUR_EV_IDX, None)
	dct_put(dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, None)
	dct_put(dct, ADO_CFG_CUR_SAMPLE_POS, None)
	dct_put(dct, ADO_CFG_CUR_SEQ_NUM, None)
	dct_put(dct, ADO_CFG_DATA_DIR, None)
	dct_put(dct, ADO_CFG_DATA_FILE_NAME, None) 	#the data file name WITHOUT the extension, that is determined by the
	dct_put(dct, ADO_CFG_UNIQUEID, None)
	dct_put(dct, ADO_CFG_DATA_STATUS, DATA_STATUS_NOT_FINISHED)
	
	return(dct)


def assign_datafile_names_to_sp_db(sp_db, d):
    ''' d keys ['thumb_name', 'prefix', 'data_ext', 'stack_dir', 'data_name', 'thumb_ext']
    '''
    ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
    dct_put(ado_obj, ADO_CFG_DATA_FILE_NAME, d['data_name']) 
    dct_put(ado_obj, ADO_CFG_DATA_THUMB_NAME, d['thumb_name'])
    dct_put(ado_obj, ADO_CFG_PREFIX, d['prefix'])
    
def get_datafile_names_from_sp_db(sp_db):
    ''' d keys ['thumb_name', 'prefix', 'data_ext', 'stack_dir', 'data_name', 'thumb_ext']
    '''
    ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
    dct_put(ado_obj, ADO_CFG_DATA_FILE_NAME, d['data_name']) 
    dct_put(ado_obj, ADO_CFG_DATA_THUMB_NAME, d['thumb_name'])
    dct_put(ado_obj, ADO_CFG_PREFIX, d['prefix'])
    


class ActiveDataObj(object):
	
	def __init__(self):
		"""
		a standard dict used during data collection, all recorded data during a scan must use this dict
		then pass it to the dataIO module for export into the desired format on disk
		"""
		self.dct = {}
		self.reset_data_dct()
	
	def reset_data_dct(self):
		dct_put(self.dct, 'ID', 'ACTIVE_DATA_DICT')	#the id of this dict type
		dct_put(self.dct, 'HDF5_Version', None)
		dct_put(self.dct, 'NeXus_version', None)
		dct_put(self.dct, 'TIME', None)
		dct_put(self.dct, 'DATA_DIR', None)
		dct_put(self.dct, 'DATA_FILE_NAME', None)
		dct_put(self.dct, 'ENTRIES', None)
	
	def get_data_dct(self):
		return(self.dct)
	
	def set_scan_start_time(self):
		"""
		"""
		dct_put(self.dct, ADO_START_TIME, make_timestamp_now())
		
	def set_scan_end_time(self):
		"""
		"""
		dct_put(self.dct, ADO_END_TIME, make_timestamp_now())

def get_data_status_from_wdg_com(wdg_com):
	ado_obj = get_ado_obj_from_wdg_com(wdg_com)
	data_status = dct_get(ado_obj, ADO_CFG_DATA_STATUS)
	return(data_status)

def get_scan_request_from_wdg_com(wdg_com):
	ado_obj = get_ado_obj_from_wdg_com(wdg_com)
	data_status = dct_get(ado_obj, ADO_CFG_DATA_STATUS)
	return(data_status)

def get_cfg_from_ado_wdg_com(wdg_com):
	ado_obj = get_ado_obj_from_wdg_com(wdg_com)
	cfg = dct_get(ado_obj, ADO_CFG)
	return(cfg)
	
def get_ado_obj_from_wdg_com(wdg_com):
	sp_db = get_first_sp_db_from_wdg_com(wdg_com)
	ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
	return(ado_obj)

def get_first_sp_db_from_wdg_com(wdg_com):
	(sp_roi_dct, sp_ids, sp_id, sp_db) = wdg_to_sp(wdg_com)
	return(sp_db)

def get_first_sp_id_from_wdg_com(wdg_com):
	(sp_roi_dct, sp_ids, sp_id, sp_db) = wdg_to_sp(wdg_com)
	return(sp_id)

def get_sp_ids_from_wdg_com(wdg_com):
	(sp_roi_dct, sp_ids, sp_id, sp_db) = wdg_to_sp(wdg_com)
	return(sp_ids)

def get_sp_roi_dct_from_wdg_com(wdg_com, sp_id=None):
	(sp_roi_dct, sp_ids, sp_id, sp_db) = wdg_to_sp(wdg_com, sp_id)
	return(sp_roi_dct)

def get_sp_db_from_wdg_com(wdg_com, sp_id=None):
	(sp_roi_dct, sp_ids, sp_id, sp_db) = wdg_to_sp(wdg_com, sp_id)
	return(sp_db)

def wdg_to_sp(wdg_com, sp_id=None):
	sp_roi_dct = dct_get(wdg_com, SPDB_SPATIAL_ROIS)
	if(type(sp_roi_dct) == dict):
		if(sp_roi_dct):
			sp_ids = list(sp_roi_dct.keys())
			if(sp_id == None):
				sp_id = sp_ids[0]
			sp_db = sp_roi_dct[sp_id]
			return((sp_roi_dct, sp_ids, sp_id, sp_db))
		else:
			return(({}, [], None, {}))
	else:
		return(({}, [], None, {}))

def make_base_wdg_com():
	wdg_com = {}
	dct_put(wdg_com, WDGCOM_CMND, None)
	dct_put(wdg_com, WDGCOM_SPATIAL_ROIS,  {})
	dct_put(wdg_com, SPDB_SINGLE_LST_SP_ROIS, [])
	dct_put(wdg_com, SPDB_SINGLE_LST_POL_ROIS, [])
	dct_put(wdg_com, SPDB_SINGLE_LST_DWELLS, [])
	dct_put(wdg_com, SPDB_SINGLE_LST_EV_ROIS, [])
	return(wdg_com)
""" 
Define the standard dicts that will be used in the three main group of activities:


	1. Communication between GUI and widgets [WDG_COM_DICT].
		This dict consists of scan parameters for X, Y, Z and EV, as well as the image type and the 
		dicts of the InputState class (located in StxmImageWidget). 
		Situations that this dict is to be used for:
			- stxmImageWidget emitting _new_roi() signal
			- stxmImageWidget emitting scan_loaded() signal
			- scan pluggins mod_roi() function expect this dict as an argument to set the scan parameters
			- scan pluggins populate this dict in their update_data() functions
			- scan engine expects to configure a scan using this type of dict
			
	2. Recording data in the GUI and passing a standard dict to the dataIO module for translation into the desired format of disk file [ACTIVE_DATA_DICT].
			




 
MAIN_OBJ.set('SCAN.DATA.SSCANS.' + scan.section_name, scan.get_all_data())
			#flip upside down
			#make a copy of teh data so that it will not be overwritten (reinitialized) before it has been saved to disk
			_data = np.flipud(self.data[_ev_idx]).copy()
				
			#MAIN_OBJ.set('SCAN.CFG.ROI', self.roi)
			#MAIN_OBJ.set('SCAN.DATA.POINTS.' + str(_evidx), _data )
			
			MAIN_OBJ.set('SCAN.CFG.SCAN_TYPE',self.roi['SCAN_TYPE']) 
			MAIN_OBJ.set('SCAN.CFG.ROI', self.roi)
			MAIN_OBJ.set('SCAN.DATA.POINTS', self.data )
							
			sample_pos = 1
			datadir = self.get_data_dir()
			seq_num = self.get_next_number(datadir)
			fname = '%s%d-%05d' % (self.roi['DATA_FILE_PFX'], sample_pos, seq_num + _img_idx)
			unique_id = 'm%s%d-%05d' % (self.roi['DATA_FILE_PFX'], sample_pos, seq_num + _img_idx)
				
			#MAIN_OBJ.set('SCAN.CFG.UNIQUEID', 'ms%d-%05d' % (sample_pos, seq_num))
			MAIN_OBJ.set('SCAN.TIME', make_timestamp_now())
			MAIN_OBJ.set('SCAN.CFG.CUR_EV_IDX', _ev_idx)
			MAIN_OBJ.set('SCAN.CFG.CUR_SPATIAL_ROI_IDX', _spatial_roi_idx)
			MAIN_OBJ.set('SCAN.CFG.CUR_SAMPLE_POS', sample_pos)
			MAIN_OBJ.set('SCAN.CFG.CUR_SEQ_NUM', seq_num)
			MAIN_OBJ.set('SCAN.CFG.DATA_DIR', datadir)
			MAIN_OBJ.set('SCAN.CFG.DATA_FILE_NAME', fname)
			MAIN_OBJ.set('SCAN.CFG.UNIQUEID', unique_id)
			MAIN_OBJ.set('SCAN.DEVICES', MAIN_OBJ.get_devices())

"""