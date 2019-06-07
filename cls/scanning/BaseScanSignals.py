'''
Created on Sep 26, 2016

@author: bergr
'''
from PyQt5 import QtCore

class BaseScanSignals(QtCore.QObject):
    """
    The base signals provided in the API for scans, this class provides the following signals to every sscan record
    
    :signal started: The sscan has started
    :signal stopped: The sscan has stopped
    :signal done: The sscan is done
    :signal data_ready: If the sscan is the data_level then when it is done emit data_ready signal
    :signal status: , QtCore.pyqtSignal(object)
    :signal progress: The progress in % complete of the current scan, QtCore.pyqtSignal(object)
    :signal aborted: The sscan has aborted, QtCore.pyqtSignal(object) 
    :signal abort_scan: The sscan has been requested to abort the scan

    :returns: None
     
    """
    started = QtCore.pyqtSignal(object)
    stopped = QtCore.pyqtSignal(object)
    done = QtCore.pyqtSignal() 
    data_ready = QtCore.pyqtSignal()
    status = QtCore.pyqtSignal(object) #roi object, data
    progress = QtCore.pyqtSignal(object) #progress
    aborted = QtCore.pyqtSignal(object) #True
    changed = QtCore.pyqtSignal(object) #dct
    abort_scan = QtCore.pyqtSignal()
    
    
    def __init__(self, parent=None):
        """
        __init__(): description

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        QtCore.QObject.__init__(self, parent)
    
    
if __name__ == '__main__':
    pass