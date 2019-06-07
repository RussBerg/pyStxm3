#!/usr/bin/python
from bcm.devices import BaseObject

class Stringin(BaseObject):
    "Simple string input device"
    attrs = ('VAL','NAME','DESC','INP')

    def __init__(self, base_signal_name=None):
        super(Stringin, self).__init__(base_signal_name)

        for _attr in self.attrs:
            # sig_name = self.base_signal_name + self._delim + '%s' % _attr
            # self.add_device(sig_name, write_pv=sig_name)
            self.add_device(_attr, is_dev_attr=True)

