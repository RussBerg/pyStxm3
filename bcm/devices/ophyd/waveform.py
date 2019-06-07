from bcm.devices import BaseObject

class Waveform(BaseObject):
    "Simple string input device"
    attrs = ('NAME', 'INP','NELM','DESC','FTVL', 'RARM', 'VAL', 'NORD', 'BUSY')

    def __init__(self, base_signal_name=None):
        super(Waveform, self).__init__(base_signal_name)

        for _attr in self.attrs:
            # sig_name = self.base_signal_name + self._delim + '%s' % _attr
            # self.add_device(sig_name, write_pv=sig_name)
            self.add_device(_attr, is_dev_attr=True)

