'''
Created on 2014-07-15

@author: bergr
'''
import sys
import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import queue
import atexit

from bcm.devices import BaseDevice
#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES
from cls.appWidgets.main_object import  POS_TYPE_BL, POS_TYPE_ES
from cls.app_data.defaults import master_colors, get_style
from cls.utils.log import get_module_logger
from cls.utils.sig_utils import disconnect_signal, reconnect_signal
from cls.scanning.paramLineEdit import dblLineEditParamObj
from cls.applications.pyStxm.widgets.spfbk_small import Ui_Form as spfbk_small
from cls.applications.pyStxm.widgets.sp_small import Ui_Form as sp_small
from cls.applications.pyStxm.widgets.button_small_wbtn import Ui_Form as btn_small_pass_a_btn

#from cls.caWidgets.caPushBtn import caPushBtn, caPushBtnWithFbk
from cls.devWidgets.ophydPushBtn import ophydPushBtn, ophydPushBtnWithFbk
from cls.devWidgets.ophydLabelWidget import assign_aiLabelWidget
from cls.scanning.paramLineEdit import intLineEditParamObj, dblLineEditParamObj

iconsDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','icons','small')
mtrDetailDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'ui')



#motor internal status
NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
TIMEOUT, TIMEOUT_BUTDONE			  =  -8,  -7
UNKNOWN_ERROR						 =  -5
DONEW_SOFTLIM, DONEW_HARDLIM		  =  -4, -3
DONE_OK							   =   0
MOVE_BEGUN, MOVE_BEGUN_CONFIRMED	  =   0, 1
NOWAIT_SOFTLIM, NOWAIT_HARDLIM		=   4, 3

FEEDBACK_DELAY = 100

_sp_not_moving = master_colors['app_ltgray']
_fbk_not_moving = master_colors['app_ltblue']
_fbk_moving = master_colors['fbk_moving_ylw']

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
	def __init__(self, positioner_set='ES', exclude_list=[], main_obj=None, parent=None):
		super(PositionersPanel, self).__init__(parent)
		self.exclude_list = exclude_list
		self.enum_list = ['EPUPolarization', 'EPUHarmonic', 'Branch' ]
		self.main_obj = main_obj
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
		
		devs = self.main_obj.get_devices()
		#DEVICE_CFG.get_device_list()
		pos_keys = list(devs['POSITIONERS'].keys())
		pos_keys.sort()
		for dev in pos_keys:
			#print dev
			if(dev in self.exclude_list):
				continue
			
			usethis = False
			mtr = self.main_obj.device(dev)

			if(self.positioner_set.find(POS_TYPE_BL) > -1):
				if(mtr._pos_set == POS_TYPE_BL):
					usethis = True
			
			if(self.positioner_set.find(POS_TYPE_ES) > -1):
				if(mtr._pos_set == POS_TYPE_ES):
					usethis = True
			
			if(usethis):
				widg = QtWidgets.QWidget()
				dev_ui = spfbk_small()
				dev_ui.setupUi(widg)
				dev_ui.stopBtn.setIcon(QtGui.QIcon(os.path.join(iconsDir, 'stop.png')))
				dev_ui.detailsBtn.setIcon(QtGui.QIcon(os.path.join(iconsDir, 'details.png')))
				dev_ui.setPosFld.installEventFilter(self)
				self.mtr_dict[mtr.get_name()] = ( dev, dev_ui, widg,  mtr)
				dev_ui.setPosFld.mtr_info = ( dev, dev_ui, widg,  mtr)
				self.update_setpoint_field_range(dev_ui.setPosFld, mtr)
				self.connect_motor_widgets(dev, dev_ui, widg, mtr)
				#_logger.debug('DONE uic.loadUi [%s]' % dev)
				#print 'positioner: [%s] pvname [%s]' % (dev, mtr.get_name())

		self.fbk_enabled = False
		atexit.register(self.on_exit)
		self.enable_feedback()

	def update_setpoint_field_range(self, fld, mtr):
		llm = mtr.get_low_limit()
		hlm = mtr.get_high_limit()

		if ((hlm is not None) and (llm is not None)):
			if (not hasattr(fld, 'dpo')):
				fld.dpo = dblLineEditParamObj(fld.objectName(), llm, hlm, 2, parent=fld)
			fld.dpo._min = llm
			fld.dpo._max = hlm
		else:
			# this will need to be handled correctly in the future, for now leave myself a message
			ma_str = 'pv wasnt connected yet'



	def eventFilter(self, object, event):
		'''
		This event filter was primarily setup to dynamically set the min max range msgs in the ToolTips
		:param object:
		:param event:
		:return:
		'''
		if event.type() == (QtCore.QEvent.ToolTip or QtCore.QEvent.FocusIn):
			(dev, dev_ui, widg, mtr) = object.mtr_info
			llm = mtr.get_low_limit()
			hlm = mtr.get_high_limit()
			if ((hlm is not None) and (llm is not None)):
				ma_str = 'move absolute between %.2f and %.2f' % (llm, hlm)
				object.dpo._min = llm
				object.dpo._max = hlm
			else:
				# this will need to be handled correctly in the future, for now leave myself a message
				ma_str = 'pv wasnt connected yet'
			object.setToolTip(ma_str)


		# if event.type() == QtCore.QEvent.FocusOut:
		# 	self.__showCursor(False)
		# if event.type() == QtCore.QEvent.Paint:
		# 	QtWidgets.QApplication.postEvent(self, QtCore.QEvent(QtCore.QEvent.User))
		# elif event.type() == QtCore.QEvent.MouseButtonPress:
		# 	self.__select(event.pos())
		# 	return True
		# elif event.type() == QtCore.QEvent.MouseMove:
		# 	self.__move(event.pos())
		# 	return True
		# if event.type() == QtCore.QEvent.KeyPress:
		# 	delta = 5
		# 	key = event.key()
		# 	if key == QtCore.Qt.Key_Up:
		# 		self.__shiftCurveCursor(True)
		# 		return True
		# 	elif key == QtCore.Qt.Key_Down:
		# 		self.__shiftCurveCursor(False)
		# 		return True
		# 	elif key == QtCore.Qt.Key_Right or key == QtCore.Qt.Key_Plus:
		# 		if self.__selectedCurve:
		# 			self.__shiftPointCursor(True)
		# 		else:
		# 			self.__shiftCurveCursor(True)
		# 		return True
		# 	elif key == QtCore.Qt.Key_Left or key == QtCore.Qt.Key_Minus:
		# 		if self.__selectedCurve:
		# 			self.__shiftPointCursor(False)
		# 		else:
		# 			self.__shiftCurveCursor(True)
		# 		return True
		# 	if key == QtCore.Qt.Key_1:
		# 		self.__moveBy(-delta, delta)
		# 	elif key == QtCore.Qt.Key_2:
		# 		self.__moveBy(0, delta)
		# 	elif key == QtCore.Qt.Key_3:
		# 		self.__moveBy(delta, delta)
		# 	elif key == QtCore.Qt.Key_4:
		# 		self.__moveBy(-delta, 0)
		# 	elif key == QtCore.Qt.Key_6:
		# 		self.__moveBy(delta, 0)
		# 	elif key == QtCore.Qt.Key_7:
		# 		self.__moveBy(-delta, -delta)
		# 	elif key == QtCore.Qt.Key_8:
		# 		self.__moveBy(0, -delta)
		# 	elif key == QtCore.Qt.Key_9:
		# 		self.__moveBy(delta, -delta)
		return QtWidgets.QWidget.eventFilter(self, object, event)

	def enable_feedback(self):
		self.updateTimer.start(FEEDBACK_DELAY)
		self.fbk_enabled = True

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
		# hlm = llm = None
		# hlm = mtr.get_high_limit()
		# llm = mtr.get_low_limit()
		#
		# #desc = mtr.get('description')
		desc = mtr.get_desc()
		pv_name = mtr.get_name()
		# if((hlm is not None) and (llm is not None)):
		# 	ma_str = 'move absolute between %.2f and %.2f' % (llm, hlm)
		# else:
		# 	#this will need to be handled correctly in the future, for now leave myself a message
		# 	ma_str = 'pv wasnt connected yet'

		mtr_ui.stopBtn.clicked.connect(self.stop)
		mtr_ui.detailsBtn.clicked.connect(self.on_details)
		mtr_ui.setPosFld.returnPressed.connect(self.on_return_pressed)	
		#mtr_ui.setPosFld.editingFinished.connect(self.on_editing_finished)
		
		#mtr_ui.setPosFld.setToolTip(ma_str)
		
		#mtr_ui.setPosFld.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		#mtr_ui.setPosFld.customContextMenuRequested.connect(self.contextMenuEvent)

		mtr_ui.mtrNameFld.setText(name)
		mtr_ui.mtrNameFld.setToolTip(desc)
		mtr_ui.mtrNameFld.setStyleSheet("border: 2 px solid %s; background-color: %s;" % (_fbk_not_moving, _fbk_not_moving))
		#mtr_ui.mtrNameFld.setStyleSheet(
		#	"QLabel[moving = False] { border: 2 px solid % s; background - color: % s; } \
		#	QLabel[moving = True] { border: 2 px solid % s; background - color: % s; }" % (_fbk_not_moving, _fbk_not_moving, _fbk_moving, _fbk_moving))

		mtr_ui.setPosFld.setStatusTip(pv_name)
		mtr_ui.stopBtn.setStatusTip(pv_name)
		mtr_ui.detailsBtn.setStatusTip(pv_name)

		mtr.add_callback('motor_done_move', self.updateMoving)
		mtr.add_callback('user_readback', self.updateFbk)
		#mtr_fbk = mtr.get_dev('RBV')
		#assign_aiLabelWidget(mtr_ui.posFbkLbl, mtr_fbk, hdrText=None, format='%5.2f', egu='um', title_color=None, var_clr=None, warn=None, alarm=None)

		fbk = mtr.get_position()
		units = str(mtr.get_units())
		if(type(fbk) is float):
			s = '%6.3f' % fbk
			mtr_ui.posFbkLbl.setText(s)

		if(len(units)>0):
			mtr_ui.unitsLbl.setText(units)

		self.vbox.addWidget(widg)
		#_logger.debug('Done[%s] \n\n' % name)

	def append_widget_to_positioner_layout(self, widg):
		self.vbox.addWidget(widg)

	def append_setpoint_device(self, name, desc, units, dev, _min, _max, prec=2 ):
		widg = QtWidgets.QWidget()
		dev_ui = sp_small()
		dev_ui.setupUi(widg)
		dev_ui.mtrNameFld.setText(name)
		dev_ui.unitsLbl.setText(units)
		dev_ui.mtrNameFld.setToolTip(desc)
		dev_ui.mtrNameFld.setStyleSheet(
			#"border: 2 px solid %s; background-color: %s;" % (_fbk_not_moving, _fbk_not_moving))
			 "border: 2 px solid %s; background-color: %s;" % (_sp_not_moving, _sp_not_moving))

		dev_ui.setPosFld.setStatusTip(dev.get_name())

		dev_ui.setPosFld.dpo = dblLineEditParamObj(dev.get_name(), _min, _max, prec, parent=dev_ui.setPosFld)
		#dev_ui.setPosFld.dpo.valid_returnPressed.connect(on_changed_cb)
		dev_ui.setPosFld.dpo.valid_returnPressed.connect(self.on_setpoint_dev_changed)

		self.mtr_dict[dev.get_name()] = {'dev': dev, 'dev_ui': dev_ui}

		self.append_widget_to_positioner_layout(widg)

	def append_toggle_btn(self, name, desc, off_val, on_val, off_str, on_str, cb):
		'''

		:param name:
		:param desc:
		:param off_val:
		:param on_val:
		:param off_str:
		:param on_str:
		:param cb: callback to execute when clicked
		:return:
		'''
		dev_dct = {}
		dev_dct['on_val'] = on_val
		dev_dct['on_str'] = on_str
		dev_dct['off_val'] = off_val
		dev_dct['off_str'] = off_str

		ss = get_style('dark')
		widg = QtWidgets.QWidget()
		dev_ui = btn_small_pass_a_btn()
		pBtn = QtWidgets.QPushButton()
		pBtn.setStyleSheet('QPushButton::indicator::checked{<b>%s</b>}		QPushButton::indicator::unchecked{<b>%s</b>}' % (on_str, off_str))
		pBtn.clicked.connect(cb)
		pBtn.setStyleSheet(ss)
		dev_ui.setupUi(widg, pBtn)

		dev_ui.mtrNameFld.setText(name)
		dev_ui.mtrNameFld.setToolTip(desc)
		_nm = name.replace(' ','')
		id =  _nm + '_btn'
		dev_ui.pushBtn.setObjectName(id)
		dev_ui.mtrNameFld.setStyleSheet(
			#"border: 2 px solid %s; background-color: %s;" % (_fbk_not_moving, _fbk_not_moving))
			"border: 2 px solid %s; background-color: %s;" % (_sp_not_moving, _sp_not_moving))

		self.append_widget_to_positioner_layout(widg)

		#self.mtr_dict[_nm] = {'dev': None, 'dev_ui': dev_ui, dev_dct: dev_dct}




	def append_toggle_btn_device(self, name, desc, dev, off_val, on_val, off_str, on_str, cb=None, fbk_dev=None, toggle=True):
		ss = get_style('dark')

		widg = QtWidgets.QWidget()
		dev_ui = btn_small_pass_a_btn()
		if(fbk_dev):
			pBtn = ophydPushBtnWithFbk(dev, sig_change_kw='value', off_val=off_val, on_val=on_val, off_str=off_str, on_str=on_str,fbk_dev=fbk_dev,toggle=toggle)
		else:
			pBtn = ophydPushBtn(dev, off_val=off_val, on_val=on_val, off_str=off_str, on_str=on_str,toggle=toggle)

		pBtn.setStyleSheet(ss)
		dev_ui.setupUi(widg, pBtn)
		dev_ui.mtrNameFld.setText(name)
		dev_ui.mtrNameFld.setToolTip(desc)
		id = dev.get_name() + '_btn'
		dev_ui.pushBtn.setObjectName(id)

		font = dev_ui.pushBtn.font()
		font.setPixelSize(11)
		dev_ui.pushBtn.setFont(font)

		dev_ui.mtrNameFld.setStyleSheet(
			#"border: 2 px solid %s; background-color: %s;" % (_fbk_not_moving, _fbk_not_moving))
			"border: 2 px solid %s; background-color: %s;" % (_sp_not_moving, _sp_not_moving))

		self.append_widget_to_positioner_layout(widg)

	def on_btn_dev_push(self, chkd):
		btn = self.sender()
		id = btn.objectName()
		dev_dct = self.mtr_dict[id]
		if(chkd):
			val = dev_dct['on_val']
			val_str = dev_dct['on_str']
		else:
			val = dev_dct['off_val']
			val_str = dev_dct['off_str']

		btn.setText(val_str)
		dev_dct['dev'].put(val)


	def on_setpoint_dev_changed(self):
		fld = self.sender()
		dev_dct = self.mtr_dict[fld.id]
		dev_dct['dev'].put(fld.cur_val)
	
	def on_editing_finished(self):

		print('on_editing_finished')	
	
	def update_widgets(self):
		call_task_done = False
		while not self.updateQueue.empty():
			resp = self.updateQueue.get()
			if(isinstance(resp, dict)):
				if('setStyleSheet' in list(resp.keys())):
					for ss in resp['setStyleSheet']:
						widget = ss[0]
						clr_str = ss[1]
						is_moving = ss[2]
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
		if(not self.fbk_enabled):
			return
		is_moving = False
		pvname = kwargs['obj'].parent.name
		(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname]
		val = float(kwargs['value'])
		txt_clr = "color: black;"
		#this is for the DMOV or DONE Moving, I want Moving so invert logic
		if(val):
			is_moving = False
			clr_str = _fbk_not_moving
			#txt_clr = "color: black;"
		else:
			is_moving = True
			clr_str = _fbk_moving
			#txt_clr = "color: white;"
		
		_dct = {}
		#_dct['setStyleSheet'] = [(dev_ui.mtrNameFld, "background-color: " + clr_str), (dev_ui.posFbkLbl, txt_clr)]
		#_dct['setStyleSheet'] = [(dev_ui.mtrNameFld, "border: 2 px solid %s; background-color: %s;" % (clr_str, clr_str), is_moving), (dev_ui.posFbkLbl, txt_clr)]
		_dct['setStyleSheet'] = [
			(dev_ui.mtrNameFld, "border: 2 px solid %s; background-color: %s;" % (clr_str, clr_str), is_moving)]

		self.updateQueue.put_nowait(_dct)
		
		 
	
	def updateFbk(self, **kwargs):
		""" do not try to set a widget property here as
		it will eventually scew up teh main GUI thread
		Hence the use of a Queue and QTimer
		"""
		#print('updateFbk:', kwargs)
		if(self.fbk_enabled is True):
			pvname =  kwargs['obj']._read_pv.pvname
			if(pvname.find('.') > -1):
				idx = pvname.find('.')
				pvname = pvname[0:idx]
			#(dev, dev_ui, widg, mtr) = self.mtr_dict[pvname[0:idx]]
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
		if(hasattr(mtr, 'check_tr_A')):
			mtr.check_tr_A.put(pos)
			sts = 'success'
		else:
			sts = mtr.move(pos, wait=False)
		
		if(sts == OUTSIDE_LIMITS):
			#outside the limits
			clr_str = "yellow;"
		else:
			clr_str = "white;"
		
		_dct = {}
		_dct['setStyleSheet'] = [(dev_ui.setPosFld, "background-color: " + clr_str, False)]
		self.updateQueue.put_nowait(_dct)
	
	def check_soft_limits(self, mtr, sp):
		lvio = mtr.get('soft_limit')
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
			#if(mtr._pvs['setpoint'].connected):
			if (mtr.user_setpoint.connected):
				hlm = mtr.get_high_limit()
				llm = mtr.get_low_limit()
				
				if((llm is not None) and (hlm is not None)):
					ma_str = 'move %s absolute between %.2f and %.2f' % (dev, llm, hlm)
			else:
				ma_str = 'Motor %s not connected' % (dev)
				
			self.menu = QtWidgets.QMenu(self)
			renameAction = QtWidgets.QAction(ma_str, self)
			#renameAction.triggered.connect(self.renameSlot)
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
		ss = get_style('dark')
		detForm.setStyleSheet(ss)
		detForm.exec_()
		
		

class PositionerDetail(QtWidgets.QDialog):
	'''
	classdocs
	'''
	changed = QtCore.pyqtSignal(float)

	def __init__(self, positioner, dev_ui, mtr):
		super(PositionerDetail, self).__init__()
		uic.loadUi(os.path.join(mtrDetailDir, 'spfbk_detail.ui'), self)
		self.mtr = mtr
		self.positioner = positioner
		self.dev_ui = dev_ui

		self.units = ''
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

		self.changed.connect(self.update_fbk)
		self.loadMotorConfig(self.positioner)
		
				
	def loadMotorConfig(self, positioner='AbsSampleX'):
		posner_nm = str(positioner)
		
		if(self.mtr != None):
			self.mtr.add_callback('user_readback', self.on_change)
			# disconnect_signal(self.mtr, self.mtr.changed.changed)
			# disconnect_signal(self.mtr, self.mtr.status)
			# disconnect_signal(self.mtr, self.mtr.calib_changed)
			# disconnect_signal(self.mtr, self.mtr.moving)
			# disconnect_signal(self.mtr, self.mtr.log_msg)
			#
			# del(self.mtr)
			# self.mtr = None

		self.mtrNameFld.setText(posner_nm)
		self.unitsLbl.setText(self.units)
		#self.mtr = self.positioner
		self.loadParamsToGui(self.mtr)
		#self.mtr.changed.connect(self.updateFbk)
		
		#self.mtr.changed.connect(self.update_fbk)
		# self.mtr.calib_changed.connect(self.check_calibd)
		# self.mtr.status.connect(self.on_status)
		# self.mtr.moving.connect(self.on_moving)
		# self.mtr.log_msg.connect(self.on_log_msg)
		
		# self.moveThread = QtCore.QThread()
		# self.scanObj = scanThread(self.mtr)
		# self.scanObj.moveToThread(self.moveThread)
		# self.scanObj.done.connect(self.on_scan_done)
		# self.moveThread.started.connect(self.scanObj.do_moves)
		# self.moveThread.terminated.connect(self.move_terminated)
		# self.q = QtCore.QEventLoop()
			


	def loadParamsToGui(self, mtr):
		self.posFbkLbl.setText('%.3f' % (self.mtr.position))
		#self.zeroOffsetLbl.setText('%.6f' % (self.mtr.unit_offset))
		#self.absPosLbl.setText(str('%.3f' % (self.mtr.abs_position)))
		# self.encSlopeLbl.setText(str('%.6f' % (self.mtr.enc_slope)))
		# self.negWindowLbl.setText(str('%.3f' % (self.mtr.negWindow)))
		# self.posWindowLbl.setText(str('%.3f' % (self.mtr.posWindow)))
		
		self.velFbkLbl.setText(str('%.3f' % (self.mtr.velocity.get())))
		self.accFbkLbl.setText(str('%.3f' % (self.mtr.acceleration.get())))
			

	def on_change(self, **kwargs):
		#print(kwargs)
		val = kwargs['value']
		self.changed.emit(val)

	def update_fbk(self, val):
		#print 'on_change: %s: %.2f' % (positioner, val)
		self.posFbkLbl.setText('%.3f' % (val))
		#self.zeroOffsetLbl.setText('%.6f' % (self.mtr.unit_offset))
		#self.absPosLbl.setText(str('%.3f' % (self.mtr.abs_position)))
		#self.encSlopeLbl.setText(str('%.6f' % (self.mtr.enc_slope)))
		#self.negWindowLbl.setText(str('%.3f' % (self.mtr.negWindow)))
		#self.posWindowLbl.setText(str('%.3f' % (self.mtr.posWindow)))

		self.velFbkLbl.setText(str('%.3f' % (self.mtr.velocity.get())))
		self.accFbkLbl.setText(str('%.3f' % (self.mtr.acceleration.get())))
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
			
			self.mtr.move(val, wait=True)
			
	
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
	window2.enable_feedback()
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
	#log_to_qt()
	go()
	#profile_it()
	
	#test()
	


	
	
	
	
	