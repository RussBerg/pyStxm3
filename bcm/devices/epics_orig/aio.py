r""" Counter Device objects

A counter device enables counting and averaging over given time periods.

Each Counter device obeys the following interface:

	methods:

	count(time)
		count for the specified amount of time and return the numeric value
		corresponding to the average count. This method blocks for the specified
		time.

"""
import os
import time
import queue
import atexit
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal
import numpy as np

from cls.utils.developer_tools import DONT_FORGET

from .base import BaseDevice

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.enum_utils import Enum

trig_types = Enum('DAQmx_Val_None', 'DAQmx_Val_AnlgEdge', 'DAQmx_Val_AnlgWin', 'DAQmx_Val_DigEdge',
                  'DAQmx_Val_DigPattern', 'SOFT_TRIGGER')

hostname = os.getenv('COMPUTERNAME')
if (hostname == 'WKS-W001465'):
    # the new test computer in old magnet mapping room
    GENERATE_DATA = False
elif (hostname == 'NBK-W001021'):
    # my notebook computer
    SIMULATE = True
    GENERATE_DATA = True
else:
    # teh old stxm_control conmputer
    SIMULATE = False
    GENERATE_DATA = False

DATA_OFFSET = 2


# setup module logger with a default do-nothing handler
# _logger = get_module_logger(__name__)

class aio(BaseDevice):

    """ just a convienience class so that PVs can be configured in the beamline configuration file
    and used as if they were other devices, making the rest of the code cleaner

    ret_kwarg can be anyone of the following keys
    {'lower_disp_limit': None,
     'char_value': '1094.716',
     'chid': 162172624,
     'severity': 0,
     'upper_ctrl_limit': None,
     'read_access': True,
     'access': 'read/write',
     'ftype': 20,
     'units': None,
     'lower_ctrl_limit': None,
     'write_access': True,
     'type': 'time_double',
     'pvname': 'IOC:m105.HLM',
     'status': 0,
     'cb_info': (1, <PV 'IOC:m105.HLM', count=1, type=time_double, access=read/write>),
     'upper_disp_limit': None,
     'timestamp': 1537456674.92749,
     'nelm': 1,
     'lower_alarm_limit': None,
     'precision': None,
     'host': 'IOC1610-303.clsi.ca:49532',
     'upper_alarm_limit': None,
     'count': 1,
     'value': 1094.716,
     'enum_strs': None,
     'lower_warning_limit': None,
     'upper_warning_limit': None,
     'typefull': 'time_double'}
    """
    _new_data = pyqtSignal(object)
    changed = pyqtSignal(object)

    def __init__(self, pv_name=None, desc=None, egu='', cb=None, ret_kwarg='value', **cb_kwargs):
        super(aio, self).__init__()
        self._name = pv_name
        self.value = None
        self.ctrl_vars = {}
        self.cb_args = {}
        #the key word to use in the kwargs dict
        self.return_kwarg = ret_kwarg

        for k in cb_kwargs:
            self.cb_args[k] = cb_kwargs[k]

        if(len(cb_kwargs) < 1):
            self.cb_args

        if (desc is not None):
            self.desc = desc
        else:
            self.desc = pv_name

        self.egu = egu

        if (pv_name is not None):
            self.pv = self.add_pv(pv_name)
            self.connected = self.pv.connected
            if(cb is None):
                #setup default callback for changed
                self.pv.add_callback(self._on_pv_changed, with_ctrlvars=False, **cb_kwargs)
                self.pv.connection_callbacks.append(self.con_cb_fired)
            else:
                #the user wants to override the default and setup their own handler for 'changed' signal
                self.pv.add_callback(cb, **cb_kwargs)
            self._new_data.connect(self.count)

    def con_cb_fired(self, pvname, conn, pv):
        if(pv.connected and conn):
            if(conn):
                print('con_cb_fired: [%s]: pv is reporting CONNECTED', pvname)
            else:
                print('con_cb_fired: [%s]: pv is reporting NOT connected', pvname)



    def is_connected(self):
        return(self.pv.connected)

    def add_callback(self, func, **kwargs):
        self.pv.add_callback(func, **kwargs)

    def _on_pv_changed(self, *args, **kwargs):
        '''
        ALWAYS return 'value' plus whatever kwargs the user passed in
        :param kwargs:
        :return:
        '''
        if(kwargs['enum_strs'] is not None):
            print()
        dct = {}
        #'value' must be a part of default kwargs
        if(len(self.cb_args) == 0):
            #only return the value by itself
            #self._new_data.emit(kwargs[self.return_kwarg])
            self.changed.emit(kwargs[self.return_kwarg])
        else:
            #else return a dict of value plus cb_args
            dct['value'] = kwargs[self.return_kwarg]
            for k in self.cb_args:
                dct[k] = kwargs[k]
            #emit the changed signal
            #self._new_data.emit(dct)
            self.changed.emit(dct)

    def get_desc(self):
        return(self.desc)

    def get_egu(self):
        return(self.egu)

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'name', self.name)
        return (dct)

    def get_name(self):
        return (self._name)

    def get_position(self):
        return (self.pv.get())

    def count(self, val):
        #print 'count called', val
        self.changed.emit(val)
        return (val)

    def get(self):
        return (self.pv.get())

    def put(self, val):
        self.pv.put(val)

    def get_low_limit(self):
        return (None)

        # i = 0
        # while ((len(self.ctrl_vars) == 0) and (i < 50)):
        #     self.ctrl_vars = self.pv.get_ctrlvars()
        #     i += 1
        #     time.sleep(0.001)
        # if ('lower_ctrl_limit' in list(self.ctrl_vars.keys())):
        #     return (self.ctrl_vars['lower_ctrl_limit'])
        # else:
        #     return (None)

    def get_high_limit(self):
        return (None)
        # i = 0
        # while ((len(self.ctrl_vars) == 0) and (i < 50)):
        #     self.ctrl_vars = self.pv.get_ctrlvars()
        #     i += 1
        #     time.sleep(0.001)
        #
        # if ('upper_ctrl_limit' in list(self.ctrl_vars.keys())):
        #     return (self.ctrl_vars['upper_ctrl_limit'])
        # else:
        #     return (None)

    def get_enum_str(self):
        val = self.pv.get()
        val_str = self.pv.enum_strs[val]
        return (val_str)

    def get_enum_str_as_int(self):
        val = self.pv.get()
        if (type(val) is int):
            final = val
        else:
            final = int(self.pv.enum_strs[val])
        return (final)


if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets

    def on_new_pmt(**kwargs):
        print('MY CALLBACK IS BEING CALLED:')
        print(kwargs)


    def on_new_pmt_val(val):
        print(val)


    #
    app = QtWidgets.QApplication(sys.argv)
    #ai3 = EpicsPv('uhvAi:ai:ai3_RBV', cb=on_new_pmt, cb_arg1='Hey man', id=234, mydct={'id':23, 'desc':'the fake description'})
    #ai1 = EpicsPv('uhvAi:ai:ai1_RBV', id=234, mydct={'id': 23, 'desc': 'the fake description'})
    ai0 = aio('uhvAi:ai:ai0_RBV', id=554)
    ai0.changed.connect(on_new_pmt_val)
    #ai1.changed.connect(on_new_pmt_val)
    #ai3.changed.connect(on_new_pmt_val)
    app.exec_()
