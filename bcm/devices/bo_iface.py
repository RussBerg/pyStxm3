#!/usr/bin/env python

from PyQt5.QtCore import QObject, Qt, pyqtSignal


class bo(QObject):
    """
    Simple binary output device
    """

    def __init__(self, prefix, **kwargs):
        '''
                prefix is the low level control system name for this bi device
                to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
        return the low level control system name for this bi device
        to be implemented by inheriting class'''
        pass