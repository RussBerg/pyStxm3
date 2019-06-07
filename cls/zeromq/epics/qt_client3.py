'''
Created on Nov 19, 2015

@author: bergr
'''

from PyQt5 import QtCore, QtGui, QtWidgets
import os
import time
import zmq

from bcm.devices.device_names import *
from cls.zeromq.epics.epics_api import *
from cls.utils.json_threadsave import json_string_to_dct
from cls.utils.file_system_tools import split_data_dir
import simplejson as json

save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#context = zmq.Context()

#  Socket to talk to server
#print('Connecting to zmq_epics_server3')
# client_receiver.RCVTIMEO = 1000 # in milliseconds
#sock = context.socket(zmq.REQ)
#sock.RCVTIMEO = 1000
#sock.connect("tcp://localhost:5555")

cntr = 0

class zmq_epicsClient(QtWidgets.QWidget):
    def __init__(self, sock=None):
        super(zmq_epicsClient, self).__init__()

        self.sock = sock
        self.configScanBtn = QtWidgets.QPushButton('Config Scan')
        self.getUpdateBtn = QtWidgets.QPushButton('Update Tmp File')
        self.newFileBtn = QtWidgets.QPushButton('Create New Tmp File')
        self.fnameFld = QtWidgets.QLineEdit("%s" % ('tempfile.nxstxm_baseline.tmp') )

        self.configScanBtn.clicked.connect(self.init_new_scan)
        self.getUpdateBtn.clicked.connect(self.zmq_update_tmp_file)
        self.newFileBtn.clicked.connect(self.send_create_new_file)
        self.fnameFld.returnPressed.connect(self.send_set_filename)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.fnameFld)
        layout.addWidget(self.configScanBtn)
        layout.addWidget(self.getUpdateBtn)
        layout.addWidget(self.newFileBtn)

        self.setLayout(layout)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Icon')
        self.setWindowIcon(QtGui.QIcon('web.png'))


    def init_new_scan(self, fname=None, upd_lst=[]):
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
        resp = snd_rcv(self.sock, CMD_UPDATE_POSNER_SNAPSHOT)
        print(resp)


    def zmq_update_tmp_file(self, cntr):
        #global cntr
        send_do_update_msg(self.sock, CMD_UPDATE_UPD_SNAPSHOT, cntr)
        #cntr += 1

    def send_create_new_file(self):
        self.exec_cmnd(CMD_CREATE_NEW_FILE)
        resp = snd_rcv(self.sock, CMD_UPDATE_POSNER_SNAPSHOT)
        print(resp)

        #self.save_img_idx_map()

    def exec_cmnd(self, cmnd):
        resp = snd_rcv(self.sock, cmnd)
        print(resp)

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
            update_dev_lst.append(DNM_TYCHO_CAMERA)

        send_register_update_list_msg(self.sock, CMD_REGISTER_UPD_LIST, update_dev_lst)

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

        send_register_img_idx_map_msg(self.sock, CMD_REGISTER_IMG_IDX_MAP, img_idx_map)






if __name__ == "__main__":
    import sys

    #app = QtWidgets.QApplication(sys.argv)
    # start_server()
    app = QtWidgets.QApplication(sys.argv)

    w = zmq_epicsClient()
    w.show()


    # slist = snd_rcv(sock, CMD_DISC_POSNER_LIST)
    # pos_keys = process_str_to_list(slist)
    # print pos_keys
    #
    # resp = snd_rcv(sock, CMD_UPDATE_POSNER_SNAPSHOT)
    # resp = snd_rcv(sock, CMD_UPDATE_DETECTOR_SNAPSHOT)
    # resp = snd_rcv(sock, CMD_UPDATE_PV_SNAPSHOT)
    #
    # snap_dct = snd_rcv(sock, CMD_GET_POSNER_SNAPSHOT)
    # pos_snapshot_dct = process_str_to_dict(snap_dct)
    # print 'posner_dct keys', pos_snapshot_dct.keys()
    #
    # snap_dct = snd_rcv(sock, CMD_GET_DETECTOR_SNAPSHOT)
    # pos_snapshot_dct = process_str_to_dict(snap_dct)
    # print 'detector_dct keys', pos_snapshot_dct.keys()
    #
    # snap_dct = snd_rcv(sock, CMD_GET_PV_SNAPSHOT)
    # pos_snapshot_dct = process_str_to_dict(snap_dct)
    # print 'pv_dct keys', pos_snapshot_dct.keys()
    #
    # upd_list = ['uhvstxm:det:scan1', 'uhvstxm:det:scan2', 'uhvstxm:osa:scan1', 'uhvstxm:osa:scan2']
    #
    # send_update_list_msg(sock, CMD_UPDATE_SSCAN_SNAPSHOT, upd_list)
    # # print resp
    # snapshot_dct = send_get_sscan_msg(sock, CMD_GET_SSCAN_SNAPSHOT, upd_list)
    #
    # print snapshot_dct.keys()
    #
    # zmq_send_dct(sock, snapshot_dct)
    #
    # print 'is server still running?'
    # resp = snd_rcv(sock, CMD_CHECK_IF_RUNNING)
    # if (resp == 'YES'):
    #     print 'Yes it is'
    # else:
    #     print 'NO it isnt'

    #print 'sending zmq_epics_server abort'
    #resp = snd_rcv(sock, CMD_ABORT)

    sys.exit(app.exec_())

