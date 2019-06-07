'''
Created on Nov 17, 2015

@author: bergr
'''


#
#   Hello World client in Python
#   Connects REQ sock to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
import time
import zmq

from bcm.devices.device_names import *

def snd_rcv(sock, request):
	sock.send(request)
	time.sleep(0.001)
	message = sock.recv()
	return(message)

def send_put_msg(sock, nm, attr, val):
	request = b"PUT>%s#%s=%d" % (nm, attr, val)
	message = snd_rcv(sock, request)
	print(("Received reply %s [ %s ]" % (request, message)))

def send_get_msg(sock, nm, attr):
	request = b"GET>%s#%s" % (nm, attr)
	message = snd_rcv(sock, request)
	#print("Received reply %s [ %s ]" % (request, message))
	return(message)





context = zmq.Context()

#  Socket to talk to server
print('Connecting to server')
sock = context.socket(zmq.REQ)
#sock.connect("tcp://localhost:5555")
sock.connect("tcp://10.51.3.31:5555")


#  Do 10 requests, waiting each time for a response
#for request in range(2):

#pos_fbk = send_get_msg(sock, DNM_DETECTOR_Z, 'RBV')
#print 'pos_fbk = %s' % pos_fbk
#send_put_msg(sock, DNM_DETECTOR_Z, 'SPMG', 0)
#send_put_msg(sock, DNM_DETECTOR_Z, 'VELO', 200)
#send_put_msg(sock, DNM_DETECTOR_Z, 'SPMG', 3)
#send_put_msg(sock, DNM_DETECTOR_Z, 'VAL', 0)
#send_put_msg(sock, DNM_DETECTOR_Z, 'VAL', 0)

send_put_msg(sock, DNM_DETECTOR_X, 'VAL', 5000)
print('sent Detector X 5000')


#for i in range(2):
#	pos_fbk = send_get_msg(sock, DNM_DETECTOR_Z, 'RBV')
#	print 'pos_fbk = %s' % pos_fbk
