#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import os
import time

import numpy as np
np.set_printoptions(threshold='nan')


import zmq
import traceback
import io
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QPlainTextEdit, QPushButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QSocketNotifier, QTimer

from bcm.devices.device_names import *
from cls.zeromq.epics.epics_api import *


LOCAL_ENDPOINT = "tcp://localhost:5555"
REMOTE_ENDPOINT = "tcp://10.51.3.31:5555"
save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to <%s>.\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("russ.berg@lightsource.ca", "")
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


class zmq_epicsClient():
    def __init__(self, socket=None):
        #context = zmq.Context.instance()
        #client = context.socket(zmq.REP)
        #client.setsockopt(zmq.IDENTITY, b'Qtzmq_epicsClient')
        #client.connect(ENDPOINT)

        if(socket is not None):
            self.socket = socket
        else:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(LOCAL_ENDPOINT)
            self.socket.connect(REMOTE_ENDPOINT)



    def dispatch(self, msg):
        print('qt5_epics_client: dispatch going to try and send this [%s]' % msg)
        #msg = bytes(msg, 'utf-8')
        #uid = uuid.uuid4().bytes
        self.socket.send(msg)
        self.recv()
        #return msg

    def recv(self):
        message =  self.socket.recv()
        print(("qt5_epics_client: Received request: %s" % message))
        return(message)

    def zmq_send_array(self, idx, arr):
        #send_array(self.socket, arr)
        dct = {}
        ht, wd = arr.shape
        dct['ht'] = ht
        dct['wd'] = wd
        dct['idx'] = idx
        dct['devname'] = 'counter0'
        dct['data'] = arr
        send_zipped_pickle(self.socket, dct)

    def init_new_scan(self, fname=None, upd_lst=None):
        fname = self.send_set_filename(fname=fname)
        self.send_create_new_file()
        self.zmq_register_upd_list(update_dev_lst=upd_lst)
        resp = self.exec_cmnd(CMD_UPDATE_POSNER_SNAPSHOT)
        #self.save_img_idx_map()

    def send_set_filename(self, fname=None):
        dct = {}
        if(fname is None):
            dct['fname'] = self.fnameFld.text()
        else:
            dct['fname'] = fname
        dct['dir'] = save_dir
        d_str = dict_to_str(dct)
        #        CMD_SET_FILE_NAME
        msg = '%s%s' % (CMD_SET_FILE_NAME, d_str)
        self.exec_cmnd(msg)
        fpath = os.path.join(save_dir, dct['fname'])
        return(fpath)


    def send_create_new_file(self):
        self.exec_cmnd(CMD_CREATE_NEW_FILE)
        resp = snd_rcv(self.socket, CMD_UPDATE_POSNER_SNAPSHOT)
        #print resp


    def zmq_update_tmp_file(self, cntr):
        #global cntr
        send_do_update_msg(self.socket, CMD_UPDATE_UPD_SNAPSHOT, cntr)

    def send_create_new_file(self):
        self.exec_cmnd(CMD_CREATE_NEW_FILE)
        resp = snd_rcv(self.socket, CMD_UPDATE_POSNER_SNAPSHOT)
        #print resp

        #self.save_img_idx_map()

    def exec_cmnd(self, cmnd):
        resp = snd_rcv(self.socket, cmnd)
        #print resp

    def zmq_register_upd_list(self, update_dev_lst=None):
        if(update_dev_lst is None):
            update_dev_lst = []
            update_dev_lst.append(DNM_ENERGY)
            update_dev_lst.append(DNM_EPU_POLARIZATION)
            update_dev_lst.append(DNM_EPU_ANGLE)
            update_dev_lst.append(DNM_EPU_GAP)
            update_dev_lst.append(DNM_EPU_HARMONIC)
            update_dev_lst.append(DNM_EPU_OFFSET)
            update_dev_lst.append(DNM_PMT)
            update_dev_lst.append(DNM_RING_CURRENT)
            # update_dev_lst.append(DNM_TYCHO_CAMERA) This adds significant file size because its
            # 640x480x4bytes per frame = 1,288,800 bytes per frame

        send_register_update_list_msg(self.socket, CMD_REGISTER_UPD_LIST, update_dev_lst)

    def gen_img_idx_map(self):
        img_idx_map = {}
        numE = 10
        numEPU = 3
        numSPIDS = 4
        indiv_img_idx = 0

        for i in range(numE):
            entry_idx = 0
            for k in range(numEPU):
                for j in range(numSPIDS):
                    img_idx_map[indiv_img_idx] = {'e_idx': i, 'pol_idx': k, 'sp_idx': j,
                                                       'entry': 'entry%d' % entry_idx}
                    indiv_img_idx += 1
                    entry_idx += 1
        return(img_idx_map)

    def zmq_register_img_idx_map(self, img_idx_map=None):
        if(img_idx_map is None):
            img_idx_map = self.gen_img_idx_map()

        send_register_img_idx_map_msg(self.socket, CMD_REGISTER_IMG_IDX_MAP, img_idx_map)


class Example(QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()
        self._client = zmq_epicsClient()
        socket = self._client.socket

        self._notifier = QSocketNotifier(socket.getsockopt(zmq.FD), QSocketNotifier.Read, self)
        self._notifier.activated.connect(self._socket_activity)
        self._counter = 0

        self._client.init_new_scan(fname=r'S:\STXM-data\Cryo-STXM\2017\guest\0719\qt5_epics_client.tmp')
        self._client.zmq_register_img_idx_map()


        self.testTimer = QTimer()
        self.testTimer.timeout.connect(self._send_data)
        #self.testTimer.start(500)


    def initUI(self):
        self.qpteText = QPlainTextEdit(self)
        btn = QPushButton("Send something")
        btn.clicked.connect(self._send_data)

        layout = QGridLayout()
        layout.addWidget(self.qpteText, 1, 1)
        layout.addWidget(btn, 2, 1)
        self.setLayout(layout)

        self.setGeometry(200, 200, 480, 400)
        self.setWindowTitle('QT & ZMQ integration test')
        self.show()

        self._log('[UI] started')

    def _log(self, data):
        text = self.qpteText.toPlainText()
        self.qpteText.setPlainText(text + data + '\n')

    def _send_data(self):
        if(self._counter > 1000):
            quit()

        data = np.random.randint(65535, size=(100, 100))
        self._client.zmq_send_array(self._counter, data)
        self._client.zmq_update_tmp_file(self._counter )
        self._counter += 1

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
    w = Example()

    # Ensure that the application quits using CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())