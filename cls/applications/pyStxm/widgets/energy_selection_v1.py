'''
Created on 2013-05-29

@author: bergr
'''
import numpy as np

from PyQt5 import QtGui, QtCore
from PyQt5 import uic
import PyQt4.Qwt5 as Qwt

from guiqwt.builder import make

from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.fileUtils import loadDatToXY, loadDatToArray, loadDatTo2DArray, readColumnStrs
from bcm.utils.cfgparser import ConfigClass

from guiqwt.signals import (SIG_MARKER_CHANGED, SIG_PLOT_LABELS_CHANGED,
							SIG_ANNOTATION_CHANGED, SIG_AXIS_DIRECTION_CHANGED,
							SIG_ITEMS_CHANGED, SIG_ACTIVE_ITEM_CHANGED, SIG_ITEM_MOVED,
							SIG_LUT_CHANGED, SIG_ITEM_SELECTION_CHANGED, SIG_STOP_MOVING, 
							SIG_RANGE_CHANGED)

from cls.scanning.ScanDef import BaseScanDef
from cls.scanning.ScanTableView import EnergyScanTableView
from sm.stxm_control.plotters.curveWidget import CurveViewerWidget

import sm.stxm_control.stxm_main_qrc

#try:
#	_fromUtf8 = QtCore.QString.fromUtf8
#except AttributeError:
_fromUtf8 = lambda s: s

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

#appConfig = ConfigClass(r'../stxmMain.ini')
#widgetsDir = appConfig.get_value('DEFAULT', 'widgetsDir')
#imagesDir = appConfig.get_value('DEFAULT', 'imagesDir')
#SLASH = appConfig.get_value('DEFAULT', 'dirslash')




class EnergySelector(CurveViewerWidget):
	new_range = QtCore.pyqtSignal(object, float, float)
	
	def __init__(self,winTitleStr = "Energy Selector", toolbar = False, show_table=False, options = {}):
		super(EnergySelector, self).__init__(winTitleStr = winTitleStr, toolbar = toolbar, options = {})
		#self.ui = uic.loadUi(widgetsDir + SLASH + 'energySelect.ui')
		self.setMinimumSize(1300,1000)
		
		#self.setPlotAxisStrs(title=None, xstr="eV", ystr=None)
		
		#self.regTools()
		self.addTool('HRangeTool')
		self.model = None
		#self.create_test_plot(200, 2000)
		self._rng_min = 200 
		self._rng_max = 2000

#		self.create_base_line(0, self._rng_max+200)
#		self.create_range(self._rng_min, self._rng_max)
		#self.create_test_plot()
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
		self.addRngBtn.setObjectName(_fromUtf8("forwardButton"))
		self.addRngBtn.clicked.connect(self.on_new_range)
		
		
		
		#selEnLbl = QtWidgets.QLabel('Selecting Energy for: ')
		#self.curRegionLbl = QtWidgets.QLabel('None')
		self.scanEvTable = EnergyScanTableView()
		self.scanEvTable.range_changed.connect(self.on_model_changed)
		self.startEdit = QtWidgets.QLineEdit()
		self.stopEdit = QtWidgets.QLineEdit()
		self.stepsEdit = QtWidgets.QLineEdit()
		#stopEdit.textEdited.connect(self.on_stop_edited)
		self.startEdit.returnPressed.connect(self.on_start_changed)
		self.stopEdit.returnPressed.connect(self.on_stop_changed)
		self.stepsEdit.returnPressed.connect(self.on_steps_changed)
		
		self.cur_energy_id = 0
		self.cur_scan_id = 0
		
		
		# Set up the mapper.
#		self.setupModel()
#		self.hdrList = ['Name','Start', 'Stop', 'Step', 'Points', 'Dwell', 'Pol1', 'Pol2', 'Off1', 'Off2', 'XMCD']
#		self.mapper = QtWidgets.QDataWidgetMapper(self)
#		self.mapper.setModel(self.model)
#		self.mapper.addMapping(self.startEdit, 0)
#		self.mapper.addMapping(self.stopEdit, 1)
#		self.mapper.addMapping(self.stepsEdit, 2)
		
		self.tableView = QtWidgets.QTableView()
		self.tableView.setModel(self.model)
		self.tableView.setColumnWidth(0,100)
		self.tableView.setColumnWidth(1,100)
		self.tableView.setColumnWidth(2,100)
		#self.tableView.resizeColumnsToContents()
		self.tableView.setWindowTitle("my view")
		
		
		spacer = QtWidgets.QSpacerItem(5000,100,QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
		self.selPeriodicTableBtn = QtWidgets.QToolButton()

		self.startLbl = QtWidgets.QLabel('Start:')
		self.stopLbl = QtWidgets.QLabel('Stop:')
		self.stepsLbl = QtWidgets.QLabel('Steps:')
		
		self.startLbl.setBuddy(self.startEdit)
		self.stopLbl.setBuddy(self.stopEdit)
		self.stepsLbl.setBuddy(self.stepsEdit)
		
		vlayout = self.layout()
#		vlayout.setContentsMargins(QtCore.QMargins(2,2,2,2))
		vlayout.addWidget(self.addRngBtn)
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
		
	def on_new_range(self):
		self.create_base_line(0, self._rng_max+200)
		rng_item = make.range(self._rng_min, self._rng_max)
		self.plot.add_item(rng_item)
		#self.create_range(self._rng_min, self._rng_max)
		#scan = BaseScanDef(self._rng_min,self._rng_max,0,10)
		#self.add_energy(scan)
		self.update_curve()
		
	def on_start_changed(self):
		edt = self.sender()
		self._rng_min, ok = edt.text().toFloat()
		print('start changed to %f eV' % (self._rng_min))  
		self.modify_range(self._rng_min, self._rng_max, dosignal=False)
	
	def on_stop_changed(self):
		edt = self.sender()
		self._rng_max, ok = edt.text().toFloat()
		print('stop changed to %f eV ' % (self._rng_max))
		self.modify_range(self._rng_min, self._rng_max, dosignal=False)
		
	def on_steps_changed(self):
		edt = self.sender()
		val, ok = edt.text().toInt()
		print('steps changed to %d ' % (val))
		

	def set_region_name(self, region_name):
		self.region_name = region_name
	
	def set_cur_scan_id(self, scan_id):
		self.cur_scan_id = scan_id

	
	def on_model_changed(self, row, scan):
		ev_scandef = scan.get_ev_regions()[row]			 
#		self._rng_min = ev_scandef.get_start()
#		self._rng_max = ev_scandef.get_stop()
#		#mofify the visual of the range for the new values
#		self.adjust_range(self._rng_min, self._rng_max)
		self.update_plot(ev_scandef)
		   
	def modify_range(self, scan_id, scan, dosignal=False):
		#print 'modify_range(%.2f, %.2f)' % (_min, _max)
		self.update_plot(scan)
#		self._rng_min = scan.get_start()
#		self._rng_max = scan.get_stop()
#		#mofify the visual of the range for the new values
#		self.adjust_range(self._rng_min, self._rng_max, dosignal)
		#change the model
		self.scanEvTable.modify_data(scan.scan_id, scan)
		
	
	def zoom_to_range(self):
		x = np.linspace(self._rng_min-20, self._rng_max+20)
		y = np.zeros(len(x))
		self.setXYData('bckgrnd', x, y, update=False)
		self.set_autoscale()
	
	def range_changed(self, rng, _min, _max):
		print('range changed: %s: %f, %f' % (self.region_name, _min, _max))
		self._rng_min = _min
		self._rng_max = _max
		self.startEdit.setText('%.2f' % self._rng_min)
		self.stopEdit.setText('%.2f' % self._rng_max)
		#self.mapper.submit()
		self.new_range.emit(self.region_name, self._rng_min, self._rng_max)
		
	

	 
	def create_test_plot(self, start, stop):
		x = np.linspace(start, stop)
		y = np.sin(np.sin(np.sin(x)))
		self.create_curve('bckgrnd',x, y)
	
	def create_base_line(self, start, stop):
		x = np.linspace(start, stop)
		y = np.zeros(len(x))
		self.create_curve('bckgrnd',x, y)
	
#		def on_stop_edited(self, qstr):
#		valstr = str(qstr)
#		edit = self.sender()
#		print '[%s] edited = %s' % (edit.toolTip(), valstr)
#		print 'current row in model is %d' % self.mapper.currentIndex()
	
	def on_stop_editingFinished(self):
		edit = self.sender()
		#self.model.
	
	def add_energy(self, scan):
		self.set_region_name = 'EV%d' % self.cur_energy_id
		scan.set_scan_name(self.set_region_name)
		self.scanEvTable.add_scan(self.cur_energy_id, scan)
		self.update_plot(scan)
		self.cur_energy_id += 1
		
	def update_plot(self, scan):
		self._rng_min = scan.get_start()
		self._rng_max = scan.get_stop()
		#mofify the visual of the range for the new values
		self.adjust_range(self._rng_min, self._rng_max)

	
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
 

if __name__ == "__main__":

	import sys

	def on_new_range(rng, min, max):
		#print 'range = %.2f,%.2f' % (min,max)
		pass

	app = QtWidgets.QApplication(sys.argv)

	win = EnergySelector(show_table=True)
	
	win.new_range.connect(on_new_range)
	
	win.show()
	
	sys.exit(app.exec_())
	#print "all done"
		