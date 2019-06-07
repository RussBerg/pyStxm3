'''

Created on Apr 27, 2017

@author: bergr

Zebra
        Set TRG1607-801:SOFT_IN:B0.HIGH = 0.1, unless you prefer explicitly setting it back to 0.
        Set TRG1607-801:PULSE2_INP = 60
        Set TRG1607-801:POLARITY:BD = 0
        Set TRG1607-801:PULSE2_WID = 1,  this configures a 1 ms pulse to be sent to the scalar
        Set TRG1607-801:PULSE2_DLY = 0
        Set TRG1607-801:PULSE2_PRE = 0
        Set TRG1607-801:OUT1_NIM = 53
        Set TRG1607-801:PC_DISARM = 1


'''
from PyQt5 import QtCore
from bcm.device.base import BaseDevice


class Zebra_Trig_Module(BaseDevice):
    """
    Represents a Zebra Trigger Module created at Diamond
    """
    chfbk_changed = QtCore.pyqtSignal(object)

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]

        super(Zebra_Trig_Module, self).__init__()

        self.prefix = prefix

        self.pv_pulse2_inp = self.add_pv('%s:PULSE2_INP' % (prefix))
        self.pv_polarity_bd = self.add_pv('%s:POLARITY:BD' % (prefix))
        self.pv_pulse_wid = self.add_pv('%s:PULSE2_WID' % (prefix))
        self.pv_pulse2_dly = self.add_pv('%s:PULSE2_DLY' % (prefix))
        self.pv_pulse2_pre = self.add_pv('%s:PULSE2_PRE' % (prefix))
        self.pv_out1_nim = self.add_pv('%s:OUT1_NIM' % (prefix))
        self.pv_pc_disarm = self.add_pv('%s:PC_DISARM' % (prefix))



    def set_pulse2_inp(self, inp):
        self.pv_pulse2_inp.put(inp)

    def set_polarity_bd(self, bd):
        self.pv_polarity_bd.put(bd)

    def set_tpulse_width(self, wid):
        self.pv_pulse_wid.put(wid)

    def set_pulse2_dly(self, dly):
        self.pv_pulse2_dly.put(dly)

    def set_pulse2_pre(self, pre):
        self.pv_pulse2_pre.put(pre)

    def set_out1_nim(self, nim):
        self.pv_out1_nim.put(nim)

    def set_pc_disarm(self, dis):
        self.pv_pc_disarm.put(dis)



if __name__ == "__main__":

    zebra = Zebra_Trig_Module('TRG1607-801')

    zebra.set_pulse2_inp(60)# was 60
    zebra.set_pulse2_dly(0.000) #was 0.0000


