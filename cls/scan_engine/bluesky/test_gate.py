import time as ttime
import numpy as np

import ophyd
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, DeviceStatus
from cls.utils.enum_utils import Enum
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
trig_types = Enum('DAQmx_Val_None', 'DAQmx_Val_AnlgEdge', 'DAQmx_Val_AnlgWin', 'DAQmx_Val_DigEdge',
                  'DAQmx_Val_DigPattern', 'SOFT_TRIGGER')

trig_src_types = Enum('NORMAL_PXP', 'NORMAL_LXL', 'E712')


class GateDevice(ophyd.Device):
    run = Cpt(EpicsSignal, 'Run', kind='omitted')

    def __init__(self, prefix, name):
        super(GateDevice, self).__init__(prefix, name=name)

    def stage(self):
        st = super().trigger()
        self.run.put(1)
        st._finished = True
        return(st)

    def unstage(self):
        st = super().trigger()
        self.run.put(0)
        st._finished = True
        return(st)


class BaseCounterOutputDevice(ophyd.Device):
    run = Cpt(EpicsSignal, 'Run', kind='omitted')
    device_select = Cpt(EpicsSignal, 'DeviceSelect', kind='config')
    counter_select = Cpt(EpicsSignal, 'CounterSelect', kind='config')
    initial_count = Cpt(EpicsSignal, 'InitialCount', kind='config')
    count_dir = Cpt(EpicsSignal, 'CountDir', kind='config')
    max_points = Cpt(EpicsSignal, 'MaxPoints', kind='config')
    sample_mode = Cpt(EpicsSignal, 'SampleMode', kind='config')
    signal_src_clock_select = Cpt(EpicsSignal, 'SignalSrcClockSelect', kind='config')
    edge_select = Cpt(EpicsSignal, 'EdgeSelect', kind='config')
    retriggerable = Cpt(EpicsSignal, 'Retriggerable', kind='config')
    trig_type = Cpt(EpicsSignal, 'TriggerType', kind='config')
    trig_src_select = Cpt(EpicsSignal, 'TrigSrcSelect', kind='config')
    dwell = Cpt(EpicsSignal, 'Dwell', kind='config')
    max_points = Cpt(EpicsSignal, 'MaxPoints', kind='config')
    duty_cycle = Cpt(EpicsSignal, 'DutyCycle', kind='config')
    sample_mode = Cpt(EpicsSignal, 'SampleMode', kind='config')
    output_idle_state = Cpt(EpicsSignal, 'OutputIdleState', kind='config')
    clock_src_select = Cpt(EpicsSignal, 'ClockSrcSelect', kind='config')
    trigger_delay = Cpt(EpicsSignal, 'TriggerDelay', kind='config')
    soft_trigger = Cpt(EpicsSignal, 'SoftTrigger', kind='config')
    run_rbv = Cpt(EpicsSignalRO, 'Run_RBV', kind='omitted')

    #self.runningcb_idx = self.add_callback('Run_RBV', self.on_running)

    def __init__(self, prefix, name):
        super(BaseCounterOutputDevice, self).__init__(prefix, name=name)
        self.cntr = 0
        self.p_dwell = 1.0
        self.p_duty_cycle = 0.5
        self.p_num_points = 1
        self.p_trig_src = 4
        self.trig = None
        self.mode = bs_dev_modes.NORMAL_PXP # 0 == point, 1 == line

    def report(self):
        print('\tname = %s, type = %s' % (str(self.__class__), self.name))

    def set_trig_src(self, src=trig_src_types.NORMAL_PXP):
        assert src in trig_src_types._dict.keys(), "src must be of type trig_src_types"
        if(src in trig_src_types._dict.keys()):
            if(src is trig_src_types.NORMAL_PXP):
                self.p_trig_src = 4
            elif(src is trig_src_types.NORMAL_LXL):
                self.p_trig_src = 3
            elif(src is trig_src_types.E712):
                self.p_trig_src = 3
        self.trig_src_select.put(self.p_trig_src)

    def set_mode(self, val):
        self.mode = val

    def set_dwell(self, val):
        self.p_dwell = val
        self.dwell.put(val)

    def set_duty_cycle(self, val):
        self.p_duty_cycle = val
        self.duty_cycle.put(val)

    def set_num_points(self, val):
        self.p_num_points = val
        self.max_points.put(self.p_num_points)

    def stage(self):
        super().stage()
        self.run.put(1)
        st = DeviceStatus(self)
        st._finished = True
        return (st)

    def unstage(self):
        super().unstage()
        self.run.put(0)
        st = DeviceStatus(self)
        st._finished = True
        return (st)

    def trigger(self):
        st = DeviceStatus(self)
        self.read_counts.put(1, callback=st._finished)
        return st

    def read(self):
        #print('TestDetectorDevice: read called')
        #return(self.single_value_rbv.get())
        self.cntr += 1

        return {self.name + '_single_value_rbv': {'value': self.single_value_rbv.get(),
                            'cntr': self.cntr, 'timestamp': ttime.time()}}

    def describe(self):
        #print('TestDetectorDevice: describe called')
        res = super().describe()
        for key in res:
            res[key]['units'] = "counts"
        return res

    #def configure(self, num_points=1, dwell=2.0, duty=0.5, soft_trig=False, trig_delay=0.0):
    def configure(self, soft_trig=False, trig_delay=0.0):
        # self.p_dwell = dwell
        # self.p_duty_cycle = duty
        # self.p_num_points = num_points
        if (self.mode is bs_dev_modes.NORMAL_PXP):
            self.max_points.put(self.p_num_points)
        else:
            self.max_points.put(self.p_num_points + 2)
        self.dwell.put(self.p_dwell)
        self.duty_cycle.put(self.p_duty_cycle)
        self.trig_delay.put(trig_delay)

        if (self.trig is not None):
            self.trig_type.put(trig_types.SOFT_TRIGGER)
        else:
            self.trig_type.put(trig_types.DAQMX_VAL_DIGEDGE)

    def load_defaults(self):
        self.set_duty_cycle(0.5)
        self.set_num_points(1)
        self.retrig.set(0)

    def open(self):
        self.start()

    def start(self):
        self.run.put(1)

    # self.isRunning = 1

    def do_trigger(self):
        if (self.trig is not None):
            self.trig.put(1)

class GateDevice(BaseCounterOutputDevice):

    def __init__(self, prefix, name):
        super(GateDevice, self).__init__(prefix, name=name)

    def stage(self):
        if(self.mode is bs_dev_modes.NORMAL_PXP):
            self.do_point_config()
        else:
            self.do_line_config()
        self.cntr = 0
        self.run.put(1)
        st = super().stage()
        return(st)

    def unstage(self):
        st = super().unstage()
        return (st)

    def configure(self, num_points=1, dwell=1.0, duty=0.5, soft_trig=False, trig_delay=0.0):

        self.max_points.put(num_points)
        self.dwell.put(dwell)
        self.duty_cycle.put(duty)
        self.trigger_delay.put(trig_delay)

        if (self.trig is not None):
            self.trig_type.put(trig_types.SOFT_TRIGGER)
        else:
            self.trig_type.put(trig_types.DAQMX_VAL_DIGEDGE)

    def do_point_config(self):
        """ a convienience function to have a single place to configure the devices to acquire single points """

        self.set_num_points(1)
        self.set_duty_cycle(0.9999)
        #trig_src_pfi = 4
        self.configure(1, dwell=self.p_dwell, duty=0.999, trig_delay=0.0)
        self.trig_src_select.put(self.p_trig_src)  # /PFI 4  this will need to be part of a configuration at some point
        self.retriggerable.put(1)

    def do_line_config(self):
        """ a convienience function to have a single place to configure the devices to acquire single points """

        #trig_src_pfi = 3
        xnpoints = self.p_num_points + 2
        self.configure(num_points=xnpoints, dwell=self.p_dwell, duty=0.5)
        self.trig_src_select.put(self.p_trig_src)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire
        self.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
        self.trig_src_select.put(self.p_trig_src)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire



