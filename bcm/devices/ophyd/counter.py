r""" Counter Device objects

A counter device enables counting and averaging over given time periods.

Each Counter device obeys the following interface:

	methods:

	count(time)
		count for the specified amount of time and return the numeric value
		corresponding to the average count. This method blocks for the specified 
		time.

"""
import os
import time
import queue
import atexit
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal
import numpy as np

from bcm.devices import BaseObject

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.thread_logger import doprint
from cls.utils.enum_utils import Enum

trig_types = Enum('DAQmx_Val_None', 'DAQmx_Val_AnlgEdge', 'DAQmx_Val_AnlgWin', 'DAQmx_Val_DigEdge',
                  'DAQmx_Val_DigPattern', 'SOFT_TRIGGER')

hostname = os.getenv('COMPUTERNAME')
if (hostname == 'WKS-W001465'):
    # the new test computer in old magnet mapping room
    GENERATE_DATA = False
elif (hostname == 'NBK-W001021'):
    # my notebook computer
    SIMULATE = True
    GENERATE_DATA = True
else:
    # teh old stxm_control conmputer
    SIMULATE = False
    GENERATE_DATA = False

DATA_OFFSET = 2


# setup module logger with a default do-nothing handler
# _logger = get_module_logger(__name__)

class CounterError(Exception):
    """Base class for errors in the counter module."""


class Counter(BaseObject):
    """class for counters that are accessed as epics PV's in the counter module."""
    changed = pyqtSignal(object, object)  # device, state
    new_data = pyqtSignal(object, object)  # row num, data

    ##implements(ICounter)

    def __init__(self, base_signal_name=None, zero=0, **kwargs):
        super(Counter, self).__init__(base_signal_name=base_signal_name, **kwargs)
        self.zero = float(zero)
        self.value = None
        self.DESC = ''

        self.changed.connect(self.on_device_active)

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'name', self.get_name())
        return (dct)

    def _on_name_change(self, pv, val):
        if val != '':
            self.name = val

    def count(self, t):
        if t <= 0.0:
            return self.value.get() - self.zero

        doprint('debug', 'Averaging detector (%s) for %0.2f sec.' % (self.name, t))
        interval = 0.01
        values = []
        time_left = t
        while time_left > 0.0:
            values.append(self.value.get())
            time.sleep(interval)
            time_left -= interval
        total = (sum(values, 0.0) / len(values)) - self.zero
        doprint('debug', '(%s) Returning average of %d values for %0.2f sec.' % (self.name, len(values), t))
        return total


def make_counter(num_samples):
    if (GENERATE_DATA):
        print('make_counter: making counter to generate data')
        counter = DAQmxLineCounter('', cntrName=r'/Dev4/Ctr2', srcTerminal=r'/Dev4/PFI0', gateTerminal=r'/Dev4/PFI1',
                                   dwell=0.050, num_samples=num_samples, dcOffset=0.0)
        return (counter)
    else:
        print('make_counter: making real counter')
        counter = DAQmxLineCounter('', cntrName=r'/Dev2/ctr0', num_samples=num_samples)
        return (counter)


class BaseGate(BaseObject):
    """
    This class represents a counter output task that generates a pulse train used to gate other
    counter tasks, this it is stored here in the counter module
    """

    # def __init__(self, prefix, num_points=1, dwell=2.0, duty=0.5, soft_trig=False):
    def __init__(self, base_signal_name=None, **kwargs):
        super(BaseGate, self).__init__(base_signal_name=base_signal_name, **kwargs)
        self.p_dwell = 2.0
        self.p_duty_cycle = 0.5
        self.p_num_points = 1

        self.run = self.add_device('Run', _delim=':', is_dev_attr=True)
        self.dwell = self.add_device('Dwell',_delim=':', is_dev_attr=True)
        self.max_points = self.add_device('MaxPoints', _delim=':', is_dev_attr=True)
        self.duty_cycle = self.add_device('DutyCycle', _delim=':', is_dev_attr=True)
        self.trig_type = self.add_device('TriggerType', _delim=':', is_dev_attr=True)
        self.trig_delay = self.add_device('TriggerDelay', _delim=':', is_dev_attr=True)
        self.retrig = self.add_device('Retriggerable', _delim=':', is_dev_attr=True)

        self.device_select = self.add_device('DeviceSelect', _delim=':', is_dev_attr=True)
        self.counter_select = self.add_device('CounterSelect', _delim=':', is_dev_attr=True)
        self.sample_mode = self.add_device('SampleMode', _delim=':', is_dev_attr=True)
        self.output_idle_state = self.add_device('OutputIdleState', _delim=':', is_dev_attr=True)
        self.clock_src_select = self.add_device('ClockSrcSelect', _delim=':', is_dev_attr=True)
        self.retriggerable = self.add_device('Retriggerable', _delim=':', is_dev_attr=True)
        self.trigger_type = self.add_device('TriggerType', _delim=':', is_dev_attr=True)
        self.trig_src_select = self.add_device('TrigSrcSelect', _delim=':', is_dev_attr=True)
        self.edge_select = self.add_device('EdgeSelect', _delim=':', is_dev_attr=True)
        self.trigger_delay = self.add_device('TriggerDelay', _delim=':', is_dev_attr=True)
        self.soft_trigger = self.add_device('SoftTrigger', _delim=':', is_dev_attr=True)
        self.run_rbv = self.add_device('Run_RBV', _delim=':', is_dev_attr=True)

        self.runningcb_idx = self.add_callback('Run_RBV', self.on_running)

        self.trig = None

        # if(soft_trig):
        #	self.trig = self.add_device('SoftTrigger')

        self.isRunning = 0
        time.sleep(0.4)
        self.stop()

    # self.configure()
    def get_name(self):
        return (self.p_prefix + ':Run')

    # def on_running(self, **kwargs):
    #     rawData = kwargs['value']
    #     # print 'BaseGate: on_running' , kwargs
    #     self.isRunning = kwargs['value']
    def on_running(self, val):
        # print 'BaseGate: on_running' , kwargs
        self.isRunning = val

    def wait_till_stopped(self, proc_qt_msgs=True):
        while self.isRunning:
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()

    def wait_till_running(self, proc_qt_msgs=True):
        while not self.isRunning:
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()

    def wait_till_running_polling(self, proc_qt_msgs=True):
        idx = 0
        while (not self.run_rbv.get() and (idx < 10)):
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()
            idx += 1

    def stop(self):
        if(self.run.is_connected()):
            self.run.put(0)
        # self.isRunning = 0

    def configure(self, num_points=1, dwell=2.0, duty=0.5, soft_trig=False, trig_delay=0.0):
        self.p_dwell = dwell
        self.p_duty_cycle = duty
        self.p_num_points = num_points

        self.max_points.put(self.p_num_points)
        self.dwell.put(self.p_dwell)
        self.duty_cycle.put(self.p_duty_cycle)
        self.trig_delay.put(trig_delay)

        if (self.trig is not None):
            self.trig_type.put(trig_types.SOFT_TRIGGER)
        else:
            self.trig_type.put(trig_types.DAQMX_VAL_DIGEDGE)

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'dwell', self.dwell.get())
        dct_put(dct, 'max_points', self.max_points.get())
        dct_put(dct, 'duty_cycle', self.duty_cycle.get())
        dct_put(dct, 'trig_type', self.trig_type.get())
        dct_put(dct, 'trig_delay', self.trig_delay.get())
        dct_put(dct, 'retrig', self.retrig.get())
        dct_put(dct, 'device_select', self.device_select.get())
        dct_put(dct, 'counter_select', self.counter_select.get())
        dct_put(dct, 'sample_mode', self.sample_mode.get())
        dct_put(dct, 'output_idle_state', self.output_idle_state.get())
        dct_put(dct, 'clock_src_select', self.clock_src_select.get())
        dct_put(dct, 'retriggerable', self.retriggerable.get())
        dct_put(dct, 'trigger_type', self.trigger_type.get())
        dct_put(dct, 'trig_src_select', self.trig_src_select.get())
        dct_put(dct, 'edge_select', self.edge_select.get())
        dct_put(dct, 'trigger_delay', self.trigger_delay.get())
        return (dct)

    def load_defaults(self):
        self.duty_cycle.set(0.5)
        self.max_points(1)
        self.retrig.set(0)

    def open(self):
        self.start()

    def start(self):
        self.run.put(1)

    # self.isRunning = 1

    def do_trigger(self):
        if (self.trig is not None):
            self.trig.put(1)


class BaseCounter(BaseObject):
    changed = QtCore.pyqtSignal(int, object)
    proc_queue = QtCore.pyqtSignal()

    def __init__(self, base_signal_name=None, **kwargs):
        super(BaseCounter, self).__init__(base_signal_name=base_signal_name, **kwargs)
        self.name = self.base_signal_name = self.base_signal_name + ':Run'
        self.data_q = queue.Queue()
        self.proc_queue.connect(self.on_proc_queue)

        self.run = self.add_device('Run', _delim=':', is_dev_attr=True)
        self.row_mode = self.add_device('RowMode', _delim=':', is_dev_attr=True)
        self.points_per_row = self.add_device('PointsPerRow', _delim=':', is_dev_attr=True)
        self.device_select = self.add_device('DeviceSelect', _delim=':', is_dev_attr=True)
        self.counter_select = self.add_device('CounterSelect', _delim=':', is_dev_attr=True)
        self.signal_src_pin_select = self.add_device('SignalSrcPinSelect', _delim=':', is_dev_attr=True)
        self.initial_count = self.add_device('InitialCount', _delim=':', is_dev_attr=True)
        self.count_dir = self.add_device('CountDir', _delim=':', is_dev_attr=True)
        self.max_points = self.add_device('MaxPoints', _delim=':', is_dev_attr=True)
        self.sample_mode = self.add_device('SampleMode', _delim=':', is_dev_attr=True)
        self.signal_src_clock_select = self.add_device('SignalSrcClockSelect', _delim=':', is_dev_attr=True)
        self.sampling_rate = self.add_device('SamplingRate', _delim=':', is_dev_attr=True)
        self.edge_select = self.add_device('EdgeSelect', _delim=':', is_dev_attr=True)
        self.retriggerable = self.add_device('Retriggerable', _delim=':', is_dev_attr=True)
        self.trig_type = self.add_device('TriggerType', _delim=':', is_dev_attr=True)
        self.trig_src_select = self.add_device('TrigSrcSelect', _delim=':', is_dev_attr=True)
        self.row_num_rbv = self.add_device('RowNum_RBV', _delim=':', is_dev_attr=True)
        self.point_num_rbv = self.add_device('PointNum_RBV', _delim=':', is_dev_attr=True)
        self.read_counts = self.add_device('ReadCounts', _delim=':', is_dev_attr=True)
        self.point_dwell = self.add_device('PointDwell', _delim=':', is_dev_attr=True)
        self.single_value_rbv = self.add_device('SingleValue_RBV', _delim=':', is_dev_attr=True)
        self.run_rbv = self.add_device('Run_RBV', _delim=':', is_dev_attr=True)

        # self.data = self.add_device('Waveform_RBV')
########        self.data = self.add_device('Waveform_RBV', _delim=':', is_dev_attr=True)

########        self.runningcb_idx = self.add_callback('Run_RBV', self.on_running)

        # self.data.changed.connect(self.on_new_data)
        self.num_points = 1
        self.isRunning = 0
        self.connected = False
        time.sleep(0.2)

        self.cb_idx = None
        self.mode = 'Line'


        # self.configure()

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'row_mode', self.row_mode.get())
        dct_put(dct, 'points_per_row', self.points_per_row.get())
        dct_put(dct, 'device_select', self.device_select.get())
        dct_put(dct, 'counter_select', self.counter_select.get())
        dct_put(dct, 'signal_src_pin_select', self.signal_src_pin_select.get())
        dct_put(dct, 'initial_count', self.initial_count.get())
        dct_put(dct, 'count_dir', self.count_dir.get())
        dct_put(dct, 'max_points', self.max_points.get())
        dct_put(dct, 'sample_mode', self.sample_mode.get())
        dct_put(dct, 'signal_src_clock_select', self.signal_src_clock_select.get())
        dct_put(dct, 'sampling_rate', self.sampling_rate.get())
        dct_put(dct, 'edge_select', self.edge_select.get())
        dct_put(dct, 'retriggerable', self.retriggerable.get())
        dct_put(dct, 'trig_type', self.trig_type.get())
        dct_put(dct, 'trig_src_select', self.trig_src_select.get())
        dct_put(dct, 'row_num_rbv', self.row_num_rbv.get())
        dct_put(dct, 'point_num_rbv', self.point_num_rbv.get())
        dct_put(dct, 'point_dwell', self.point_dwell.get())

        return (dct)

    def get_position(self):
        """ this is an API function for all devices/pvs/detectors """
        return (-1)


    def set_mode(self, mode='Line'):
        """ mode can be either Line or Point """
        self.mode = mode


    def start(self):
        self.run.put(1)


    # self.isRunning = 1

    def stop(self):
        self.run.put(0)
        self.read_counts.put(0)


    # self.isRunning = 0

    def configure(self, dwell, num_points=1, row_mode='Line'):
        num_points = int(num_points)
        self.set_mode(row_mode)
        self.num_points = num_points
        self.max_points.put(num_points)
        self.point_dwell.put(dwell)
        if (self.connected):
            # self.data.changed.disconnect()
            self.data.remove_callback(self.cb_idx)

        if (self.mode.find('Line') > -1):
            # self.data.changed.connect(self.on_new_data)
            self.cb_idx = self.data.add_callback(self.on_new_data)
        else:
            # self.data.changed.connect(self.on_new_point_data)
            self.cb_idx = self.data.add_callback(self.on_new_point_data)
        self.connected = True


    def on_running(self, **kwargs):
        rawData = kwargs['value']
        # print 'BaseCounter: on_running' , kwargs
        self.isRunning = kwargs['value']


    def wait_till_stopped(self, proc_qt_msgs=True):
        while self.isRunning:
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()


    def wait_till_running(self, proc_qt_msgs=True):
        while not self.isRunning:
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()


    def wait_till_running_polling(self, proc_qt_msgs=True):
        idx = 0
        while (not self.run_rbv.get() and (idx < 10)):
            time.sleep(0.1)
            if (proc_qt_msgs):
                QtWidgets.QApplication.processEvents()
            idx += 1


    def on_new_data(self, **kwargs):
        # print 'on_new_data \n',arr
        # print 'on_new_data: count=%d' % kwargs['count']
        self.num_points = kwargs['count']
        rawData = kwargs['value']
        row = int(rawData[0])
        self.data_q.put_nowait((row, rawData))
        self.proc_queue.emit()


    # (row, data) = self.process_scalar_line_data(rawData)
    # self.changed.emit(int(row), data)

    def on_proc_queue(self):
        while not self.data_q.empty():
            (row, rawData) = self.data_q.get()
            # print 'rawData[0:20', rawData[0:20]
            (row, data) = self.process_scalar_line_data(rawData)
            self.changed.emit(int(row), data)

        self.data_q.task_done()


    def on_new_point_data(self, **kwargs):
        rawData = kwargs['value']
        # print 'row=%d, point=%d, val=%d' % (arr[0], arr[1], arr[2])
        row = int(rawData[0])
        point = int(rawData[1])
        val = rawData[2]
        # print '%s: on_new_point_data row=%d point=%d val=%d\n' % (self.p_prefix, row, point, val)

        self.changed.emit(row, (point, val))


    def process_scalar_line_data(self, data):
        """ stores raw scalar data of increasing counts """

        arr = np.array(data)
        row = int(arr[0])
        arr2 = arr[DATA_OFFSET: self.num_points + DATA_OFFSET]
        arr3 = self.line_as_ediff(arr2, len(arr2))
        return (row, arr3)


    def line_as_ediff(self, arr, npoints, even=True, reverse=False):
        if (even):
            # this one adds a zero to the end of the array keeping teh priginal size  dat = np.ediff1d(arr, to_end=np.array([0])).clip([0,])
            dat = np.ediff1d(arr).clip([0, ])
            if (reverse):
                dat = dat[::-1]
            # dat = np.roll(dat,1)
        else:
            # dat = np.ediff1d(arr, to_end=np.array([0])).clip([0,])
            dat = np.ediff1d(arr).clip([0, ])
        # dat[0] = 0
        # dat2 = np.resize(dat, (npoints,))

        # dat2[0] = dat2[1]
        # dat2[-1] = dat2[]
        # return(dat2)
        return (dat)


    def mark_data(self, row, data):
        try:
            data[0] = 100
            data[1] = 100
            data[2] = 105
            data[3] = 555
            data[8] = 655
            data[9] = 755
            data[10] = 855
            data[11] = 155
            data[12] = 155
            data[13] = 155
            data[14] = 155
            data[15] = 0
            data[16] = 0
            data[17] = 0
            if (row < 5):
                data[0:5] = 155
            return (data)
        except IndexError:
            pass


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


if __name__ == "__main__":
    import sys
    from PyQt5 import QtCore, QtGui
    from bcm.protocol.epics import PV


    def on_new_pmt(**kwargs):
        print(kwargs)


    def on_new_pmt_val(val):
        print(val)


    #
    app = QtWidgets.QApplication(sys.argv)
    # 	cntr = BaseCounter('uhvCI:counter')
    # 	gate = BaseGate('uhvCO:gate')
    #
    # 	for dwell in drange(2.0, 10, 0.5):
    # 		cntr.configure(dwell, 1, row_mode='Point')
    # 		gate.configure(num_points=1, dwell=dwell, duty=0.99, soft_trig=False, trig_delay=0.0)
    # 		cntr.start()
    # 		gate.start()
    #
    # 		cntr.read_counts.put(1)
    # 		print 'dwell=%.3f ms, counts = %d' % (dwell, cntr.single_value_rbv.get())
    # 		cntr.stop()
    # 		gate.stop()

    # pmt = EpicsPvCounter('uhvPMT:pv_snapshot_RBV')
    # pmt.changed.connect(on_new_pmt_val)
    # pmt = BaseCounter('PMT:ctr')
    # pmt.configure(5, row_mode='Line')

    # pmt = EpicsPvCounter('PMT:ctr:SingleValue_RBV')
    # pmt = PV('PMT:ctr:SingleValue_RBV')
    # pmt.add_callback(on_new_pmt)

    ai0 = EpicsPvCounter('uhvAi:ai:ai0_RBV')
    ai0.changed.connect(on_new_pmt_val)
    app.exec_()
