'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
from PyQt5 import QtWidgets
import sys
import zmq
import time
from cls.zeromq.ports import put_port
from cls.zeromq.epics.epics_api import *
from cls.zeromq.forwarder.device_map import motors, ais, get_motor, get_ai, put_devs, dev_types, get_devs



class sender_widget(QtWidgets.QWidget):

    def __init__(self):
        super(sender_widget, self).__init__()
        lbl = QtWidgets.QLabel('Send ZMQ message')
        self.valFld = QtWidgets.QLineEdit()
        self.valFld.returnPressed.connect(self.on_ret_pressed)

        self.devComboBox = QtWidgets.QComboBox()
        self.dev_lst = []
        for dev_nm in put_devs:
            dev = put_devs[dev_nm]
            self.devComboBox.addItem('%s [%s]' % (dev_nm, dev_types[dev['TYPE']]), dev)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % put_port)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(lbl)
        vlayout.addWidget(self.devComboBox)
        vlayout.addWidget(self.valFld)
        
        self.setLayout(vlayout)

    def on_ret_pressed(self):
        val = float(self.valFld.text())
        ext_name, _type = str(self.devComboBox.currentText()).split()
        dct = get_motor(ext_name)
        if(len(list(dct.keys()))> 0):
            if(val is not None):
                dct['PUT_VAL'] = val
                dct['CMD'] = CMD_PUT
                print('on_ret_pressed: sending ', dct)
                zmq_send_dct(self.socket, dct, do_rcv=False)
                #self.socket.send_string("%s" % (txt))
            else:
                print('problem converting the string value to an actual value')





if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    #s = b"PUT>%s#%s=%s" % (sys.argv[1], sys.argv[1], sys.argv[2])
    #send_msg(socket, s)
    sw = sender_widget()
    sw.show()

    sys.exit(app.exec_())

