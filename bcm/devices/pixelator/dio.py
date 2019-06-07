'''
Created on 2014-05-26

@author: bergr
'''
#!/usr/bin/env python
""" digital input output device"""

from PyQt5.QtCore import QObject, Qt, pyqtSignal

class digitalIO(QObject):
	"Simple interface to digital IO task"

	def __init__(self, prefix, **kwargs):
		'''
			prefix is the low level control system name for this dio device
		    to be implemented by inheriting class'''
		pass

	def get_name(self):
		'''
        return the low level control system name for this dio device
        to be implemented by inheriting class'''
		pass
	
	def configure(self):
		""" to be implemented by inheriting class """
		pass
	
	def set_bit(self, bit, val):
		"""
		set a bit with value
		to be implemented by inheriting class """
		pass
		
	def set_port(self, port, val):
		"""
		set an entire port (register/set of bits) with value
		to be implemented by inheriting class """
		pass
		
	def get_bit(self, bit):
		"""
		get a bit
		to be implemented by inheriting class """
		pass
		
		
	def get_port(self, port):
		"""
		get an entire port (register/set of bits) with value
		to be implemented by inheriting class """
		pass




class BaseTrigger(digitalIO):
	""" test trigger """

	def __init__(self, prefix, **kwargs):
		'''
					prefix is the low level control system name for this trigger device
				    to be implemented by inheriting class'''
		pass

	def get_name(self):
		'''
        return the low level control system name for this trigger device
        to be implemented by inheriting class'''
		pass

	def configure(self):
		""" to be implemented by inheriting class """
		pass


		
		
		
		
