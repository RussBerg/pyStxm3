'''
Created on Nov 17, 2015

@author: bergr
'''
'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#
from PyQt5 import QtCore, QtGui
import time
import zmq
import simplejson as json
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.utils.json_threadsave import dict_to_json_string

from cls.zeromq.epics_api import * 



	
devs = MAIN_OBJ.get_devices()

class zmq_motor(QtCore.QObject):
	changed = QtCore.pyqtSignal(object)
	def __init__(self, nm):
		global devs
		import queue
		self.name = nm
		self.queue = queue.Queue()
		self.mtr = devs['POSITIONERS'][nm]
		self.mtr.add_callback('RBV', self.on_changed) 
	
	def addCallback(self, attr, cb):
		self.mtr.add_callback(attr, cb)
	
	def update(self):
		while not self.queue.empty():
			val = self.queue.get()
			self.changed.emit(val)  
		self.queue.task_done()
	
	def on_changed(self, **kwargs):
		#data = kwargs
		#print 'EpicsPvCounter: on_new_data: %s' % kwargs['type']
		print(kwargs)
		if(kwargs['type'] == 'double'):
			#self.changed.emit(float(kwargs['char_value']))
			val = float(kwargs['char_value'])
		elif(kwargs['type'] == 'integer'):
			#self.changed.emit(int(kwargs['char_value']))
			val = int(kwargs['char_value'])
		elif(kwargs['type'] == 'float'):
			#self.changed.emit(float(kwargs['char_value']))
			val = float(kwargs['char_value'])			
		else:
			#self.changed.emit(kwargs['char_value'])
			val = kwargs['char_value']
		self.queue.put_nowait(val)	
		

def on_fbk_changed(**dct):
	global socket
	print(dct)
	fbk_str= '%s %.3f' % (dct['pvname'], float(dct['value']))
	snd(socket,fbk_str)



context = zmq.Context()
# the zmq.REPly socket type 
# It will block on recv() to get a request before it can send a reply.
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
	
def start_server():
	global socket
	time.sleep(0.5)
	devices = MAIN_OBJ.get_devices()
	dev_keys = list(devices.keys())
	posners = devices['POSITIONERS']
	pos_keys = list(posners.keys())
	detectors = devices['DETECTORS']
	det_keys = list(detectors.keys())
	zmq_mtr_dct = {}
	for pos in pos_keys:
		zmq_mtr_dct[pos] = zmq_motor(pos)
		zmq_mtr_dct[pos].addCallback('RBV', on_fbk_changed)
	
	
	#self.devices['POSITIONERS'][DNM_DETECTOR_Z]
	while True:
		
		#  Wait for next request from client
		print('waiting for messages from the client')
		message = socket.recv()
		print(("Received request: %s" % message))
		get = False
		put = False
		
		if(message.find(CMD_DISC_POSNER_LIST) > -1):
			socket.send(b"%s" % (dict_to_json_string(pos_keys)))
			
		
		elif(message.find('GET>') > -1):
			get = True
			nm, attr = get_get_args(message)
			print(nm, attr)
			
		elif(message.find('PUT>') > -1):
			''' PUT>DNM_DETECTOR_Z=2500'''
			put = True
			nm, attr, val = get_put_args(message)
			socket.send(b"PUT to %s.%s DONE" % (nm , attr))
	
		elif(nm in pos_keys):
			print('nm[%s] is in pos_keys' % nm)
			if(get):
				print('in get')
				fbk = posners[nm].get(attr)
				socket.send(b"%.3f" % fbk)
			if(put):
				posners[nm].put(attr, val)		
		else:
			print('nm[%s] is NOT in pos_keys' % nm)
			socket.send(b"nm[%s] is NOT in pos_keys"% nm)
	
		#  Do some 'work'
		time.sleep(0.01)
	
		#  Send reply back to client
		#print ' sending WORLD'
		#socket.send(b"World")
		
if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	start_server()
	sys.exit(app.exec_())