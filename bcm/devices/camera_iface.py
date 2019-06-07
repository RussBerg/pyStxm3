'''
Created on Oct 5, 2016

@author: bergr
'''
import time

from PyQt5.QtCore import pyqtSignal, QObject
import numpy as np
#from epics.pv import PV


class camera(QObject):
    changed = pyqtSignal(object)
    acquire_frame = pyqtSignal(int)
    """
     Represents a very basic camera as defined in the epics database calib_camera.db which is
     a part of the blApi epics application, these pv's are merley placeholders that will be filled
     in by an application that wants to read and write to this epics calibration camera instance. 
     
        CCD1610-I10:uhv:serial_num:fbk
        CCD1610-I10:uhv:start_cap
        CCD1610-I10:uhv:fw_version:fbk
        CCD1610-I10:uhv:model:fbk
        CCD1610-I10:uhv:sensor:fbk
        CCD1610-I10:uhv:vendor:fbk
        CCD1610-I10:uhv:calib_cam:wv:fbk

     """
    def __init__(self, prefix, width=640, ht=480):
        '''
            prefix is the low level control system name for this camera device
            to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
        return the low level control system name for this camera device
        to be implemented by inheriting class'''
        pass

    def start_capture(self):
        '''
            start capture
            to be implemented by inheriting class'''
        pass

    def stop_capture(self):
        '''
            stop capture
            to be implemented by inheriting class'''
        pass

    def get_single_frame(self, numpts=None):
        '''
            return single frame of image data
            to be implemented by inheriting class'''
        pass

    def get_image_data(self, numpts=None):
        '''
            get the current image data
            to be implemented by inheriting class'''
        pass


    def on_copy_data(self, data):
        '''
            copy data to self.data
            to be implemented by inheriting class'''
        pass

    # def on_changed(self, data):
    #     print 'on_changed'

    def on_new_data(self, **kwargs):
        '''
                    copy data to self.data
                    to be implemented by inheriting class'''
        pass

        # data = kwargs['value']
        # print 'on_new_data \n', data[0:10]
        # self.changed.emit(data)
    

