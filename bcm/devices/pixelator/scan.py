#!/usr/bin/env python
"""
 scan device
"""
import epics
import threading

from PyQt5.QtCore import QObject, Qt, pyqtSignal


class Scan(QObject):
	"""
	A Device representing an Epics sscan record.

	The Scan Device represents an sscan record.
	"""

	def __init__(self, name, **kwargs):
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

	def run(self, wait=False):
		"""
		Execute the scan.
		"""
		pass


	def _onDone(self, **kwargs):
		'''
			        return the low level control system name for this device
			        to be implemented by inheriting class'''
		pass
		# if kwargs['value'] == 0:
		# 	self.waitSemaphore.release()
	

