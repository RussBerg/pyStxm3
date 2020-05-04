'''
Created on May 16, 2019

@author: bergr
'''

# BCM GLOBAL Settings for stxm
import os

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets

from bcm.devices import camera
from bcm.devices import BaseDevice
from bcm.devices import Mbbi
from bcm.devices import Mbbo

from bcm.devices import Motor_Qt
from bcm.devices import sample_motor, sample_abstract_motor, e712_sample_motor
from bcm.devices import  Scan
from bcm.devices import  Transform

from bcm.devices import BaseGate, BaseCounter
from bcm.devices.device_names import *
from bcm.devices import PvShutter
from bcm.devices import E712WGDevice



from cls.appWidgets.main_object import main_object_base, dev_config_base, POS_TYPE_BL, POS_TYPE_ES
from cls.appWidgets.splashScreen import get_splash
from cls.app_data.defaults import Defaults
from cls.applications.pyStxm import abs_path_to_ini_file
from cls.scanning.e712_wavegen.e712 import E712ControlWidget
from cls.types.beamline import BEAMLINE_IDS
from cls.types.stxmTypes import sample_positioning_modes, sample_fine_positioning_modes, endstation_id_types
from cls.utils.cfgparser import ConfigClass
from cls.utils.log import get_module_logger
from cls.scan_engine.bluesky.test_detector import PointDetectorDevice, LineDetectorFlyerDevice, LineDetectorDevice
from cls.scan_engine.bluesky.test_gate import GateDevice

# from twisted.python.components import globalRegistry
_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)


__version__ = '1.0.0'


AMBIENT_STXM = False


BEAMLINE_NAME = '10ID-1'
BEAMLINE_TYPE = 'STXM'
BEAMLINE_ENERGY_RANGE = (4.0, 18.5)



# class SplashScreen(QtWidgets.QWidget):
#     def __init__(self, hdr_msg, parent=None):
#         super(SplashScreen, self).__init__(parent)
#
#         self.msg = QtWidgets.QLabel(hdr_msg)
#         self.connect_lbl = QtWidgets.QLabel("Connecting: ")
#         vbox = QtWidgets.QVBoxLayout()
#         vbox.addWidget(self.msg)
#         vbox.addWidget(self.connect_lbl)
#         self.setLayout(vbox)
#
#     def on_new_connection(self, msg):
#         self.connect_lbl.setText(msg)

SCANNING_MODE = 'SAMPLEXY'
#SCANNING_MODE = 'GONI'

class dev_config_sim_ambient(dev_config_base):
    def __init__(self, splash=None):
        super(dev_config_sim_ambient, self).__init__(splash=splash)
        print('Using simulated DEVICES')
        self.beamline = 'Ambient STXM 10ID1'
        self.sscan_rec_prfx = 'amb'
        self.es_id = endstation_id_types.AMBIENT
        self.sample_positioning_mode = sample_positioning_modes.COARSE
        self.splash = splash
        self.done = False
        #self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.on_timer)
        self.init_devices()
        self.init_presets()


    def init_presets(self):
        self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 350
        self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 200

        self.devices['PVS'][DNM_ENERGY_ENABLE].put(0)


    def init_devices(self):

        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = Motor_Qt('SIM_IOC:m1',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = Motor_Qt('SIM_IOC:m2',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_COARSE_X] = Motor_Qt( 'SIM_IOC:m3',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_COARSE_Y] = Motor_Qt( 'SIM_IOC:m4',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_OSA_X] = Motor_Qt('SIM_IOC:m5',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_OSA_Y] = Motor_Qt('SIM_IOC:m6',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_X] = Motor_Qt( 'SIM_IOC:m7',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_Y] = Motor_Qt( 'SIM_IOC:m8',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_Z] = Motor_Qt( 'SIM_IOC:m9',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z] = Motor_Qt( 'SIM_IOC:m10',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_SAMPLE_X] = Motor_Qt( 'SIM_IOC:m11',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_SAMPLE_Y] = Motor_Qt('SIM_IOC:m12',pos_set=POS_TYPE_ES)

        self.devices['POSITIONERS'][DNM_COARSE_Z] = Motor_Qt('SIM_IOC:m13',pos_set=POS_TYPE_ES)

        prfx = self.sscan_rec_prfx
        connect_standard_beamline_positioners(self.devices, prfx)
        connect_devices(self.devices, prfx)

        print('finished connecting to devices')
        self.done = True


class dev_config_amb(dev_config_base):
    def __init__(self, splash=None):
        super(dev_config_amb, self).__init__(splash=splash)
        print('Using Full Ambient STXM Hardware Devices')
        self.beamline = 'AMB STXM 10ID1'
        self.sscan_rec_prfx = 'amb'
        self.es_id = endstation_id_types.AMBIENT
        self.sample_positioning_mode = sample_positioning_modes.COARSE
        self.splash = splash
        self.done = False
        #self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.on_timer)
        self.init_devices()
        self.init_presets()


    def init_presets(self):
        self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 350
        self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 200
        use_laser = appConfig.get_value('MAIN', 'use_laser')

        self.devices['PVS'][DNM_ENERGY_ENABLE].put(0)

        self.devices['PRESETS']['USE_LASER'] = use_laser


    def init_devices(self):

        #I don't have an elegant way yet to create these and also emit a signal to the splash screen
        #so this is a first attempt
        #self.timer.start(100)
        # maps names to device objects

        #self.msg_splash("Creating device[SampleFineX]")
        #								ApsMotorRecordMotor(motorCfgObj, positioner, pv_name, motor_type)
        #self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = Motor_Qt('SIM_IOC:m1',pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = Motor_Qt('SIM_IOC:m2',pos_set=POS_TYPE_ES)

        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = sample_motor('SIM_IOC:m1',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = sample_motor('SIM_IOC:m2',pos_set=POS_TYPE_ES)

        self.devices['POSITIONERS'][DNM_COARSE_X] = Motor_Qt( 'SIM_IOC:m3',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_COARSE_Y] = Motor_Qt( 'SIM_IOC:m4',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_OSA_X] = Motor_Qt('SIM_IOC:m5',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_OSA_Y] = Motor_Qt('SIM_IOC:m6',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_X] = Motor_Qt( 'SIM_IOC:m7',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_Y] = Motor_Qt( 'SIM_IOC:m8',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_DETECTOR_Z] = Motor_Qt( 'SIM_IOC:m9',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z] = Motor_Qt( 'SIM_IOC:m10',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z_BASE] = Motor_Qt( 'SIM_IOC:m10')

        #self.devices['POSITIONERS'][DNM_SAMPLE_X] = Motor_Qt( 'SIM_IOC:m11',pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_SAMPLE_Y] = Motor_Qt('SIM_IOC:m12',pos_set=POS_TYPE_ES)

        self.devices['POSITIONERS'][DNM_SAMPLE_X] = sample_abstract_motor( 'SIM_IOC:m11',pos_set=POS_TYPE_ES)
        self.devices['POSITIONERS'][DNM_SAMPLE_Y] = sample_abstract_motor('SIM_IOC:m12',pos_set=POS_TYPE_ES)

        self.devices['POSITIONERS'][DNM_COARSE_Z] = Motor_Qt('SIM_IOC:m13',pos_set=POS_TYPE_ES)

        prfx = self.sscan_rec_prfx
        connect_standard_beamline_positioners(self.devices, prfx)
        connect_devices(self.devices, prfx)


        #key, value in self.devices.iteritems():
        #	print key,value
        print('finished connecting to devices')
        self.done = True

class dev_config_uhv(dev_config_base):
    def __init__(self, splash=None, sample_pos_mode=sample_positioning_modes.COARSE, fine_sample_pos_mode=sample_fine_positioning_modes.SAMPLEFINE):
        super(dev_config_uhv, self).__init__(splash=splash)
        print('Using UHV STXM DEVICES')
        self.beamline = 'UHV STXM 10ID1'
        self.sscan_rec_prfx = 'uhv'
        self.es_id = endstation_id_types.UHV
        self.sample_pos_mode = sample_pos_mode
        self.fine_sample_pos_mode = fine_sample_pos_mode
        #self.splash = splash
        self.done = False
        #self.timer = QtCore.QTimer()
        #self.timer.timeout.connect(self.on_timer)
        self.init_devices()
        self.init_presets()
        self.device_reverse_lookup_dct = self.make_device_reverse_lookup_dict()
        #self.get_cainfo()

        if(self.sample_pos_mode is sample_positioning_modes.GONIOMETER):
            self.set_exclude_positioners_list([DNM_SAMPLE_X, DNM_SAMPLE_Y, DNM_ZONEPLATE_Z_BASE, DNM_SAMPLE_FINE_X, DNM_SAMPLE_FINE_Y, DNM_COARSE_X, DNM_COARSE_Y, 'AUX1', 'AUX2', 'Cff', 'PeemM3Trans'])
        elif(self.sample_pos_mode is sample_positioning_modes.COARSE):
            if(self.fine_sample_pos_mode is sample_fine_positioning_modes.SAMPLEFINE):
                self.exclude_list = [DNM_GONI_X, DNM_GONI_Y, DNM_GONI_Z, DNM_GONI_THETA, DNM_ZONEPLATE_Z_BASE, DNM_SAMPLE_FINE_X, DNM_SAMPLE_FINE_Y,
                                     DNM_COARSE_X, DNM_COARSE_Y, 'AUX1', 'AUX2', 'Cff', 'PeemM3Trans']
            else:
                #zoneplate
                self.exclude_list = [DNM_GONI_X, DNM_GONI_Y, DNM_GONI_Z, DNM_GONI_THETA, DNM_ZONEPLATE_X, DNM_ZONEPLATE_Y, DNM_ZONEPLATE_Z_BASE,
                                     DNM_SAMPLE_FINE_X, DNM_SAMPLE_FINE_Y,
                                     DNM_COARSE_X, DNM_COARSE_Y, 'AUX1', 'AUX2', 'Cff', 'PeemM3Trans']
        #init_posner_snapshot_cbs(self.devices['POSITIONERS'])
        #self.close_splash()
        print('leaving dev_config_uhv')

    def parse_cainfo_stdout_to_dct(self, s):
        dct = {}
        s2 = s.split('\n')
        for l in s2:
            l2 = l.replace(' ', '')
            l3 = l2.split(':')
            if(len(l3) > 1):
                dct[l3[0]] = l3[1]
        return(dct)

    def do_cainfo(self, pvname):
        import subprocess
        print('cainfo [%s]' % pvname)
        proc = subprocess.Popen('cainfo %s' % pvname, stdout=subprocess.PIPE)
        stdout_str = proc.stdout.read()
        _dct = self.parse_cainfo_stdout_to_dct(stdout_str)
        return(_dct)

    def get_cainfo(self):

        skip_lst = ['PVS_DONT_RECORD', 'PRESETS','DETECTORS_NO_RECORD','WIDGETS']
        dev_dct = {}
        sections = list(self.devices.keys())
        for section in sections:
            keys = []
            if(section not in skip_lst):
                keys = list(self.devices[section].keys())
                #check to see if this is a subsectioned section that has pvs for BL (beamline) and ES (endstation)
                #if so do those
                if(keys == ['BL', 'ES']):
                    dev_dct[section] = {}
                    for subsec in keys:
                        for pvname in list(self.devices[section][subsec].keys()):
                            _dct = self.do_cainfo(pvname)
                            dev_dct[section][pvname] = {}
                            dev_dct[section][pvname]['dev'] = self.devices[section][subsec][pvname]
                            dev_dct[section][pvname]['cainfo'] = _dct
                            if (_dct['State'].find('dis') > -1):
                                print('[%s] does not appear to exist' % k)
                                print(_dct)
                else:
                    for k in keys:
                        dev = self.devices[section][k]
                        dev_dct[section] = {}
                        dev_dct[section][k] = {}
                        dev_dct[section][k]['dev'] = dev
                        if(not hasattr(dev, 'get_name')):
                            print('crap!', dev)
                        _dct = self.do_cainfo(dev.get_name())
                        dev_dct[section][k]['cainfo'] = _dct
                        if(_dct['State'].find('dis') > -1):
                            print('[%s] does not appear to exist' % k)
                            print(_dct)

        dev_dct



    def init_presets(self):
        # these need to come from teh app.ini file FINE_SCAN_RANGES, leave as hack for now till I get time

        maxCX = appConfig.get_value('SCAN_RANGES', 'coarse_x')
        maxCY = appConfig.get_value('SCAN_RANGES', 'coarse_y')
        maxFX = appConfig.get_value('SCAN_RANGES', 'fine_x')
        maxFY = appConfig.get_value('SCAN_RANGES', 'fine_y')
        use_laser = appConfig.get_value('MAIN', 'use_laser')



        #self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 98
        #self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 98

        if(self.sample_pos_mode is sample_positioning_modes.GONIOMETER):
            self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = maxFX
            self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = maxFY
        else:
            self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = maxCX
            self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = maxCY

        self.devices['PRESETS']['MAX_FINE_SCAN_RANGE_X'] = maxFX
        self.devices['PRESETS']['MAX_FINE_SCAN_RANGE_Y'] = maxFY

        #self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_X'] = maxFX
        #self.devices['PRESETS']['MAX_ZP_SCAN_RANGE_Y'] = maxFY


       # self.devices['PRESETS']['MAX_ZP_SUBSCAN_RANGE_X'] = maxFX
       # self.devices['PRESETS']['MAX_ZP_SUBSCAN_RANGE_Y'] = maxFY

        #self.devices['PVS'][DNM_ENERGY_ENABLE].put(0)
        self.devices['PRESETS']['USE_LASER'] = use_laser


    def init_devices(self):

        #I don't have an elegant way yet to create these and also emit a signal to the splash screen
        #so this is a first attempt
        #self.timer.start(100)
        # maps names to device objects
        #self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = Motor_Qt('SIM_IOC:m100',pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = Motor_Qt('SIM_IOC:m101',pos_set=POS_TYPE_ES)


        prfx = self.sscan_rec_prfx
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_X)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = e712_sample_motor('SIM_IOC:m100', name='SIM_IOC:m100', pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_FINE_X] = Motor_Qt('SIM_IOC:m100', name='SIM_IOC:m100')
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_Y)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = e712_sample_motor('SIM_IOC:m101', name='SIM_IOC:m101', pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_FINE_Y] = Motor_Qt('SIM_IOC:m101', name='SIM_IOC:m101')
        self.msg_splash("connecting to: [%s]" % DNM_COARSE_X)
        self.devices['POSITIONERS'][DNM_COARSE_X] = Motor_Qt( 'SIM_IOC:m112', name='SIM_IOC:m112', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_COARSE_Y)
        self.devices['POSITIONERS'][DNM_COARSE_Y] = Motor_Qt( 'SIM_IOC:m113', name='SIM_IOC:m113', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_X)
        self.devices['POSITIONERS'][DNM_OSA_X] = Motor_Qt('SIM_IOC:m104', name='SIM_IOC:m104', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Y)
        self.devices['POSITIONERS'][DNM_OSA_Y] = Motor_Qt('SIM_IOC:m105', name='SIM_IOC:m105', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Z)
        self.devices['POSITIONERS'][DNM_OSA_Z] = Motor_Qt('SIM_IOC:m106C', name='SIM_IOC:m106C', pos_set=POS_TYPE_ES, collision_support=True)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Z_BASE)
        self.devices['POSITIONERS'][DNM_OSA_Z_BASE] = Motor_Qt('SIM_IOC:m106', name='SIM_IOC:m106', )

        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_X)
        self.devices['POSITIONERS'][DNM_DETECTOR_X] = Motor_Qt( 'SIM_IOC:m114', name='SIM_IOC:m114', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_Y)
        self.devices['POSITIONERS'][DNM_DETECTOR_Y] = Motor_Qt( 'SIM_IOC:m115', name='SIM_IOC:m115', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_Z)
        self.devices['POSITIONERS'][DNM_DETECTOR_Z] = Motor_Qt( 'SIM_IOC:m116', name='SIM_IOC:m116', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_X)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_X] = e712_sample_motor( 'SIM_IOC:m102', name='SIM_IOC:m102', pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_FINE_ZX] = Motor_Qt( 'SIM_IOC:m102', name='SIM_IOC:m102')
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Y)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Y] = e712_sample_motor( 'SIM_IOC:m103', name='SIM_IOC:m103', pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_FINE_ZY] = Motor_Qt('SIM_IOC:m102', name='SIM_IOC:m102')
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Z)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z] = Motor_Qt( 'SIM_IOC:m111C', name='SIM_IOC:m111C', pos_set=POS_TYPE_ES, collision_support=True)
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Z_BASE)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z_BASE] = Motor_Qt( 'SIM_IOC:m111', name='SIM_IOC:m111' )

        #self.devices['POSITIONERS'][DNM_SAMPLE_X] = Motor_Qt( 'SIM_IOC:m117',pos_set=POS_TYPE_ES)
        #self.devices['POSITIONERS'][DNM_SAMPLE_Y] = Motor_Qt('SIM_IOC:m118',pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_X)
        self.devices['POSITIONERS'][DNM_SAMPLE_X] = sample_abstract_motor( 'SIM_IOC:m117', name='SIM_IOC:m117', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_Y)
        self.devices['POSITIONERS'][DNM_SAMPLE_Y] = sample_abstract_motor('SIM_IOC:m118', name='SIM_IOC:m118', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_X)
        self.devices['POSITIONERS'][DNM_GONI_X] = Motor_Qt('SIM_IOC:m107', name='SIM_IOC:m107', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_Y)
        self.devices['POSITIONERS'][DNM_GONI_Y] = Motor_Qt('SIM_IOC:m108', name='SIM_IOC:m108', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_Z)
        self.devices['POSITIONERS'][DNM_GONI_Z] = Motor_Qt('SIM_IOC:m109', name='SIM_IOC:m109', pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_GONI_THETA)
        self.devices['POSITIONERS'][DNM_GONI_THETA] = Motor_Qt('SIM_IOC:m110', name='SIM_IOC:m110', pos_set=POS_TYPE_ES)

        #self.msg_splash("connecting to: [%s]" % DNM_CALIB_CAMERA_SRVR)
        #self.devices['DETECTORS_NO_RECORD'][DNM_CALIB_CAMERA_SRVR] = camera('CCD1610-I10:%s' % prfx, server=True)
        self.msg_splash("connecting to: [%s]" % DNM_CALIB_CAMERA_CLIENT)
        self.devices['DETECTORS_NO_RECORD'][DNM_CALIB_CAMERA_CLIENT] = camera('SIM_CCD1610-I10:%s' % prfx)

        connect_standard_beamline_positioners(self.devices, prfx, devcfg=self)
        connect_devices(self.devices, prfx, devcfg=self)

        #check_if_pv_exists(self.devices['POSITIONERS'])
        # for key, value in self.devices.iteritems():
        # 	print key,value

        print('finished connecting to devices')
        self.done = True

    def make_device_reverse_lookup_dict(self):
        subcat_lst = ['PRESSURES', 'TEMPERATURES']
        skip_lst = ['DETECTORS', 'DETECTORS_NO_RECORD', 'DIO', 'SSCANS', 'PVS_DONT_RECORD','PRESETS', 'WIDGETS']
        dct = {}
        for category in self.devices.keys():
            if(category in skip_lst):
                continue
            if(category in subcat_lst):
                for subcat in self.devices[category].keys():
                    dev_dct = self.devices[category][subcat]
                    for dev_nm, dev in dev_dct.items():
                        #dct[dev.get_name()] = self.fix_device_nm(dev_nm)
                        dct[dev_nm] = dev.get_name()
            else:
                dev_dct = self.devices[category]
                for dev_nm, dev in dev_dct.items():
                    #dct[dev.get_name()] = self.fix_device_nm(dev_nm)
                    dct[dev_nm] = dev.get_name()

        return(dct)

    # def make_device_reverse_lookup_dict(self):
    #     dct = {}
    #     dev_dct = self.devices['POSITIONERS']
    #     for dev_nm, dev in dev_dct.items():
    #         dct[dev.get_name()] = self.fix_device_nm(dev_nm)
    #
    #     return(dct)

    def fix_device_nm(self, nm_str):
        l = nm_str.lower()
        l = l.replace('.','_')
        return(l)

def connect_standard_beamline_positioners(dev_dct, prfx='uhv', devcfg=None):
    devcfg.msg_splash("connecting to: [%s]" % DNM_ENERGY)
    dev_dct['POSITIONERS'][DNM_ENERGY] = Motor_Qt('SIM_BL1610-I10:ENERGY', name='SIM_BL1610-I10:ENERGY', abstract_mtr=True, pos_set=POS_TYPE_ES)
    devcfg.msg_splash("connecting to: [%s]" % DNM_SLIT_X)
    dev_dct['POSITIONERS'][DNM_SLIT_X] = Motor_Qt('SIM_BL1610-I10:slitX', name='SIM_BL1610-I10:slitX', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_SLIT_Y)
    dev_dct['POSITIONERS'][DNM_SLIT_Y] = Motor_Qt('SIM_BL1610-I10:slitY', name='SIM_BL1610-I10:slitY', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_M3_PITCH)
    dev_dct['POSITIONERS'][DNM_M3_PITCH] = Motor_Qt('SIM_BL1610-I10:m3STXMPitch', name='SIM_BL1610-I10:m3STXMPitch', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_GAP)
    dev_dct['POSITIONERS'][DNM_EPU_GAP] = Motor_Qt('SIM_BL1610-I10:epuGap', name='SIM_BL1610-I10:epuGap', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_OFFSET)
    dev_dct['POSITIONERS'][DNM_EPU_OFFSET] = Motor_Qt('SIM_BL1610-I10:epuOffset', name='SIM_BL1610-I10:epuOffset', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_HARMONIC)
    dev_dct['POSITIONERS'][DNM_EPU_HARMONIC] = Motor_Qt('SIM_BL1610-I10:epuHarmonic', name='SIM_BL1610-I10:epuHarmonic', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_POLARIZATION)
    dev_dct['POSITIONERS'][DNM_EPU_POLARIZATION] = Motor_Qt('SIM_BL1610-I10:epuPolarization', name='SIM_BL1610-I10:epuPolarization', abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_ANGLE)
    dev_dct['POSITIONERS'][DNM_EPU_ANGLE] = Motor_Qt('SIM_BL1610-I10:epuAngle', name='SIM_BL1610-I10:epuAngle', abstract_mtr=True, pos_set=POS_TYPE_BL)


def connect_devices(dev_dct, prfx='uhv', devcfg=None):

    devcfg.msg_splash("connecting to: [%s]" % DNM_GATE)
    dev_dct['DIO'][DNM_GATE] = BaseGate('SIM_%sCO:gate' % prfx)
    devcfg.msg_splash("connecting to: [%s]" % DNM_SHUTTER)
    dev_dct['DIO'][DNM_SHUTTER] = PvShutter('SIM_%sDIO:shutter:ctl' % prfx)
    devcfg.msg_splash("connecting to: [%s]" % 'ShutterTaskRun')
    dev_dct['DIO']['ShutterTaskRun'] = BaseDevice('SIM_%sDIO:shutter:Run' % prfx)

    devcfg.msg_splash("connecting to: [%s]" % DNM_COUNTER_APD)
    dev_dct['DETECTORS'][DNM_COUNTER_APD] = BaseCounter('SIM_%sCI:counter' % prfx)
    #dev_dct['DETECTORS']['Det_Cntr'] = EpicsPvCounter('%sPMT:ctr:SingleValue_RBV' % prfx)
    devcfg.msg_splash("connecting to: [%s]" % DNM_PMT)
    dev_dct['DETECTORS'][DNM_PMT] = BaseDevice('SIM_%sPMT:ctr:SingleValue_RBV' % prfx)

    dev_dct['DETECTORS'][DNM_POINT_DET] = PointDetectorDevice('uhvCI:counter:', name=DNM_DEFAULT_COUNTER)
    dev_dct['DIO'][DNM_POINT_GATE] = GateDevice('SIM_uhvCO:gate:', name='gate_control')

    dev_dct['DETECTORS'][DNM_LINE_DET] = LineDetectorDevice('SIM_uhvCI:counter:', name=DNM_DEFAULT_COUNTER)
    dev_dct['DETECTORS'][DNM_LINE_DET_FLYER] = LineDetectorFlyerDevice('SIM_uhvCI:counter:', name=DNM_DEFAULT_COUNTER,
                                                  stream_names={'line_det_strm': 'primary'},
                                                  monitor_attrs=['waveform_rbv'], pivot=False)


    dev_dct['PVS'][DNM_RING_CURRENT] = BaseDevice('SIM_PCT1402-01:mA:fbk', units='mA')
    #dev_dct['DETECTORS'][DNM_TYCHO_CAMERA] = SimCamera(sim_get_time=0.5)

#    dev_dct['DETECTORS_NO_RECORD']['DetCntr_Snapshot'] = BaseDevice('%sPMT:det_snapshot_RBV' % prfx)
#    dev_dct['DETECTORS_NO_RECORD']['OsaCntr_Snapshot'] = BaseDevice('%sPMT:osa_snapshot_RBV' % prfx)

    #dev_dct['DETECTORS']['Ax1InterferVolts'] = EpicsPvCounter('%sAi:ai:ai0_RBV' % prfx)
    #dev_dct['DETECTORS']['Ax2InterferVolts'] = EpicsPvCounter('%sAi:ai:ai1_RBV' % prfx)

    dev_dct['PVS'][DNM_IDEAL_A0] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:fbk:tr.K' % prfx)
    #dev_dct['PVS'][DNM_CALCD_ZPZ] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:fbk:tr.L' % prfx)
    dev_dct['PVS'][DNM_CALCD_ZPZ] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:fbk:tr.I' % prfx)

    dev_dct['PVS']['Zpz_adjust'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:adjust_zpz' % prfx)

    devcfg.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_SCAN_MODE)
    #dev_dct['PVS']['Zpz_scanModeFlag'] = Mbbo('SIM_BL1610-I10:ENERGY:%s:zp:scanselflag' % prfx) #used to control which value gets sent to Zpz, fl or fl - A0
    dev_dct['PVS'][DNM_ZONEPLATE_SCAN_MODE] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:scanselflag' % prfx)  # used to control which value gets sent to Zpz, fl or fl - A0
    dev_dct['PVS'][DNM_ZONEPLATE_INOUT] = BaseDevice('SIM_BL1610-I10:%s:zp_inout' % prfx)  # used to convieniently move zp z in and out
    dev_dct['PVS'][DNM_ZONEPLATE_INOUT_FBK] = Mbbi('SIM_BL1610-I10:%s:zp_inout:fbk' % prfx)  # used to convieniently move zp z in and out
    #used to adjust the current focus value, the delta represents the relative microns for zpz to move to new focus position
    dev_dct['PVS'][DNM_DELTA_A0] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:delta_A0' % prfx)
    dev_dct['PVS'][DNM_FOCAL_LEN] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:FL' % prfx, units='um')
    dev_dct['PVS'][DNM_A0] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:A0' % prfx)
    dev_dct['PVS'][DNM_A0MAX] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:A0Max' % prfx)
    dev_dct['PVS'][DNM_A0_FOR_CALC] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:A0:for_calc' % prfx)

    devcfg.msg_splash("connecting to: [%s]" % 'zoneplate definitions')
    dev_dct['PVS'][DNM_ZPZ_POS] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:zpz_pos' % prfx)
    dev_dct['PVS']['Zp_def'] = Transform('SIM_BL1610-I10:ENERGY:%s:zp:def' % prfx)
    dev_dct['PVS']['OSA_def'] = Transform('SIM_BL1610-I10:ENERGY:%s:osa:def' % prfx)

    dev_dct['PVS'][DNM_ZP_SELECT] = Mbbo('SIM_BL1610-I10:ENERGY:%s:zp' % prfx)
    dev_dct['PVS'][DNM_OSA_SELECT] = Mbbo('SIM_BL1610-I10:ENERGY:%s:osa' % prfx)

    devcfg.msg_splash("connecting to: [%s]" % 'Energy_enable')
    dev_dct['PVS'][DNM_ENERGY_ENABLE] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:enabled' % prfx)
    dev_dct['PVS'][DNM_ENERGY_RBV] = BaseDevice('SIM_BL1610-I10:ENERGY.RBV', egu='um')
    dev_dct['PVS'][DNM_ZPZ_RBV] = BaseDevice('SIM_IOC:m111C.RBV', egu='um')
    dev_dct['PVS'][DNM_ZP_DEF_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:def.A' % prfx)

    devcfg.msg_splash("connecting to: [%s]" % 'Zp_def1 -> 7')
    dev_dct['PVS'][DNM_ZP_DEF1_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp1:def.A' % prfx)
    dev_dct['PVS'][DNM_ZP_DEF2_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp2:def.A' % prfx)
    dev_dct['PVS'][DNM_ZP_DEF3_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp3:def.A' % prfx)
    dev_dct['PVS'][DNM_ZP_DEF4_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp4:def.A' % prfx)
    dev_dct['PVS'][DNM_ZP_DEF5_A] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp5:def.A' % prfx)
    dev_dct['PVS']['Zp_def6_A'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp6:def.A' % prfx)
    dev_dct['PVS']['Zp_def7_A'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp7:def.A' % prfx)

    #dev_dct['PVS']['SRStatus_msgL1'] = BaseDevice('SRStatus:msg:tL1')
    #dev_dct['PVS']['SRStatus_msgL2'] = BaseDevice('SRStatus:msg:tL2')
    #dev_dct['PVS']['SRStatus_msgL3'] = BaseDevice('SRStatus:msg:tL3')
    devcfg.msg_splash("connecting to: [%s]" % 'SRStatus_shutters')
    dev_dct['PVS']['SRStatus_shutters'] = BaseDevice('SIM_SRStatus:shutters')

    devcfg.msg_splash("connecting to: [%s]" % 'Mono_ev_fbk')
    dev_dct['PVS'][DNM_MONO_EV_FBK] = BaseDevice('SIM_MONO1610-I10-01:energy:fbk', units='eV')
    devcfg.msg_splash("connecting to: [%s]" % 'Mono_grating_fbk')
    _pv = BaseDevice('SIM_MONO1610-I10-01:grating:select:fbk')
    _pv.get_position = _pv.get_enum_str_as_int
    dev_dct['PVS']['Mono_grating_fbk'] = _pv

    devcfg.msg_splash("connecting to: [%s]" % 'Epu_pol_fbk')
    dev_dct['PVS']['Epu_pol_fbk'] = Mbbo('SIM_UND1410-01:polarization')
    devcfg.msg_splash("connecting to: [%s]" % 'Epu_pol_angle')
    dev_dct['PVS']['Epu_pol_angle'] = BaseDevice('SIM_UND1410-01:polarAngle', units='udeg')

    devcfg.msg_splash("connecting to: [%s]" % 'Epu_gap_fbk')
    dev_dct['PVS']['Epu_gap_fbk'] = BaseDevice('SIM_UND1410-01:gap:mm:fbk', units='mm')

    # devcfg.msg_splash("connecting to: [%s]" % 'Epu_gap_fbk')
    # dev_dct['PVS']['Epu_gap_fbk'] = BaseDevice('RUSSTEST:VAL')

    devcfg.msg_splash("connecting to: [%s]" % 'Epu_gap_offset')
    dev_dct['PVS']['Epu_gap_offset'] = BaseDevice('SIM_UND1410-01:gap:offset', units='mm')
    devcfg.msg_splash("connecting to: [%s]" % 'Epu_harmonic')
    dev_dct['PVS']['Epu_harmonic'] = BaseDevice('SIM_UND1410-01:harmonic')


    devcfg.msg_splash("connecting to PVs: [1]")
    dev_dct['PVS']['SYSTEM:mode:fbk'] = BaseDevice('SYSTEM:mode:fbk')
    #dev_dct['PVS']['mbbiSYSTEM:mode:fbk'] = Mbbi('SYSTEM:mode:fbk')
    dev_dct['PVS'][DNM_BEAM_DEFOCUS] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:zp:defocus' % prfx, units='um')


    dev_dct['PVS_DONT_RECORD']['ticker'] = BaseDevice('SIM_TRG2400:cycles', egu='counts')

    dev_dct['PVS_DONT_RECORD']['CX_auto_disable_power'] = BaseDevice('SIM_IOC:m112:XPS_AUTO_DISABLE_MODE')
    dev_dct['PVS_DONT_RECORD']['CY_auto_disable_power'] = BaseDevice('SIM_IOC:m113:XPS_AUTO_DISABLE_MODE')
    dev_dct['PVS_DONT_RECORD']['DX_auto_disable_power'] = BaseDevice('SIM_IOC:m114:XPS_AUTO_DISABLE_MODE')
    dev_dct['PVS_DONT_RECORD']['DY_auto_disable_power'] = BaseDevice('SIM_IOC:m115:XPS_AUTO_DISABLE_MODE')

    dev_dct['PVS_DONT_RECORD']['accRange'] = BaseDevice('SIM_uhvTestSIG:signal:MaxPoints')

    dev_dct['PVS_DONT_RECORD']['FX_force_done'] = BaseDevice('SIM_IOC:m100:ForceDone')
    dev_dct['PVS_DONT_RECORD']['FY_force_done'] = BaseDevice('SIM_IOC:m101:ForceDone')

#    dev_dct['PVS_DONT_RECORD']['OX_force_done'] = BaseDevice('SIM_IOC:m104:ForceDone')
#    dev_dct['PVS_DONT_RECORD']['OY_force_done'] = BaseDevice('SIM_IOC:m105:ForceDone')

    dev_dct['PVS_DONT_RECORD'][DNM_OSAX_TRACKING] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osax_track_enabled' % prfx)
    dev_dct['PVS_DONT_RECORD'][DNM_OSAY_TRACKING] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osay_track_enabled' % prfx)
    dev_dct['PVS_DONT_RECORD'][DNM_OSAZ_TRACKING] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osaz_track_enabled' % prfx)

#    dev_dct['PVS_DONT_RECORD']['OSAXYZ_lockposition_enabled'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osaxyz_lockpos_enabled' % prfx)

#    dev_dct['PVS_DONT_RECORD']['OSAXY_goto_lockposition'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osaxy_goto_lockpos' % prfx)
#    dev_dct['PVS_DONT_RECORD']['OSAZ_goto_lockposition'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:osaz_goto_lockpos' % prfx)

    devcfg.msg_splash("connecting to PVs: [15]")

    dev_dct['PVS_DONT_RECORD']['Set_XY_lockposition'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:set_xy:lockposn' % prfx, units='um')
    dev_dct['PVS_DONT_RECORD']['Set_Z_lockposition'] = BaseDevice('SIM_BL1610-I10:ENERGY:%s:set_z:lock_posn' % prfx, units='um')

    dev_dct['PVS'][DNM_AX1_INTERFER_VOLTS] = BaseDevice('SIM_%sAi:ai:ai0_RBV' % prfx, rd_only=True)
    dev_dct['PVS'][DNM_AX2_INTERFER_VOLTS] = BaseDevice('SIM_%sAi:ai:ai1_RBV' % prfx, rd_only=True)


    #devcfg.msg_splash("connecting to SSCAN: [%s]" % ('SIM_%sstxm:det:' % prfx))

    # devcfg.msg_splash("connecting to SSCAN: [%s]" % ('%sstxm:' % prfx))
    # dev_dct['PVS_DONT_RECORD']['%sstxm:cmd_file' % prfx] = BaseDevice('SIM_%sstxm:cmd_file' % prfx)ut
    # dev_dct['SSCANS']['%sstxm:scan1' % prfx] = Scan('%sstxm:scan1' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan2' % prfx] = Scan('%sstxm:scan2' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan3' % prfx] = Scan('%sstxm:scan3' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan4' % prfx] = Scan('%sstxm:scan4' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan5' % prfx] = Scan('%sstxm:scan5' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan6' % prfx] = Scan('%sstxm:scan6' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan7' % prfx] = Scan('%sstxm:scan7' % prfx)
    # dev_dct['SSCANS']['%sstxm:scan8' % prfx] = Scan('%sstxm:scan8' % prfx)
    #
    # dev_dct['PVS_DONT_RECORD']['%sstxm:scan1:sts' % prfx] = BaseDevice('%sstxm:scan1.SMSG' % prfx)

    # ES = endstation temperatures
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-01]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-01'] = BaseDevice('SIM_TM1610-3-I12-01', desc='Turbo cooling water', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-30]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-30'] = BaseDevice('SIM_TM1610-3-I12-30', desc='Sample Coarse Y', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-32]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-32'] = BaseDevice('SIM_TM1610-3-I12-32', desc='Detector Y', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-21]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-21'] = BaseDevice('SIM_TM1610-3-I12-21', desc='Chamber temp #1', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-22]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-22'] = BaseDevice('SIM_TM1610-3-I12-22', desc='Chamber temp #2', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-23]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-23'] = BaseDevice('SIM_TM1610-3-I12-23', desc='Chamber temp #3', units='deg C')
    devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-24]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-24'] = BaseDevice('SIM_TM1610-3-I12-24', desc='Chamber temp #4', units='deg C')


    #pressures
    devcfg.msg_splash("connecting to PRESSURES: [FRG1610-3-I12-01:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['FRG1610-3-I12-01:vac:p'] = BaseDevice('SIM_FRG1610-3-I12-01:vac:p', desc='Chamber pressure', units='torr')
    devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-03:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-03:vac:p'] = BaseDevice('SIM_TCG1610-3-I12-03:vac:p', desc='Turbo backing pressure', units='torr')
    devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-04:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-04:vac:p'] = BaseDevice('SIM_TCG1610-3-I12-04:vac:p', desc='Load lock pressure', units='torr')
    devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-05:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-05:vac:p'] = BaseDevice('SIM_TCG1610-3-I12-05:vac:p', desc='Rough line pressure', units='torr')

    connect_ES_devices(dev_dct, prfx)
    connect_BL_devices(dev_dct, prfx)
    connect_heartbeats(dev_dct, prfx)
    connect_e712(dev_dct, prfx)


def connect_heartbeats(dev_dct, prfx='uhv'):
    '''

    :param dev_dct:
    :param prfx:
    :return:
    '''
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS'] = {}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['sscan_hrtbt'] = {'dev':BaseDevice('SIM_uhvstxm:hrtbt:alive'), 'desc':'SSCAN App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['blApi_hrtbt'] = {'dev':BaseDevice('SIM_uhvBlApi:hrtbt:alive'), 'desc':'BlApi App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['ai_hrtbt'] = {'dev': BaseDevice('SIM_uhvAI:hrtbt:alive'),
                                                            'desc': 'AnalogInput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['ci_hrtbt'] = {'dev':BaseDevice('SIM_uhvCI:hrtbt:alive'), 'desc':'CounterInput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['co_hrtbt'] = {'dev':BaseDevice('SIM_uhvCO:hrtbt:alive'), 'desc':'CounterOutput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['dio_hrtbt'] = {'dev':BaseDevice('SIM_uhvDIO:hrtbt:alive'), 'desc':'Digital IO App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_hrtbt'] = {'dev':BaseDevice('SIM_UHVMTRS:hrtbt:alive'), 'desc':'Main Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtr_calib_hrtbt'] = {'dev':BaseDevice('SIM_UHVMTR_CALIB:hrtbt:alive'), 'desc':'MotorCalibrations'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_osa_hrtbt'] = {'dev':BaseDevice('SIM_UHVMTR_OSA:hrtbt:alive'), 'desc':'OSA Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_zp_hrtbt'] = {'dev':BaseDevice('SIM_UHVMTR_ZP:hrtbt:alive'), 'desc':'ZPz Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['gate_cntr_scan_cfg'] = {'dev':BaseDevice('SIM_gate_cntr_scan_cfg:hrtbt:alive'), 'desc':'Gate/Counter scan cfg App'}



def connect_e712(dev_dct, prfx='uhv', e712_prfx='SIM_IOCE712'):

    # dev_dct['SSCANS']['SampleImageWithE712Wavegen'] = SampleImageWithE712Wavegen()
    dev_dct['WIDGETS'][DNM_E712_WIDGET] = E712ControlWidget('SIM_%s:' % e712_prfx,
                                                                counter=dev_dct['DETECTORS'][DNM_COUNTER_APD],
                                                                gate=dev_dct['DIO'][DNM_GATE])
    dev_dct['WIDGETS'][DNM_E712_OPHYD_DEV] = E712WGDevice('SIM_IOCE712:', name='e712_wgenerator_flyerdev')
    # waveform PV
    dev_dct['PVS_DONT_RECORD']['e712_dwells'] = BaseDevice('SIM_%s:dwells' % e712_prfx, units='mA')
    dev_dct['PVS_DONT_RECORD']['e712_xresetposns'] = BaseDevice('SIM_%s:xreset:posns' % e712_prfx, units='um')
    dev_dct['PVS_DONT_RECORD']['e712_yresetposns'] = BaseDevice('SIM_%s:yreset:posns' % e712_prfx, units='um')
    dev_dct['PVS_DONT_RECORD']['e712_sp_ids'] = BaseDevice('SIM_%s:sp_roi:ids' % e712_prfx)
    dev_dct['PVS_DONT_RECORD']['e712_current_sp_id'] = BaseDevice('SIM_%s:sp_roi:current' % e712_prfx)
    dev_dct['PVS_DONT_RECORD']['e712_x_start_pos'] = BaseDevice('SIM_%s:XStartPos' % e712_prfx)
    dev_dct['PVS_DONT_RECORD']['e712_y_start_pos'] = BaseDevice('SIM_%s:YStartPos' % e712_prfx)

    # pvs that will hold up to 10 DDL tables for a multi spatial scan
    dev_dct['PVS_DONT_RECORD']['e712_ddl_tbls'] = [ BaseDevice('SIM_%s:ddl:0' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:1' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:2' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:3' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:4' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:5' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:6' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:7' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:8' % e712_prfx),
                                                    BaseDevice('SIM_%s:ddl:9' % e712_prfx) ]



    dev_dct['PVS_DONT_RECORD']['e712_image_idx'] = BaseDevice('SIM_%s:image_idx' % e712_prfx)
    dev_dct['PVS_DONT_RECORD']['e712_scan_mode'] = BaseDevice('SIM_%s:ScanMode' % e712_prfx)

    if (MAIN_OBJ.get_fine_sample_positioning_mode() is sample_fine_positioning_modes.ZONEPLATE):
        # here using x2 and y2 because we are zoneplate scanning and they are channels 3 and 4 respectively
        # waveform PV's

        dev_dct['PVS_DONT_RECORD']['e712_x_start_mode'] = BaseDevice('SIM_%s:wg3:startmode' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_start_mode'] = BaseDevice('SIM_%s:wg4:startmode' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_wavtbl_ids'] = BaseDevice('SIM_%s:wg3_tbl:ids' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_wavtbl_ids'] = BaseDevice('SIM_%s:wg4_tbl:ids' % e712_prfx)

        # short PV's
        dev_dct['PVS_DONT_RECORD']['e712_x_npts'] = BaseDevice('SIM_%s:wg3:npts' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_npts'] = BaseDevice('SIM_%s:wg4:npts' % e712_prfx)

        # pvs that hold the flags for each waveformgenerator (4) for each supported sp_roi (max of 10)
        dev_dct['PVS_DONT_RECORD']['e712_x_useddl'] = BaseDevice('SIM_%s:wg3:useddl' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_useddl'] = BaseDevice('SIM_%s:wg4:useddl' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_usereinit'] = BaseDevice('SIM_%s:wg3:usereinit' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_usereinit'] = BaseDevice('SIM_%s:wg4:usereinit' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_strtatend'] = BaseDevice('SIM_%s:wg3:strtatend' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_strtatend'] = BaseDevice('SIM_%s:wg4:strtatend' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_usetablenum'] = BaseDevice('SIM_%s:WavGen3UseTblNum' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_usetablenum'] = BaseDevice('SIM_%s:WavGen4UseTblNum' % e712_prfx)

    else:
        # here using x1 and y1 because we are sample scanning and they are channels 1 and 2 respectively
        # waveform PV's
        dev_dct['PVS_DONT_RECORD']['e712_x_start_mode'] = BaseDevice('SIM_%s:wg1:startmode' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_start_mode'] = BaseDevice('SIM_%s:wg2:startmode' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_wavtbl_ids'] = BaseDevice('SIM_%s:wg1_tbl:ids' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_wavtbl_ids'] = BaseDevice('SIM_%s:wg2_tbl:ids' % e712_prfx)

        # short PV's
        dev_dct['PVS_DONT_RECORD']['e712_x_npts'] = BaseDevice('SIM_%s:wg1:npts' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_npts'] = BaseDevice('SIM_%s:wg2:npts' % e712_prfx)

        # pvs that hold the flags for each waveformgenerator (4) for each supported sp_roi (max of 10)
        dev_dct['PVS_DONT_RECORD']['e712_x_useddl'] = BaseDevice('SIM_%s:wg1:useddl' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_useddl'] = BaseDevice('SIM_%s:wg2:useddl' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_usereinit'] = BaseDevice('SIM_%s:wg1:usereinit' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_usereinit'] = BaseDevice('SIM_%s:wg2:usereinit' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_strtatend'] = BaseDevice('SIM_%s:wg1:strtatend' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_strtatend'] = BaseDevice('SIM_%s:wg2:strtatend' % e712_prfx)

        dev_dct['PVS_DONT_RECORD']['e712_x_usetablenum'] = BaseDevice('SIM_%s:WavGen1UseTblNum' % e712_prfx)
        dev_dct['PVS_DONT_RECORD']['e712_y_usetablenum'] = BaseDevice('SIM_%s:WavGen2UseTblNum' % e712_prfx)

def connect_ES_devices(dev_dct, prfx='uhv'):
    if(prfx.find('uhv') > -1):
        #dev_dct['TEMPERATURES'][POS_TYPE_ES]['CCTL1610-I10:temp:fbk'] = BaseDevice('CCTL1610-I10:temp:fbk', desc='Gatan rod temp')
        pass
    else:
        pass

def connect_BL_devices(dev_dct, prfx='uhv'):
    if(prfx.find('uhv') > -1):
        dev_dct['DIO']['InterferShutter'] = PvShutter('SIM_%sDIO-2:shutter:ctl' % prfx)

        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-01:vac:p'] = BaseDevice('SIM_CCG1410-01:vac:p', desc='Sec. 1', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-I00-01:vac:p'] = BaseDevice('SIM_CCG1410-I00-01:vac:p', desc='Sec. 2', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-I00-02:vac:p'] = BaseDevice('SIM_CCG1410-I00-02:vac:p', desc='Sec. 4', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-1-I00-02:vac:p'] = BaseDevice('SIM_CCG1610-1-I00-02:vac:p', desc='Sec. 6', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['HCG1610-1-I00-01:vac:p'] = BaseDevice('SIM_HCG1610-1-I00-01:vac:p', desc='Sec. 7', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-1-I00-03:vac:p'] = BaseDevice('SIM_CCG1610-1-I00-03:vac:p', desc='Sec. 8', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-01:vac:p'] = BaseDevice('SIM_CCG1610-I10-01:vac:p', desc='Sec. 10', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-02:vac:p'] = BaseDevice('SIM_CCG1610-I10-02:vac:p', desc='Sec. 11', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-03:vac:p'] = BaseDevice('SIM_CCG1610-I10-03:vac:p', desc='Sec. 12', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-04:vac:p'] = BaseDevice('SIM_CCG1610-I10-04:vac:p', desc='Sec. 13', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I12-01:vac:p'] = BaseDevice('SIM_CCG1610-I12-01:vac:p',desc='Sec. 14', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I12-02:vac:p'] = BaseDevice('SIM_CCG1610-I12-02:vac:p', desc='Sec. 15', units='torr')
        dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-3-I12-01:vac:p'] = BaseDevice('SIM_CCG1610-3-I12-01:vac:p', desc='Sec. 16', units='torr')

    else:
        pass

#Feb6	dev_dct['ACTUATORS']['SSH'] = PvValve('SSH1410-I00-01')
#Feb6	dev_dct['ACTUATORS']['PSH'] = PvValve('PSH1410-I00-02')
#Feb6	dev_dct['ACTUATORS']['SM-PSH'] = PvValve('PSH1610-1-I10-01')
#Feb6	dev_dct['ACTUATORS']['BSH'] = PvValve('VVR1610-I12-03')


def print_keys(d):
    if(isinstance(d, list)):
        print_keys(d[0])

    for key in d:
        if(isinstance(d[key], dict)):
            print_keys(d[key])
        else:
            print(key, d[key].is_active())






MAIN_OBJ = None
DEVICE_CFG = None

if(AMBIENT_STXM):
    MAIN_OBJ = main_object_base('CLS SM 10ID1', 'Ambient STXM', BEAMLINE_IDS.STXM)
    MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
    MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.SAMPLEFINE)
    MAIN_OBJ.set_datafile_prefix('A')
    MAIN_OBJ.set_thumbfile_suffix('jpg')
    MAIN_OBJ.set_endstation_prefix('amb')

    #DEVICE_CFG = dev_config()
    splash = get_splash(img_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyStxmSplash.png'))
    DEVICE_CFG = dev_config_sim_ambient(splash=splash, sample_pos_mode=sample_positioning_modes.COARSE, fine_sample_pos_mode=sample_fine_positioning_modes.SAMPLEFINE)
    MAIN_OBJ.set_devices(DEVICE_CFG)
    DEFAULTS = Defaults('ambstxm_dflts.json', new=False)

    #MAIN_OBJ.device_report()
    #scanning_mode = appConfig.get_value('MAIN', 'scanning_mode')
else:

    MAIN_OBJ = main_object_base('CLS SM 10ID1','UHV STXM', BEAMLINE_IDS.STXM)
    #MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
    MAIN_OBJ.set_datafile_prefix('C')
    MAIN_OBJ.set_thumbfile_suffix('jpg')
    MAIN_OBJ.set_endstation_prefix('uhv')
    ver_str = 'Version %s.%s' % (MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'))
    splash = get_splash(img_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyStxmSplash.png'),
                        ver_str=ver_str)
    #sample_positioning_mode = appConfig.get_value('MAIN', 'sample_positioning_mode')
    #fine_sample_positioning_mode = appConfig.get_value('MAIN', 'fine_sample_positioning_mode')
    scanning_mode = appConfig.get_value('MAIN', 'scanning_mode')

    # sample_mode = None
    # fine_sample_mode = None
    #
    # if(sample_positioning_mode == 'GONIOMETER'):
    #     #must be ZONEPLATE SCANNING, so set all
    #     MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.GONIOMETER)
    #     MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
    #     MAIN_OBJ.set_sample_scanning_mode_string('Zoneplate Scanning')
    #
    #     sample_mode = sample_positioning_modes.GONIOMETER
    #     fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE
    #
    #
    # elif(sample_positioning_mode == 'SAMPLEXY'):
    #     #set coarse mode
    #     MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
    #     sample_mode = sample_positioning_modes.COARSE
    #     MAIN_OBJ.set_sample_scanning_mode_string('Conventional Scanning')
    #     #set fine mode
    #     if (fine_sample_positioning_mode == 'SAMPLE'):
    #         MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.SAMPLEFINE)
    #         fine_sample_mode = sample_fine_positioning_modes.SAMPLEFINE
    #     else:
    #         MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
    #         fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE
    #
    # elif (sample_positioning_mode == 'HYBRID'):
    #     # set coarse mode
    #     MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
    #     MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
    #     sample_mode = sample_positioning_modes.COARSE
    #     fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE
    #     MAIN_OBJ.set_sample_scanning_mode_string('Hybrid Scanning')
    #
    # if((sample_mode is not None) and (fine_sample_mode is not None)):
    #     DEVICE_CFG = dev_config_uhv(splash=splash, sample_pos_mode=sample_mode, fine_sample_pos_mode=fine_sample_mode)
    #     MAIN_OBJ.set_devices(DEVICE_CFG)
    #     DEFAULTS = Defaults('uhvstxm_dflts.json', new=False)
    # else:
    #     print 'NO SAMPLE POSITIONING MODE SELECTED'
    #     exit()
    sample_mode = None
    fine_sample_mode = None

    # COARSE_SAMPLEFINE (formerly 'conventional') scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=SAMPLE_FINE
    # scanning_mode = COARSE_SAMPLEFINE

    # GONI_ZONEPLATE scanning mode = Sample_pos_mode=GONIOMETER, sample_fine_pos_mode=ZONEPLATE
    # scanning_mode = GONI_ZONEPLATE

    # COARSE_ZONEPLATE scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=ZONEPLATE
    # scanning_mode = COARSE_ZONEPLATE

    if (scanning_mode == 'GONI_ZONEPLATE'):
        # must be ZONEPLATE SCANNING, so set all
        MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.GONIOMETER)
        MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
        MAIN_OBJ.set_sample_scanning_mode_string('GONI_ZONEPLATE Scanning')

        sample_mode = sample_positioning_modes.GONIOMETER
        fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE


    elif (scanning_mode == 'COARSE_SAMPLEFINE'):
        # set coarse mode
        MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
        sample_mode = sample_positioning_modes.COARSE
        MAIN_OBJ.set_sample_scanning_mode_string('COARSE_SAMPLEFINE Scanning')
        MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.SAMPLEFINE)
        fine_sample_mode = sample_fine_positioning_modes.SAMPLEFINE
        #else:
        #    MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
        #    fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE

    elif (scanning_mode == 'COARSE_ZONEPLATE'):
        # set coarse mode
        MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
        MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
        sample_mode = sample_positioning_modes.COARSE
        fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE
        MAIN_OBJ.set_sample_scanning_mode_string('COARSE_ZONEPLATE Scanning')

    if ((sample_mode is not None) and (fine_sample_mode is not None)):
        DEVICE_CFG = dev_config_uhv(splash=splash, sample_pos_mode=sample_mode, fine_sample_pos_mode=fine_sample_mode)
        MAIN_OBJ.set_devices(DEVICE_CFG)
        DEFAULTS = Defaults('uhvstxm_dflts.json', new=False)
    else:
        print('NO SAMPLE POSITIONING MODE SELECTED')
        exit()

    #DEVICE_CFG.device_report()



class cfgReader(QtCore.QObject):
    new_message = QtCore.pyqtSignal(object)

    def __init__(self):
        super(cfgReader, self).__init__()
    #globalRegistry.register([], IBeamline, '', self)

    def read_devices(self):
        devcfg = dev_config()
        DEVICES = devcfg.get_devices()
        for dev in list(DEVICES.keys()):
            (hlth,hstr) = DEVICES[dev].state_info['health']
            if(hlth):
                conStr = 'GOOD'
            else:
                conStr = 'NOT_GOOD'
            s = 'Connection to : [%s] is %s' % (dev, conStr)
            self.new_message.emit(s)




if __name__ == '__main__':
    global app
    import sys
    app = QtWidgets.QApplication(sys.argv)
    def on_dev_status(msg):
        print(msg)

    cfgRdr = cfgReader()
    cfgRdr.new_message.connect(on_dev_status)
    cfgRdr.read_devices()


    app.quit()

    print('done')
	

