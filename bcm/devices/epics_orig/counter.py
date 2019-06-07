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

from cls.utils.developer_tools import DONT_FORGET

from bcm.devices.epics.base import BaseDevice
from epics import PV
from .aio import aio
from cls.utils.dict_utils import dct_get, dct_put
# from cls.utils.log import get_module_logger
from cls.utils.xim2array import loadXim2Array
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


class Counter(QObject):
    """class for counters that are accessed as epics PV's in the counter module."""
    changed = pyqtSignal(object, object)  # device, state
    new_data = pyqtSignal(object, object)  # row num, data

    ##implements(ICounter)

    def __init__(self, pv_name=None, zero=0):
        super(Counter, self).__init__()
        self.name = pv_name
        self.zero = float(zero)
        self.value = None
        self.DESC = ''
        if (pv_name is not None):
            self.value = self.add_pv(pv_name)
            self.DESC = self.add_pv('%s.DESC' % pv_name)
        # self.DESC.connect('changed', self._on_name_change)
        # QObject.connect(self.DESC, SIGNAL('changed(object)'), self.on_device_active)
        self.changed.connect(self.on_device_active)

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'name', self.name)
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


# class EpicsPv(QObject):
#     """ just a convienience class so that PVs can be configured in the beamline configuration file
#     and used as if they were other devices, making the rest of the code cleaner
#     """
#     # new_data = pyqtSignal(object)
#     changed = pyqtSignal(object)
#
#     def __init__(self, pv_name=None, zero=0, desc=None):
#         super(EpicsPv, self).__init__()
#         self._name = pv_name
#         self.zero = float(zero)
#         self.value = None
#         self.ctrl_vars = {}
#
#         if (desc is not None):
#             self.DESC = desc
#         else:
#             self.DESC = pv_name
#
#         if (pv_name is not None):
#             self.pv = PV(pv_name)
#             # self.changed.connect(self.count)
#             # self.pv.changed.connect(self.count)
#             self.connected = self.pv.connected
#             self.add_callback = self.pv.add_callback
#             self.pv.add_callback(self.on_pv_changed)
#         # self.changed.connect(self.count)
#
#     def on_pv_changed(self, **kwargs):
#         val = kwargs['value']
#         self.count(val)
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def get_name(self):
#         return (self._name)
#
#     def get_position(self):
#         return (self.pv.get())
#
#     def count(self, val=None):
#         # print 'count called'
#         self.changed.emit(val)
#         return (val)
#
#     def get(self):
#         return (self.pv.get())
#
#     def put(self, val):
#         self.pv.put(val)
#
#     def get_low_limit(self):
#         i = 0
#         while ((len(self.ctrl_vars) == 0) and (i < 50)):
#             self.ctrl_vars = self.pv.get_ctrlvars()
#             i += 1
#             time.sleep(0.001)
#         if ('lower_ctrl_limit' in self.ctrl_vars.keys()):
#             return (self.ctrl_vars['lower_ctrl_limit'])
#         else:
#             return (None)
#
#     def get_high_limit(self):
#         i = 0
#         while ((len(self.ctrl_vars) == 0) and (i < 50)):
#             self.ctrl_vars = self.pv.get_ctrlvars()
#             i += 1
#             time.sleep(0.001)
#
#         if ('upper_ctrl_limit' in self.ctrl_vars.keys()):
#             return (self.ctrl_vars['upper_ctrl_limit'])
#         else:
#             return (None)
#
#     def get_enum_str(self):
#         val = self.pv.get()
#         val_str = self.pv.enum_strs[val]
#         return (val_str)
#
#     def get_enum_str_as_int(self):
#         val = self.pv.get()
#         if (type(val) is int):
#             final = val
#         else:
#             final = int(self.pv.enum_strs[val])
#         return (final)
#
#
# class EpicsOldPv(aio):
#     """ just a convienience class so that PVs can be configured in the beamline configuration file
#     and used as if they were other devices, making the rest of the code cleaner
#     """
#     # new_data = pyqtSignal(object)
#     changed = pyqtSignal(object)
#
#     def __init__(self, pv_name=None, zero=0):
#         super(EpicsPv, self).__init__(pv_name)
#         self._name = pv_name
#         self.zero = float(zero)
#         self.value = None
#
#         self.DESC = ''
#         if (pv_name is not None):
#             self.pv = PV(pv_name)
#             self.changed.connect(self.count)
#             self.connected = self.pv.connected
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def get_name(self):
#         return (self._name)
#
#     def get_position(self):
#         return (self.pv.get())
#
#     def count(self, val=None):
#         self.changed.emit(val)
#         return (val)
#
#     def get(self):
#         return (self.pv.get())
#
#     def put(self, val):
#         self.pv.put(val)
#
#
# class EpicsPvCounter(QObject):
#     changed = pyqtSignal(object)
#     pv_changed = pyqtSignal(object)
#
#     ##implements(ICounter)
#
#     def __init__(self, pv_name=None, zero=0, do_cb=False):
#         # super(EpicsPvCounter, self).__init__(pv_name)
#         super(EpicsPvCounter, self).__init__()
#         # from epics import PV
#         import Queue
#         self.name = pv_name
#         self.zero = float(zero)
#         self.queue = Queue.Queue()
#         self.value = None
#         self.DESC = ''
#         # if (pv_name is not None):
#         #     self.pv = PV(pv_name)
#         #     #self.pv.add_callback(self.on_new_data)
#         #     self.changed = self.pv.changed
#         #     self.connected = self.pv.connected
#         # # self.timer = QtCore.QTimer()
#         # # self.timer.timeout.connect(self.update)
#         # # self.startTimer(100)
#         if (pv_name is not None):
#             self.pv = PV(pv_name)
#             # self.changed.connect(self.count)
#             # self.pv.changed.connect(self.count)
#             self.connected = self.pv.connected
#             self.add_callback = self.pv.add_callback
#             self.pv.add_callback(self.on_new_data)
#         # self.pv_changed.connect(self.count)
#
#     def update(self):
#         while not self.queue.empty():
#             val = self.queue.get()
#             self.changed.emit(val)
#         self.queue.task_done()
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def get_name(self):
#         return (self.name)
#
#     def get_position(self):
#         return (self.pv.get())
#
#     def on_new_data(self, **kwargs):
#         # data = kwargs
#         # print 'EpicsPvCounter: on_new_data: %s' % kwargs['type']
#         # print kwargs
#         if (kwargs['type'] == 'double'):
#             # self.changed.emit(float(kwargs['char_value']))
#             val = float(kwargs['char_value'])
#         elif (kwargs['type'] == 'integer'):
#             # self.changed.emit(int(kwargs['char_value']))
#             val = int(kwargs['char_value'])
#         elif (kwargs['type'] == 'float'):
#             # self.changed.emit(float(kwargs['char_value']))
#             val = float(kwargs['char_value'])
#         else:
#             # self.changed.emit(kwargs['char_value'])
#             val = kwargs['char_value']
#         # self.queue.put_nowait(val)
#         self.changed.emit(val)
#
#     def count(self, val=None):
#         if (val is not None):
#             print 'count: %s: data = %d' % (self.name, val)
#             self.changed.emit(val)
#         return (val)
#
#
# class SimCounter(Counter):
#     """class for counters that are Simulated in the counter module."""
#
#     ##implements(ICounter)
#
#     def __init__(self, name, filename=None, zero=0):
#         Counter.__init__(self, name)
#         import scipy
#         from bcm.device.misc import SimPositioner
#         self.zero = float(zero)
#         self.name = name
#         self.value = SimPositioner('PV', 1.0, '')
#         self.set_state(active=True)
#         self.fileData = None
#         self.wPtr = 0
#         self.hPtr = 0
#         self.dataWidth = 0
#         self.dataHeight = 0
#         self.dataAtMax = False
#         # square data filename = r'C:\playground_mks2005\STXM\StxmDir\data\a101207\A101207006_a.xim'
#         # filename = r'C:\playground_mks2005\STXM\StxmDir\data\a101207\A101207005_a.xim'
#
#         if (filename != None):
#             # self.fileData = np.loadtxt(filename, dtype=np.int32, delimiter='\t')
#             array = loadXim2Array(filename)
#             self.fileData = array
#
#             # self.fileData = np.flipud(self.fileData)
#             # [self.dataWidth,self.dataHeight] = self.fileData.shape
#             # remember it is [row, column]
#             [self.dataHeight, self.dataWidth] = self.fileData.shape
#             self.hPtr = self.dataHeight - 1
#             print self.fileData.shape
#
#     def __repr__(self):
#         s = "<%s:'%s'>" % (self.__class__.__name__, self.name)
#         return s
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'pv_name', self.p_prefix)
#         return (dct)
#
#     def resetData(self):
#         self.wPtr = 0
#         self.hPtr = self.dataHeight - 1
#
#     def count(self, t, i=None, j=None):
#         time.sleep(t)
#         if ((self.fileData != None) and (self.dataAtMax != True)):
#             if ((i != None) and (j != None)):
#                 # grab specified row(j) and col(i)
#                 val = self.fileData[i, j]
#             else:
#                 val = self.fileData[self.hPtr, self.wPtr]
#             self.incrWidthPtr()
#             buf = scipy.random.randint(0, 255, (self.wPtr,))
#             self.new_buffer.emit(self.hPtr, buf)
#             return val
#         else:
#             return np.random.random_integers(0, high=200)
#
#     def incrWidthPtr(self):
#         self.wPtr += 1
#         if (self.wPtr >= self.dataWidth):
#             # reset the width pointer
#             self.wPtr = 0
#             self.decrHeightPtr()
#         return [self.wPtr, self.hPtr]
#
#     def decrHeightPtr(self):
#         self.hPtr -= 1
#         if (self.hPtr <= 0):
#             # reset the height pointer
#             self.hPtr = self.dataHeight
#             self.dataAtMax = True
#
#
# class SimLineCounter(aio):
#     """class for counters that are Simulated in the counter module."""
#
#     ##implements(ICounter)
#
#     def __init__(self, name, filename=None, zero=0, type='point', width=2560, maxval=16383):
#         super(EpicsPvCounter, self).__init__(name)
#         from bcm.device.misc import SimPositioner
#         self.zero = float(zero)
#         self.name = name
#         self.value = SimPositioner('PV', 1.0, '')
#         self.set_state(active=True)
#         self.fileData = None
#         self.wPtr = 0
#         self.hPtr = 0
#         self.dataWidth = 0
#         self.dataHeight = 0
#         self.dataAtMax = False
#
#         self.type = type
#         self.width = width
#         self.maxval = maxval
#
#         if (filename != None):
#             # self.fileData = np.loadtxt(filename, dtype=np.int32, delimiter='\t')
#             array = loadXim2Array(filename)
#             self.fileData = array
#             # remember it is [row, column]
#             [self.dataHeight, self.dataWidth] = self.fileData.shape
#             self.hPtr = self.dataHeight - 1
#             print self.fileData.shape
#
#     def __repr__(self):
#         s = "<%s:'%s'>" % (self.__class__.__name__, self.name)
#         return s
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def resetData(self):
#         self.wPtr = 0
#         self.hPtr = self.dataHeight - 1
#
#     def count(self, t, i=None, j=None):
#         time.sleep(t)
#         if (self.type == 'point'):
#             val = self.get_point(i, j)
#         else:
#             val = self.get_line(i)
#
#     def get_point(self, i=None, j=None):
#         if ((self.fileData != None) and (self.dataAtMax != True)):
#             if ((i != None) and (j != None)):
#                 # grab specified row(j) and col(i)
#                 val = self.fileData[i, j]
#             else:
#                 val = self.fileData[self.hPtr, self.wPtr]
#             self.incrWidthPtr()
#             return val
#         else:
#             return np.random.random_integers(0, high=self.maxval)
#
#     def get_line(self, i=None):
#         if ((self.fileData != None) and (self.dataAtMax != True)):
#             if ((i != None)):
#                 # grab specified row(j) and col(i)
#                 val = self.fileData[i]
#             else:
#                 val = self.fileData[self.hPtr]
#             self.incrWidthPtr()
#             return val
#         else:
#             return np.random.randint(self.maxval, size=self.dataWidth)
#
#     def incrWidthPtr(self):
#         self.wPtr += self.maxval
#         if (self.wPtr >= self.dataWidth):
#             # reset the width pointer
#             self.wPtr = 0
#             self.decrHeightPtr()
#         return [self.wPtr, self.hPtr]
#
#     def decrHeightPtr(self):
#         self.hPtr -= 1
#         if (self.hPtr <= 0):
#             # reset the height pointer
#             self.hPtr = self.dataHeight
#             self.dataAtMax = True
#
#
# # class DAQmxCounter(aio):
# class DAQmxCounter(QObject):
#     """class for NI DAQmx counters that are in the counter module."""
#
#     ##implements(ICounter)
#
#     def __init__(self, cntrName=r'/Dev2/ctr0', cntrGate=None, dwell=0.050, max=1000, dcOffset=0.0):
#         super(DAQmxCounter, self).__init__()
#         from bcm.device.daqmx_tasks import GatedCounter
#         atexit.register(self.__del__)
#         self.name = cntrName
#         self.zero = float(dcOffset)
#         self.value = 0
#         self.DESC = cntrName
#
#         self.daqmx = DAQmxFunctions
#         self.daqmxCnsts = DAQmxConstants
#         self.max_num_samples = max
#         self.dwell = dwell
#
#         self.counterName = cntrName
#
#         self.pulses = np.zeros((self.max_num_samples,), dtype=np.float64)
#
#         # a DAQmx task handle for performing the counting
#         self.task = self.daqmx.TaskHandle()
#
#         if (cntrGate != None):
#             # the counting of teh source will be gated by cntrGateDev, usually from a motor on ND_PFI_18
#             self.createMotorTriggeredCounting(cntrGateDev=cntrGate)
#         else:
#             # the counting of the source will be gated by a pulse train of specified freq and dutyCycle and
#             # sent out to ND_PFI_20 or ND_COUNTER_4 which is wired to ND_PFI_38 (COUNTER_0) and ND_PFI_34 (COUNTER_1)
#             self.gateOutDev = r'/Dev2/ctr4'
#             self.createPulseTrainTriggeredCounting()
#             self.cntrGateTask = self.createGenPulseTrainTask(self.gateOutDev, freq=10000000.0, dutyCycle=self.dwell,
#                                                              numPulse=-1)
#             self.daqmx.DAQmxStartTask(self.cntrGateTask)
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def __del__(self):
#         try:
#             self.daqmx.DAQmxClearTask(self.task)
#             if (self.cntrGateTask != None):
#                 self.daqmx.DAQmxStopTask(self.cntrGateTask)
#                 self.daqmx.DAQmxClearTask(self.cntrGateTask)
#                 doprint('debug', 'DAQmxCounter: at exit')
#         except:
#             pass
#
#     def _on_name_change(self, pv, val):
#         if val != '':
#             self.name = val
#
#     def count(self, t):
#         if t <= 0.0:
#             return self.getValue() - self.zero
#
#         doprint('debug', 'Averaging detector (%s) for %0.2f sec.' % (self.name, t))
#         interval = 0.01
#         values = []
#         time_left = t
#         while time_left > 0.0:
#             values.append(self.getValue())
#             time.sleep(interval)
#             time_left -= interval
#         total = (sum(values, 0.0) / len(values)) - self.zero
#         doprint('debug', '(%s) Returning average of %d values for %0.2f sec.' % (self.name, len(values), t))
#         return total
#
#     def getValue(self):
#         read = self.daqmx.int32()
#         self.daqmx.DAQmxStartTask(self.task)
#         self.daqmx.DAQmxReadCounterF64(self.task, self.max_num_samples, 10.0, self.pulses, self.max_num_samples,
#                                        self.daqmx.byref(read), None)
#         self.daqmx.DAQmxStopTask(self.task)
#         # print "Acquired %d points\n"%read.value
#         x = range(0, len(self.pulses))
#         y = self.pulses
#         # y = float(np.average(self.pulses))
#         return float(np.average(y))
#
#     ###############3 these should be moved to their own class
#     def createMotorTriggeredCounting(self, gateInDev):
#         self.daqmx.DAQmxCreateTask("TrigerredTask", self.daqmx.byref(self.task))
#         self.daqmx.DAQmxCreateCICountEdgesChan(self.task, self.counterName, "", self.daqmxCnsts.DAQmx_Val_Rising, 0,
#                                                self.daqmxCnsts.DAQmx_Val_CountUp)
#         self.daqmx.DAQmxSetPauseTrigType(self.task, self.daqmxCnsts.DAQmx_Val_DigLvl)
#         self.daqmx.DAQmxSetDigLvlPauseTrigSrc(self.task, gateInDev)
#         self.daqmx.DAQmxSetDigLvlPauseTrigWhen(self.task, self.daqmxCnsts.DAQmx_Val_Low)
#
#     def createPulseTrainTriggeredCounting(self):
#         self.daqmx.DAQmxCreateTask("nonTrigerredTask", self.daqmx.byref(self.task))
#         self.daqmx.DAQmxCreateCICountEdgesChan(self.task, self.counterName, "", self.daqmxCnsts.DAQmx_Val_Rising, 0,
#                                                self.daqmxCnsts.DAQmx_Val_CountUp)
#
#     def createGenPulseTrainTask(self, cntrName, freq=100.0, dutyCycle=0.1, numPulse=-1):
#         task = self.daqmx.TaskHandle()
#         self.daqmx.DAQmxCreateTask("genPulseTrain", self.daqmx.byref(task))
#
#         # taskHandle <class 'ctypes.c_ulong'>	counter <class 'ctypes.c_char_p'>	nameToAssignToChannel <class 'ctypes.c_char_p'>	units <class 'ctypes.c_long'>	idleState <class 'ctypes.c_long'>	initialDelay <class 'ctypes.c_double'>	freq <class 'ctypes.c_double'>	dutyCycle <class 'ctypes.c_double'>
#         self.daqmx.DAQmxCreateCOPulseChanFreq(task, cntrName, "", self.daqmxCnsts.DAQmx_Val_Hz,
#                                               self.daqmxCnsts.DAQmx_Val_Low, 0.0, freq, dutyCycle)
#         if (numPulse > -1):
#             self.daqmx.DAQmxCfgImplicitTiming(task, self.daqmxCnsts.DAQmx_Val_FiniteSamps, numPulse)
#         else:
#             self.daqmx.DAQmxCfgImplicitTiming(task, self.daqmxCnsts.DAQmx_Val_ContSamps, numPulse)
#
#         return task
#
#
# class DAQmxLineCounter(QObject):
#     new_data = pyqtSignal(int, object)
#     done = pyqtSignal()
#
#     def __init__(self, name, cntrName=r'/Dev2/ctr0', srcTerminal=r'/Dev2/PFI39', gateTerminal=r'/Dev2/PFI38',
#                  dwell=0.050, num_samples=1000, dcOffset=0.0, sync_cbs=False):
#         super(DAQmxLineCounter, self).__init__()
#         from bcm.device.daqmx_tasks import GatedCounter
#         atexit.register(self.__del__)
#         self.name = name
#         self.ready = False
#         self.num_samples = num_samples
#         # self.readTask = GatedCounter(name, cntrName=r'Dev2/ctr0', srcTerminal = r'/Dev2/PFI39', gateTerminal = r'/Dev2/PFI38', num_samples=num_samples)
#         self.readTask = GatedCounter(name, cntrName=cntrName, srcTerminal=srcTerminal, gateTerminal=gateTerminal,
#                                      num_samples=num_samples, sync_cbs=sync_cbs)
#         if (GENERATE_DATA):
#             doprint('info', 'DAQmxLineCounter: using marked counter data')
#             self.readTask.sig.new_buffer.connect(self.on_new_sim_data)
#         else:
#             doprint('info', 'DAQmxLineCounter: using real data')
#             self.readTask.sig.new_buffer.connect(self.on_new_data)
#
#         self.readTask.sig.done.connect(self.on_done)
#         self.data = -1
#         self.row = 0
#         self.ready = True
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def is_ready(self):
#         return (self.ready)
#
#     def start(self):
#         doprint('debug', 'DAQmxLineCounter: started')
#         # self.data_rdy = False
#         self.ready = False
#         self.readTask.start()
#
#     def count(self, data):
#         idx = 0
#         while ((self.data_rdy == False) and (idx < 1000)):
#             time.sleep(0.001)
#             idx += 1
#         if (idx >= 1000):
#             doprint('error', 'DAQmxLineCounter: counter timed out')
#         # self.data_rdy = False
#         self.ready = False
#         return (self.data)
#
#     def on_new_data(self, row, data):
#         doprint('debug', 'DAQmxLineCounter: on_new_data')
#         if (row > self.num_samples):
#             # print 'DAQmxLineCounter ERROR: row > num_samples'
#             self.readTask.init_defaults()
#             self.row = 0
#             row = 0
#
#         # print 'counter data:' , data
#
#         dat = np.ediff1d(data, to_end=np.array([0]))
#
#         # test alternating reverse rows
#         if (row % 2):
#             # reverse the data
#             dat = dat[::-1]
#
#         # dat = self.mark_data(row, dat)
#         self.new_data.emit(row, dat)
#         self.data = dat
#         doprint('debug', 'Counter emitting new data')
#
#     # print 'counter dat:' , dat
#     # self.data_rdy = True
#     # self.ready = True
#
#     def on_new_sim_data(self, row, data):
#         if (row > self.num_samples):
#             # print 'DAQmxLineCounter ERROR: row > num_samples'
#             self.readTask.init_defaults()
#             self.row = 0
#             row = 0
#         # SIM ONLY
#         # data = np.random.randint(255, size=self.num_samples)
#         data = np.zeros(self.num_samples)
#
#         # data = self.array_as_scaler(np.random.randint(255, size=self.num_samples))
#         data = self.mark_data(row, data)
#         # print 'counter:' , data
#         self.new_data.emit(row, data)
#         self.data = data
#
#     # self.data_rdy = True
#     # self.ready = True
#
#
#     def mark_data(self, row, data):
#         data[7] = 0
#         data[8] = 0
#         data[9] = 0
#         data[10] = 155
#         data[11] = 155
#         data[12] = 155
#         data[13] = 155
#         data[14] = 155
#         data[15] = 0
#         data[16] = 0
#         data[17] = 0
#         if (row < 5):
#             data[0:5] = 155
#         return (data)
#
#     def array_as_scaler(self, arr):
#         w, = arr.shape
#         final = []
#         for i in range(w):
#             if (i != 0):
#                 arr[i] += arr[i - 1]
#                 final.append(arr[i])
#             else:
#                 final.append(arr[i])
#
#         farr = np.array(final)
#         return (farr)
#
#     def on_done(self):
#         doprint('debug', 'DAQmxLineCounter: done reading line')
#         self.stop()
#         self.ready = True
#         self.done.emit()
#
#     def clear(self):
#         # doprint('debug', 'DAQmxLineCounter: cleared')
#         self.readTask.sig.new_buffer.disconnect()
#         self.readTask.sig.done.disconnect()
#
#         self.readTask.clear()
#
#     def stop(self):
#         # print 'DAQmxLineCounter: stopped'
#         self.readTask.stop()
#
#     def stop_and_clear(self):
#         self.stop()
#         self.clear()
#
#     def __del__(self):
#         try:
#             self.stop()
#             self.clear()
#         # doprint('debug', 'DAQmxLineCounter: at exit')
#         except:
#             pass
#
#
# class Dp5Counter(QObject):
#     """class for Amptek DP5 counters that are in the counter module."""
#
#     def __init__(self, name='Amptek DP5', iface='usb', params={}):
#         # aio.__init__(self)
#         super(Dp5Counter, self).__init__()
#
#         if iface not in ['usb', 'serial', 'ip']:
#             doprint('error', "Unable to create counter '%s' with iface type '%s'." % (name, iface))
#             raise MotorError("Counter type must be one of 'usb', 'serial', 'ip'")
#
#         self.name = name
#         self.zero = float(0)
#         self.value = 0
#         self.DESC = name
#         # QObject.connect(self.DESC, SIGNAL('changed(object)'), self.on_device_active)
#
#         self.iface = iface
#
#         self.dp5lib = dp5_Functions
#         self.dp5Cnsts = dp5_Constants
#         self.max_num_samples = params['max_samples']
#         self.dwell = params['dwell']
#
#         self.dp5lib.InitUSB()
#
#     def get_report(self):
#         """ return a dict that reresents all of the settings for this device """
#         dct = {}
#         dct_put(dct, 'name', self.name)
#         return (dct)
#
#     def _on_name_change(self, pv, val):
#         if val != '':
#             self.name = val
#
#     def count(self, t):
#         if t <= 0.0:
#             return self.getValue() - self.zero
#
#         doprint('debug', 'Averaging detector (%s) for %0.2f sec.' % (self.name, t))
#         interval = 0.01
#         values = []
#         time_left = t
#         while time_left > 0.0:
#             values.append(self.getValue())
#             time.sleep(interval)
#             time_left -= interval
#         total = (sum(values, 0.0) / len(values)) - self.zero
#         doprint('debug', '(%s) Returning average of %d values for %0.2f sec.' % (self.name, len(values), t))
#         return total


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


class BaseGate(BaseDevice):
    """
    This class represents a counter output task that generates a pulse train used to gate other
    counter tasks, this it is stored here in the counter module
    """

    # def __init__(self, prefix, num_points=1, dwell=2.0, duty=0.5, soft_trig=False):
    def __init__(self, prefix):
        super(BaseGate, self).__init__(prefix)
        self.p_prefix = prefix
        self.p_dwell = 2.0
        self.p_duty_cycle = 0.5
        self.p_num_points = 1
        self.run = self.add_pv(self.p_prefix + ':Run')
        self.dwell = self.add_pv(self.p_prefix + ':Dwell')
        self.max_points = self.add_pv(self.p_prefix + ':MaxPoints')
        self.duty_cycle = self.add_pv(self.p_prefix + ':DutyCycle')
        self.trig_type = self.add_pv(self.p_prefix + ':TriggerType')
        self.trig_delay = self.add_pv(self.p_prefix + ':TriggerDelay')
        self.retrig = self.add_pv(self.p_prefix + ':Retriggerable')

        self.device_select = self.add_pv(self.p_prefix + ':DeviceSelect')
        self.counter_select = self.add_pv(self.p_prefix + ':CounterSelect')
        self.sample_mode = self.add_pv(self.p_prefix + ':SampleMode')
        self.output_idle_state = self.add_pv(self.p_prefix + ':OutputIdleState')
        self.clock_src_select = self.add_pv(self.p_prefix + ':ClockSrcSelect')
        self.retriggerable = self.add_pv(self.p_prefix + ':Retriggerable')
        self.trigger_type = self.add_pv(self.p_prefix + ':TriggerType')
        self.trig_src_select = self.add_pv(self.p_prefix + ':TrigSrcSelect')
        self.edge_select = self.add_pv(self.p_prefix + ':EdgeSelect')
        self.trigger_delay = self.add_pv(self.p_prefix + ':TriggerDelay')
        self.soft_trigger = self.add_pv(self.p_prefix + ':SoftTrigger')
        self.run_rbv = self.add_pv(self.p_prefix + ':Run_RBV')
        self.runningcb_idx = self.run_rbv.add_callback(self.on_running)

        self.trig = None

        # if(soft_trig):
        #	self.trig = self.add_pv(self.p_prefix + ':SoftTrigger')

        self.isRunning = 0
        time.sleep(0.4)
        self.stop()

    # self.configure()
    def get_name(self):
        return (self.p_prefix + ':Run')

    def on_running(self, **kwargs):
        rawData = kwargs['value']
        # print 'BaseGate: on_running' , kwargs
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

    def stop(self):
        if (self.run.connected):
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


class BaseCounter(BaseDevice):
    changed = QtCore.pyqtSignal(int, object)
    proc_queue = QtCore.pyqtSignal()

    def __init__(self, prefix):
        super(BaseCounter, self).__init__(prefix)
        self.p_prefix = prefix
        self.data_q = queue.Queue()
        self.proc_queue.connect(self.on_proc_queue)

        self.run = self.add_pv(self.p_prefix + ':Run')

        self.row_mode = self.add_pv(self.p_prefix + ':RowMode')
        self.points_per_row = self.add_pv(self.p_prefix + ':PointsPerRow')
        self.device_select = self.add_pv(self.p_prefix + ':DeviceSelect')
        self.counter_select = self.add_pv(self.p_prefix + ':CounterSelect')
        self.signal_src_pin_select = self.add_pv(self.p_prefix + ':SignalSrcPinSelect')
        self.initial_count = self.add_pv(self.p_prefix + ':InitialCount')
        self.count_dir = self.add_pv(self.p_prefix + ':CountDir')
        self.max_points = self.add_pv(self.p_prefix + ':MaxPoints')
        self.sample_mode = self.add_pv(self.p_prefix + ':SampleMode')
        self.signal_src_clock_select = self.add_pv(self.p_prefix + ':SignalSrcClockSelect')
        self.sampling_rate = self.add_pv(self.p_prefix + ':SamplingRate')
        self.edge_select = self.add_pv(self.p_prefix + ':EdgeSelect')
        self.retriggerable = self.add_pv(self.p_prefix + ':Retriggerable')
        self.trig_type = self.add_pv(self.p_prefix + ':TriggerType')
        self.trig_src_select = self.add_pv(self.p_prefix + ':TrigSrcSelect')
        self.row_num_rbv = self.add_pv(self.p_prefix + ':RowNum_RBV')
        self.point_num_rbv = self.add_pv(self.p_prefix + ':PointNum_RBV')
        self.read_counts = self.add_pv(self.p_prefix + ':ReadCounts')
        self.point_dwell = self.add_pv(self.p_prefix + ':PointDwell')
        self.single_value_rbv = self.add_pv(self.p_prefix + ':SingleValue_RBV')
        self.run_rbv = self.add_pv(self.p_prefix + ':Run_RBV')

        # self.data = self.add_pv(self.p_prefix + ':Waveform_RBV')
        self.data = PV(self.p_prefix + ':Waveform_RBV')

        self.runningcb_idx = self.run_rbv.add_callback(self.on_running, with_ctrlvars=False)

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

    def get_name(self):
        return self.p_prefix + ':Run'

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
