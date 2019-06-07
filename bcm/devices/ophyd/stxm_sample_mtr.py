'''
Created on 2014-07-03

@author: bergr
'''
#!/usr/bin/env python

from bcm.devices import Motor_Qt
from ophyd.signal import (EpicsSignal, EpicsSignalRO)
from ophyd.device import (Device, Component as Cpt)

class sample_abstract_motor(Motor_Qt):
    """
    Represents an abstract motor that connects to a defined set of PV's of an Abstract positioner (Coarse Stepper Motor and Fine piezo motor combined) 
    """

    #attrs = ('VAL')
    

    def __init__(self, signal_name, **kwargs):
        # if signal_name.endswith('.'):
        #     signal_name = signal_name[:-1]
        Motor_Qt.__init__(self, signal_name, **kwargs)
        myattrs = ('Mode', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'AtzSetCoarsePos')
        
        for attr in myattrs:
            devname = '%s:%s' % (signal_name, attr)
            self.add_dev(devname, attr=attr)


class sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    #attrs = ('VAL')
    

    def __init__(self, signal_name, **kwargs):
        # if signal_name.endswith('.'):
        #     signal_name = signal_name[:-1]
        Motor_Qt.__init__(self, signal_name, **kwargs)
        myattrs = ('Mode', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'ServoPower', \
				'ServoPower_RBV', 'OutputVolt_RBV', 'AutoZero')
        
        for attr in myattrs:
            devname = '%s:%s' % (signal_name, attr)
            self.add_dev(devname, attr=attr)


class e712_sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    Mode = Cpt(EpicsSignal, ':Mode', kind='omitted')
    ScanStart = Cpt(EpicsSignal, ':ScanStart', kind='omitted')
    MarkerStart = Cpt(EpicsSignal, ':MarkerStart', kind='omitted')
    MarkerStop = Cpt(EpicsSignal, ':MarkerStop', kind='omitted')
    SetMarker = Cpt(EpicsSignal, ':SetMarker', kind='omitted')
    ServoPower = Cpt(EpicsSignal, ':ServoPower', kind='omitted')
    ServoPower_RBV = Cpt(EpicsSignalRO, ':ServoPower_RBV', kind='omitted')
    OutputVolt_RBV = Cpt(EpicsSignalRO, ':OutputVolt_RBV', kind='omitted')
    AutoZero = Cpt(EpicsSignal, ':AutoZero', kind='omitted')
    DigFltBWidth_RBV = Cpt(EpicsSignalRO, ':DigFltBWidth_RBV', kind='omitted')
    DigFltParm1_RBV = Cpt(EpicsSignalRO, ':DigFltParm1_RBV', kind='omitted')
    DigFltParm2_RBV = Cpt(EpicsSignalRO, ':DigFltParm2_RBV', kind='omitted')
    DigFltParm3_RBV = Cpt(EpicsSignalRO, ':DigFltParm3_RBV', kind='omitted')
    DigFltParm4_RBV = Cpt(EpicsSignalRO, ':DigFltParm4_RBV', kind='omitted')
    DigFltParm5_RBV = Cpt(EpicsSignalRO, ':DigFltParm5_RBV', kind='omitted')
    CapSensBParm_RBV = Cpt(EpicsSignalRO, ':CapSensBParm_RBV', kind='omitted')
    CapSensMParm_RBV = Cpt(EpicsSignalRO, ':CapSensMParm_RBV', kind='omitted')
    PTerm_RBV = Cpt(EpicsSignalRO, ':PTerm_RBV', kind='omitted')
    ITerm_RBV = Cpt(EpicsSignalRO, ':ITerm_RBV', kind='omitted')
    DTerm_RBV = Cpt(EpicsSignalRO, ':DTerm_RBV', kind='omitted')
    SlewRate_RBV = Cpt(EpicsSignalRO, ':SlewRate_RBV', kind='omitted')
    NotchFreq1_RBV = Cpt(EpicsSignalRO, ':NotchFreq1_RBV', kind='omitted')
    NotchFreq2_RBV = Cpt(EpicsSignalRO, ':NotchFreq2_RBV', kind='omitted')
    NotchReject1_RBV = Cpt(EpicsSignalRO, ':NotchReject1_RBV', kind='omitted')
    NotchReject2_RBV = Cpt(EpicsSignalRO, ':NotchReject2_RBV', kind='omitted')
    NotchBW1_RBV = Cpt(EpicsSignalRO, ':NotchBW1_RBV', kind='omitted')
    NotchBW2_RBV = Cpt(EpicsSignalRO, ':NotchBW2_RBV', kind='omitted')

    def __init__(self, signal_name, **kwargs):
        # if signal_name.endswith('.'):
        #     signal_name = signal_name[:-1]
        Motor_Qt.__init__(self, signal_name, **kwargs)
        # myattrs = (
        # 'Mode', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'ServoPower', \
        # 'ServoPower_RBV', 'OutputVolt_RBV', 'AutoZero', 'DigFltBWidth_RBV','DigFltParm1_RBV','DigFltParm2_RBV','DigFltParm3_RBV' , \
        # 'DigFltParm4_RBV' ,'DigFltParm5_RBV' ,'CapSensBParm_RBV','CapSensMParm_RBV','PTerm_RBV', 'ITerm_RBV', 'DTerm_RBV', 'SlewRate_RBV','NotchFreq1_RBV', \
        # 'NotchFreq2_RBV', 'NotchReject1_RBV','NotchReject2_RBV', 'NotchBW1_RBV','NotchBW2_RBV.get()

        # for attr in myattrs:
        #     devname = '%s:%s' % (signal_name, attr)
        #     self.add_dev(devname, attr, **kwargs)



    def get_stage_params(self):
        dct = {}
        dct['DigFltBWidth'] = self.DigFltBWidth_RBV.get()
        dct['DigFltParm1'] = self.DigFltParm1_RBV.get()
        dct['DigFltParm2'] = self.DigFltParm2_RBV.get()
        dct['DigFltParm3'] = self.DigFltParm3_RBV.get()
        dct['DigFltParm4'] = self.DigFltParm4_RBV.get()
        dct['DigFltParm5'] = self.DigFltParm5_RBV.get()
        dct['CapSensBParm'] = self.CapSensBParm_RBV.get()
        dct['CapSensMParm'] = self.CapSensMParm_RBV.get()
        dct['PTerm'] = self.PTerm_RBV.get()
        dct['ITerm'] = self.ITerm_RBV.get()
        dct['DTerm'] = self.DTerm_RBV.get()
        dct['SlewRate'] = self.SlewRate_RBV.get()
        #dct['SlewRate'] = self.velocity')
        dct['NotchFreq1'] = self.NotchFreq1_RBV.get()
        dct['NotchFreq2'] = self.NotchFreq2_RBV.get()
        dct['NotchReject1'] = self.NotchReject1_RBV.get()
        dct['NotchReject2'] = self.NotchReject2_RBV.get()
        dct['NotchBW1'] = self.NotchBW1_RBV.get()
        dct['NotchBW2'] = self.NotchBW2_RBV.get()

        return(dct)
            

if __name__ == "__main__":
    
    mtr = sample_motor('IOC:m100')
    print(mtr.RBV.get())
    