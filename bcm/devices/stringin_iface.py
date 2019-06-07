#!/usr/bin/python
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class Stringin(QObject):
    "Simple string input device"

    def __init__(self,prefix):
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

