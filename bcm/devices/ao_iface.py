#!/usr/bin/ao python
"""interface for an analog input device"""

from PyQt5.QtCore import QObject, Qt, pyqtSignal

class ao(QObject):
    "Simple analog output device"

    def __init__(self, prefix, **kwargs):
        '''
        		prefix is the low level control system name for this ao device
        		to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
        return the low level control system name for this ao device
        to be implemented by inheriting class'''
        pass

    def put(self):
        '''
        return the low level control system name for this ao device
        to be implemented by inheriting class'''
        pass

