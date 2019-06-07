'''
Created on Aug 26, 2014

@author: bergr
'''
'''
Created on Aug 26, 2014

@author: bergr
'''
import  sys 
from PyQt5 import QtCore , QtGui, QtWidgets

from spyder.widgets import internalshell 

class Window(QtWidgets.QMainWindow):
	
	def __init__(self, parent=None):
		super(Window, self).__init__(parent)
		self.setup_dock()
		#self.setup_widget()
		
		
	def setup_dock(self):
		self.pythonshell = ShellDock()
		self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.pythonshell)
	
	def setup_widget(self):
		self.pythonshell = ShellWidget(self)
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0)
		self.layout.addWidget(self.pythonshell)
		#self.layout().addWidget(self.pythonshell)

		
		
class ShellDock(QtWidgets.QDockWidget):
	ALLOWED_AREAS = QtCore.Qt.AllDockWidgetAreas
	LOCATION = QtCore.Qt.TopDockWidgetArea
	FEATURES = QtWidgets.QDockWidget.DockWidgetClosable | \
			   QtWidgets.QDockWidget.DockWidgetFloatable | \
			   QtWidgets.QDockWidget.DockWidgetMovable
	def __init__(self, ):
		super(ShellDock, self).__init__("Python Shell")
		self.pythonshell = internalshell.InternalShell(self, namespace=globals(),commands=[], multithreaded=False)
		self.setWidget(self.pythonshell)
		self.setup()
			
	def setup(self):
		
		self.setAllowedAreas(self.ALLOWED_AREAS)
		self.setFeatures(self.FEATURES)
		#self.setWidget(self)
		
		font = QtGui.QFont("Courier new")
		font.setPointSize(8)
		self.pythonshell.set_font(font)
		self.pythonshell.set_codecompletion_auto(True)
		self.pythonshell.set_calltips(True)
		self.pythonshell.setup_calltips(size=600, font=font)
		self.pythonshell.setup_completion(size=(300, 180), font=font)


class ShellWidget(QtWidgets.QWidget):
	name = "Python Console"
	
	def __init__(self, parent=None, namespace=globals(),commands=[], multithreaded=False):
		super(ShellWidget, self).__init__(parent)
		self.setObjectName('pyConsole')
		#self.pythonshell = internalshell.InternalShell(parent, namespace=namespace,commands=commands, multithreaded=multithreaded)
		#parent=None, namespace=None, commands=[], message="",
		#		 max_line_count=300, font=None, debug=False, exitfunc=None,
		#		 profile=False, multithreaded=True, light_background=True):
		self.pythonshell = internalshell.InternalShell(parent, namespace=namespace,commands=commands, multithreaded=multithreaded,light_background=False)
		
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget(self.pythonshell)
		self.setup()
		self.setLayout(layout)
		
			
	def setup(self):
		font = QtGui.QFont("Courier new")
		font.setPointSize(8)
		self.pythonshell.set_font(font)
		self.pythonshell.set_codecompletion_auto(True)
		self.pythonshell.set_calltips(True)
		#self.pythonshell.setup_calltips(size=600, font=font)
		#self.pythonshell.setup_completion(size=(300, 180), font=font)
		self.pythonshell.setup_completion()
		
	def paintEvent(self, evt):
		super(ShellWidget,self).paintEvent(evt)
		opt = QtWidgets.QStyleOption()
		opt.initFrom(self)
		p = QtGui.QPainter(self)
		s = self.style()
		s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self) 

if __name__ == '__main__':
	
	#motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
	app = QtWidgets.QApplication(sys.argv)
	
	#log_to_qt()
	#shell = Window()
	shell = ShellWidget()
	shell.show()
	sys.exit(app.exec_())