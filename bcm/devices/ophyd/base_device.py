import sys
import time as ttime

from PyQt5 import QtWidgets, QtCore
from ophyd.signal import EpicsSignal,EpicsSignalRO
from .ophyd_qt_dev import OphydQt_AIDevice, OphydQt_NodeDevice
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, DeviceStatus
from bcm.devices.dev_categories import dev_categories

from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

SIMULATE = False

class BaseDevice(QtCore.QObject):

    changed = QtCore.pyqtSignal(object)
    on_connect = QtCore.pyqtSignal(object)

    #def __init__(self, sig_name, write_pv=None, val_only=False, val_kw='value', backend='epics', **kwargs):
    def __init__(self, sig_name, name=None, write_pv=None, rd_only=False, val_only=False, val_kw='value', backend='epics', **kwargs):
        super(BaseDevice, self).__init__()
        #name here for compatability
        self.name = sig_name
        self.sig_name = sig_name
        self.rd_only = rd_only
        self.can_write = True
        self._ophyd_dev = None
        self._prev_val = None
        self._num_since_update = 0

        if ('units' in kwargs.keys()):
            self._units = kwargs['units']
        else:
            self._units = 'counts'

        if ('desc' in kwargs.keys()):
            self._desc = kwargs['desc']
        else:
            self._desc = 'Device'

        if(sig_name.find('.') == -1):
            if(name is None):
                self._ophyd_dev = OphydQt_AIDevice(sig_name, sig_name, **kwargs)
            else:
                self._ophyd_dev = OphydQt_AIDevice(sig_name, name, **kwargs)
        else:
            self._ophyd_dev = OphydQt_NodeDevice(sig_name, sig_name, **kwargs)

        if(rd_only):
            self.can_write = False

        if((write_pv is None) and self.can_write):
            self.write_pv = sig_name
        else:
            self.write_pv = write_pv

        self._attrs = {}
        for kw in kwargs:
            self._attrs[kw] = kwargs[kw]

        self.backend = backend
        self.val_only = val_only
        self.val_kw = val_kw
        self.val_kw_exists = True

        if(backend.find('epics') > -1):
            # an EpicsSignal here please
            if(self.can_write):
                self.signal = EpicsSignal(sig_name, write_pv=self.write_pv)
            else:
                self.signal = EpicsSignalRO(sig_name, auto_monitor=True)

        elif(backend.find('tango') > -1):
            # a Tango version of Signal here, just roughed in for now
            print('signal_base: ERROR: backend [%s] unsupported' % backend)
            exit()
        elif(backend.find('zmq') > -1):
            # a ZMQ version of Signal here, just roughed in for now
            print('signal_base: ERROR: backend [%s] unsupported' % backend)
            exit()
        else:
            print('signal_base: ERROR: backend [%s] unsupported' % backend)
            exit()

        #RUSS py3        self.signal.wait_for_connection()

        self.info = dict(called=False)
        self.signal.subscribe(self._sub_test, run=False, event_type=self.signal.SUB_VALUE)
        self.signal._read_pv.connection_callbacks.append(self.on_connection)

    def set(self, val):
        '''
        part of the API required to execute from a scan plan
        :param val:
        :return:
        '''
        self.put(val)
        st = DeviceStatus(self)
        st.done = True
        st.success = True
        return(st)

    def get_ophyd_device(self):
        return(self._ophyd_dev)

    def add_callback(self, func, **kwargs):
        self.signal.subscribe(func, run=False, event_type=self.signal.SUB_VALUE)


    def on_connection(self, pvname, conn, pv):
        if(conn):
            #print('BaseDevice: [%s] is connected' % pvname)
            self.on_connect.emit(self)
        else:
            #print('BaseDevice: [%s] is not connected' % pvname)
            pass


    def is_connected(self):
        return(self.signal.connected)

    def set_can_write(self, val):
        '''

        :param val:
        :return:
        '''
        self.can_write = val

    def set_return_val_only(self, val):
        '''

        :param val:
        :return:
        '''
        self.val_only = val

    def get_name(self):
        return (self.sig_name)

    def get_position(self):
        return (self.get())

    def report(self):
        """ return a dict that reresents all of the settings for this device """
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def get_report(self):
        """ return a dict that reresents all
         of the settings for this device

         To be implemented by the inheriting class
         """
        dct = {}
        return dct

    def get_desc(self):
        return(self.get_name())

    def get_egu(self):
        return(self.egu)

    def get_low_limit(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        return (None)

    def get_high_limit(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        return (None)

    def get_enum_str(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        print('get_enum_str: NEED TO IMPLEMENT THIS')
        return([])

    def get_enum_str_as_int(self):
        '''

        :return:
        '''
        # val = self.pv.get()
        # if (type(val) is int):
        #     final = val
        # else:
        #     final = int(self.pv.enum_strs[val])
        # return (final)
        print('get_enum_str_as_int: NEED TO IMPLEMENT THIS')
        return([])

    def put(self, val):
        if(self.can_write):
            if(SIMULATE):
                print('simulating a put of:  ', self.get_name(), val)
            else:
                self.signal.put(val)

    def get(self):
        #_logger.debug('GET: [%s]' % self.get_name())
        return(self.signal.get())

    def get_array(self):
        return (self.signal.get(as_numpy=True))

    def _sub_test(self, **kwargs):
        '''
            {'old_value': 5529854,
             'value': 5529855,
             'timestamp': 1547055932.448674,
             'sub_type': 'value',
             'obj': EpicsSignal(read_pv='TRG2400:cycles', name='TRG2400:cycles', value=5529855, timestamp=1547055932.448674,
                    pv_kw={}, auto_monitor=False, string=False, write_pv='TRG2400:cycles', limits=False, put_complete=False)}


            {'old_value': 49.94191734, 'value': 49.94235335, 'timestamp': 1547665997.231133, 'sub_type': 'value',
            'obj': EpicsSignal(read_pv='IOC:m103:OutputVolt_RBV', name='IOC:m103:OutputVolt_RBV',
            value=49.94235335, timestamp=1547665997.231133, pv_kw={},
            auto_monitor=False, string=False, write_pv='IOC:m103:OutputVolt_RBV',
            limits=False, put_complete=False)}
            :param kwargs:
            :return:
        '''

        self.info['called'] = True
        self.info['kw'] = kwargs
        if(self.val_only):
            if(self.val_kw_exists):
                if(self.val_kw in kwargs.keys()):
                    #print(kwargs)
                    # self._num_since_update = 0
                    val = kwargs[self.val_kw]
                    if(val != self._prev_val):
                        self.changed.emit(kwargs[self.val_kw])
                    else:
                        print('Skipping changed sig [%d]' % self._num_since_update)
                        self._num_since_update += 1
                    self._prev_val = kwargs[self.val_kw]
                else:
                    self.val_kw_exists = False

        else:
            #entire dict
            self.changed.emit(kwargs)





if __name__ == '__main__':
    #from .base_object import BaseObject

    def mycallback(kwargs):
        print(kwargs)

    app = QtWidgets.QApplication(sys.argv)
#    w = BaseDevice('IOC:m913.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    #obj = BaseObject('IOC:m912.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    #d = obj.add_device('IOC:m914.RBV', write_pv='IOC:m914.VAL', val_only=True, val_kw='timestamp')
    #s = obj.add_device('SYSTEM:mode:fbk', val_only=True, val_kw='value')

#    w.changed.connect(mycallback)
    #d.changed.connect(mycallback)
    #s.changed.connect(mycallback)
#    w.put(3999.123)
#    arr = BaseDevice('IOCE712:ddl:1')
#    a = arr.get_array()

    sv = BaseDevice('uhvCI:counter:Waveform_RBV', name='counter0')
    print(sv.info)
    print (sv.get())
    #d.put(-6749.321)
    #print('MODE fbk is: ',s.get())

    sys.exit(app.exec_())

