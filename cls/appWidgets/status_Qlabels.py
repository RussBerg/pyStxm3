'''
Created on 2013-01-08

@author: bergr
'''

from PyQt5 import QtCore, QtGui


#the following are QtPallete color schemes for providing status labels in an application

def gen_palette(txt_color=QtGui.QColor('gray'), bg_color=QtGui.QColor('black')):
	pal = QtGui.QPalette()
	pal.setColor(QtGui.QPalette.WindowText, txt_color)
	pal.setColor(QtGui.QPalette.Window, bg_color)
	return(pal)

#setup standard palettes
normal_palette = gen_palette()
#ready_palette = gen_palette(QtGui.QColor('black'),QtGui.QColor('lightGray')) 
ready_palette = gen_palette(QtGui.QColor('black'),QtGui.QColor('lightGreen'))
#busy_palette = gen_palette(QtGui.QColor('white'),QtGui.QColor('green'))
busy_palette = gen_palette(QtGui.QColor('white'),QtGui.QColor('red'))
warning_palette = gen_palette(QtGui.QColor('black'),QtGui.QColor('yellow'))
error_palette = gen_palette(QtGui.QColor('black'),QtGui.QColor('red'))
alert_palette = gen_palette(QtGui.QColor('white'),QtGui.QColor('darkRed'))

normal_sts = {'type':'NORMAL','text':'','palette':ready_palette,'setAutoFill':True}
ready_sts = {'type':'READY','text':'READY','palette':ready_palette,'setAutoFill':True}
busy_sts = {'type':'BUSY','text':'BUSY','palette':busy_palette,'setAutoFill':True}
warning_sts = {'type':'WARNING','text':'WARNING','palette':warning_palette,'setAutoFill':True}
error_sts = {'type':'ERROR','text':'ERROR','palette':error_palette,'setAutoFill':True}
alert_sts = {'type':'ALERT','text':'ALERT','palette':error_palette,'setAutoFill':True}


def create_status_QLabel(text, typ='NORMAL', lbl=None):   
	''' create a new QLabel with the given text and assign it the 
	background and foreground colors of the given type 
	'''
	if(lbl is None):
		lbl = QtWidgets.QLabel(text)
	else:
		lbl.setText(text)
	lbl = assign_status_colors(lbl, typ)
	return(lbl)

def make_into_status_QLabel(lbl, text, typ='NORMAL'):
	lbl.setText(text)
	lbl = assign_status_colors(lbl, typ)

def set_status(lbl, typ='NORMAL'):
	lbl.setText(typ)
	assign_status_colors(lbl, typ)

def assign_status_colors(lbl, typ='NORMAL'):   
	''' take an existing QLabel and assign it the 
	background and foreground colors of the given type 
	'''
	if(typ.find('NORMAL') > -1):
		lbl.setAutoFillBackground(normal_sts['setAutoFill'])
		lbl.setPalette(normal_sts['palette'])
	if(typ.find('READY') > -1):
		lbl.setAutoFillBackground(ready_sts['setAutoFill'])
		lbl.setPalette(ready_sts['palette'])
	if(typ.find('BUSY') > -1):
		lbl.setAutoFillBackground(busy_sts['setAutoFill'])
		lbl.setPalette(busy_sts['palette'])
	if(typ.find('WARNING') > -1):
		lbl.setAutoFillBackground(warning_sts['setAutoFill'])
		lbl.setPalette(warning_sts['palette'])
	if(typ.find('ERROR') > -1):
		lbl.setAutoFillBackground(error_sts['setAutoFill'])
		lbl.setPalette(error_sts['palette'])
	if(typ.find('ALERT') > -1):
		lbl.setAutoFillBackground(alert_sts['setAutoFill'])
		lbl.setPalette(alert_sts['palette'])
	
	return(lbl)

