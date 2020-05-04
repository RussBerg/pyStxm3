'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from bcm.devices.device_names import *
import time
import zmq


def get_put_args(msg):
	''' PUT>DNM_DETECTOR_Z#VAL=2500
	
	returns: pvname, attr, val
	
	'''
	m1 = msg.split('>')
	m2 = m1[1].split('#')
	m3 = m2[1].split('=')
	return(m2[0], m3[0], m3[1])

def get_get_args(msg):
	''' GET>DNM_DETECTOR_Z#RBV
	
	returns: pv, attr
	
	'''
	m1 = msg.split('>')
	m2 = m1[1].split('#')
	return(m2[0], m2[1])
	



context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
time.sleep(0.5)
#self.devices['POSITIONERS'][DNM_DETECTOR_Z]
while True:
	devices = MAIN_OBJ.get_devices()
	dev_keys = list(devices.keys())
	posners = devices['POSITIONERS']
	pos_keys = list(posners.keys())
	detectors = devices['DETECTORS']
	det_keys = list(detectors.keys())
	#  Wait for next request from client
	print('waiting for messages from the client')
	message = socket.recv()
	print(("Received request: %s" % message))
	get = False
	put = False
	if(message.find('GET>') > -1):
		get = True
		nm, attr = get_get_args(message)
		print(nm, attr)
		
	if(message.find('PUT>') > -1):
		''' PUT>DNM_DETECTOR_Z=2500'''
		put = True
		nm, attr, val = get_put_args(message)
		socket.send(b"PUT to %s.%s DONE" % (nm , attr))

	if(nm in pos_keys):
		print('nm[%s] is in pos_keys' % nm)
		if(get):
			print('in get')
			fbk = posners[nm].get(attr)
			socket.send(b"%.3f" % fbk)
		if(put):
			posners[nm].put(attr, val)		
	else:
		print('nm[%s] is NOT in pos_keys' % nm)

	#  Do some 'work'
	time.sleep(0.01)

	#  Send reply back to client
	#print ' sending WORLD'
	#socket.send(b"World")
