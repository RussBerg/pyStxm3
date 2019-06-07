'''
Created on Sep 28, 2015

@author: bergr
'''
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QRectF, QPointF	
from cls.plotWidgets.color_def import *

class ROILimitObj(object):
	def __init__(self, qrect, qclr, label, fpattern):
		"""
		__init__(): an object for encapsulating all the information for the restriction and display of
		plot a single ShapeItem
			 - rect: the bounding rect for this restriction def, this defines the floor and ceiling values for x and y
			 - qclr: the QColor (includes alpha) to use for this restriction def
			 - label: the label to display for this restriction def
			 - fpattern: the brush fill pattern to use, see QBrush Style

		:returns: None
		"""
		self.qrect = qrect
		self.qclr = qclr
		self.label = label
		self.fill_pattern = fpattern
	
	def get_qrect(self):
		return(self.qrect)	
	
	def is_within_bounds(self, bounding_qrect):
		if(bounding_qrect.contains(self.qrect)):
			return(True)
		else:
			return(False)
			
		
	def exceeds(self, qrect):
		if(self.exceeds_range(qrect)):
			return(True)
		
		if(self.exceeds_bounds(qrect)):
			return(True)
		
		return(False)	
	
	def exceeds_range(self, qrect):
		""" check the rect given against the definition and set the color and label accordingly
		
		:returns: bool if the rect passed in exceeds the one it has for a definition
		"""
		if(abs(qrect.width()) > abs(self.qrect.width())):
			return(True)	
		
		if(abs(qrect.height()) > abs(self.qrect.height())):
			return(True)
		
		return(False)
		
	def exceeds_bounds(self, qrect):
		""" check the rect given against the definition and returnTrue if rect exceeds definition
		
		if qrect is a horizontal line then contains() doesn't work, it needs y1 and y2 to be different even just a little
		
		:returns: bool if the rect passed in exceeds the one it has for a definition
		"""
		ret = False
		#print('exceeds_bounds: qrect left=%.1f, right=%.1f, top=%.1f, btm=%.1f, width=%.1f, ht=%.1f' % (qrect.left(), qrect.right(), qrect.top(), qrect.bottom(), qrect.width(), abs(qrect.height())))
		#print('exceeds_bounds: self.qrect left=%.1f, right=%.1f, top=%.1f, btm=%.1f, width=%.1f, ht=%.1f' % (self.qrect.left(), self.qrect.right(), self.qrect.top(), self.qrect.bottom(), self.qrect.width(), abs(self.qrect.height())))
		#check to see if it is a horizontal line, if so contains() doesn't work without adjust y2 a little bit
		if(qrect.top() == qrect.bottom()):
			#for the purposes of the check just adjust y2 a little
			y2 = qrect.bottom()
			qrect.setBottom(y2 - 0.01)
			if(not self.qrect.contains(qrect)):
				ret = True
			qrect.setBottom(y2)	
		else:
			#if qrect is inside self.qrect then return false as boundaries are not exceeded
			if(not self.qrect.contains(qrect)):
				ret = True
		
		return(ret)


ROI_STATE_NORMAL = 0
ROI_STATE_WARN = 1
ROI_STATE_ALARM = 2


class ROILimitDef(object):
	def __init__(self, bounding, normal, warn=None, alarm=None):
		"""
		__init__(): an object for encapsulating all the information for the restriction and display of
		plot ShapeItems, takes 4 arguments:
			- bounding: a ROILimitObj() that represents the outermost bounds for this shape, the rect tuple defines teh floor and ceiling values 
			- normal: a ROILimitObj() that represents when this shape is 'normal'
			- warn: a ROILimitObj() that represents when this shape exceeds 'normal' but is less than 'alarm' thus 'warn'
			- alarm: a ROILimitObj() that represents when this shape exceeds 'warn' thus 'alarm'
		
		The logic for the validation of the qrect is:
			if(qrect is within the bounds of the bounding rect):
				#check to see if the qrect is larger than the warn rect
					if not then return normal
					if yes 
						then set state to warn
						check if qrect is larger then alarm
						if yes 
							then set state to alarm
			if not then return alarm			
								
		
		:returns: None
		"""
		self.state = ROI_STATE_NORMAL
		self.bounding = bounding 
		self.normal = normal
		if(warn is None):
			self.warn = normal
		else:
			self.warn = warn	
		
		if(alarm is None):	
			self.alarm = normal
		else:
			self.alarm = alarm	
		
		self.state_qclr = None
		self.state_label = None
		self.state_fpattern = None
		self.state_qrect = None
	
	def get_color(self):
		return(self.state_qclr)
	
	def get_label(self):
		return(self.state_label)
	
	def get_fill_pattern(self):
		return(self.state_fpattern)
	
	def get_normal_def(self, as_qrect=False):
		if(as_qrect):
			return(self.normal.get_qrect())
		else:
			return(self.normal)
	
	def get_warn_def(self, as_qrect=False):
		if(as_qrect):
			return(self.warn.get_qrect())
		else:
			return(self.warn)
	
	def get_alarm_def(self, as_qrect=False):
		if(as_qrect):
			return(self.alarm.get_qrect())
		else:
			return(self.alarm)
	
	def get_qrect(self):
		return(self.state_qrect)	
		
	def check_limits(self, qrect):
		'''
		The logic for the validation of the qrect is:
			if(qrect is within the bounds of the bounding rect):
				#check to see if the qrect is larger than the warn rect
					if not then return normal
					if yes 
						then set state to warn
						check if qrect is larger then alarm
						if yes 
							then set state to alarm
			if not then return alarm	
		'''
		#if(self.bounding_qrect.contains(qrect)):
		if(not self.bounding.exceeds(qrect)):
			#print('check_limits: setting NORMAL')
			self._set_state('normal')
			self.state_qrect = qrect
			if(self.warn):	
				if(self.warn.exceeds(qrect)):
					self._set_state('warn')
					#print('check_limits: setting WARN')
					self.state_qrect = qrect
					if(self.alarm):
						if(self.alarm.exceeds_range(qrect)):
							self._set_state('alarm')
							#print('check_limits: setting ALARM')
							self.state_qrect = self._limit_qrect(self.alarm.get_qrect(), qrect)
		else:
			self._set_state('bounding_alarm')
			#print('check_limits: setting BOUNDING ALARM')
			self.state_qrect = qrect	
		
		return(self.state_qrect)
				
	def _limit_qrect(self, limit_qrect, qrect):
		''' take a limit qrect and limit the qrect to the limit_qrectboundaries '''
		
		if(qrect.left() < limit_qrect.left()):
			qrect.setLeft(limit_qrect.left())
			
		if(qrect.right() > limit_qrect.right()):
			qrect.setRight(limit_qrect.right())
		
		if(qrect.bottom() < limit_qrect.bottom()):
			qrect.setBottom(limit_qrect.bottom())
			
		if(qrect.top() > limit_qrect.top()):
			qrect.setTop(limit_qrect.top())		
		
		return(qrect)	
				

	def _set_state(self, state='normal'):
		'''

		:param state:
		:return:
		'''
		
		if(state == 'normal'):
			self.state_qclr = self.normal.qclr
			self.state_label = self.normal.label
			self.state_fpattern = self.normal.fill_pattern
			self.state = ROI_STATE_NORMAL
		elif(state == 'warn'):
			if(self.warn):
				self.state_qclr = self.warn.qclr
				self.state_label = self.warn.label
				self.state_fpattern = self.warn.fill_pattern
				self.state = ROI_STATE_WARN
		elif(state == 'alarm'):
			if(self.alarm):
				self.state_qclr = self.alarm.qclr
				self.state_label = self.alarm.label
				self.state_fpattern = self.alarm.fill_pattern
				self.state = ROI_STATE_ALARM
		elif(state == 'bounding_alarm'):
				self.state_qclr = self.bounding.qclr
				self.state_label = self.bounding.label
				self.state_fpattern = self.bounding.fill_pattern
				self.state = ROI_STATE_ALARM		
		
			
			

if __name__ == "__main__":
	
		bounding_qrect = QRectF(QPointF(-1000, 1000), QPointF(1000, -1000))
		norm_qrect = QRectF(QPointF(0, 0), QPointF(50, -50))
		warn_qrect = QRectF(QPointF(0, 0), QPointF(100, -300))
		alarm_qrect = QRectF(QPointF(0, 0), QPointF(700, -100))
		
		test_qrect = QRectF(200, 200, 220, 220)
		
		
		bounding = ROILimitObj(bounding_qrect, get_alarm_clr(255), 'Out of Bounds', get_normal_fill_pattern())
		normal = ROILimitObj(QRectF(QPointF(0,0), QPointF(100,-100)), get_normal_clr(25), 'All is Normal', get_normal_fill_pattern())
		warn = ROILimitObj(QRectF(QPointF(0,0), QPointF(250,-250)), get_warn_clr(150), 'Warning', get_warn_fill_pattern())
		alarm = ROILimitObj(QRectF(QPointF(0,0), QPointF(500,-500)), get_alarm_clr(255), 'ALARM the selectoin box is too larg', get_alarm_fill_pattern())
		
		limdef = ROILimitDef(bounding, normal, warn, alarm)
		
# 		print 'testing Normal'
# 		limdef.check_limits(norm_qrect)
# 		print limdef.state_qclr.getRgb()
# 		print limdef.state_label
# 		
# 		print 'testing Warning'
# 		limdef.check_limits(warn_qrect)
# 		print limdef.state_qclr.getRgb()
# 		print limdef.state_label
# 		
# 		print 'testing Alarm'
# 		limdef.check_limits(alarm_qrect)
# 		print limdef.state_qclr.getRgb()
# 		print limdef.state_label
		
		print('\ntesting TEST')
		limdef.check_limits(test_qrect)
		print(limdef.state_qclr.getRgb())
		print(limdef.state_label)
		
		
		
		
			
