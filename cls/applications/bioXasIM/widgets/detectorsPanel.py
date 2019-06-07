'''
Created on Nov 14, 2016

@author: bergr
'''
import os
from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5 import uic

#from PyQt5.Qt import QToolButton

from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ
from cls.app_data.defaults import  get_style

uiDir = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'ui')

class BaseDetectorDetailDialog(QtWidgets.QDialog):
    
    def __init__(self, name, det, args={}, parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.setModal(True)
        self.titleLbl = QtWidgets.QLabel(name)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.titleLbl)
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)
        
        self.setLayout(layout)
        
        self.dct = {}
        self.dct['name'] = name
        self.dct['det_dev'] = det
        self.dct['args'] = args
        
    def get_cfg(self):
        """
         get all of the devices configuration params here and put into dct
        """
        return(self.dct)


class APD_DetailDialog(BaseDetectorDetailDialog):
    def __init__(self, name, det, args={}, parent=None):
        super(APD_DetailDialog, self).__init__(name, det)
        
class PMT_DetailDialog(BaseDetectorDetailDialog):
    def __init__(self, name, det, args={}, parent=None):
        super(PMT_DetailDialog, self).__init__(name, det)

class DAQMX_DetailDialog(BaseDetectorDetailDialog):
    def __init__(self, name, det, args={}, parent=None):
        super(DAQMX_DetailDialog, self).__init__(name, det)

class EPICS_DetailDialog(BaseDetectorDetailDialog):
    def __init__(self, name, det, args={}, parent=None):
        super(EPICS_DetailDialog, self).__init__(name, det)


def make_detail_detector_form(name, det):
    ddf = EPICS_DetailDialog(name, det)
    if(name.find('PMT') > -1):
        ddf = PMT_DetailDialog(name, det)
    
    if(name.find('APD') > -1):
        ddf = APD_DetailDialog(name, det)    
    
    if(name.find('StorageRingCurrent') > -1):
        ddf = EPICS_DetailDialog(name, det)
    
    return(ddf)

class DetectorItem(QtWidgets.QWidget):
    
    def __init__(self, name, det, details_wdg, parent=None):
        QtWidgets.QWidget.__init__(self,parent)
        self.name = name
        self.dcs_name = det.get_name()
        self.det_cfg = details_wdg.get_cfg()
        
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(2,2,2,2)
        self.detailsWdg = details_wdg
        self.detailsBtn = QtWidgets.QToolButton()
        self.detailsBtn.setToolTip('Config ' + name + ' details')
        #self.radioBtn = QtWidgets.QRadioButton(name)
        self.chkBox = QtWidgets.QCheckBox(name)
        layout.addWidget(self.detailsBtn)
        #layout.addWidget(self.radioBtn)
        layout.addWidget(self.chkBox)
        
        self.detailsBtn.clicked.connect(self.on_show_details)
        #self.radioBtn.clicked.connect(self.on_radio_clicked)
        self.chkBox.clicked.connect(self.on_checkbox_clicked)
        
        self.is_checked = False
        
        self.setLayout(layout)
        
    def on_show_details(self):
        self.detailsWdg.show()
    
    def on_radio_clicked(self, chkd):
        self.is_checked = chkd
    
    def on_checkbox_clicked(self, chkd):
        self.is_checked = chkd
    
    def is_checked(self):
        return(self.is_checked)
    
    def get_name(self):
        return(self.name)
    
    def get_dcs_name(self):
        return(self.dcs_name) 
    


class DetectorsPanel(QtWidgets.QDialog):
    
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self,parent)
        self.widgetList = []
        self.qssheet = get_style('dark')
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(2,2,2,2)
        for detname in MAIN_OBJ.get_device_list(detectors=True):
            det = MAIN_OBJ.device(detname)
            ddf = make_detail_detector_form(detname, det)
            widget = DetectorItem(detname, det, ddf)
            widget.setStyleSheet(self.qssheet)
            self.widgetList.append(widget)
            layout.addWidget(widget)
        self.setLayout(layout)
        
        self.setStyleSheet(self.qssheet)
    
    def get_selected_detectors(self):
        """
        walk all of the detectors and record which ones are checked
        """
        lst = []
        for d in self.widgetList:
            if(d.is_checked):
                dct = {}
                dct['name'] = d.get_name()
                dct['dcs_name'] = d.get_dcs_name()
                lst.append(dct)
        
        return(lst)


        
        

if __name__ == '__main__':
    import sys
    #motorCfgObj = StxmMotorConfig(r'C:\controls\py2.7\Beamlines\sm\stxm_control\StxmDir\Microscope Configuration\Motor.cfg')
    app = QtWidgets.QApplication(sys.argv)
    
    #log_to_qt()
    motorPanel = DetectorsPanel()
    motorPanel.show()
    sys.exit(app.exec_())        

