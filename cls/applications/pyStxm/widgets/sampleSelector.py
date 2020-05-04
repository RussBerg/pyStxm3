'''
Created on 2013-07-16

@author: bergr
'''
'''
Created on 2013-06-28

@author: bergr
'''
#!/usr/bin/python

import sys
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets

from cls.applications.pyStxm import abs_path_to_ini_file
#from cls.scanning.ScanDef import ImageLineUniScanDef, EnergyRegionScanDef
#from cls.applications.pyStxm.bl10ID01 import DEVICE_CFG
from cls.utils.cfgparser import ConfigClass
from bcm.epics_devices_MOVED.motor_v2 import Motor_V2

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ

#read the ini file and load the default directories
appConfig = ConfigClass(abs_path_to_ini_file)
uiDir = appConfig.get_value('MAIN', 'uiDir')
dataDir = appConfig.get_value('MAIN', 'dataDir')
mtrcfg = appConfig.get_value('MAIN', 'mtrcfg')
SLASH = appConfig.get_value('MAIN', 'dirslash')

_sample_positions = {}

xpos_1 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_1')
ypos_1 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_1')
xpos_2 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_2')
ypos_2 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_2')
xpos_3 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_3')
ypos_3 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_3')
xpos_4 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_4')
ypos_4 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_4')
xpos_5 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_5')
ypos_5 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_5')
xpos_6 = appConfig.get_value('SAMPLE_POSITIONS', 'xpos_6')
ypos_6 = appConfig.get_value('SAMPLE_POSITIONS', 'ypos_6')
xi0pos = appConfig.get_value('SAMPLE_POSITIONS', 'xi0pos')
yi0pos = appConfig.get_value('SAMPLE_POSITIONS', 'yi0pos')
sample_circle_diam = float(appConfig.get_value('SAMPLE_POSITIONS', 'sample_circle_diam'))


_sample_positions['pos1'] = (float(xpos_1), float(ypos_1))
_sample_positions['pos2'] = (float(xpos_2), float(ypos_2))
_sample_positions['pos3'] = (float(xpos_3), float(ypos_3))
_sample_positions['pos4'] = (float(xpos_4), float(ypos_4))
_sample_positions['pos5'] = (float(xpos_5), float(ypos_5))
_sample_positions['pos6'] = (float(xpos_6), float(ypos_6))
_sample_positions['i0pos'] = (float(xi0pos), float(yi0pos))

MOTORFBK_TO_SCREEN_UNITS = (52.5 / 5000)

def get_velo_for_scan(start, stop, points, dwell): 
		""" Calc required velocity for desired scan
		
		:param scan: a valid scanDef object that contains all the information 
				required to execute the scan. 
		:type scan: scanDef.
		:param dwell: the dwell time (in ms) specified in the energy region definition for this scan
		:type dwell: float
		:param accdccD: the accelerate deccelerate distance that is padded to the start and stop of each
			scan move, this distance is required to give the motor enough time to reach 
			constant velocity before reaching the position at which the shutter will be opened,
			and enough distance for the motor to go past the position at which the shutter will
			close.
		:type accdccD: float
						
		:returns:  None 
		
		"""
		#maxVeloX = scan.get_X_positioner().get_max_velocity()
		delta = stop - start
		accRange = delta * 0.08  # %4 of desired line length, any smaller and the scan fails due to marker location too close to
		dccRange = delta * 0.0000001 
		accdccD = accRange + dccRange
		lineTime = points * (dwell *0.001)
		ttlDist = (stop - start) / 1000.0 #to turn back into mm
		velo = ttlDist / lineTime 
		print('get_velo_for_scan: points = %d, range = %.3f, dwell = %.2f ms,  velo = %.3ff mm/s' % (points, ttlDist, dwell, velo)) 
		return(velo)


class SenderObject(QtCore.QObject):
	selected = QtCore.pyqtSignal(object)

class Node(QtWidgets.QGraphicsItem):
	""" a class to draw sample position circles that are selectable 
	"""

	def __init__(self, parent = None, name='NONE', pos_num=1, x=10, y=10, rad = 10, scaler=1.0, clr=QtCore.Qt.gray):
		#QtWidgets.QGraphicsItem.__init__(self,parent)
		super(Node, self).__init__(parent)
		self.sig = SenderObject()
		self.name = name
		self.pos_num = pos_num
		#self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
		self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
		self.x = x - rad
		self.y = y - rad
		self.wd = rad * 2.0
		self.ht = rad * 2.0
		self.scaler = scaler
		
		
		self.centerX = (self.x + (0.5 * self.wd)) * scaler
		self.centerY = (self.y + (0.5 * self.wd)) * scaler
		#print 'circle [%d] cx=%f cy=%f' % (pos_num, self.centerX, self.centerY)
		
		#int x, int y, int width, int height
		
		self.frame = np.array([self.x, self.y, self.wd, self.ht]) * scaler
		self.bndgrect = np.array([self.x, self.y, self.wd, self.ht]) * scaler
		self.circle = np.array([self.x, self.y, self.wd, self.ht]) * scaler
		self.clridx = 0
		self.clr = clr
		self.selected = False
		
		#self.update(self.left, self.top, self.right, self.btm)
	def on_selected(self, circle):
		self.sig.selected.emit(self)
	
	def set_selected(self, sel=False):
		self.selected = sel
		self.update()
	
	def boundingRect(self):
		adjust = 2.0
		return QtCore.QRectF(self.bndgrect[0] - adjust, self.bndgrect[1] - adjust, self.bndgrect[2] + adjust,  self.bndgrect[3] + adjust)
	
	def paint(self, painter, option, widget):
#		 painter.setPen(QtCore.Qt.NoPen)
#		 painter.setBrush(QtCore.Qt.darkGray)
#		 painter.drawEllipse(self.circle[0], self.circle[1], self.circle[2], self.circle[3])
# 
		gradient = QtGui.QRadialGradient(-3, -3, 10)
#		 if option.state & QtWidgets.QStyle.State_Sunken:
#			 gradient.setCenter(3, 3)
#			 gradient.setFocalPoint(3, 3)
#			 gradient.setColorAt(1, QtGui.QColor(QtCore.Qt.yellow).light(120))
#			 gradient.setColorAt(0, QtGui.QColor(QtCore.Qt.darkYellow).light(120))
#		 else:
		if(self.selected):
			#self.clr = QtCore.Qt.green
			self.clr = QtCore.Qt.darkGreen
		else:
			self.clr = QtCore.Qt.gray
			
		gradient.setColorAt(0, self.clr)
		gradient.setColorAt(1, self.clr)
# 
		painter.setBrush(QtGui.QBrush(gradient))
		painter.setPen(QtGui.QPen(self.clr, 0))
		painter.drawEllipse(self.frame[0], self.frame[1], self.frame[2], self.frame[3])
	
	def itemChange(self, change, value):
		if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
			print('[%s] ItemPosition changed' % self.name)
	
		return super(Node, self).itemChange(change, value)

	def mousePressEvent(self, event):
		#print '[%s] mouse pressed' % self.name
		if(self.selected):
			self.selected = False
			#self.clr = QtCore.Qt.gray
		else:
			self.selected = True
			#self.clr = QtCore.Qt.green
		self.sig.selected.emit(self)
		
#		 self.clridx += 1
#		 if(self.clridx > 5):
#			 self.clridx = 0
#			
#		 if(self.clridx == 0):
#			 self.clr = QtCore.Qt.blue
#		 elif(self.clridx == 1):
#			 self.clr = QtCore.Qt.yellow
#		 elif(self.clridx == 2):
#			 self.clr = QtCore.Qt.cyan
#		 elif(self.clridx == 3):
#			 self.clr = QtCore.Qt.red
#		 elif(self.clridx == 4):
#			 self.clr = QtCore.Qt.black
#		 elif(self.clridx == 5):
#			 self.clr = QtCore.Qt.green
		self.update()
		super(Node, self).mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		#print '[%s] mouse released' % self.name

		self.update()
		super(Node, self).mouseReleaseEvent(event)


class crossHairItem(QtWidgets.QGraphicsEllipseItem):
	def __init__(self, scalar, parent=None):
		QtWidgets.QGraphicsPixmapItem.__init__(self, parent)

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
		#self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
		self.centerX = 0
		self.centerY = 0
		self.radius = 8
		
		self.x_fbk = 0
		self.y_fbk = 0
		
		self.x_zoffset = scalar * 125.333
		self.y_zoffset = scalar * 84.0
		
		self.setPen(QtGui.QPen(QtGui.QColor(QtCore.Qt.yellow)))
		#self.setPen(QtGui.QPen(QtGui.QColor(QtCore.Qt.blue)))
		self.setRect(QtCore.QRectF(self.centerX-self.radius, self.centerY-self.radius, self.radius, self.radius))
	
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update_fbk)
		self.timer.start(20)
	
	def calc_crossHair_centerX(self, fbk):
		chx = (MOTORFBK_TO_SCREEN_UNITS)*fbk + self.x_zoffset
		return(chx)
	
	def calc_crossHair_centerY(self, fbk):
		chy = -1.0*(MOTORFBK_TO_SCREEN_UNITS)*fbk + self.y_zoffset
		return(chy)
	
	def set_x_fbk(self, fbk):
		self.x_fbk = fbk
		
	def set_y_fbk(self, fbk):
		self.y_fbk = fbk	
	
	def update_fbk(self):
		#print 'update_fbk: xfk=%f yfbk=%f' % (self.x_fbk, self.y_fbk)
		x = self.calc_crossHair_centerX(self.x_fbk)
		y = self.calc_crossHair_centerY(self.y_fbk)
		#print 'CHAIR: cx=%f cy=%f' % (x, y)
		self.set_center(x, y)
	
	def set_center(self, x, y):
		
		self.centerX = x
		self.centerY = y
		self.setRect(QtCore.QRectF(self.centerX-self.radius, self.centerY-self.radius, self.radius, self.radius))
	
	def move_center(self, x, y):
		self.centerX += x
		self.centerY += y
		self.setRect(QtCore.QRectF(self.centerX-self.radius, self.centerY-self.radius, self.radius, self.radius))
			
	

class SampleSelectorView(QtWidgets.QGraphicsView):
	""" the class that is the view of the scene which will hold our 6 sample position circles """
	selected = QtCore.pyqtSignal(int)
	
	def __init__(self, parent = None, name='NONE', centerx=10, centery=10, rad = 10, scaler=1.0, clr=QtCore.Qt.blue, mutually_exclude=True):
		QtWidgets.QGraphicsView.__init__(self,parent)
		self.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.lightGray))
		
		self.scene = QtWidgets.QGraphicsScene()
		self.setMinimumSize(250, 150)
		
		self.circles = []
		self.circles.append(self.add_text('1',0,  50, 10, 30, scaler))
		self.circles.append(self.add_text('2',1,  120, 10, 30, scaler)) 
		self.circles.append(self.add_text('3',2,  190, 10, 30, scaler))
		self.circles.append(self.add_text('4',3,  50, 80, 30, scaler))
		self.circles.append(self.add_text('5',4,  120, 80, 30, scaler))
		self.circles.append(self.add_text('6',5,  190, 80, 30, scaler))
		
		self.crosshair = crossHairItem(scaler)
		
		#self.absMtrX = Motor_V2('IOC:m11')
		#self.absMtrY = Motor_V2('IOC:m12')
		
		
		self.absMtrX = MAIN_OBJ.device('SampleX')
		self.absMtrY = MAIN_OBJ.device('SampleY')
		
		
		self.absMtrX.add_callback('RBV', self.on_xmotor_fbk_change)
		self.absMtrY.add_callback('RBV', self.on_ymotor_fbk_change)
		#self.crosshair = self.add_crossHair('CH',6,  120, 80, 30, scaler)
		
		
		self.crosshair.set_x_fbk(self.absMtrX.get('RBV'))
		self.crosshair.set_y_fbk(self.absMtrY.get('RBV'))

		self.scene.addItem(self.crosshair)
		self.setScene(self.scene)
		
		self.mutually_exclude = mutually_exclude
	
	
	def on_xmotor_fbk_change(self, **kw):
		""" user units readback changed """
		self.crosshair.set_x_fbk(kw['value'])
		#self.crosshair.update_fbk()
		
	def on_ymotor_fbk_change(self, **kw):
		""" user units readback changed """
		self.crosshair.set_y_fbk(kw['value'])
		#self.crosshair.update_fbk()


	def deselect_all(self):
		for i in range(len(self.circles)):
			self.circles[i].set_selected(False)
	 
		
	def on_clicked(self, circle):
		#print '%s clicked' % circle.name
		for i in range(len(self.circles)):
			#print self.circles[i]
			if(circle.name == self.circles[i].name):
				self.selected.emit(i)
				pass
			else:
				if(self.mutually_exclude):
					#deselect the other circles
					self.circles[i].set_selected(False)
					
	def get_selected_positions(self):
		lst = []
		for i in range(len(self.circles)):
			if(self.circles[i].selected):
				lst.append(self.circles[i])
		return(lst)
	
	def get_sample_position(self, pos):
		return(self.circles[pos])
	
	def add_text(self, text, pos_num, x, y, rad, scaler):
		node = Node(name='pos' + text, pos_num=pos_num, x=x, y=y, rad=rad, scaler=scaler)
		node.sig.selected.connect(self.on_clicked)
		self.scene.addItem(node)
		txt = self.scene.addText(text)
		fontSize = (10 * scaler)
		txt.setFont(QtGui.QFont('Arabeyesqr', fontSize))
		centerx = (x - (fontSize/1.0)+2) * scaler
		centery = (y - ((fontSize/2)+8)) * scaler
		txt.setPos(centerx, centery)
		return(node)
	
	def move_crosshair(self, x, y):
		self.crosshair.move_center(x,y)
		
	def move_motors(self, x, y):
		self.absMtrX.move(x)
		self.absMtrY.move(y)
		
	
class SampleSelectorWidget(QtWidgets.QWidget):
	
	do_preview = QtCore.pyqtSignal(object)
	abort_preview = QtCore.pyqtSignal()
	selected = QtCore.pyqtSignal(int)
	
	def __init__(self, parent = None, name='NONE', centerx=10, centery=10, rad = 10, scaler=1.0, clr=QtCore.Qt.blue):
		QtWidgets.QWidget.__init__(self,parent)
		#self.setGeometry(50,50,400, 300)
		#these are the values when scaler=1.0, normalized width and height
		self.normWidth = 275 * scaler
		self.normHt = 300 * scaler
		#self.setMinimumSize(self.normWidth, self.normHt)
		#self.setMaximumSize(self.normWidth, self.normHt)
		self.btns_enabled = False
		#self.clearBtn = QtWidgets.QPushButton("Clear all")
		#self.calibrateBtn = QtWidgets.QPushButton("Calibrate")
# 		self.previewBtn = QtWidgets.QPushButton("Preview")
# 		self.abortBtn = QtWidgets.QPushButton("Abort")
# 		
# 		gridLayout = QtWidgets.QGridLayout()
# 		self._20x20Btn = QtWidgets.QPushButton("20x20")
# 		self._50x50Btn = QtWidgets.QPushButton("50x50")
# 		self._75x75Btn = QtWidgets.QPushButton("75x75")
# 		self._100x100Btn = QtWidgets.QPushButton("100x100")
# 		self._200x200Btn = QtWidgets.QPushButton("200x200")
# 		self._300x300Btn = QtWidgets.QPushButton("300x300")
# 		
# 		self._100x50Btn = QtWidgets.QPushButton("100x50")
# 		self._200x50Btn = QtWidgets.QPushButton("200x50")
# 		self._300x50Btn = QtWidgets.QPushButton("300x50")
# 		
# 		self._20x20Btn.clicked.connect(self.on_previewBtn)
# 		self._50x50Btn.clicked.connect(self.on_previewBtn)
# 		self._75x75Btn.clicked.connect(self.on_previewBtn)
# 		self._100x100Btn.clicked.connect(self.on_previewBtn)
# 		self._200x200Btn.clicked.connect(self.on_previewBtn)
# 		self._300x300Btn.clicked.connect(self.on_previewBtn)
# 		
# 		self._100x50Btn.clicked.connect(self.on_previewBtn)
# 		self._200x50Btn.clicked.connect(self.on_previewBtn)
# 		self._300x50Btn.clicked.connect(self.on_previewBtn)
# 		
# 		gridLayout.addWidget(self._20x20Btn, 0,0)
# 		gridLayout.addWidget(self._50x50Btn, 0,1)
# 		gridLayout.addWidget(self._75x75Btn, 0,2)
# 		gridLayout.addWidget(self._100x100Btn, 1,0)
# 		gridLayout.addWidget(self._200x200Btn, 1,1)
# 		gridLayout.addWidget(self._300x300Btn, 1,2)
# 		gridLayout.addWidget(self._100x50Btn, 2,0)
# 		gridLayout.addWidget(self._200x50Btn, 2,1)
# 		gridLayout.addWidget(self._300x50Btn, 2,2)
# 		
# 		self.energyLbl = QtWidgets.QLabel("Energy")
# 		self.energyFld = QtWidgets.QLineEdit("650.5")
# 		self.energyFld.setValidator(QtGui.QDoubleValidator(130.0, 3000.0, 3, self))
# 		self.dwellLbl = QtWidgets.QLabel("Dwell")
# 		self.dwellFbkLbl = QtWidgets.QLabel("0.0")
# 		self.dwellSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
# 		self.dwellSlider.setMinimum(1.0)
# 		self.dwellSlider.setMaximum(100.0)
# 		self.dwellSlider.setValue(2)
# 		self.dwellFbkLbl.setText('%.1f ms' % self.dwellSlider.value())
# 		#self.dwellSlider.setFocusPolicy(QtCore.Qt.NoFocus)
# 		self.dwellSlider.valueChanged.connect(self.on_dwell_slider_changed)
# 		
# 		self.enable_btns(False)
		
		
		
		self.selected_position = 1
		
		#self.clearBtn.clicked.connect(self.on_clearBtn)
		#self.calibrateBtn.clicked.connect(self.on_calibrateBtn)
# 		self.previewBtn.clicked.connect(self.on_previewBtn)
# 		self.abortBtn.clicked.connect(self.on_abortBtn)
# 		
 		vlayout = QtWidgets.QVBoxLayout()
# 		
# 		hlayout = QtWidgets.QHBoxLayout()
# 		hlayout.addWidget(self.energyLbl)
# 		hlayout.addWidget(self.energyFld)
# 		
# 		hlayout2 = QtWidgets.QHBoxLayout()
# 		hlayout2.addWidget(self.dwellLbl)
# 		hlayout2.addWidget(self.dwellSlider)
# 		hlayout2.addWidget(self.dwellFbkLbl)
# 		
# 		hlayout3 = QtWidgets.QHBoxLayout()
# # 		hlayout3.addWidget(self.clearBtn)
# # 		hlayout3.addWidget(self.calibrateBtn)
# 		#hlayout3.addWidget(self.previewBtn)
# 		hlayout3.addWidget(self.abortBtn)
# 		
		#hlayout3.setGeometry(QtCore.QRect(10,10,self.width(), self.height()))
		
		self.view = SampleSelectorView(parent=parent, name=name, centerx=centerx, centery=centery, rad = rad, scaler=scaler, clr=clr)
		self.view.selected.connect(self.on_selected)
		
		vlayout.addWidget(self.view)
# 		vlayout.addLayout(hlayout)
# 		vlayout.addLayout(hlayout2)
# 		vlayout.addLayout(gridLayout)
# 		vlayout.addLayout(hlayout3)
		
		
		self.setLayout(vlayout)
	
	def on_selected(self, pos_num):
		#self.enable_btns(True)
		self.selected_position = pos_num
		self.selected.emit(pos_num)
		self.goto_pos(pos_num)
	
	def goto_pos(self, pos):
		posStr = 'pos' + (str('%d'%(pos+1)))
		(x,y) = _sample_positions[posStr] 
		self.view.move_motors(x, y)
		
	
	def enable_btns(self, enable):
		self._20x20Btn.setEnabled(enable)
		self._50x50Btn.setEnabled(enable)
		self._75x75Btn.setEnabled(enable)
		self._100x100Btn.setEnabled(enable)
		self._200x200Btn.setEnabled(enable)
		self._300x300Btn.setEnabled(enable)
		self._100x50Btn.setEnabled(enable)
		self._200x50Btn.setEnabled(enable)
		self._300x50Btn.setEnabled(enable)
		self.abortBtn.setEnabled(enable)
		self.dwellSlider.setEnabled(enable)
		
	def get_selected_position(self):
		return(self.selected_position)
	
	def on_dwell_slider_changed(self, val):
		self.dwellFbkLbl.setText('%.1f ms' % float(val))
		
	
	def on_clearBtn(self):
		self.view.deselect_all()
	
	def on_abortBtn(self):
		self.abort_preview.emit()
		
	def on_calibrateBtn(self):
		pass
	
	def get_selected_list(self):
		scan_list = []
		posLst = self.view.get_selected_positions()
		(energy, valid) = self.energyFld.text().toFloat() 
		dwell = self.dwellSlider.value()
		
		for pos in posLst:
			pos_num = pos.pos_num
			posname = pos.name
			(xCenter, yCenter) = _sample_positions[posname]
			startX = xCenter - (0.5 * sample_circle_diam)
			stopX = xCenter + (0.5 * sample_circle_diam)
			startY = yCenter - (0.5 * sample_circle_diam)
			stopY = yCenter + (0.5 * sample_circle_diam)
			scan_list.append( {'pos_num':pos_num, 'posname':posname, 'startX':startX, 'stopX':stopX, 'startY':startY, 'stopY':stopY, 'xCenter':xCenter, 'yCenter':yCenter, 'energy':energy, 'dwell':dwell} )

			return(scan_list)
	
	def on_previewBtn(self):
		""" callect all selected positions and their configured position values and emit it"""
		btn = self.sender()
		txt = str(btn.text())
		if(txt == '20x20'):
			npointsX = 20
			npointsY = 20
			#self.dwellSlider.setValue(10)
			self.dwellSlider.setMinimum(10.0)
		elif(txt == '50x50'):
			npointsX = 50
			npointsY = 50
			self.dwellSlider.setMinimum(4.0)
		elif(txt == '75x75'):
			npointsX = 75
			npointsY = 75
		elif(txt == '100x100'):
			npointsX = 100
			npointsY = 100
		elif(txt == '200x200'):
			npointsX = 200
			npointsY = 200
		elif(txt == '300x300'):
			npointsX = 300
			npointsY = 300
		elif(txt == '100x50'):
			npointsX = 100
			npointsY = 50
		elif(txt == '200x50'):
			npointsX = 200
			npointsY = 50
		elif(txt == '300x50'):
			npointsX = 300
			npointsY = 50
		else:
			npointsX = 25
			npointsY = 25

			
		scan_list = []
		posLst = self.view.get_selected_positions()
		(energy, valid) = self.energyFld.text().toFloat() 
		dwell = self.dwellSlider.value()
		
		for pos in posLst:
			pos_num = pos.pos_num
			posname = pos.name
			(xCenter, yCenter) = _sample_positions[posname]
			startX = xCenter - (0.5 * sample_circle_diam)
			stopX = xCenter + (0.5 * sample_circle_diam)
			startY = yCenter - (0.5 * sample_circle_diam)
			stopY = yCenter + (0.5 * sample_circle_diam)
			scan_list.append( {'pos_num':pos_num, 'posname':posname, 
							'startX':startX, 'stopX':stopX, 'startY':startY, 'stopY':stopY,
							'npointsX':npointsX, 'npointsY':npointsY, 
							'xCenter':xCenter, 'yCenter':yCenter, 
							'energy':energy, 
							'dwell':dwell} )
		
		#get_velo_for_scan(startX, stopX, npointsX, dwell)
		self.do_preview.emit(scan_list)
			
			
		

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)

	#view = QtWidgets.QGraphicsView(scene)
	window = SampleSelectorWidget(scaler=0.75)
	window.show()

	sys.exit(app.exec_())