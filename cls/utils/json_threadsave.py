'''
Created on 2014-10-06

@author: bergr
'''
import os
import datetime
import simplejson as json
import threading
import numpy as np
import types 

from cls.appWidgets.user_account.user_object import user_obj
from cls.utils.log import get_module_logger

from cls.data_utils.jsonEncoder import NumpyAwareJSONEncoder

_logger = get_module_logger(__name__)

def mime_to_dct(mimeData):
	"""
	the mime data is a json string that has been written to a mime datastream
	"""
	if mimeData.hasText():
		dct = json.loads(str(mimeData.text()))
		return(dct)
	else:
		return({})	 



def dict_to_json_string(dct, to_unicode=False):
	s = json.dumps(dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
	if(to_unicode):
		s = str(s)
	return(s)

def json_string_to_dct(jstr):
	dct = json.loads(jstr)#[0]
	return(dct)

class ThreadJsonSave(threading.Thread):
	"""Threaded file Save"""
	def __init__(self, data_dct, name='', verbose=False):
		threading.Thread.__init__(self, name=name)
		self.data_dct = data_dct
		self.name = 'JSON-SV.' + name
		self.verbose = verbose
		#print 'ThreadJsonSave: [%s] started' % self.name 
		
	def run(self):
		if self.data_dct != None:
			j=json.dumps(self.data_dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
			#fstr = self.data_dct['fpath'].replace('\\', '/')
			fstr = self.data_dct['fpath']
			f=open(fstr,'w')
			f.write(j)
			f.close()
			#_logger.info('ThreadJsonSave: [%s] saved [%s]' % (self.name, self.data_dct['fpath']))
			if(self.verbose):
				print('ThreadJsonSave: [%s] saved [%s]' % (self.name, self.data_dct['fpath']))
		
		#_logger.info('ThreadJsonSave: [%s] DONE' % self.name) 
		
def loadJson(filename):
	"""load json data from disk"""
	if os.path.exists(filename):
		js = json.loads(file(filename).read())
	else:
		print("json_ThreadSave: loadJson: file [%s] doesn't exist: No File Loaded" % filename)
		js = None
	return js	

def saveJson(filename, data_dct):
	if data_dct != None:
		j=json.dumps(data_dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
		f=open(filename,"w")
		f.write(j)
		f.close()	
		