'''
Created on Nov 2, 2015

@author: bergr
'''
'''
Created on Nov 2, 2015

@author: bergr
'''
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import time
import queue
import atexit


#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES
from cls.appWidgets.main_object import  POS_TYPE_BL, POS_TYPE_ES
from cls.applications.pyStxm.widgets.fbk import fbkClass
from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.utils.log import get_module_logger, log_to_qt

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


class DevsPanel(QtWidgets.QWidget):
	'''
	This is a widget that is given a list of dev's that MUST exist in the MAIN_OBJ dict and creates Qlabel and ca_aiLabel
	for each 
	
	:returns:  None
	'''
	def __init__(self, dev_dict, egu='', engineering_notation=False, main_obj=None, parent=None):
		super(DevsPanel, self).__init__(parent)
		self.main_obj = main_obj
		self.dev_dct = None
		self.dev_lst = None

		if(type(dev_dict) is list):
			self.dev_lst = dev_dict
		else:
			self.dev_dct = dev_dict

		self.exclude_list = [ ]
		
		self.fbk_enabled = False
		self.tm = None	
		self.tmlib = None
		
		self.vbox = QtWidgets.QVBoxLayout()
		self.vbox.setContentsMargins(0,0,0,0)
		self.vbox.setSpacing(0)
		
		self.setLayout(self.vbox)		
		self.dev_dict = {}

		if(self.dev_lst):
			#process as an ordered list
			for dev in self.dev_lst:
				dev_name = dev.get_name()
				if (dev_name in self.exclude_list):
					continue
				if(dev.is_connected()):
					fbk_val = dev.get_position()
					desc = dev.get_desc()
				else:
					fbk_val = -0.0
					desc = 'NOT_CONNECTED'
				dev_ui = fbkClass(dev, desc, fbk_val=fbk_val, engineering_notation=engineering_notation)
				dev_ui.unitsLbl.setText(egu)
				self.vbox.addWidget(dev_ui)

				self.dev_dict[dev_name] = (dev_name, dev_ui)  # , ca_Lbl)
		else:
			# process as a dict
			dev_keys = list(self.dev_dct.keys())
			dev_keys.sort()
			for dev_name in dev_keys:
				if(dev_name in self.exclude_list):
					continue

				dev = self.dev_dct[dev_name]
				#desc = dev.get_desc()
				#fbk_val = dev.get_position()
				if (dev_name in self.exclude_list):
					continue
				if(dev.is_connected()):
					fbk_val = dev.get_position()
					desc = dev.get_desc()
				else:
					fbk_val = -0.0
					desc = 'NOT_CONNECTED'

				dev_ui = fbkClass(dev, desc, fbk_val=fbk_val, engineering_notation=engineering_notation)
				dev_ui.unitsLbl.setText(egu)
				self.vbox.addWidget(dev_ui)

				self.dev_dict[dev_name] = ( dev_name, dev_ui)#, ca_Lbl)
			
		self.fbk_enabled = True
		#atexit.register(self.on_exit)
	
	def on_exit(self):
		#print 'on_exit'
		pass
		
def go():
	app = QtWidgets.QApplication(sys.argv)
	dev_obj = self.main_obj.get_device_obj()
	temps = dev_obj.get_all_temperatures(POS_TYPE_ES)
	window2 = DevsPanel(temps, egu='deg C')
	prssrs = dev_obj.get_all_pressures(POS_TYPE_ES)
	window3 = DevsPanel(prssrs, egu='torr', engineering_notation=True)
	window2.show()
	window3.show()
	app.exec_()
	
	
def profile_it():
	#determine_profile_bias_val()
	profile.Profile.bias = 9.95500362835e-07
	profile.run('go()', 'testprof.dat')
	p = pstats.Stats('testprof.dat')
	p.sort_stats('cumulative').print_stats(100)
	
		
if __name__ == '__main__':
	#import profile
	#import pstats
	#log_to_qt()
	app = QtWidgets.QApplication(sys.argv)
	dev_obj = MAIN_OBJ.get_device_obj()
	temps = dev_obj.get_all_temperatures(POS_TYPE_ES)
	window2 = DevsPanel(temps, egu='deg C')
	prssrs = dev_obj.get_all_pressures(POS_TYPE_ES)
	window3 = DevsPanel(prssrs, egu='torr', engineering_notation=True)
	window2.show()
	window3.show()
	app.exec_()
	#profile_it()
	
	#test()
	


	
	
	
	
	