'''
Created on May 9, 2012

@author: bergr
'''
import os
from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5 import uic

uiDir = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'ui')

class fbkClass(QtWidgets.QWidget):
	changed = QtCore.pyqtSignal(float)
	
	def __init__(self, pv, lblText, fbk_val=None, parent=None, engineering_notation=False):
		QtWidgets.QWidget.__init__(self,parent)
		uic.loadUi(uiDir + 'fbk.ui', self)
		self.pv = pv
		self.name = pv.get_name()
		self.pvNameFld.setText(lblText)
		pv.add_callback('setpoint', self._on_new_pv_data)
		self.pvdetail = None
		self.changed.connect(self.on_change)
		self.posFbkLbl.setToolTip(self.name)	
		self.use_eng_frmt = engineering_notation
		if(fbk_val is not None):
			self.on_change(fbk_val)	
	
# 	def check_calibd(self, cal):
# 		if(cal):
# 			clr =  QtGui.QColor(0,255,0) # (r,g,b)
# 		else:
# 			clr =  QtGui.QColor(255,0,0) # (r,g,b)
# 		self.calibdWgt.setStyleSheet("QWidget { background-color: %s }" % clr.name()) 
# 	
# 	def on_moving(self, is_moving):
# 		if(is_moving):
# 			clr =  QtGui.QColor(255,0,0) # (r,g,b)
# 		else:
# 			clr =  QtGui.QColor(240,240,240) # (r,g,b)
# 
# 		self.movingWgt.setStyleSheet("QWidget { background-color: %s }" % clr.name())
	
	def on_change(self, val):
		if(self.use_eng_frmt):
			self.posFbkLbl.setText("%.3e" % val )
		else:	
			self.posFbkLbl.setText('%.3f' % val)
		
	
	def _on_new_pv_data(self, **kwargs):
		#print 'on_new_data \n',arr	
		val = kwargs['value']
		self.changed.emit(val)
	
		
		
		

