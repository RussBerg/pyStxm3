'''
Created on Nov 17, 2015

@author: bergr
'''

#
from PyQt5 import QtWidgets
import sys
import zmq
import time
from epics import PV
from cls.zeromq.ports import get_port
from cls.zeromq.epics.epics_api import *
from cls.zeromq.forwarder.device_map import motors, ais, get_motor, get_ai, put_devs, dev_types, get_devs, all_devs, get_epics_rbv_name



class zeromq_get_qt_server_widget(QtWidgets.QWidget):

    def __init__(self):
        super(zeromq_get_qt_server_widget, self).__init__()
        #config socket first
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % get_port)


        lbl = QtWidgets.QLabel('Send ZMQ fbk message when PV changes')
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(lbl)

        self.dev_dct = {}
        for dev_nm in all_devs:
            hlayout = QtWidgets.QHBoxLayout()
            dev = all_devs[dev_nm]
            dev_nm_lbl = QtWidgets.QLabel(dev_nm + ': ')
            dev_fbk_lbl = QtWidgets.QLabel('0.000')
            hlayout.addWidget(dev_nm_lbl)
            hlayout.addWidget(dev_fbk_lbl)
            vlayout.addLayout(hlayout)
            pv = PV(get_epics_rbv_name(all_devs, dev_nm))
            pv.add_callback(self.on_fbk_changed, dev_fbk_lbl)
            self.dev_dct[dev_nm] = dev_fbk_lbl


        self.setLayout(vlayout)

    def on_fbk_changed(self, **kwargs):
        lbl = kwargs['cb_info'][0]

        #print kwargs
        val = kwargs['value']
        lbl.setText(str(val))
        dct = {}
        dct['GET_VAL'] = val
        dct['CMD'] = CMD_GET
        #print 'on_fbk_changed: sending ', dct
        zmq_send_dct(self.socket, dct, do_rcv=False)




if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    #s = b"PUT>%s#%s=%s" % (sys.argv[1], sys.argv[1], sys.argv[2])
    #send_msg(socket, s)
    sw = zeromq_get_qt_server_widget()
    sw.show()

    sys.exit(app.exec_())

