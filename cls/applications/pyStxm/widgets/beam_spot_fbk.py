'''
Created on Sept 14, 2017

@author: bergr
'''

from PyQt5.QtCore import pyqtSignal, QObject, QTimer

from bcm.devices.device_names import *
from cls.types.stxmTypes import sample_positioning_modes, sample_fine_positioning_modes
from bcm.devices import Motor_Qt as apsMotor
from bcm.devices import sample_motor


class BeamSpotFeedbackObj(QObject):
    '''
    This is an object
    '''
    new_beam_pos = pyqtSignal(float, float)

    def __init__(self, main_obj):
        QObject.__init__(self)
        self.main_obj = main_obj
        self.fbkTimer = QTimer()
        self.fbkTimer.timeout.connect(self.on_fbk_timer)

        # sample_positioning_modes.COARSE
        # sample_fine_positioning_modes.SAMPLEFINE

        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()

        if(sample_positioning_mode is sample_positioning_modes.GONIOMETER):
            self.cx = self.main_obj.device(DNM_GONI_X)
            self.cy = self.main_obj.device(DNM_GONI_Y)
        else:
            self.cx = self.main_obj.device(DNM_COARSE_X)
            self.cy = self.main_obj.device(DNM_COARSE_Y)

        if (fine_sample_positioning_mode is sample_fine_positioning_modes.ZONEPLATE):
            self.fx = self.main_obj.device(DNM_ZONEPLATE_X)
            self.fy = self.main_obj.device(DNM_ZONEPLATE_Y)
        else:
            self.fx = self.main_obj.device(DNM_SAMPLE_FINE_X)
            self.fy = self.main_obj.device(DNM_SAMPLE_FINE_Y)

        #self.fx.add_callback('RBV', self.on_mtr_fbk_changed)

        self.fbkTimer.start(10)

    #def on_mtr_fbk_changed(self, **kwargs):

    def on_fbk_timer(self):
        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()

        if (sample_positioning_mode is sample_positioning_modes.GONIOMETER):
            #goni uses sum of Gx Gy and Zx Zy
            fxpos = self.fx.get_position()
            fypos = self.fy.get_position()
            cxpos = self.cx.get_position()
            cypos = self.cy.get_position()
            lst = [cxpos, fxpos, cypos, fypos]
            if(None in lst):
                #one of the feedbacks must  have disconnected
                x = y = None
            else:
                #fbk is ok
                x = cxpos + fxpos
                y = cypos + fypos
        else:
            #sample scanning uses interferometer only for both
            x = self.fx.get_position()
            y = self.fy.get_position()

        if(None in [x, y]):
            #one of tehe feedbacks disconnected
            pass
        else:
            #print 'on_fbk_timer: emitting (%.2f, %.2f)' % (x,y)
            self.new_beam_pos.emit(x, y)


class BeamSpotFeedbackObjStandAlone(QObject):
    '''
    This is an object
    self.devices['POSITIONERS'][DNM_GONI_X] = apsMotor('IOC:m107',pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_Y)
        self.devices['POSITIONERS'][DNM_GONI_Y] = apsMotor('IOC:m108',pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_Z)
        self.devices['POSITIONERS'][DNM_GONI_Z] = apsMotor('IOC:m109',pos_set=POS_TYPE_ES)

    self.devices['POSITIONERS'][DNM_ZONEPLATE_X] = sample_motor( 'IOC:m102',pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Y)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Y] = sample_motor( 'IOC:m103',pos_set=POS_TYPE_ES)

    self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = sample_motor('IOC:m100',pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_Y)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = sample_motor('IOC:m101',pos_set=POS_TYPE_ES)

    '''
    new_beam_pos = pyqtSignal(float, float)

    def __init__(self, sample_positioning_mode=sample_positioning_modes.COARSE, fine_sample_positioning_mode=sample_fine_positioning_modes.SAMPLEFINE):
        QObject.__init__(self)
        self.fbkTimer = QTimer()
        self.fbkTimer.timeout.connect(self.on_fbk_timer)
        self.sample_positioning_mode = sample_positioning_mode
        self.fine_sample_positioning_mode = fine_sample_positioning_mode
        # sample_positioning_modes.COARSE
        # sample_fine_positioning_modes.SAMPLEFINE

        if(sample_positioning_mode is sample_positioning_modes.GONIOMETER):
            self.cx = apsMotor('IOC:m107')
            self.cy = apsMotor('IOC:m108')

        if (fine_sample_positioning_mode is sample_fine_positioning_modes.ZONEPLATE):
            self.fx = sample_motor('IOC:m102')
            self.fy = sample_motor('IOC:m103')
        else:
            self.fx = sample_motor('IOC:m100')
            self.fy = sample_motor('IOC:m101')

        self.fbkTimer.start(10)

    #def on_mtr_fbk_changed(self, **kwargs):

    def on_fbk_timer(self):

        if (self.sample_positioning_mode is sample_positioning_modes.GONIOMETER):
            #goni uses sum of Gx Gy and Zx Zy
            fxpos = self.fx.get_position()
            fypos = self.fy.get_position()
            cxpos = self.cx.get_position()
            cypos = self.cy.get_position()
            lst = [cxpos, fxpos, cypos, fypos]
            if (None in lst):
                # one of the feedbacks must  have disconnected
                x = y = None
            else:
                # fbk is ok
                x = cxpos + fxpos
                y = cypos + fypos
        else:
            #sample scanning uses interferometer only for both
            x = self.fx.get_position()
            y = self.fy.get_position()

        if (None in [x, y]):
            # one of tehe feedbacks disconnected
            pass
        else:
            print('on_fbk_timer: emitting (%.2f, %.2f)' % (x,y))
            self.new_beam_pos.emit(x, y)