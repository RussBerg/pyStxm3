'''
Created on Nov 19, 2015

@author: bergr
'''
'''
Created on Nov 17, 2015

@author: bergr
'''
'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#
import os, sys
#from sm_dev_env_path_setup import pypath #located in c:\python27/Lib/site_packages


# pp = pypath.split(';')
# for p in pp:
# 	print p
# 	sys.path.append(p)
	
from PyQt5 import QtCore, QtGui
import copy
import time
import zmq
import simplejson as json
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.utils.json_threadsave import dict_to_json_string
from cls.appWidgets.splashScreen import get_splash, del_splash
from cls.scanning.nexus.cls_nx_api import _group, _dataset, nx_close, nx_open, nx_get, nx_put
from cls.utils.log import get_module_logger
from cls.zeromq.epics.epics_api import * 

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = "10000000"

_logger = get_module_logger(__name__)

splash = get_splash()
didit = splash.close()
	
devs = MAIN_OBJ.get_devices()
posners_dct = devs['POSITIONERS']
detectors_dct = devs['DETECTORS']
pvs_dct = devs['PVS']
sscans_dct = devs['SSCANS']
sscans_dct_keys = list(sscans_dct.keys())

posner_snapshot = {}
det_snapshot = {}
pv_snapshot = {}
sscan_snapshot = {}
dev_update_dct = {}

save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

def update_posner_snapshot():
	for k in list(posners_dct.keys()):
		posner_snapshot[k] = {}
		posner_snapshot[k]['VELO'] = posners_dct[k].get('velocity')
		posner_snapshot[k]['VAL'] = posners_dct[k].get('VAL')
		posner_snapshot[k]['DESC'] = posners_dct[k].get('description')
		posner_snapshot[k]['NAME'] = posners_dct[k].get_name()
		posner_snapshot[k]['ACCL'] = posners_dct[k].get('ACCL')
		posner_snapshot[k]['RRBV'] = posners_dct[k].get('RRBV')
		posner_snapshot[k]['LLM'] = posners_dct[k].get_low_limit()
		posner_snapshot[k]['HLM'] = posners_dct[k].get_high_limit()
		posner_snapshot[k]['RDBD'] = posners_dct[k].get('RDBD')
		posner_snapshot[k][RBV] = posners_dct[k].get('RBV')

	return(posner_snapshot)


def update_dev_snapshot():
	global dev_update_dct
	upd_dct = {}
	for dev_name in list(dev_update_dct.keys()):
		dev = MAIN_OBJ.device(dev_name)
		val = None
		if(dev is not None):
			val = dev.get_position()

		upd_dct[dev_name] = val

	return(upd_dct)

def register_dev_update_lst(dev_lst):
	global dev_update_dct
	dev_update_dct = {}
	for dev_name in dev_lst:
		dev_update_dct[dev_name] = {}


def save_snapshot_to_tmp_file(fname, dct, modify=False):
	nf = nx_open(fname)
	if (nf is None):
		_logger.error('Problem creating temp posner file [%s]' % fname)
		return

	#check if snapshot already exists
	if('snapshot' in list(nf.keys())):
		nxgrp = nf['snapshot']
		modify = True
	else:
		if(not modify):
			nxgrp = _group(nf, 'snapshot', 'NX_none')
		else:
			nxgrp = nf['snapshot']

	for k in dct:
		if(modify):
			posgrp = nxgrp[k]
		else:
			posgrp = _group(nxgrp, k, 'NX_none')

		for fld in list(dct[k].keys()):
			if(modify):
				posgrp[fld][()] = dct[k][fld]
			else:
				_dataset(posgrp, fld, dct[k][fld],'NX_none')

	print('Saved [%s]' % fname)
	nx_close(nf)

def save_data_to_tmp_file_idx(fname, idx, dname, data, modify=False):
	nf = nx_open(fname)
	if (nf is None):
		_logger.error('save_data_to_tmp_file_idx: Problem opening tmp file [%s]' % fname)
		return
	idx_str = 'idx%d' % idx
	if(idx_str in list(nf.keys())):
		idxgrp = nf[idx_str]
		modify = True
	else:
		if (not modify):
			idxgrp = _group(nf, idx_str, 'NX_none')
		else:
			idxgrp = nf[idx_str]

	if(dname in list(idxgrp.keys())):
		#delete it so that its shape wont restrict assignment
		del idxgrp[dname]
	#assign the data
	datagrp = _group(idxgrp, dname, 'NX_none')
	_dataset(datagrp, 'DATA', data, 'NX_none')

	print('Saved [%s] data to [%s/%s]' % (fname, idx_str,dname))
	nx_close(nf)

def save_dev_update_to_tmp_file(fname, idx, dev_dct):
	nf = nx_open(fname)
	if (nf is None):
		_logger.error('Problem creating temp posner file [%s]' % fname)
		return

	modify = False
	#check if idx exists
	idx_str = 'idx%d' % idx
	if(idx_str in list(nf.keys())):
		nxgrp = nf[idx_str]
	else:
		nxgrp = _group(nf, idx_str, 'NX_none')
		modify = True

	for k in dev_dct:
		if(k in nxgrp):
			posgrp = nxgrp[k]
		else:
			posgrp = _group(nxgrp, k, 'NX_none')

		if('DATA' in list(posgrp.keys())):
			posgrp['DATA'][()] = dev_dct[k]
		else:
			_dataset(posgrp, 'DATA', dev_dct[k],'NX_none')

	print('Dev Update [%d] Saved [%s]' % (idx, fname))
	nx_close(nf)



def save_img_idx_map_to_tmp_file(fname, dct_str):
	nf = nx_open(fname)
	if (nf is None):
		_logger.error('Problem opening temp file [%s]' % fname)
		return

	modify = False
	#check if idx exists
	idx_str = 'idx_map'
	if(idx_str in list(nf.keys())):
		nf[idx_str][()] = dct_str
	else:
		_dataset(nf, idx_str, dct_str,'NX_none')

	print('save_img_idx_map_to_tmp_file Saved [%s]' % (fname))
	nx_close(nf)

def update_detector_snapshot():
	"""
	update_detector_snapshot(): description
	:param detectors_dct: detectors_dct description
	:type detectors_dct: detectors_dct type
	:returns: None
	"""
	"""
	This function grabs the current values of all positioners for the 
	data saving thread to use
	
	"""
	for k in list(detectors_dct.keys()):
		det_snapshot[k] = {}
		det_snapshot[k][RBV] = detectors_dct[k].get_position()
	return(det_snapshot)

def update_pvs_snapshot():
	"""
	update_pvs_snapshot(): description

	:param pvs_dct: pvs_dct description
	:type pvs_dct: pvs_dct type
	:returns: None
	"""
	"""
	This function grabs the current values of all positioners for the 
	data saving thread to use
	
	"""
	for k in list(pvs_dct.keys()):
		pv_snapshot[k] = {}
		pv_snapshot[k][RBV] = pvs_dct[k].get_position()

	return(pv_snapshot)



def get_positioner_points(sscan,  pnum, npts=None):
	"""
	get_positioner_points(): description
		:param pnum: pnum description
	:type pnum: pnum type
		:param npts=None: npts=None description
	:type npts=None: npts=None type
		:returns: None
	"""
	dat_attr = 'P%dRA' % pnum
	try:
		#print 'get_positioner_points: [%s] getting [%s] ' % (self.positioner, dat_attr)
		if(npts is None):
		#get all points
			pts = sscan.get(dat_attr)
		else:
			if(npts == 1):
				start = sscan.get('P1SP')
				end = sscan.get('P1EP')
				pts = [start, end]
			else:
				pts = sscan.get(dat_attr)[0:npts]
		return(pts)
	
	except KeyError as e:
		print('get_positioner_points: Error: [%s]' % str(e))

def get_all_positioner_points(sscan):
	"""
	get_all_positioner_points(): description
		:returns: None
	"""
	npts = sscan.get('NPTS')
	all_data = {}
	for i in range(1,4):
		pv_attr = 'P%dPV' % i
		pra_attr = 'P%dRA' % i
		pvname = sscan.get(pv_attr)
		if(len(pvname) > 0):
			pts = get_positioner_points(sscan, i, int(npts))
			all_data[pra_attr] = pts
					
	return(all_data)
	
			
def get_all_data(sscan):
	"""
	get_all_data(): description
	:returns: None
	"""
	#print '[%s] get_all() called' % self.positioner
	try:
		scan_data = get_all_positioner_points(sscan)
		scan_data['CPT'] = sscan.get('CPT')
		scan_data['NPTS'] = sscan.get('NPTS')
		return(scan_data)
	except KeyError as e:
		print('no key in scan data for [%s]' % str(e))
		return({})


def update_sscan_snapshot(sscan_name_list):
	"""
	update_sscan_snapshot(): description

	:param pvs_dct: pvs_dct description
	:type pvs_dct: pvs_dct type
	:returns: None
	"""
	"""
	This function grabs the current values of all positioners for the 
	data saving thread to use
	
	"""
	#for sscan_name in sscan_name_list:
	for sscan_name in sscans_dct_keys:
		sscan = sscans_dct[sscan_name]
		sscan_snapshot[sscan_name] = get_all_data(sscan)


def get_all_sscans_snapshot(sscan_name_list):
	'''
	return all in list
	'''
	dct = {}
	#for sscan_name in sscan_name_list:
	for sscan_name in sscans_dct_keys:
		sscan = sscans_dct[sscan_name]
		dct[sscan_name] = sscan_snapshot[sscan_name]
	return(dct)


def start_server():

	context = zmq.Context()
	# the zmq.REPly socket type
	# It will block on recv() to get a request before it can send a reply.
	socket = context.socket(zmq.REP)
	socket.bind("tcp://*:5555")
	# update_posner_snapshot()

	time.sleep(0.5)
	fname = os.path.join(save_dir, 'tempfile.nxstxm_baseline.tmp')

	devices = MAIN_OBJ.get_devices()
	dev_keys = list(devices.keys())
	posners = devices['POSITIONERS']
	pos_keys = list(posners.keys())
	detectors = devices['DETECTORS']
	det_keys = list(detectors.keys())
	
	sscans = devices['SSCANS']
	sscan_keys = list(sscans.keys())
	
	print('zmq_epics_server: waiting for messages from the client(s)')
	abort = False
	while not abort:
		#  Wait for next request from client
		message = socket.recv()
		print(("Received request: %s" % message[0:10]))
		get = False
		put = False
		
		
		if(message.find(CMD_CHECK_IF_RUNNING) > -1):
			snd(socket, b"YES")

		elif(message.find('shape') > -1):
			snd(socket, b"Receiving Array")
			rcv_array(socket)

		elif (message.find('?') > -1):
			snd(socket, b"Receiving Zipped Pickle")
			_dct = proc_zipped_pickle(message)
			print('rcvd: zipped pickled dict', _dct)
			save_data_to_tmp_file_idx(fname, _dct['idx'], _dct['devname'], _dct['data'], modify=False)


		elif(message.find(CMD_ABORT) > -1):
			abort = True
			snd(socket, b"ABORTING")

		elif(message.find(CMD_SET_FILE_NAME) > -1):
			dct = process_str_to_dict(message, strip_cmd=True)
			if(os.path.exists(dct['dir'])):
				fname = os.path.join(dct['dir'], dct['fname'])
				snd(socket, b"FNAME [%s] IS SET" % (fname))
			else:
				snd(socket, b"DIR [%s] DOES NOT EXIST" % (dct['dir']))

		elif(message.find(CMD_SAVE_DATA_TO_IDX) > -1):
			(devname, idx, data) = parse_get_idx_from_save_data_msg(message)
			save_data_to_tmp_file_idx(fname, idx, devname, data, modify=False)

		elif (message.find(CMD_REGISTER_UPD_LIST) > -1):
			snd(socket, b"UPDATE_LIST REGISTERED")
			cmd, dv_lst = parse_get_list_msg(message)
			register_dev_update_lst(dv_lst)


		elif (message.find(CMD_UPDATE_UPD_SNAPSHOT) > -1):
			snd(socket, b"UPDATE_SNAPSHOT")
			idx = parse_get_idx_from_update_dev_msg(message)
			_dct = update_dev_snapshot()
			save_dev_update_to_tmp_file(fname, idx, _dct)


		elif(message.find(CMD_DISC_POSNER_LIST) > -1):
			snd(socket, b"%s" % (dict_to_json_string(pos_keys)))
		###################
		elif(message.find(CMD_GET_POSNER_SNAPSHOT) > -1):
			snd(socket, b"%s" % (dict_to_json_string(posner_snapshot)))	
		
		elif(message.find(CMD_UPDATE_POSNER_SNAPSHOT) > -1):
			snd(socket, b"POSITIONER UPDATE DONE")
			_dct = update_posner_snapshot()
			save_snapshot_to_tmp_file(fname, _dct, modify=False)

		###################
		elif (message.find(CMD_CREATE_NEW_FILE) > -1):
			nx_open(fname, force_new=True)
			snd(socket, b"NEW FILE CREATED")

		elif (message.find(CMD_SET_FILE_NAME) > -1):
			_dir, _fstr = process_str_to_list(message)
			if(os.path.exists(_dir)):
				fname = os.path.join(_dir, _fstr)
				snd(socket, b"FILENAME SET [%s]" % fname)
			else:
				fname = None
				snd(socket, b"DIR [%s] IS NOT VALID" % _dir)

		###################

		elif (message.find(CMD_REGISTER_IMG_IDX_MAP) > -1):
			snd(socket, b"IMAGE_IDX REGISTERED ")
			msg = strip_command_from_msg(message)
			save_img_idx_map_to_tmp_file(fname, msg)

		###################
		elif(message.find(CMD_GET_DETECTOR_SNAPSHOT) > -1):
			snd(socket, b"%s" % (dict_to_json_string(det_snapshot)))	
		
		elif(message.find(CMD_UPDATE_DETECTOR_SNAPSHOT) > -1):
			snd(socket, b"DETECTOR UPDATE DONE")
			update_detector_snapshot()
			
		###################	
		elif(message.find(CMD_GET_PV_SNAPSHOT) > -1):
			snd(socket, b"%s" % (dict_to_json_string(pv_snapshot)))	
		
		elif(message.find(CMD_UPDATE_PV_SNAPSHOT) > -1):
			snd(socket, b"PV UPDATE DONE")	
			update_pvs_snapshot()
		
		###################
		elif(message.find(CMD_UPDATE_SSCAN_SNAPSHOT) > -1):
			print(message)
			cmd, lst = parse_update_list_msg(message)
			snd(socket, b"SSCAN UPDATE DONE")
			update_sscan_snapshot(lst)
			
		elif(message.find(CMD_GET_SSCAN_SNAPSHOT) > -1):
			cmd, lst = parse_get_list_msg(message)
			snd(socket, b"%s" % (dict_to_json_string(get_all_sscans_snapshot(lst))))	
		
		######################
		elif(message.find(CMD_SENDING_DICT) > -1):
			dct = process_str_to_dict(message, strip_cmd=True)
			snd(socket, b"RCVD DICT")
			print(list(dct.keys()))
			print(dct)
				
		###################
		elif(message.find('GET>') > -1):
			get = True
			nm, attr = get_get_args(message)
			#print nm, attr
			
		###################	
		elif(message.find('PUT>') > -1):
			''' PUT>DNM_DETECTOR_Z=2500'''
			put = True
			nm, attr, val = get_put_args(message)
			snd(socket, b"PUT to %s.%s DONE" % (nm , attr))
		
		###################
		# elif(nm in pos_keys):
		# 	print 'nm[%s] is in pos_keys' % nm
		# 	if(get):
		# 		print 'in get'
		# 		fbk = posners[nm].get(attr)
		# 		snd(socket, b"%.3f" % fbk)
		# 	if(put):
		# 		posners[nm].put(attr, val)
		# else:
		# 	print 'nm[%s] is NOT in pos_keys' % nm
		# 	snd(socket, b"nm[%s] is NOT in pos_keys"% nm)
	
		#  Do some 'work'
		time.sleep(0.01)
	
		#  Send reply back to client
		#print ' sending WORLD'
		#snd(socket, b"World")
	print('zmq_epics_server exited!')
		
if __name__ == '__main__':	
	
	start_server()