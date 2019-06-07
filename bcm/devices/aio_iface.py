
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class basedevice(QObject):
    """ just a convienience class so that PVs can be configured in the beamline configuration file
    and used as if they were other devices, making the rest of the code cleaner
    """
    _new_data = pyqtSignal(object)
    changed = pyqtSignal(object)

    def __init__(self, pv_name=None, desc=None, egu='', cb=None, **cb_kwargs):
        '''
        		prefix is the low level control system name for this ai device
        		to be implemented by inheriting class'''
        pass

    def is_connected(self):
        '''
                		return True or False if the low level control device is connected
                		to be implemented by inheriting class'''
        pass

    def add_callback(self, func, **kwargs):
        '''
                		adda callback to call when the attr changes
                		to be implemented by inheriting class'''
        pass


    def get_desc(self):
        '''
                		return the description
                		to be implemented by inheriting class'''
        pass

    def get_egu(self):
        '''
                		return the engineering units as a string
                		to be implemented by inheriting class'''
        pass

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        '''
         		to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
            return teh low level control system name for this device
            to be implemented by inheriting class'''
        pass

    def get_position(self):
        '''
            return teh current position of the device
                		to be implemented by inheriting class'''
        pass

    def get(self):
        '''
            return the current position of the device
                		to be implemented by inheriting class'''
        pass

    def put(self, val):
        '''
                		put a value to the current device
                		to be implemented by inheriting class'''
        pass

    def get_low_limit(self):
        '''
                		prefix is the low level control system name for this ai device
                		to be implemented by inheriting class'''
        pass

    def get_high_limit(self):
        '''
                		prefix is the low level control system name for this ai device
                		to be implemented by inheriting class'''
        pass

    def get_enum_str(self):
        '''
                		prefix is the low level control system name for this ai device
                		to be implemented by inheriting class'''
        pass

    def get_enum_str_as_int(self):
        '''
                		prefix is the low level control system name for this ai device
                		to be implemented by inheriting class'''
        pass