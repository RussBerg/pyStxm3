import sys
import time

from bcm.dcs.epics.devices.scan import Scan
from bcm.protocol.ca import PV


class Window(QtWidgets.QWidget):
	"""
	classdocs
	"""
	
	def __init__(self):
		QtWidgets.QWidget.__init__(self)
		#uic.loadUi('C:/controls/py2.7/Beamlines/sm/stxm_control/ui/videoTest.ui', self)
		self.setGeometry(550,550,500,500)
		self.startBtn = QtWidgets.QPushButton("Start Scan")
		self.stopBtn = QtWidgets.QPushButton("Abort Scan")
		self.pauseBtn = QtWidgets.QPushButton("Pause Scan")
		self.clearErrorsBtn = QtWidgets.QPushButton("Clear Errors")
		self.reloadBtn = QtWidgets.QPushButton("Reload Scan")
		
		self.statusLbl = QtWidgets.QLabel("")
		
		
		self.startBtn.clicked.connect(self.on_start_clicked)
		self.stopBtn.clicked.connect(self.on_stop_clicked)
		self.pauseBtn.clicked.connect(self.on_pause_clicked)
		self.pauseBtn.setCheckable(True)
		self.clearErrorsBtn.clicked.connect(self.on_clear_errors)
		self.reloadBtn.clicked.connect(self.on_reload_clicked)
		self.is_paused = False
		
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.startBtn)
		layout.addWidget(self.stopBtn)
		layout.addWidget(self.pauseBtn)
		layout.addWidget(self.reloadBtn)
		layout.addWidget(self.clearErrorsBtn)
		layout.addWidget(self.statusLbl)
		
		
		self.setLayout(layout)
		self.sscans = {}
		
		for i in range(1,16):
			sscan = Scan('ambstxm:energy:scan%d' % i)
			scanparms = PV('ambstxm:energy:scan%d:scanParms.LOAD' % i)
			abort_pv = PV('ambstxm:energy:AbortScans.PROC')
			pause_pv = PV('ambstxm:energy:scanPause.VAL')
			#clear_all_pv = PV('ambstxm:energy:clear')
			clear_errors_pv = PV('ambstxm:energy:clear_errors')
			
			
			self.sscans[i] = {'sscan': sscan, 'scanparms': scanparms, 'abort': abort_pv, 'pause': pause_pv, 'clear_errors':clear_errors_pv}
		
		#self.sscans[16] = {'sscan': Scan('ambstxm:imglxl:scan2'), 'scanparms': epics.PV('ambstxm:imglxl:scan2:scanParms.LOAD') }
		#self.sscans[17] = {'sscan': Scan('ambstxm:imglxl:scan1'), 'scanparms': epics.PV('ambstxm:imglxl:scan1:scanParms.LOAD') }
		
		self.num_scans = len(self.sscans)
		self.topLvlScan = self.sscans[9] 
		self.topLvlScan['sscan'].add_callback('SMSG', self.on_status_str)
		
		self.statusLbl.setText(self.topLvlScan['sscan'].get('SMSG'))
	
	def on_clear_errors(self):
		self.topLvlScan['clear_errors'].put(1)
		
	def on_status_str(self,  **kw):
		s = kw['char_value']
		self.statusLbl.setText(s)
		
	def on_start_clicked(self):
		print('on_start_clicked clicked')
		self.topLvlScan['sscan'].put('EXSC', 1)
		
	def on_stop_clicked(self):
		print('on_stop_clicked clicked')
		for i in range(3):
			self.topLvlScan['abort'].put(1)
			time.sleep(0.1)
	
	def on_pause_clicked(self, chkd):
		print('on_clear_clicked clicked')
		if(chkd):
			self.topLvlScan['pause'].put(1)
			self.is_paused = True
		else:
			self.topLvlScan['pause'].put(0)
			self.is_paused = False
		
	def on_reload_clicked(self):
		print('on_reload_clicked clicked')
		for i in range(3,self.num_scans):
			self.sscans[i]['scanparms'].put(1)
		

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)

	window = Window()
	window.show()
	sys.exit(app.exec_())