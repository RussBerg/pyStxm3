'''
Created on Nov 2, 2015

@author: bergr
'''
'''
Created on Nov 2, 2015

@author: bergr
'''
'''
Created on 2014-07-15

@author: bergr
'''
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import time
import queue
import atexit

from cls.applications.bioXasIM.widgets.fbk import fbkClass
from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES 

from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.utils.log import get_module_logger, log_to_qt

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


class PVsPanel(QtWidgets.QWidget):
	'''
	This is a widget that is given a list of pv's that MUST exist in the MAIN_OBJ dict and creates Qlabel and ca_aiLabel
	for each 
	
	:returns:  None
	'''
	def __init__(self, pv_dict, egu='', engineering_notation=False):
		super(PVsPanel, self).__init__()
		
		self.pv_dct = pv_dict
		self.exclude_list = [ ]
		
		self.fbk_enabled = False
		self.tm = None	
		self.tmlib = None
		
		self.vbox = QtWidgets.QVBoxLayout()
		self.vbox.setContentsMargins(0,0,0,0)
		self.vbox.setSpacing(0)
		
		self.setLayout(self.vbox)		
		self.pv_dict = {}

		pv_keys = list(self.pv_dct.keys())
		pv_keys.sort()
		for pv_name in pv_keys:
			if(pv_name in self.exclude_list):
				continue
			
			pv = self.pv_dct[pv_name]
			fbk_val = pv.get_position()
			pv_ui = fbkClass(pv, pv.DESC, fbk_val=fbk_val, engineering_notation=engineering_notation)
			pv_ui.unitsLbl.setText(egu)
			self.vbox.addWidget(pv_ui)
			
			self.pv_dict[pv_name] = ( pv_name, pv_ui)#, ca_Lbl)
			
		self.fbk_enabled = True
		atexit.register(self.on_exit)
	
	def on_exit(self):
		#print 'on_exit'
		pass
		
def go():
	app = QtWidgets.QApplication(sys.argv)
	dev_obj = MAIN_OBJ.get_device_obj()
	temps = dev_obj.get_all_temperatures(POS_TYPE_ES)
	window2 = PVsPanel(temps, egu='deg C')
	prssrs = dev_obj.get_all_pressures(POS_TYPE_ES)
	window3 = PVsPanel(prssrs, egu='torr', engineering_notation=True)
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
	log_to_qt()
	go()
	#profile_it()
	
	#test()
	


	
	
	
	
	