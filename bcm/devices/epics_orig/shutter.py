'''
Created on Mar 23, 2013

@author: User
'''
import time
import math
import logging
import ctypes

from PyQt5.QtCore import QObject, Qt, pyqtSignal
import numpy as np

from .base import BaseDevice

from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.enum_utils import Enum

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

shutter_modes = Enum('Manual', 'Auto')


class PvShutter(BaseDevice):
    """class for shutter that are accessed as daqmx device digital output bits"""

    def __init__(self, name, openval=1, closeval=0):

        super(PvShutter, self).__init__()
        self.name = name
        self.pv = self.add_pv(name)
        self.ready = True
        self._open_val = openval
        self._close_val = closeval
        self._mode = shutter_modes.MANUAL
        self.is_open = False


    def add_callback(self, cb):
        self.pv.add_callback(cb)

    def get_name(self):
        return (self.name)

    def set_to_auto(self):
        self._mode = shutter_modes.AUTO

    def set_to_manual(self):
        self._mode = shutter_modes.MANUAL

    def is_auto(self):
        if (self._mode == shutter_modes.AUTO):
            return (True)
        else:
            return (False)

    def is_ready(self):
        return (self.ready)

    def start(self):
        self.open()
        self.is_open = True

    def stop(self):
        self.close()
        self.is_open = False

    def open(self):
        # _logger.debug("opening shutter")
        self.pv.put(self._open_val)

    def close(self):
        # _logger.debug("closing shutter")
        self.pv.put(self._close_val)

    def get(self):
        return (self.pv.get())

    def get_state(self):
        return (self.pv.get())

    def clear(self):
        pass

    # self.do.clear()

    def stop_and_clear(self):
        pass

    # self.stop()
    # self.clear()

    def get_report(self):
        dct = {}
        dct_put(dct, 'TO-DO', '')
        return (dct)


if __name__ == '__main__':
    # 	#Dev1 is the 6036
    # 	#dev2 is teh 6602
    # 	dout = DaqMxShutter('Shutter','Dev1/port0/line7:0',1)
    # 	dout.close()
    # 	print 'get_state = ' , dout.get_state()
    # 	dout.open()
    # 	print 'get_state = ' , dout.get_state()
    # 	dout.close()
    # 	print 'get_state = ' , dout.get_state()
    #
    # 	#test Task interface
    # 	dout.stop()
    # 	print 'get_state = ' , dout.get_state()
    # 	dout.start()
    # 	print 'get_state = ' , dout.get_state()
    # 	dout.stop()
    # 	print 'get_state = ' , dout.get_state()
    psht = PvShutter('uhvDIO:shutter:ctl')


# __all__ = ['Shutter', 'DaqMxShutter']
