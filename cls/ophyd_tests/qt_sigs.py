import sys

from typing import overload
from typing import Any, Optional

from ophyd.signal import (Signal, EpicsSignal, EpicsSignalRO, DerivedSignal)

from PyQt5 import QtWidgets, QtCore

class signal_base(QtCore.QObject):

    changed = QtCore.pyqtSignal(object)

    def __init__(self, sig_name, write_pv=None, val_only=False, val_kw='value', backend='epics'):
        super(signal_base, self).__init__()
        self.can_write = False
        if(write_pv):
            self.can_write = True

        self.backend = backend
        self.val_only = val_only
        self.val_kw = val_kw
        self.val_kw_exists = True

        if(backend.find('epics') > -1):
            # an EpicsSignal here please
            self.signal = EpicsSignal(sig_name, write_pv=write_pv)
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

        self.signal.wait_for_connection()
        self.info = dict(called=False)
        self.signal.subscribe(self._sub_test, run=False, event_type=self.signal.SUB_VALUE)


    def put(self, val):
        if(self.can_write):
            self.signal.put(val)

    def get(self):
        return(self.signal.get())

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
                    self.changed.emit(kwargs[self.val_kw])
                else:
                    self.val_kw_exists = False

        else:
            #entire dict
            self.changed.emit(kwargs)



class BaseDevice(QtCore.QObject):

    changed = QtCore.pyqtSignal(object)

    def __init__(self, sig_name, write_pv=None, val_only=False, val_kw='value', backend='epics'):
        super(BaseDevice, self).__init__()
        self.sig_name = sig_name
        self.devs = {}
        self.devs[sig_name] = signal_base(sig_name, write_pv=write_pv, val_only=val_only, val_kw=val_kw, backend=backend)
        self.devs[sig_name].changed.connect(self.on_change)

    def get_name(self):
        '''

        :return:
        '''
        return(self.sig_name)

    def on_change(self, val):
        self.changed.emit(val)

    def add_device(self, sig_name, write_pv=None, val_only=False, val_kw='value', backend='epics'):
        '''
        :param sig_name:
        :param write_pv:
        :param val_only:
        :param val_kw:
        :param backend:
        :return:
        '''
        self.devs[sig_name] = signal_base(sig_name, write_pv=write_pv, val_only=val_only, val_kw=val_kw,
                                          backend=backend)
        return(self.devs[sig_name])

    def add_callback(self, sig_name, cb):
        '''
        :param sig_name:
        :param cb:
        :return:
        '''
        self.devs[sig_name].changed.connect(cb)

    def remove_callback(self, sig_name):
        '''

        :param sig_name:
        :return:
        '''
        self.devs[sig_name].disconnect()

    def get(self, sig_name=None):
        '''

        :param sig_name:
        :return:
        '''
        if(sig_name):
            val = self.devs[sig_name].get()
        else:
            val = self.devs[self.sig_name].get()
        return(val)

    def put(self, sig_name=None, val=None):
        '''
        here I set both args to None in the hopes that if a user
        :param sig_name:
        :param val:
        :return:
        '''
        if(val is None):
            if(sig_name is None):
                print('Error: put requires at least 1 argument, 0 specified')
                return
            else:
                #the arg passed is the value
                val = sig_name
            self.devs[self.sig_name].put(val)
        else:
            #use the passed in sig_name
            self.devs[sig_name].put(val)


if __name__ == '__main__':
    def mycallback(kwargs):
        print(kwargs)

    app = QtWidgets.QApplication(sys.argv)
    w = BaseDevice('IOC:m913.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    d = w.add_device('IOC:m914.RBV', write_pv='IOC:m914.VAL', val_only=True, val_kw='timestamp')
    s = w.add_device('SYSTEM:mode:fbk', val_only=True, val_kw='value')
    w.changed.connect(mycallback)
    d.changed.connect(mycallback)
    s.changed.connect(mycallback)
    w.put(-3999.123)
    d.put(-6749.321)
    print('MODE fbk is: ',s.get())

    sys.exit(app.exec_())
