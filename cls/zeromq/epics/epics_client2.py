'''
Created on Nov 17, 2015

@author: bergr
'''
'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World client in Python
#   Connects REQ sock to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
from PyQt5 import QtCore, QtGui
import time
import zmq

from bcm.devices.device_names import *
from cls.zeromq.epics_api import * 
from sm.stxm_control.stxm_utils.json_threadsave import json_string_to_dct

context = zmq.Context()

#  Socket to talk to server
print('Connecting to hello world server')
sock = context.socket(zmq.REQ)
sock.connect("tcp://localhost:5555")

def process_str_to_list(str):
	s2 = str.replace('[','')
	s2 = s2.replace(']','')
	s2 = s2.replace('"','')
	s2 = s2.replace(' ','')
	s2 = s2.replace('\n','')
	s2 = s2.strip()
	s2 = s2.rstrip()
	l = s2.split(',')
	return(l)


if __name__ == "__main__":
	import sys
	#app = QtWidgets.QApplication(sys.argv)
	#start_server()
	
	#  Do 10 requests, waiting each time for a response
	#for request in range(2):
	
	#pos_fbk = send_get_msg(sock, DNM_DETECTOR_Z, 'RBV')
	#print 'pos_fbk = %s' % pos_fbk
	#send_put_msg(sock, DNM_DETECTOR_Z, 'SPMG', 0)
	#send_put_msg(sock, DNM_DETECTOR_Z, 'VELO', 200)
	#send_put_msg(sock, DNM_DETECTOR_Z, 'SPMG', 3)
	#send_put_msg(sock, DNM_DETECTOR_Z, 'VAL', 0)
	#send_put_msg(sock, DNM_DETECTOR_Z, 'VAL', 0)
	slist = snd_rcv(sock, CMD_DISC_POSNER_LIST)
	pos_keys = process_str_to_list(slist)
	print(pos_keys)
	
	#send_put_msg(sock, DNM_DETECTOR_X, 'VAL', 5000)
	print('sending %.3f to %s.VAL' % (5000, pos_keys[1]))
	send_put_msg(sock, pos_keys[1], 'VAL', 5000)
	
	
	#for i in range(2):
	#	pos_fbk = send_get_msg(sock, DNM_DETECTOR_Z, 'RBV')
	#	print 'pos_fbk = %s' % pos_fbk
	#sys.exit(app.exec_())