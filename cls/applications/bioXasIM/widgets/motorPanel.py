'''
Created on 2014-07-15

@author: bergr
'''
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import time
import queue
import atexit

from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES 
from cls.applications.bioXasIM.widgets.spfbk_small import Ui_Form as spfbk_small

from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.utils.log import get_module_logger, log_to_qt

#motor internal status
NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
TIMEOUT, TIMEOUT_BUTDONE			  =  -8,  -7
UNKNOWN_ERROR						 =  -5
DONEW_SOFTLIM, DONEW_HARDLIM		  =  -4, -3
DONE_OK							   =   0
MOVE_BEGUN, MOVE_BEGUN_CONFIRMED	  =   0, 1
NOWAIT_SOFTLIM, NOWAIT_HARDLIM		=   4, 3


#_fbk_not_moving = "background-color: rgb(130,130,130); border: 1px solid gray;"
_fbk_not_moving = master_colors['app_blue']

#_fbk_moving = "background-color: rgb(240, 88, 33);"
_fbk_moving = "rgb(254, 233, 0);"
# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


class PositionersPanel(QtWidgets.QWidget):
	'''
	This is a widget that takes from the arg 'positioner_set' the positioners to filter from the 
	master device list in the main object. This allows this Panel to present a panel of Endstation or Beamline
	positioners depending.
	positioner_set='endstation'
	:param positioner_set: a string that is used to decide which positioners to include on the panel. Supported
			options are:
				'endstation'
				'beamline'
		
	:type string:  
	
	:returns:  None
	'''
	def __init__(self, positioner_set='ES', exclude_list=[]):
		super(PositionersPanel, self).__init__()
		
		
		#self.exclude_list = ['_ZonePlateZ_base', 'SampleFineX', 'SampleFineY', 'CoarseX.X', 'CoarseY.Y', 'AUX1','AUX2','Cff','PeemM3Trans']
		self.exclude_list = exclude_list
		#self.bl_list = ['EPUPolarization', 'EPUGap', 'SlitY', 'SlitX', 'EPUOffset', 'EPUHarmonic', 'EPUFollowing', \
		#			'Branch', 'Grating', 'Cff', 'AUX1', 'AUX2','MonoTrans', 'PeemM3Trans', 'M3STXMPitch']		
		
		self.enum_list = ['EPUPolarization', 'EPUHarmonic', 'Branch' ]
		
		self.fbk_enabled = False
		self.positioner_set = positioner_set
		self.mtr = None	
		self.mtrlib = None
		
		self.vbox = QtWidgets.QVBoxLayout()
		self.vbox.setContentsMargins(0,0,0,0)
		self.vbox.setSpacing(0)
		
		self.styleBtn = QtWidgets.QPushButton('Update Style')
		self.styleBtn.clicked.connect(self.on_update_style)
		
		#self.vbox.addWidget(self.styleBtn)
		self.updateQueue = queue.Queue()
		
		self.updateTimer = QtCore.QTimer()
		self.updateTimer.timeout.connect(self.update_widgets)
		
		
		self.setLayout(self.vbox)		
		self.mtr_dict = {}
		#self.qssheet = get_style('dark')
		#self.setStyleSheet(self.qssheet)
		
		devs = MAIN_OBJ.get_devices()
		#DEVICE_CFG.get_device_list()
		pos_keys = list(devs['POSITIONERS'].keys())
		pos_keys.sort()
		for dev in pos_keys:
			#print dev
			if(dev in self.exclude_list):
				continue
			
			usethis = False
			mtr = MAIN_OBJ.device(dev)
			if(self.positioner_set.find(POS_TYPE_BL) > -1):
				if(mtr._pos_set == POS_TYPE_BL):
					usethis = True
			
			if(self.positioner_set.find(POS_TYPE_ES) > -1):
				if(mtr._pos_set == POS_TYPE_ES):
					usethis = True
			
			if(usethis):
				#if(dev in self.enum_list):
				#	cbox = ca_mbbiComboBoxWidget(mtr.get_name(), hdrText='Mode')
				#	self.vbox.addWidget(cbox)
				#else:	
				#_logger.debug('uic.loadUi [%s]' % dev)
				#dev_ui = uic.loadUi(r'C:\controls\py2.7\Beamlines\sm\stxm_control\widgets\ui\spfbk_small.ui')
				widg = QtWidgets.QWidget()
				dev_ui = spfbk_small()
				dev_ui.setupUi(widg)
				
				#dev_ui.setPosFld.installEventFilter(Filter())
				#mtr = MAIN_OBJ.device(dev)
				self.mtr_dict[mtr.get_name()] = ( dev, dev_ui, widg,  mtr)
				self.connect_motor_widgets(dev, dev_ui, widg, mtr)
				#_logger.debug('DONE uic.loadUi [%s]' % dev)
				#print 'positioner: [%s] pvname [%s]' % (dev, mtr.get_name())
		self.updateTimer.start(100)
		self.fbk_enabled = True
		#self.loadMotorConfig(positioner)
		atexit.register(self.on_exit)
	
	def on_exit(self):
		#print 'on_exit'
		pass
		
			
	def on_update_style(self):
		""" handler for interactive button """
		self.qssheet = get_style('dark')
		self.setStyleSheet(self.qssheet)
				
	def connect_motor_widgets(self, name, mtr_ui, widg, mtr):
		_logger.debug('connect_motor_widgets[%s]' % name)
		#connect btn handlers
		#hlm = mtr.get_high_limit()
		#llm = mtr.get_low_limit()
		desc = mtr.get('description')
		pv_name = mtr.get_name()
		#ma_str = 'move absolute between %.2f and %.2f' % (llm, hlm)
		mtr_ui.stopBtn.clicked.connect(self.stop)
		mtr_ui.detailsBtn.clicked.connect(self.on_details)
		mtr_ui.setPosFld.returnPressed.connect(self.on_return_pressed)	
		#mtr_ui.setPosFld.editingFinished.connect(self.on_editing_finished)
		
		#mtr_ui.setPosFld.setToolTip(ma_str)
		
		mtr_ui.setPosFld.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		mtr_ui.setPosFld.customContextMenuRequested.connect(self.contextMenuEvent)
		
		mtr_ui.mtrNameFld.setText(name)
		mtr_ui.mtrNameFld.setToolTip(desc)
		mtr_ui.setPosFld.setStatusTip(pv_name)
		mtr_ui.stopBtn.setStatusTip(pv_name)
		mtr_ui.detailsBtn.setStatusTip(pv_name)
		
		#_logger.debug('adding callbacks DMOV,RBV for [%s]' % name)
		#if(hasattr(mtr, 'add_callback')):
		#_logger.debug('add_callback(DMOV [%s]' % name)
		mtr.add_callback('done_moving', self.updateMoving)
		#_logger.debug('add_callback(RBV [%s]' % name)
		mtr.add_callback('RBV', self.updateFbk)
		#_logger.debug('get_position() [%s]' % name)
		
		#_logger.debug('getting RBV,EGU for [%s]' % name)
		fbk = mtr.get_position()
		#_logger.debug('add_callback(EGU [%s]' % name)
		units = str(mtr.get('EGU'))
		#_logger.debug('done connecting [%s]' % name)
		s = '%6.3f' % fbk
		mtr_ui.posFbkLbl.setText(s)
		mtr_ui.unitsLbl.setText(units)
			
		#elif(hasattr(mtr, 'changed')):
		#	#print 'Standard PV: unsupported positioner [%s]' % name
		#	pass
		#else:
		#	print 'unsupported positioner [%s]' % name
		
		self.vbox.addWidget(widg)
		#_logger.debug('Done[%s] \n\n' % name)
	
	def on_editing_finished(self):
		print('on_editing_finished')	
	
	def update_widgets(self):
		call_task_done = False
		while not self.updateQueue.empty():
			resp = self.updateQueue.get()
			if('setStyleSheet' in list(resp.keys())):
				for ss in resp['setStyleSheet']:
					widget = ss[0]
					clr_str = ss[1]
					#print 'update_widgets: setStyleSheet(%s)' % clr_str
					widget.setStyleSheet(clr_str)
					call_task_done = True
			
			if('setText' in list(resp.keys())):
				widget = resp['setText'][0]
				_str = resp['setText'][1]
				#print 'update_widgets: setText(%s)' % _str
				widget.setText(_str)
				call_task_done = True
				
		if(call_task_done):
			self.updateQueue.task_done() 
		
		
	def stop(self):
		fld = self.sender()
		pvname = str(fld.statusTip())
		(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
		mtr.stop()

	def updateMoving(self, **kwargs):
		""" do not try to set a widget property here as
		it will eventually scew up teh main GUI thread
		Hence the use of a Queue and QTimer
		"""
		pvname =  kwargs['pvname'].split('.')[0]
		(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
		val = float(kwargs['value'])
		txt_clr = "color: black;"
		#this is for the DMOV or DONE Moving, I want Moving so invert logic
		if(val):
			clr_str = _fbk_not_moving
			#txt_clr = "color: black;"
		else:
			clr_str = _fbk_moving
			#txt_clr = "color: white;"
		
		_dct = {}
		_dct['setStyleSheet'] = [(dev_ui.mtrNameFld, "background-color: " + clr_str), (dev_ui.posFbkLbl, txt_clr)]
		self.updateQueue.put_nowait(_dct)
		
		 
	
	def updateFbk(self, **kwargs):
		""" do not try to set a widget property here as
		it will eventually scew up teh main GUI thread
		Hence the use of a Queue and QTimer
		"""
		if(self.fbk_enabled is True):
			pvname =  kwargs['pvname'].split('.')[0]
			(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
			val = float(kwargs['value'])
			s = '%6.3f' % val
			_dct = {}
			_dct['setText'] = (dev_ui.posFbkLbl, s)
			self.updateQueue.put_nowait(_dct) 
	
	def on_return_pressed(self):
		fld = self.sender()
		pvname = str(fld.statusTip())
		(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
		pos = float(str(self.sender().text()))
		sts = mtr.move(pos)
		
		if(sts == OUTSIDE_LIMITS):
			#outside the limits
			clr_str = "yellow;"
		else:
			clr_str = "white;"
		
		_dct = {}
		_dct['setStyleSheet'] = [(dev_ui.setPosFld, "background-color: " + clr_str)]
		self.updateQueue.put_nowait(_dct)
	
	def check_soft_limits(self, mtr, sp):
		lvio = mtr.get('LVIO')
		if(lvio == 0):
			return(True)
		else:
			return(False)
		
	def contextMenuEvent(self, event):
		fld = self.sender()
		if(fld):
			pvname = str(fld.statusTip())
			(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
			
			#self._pvs['VAL'].connected
			if(mtr._pvs['VAL'].connected):
				hlm = mtr.get_high_limit()
				llm = mtr.get_low_limit()
				
				if((llm is not None) and (hlm is not None)):
					ma_str = 'move %s absolute between %.2f and %.2f' % (dev, llm, hlm)
			else:
				ma_str = 'Motor %s not connected' % (dev)
				
			self.menu = QtWidgets.QMenu(self)
			renameAction = QtWidgets.QAction(ma_str, self)
			renameAction.triggered.connect(self.renameSlot)
			self.menu.addAction(renameAction)
			# add other required actions
			self.menu.popup(QtGui.QCursor.pos())
		

	def renameSlot(self):
		print("renaming slot called")
		# get the selected cell and perform renaming	
	
	
	def on_details(self):
		fld = self.sender()
		pvname = str(fld.statusTip())
		(dev, dev_ui, widg,  mtr) = self.mtr_dict[pvname]
		#dev_ui = uic.loadUi(r'C:\controls\py2.7\Beamlines\sm\stxm_control\widgets\ui\spfbk_detail.ui')
		detForm = PositionerDetail(dev, dev_ui, mtr)
		detForm.exec_()
		
		

class PositionerDetail(QtWidgets.QDialog):
	'''
	classdocs
	'''
	def __init__(self, positioner, dev_ui, mtr):
		super(PositionerDetail, self).__init__()
		uic.loadUi(r'C:\controls\py2.7\Beamlines\sm\stxm_control\widgets\ui\spfbk_detail.ui', self)
		self.mtr = mtr
		self.positioner = positioner
		self.dev_ui = dev_ui	
		#load the Motor.cfg file
		
		#connect btn handlers
		self.stopBtn.clicked.connect(self.on_stop_btn)
		self.calBtn.clicked.connect(self.calibrate)
		self.goHomeBtn.clicked.connect(self.on_home_btn)
		self.forceCalibratedBtn.clicked.connect(self.on_force_calibrated)
		self.zeroMtrBtn.clicked.connect(self.on_zero_motor)
		self.onOffBtn.clicked.connect(self.on)
		self.mtrGrpBox.clicked.connect(self.on_enable)
		self.domovesBtn.clicked.connect(self.do_moves)
				
		self.relSetpointFld.returnPressed.connect(self.on_move_rel_position)
		self.setpointFld.returnPressed.connect(self.on_move_to_position)
		self.setPosFld.returnPressed.connect(self.on_set_position)
		self.velFld.returnPressed.connect(self.on_set_velo)
		
		
				
	def loadMotorConfig(self, positioner='AbsSampleX'):
		positioner = str(positioner)
		
		if(self.mtr != None):
			self.mtr.changed.disconnect()
			self.mtr.status.disconnect()
			del(self.mtr)
			self.mtr = None
		self.mtrNameFld.setText(positioner)
		self.unitsLbl.setText(self.units)
		self.mtr = self.devices[positioner]
		self.loadParamsToGui(self.mtr)
		#self.mtr.changed.connect(self.updateFbk)
		
		self.mtr.changed.connect(self.on_change)
		self.mtr.calib_changed.connect(self.check_calibd)
		self.mtr.status.connect(self.on_status)
		self.mtr.moving.connect(self.on_moving)
		self.mtr.log_msg.connect(self.on_log_msg)
		
		self.moveThread = QtCore.QThread()
		self.scanObj = scanThread(self.mtr)
		self.scanObj.moveToThread(self.moveThread)
		self.scanObj.done.connect(self.on_scan_done)
		self.moveThread.started.connect(self.scanObj.do_moves)
		self.moveThread.terminated.connect(self.move_terminated)
		self.q = QtCore.QEventLoop()
			


	def loadParamsToGui(self, mtr):
		self.posFbkLbl.setText('%.3f' % (self.mtr.position))
		self.zeroOffsetLbl.setText('%.6f' % (self.mtr.unit_offset))
		self.absPosLbl.setText(str('%.3f' % (self.mtr.abs_position)))
		self.encSlopeLbl.setText(str('%.6f' % (self.mtr.enc_slope)))
		self.negWindowLbl.setText(str('%.3f' % (self.mtr.negWindow)))
		self.posWindowLbl.setText(str('%.3f' % (self.mtr.posWindow)))
		
		self.velFbkLbl.setText(str('%.3f' % (self.mtr.dVel)))
		self.accFbkLbl.setText(str('%.3f' % (self.mtr.dAccel)))
			
			


	def on_change(self, val):
		#print 'on_change: %s: %.2f' % (positioner, val)
		self.posFbkLbl.setText('%.3f' % (val))
		self.zeroOffsetLbl.setText('%.6f' % (self.mtr.unit_offset))
		self.absPosLbl.setText(str('%.3f' % (self.mtr.abs_position)))
		self.encSlopeLbl.setText(str('%.6f' % (self.mtr.enc_slope)))
		self.negWindowLbl.setText(str('%.3f' % (self.mtr.negWindow)))
		self.posWindowLbl.setText(str('%.3f' % (self.mtr.posWindow)))
		
		self.velFbkLbl.setText(str('%.3f' % (self.mtr.dVel)))
		self.accFbkLbl.setText(str('%.3f' % (self.mtr.dAccel)))
		#self.check_calibd()

	def on_log_msg(self, msg):
		self.logStringLbl.setText(str(msg))
	
	def clear_error(self):
		self.logStringLbl.setText('')	

	#def on_status(self, positioner, status):
	#	if(self.mtr != None):
	#		self.statusLbl.setText(str(status))
	
	def on_enable(self, is_checked):
		self.mtr.set_enable(is_checked)
	
	def on_status(self, status):
		if(self.mtr != None):
			self.statusLbl.setText(str(status))
	
	def on_moving(self, is_moving):
		if(is_moving):
			clr =  QtGui.QColor(255,0,0) # (r,g,b)
		else:
			clr =  QtGui.QColor(130,130,130) # (r,g,b)
			self.clear_error()
			#if(self.isdiff != is_moving):
			#	objgraph.show_growth()
		self.isdiff = is_moving
		self.movingWgt.setStyleSheet("QWidget { background-color: %s }" % clr.name()) 
	
	def check_calibd(self, cal):
		if(cal):
			clr =  QtGui.QColor(0,255,0) # (r,g,b)
		else:
			clr =  QtGui.QColor(255,0,0) # (r,g,b)
		self.calibratedWgt.setStyleSheet("QWidget { background-color: %s }" % clr.name()) 
	
	def on_zero_motor(self):
		if(self.mtr != None):
			self.mtr.zero_motor()
			
	def on_force_calibrated(self):
		if(self.mtr != None):
			self.mtr.force_calibrated()
	
	def on_set_velo(self):
		if(self.mtr != None):
			val = float(str(self.velFld.text()))
			self.mtr.set_velocity(val)
	
	def on_set_scan_start(self):
		if(self.mtr != None):
			strtval = float(str(self.scanStartFld.text())) 
			rngval = float(str(self.rangeFld.text())) 
			
			centerx = strtval + (0.5 * rngval)
			if(rngval > 80):
				self.mtr.set_for_coarse_scan(True, centerx)
			else:
				self.mtr.set_for_coarse_scan(False, centerx)
			
			self.mtr.move_to_finescan_start(centerx, rngval)
			self.mtr.set_marker(strtval)
	
	def on_move_to_position(self):
		if(self.mtr != None):
			print('')
			val = float(str(self.setpointFld.text()))
			
			self.mtr.move_to(val, wait=True)
			
	
	def on_move_rel_position(self):		
		if(self.mtr != None):
			val = float(str(self.relSetpointFld.text()))
			self.mtr.move_by(val, wait=True)
			
	def on_set_position(self):
		if(self.mtr != None):
			val = float(str(self.setPosFld.text()))
			self.mtr.set_position(val)

	def on_stop_btn(self):
		if(self.mtr != None):
			#self.mtr.set_for_coarse_scan(True, -46.7)
			self.mtr.stop()
				
	def on_home_btn(self):
		if(self.mtr != None):
			self.mtr.go_home()
			#self.mtr.set_for_coarse_scan(False, -46.7)
			
	def stop(self):
		if(self.mtr != None):
			self.mtr._stop_motor()
	
	def calibrate(self):
		if(self.mtr != None):
			self.mtr.calibrate()
	
	def goHome(self):
		if(self.mtr != None):
			self.mtr.go_home(wait=False)
	
	def on_scan_done(self):
		print('on_scan_done: called')
		self.q.quit()
	
	def on(self, ischecked):
		if(self.mtr != None):
			if(ischecked):
				self.mtr.motor_on()
			else:
				self.mtr.motor_off()
	
	def do_moves(self):
		self.moveThread.start()	
		
		self.q.exec_()
		print('after self.q.exec_()')
		#self.moveThread.done.disconnect()
		self.moveThread.wait(50)
		self.moveThread.terminate()
		print('done')
		#objgraph.show_growth()
			
	def move_terminated(self):
		print('self.moveThread: finally this sucker died')		
		
	def on_exit(self):
		pass
		#self.moveThread.wait(50)
		#self.moveThread.quit()
		#self.moveThread.terminate()
		#if(self.mtr is not None):
		#	self.mtr.close_mtr()

# if __name__ == '__main__':
# 
# 	app = QtWidgets.QApplication(sys.argv)
# 	window = PositionersPanel('beamline')
# 	window.show()
# 	window2 = PositionersPanel('endstation')
# 	window2.show()
# 	
# 	app.exec_()
# 	
# 	
def go():
	app = QtWidgets.QApplication(sys.argv)
	#window = PositionersPanel('beamline')
	#window.show()
	window2 = PositionersPanel('ES')
	window2.show()
	
	app.exec_()
	
	
def profile_it():
	
	#determine_profile_bias_val()
	
	profile.Profile.bias = 9.95500362835e-07
	
	profile.run('go()', 'testprof.dat')
	
	p = pstats.Stats('testprof.dat')
	p.sort_stats('cumulative').print_stats(100)
	
		
if __name__ == '__main__':
	import profile
	import pstats
	log_to_qt()
	go()
	#profile_it()
	
	#test()
	


	
	
	
	
	