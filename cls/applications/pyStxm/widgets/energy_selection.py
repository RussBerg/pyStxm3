'''
Created on 2013-06-18

@author: bergr
'''
'''
Created on 2013-05-29

@author: bergr
'''
import numpy as np

from PyQt5 import QtCore, QtGui 
from PyQt5 import uic
import PyQt4.Qwt5 as Qwt

from guiqwt.builder import make

from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.fileUtils import loadDatToXY, loadDatToArray, loadDatTo2DArray, readColumnStrs
from bcm.utils.cfgparser import ConfigClass
from bcm.utils.unique_id import uniqueshortid

from guiqwt.signals import (SIG_MARKER_CHANGED, SIG_PLOT_LABELS_CHANGED,
							SIG_ANNOTATION_CHANGED, SIG_AXIS_DIRECTION_CHANGED,
							SIG_ITEMS_CHANGED, SIG_ACTIVE_ITEM_CHANGED, SIG_ITEM_MOVED,
							SIG_LUT_CHANGED, SIG_ITEM_SELECTION_CHANGED, SIG_STOP_MOVING, 
							SIG_RANGE_CHANGED)

from sm.stxm_control.plotters.curveWidget import CurveViewerWidget
import sm.stxm_control.stxm_main_qrc

#try:
#	_fromUtf8 = QtCore.QString.fromUtf8
#except AttributeError:
_fromUtf8 = lambda s: s

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

class EnergySelector(CurveViewerWidget):
	new_range = QtCore.pyqtSignal(object, float, float, int)
	rng_changed = QtCore.pyqtSignal(object, float, float, int)
	
	def __init__(self,winTitleStr = "Energy Selector", toolbar = False, show_table=False, options = {}):
		super(EnergySelector, self).__init__(winTitleStr = winTitleStr, toolbar = toolbar, options = {})
		#self.ui = uic.loadUi(widgetsDir + SLASH + 'energySelect.ui')
		self.setMinimumSize(1300,1000)
		
		self.setPlotAxisStrs(xstr="eV", ystr=None)
		
		#self.regTools()
		self.addTool('HRangeTool')
		self.model = None
		#self.create_test_plot(200, 2000)
		
		self._default_rng_center = 395 
		self._default_rng_total = 0
		self._default_rng_npnts = 1
		
		self._rng_center = self._default_rng_center 
		self._rng_total = self._default_rng_total
		self._rng_npoints = self._default_rng_npnts

		#self.set_axis_font_size('left', 1)
		#self.set_axis_font_size('top', 4)
		
		self.region_name = 'None'
		self.scan_id = 0
		
		self.addRngBtn = QtWidgets.QToolButton()
		self.addRngBtn.setText(_fromUtf8(""))
		icon4 = QtGui.QIcon()
		
		icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/guiqwt/icons/images/xrange.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/guiqwt/icons/images/xrange.png")), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.addRngBtn.setIcon(icon4)
		self.addRngBtn.setIconSize(QtCore.QSize(16, 16))
		self.addRngBtn.setAutoRaise(True)
		self.addRngBtn.setObjectName(_fromUtf8("newRangeButton"))
		self.addRngBtn.setToolTip(_fromUtf8("add energy range"))
		self.addRngBtn.clicked.connect(self.on_btn_new_range)
		
		self.create_base_line(0, 2500)
		
		self.centerEdit = QtWidgets.QLineEdit()
		self.rangeEdit = QtWidgets.QLineEdit()
		self.npointsEdit = QtWidgets.QLineEdit()

		self.centerEdit.setValidator(QtGui.QDoubleValidator(100.0, 2500.0, 3, self))
		self.rangeEdit.setValidator(QtGui.QDoubleValidator(100.0, 2500.0, 3, self))
		self.npointsEdit.setValidator(QtGui.QIntValidator(1, 1000, self))

		self.centerEdit.returnPressed.connect(self.on_start_changed)
		self.rangeEdit.returnPressed.connect(self.on_stop_changed)
		self.npointsEdit.returnPressed.connect(self.on_npoints_changed)
		
		self.energy_id = 0
		self.cur_range_item = None
		
		spacer = QtWidgets.QSpacerItem(5000,100,QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)

		self.startLbl = QtWidgets.QLabel('Start:')
		self.stopLbl = QtWidgets.QLabel('Stop:')
		self.npointsLbl = QtWidgets.QLabel('#Points:')
		
		self.startLbl.setBuddy(self.centerEdit)
		self.stopLbl.setBuddy(self.rangeEdit)
		self.npointsLbl.setBuddy(self.npointsEdit)
		
		self.scanEvTable = EnergyScanTableView()
		self.scanEvTable.range_changed.connect(self.on_model_changed)
		
		vlayout = self.layout()
		
		if(show_table):
			vlayout.addWidget(self.scanEvTable)
			self.setMinimumSize(100,200)
			self.setMinimumHeight(200)
			self.setMaximumHeight(400)
			self.scanEvTable.setMinimumHeight(400)
		else:
			self.setMinimumSize(100,150)
			self.setMinimumHeight(150)
			self.setMaximumHeight(150)
			hlayout2 = QtWidgets.QHBoxLayout()
			hlayout2.addWidget(self.startLbl)
			hlayout2.addWidget(self.startEdit)
			
			hlayout2.addWidget(self.stopLbl)
			hlayout2.addWidget(self.stopEdit)
			hlayout2.addItem(spacer)
			hlayout2.addWidget(self.stepsLbl)
			hlayout2.addWidget(self.stepsEdit)
			#vlayout.addLayout(hlayout1)
			vlayout.addLayout(hlayout2)
			#vlayout.addWidget(self.tableView)
		
	def get_range_id(self):
		return(self.energy_id)
	
	def set_range_id(self, energy_id):
		self.energy_id = energy_id
	
	def get_center(self):
		return(self._rng_center)
	
	def get_range(self):
		return(self._rng_total)
	
	def get_npoints(self):
		return(self._rng_npoints)
	
	def on_btn_new_range(self):
		self.create_new_range(self._rng_center, self._rng_total)
	
	def create_new_range(self, center=None, rng=None, dosignal=True):
		if(center is None):
			center = self._default_rng_center
		if(rng is None): 
			rng = self._default_rng_total
		
		if(self.cur_range_item is not None):
			self.delPlotItem(self.cur_range_item, replot=True)
		
		self._rng_center = center
		self._rng_total = rng
		self._rng_npoints = self._default_rng_npnts

		self.cur_range_item = make.range(center - (0.5*rng), center + (0.5*rng))
		self.energy_id = uniqueshortid()
		self.update_edit_widgets()
		if(dosignal):
			self.new_range.emit(self.energy_id, self._rng_center, self._rng_total, self._rng_npoints)
		self.update_curve()
		return(self.energy_id)
	
	def on_start_changed(self):
		if(self.cur_range_item is not None):
			edt = self.sender()
			self._rng_center, ok = edt.text().toFloat()
			#print 'start changed to %f eV' % (self._rng_center)  
			self.modify_range(self._rng_center, self._rng_total, dosignal=True)
	
	def on_stop_changed(self):
		if(self.cur_range_item is not None):
			edt = self.sender()
			self._rng_total, ok = edt.text().toFloat()
			#print 'stop changed to %f eV ' % (self._rng_total)
			self.modify_range(self._rng_center, self._rng_total, dosignal=True)
		
	def on_npoints_changed(self):
		if(self.cur_range_item is not None):
			edt = self.sender()
			val, ok = edt.text().toInt()
			self._rng_npoints = val
			#print 'steps changed to %d ' % (val)
			self.modify_range(self._rng_center, self._rng_total, dosignal=True)
		
		  
	def modify_range(self, center, rng, npoints, dosignal=True, doZoom=False):
		#print 'modify_range(%.2f, %.2f)' % (center, rng)
		self._rng_center = center
		self._rng_total = rng
		self._rng_npoints = npoints
		self.update_plot(center, rng)
		if(doZoom):
			self.zoom_to_range()
			
		if(dosignal):
			self.rng_changed.emit(self.energy_id, center, rng, npoints)
		
	
	def zoom_to_range(self):
		_delta = self._rng_total
		_pad = _delta*0.05
		
		_min = self._rng_center - (0.5 * self._rng_total)
		_max = self._rng_center + (0.5 * self._rng_total)
		
		x = np.linspace(_min - _pad, _max + _pad)
		y = np.zeros(len(x))
		self.setXYData('bckgrnd', x, y, update=False)
		self.set_autoscale()
	
	def range_changed(self, regionWidget, rng):
		p1, p2 = regionWidget.get_range()
		# not sure if teh handle the wdiget grabbed was the max or min
		if(p1 > p2):
			max = p1
			min = p2
		else:
			max = p2
			min = p1
		self._rng_center = (max + min)/2.0
		self._rng_total = max - min
		print('range changed: %s: %f, %f' % (self.energy_id, self._rng_center, self._rng_total))
		self.update_edit_widgets()
		#self.mapper.submit()
		self.rng_changed.emit(self.energy_id, self._rng_center, self._rng_total, self._rng_npoints)

	def update_edit_widgets(self):
		self.centerEdit.setText('%.2f' % self._rng_center)
		self.rangeEdit.setText('%.2f' % self._rng_total)
		self.npointsEdit.setText('%.d' % self._rng_npoints)
		
	def create_test_plot(self, start, stop):
		x = np.linspace(start, stop)
		y = np.sin(np.sin(np.sin(x)))
		self.create_curve('bckgrnd',x, y)
	
	def create_base_line(self, start, stop):
		x = np.linspace(start, stop)
		y = np.zeros(len(x))
		#self.create_curve('bckgrnd',x, y,selectable=False)
		self.create_curve('bckgrnd',x, y)
	
	
	def on_stop_editingFinished(self):
		edit = self.sender()
		#self.model.
	
	def update_plot(self, center, rng):
		if(self.cur_range_item is not None):
			self._rng_center = center
			self._rng_total = rng
			#mofify the visual of the range for the new values
			_min = center - (0.5 * rng)
			_max = center + (0.5 * rng)
			self.adjust_range(_min, _max)

	
	def setupModel(self):
		self.model = QtWidgets.QStandardItemModel(1, len(self.hdrList), self)
		row = 0
		scanstart = ("15.53")
		scanstop = ("45.53")
		scanstep = ("10")
		
		item = QtWidgets.QStandardItem(scanstart)
		self.model.setItem(row, 0, item)
		item = QtWidgets.QStandardItem(scanstop)
		self.model.setItem(row, 1, item)
		item = QtWidgets.QStandardItem(scanstep)
		self.model.setItem(row, 2, item)
		
		#without this the mapping doesn't work
		self.mapper.toFirst()
	
	def mouseReleaseEvent(self, ev):
		#print 'StxmImageWidget: mouse released'
		if ev.button() == QtCore.Qt.MiddleButton:
			self.zoom_to_range()


if __name__ == "__main__":

	import sys

	def my_new_range(id, center, rng, step):
		print('new range! [%d] = %.2f,%.2f step = %d' % (id, center, rng, step))
		
	def my_range_changed(id, center, rng, step):
		print('range changed[%d] = %.2f,%.2f step = %d' % (id, center, rng, step))
	   

	app = QtWidgets.QApplication(sys.argv)

	win = EnergySelector(show_table=True)
	win.new_range.connect(my_new_range)
	win.rng_changed.connect(my_range_changed)
	
	win.show()
	
	sys.exit(app.exec_())
	#print "all done"
		