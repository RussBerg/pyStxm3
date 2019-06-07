#!/usr/bin/python 

from PyQt5.QtCore import QObject, Qt, pyqtSignal

class Mbbo(QObject):
	""" 
	Simple multi binary bit input device
	"""
	def __init__(self, prefix, **kwargs):
		'''
							prefix is the low level control system name for this dio device
						    to be implemented by inheriting class'''
		pass

	def get_name(self):
		'''
        return the low level control system name for this device
        to be implemented by inheriting class'''
		pass

	def get_position(self):
		''''
	      return the current position of the device
	      to be implemented by inheriting class'''
		pass
	
	def get_report(self):
		""" return a dict that reresents all 
		 of the settings for this device """
		pass
	




		