'''
Created on 2014-07-15

@author: bergr
'''
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import time
import queue
import atexit

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, POS_TYPE_BL, POS_TYPE_ES
from bcm.devices.device_names import *
from cls.applications.pyStxm.widgets.piezo_recal import piezo_recal
 
from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.utils.log import get_module_logger, log_to_qt

#motor internal status
NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
TIMEOUT, TIMEOUT_BUTDONE              =  -8,  -7
UNKNOWN_ERROR                         =  -5
DONEW_SOFTLIM, DONEW_HARDLIM          =  -4, -3
DONE_OK                               =   0
MOVE_BEGUN, MOVE_BEGUN_CONFIRMED      =   0, 1
NOWAIT_SOFTLIM, NOWAIT_HARDLIM        =   4, 3


#_fbk_not_moving = "background-color: rgb(130,130,130); border: 1px solid gray;"
_fbk_not_moving = master_colors['app_blue']

#_fbk_moving = "background-color: rgb(240, 88, 33);"
_fbk_moving = "rgb(254, 233, 0);"
# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


class PiezoRecalibPanel(QtWidgets.QWidget):
    '''
    
    :param positioner_set: a string that is used to decide which positioners to include on the panel. Supported
            options are:
                'endstation'
                'beamline'
        
    :type string:  
    
    :returns:  None
    '''
    def __init__(self):
        super(PiezoRecalibPanel, self).__init__()
        
        
        self.posner_list = [DNM_SAMPLE_X, DNM_SAMPLE_Y, DNM_ZONEPLATE_X, DNM_ZONEPLATE_Y]
        self.fbk_enabled = False
        self.mtr = None    
        
        self.mtr_dict = {}
        
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setContentsMargins(0,0,0,0)
        self.vbox.setSpacing(0)
        
        self.styleBtn = QtWidgets.QPushButton('Update Style')
        self.styleBtn.clicked.connect(self.on_update_style)
        
        #self.vbox.addWidget(self.styleBtn)
        self.updateQueue = queue.Queue()
        
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.update_widgets)
        
        
        self.setLayout(self.vbox)        
        self.mtr_dict = {}
        #self.qssheet = get_style('dark')
        #self.setStyleSheet(self.qssheet)
        
        devs = MAIN_OBJ.get_devices()
        #DEVICE_CFG.get_device_list()
        for posner in self.posner_list:
            posner_ui = piezo_recal()
            mtr = MAIN_OBJ.device(posner)
            #dev_ui.setPosFld.installEventFilter(Filter())
            #mtr = MAIN_OBJ.device(dev)
            #self.mtr_dict[mtr.get_name()] = ( posner, posner_ui, mtr)
            self.connect_motor_widgets(posner, posner_ui, mtr)
            #_logger.debug('DONE uic.loadUi [%s]' % dev)
            #print 'positioner: [%s] pvname [%s]' % (dev, mtr.get_name())
        self.updateTimer.start(100)
        self.fbk_enabled = True
        #self.loadMotorConfig(positioner)
        #atexit.register(self.on_exit)
    
    def on_exit(self):
        #print 'on_exit'
        pass
        
            
    def on_update_style(self):
        """ handler for interactive button """
        self.qssheet = get_style('dark')
        self.setStyleSheet(self.qssheet)
                
    def connect_motor_widgets(self, name, mtr_ui, mtr):
        #_logger.debug('connect_motor_widgets[%s]' % name)
        desc = mtr.get('description')
        pv_name = mtr.get_name()

        mtr_ui.recenterBtn.clicked.connect(self.on_recenter)
        
        #self.posner_list = ['SampleFineX', 'SampleFineY', 'ZoneplateX.X', 'ZoneplateY.Y']
        
        mtr_ui.recenterBtn.setText('Recenter %s' % name)
        mtr_ui.recenterBtn.setToolTip(pv_name)
        
        mtr.add_callback('done_moving', self.updateMoving)
        #_logger.debug('add_callback(RBV [%s]' % name)
        mtr.add_callback('RBV', self.updateFbk)
        
        #_logger.debug('getting RBV,EGU for [%s]' % name)
        fbk = mtr.get_position()
        #_logger.debug('add_callback(EGU [%s]' % name)
        #units = str(mtr.get('EGU'))
        #_logger.debug('done connecting [%s]' % name)
        s = '%6.3f' % fbk
        mtr_ui.posFbkLbl.setText(s)
        self.mtr_dict[mtr.get_name()] = ( name, mtr_ui, mtr)
        #mtr_ui.unitsLbl.setText(units)
            
        #elif(hasattr(mtr, 'changed')):
        #    #print 'Standard PV: unsupported positioner [%s]' % name
        #    pass
        #else:
        #    print 'unsupported positioner [%s]' % name
        
        self.vbox.addWidget(mtr_ui)
        #_logger.debug('Done[%s] \n\n' % name)
    
    def on_recenter(self):
        btn = self.sender()
        #txt = str(btn.text())
        pv_name = str(btn.toolTip().toAscii().data())
        txt, mtr_ui, mtr = self.mtr_dict[pv_name]
         
        if(txt.find(DNM_SAMPLE_X) > -1):
            #mtr = self.mtr_dict[DNM_SAMPLE_X]
            mtr.put('AtzSetCoarsePos', 1)
        elif(txt.find(DNM_SAMPLE_Y) > -1):
            #mtr = self.mtr_dict[DNM_SAMPLE_Y]
            mtr.put('AtzSetCoarsePos', 1)
        elif(txt.find(DNM_ZONEPLATE_X) > -1):
            #mtr = self.mtr_dict[DNM_ZONEPLATE_X]
            mtr.put('AutoZero', 1)
        elif(txt.find(DNM_ZONEPLATE_Y) > -1):
            #mtr = self.mtr_dict[DNM_ZONEPLATE_Y]
            mtr.put('AutoZero', 1)
        else:
            _logger.error('on_recenter: Unrecognized motor [%s]' % txt)    
            
    
    def on_editing_finished(self):
        print('on_editing_finished')    
    
    def update_widgets(self):
        call_task_done = False
        while not self.updateQueue.empty():
            resp = self.updateQueue.get()
            if('setStyleSheet' in list(resp.keys())):
                for ss in resp['setStyleSheet']:
                    widget = ss[0]
                    clr_str = ss[1]
                    #print 'update_widgets: setStyleSheet(%s)' % clr_str
                    widget.setStyleSheet(clr_str)
                    call_task_done = True
            
            if('setText' in list(resp.keys())):
                widget = resp['setText'][0]
                _str = resp['setText'][1]
                #print 'update_widgets: setText(%s)' % _str
                widget.setText(_str)
                call_task_done = True
                
        if(call_task_done):
            self.updateQueue.task_done() 
        
        
    def stop(self):
        fld = self.sender()
        pvname = str(fld.statusTip())
        (dev, dev_ui, mtr) = self.mtr_dict[pvname]
        mtr.stop()

    def updateMoving(self, **kwargs):
        """ do not try to set a widget property here as
        it will eventually scew up teh main GUI thread
        Hence the use of a Queue and QTimer
        """
        pvname =  kwargs['pvname'].split('.')[0]
        (dev, dev_ui, mtr) = self.mtr_dict[pvname]
        val = float(kwargs['value'])
        txt_clr = "color: black;"
        #this is for the DMOV or DONE Moving, I want Moving so invert logic
        if(val):
            clr_str = _fbk_not_moving
            #txt_clr = "color: black;"
        else:
            clr_str = _fbk_moving
            #txt_clr = "color: white;"
        
        _dct = {}
        _dct['setStyleSheet'] = [(dev_ui.recenterBtn, "background-color: " + clr_str), (dev_ui.posFbkLbl, txt_clr)]
        self.updateQueue.put_nowait(_dct)
        
         
    
    def updateFbk(self, **kwargs):
        """ do not try to set a widget property here as
        it will eventually scew up teh main GUI thread
        Hence the use of a Queue and QTimer
        """
        if(self.fbk_enabled is True):
            pvname =  kwargs['pvname'].split('.')[0]
            (dev, dev_ui, mtr) = self.mtr_dict[pvname]
            val = float(kwargs['value'])
            s = '%6.3f' % val
            _dct = {}
            _dct['setText'] = (dev_ui.posFbkLbl, s)
            self.updateQueue.put_nowait(_dct) 
    
    
    def contextMenuEvent(self, event):
        fld = self.sender()
        if(fld):
            pvname = str(fld.statusTip())
            (dev, dev_ui, mtr) = self.mtr_dict[pvname]
            
            #self._pvs['VAL'].connected
            if(mtr._pvs['VAL'].connected):
                hlm = mtr.get_high_limit()
                llm = mtr.get_low_limit()
                
                if((llm is not None) and (hlm is not None)):
                    ma_str = 'move %s absolute between %.2f and %.2f' % (dev, llm, hlm)
            else:
                ma_str = 'Motor %s not connected' % (dev)
                
            self.menu = QtWidgets.QMenu(self)
            renameAction = QtWidgets.QAction(ma_str, self)
            renameAction.triggered.connect(self.renameSlot)
            self.menu.addAction(renameAction)
            # add other required actions
            self.menu.popup(QtGui.QCursor.pos())
        


def go():
    app = QtWidgets.QApplication(sys.argv)
    #window = PiezoRecalibPanel('beamline')
    #window.show()
    window2 = PiezoRecalibPanel()
    window2.show()
    
    app.exec_()
    
    
def profile_it():
    
    #determine_profile_bias_val()
    
    profile.Profile.bias = 9.95500362835e-07
    
    profile.run('go()', 'testprof.dat')
    
    p = pstats.Stats('testprof.dat')
    p.sort_stats('cumulative').print_stats(100)
    
        
if __name__ == '__main__':
    import profile
    import pstats
    log_to_qt()
    go()
    #profile_it()
    
    #test()
    


    
    
    
    
    