import sys
from PyQt5 import QtWidgets, QtCore

from bcm.devices import BaseDevice

class BaseObject(QtCore.QObject):

    def __init__(self, base_signal_name, write_pv=None, val_only=False, val_kw='value', backend='epics'):
        super(BaseObject, self).__init__()
        self.base_signal_name = base_signal_name
        self.backend = backend
        self.devs = {}

    def report(self):
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def get_name(self):
        '''

        :return:
        '''
        return (self.base_signal_name)

    def on_change(self, val):
        self.changed.emit(val)

    def add_device(self, sig_name, write_pv=None, val_only=False, val_kw='value', is_dev_attr=False, _delim = '.'):
        '''
        :param sig_name:
        :param write_pv:
        :param val_only:
        :param val_kw:
        :param backend:
        :param is_dev_attr: basically all this means is that if the device is an attr to the main object then use the
        base_signal_name + sig_name, otherwise just use sig_name, makes it cleaner when adding addrs such as for an
        Mbbi object definition, then the attrs are stored in the self.devs by attr not the fully qualified name, so gets
        and puts become self.dev.put('VAL') as opposed to self.dev.put('BL1610-I10:ScanSelflag.A')
        :return:
        '''
        if(is_dev_attr):
            # construct the full name and store using just the attr name
            complete_sig_name = self.base_signal_name + _delim + sig_name
            self.devs[sig_name] = BaseDevice(complete_sig_name, write_pv=complete_sig_name, val_only=val_only, val_kw=val_kw,
                                             backend=self.backend)
        else:
            self.devs[sig_name] = BaseDevice(sig_name, write_pv=write_pv, val_only=val_only, val_kw=val_kw,
                                             backend=self.backend)
        return (self.devs[sig_name])

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
        if (sig_name):
            val = self.devs[sig_name].get()
        else:
            print('get: Error: sig_name [%s] does not exist' % sig_name)
            val = None
        return (val)

    def put(self, sig_name=None, val=None):
        '''
        here I set both args to None in the hopes that if a user
        :param sig_name:
        :param val:
        :return:
        '''
        if (sig_name is not None):
            if (val is not None):
                # use the passed in sig_name
                self.devs[sig_name].put(val)
            else:
                print('Error: put requires at least 2 arguments, 1 specified')
                return
        else:
            print('Error: put requires at least 2 arguments, 0 specified')
            return


if __name__ == '__main__':
    def mycallback(kwargs):
        print(kwargs)


    app = QtWidgets.QApplication(sys.argv)
    obj = BaseObject('IOC:m912.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    e = obj.add_device('IOC:m913.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    d = obj.add_device('IOC:m914.RBV', write_pv='IOC:m914.VAL', val_only=True, val_kw='timestamp')
    s = obj.add_device('SYSTEM:mode:fbk', val_only=True, val_kw='value')
    d.changed.connect(mycallback)
    e.changed.connect(mycallback)
    s.changed.connect(mycallback)
    d.put(-6749.321)
    e.put(-1749.321)
    print('MODE fbk is: ', s.get())

    sys.exit(app.exec_())
