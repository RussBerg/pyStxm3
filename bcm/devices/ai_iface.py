#!/usr/bin/env python
"""interface for an analog input device"""

from PyQt5.QtCore import QObject, Qt, pyqtSignal

class ai(QObject):
	"Simple analog input device"

	def __init__(self, prefix, **kwargs):
		'''
		prefix is the low level control system name for this ai device
		to be implemented by inheriting class'''
		pass


	def get_position(self):
		'''
		return the current value of the ai device
		to be implemented by inheriting class'''
		pass

	def get_name(self):
		'''
		return the low level control system name for this ai device
		to be implemented by inheriting class'''
		pass

	def put_desc(self, desc):
		'''to be implemented by inheriting class'''
		pass
		
