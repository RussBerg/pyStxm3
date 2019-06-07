#!/usr/bin/env python
"""Epics analog input record"""
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class counterIn(QObject):
	"Simple interface to counter input device"
	changed = pyqtSignal(int, object)

	def __init__(self, prefix, **kwargs):
		'''
		                prefix is the low level control system name for this counter input device
		                to be implemented by inheriting class'''
		pass

	def configure(self, cfg_dct):
		'''
             a function for configuring the counter, a configuration dict is passed in
            to be implemented by inheriting class'''
		pass

	def get_base_cfg_dict(self):
		'''
			return a default config dict
		    to be implemented by inheriting class'''
		pass

	def set_default_cfg(self, cfg_dct):
		# cfg_dct['EdgeSelect'] = 0 #DAQmx_Val_Rising
		# cfg_dct['Retriggerable'] =  0 # No
		# cfg_dct['DeviceSelect'] =  0
		# cfg_dct['RowMode'] = 0 # LINE
		# cfg_dct['TimePerDivSelect'] =  0
		# cfg_dct['TimePerDiv'] =  0.0
		# cfg_dct['UpdateTime'] =  0.02
		# cfg_dct['Run'] =  0
		# cfg_dct['AutoRead:enabled'] =  0
		# cfg_dct['CounterSelect'] =  0 # ctr2
		# cfg_dct['TrigSrcSelect'] =  0 # /PFI3
		# cfg_dct['SoftTrigger'] =  0
		# cfg_dct['TriggerType'] =  3 #DAQmx_DigEdge
		# cfg_dct['CountDir'] =  0 #Countup
		# cfg_dct['SignalSrcClockSelect'] =  12 # /PFI12
		# cfg_dct['PointsPerRow'] = 1
		# cfg_dct['InitialCount'] =  0
		# cfg_dct['SignalSrcPinSelect'] =  0 # /PFI0
		# cfg_dct['SamplingRate'] =  50000
		# cfg_dct['TriggerDelay'] =  0.0
		# cfg_dct['SampleMode'] =  0 #FiniteSamps
		# cfg_dct['MaxPoints'] =	2
		# return(cfg_dct)
		'''
              create a default config dict
              to be implemented by inheriting class'''
		pass


	
			
		
		
		
		
