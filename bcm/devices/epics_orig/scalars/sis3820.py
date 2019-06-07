'''

Created on Apr 27, 2017

@author: bergr

Scalar
                Set MCS1607-801:mcs:inputMode = 1
                Set MCS1607-801:mcs:mode = 0
                Set MCS1607-801:mcs:triggerSource = 1
                Set MCS1607-801:mcs:source = 0
                Set MCS1607-801:mcs:nscan = 1
                Set MCS1607-801:mcs:scanCount = 1
                Set MCS1607-801:mcs:continuous = 0
                Set MCS1607-801:mcs16:enable = 1         (I0, noise until there is beam)
                Set MCS1607-801:mcs17:enable = 1         (I1, temporarily a sine wave with a period of 10s)
                Set MCS1607-801:mcs18:enable = 0         (1MHz reference, this is +- 1 count per second)



'''
from PyQt5 import QtCore
from bcm.device.base import BaseDevice


class SSI3820_Scalar(BaseDevice):
    """
    Represents a SIS3820 scalar
    """
    chfbk_changed = QtCore.pyqtSignal(object)

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]

        super(SSI3820_Scalar, self).__init__()

        self.prefix = prefix

        self.pv_input_mode = self.add_pv('%s:mcs:inputMode' % (prefix))
        self.pv_mode = self.add_pv('%s:mcs:mode' % (prefix))
        self.pv_trig_src = self.add_pv('%s:mcs:triggerSource' % (prefix))
        self.pv_src = self.add_pv('%s:mcs:source' % (prefix))
        self.pv_nscan = self.add_pv('%s:mcs:nscan' % (prefix))
        self.pv_scanCount = self.add_pv('%s:mcs:scanCount' % (prefix))
        self.pv_continuous = self.add_pv('%s:mcs:continuous' % (prefix))

        self.pv_chans = {}
        #add channel enables
        for i in range(0,31):

            en_pv = self.add_pv('%s:mcs%02d:enable' % (prefix, i))
            fbk_pv = self.add_pv('%s:mcs%02d:fbk' % (prefix, i))
            fbk_pv.add_callback(self.on_mcsfbk_changed, chan=i)

            self.pv_chans[i] = {'en_pv':en_pv, 'fbk_pv':fbk_pv}

    def on_mcsfbk_changed(self, **kwargs):
        chan = kwargs['chan']
        val = kwargs['value']
        #print 'on_mcsfbk_changed: [%d] = %.3f' % (chan, val)
        self.chfbk_changed.emit({'chan':chan, 'val':val})


    def set_input_mode(self, mode):
        self.pv_input_mode.put(mode)

    def set_mode(self, mode):
        self.pv_mode.put(mode)

    def set_trig_src(self, src):
        self.pv_trig_src.put(src)

    def set_src(self, src):
        self.pv_src.put(src)

    def set_nscan(self, n):
        self.pv_nscan.put(n)

    def set_scan_count(self, count):
        self.pv_scanCount.put(count)

    def set_continuous(self, c):
        self.pv_scanCount.put(c)

    def set_chan_enable(self, chan, en):
        pv = self.pv_chans[chan]['en_pv']
        pv.put(en)




if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets

    def on_ch_fbk_changed(fbk_dct):
        print('Chan[%d] = %.3f' % (fbk_dct['chan'], fbk_dct['val']))

    app = QtWidgets.QApplication(sys.argv)

    sis = SSI3820_Scalar('MCS1607-801')
    sis.chfbk_changed.connect(on_ch_fbk_changed)

    sis.set_chan_enable(0, 1)
    sis.set_chan_enable(30, 1)


    sys.exit(app.exec_())


