#!/usr/bin/env python
"""Epics transform record"""
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class Transform(QObject):
	"Epics transfrom record"

	def __init__(self, prefix, **kwargs):
		"""
		                	Initialize the scan.

		                	name: The name of the scan record.
		                	"""
		pass

	def get_name(self):
		'''
	    return the low level control system name for this device
	    to be implemented by inheriting class'''
		pass

	def get_position(self):
		""" this is an API function for all devices/pvs/detectors """
		return(self.get_all())
	
	def get_all(self):
		'''
			    return all attributes and their values for this device
			    to be implemented by inheriting class'''
		pass
	
