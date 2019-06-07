#!/usr/bin/env python
""" multichannel analyzer device"""
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class Mca(QObject):
    """
     Mca device.
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

    def Read(self):
        "return value"
        pass

    def calibration(self):
        """return calibration values:
        CALO, CALS, CALQ, TTH
        """
        pass
