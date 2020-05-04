#C:\Python27\python.exe
# -*- coding: UTF-8 -*-
import os
from datetime import timedelta, datetime
import numpy as np
import copy 
import time

from PyQt5 import QtCore, QtGui

from cls.utils.unique_id import uniqueid
from cls.utils.enum_utils import Enum
from cls.applications.pyStxm.main_obj_init import DEVICE_CFG

from bcm.epics_devices_MOVED.scan import Scan
from bcm.epics_devices_MOVED.motor_v2 import Motor_V2 as Motor
#from bcm.devices.base import BaseDevice
from bcm.device.interfaces import IClkGenerator
from bcm.device.counter import ICounter
from bcm.device.interfaces import IPlotter
from bcm.device.shutter import IShutter

# hostname = os.getenv('COMPUTERNAME')
# if(hostname == 'WKS-W001465'):
# 	pass
# elif(hostname == 'NBK-W001021'):
# 	pass
# else:
# 	from cls.applications.pyStxm.bl10ID01 import DEVICE_CFG



#from cls.scanning.stxmTypes import TWO_D, SEG, PNT, SPATIAL_TYPE_PREFIX

LINE_UNIDIR = 'Line-UniDir'
LINE_BIDIR = 'Line-BiDir'
LINE_PTBYPT = 'Line-PointByPoint'
POINT = 'Point'

ScanType = Enum('Point','LinePxP','LineFull','ImagePxP', 'ImageLineUni')
ScanStatus = Enum('READY','BUSY','ABORTING','PAUSED','ERROR')
ScanMode = Enum('PREVIEW','DATA')


class ScanDefError(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)

class ScanDef_OLD(object):
	"""@Interface"""
	
	def __init__(self):
		self._type = None
		""" string"""
		self._name = None
		""" string"""
		self._sample_position = 1 
		""" string: this represents the sample position (1 - 6) """
		
		self._mode = ScanMode.PREVIEW
		""" enum ScanMode: either PREVIEW or DATA, PREVIEW means that the data that is being collected is
		an initial preview scan (stored in /preview dir), if DATA then data is stored in the sample_position sub dir
		"""
		
		self._dir = None 
		""" string: teh base dir of the scan"""
		self._datadir = None
		""" string: the data dir of the scan"""
		
		#self.scan_id = None
		self.scan_id = uniqueid()
		""" int"""
		self.scan_seq_id = 0
		""" int"""
		self._ev_regions = []
		""" a dict to hold either energy scandefs or other spatial region scandefs,  """
		self._filename = None
		self._filenames = []
		self._fprefix = None
		""" string"""
		self._startX = None
		""" int"""
		self._stopX = None
		""" float"""
		
# 		self._offsetX = 0.0 
# 		""" float that is used to be the absolute offset so scan can be set to 
# 			a particular sample position (1 of possible 6), this offset then allows
# 			the ROI selections to be absolute to thie offset, so for instance if this
# 			scan was set to sample holder position 5:
# 				then (from stxmMain.ini) the offsetX would be -5000 and offsetY would be 0, 
# 				and startX and stopX etc would be relative to these offsets
# 		"""
# 		self._offsetY = 0.0 
# 		""" float that is used to be the absolute offset so scan can be set to 
# 			a particular sample position (1 of possible 6), this offset then allows
# 			the ROI selections to be absolute to thie offset, so for instance if this
# 			scan was set to sample holder position 5:
# 				then (from stxmMain.ini) the offsetX would be -5000 and offsetY would be 0, 
# 				and startX and stopX etc would be relative to these offsets
# 		"""

		
		self._startY = None
		""" float"""
		self._stopY = None
		""" float"""
		self._stepX = None
		""" float"""
		self._stepY = None
		""" float"""
		self._npointsX = None
		""" int"""
		self._npointsY = None
		""" int"""
		self._dwell = None
		""" float"""
		self._xPositioner = None
		""" stxm_control.positioners.IPositioner"""
		self._yPositioner = None
		""" stxm_control.positioners.IPositioner"""
		self._evPositioner = None
		""" stxm_control.positioners.IPositioner"""
		self._counterList = []
		""" stxm_control.counters.ICounter"""
		self._gate = None
		""" stxm_control.counters.IClkGenerator"""
		self._shutter = None
		
		#self._energy = None
		#self._polarity = None
		
		self._scan_data = None
		self.scan_progress = 0
		
		
		self._flags = None		
	
	
# 	def get_offsetX(self):
# 		return(self._offsetX)
# 	
# 	def set_offsetX(self, offset):
# 		self._offsetX = offset
# 
# 	def get_offsetY(self):
# 		return(self._offsetY)
# 	
# 	def set_offsetY(self, offset):
# 		self._offsetY = offset
	
# 	def __getattr__(self, attr):
# 		" internal method "
# 		if attr in self._attrs:
# 			return self._attrs[attr]
# 		elif attr in self.__dict__: 
# 			return self.__dict__[attr]
# 		else:
# 			pass
# 			#return self._pvs[attr]
# 				
# 	def __setattr__(self, attr, val):
# 		# print 'SET ATTR ', attr, val
# 		if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
# 					'_attrs', '_nonpvs', '_extra', '_callbacks'):
# 			self.__dict__[attr] = val
# 			return 
# 		if attr in self._attrs:
# 			self._attrs[attr] = val
# 		elif attr in self.__dict__: 
# 			self.__dict__[attr] = val		   
# 		elif self._init:
# 			pass
		
	def get_mode(self):
		return(self._mode)
	
	def set_mode(self, mode=ScanMode.PREVIEW):
		self._mode = mode
	
	def set_mode_to_preview(self):
		self._mode = ScanMode.PREVIEW
	
	def set_mode_to_data(self):
		self._mode = ScanMode.DATA 
	
	def get_sample_position(self):
		return(self._sample_position)
	
	def set_sample_position(self, pos):
		""" valid numbers are 1 - 6 """
		self._sample_position = pos
	
	def get_ev_regions(self):
		return(self._ev_regions)
	
	def get_ev_region(self, scan_id):
		for ev_reg in self._ev_regions:
			if(ev_reg.scan_id == scan_id):
				return(ev_reg)
		return(None)
	
	def add_ev_region(self, ev_reg):
		""" add a scandef (energy or spatial) to the dict of children, the key is the scan_id """ 
		self._ev_regions.append(ev_reg)
	
	def remove_ev_region(self, scan):
		for s in self._ev_regions:
			if(s.scan_id == scan.scan_id):
				self._ev_regions.remove(s)
	
	def set_filename(self, fname):
		self._filename = fname
	
	def get_filename(self):
		#return(self._filename)
		return(self._filenames[0])
	
	def init_data_filesystem(self, baseDir, scan_sequence, fileSeqStart, num_files=1):
		self.set_scan_seq_id(scan_sequence)
		dct = self.gen_scan_resources(baseDir, self.scan_seq_id, fileSeqStart, num_files=num_files)
		self._filenames = copy.deepcopy(dct['filename_list'])
		self._dir = dct['basedir']
		self._datadir = dct['datadir']
		self._fprefix = dct['prefix']
		self.set_scan_name(self._fprefix)
		#self.make_a_dir(self._dir)
		#self.make_proj_subdirs()
		
	
	def gen_name_prefix(self):
		""" the name is AYYMMDD### where ### is a 3 digit sequence number """
		# take only last to chars of Year
		year = datetime.utcnow().strftime('%Y')[2:]
		monthDay = datetime.utcnow().strftime('%m%d')
		prefix = 'A' + year + monthDay 
		return(prefix)


	def gen_sequenced_filename(self, filename, seqNum, num_files=1):
		""" the data filename is YYMMDDxxxx.hdr where xxx is a sequenced number """
		# cnt = filename.count('#')
		cnt = 4
		fnamelist = []
		for seq in range(seqNum, seqNum + num_files):
			# create format string ex: '%03d'
			frmt = n = filename + '_' + '%' + r'0%d' % (cnt) + 'd'
			# now sub in the scan number
			fname = frmt % seq
			fnamelist.append(fname)
		   
		return(fnamelist)
	
		
	def gen_scan_resources(self, baseDir, seq_num, fseqNum, num_files=1):
		""" generate the dirname and filename, create the directory if it doesnt exist
		and return the prefix, dirname and filename.
		Args:
		baseDir = the base data directory which is the parent of the generated directory name
		dseqNum = the directory sequence number, the directory name is based on %YYMMDD#### where #### is a sequence number
		fseqNum = the filename starting sequence number
		num_files=1 the number of filenames to generate, this will determine the relative end of the sequence (end number = fseqNum + num+files)
		
		""" 
		result = {}
		for i in range(9999):
			prefix = self.gen_name_prefix() + '%d' % i
			# fn = gen_filename(prefix)
			
			data_dir = baseDir + '/' + prefix + '/'
			
			if os.path.exists(data_dir):
				pass
				# that sequence number already exists so try next one
			else:
				# use this one
				os.mkdir(data_dir)
				break
		
		if(self._mode == ScanMode.PREVIEW):
			for j in range(9999):
				#pos_string = 'pos%d' % (self.get_sample_position() + 1)
				fprefix = 'prev%d_%02d' % (self.get_sample_position() + 1, j)
				#preview_file = base_dir + '\\' + pos_string + '\\' + fprefix + '.json'
				preview_file = data_dir + fprefix + '.json'
				if os.path.exists(preview_file):
					pass
					# that sequence number already exists so try next one
				else:
					#use this fprefix
					break
		else:
			fprefix = prefix
		
		fnamelist = self.gen_sequenced_filename(fprefix, fseqNum, num_files)
		result['prefix'] = fprefix
		result['basedir'] = baseDir
		result['filename_list'] = fnamelist
		#datadir = base_dir + '\\pos%d' % self.get_sample_position()
		result['datadir'] = data_dir
		
		return(result)

	
	def make_data_dir(self):
		if os.path.exists(self._dir):
			print('data dir [%s] already exists' % self._dir)
			#that sequence number already exists so try next one
		else:
			#use this one
			os.mkdir(self._dir)

	def make_a_dir(self, dirname):
		""" a func to make a dir if it doesnt exist """
		if not os.path.exists(dirname):
			os.mkdir(dirname)
		

	def set_scan_seq_id(self, sequence_num):
		""" this holds a sequence val so that scan prefix's can easily distinguish instances of scans """
		self.scan_seq_id = sequence_num
	
	def get_scan_seq_id(self):
		return(self.scan_seq_id)
	
	def get_scan_name(self):
		return(self._name)

	def set_scan_name(self, aName):
		self._name = aName	

	def get_scan_filename_list(self):
		return(self._filenames)

	def get_scan_dir(self):
		return(self._dir)
	
	def get_scandata_dir(self):
		return(self._datadir)
	
	def get_scan_prefix(self):
		return(self._fprefix)
		
	def get_scan_type(self):
		return(self._type)
	
	def set_scan_type(self, aType):
		self._type = aType
		
	def get_counter(self, idx):
		try:
			if(idx in range(0,len(self._counterList))):
				return(self._counterList[idx])
		except IndexError:
			s = "Index[%d] error in counter list" % idx
			raise ScanDefError(s)

	def add_counter(self, aCounter):  
		counter = ICounter(aCounter)
		self._counterList.append(counter)  		

	def set_gate(self, aGate):
		gate = IClkGenerator(aGate)
		self._gate = gate  	
	
	def get_gate(self):
		return(self._gate)	

	def set_shutter(self, aShutter):
		shutter = IShutter(aShutter)
		self._shutter = shutter  	
	
	def get_shutter(self):
		return(self._shutter)	


	def set_startX(self, aStartX):
		"""@ParamType aStartX int"""
		self._startX = float(aStartX)

	
	def get_startX(self):
		"""@ReturnType int"""
		return self._startX

	
	def set_stopX(self, aStopX):
		"""@ParamType aStopX float"""
		self._stopX = float(aStopX)

	
	def get_stopX(self):
		"""@ReturnType float"""
		return self._stopX

	
	def set_startY(self, aStartY):
		"""@ParamType aStartY float"""
		self._startY = float(aStartY)

	
	def get_startY(self):
		"""@ReturnType float"""
		return self._startY

	
	def set_stopY(self, aStopY):
		"""@ParamType aStopY float"""
		self._stopY = float(aStopY)

	
	def get_stopY(self):
		"""@ReturnType float"""
		return self._stopY

	
	def set_stepX(self, aStepX):
		"""@ParamType aStep float"""
		self._stepX = float(aStepX)

	
	def get_stepX(self):
		"""@ReturnType float"""
		return self._stepX
	
	def set_stepY(self, aStepY):
		"""@ParamType aStep float"""
		self._stepY = float(aStepY)

	
	def get_stepY(self):
		"""@ReturnType float"""
		return self._stepY

	
	def set_NpointsX(self, aNpointsX):
		"""@ParamType aNpoints int"""
		self._npointsX = int(aNpointsX)

	
	def get_NpointsX(self):
		"""@ReturnType int"""
		return self._npointsX


	def set_NpointsY(self, aNpointsY):
		"""@ParamType aNpoints int"""
		self._npointsY = int(aNpointsY)

	
	def get_NpointsY(self):
		"""@ReturnType int"""
		return self._npointsY
	
	def get_scan_data(self):
		return self._scan_data
	
	def set_scan_data(self, scan_data):
		self._scan_data = scan_data
	
	

###############################################################
############## Motor Positioner methods ########################	
	def set_X_positioner(self, aXPositioner):
		"""@ParamType aXPositioner stxm_control.positioners.IPositioner"""
		self._xPositioner = aXPositioner

	
	def get_X_positioner(self):
		"""@ReturnType stxm_control.positioners.IPositioner"""
		return self._xPositioner

	
	def set_Y_positioner(self, aYPositioner):
		"""@ParamType aYPositioner stxm_control.positioners.IPositioner"""
		self._yPositioner = aYPositioner

	
	def get_Y_positioner(self):
		"""@ReturnType stxm_control.positioners.IPositioner"""
		return self._yPositioner
	
	def set_Energy_positioner(self, aPositioner):
		"""@ParamType aYPositioner stxm_control.positioners.IPositioner"""
		self._evPositioner = aPositioner

	def get_Energy_positioner(self):
		"""@ReturnType stxm_control.positioners.IPositioner"""
		return self._evPositioner
	
##############################################################################
############# FLAGS ##########################################################	
	def set_scan_flags(self, aFlags):
		self._flags = aFlags
	
	def get_scan_flags(self):
		return self._flags
	
	


class BaseRegionDef(object):
	"""
	This class represents a base region definition
	"""
	def __init__(self, center=0.0, rng=0.0, step=None, npoints=None):
		super(BaseRegionDef, self).__init__()
		
		self._name = ''
		self._center = center
		self._range = rng
		self._start = self.calc_start()
		self._stop = self.calc_stop()
		self._step = step
		self._npoints = npoints
		#if False then calc using steps first
		self._npnts_haspriority = True
 		
		self.gen_setpoints()
		
		if(step is None and npoints is None):
			s = 'BaseRegionDef: must specify step size or number of points'
			raise ScanDefError(s)
		if(step is None):
			self._step = self._step_calc(self._start, self._stop, self._npoints)
		else:
			self._npoints = self._npoints_calc(self._start, self._stop, self._step)
	
	
	def get_scan_name(self):
		return(self._name)
	
	def set_scan_name(self, aName):
		self._name = aName	
	
	def _step_calc(self, start, stop, npoints):
		if(npoints < 1):
			npoints = 1
		step = (stop - start) / npoints
		return(step)
	
	def _npoints_calc(self, start, stop, step):
		if(step < 1):
			step = 1.0
		npoints = int((stop - start) / step)
		return(npoints)
	
	def recalc_step(self):
		self._step = self._step_calc(self._start, self._stop, self._npoints)
		#return(steps)
	
	def recalc_npoints(self):
		self._npoints = int(self._npoints_calc(self._start, self._stop, self._step))
		#return(npoints)
		
	def get_range(self):
		return(self._range)
	
	def get_center(self):
		return(self._center)
	
	def get_start(self):
		return(self._start)
	
	def get_stop(self):
		return(self._stop)
	
	def calc_start(self):
		self._start = self._center - (0.5 * self._range)
		return(self._start)
	
	def calc_stop(self):
		self._stop = self._center + (0.5 * self._range)
		return(self._stop)
	
	def set_calc_priority(self, calc_using_points = True):
		self._npnts_haspriority = calc_using_points
	
	def recalc(self):
		""" force reclac of parameters for scan """
		if(self._npnts_haspriority):
			#self.recalc_npoints()
			self.calc_start()
			self.calc_stop()
			self.recalc_step()
		else:
			#self.recalc_step()
			self.calc_start()
			self.calc_stop()
			self.recalc_npoints()
		self.gen_setpoints()
		
	def gen_setpoints(self):
		#self._setpoints = np.linspace(self._start, self._stop, self._npoints)
		#we must remember that because the beam is stationary we need to move the sample relative to this
		#stationary position. Movement to the sample positions therefore is inverted
		self._setpoints = np.linspace(self._stop, self._start, self._npoints)


	def set_center(self, aCenter, recalc=True):
		"""@ParamType aCenter int"""
		self._center = float(aCenter)
		if(recalc):
			self.recalc()
	
	def set_range(self, aRange, recalc=True):
		"""@ParamType aRange int"""
		self._range = float(aRange)
		if(recalc):
			self.recalc()
	
				
	def set_start(self, aStart, recalc=True):
		"""@ParamType aStart int"""
		self._start = float(aStart)
		if(recalc):
			self.recalc()

	def set_stop(self, aStop, recalc=True):
		"""@ParamType aStop float"""
		self._stop = float(aStop)
		if(recalc):
			self.recalc()

	def get_step(self):
		"""@ReturnType float"""
		return self._step
	
	def set_step(self, aStep, recalc=True):
		"""@ParamType aStep float"""
		self._step = float(aStep)
		if(recalc):
			self.set_calc_priority(calc_using_points = False)
			self.recalc()
	
	def set_Npoints(self, aNpoints, recalc=True):
		"""@ParamType aNpoints int"""
		self._npoints = int(aNpoints)
		if(recalc):
			self.set_calc_priority(calc_using_points = True)
			self.recalc()
	
	def get_Npoints(self):
		"""@ReturnType int"""
		return self._npoints
	
	def get_setpoints(self):
		return(self._setpoints)


class EPUPolarity(object):
	
	def __init__(self, polarity, offset):
		self._enabled = False
		self._polarity = polarity
		self._offset = offset
	
	def set_enabled(self, enable):
		self._enabled = enable
	
	def is_enabled(self):
		return(self._enabled)	
	
	def get_polarity(self):
		return(self._polarity)
	
	def get_offset(self):
		return(self._offset)
	
	def set_polarity(self, polarity):
		self._polarity = polarity
		
	def set_offset(self,offset):
		self._offset = offset
	

class EnergyRegionScanDef(BaseRegionDef):
	def __init__(self, ev_id, center=0.0, rng=0.0, step=None, npoints=None, dwell=2.0, xmcd=False):
		BaseRegionDef.__init__(self, center=center, rng=rng, step=step, npoints=npoints)
		#set flag to enable to disable xmcd
		self.scan_id = ev_id
		self._xmcd = xmcd
		self._pol1 = EPUPolarity(-1, -0.01)
		self._pol2 = EPUPolarity(1, 0.04)
		self._dwell = dwell #in ms
		if(xmcd):
			self._pol1.set_enabled(True)
			self._pol2.set_enabled(True)
			
		self.modelIface = {}
		
		# create a dict in the order you want the columns to appear in the table view
		# because the model view code fires events and passes column idx's
		# fromt eh tablemodel then I can get/set any of these parameters by calling:
		#	scan.modelIface[0]['get']()
		#	scan.modelIface[1]['get']()
		#	scan.modelIface[1]['set'](55.235)
		#hdrList = ['ID','Center', 'Range', 'Step', 'Points', 'Dwell', 'Pol1', 'Pol2', 'Off1', 'Off2', 'XMCD']
		self.modelIface[0] = {'hdr_str': 'ID', 'get' : self.get_ev_id, 'set' : None } 
		self.modelIface[1] = {'hdr_str': 'Center', 'get' : self.get_center, 'set' : self.set_center }
		self.modelIface[2] = {'hdr_str': 'Range', 'get' : self.get_range, 'set' : self.set_range }
		self.modelIface[3] = {'hdr_str': 'Step', 'get' : self.get_step, 'set' : self.set_step }
		self.modelIface[4] = {'hdr_str': 'Points', 'get' : self.get_Npoints, 'set' : self.set_Npoints }
		self.modelIface[5] = {'hdr_str': 'Dwell', 'get' : self.get_dwell, 'set' : self.set_dwell }
		
		self.modelIface[6] = {'hdr_str': 'Pol1', 'get' : self.get_pol1, 'set' : self.set_pol1 }
		self.modelIface[7] = {'hdr_str': 'Pol2', 'get' : self.get_pol2, 'set' : self.set_pol2 }
		self.modelIface[8] = {'hdr_str': 'Off1', 'get' : self.get_off1, 'set' : self.set_off1 }
		self.modelIface[9] = {'hdr_str': 'Off2', 'get' : self.get_off2, 'set' : self.set_off2 }
		self.modelIface[10] = {'hdr_str': 'XMCD', 'get' : self.get_xmcd, 'set' : self.set_xmcd }
				
# 		self.callFunc = {}
# 		self.callFunc['get_scan_name'] = self.get_scan_name
# 		self.callFunc['get_setpoints'] = self.get_setpoints
# 		self.callFunc['get_center'] = self.get_center
# 		self.callFunc['get_range'] = self.get_range
# 		
# 		self.callFunc['get_start'] = self.get_start  
# 		self.callFunc['get_stop'] = self.get_stop   
# 		self.callFunc['get_step'] = self.get_step   
# 		self.callFunc['get_Npoints'] = self.get_Npoints
# 		self.callFunc['get_pol1'] = self.get_pol1
# 		self.callFunc['get_pol2'] = self.get_pol2
# 		self.callFunc['get_off1'] = self.get_off1
# 		self.callFunc['get_off2'] = self.get_off2
# 		self.callFunc['get_xmcd'] = self.get_xmcd
# 		self.callFunc['get_dwell'] = self.get_dwell
# 		self.callFunc['get_ev_id'] = self.get_ev_id
# 			
# 		self.callFunc['set_scan_name'] = self.set_scan_name
# 		self.callFunc['set_start'] = self.set_start  
# 		self.callFunc['set_stop'] = self.set_stop   
# 		self.callFunc['set_step'] = self.set_step   
# 		self.callFunc['set_Npoints'] = self.set_Npoints
# 		self.callFunc['set_pol1'] = self.set_pol1
# 		self.callFunc['set_pol2'] = self.set_pol2
# 		self.callFunc['set_off1'] = self.set_off1
# 		self.callFunc['set_off2'] = self.set_off2
# 		self.callFunc['set_xmcd'] = self.set_xmcd
# 		self.callFunc['set_dwell'] = self.set_dwell
# 		self.callFunc['set_ev_id'] = self.set_ev_id
			
	def set_ev_id(self, id):
		self.scan_id = id
		
	def get_ev_id(self):
		return(self.scan_id)
	
	#convienience functions
	def get_pol1(self):
		return(self.get_polarity('pol1'))
	def get_pol2(self):
		return(self.get_polarity('pol2'))
	def get_off1(self):
		return(self.get_offset('pol1'))
	def get_off2(self):
		return(self.get_offset('pol2'))
			
	def set_pol1(self, val):
		return(self.set_polarity('pol1', val))
	def set_pol2(self, val):
		return(self.set_polarity('pol2', val))
	def set_off1(self, val):
		return(self.set_offset('pol1', val))
	def set_off2(self, val):
		return(self.set_offset('pol2', val))
	
	
	def set_dwell(self, aDwell):
		"""@ParamType aDwell """
		self._dwell = float(aDwell) 
	
	def get_dwell(self):
		"""@ReturnType float"""
		return self._dwell
	
	def get_polarity(self, polname='pol1'):
		if(polname == 'pol1'):
			return(self._pol1.get_polarity())
		elif(polname == 'pol2'):
			return(self._pol2.get_polarity())
		else:
			print('EnergyRegionScanDef: get_polarity: polname [%s] does not exist' % polname)
			return(None)
	
	def get_offset(self, polname='pol1'):
		if(polname == 'pol1'):
			return(self._pol1.get_offset())
		elif(polname == 'pol2'):
			return(self._pol2.get_offset())
		else:
			print('EnergyRegionScanDef: get_offset: polname [%s] does not exist' % polname)
			return(None)
	
	def set_polarity(self, polname, polarity):
		if(polname == 'pol1'):
			self._pol1.set_polarity(polarity)
		elif(polname == 'pol2'):
			self._pol2.set_polarity(polarity)
		else:
			print('EnergyRegionScanDef: set_polarity: polname [%s] does not exist' % polname)
			return(None)
	
	def set_offset(self, polname, offset):
		if(polname == 'pol1'):
			self._pol1.set_offset(offset)
		elif(polname == 'pol2'):
			self._pol2.set_offset(offset)
		else:
			print('EnergyRegionScanDef: set_offset: polname [%s] does not exist' % polname)
			return(None)
		
	def get_xmcd(self):
		return(self._xmcd)
	
	def set_xmcd(self, do_xmcd):
		self._xmcd = do_xmcd




# class BaseScanEngine(BaseDevice):
# 	'''
# 	BaseScanEngine is an abstraction of the SSCAN record which is the current scan engine implementation, this may change
# 	in the future so I want a layer in between use and implementation and this is it
# 	'''
# 	sig_done = QtCore.pyqtSignal(int)
# 	sig_counts = QtCore.pyqtSignal(int)
# 	sig_status = QtCore.pyqtSignal(int, str)
#
# 	def __init__(self, scan_pvname, scan_num, scan_type, npoints, parent=None):
# 		super(BaseScanEngine, self).__init__()
# 		self.scan_prefix = scan_pvname
# 		self.scan_num = scan_num
# 		self.scan_type = scan_type
# 		self.scan_name = self.scan_prefix + ':scan%d' % scan_num
# 		self.num_points = npoints
# 		self.cur_counts = 0
#
# 		#Enum('READY','BUSY','ABORTING','PAUSED','ERROR')
# 		self.status = ScanStatus.READY
#
# 		self.scanPause = self.add_pv(self.scan_prefix + ':scanPause.VAL')	 # [Go, Pause]
# 		self.scanResumeSEQ_DLY1 = self.add_pv(self.scan_prefix + ':scanResumeSEQ.DLY1')	 # delay resume (float) [1.0]
# 		self.AbortScans_PROC = self.add_pv(self.scan_prefix + ':AbortScans.PROC')	 # abort the scan
#
# 		self.scn = Scan(scan_pvname + ':scan%d' % scan_num)
# 		self.scn.put('NPTS', self.num_points)
#
# 		self.SMSG.changed.connect(self.on_scan_status)
# 		self.FAZE.changed.connect(self.on_faze)
# 		time.sleep(0.3)
#
# 		self.setup_scan()
#
# 	def setup_before_scan(self, bs_pv, bs_val):
# 		""" configure before scan fields
# 		"""
# 		self.scn.put('BSPV', bs_pv) 	# Before scan PV
# 		self.scn.put('BSCD', bs_val) 	# Before scan VAL
#
# 	def check_pos_id(self, pos_id):
# 		if(pos_id > 4):
# 			pos_id = 4
# 		if(pos_id < 1):
# 			pos_id = 1
# 		return(pos_id)
#
# 	def check_mode(self, mode):
# 		if(mode > 2):
# 			mode = 2
# 		if(mode < 0):
# 			mode = 0
# 		return(mode)
#
# 	def check_after_scan_mode(self, mode):
# 		if(mode > 7):
# 			mode = 7
# 		if(mode < 0):
# 			mode = 0
# 		return(mode)
#
# 	def setup_positioner_pv(self, pos_idx, pos_pv):
# 		""" set positioner x pv of sscan record, min is 1 max is 4
# 		"""
# 		pos_str = 'P%dPV' % self.check_pos_id(pos_idx)
# 		self.scn.put(pos_str, pos_pv) 	# Before scan PV
#
# 	def setup_positioner_params(self, pos_idx, start, stop):
# 		""" set move parameters for positioner x, these are the Start, End parameters, the step size and width are calc automatically
# 		by sscan rec
# 		"""
# 		id = self.check_pos_id(pos_idx)
# 		pXsp = 'P%dSP' % id
# 		pXep = 'P%dEP' % id
# 		self.scn.put(pXsp, start) 	# start position
# 		self.scn.put(pXep, stop) 	# end position
#
# 	def setup_scan_mode(self, mode=0):
# 		"""
# 		0 = Linear
# 		1 = Table
# 		2 = Fly
# 		"""
# 		m = self.check_mode(mode)
# 		self.scn.put('P1SM', m)
#
# 	def setup_after_scan(self, mode=0):
# 		"""
# 		0 = Stay
# 		1 = Start_Pos
# 		2 = Prior_Pos
# 		3 = Peak_Pos
# 		4 = Valley_Pos
# 		5 = +Edge_Pos
# 		6 = -Edge_Pos
# 		7 = CNTR_Of_MAss
# 		"""
# 		m = self.check_after_scan_mode(mode)
# 		self.scn.put('PASM', m)
#
#
# 	def setup_positioner_settle_time(self, delay):
# 		""" this delay occurs after the positioners have all moved to their next positions and stopped
# 		"""
# 		self.scn.put('PDLY', delay)
#
# 	def setup_detector_settle_time(self, delay):
# 		""" this delay occurs after the positioners have all moved to their next positions and stopped
# 		"""
# 		self.scn.put('DDLY', delay)
#
# 	def setup_detector_trigger(self, pos_idx, det_pv, det_val):
# 		""" set move parameters for detector trigger x, the value in det_val will be pushed to the det_pv each iteration of this scan
# 		after the positioners have all reported completed of their next move
# 		"""
# 		id = self.check_pos_id(pos_idx)
# 		tXpv = 'T%dPV' % id
# 		tXcd = 'T%dCD' % id
# 		self.scn.put(tXpv, det_pv) 	# detector trigger pv
# 		self.scn.put(tXcd, det_val) # detector trigger val
#
# 	def link_to_inner_scan(self, inner_scan):
# 		"""
# 		create s a link to an inner loop scan so that the inner_scan will execute for each iteration of this scan
#
# 		"""
# 		self.setup_detector_trigger(1, inner_scan + '.EXSC')
# 		self.setup_detector_trigger(2, inner_scan + '.WAIT')
#
#
# 	def setup_scan(self):
# 		""" setup scan: to be implemented by inheriting class"""
# 		pass
#
# 	def load_table_points(self, pos_idx, arr):
# 		""" load an array of setpoints to a table:
# 		ex: 'P2PA'
# 		"""
# 		id = self.check_pos_id(pos_idx)
# 		posner = 'P%dPA' % id
# 		self.scn.put(posner, arr)
#
# 	def on_scan_status(self, msg):
# 		self.status.emit(self.status ,msg)
# 		#print '[%s]: SMSG:  %s' % (self.scan_name, msg)
# 		#_logger.info('[%s]: SMSG:  %s' % (self.scan_name, msg))
#
# 	def on_faze(self, faze):
# 		self.cur_counts = self.scn.get('CPT')
# 		self.sig_counts.emit(self.cur_counts)
# 		pass
# #
# # 		print '[%s]: FAZE:  %s' % (self.scan_name, faze)
# # 		if((faze == 0) and (cur_counts >= self.num_points)):
# # 			self.done.emit(1)
# # 		else:
# # 			self.done.emit(0)
# #
# # 		pass
#
# 	def start(self):
# 		self.status = ScanStatus.BUSY
# 		self.scn.put('EXSC', 1)
#
#
# 	def stop(self):
# 		self.status = ScanStatus.ABORTING
# 		self.AbortScans_PROC.put(1)
#
# 	def pause(self):
# 		self.status = ScanStatus.PAUSED
# 		self.scanPause.put(1)
#
# 	def unpause(self):
# 		self.status = ScanStatus.BUSY
# 		self.scanPause.put(0)
#
	
class BaseScanDef(ScanDef):
	"""for a basic scan def"""
	
	def __init__(self, scan_type, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1, dwell=1.0, evRegion=None):
		super(BaseScanDef, self).__init__()
		self.scan_id = uniqueid()
		
		self._type = scan_type
		self._filename = None
		self._regionX = BaseRegionDef(startX, stopX, stepX, npointsX)
		self._regionY = BaseRegionDef(startY, stopY, stepY, npointsY)
		
		self._startX = self._regionX.get_start() 
		self._stopX = self._regionX.get_stop()
		self._startY = self._regionY.get_start()
		self._stopY = self._regionY.get_stop()
		
		self._stepX = self._regionX.get_step() 
		self._stepY = self._regionY.get_step()
		self._npointsX = self._regionX.get_Npoints()
		self._npointsY = self._regionY.get_Npoints()
		
	
		self._progress = 0
		self._status = ScanStatus.READY

		
		self._plotterList = []
		
		#put getters and setters into a list that will be accessed by the TableView
		self.get = []
		
		self.get.append(self.get_scan_name)
		#self.get.append(self.get_scan_type)
		self.get.append(self._regionX.get_start)
		self.get.append(self._regionX.get_stop)
		self.get.append(self._regionY.get_start)
		self.get.append(self._regionY.get_stop)
		self.get.append(self._regionX.get_step)
		self.get.append(self._regionY.get_step)
		self.get.append(self._regionX.get_Npoints)
		self.get.append(self._regionY.get_Npoints)
		
		
		self.set = []
		#self.set.append(self.set_scan_name)
		self.set.append(self._regionX.set_start)
		self.set.append(self._regionX.set_stop)
		self.set.append(self._regionY.set_start)
		self.set.append(self._regionY.set_stop)
		self.set.append(self._regionX.set_step)
		self.set.append(self._regionY.set_step)
		self.set.append(self._regionX.set_Npoints)
		self.set.append(self._regionY.set_Npoints)
		
		#overide getters and setters
		self.set_startX = self._regionX.set_start 
		self.set_stopX = self._regionX.set_stop
		self.set_startY = self._regionY.set_start 
		self.set_stopY = self._regionY.set_stop
		self.set_NpointsX = self._regionX.set_Npoints
		self.set_NpointsY = self._regionY.set_Npoints
		self.set_stepX = self._regionX.set_step
		self.set_stepY = self._regionY.set_step
		
		self.get_startX = self._regionX.get_start 
		self.get_stopX = self._regionX.get_stop
		self.get_startY = self._regionY.get_start 
		self.get_stopY = self._regionY.get_stop
		self.get_NpointsX = self._regionX.get_Npoints
		self.get_NpointsY = self._regionY.get_Npoints
		self.get_stepX = self._regionX.get_step
		self.get_stepY = self._regionY.get_step
		self.get_setpointsX = self._regionX.get_setpoints
		self.get_setpointsY = self._regionY.get_setpoints
		self.get_centerX = self._regionX.get_center
		self.get_rangeX = self._regionX.get_range		
		self.get_centerY = self._regionY.get_center
		self.get_rangeY = self._regionY.get_range		
		

		self.callFunc = {}
		#add getters
		self.callFunc['get_scan_name'] = self.get_scan_name
		self.callFunc['get_scan_type'] = self.get_scan_type
		self.callFunc['get_startX'] = self._regionX.get_start       
		self.callFunc['get_stopX'] =  self._regionX.get_stop    
		self.callFunc['get_startY'] = self._regionY.get_start   
		self.callFunc['get_stopY'] =  self._regionY.get_stop    
		self.callFunc['get_stepX'] =  self._regionX.get_step    
		self.callFunc['get_stepY'] =  self._regionY.get_step    
		self.callFunc['get_NpointsX'] = self._regionX.get_Npoints 
		self.callFunc['get_NpointsY'] = self._regionY.get_Npoints 
		self.callFunc['get_centerX'] = self._regionX.get_center
		self.callFunc['get_rangeX'] = self._regionX.get_range		
		self.callFunc['get_centerY'] = self._regionY.get_center
		self.callFunc['get_rangeY'] = self._regionY.get_range		


		#add setters		
		#self.callFunc['set_scan_name'] = self.set_scan_name		
		self.callFunc['set_scan_type'] = self.set_scan_type
		self.callFunc['set_startX'] = self._regionX.set_start       
		self.callFunc['set_stopX'] =  self._regionX.set_stop    
		self.callFunc['set_startY'] = self._regionY.set_start   
		self.callFunc['set_stopY'] =  self._regionY.set_stop    
		self.callFunc['set_stepX'] =  self._regionX.set_step    
		self.callFunc['set_stepY'] =  self._regionY.set_step    
		self.callFunc['set_NpointsX'] = self._regionX.set_Npoints 
		self.callFunc['set_NpointsY'] = self._regionY.set_Npoints 
		
		self.recalc()
	
	def recalc(self):
		self._regionX.recalc()
		self._regionY.recalc()
		
	def get_rangeX(self):
		return(self._regionX.get_range())
	
	def get_rangeY(self):
		return(self._regionY.get_range())
	
	def add_plotter(self, plotter):
		self._plotterList.append(plotter)
		
	def get_progress(self):
		return(self._progress)
	
	def set_progress(self, progress):
		self._progress = progress
		
	
	def set_ev_region(self, ev_id, start, stop, step, npoints, dwell, xmcd=False):
		"""
		Create an ev region instance and assign it
		"""
		#ev_reg = EnergyRegionScanDef(9999, start=energy, stop=energy, step=1, npoints=1, dwell=dwell, xmcd=False)
		ev_reg = EnergyRegionScanDef(ev_id, start, stop, step, npoints, dwell, xmcd=False)
		self.add_ev_region(ev_reg)
		
		
		
		
class BaseXScanDef(ScanDef):
	"""for a basic scan of a single positioner def"""
	done = QtCore.pyqtSignal(int)
	counts = QtCore.pyqtSignal(int)
	status = QtCore.pyqtSignal(int, str)
	
	def __init__(self, scan_type, centerX=0.0, rangeX=0.0, stepX=1, npointsX=1):
		super(BaseXScanDef, self).__init__()
		
		
		self._type = scan_type
		self._filename = None
		self._regionX = BaseRegionDef(centerX, rangeX, stepX, npointsX)
		
		self._centerX = centerX
		self._rangeX = rangeX
		self._startX = self._regionX.get_start() 
		self._stopX = self._regionX.get_stop()
		self._stepX = self._regionX.get_step() 
		self._npointsX = self._regionX.get_Npoints()

		self._progress = 0
		self._status = ScanStatus.READY
		
	
		self._plotterList = []
		
		#put getters and setters into a list that will be accessed by the TableView
		#need a cleaner way to do this
		self.get = []
		
		self.get.append(self.get_scan_name)
		#self.get.append(self.get_scan_type)
		self.get.append(self._regionX.get_start)
		self.get.append(self._regionX.get_stop)
		self.get.append(self._regionX.get_step)
		self.get.append(self._regionX.get_Npoints)
		
		
		self.set = []
		#self.set.append(self.set_scan_name)
		self.set.append(self._regionX.set_start)
		self.set.append(self._regionX.set_stop)
		self.set.append(self._regionX.set_step)
		self.set.append(self._regionX.set_Npoints)
		
		#overide getters and setters
		self.set_startX = self._regionX.set_start 
		self.set_stopX = self._regionX.set_stop
		self.set_NpointsX = self._regionX.set_Npoints
		self.set_stepX = self._regionX.set_step
		
		self.get_startX = self._regionX.get_start 
		self.get_stopX = self._regionX.get_stop
		self.get_NpointsX = self._regionX.get_Npoints
		self.get_stepX = self._regionX.get_step
		self.get_setpointsX = self._regionX.get_setpoints
		self.get_centerX = self._regionX.get_center
		self.get_rangeX = self._regionX.get_range		

		self.callFunc = {}
		#add getters
		self.callFunc['get_scan_name'] = self.get_scan_name
		self.callFunc['get_scan_type'] = self.get_scan_type
		self.callFunc['get_startX'] = self._regionX.get_start       
		self.callFunc['get_stopX'] =  self._regionX.get_stop    
		self.callFunc['get_stepX'] =  self._regionX.get_step    
		self.callFunc['get_NpointsX'] = self._regionX.get_Npoints 
		self.callFunc['get_centerX'] = self._regionX.get_center
		self.callFunc['get_rangeX'] = self._regionX.get_range		


		#add setters		
		#self.callFunc['set_scan_name'] = self.set_scan_name		
		self.callFunc['set_scan_type'] = self.set_scan_type
		self.callFunc['set_startX'] = self._regionX.set_start       
		self.callFunc['set_stopX'] =  self._regionX.set_stop    
		self.callFunc['set_stepX'] =  self._regionX.set_step    
		self.callFunc['set_NpointsX'] = self._regionX.set_Npoints 
		
		self.recalc()
	
	def recalc(self):
		self._regionX.recalc()
		
	def get_rangeX(self):
		return(self._regionX.get_range())
	
	def add_plotter(self, plotter):
		self._plotterList.append(plotter)
		
	def get_progress(self):
		return(self._progress)
	
	def set_progress(self, progress):
		self._progress = progress
		
	
		
class BaseXYScanDef(ScanDef):
	"""for a basic X Y scan def"""
	
	#def __init__(self, scan_type, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1, dwell=1.0, evRegion=None):
	def __init__(self, scan_type, centerX=0.0, centerY=0.0, rngX=0.0, rngY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1, dwell=1.0, evRegion=None):
	
		super(BaseXYScanDef, self).__init__()
		self.scan_id = uniqueid()
		
		self._type = scan_type
		self._filename = None
		
		self._regionX = BaseRegionDef(centerX, rngX, stepX, npointsX)
		self._regionY = BaseRegionDef(centerY, rngY, stepY, npointsY)
		
		self._startX = self._regionX.get_start() 
		self._stopX = self._regionX.get_stop()
		self._startY = self._regionY.get_start()
		self._stopY = self._regionY.get_stop()
		
		self._stepX = self._regionX.get_step() 
		self._stepY = self._regionY.get_step()
		self._npointsX = self._regionX.get_Npoints()
		self._npointsY = self._regionY.get_Npoints()
		
	
		self._progress = 0
		self._status = ScanStatus.READY

		
		self._plotterList = []
		
		#put getters and setters into a list that will be accessed by the TableView
#		self.get = []
		
		self.modelIface = {}
		
		# create a dict in the order you want the columns to appear in the table view
		# because the model view code fires events and passes column idx's
		# fromt eh tablemodel then I can get/set any of these parameters by calling:
		#	scan.modelIface[0]['get']()
		#	scan.modelIface[1]['get']()
		#	scan.modelIface[1]['set'](55.235)
		self.modelIface[0] = {'hdr_str': 'Type', 'get' : self.get_scan_name, 'set' : None } 
		self.modelIface[1] = {'hdr_str': 'CenterX', 'get' : self._regionX.get_center, 'set' : self._regionX.set_center }
		self.modelIface[2] = {'hdr_str': 'RangeX', 'get' : self._regionX.get_range, 'set' : self._regionX.set_range }
		self.modelIface[3] = {'hdr_str': 'CenterY', 'get' : self._regionY.get_center, 'set' : self._regionY.set_center }
		self.modelIface[4] = {'hdr_str': 'RangeY', 'get' : self._regionY.get_range, 'set' : self._regionY.set_range }
		self.modelIface[5] = {'hdr_str': 'StepX', 'get' : self._regionX.get_step, 'set' : self._regionX.set_step }
		self.modelIface[6] = {'hdr_str': 'StepY', 'get' : self._regionY.get_step, 'set' : self._regionY.set_step }
		self.modelIface[7] = {'hdr_str': 'PointsX', 'get' : self._regionX.get_Npoints, 'set' : self._regionX.set_Npoints }
		self.modelIface[8] = {'hdr_str': 'PointsY', 'get' : self._regionY.get_Npoints, 'set' : self._regionY.set_Npoints }
		
		self.recalc()
	
	def set_centerX(self, val):
		self._regionX.set_center(val)
	
	def set_centerY(self, val):
		self._regionY.set_center(val)
	
	def set_rangeX(self, val):
		self._regionX.set_range(val)
	
	def set_rangeY(self, val):
		self._regionY.set_range(val)
		
	def set_stepX(self, val):
		self._regionX.set_step(val)
	
	def set_stepY(self, val):
		self._regionY.set_step(val)
	
	def set_NpointsX(self, val):
		self._regionX.set_Npoints(val)
	
	def set_NpointsY(self, val):
		self._regionY.set_Npoints(val)
		
	
	def recalc(self):
		self._regionX.recalc()
		self._regionY.recalc()
		
	def get_rangeX(self):
		return(self._regionX.get_range())
	
	def get_rangeY(self):
		return(self._regionY.get_range())
	
	def add_plotter(self, plotter):
		self._plotterList.append(plotter)
		
	def get_progress(self):
		return(self._progress)
	
	def set_progress(self, progress):
		self._progress = progress
		
	
	def create_ev_region(self, ev_id, center, rng, step, npoints, dwell, xmcd=False):
		"""
		Create an ev region instance and assign it to base class, then return it to caller
		"""
		#ev_reg = EnergyRegionScanDef(9999, start=energy, stop=energy, step=1, npoints=1, dwell=dwell, xmcd=False)
		ev_reg = EnergyRegionScanDef(ev_id, center, rng, step, npoints, dwell, xmcd=False)
		#add it to teh base class list of ev regions
		self.add_ev_region(ev_reg)		
		return(ev_reg)

		


class ScanData(object):
	"""the object that is emitted during scan to all other objects, used by plotters, data recorders and the main GUI
	This data represents the typical data required by STXM raster scans
	"""
	def __init__(self, scan_id, scan_type):
		super(ScanData, self).__init__()

		self._scan_id = scan_id
		self._scan_type = scan_type
		self._row = None
		self._col = None
		self._yFbk = None
		self._xFbk = None
		self._data = None
		self._evFbk = None
		self._seqNum = None
		self._gapFbk = None
		self._polFbk = None
		self._polloffsetFbk = None
		self._dwell = None

	def get_scan_id(self):
		return self._scan_id
	def set_scan_id(self, scan_id):
		self._scan_id = scan_id
		
	def get_scan_type(self):
		return self._scan_type
	def set_scan_type(self, scan_type):
		self._scan_type = scan_type
		
	def get_row(self):
		return self._row
	def set_row(self, row):
		self._row = row

	def get_col(self):
		return self._col
	def set_col(self, col):
		self._col = col
	
	def get_yFbk(self):
		return self._yFbk
	def set_yFbk(self, yFbk):
		self._yFbk = yFbk
		
	def get_xFbk(self):
		return self._xFbk
	def set_xFbk(self, xFbk):
		self._xFbk = xFbk

	def get_data(self):
		return self._data
	def set_data(self, data):
		self._data = data

	def get_evFbk(self):
		return self._evFbk
	def set_evFbk(self, evFbk):
		self._evFbk = evFbk

	def get_seqNum(self):
		return self._seqNum
	def set_seq_id(self, seqNum):
		self._seqNum = seqNum

	def get_gapFbk(self):
		return self._gapFbk
	def set_gapFbk(self, gapFbk):
		self._gapFbk = gapFbk		
		
	def get_polFbk(self):
		return self._polFbk
	def set_polFbk(self, polFbk):
		self._polFbk = polFbk

	def get_polloffsetFbk(self):
		return self._polloffsetFbk
	def set_polloffsetFbk(self, polloffsetFbk):
		self._polloffsetFbk = polloffsetFbk	
		
	def get_dwell(self):
		return self._dwell
	
	def set_dwell(self, dwell):
		self._dwell = dwell	

		
class PointScanDef(BaseXYScanDef):
	#def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=None, npointsX=None, stepY=None, npointsY=None, dwell=1.0):
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		BaseXYScanDef.__init__(self,ScanType.POINT, startX=startX, stopX=startX, startY=startY, stopY=startY, stepX=1, npointsX=1, stepY=1, npointsY=1)
		self.set_scan_flags("Point Scan")
		

class LinePxPScanDef(BaseXYScanDef):
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		BaseXYScanDef.__init__(self,ScanType.LINEPXP, startX=startX, stopX=stopX, startY=startY, stopY=stopY, stepX=stepX, npointsX=npointsX, stepY=stepY, npointsY=npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("Line Pnt by Pnt")
		
class LineFullScanDef(BaseXYScanDef):
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		BaseXYScanDef.__init__(self,ScanType.LINEFULL, startX=startX, stopX=stopX, startY=startY, stopY=stopY, stepX=stepX, npointsX=npointsX, stepY=stepY, npointsY=npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("Line Full Scan")

class ImagePxPScanDef(BaseXYScanDef):
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		BaseXYScanDef.__init__(self,ScanType.IMAGEPXP, startX=startX, stopX=stopX, startY=startY, stopY=stopY, stepX=stepX, npointsX=npointsX, stepY=stepY, npointsY=npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("Image Stack")
		
class ImageLineUniScanDef(BaseXYScanDef):
	#def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
	def __init__(self, centerX=0.0, centerY=0.0, rngX=0.0, rngY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		#BaseXYScanDef.__init__(self,ScanType.IMAGELINEUNI, startX=startX, stopX=stopX, startY=startY, stopY=stopY, stepX=stepX, npointsX=npointsX, stepY=stepY, npointsY=npointsY)
		BaseXYScanDef.__init__(self,ScanType.IMAGELINEUNI, centerX=centerX, centerY=centerY, rngX=rngX, rngY=rngY, stepX=stepX, npointsX=npointsX, stepY=stepY, npointsY=npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("Image Stack")
		
		
class SampleImageScanDef(ImageLineUniScanDef):
	""" move teh sample x and y in a user defined grid, example is 250 x 250 um, 20 points x 20 points, 10 ms dwell
		a 2d image is produced. 
	"""
	#def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
	def __init__(self, centerX=0.0, centerY=0.0, rngX=0.0, rngY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		#ImageLineUniScanDef.__init__(self, startX, stopX, startY, stopY, stepX, npointsX, stepY, npointsY)
		ImageLineUniScanDef.__init__(self, centerX, centerY, rngX, rngY, stepX, npointsX, stepY, npointsY)

		self.set_scan_flags("ImageLinecan")
		self.set_X_positioner(DEVICE_CFG.device('SampleX'))
		self.set_Y_positioner(DEVICE_CFG.device('SampleY'))
		self.set_Energy_positioner(DEVICE_CFG.device('Energy'))
		self.set_shutter(DEVICE_CFG.device('Shutter'))



class SamplePreviewScanDef(ImageLineUniScanDef):
	""" move the sample x and y in a user defined grid, example is 250 x 250 um, 20 points x 20 points, 10 ms dwell
		a 2d image is produced. 
		
	"""
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		ImageLineUniScanDef.__init__(self, startX, stopX, startY, stopY, stepX, npointsX, stepY, npointsY)

		self.set_scan_flags("ImagePreviewScan")
		# set the positioners for this scan
		self.set_X_positioner(DEVICE_CFG.device('SampleX'))
		self.set_Y_positioner(DEVICE_CFG.device('SampleY'))
		self.set_Energy_positioner(DEVICE_CFG.device('Energy'))
		self.set_shutter(DEVICE_CFG.device('Shutter'))
		
		"""
		LINE_UNIDIR = 'Line-UniDir'
		LINE_BIDIR = 'Line-BiDir'
		LINE_PTBYPT = 'Line-PointByPoint'
		POINT = 'Point'
		"""
		
		#self.ev_scan_engine = BaseScanEngine("stxm1", 1, scan_type=LINE_UNIDIR, npointsX=)
		#self.pnt_scan_engine = BaseScanEngine("stxm1", 2, scan_type, npointsY)
		
		
	
	


class OSAScanDef(ImageLineUniScanDef):
	""" move OSA x and y in a user defined grid, example is 250 x 250 um, 20 points x 20 points, 10 ms dwell
		the i2d mage that is produced is a circle with a white center (this is ~"the" center of the OSA ) and is darker as you 
		move to the outer edges of the 2d image, the center of the circle is the desired OSA (x,y) position.
	"""
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		ImageLineUniScanDef.__init__(self, startX, stopX, startY, stopY, stepX, npointsX, stepY, npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("OSAScan")
		self.set_X_positioner(DEVICE_CFG.device('SampleX'))
		self.set_Y_positioner(DEVICE_CFG.device('SampleY'))
		self.set_Energy_positioner(DEVICE_CFG.device('Energy'))
		self.set_shutter(DEVICE_CFG.device('Shutter'))

class OSASFocuscanDef(LineFullScanDef):
	""" an OSA focus scan is a fixed horizontal line (usually across the boundaries of contrast on an OSA scan image) and this line is repeatedly
		scanned at a range of ZP Z values, this produces a 2d image that looks like a square made from 4 triangles, the center of the triangles is the
		desired ZP Z value where the image is most focused.
	""" 
	def __init__(self, startX=0.0, stopX=0.0, startY=0.0, stopY=0.0, stepX=1, npointsX=1, stepY=1, npointsY=1):
		LineFullScanDef.__init__(self,startX, stopX, startY, stopY, stepX, npointsX, stepY, npointsY)
		#just stubbed in, this needs to be fleshed out
		self.set_scan_flags("OSASFocuscan")
		self.set_X_positioner(DEVICE_CFG.device('ZonePlateX.X'))
		self.set_Y_positioner(DEVICE_CFG.device('ZonePlateZ.Z'))
		self.set_Energy_positioner(DEVICE_CFG.device('Energy'))
		self.set_shutter(DEVICE_CFG.device('Shutter'))
				




if __name__ == '__main__':
	import sys

	scans = [
		[PointScanDef(0.0, 50.0, 0.0, 50.0, stepX=0.25,npointsY=17, dwell=3.0)],
		[LinePxPScanDef(10.0, 60.0, 0.0, 50.0, stepX=0.50,npointsY=24, dwell=2.5)], 
		[LineFullScanDef(20.0, 70.0, 0.0, 50.0, stepX=0.35,npointsY=10, dwell=5.0)],
		[ImagePxPScanDef(30.0, 80.0, 0.0, 50.0, stepX=0.15,npointsY=20, dwell=7.0)],
		[ImageLineUniScanDef(40.0, 90.0, 0.0, 50.0, stepX=0.05,npointsY=30, dwell=4.0)] 
	] 


	
__all__ = ['ScanDef']	
