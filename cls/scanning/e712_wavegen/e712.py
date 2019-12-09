import socket
import time
from time import mktime, strftime, strptime, gmtime
import numpy as np
import math
import os
import copy
import traceback
import io
import queue

from PyQt5 import uic, QtWidgets, QtCore, QtGui

from bcm.devices import BaseGate, BaseCounter
from cls.scanning.scan_cfg_utils import set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan
from cls.plotWidgets.curveWidget import CurveViewerWidget, get_basic_line_style,get_trigger_line_style
from cls.plotWidgets.imageWidget import make_default_stand_alone_stxm_imagewidget
from cls.plotWidgets.utils import *
from cls.utils.images import array_to_jpg
from cls.utils.json_utils import json_to_file, dict_to_json
from cls.utils.sig_utils import reconnect_signal
#from cls.types.stxmTypes import scanning_mode
import cls.types.stxmTypes as types

#from epics import BaseDevice
from bcm.devices import BaseDevice

from cls.utils.roi_utils import get_base_start_stop_roi, get_base_energy_roi

from cls.applications.pyStxm import abs_path_to_ini_file

from cls.utils.json_threadsave import loadJson
from cls.utils.dict_utils import dct_merge
from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *

from cls.appWidgets.dialogs import getOpenFileName

from cls.scanning.e712_wavegen.e712_errors import e712_errors
from cls.scanning.e712_wavegen.e712_utils import *
from cls.scanning.e712_wavegen.e712_com_cmnds import e712_cmds, make_base_e712_com_dict
from cls.scanning.e712_wavegen.e712_datarecorder import PI_E712_DataRecorder

from cls.utils.cfgparser import ConfigClass
from cls.utils.file_system_tools import get_next_file_in_seq
from cls.utils.json_threadsave import ThreadJsonSave
from cls.utils.image_threadsave import ThreadImageSave
from cls.utils.save_settings import SaveSettings

from cls.scanning.e712_wavegen.e712_com_thread import E712ComThread
from cls.scanning.e712_wavegen.ddl_store import DDL_Store, gen_ddl_database_key

from bcm.devices import e712_sample_motor

appConfig = ConfigClass(abs_path_to_ini_file)
#dataDir = os.path.join(appConfig.get_value('DEFAULT', 'dataDir') ,'e712Testing','ddlTesting')
#dataDir = os.path.join(appConfig.get_value('DEFAULT', 'dataDir') ,'e712Testing','ddl_testing_apr24')
_logger = get_module_logger(__name__)

# COARSE_SAMPLEFINE (formerly 'conventional') scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=SAMPLE_FINE
#scanning_mode = COARSE_SAMPLEFINE

# GONI_ZONEPLATE scanning mode = Sample_pos_mode=GONIOMETER, sample_fine_pos_mode=ZONEPLATE
#scanning_mode = GONI_ZONEPLATE

# COARSE_ZONEPLATE scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=ZONEPLATE
#scanning_mode = COARSE_ZONEPLATE

DATARECORDER_ENABLED = True

scan_mode = appConfig.get_value('DEFAULT', 'scanning_mode')
if(scan_mode == types.scanning_mode.get_str_by_num(types.scanning_mode.COARSE_SAMPLEFINE)):
    from bcm.devices.device_names import (DNM_SAMPLE_FINE_X, DNM_SAMPLE_FINE_Y, DNM_ENERGY)
    # SAMPLE
    X_AXIS_ID = 1
    Y_AXIS_ID = 2
    X_WAVE_TABLE_ID = 1
    Y_WAVE_TABLE_ID = 2
    FINE_X = DNM_SAMPLE_FINE_X
    FINE_Y = DNM_SAMPLE_FINE_Y
    ENERGY = DNM_ENERGY
    ZONEPLATE_SCANNING = False
    SCAN_MODE = types.scanning_mode.COARSE_SAMPLEFINE

elif(scan_mode == types.scanning_mode.get_str_by_num(types.scanning_mode.GONI_ZONEPLATE)):
    from bcm.devices.device_names import (DNM_ZONEPLATE_X, DNM_ZONEPLATE_Y, DNM_ENERGY)

    X_AXIS_ID = 3
    Y_AXIS_ID = 4
    X_WAVE_TABLE_ID = 3
    Y_WAVE_TABLE_ID = 4
    FINE_X = DNM_ZONEPLATE_X
    FINE_Y = DNM_ZONEPLATE_Y
    ENERGY = DNM_ENERGY
    ZONEPLATE_SCANNING = True
    SCAN_MODE = types.scanning_mode.GONI_ZONEPLATE

elif(scan_mode == types.scanning_mode.get_str_by_num(types.scanning_mode.COARSE_ZONEPLATE)):
    from bcm.devices.device_names import (DNM_ZONEPLATE_X, DNM_ZONEPLATE_Y, DNM_ENERGY)

    X_AXIS_ID = 3
    Y_AXIS_ID = 4
    X_WAVE_TABLE_ID = 3
    Y_WAVE_TABLE_ID = 4
    FINE_X = DNM_ZONEPLATE_X
    FINE_Y = DNM_ZONEPLATE_Y
    ENERGY = DNM_ENERGY
    ZONEPLATE_SCANNING = True
    SCAN_MODE = types.scanning_mode.COARSE_ZONEPLATE
else:
    _logger.error('E712: could not determine scanning mode')
    exit()

WAVEFORM_GEN_CYCLE_TIME = 0.00005 # in seconds

MAX_NUM_DATAREC_POINTS = 699050
MIN_DATAREC_RATE = 0.00005

#MIN_LINE_RETURN_TIME = 0.04
MIN_LINE_RETURN_TIME = 0.005

MIN_PNT_TIME_RES = 0.00005
PNT_TIME_RES = MIN_PNT_TIME_RES
MAX_WAVTBL_PTS = 262144
MAX_WAVTBL_TIME = PNT_TIME_RES * MAX_WAVTBL_PTS #13.1072 seconds, this needs to be shared between all 4 Wavetables
#WIDTH_DISTORTION_FUDGE = 0.01
#this var is used to extend the segment line such that the desired pulse train finishes when the stage is still at constant velocity
#June 15 2018
WIDTH_DISTORTION_FUDGE = 0.000

SEND_LIST = []

except_busy = False

def on_wave_table_rate_changed(wave_table_rate):
    global PNT_TIME_RES, MIN_DATAREC_RATE, MAX_WAVTBL_TIME, WAVEFORM_GEN_CYCLE_TIME
    PNT_TIME_RES = WAVEFORM_GEN_CYCLE_TIME = MIN_DATAREC_RATE * wave_table_rate
    MAX_WAVTBL_TIME = PNT_TIME_RES * MAX_WAVTBL_PTS

def calc_optimal_wavetable_rate(npoints, dwell_sec, forced_rate=None):
    '''
    find the minnimum wavetable rate that will allow npoints of dwell time to fir into the finite wavegen table memory
    :param npoints:
    :param dwell_ms:
    :param forced_rate:
    :return:
    '''
    global MIN_PNT_TIME_RES, PNT_TIME_RES, MIN_DATAREC_RATE, MAX_WAVTBL_TIME
    #start at wavetable rate of 1 and increase until the points fit in the memory (max num points of 262144)
    time_between_pnts = 0.005
    line_time = (dwell_sec + time_between_pnts) * npoints
    print('calc_optimal_wavetable_rate: line time = %.2f sec' % line_time)
    if(forced_rate is not None):
        t_per_pnt = MIN_PNT_TIME_RES * forced_rate
        num_wgpnts_needed = line_time / t_per_pnt
        # only look at using 1/2 max because I need points for X and Y
        half_max_wgpnts = MAX_WAVTBL_PTS * 0.5
        if (num_wgpnts_needed < half_max_wgpnts):
            print('wavetable rate is forced to %d = %d pnts/%d' % (forced_rate, num_wgpnts_needed, MAX_WAVTBL_PTS))
        rate = forced_rate
    else:
        for rate in range(1,100):
            t_per_pnt = MIN_PNT_TIME_RES * rate
            num_wgpnts_needed = line_time / t_per_pnt
            #only look at using 1/2 max because I need points for X and Y
            half_max_wgpnts = MAX_WAVTBL_PTS * 0.5
            if(num_wgpnts_needed < half_max_wgpnts):
                print('optimal wavetable rate is %d = %d pnts/%d' % (rate, num_wgpnts_needed, MAX_WAVTBL_PTS))
                break
    return(rate)

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    global except_busy
    if(except_busy):
        return
    except_busy = True
    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to <%s>.\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("yourmail at server.com", "")
    versionInfo = "0.0.1"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(str(notice) + str(msg) + str(versionInfo))
    errorbox.exec_()
    except_busy = False

class E712Exception(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


def calc_optimal_data_record_rate(dwell_sec, nptsX, nptsY):
    total_scan_time = ((dwell_sec * nptsX) * nptsY)
    for i in range(1,20):
        num_points_required = total_scan_time / (i * MIN_DATAREC_RATE)
        if(num_points_required < MAX_NUM_DATAREC_POINTS):
            return(i)
    return(None)




def make_dflt_settings_dct():
    dct = {}
    dct['dwell'] = 0.5
    dct['max_rcv_bytes']= 16384
    dct['max_sock_timeout']= 1.0
    dct['pnt_step_time']= 0.04
    dct['pnt_start_delay']= 0.300
    dct['pnt_updown_time']= 0.005

    dct['line_start_delay'] = 0.300
    dct['line_accrange']= 1.2
    dct['line_step_time']= 0.08
    dct['line_updown_time']= 0.015
    dct['line_return_time'] = 0.08
    dct['line_trig_time'] = 0.04

    dct['mode'] = 0
    dct['numX'] = 50
    dct['numY'] = 50
    dct['startX'] = -45.0
    dct['stopX'] = 45.0
    dct['startY'] = -45.0
    dct['stopY'] = 45.0

    dct['x1_wavTbl_id'] = 0
    dct['y1_wavTbl_id'] = 0
    dct['x2_wavTbl_id'] = 0
    dct['y2_wavTbl_id'] = 0

    return(dct)


def make_dflt_ddl_table_settings_dct():
    """
    DDL is used in addition to the "normal" servo algorithm and makes it possible to achieve significantly better position accuracy for dynamic applications
    with periodic motion. A "DDL table" is used to compensate for the tracking error of an axis. The available tables and settings depend on your controller.
    See the User Manual of your controller for more information and for how to activate the DDL feature.

    CAUTION:
    An initialization phase is required to fill the DDL table with data. DDL initialization must be repeated when a new stage is connected, the servo parameters
    are changed (e.g. due to load changes) or the waveform is changed.
    Before you work with the DDL, adjust the servo parameters (notch filter frequency, servo-loop P-term (loop gain), servo-loop I-term (time constant),
    servo-loop slew rate) using the NanoCapture software to eliminate any residual oscillations.


    How to initialize and use the DDL for an axis:

    Step1: On the Wave Table Editor tab card, define the waveform.

    Step2: Configure the DDL for the axis:
    a) Select the axis.
    b) Select the DDL table to use for the axis (presently, the factory default can not be changed).
    c) Set the number of wave generator cycles to use for DDL initialization ("DDL init. repeat", factory default = 35).
    d) Recalculate the internal DDL processing parameters if necessary by pressing "Calculate the processing parameters".

    Step3: On the Wave Generator tab card:
    a) Select the wave generator and hence the axis (the same axis as selected on the DDL Settings tab card).
    b) Assign the waveform (i.e. the wave table) to the axis.
    c) Activate the "Use and reinitialize DDL" flag.
    d) Start the wave generator and thus also the DDL initialization/usage.

    Step4: Check the content of the DDL table in the graphics display. Press "Get the DDL table" to load the data.

    As long as your application does not change, you can use the current DDL table content without new initialization. In this case, deactivate the
    "Use and reinitialize DDL" flag on the "Wave Generator" tab card and start the wave generator with the "Use DDL" flag activated.


    NOTES

    It is recommended to start the DDL initialization for all axes at the same time. Each new initialization will stop all running initialization processes.

    The DDL table content and the calculated processing parameters will be lost when the controller is powered down or rebooted.
    :return:
    """
    dct = {}
    dct['dwell'] = 0.5
    dct['max_rcv_bytes']= 16384
    dct['max_sock_timeout']= 1.0
    dct['pnt_start_delay']= 0.300
    dct['pnt_step_time']= 0.04
    dct['pnt_updown_time']= 0.005
    dct['line_accrange']= 1.2
    dct['line_step_time']= 0.08
    dct['line_updown_time']= 0.015
    dct['line_return_time'] = 0.08
    dct['line_trig_time'] = 0.04

    dct['mode'] = 0
    dct['numX'] = 50
    dct['numY'] = 50
    dct['startX'] = -45.0
    dct['stopX'] = 45.0
    dct['startY'] = -45.0
    dct['stopY'] = 45.0

    dct['x1_wavTbl_id'] = 0
    dct['y1_wavTbl_id'] = 0
    dct['x2_wavTbl_id'] = 0
    dct['y2_wavTbl_id'] = 0


    return(dct)

class PI_E712_wave_generator(QtCore.QObject):

    #RUSS py3 status_changed = QtCore.pyqtSignal(bool)
    status_changed = QtCore.pyqtSignal(object)


    def __init__(self, prefix='IOCE712:',wvgen_num=1):
        super(PI_E712_wave_generator, self).__init__()
        self.prefix = prefix
        self.wg_num = wvgen_num

        self.wavtbl_len_rbv = BaseDevice('%sWaveTbl%dLen_RBV' % (self.prefix, self.wg_num), rd_only=True)

        self.clr_wavtbl = BaseDevice('%sClearWavTbl%d' % (self.prefix, self.wg_num))
        # self.get_wavtbl = BaseDevice('%sGetWavTbl%d' % (self.prefix, self.wg_num))
        # self.wavtbl_rbv = BaseDevice('%sWaveTbl%d_RBV' % (self.prefix, self.wg_num))

        self.clr_ddltbl = BaseDevice('%sClearDDLTbl%d' % (self.prefix, self.wg_num))
        self.ddltbl = BaseDevice('%sDDLTbl%d' % (self.prefix, self.wg_num))
        # self.get_ddltbl = BaseDevice('%sGetDDLTbl%d' % (self.prefix, self.wg_num))
        # self.ddltbl_rbv = BaseDevice('%sDDLTbl%d_RBV' % (self.prefix, self.wg_num))

        self.start_mode = BaseDevice('%sWavTbl%dStartMode' % (self.prefix, self.wg_num))
        self.start_mode_rbv = BaseDevice('%sWavTbl%dStartMode_RBV' % (self.prefix, self.wg_num), rd_only=True)

        self.use_ddl = BaseDevice('%sWavTbl%dUseDDL' % (self.prefix, self.wg_num))
        self.use_ddl_rbv = BaseDevice('%sWavTbl%dUseDDL_RBV' % (self.prefix, self.wg_num), rd_only=True)

        self.use_reinit_ddl = BaseDevice('%sWavTbl%dUseReinitDDL' % (self.prefix, self.wg_num))
        self.use_reinit_ddl_rbv = BaseDevice('%sWavTbl%dUseReinitDDL_RBV' % (self.prefix, self.wg_num), rd_only=True)

        self.start_at_end_pos = BaseDevice('%sWavTbl%dStartAtEndPos' % (self.prefix, self.wg_num))
        self.start_at_end_pos_rbv = BaseDevice('%sWavTbl%dStartAtEndPos_RBV' % (self.prefix, self.wg_num), rd_only=True)

        self.wavgen_usetbl_num = BaseDevice('%sWavGen%dUseTblNum' % (self.prefix, self.wg_num))
        self.wavgen_usetbl_num_rbv = BaseDevice('%sWavGen%dUseTblNum_RBV' % (self.prefix, self.wg_num), rd_only=True)

        #self.ddl_tbl = BaseDevice('%sDDLTbl%d' % (self.prefix, self.wg_num))

        self.status_rbv = BaseDevice('%sWaveGen%dStatus_RBV' % (self.prefix, self.wg_num), rd_only=True)

        #self.status_rbv.add_callback(self.on_status_changed)
        self.status_rbv.changed.connect(self.on_status_changed)



    # def on_status_changed(self, **kwargs):
    #     val = kwargs['value']
    #     self.status_changed.emit(val)
    def on_status_changed(self, val):
        self.status_changed.emit(val)

    def clear_wavtable(self):
        #self.clr_wavtbl.put(1)
        self.clr_wavtbl.put(1)

    def clear_ddltable(self):
        #self.clr_ddltbl.put(1)
        self.clr_ddltbl.put(1)



class PI_E712(QtCore.QObject):

    wvgen_status = QtCore.pyqtSignal(object)
    elapsed_time_chgd = QtCore.pyqtSignal(object)
    estimated_time_chgd = QtCore.pyqtSignal(object)
    table_data_changed = QtCore.pyqtSignal(object)

    def __init__(self, x_tbl_id=3, y_tbl_id=4, prefix='IOCE712:', e712com=None,e712comQ=None):
        super(PI_E712, self).__init__()
        self.prefix = prefix
        self.x_tbl_id = x_tbl_id
        self.y_tbl_id = y_tbl_id
        self.init_tuning_params(None)
        self.is_pxp = False

        #self.ddl_tables_ss = SaveSettings('ddl_tables.json', dct_template=osa_smplhldr_dct)

        self.xAxisId = BaseDevice('%sXAxisId_RBV' % self.prefix)

        self.ddl_db = DDL_Store()

        self.wg1 = PI_E712_wave_generator(prefix=prefix, wvgen_num=1)
        self.wg2 = PI_E712_wave_generator(prefix=prefix, wvgen_num=2)
        self.wg3 = PI_E712_wave_generator(prefix=prefix, wvgen_num=3)
        self.wg4 = PI_E712_wave_generator(prefix=prefix, wvgen_num=4)

        self.e712_cmnd_queue = e712comQ
        self.e712_wv_table_data = e712com
        self.e712_wv_table_data.data_changed.connect(self.on_e712_com)

        # self.e712_cmnd_queue = Queue.Queue()
        # self.e712_wv_table_data = E712ComThread(self.prefix, self.e712_cmnd_queue)
        # self.e712_wv_table_data.data_changed.connect(self.on_e712_com)
        #
        # #self.e712_com_thread = QtCore.QThread()
        # #self.e712_wv_table_data.moveToThread(self.e712_com_thread)
        # #self.e712_com_thread.started.connect(self.e712_wv_table_data.start_q_mon)
        # self.e712_wv_table_data.start()

        #self.wg1.status_changed.connect(self.on_status)
        #self.wg2.status_changed.connect(self.on_status)
        self.wg3.status_changed.connect(self.on_status)
        #self.wg4.status_changed.connect(self.on_status)


        # self.wg_cmnds = BaseDevice('%sSendCmnds' % self.prefix)

        self.run_scan_config = BaseDevice('%srun_scan_config' % self.prefix)

        self.calc_ddl_params = BaseDevice('%sCalcDDLParms' % self.prefix)

        self.wg_clr_trig_table = BaseDevice('%sClearTrigTbl' % self.prefix)
        #self.wg_get_trig_table = BaseDevice('%sGetTrigTbl' % self.prefix)
        #self.wg_trig_table = BaseDevice('%sTrigTbl_RBV' % self.prefix)

        self.e712_idn = BaseDevice('%sGetIDN_RBV' % self.prefix)

        self.start_wg = BaseDevice('%sStartWavgen' % self.prefix)
        self.stop_wg = BaseDevice('%sStopWavgen' % self.prefix)

        self.calc_ddl_parms = BaseDevice('%sCalcDDLParms' % self.prefix)

        self.num_cycles = BaseDevice('%sNumCycles' % self.prefix)
        self.num_cycles_rbv = BaseDevice('%sNumCycles_RBV' % self.prefix)

        self.ttl_pnts_left_rbv = BaseDevice('%sTotalPointsLeft_RBV' % self.prefix)

        self.wave_tbl_rate = BaseDevice('%sWaveTableRate' % self.prefix)
        self.wave_tbl_rate_rbv = BaseDevice('%sWaveTableRate_RBV' % self.prefix)

        self.x_axis_id = BaseDevice('%sXAxisId' % self.prefix)
        self.x_axis_id_rbv = BaseDevice('%sXAxisId_RBV' % self.prefix)

        self.y_axis_id = BaseDevice('%sYAxisId' % self.prefix)
        self.y_axis_id_rbv = BaseDevice('%sYAxisId_RBV' % self.prefix)

        self.x_start_pos = BaseDevice('%sXStartPos' % self.prefix)
        self.x_start_pos_rbv = BaseDevice('%sXStartPos_RBV' % self.prefix)

        self.y_start_pos = BaseDevice('%sYStartPos' % self.prefix)
        self.y_start_pos_rbv = BaseDevice('%sYStartPos_RBV' % self.prefix)

        self.comm_status_rbv = BaseDevice('%sCommStatus_RBV' % self.prefix)

        self.comm_status_rbv = BaseDevice('%sCommStatus_RBV' % self.prefix)

        self.xstage_return_time = 0.1
        self.hline_in_points = 0
        self.is_running = False
        self.return_npts = 0

        self.get_e712_id()
        self.start_time = 0
        self.elapsed_ticker = 0

        self.elapsed_timer = QtCore.QTimer()
        self.elapsed_timer.timeout.connect(self.check_time)
        #self.e712_com_thread.start()

    def reinit_vars(self):
        self.return_npts = 0
        self.hline_in_points = 0
        self.is_running = False

    def reset_run_scan_config(self):
        self.run_scan_config.put(0)

    def get_ttl_points_remaining(self):
        return(self.ttl_pnts_left_rbv.get())

    def on_e712_com(self, e712com_dct):
        self.table_data_changed.emit(e712com_dct)

    def is_busy(self):
        val = self.comm_status_rbv.get()
        if(val):
            return(True)
        else:
            return(False)

    def calc_new_estemate(self, y_npoints, in_seconds=False):
        total_time_sec = float(y_npoints) * (float(self.hline_in_points) * WAVEFORM_GEN_CYCLE_TIME)
        s = 'Estimated time: %s' % self.secondsToStr(total_time_sec)
        self.estimated_time_chgd.emit(s)
        if(in_seconds):
            return(total_time_sec)
        else:
            return(s)

    def start_timer(self):
        # timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
        self.elapsed_timer.start(1000)
        self.start_time = time.time()  # taking current time as starting time


    def secondsToStr(self, t):
        return (strftime("%H:%M:%S", gmtime(t)))

    def check_time(self):
        if (self.start_time is None):
            self.start_time = time.time()
        self.elapsed_time = time.time() - self.start_time
        self.elapsed_time_chgd.emit(self.secondsToStr(self.elapsed_time))

    def calc_ddl_parameters(self):
        self.calc_ddl_params.put(1)

    #def calc_ddl_parameters(self, wavetbl):
    #    self.calc_ddl_params.put(wavetbl)

    def clear_trigger_table(self):
        self.wg_clr_trig_table.put(1)

    def on_status(self, val):
        #print 'status of wg3 is [%d]' % val
        if((val == 0) and self.is_running):
            self.stop_wave_generator()
        elif(val == 1):
            self.is_running = True

        self.wvgen_status.emit(val)

    def start_wave_generator(self):
        self.start_timer()
        self.start_wg.put(1)

    def stop_wave_generator(self):
        self.elapsed_timer.stop()
        self.stop_wg.put(1)

    def set_num_cycles(self, num_cycles):
        self.num_cycles.put(int(num_cycles))

    def get_num_cycles(self):
        val = self.num_cycles_rbv.get()
        return(int(val))


    # def set_wave_table_rate(self, rate):
    #     self.wave_tbl_rate.put(int(rate))
    def set_wave_table_rate(self, rate):
        self.wave_tbl_rate.put(int(rate))
        #update the timing constants
        on_wave_table_rate_changed(rate)

    def get_wave_table_rate(self):
        val = self.wave_tbl_rate_rbv.get()
        return(int(val))

    def set_x_axis_id(self, id):
        self.x_axis_id.put(int(id))

    def get_x_axis_id(self):
        val = self.x_axis_id_rbv.get()
        return (int(val))

    def get_y_axis_id(self):
        val = self.y_axis_id_rbv.get()
        return (int(val))

    def set_axis_wg_usetbl_num(self, axis=-1, num=-1):
        '''
        A convienience function to set the x1 axis wavegenerator (#1)
        to use a particular wavetable (1 - 120).

        Each waveform generator is locked to an individual axis
            axis 1 -> wavegenerator 1
            axis 2 -> wavegenerator 2
            axis 3 -> wavegenerator 3
            axis 4 -> wavegenerator 4
        :param num:
        :return:
        '''
        if((num > 0) and (num <=120)):
            if(axis is 1):
                self.wg1.wavgen_usetbl_num.put(num)
            elif(axis is 2):
                self.wg2.wavgen_usetbl_num.put(num)
            elif(axis is 3):
                self.wg3.wavgen_usetbl_num.put(num)
            elif(axis is 4):
                self.wg4.wavgen_usetbl_num.put(num)
            else:
                _logger.error('invalid axis ID number ->[%d] must be between 1 and 4' % axis)
        else:
            _logger.error('invalid wavetable number ->[%d] must be between 1 and 120' % num)


    def set_y_axis_id(self, id):
        self.y_axis_id.put(int(id))

    def set_x_start_pos(self, pos):
        self.x_start_pos.put(float(pos))

    def get_x_start_pos(self):
        val = self.x_start_pos_rbv.get()
        return (float(val))

    def set_y_start_pos(self, pos):
        self.y_start_pos.put(float(pos))

    def get_y_start_pos(self):
        val = self.y_start_pos_rbv.get()
        return (float(val))


    def get_wav_tbl_length(self, xaxis):
        #xaxis = int(self.xAxisId.get())
        val = 0
        if(xaxis is 1):
            val = self.wg1.wavtbl_len_rbv.get()
        elif(xaxis is 2):
            val = self.wg2.wavtbl_len_rbv.get()
        elif (xaxis is 3):
            val = self.wg3.wavtbl_len_rbv.get()
        elif (xaxis is 4):
            val = self.wg4.wavtbl_len_rbv.get()
        print('get_wav_tbl_length[%d]: = %d' % (xaxis, val))
        return(int(val))


    def get_trig_table(self):
        data = []
        self.wg_get_trig_table.put(1)
        time.sleep(0.25)
        data = self.wg_trig_table.get()
        return(data)

    def get_ddl_table(self, tblid, cb=None):
        # if(DATARECORDER_ENABLED):
        #     #datarecorder and ddl stuff are mutually exclusive
        #     return

        data = []
        e712com_dct = make_base_e712_com_dict(e712_cmds.GET_DDL_DATA, tblid, None, cb=cb)
        self.e712_cmnd_queue.put_nowait(e712com_dct)

    def store_ddl_table(self, key, data, dct=None):
        if(data is None):
            _logger.error('store_ddl_table: was passed data=None for some reason')
            return
        if(len(data) > 0):
            #do not save a table that has a zero in it
            #if(np.prod(data) != 0.0):
            self.ddl_db.save_ddl_table(key, data, dct=dct)

    def put_ddl_table(self, tblid, data):
        if (tblid == 1):
            self.wg1.clr_ddltbl.put(1)
        elif (tblid == 2):
            self.wg2.clr_ddltbl.put(1)
        elif (tblid == 3):
            self.wg3.clr_ddltbl.put(1)
        elif (tblid == 4):
            self.wg4.clr_ddltbl.put(1)

        if(tblid == 1):
            self.wg1.ddltbl.put(data)
        elif(tblid == 2):
            self.wg2.ddltbl.put(data)
        elif (tblid == 3):
            self.wg3.ddltbl.put(data)
        elif (tblid == 4):
            self.wg4.ddltbl.put(data)

    def get_all_wav_table(self, cb=None):
        e712com_dct = make_base_e712_com_dict(e712_cmds.GET_ALL_WAV_DATA, None, None, cb=cb)
        self.e712_cmnd_queue.put_nowait(e712com_dct)


    def get_wav_table(self, tblid, cb=None):
        data = []
        e712com_dct = make_base_e712_com_dict(e712_cmds.GET_WAV_DATA, tblid, None, cb=cb)
        self.e712_cmnd_queue.put_nowait(e712com_dct)

    def send_command_string(self, cmnds, cb=None, verbose=True):
        e712com_dct = make_base_e712_com_dict(e712_cmds.SEND_COMMANDS, cmnds, None, cb=cb)
        self.e712_cmnd_queue.put_nowait(e712com_dct)

    def set_is_pxp(self, is_it=False):
        self.is_pxp = is_it

    def get_wavgen_sts(self):
        sts = copy.copy(self.sts)
        return (sts)

    def init_tuning_params(self, dct=None):
        if (dct is None):
            dct = make_dflt_settings_dct()

        self.dwell = dct['dwell']
        self.max_rcv_bytes = dct['max_rcv_bytes']
        self.max_sock_timeout = dct['max_sock_timeout']
        self.pnt_start_delay = dct['pnt_start_delay']
        self.pnt_step_time = dct['pnt_step_time']
        self.pnt_updown_time = dct['pnt_updown_time']

        self.line_start_delay = dct['line_start_delay']
        self.line_accrange = dct['line_accrange']
        self.line_step_time = dct['line_step_time']
        self.line_updown_time = dct['line_updown_time']
        self.line_return_time = dct['line_return_time']
        #self.line_trig_time = dct['line_trig_time']


    def get_e712_id(self):
        pass
        #data = self.sock_send('*IDN?')
        #data = self.e712_idn.get()
        #if (len(data) is 0):
        #    print 'oops trouble connecting to E712'
        #    exit()
        #else:
        #    print 'received "%s"' % data
        #return (data)

    def clear_wavetable(self, tbl_id):
        if(tbl_id is 1):
            self.wg1.clear_wavtable()
        elif(tbl_id is 2):
            self.wg2.clear_wavtable()
        elif (tbl_id is 3):
            self.wg3.clear_wavtable()
        elif (tbl_id is 4):
            self.wg4.clear_wavtable()

    def clear_DDLtable(self, tbl_id):
        if (tbl_id is 1):
            self.wg1.clear_ddltable()
        elif (tbl_id is 2):
            self.wg2.clear_ddltable()
        elif (tbl_id is 3):
            self.wg3.clear_ddltable()
        elif (tbl_id is 4):
            self.wg4.clear_ddltable()

    def calc_hline_time(self, dwell, npoints, pxp=True):

        segtime = dwell * 0.001
        if(pxp):
            #hline_in_sec = (npoints * (self.pnt_step_time + segtime) + self.xstage_return_time)
            hline_in_sec = (npoints * (self.pnt_step_time + segtime) + self.line_return_time)
        else:
            hline_in_sec = ((npoints * segtime) + self.line_step_time + self.line_return_time)
        return(hline_in_sec)

    def define_x_segments(self, start, stop, npoints, dwell, x_tbl_id, send=True, use_fit_function=False):
        '''
        Define the points that make up the horizontal line movement
        :param start: 
        :param stop: 
        :param npoints: 
        :param dwell: 
        :param x_tbl_id: 
        :param send: 
        :param use_fit_function: 
        :return: 
        '''
        # start, stop, step, npoints, dwell, do_clear=False, tbl_id=1)
        rng = stop - start

        step = rng / npoints
        lst = self.gen_x_line_wav_strs(start, stop, step, npoints, dwell, do_clear=True, tbl_id=x_tbl_id)
        
        #decide whether to use the fit function to pick the step time or use a user controlled value from teh GUI
        if(use_fit_function):
            step_time = self.get_fitted_step_time(step, dwell, line=False)
        else:
            step_time = self.line_step_time
            
        segtime = dwell * 0.001
        
        
        #self.hline_in_points = ((npoints * segtime) + step_time + self.line_return_time) / WAVEFORM_GEN_CYCLE_TIME
        # WAV 1 X LIN 6400 8 -1.5 6400 0 1200
        # WAV 1 & LIN 1200 -8 6.5 1200 0 400
        if (send):
            self.send_list(lst)
        return (lst)

    def define_y_segments(self, start, stop, npoints, dwell, y_tbl_id, send=True):
        # start, stop, step, npoints, dwell, do_clear=False, tbl_id=1)
        rng = float(stop - start)
        step = float(rng / npoints)
        step_time = self.pnt_step_time
        sit_time = dwell
        lst = self.gen_y_line_wav_strs(start, stop, step, step_time, dwell, do_clear=True, tbl_id=y_tbl_id)
        # WAV 1 X LIN 6400 8 -1.5 6400 0 1200
        # WAV 1 & LIN 1200 -8 6.5 1200 0 400
        if (send):
            self.send_list(lst)
        return (lst)

    def define_pxp_segments(self, start, step, npoints, dwell, tblid=1, send=True, do_clear=True, use_fit_function=False, is_y=False):
        #xstage_return_time = 0.1
        lst = []
        #if (do_clear):
        #    lst.append('WCL %d' % tblid)
        # start, stop, step, npoints, dwell, do_clear=False, tbl_id=1)
        step = round(step, 3)
        if (use_fit_function):
            step_time = self.get_fitted_step_time(step, dwell, line=False)
            self.pnt_step_time = step_time
        else:
            step_time = self.pnt_step_time

        updown_time = self.pnt_updown_time
        sit_time = dwell
        segtime = dwell
        #only allow a minnimum segtime (the time waiting at location for dwell) to be a certain value and no lower
        #if(segtime < 0.005):
        #    segtime = 0.005

        # lst.append(self.define_seg_by_time(xline_time, 0.00, 0.0, y_roi[STEP], _new=True, tblid=tblid))
        # define_seg_by_time(self, seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1)
        lst.append(self.define_seg_by_time(self.pnt_start_delay, updown_time, 0.0, start, _new=True, tblid=tblid))

        #lst.append(self.define_seg_by_time(step_time, updown_time, step, start, _new=True, tblid=tblid))
        lst.append(self.define_seg_by_time(step_time, updown_time, step, start, _new=False, tblid=tblid))

        lst.append(self.define_seg_by_time(segtime, 0.00, 0.00, start + step, _new=False, tblid=tblid))
        for i in range(1, npoints):
            # define_seg_by_time(seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1):
            lst.append(self.define_seg_by_time(step_time, updown_time, step, start + (i * step), _new=False, tblid=tblid))
            lst.append(self.define_seg_by_time(segtime, 0.00, 0.00, start + (i * step) + step, _new=False, tblid=tblid))


        #replace the last point with one that is twice the length in time
        #lst.append(self.define_seg_by_time(segtime, 0.00, 0.00, start + (i * step) + step, _new=False, tblid=tblid))
        #lst.append(self.define_seg_by_time(100*segtime, 10*segtime, 0.00, -0.5*(start + (i * step) + step), _new=False, tblid=tblid))
        #lst.append( self.define_seg_by_time(10 * segtime, 10 * segtime, -1.0 * (start + (i * step) + step), start + (i * step) + step, _new=False, tblid=tblid))

        lst.append(self.define_seg_by_time(0.005, 0.00, 0.00, start + (i * step) + step, _new=False, tblid=tblid))
        #lst.append(self.define_seg_by_time(self.xstage_return_time, segtime, -1.0 * (start + (i * step) + step),    start + (i * step) + step, _new=False, tblid=tblid))
        lst.append(self.define_seg_by_time(self.line_return_time, segtime, -1.0 * (start + (i * step) + step),
                                           start + (i * step) + step, _new=False, tblid=tblid))
        if(not is_y):
            self.hline_in_points = (npoints * (step_time + segtime ) + self.xstage_return_time) / WAVEFORM_GEN_CYCLE_TIME

        # WAV 1 X LIN 6400 8 -1.5 6400 0 1200
        # WAV 1 & LIN 1200 -8 6.5 1200 0 400
        if (send):
            self.send_list(lst)
        return (lst)

    # def gen_x_line_wav_strs(self, start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
    #     """
    #     """
    #
    #
    #     l = []
    #     if (start < stop):
    #         rng = abs(float(start - stop))
    #     else:
    #         rng = abs(float(stop - start))
    #
    #     linetime = (npoints * (dwell * 0.001)) + self.line_step_time
    #     speedupdown_npnts = self.pnts_per_seg(self.line_step_time + self.line_updown_time)
    #     seglen_npts = self.pnts_per_seg(linetime + WIDTH_DISTORTION_FUDGE)
    #     amp = rng + (2.0 * self.line_accrange)
    #     return_npts = self.pnts_per_seg(self.line_return_time)
    #     offset = start - self.line_accrange
    #
    #     # l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, start, _new=True, tblid=tbl_id))
    #     #fits the flat line at begining of X waveform
    #     l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, start - self.line_accrange,  _new=True, tblid=tbl_id))
    #
    #     #next the waveform that has the accel, constant velo and deccel to end of range
    #     l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=False))
    #
    #     #lastly the return waveform to the start
    #     l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts, wavtype='LIN', _new=False))
    #
    #     self.line_accrange
    #
    #     #l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
    #     #l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts,  wavtype='LIN', _new=False))
    #
    #     return (l)


    # def gen_x_line_wav_strs(self, start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
    #     """
    #
    #     """
    #     l = []
    #     if (start < stop):
    #         rng = abs(float(start - stop))
    #     else:
    #         rng = abs(float(stop - start))
    #
    #     # desired velo for only the scanned line, use this to calc the acc range and decc range
    #     v = float(rng / float((npoints * (dwell * 0.001))))
    #     self.line_accrange = v * (self.line_step_time * 2.0)
    #     decc_range = v * (self.line_updown_time) #+ self.line_accrange
    #     amp = self.line_accrange + rng + decc_range
    #
    #     # the time of entire length of line including speed up and slow down (hence * 2.0)
    #     # linetime = (constant velo time) + (self.line_step_time * 2.0)
    #     #linetime = (npoints * (dwell * 0.001)) + (self.line_step_time + self.line_updown_time)
    #     linetime = (npoints * (dwell * 0.001))
    #
    #     speedupdown_npnts = self.pnts_per_seg(self.line_updown_time)
    #     # seglen_npts = self.pnts_per_seg(linetime + WIDTH_DISTORTION_FUDGE)
    #
    #     self.return_npts = self.pnts_per_seg(self.line_return_time)
    #     wavlen_npts = self.pnts_per_seg(self.line_step_time * 2) + self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time)
    #     #seglen is the length of entire line from start to stop
    #     seglen_npts = self.pnts_per_seg(linetime) + + self.pnts_per_seg(self.line_step_time) + self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(self.line_start_delay)
    #
    #     # set the start of the scan to include acceleration range
    #     # offset = start - self.line_accrange
    #     offset = 0.0
    #
    #     # l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, start, _new=True, tblid=tbl_id))
    #     # fits the flat line at begining of X waveform
    #     # define_seg_by_time( segment time, speedupdown time, step size, offset, _new, table id)
    #     #l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, offset, _new=True, tblid=tbl_id))
    #     #reduce line start delay by 25ms so that its rampup
    #     l.append(
    #         self.define_seg_by_time(self.line_start_delay , 0.0, 0.0, offset, _new=True, tblid=tbl_id))
    #
    #     # next the waveform that has the accel, constant velo and deccel to end of range
    #     # gen_wav_table_strs(table id, segment length in points, amplitude, offset, wave length in points, starting point number, speedupdown npoints, wav type)
    #     print 'amp=%.2f' % amp
    #     #l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp , offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=False))
    #     l.append(
    #         self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN',
    #                                 _new=False))
    #
    #     # lastly the return waveform to the start
    #     l.append(self.gen_wav_table_strs(tbl_id, self.return_npts, -1.0 * amp, amp + offset, self.return_npts, 0, self.return_npts,
    #                                      wavtype='LIN', _new=False))
    #
    #     # l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
    #     # l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts,  wavtype='LIN', _new=False))
    #
    #     # self.hline_in_points = ((npoints * segtime) + step_time + self.line_return_time) / WAVEFORM_GEN_CYCLE_TIME
    #     self.hline_in_points = seglen_npts + self.return_npts + self.pnts_per_seg(self.line_start_delay)
    #
    #     return (l)

    def calc_acc_dist(self, amp, speedupdwn, seg_time):
        '''
            seg_time=180e-3
            speed_up_down=15e-3
            amplitude=32e-6
            acc_dist=amplitude*speed_up_down/(2*(seg_time-speed_up_down))
            print(acc_dist)
            1.4545454545454546e-06
            => the plot in the PI software showed 1.45um (which I guess is rounded)

            curve_lengts=150e-3
            speed_up_down=5e-3
            amplitude=32e-6
            acc_dist=amplitude*speed_up_down/(2*(curve_lengts-speed_up_down))
            print(acc_dist)
            5.517241379310345e-07

        :param amp:
        :param speedupdwn:
        :param seg_time:
        :return:
        '''
        #amp = amp + (2 * desired_acc_rng)
        if(seg_time == speedupdwn):
            acc_dist = amp * speedupdwn / (2 * speedupdwn)
        else:
            acc_dist = amp * speedupdwn / (2 * (seg_time - speedupdwn))
        print('calc_acc_dist: %.4f' % acc_dist)
        return (acc_dist)

    def gen_x_line_wav_strs(self, start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
        """

        """
        l = []
        if (start < stop):
            rng = abs(float(start - stop))
        else:
            rng = abs(float(stop - start))

        linetime = (npoints * (dwell * 0.001))
        self.line_accrange = self.calc_acc_dist(rng, self.line_updown_time, linetime)
        amp = rng + (2.0 * self.line_accrange)
        speedupdown_npnts = self.pnts_per_seg(self.line_updown_time)
        self.return_npts = self.pnts_per_seg(self.line_return_time)

        #wavlen_npts = self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(self.line_updown_time)
        wavlen_npts = self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time)# + self.pnts_per_seg(self.line_updown_time)
        #seglen is the length of entire line from start to stop
        seglen_npts = wavlen_npts

        offset = 0.0

        # fits the flat line at begining of X waveform
        # define_seg_by_time( segment time, speedupdown time, step size, offset, _new, table id)
        #l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, offset, _new=True, tblid=tbl_id))
        l.append(
            self.define_seg_by_time(self.line_start_delay , 0.0, 0.0, offset, _new=True, tblid=tbl_id))

        # next the waveform that has the accel, constant velo and deccel to end of range
        # gen_wav_table_strs(table id, segment length in points, amplitude, offset, wave length in points, starting point number, speedupdown npoints, wav type)
        print('amp=%.2f' % amp)
        #l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp , offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=False))
        l.append(
            self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN',
                                    _new=False))

        # lastly the return waveform to the start
        l.append(self.gen_wav_table_strs(tbl_id, self.return_npts, -1.0 * amp, amp + offset, self.return_npts, 0, self.return_npts,
                                         wavtype='LIN', _new=False))

        # l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
        # l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts,  wavtype='LIN', _new=False))

        # self.hline_in_points = ((npoints * segtime) + step_time + self.line_return_time) / WAVEFORM_GEN_CYCLE_TIME
        self.hline_in_points = seglen_npts + self.return_npts + self.pnts_per_seg(self.line_start_delay)

        return (l)

    # def gen_x_line_wav_strs(self, start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
    #     """
    #   used this before sept 18 2018, where I think teh velocity ends up not being correct
    #     """
    #     l = []
    #     if (start < stop):
    #         rng = abs(float(start - stop))
    #     else:
    #         rng = abs(float(stop - start))
    #
    #     # desired velo for only the scanned line, use this to calc the acc range and decc range
    #     v = float(rng / float((npoints * (dwell * 0.001))))
    #     self.line_accrange = decc_range = v * (self.line_updown_time)
    #     #amplitude of entire scan line
    #     amp = self.line_accrange + rng + decc_range
    #
    #     linetime = (npoints * (dwell * 0.001))
    #
    #     speedupdown_npnts = self.pnts_per_seg(self.line_updown_time)
    #
    #     self.return_npts = self.pnts_per_seg(self.line_return_time)
    #
    #     #wavlen_npts = self.pnts_per_seg(self.line_step_time * 2) + self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time)
    #     wavlen_npts = self.pnts_per_seg(self.line_start_delay) + self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time)
    #     #seglen is the length of entire line from start to stop
    #     seglen_npts = self.pnts_per_seg(linetime) + self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(self.line_updown_time) + self.pnts_per_seg(self.line_start_delay)
    #
    #     offset = 0.0
    #
    #     # fits the flat line at begining of X waveform
    #     # define_seg_by_time( segment time, speedupdown time, step size, offset, _new, table id)
    #     #l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, offset, _new=True, tblid=tbl_id))
    #     l.append(
    #         self.define_seg_by_time(self.line_start_delay , 0.0, 0.0, offset, _new=True, tblid=tbl_id))
    #
    #     # next the waveform that has the accel, constant velo and deccel to end of range
    #     # gen_wav_table_strs(table id, segment length in points, amplitude, offset, wave length in points, starting point number, speedupdown npoints, wav type)
    #     print 'amp=%.2f' % amp
    #     #l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp , offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=False))
    #     l.append(
    #         self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN',
    #                                 _new=False))
    #
    #     # lastly the return waveform to the start
    #     l.append(self.gen_wav_table_strs(tbl_id, self.return_npts, -1.0 * amp, amp + offset, self.return_npts, 0, self.return_npts,
    #                                      wavtype='LIN', _new=False))
    #
    #     # l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
    #     # l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts,  wavtype='LIN', _new=False))
    #
    #     # self.hline_in_points = ((npoints * segtime) + step_time + self.line_return_time) / WAVEFORM_GEN_CYCLE_TIME
    #     self.hline_in_points = seglen_npts + self.return_npts + self.pnts_per_seg(self.line_start_delay)
    #
    #     return (l)

    # def gen_x_line_wav_strs(self, start, stop, step, npoints, dwell, do_clear=False, tbl_id=1):
    #     """
    #
    #     """
    #     l = []
    #     if (start < stop):
    #         rng = abs(float(start - stop))
    #     else:
    #         rng = abs(float(stop - start))
    #
    #
    #     # the time of entire length of line including speed up and slow down (hence * 2.0)
    #     # linetime = (constant velo time) + (self.line_step_time * 2.0)
    #     linetime = (npoints * (dwell * 0.001)) + (self.line_step_time + self.line_updown_time)
    #
    #     speedupdown_npnts = self.pnts_per_seg(self.line_step_time + self.line_updown_time)
    #     #seglen_npts = self.pnts_per_seg(linetime + WIDTH_DISTORTION_FUDGE)
    #
    #     #seglen_npts = self.pnts_per_seg(linetime + WIDTH_DISTORTION_FUDGE)
    #     seglen_npts = wavlen_npts = self.pnts_per_seg(linetime) + speedupdown_npnts
    #
    #     amp = rng + (2.0 * self.line_accrange)
    #     return_npts = self.pnts_per_seg(self.line_return_time)
    #
    #     #set the start of the scan to include acceleration range
    #     #offset = start - self.line_accrange
    #     offset = 0.0
    #
    #     # l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, start, _new=True, tblid=tbl_id))
    #     #fits the flat line at begining of X waveform
    #     # define_seg_by_time( segment time, speedupdown time, step size, offset, _new, table id)
    #     l.append(self.define_seg_by_time(self.line_start_delay, self.line_updown_time, 0.0, offset,  _new=True, tblid=tbl_id))
    #
    #     #next the waveform that has the accel, constant velo and deccel to end of range
    #     # gen_wav_table_strs(table id, segment length in points, amplitude, offset, wave length in points, starting point number, speedupdown npoints, wav type)
    #     l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, wavlen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=False))
    #
    #     #lastly the return waveform to the start
    #     l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts, wavtype='LIN', _new=False))
    #
    #     #l.append(self.gen_wav_table_strs(tbl_id, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN', _new=True))
    #     #l.append(self.gen_wav_table_strs(tbl_id, return_npts, -1.0 * amp, amp + offset, return_npts, 0, return_npts,  wavtype='LIN', _new=False))
    #
    #     #self.hline_in_points = ((npoints * segtime) + step_time + self.line_return_time) / WAVEFORM_GEN_CYCLE_TIME
    #     self.hline_in_points =  seglen_npts + return_npts
    #
    #     return (l)

    def gen_y_line_wav_strs(self, start, stop, step, step_time, sit_time, do_clear=False, tbl_id=2):
        """
        """
        l = []
        # reset the y offset to 0.0
        #self.sock_send(gen_set_wavetable_offset_cmnd(tbl_id, 0.0), do_rcv=False)
        #self.send_command_string(gen_set_wavetable_offset_cmnd(tbl_id, 0.0))
        # speedup/slowdown time
        #xlinetime_points = self.get_wav_tbl_length(X_WAVE_TABLE_ID)

        xlinetime_points = self.hline_in_points
        segtime = PNT_TIME_RES * xlinetime_points
        # segtime = step_time + sit_time



        # define_seg_by_time(seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1)
        if(self.is_pxp):
            l.append(self.define_seg_by_time(self.pnt_step_time, self.pnt_updown_time, step, 0.0, _new=True, tblid=tbl_id))
            l.append(self.define_seg_by_time(segtime, self.pnt_updown_time, 0.00, step, _new=False, tblid=tbl_id))
        else:

            #l.append(self.define_seg_by_time(self.line_step_time, self.line_updown_time, step, 0.0, _new=True, tblid=tbl_id))
            #l.append(self.define_seg_by_time(segtime, self.line_updown_time, 0.00, step, _new=False, tblid=tbl_id))

            l.append(self.define_seg_by_time(self.line_step_time, self.line_updown_time, step, 0.0, _new=True, tblid=tbl_id))
            l.append(self.define_seg_by_time(segtime + self.line_start_delay, self.line_updown_time, 0.00, step, _new=False, tblid=tbl_id))

        return (l)

    def send_list(self, lst):

        #for l in lst:
        #    self.sock_send(l, do_rcv=False)
        #    self.check_for_error()

        #for l in lst:
        #    self.send_command_string(l + ';')
        cmnd_string = ";".join(lst) + ';'
        self.send_command_string(cmnd_string)
        #time.sleep(0.15)

    def define_seg_by_time(self, seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1):
        seglen_npts = self.pnts_per_seg(seg_time)
        speedupdown_npnts = self.pnts_per_seg(speedupdown_time)
        amp = step_size
        s = self.gen_wav_table_strs(tblid, seglen_npts, amp, offset, seglen_npts, 0, speedupdown_npnts, wavtype='LIN',
                                    _new=_new)
        return (s)

    def gen_wav_table_strs(self, tblid, seglen_npts, amp, offset, wavlen, startpoint, speedupdown_npts, wavtype='LIN',
                           _new=False):
        '''
        WAV <TableID> <AppendWave> <WaveType> <SegLength> <Amp> <Offset> <Wavelength> <Startpoint> <Speedupdown>
        <TableID>: integer betwen 1 and 120
        <AppendWave>:   'X' clears the table and starts with 1st point
                        '&' appends to the existing table
        <WaveType>: 'PNT' user defined curve
                    'SIN_P' inverted cosine curve
                    'RAMP' ramp curve
                    'LIN' single scan line curve
        <SegLength>: the length of the wave table segment in points, only the number of points
                    given by seglen will be written to the wave table
        <Amp>:     The amplitude of the scan in EGU
        <Offset>:  the offset of the scan line in EGU
        <Wavelength>: the length of the single scan line in curve points
        <Startpoint>: the index of the starting point of the scan line in the segment.
                        lowest possible value is 0
        <Speedupdown>: the number of points for speed up and slow down


        NOTE: for SIN_P, RAMP and LIN wave types: if the SegLen values is larger than the WaveLength value, the missing points in hte segment
            are filled with the endpoint value
            - # 200 points == 10ms
        '''
        if (_new):
            append_wv = 'X'
        else:
            append_wv = '&'
        s = 'WAV %d %s %s %d %.3f %.3f %d %d %d' % (
            tblid, append_wv, wavtype, seglen_npts, amp, offset, wavlen, startpoint, speedupdown_npts)
        #print(s)
        return (s)

    def pnts_per_seg(self, linetime):
        '''
        2 points = 0.1ms
        20 points == 1ms
        200 points == 10ms


        100ms == 2000 pts
        pnts = (linetime / 0.010) * 200
        '''
        pnts = int((linetime / 0.010) * 200)
        return (pnts)

    def get_npoints_from_ms(self, ms):
        return (ms * 20)

    def line_time(self, rng, dwell, num_points):
        # linetime = rng * (dwell * num_points * 0.001)
        linetime = (dwell * num_points * 0.001)
        return (linetime)

    def xline_time(self, npoints):
        '''
        calc the number of points (in time) it will take for the x pxp to do 1 line
        :param npoints:
        :return:
        '''
        # return(self.pnts_per_seg(0.15 * float(npoints)))
        return (self.pnts_per_seg(float(npoints)))

    def scan_velo(self, rng, linetime):

        if(rng is 0.0):
            velo = 10000
        else:
            velo = rng / linetime
        return (velo)

    def accel_time(self, accRange, velo):
        acctime = accRange / velo
        return (acctime)

    def gen_trigger_string(self, output_id):
        '''
        CTO <TrigOutId> <CTOPam> <Value>
        CTOPam:
            1 = TriggerStep
            2 = Axis
            3 = TriggerMode
            5 = MinThreshold
            6 = MaxThreshold

            TriggerModes:
                0 = Position Distance
                2 = OnTarget
                3 = MonMax Threshold
                4 = Generator Trigger

        :param output_id:
        :return:
        '''
        l = []
        #axis
        l.append('CTO %d 2 %d' % (output_id, X_AXIS_ID))
        #TriggerMode
        l.append('CTO %d 3 %d' % (output_id, X_AXIS_ID, E712_TRIG_MODES.GENERATOR))
        return(l)


    def gen_pxp_line_trig_str(self, dwell, npoints, accRange, velo, is_pxp=True, send=True, step_time=0.005,
                              updown_time=0.005):
        '''
        1 ms == 20 points, so if the line is made of of n points with a dwell of m ms then I should be
        able to calc the point for each point on the line
        using the TWS command
            TWS <TrigOutputId> <point number> <switch hi/low>

        trig_lst = gen_pxp_line_trig_str(dwell, 1, accRange, scanvelo)

        '''
        cmnds = []
        output_id = 1
        pts_per_dwell = dwell * 20
        dwell_ms = dwell * 0.001
        nums = []
        #acctime = self.accel_time(accRange, velo)
        if (is_pxp):
            speedupdown_pnt = self.pnts_per_seg(step_time)
        else:
            speedupdown_pnt = self.pnts_per_seg(step_time)
            npoints = 1

        l = []
        l.append('TWC')
        l.append('CTO %d 3 %d' % (output_id, E712_TRIG_MODES.GENERATOR))
        #l.append('CTO %d %d %d' % (output_id, X_AXIS_ID, E712_TRIG_MODES.GENERATOR))
        #l.append(self.gen_trigger_string(output_id))
        if (is_pxp):
            # make the first point
            step_time = step_time
            #pnt_num = self.pnts_per_seg(step_time) + 2

            #l.append('TWS %d %d 1' % (output_id, pnt_num))
            #nums.append(1)

            #need an extra trigger point here to account for the requirement of each point being hte delta between it and the next point
            for i in range(0, npoints + 1):

                #pnt_num = self.pnts_per_seg(float(i) * (step_time + dwell_ms) + step_time) + 2
                pnt_num = self.pnts_per_seg(float(i) * (step_time + dwell_ms) + step_time + self.pnt_start_delay) + 2

                l.append('TWS %d %d 1' % (output_id, pnt_num))
                nums.append(1)
                for j in range(int(pts_per_dwell)):
                    l.append('TWS %d %d 1' % (output_id, pnt_num + j))
                    nums.append(1)

                #make sure the trigger is turned off
                #l.append('TWS %d %d 0' % (output_id, pnt_num + j + 1))

                if(len(l) > 500):
                    cmnds.append(copy.copy(l))
                    l = []

            cmnds.append(copy.copy(l))

        else:
            pnt_num = self.pnts_per_seg(step_time)
            #pnt_num = self.pnts_per_seg(step_time + self.line_step_time)

            l.append('TWS %d %d 1' % (output_id, pnt_num))
            #for j in range(int(pts_per_dwell)):
            for j in range(10):
                l.append('TWS %d %d 1' % (output_id, pnt_num + j))

            # make sure the trigger is turned off
            l.append('TWS %d %d 0' % (output_id, pnt_num + j + 1))

            cmnds.append(copy.copy(l))
        # now set the trigger mode to Generator Trigger
        nums_d = np.array(nums)
        #print 'last trig occurs at %.2f sec' % (pnt_num * WAVEFORM_GEN_CYCLE_TIME)
        #print 'num_trigs sent = %d' % (nums_d.sum()/20)

        if (send):
            for lst in cmnds:
                self.send_list(lst)

        return (l)

    # def gen_pxp_line_trig_str(self, dwell, npoints, accRange, velo, is_pxp=True, send=True, step_time=0.04,
    #                           updown_time=0.005):
    #     '''
    #     1 ms == 20 points, so if the line is made of of n points with a dwell of m ms then I should be
    #     able to calc the point for each point on the line
    #     using the TWS command
    #         TWS <TrigOutputId> <point number> <switch hi/low>
    #
    #     trig_lst = gen_pxp_line_trig_str(dwell, 1, accRange, scanvelo)
    #
    #     '''
    #     cmnds = []
    #     output_id = 1
    #     pts_per_dwell = dwell * 20
    #     dwell_ms = dwell * 0.001
    #     nums = []
    #     acctime = self.accel_time(accRange, velo)
    #     if (is_pxp):
    #         speedupdown_pnt = self.pnts_per_seg(step_time)
    #     else:
    #         speedupdown_pnt = self.pnts_per_seg(step_time)
    #         npoints = 1
    #
    #     l = []
    #     l.append('TWC')
    #     l.append('CTO %d 3 %d' % (output_id, E712_TRIG_MODES.GENERATOR))
    #     #l.append('CTO %d %d %d' % (output_id, X_AXIS_ID, E712_TRIG_MODES.GENERATOR))
    #     #l.append(self.gen_trigger_string(output_id))
    #     if (is_pxp):
    #         # make the first point
    #         step_time = step_time
    #         #pnt_num = self.pnts_per_seg(step_time) + 2
    #
    #         #l.append('TWS %d %d 1' % (output_id, pnt_num))
    #         #nums.append(1)
    #
    #         #need an extra trigger point here to account for the requirement of each point being hte delta between it and the next point
    #         for i in range(0, npoints + 1):
    #
    #             #pnt_num = self.pnts_per_seg(float(i) * (step_time + dwell_ms) + step_time) + 2
    #             pnt_num = self.pnts_per_seg(float(i) * (step_time + dwell_ms) + step_time + self.pnt_start_delay) + 2
    #
    #             l.append('TWS %d %d 1' % (output_id, pnt_num))
    #             nums.append(1)
    #             for j in range(int(pts_per_dwell)):
    #                 l.append('TWS %d %d 1' % (output_id, pnt_num + j))
    #                 nums.append(1)
    #
    #             #make sure the trigger is turned off
    #             #l.append('TWS %d %d 0' % (output_id, pnt_num + j + 1))
    #
    #             if(len(l) > 500):
    #                 cmnds.append(copy.copy(l))
    #                 l = []
    #
    #         cmnds.append(copy.copy(l))
    #
    #     else:
    #         pnt_num = self.pnts_per_seg(step_time)
    #         #pnt_num = self.pnts_per_seg(step_time + self.line_step_time)
    #
    #         l.append('TWS %d %d 1' % (output_id, pnt_num))
    #         #for j in range(int(pts_per_dwell)):
    #         for j in range(10):
    #             l.append('TWS %d %d 1' % (output_id, pnt_num + j))
    #
    #         # make sure the trigger is turned off
    #         l.append('TWS %d %d 0' % (output_id, pnt_num + j + 1))
    #
    #         cmnds.append(copy.copy(l))
    #     # now set the trigger mode to Generator Trigger
    #     nums_d = np.array(nums)
    #     #print 'last trig occurs at %.2f sec' % (pnt_num * WAVEFORM_GEN_CYCLE_TIME)
    #     #print 'num_trigs sent = %d' % (nums_d.sum()/20)
    #
    #     if (send):
    #         for lst in cmnds:
    #             self.send_list(lst)
    #
    #     return (l)

    # def get_fitted_step_time(self, step_size, dwell, line=False):
    #     '''
    #     fit function from Jan June 20 2017
    #     :param step_size:
    #     :param dwell:
    #     :return step time in seconds:
    #     '''
    #     dwell = dwell * 1000.0
    #     if(line):
    #         a = 1.894
    #         b = 0.6173
    #         c = -0.562
    #         step_time = a * math.exp(b * step_size + c * dwell)
    #     else:
    #
    #         a = 1.894
    #         b = 0.6173
    #         c = -0.562
    #         step_time = a * math.exp(b * step_size + c * dwell)
    #
    #     return(step_time * 0.001)

    def get_fitted_step_time(self, step_size, dwell, line=False):
        dwell = dwell * 1000.0
        if (line):
            a = 1.922
            b = 0.4946
            c = -0.3447
            d = -0.4096
            e = 0.1268
        else:
            a = 1.922
            b = 0.4946
            c = -0.3447
            d = -0.4096
            e = 0.1268

        step_time = a * math.exp(b * (step_size - c) + d * (dwell - e))
        step_time = 3.0
        return (step_time * 0.001)

    def do_point_by_point(self, dwell, x_roi, y_roi, y_is_pxp=False, x_tbl_id=None, y_tbl_id=None, forced_rate=None):
        '''
        WAV 3 X LIN 2000 0.25 0 2000 0 400
        WAV 3 & LIN 1000 0 0.25 1000 0 0
        WAV 3 & LIN 2000 0.25 0.25 2000 0 400
        WAV 3 & LIN 1000 0 0.5 1000 0 0

        :return:
        '''
        #move the piezo's to their start position
        #s = 'MOV %d %.3f;MOV %d %.3f;' % (X_WAVE_TABLE_ID, x_roi[START], Y_WAVE_TABLE_ID, y_roi[START])
        #self.send_command_string(s)


        NUM_FOR_EDIFF = 0
        scan_velo = 9000000.0
        #dwell = e_roi[DWELL]
        xdwell = dwell * 0.001

        if(x_tbl_id is None):
            x_tbl_id = X_WAVE_TABLE_ID
        if(y_tbl_id is None):
            y_tbl_id = Y_WAVE_TABLE_ID

        # recalc the wave table rate and set it here before doing anything else
        new_rate = calc_optimal_wavetable_rate(x_roi[NPOINTS], xdwell, forced_rate=forced_rate)
        self.set_wave_table_rate(new_rate)
        # create one complete line assuming starting from 0 and stepping up by one step, the actual starting offset is handled elsewhere

        #xpoints = self.define_pxp_segments(0.0, x_roi[STEP], x_roi[NPOINTS] + NUM_FOR_EDIFF, xdwell, send=True, tblid=3, do_clear=True)
        #xpoints = self.define_pxp_segments(0.0, x_roi[STEP], int(x_roi[NPOINTS]) + NUM_FOR_EDIFF, xdwell, send=False,
        #                                   tblid=X_WAVE_TABLE_ID, do_clear=True, use_fit_function=True)
        xpoints = self.define_pxp_segments(0.0, x_roi[STEP], int(x_roi[NPOINTS]) + NUM_FOR_EDIFF, xdwell,
                                           send=False, tblid=x_tbl_id, do_clear=True, use_fit_function=False)

        self.send_list(xpoints)

        step_time = self.pnt_step_time
        updown_time = self.pnt_updown_time

        time.sleep(0.25)


        #xlinetime_points = self.get_wav_tbl_length(X_WAVE_TABLE_ID)
        #print 'self.hline_in_points=%d' % self.hline_in_points
        xline_time = PNT_TIME_RES * self.hline_in_points + self.pnt_start_delay

        ypoints = []
        if(y_is_pxp):
            #we are most likely doing a LineSpec arbitrary line scan so Y waveform must be a set of stairs like X
            ypoints = self.define_pxp_segments(0.0, y_roi[STEP], int(y_roi[NPOINTS]) + NUM_FOR_EDIFF, xdwell,
                                     send=False, tblid=Y_WAVE_TABLE_ID, do_clear=True, use_fit_function=False, is_y=y_is_pxp)


        else:
            # create one complete line assuming starting from 0 and stepping up by one step, the actual starting offset is handled elsewhere
            #time.sleep(1.0)
            # def define_seg_by_time(self, seg_time, speedupdown_time, step_size, offset, _new=True, tblid=1)
            #ypoints.append(self.define_seg_by_time(step_time, updown_time, y_roi[STEP], 0.0, _new=True, tblid=Y_WAVE_TABLE_ID))
            ypoints.append(self.define_seg_by_time(step_time, updown_time, y_roi[STEP], 0.0, _new=True, tblid=Y_WAVE_TABLE_ID))
            ypoints.append(self.define_seg_by_time(xline_time, 0.00, 0.0, y_roi[STEP], _new=False, tblid=Y_WAVE_TABLE_ID))

        self.send_list(ypoints)

        time.sleep(0.25)
        #all_points = xpoints
        #all_points += ypoints
        #self.send_list(all_points)

        #trig_lst = self.gen_pxp_line_trig_str(dwell, x_roi[NPOINTS] + NUM_FOR_EDIFF, 0.0, scan_velo, is_pxp=True, send=True,
        #                                      step_time=self.pnt_step_time, updown_time=self.pnt_updown_time)
        trig_lst = self.gen_pxp_line_trig_str(dwell, int(x_roi[NPOINTS]) + NUM_FOR_EDIFF, 0.0, scan_velo, is_pxp=True,
                                              send=True, step_time=self.pnt_step_time, updown_time=self.pnt_updown_time)

        self.calc_new_estemate(y_roi[NPOINTS])

    def validate_line_return_time(self):
        '''
        want to check the current setting for line return time and make sure that it is:
            - no less than the minnimum of  40ms
            - if greater than 40ms it is to be set to 2 * dwell + 40ms
                the reason for the 2 * is because the current scalar requires 2 extra points per line so that the
                pixel values 9 hte delta between two adjacent points) is calculated correctlty)
        :return:
        '''

        dwell = self.dwell * 0.001 #in ms
        #self.line_return_time = float(self.returnTimeFld.text())
        dwell_and_return = float(2.0 * dwell) + MIN_LINE_RETURN_TIME
        if(self.line_return_time < dwell_and_return):
            self.line_return_time = dwell_and_return
        #else:
        #    self.line_return_time = MIN_LINE_RETURN_TIME

        #self.returnTimeFld.setText(str('%.3f' % self.line_return_time))


    def do_line_by_line(self, dwell, x_roi, y_roi, x_tbl_id, y_tbl_id):
        #reset wave table rate
        self.set_wave_table_rate(1)
        #check line return time to make sure it is adequate
        self.validate_line_return_time()

        #only move to start if in GONI_ZONEPLATE mode because the x_roi coordinates are full range of fine stage only
        #COARSE_ZONEPLATE mode coordinates are absolute interferometer so x_roi range is +/- 7000 um
        if(scan_mode == types.scanning_mode.GONI_ZONEPLATE):
            #move the piezo's to their start position
            s = 'MOV %d %.3f;MOV %d %.3f;' % (X_AXIS_ID, x_roi[START], Y_AXIS_ID, y_roi[START])
            self.send_command_string(s)

        # define_x_segments(start, stop, npoints, dwell, x_tbl_id, send=True, use_fit_function=False):
        #xlines = self.define_x_segments(x_roi[START], x_roi[STOP], x_roi[NPOINTS], e_roi[DWELL], send=True)
        xlines = self.define_x_segments(0.0, x_roi[RANGE], x_roi[NPOINTS], dwell, x_tbl_id, send=True)

        # define_y_segments(start, stop, npoints, dwell, y_tbl_id, send=True)
        ylines = self.define_y_segments(y_roi[START], y_roi[STOP], y_roi[NPOINTS], dwell, y_tbl_id, send=True)

        xlinetime_points = self.hline_in_points

        if(xlinetime_points is 0):
            print('oops, the X wave didnt take for some reason, bailing')
            return

        #xline_time = PNT_TIME_RES * xlinetime_points

        # scanvelo = self.scan_velo(x_roi[RANGE], float((x_roi[NPOINTS] * (dwell * 0.001))))
        #
        # #trig_lst = self.gen_pxp_line_trig_str(e_roi[DWELL], 1, self.line_accrange, scanvelo, step_time=self.line_trig_time, is_pxp=False)
        # trig_start_time =  (self.line_updown_time) + self.line_start_delay
        # #trig_start_time = trig_start_time * 1.2
        # #trig_start_time = trig_start_time * 1.094
        # #1.094 = 218.812 / 200um/s
        # trig_scale =  218.812  / float(scanvelo)
        # trig_start_time = trig_start_time * trig_scale
        # #trig_lst = self.gen_pxp_line_trig_str(dwell, 1, self.line_accrange, scanvelo, step_time=self.line_step_time,is_pxp=False)

        self.trig_start_time = self.line_updown_time + self.line_start_delay
        #IGNORE accrange var as it is not used FIX THIS
        trig_lst = self.gen_pxp_line_trig_str(dwell, 1, self.line_updown_time, 0.0, step_time=self.trig_start_time,
                                              is_pxp=False)

        lines = xlines + ylines + trig_lst
        self.calc_new_estemate(y_roi[NPOINTS])
        return(lines)



class E712ControlWidget(QtWidgets.QWidget):
    '''

    classdocs

    '''

    changed = QtCore.pyqtSignal(object)
    upd_plot = QtCore.pyqtSignal()
    wvgen_stopped = QtCore.pyqtSignal()

    def __init__(self, prefix='IOCE712:', gate=None, counter=None, e712_com=None, show_plot=False, automated_data_dir=r'S:\STXM-data\Cryo-STXM\2018\guest\automated_data_dir'):
        super(E712ControlWidget, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e712_wavegen_compact.ui'), self)
        from cls.data_io.stxm_data_io import STXMDataIo

        self.prefix = prefix
        self.show_plot = show_plot
        # self.cntr = BaseCounter('uhvCI:counter')
        # self.gate = BaseGate('uhvCO:gate')
        self.cntr = counter
        self.gate = gate

        if((self.cntr is None) or (self.gate is None)):
            _logger.error('Counter and/or Gate device not specified')
            raise E712Exception('Counter and/or Gate device not specified')
            exit()

        self.curve_plot = CurveViewerWidget(toolbar=True)
        self.ddl_curve_plot = CurveViewerWidget(toolbar=True)
        self.image_plot = make_default_stand_alone_stxm_imagewidget()

        settings_dct = make_dflt_settings_dct()
        self.ss = SaveSettings('e712.ini', dct_template=settings_dct)

        self.forced_rate = None
        self.running_automated = False
        self.cur_job = None
        self.cur_job_idx = 0
        self.automated_data_dir = automated_data_dir
        self.scan_ok_to_exec = True
        self.e712_cmnd_queue = queue.Queue()
        self.e712_com = E712ComThread(self.prefix, self.e712_cmnd_queue, xaxis_id=X_AXIS_ID, yaxis_id=Y_AXIS_ID)
        self.e712_com.start()

        self.e712 = PI_E712(prefix=self.prefix, e712com=self.e712_com, e712comQ=self.e712_cmnd_queue)

        self.datarecorder = None
        if(DATARECORDER_ENABLED):
            self.datarecorder = PI_E712_DataRecorder(x_tbl_id=X_AXIS_ID, y_tbl_id=Y_AXIS_ID, prefix=self.prefix, parent=self)
            drlayout = QtWidgets.QVBoxLayout()
            drlayout.addWidget(self.datarecorder)
            self.datarecorderFrame.setLayout(drlayout)
            self.datarecorder.set_filepath(r'S:\STXM-data\Cryo-STXM\2018\guest\0724\000.hdf5')

        self.prev_data = None

        self.e712.elapsed_time_chgd.connect(self.on_elapsed_time_changed)
        self.e712.estimated_time_chgd.connect(self.on_estimated_time_changed)
        self.e712.table_data_changed.connect(self.on_new_table_data)

        self.e712.wvgen_status.connect(self.on_wavgen_status)
        # self.e712.wg1.status_rbv.add_callback(self.on_wgStatus, lbl=self.wvgen1StsLbl, wvgen=1)
        # self.e712.wg2.status_rbv.add_callback(self.on_wgStatus, lbl=self.wvgen2StsLbl, wvgen=2)
        # self.e712.wg3.status_rbv.add_callback(self.on_wgStatus, lbl=self.wvgen3StsLbl, wvgen=3)
        # self.e712.wg4.status_rbv.add_callback(self.on_wgStatus, lbl=self.wvgen4StsLbl, wvgen=4)
        self.e712.wg1.status_rbv.changed.connect(lambda: self.on_wgStatus(lbl=self.wvgen1StsLbl, wvgen=1))
        self.e712.wg2.status_rbv.changed.connect(lambda: self.on_wgStatus(lbl=self.wvgen2StsLbl, wvgen=2))
        self.e712.wg3.status_rbv.changed.connect(lambda: self.on_wgStatus(lbl=self.wvgen3StsLbl, wvgen=3))
        self.e712.wg4.status_rbv.changed.connect(lambda: self.on_wgStatus(lbl=self.wvgen4StsLbl, wvgen=4))

        #this needs to be fixed so its not hard coded
        print('e712.py: 1675: !!!!!!!!!!!!! this needs to be fixed so its not hard coded !!!!!!!!!!!!!!!!!!!!!')
        self.xmtr = e712_sample_motor('IOC:m102', name='IOC:m102')
        self.ymtr = e712_sample_motor('IOC:m103', name='IOC:m103')
        #############################################

        self.data_q = queue.Queue()
        self.job_q = queue.Queue()

        self.curve_plot.regTools()
        self.curve_plot.add_legend("TL")
        self.curve_plot.set_dataIO(STXMDataIo)

        self.data = None
        self.numX = 0
        self.numY = 0
        self.x_roi = None
        self.y_roi = None
        self.e_roi = None
        self.plotter_busy = False
        self.x_scan_reset_pos = 0.0


        self.wavgen_table_map = {}

        self.x_use_ddl = False
        self.x_use_reinit_ddl = False
        self.x_start_end_pos = False
        self.x_force_reinit = False
        self.x_auto_ddl = False

        self.max_jobs_in_q = 0
        self.loopProgBar.setValue(0)

        self.stop_loop = False
        self.is_pxp = True
        self.start_msg = ''
        self.curve_plot.clear_plot()
        self.ddl_curve_plot.clear_plot()
        # self.curve_plot.create_curve('WaveTbl_%d' % X_WAVE_TABLE_ID, curve_style=None)
        # self.curve_plot.create_curve('WaveTbl_%d' % Y_WAVE_TABLE_ID, curve_style=None)

        self.sts_lbls = [self.wvgen1StsLbl, self.wvgen2StsLbl, self.wvgen3StsLbl, self.wvgen4StsLbl]
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.curve_plot)
        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.addWidget(self.ddl_curve_plot)
        self.plotFrame.setLayout(vbox)
        self.ddlPlotFrame.setLayout(vbox2)
        self.loadDDLTableBtn.clicked.connect(self.on_load_ddl_table_btn)
        self.sendWvBtn.clicked.connect(self.on_send_wave_btn)
        self.startBtn.clicked.connect(self.on_start_btn)
        self.stopBtn.clicked.connect(self.on_stop_wavegen)
        self.loadWaveDataBtn.clicked.connect(self.on_load)
        self.loadAllWavesDataBtn.clicked.connect(self.on_load_all_tables)
        self.upd_plot.connect(self.update_plot_data)
        self.modeComboBox.currentIndexChanged.connect(self.on_mode_changed)

        self.xUseDDLRadBtn.clicked.connect(self.on_x_useradbtn)
        self.autoDDLRadBtn.clicked.connect(self.on_auto_ddl_btn)
        self.xForceReinitRadBtn.clicked.connect(self.on_force_learning_btn)

        self.getDDLTableBtn.clicked.connect(self.on_get_ddl_table_btn)

        self.startLoopBtn.clicked.connect(self.on_start_loop)
        self.stopLoopBtn.clicked.connect(self.on_stop_loop)


        #self.modeComboBox.currentIndexChanged.connect(self.on_mode_changed)


        self.calcProcParmsBtn.clicked.connect(self.on_calc_the_processing_params_btn)
        self.startTimer = QtCore.QTimer()
        self.startTimer.setSingleShot(True)
        self.startTimer.timeout.connect(self.on_start)

        #self.usePIWvGenRadBtn.clicked.connect(self.on_use_pi_wvgen_clicked)

        #self.plotTimer = QtCore.QTimer()
        #self.plotTimer.timeout.connect(self.update_plot_data)

        self.data = None

        # self.stsTimer.start(250)
        if(self.show_plot):
            #self.plotTimer.start(0.350)
            self.image_plot.show()

        self.reload_settings()
        self.idx = 0

    def set_forced_rate(self, rate=None):
        '''
        this param if set to a None positive integer it will force the wave table rate to use this value
        instead of auto calculating the optimal wave table rate, this was added so that for the pattern generator
        scans all of the pattern pads will use a specified wave table rate
        :param rate:
        :return:
        '''
        if(rate is not None):
            if(rate < 1):
                rate = 1
        self.forced_rate = rate
        self.e712.set_wave_table_rate(rate)

    def set_automated_filepath(self, fpath):
        self.automated_data_dir = fpath

    def get_x_axis_id(self):
        return (self.e712.get_x_axis_id())

    def get_y_axis_id(self):
        return (self.e712.get_y_axis_id())

    def break_list_into_chunks(self, l, n):
        return ([l[i:i + n] for i in range(0, len(l), n)])


    def create_wavgen_usetable_map(self, sp_ids, single_sp_roi=False):
        '''
        taking a list of sp_ids create a list of ascending integers starting at 1 up to 120 then break that list
        into a list of lists that are in inner lists of 4 (one integer for each waveform generator)

        return the list
        :param sp_ids:
        :return self.wavgen_table_map:
        '''
        #clear current map
        self.wavgen_table_map = {}

        if(single_sp_roi):
            #likely a tomo which is each angle of a single spatial_roi is treated as its own sp_id
            tbl_ids = [[1,2,3,4]]*len(sp_ids)
        else:
            tbl_ids = self.break_list_into_chunks(list(range(1,120,1)), 4)
        #for each sp_id assign a set of tables to use
        for i in range(len(sp_ids)):
            #create a mapping between sp_id and a set of 4 table numbers
            self.wavgen_table_map[sp_ids[i]] = tbl_ids[i]

        return(self.wavgen_table_map)



    def set_axis_wg_usetbl_num(self, axis=-1, num=-1):
            self.e712.set_axis_wg_usetbl_num(axis=axis, num=num)

    def get_new_time_estemate(self):
        s = self.e712.calc_new_estemate(self.y_roi[NPOINTS])
        return(s)

    def get_new_time_in_seconds(self, nptsY):
        '''
        calculate the new time in seconds that the scan will take, then add a percentage of that time onto itself
        so that it is more accurate, this time is then used to figure out how many data recorder points are needed
        in order to capture the entire scan
        :param nptsY:
        :return:
        '''
        _sec = self.e712.calc_new_estemate(nptsY, in_seconds=True)
        _sec += (_sec * 0.18)
        return(_sec)

    def calc_hline_time(self, dwell, npoints, pxp=True):
        #first make sure that the calc will use the current tuning params
        dct = self.get_tuning_params()
        self.e712.init_tuning_params(dct)
        #now calc new horizontal line time
        hlt = self.e712.calc_hline_time(dwell, npoints, pxp=pxp)
        return(hlt)

    def get_ddl_table(self, tblid, cb=None):
        '''
        This is so that we can expose getting the ddl table at a higher level
        :param tblid:
        :param cb:
        :return:
        '''
        self.e712.get_ddl_table(tblid,cb=cb)

    def store_ddl_table(self, key, data, dct=None):
        '''
        This is so that we can expose setting the ddl table at a higher level
        :param key:
        :param data:
        :param dct:
        :return:
        '''
        self.e712.store_ddl_table(key, data, dct=dct)

    def on_check_if_ddl_is_in_database(self):
        dct = self.get_tuning_params()
        ddl_table_key = gen_ddl_database_key(dct)
        if (self.e712.ddl_db.key_exists(ddl_table_key)):
            return(True)
        else:
            return(False)

    def on_auto_ddl_btn(self):
        #self.uncheck_xddl_flags()
        self.x_use_ddl = False
        self.x_use_reinit_ddl = False
        self.x_start_end_pos = False
        self.x_force_reinit = False
        self.x_auto_ddl = True

    def save_this_ddl(self):
        #this is a function called by teh parent to see if the scan that was just run requires that teh DDL be saved or not
        # the ddl flags will have been set when the scan was run so just determine the status from them
        # if(DATARECORDER_ENABLED):
        #     #the DDL and Datarecorder are mutually exclusive, so if DATA recorder is enabled tell the caller NO to getting and saving DDL
        #     return(False)
        if(self.x_use_reinit_ddl or self.x_force_reinit):
            return(True)
        else:
            return(False)

    def on_force_learning_btn(self):
        self.set_xddl_flags_for_force_learning()


    def on_load_ddl_table_btn(self):
        fname = getOpenFileName("Get Filename", filter_str="Json Files (*.json)", search_path=r'S:\STXM-data\Cryo-STXM\2017\e712Testing')
        if(fname is not None):
            dct = loadJson(fname)
            ddl_data = np.array(dct['xddl_tbl'])
            self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)

    def set_mode(self, mode):
        if(mode is (0 or 1)):
            self.modeComboBox.setCurrentIndex(mode)
        #else:
        #    _logger.error('Invalid mode [%d]' % mode)


    def get_loop_ranges(self):
        dct = {}
        dct['mode'] = self.modeComboBox.currentIndex()
        dct['num_interp_points'] = int(self.numInterpFld.text())

        dct['dwell_start'] = float(self.dwellStartTimeFld.text())
        dct['dwell_stop'] = float(self.dwellStopTimeFld.text())
        dct['dwell_points'] = np.linspace(dct['dwell_start'], dct['dwell_stop'], dct['num_interp_points'])


        dct['pnt_start_delay'] = float(self.pntStartDelayFld_2.text())
        dct['pnt_stop_delay'] = float(self.pntStopDelayFld.text())
        dct['pnt_delay_points'] = np.linspace(dct['pnt_start_delay'], dct['pnt_stop_delay'], dct['num_interp_points'])

        dct['pnt_step_start'] = float(self.pntStepStartTimeFld.text())
        dct['pnt_step_stop'] = float(self.pntStepStopTimeFld.text())
        dct['pnt_step_points'] = np.linspace(dct['pnt_step_start'], dct['pnt_step_stop'], dct['num_interp_points'])

        dct['pnt_speed_start'] = float(self.pntSpeedStartTimeFld.text())
        dct['pnt_speed_stop'] = float(self.pntSpeedStopTimeFld.text())
        dct['pnt_speed_points'] = np.linspace(dct['pnt_speed_start'], dct['pnt_speed_stop'], dct['num_interp_points'])

        dct['line_step_start'] = float(self.lineStepStartTimeFld.text())
        dct['line_step_stop'] = float(self.lineStepStopTimeFld.text())
        dct['line_step_points'] = np.linspace(dct['line_step_start'], dct['line_step_stop'], dct['num_interp_points'])

        dct['line_speed_start'] = float(self.lineSpeedStartTimeFld.text())
        dct['line_speed_stop'] = float(self.lineSpeedStopTimeFld.text())
        dct['line_speed_points'] = np.linspace(dct['line_speed_start'], dct['line_speed_stop'], dct['num_interp_points'])

        dct['line_return_start'] = float(self.lineReturnStartTimeFld.text())
        dct['line_return_stop'] = float(self.lineReturnStopTimeFld.text())
        dct['line_return_points'] = np.linspace(dct['line_return_start'], dct['line_return_stop'], dct['num_interp_points'])

        dct['line_accR_start'] = float(self.lineAccRStartFld.text())
        dct['line_accR_stop'] = float(self.lineAccRStopFld.text())
        dct['line_accR_points'] = np.linspace(dct['line_accR_start'], dct['line_accR_stop'], dct['num_interp_points'])

        return(dct)



    def load_tune_settings(self, dct):
        self.dwellFld.setText(str(self.ss.get('dwell')))
        self.maxRcvBytesFld.setText(str(self.ss.get('max_rcv_bytes')))
        self.maxSockTimeoutFld.setText(str(self.ss.get('max_sock_timeout')))
        self.lineAccRangeFld.setText(str(self.ss.get('line_accrange')))
        self.pntStartDelayFld.setText(str(self.ss.get('pnt_start_delay')))
        self.pntStepTimeFld.setText(str(self.ss.get('pnt_step_time')))
        self.pntUpDownTimeFld.setText(str(self.ss.get('pnt_updown_time')))

        self.lineStartDelayFld.setText(str(self.ss.get('line_start_delay')))
        self.lineStepTimeFld.setText(str(self.ss.get('line_step_time')))
        self.lineUpDownTimeFld.setText(str(self.ss.get('line_updown_time')))
        self.returnTimeFld.setText(str(self.ss.get('line_return_time')))
        #self.lineTrigTimeFld.setText(str(self.ss.get('line_trig_time')))
        self.xstartFld.setText(str(self.ss.get('startX')))
        self.xstopFld.setText(str(self.ss.get('stopX')))
        self.xnpointsFld.setText(str(self.ss.get('numX')))

        self.ystartFld.setText(str(self.ss.get('startY')))
        self.ystopFld.setText(str(self.ss.get('stopY')))
        self.ynpointsFld.setText(str(self.ss.get('numY')))

    def on_stop_loop(self):
        self.running_automated = False
        self.stop_loop = True
        self.on_stop_wavegen()
        self.wvgen_stopped.emit()



    def on_start_loop(self):
        '''
        - get scan type (lxl or pxp)
        - get range of params for scan type
        - loop over first param
            - loop over second param
                - create a job dict that contains all info to be able to run a scan
                - write it to the queue
        - connect wavegen done signal to call sef.exec_scan
        -now that queue is full call self.exec_scan
        
        
        
         dct['mode'] = self.modeComboBox.currentIndex()
        dct['num_interp_points'] = int(self.numInterpFld.text())

        dct['dwell_start'] = float(self.dwellStartTimeFld.text())
        dct['dwell_stop'] = float(self.dwellStopTimeFld.text())
        dct['dwell_points'] = np.linspace(dct['dwell_start'], dct['dwell_stop'], dct['num_interp_points'])

        dct['pnt_step_start'] = float(self.pntStepStartTimeFld.text())
        dct['pnt_step_stop'] = float(self.pntStepStopTimeFld.text())
        dct['pnt_step_points'] = np.linspace(dct['pnt_step_start'], dct['pnt_step_stop'], dct['num_interp_points'])

        dct['pnt_speed_start'] = float(self.pntSpeedStartTimeFld.text())
        dct['pnt_speed_stop'] = float(self.pntSpeedStopTimeFld.text())
        dct['pnt_speed_points'] = np.linspace(dct['pnt_speed_start'], dct['pnt_speed_stop'], dct['num_interp_points'])

        dct['line_step_start'] = float(self.lineStepStartTimeFld.text())
        dct['line_step_stop'] = float(self.lineStepStopTimeFld.text())
        dct['line_step_points'] = np.linspace(dct['line_step_start'], dct['line_step_stop'], dct['num_interp_points'])

        dct['line_speed_start'] = float(self.lineSpeedStartTimeFld.text())
        dct['line_speed_stop'] = float(self.lineSpeedStopTimeFld.text())
        dct['line_speed_points'] = np.linspace(dct['line_speed_start'], dct['line_speed_stop'], dct['num_interp_points'])

        dct['line_return_start'] = float(self.lineReturnStartTimeFld.text())
        dct['line_return_stop'] = float(self.lineReturnStopTimeFld.text())
        dct['line_return_points'] = np.linspace(dct['line_return_start'], dct['line_return_stop'], dct['num_interp_points'])

        dct['line_accR_start'] = float(self.lineAccRStartFld.text())
        dct['line_accR_stop'] = float(self.lineAccRStopFld.text())
        dct['line_accR_points'] = np.linspace(dct['line_accR_start'], dct['line_accR_stop'], dct['num_interp_points'])


        :return: 
        '''
        self.running_automated = True
        if(self.datarecorder):
            self.datarecorder.push_all_selections()
            self.datarecorder.set_filename('000.dat')

        self.cur_job_idx = -1
        self.stop_loop = False
        loop_dct = self.get_loop_ranges()

        if(loop_dct['mode'] is 0):
            #pxp
            self.fill_pnt_scan_loop_queue(loop_dct)
            self.wvgen_stopped.connect(self.exec_scan)
            #self.wvgen_stopped.connect(self.datarecorder.dr_get_rec_tbls)
            #self.datarecorder.dr_status.connect(self.on_datarecorder_status)

        else:
            #lxl
            self.fill_line_scan_loop_queue(loop_dct)
            # self.wvgen_stopped.connect(self.exec_scan)
            #self.wvgen_stopped.connect(self.datarecorder.dr_get_rec_tbls)
            #self.datarecorder.dr_status.connect(self.on_datarecorder_status)
            if(self.datarecorder):
                reconnect_signal(self, self.wvgen_stopped, self.datarecorder.on_get_rec_tbls_btn)
                reconnect_signal(self.datarecorder, self.datarecorder.dr_status, self.on_datarecorder_status)

        self.exec_scan()


    def on_datarecorder_status(self, dr_sts_dct):
        if(dr_sts_dct['busy']):
            #datarecorder is saving the data
            print('on_datarecorder_status: BUSY')
        else:
            #its done so launch next one
            print('on_datarecorder_status: Calling exec_scan()')
            self.exec_scan()





    # def fill_pnt_scan_loop_queue(self, loop_dct):
    #     '''
    #     :param dct:
    #     :return:
    #     '''
    #
    #     jobs = 0
    #     for npt in range(25,300, loop_dct['num_interp_points']):
    #         for x in range(-25,25, npt):
    #             for y in range(-45, 5, npt):
    #                 for m in loop_dct['dwell_points']:
    #                     for i in loop_dct['pnt_step_points']:
    #                         dct = self.get_tuning_params()
    #                         #no modify only the ones that we want to loop on
    #                         dct['dwell'] = m
    #                         dct['pnt_step_time'] = i
    #                         dct['npoints'] = npt
    #                         dct['startX'] = -1.0 * x
    #                         dct['stopX'] = x
    #                         dct['startY'] = -1.0 * y
    #                         dct['stopY'] = y
    #                         #shove it into the queue
    #                         self.job_q.put_nowait(dct)
    #                         jobs += 1
    #
    #     self.max_jobs_in_q = jobs
    #     self.loopProgBar.setMaximum(jobs)

    def fill_pnt_scan_loop_queue(self, loop_dct):
        '''
        :param dct: 
        :return: 
        '''

        jobs_dct = {}
        jobs = 0
        for npt in range(50,250, loop_dct['num_interp_points']):
            for m in loop_dct['dwell_points']:
                for j in loop_dct['pnt_delay_points']:
                    for i in loop_dct['pnt_step_points']:
                        dct = self.get_tuning_params()
                        #no modify only the ones that we want to loop on
                        dct['dwell'] = m
                        dct['pnt_step_time'] = i
                        dct['pnt_start_delay_time'] = j
                        dct['npoints'] = npt
                        #dct['startX'] = -20.0
                        dct['startX'] = -15.0
                        dct['stopX'] = 15.0
                        #dct['startY'] = -45.0
                        dct['startY'] = -15.0
                        #dct['stopY'] = 5.0
                        dct['stopY'] = 15.0
                        #shove it into the queue
                        self.job_q.put_nowait(dct)
                        jobs_dct[jobs] = dct
                        jobs += 1

        self.max_jobs_in_q = jobs
        self.loopProgBar.setMaximum(jobs)

        # save the dct to disk for analysis
        jobs_str = dict_to_json(jobs_dct)
        json_to_file(os.path.join(self.automated_data_dir, 'jobs.json'), jobs_str)

    def fill_line_scan_loop_queue(self, loop_dct):
        '''
            
        :param dct: 
        :return: 
        '''

        # self.loopProgBar.setMaximum(6*20*20*10*10*10)
        # jobs = 0
        # for npt in range(50,300, 50):
        #     for x in range(25,500, npt):
        #         for y in range(25, 500, npt):
        #             for m in loop_dct['dwell_points']:
        #                 for i in loop_dct['line_step_points']:
        #                     for l in loop_dct['line_accR_points']:
        #                         dct = self.get_tuning_params()
        #                         # no modify only the ones that we want to loop on
        #                         dct['npoints'] = npt
        #                         dct['startX'] = -1.0 * x
        #                         dct['stopX'] = x
        #                         dct['startY'] = -1.0 * y
        #                         dct['stopY'] = y
        #                         dct['dwell'] = m
        #                         dct['line_step_time'] = i
        #                         #dct['line_updown_time'] = j
        #                         dct['line_accrange'] = l
        #                         # shove it into the queue
        #                         self.job_q.put_nowait(dct)
        #                         jobs += 1
        #                         self.loopProgBar.setValue(jobs)
        #
        # self.max_jobs_in_q = jobs
        # self.loopProgBar.setMaximum(jobs)
        if(self.datarecorder):
            fpath = self.datarecorder.get_filepath()
        self.set_automated_filepath(fpath)
        jobs_dct = {}
        self.loopProgBar.setMaximum(10 * 9 * loop_dct['num_interp_points'] )
        jobs = 0
        for npt in range(50, 500, 50):
            for xy in range(1, 45, npt):
                for m in loop_dct['dwell_points']:
                    dct = self.get_tuning_params()
                    # no modify only the ones that we want to loop on
                    dct['npoints'] = npt
                    # dct['startX'] = -15.0
                    # dct['stopX'] = 15.0
                    # dct['startY'] = -15.0
                    # dct['stopY'] = 15.0
                    dct['startX'] = -1.0 * xy
                    dct['stopX'] = xy
                    dct['startY'] = -1.0 * xy
                    dct['stopY'] = xy
                    dct['dwell'] = m
                    # shove it into the queue
                    self.job_q.put_nowait(dct)
                    jobs_dct[jobs] = dct
                    jobs += 1
                    self.loopProgBar.setValue(jobs)

                QtWidgets.QApplication.processEvents()

        self.max_jobs_in_q = jobs
        self.loopProgBar.setMaximum(jobs)

        #save the dct to disk for analysis
        jobs_str = dict_to_json(jobs_dct)
        json_to_file(os.path.join(self.automated_data_dir, 'jobs.json'), jobs_str)


    def exec_scan(self):
        '''
        - pull a dict from the job queue
        - get scan type
        - push params to fields for scan type
        - call startBtn
        
        :return: 
        '''

        dct = None
        done = False
        if(self.stop_loop):
            self.job_q.queue.clear()
            return

        if not self.job_q.empty():
            dct = self.job_q.get()
            self.cur_job = dct

            if(self.datarecorder):
                self.datarecorder.push_all_selections()
                fpath = self.datarecorder.get_filepath()
            # save previous
            if (self.image_plot.data is not None):
                #array_to_jpg(os.path.join(self.automated_data_dir, '%03d.jpg' % self.cur_job_idx), self.image_plot.get_data(flip=True))
                array_to_jpg(os.path.join(fpath, '%03d.jpg' % self.cur_job_idx), self.image_plot.get_data(flip=True))

            if(dct['mode'] is 0):
                self.do_pnt_loop_scan(dct)
            else:
                self.do_line_loop_scan(dct)

            self.cur_job_idx += 1
            if (self.datarecorder):
                self.datarecorder.push_all_selections()
                self.datarecorder.set_filename('%03d.dat' % self.cur_job_idx)
            #update loop progress bar
            self.update_loop_progress()
            done = True

        if (done):
            self.job_q.task_done()

    def do_pnt_loop_scan(self, dct):
        self.e712.init_tuning_params(dct)
        self.load_tuning_settings(dct)
        self.on_send_wave_btn()
        self.on_start_wavegen()

    def do_line_loop_scan(self, dct):

        self.e712.init_tuning_params(dct)
        self.load_tuning_settings(dct, line=True)
        #set DDL flags to learn
        self.set_xddl_flags_for_learning()
        self.on_send_wave_btn()
        self.on_start_wavegen()


    def uncheck_xddl_flags(self):
        self.autoDDLRadBtn.setChecked(False)
        #self.xUseDDLRadBtn.setChecked(False)
        #self.xUseReinitDDLRadBtn.setChecked(False)
        #self.xStartEndPosRadBtn.setChecked(False)
        #self.xForceReinitRadBtn.setChecked(False)
        self.x_use_ddl = False
        self.x_use_reinit_ddl = False
        self.x_start_end_pos = False
        self.x_force_reinit = False
        self.x_auto_ddl = False

    def set_xddl_flags_for_auto(self):
        #self.autoDDLRadBtn.setChecked(False)
        #self.xUseDDLRadBtn.setChecked(False)
        #self.xUseReinitDDLRadBtn.setChecked(False)
        #self.xStartEndPosRadBtn.setChecked(False)
        #self.xForceReinitRadBtn.setChecked(True)
        self.x_use_ddl = False
        self.x_use_reinit_ddl = False
        self.x_start_end_pos = False
        self.x_force_reinit = False
        self.x_auto_ddl = True

    def set_xddl_flags_for_force_learning(self):
        #self.autoDDLRadBtn.setChecked(False)
        #self.xUseDDLRadBtn.setChecked(False)
        #self.xUseReinitDDLRadBtn.setChecked(False)
        #self.xStartEndPosRadBtn.setChecked(False)
        #self.xForceReinitRadBtn.setChecked(True)
        self.x_use_ddl = False
        self.x_use_reinit_ddl = True
        self.x_start_end_pos = False
        self.x_force_reinit = True
        self.x_auto_ddl = False

    def set_xddl_flags_for_learning(self):
        #self.autoDDLRadBtn.setChecked(False)
        #self.xUseDDLRadBtn.setChecked(False)
        #self.xUseReinitDDLRadBtn.setChecked(True)
        #self.xStartEndPosRadBtn.setChecked(False)
        #self.xForceReinitRadBtn.setChecked(False)
        self.x_use_ddl = False
        self.x_use_reinit_ddl = True
        self.x_start_end_pos = False
        self.x_force_reinit = False


    def set_xddl_flags_for_using(self):
        #self.xUseDDLRadBtn.setChecked(True)
        #self.xUseReinitDDLRadBtn.setChecked(False)
        #self.xStartEndPosRadBtn.setChecked(False)
        #self.xForceReinitRadBtn.setChecked(False)
        self.x_use_ddl = True
        self.x_use_reinit_ddl = False
        self.x_start_end_pos = False
        self.x_force_reinit = False


    def on_x_useradbtn(self, is_checked):
        self.x_use_ddl = is_checked
        if(is_checked):
            self.e712.calc_ddl_parameters()


    def update_loop_progress(self):
        num_in_q = self.job_q.qsize()
        self.loopProgBar.setValue(self.max_jobs_in_q - int(num_in_q))


    def on_mode_changed(self, idx):
        if(idx == 0):
            #pxp
            self.uncheck_xddl_flags()
            #self.xUseDDLRadBtn.setChecked(False)
            #self.xUseReinitDDLRadBtn.setChecked(False)
            #self.xStartEndPosRadBtn.setChecked(False)
            #self.xForceReinitRadBtn.setChecked(False)
        else:
            #lxl
            pass

    def on_new_table_data(self, e712com_dct):
        cb = e712com_dct['cb']
        if(cb is not None):
            cb(e712com_dct)

    def on_elapsed_time_changed(self, t_str):
        self.elapsedTimeLbl.setText(t_str)

    def on_estimated_time_changed(self, t_str):
        self.estimatedTimeLbl.setText(t_str)

    def on_wavgen_status(self, val):
        if(val == 0):
            if(self.show_plot):
                #only do the following if we are running the wavegenerator on its own
                #self.upd_plot.emit()
                self.update_plot_data()
                self.on_stop_wavegen()
                self.wvgen_stopped.emit()

                #print self.image_plot.data.shape
                #self.cntr.stop()
                #self.gate.stop()



    def on_get_ddl_table_btn(self):
        tblid = self.ddlTblSpinBox.value()
        #ddl_data = self.e712.get_ddl_table(tblid)
        #self.plot_ddl_data(ddl_data)

        self.ddl_curve_plot.clear_plot()
        self.e712.get_ddl_table(tblid, cb=self.plot_ddl_data)

    def on_mod_ddl_table_btn(self):
        tblid = self.ddlTblSpinBox.value()
        ddl_data = self.e712.get_ddl_table(tblid)
        ddl_data[10] = -99.999
        self.e712.put_ddl_table(tblid, ddl_data)


    # def on_wgStatus(self, **kwargs):
    #     #print kwargs
    #     lbl = kwargs['lbl']
    #     if(kwargs['value'] is 0):
    #         lbl.setText('STOPPED')
    #         if(kwargs['wvgen'] is 4):
    #             self.update_plot_data()
    #     else:
    #         lbl.setText('RUNNING')

    def on_wgStatus(self, lbl, wvgen):
        if(wvgen is 0):
            lbl.setText('STOPPED')
            if(wvgen is 4):
                self.update_plot_data()
        else:
            lbl.setText('RUNNING')

    def add_data_to_q(self, dct):
        #print 'add_data_to_q', dct[CNTR2PLOT_VAL]
        row = dct[CNTR2PLOT_ROW]
        #point = dct[CNTR2PLOT_COL]
        data = dct[CNTR2PLOT_VAL]
        self.data[row] = data
        self.data_q.put_nowait(dct)
        # if(self.idx >= (self.numY / 3)):
        #     print 'emitting upd_plot'
        #     self.upd_plot.emit()
        #     self.idx = 0
        #
        # self.idx += 1


    def reload_settings(self):
        self.dwellFld.setText(str(self.ss.get('dwell')))
        self.maxRcvBytesFld.setText(str(self.ss.get('max_rcv_bytes')))
        self.maxSockTimeoutFld.setText(str(self.ss.get('max_sock_timeout')))
        self.lineAccRangeFld.setText(str(self.ss.get('line_accrange')))
        self.pntStartDelayFld.setText(str(self.ss.get('pnt_start_delay')))
        self.pntStepTimeFld.setText(str(self.ss.get('pnt_step_time')))
        self.pntUpDownTimeFld.setText(str(self.ss.get('pnt_updown_time')))

        self.lineStartDelayFld.setText(str(self.ss.get('line_start_delay')))
        self.lineStepTimeFld.setText(str(self.ss.get('line_step_time')))
        self.lineUpDownTimeFld.setText(str(self.ss.get('line_updown_time')))
        self.returnTimeFld.setText(str(self.ss.get('line_return_time')))
        #self.lineTrigTimeFld.setText(str(self.ss.get('line_trig_time')))
        self.xstartFld.setText(str(self.ss.get('startX')))
        self.xstopFld.setText(str(self.ss.get('stopX')))
        self.xnpointsFld.setText(str(self.ss.get('numX')))

        self.ystartFld.setText(str(self.ss.get('startY')))
        self.ystopFld.setText(str(self.ss.get('stopY')))
        self.ynpointsFld.setText(str(self.ss.get('numY')))


    def load_tuning_settings(self, dct, line=False):
        self.dwellFld.setText(str('%.3f' % dct['dwell']))
        self.lineAccRangeFld.setText(str('%.3f' % dct['line_accrange']))
        self.pntStartDelayFld.setText(str('%.3f' % dct['pnt_start_delay']))
        self.pntStepTimeFld.setText(str('%.3f' % dct['pnt_step_time']))
        self.pntUpDownTimeFld.setText(str('%.3f' % dct['pnt_updown_time']))
        self.lineStepTimeFld.setText(str('%.3f' % dct['line_step_time']))
        self.lineUpDownTimeFld.setText(str('%.3f' % dct['line_updown_time']))
        self.returnTimeFld.setText(str('%.3f' % dct['line_return_time']))

        self.xstartFld.setText(str(dct['startX']))
        self.xstopFld.setText(str(dct['stopX']))
        self.xnpointsFld.setText(str('%d' % dct['npoints']))

        self.ystartFld.setText(str(dct['startY']))
        self.ystopFld.setText(str(dct['stopY']))
        if(line):
            # iterations of y are only to refine the DDL table so only need a max of 50
            self.ynpointsFld.setText(str('%d' % 50))
        else:
            self.ynpointsFld.setText(str('%d' % dct['npoints']))

        print('dwell: %.3f' % dct['dwell'])
        print('line_accrange: %.3f' % dct['line_accrange'])
        print('line_step_time: %.3f' % dct['line_step_time'])
        print('pnt_start_delay: %.3f' % dct['pnt_start_delay'])
        print('pnt_step_time: %.3f' % dct['pnt_step_time'])
        print('pnt_updown_time: %.3f' % dct['pnt_updown_time'])
        print('line_return_time: %.3f' % dct['line_return_time'])

        print('npoints: %.3f' % dct['npoints'])
        print('startX: %.3f' % dct['startX'])
        print('stopY: %.3f' % dct['stopY'])
        print('startY: %.3f' % dct['startY'])
        print('stopY: %.3f' % dct['stopY'])



    def on_use_pi_wvgen_clicked(self, chkd):
        if(chkd):
            self.is_pxp = False
            self.config_devices(is_pxp=False)

            print('connecting counter to plotter')
            self.reset_image_plot()
            mode = self.modeComboBox.currentIndex()
            self.numX = int(self.xnpointsFld.text())
            self.numY = int(self.ynpointsFld.text())
            startX = float(self.xstartFld.text())
            stopX = float(self.xstopFld.text())
            startY = float(self.ystartFld.text())
            stopY = float(self.ystopFld.text())
            rect = (startX, startY, stopX, stopY)
            self.data = np.ones((self.numY, self.numX))
            # self.image_plot.initData(types.image_types.IMAGE, self.numY, self.numX, {'RECT': rect})

            self.image_plot.set_data(self.data)
            self.image_plot.set_autoscale(fill_plot_window=False)

            self.gate.start()
            self.cntr.start()
            self.cntr.changed.connect(self.on_sample_scan_counter_changed)
            self.changed.connect(self.add_line_to_plot)
        else:
            print('disconnecting counter to plotter')
            self.gate.stop()
            self.cntr.stop()
            self.cntr.changed.disconnect(self.on_sample_scan_counter_changed)
            self.changed.disconnect(self.add_line_to_plot)


    def reset_image_plot(self):
        self.image_plot.delImagePlotItems()
        self.image_plot.delShapePlotItems()
        self.image_plot.set_auto_contrast(True)

    def init_counter_to_plotter_com_dct(self, dct):
        dct[CNTR2PLOT_TYPE_ID] = types.image_types.IMAGE
        dct[CNTR2PLOT_IMG_CNTR] = 0
        dct[CNTR2PLOT_EV_CNTR] = 0
        dct[CNTR2PLOT_SP_ID] = 0
        dct[CNTR2PLOT_IS_POINT] = self.is_pxp
        dct[CNTR2PLOT_IS_LINE] = not (self.is_pxp)
        return (dct)

    def on_sample_scan_counter_changed(self, row, data):
        """
        on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN

        :param row: row description
        :type row: row type

        :param data: data description
        :type data: data type

        :returns: None
        """
        """
        The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
        The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
        The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
        slot during a point scan will receive a point+1 and in that case it should be ignored.

        LIne scan data arrives in the form data[row, < number of x points of values >]

        This slot has to handle

        """
        nptsy = self.numY
        _evidx = 0
        point = 0
        val = data[0:int(self.numX)]

        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(point)
        dct[CNTR2PLOT_VAL] = val
        # self.sigs.changed.emit(row, data)
        self.changed.emit(dct)

    def update_plot_data(self):
        if(self.plotter_busy):
            return
        self.plotter_busy = True
        resp = None
        done = False
        while not self.data_q.empty():
            resp = self.data_q.get()
            self.add_line_to_plot(resp, True)
            done = True

        if(done):
            self.image_plot.plot.replot()
            self.data_q.task_done()
        self.plotter_busy = False

    def add_line_to_plot(self, counter_to_plotter_com_dct, update=True):
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        line_data = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        self.image_plot.addLine(0, row, line_data, update)

    # def add_point_to_plot(self, row, tpl):

    def add_point_to_plot(self, counter_to_plotter_com_dct):
        row = counter_to_plotter_com_dct[CNTR2PLOT_ROW]
        col = point = counter_to_plotter_com_dct[CNTR2PLOT_COL]
        val = counter_to_plotter_com_dct[CNTR2PLOT_VAL]
        img_cntr = counter_to_plotter_com_dct[CNTR2PLOT_IMG_CNTR]
        ev_cntr = counter_to_plotter_com_dct[CNTR2PLOT_EV_CNTR]
        # print 'add_point_to_plot: row=%d, point=%d, val=%d' % (row, point, val)
        self.image_plot.addPoint(row, point, val, True)

    def on_calc_the_processing_params_btn(self):
        # ensure that the DDL params have been calculated
        self.e712.calc_ddl_params.put(X_WAVE_TABLE_ID)


    def on_load_all_tables(self):
        self.curve_plot.clear_plot()
        self.e712.get_all_wav_table(cb=self.plot_all_data)


    def on_load(self):
        self.curve_plot.clear_plot()
        tblid = self.wavTblSpinBox.value()
        self.e712.get_wav_table(tblid, cb=self.plot_data)


    def on_sts_fbk(self):
        stslst = self.e712.get_wavgen_sts()
        x = 0
        for sts in stslst:
            sts_lbl = self.sts_lbls[x]
            if (sts):
                sts_lbl.setText('RUNNING')
            else:
                sts_lbl.setText('STOPPED')
            x += 1
    def config_devices(self, is_pxp=True):
        xnpoints = int(self.xnpointsFld.text())
        dwell = float(self.dwellFld.text())
        self.cntr.stop()
        self.gate.stop()
        if (is_pxp):
            # set_devices_for_e712_wavegen_point_scan(dwell, numX, gate, counter, shutter=None)
            set_devices_for_e712_wavegen_point_scan(types.scan_types.SAMPLE_IMAGE, dwell, xnpoints, self.cntr)
        else:
            # set_devices_for_e712_wavegen_point_scan(dwell, numX, gate, counter, shutter=None)
            set_devices_for_e712_wavegen_line_scan(dwell, xnpoints, self.gate, self.cntr)

    def set_xAutoRadBtn(self, chkd):
        if(chkd):
            self.set_xAutoRadBtn.setChecked(True)
            self.x



    def set_ddl_flag_vals(self, axis='x'):
        val = 0
        if (axis is 'x'):
            if (X_AXIS_ID is 1):
                x_wg = self.e712.wg1
            else:
                x_wg = self.e712.wg3

            if (self.x_use_ddl):
                #val += E712_WVGEN_FLAGS.USE
                x_wg.use_ddl.put(1)
            else:
                x_wg.use_ddl.put(0)

            if (self.x_use_reinit_ddl):
                #val += E712_WVGEN_FLAGS.USE_AND_REINIT
                #self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                x_wg.clear_ddltable()
                x_wg.use_reinit_ddl.put(1)
            else:
                x_wg.use_reinit_ddl.put(0)

            if (self.xStartEndPosRadBtn.isChecked()):
                #val += E712_WVGEN_FLAGS.START_AT_ENDPOS
                x_wg.start_at_end_pos.put(1)
            else:
                x_wg.start_at_end_pos.put(0)

        elif (axis is 'y'):
            if (Y_AXIS_ID is 2):
                y_wg = self.e712.wg2
            else:
                y_wg = self.e712.wg4

            if (self.yUseDDLRadBtn.isChecked()):
                #val += E712_WVGEN_FLAGS.USE
                y_wg.use_ddl.put(1)
            else:
                y_wg.use_ddl.put(0)

            if (self.yUseReinitDDLRadBtn.isChecked()):
                #val += E712_WVGEN_FLAGS.USE_AND_REINIT
                y_wg.clear_ddltable()
                y_wg.use_reinit_ddl.put(1)
            else:
                y_wg.use_reinit_ddl.put(0)

            if (self.yStartEndPosRadBtn.isChecked()):
                #val += E712_WVGEN_FLAGS.START_AT_ENDPOS
                y_wg.start_at_end_pos.put(1)
            else:
                y_wg.start_at_end_pos.put(0)

        return (val)

    def set_start_mode_flags(self, cmbobox=None, axis='x'):

        val = 0
        idx = cmbobox.currentIndex()

        if(axis is 'x'):
            if(X_AXIS_ID is 1):
                wg = self.e712.wg1
            else:
                wg = self.e712.wg3
        else:
            if(Y_AXIS_ID is 2):
                wg = self.e712.wg2
            else:
                wg = self.e712.wg4

        if (idx == 0):
            #val += E712_WVGEN_START_MODES.DO_NOT_START
            wg.start_mode.put(E712_WVGEN_START_MODES.DO_NOT_START)
        if (idx == 1):
            #val += E712_WVGEN_START_MODES.IMEDDIATELY
            wg.start_mode.put(E712_WVGEN_START_MODES.IMEDDIATELY)

        #return (val)

    def set_start_mode(self, wg_id, mode):
        if(wg_id is 1):
            wg = self.e712.wg1
        elif(wg_id is 2):
            wg = self.e712.wg2
        elif(wg_id is 3):
            wg = self.e712.wg3
        elif (wg_id is 4):
            wg = self.e712.wg4
        else:
            _logger.error('set_start_mode: wg_id not valid[%d]' % wg_id)
            return

        wg.start_mode.put(mode)

    def on_start_btn(self):
        self.running_automated = False
        self.on_start_wavegen()

    def on_start_wavegen(self):

        self.idx = 0
        self.reset_image_plot()
        mode = self.modeComboBox.currentIndex()
        self.numX = int(self.xnpointsFld.text())
        self.numY = int(self.ynpointsFld.text())
        startX = float(self.xstartFld.text())
        stopX = float(self.xstopFld.text())
        startY = float(self.ystartFld.text())
        stopY = float(self.ystopFld.text())

        rect = (startX, startY, stopX, stopY)
        self.data = np.ones((self.numY, self.numX))

        self.image_plot.set_data(self.data)

        self.image_plot.set_image_parameters(self.image_plot.item, startX, startY, stopX, stopY)
        #self.image_plot.initData(types.image_types.IMAGE, self.numY, self.numX, {'RECT': rect})
        self.image_plot.set_autoscale(fill_plot_window=False)

        if (mode is 0):
            self.is_pxp = True
            self.e712.set_is_pxp(True)
            self.config_devices(is_pxp=True)
            # pxp
            self.gate.start()
            #here the gate is the clock src so make sure its running
            self.gate.soft_trigger.put(1)
            self.cntr.start()
            self.cntr.changed.connect(self.on_sample_scan_counter_changed)
            self.changed.connect(self.add_line_to_plot)

        else:
            self.is_pxp = False
            self.e712.set_is_pxp(False)
            self.config_devices(is_pxp=False)

            # self.x_use_ddl = True
            # self.x_use_reinit_ddl = False
            # self.x_start_end_pos = False
            # self.x_force_reinit = False
            # self.x_auto_ddl = False
            if(not self.x_auto_ddl and not self.x_force_reinit):
                #default to auto
                self.x_auto_ddl = True

            if(self.x_auto_ddl):
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    self.set_xddl_flags_for_using()
                    self.e712.calc_ddl_parameters()

                else:
                    self.set_xddl_flags_for_learning()
                    #then seomhow I need to autocall an actual scan using the new table

            elif(self.x_use_reinit_ddl or self.x_force_reinit):
                self.set_xddl_flags_for_learning()
            else:
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    self.set_xddl_flags_for_using()
                    self.e712.calc_ddl_parameters()



            # lxl
            # in future, teach DDL, turn on reinit and have it run for 50 iters
            self.gate.start()
            self.cntr.start()
            self.cntr.changed.connect(self.on_sample_scan_counter_changed)
            self.changed.connect(self.add_line_to_plot)
            #self.changed.connect(self.add_data_to_q)

        self.set_ddl_flag_vals('x')
        self.set_start_mode_flags(self.xStartModeComboBox, 'x')
        self.set_ddl_flag_vals('y')
        self.set_start_mode_flags(self.yStartModeComboBox, 'y')

        # give the gate and counter time to be running
        self.startTimer.start(3000)

    def start_wavegen(self, mode, x_auto_ddl=True, x_use_reinit_ddl=False, x_force_reinit=False):

        self.idx = 0

        if (mode is 0):
            self.uncheck_xddl_flags()
            self.is_pxp = True
            self.e712.set_is_pxp(True)

        else:
            self.is_pxp = False
            self.e712.set_is_pxp(False)

            if(not x_auto_ddl and not x_force_reinit):
                #default to auto
                self.x_auto_ddl = True

            if(x_auto_ddl):
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    self.set_xddl_flags_for_using()
                    self.e712.calc_ddl_parameters()

                else:
                    self.set_xddl_flags_for_learning()
                    #then seomhow I need to autocall an actual scan using the new table

            elif(x_use_reinit_ddl or x_force_reinit):
                self.set_xddl_flags_for_learning()
            else:
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    self.set_xddl_flags_for_using()
                    self.e712.calc_ddl_parameters()

        self.set_ddl_flag_vals('x')
        self.set_start_mode_flags(self.xStartModeComboBox, 'x')
        self.set_ddl_flag_vals('y')
        self.set_start_mode_flags(self.yStartModeComboBox, 'y')

    def on_start(self):
        if(self.e712.is_busy()):
            print('WaveGenerator Busy waiting 1 sec')
            self.startTimer.start(1000)
        else:
            print('Starting WaveGenerator')
            self.e712.start_wave_generator()

    def save_ddl_data(self, ddl_data=None):
        ##############################################################################################################
        # bypassing this during automated measuring
        if(self.running_automated):
            return
        #check to see if we need to save it or not (ie: check if x_use_reinit is True, else leave
        if(not self.x_use_reinit_ddl):
            return

        dct = self.get_tuning_params()
        dct['elapsed_tstr'] = self.elapsedTimeLbl.text()
        dct['estimated_tstr'] = self.estimatedTimeLbl.text()

        if(ddl_data is not None):
            dct['xddl_tbl'] = ddl_data['data']
        else:
            dct['xddl_tbl'] = []

        dct['x_roi'] = copy.copy(self.x_roi)
        dct['y_roi'] = copy.copy(self.y_roi)
        dct['e_roi'] = copy.copy(self.e_roi)
        if(self.prev_data is not None):
            dct['data'] = copy.copy(self.prev_data)
        else:
            dct['data'] = copy.copy(self.data)

        #fprefix = get_next_file_in_seq(dataDir, prefix_char='C',extension='json')
        #dct['fpath'] = os.path.join(dataDir, fprefix + '.json')


        #write the DDL data to the database for this scan
        ddl_table_key = gen_ddl_database_key(dct)
        # 'DW:1.0000RX:8.0000NX:50AR:0.0000LS:0.0500LU:0.0010PS:0.0050PU:0.0000PT:0.0306IT:0.0015DT:0.0000NF1:48.3000NR1:0.0500NBW1:1.0000NF2:68.3600NR2:0.0600NBW2:1.0000SR:1000.0000DFBW:400'

        print('save_ddl_data: key= [%s]' % ddl_table_key)
        self.e712.store_ddl_table(ddl_table_key, dct['xddl_tbl'], dct=dct)

        #for cnvienience save a jpg thumbnail image
        #imgThread = ThreadImageSave(dct, 'e712_imagesaver', verbose=True)
        #imgThread.setDaemon(True)
        #imgThread.start()

        #now save a json file of the data
        # saveThread = ThreadJsonSave(dct, 'e712_saver', verbose=True)
        # saveThread.setDaemon(True)
        # saveThread.start()

    def stop_wave_generator(self):
        self.e712.stop_wave_generator()

    def on_stop_wavegen(self):

        self.e712.stop_wave_generator()
        self.cntr.stop()
        self.gate.stop()

        mode = int(self.modeComboBox.currentIndex())
        if(mode is 0):
            self.save_ddl_data()
        else:
            if(self.x_use_reinit_ddl and (not self.running_automated)):
                self.prev_data = copy.copy(self.data)
                self.e712.get_ddl_table(X_WAVE_TABLE_ID, cb=self.save_ddl_data)

            else:
                if(not self.running_automated):
                    self.save_ddl_data()

        try:
            self.cntr.changed.disconnect()
            self.changed.disconnect(self.add_line_to_plot)
        except:
            #raise E712Exception('on_stop_wavegen: problem disconnecting signals')
            print('on_stop_wavegen: problem disconnecting signals')


    def on_wavegen_scan_done(self):

        self.e712.stop_wave_generator()

        mode = int(self.modeComboBox.currentIndex())
        if(mode is 0):
            self.save_ddl_data()
        else:
            if(self.x_use_reinit_ddl and (not self.running_automated)):
                self.prev_data = copy.copy(self.data)
                self.e712.get_ddl_table(X_WAVE_TABLE_ID, cb=self.save_ddl_data)

            else:
                if(not self.running_automated):
                    self.save_ddl_data()


    def get_tuning_params(self):
        dct = {}
        dct['dwell'] = float(self.dwellFld.text())
        self.ss.set('dwell', dct['dwell'])
        dct['max_rcv_bytes'] = float(self.maxRcvBytesFld.text())
        self.ss.set('max_rcv_bytes', dct['max_rcv_bytes'])
        dct['max_sock_timeout'] = float(self.maxSockTimeoutFld.text())
        self.ss.set('max_sock_timeout', dct['max_sock_timeout'])
        dct['line_accrange'] = float(self.lineAccRangeFld.text())
        self.ss.set('line_accrange', dct['line_accrange'])

        dct['pnt_start_delay'] = float(self.pntStartDelayFld.text())
        self.ss.set('pnt_start_delay', dct['pnt_start_delay'])

        dct['pnt_step_time'] = float(self.pntStepTimeFld.text())
        self.ss.set('pnt_step_time', dct['pnt_step_time'])
        dct['pnt_updown_time'] = float(self.pntUpDownTimeFld.text())
        self.ss.set('pnt_updown_time', dct['pnt_updown_time'])

        dct['line_start_delay'] = float(self.lineStartDelayFld.text())
        self.ss.set('line_start_delay', dct['line_start_delay'])

        dct['line_step_time'] = float(self.lineStepTimeFld.text())
        self.ss.set('line_step_time', dct['line_step_time'])
        dct['line_updown_time'] = float(self.lineUpDownTimeFld.text())
        self.ss.set('line_updown_time', dct['line_updown_time'])
        dct['line_return_time'] = float(self.returnTimeFld.text())
        self.ss.set('line_return_time', dct['line_return_time'])
        #dct['line_trig_time'] = float(self.lineTrigTimeFld.text())
        #self.ss.set('line_trig_time', dct['line_trig_time'])

        dct['mode'] = int(self.modeComboBox.currentIndex())
        self.ss.set('mode', dct['mode'])
        dct['numX'] = int(self.xnpointsFld.text())
        self.ss.set('numX', dct['numX'])
        dct['numY'] = int(self.ynpointsFld.text())
        self.ss.set('numY', dct['numY'])

        dct['startX'] = float(self.xstartFld.text())
        self.ss.set('startX', dct['startX'])
        dct['stopX'] = float(self.xstopFld.text())
        self.ss.set('stopX', dct['stopX'])
        dct['startY'] = float(self.ystartFld.text())
        self.ss.set('startY', dct['startY'])
        dct['stopY'] = float(self.ystopFld.text())
        self.ss.set('stopY', dct['stopY'])



        # #validate that there are enough points in the table to execute this scan
        # #get_ttl_points_remaining
        # pnts_rem = self.e712.get_ttl_points_remaining()
        # total_pnts_needed = self.e712.calc_hline_time(dct['dwell'], dct['numX'], pxp=False) / PNT_TIME_RES
        # if(total_pnts_needed > pnts_rem):
        #     _logger.error('Not enough points remaining in table to perform this scan')
        #     warn("Invalid scan definition", "The scan you are attempting to configure requires more points than are available", accept_str="OK", reject_str="Cancel")
        #     #errorMessage("Invalid scan definition, The scan you are attempting to configure requires more points than are available")
        pnts_rem = self.e712.get_ttl_points_remaining()
        total_pnts_needed = self.e712.calc_hline_time(dct['dwell'], dct['numX'], pxp=False) / PNT_TIME_RES
        if (total_pnts_needed > pnts_rem):
            self.scan_ok_to_exec = False
        else:
            self.scan_ok_to_exec = True

        # _logger.error('Not enough points remaining in table to perform this scan')
        #     warn("Invalid scan definition", "The scan you are attempting to configure requires more points than are available", accept_str="OK", reject_str="Cancel")
        #     #errorMessage("Invalid scan definition, The scan you are attempting to configure requires more points than are available")

        #get the x stage parameters
        xdct = self.xmtr.get_stage_params()

        final_dct = dct_merge(dct, xdct)

        self.ss.update()
        return (final_dct)

    def on_send_wave_btn(self):
        global SEND_LIST
        SEND_LIST = []
        dct = self.get_tuning_params()
        self.e712.init_tuning_params(dct)
        self.e712.clear_wavetable(1)
        self.e712.clear_wavetable(2)
        self.e712.clear_wavetable(3)
        self.e712.clear_wavetable(4)
        self.e712.clear_trigger_table()
        # normal params
        self.e712.reinit_vars()
        self.e712.reset_run_scan_config()

        time.sleep(0.15)
        mode = self.modeComboBox.currentIndex()
        dwell = float(self.dwellFld.text())
        xstart = float(self.xstartFld.text())
        xstop = float(self.xstopFld.text())
        xnpoints = int(self.xnpointsFld.text())
        ystart = float(self.ystartFld.text())
        ystop = float(self.ystopFld.text())
        ynpoints = int(self.ynpointsFld.text())

        mode = self.modeComboBox.currentIndex()
        self.x_roi = get_base_start_stop_roi('X', FINE_X, xstart, xstop, xnpoints, is_point=False)
        self.y_roi = get_base_start_stop_roi('Y', FINE_Y, ystart, ystop, ynpoints, is_point=False)
        self.e_roi = get_base_energy_roi('EV', ENERGY, start=395.0, stop=395.0, rng=0.0, npoints=1, dwell=dwell)
        if (mode is 0):
            #print 'Doing PXP test'
            lines = self.e712.do_point_by_point(dwell, self.x_roi, self.y_roi)
        else:
            #print 'Doing LXL test'
            lines = self.e712.do_line_by_line(dwell, self.x_roi, self.y_roi, x_tbl_id=X_WAVE_TABLE_ID, y_tbl_id=Y_WAVE_TABLE_ID)

        #self.e712.set_x_start_pos(xstart)
        self.e712.set_x_start_pos(xstart - self.e712.line_accrange)

        self.e712.set_y_start_pos(ystart)
        self.e712.set_num_cycles(ynpoints)

    def set_ddl_flags(self, x_auto_ddl=True, x_force_reinit=False):
        self.x_auto_ddl = x_auto_ddl
        self.x_force_reinit = x_force_reinit

    def clear_wavetables(self):
        for i in range(1, 120, 1):
            self.e712.clear_wavetable(i)

    def clear_wavgen_use_tbl_ids(self):
        #120 is used as the id to ignore
        self.e712.set_axis_wg_usetbl_num(1, 120)
        self.e712.set_axis_wg_usetbl_num(2, 120)
        self.e712.set_axis_wg_usetbl_num(3, 120)
        self.e712.set_axis_wg_usetbl_num(4, 120)

    def clear_start_modes(self):
        self.set_start_mode(1, E712_WVGEN_START_MODES.DO_NOT_START)
        self.set_start_mode(2, E712_WVGEN_START_MODES.DO_NOT_START)
        self.set_start_mode(3, E712_WVGEN_START_MODES.DO_NOT_START)
        self.set_start_mode(4, E712_WVGEN_START_MODES.DO_NOT_START)


    def get_stored_ddl_table(self):
        '''
        using the currently entered paarameters it will generate a key to the ddl database and
        retrieve a ddl table if it exists else it will return None
        :return:
        '''
        ddl_data = None
        dct = self.get_tuning_params()
        ddl_table_key = gen_ddl_database_key(dct)
        if (self.e712.ddl_db.key_exists(ddl_table_key)):
            print('key already in database, using table from database')
            ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)

        return(ddl_data)


    def set_data_recorder_fpath(self, fpath):
        '''
        sets the absolute file path to to save the data recorder .dat file
        :param fpath:
        :return:
        '''
        self.datarecorder.set_filepath(fpath)

    def get_wg_table_ids(self, sp_id):
        x_tbl_id = None
        y_tbl_id = None
        if(sp_id in self.wavgen_table_map.keys()):
            tbl_ids = self.wavgen_table_map[sp_id]
            x_tbl_id = tbl_ids[self.base_zero(X_WAVE_TABLE_ID)]
            y_tbl_id = tbl_ids[self.base_zero(Y_WAVE_TABLE_ID)]
        return((x_tbl_id, y_tbl_id))

    def send_wave(self, sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=True, x_force_reinit=False, y_is_pxp=False, do_datarecord=True):
        '''
        This function takes all the arguments needed to create the waveforms and configure the controller to execute
        a scan with the waveform generators.
        :param sp_id:
        :param x_roi:
        :param y_roi:
        :param dwell:
        :param mode:
        :param x_auto_ddl:
        :param x_force_reinit:
        :param x_wavtable_id:
        :param y_wavtable_id:
        :param y_is_pxp: needed when doing LineSpec scans of an arbitrary line
        :return:
        '''
        global SEND_LIST
        SEND_LIST = []


        ddl_data = None
        self.x_auto_ddl = x_auto_ddl
        self.x_force_reinit = x_force_reinit
        self.x_use_reinit_ddl = x_force_reinit

        self.x_scan_reset_pos = x_roi[START]
        self.xstartFld.setText(str(x_roi[START]))
        self.xstopFld.setText(str(x_roi[STOP]))
        self.xnpointsFld.setText(str('%d' % x_roi[NPOINTS]))
        self.ystartFld.setText(str(y_roi[START]))
        self.ystopFld.setText(str(y_roi[STOP]))
        self.ynpointsFld.setText(str('%d' % y_roi[NPOINTS]))
        self.dwellFld.setText(str(dwell))
        self.modeComboBox.setCurrentIndex(mode)

        self.e712.reinit_vars()
        dct = self.get_tuning_params()
        self.e712.init_tuning_params(dct)

        # assign the wavetables to the waveform generators

        #tbl_ids = self.wavgen_table_map[sp_id]
        # x_tbl_id = tbl_ids[self.base_zero(X_WAVE_TABLE_ID)]
        # y_tbl_id = tbl_ids[self.base_zero(Y_WAVE_TABLE_ID)]
        x_tbl_id, y_tbl_id = self.get_wg_table_ids(sp_id)
        print('send_wave: x_tbl_id=%d, y_tbl_id=%d' % (x_tbl_id, y_tbl_id))

        self.e712.reset_run_scan_config()

        self.x_roi = copy.copy(x_roi)
        self.y_roi = copy.copy(y_roi)

        if (mode is 0):
            print('Doing PXP test')
            self.uncheck_xddl_flags()
            lines = self.e712.do_point_by_point(dwell, self.x_roi, self.y_roi, y_is_pxp=y_is_pxp, x_tbl_id=x_tbl_id, y_tbl_id=y_tbl_id, forced_rate=self.forced_rate)
        else:
            print('Doing LXL ')

            if(x_auto_ddl):
                self.set_xddl_flags_for_auto()
            elif(x_force_reinit):
                self.set_xddl_flags_for_force_learning()

            self.is_pxp = False
            self.e712.set_is_pxp(False)

            if (not x_auto_ddl and not x_force_reinit):
                # default to auto
                self.x_auto_ddl = True

            if (self.x_auto_ddl):
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    #self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    self.e712.clear_DDLtable(x_tbl_id)
                    time.sleep(0.5)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    tbl_check = self.is_ddl_table_valid(ddl_data)
                    #self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    if(tbl_check):
                        self.e712.put_ddl_table(x_tbl_id, ddl_data)
                        time.sleep(0.5)
                        self.set_xddl_flags_for_using()
                        self.e712.calc_ddl_parameters()

                    else:
                        self.set_xddl_flags_for_learning()

                else:
                    self.set_xddl_flags_for_learning()
                    # then seomhow I need to autocall an actual scan using the new table

            elif (self.x_use_reinit_ddl or x_force_reinit):
                self.set_xddl_flags_for_learning()
            else:
                # gen the ddl key and see if it exists
                dct = self.get_tuning_params()
                ddl_table_key = gen_ddl_database_key(dct)
                if (self.e712.ddl_db.key_exists(ddl_table_key)):
                    #self.e712.clear_DDLtable(X_WAVE_TABLE_ID)
                    self.e712.clear_DDLtable(x_tbl_id)
                    print('key already in database, using table from database')
                    ddl_data = self.e712.ddl_db.get_ddl_table(ddl_table_key)
                    #self.e712.put_ddl_table(X_WAVE_TABLE_ID, ddl_data)
                    self.e712.put_ddl_table(x_tbl_id, ddl_data)
                    self.set_xddl_flags_for_using()
                    self.e712.calc_ddl_parameters()

            lines = self.e712.do_line_by_line(dwell, self.x_roi, self.y_roi, x_tbl_id, y_tbl_id)

        self.set_axis_wg_usetbl_num(axis=X_AXIS_ID, num=x_tbl_id)
        self.set_axis_wg_usetbl_num(axis=Y_AXIS_ID, num=y_tbl_id)

        self.set_ddl_flag_vals('x')
        self.set_start_mode_flags(self.xStartModeComboBox, 'x')
        self.set_ddl_flag_vals('y')
        self.set_start_mode_flags(self.yStartModeComboBox, 'y')

        #need to set the waveform offsets
        #self.e712.set_x_start_pos(x_roi[START])
        #take into account the acc range
        self.x_scan_reset_pos = x_roi[START] - self.e712.line_accrange
        self.e712.set_x_start_pos(x_roi[START] - self.e712.line_accrange)
        self.e712.set_y_start_pos(y_roi[START])
        self.e712.set_num_cycles(y_roi[NPOINTS])

        # configure the data recorder data rec rate, dwell must be in seconds
        scan_time = self.get_new_time_in_seconds(y_roi[NPOINTS])
        if (self.datarecorder and do_datarecord):
            #self.datarecorder.enable_auto_data_recording(True)
            self.datarecorder.auto_set_datarec_rate(scan_time)
        else:
            self.datarecorder.enable_auto_data_recording(False)

        return(ddl_data)

    def get_x_scan_reset_pos(self):
        return (self.x_scan_reset_pos)

    def is_ddl_table_valid(self, ddl_data):
        val = np.sum(ddl_data[0:50]) != 0.0
        return(val)

    def set_num_cycles(self, num_cycles):
        self.e712.set_num_cycles(num_cycles)

    def base_zero(self, val):
        return(val - 1)

    def get_wave_table_data(self):
        # get data to display in plot
        #x_tbl_data = self.e712.get_wav_datatbl(tblid=X_WAVE_TABLE_ID)
        x_tbl_data = self.e712.get_wav_table(tblid=X_WAVE_TABLE_ID)
        #print('after get_wav_table X')
        if(x_tbl_data is None):
            print('there is no data to get')
            return(None, None, None)

        #y_tbl_data = 8 * self.e712.get_wav_datatbl(tblid=Y_WAVE_TABLE_ID)
        y_tbl_data = 8 * self.e712.get_wav_table(tblid=Y_WAVE_TABLE_ID)
        #print('after get_wav_table Y')
        #trig_tbl_data = 10 * self.e712.get_trig_datatbl(trig_out_id=1,
        #                                                num_points_expected=self.e712.get_wav_tbl_length(X_WAVE_TABLE_ID))
        trig_tbl_data = 10 * self.e712.get_trig_table()
        #print('after get_trig_table')

        x_len, = x_tbl_data.shape
        y_len, = y_tbl_data.shape
        trig_len, = trig_tbl_data.shape
        shortest = None
        if (y_len < x_len):
            shortest = y_len
        else:
            shortest = x_len
        if (x_len < trig_len):
            shortest = x_len
        else:
            shortest = trig_len

        #print('leaving get_wave_table_data')

        return (x_tbl_data[:shortest], y_tbl_data[:shortest], trig_tbl_data[:shortest])


    def plot_all_data(self, e712com_dct):
        (xdat, ydat, trigdat) = e712com_dct['data']
        print('starting plot data')
        self.curve_plot.clear_plot()
        self.curve_plot.create_curve('WaveTbl_%d' % X_WAVE_TABLE_ID, curve_style=get_basic_line_style('red'))
        self.curve_plot.create_curve('WaveTbl_%d' % Y_WAVE_TABLE_ID, curve_style=get_basic_line_style('yellow'))
        # plot.set_data_dir(r'S:\STXM-data\Cryo-STXM\2017\guest\0106')
        if(xdat is not None):
            pnts, = xdat.shape
            x_time_pnts = np.arange(float(pnts)) * WAVEFORM_GEN_CYCLE_TIME
            self.curve_plot.setXYData('WaveTbl_%d' % X_WAVE_TABLE_ID, x_time_pnts, xdat, update=True)

        if (ydat is not None):
            pnts, = ydat.shape
            x_time_pnts = np.arange(float(pnts)) * WAVEFORM_GEN_CYCLE_TIME
            self.curve_plot.setXYData('WaveTbl_%d' % Y_WAVE_TABLE_ID, x_time_pnts, ydat, update=True)

        maxx = max(xdat)
        if (trigdat is not None):
            pnts, = trigdat.shape
            x_time_pnts = np.arange(float(pnts)) * WAVEFORM_GEN_CYCLE_TIME
            self.curve_plot.create_curve('trigger', curve_style=None)
            #self.curve_plot.create_curve('trigger', curve_style = get_trigger_line_style('blue'))
            self.curve_plot.setXYData('trigger', x_time_pnts, trigdat * maxx, update=True)

        self.curve_plot.setPlotAxisStrs(ystr='um', xstr='seconds')
        print('done plot data')
         # self.curve_plot.show()


    def plot_data(self, e712com_dct):
        print('starting plot data')
        self.curve_plot.clear_plot()
        data = e712com_dct['data']
        tblid = e712com_dct['arg']
        self.curve_plot.create_curve('WaveTbl_%d' % tblid, curve_style=get_basic_line_style('yellow'))

        if(data is not None):
            pnts, = data.shape
            x_time_pnts = np.arange(float(pnts)) * WAVEFORM_GEN_CYCLE_TIME
            self.curve_plot.setXYData('WaveTbl_%d' % tblid, x_time_pnts, data, update=True)

        self.curve_plot.setPlotAxisStrs(ystr='um', xstr='seconds')
        print('done plot data')

    def plot_ddl_data(self,  e712com_dct):
        self.ddl_curve_plot.clear_plot()
        data = e712com_dct['data']
        tblid = e712com_dct['arg']

        pnts, = data.shape
        xdat = list(range(0,pnts))
        self.ddl_curve_plot.create_curve('DDLTbl_%d' % tblid, curve_style=get_basic_line_style('yellow'))

        x_time_pnts = np.arange(float(pnts)) * WAVEFORM_GEN_CYCLE_TIME
        self.ddl_curve_plot.setXYData('DDLTbl_%d' % tblid, x_time_pnts, data, update=True)
        rms_str = 'RMS: %.2f' % self.rms(data)
        self.ddl_curve_plot.setPlotAxisStrs(ystr='um', xstr='seconds [%s]' % rms_str)

    def rms(self, x):
        return np.sqrt(x.dot(x) / x.size)


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    from cls.app_data.defaults import get_style

    app = QtWidgets.QApplication(sys.argv)
    sys.excepthook = excepthook
    cntr = BaseCounter('uhvCI:counter')
    gate = BaseGate('uhvCO:gate')
    ss = get_style('dark')


    win = E712ControlWidget('IOCE712:', counter=cntr, gate=gate, show_plot=True)
    win.setStyleSheet(ss)
    win.show()

    sys.exit(app.exec_())
