'''
Created on Nov 19, 2015

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
from cls.zeromq.epics.epics_api import *
from cls.utils.json_threadsave import json_string_to_dct
import simplejson as json

context = zmq.Context()

#  Socket to talk to server
print('Connecting to zmq_epics_server3')
#client_receiver.RCVTIMEO = 1000 # in milliseconds
sock = context.socket(zmq.REQ)
sock.RCVTIMEO = 1000
sock.connect("tcp://localhost:5555")



if __name__ == "__main__":
	import sys
	
	#app = QtWidgets.QApplication(sys.argv)
	#start_server()
	
	slist = snd_rcv(sock, CMD_DISC_POSNER_LIST)
	pos_keys = process_str_to_list(slist)
	print(pos_keys)
	
	
	resp = snd_rcv(sock, CMD_UPDATE_POSNER_SNAPSHOT)
	resp = snd_rcv(sock, CMD_UPDATE_DETECTOR_SNAPSHOT)
	resp = snd_rcv(sock, CMD_UPDATE_PV_SNAPSHOT)
	
	snap_dct = snd_rcv(sock, CMD_GET_POSNER_SNAPSHOT)
	pos_snapshot_dct = process_str_to_dict(snap_dct)
	print('posner_dct keys' , list(pos_snapshot_dct.keys()))
	
	
	snap_dct = snd_rcv(sock, CMD_GET_DETECTOR_SNAPSHOT)
	pos_snapshot_dct = process_str_to_dict(snap_dct)
	print('detector_dct keys' , list(pos_snapshot_dct.keys()))
	
	snap_dct = snd_rcv(sock, CMD_GET_PV_SNAPSHOT)
	pos_snapshot_dct = process_str_to_dict(snap_dct)
	print('pv_dct keys' , list(pos_snapshot_dct.keys()))
	
	
	upd_list = ['uhvstxm:det:scan1', 'uhvstxm:det:scan2', 'uhvstxm:osa:scan1', 'uhvstxm:osa:scan2']
	
	
	send_update_list_msg(sock, CMD_UPDATE_SSCAN_SNAPSHOT, upd_list)
	#print resp	
	snapshot_dct = send_get_sscan_msg(sock, CMD_GET_SSCAN_SNAPSHOT, upd_list)
	
	print(list(snapshot_dct.keys()))
	
	zmq_send_dct(sock, snapshot_dct)
	
	print('is server still running?')
	resp = snd_rcv(sock, CMD_CHECK_IF_RUNNING)
	if(resp == 'YES'):
		print('Yes it is')
	else:
		print('NO it isnt')	
	
	print('sending zmq_epics_server abort')
	resp = snd_rcv(sock, CMD_ABORT)
	
	print('is server still running?')
	try:
	 	resp = snd_rcv(sock, CMD_CHECK_IF_RUNNING)
		if(resp == 'YES'):
			print('Yes it is')
		else:
			print('NO it isnt')
		
	except:
		print('NO it isnt')
	#sys.exit(app.exec_())