'''
Created on 2012-05-29

@author: bergr
'''
#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Hans-Peter Jansen <hpj@urpla.net>.
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
## A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
###########################################################################


# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QString', 2)
import os
import time
from datetime import date
import bz2
from PyQt5 import QtCore, QtGui, uic, QtWidgets

from cls.utils.log import get_module_logger, log_to_console, log_to_qt
from cls.appWidgets.dialogs import questionMessage, info
from cls.appWidgets.enum import Enum

from cls.utils.cfgparser import ConfigClass

_logger = get_module_logger(__name__)

ACCESS_LVLS = Enum(["GUEST","USER", "STAFF", "ADMIN"])

class loginWidget(QtWidgets.QDialog):
	def __init__(self, accnt_mgr=None, modal=True, auto_login=False, parent=None):
		super(loginWidget, self).__init__()
		self.parent = parent
		self._user_accnt_mgr = accnt_mgr
		self._usr_object = None
		
		if(auto_login):
			self.doLogin(auto_login=True)
			return
			
		if(accnt_mgr is None):
			_logger.error("loginWidget: no account manager specified")
			return
		self._userName = ""
		self._password = ""
		
		cwd = os.getcwd()
		self._form = uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'userlogin.ui'), self)
		self.setModal(modal)
		if not modal:
			#print "DELETE ON CLOSE"
			self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		self._form.stackedWidget.setCurrentIndex(0)
		self._logged_in = False
		
		self._form.userNameFld.setFocus()
		self._form.userNameFld.textChanged.connect(self._adjustLoginButton)
		self._form.userNameFld.returnPressed.connect(self._inputPassword)

		self._form.passwordFld.textChanged.connect(self._adjustLoginButton)
		self._form.passwordFld.returnPressed.connect(self.doLogin)
		
		
		self._form.newuserNameFld.setFocus()
		self._form.newuserNameFld.textChanged.connect(self._adjustLoginButton)
		self._form.newuserNameFld.returnPressed.connect(self._inputPassword)

		self._form.confirmpasswordFld.textChanged.connect(self._adjustCreateButton)
		self._form.confirmpasswordFld.returnPressed.connect(self._doCreateUser)

		self._form.loginButton.setEnabled(False)
		self._form.loginButton.clicked.connect(self.doLogin)
		self._form.createBtn.setEnabled(False)
		self._form.createBtn.clicked.connect(self._doCreateUser)
		
		
	def _create_user(self, username, password):
		self._usr_object = self._user_accnt_mgr.add_user(username, password)
		return(self._usr_object)

	def showStatus(self, msg):
		pass
		#self._form.statusLabel.setText(msg)
		#self._form.stackedWidget.setCurrentIndex(0)

	def showError(self, msg):
		pass
		#self._form.progressBar.hide()
		#self.showStatus("Error: %s" % msg)

	def _document(self):
		pass
		#return self._form.webView.page().mainFrame().documentElement()

	def _adjustLoginButton(self):
		self._userName = str(self._form.userNameFld.text())
		self._password = str(self._form.passwordFld.text())
		self._form.loginButton.setEnabled(bool(self._userName and self._password))
 
	def _inputPassword(self):
		if self._form.userNameFld.text():
			self._form.passwordFld.setFocus()
	
	def is_logged_in(self):
		return(self._logged_in)
	
	def doLogin(self, autocreate=True, auto_login=False):
		if(auto_login):
			self._userName = 'guest'
			self._password = 'welcome1'
			(sts, usr_obj, stsmsg) = self._user_accnt_mgr.validate_usernmpassword(str(self._userName), str(self._password))
			self._logged_in = True
			
			usr_obj.create_data_dir()
			self._usr_object = usr_obj
			return(sts, usr_obj)
			
		self._userName = str(self._form.userNameFld.text())
		self._password = str(self._form.passwordFld.text())
		if not (self._userName and self._password):
			return
		if(self._user_accnt_mgr.get_user(self._userName)):
			#user exists so check for valid
			(sts, usr_obj, stsmsg) = self._user_accnt_mgr.validate_usernmpassword(str(self._userName), str(self._password))
			self.msgLbl.setText(stsmsg)
			self.passwordFld.setText('')
			
			if(sts):
				self._logged_in = True
				usr_obj.create_data_dir()
				self.close()
			else:
				self._logged_in = False
			self._usr_object = usr_obj
			return(sts, usr_obj)
		else:
			if(not autocreate):
				ans = questionMessage(title="User does not exist", msg="Do you want to create a new user account?", yes_str="Yes", no_str="No", cancel_str="Cancel")
				#QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
				#QtWidgets.QMessageBox.Cancel
				if(ans == QtWidgets.QMessageBox.Yes):
					#new account page of stack widget
					self._form.newuserNameFld.setText(self._form.userNameFld.text())
					self._form.stackedWidget.setCurrentIndex(1)
				elif(ans == QtWidgets.QMessageBox.No):
					self._form.stackedWidget.setCurrentIndex(0)
				else:
					self._form.stackedWidget.setCurrentIndex(0)
			else:
				#just go ahead and get the user to confirm their password and create the
				#account
				self._form.newuserNameFld.setText(self._form.userNameFld.text())
				self._form.stackedWidget.setCurrentIndex(1)

		
			
	
	def _adjustCreateButton(self):
		self._newuserName = str(self._form.newuserNameFld.text())
		self._newpassword = str(self._form.newpasswordFld.text())
		self._confirmpassword = str(self._form.confirmpasswordFld.text())
		
		self._form.createBtn.setEnabled(bool(self._newpassword and self._confirmpassword))
 
	def _inputCreatePassword(self):
		if self._form.newpasswordFld.text():
			self._form.confirmpasswordFld.setFocus()

	def _doCreateUser(self):
		self._newuserName = str(self._form.newuserNameFld.text())
		self._newpassword = str(self._form.newpasswordFld.text())
		if not (self._newuserName and self._newpassword and self._confirmpassword):
			return
		usr_obj = self._create_user(self._newuserName, self._newpassword)
		if(usr_obj):
			_logger.info('User account created, logging in')
		else:
			_logger.info('User account created, logging in')
		self.close()
		return(usr_obj)
		
	def get_user_obj(self):
		return(self._usr_object)
	
	def hideElements(self):
		pass
#		self.document().findFirst('.footer-footer').removeFromDocument()
#		self.document().findFirst('.title-bar-bg .title-bar').removeFromDocument()
#		QtCore.QTimer.singleShot(2000, self.hideElements)

	def loginPage(self, ok):
		pass


if __name__ == '__main__':

	import sys
	log_to_console()
	app = QtWidgets.QApplication(sys.argv)

	#QtNetwork.QNetworkProxyFactory.setUseSystemConfiguration(True)
	#acct_mgr = user_accnt_mgr()
	login = loginWidget(usr_acct_mgr)
	login.show()

	sys.exit(app.exec_())
