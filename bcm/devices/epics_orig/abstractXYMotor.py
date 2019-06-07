'''
Created on Aug 31, 2016

@author: bergr
'''

#!/usr/bin/env python
import time
from PyQt5 import QtCore
from bcm.protocol.epics.motor import Motor
# !/usr/bin/env python
import time

from PyQt5 import QtCore
from bcm.protocol.epics.motor import Motor


def get_sample_motor(nm, attrs=[]):
    mtr = Motor(nm)
    for attr in attrs:
        mtr.add_pv('%s%s' % (nm, attr), attr=attr[1:])
    
    return(mtr)

class sampleXYMotor(Motor):
    """
    Represents an XY abstract motor, needs knowledge of the coarse X and Y motors as well as trhe fine X and Y motors
    """

    attrs = ('VAL')
    

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        Motor.__init__(self, prefix, 
                              **kwargs)
        myattrs = (':Mode', ':Mode_RBV', ':ScanStart', ':ScanStop', ':MarkerStart', ':MarkerStop', ':SetMarker', ':ServoPower', ':ServoPower_RBV', ':OutputVolt_RBV')
        
        for attr in myattrs:
            self.add_pv('%s%s' % (prefix, attr), attr=attr[1:])
        
class abstractXYMotor(QtCore.QObject):
    """
    Represents an XY abstract motor, needs knowledge of the coarse X and Y motors as well as trhe fine X and Y motors
    """

    def __init__(self, prefix, **kwargs):
        super(abstractXYMotor, self).__init__()
    
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        self.cx = kwargs['cx'] #coarse X
        self.cy = kwargs['cy'] #coarse Y
        self.fx = kwargs['fx'] #fine X
        self.fy = kwargs['fy'] #fine Y
        self.sx = kwargs['sx'] #Sample X
        self.sy = kwargs['sy'] #Sample Y
        self.prevX_center_pos = 0
        self.prevY_center_pos = 0
        
    def set_prevX_center_pos(self, pos):
        self.prevX_center_pos = pos
    
    def set_prevY_center_pos(self, pos):
        self.prevY_center_pos = pos    
    
    def get_servo_power(self, servos=[]):
        pwr = []
        for mtr in servos:
            pwr.append(mtr.get('ServoPower_RBV'))
        return(pwr)
    
    def put_servo_power(self, servos=[], pwr_lst=[]):
        idx = 0
        for mtr in servos:
            self.servo_power(mtr, pwr_lst[idx])
            idx += 1
    
    def all_servos_off(self, servos=[]):
        for mtr in servos:
            self.servo_power(mtr, 0)
    
    def get_all_volts(self, servos=[]):
        volts = []
        for mtr in servos:
            volts.append(mtr.get('OutputVolt_RBV'))
        return(volts)
    
    def servo_power(self, mtr, val):
        mtr.put('ServoPower', val)
    
    
    def all_servos_on(self, servos=[]):
        for mtr in servos:
            self.servo_power(mtr, 1)
    
    def waitUntilStopped(self, mtr):
        time.sleep(0.4)
        sts = mtr.get('MOVN')
        cnt = 0
        while sts == 1:
            time.sleep(0.02)
            sts = mtr.get('MOVN')
            if(cnt > 9999999):
                sts = 0
            cnt += 1
            
    def moveFineToPrevCenter(self, fmtr, position, prev_center_pos):
        self.servo_power(fmtr, 1)   
        fmtr.put('VAL', prev_center_pos)
        self.waitUntilStopped(fmtr)
        self.servo_power(fmtr, 0) 
    
    def moveAndSet_X_CoarsePosition(self, pos, test_scan_range=False):
        scan_range = 45
        self.moveAnSetCoarsePosition(self.cx, self.cy, self.fx, self.fy, self.sx, self.sy, pos, self.prevX_center_pos)
        self.prevX_center_pos = pos
        
        if(test_scan_range):
            self.fx.put('VAL', pos - scan_range)
            self.waitUntilStopped(self.fx)
            print('checking scan range at center - %d:' % scan_range)
            print(self.get_all_volts([self.fx, self.fy]))
            self.fx.put('VAL', pos + scan_range)
            self.waitUntilStopped(self.fx)
            print('checking scan range at center + %d:' % scan_range)
            print(self.get_all_volts([self.fx, self.fy]))
            self.fx.put('VAL', pos + 10 )
        
    def moveAndSet_Y_CoarsePosition(self, pos, test_scan_range=False):
        scan_range = 45
        self.moveAnSetCoarsePosition(self.cy, self.cx, self.fy, self.fx, self.sy, self.sx, pos, self.prevY_center_pos)
        self.prevY_center_pos = pos
        if(test_scan_range):
            self.fy.put('VAL', pos - scan_range)
            self.fy.put('VAL', pos + scan_range)
            self.fy.put('VAL', pos + 10 )
    
        
    def moveAndSet_XY_CoarsePosition(self, pos):
        pass    
        
    
    def moveAnSetCoarsePosition(self, cmtr1, cmtr2, fmtr1, fmtr2, smtr1, smtr2, pos, prev_center_pos):
        
        prev_pwr_states = self.get_servo_power([fmtr1, fmtr2])
        
        self.moveFineToPrevCenter(fmtr1, pos, prev_center_pos)
            
        self.all_servos_off([fmtr1, fmtr2])
        cmtr1.put('VAL', pos)
        
        self.waitUntilStopped(cmtr1)
        
        cmtr1_fbk = cmtr1.get('RBV')
        smtr1.set_position(cmtr1_fbk)
        
        cmtr2_fbk = cmtr2.get('RBV')
        smtr2.set_position(cmtr2_fbk)
        
        #all_servos_on()
        self.put_servo_power([fmtr1, fmtr2], prev_pwr_states)
        smtr1.put('VAL', pos)
        smtr2.put('VAL', cmtr2_fbk)

if __name__ == '__main__':
    from bcm.protocol.epics.motor import Motor

    ZONEPLATE_MODE = False
    
    sx = sampleXYMotor('IOC:m117')
    #sx = sample_motor('IOC:m117')
    
    sy = sampleXYMotor('IOC:m118')
    
    if(ZONEPLATE_MODE):
        fx = sampleXYMotor('IOC:m102')
        fy = sampleXYMotor('IOC:m103')
    else:    
        fx = sampleXYMotor('IOC:m100')
        fy = sampleXYMotor('IOC:m101')
    
        
    cx = Motor('IOC:m112')
    cy = Motor('IOC:m113')

    sample_mtrx = abstractXYMotor('IOC:m100', cx=cx, cy=cy, fx=fx, fy=fy, sx=sx, sy=sy)
    sample_mtrx.set_prevX_center_pos(cx.get('RBV'))
    sample_mtrx.set_prevY_center_pos(cy.get('RBV'))
    
    sample_mtrx.moveAndSet_X_CoarsePosition(3130, test_scan_range=True)
    
    #sample_mtrx.moveAndSet_Y_CoarsePosition(1000, test_scan_range=True)
    
    sample_mtrx.moveAndSet_X_CoarsePosition(-100, test_scan_range=True)
    
    #sample_mtrx.moveAndSet_Y_CoarsePosition(3000, test_scan_range=True)
    
    sample_mtrx.moveAndSet_X_CoarsePosition(570, test_scan_range=True)
    
    #sample_mtrx.moveAndSet_Y_CoarsePosition(5564, test_scan_range=True)
    
    sample_mtrx.moveAndSet_X_CoarsePosition(-1300, test_scan_range=True)
    
    #sample_mtrx.moveAndSet_Y_CoarsePosition(500, test_scan_range=True)
    
    sample_mtrx.moveAndSet_X_CoarsePosition(4500, test_scan_range=True)
    
    #sample_mtrx.moveAndSet_Y_CoarsePosition(4000, test_scan_range=True)
    
    sample_mtrx.moveAndSet_X_CoarsePosition(-250, test_scan_range=True)
    
    
    
    
    