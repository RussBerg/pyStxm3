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
from cls.zeromq.ports import front_port, back_port, pub_port, sub_port
from cls.zeromq.epics.epics_api import *
from cls.zeromq.forwarder.device_map import motors, ais, get_motor, get_ai


class sender_widget(QtWidgets.QWidget):

    def __init__(self):
        super(sender_widget, self).__init__()
        self.msgFld = QtWidgets.QLineEdit()
        self.msgFld.returnPressed.connect(self.on_ret_pressed)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % sub_port)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self.msgFld)
        self.setLayout(vlayout)

    def on_ret_pressed(self):
        txt = str(self.msgFld.text())
        ext_name, val = txt.split('=')
        dct = get_motor(ext_name)
        if(len(list(dct.keys()))> 0):
            val = string_to_value(val)
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

