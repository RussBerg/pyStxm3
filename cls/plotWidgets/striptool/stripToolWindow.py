# -*- coding:utf-8 -*-
"""
Created on 2011-03-09

@author: bergr

"""

import os
	
path_sep = ';'
epicsPath = r'C:\controls\epics\base-3-14-11\bin\win32-x86;C:\controls\epics\base-3-14-11\lib\win32-x86;C:\controls\py2.7\cls;C:\controls\py2.7\blctl'
path  = [os.environ['PATH']]
path.extend(epicsPath.split(';'))
os.environ['PATH'] = path_sep.join(path)  
os.environ['PYTHONPATH'] = path_sep.join(path)

from PyQt5 import QtGui, QtCore
from PyQt5 import uic

from guiqwt.builder import make
import guiqwt

from bcm.protocol import ca 
from cls.utils.log import get_module_logger, log_to_qt
from bcm.utils.cfgparser import ConfigClass
from bcm.qt4.curveWidget import CurveViewerWidget


#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

#read the ini file and load the default directories
appConfig = ConfigClass(r'./striptool.ini')
uiDir = appConfig.get_value('DEFAULT', 'uiDir')
dataDir = appConfig.get_value('DEFAULT', 'dataDir')
cfgDir = appConfig.get_value('DEFAULT', 'cfgDir')
pvList = appConfig.get_value('PV', 'pvList')
SLASH = appConfig.get_value('DEFAULT', 'dirslash')


from guidata.dataset.datatypes import DataSet
from guidata.dataset.dataitems import FloatItem, ColorItem


class gridDataSet(DataSet):
	"""
	Parameters
	<b>Striptool Parameters</b>
	"""
	#enable = BoolItem(u"Enable parameter set",
	#				  help=u"If disabled, the following parameters will be ignored",
	#				  default=False)
	#param0 = ChoiceItem(u"Param 0", ['choice #1', 'choice #2', 'choice #3'])
	timeSpan = FloatItem("Viewable Timespan (minutes)", default=3, min=0.6)
	updateInterval = FloatItem("Data Sample Interval (seconds)", default=1, min=0.1)
	bgColor = ColorItem("Background Color", default="black")
	gridColor = ColorItem("Grid Color", default="#515151")


#stripToolDataSet.set_defaults()

class MainWindow(QtWidgets.QMainWindow):
	"""
		This is a first crack at a striptool, the desired PV's are retrieved from
		a list given in the striptool.ini file under the PV section header, 
		when teh app starts the pv names are read from the ini file and then their
		values are posted at a rate of 1Hz, the window size is 300 seconds or 5 min,
		this can be adjusted 
		
		The main ui was created using qtDesigner and it is loaded in MainWindow
		such that MainWindow IS the ui file as a widget. The widgets used in the 
		ui file were named in the properties window of qtDesigner.
		 
	"""

	def __init__(self, parent=None):
		QtWidgets.QMainWindow.__init__(self, parent)
		
		self.log = log_to_qt()
		uic.loadUi(uiDir + SLASH + 'striptool.ui', self)
		
		self.gridparam = make.gridparam(background="black", 
								   minor_enabled=(False, False), 
								   major_enabled=(True,True))
		self.gridparam.maj_line.color = '#515151'
		self.gridparam.min_line.color = '#515151'
		self.scanplot = CurveViewerWidget(winTitleStr = "", options=dict(xlabel="", gridparam=self.gridparam))
		self.scanplot.regTools()
		self.updateInterval = 1.0
		self.timeSpan = 3 #minutes
		s = '%3.2f minute Window' % (self.timeSpan )
		
		self.scanplot.setPlotAxisStrs(xstr=s)
		
		self.gridDSet = gridDataSet()
		
		#self.scanplot.right_mouse_click.connect(self.on_rt_mouse)
		
		#connect our data saver handler to the scan plot "save As" tool
		self.scanplot.save_file.connect(self.on_save_data)
		self.handlers_connected = False
		self.ctrlrFbkPv = None
		
		self.scanTab.layout().addWidget(self.scanplot)
		
		self.total_points = 0
		self.data = []
		
		
		#connect the menu button action
		self.actionExit.triggered.connect(self.close)
		self.actionSettings.triggered.connect(self.edit_params)

		#the storage ring current
		self.ringCrntPv = ca.PV('PCT1402-01:mA:fbk')
		self.ringCrntPv.changed.connect(self.on_ringpv_changed)
		self.ringCurrent = 0
		
		self.bpmpvs = {}
		self.pvNames = self.get_pvList()
		self.create_pvs(self.pvNames)
		self.scanplot.set_time_window(self.pvNames, self.timeSpan * 60)
		
		self.ringCrntPv.changed.connect(self.on_ringpv_changed)
		
		self.timeIdx = -1
		
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.on_timer)
		self.timer.start(500)
		
		self.init = True
		
		
		#this logs time stamped messages to the log window at the bottom of the 
		#application
		_logger.info("Application started")
		
	def edit_params(self):
		self.gridDSet.edit()
		
		#reset timer
		self.timer.stop()
		self.updateInterval = self.gridDSet.updateInterval
		self.timeSpan = self.gridDSet.timeSpan
		self.scanplot.set_time_window(self.pvNames, self.timeSpan * 60)
		self.timer.start(self.gridDSet.updateInterval * 1000)
		s = '%3.2f minute Window' % (self.timeSpan )
		self.scanplot.setPlotAxisStrs(xstr=s)
		self.gridparam.maj_line.color = self.gridDSet.gridColor
		self.gridparam.min_line.color = self.gridDSet.gridColor
		self.gridparam.background = self.gridDSet.bgColor
		plot = self.scanplot.get_plot()
		items = plot.get_items()
		for item in items:
			if(isinstance(item, guiqwt.curve.GridItem)):
				item.gridparam = self.gridparam
				item.update_params()
				plot.replot()
				break
		

	def get_pvList(self):
		l1 = pvList.replace(' ','')
		list = l1.split(',')
		return(list)
	
	def on_timer(self):
		self.timeIdx += 1
		
		for name in self.pvNames:
			val = self.bpmpvs[name][1]
			#self.scanplot.addXPoint(name, self.timeIdx, update=False)
			self.scanplot.addXYPoint(name, self.timeIdx, val, update=True)
		
	
	def create_pvs(self, nameList):
		for name in nameList:
			self.scanplot.create_curve(name)
			# atuple (pv object, val)
			self.bpmpvs[name] = (ca.PV(name), 0)
			self.bpmpvs[name][0].changed.connect(self.on_bpmpv_changed)
			
		

	def on_bpmpv_changed(self, val):
		"""
			handler to update the ring current label when the PV changes
		"""
		name = self.sender()._name
		self.bpmpvs[name] = (self.bpmpvs[name][0], val)

	def on_save_data(self, filename):
		"""
		write self.data out to the specified filename and path
		"""
		#print 'on_save_data(%s) called ' % filename
		fout = open(filename, 'w')
		if(fout):
			l = '# SR Ring Current: %.2f mA\n' % self.ringCurrent
			fout.write(l)
			for l in self.data:
				fout.write(l)
				fout.write('\n')
			
			fout.close()
			_logger.critical("Data saved to: %s", filename)
		else:
			_logger.error("Error: unable to open file for write: %s", filename)
		

		
	def set_scanplot_axis_strs(self, dacq):
		"""
			set the plot axis strings for our cfg file
		"""
		plotStrs = self.dacq.acq_info.get_pv_names()
		title = dacq.acq_info.get_scan_name()
		self.currentScanName = title
		self.scanplot.setPlotAxisStrs(title, plotStrs[0], plotStrs[1])
		self.init_feedback_panel(plotStrs)  
	
	
	def init_feedback_panel(self, ctrlPvNames):
		"""
			There is a panel that shows the current scan motor position feedback
			so that the user can see what the motor is doing. 
			Use the one that is the motor (SMTR), but use the first by default
		"""
		name = ctrlPvNames[0]
		for nm in ctrlPvNames:
			if(nm.find('SMTR') > -1):
				name = nm
				
		if(self.ctrlrFbkPv != None):
			self.ctrlrFbkPv.changed.disconnect()
			
		self.ctrlrLbl.setText(name)
		self.ctrlrFbkPv = ca.PV(name)
		self.ctrlrFbkPv.changed.connect(self.on_ctrlFbkpv_changed)

	def on_ctrlFbkpv_changed(self, val):
		"""
			handler to update the Controlelr feedback label when the PV changes
		"""
		#print 'on_ringpv_changed: %f' % val
		s = '%.2f' % val
		self.ctrlrFbkFld.setText(s)
		 
		
			
	def on_ringpv_changed(self, val):
		"""
			handler to update the ring current label when the PV changes
		"""
		#print 'on_ringpv_changed: %f' % val
		self.ringCurrent = val
		s = '%.2f mA' % self.ringCurrent
		self.ringCurrentLbl.setText(s)

	
	def on_startup(self):
		"""
			Signal handler that is connected to the startup signal emitted
			by the acquisition module
		"""
		
		_logger.info("wireScanViewWidg: callback from acq start")
	 
	def on_status(self, sts):
		"""
			Signal handler that is connected to the status signal emitted
			by the acquisition module, it shows the current state of the scan
			Off, Run, Standby
		"""
		#print 'on_status: %s' %sts
		self.scanStateLbl.setText('Scan Status:[%s]' % sts)
		
	def add_to_log(self, clr, msg):
		"""
			This is a signal handler that is connected to the logger so that
			messages sent to the logger are  then displayed by this apps loggin 
			widget, color is supported for the varying levels of message logged
		"""
		pass
		#self.logTextEdit.setTextColor(clr)
		#self.logTextEdit.append(msg)
	
	

def runApp(mode):
	
	import sys
	
	ca.threads_init()
	app = QtWidgets.QApplication(sys.argv)
	win = MainWindow()
	win.show()
	app.exec_()

if __name__ == "__main__":
	
	#test file import
	runApp(0)



