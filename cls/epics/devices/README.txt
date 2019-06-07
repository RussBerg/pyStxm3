Callbacks:
Given the fallowing:

import epics
import time
import threading
import sys
import numpy
import os

from PyQt4.QtGui import (QMainWindow, QWidget)
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4 import uic

from epics.devices import ai

		class caTest(ai):
		    def __init__(self, prefix):
		        
		        """ 
		        Simple implementation of SynApps Scaler Record.   
		        """
		        self.attrs = ('.VAL')
		        #chan_attrs = ('.NM%i', '.S%i','_calc%i.VAL', '_calc%i.CALC')
		
		        
		        #epics.Device.ai.__init__(self, prefix, attrs=self.attrs)
		        ai.__init__(self, prefix)
		        self.prefix = prefix
		        self.add_callback('VAL', self._signal_change)
		
		        
		        
		
		
		    def _signal_change(self, **kw):
		        print 'signal changed:'
		        print kw
		        print kw['value']
		
		        
		    #def get_value(self):
		    #    pass
		    #    #a = self.A.get()
		    #    #return a
		    
		   
		
		class test(QWidget):
		    """Test"""
		    # -- Create QApplication
		    # --    
		    def __init__(self):
		        QWidget.__init__(self)
		        self.win = caTest('TRG2400:cycles')
		
		if __name__ == "__main__":
		    import guidata
		    app = guidata.qapplication()
		
		    win = test()
		    
		    win.resize(300,300)
		    win.show()
		    app.exec_()

    
	
the callback will be called with kw being set to the following dictionary:

	{
		'lower_disp_limit': None, 
		'char_value': '12959820', 
		'chid': 72481816, 
		'severity': None, 
		'upper_ctrl_limit': None, 
		'read_access': True, 
		'access': 'read-only', 
		'ftype': 5, 'units': None, 
		'lower_ctrl_limit': None, 
		'write_access': False, 
		'type': 'long', 
		'pvname': 'TRG2400:cycles.VAL', 
		'status': 1, 
		'cb_info': (1, <bound method PV.remove_callback of <PV 'TRG2400:cycles.VAL', count=1, type=long, access=read-only>>), 
		'upper_disp_limit': None, 
		'timestamp': 1299532022.6400001, 
		'lower_alarm_limit': None, 
		'precision': None, 
		'host': 'epicsgw-400.clsi.ca:5064', 
		'upper_alarm_limit': None, 
		'count': 1, 
		'value': 12959820, 
		'enum_strs': None, 
		'lower_warning_limit': None, 
		'upper_warning_limit': None
	}