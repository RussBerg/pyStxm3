'''
Created on 2013-10-03

@author: bergr
'''
from PyQt5 import QtCore

#from cls.applications.pyStxm.bl10ID01 import MasterLogger

def doprint(typ, msg):
	
	if(typ.find('warning') > -1):
		typeStr = 'WARNING: '
	elif(typ.find('debug') > -1):
		typeStr = 'DEBUG: ' 
	elif(typ.find('error') > -1):
		typeStr = 'ERROR: '
	else:
		typeStr = 'INFO: '
	
	s = typeStr + msg
	print(s)		
	#QtCore.QObject().emit(QtCore.SIGNAL('new_log(object)'))
	#QtCore.QObject().emit(QtCore.SIGNAL('new_log(PyQt_PyObject)'), s)
	#self.connect(self.button, SIGNAL('clicked()'), self.buttonClicked)
	

def thread_log(typ, msg):
	"""
	doprint should have been called this from the start, use this for any new
	logger calls from a thread
	"""
	if(typ.find('warning') > -1):
		typeStr = 'WARNING: '
	elif(typ.find('debug') > -1):
		typeStr = 'DEBUG: ' 
	elif(typ.find('error') > -1):
		typeStr = 'ERROR: '
	else:
		typeStr = 'INFO: '
	
	s = typeStr + msg
	print(s)		
	#QtCore.QObject().emit(QtCore.SIGNAL('new_log(object)'))
	QtCore.QObject().emit(QtCore.SIGNAL('new_log(PyQt_PyObject)'), s)
	#self.connect(self.button, SIGNAL('clicked()'), self.buttonClicked)

		
	


