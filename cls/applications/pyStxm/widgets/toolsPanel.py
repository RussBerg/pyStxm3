'''
Created on Sep 9, 2016

@author: bergr
'''
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import time
import queue
import atexit

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES
from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.utils.log import get_module_logger, log_to_qt
from cls.applications.pyStxm.widgets.piezoRecalibrate import PiezoRecalibPanel
#from cls.caWidgets.caLabelWidget import assign_aiLabelWidget

# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


class ToolsPanel(QtWidgets.QWidget):
    '''
    This is a widget that is given a list of pv's that MUST exist in the MAIN_OBJ dict and creates Qlabel and ca_aiLabel
    for each 
    
    :returns:  None
    '''
    def __init__(self):
        super(ToolsPanel, self).__init__()
        self.setMinimumSize(100, 100)
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setContentsMargins(0,0,0,0)
        self.vbox.setSpacing(0)
        
        self.setLayout(self.vbox)        
        
        self.piezoRecalWidget = PiezoRecalibPanel()
        self.addWidget(self.piezoRecalWidget)
        
        #atexit.register(self.on_exit)
    
    def addWidget(self, widg):
        self.vbox.addWidget(widg)    
    
    def on_exit(self):
        #print 'on_exit'
        pass
        
if __name__ == '__main__':
    
    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    window2 = ToolsPanel()
    #p = PiezoRecalibPanel()
    #window2.addWidget(p)
    window2.show()
    app.exec_()
    


    
    
    
    
    