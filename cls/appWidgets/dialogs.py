'''
Created on 2012-05-25

@author: bergr
'''
#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##	 notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##	 notice, this list of conditions and the following disclaimer in
##	 the documentation and/or other materials provided with the
##	 distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##	 the names of its contributors may be used to endorse or promote
##	 products derived from this software without specific prior written
##	 permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


import sys, os
import traceback
import time
import io
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
uiDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui')

class Dialog(QtWidgets.QDialog):
	MESSAGE = "<p>Message boxes have a caption, a text, and up to three " \
			"buttons, each with standard or custom texts.</p>" \
			"<p>Click a button to close the message box. Pressing the Esc " \
			"button will activate the detected escape button (if any).</p>"

	def __init__(self, parent=None):
		super(Dialog, self).__init__(parent)

		self.openFilesPath = ''
		self.errorMessageDialog = QtWidgets.QErrorMessage(self)
		#self.setWindowTitle("Standard Dialogs")
		self.native = QtWidgets.QCheckBox()
		self.native.setText("Use native file dialog.")
		self.native.setChecked(True)
		if sys.platform not in ("win32", "darwin"):
			self.native.hide()

	def setInteger(self, title, msg, min, max, incr, val=0):	
		i, ok = QtWidgets.QInputDialog.getInt(self,
				title, 
				msg + ':', val, min, max, incr)
		return i
		#if ok:
		#	self.integerLabel.setText("%d%%" % i)

	def setDouble(self, title, msg, min, max, incr, val=0):	
		d, ok = QtWidgets.QInputDialog.getDouble(self, title,
				msg + ":", val, min, max, incr)
		return d
		#if ok:
		#	self.doubleLabel.setText("$%g" % d)

	def setItem(self, title, msg, item_strs):	
		
		items = item_strs
		item, ok = QtWidgets.QInputDialog.getItem(self, title,
				msg + ":", items, 0, False)
		return item
		#if ok and item:
		#	self.itemLabel.setText(item)

	def setText(self, title, msg):
		text, ok = QtWidgets.QInputDialog.getText(self, title,
				msg + ":", QtWidgets.QLineEdit.Normal,
				QtCore.QDir.home().dirName())
		return str(text)
		#if ok and text != '':
		#	self.textLabel.setText(text)

	def setColor(self):	
		color = QtGui.QColorDialog.getColor(QtCore.Qt.green, self)
		return color
		#if color.isValid(): 
		#	self.colorLabel.setText(color.name())
		#	self.colorLabel.setPalette(QtGui.QPalette(color))
		#	self.colorLabel.setAutoFillBackground(True)

	def setFont(self):	
		font, ok = QtGui.QFontDialog.getFont(QtGui.QFont(""), self)
		return font
		#if ok:
		#	self.fontLabel.setText(font.key())
		#	self.fontLabel.setFont(font)

	def setExistingDirectory(self, title, init_dir=""):
		#QFileDialog::QFileDialog(QWidget * parent = 0, const QString & caption = QString(), const QString & directory = QString(), const QString & filter = QString())	
		options = QtWidgets.QFileDialog.DontResolveSymlinks | QtWidgets.QFileDialog.ShowDirsOnly
		directory = QtWidgets.QFileDialog.getExistingDirectory(self,
				title,
				init_dir, options)

		return str(directory)
		#if directory:
		#	self.directoryLabel.setText(directory)
	
	def getSaveFileName(self, title, fname_str, filter_str="All Files (*);;Text Files (*.txt)", search_path=None):
		options = QtWidgets.QFileDialog.Options()

		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		#fileName = QtWidgets.QFileDialog.getSaveFileName(self,
		#		title,
		#		fname_str,
		#		filter_str, '', options)
		#fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save as...", filter_str, dir=search_path)
		#QString QFileDialog::getSaveFileName(QWidget *parent = Q_NULLPTR, const QString &caption = QString(), const QString &dir = QString(), const QString &filter = QString(), QString *selectedFilter = Q_NULLPTR, Options options = Options())
		fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, title, search_path, filter_str, '*', options)
		return str(fileName)
	
	def setOpenFileName(self, title, fname_str, filter_str="All Files (*);;Text Files (*.txt)"):	
		options = QtWidgets.QFileDialog.Options()
		
		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		fileName = QtWidgets.QFileDialog.getOpenFileName(self,
				title,
				fname_str,
				filter_str, '', options)
		return str(fileName)
		#if fileName:
		#	self.openFileNameLabel.setText(fileName)

	def setOpenFileNames(self, title, filter_str="All Files (*);;Text Files (*.txt)"):	
		options = QtWidgets.QFileDialog.Options()
		
		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		files = QtWidgets.QFileDialog.getOpenFileNames(self,
				title, self.openFilesPath,
				filter_str, '', options)
		if(len(files[0]) > 0):
			return str(files[0][0])
		else:
			print('No file selected')
			return(None) 
		
	def getOpenFileName(self, title, filter_str="All Files (*);;Text Files (*.txt)", search_path=''):	
		options = QtWidgets.QFileDialog.Options()
		
		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		files = QtWidgets.QFileDialog.getOpenFileNames(self,
				title, search_path,
				filter_str, '', options)
		#if(not files.isEmpty()):
		if(len(files[0]) > 0):
			return str(files[0][0])
		else:
			print('No file selected')
			return(None)

	def getOpenFileNames(self, title, filter_str="All Files (*);;Text Files (*.txt)", search_path=''):
		options = QtWidgets.QFileDialog.Options()

		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		files = QtWidgets.QFileDialog.getOpenFileNames(self,
													   title, search_path,
													   filter_str, '', options)
		# if(not files.isEmpty()):
		if (len(files[0]) > 0):
			return (files[0])
		else:
			print('No file selected')
			return (None)

	def setSaveFileName(self, title, fname_str, filter_str="All Files (*);;Text Files (*.txt)"):	
		options = QtWidgets.QFileDialog.Options()
		if not self.native.isChecked():
			options |= QtWidgets.QFileDialog.DontUseNativeDialog
		fileName = QtWidgets.QFileDialog.getSaveFileName(self,
				title,
				fname_str,
				filter_str,'', options)
		return str(fileName)
		#if fileName:
		#	self.saveFileNameLabel.setText(fileName)

	def criticalMessage(self, title, msg, abort_str="Abort", retry_str="Retry", critical_str="Ignore"):	
		reply = QtWidgets.QMessageBox.critical(self, title,
				msg,
				QtWidgets.QMessageBox.Abort | QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Ignore)
		
		if reply == QtWidgets.QMessageBox.Abort:
			return str(abort_str)
		elif reply == QtWidgets.QMessageBox.Retry:
			return str(retry_str)
		else:
			return str(critical_str)

	def informationMessage(self, title, msg="", ok_str="Ok", cancel_str="Cancel"):	
		reply = QtWidgets.QMessageBox.information(self, title, msg)
		
		if reply == QtWidgets.QMessageBox.Ok:
			return str(ok_str)
		else:
			return str(cancel_str)

	def questionMessage(self, title, msg="", yes_str="Yes", no_str="No", cancel_str="Cancel"):	
		reply = QtWidgets.QMessageBox.question(self, title,
				msg,
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
		return str(reply)
		#if reply == QtWidgets.QMessageBox.Yes:
		#	self.questionLabel.setText(yes_str)
		#elif reply == QtWidgets.QMessageBox.No:
		#	self.questionLabel.setText(no_str)
		#else:
		#	self.questionLabel.setText(cancel_str)
		

	def warningMessage(self, title, msg="", accept_str="Save Again", reject_str="Continue"):
		msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
				title, msg,
				QtWidgets.QMessageBox.NoButton, self)
		msgBox.addButton(accept_str, QtWidgets.QMessageBox.AcceptRole)
		msgBox.addButton(reject_str, QtWidgets.QMessageBox.RejectRole)

		if msgBox.exec_() == QtWidgets.QMessageBox.AcceptRole:
			return str(accept_str)
			#self.warningLabel.setText(accept_str)
		else:
			return str(reject_str)
			#self.warningLabel.setText(reject_str)
	
	def notifyMessage(self, title, msg="", accept_str="Understood"):	
		msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
				title, msg,
				QtWidgets.QMessageBox.NoButton, self)
		msgBox.addButton(accept_str, QtWidgets.QMessageBox.AcceptRole)
		if msgBox.exec_() == QtWidgets.QMessageBox.AcceptRole:
			return str(accept_str)

	def errorMessage(self, error_msg):	
		#self.errorMessageDialog.showMessage("This dialog shows and remembers "
		#		"error messages. If the checkbox is checked (as it is by "
		#		"default), the shown message will be shown again, but if the "
		#		"user unchecks the box the message will not appear again if "
		#		"QErrorMessage.showMessage() is called with the same message.")
		#self.errorLabel.setText("If the box is unchecked, the message won't "
		#		"appear again.")
		self.errorMessageDialog.showMessage(error_msg)

	def message_no_btns(self, title, msg):
		msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
									   title, msg,
									   QtWidgets.QMessageBox.NoButton, self)
		msgBox.exec_()
		
		
	
class progress_class(QtWidgets.QWidget):
	
	def __init__(self, parent=None, msg='Loading'):
		super(progress_class, self).__init__(parent)
		uic.loadUi( uiDir + 'progress.ui', self)
		self.msgLabel.setText(msg)
		#self.show()
	
	def set_progress(self, val):
		#print 'progress: %d' % val
		self.progressBar.setValue(val)
		

def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    logFile = "simple.log"
    notice = \
        """An unhandled exception occurred. Please report the problem\n""" \
        """using the error reporting dialog or via email to <%s>.\n""" \
        """A log has been written to "%s".\n\nError information:\n""" % \
        ("russ.berg@lightsource.ca", "")
    versionInfo = "0.0.1"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    errorbox = QtWidgets.QMessageBox()
    errorbox.setText(str(notice) + str(msg) + str(versionInfo))
    errorbox.exec_()



def message_no_btns(title, msg):
	dialog = Dialog()
	ret = dialog.message_no_btns(title, msg)
	return ret


def notify(title, msg, accept_str):
	dialog = Dialog()
	ret = dialog.notifyMessage(title, msg, accept_str)
	return ret

def warn(title, msg, accept_str, reject_str, ss=None, posn=None):
	dialog = Dialog()
	#from PyQt5 import QtGui, QtCore, QtWidgets
	#rect = QtCore.QRect(250, 250, dialog.width(), dialog.height())
	if(posn):
		dialog.setGeometry(QtCore.QRect(posn[0], posn[1],dialog.width(), dialog.height()))

	if(ss):
		dialog.setStyleSheet(ss)
		
	ret = dialog.warningMessage(title, msg, accept_str, reject_str)
	return ret

def info(title, msg, ok_str, cancel_str):
	dialog = Dialog()
	ret = dialog.informationMessage(title, msg, ok_str, cancel_str)
	return ret

def setInteger( msg, min, max, incr, val=0):
	dialog = Dialog()
	ret = dialog.setInteger( msg, min, max, incr, val) 
	return ret
	 
def setDouble(msg, min, max, incr, val=0.0):
	dialog = Dialog()
	ret = dialog.setDouble(msg, min, max, incr, val) 
	return ret   
		
def setItems(title="Set Items", msg="Set the Items", item_strs=()):
	dialog = Dialog()
	ret = dialog.setItem(title, msg, item_strs) 
	return ret 
		
def setText(title="Check This", msg="Set this text"):
	dialog = Dialog()
	ret = dialog.setText(title, msg)
	return ret
	
def setColor():
	dialog = Dialog()
	ret = dialog.setColor()
	return ret  
		
def setFont():
	dialog = Dialog()
	ret = dialog.setFont()
	return ret   
		
def setExistingDirectory(title="Select Directory", init_dir=""):
	dialog = Dialog()
	ret = dialog.setExistingDirectory(title, init_dir)
	return ret

def getSaveFileName(title="Get Filename", fname_str='*', filter_str="Dat Files (*.dat)", search_path=''):
	dialog = Dialog()
	#getSaveFileName(self, title, fname_str, filter_str = "All Files (*);;Text Files (*.txt)", search_path = None):
	ret = dialog.getSaveFileName(title, fname_str, filter_str, search_path=search_path)
	return ret

def getOpenFileName(title="Get Filename", filter_str="Dat Files (*.dat)", search_path=''):
	dialog = Dialog()
	ret = dialog.getOpenFileName(title, filter_str, search_path) 
	return ret

def getOpenFileNames(title="Get Filename", filter_str="Dat Files (*.dat)", search_path=''):
	dialog = Dialog()
	ret = dialog.getOpenFileNames(title, filter_str, search_path)
	return ret

def setOpenFileName(title="Set Filename", fname="untitled.dat", filter_str="Dat Files (*.dat)"):
	dialog = Dialog()
	ret = dialog.setOpenFileName(title, fname, filter_str) 
	return ret

def setOpenFileNames(title="Open Text File", filter_str="All Files (*);;Text Files (*.txt)"):
	dialog = Dialog()
	ret = dialog.setOpenFileNames(title, filter_str)
	return ret
	
def setSaveFileName(title="Save CSV file", fname="untitled.csv", filter_str="CSV Files (*.csv)"):
	dialog = Dialog()
	ret = dialog.setSaveFileName(title, fname, filter_str)
	return ret
	
def criticalMessage(title="Oh Crap!!!", msg="Something has seriously gone wrong now message", abort_str="Abort", retry_str="Retry", critical_str="Ignore"):
	dialog = Dialog()
	ret =  dialog.criticalMessage(title, msg, abort_str, retry_str, critical_str)
	return ret
   
def questionMessage(title="Do you really want to do that?", msg="I am asking you know as a question", yes_str="Yes", no_str="No", cancel_str="Cancel"):
	dialog = Dialog()
	ret = dialog.questionMessage(title, msg, yes_str, no_str, cancel_str)
	return ret	
		 
def errorMessage(msg="you shouldn't have done that \nnow it's all broken" "I hope you are happy"):   
	dialog = Dialog()
	ret = dialog.errorMessage(msg)
	return ret
	
class test_all(object):
	
	def __init__(self):
		object.__init__(self)
		dialog = Dialog()
		info("Info box", "Here is the info you asked for", ok_str="OK", cancel_str="Nope")
		setInteger("set X", "X", -5, 50, 23)	
		setDouble("set Y Position", "Y", -1000, 1000, 342)	
		setItems("Pick One", "Select an Item", ("A", "B", "C", "D"))	
		setText("Enter Text", "Enter a text string here")
		setColor()   
 	 
		setFont()	
		setExistingDirectory("Pick Directory", r'c:\\')	
		getOpenFileName("Set Filename", filter_str="Dat Files (*)", search_path=r'c:/tmp')
		setOpenFileName("Set Filename", "*", filter_str="Dat  Files(*)")	
		setOpenFileNames("Open Text File", filter_str="All Files (*);;Text Files (*.txt)")	
		setSaveFileName("Save CSV file", "data.csv", filter_str="CSV Files (*.csv)")	
		criticalMessage("Oh Crap!!!", "Something has seriously gone wrong now message", abort_str="Abort", retry_str="Retry", critical_str="Ignore")	
		questionMessage("Do you really want to do that?", "I am asking you know as a question", yes_str="Yes", no_str="No", cancel_str="Cancel")	
		warn("Seriously I'm warning you", "Here is the warning message", accept_str="Save Again", reject_str="Continue")	
		errorMessage("you shouldn't have done that" "now it's all broken" "I hope you are happy")	

class test_warn(object):
	def __init__(self):
		notify("WARNING Invalid scan definition",
			 "The number of points required for this scan is larger than the amount available on the E712 controller. Try reducing either the number of points for X or dwell time per point, In short the scan will not execute properly if at all",
			 accept_str="OK")

if __name__ == '__main__':
	from cls.app_data.defaults import get_style
	app = QtWidgets.QApplication(sys.argv)
	#dialog = Dialog()
	#dialog.informationMessage("Info box", ok_str="OK", cancel_str="Nope")
	#tst = test_all()
	#tst = test_warn()
	#msg = message_no_btns('Please Wait', 'Please wait while the scan shuts down')
	ss = get_style('dark')
	ss = 'QWidget{	background-color: rgb(180, 180, 180); font-weight: bold;} QPushButton{	background-color: rgb(208, 208, 208); font-weight: bold;}'
	#ss = 'QWidget{	color: rgb(255, 255, 255); background-color: rgb(77, 77, 77);}'
	resp = warn("Save Data", "Do you want to save this data? [C1234567.hdf5]", accept_str="Yes", reject_str="No",ss=ss)

	#names = getOpenFileNames("Get Filenames", filter_str="hdf5 Files (*.hdf5)", search_path=r'S:\STXM-data\Cryo-STXM\2017\guest\0530')
	# getSaveFileName(self, title, fname_str, filter_str = "All Files (*);;Text Files (*.txt)", search_path = None):
	#name = getSaveFileName("Save Filename", '*.json', filter_str="Json  Files(*.json)", search_path=r'S:\STXM-data\Cryo-STXM\2017\guest\scan_defs')
	#print name
	#dir = setExistingDirectory("Pick Directory", r'c:\\')	
	#print dir
	#setText("Enter Text", "Enter a text string here")
	#setColor()   
	#info("Info box", "Here is the info you asked for", ok_str="OK", cancel_str="Nope")
	#result = warn("Seriously I'm warning you", "Here is the warning message", accept_str="Save Again", reject_str="Continue")
	#print result
	#result = info("Info for you","some info message here", ok_str="Ok", cancel_str="Cancel")
	#print result
	#fname = getOpenFileName("Open File", filter_str="JPG Files (*.jpg)", search_path=r'c:/windows')
	#print 'file to open is %s' % fname

	
	sys.exit(app.exec_())
