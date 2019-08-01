import time as ttime
import numpy as np
import copy
from PyQt5 import QtCore
import ophyd
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, DeviceStatus
#from ophyd.device import (Device)
from ophyd.flyers import MonitorFlyerMixin
from cls.plotWidgets.utils import *

from cls.types.stxmTypes import scan_types

DATA_OFFSET = 2

class BaseDeviceSignals(QtCore.QObject):
    """
    The base signals provided in the API for scans, this class provides the following signals to every sscan record

    :signal changed: The detectordevice has read a new value

    :returns: None

    """
    changed = QtCore.pyqtSignal(object)  # dct
    sig_do_read = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """
        __init__(): description

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        QtCore.QObject.__init__(self, parent)


class BaseCounterInputDevice(ophyd.Device):
    # mtr = Cpt(EpicsSignal, 'mtr', kind='hinted')
    # exp = Cpt(EpicsSignal, 'exp', kind='config')
    # det = Cpt(EpicsSignalRO, 'det', kind='hinted')
    # acq = Cpt(EpicsSignal, 'acq', kind='omitted')
    # busy = Cpt(EpicsSignalRO, 'busy', kind='omitted')
    run = Cpt(EpicsSignal, 'Run', kind='omitted')
    row_mode = Cpt(EpicsSignal, 'RowMode', kind='config')
    points_per_row = Cpt(EpicsSignal, 'PointsPerRow', kind='config')
    device_select = Cpt(EpicsSignal, 'DeviceSelect', kind='config')
    counter_select = Cpt(EpicsSignal, 'CounterSelect', kind='config')
    signal_src_pin_select = Cpt(EpicsSignal, 'SignalSrcPinSelect', kind='config')
    initial_count = Cpt(EpicsSignal, 'InitialCount', kind='config')
    count_dir = Cpt(EpicsSignal, 'CountDir', kind='config')
    max_points = Cpt(EpicsSignal, 'MaxPoints', kind='config')
    sample_mode = Cpt(EpicsSignal, 'SampleMode', kind='config')
    signal_src_clock_select = Cpt(EpicsSignal, 'SignalSrcClockSelect', kind='config')
    sampling_rate = Cpt(EpicsSignal, 'SamplingRate', kind='config')
    edge_select = Cpt(EpicsSignal, 'EdgeSelect', kind='config')
    retriggerable = Cpt(EpicsSignal, 'Retriggerable', kind='config')
    trig_type = Cpt(EpicsSignal, 'TriggerType', kind='config')
    trig_src_select = Cpt(EpicsSignal, 'TrigSrcSelect', kind='config')
    row_num_rbv = Cpt(EpicsSignalRO, 'RowNum_RBV', kind='omitted')
    point_num_rbv = Cpt(EpicsSignalRO, 'PointNum_RBV', kind='omitted')
    read_counts = Cpt(EpicsSignal, 'ReadCounts', kind='omitted')
    point_dwell = Cpt(EpicsSignal, 'PointDwell', kind='config')
    #single_value_rbv = Cpt(EpicsSignalRO, 'SingleValue_RBV', kind='hinted')
    run_rbv = Cpt(EpicsSignalRO, 'Run_RBV', kind='omitted')
    #waveform_rbv = Cpt(EpicsSignalRO, 'Waveform_RBV', kind='hinted')


    def __init__(self, prefix, name, **kwargs):
        super(BaseCounterInputDevice, self).__init__(prefix, name=name)
        self.cntr = 0
        #to allow Qt Signals to be emitted
        self.sigs = BaseDeviceSignals()
        self.p_num_points = 1
        self._scan_type = None
        self.mode = 0
        if ('scan_type' in kwargs.keys()):
            self._scan_type = kwargs['scan_type']


    def configure(self):
        '''
        to be implemented by inheriting class
        :return:
        '''
        pass

    def set_dwell(self, dwell):
        self.point_dwell.put(dwell)

    def set_mode(self, val):
        self.mode = val

    def set_scan_type(self, _stype):
        self._scan_type = _stype

    def get_name(self):
        return(self.name)

    def get_position(self):
        return(0)

    def set_num_points(self, val):
        self.p_num_points = val
        self.max_points.put(val)

    def stage(self):
        self.cntr = 0
        self.run.put(1)

    def unstage(self):
        self.run.put(0)

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



class PointDetectorDevice(BaseCounterInputDevice):
    single_value_rbv = Cpt(EpicsSignalRO, 'SingleValue_RBV', kind='hinted')
    def __init__(self, prefix, name):
        super(PointDetectorDevice, self).__init__(prefix, name=name)
        self.single_value_rbv.subscribe(self.on_change)
        self.mode = 0  # 0 == point, 1 == line

    def report(self):
        """ return a dict that reresents all of the settings for this device """
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def configure(self):
        self.do_point_config(scan_types.SAMPLE_POINT_SPECTRA, 2.0, 1, 1)

    def stage(self):
        # if (self.mode is 0):
        #     self.do_point_config(scan_types.SAMPLE_POINT_SPECTRA, 2.0, 1, 1)
        # else:
        #     pass
        self.configure()
        self.cntr = 0
        self.run.put(1)

    def on_change(self, **kwargs):
        '''
        {'old_value': 2.0,
        'value': 4.0,
        'timestamp': 1549577201.36433,
        'sub_type': 'value',
        'obj':
            EpicsSignalRO(read_pv='uhvCI:counter:SingleValue_RBV',
                name='noisy_det_single_value_rbv',
                parent='noisy_det',
                value=4.0,
                timestamp=1549577201.36433,
                pv_kw={},
                auto_monitor=False,
                string=False)
        }

        :param kwargs:
        :return:
        '''
        #print('PointDetectorDevice: on_change')
        self.sigs.changed.emit(kwargs)
        #print(kwargs)

    def do_point_config(self, scan_type, dwell, numE, numX):
        trig_src_pfi = 4
        self.trig_src_select.put(trig_src_pfi)  # /PFI 4  this will need to be part of a configuration at some point
        self.signal_src_clock_select.put(12)  # /PFI 12
        self.trig_type.put(3)  # Digital_EDge
        self.sample_mode.put(2)  # DAQmx_HWTimedSinglePoint
        # self.max_points.put(roi['X'][NPOINTS]) #X points
        self.max_points.put(2)  # X points, so that the waveform returns <row> <point> <value> <pad>
        self.row_mode.put(1)  # 1 point
        self.retriggerable.put(True)

        if (scan_type == scan_types.SAMPLE_POINT_SPECTRA):
            self.points_per_row.put(numE)  # EV point spectra
        else:
            self.points_per_row.put(numX)  # X points


    # def describe(self):
    #     #print('PointDetectorDevice: describe called')
    #     res = super().describe()
    #     for key in res:
    #         res[key]['units'] = "counts"
    #         res[key]['shape'] = '[%d,]' % len(res[key]['data'])
    #     return res


#class LineDetectorDevice(BaseCounterInputDevice, QtCore.QObject):
class LineDetectorDevice(BaseCounterInputDevice):
    '''
    This Device simply connects to the line detector and sets up a subscription such that when the line changes
    it emits the data on its chcnged signal so that a plotter can plot it, the data acquisition is done on the
     flyer device
    '''
    #sig_do_read = QtCore.pyqtSignal()
    #changed = QtCore.pyqtSignal(object)
    waveform_rbv = Cpt(EpicsSignalRO, 'Waveform_RBV', kind='hinted', auto_monitor=True)
    def __init__(self, prefix, name):
        super(LineDetectorDevice, self).__init__(prefix, name=name)
        self.num_points = 0
        self.waveform_rbv.subscribe(self.on_waveform_changed, event_type='value')
        self.sigs.sig_do_read.connect(self.read)
        #'readback'
        self._default_sub = 'acq_done'
        #self.subscribe(self._pos_changed, event_type='acq_done')
        self.rawData = None
        self._plot_dct = make_counter_to_plotter_com_dct()

    def report(self):
        """ return a dict that reresents all of the settings for this device """
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def configure(self, npoints, scan_type):
        self.set_num_points(npoints)
        self.set_scan_type(scan_type)
        self.do_line_config()

    def stage(self):
        # if (self.mode is 0):
        #     self.do_line_config()
        # else:
        #     pass
        self.cntr = 0
        self.run.put(1)

    def do_line_config(self):

        NUM_FOR_EDIFF = 2
        trig_src_pfi = 3
        xnpoints = self.p_num_points + 2

        #self.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
        self.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire
        self.trig_type.put(3)  # DAQmx_Val_DigPattern
        self.signal_src_clock_select.put(12)  # /PFI 12
        self.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
        self.max_points.put(xnpoints)  #
        self.row_mode.put(0)  # 0 LINE
        self.points_per_row.put(self.p_num_points)
        self.retriggerable.put(False)

    def do_read(self):
        self.read()
    #
    def on_waveform_changed(self, *args, **kwargs):
         #self._is_running = kwargs['value']
         # print(kwargs)
         self.rawData = copy.copy(kwargs['value'])
         self.sigs.sig_do_read.emit()


    def read(self):
        #print('LineDetectorDevice: read called')
        #return(self.waveform_rbv.get())
        self.cntr += 1
        #rawData = self.waveform_rbv.get()
        if(hasattr(self.rawData, 'shape')):
            self.num_points,  = self.rawData.shape
            if(self.num_points > 0):
                (row, data) = self.process_scalar_line_data(self.rawData)
                if(self._scan_type is scan_types.SAMPLE_LINE_SPECTRA):
                    #print('LineDetectorDevice: SAMPLE_LINE_SPECTRA: row=%d' % (row))
                    self._plot_dct[CNTR2PLOT_ROW] = 0
                    self._plot_dct[CNTR2PLOT_COL] = int(row)
                else:
                    #print('LineDetectorDevice: row=%d' % (row))
                    self._plot_dct[CNTR2PLOT_ROW] = int(row)
                    self._plot_dct[CNTR2PLOT_COL] = 0

                #self._plot_dct[CNTR2PLOT_VAL] = data[0:self.p_num_points]
                self._plot_dct[CNTR2PLOT_VAL] = data
                self._plot_dct[CNTR2PLOT_IS_LINE] = True
                self._plot_dct[CNTR2PLOT_SCAN_TYPE] = self._scan_type
                self.sigs.changed.emit(self._plot_dct)
                #self.changed.emit((row, data))

                # return {self.name + '_waveform_rbv': {'value': data,
                #                     'cntr': self.cntr, 'timestamp': ttime.time(), 'row': int(row)}}

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


class LineDetectorFlyerDevice(MonitorFlyerMixin, BaseCounterInputDevice):
    waveform_rbv = Cpt(EpicsSignalRO, 'Waveform_RBV', kind='hinted', auto_monitor=True)

    def __init__(self, *args, stream_names=None, **kwargs):
        if(stream_names is not None):
            s_keys = list(stream_names.keys())
            self.stream_name = stream_names[s_keys[0]]

        super().__init__(*args, **kwargs)

        self.p_num_points = 1
        self._is_point = False

    def report(self):
        """ return a dict that reresents all of the settings for this device """
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def configure(self, npoints, scan_type):
        self.set_num_points(npoints)
        self.set_scan_type(scan_type)
        # if(self.mode is 0):
        #     self._is_point = True
        #     self.do_point_config()
        # else:
        self._is_point = False
        self.do_line_config()

    def set_num_points(self, val):
        self.p_num_points = val
        #self.max_points.put(val)

    def kickoff(self):
        st = super().kickoff()
        self.run.put(1)
        ttime.sleep(0.5)
        st._finished = True
        return(st)

    def stage(self):
        #self.do_line_config()
        self.run.put(1)

    def do_line_config(self):

        NUM_FOR_EDIFF = 2
        trig_src_pfi = 3
        xnpoints = self.p_num_points + 2

        #self.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
        self.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire
        self.trig_type.put(3)  # DAQmx_Val_DigPattern
        self.signal_src_clock_select.put(12)  # /PFI 12
        self.sample_mode.put(0)  # DAQmx_Val_FiniteSamps
        self.max_points.put(xnpoints)  #
        self.row_mode.put(0)  # 0 LINE
        self.points_per_row.put(self.p_num_points)
        self.retriggerable.put(False)


    def do_point_config(self):
        """ a convienience function to have a single place to configure the devices to acquire a line of points
        while scanning using the E712's wave form generator
        """
        NUM_FOR_EDIFF = 2
        # NUM_FOR_EDIFF = 0
        trig_src_pfi = 3
        xnpoints = self.p_num_points #+ NUM_FOR_EDIFF

        # gate.configure(xnpoints, dwell=dwell, duty=0.5)
        # gate.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI4 to the interferometer "pixelclock" wire

        #self.configure(dwell, num_points=xnpoints, row_mode='Line')  # , row_mode='LINE')
        self.trig_src_select.put(trig_src_pfi)  # /PFI 3  connect PFI3 to the interferometer "pixelclock" wire

        # counter.trig_type.put(3)  # DAQmx_Val_DigPattern
        self.trig_type.put(6)  # Pause Trigger
        self.signal_src_clock_select.put(3)  # /PFI 3 this is connected to the E712 OUT1

        self.sample_mode.put(1)  # DAQmx_Val_ContSamps
        if (self._scan_type == scan_types.SAMPLE_LINE_SPECTRA):
            # dont need the extra points
            self.max_points.put(self.p_num_points + 1)  #
        else:
            self.max_points.put(xnpoints)  #
        self.row_mode.put(0)  # 0 LINE
        self.points_per_row.put(self.p_num_points)
        self.retriggerable.put(False)

        if (self._scan_type == scan_types.SAMPLE_POINT_SPECTRA):
            #self.points_per_row.put(numE)  # EV point spectra
            self.points_per_row.put(self.p_num_points)  # EV point spectra
        else:
            self.points_per_row.put(self.p_num_points)  # X points

    def unstage(self):
        super().unstage()
        self.run.put(0)
        st = DeviceStatus(self)
        st._finished = True
        return(st)

    def complete(self):
        st = super().complete()
        self.unstage()
        st._finished = True
        return (st)

    def process_scalar_line_data(self, data):
        """ stores raw scalar data of increasing counts """
        npts, = data.shape
        num_points = npts - DATA_OFFSET - DATA_OFFSET + 1
        arr = np.array(data)
        row = int(arr[0])
        arr2 = arr[DATA_OFFSET: num_points + DATA_OFFSET]
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
        return (dat)

    def describe_collect(self):
        '''Describe details for the flyer collect() method'''
        desc = dict()
        desc.update(self.waveform_rbv.describe())
        d = {self.stream_name: desc}
        #print('describe_collect: ', d)
        return d

    def collect(self):
        '''Retrieve all collected data, must return exact same keys as layed out in describe_collect()

        {'line_det_strm': {
            'line_det_waveform_rbv': {
                   'source': 'PV:uhvCI:counter:Waveform_RBV',
                   'dtype': 'array',
                   'shape': [104],
                   'units': None,
                   'lower_ctrl_limit': None,
                   'upper_ctrl_limit': None},
            }
        }
        '''
        if self._acquiring:
            raise RuntimeError('Acquisition still in progress. Call complete()'
                               ' first.')

        collected = self._collected_data
        self._collected_data = None

        if self._pivot:
            for attr, data in collected.items():
                name = getattr(self, attr).name
                for ts, value in zip(data['timestamps'], data['values']):
                    d = dict(time=ts,
                               timestamps={name: ts},
                               data={name: value},
                               )
                    #print('collect: ', d)
                    yield d
        else:
            for attr, data in collected.items():
                # name = getattr(self, attr).name
                # for attr, data in collected.items():
                #     name = getattr(self, attr).name
                #     yield dict(time=self._start_time,
                #                timestamps={name: data['timestamps']},
                #                data={name: data['values']},
                #                )
                name = getattr(self, attr).name
                rows = len(data['values'])
                cols, = data['values'][0].shape
                #final_data = np.zeros((rows, cols - 4), dtype='int')
                final_data = []
                #for ldat in data['values']:
                # skip first row cause it is the last row of previous scan
                for ldat in data['values'][1:]:
                    (row, ndata) = self.process_scalar_line_data(ldat)
                    d =  dict(time=self._start_time,
                               timestamps={name: data['timestamps']},
                               data={name: ndata},
                               )

                    #print('collect: ', d)
                    yield d

