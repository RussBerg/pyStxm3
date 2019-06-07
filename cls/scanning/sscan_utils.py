'''
Created on 2014-09-08

@author: bergr
'''
import os
import time

import numpy as np
import simplejson as json
# from bcm.protocol.epics import PV
from epics import PV

from bcm.dcs.epics.devices.scan import Scan, NUM_POSITIONERS, NUM_TRIGGERS, NUM_DETECTORS
from cls.utils.log import get_module_logger

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


zpz_scanlist = ['ambstxm:xyz:scan3']
energy_scanlist = ['ambstxm:energy:scan1','ambstxm:energy:scan2','ambstxm:energy:scan3']
samplexy_scanlist = ['ambstxm:samplexy:scan1','ambstxm:samplexy:scan2']
xy_scanlist = ['ambstxm:xyz:scan1','ambstxm:xyz:scan2']
xyz_scanlist = ['ambstxm:xyz:scan1','ambstxm:xyz:scan2','ambstxm:xyz:scan3']

energy_scan_cfgs = energy_scanlist
image_lxl_scan_cfgs = energy_scanlist + samplexy_scanlist
image_pxp_scan_cfgs = energy_scanlist + samplexy_scanlist
point_scan_cfgs = energy_scanlist + samplexy_scanlist
det_scan_cfgs = xy_scanlist
osa_scan_cfgs = xy_scanlist
osa_focus_cfgs = xyz_scanlist
focus_scan_cfgs = zpz_scanlist + samplexy_scanlist


class sscan_parser(object):
	
	def __init__(self, sscan_dict):
		super(sscan_parser, self).__init__()
		self.sscan = sscan_dict
		
	
	def get_detector_data(self, det_num, npts=None):
		"""
		Data and related PV's:
		Field	Summary	Type	DCT	Initial/Default	Read	Modify	Posted	PP
		For nn in [01..70] (e.g., "D01PV", "D02PV", ... "D70PV") :
		DnnPV	data nn Process Variable name	STRING [40]	Yes	Null	Yes	Yes	No	No
		DnnNV	data nn Name Valid	LONG	No	0	Yes	Yes	Yes	No
		DnnDA	Detector nn End-Of-Scan Data Array	FLOAT[ ]	No	Null	Yes	No	Yes	No
		DnnCA	Detector nn Current-Data Array	FLOAT[ ]	No	Null	Yes	No	Yes	No
		DnnEU	Detector nn Eng. Units	STRING [16]	Yes	16	Yes	Yes	No	No
		DnnHR	Det. nn High Range	DOUBLE	Yes	0	Yes	Yes	No	No
		DnnLR	Det. nn Low Range	DOUBLE	Yes	0	Yes	Yes	No	No
		DnnPR	Det. nn Precision	SHORT	Yes	0	Yes	Yes	No	No
		DnnCV	Detector nn Current Value	FLOAT	No	0	Yes	No	Yes	No
		DnnLV	Detector nn Last Value	FLOAT	No	0	Yes	No	No	No

		"""
		dat_attr = 'D%02dDA' % det_num
		pv_attr = 'D%02dPV' % det_num
		hval_attr = 'D%02dHR' % det_num
		lval_attr = 'D%02dLR' % det_num
		#print 'get_detector_data: [%s] getting [%s] ' % (self.positioner, dat_attr)
		if(npts is None):
			#get all points
			#dat = self.scn.get(dat_attr)
			dat = self.scan_data[dat_attr]
		else:
			dat = self.scan_data[dat_attr][0:npts]
		pvname = self.scan_data[pv_attr]
		hval = self.scan_data[hval_attr]
		lval = self.scan_data[lval_attr]
		dct = {}
		dct['pvname'] = pvname
		dct['lval'] = lval
		dct['hval'] = hval
		dct['data'] = dat
		dct['npts'] = npts
		return(dct)
	
	def gen_positioner_points(self, pnum, npts):
		start = self.sscan['P%dSP' % pnum]
		end = self.sscan['P%dEP' % pnum]
		pts = np.linspace(start, end, npts)
		return(pts)
		
	def get_positioner_points(self, pnum, npts=None):
		dat_attr = 'P%dRA' % pnum
		lst = []
		try:
			#print 'get_positioner_points: [%s] getting [%s] ' % (self.positioner, dat_attr)
			if(npts is None):
				#get all points
				pts = self.sscan[dat_attr]
			else:
				if(npts == 2):
					start = self.sscan['P%dSP' % pnum]
					end = self.sscan['P%dEP' % pnum]
					pts = [start, end]
				else:
					pts = self.sscan[dat_attr][0:npts]
			return(pts)
			
		except KeyError as e:
			print('get_positioner_points: Error: [%s]' % str(e))
			
	def get(self, attr):
		if(attr in list(self.sscan.keys())):
			return(self.sscan[attr])
	
	def get_all_detector_data(self):
		all_data = {}
		for i in range(1,70):
			pv_attr = 'D%02dPV' % i
			pvname = self.sscan[pv_attr]
			if(len(pvname) > 0):
				dct_str = 'D%d_POINTS' % i
				all_data[dct_str] = self.get_detector_data(i, int(self.num_points))
				#all_data.append(dct)
		return(all_data)

	def get_all_positioner_points(self):
		all_data = {}
		for i in range(1,4):
			pv_attr = 'P%dPV' % i
			if(pv_attr in list(self.sscan.keys())):
				pvname = self.sscan[pv_attr]
				if(len(pvname) > 0):
					npts = self.sscan['NPTS']
					all_data['P%d_POINTS' % i] = self.get_positioner_points(i, int(npts))
					#all_data['NUM_P%d_POINTS' % i] = len(all_data['P%d_POINTS' % i])
					
		return(all_data)


def get_base_fields():
	fields = ['NPTS','BSPV','BSCD','PASM','AWCT','ACQT','ACQM','ATIME','COPYTO','ASPV','ASCD','A1PV','A1CD','ASWAIT']
	return(fields)

def get_positioner_fields(with_arrays=False, for_restore=False):
	
	array_attrs = ('AR', 'RA', 'PA')
	non_restore_attrs = ('CP', 'SI', 'WD')
	base_posit_attrs = ('PV', 'SP', 'EP', 'SM', 'EU')
	
	posit_attrs = base_posit_attrs
	pos_fields = []
	
	if(with_arrays):
		pos_fields += array_attrs 
	
	if(not for_restore):
		#not for restoring only for recording so include the non restore fields
		posit_attrs += non_restore_attrs
	
	
	for i in range(1, NUM_POSITIONERS+1):
		for a in posit_attrs:
			pos_fields.append('P%i%s' % (i, a))
	
	
	for i in range(1, NUM_POSITIONERS+1):
		pos_fields.append('R%iPV' % (i))
	
	pos_fields.append('PASM')
	pos_fields.append('PDLY')
	pos_fields.append('REFD')
			
	return(pos_fields)


def get_dettrig_fields():
	posit_attrs = ('PV', 'CD')
	_fields = []
	
	for i in range(1, NUM_TRIGGERS+1):
		for a in posit_attrs:
			_fields.append('T%i%s' % (i, a))
	_fields.append('DDLY')
	
	return(_fields)

def get_det_fields():
	_fields = []
	for i in range(1, NUM_DETECTORS+1):
		_fields.append('D%2.2iPV' % (i))
	
	return(_fields)


class NumpyAwareJSONEncoder(json.JSONEncoder):
	def default(self, obj):
		try:
			if isinstance(obj, np.ndarray) and obj.ndim == 1:
				return obj.tolist()
			elif isinstance(obj, np.ndarray) and obj.ndim == 2:
				return obj.tolist()
			elif isinstance(obj, np.ndarray) and obj.ndim == 3:
				return obj.tolist()
			elif isinstance(obj, np.generic):
				return obj.item()
			elif isinstance(obj, set):
				return list(obj)
			return json.JSONEncoder.default(self, obj)
		except TypeError:
			_logger.error('dataRecorder.py: NumpyAwareJSONEncoder: TypeError')

def loadJson(filename):
	"""internel load json data from disk"""
	if os.path.exists(filename):
		js = json.loads(file(filename).read())
	else:
		_logger.error('json file does not exist: [%s]' % filename)
		js = {}
	return js


def saveAs(filename, dataObj):
		"""save the data in the data object to the given filename """
		if dataObj != None:
			j=json.dumps(dataObj, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
			f=open(filename,"w")
			f.write(j)
			f.close()
			_logger.info('Saved: %s' % filename)

def get_fields(fields, sscan, with_positioners=True, with_detectors=False):
	
	#pos_fields = get_positioner_fields(with_arrays=False)
	det_fields = get_det_fields()
	
	
	#use_fields = get_base_fields()
	
	#if(not with_positioners):
	#	use_fields += pos_fields

	#if(not with_detectors):
	#	use_fields += det_fields
	
	dct = {}
	for fname in fields:
		#skip any fields that have been set
		if(fname in det_fields):
			pass
		else:
			#as_string=False
			#dct[fname] = sscan.get(fname)
			dct[fname] = sscan.get(fname, as_string=True)
	
	return(dct)

def restore_sscan_cfg(sscan_name, sscan_dct, with_positioners=False, with_detectors=False, sscans={}):
	
	pos_fields = get_positioner_fields(with_arrays=False, for_restore=True)
	det_fields = get_det_fields()
	use_fields = get_base_fields() + get_dettrig_fields()
	
	if(with_positioners):
		use_fields += pos_fields

	if(with_detectors):
		use_fields += det_fields
	
	if(sscan_name in list(sscans.keys())):
		#use passed in instance
		sscan = sscans[sscan_name]
	else:
		#make a new instance
		sscan = Scan(sscan_name)
	
	for k in list(sscan_dct.keys()):
		#skip any fields that have been set
		if(k in use_fields):
			#put(self, attr, value, wait=False, use_complete=False, timeout=10)
			#print 'restoring [%s.%s] = %s' % (sscan_name, k, str(sscan_dct[k]))
			sscan.put(k, sscan_dct[k])
	
	#print '[%s] restored' % (sscan_name)


def qt_restore_sscan_cfg(sscan_name, sscan_dct, with_positioners=False, with_detectors=False, sscans={}):
	
		pos_fields = get_positioner_fields(with_arrays=False, for_restore=True)
		det_fields = get_det_fields()
		use_fields = get_base_fields() + get_dettrig_fields()
		
		if(with_positioners):
			use_fields += pos_fields
	
		if(with_detectors):
			use_fields += det_fields
		
		#if(sscan_name in sscans.keys()):
		#	#use passed in instance
		#	sscan = sscans[sscan_name]
		#else:
		#	#make a new instance
		#	sscan = Scan(sscan_name)
		
		for k in list(sscan_dct.keys()):
			#skip any fields that have been set
			if(k in use_fields):
				#put(self, attr, value, wait=False, use_complete=False, timeout=10)
				#print 'restoring [%s] = %s' % (sscan_name + '.' + k, str(sscan_dct[k]))
				p = PV(sscan_name + '.' + k)
				p.put(sscan_dct[k], use_complete=True)
				waiting = True
				while waiting:
					time.sleep(0.001)
					waiting = not p.put_complete
					QtWidgets.QApplication.processEvents()
				#print 'All puts are done!'
				
				#print 'qt_restore_sscan_cfg: [%s] restored' % (sscan_name)

def get_sscan_cfg(sscan_name, with_positioners=True, sscans={}):
	""" given an sscan record name string retrieve all of the current configuration
	so that I can capture a config once I have figured it out
	"""
	pos_fields = get_positioner_fields(with_arrays=False)
	
	detrig_fields = get_dettrig_fields()
	
	det_fields = get_det_fields()
	
	#get all fields that you can see from main screen
	fields = get_base_fields()

	fields +=  pos_fields + detrig_fields + det_fields
	
	if(sscan_name in list(sscans.keys())):
		#use passed in instance
		sscan = sscans[sscan_name]
	else:
		#make a new instance
		sscan = Scan(sscan_name)
		
	sscan_dct = get_fields(fields, sscan, with_positioners=with_positioners)
	
	return(sscan_dct)


def get_scan_cfgs(scanname_list, with_positioners=True):
	""" walk a list of scan names and retrieve their configurations returning them all in a
	dict with each scan name as a key
	""" 
	cfgs = {}
	for sname in scanname_list:
		#print 'retrieving [%s]' % sname
		cfgs[sname] = get_sscan_cfg(sname, with_positioners=with_positioners)

	return(cfgs)
	
def restore_scan_cfgs(cfg_fname, with_positioners=True, with_detectors=False, sscans={}):
	cfg_dct = loadJson(cfg_fname)
	
	for sname in cfg_dct:
		#if(sname in sscans.keys()):
		_logger.info('Restoring: [%s]' % sname)
		restore_sscan_cfg(sname, cfg_dct[sname], with_positioners=with_positioners, with_detectors=with_detectors, sscans=sscans)
	_logger.info('Restoration Done')

def qt_restore_scan_cfgs(cfg_fname, with_positioners=True, sscans={}):
	cfg_dct = loadJson(cfg_fname)
	
	for sname in cfg_dct:
		#if(sname in sscans.keys()):
		_logger.info('Restoring: [%s]' % sname)
		qt_restore_sscan_cfg(sname, cfg_dct[sname], with_positioners=with_positioners, sscans=sscans)
	_logger.info('Restoration Done')

def reset_scan_cfgs(sscan_names, with_positioners=True, sscans={}):
	savedir = r'C:\controls\py2.7\Beamlines\sm\data\guest\scan_cfgs\\'
	cfg_fname = savedir + 'reset.cfg'
	
	cfg_dct = loadJson(cfg_fname)
	
	for sscan_name in sscan_names:
		#print 'Restoring: [%s]' % sscan_name
		restore_sscan_cfg(sscan_name, cfg_dct['reset'], with_positioners=with_positioners, sscans=sscans)

def save_point_scan_cfgs(fname):
	_cfgs = get_scan_cfgs(point_scan_cfgs, with_positioners=True)
	saveAs(fname, _cfgs)

def reset_point_scan_cfg():
	reset_scan_cfgs(point_scan_cfgs)

def restore_point_scan_cfg(fname):
	#savedir = r'C:\controls\py2.7\Beamlines\sm\data\guest\scan_cfgs\\'
	restore_scan_cfgs(fname, with_positioners=False)


	
if __name__ == '__main__':
	
	savedir = r'C:\controls\py2.7\Beamlines\sm\data\guest\scan_cfgs\\'
	savefname =  r'scancfg3.json'
	
	
# 	reset_scan_cfgs('ambstxm:xyz:scan1')
	
# 	cfg_dct = get_sscan_cfg('ambstxm:samplexy:scan2')
# 	
# 	saveAs(r'C:\controls\py2.7\Beamlines\sm\data\guest\scancfg3.json',cfg_dct)
# 	rest_dct = loadJson(r'C:\controls\py2.7\Beamlines\sm\data\guest\scancfg.json')
# 	
# 	#rest_dct['R1PV'] = 'OOPS:WRONG:PV'
# 	restore_sscan_cfg('ambstxm:samplexy:scan2', rest_dct)
# 	restore_sscan_cfg('ambstxm:xyz:scan1', rest_dct)
	
# 	energy_scanlist = ['ambstxm:energy:scan1','ambstxm:energy:scan2','ambstxm:energy:scan3']
# 	samplexy_scanlist = ['ambstxm:samplexy:scan1','ambstxm:samplexy:scan2']
# 	xyz_scanlist = ['ambstxm:xyz:scan1','ambstxm:xyz:scan2','ambstxm:xyz:scan3']
# 	
# 	point_scan_cfgs = energy_scanlist + samplexy_scanlist
# 	
# 	reset_scan_cfgs(point_scan_cfgs)
# 	#save_point_scan_cfgs(savedir + 'point_scans.cfg')
# 	restore_scan_cfgs(savedir + 'point_scans.cfg', with_positioners=True)
# 	
# 	save_point_scan_cfgs(savedir + 'point_scans.cfg')
# 	
	#OSA FOCUS SCAN
	#osa_focus_dct = get_scan_cfgs(osa_focus_cfgs)
	#saveAs(savedir + 'osa_focus.cfg', osa_focus_dct)
	#reset_scan_cfgs(osa_focus_cfgs)
	#restore_scan_cfgs(savedir + 'osa_focus.cfg', with_positioners=True)
	
	#OSA FOCUS UNIDIR SCAN
	#osa_focus_dct = get_scan_cfgs(osa_focus_cfgs)
	#saveAs(savedir + 'osa_focus-unidir.cfg', osa_focus_dct)
	#reset_scan_cfgs(osa_focus_cfgs)
	#restore_scan_cfgs(savedir + 'osa_focus-unidir.cfg', with_positioners=True)
	
	#OSA SCAN
	#osa_dct = get_scan_cfgs(osa_scan_cfgs)
	#saveAs(savedir + 'osa.cfg', osa_dct)
	#reset_scan_cfgs(osa_focus_cfgs)
	#restore_scan_cfgs(savedir + 'osa.cfg', with_positioners=True)
	
	#OSA UNIDIR SCAN
	#osa_dct = get_scan_cfgs(osa_scan_cfgs)
	#saveAs(savedir + 'osa-unidir.cfg', osa_dct)
	#reset_scan_cfgs(osa_focus_cfgs)
	#restore_scan_cfgs(savedir + 'osa-unidir.cfg', with_positioners=True)
	
	#DETECTOR SCAN
	#det_dct = get_scan_cfgs(det_scan_cfgs)
	#saveAs(savedir + 'detector.cfg', det_dct)
	#reset_scan_cfgs(det_scan_cfgs)
	#restore_scan_cfgs(savedir + 'detector.cfg', with_positioners=True)
	
	#DETECTOR UNIDIR SCAN
	#det_dct = get_scan_cfgs(det_scan_cfgs)
	#saveAs(savedir + 'detector-unidir.cfg', det_dct)
	#reset_scan_cfgs(det_scan_cfgs)
	#restore_scan_cfgs(savedir + 'detector-unidir.cfg', with_positioners=True, with_detectors=True)
	
	#IMAGE POINT BY POINT SCAN
	#img_dct = get_scan_cfgs(image_pxp_scan_cfgs)
	#saveAs(savedir + 'image_pxp.cfg', img_dct)
	#reset_scan_cfgs(image_pxp_scan_cfgs)
	#restore_scan_cfgs(savedir + 'image_pxp.cfg', with_positioners=True)
	
	#IMAGE LINE BY LINE SCAN
	#img_dct = get_scan_cfgs(image_lxl_scan_cfgs)
	#saveAs(savedir + 'image_lxl_scans.cfg', img_dct)
	#reset_scan_cfgs(image_lxl_scan_cfgs)
	restore_scan_cfgs(savedir + 'image_lxl_scans.cfg', with_positioners=True)
	
	#ENERGY SCAN
	#ev_dct = get_scan_cfgs(energy_scan_cfgs)
	#saveAs(savedir + 'energy_scans.cfg', ev_dct)
	#reset_scan_cfgs(image_lxl_scan_cfgs)
	#restore_scan_cfgs(savedir + 'image_lxl.cfg', with_positioners=True)
	
	#POINT SCAN
	#point_dct = get_scan_cfgs(point_scan_cfgs)
	#saveAs(savedir + 'point_scans.cfg', point_dct)
	#reset_scan_cfgs(image_lxl_scan_cfgs)
	#restore_scan_cfgs(savedir + 'image_lxl.cfg', with_positioners=True)
	
	#FOCUS SCAN
	#focus_dct = get_scan_cfgs(focus_scan_cfgs)
	#saveAs(savedir + 'focus_scans.cfg', focus_dct)
	#reset_scan_cfgs(image_lxl_scan_cfgs)
	#restore_scan_cfgs(savedir + 'image_lxl.cfg', with_positioners=True)
# 	
# 	ev_cfgs = get_scan_cfgs(energy_scanlist)
# 	saveAs(savedir + 'energy.cfg', ev_cfgs)
# 	
# 	sample_cfgs = get_scan_cfgs(samplexy_scanlist)
# 	saveAs(savedir + 'samplexy.cfg', sample_cfgs)
# 	
# 	xyz_cfgs = get_scan_cfgs(xyz_scanlist)
# 	saveAs(savedir + 'xyz-all.cfg', xyz_cfgs)
# 	
# 	restore_scan_cfgs(savedir + 'xyz.cfg', with_positioners=True)
	
	
__all_=['save_point_scan_cfgs','get_scan_cfgs', 'saveAs','reset_point_scan_cfg','reset_scan_cfgs','restore_point_scan_cfg', 'energy_scan_cfgs','image_lxl_scan_cfgs','image_pxp_scan_cfgs', 'point_scan_cfgs', 'det_scan_cfgs', 'osa_scan_cfgs', 'osa_focus_cfgs', 'focus_scan_cfgs' ]
	
	
	
	
