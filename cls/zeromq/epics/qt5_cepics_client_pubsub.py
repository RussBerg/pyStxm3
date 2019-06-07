#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import os
import time
import numpy as np

#RUSS py3   np.set_printoptions(threshold='nan')

import zmq
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QPlainTextEdit, QPushButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QSocketNotifier, QTimer

from cls.utils.excepthook import excepthook
from cls.utils.time_utils import make_timestamp_now
#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.appWidgets.splashScreen import get_splash, del_splash
from bcm.devices.device_names import *
from cls.zeromq.epics.epics_api import *
from cls.utils.dict_utils import dct_merge
from cls.zeromq.epics.epics_api import dict_to_str, compression_types
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = "10000000"

#splash = get_splash()
#didit = splash.close()

LOCAL_ENDPOINT = "tcp://*:5555"
REMOTE_ENDPOINT = "tcp://10.51.3.31:5555"
save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# devs = MAIN_OBJ.get_devices()
# posners_dct = devs['POSITIONERS']
# detectors_dct = devs['DETECTORS']
# temperatures_dct = devs['TEMPERATURES']
# pressures_dct = devs['PRESSURES']
# pvs_dct = devs['PVS']
# sscans_dct = devs['SSCANS']
#sscans_dct_keys = sscans_dct.keys()

posner_snapshot = {}
det_snapshot = {}
pv_snapshot = {}
temps_snapshot = {}
press_snapshot = {}
sscan_snapshot = {}
dev_update_dct = {}


def update_posner_snapshot():
	for k in list(posners_dct.keys()):
		posner_snapshot[k] = {}
		posner_snapshot[k]['VELO'] = posners_dct[k].get('velocity')
		posner_snapshot[k]['VAL'] = posners_dct[k].get('VAL')
		posner_snapshot[k]['DESC'] = posners_dct[k].get('description')
		posner_snapshot[k]['NAME'] = posners_dct[k].get_name()
		posner_snapshot[k]['ACCL'] = posners_dct[k].get('ACCL')
		posner_snapshot[k]['RRBV'] = posners_dct[k].get('RRBV')
		posner_snapshot[k]['LLM'] = posners_dct[k].get_low_limit()
		posner_snapshot[k]['HLM'] = posners_dct[k].get_high_limit()
		posner_snapshot[k]['RDBD'] = posners_dct[k].get('RDBD')
		posner_snapshot[k][RBV] = posners_dct[k].get('RBV')   

	return(posner_snapshot)


def update_detector_snapshot():
    """
    update_detector_snapshot(): description
    :param detectors_dct: detectors_dct description
    :type detectors_dct: detectors_dct type
    :returns: None
    """
    """
    This function grabs the current values of all positioners for the
    data saving thread to use

    """
    for k in list(detectors_dct.keys()):
        det_snapshot[k] = {}
        det_snapshot[k][RBV] = detectors_dct[k].get_position()
    return (det_snapshot)


def update_pvs_snapshot():
    """
    update_pvs_snapshot(): description

    :param pvs_dct: pvs_dct description
    :type pvs_dct: pvs_dct type
    :returns: None
    """
    """
    This function grabs the current values of all positioners for the
    data saving thread to use

    """
    for k in list(pvs_dct.keys()):
        pv_snapshot[k] = {}
        pv_snapshot[k][RBV] = pvs_dct[k].get_position()

    return (pv_snapshot)

def update_snapshot(dct):
    """
    update_pvs_snapshot(): description

    :param pvs_dct: pvs_dct description
    :type pvs_dct: pvs_dct type
    :returns: None
    """
    """
    This function grabs the current values of all positioners for the
    data saving thread to use

    """
    _snapshot = {}
    for k in list(dct.keys()):
        _snapshot[k] = dct[k].get_position()

    return (_snapshot)



def update_dev_snapshot(dev_lst):
	upd_dct = {}
	for dev_name in dev_lst:
		dev = MAIN_OBJ.device(dev_name)
		val = None
		if(dev is not None):
			val = dev.get_position()

		upd_dct[dev_name] = val

	return(upd_dct)

class CompressionBase(object):
    '''
    a base class that represents what a compression object needs to support
    '''

    def __init__(self, compression_type=compression_types.PICKLE):
        self.compression_type = compression_type

    def send_compressed(self, socket, obj, do_recv=True):
        pass

    def recv_compressed(self, socket):
        pass

class MsgpackComp(CompressionBase):
    '''
    a compression object for sending and receiving msgs using the msgpack module
    '''

    def __init__(self, socket=None):
        super(MsgpackComp, self).__init__(compression_type=compression_types.MSGPACK)

    def send_compressed(self, socket, obj, do_rcv=True):
        if (do_rcv):
            rcv_msg = send_msgpack_msg(socket, obj, flags=0, do_rcv=do_rcv)
            return(rcv_msg)
        else:
            send_msgpack_msg(socket, obj, flags=0, do_rcv=do_rcv)

    def recv_compressed(self, socket):
        dct = proc_msgpack(socket)
        return dct

class PickleMsgComp(CompressionBase):
    '''
    a compression object for sending and receiving msgs using the pickle module with gzip
    '''

    def __init__(self, socket=None):
        super(PickleMsgComp, self).__init__(compression_type=compression_types.PICKLE)

    def send_compressed(self, socket, obj, do_rcv=True):
        if (do_rcv):
            rcv_msg = send_zipped_pickle(socket, obj, flags=0, protocol=-1, do_rcv=do_rcv)
            return(rcv_msg)
        else:
            send_zipped_pickle(socket, obj, flags=0, protocol=-1, do_rcv=do_rcv)

    def recv_compressed(self, socket):
        p = recv_zipped_pickle(socket, flags=0, protocol=-1)
        return pickle.loads(p)


class zmq_epicsClient():
    def __init__(self, socket=None, compression_type=compression_types.PICKLE):
        #context = zmq.Context.instance()
        #client = context.socket(zmq.REP)
        #client.setsockopt(zmq.IDENTITY, b'Qtzmq_epicsClient')
        #client.connect(ENDPOINT)

        self.compression_type = compression_type

        if(compression_type is compression_types.PICKLE):
            self.comp_mod = PickleMsgComp()
        elif(compression_type is compression_types.MSGPACK):
            self.comp_mod = MsgpackComp()
        else:
            self.comp_mod = None
            _logger.error('ERROR: no compression object specified for qt5_epics_client_pubsub')
            return

        if(socket is not None):
            self.socket = socket
        else:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.bind(LOCAL_ENDPOINT)

    def init_new_scan(self, fname=None, subdir=None):
        fname = self.zmq_send_set_filename(fname=fname, subdir=subdir)


    def dispatch(self, msg):
        print('dispatch going to try and send this [%s]' % msg)
        #msg = bytes(msg, 'utf-8')
        #uid = uuid.uuid4().bytes
        self.socket.send(msg)
        self.recv()
        #return msg

    def recv(self):
        message =  self.socket.recv()
        print(("Received request: %s" % message))
        return(message)

    def zmq_send_counter_data(self, idx, counter, arr):
        #send_array(self.socket, arr)
        dct = {}
        ht, wd = arr.shape
        dct['cmd'] = CMD_SAVE_DATA_TO_IDX
        dct['devs'] = {}
        dct['devs'][counter] = {'ht':ht, 'wd':wd, 'idx':idx, 'data':arr}
        #send_zipped_pickle(self.socket, dct, do_rcv=False)
        self.comp_mod.send_compressed(self.socket, dct, do_rcv=False)

    def zmq_send_posner_snapshot(self, idx):
        #send_array(self.socket, arr)
        dct = {}
        posner_dct = update_posner_snapshot()
        dct['cmd'] = CMD_UPDATE_PV_SNAPSHOT
        dct['data_dct'] = posner_dct
        dct['idx'] = idx
        #send_zipped_pickle(self.socket, dct, do_rcv=False)
        self.comp_mod.send_compressed(self.socket, dct, do_rcv=False)

    def zmq_send_set_filename(self, fname=None, subdir=None):
        dct = {}
        if(fname is None):
            dct['fname'] = self.fnameFld.text()
        else:
            dct['fname'] = fname

        dct['cmd'] = CMD_SET_FILE_NAME
        if(subdir):
            dct['subdir'] = subdir
        else:
            dct['subdir'] = ''

        dct['fname'] = fname
        #send_zipped_pickle(self.socket, dct, do_rcv=False)
        self.comp_mod.send_compressed(self.socket, dct, do_rcv=False)

    def zmq_send_create_new_file(self):
        self.exec_cmnd(CMD_CREATE_NEW_FILE)
        #resp = snd(self.socket, CMD_UPDATE_POSNER_SNAPSHOT)
        #print resp

    def zmq_register_img_idx_map(self, img_idx_map=None, do_rcv=False):
        if(img_idx_map is None):
            img_idx_map = self._gen_img_idx_map()

        send_register_img_idx_map_msg(self.socket, CMD_REGISTER_IMG_IDX_MAP, img_idx_map, do_rcv=do_rcv)

    def send_dict_to_tmp_file_idx(self, dct):
        #send_zipped_pickle(self.socket, dct, do_rcv=False)
        self.comp_mod.send_compressed(self.socket, dct, do_rcv=False)
        #send_msgpack_msg(self.socket, dct)

    def send_json_to_tmp_file(self, dct):
        #send_zipped_pickle(self.socket, dct, do_rcv=False)
        self.comp_mod.send_compressed(self.socket, dct, do_rcv=False)

    def exec_cmnd(self, cmnd):
        #resp = snd(self.socket, cmnd)
        snd(self.socket, cmnd)
        #print resp

    def close(self):
        self.socket.close()
        self.context.term()




class qt5_zmqClientWidget(QWidget):

    def __init__(self, compression_type=compression_types.PICKLE):
        super(qt5_zmqClientWidget, self).__init__()

        self._client = zmq_epicsClient(compression_type=compression_type)
        socket = self._client.socket

        self._notifier = QSocketNotifier(socket.getsockopt(zmq.FD), QSocketNotifier.Read, self)
        self._notifier.activated.connect(self._socket_activity)
        self._counter = 0

        #self._client.init_new_scan(fname=r'qt5_epics_client.tmp', subdir='C100001')
        #self._client.zmq_register_img_idx_map()

        self.fname = None
        self.subdir = None

        self.testTimer = QTimer()
        self.testTimer.timeout.connect(self._send_data)
        #self.testTimer.start(500)
        self.subdirFld = QtWidgets.QLineEdit("C100010")
        self.subdirFld.returnPressed.connect(self.set_new_subdir)
        self.fnameFld = QtWidgets.QLineEdit("%s" % ('tempfile.nxstxm_baseline.tmp'))
        self.fnameFld.returnPressed.connect(self.set_new_filename)
        self.qpteText = QPlainTextEdit(self)

        startTimerBtn = QPushButton("Start Timer Run")
        startTimerBtn.clicked.connect(self._start_timer_run)

        dctToIdxBtn = QPushButton("Send Dict to index")
        dctToIdxBtn.clicked.connect(self.on_send_dict_to_idx)

        imgIdxBtn = QPushButton("Send Img Idx Map")
        imgIdxBtn.clicked.connect(self.on_send_img_idx_map)

        strtTimeBtn = QPushButton("Send Start Time")
        strtTimeBtn.clicked.connect(self.starttime_to_tmp_file)

        stopTimeBtn = QPushButton("Send Stop Time")
        stopTimeBtn.clicked.connect(self.stoptime_to_tmp_file)

        subdirLbl = QtWidgets.QLabel('Subdir')
        fnameLbl = QtWidgets.QLabel('Fname')

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(subdirLbl)
        hlayout.addWidget(self.subdirFld)
        hlayout.addWidget(fnameLbl)
        hlayout.addWidget(self.fnameFld)
        layout.addLayout(hlayout)
        layout.addWidget(self.qpteText)
        layout.addWidget(startTimerBtn)

        layout.addWidget(strtTimeBtn)
        layout.addWidget(stopTimeBtn)
        layout.addWidget(dctToIdxBtn)
        layout.addWidget(imgIdxBtn)


        self.setLayout(layout)

        self._client.zmq_send_create_new_file()

        self.setGeometry(200, 200, 480, 400)
        self.setWindowTitle('QT & ZMQ integration test')
        self._log('[UI] started')

    def terminate(self):
        self._notifier.setEnabled(False)
        self._client.close()

    def _start_timer_run(self):
        self._counter = 0
        self.testTimer.start(100)

    def set_new_filename(self, fname=None, subdir=None):
        if (fname is None):
            fname = self.fnameFld.text()

        if(subdir is None):
            subdir = self.subdir

        self.fname = fname
        self._client.init_new_scan(fname=fname, subdir=subdir)

    def set_new_subdir(self, subdir=None):
        if(subdir is None):
            subdir = self.subdirFld.text()
        self.subdir = subdir
        self.set_new_filename(self.fname, self.subdir)

    def rename_tmp_to_final(self):
        dct = {}
        dct['cmd'] = CMD_RNAME_TMP_TO_FINAL
        self._client.send_dict_to_tmp_file_idx(dct)


    def send_dict_to_tmp_file(self, dct=None):
        '''
        This function can be called from a parent and supply a dct that will be written to the temp hdf file
        with the same dict structure
        :param dct:
        :return:
        '''
        if(dct is None):
            dct = {}
            dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
            idx_dct = {}
            idx_str = 'idx%d' % self._counter
            idx_dct[idx_str] = {}
            #posnerdevlst = self._gen_register_posner_upd_list()
            idx_dct[idx_str]['positioners'] = update_posner_snapshot()
            idx_dct[idx_str]['temperatures'] = update_snapshot(temperatures_dct['ES'])
            idx_dct[idx_str]['pressures'] = update_snapshot(pressures_dct['ES'])
            idx_dct[idx_str]['detectors'] = update_detector_snapshot()
            idx_dct[idx_str]['pvs'] = update_pvs_snapshot()
            dct['dct'] = idx_dct

        #print 'send_dict_to_tmp_file: sending %s' % dct['dct']
        self._client.send_dict_to_tmp_file_idx(dct)
        #self._client.send_dict_to_tmp_file_idx_via_msgpack(dct)
        self._counter += 1

    def starttime_to_tmp_file(self):
        '''
        create the base attributes
        :return:
        '''
        dct = {}
        dct['cmd'] = dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
        dct['dct'] = {}
        dct['dct']['start_time'] = make_timestamp_now()
        dct['dct']['title'] = 'NeXus'
        dct['dct']['version'] = '1.0'
        dct['dct']['definition'] = 'NXstxm sample'
        self._client.send_dict_to_tmp_file_idx(dct)

    def stoptime_to_tmp_file(self):
        dct = {}
        dct['cmd'] = dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
        dct['dct'] = {}
        dct['dct']['end_time'] = make_timestamp_now()
        self._client.send_dict_to_tmp_file_idx(dct)

    def on_send_img_idx_map(self, img_idx_map=None):
        self.send_img_idx_map()

    def send_img_idx_map(self, img_idx_map=None):
        if(img_idx_map is None):
            img_idx_map = self._gen_img_idx_map()

        dct = {}
        dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
        #dct['dct'] = dict_to_str(img_idx_map)
        dct['dct'] = {'img_idx_map': dict_to_str(img_idx_map)}
        self._client.send_dict_to_tmp_file_idx(dct)

    def _log(self, data):
        text = self.qpteText.toPlainText()
        self.qpteText.setPlainText(text + data + '\n')

    def _send_data(self):
        if(self._counter > 100):
            self.testTimer.stop()
            print('timer completed')
            return

        #sim 3 CCD detectors
        shapes = [(100,100), (25,25), (50,200)]
        for i in range(3):
            data = np.random.randint(65535, size=shapes[i])
            self._client.zmq_send_counter_data(self._counter, 'counter%d' % i, data)

        self._client.zmq_update_tmp_file(self._counter)
        self._send_snapshot()
        self._counter += 1

    def on_send_dict_to_idx(self):
        self.send_dict_to_idx()


    def _gen_register_posner_upd_list(self, update_dev_lst=None, do_rcv=False):
        update_dev_lst = []
        update_dev_lst.append(DNM_ENERGY)
        update_dev_lst.append(DNM_EPU_POLARIZATION)
        update_dev_lst.append(DNM_EPU_ANGLE)
        update_dev_lst.append(DNM_EPU_GAP)
        update_dev_lst.append(DNM_EPU_HARMONIC)
        update_dev_lst.append(DNM_EPU_OFFSET)

        #update_dev_lst.append(DNM_PMT)
        #update_dev_lst.append(DNM_RING_CURRENT)

        # update_dev_lst.append(DNM_TYCHO_CAMERA) This adds significant file size because its
        # 640x480x4bytes per frame = 1,288,800 bytes per frame
        return(update_dev_lst)


    def _gen_img_idx_map(self):
        dct = {}
        img_idx_map = {}
        numE = 4
        numEPU = 2
        numSPIDS = 3
        indiv_img_idx = 0

        for i in range(numE):
            entry_idx = 0
            for k in range(numEPU):
                for j in range(numSPIDS):
                    img_idx_map['%d' % indiv_img_idx] = {'e_idx': i, 'pol_idx': k, 'sp_idx': j,
                                                       'entry': 'entry%d' % entry_idx}
                    indiv_img_idx += 1
                    entry_idx += 1
        dct['img_idx_map'] = img_idx_map
        return(dct)

    def _socket_activity(self):
        self._notifier.setEnabled(False)

        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))

        if flags & zmq.POLLIN:
            received = self._client.recv()
            self._log("[Socket] zmq.POLLIN")
            self._log("[Socket] received: " + repr(received))
        elif flags & zmq.POLLOUT:
            #self._log("[Socket] zmq.POLLOUT")
            pass
        elif flags & zmq.POLLERR:
            self._log("[Socket] zmq.POLLERR")

        else:
            self._log("[Socket] FAILURE")
        self._notifier.setEnabled(True)

        # I have no idea why I need this here, but it won't work more than once
        # if this is not used
        flags = self._client.socket.getsockopt(zmq.EVENTS)
        self._log("[Socket] socket.getsockopt(zmq.EVENTS): " + repr(flags))




if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = excepthook
    w = qt5_zmqClientWidget()
    w.show()
    # Ensure that the application quits using CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())