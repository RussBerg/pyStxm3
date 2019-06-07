'''
Created on 2013-10-04

@author: bergr
'''
from PyQt5 import QtGui, QtCore

import atexit
import smtplib
from email.mime.text import MIMEText



class BaseNotification(QtCore.QObject):
	""" a class to take a message and send it via email
	"""
	
	def __init__(self, server='smtp.gmail.com', port=587, fromaddr='whiskeypistols@gmail.com', toaddrs=['russ.berg@lightsource.ca', 'whiskeypistols@gmail.com'], username='whiskeypistols', password='dfJaltni'):
		"""
		This class is used to create a notification connection to an email address, such that an email can be sent when an event occurs
		
		:param server: The text that describes the image acquisition params
		:type server: str
		:param fromaddr: A 2d numpy arra of the image data
		:type fromaddr: 2d numpy array of integers
		:param toaddrs: A 2d numpy arra of the image data
		:type toaddrs: 2d numpy array of integers
		:param username: A 2d numpy arra of the image data
		:type username: 2d numpy array of integers
		:param password: A 2d numpy arra of the image data
		:type password: 2d numpy array of integers
		
		:returns None:
		
		"""
		QtCore.QObject.__init__(self)
		self.server_str = server + ':%d' % port 
		self.fromaddr = fromaddr
		self.toaddrs = toaddrs
		self.username = username
		self.password = password
		
		self.attachment = None
		self.email_type = 'acsii'
		self.server = smtplib.SMTP(self.server_str)
		self.server.starttls()
		self.server.login(self.username,self.password)
		atexit.register(self.close)
	
	
	def send(self, msg):
		mime_msg = MIMEText(msg)
		mime_msg['Subject'] = 'Update Notification'
		mime_msg['From'] = self.fromaddr
		
		for addr in self.toaddrs:
			mime_msg['To'] = addr
			self.server.sendmail(self.fromaddr, addr,  mime_msg.as_string())
			print('BaseNotification: email sent to [%s]' % addr)
	
	def close(self):
		print('BaseNotification: quitting server')
		self.server.quit()


if __name__ == '__main__':
	import sys

	#app = QtWidgets.QApplication(sys.argv)
	

	fromaddr = 'whiskeypistols@gmail.com'
	toaddrs  = 'dabergs@shaw.ca'
	msg = 'There was a terrible error that occured and I wanted you to know!'
	
	bnotif = BaseNotification(server='smtp.gmail.com', port=587, fromaddr='whiskeypistols@gmail.com', toaddrs=['russ.berg@lightsource.ca', 'whiskeypistols@gmail.com'], username='whiskeypistols', password='dfJaltni')
	bnotif.send('Here is a test notification')
	#sys.exit(app.exec_())


