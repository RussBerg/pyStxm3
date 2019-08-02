#!/usr/bin/python
from bcm.devices import BaseObject


class Bo(BaseObject):
    """
    Simple bo device
    """

    def __init__(self, base_signal_name=None, write_pv=None, desc=None, egu='', cb=None, ret_kwarg='value',
                 **cb_kwargs):

        super(Bo, self).__init__(base_signal_name, write_pv=base_signal_name + '.VAL', **cb_kwargs)

        self.attrs = ('VAL', 'OUT', 'NAME', 'DESC',
                      'ZNAM', 'ONAM')
        self.main_dev = self.add_device(base_signal_name)
        self.changed = self.main_dev.changed

        for _attr in self.attrs:
            # sig_name = self.base_signal_name + self._delim + '%s' % _attr
            # self.add_device(sig_name, write_pv=sig_name)
            self.add_device(_attr, is_dev_attr=True)

    def get_position(self):
        return (self.get('VAL'))

    def get(self, _attr):
        if (_attr in self.devs.keys()):
            return (self.devs[_attr].get())

    def put(self, val=None):
        return (self.devs['VAL'].put(val))


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets, QtCore

    def mycallback(kwargs):
        print(kwargs)

    app = QtWidgets.QApplication(sys.argv)
    t = Bo('BL1610-I10:ENERGY:uhv:enabled', val_only=False, val_kw='value')
    t.get('VAL')
    t.changed.connect(mycallback)

    sys.exit(app.exec_())