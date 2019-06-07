'''
Created on Nov 19, 2015

@author: bergr
'''

'''
Created on 2012-05-16

@author: bergr
'''
# BCM GLOBAL Settings for stxm
from . import init_qt
import os
import time
import copy
from PyQt5 import QtCore, QtGui, QtWidgets

#from twisted.python.components import globalRegistry

from bcm.settings import *
#from bcm.beamline.interfaces import IBeamline
from bcm.device.counter import SimCounter, DAQmxLineCounter, Counter, EpicsPv, EpicsPvCounter, BaseGate, BaseCounter, BaseDIO
from bcm.device.shutter import PvShutter
from bcm.device.valve import PvValve
#from bcm.device.drivers.stxmMotor.loadMtrConfig import StxmMotorConfig

#from epics.motor import Motor as apsMotor
from bcm.epics_devices_MOVED.motor_v2 import Motor_V2 as apsMotor
from bcm.epics_devices_MOVED.ai import ai

from bcm.epics_devices_MOVED.stxm_sample_mtr import sample_motor, sample_abstract_motor
from bcm.epics_devices_MOVED.mbbi import Mbbi
from bcm.epics_devices_MOVED.mbbo import Mbbo

from bcm.epics_devices_MOVED.camera import camera
from bcm.epics_devices_MOVED.scan import Scan
from bcm.epics_devices_MOVED.transform import Transform

from cls.applications.bioXasIM.device_names import *

from cls.appWidgets.main_object import gen_session_obj, main_object_base, dev_config_base, POS_TYPE_BL, POS_TYPE_ES
from cls.utils.dirlist import dirlist
from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.dict_utils import dct_get, dct_put, dct_merge
from cls.app_data.defaults import Defaults
from cls.scanning.bioxasTypes import sample_positioning_modes, sample_fine_positioning_modes, endstation_id_types
from cls.types.beamline import BEAMLINE_IDS

import zmq
from cls.zeromq.epics.epics_api import *
from cls.utils.json_threadsave import json_string_to_dct
from cls.appWidgets.get_mks_prj_rev import get_mks_project_rev
#import simplejson as json
		
__version__ = '1.0.0'


BEAMLINE_NAME = '07ID-1'
BEAMLINE_TYPE = 'BIOXAS'
BEAMLINE_ENERGY_RANGE = (4.0, 18.5)

USE_ZMQ = False


class dev_config_bioxas(dev_config_base):
	def __init__(self, splash=None):
		super(dev_config_bioxas, self).__init__()
		print('Using BIOXAS DEVICES')
		self.beamline = 'BIOXAS Imaging 07ID1'
		self.sscan_rec_prfx = 'bioxas'
		self.es_id = endstation_id_types.IMAG
		self.splash = splash
		self.done = False
		#self.timer = QtCore.QTimer()
		#self.timer.timeout.connect(self.on_timer)
		self.init_devices()
		self.init_presets()
		#init_posner_snapshot_cbs(self.devices['POSITIONERS'])

		
	def init_presets(self):
		#self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 98
		#self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 98
		
		self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 70
		self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 70
		
		self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_X'] = 98
		self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_Y'] = 98
		
		#for now
		#self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_X'] = 11
		#self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_Y'] = 11
		
		self.devices['PRESETS']['MAX_ZP_SUBSCAN_RANGE_X'] = 98
		self.devices['PRESETS']['MAX_ZP_SUBSCAN_RANGE_Y'] = 98
		
		#self.devices['PVS'][DNM_ENERGY_ENABLE].put(0)
		
		
	def init_devices(self):
		
		#I don't have an elegant way yet to create these and also emit a signal to the splash screen
		#so this is a first attempt
		#self.timer.start(100)
		# maps names to device objects
		#self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = apsMotor('IOC:m100',pos_set=POS_TYPE_ES)
		#self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = apsMotor('IOC:m101',pos_set=POS_TYPE_ES)
		prfx = self.sscan_rec_prfx
		

		self.devices['POSITIONERS'][DNM_ENERGY] = apsMotor('BIOXAS:m100',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_DETECTOR_X] = apsMotor('BIOXAS:m101',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_DETECTOR_Y] = apsMotor('BIOXAS:m102',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_DETECTOR_Z ] = apsMotor('BIOXAS:m103',pos_set=POS_TYPE_ES)		
#		self.devices['POSITIONERS'][DNM_PFIL1607_5_I10_01] = apsMotor('BIOXAS:m100',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_PFIL1607_5_I10_02] = apsMotor('BIOXAS:m101',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_M1_VERT_PandR_IN_UP] = apsMotor('BIOXAS:m102',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_M1_VERT_PandR_OUT_UP ] = apsMotor('BIOXAS:m103',pos_set=POS_TYPE_ES)
		
		self.devices['POSITIONERS'][DNM_IMAG_M1_VERT_PandR_DOWN] = apsMotor('BIOXAS:m104',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_IMAG_M1_HORZ_STRIPE_SEL] = apsMotor('BIOXAS:m105',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_IMAG_M1_YAW] = apsMotor('BIOXAS:m106',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_IMAG_M1_BENDER_UPSTREAM] = apsMotor('BIOXAS:m107',pos_set=POS_TYPE_ES)
		self.devices['POSITIONERS'][DNM_IMAG_M1_BENDER_DOWNSTREAM] = apsMotor('BIOXAS:m108',pos_set=POS_TYPE_ES)

		self.devices['POSITIONERS'][DNM_IMAG_M2_VERT_PandR_IN_UP] = apsMotor('BIOXAS:m109',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_VERT_PandR_OUT_UP] = apsMotor('BIOXAS:m110',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_VERT_PandR_DOWN] = apsMotor('BIOXAS:m111',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_HORZ_STRIPE_SEL] = apsMotor('BIOXAS:m112',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_YAW] = apsMotor('BIOXAS:m113',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_BENDER_UPSTREAM] = apsMotor('BIOXAS:m114',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_M2_BENDER_DOWNSTREAM] = apsMotor('BIOXAS:m115',pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_MONO_BRAGG] = apsMotor('BIOXAS:m116',pos_set=POS_TYPE_BL)


		#actual beamline motors
		self.devices['POSITIONERS'][DNM_IMAG_MACRO_STAGE_HORIZ] = apsMotor('BL1607-I10:MacroHorizontal:SoftMotor',
																		   pos_set=POS_TYPE_BL)
		self.devices['POSITIONERS'][DNM_IMAG_MACRO_STAGE_VERT] = apsMotor('BL1607-I10:MacroVertical:SoftMotor',
																		   pos_set=POS_TYPE_BL)


#		
#		self.devices['POSITIONERS'][DNM_IMAG_VM_UPPER_BLADE] = apsMotor('BIOXAS:m117',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_VM_LOWER_BLADE] = apsMotor('BIOXAS:m118',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_CRYSTAL_2_Z2] = apsMotor('BIOXAS:m119',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_CRYSTAL_2_Y2] = apsMotor('BIOXAS:m120',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_CRYSTAL_2_Theta2] = apsMotor('BIOXAS:m121',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_CRYSTAL_2_CHI_2] = apsMotor('BIOXAS:m122',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_TABLE_VERT_Y] = apsMotor('BIOXAS:m123',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MONO_TABLE_HORZ_X ] = apsMotor('BIOXAS:m124',pos_set=POS_TYPE_ES)
#		
#		self.devices['POSITIONERS'][DNM_IMAG_TABLE_VERTICAL_1] = apsMotor('BIOXAS:m125',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_TABLE_VERTICAL_2] = apsMotor('BIOXAS:m126',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_TABLE_VERTICAL_3] = apsMotor('BIOXAS:m127',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_TABLE_HORIZONTAL_1] = apsMotor('BIOXAS:m128',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_TABLE_HORIZONTAL_2] = apsMotor('BIOXAS:m129',pos_set=POS_TYPE_ES)
#		
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_US_VERT_GAP] = apsMotor('BIOXAS:m130',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_US_VERT_CENTER] = apsMotor('BIOXAS:m131',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_US_HOR_GAP] = apsMotor('BIOXAS:m132',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_US_HOR_CENTER] = apsMotor('BIOXAS:m133',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_HORIZ_KB_BENDER_1] = apsMotor('BIOXAS:m134',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_HORIZ_KB_BENDER_2] = apsMotor('BIOXAS:m135',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_HORIZ_KB_VERTICAL] = apsMotor('BIOXAS:m136',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_HORIZ_KB_TILT] = apsMotor('BIOXAS:m137',pos_set=POS_TYPE_ES)
#		
#		self.devices['POSITIONERS'][DNM_IMAG_VERT_KB_BENDER_1] = apsMotor('BIOXAS:m138',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_VERT_KB_BENDER_2] = apsMotor('BIOXAS:m139',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_VERT_KB_VERTICAL] = apsMotor('BIOXAS:m140',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_VERT_KB_TILT] = apsMotor('BIOXAS:m141',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_DETECTOR_1_VERTICAL] = apsMotor('BIOXAS:m142',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_DETECTOR_1_LATERAL] = apsMotor('BIOXAS:m143',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_DETECTOR_2_VERTICAL] = apsMotor('BIOXAS:m144',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_DETECTOR_2_LATERAL] = apsMotor('BIOXAS:m145',pos_set=POS_TYPE_ES)
#		
#		self.devices['POSITIONERS'][DNM_IMAG_SAMPLE_ROTARY_STAGE] = apsMotor('BIOXAS:m146',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_ZONE_PLATE_X] = apsMotor('BIOXAS:m147',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_ZONE_PLATE_Y] = apsMotor('BIOXAS:m148',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_ZONE_PLATE_Z] = apsMotor('BIOXAS:m149',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_ZONE_PLATE_PITCH] = apsMotor('BIOXAS:m150',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_ZONE_PLATE_YAW] = apsMotor('BIOXAS:m151',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_OPTICAL_SAMPLE_VERT ] = apsMotor('BIOXAS:m152',pos_set=POS_TYPE_ES)
#
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_DS_VERT_GAP] = apsMotor('BIOXAS:m153',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_DS_VERT_CENTER] = apsMotor('BIOXAS:m154',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_DS_HOR_GAP] = apsMotor('BIOXAS:m155',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_JJ_SLIT_DS_HOR_CENTER] = apsMotor('BIOXAS:m156',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MACRO_STAGE_UP_DOWN] = apsMotor('BIOXAS:m157',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MACRO_STAGE_HORIZ] = apsMotor('BIOXAS:m158',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_MACRO_STAGE_VERT] = apsMotor('BIOXAS:m159',pos_set=POS_TYPE_ES)
#		self.devices['POSITIONERS'][DNM_IMAG_VISUALIZATION_VERT] = apsMotor('BIOXAS:m160',pos_set=POS_TYPE_ES)

		
		
		connect_standard_beamline_positioners(self.devices, prfx)
		connect_devices(self.devices, prfx)
		
		#key, value in self.devices.iteritems():
		#	print key,value
		print('finished connecting to devices')
		self.done = True

def connect_standard_beamline_positioners(dev_dct, prfx='bioxas'):
	
	return
# 	dev_dct['POSITIONERS'][DNM_ENERGY] = apsMotor('BL1607-I10:ENERGY',pos_set=POS_TYPE_ES)
# 	dev_dct['POSITIONERS'][DNM_SLIT_X] = apsMotor('BL1607-I10:slitX',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_SLIT_Y] = apsMotor('BL1607-I10:slitY',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_M3_PITCH] = apsMotor('BL1607-I10:m3STXMPitch',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_EPU_GAP] = apsMotor('BL1607-I10:epuGap',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_EPU_OFFSET] = apsMotor('BL1607-I10:epuOffset',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_EPU_HARMONIC] = apsMotor('BL1607-I10:epuHarmonic',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_EPU_POLARIZATION] = apsMotor('BL1607-I10:epuPolarization',pos_set=POS_TYPE_BL)
# 	dev_dct['POSITIONERS'][DNM_EPU_ANGLE] = apsMotor('BL1607-I10:epuAngle',pos_set=POS_TYPE_BL)
# 	

def connect_devices(dev_dct, prfx='bioxas'):
	""" populate the following device sections
			PVS: singular PV connections
			DETECTORS: devices that return data
			SSCANS:
			PVS_DONT_RECORD:
			TEMPERATURES:
			PRESSURES:
		"""
			
			
	
	dev_dct['PVS'][DNM_SYSTEM_MODE_FBK] = EpicsPv(DNM_SYSTEM_MODE_FBK)
	dev_dct['PVS_DONT_RECORD'][DNM_TICKER] = EpicsPv('TRG2400:cycles')
	dev_dct['PVS'][DNM_SRSTATUS_SHUTTERS] = EpicsPv('SRStatus:shutters')
	
	dev_dct['DETECTORS']['StorageRingCurrent'] = EpicsPv('PCT1402-01:mA:fbk')
		
	dev_dct['DIO'][DNM_GATE] = EpicsPv('TRG2400:cycles')
# 	dev_dct['DIO'][DNM_GATE] = BaseGate('%sCO:gate' % prfx)
# 	dev_dct['DIO'][DNM_SHUTTER] = PvShutter('%sDIO:shutter:ctl' % prfx)
 	dev_dct['DIO'][DNM_SHUTTER] = EpicsPv('TRG2400:cycles')
# 	dev_dct['DIO'][DNM_SHUTTERTASKRUN] = EpicsPv('%sDIO:shutter:Run' % prfx)
# 	
# 	dev_dct['DETECTORS'][DNM_COUNTER_APD] = BaseCounter('%sCI:counter' % prfx)
 	dev_dct['DETECTORS'][DNM_COUNTER_APD] = EpicsPv('TRG2400:cycles')
# 	#dev_dct['DETECTORS']['Det_Cntr'] = EpicsPvCounter('%sPMT:ctr:SingleValue_RBV' % prfx)
# 	dev_dct['DETECTORS'][DNM_PMT] = EpicsPv('%sPMT:ctr:SingleValue_RBV' % prfx)
# 	
# 	dev_dct['DETECTORS_NO_RECORD'][DNM_DETCNTR_SNAPSHOT] = EpicsPvCounter('%sPMT:det_snapshot_RBV' % prfx)
# 	dev_dct['DETECTORS_NO_RECORD'][DNM_OSACNTR_SNAPSHOT] = EpicsPvCounter('%sPMT:osa_snapshot_RBV' % prfx)
# 		
# 	dev_dct['PVS'][DNM_IDEAL_A0] = EpicsPv('BL1607-I10:ENERGY:%s:zp:fbk:tr.K' % prfx)
# 	dev_dct['PVS'][DNM_CALCD_ZPZ] = EpicsPv('BL1607-I10:ENERGY:%s:zp:fbk:tr.L' % prfx)
# 
# 	dev_dct['PVS']['Zpz_scanModeFlag'] = Mbbo('BL1607-I10:ENERGY:%s:zp:scanselflag' % prfx) #used to control which value gets sent to Zpz, fl or fl - A0
# 	#used to adjust the current focus value, the delta represents the relative microns for zpz to move to new focus position
# 	dev_dct['PVS']['Delta_Zpz'] = EpicsPv('BL1607-I10:ENERGY:%s:delta_zpz' % prfx) 
# 	dev_dct['PVS'][DNM_FOCAL_LENGTH] = EpicsPv('BL1607-I10:ENERGY:%s:zp:FL' % prfx)
# 	dev_dct['PVS'][DNM_A0] = EpicsPv('BL1607-I10:ENERGY:%s:A0' % prfx)
# 	dev_dct['PVS'][DNM_A0MAX] = EpicsPv('BL1607-I10:ENERGY:%s:A0Max' % prfx)
# 	
# 	dev_dct['PVS'][DNM_ZPZ_POS] = EpicsPv('BL1607-I10:ENERGY:%s:zp:zpz_pos' % prfx)
# 	dev_dct['PVS'][DNM_ZP_DEF] = Transform('BL1607-I10:ENERGY:%s:zp:def' % prfx)
# 	dev_dct['PVS'][DNM_OSA_DEF] = Transform('BL1607-I10:ENERGY:%s:osa:def' % prfx)
# 		
# 	dev_dct['PVS'][DNM_ZP_SELECT] = Mbbo('BL1607-I10:ENERGY:%s:zp' % prfx)
# 	dev_dct['PVS'][DNM_OSA_SELECT] = Mbbo('BL1607-I10:ENERGY:%s:osa' % prfx)
# 	
# 	dev_dct['PVS'][DNM_ENERGY_ENABLE] = EpicsPv('BL1607-I10:ENERGY:%s:enabled' % prfx)
# 	dev_dct['PVS'][DNM_ENERGY_RBV] = EpicsPv('BL1607-I10:ENERGY.RBV')
# 	dev_dct['PVS'][DNM_ZP_DEF_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp:def.A' % prfx)
# 	
# 	
# 	dev_dct['PVS'][DNM_ZP_DEF1_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp1:def.A' % prfx)
# 	dev_dct['PVS'][DNM_ZP_DEF2_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp2:def.A' % prfx)
# 	dev_dct['PVS'][DNM_ZP_DEF3_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp3:def.A' % prfx)
# 	dev_dct['PVS'][DNM_ZP_DEF4_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp4:def.A' % prfx)
# 	dev_dct['PVS'][DNM_ZP_DEF5_A] = EpicsPv('BL1607-I10:ENERGY:%s:zp5:def.A' % prfx)
# 		
# 	#dev_dct['PVS']['SRStatus_msgL1'] = EpicsPv('SRStatus:msg:tL1')
# 	#dev_dct['PVS']['SRStatus_msgL2'] = EpicsPv('SRStatus:msg:tL2')
# 	#dev_dct['PVS']['SRStatus_msgL3'] = EpicsPv('SRStatus:msg:tL3')
# 	
# 		
# 	dev_dct['PVS'][DNM_MONO_EV_FBK] = EpicsPv('MONO1610-I10-01:energy:fbk')
# 	dev_dct['PVS'][DNM_EPU_POL_FBK] = Mbbi('UND1410-01:polarization')
# 	dev_dct['PVS'][DNM_EPU_POL_ANGLE] = EpicsPv('UND1410-01:polarAngle')
# 	dev_dct['PVS'][DNM_EPU_GAP_FBK] = EpicsPv('UND1410-01:gap:mm:fbk')
# 	dev_dct['PVS'][DNM_EPU_GAP_OFFSET] = EpicsPv('UND1410-01:gap:offset')
# 	dev_dct['PVS'][DNM_EPU_HARMONIC] = EpicsPv('UND1410-01:harmonic')
# 		
# 	
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_CX_AUTO_DISABLE_POWER] = EpicsPv('IOC:m112:XPS_AUTO_DISABLE_MODE')
# 	dev_dct['PVS_DONT_RECORD'][DNM_CY_AUTO_DISABLE_POWER] = EpicsPv('IOC:m113:XPS_AUTO_DISABLE_MODE')
# 	dev_dct['PVS_DONT_RECORD'][DNM_DX_AUTO_DISABLE_POWER] = EpicsPv('IOC:m114:XPS_AUTO_DISABLE_MODE')
# 	dev_dct['PVS_DONT_RECORD'][DNM_DY_AUTO_DISABLE_POWER] = EpicsPv('IOC:m115:XPS_AUTO_DISABLE_MODE')
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_ACCRANGE] = EpicsPv('uhvTestSIG:signal:MaxPoints')
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_FX_FORCE_DONE] = EpicsPv('IOC:m100:ForceDone')
# 	dev_dct['PVS_DONT_RECORD'][DNM_FY_FORCE_DONE] = EpicsPv('IOC:m101:ForceDone')
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_OX_FORCE_DONE] = EpicsPv('IOC:m104:ForceDone')
# 	dev_dct['PVS_DONT_RECORD'][DNM_OY_FORCE_DONE] = EpicsPv('IOC:m105:ForceDone')
# 	
# 	dev_dct['PVS_DONT_RECORD']['OX_tracking_enabled'] = EpicsPv('BL1607-I10:ENERGY:%s:osax_track_enabled' % prfx)
# 	dev_dct['PVS_DONT_RECORD']['OY_tracking_enabled'] = EpicsPv('BL1607-I10:ENERGY:%s:osay_track_enabled' % prfx)
# 	dev_dct['PVS_DONT_RECORD']['OZ_tracking_enabled'] = EpicsPv('BL1607-I10:ENERGY:%s:osaz_track_enabled' % prfx)
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_OSAXYZ_LOCKPOSITION_ENABLED] = EpicsPv('BL1607-I10:ENERGY:%s:osaxyz_lockpos_enabled' % prfx)
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_OSAXY_GOTO_LOCKPOSITION] = EpicsPv('BL1607-I10:ENERGY:%s:osaxy_goto_lockpos' % prfx)
# 	dev_dct['PVS_DONT_RECORD'][DNM_OSAZ_GOTO_LOCKPOSITION] = EpicsPv('BL1607-I10:ENERGY:%s:osaz_goto_lockpos' % prfx)
# 	
# 	dev_dct['PVS_DONT_RECORD'][DNM_SET_XY_LOCKPOSITION] = EpicsPv('BL1607-I10:ENERGY:%s:set_xy:lock_posn' % prfx)
# 	dev_dct['PVS_DONT_RECORD'][DNM_SET_Z_LOCKPOSITION] = EpicsPv('BL1607-I10:ENERGY:%s:set_z:lock_posn' % prfx)
		
	#for POL, OFF and ANGLE
	dev_dct['PVS_DONT_RECORD']['%s:image:cmd_file' % prfx] = EpicsPv('%s:image:cmd_file' % prfx)
	dev_dct['PVS_DONT_RECORD']['%s:image:percentDone' % prfx] = EpicsPv('%s:image:percentDone' % prfx)
	dev_dct['PVS_DONT_RECORD']['%s:image:single_progress' % prfx] = EpicsPv('%s:image:single_progress' % prfx)		
	
	dev_dct['PVS_DONT_RECORD']['%s:image:remainingTimeStr' % prfx] = EpicsPv('%s:image:remainingTimeStr' % prfx)
	dev_dct['PVS_DONT_RECORD']['%s:image:endingTimeStr' % prfx] = EpicsPv('%s:image:endingTimeStr' % prfx)
	dev_dct['PVS_DONT_RECORD']['%s:image:totalElapsedTimeStr' % prfx] = EpicsPv('%s:image:totalElapsedTimeStr' % prfx)
	
	
	dev_dct['SSCANS']['%s:image:scan1' % prfx] = Scan('%s:image:scan1' % prfx)
	dev_dct['SSCANS']['%s:image:scan2' % prfx] = Scan('%s:image:scan2' % prfx)
	dev_dct['SSCANS']['%s:image:scan3' % prfx] = Scan('%s:image:scan3' % prfx)
	dev_dct['SSCANS']['%s:image:scan4' % prfx] = Scan('%s:image:scan4' % prfx)
	dev_dct['SSCANS']['%s:image:scan5' % prfx] = Scan('%s:image:scan5' % prfx)
	
	
		
	# ES = endstation temperatures
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-01'] = ai('TM1610-3-I12-01', desc='Turbo cooling water')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-30'] = ai('TM1610-3-I12-30', desc='Sample Coarse Y')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-32'] = ai('TM1610-3-I12-32', desc='Detector Y')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-21'] = ai('TM1610-3-I12-21', desc='Chamber temp #1')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-22'] = ai('TM1610-3-I12-22', desc='Chamber temp #2')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-23'] = ai('TM1610-3-I12-23', desc='Chamber temp #3')
# 	dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-24'] = ai('TM1610-3-I12-24', desc='Chamber temp #4')
# 	
# 	
# 	#pressures
# 	dev_dct['PRESSURES'][POS_TYPE_ES]['FRG1610-3-I12-01:vac:p'] = ai('FRG1610-3-I12-01:vac:p', desc='Chamber pressure')
# 	dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-03:vac:p'] = ai('TCG1610-3-I12-03:vac:p', desc='Turbo backing pressure')
# 	dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-04:vac:p'] = ai('TCG1610-3-I12-04:vac:p', desc='Load lock pressure')
# 	dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-05:vac:p'] = ai('TCG1610-3-I12-05:vac:p', desc='Rough line pressure')
	
	connect_ES_devices(dev_dct, prfx)
	connect_BL_devices(dev_dct, prfx)
	

def connect_ES_devices(dev_dct, prfx='bioxas'):
	return
# 	if(prfx.find('uhv') > -1):
# 		dev_dct['TEMPERATURES'][POS_TYPE_ES]['CCTL1610-I10:temp:fbk'] = ai('CCTL1610-I10:temp:fbk', desc='Gatan rod temp')
# 	else:
# 		pass	

def connect_BL_devices(dev_dct, prfx='bioxas'):
	return

MAIN_OBJ = None
DEVICE_CFG = None

MAIN_OBJ = main_object_base('CLS BioXAS 07ID1','IMAG', BEAMLINE_IDS.BIOXAS)
MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.GONIOMETER)
MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
	
MAIN_OBJ.set_datafile_prefix('I')
MAIN_OBJ.set_thumbfile_suffix('jpg')
DEVICE_CFG = dev_config_bioxas()
MAIN_OBJ.set_devices(DEVICE_CFG)
DEFAULTS = Defaults('bioxas_dflts.json', new=False)



if __name__ == '__main__':
	pass
