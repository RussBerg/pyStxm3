#!/usr/bin/python
from PyQt5.QtCore import QObject, Qt, pyqtSignal


class Waveform(QObject):
    "Simple 1D array device"

    def __init__(self, prefix):
        """
			prefix is the low level control system name for this device
		    to be implemented by inheriting class
		"""
        pass


    def get_name(self):
        '''
        return the low level control system name for this device
        to be implemented by inheriting class'''
        pass
