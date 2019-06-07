#C:\Python27\python.exe
# -*- coding: UTF-8 -*-
from zope.interface import Interface, Attribute, invariant

from sm.stxm_control.devices.shutters import IShutter
from sm.stxm_control.plotters import IPlotter
from sm.stxm_control.dataRecord import IDataRecorder
from sm.stxm_control.devices.counters import ICounter
from sm.stxm_control.positioners import IPositioner

class IScanManager(Interface):
	"""@Interface for a scan Manager, this is probably unecessary and will likely be removed"""
	
	def __init__(self):
		self.___shutter = None
		""" stxm_control.devices.shutters.IShutter"""
		self.___plotter = None
		""" stxm_control.plotters.IPlotter"""
		self.___dataRecorder = None
		""" stxm_control.dataRecord.IDataRecorder"""
		self.___counter = None
		""" stxm_control.devices.counters.ICounter"""
		self.___positioner = None
		""" stxm_control.positioners.IPositioner"""
		self.___scanList = None
		""" stxm_control.scanning.IScan"""


	def start(self):
		pass

	def abort(self):
		pass

	def get_status(self):
		pass

	
