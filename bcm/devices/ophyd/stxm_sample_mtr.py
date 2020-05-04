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
    Represents an abstract motor that connects to a defined set of PV's of an Abstract positioner
    (Coarse Stepper Motor and Fine piezo motor combined), this implementation is particular to the Abstract Epics motor
    driver developed at teh CLS specifically for the STXM,
        mode - in teh driver there are 7 "modes" that determine how the driver controls the steppers and piezo's
        scan_start - is the position that a scan will start from, this position includes the acceleration distance
        scan_stop  - is teh position that a scan will use to stop at, this position includes the decceleration distance
        marker_start - is the position that the driver will trigger a digital out that is used to start the pulse train generation
        marker_stop - is the position that the pulse train generation will stop
        set_marker - will set the trigger position, is typically used to set a position that will not trigger when motor returns to scan_start
        atz_set_coarse_pos - a function that AutoZero's the piezo stage then sets its position to the current coarse stage position value
    """
    mode = Cpt(EpicsSignal, ':Mode', kind='omitted')
    scan_start = Cpt(EpicsSignal, ':ScanStart', kind='omitted')
    scan_stop = Cpt(EpicsSignal, ':ScanStop', kind='omitted')
    marker_start = Cpt(EpicsSignal, ':MarkerStart', kind='omitted')
    marker_stop = Cpt(EpicsSignal, ':MarkerStop', kind='omitted')
    set_marker = Cpt(EpicsSignal, ':SetMarker', kind='omitted')
    atz_set_coarse_pos = Cpt(EpicsSignal, ':AtzSetCoarsePos', kind='omitted')


    def __init__(self, signal_name, **kwargs):
        Motor_Qt.__init__(self, signal_name, **kwargs)
        # myattrs = ('Mode', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'AtzSetCoarsePos')
        #
        # for attr in myattrs:
        #     devname = '%s:%s' % (signal_name, attr)
        #     self.add_dev(devname, attr=attr)
        # mode defines
        self.MODE_NORMAL = 0
        self.MODE_LINE_UNIDIR = 1
        self.MODE_LINE_BIDIR = 2
        self.MODE_POINT = 3
        self.MODE_COARSE = 4
        self.MODE_SCAN_START = 5
        self.MODE_MOVETO_SET_CPOS = 6

    def set_mode(self, mode):
        '''
        put the mode value to the PV
        :param mode:
        :return:
        '''
        self.mode.put(mode)

    def config_start_stop(self, start=0.0, stop=0.0, npts=1, accRange=0.0, deccRange=1.0, line=True):
        """
        config_samplex_start_stop(): description

        :param start: start description
        :type start: start type

        :param stop: stop description
        :type stop: stop type

        :param npts: npts description
        :type npts: npts type

        :param accRange=0.0: accRange=0.0 description
        :type accRange=0.0: accRange=0.0 type

        :param deccRange=0.0: accRange=0.0 description
        :type deccRange=0.0: accRange=0.0 type

        :param line=True: line=True description
        :type line=True: line=True type
        :returns: None
        """
        if(line):
            lstart = start - accRange
            lstop = stop + deccRange
            #start
            #self._config_start_stop(xscan, x_posnum, lstart, lstop, 2)
            self.scan_start.put(lstart)
            self.scan_stop.put(lstop)
            self.marker_start.put(start)
            self.marker_stop.put(stop)
            self.set_marker.put(1000000)
        else:
            self.scan_start.put(1000000)
            self.scan_stop.put(1000000)
            self.marker_start.put(1000000)
            self.marker_stop.put(1000000)
            self.set_marker.put(1000000)



class sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    mode = Cpt(EpicsSignal, ':Mode', kind='omitted')
    scan_start = Cpt(EpicsSignal, ':ScanStart', kind='omitted')
    scan_stop = Cpt(EpicsSignal, ':ScanStop', kind='omitted')
    marker_start = Cpt(EpicsSignal, ':MarkerStart', kind='omitted')
    marker_stop = Cpt(EpicsSignal, ':MarkerStop', kind='omitted')
    set_marker = Cpt(EpicsSignal, ':SetMarker', kind='omitted')
    auto_zero = Cpt(EpicsSignal, ':AutoZero', kind='omitted')
    servo_power = Cpt(EpicsSignal, ':ServoPower', kind='omitted')
    servo_power_rbv = Cpt(EpicsSignalRO, ':ServoPower_RBV', kind='omitted')
    output_volt_rbv = Cpt(EpicsSignalRO, ':OutputVolt_RBV', kind='omitted')


    def __init__(self, signal_name, **kwargs):
        # if signal_name.endswith('.'):
        #     signal_name = signal_name[:-1]
        Motor_Qt.__init__(self, signal_name, **kwargs)
        # myattrs = ('Mode', 'ScanStart', 'ScanStop', 'MarkerStart', 'MarkerStop', 'SetMarker', 'ServoPower', \
        # 		'ServoPower_RBV', 'OutputVolt_RBV', 'AutoZero')
        #
        # for attr in myattrs:
        #     devname = '%s:%s' % (signal_name, attr)
        #     self.add_dev(devname, attr=attr)
        self.MODE_NORMAL = 0
        self.MODE_LINE_UNIDIR = 1
        self.MODE_LINE_BIDIR = 2
        self.MODE_POINT = 3
        self.MODE_COARSE = 4
        self.MODE_SCAN_START = 5
        self.MODE_MOVETO_SET_CPOS = 6

        self.POWER_OFF = 0
        self.POWER_ON = 1

    def set_power(self, val):
        '''
        turn on or off teh power to the stage
        :param val:
        :return:
        '''
        self.servo_power.put(val)

    def set_mode(self, mode):
        '''
        put the mode value to the PV
        :param mode:
        :return:
        '''
        self.mode.put(mode)


    def config_start_stop(self, start=0.0, stop=0.0, npts=1, accRange=0.0, deccRange=1.0, line=True):
        """
        config_samplex_start_stop(): description

        :param start: start description
        :type start: start type

        :param stop: stop description
        :type stop: stop type

        :param npts: npts description
        :type npts: npts type

        :param accRange=0.0: accRange=0.0 description
        :type accRange=0.0: accRange=0.0 type

        :param deccRange=0.0: accRange=0.0 description
        :type deccRange=0.0: accRange=0.0 type

        :param line=True: line=True description
        :type line=True: line=True type
        :returns: None
        """
        if (line):
            lstart = start - accRange
            lstop = stop + deccRange
            # start
            # self._config_start_stop(xscan, x_posnum, lstart, lstop, 2)
            self.scan_start.put(lstart)
            self.scan_stop.put(lstop)
            self.marker_start.put(start)
            self.marker_stop.put(stop)
            self.set_marker.put(1000000)
        else:
            self.scan_start.put(1000000)
            self.scan_stop.put(1000000)
            self.marker_start.put(1000000)
            self.marker_stop.put(1000000)
            self.set_marker.put(1000000)




class e712_sample_motor(Motor_Qt):
    """
    Represents an motor that is typically a piezo motor, either a sample fine stage or a zoneplate X/Y stage 
    """

    mode = Cpt(EpicsSignal, ':Mode', kind='omitted')
    scan_start = Cpt(EpicsSignal, ':ScanStart', kind='omitted')
    scan_stop = Cpt(EpicsSignal, ':ScanStop', kind='omitted')
    marker_start = Cpt(EpicsSignal, ':MarkerStart', kind='omitted')
    marker_stop = Cpt(EpicsSignal, ':MarkerStop', kind='omitted')
    set_marker = Cpt(EpicsSignal, ':SetMarker', kind='omitted')
    auto_zero = Cpt(EpicsSignal, ':AutoZero', kind='omitted')
    servo_power = Cpt(EpicsSignal, ':ServoPower', kind='omitted')
    servo_power_rbv = Cpt(EpicsSignalRO, ':ServoPower_RBV', kind='omitted')
    output_volt_rbv = Cpt(EpicsSignalRO, ':OutputVolt_RBV', kind='omitted')

    dig_flt_bwidth_rbv = Cpt(EpicsSignalRO, ':DigFltBWidth_RBV', kind='omitted')
    dig_flt_parm1_rbv = Cpt(EpicsSignalRO, ':DigFltParm1_RBV', kind='omitted')
    dig_flt_parm2_rbv = Cpt(EpicsSignalRO, ':DigFltParm2_RBV', kind='omitted')
    dig_flt_parm3_rbv = Cpt(EpicsSignalRO, ':DigFltParm3_RBV', kind='omitted')
    dig_flt_parm4_rbv = Cpt(EpicsSignalRO, ':DigFltParm4_RBV', kind='omitted')
    dig_flt_parm5_rbv = Cpt(EpicsSignalRO, ':DigFltParm5_RBV', kind='omitted')
    cap_sens_b_parm_rbv = Cpt(EpicsSignalRO, ':CapSensBParm_RBV', kind='omitted')
    cap_sens_m_parm_rbv = Cpt(EpicsSignalRO, ':CapSensMParm_RBV', kind='omitted')
    p_term_rbv = Cpt(EpicsSignalRO, ':PTerm_RBV', kind='omitted')
    i_term_rbv = Cpt(EpicsSignalRO, ':ITerm_RBV', kind='omitted')
    d_term_rbv = Cpt(EpicsSignalRO, ':DTerm_RBV', kind='omitted')
    slew_rate_rbv = Cpt(EpicsSignalRO, ':SlewRate_RBV', kind='omitted')
    notch_freq1_rbv = Cpt(EpicsSignalRO, ':NotchFreq1_RBV', kind='omitted')
    notch_freq2_rbv = Cpt(EpicsSignalRO, ':NotchFreq2_RBV', kind='omitted')
    notch_reject1_rbv = Cpt(EpicsSignalRO, ':NotchReject1_RBV', kind='omitted')
    notch_reject2_rbv = Cpt(EpicsSignalRO, ':NotchReject2_RBV', kind='omitted')
    notch_bw1_rbv = Cpt(EpicsSignalRO, ':NotchBW1_RBV', kind='omitted')
    notch_bw2_rbv = Cpt(EpicsSignalRO, ':NotchBW2_RBV', kind='omitted')

    def __init__(self, signal_name, **kwargs):
        Motor_Qt.__init__(self, signal_name, **kwargs)

    def get_stage_params(self):
        dct = {}
        dct['DigFltBWidth'] = self.dig_flt_bwidth_rbv.get()
        dct['DigFltParm1'] = self.dig_flt_parm1_rbv.get()
        dct['DigFltParm2'] = self.dig_flt_parm2_rbv.get()
        dct['DigFltParm3'] = self.dig_flt_parm3_rbv.get()
        dct['DigFltParm4'] = self.dig_flt_parm4_rbv.get()
        dct['DigFltParm5'] = self.dig_flt_parm5_rbv.get()
        dct['CapSensBParm'] = self.cap_sens_b_parm_rbv.get()
        dct['CapSensMParm'] = self.cap_sens_m_parm_rbv.get()
        dct['PTerm'] = self.p_term_rbv.get()
        dct['ITerm'] = self.i_term_rbv.get()
        dct['DTerm'] = self.d_term_rbv.get()
        dct['SlewRate'] = self.slew_rate_rbv.get()
        #dct['SlewRate'] = self.velocity')
        dct['NotchFreq1'] = self.notch_freq1_rbv.get()
        dct['NotchFreq2'] = self.notch_freq2_rbv.get()
        dct['NotchReject1'] = self.notch_reject1_rbv.get()
        dct['NotchReject2'] = self.notch_reject2_rbv.get()
        dct['NotchBW1'] = self.notch_bw1_rbv.get()
        dct['NotchBW2'] = self.notch_bw2_rbv.get()

        return(dct)
            

if __name__ == "__main__":
    
    mtr = sample_motor('IOC:m100')
    print(mtr.RBV.get())
    