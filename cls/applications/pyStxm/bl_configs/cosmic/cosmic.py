'''
Created on May 16, 2019

@author: bergr
'''

# BCM GLOBAL Settings for stxm
import os

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets

from bcm.devices import BaseDevice
from bcm.devices import Mbbi
from bcm.devices import Mbbo
from bcm.devices import Bo
from bcm.devices import Motor_Qt
from bcm.devices import sample_abstract_motor
from bcm.devices import BaseGate, BaseCounter
from bcm.devices.device_names import *
from bcm.devices import PvShutter

from cls.appWidgets.main_object import dev_config_base, POS_TYPE_BL, POS_TYPE_ES
from cls.appWidgets.splashScreen import get_splash
from cls.app_data.defaults import Defaults
from cls.applications.pyStxm import abs_path_to_ini_file
from cls.types.stxmTypes import sample_positioning_modes, sample_fine_positioning_modes, endstation_id_types
from cls.utils.cfgparser import ConfigClass
from cls.utils.log import get_module_logger
from cls.scan_engine.bluesky.test_detector import PointDetectorDevice, LineDetectorFlyerDevice, LineDetectorDevice
from cls.scan_engine.bluesky.test_gate import GateDevice
from cls.applications.pyStxm.bl_configs.utils import make_basedevice, get_config_name

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)
blConfig = ConfigClass(__file__.replace('.py', '.ini'))
# when simulating un comment the next line
DEVPRFX = 'SIM_'


# and comment this one
# DEVPRFX = ''


class device_config(dev_config_base):
    def __init__(self, splash=None, sample_pos_mode=sample_positioning_modes.COARSE,
                 fine_sample_pos_mode=sample_fine_positioning_modes.SAMPLEFINE):
        super(device_config, self).__init__(splash=splash)
        print('Using COSMIC STXM DEVICES')
        self.beamline = 'Lab STXM COSMIC'
        self.bl_config_prfx = get_config_name(__file__)
        #self.es_id = endstation_id_types.BASIC
        self.es_id = 'COSMIC'
        self.sample_pos_mode = sample_pos_mode
        self.fine_sample_pos_mode = fine_sample_pos_mode
        self.sample_rot_angle_dev = None
        # self.splash = splash
        self.done = False
        self.init_devices()
        self.device_reverse_lookup_dct = self.make_device_reverse_lookup_dict()
        # elif (self.sample_pos_mode is sample_positioning_modes.COARSE):
        # if (self.fine_sample_pos_mode is sample_fine_positioning_modes.SAMPLEFINE):

        # the following is a list of positioners that will not show up on teh devices panel
        self.exclude_list = [DNM_GONI_X, DNM_GONI_Y, DNM_GONI_Z, DNM_GONI_THETA, DNM_ZONEPLATE_Z_BASE,
                             DNM_SAMPLE_FINE_X, DNM_SAMPLE_FINE_Y, DNM_OSA_Z,
                             'AUX1', 'AUX2', 'Cff', 'PeemM3Trans']

        print('leaving device_config')

    def parse_cainfo_stdout_to_dct(self, s):
        dct = {}
        s2 = s.split('\n')
        for l in s2:
            l2 = l.replace(' ', '')
            l3 = l2.split(':')
            if (len(l3) > 1):
                dct[l3[0]] = l3[1]
        return (dct)

    def do_cainfo(self, pvname):
        import subprocess
        print('cainfo [%s]' % pvname)
        proc = subprocess.Popen('cainfo %s' % pvname, stdout=subprocess.PIPE)
        stdout_str = proc.stdout.read()
        _dct = self.parse_cainfo_stdout_to_dct(stdout_str)
        return (_dct)

    def get_cainfo(self):

        skip_lst = ['PVS_DONT_RECORD', 'PRESETS', 'DETECTORS_NO_RECORD', 'WIDGETS']
        dev_dct = {}
        sections = list(self.devices.keys())
        for section in sections:
            keys = []
            if (section not in skip_lst):
                keys = list(self.devices[section].keys())
                # check to see if this is a subsectioned section that has pvs for BL (beamline) and ES (endstation)
                # if so do those
                if (keys == ['BL', 'ES']):
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
                        if (not hasattr(dev, 'get_name')):
                            print('crap!', dev)
                        _dct = self.do_cainfo(dev.get_name())
                        dev_dct[section][k]['cainfo'] = _dct
                        if (_dct['State'].find('dis') > -1):
                            print('[%s] does not appear to exist' % k)
                            print(_dct)

        # dev_dct

    # def init_presets(self):
    #     # these need to come from teh app.ini file FINE_SCAN_RANGES, leave as hack for now till I get time
    #
    #     maxCX = appConfig.get_value('SCAN_RANGES', 'coarse_x')
    #     maxCY = appConfig.get_value('SCAN_RANGES', 'coarse_y')
    #     maxFX = appConfig.get_value('SCAN_RANGES', 'fine_x')
    #     maxFY = appConfig.get_value('SCAN_RANGES', 'fine_y')
    #     use_laser = appConfig.get_value('MAIN', 'use_laser')
    #     ptycho_enabled = appConfig.get_value('MAIN', 'ptychography_enabled')
    #
    #     # self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = 98
    #     # self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = 98
    #
    #     if (self.sample_pos_mode is sample_positioning_modes.GONIOMETER):
    #         self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = maxFX
    #         self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = maxFY
    #     else:
    #         self.devices['PRESETS']['MAX_SCAN_RANGE_X'] = maxCX
    #         self.devices['PRESETS']['MAX_SCAN_RANGE_Y'] = maxCY
    #
    #     self.devices['PRESETS']['MAX_FINE_SCAN_RANGE_X'] = maxFX
    #     self.devices['PRESETS']['MAX_FINE_SCAN_RANGE_Y'] = maxFY

    def init_devices(self):

        # I don't have an elegant way yet to create these and also emit a signal to the splash screen
        # so this is a first attempt
        # self.timer.start(100)
        # maps names to device objects
        # self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = Motor_Qt('%sIOC:m100' % DEVPRFX, pos_set=POS_TYPE_ES)
        # self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = Motor_Qt('%sIOC:m101' % DEVPRFX, pos_set=POS_TYPE_ES)

        prfx = self.bl_config_prfx
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_X)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_X] = Motor_Qt('%sIOC:m100' % DEVPRFX,
                                                                  name='%sIOC:m100' % DEVPRFX,
                                                                  pos_set=POS_TYPE_ES)
        # self.devices['POSITIONERS'][DNM_FINE_X] = Motor_Qt('%sIOC:m100', name='%sIOC:m100')
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_FINE_Y)
        self.devices['POSITIONERS'][DNM_SAMPLE_FINE_Y] = Motor_Qt('%sIOC:m101' % DEVPRFX,
                                                                  name='%sIOC:m101' % DEVPRFX,
                                                                  pos_set=POS_TYPE_ES)
        # self.devices['POSITIONERS'][DNM_FINE_Y] = Motor_Qt('%sIOC:m101', name='%sIOC:m101')
        self.msg_splash("connecting to: [%s]" % DNM_COARSE_X)
        self.devices['POSITIONERS'][DNM_COARSE_X] = Motor_Qt('%sIOC:m112' % DEVPRFX, name='%sIOC:m112' % DEVPRFX,
                                                             pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_COARSE_Y)
        self.devices['POSITIONERS'][DNM_COARSE_Y] = Motor_Qt('%sIOC:m113' % DEVPRFX, name='%sIOC:m113' % DEVPRFX,
                                                             pos_set=POS_TYPE_ES)
        # self.msg_splash("connecting to: [%s]" % DNM_COARSE_Z)
        # self.devices['POSITIONERS'][DNM_COARSE_Z] = Motor_Qt('%sIOC:m121' % DEVPRFX, name='%sIOC:m121' % DEVPRFX,
        #                                                      pos_set=POS_TYPE_ES)

        self.msg_splash("connecting to: [%s]" % DNM_OSA_X)
        self.devices['POSITIONERS'][DNM_OSA_X] = Motor_Qt('%sIOC:m104' % DEVPRFX, name='%sIOC:m104' % DEVPRFX,
                                                          pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Y)
        self.devices['POSITIONERS'][DNM_OSA_Y] = Motor_Qt('%sIOC:m105' % DEVPRFX, name='%sIOC:m105' % DEVPRFX,
                                                          pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Z)
        # self.devices['POSITIONERS'][DNM_OSA_Z] = Motor_Qt('%sIOC:m106C' % DEVPRFX, name='%sIOC:m106C' % DEVPRFX,
        #                                                   pos_set=POS_TYPE_ES, collision_support=True)
        self.devices['POSITIONERS'][DNM_OSA_Z] = Motor_Qt('%sIOC:m106' % DEVPRFX, name='%sIOC:m106C' % DEVPRFX,
                                                          pos_set=POS_TYPE_ES, collision_support=False)
        self.msg_splash("connecting to: [%s]" % DNM_OSA_Z_BASE)
        self.devices['POSITIONERS'][DNM_OSA_Z_BASE] = Motor_Qt('%sIOC:m106' % DEVPRFX, name='%sIOC:m106' % DEVPRFX, )

        # self.devices['POSITIONERS'][DNM_GONI_THETA] = sample_abstract_motor('%sIOC:m110' % DEVPRFX,
        #                                                                     name='%sIOC:m110' % DEVPRFX,
        #                                                                     pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_X)
        self.devices['POSITIONERS'][DNM_DETECTOR_X] = Motor_Qt('%sIOC:m114' % DEVPRFX, name='%sIOC:m114' % DEVPRFX,
                                                               pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_Y)
        self.devices['POSITIONERS'][DNM_DETECTOR_Y] = Motor_Qt('%sIOC:m115' % DEVPRFX, name='%sIOC:m115' % DEVPRFX,
                                                               pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_DETECTOR_Z)
        self.devices['POSITIONERS'][DNM_DETECTOR_Z] = Motor_Qt('%sIOC:m116' % DEVPRFX, name='%sIOC:m116' % DEVPRFX,
                                                               pos_set=POS_TYPE_ES)

        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Z)
        # self.devices['POSITIONERS'][DNM_ZONEPLATE_Z] = Motor_Qt('%sIOC:m111C' % DEVPRFX, name='%sIOC:m111C' % DEVPRFX,
        #                                                         pos_set=POS_TYPE_ES, collision_support=True)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z] = Motor_Qt('%sIOC:m111C' % DEVPRFX, name='%sIOC:m111C' % DEVPRFX,
                                                                pos_set=POS_TYPE_ES, collision_support=False)
        self.msg_splash("connecting to: [%s]" % DNM_ZONEPLATE_Z_BASE)
        self.devices['POSITIONERS'][DNM_ZONEPLATE_Z_BASE] = Motor_Qt('%sIOC:m111' % DEVPRFX,
                                                                     name='%sIOC:m111' % DEVPRFX)

        # self.devices['POSITIONERS'][DNM_SAMPLE_X] = Motor_Qt( '%sIOC:m117' % DEVPRFX, pos_set=POS_TYPE_ES)
        # self.devices['POSITIONERS'][DNM_SAMPLE_Y] = Motor_Qt('%sIOC:m118' % DEVPRFX, pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_X)
        self.devices['POSITIONERS'][DNM_SAMPLE_X] = sample_abstract_motor('%sIOC:m117' % DEVPRFX,
                                                                          name='%sIOC:m117' % DEVPRFX,
                                                                          pos_set=POS_TYPE_ES)
        self.msg_splash("connecting to: [%s]" % DNM_SAMPLE_Y)
        self.devices['POSITIONERS'][DNM_SAMPLE_Y] = sample_abstract_motor('%sIOC:m118' % DEVPRFX,
                                                                          name='%sIOC:m118' % DEVPRFX,
                                                                          pos_set=POS_TYPE_ES)

        connect_standard_beamline_devices(self.devices, devcfg=self)
        connect_devices(self.devices, devcfg=self)
        connect_temperatures(self.devices, devcfg=self)
        connect_pressures(self.devices, devcfg=self)

        # check_if_pv_exists(self.devices['POSITIONERS'])
        # for key, value in self.devices.iteritems():
        # 	print key,value

        print('finished connecting to devices')
        self.done = True

    def make_device_reverse_lookup_dict(self):
        subcat_lst = ['PRESSURES', 'TEMPERATURES']
        skip_lst = ['DETECTORS', 'DETECTORS_NO_RECORD', 'DIO', 'SSCANS', 'PVS_DONT_RECORD', 'PRESETS', 'WIDGETS']
        dct = {}
        for category in self.devices.keys():
            if (category in skip_lst):
                continue
            if (category in subcat_lst):
                for subcat in self.devices[category].keys():
                    dev_dct = self.devices[category][subcat]
                    for dev_nm, dev in dev_dct.items():
                        # dct[dev.get_name()] = self.fix_device_nm(dev_nm)
                        dct[dev_nm] = dev.get_name()
            else:
                dev_dct = self.devices[category]
                for dev_nm, dev in dev_dct.items():
                    # dct[dev.get_name()] = self.fix_device_nm(dev_nm)
                    dct[dev_nm] = dev.get_name()

        return (dct)

    def fix_device_nm(self, nm_str):
        l = nm_str.lower()
        l = l.replace('.', '_')
        return (l)


def connect_standard_beamline_devices(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
        connect standard beamline deivces
    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''
    devcfg.msg_splash("connecting to: [%s]" % DNM_ENERGY)
    dev_dct['POSITIONERS'][DNM_ENERGY] = Motor_Qt('%s:ENERGY' % prfx, name='%s:ENERGY' % prfx,
                                                  abstract_mtr=True, pos_set=POS_TYPE_ES)
    devcfg.msg_splash("connecting to: [%s]" % DNM_SLIT_X)
    dev_dct['POSITIONERS'][DNM_SLIT_X] = Motor_Qt('%s:slitX' % prfx, name='%s:slitX' % prfx,
                                                  abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_SLIT_Y)
    dev_dct['POSITIONERS'][DNM_SLIT_Y] = Motor_Qt('%s:slitY' % prfx, name='%s:slitY' % prfx,
                                                  abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_M3_PITCH)
    dev_dct['POSITIONERS'][DNM_M3_PITCH] = Motor_Qt('%s:m3STXMPitch' % prfx,
                                                    name='%s:m3STXMPitch' % prfx, abstract_mtr=True,
                                                    pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_GAP)
    dev_dct['POSITIONERS'][DNM_EPU_GAP] = Motor_Qt('%s:epuGap' % prfx,
                                                   name='%s:epuGap' % prfx, abstract_mtr=True,
                                                   pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_OFFSET)
    dev_dct['POSITIONERS'][DNM_EPU_OFFSET] = Motor_Qt('%s:epuOffset' % prfx,
                                                      name='%s:epuOffset' % prfx, abstract_mtr=True,
                                                      pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_HARMONIC)
    dev_dct['POSITIONERS'][DNM_EPU_HARMONIC] = Motor_Qt('%s:epuHarmonic' % prfx,
                                                        name='%s:epuHarmonic' % prfx, abstract_mtr=True,
                                                        pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_POLARIZATION)
    dev_dct['POSITIONERS'][DNM_EPU_POLARIZATION] = Motor_Qt('%s:epuPolarization' % prfx,
                                                            name='%s:epuPolarization' % prfx,
                                                            abstract_mtr=True, pos_set=POS_TYPE_BL)
    devcfg.msg_splash("connecting to: [%s]" % DNM_EPU_ANGLE)
    dev_dct['POSITIONERS'][DNM_EPU_ANGLE] = Motor_Qt('%s:epuAngle' % prfx,
                                                     name='%s:epuAngle' % prfx, abstract_mtr=True,
                                                     pos_set=POS_TYPE_BL)

    dev_dct['PVS'][DNM_RING_CURRENT] = make_basedevice('PVS', '%sPCT1402-01:mA:fbk' % (DEVPRFX), units='mA',
                                                       devcfg=devcfg)


def connect_devices(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
        connect to general devices
    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''

    devcfg.msg_splash("connecting to: [%s-CO:gate]" % (prfx))
    dev_dct['DIO'][DNM_GATE] = BaseGate('%s-CO:gate' % (prfx))
    devcfg.msg_splash("connecting to: [%s]" % DNM_SHUTTER)
    dev_dct['DIO'][DNM_SHUTTER] = PvShutter('%s-DIO:shutter:ctl' % (prfx))
    # devcfg.msg_splash("connecting to: [%s]" % 'ShutterTaskRun')WavGen3UseTblNum
    dev_dct['DIO']['ShutterTaskRun'] = make_basedevice('DIO', '%s-DIO:shutter:Run' % (prfx), devcfg=devcfg)

    devcfg.msg_splash("connecting to: [%s]" % DNM_COUNTER_APD)
    dev_dct['DETECTORS'][DNM_COUNTER_APD] = BaseCounter('%s-CI:counter' % (prfx))
    dev_dct['DETECTORS'][DNM_DEFAULT_COUNTER] = PointDetectorDevice('%s-CI:counter:' % (prfx),
                                                                    name=DNM_DEFAULT_COUNTER, scale_val=100.0)

    # dev_dct['DETECTORS']['Det_Cntr'] = EpicsPvCounter('%sPMT:ctr:SingleValue_RBV' % prfx)
    dev_dct['DETECTORS'][DNM_PMT] = make_basedevice('DETECTORS', '%s-PMT:ctr:SingleValue_RBV' % (prfx),
                                                    devcfg=devcfg)
    # dev_dct['DETECTORS']['Det_Cntr'] = EpicsPvCounter('%sPMT:ctr:SingleValue_RBV' % prfx)

    # dev_dct['DETECTORS'][DNM_GREATEYES_CCD] = GreatEyesDetectorCam('%sCCD1610-02:cam1:'  % (DEVPRFX), name='GE_CCD')
    # if(DEVPRFX.find('SIM')):
    #     dev_dct['DETECTORS'][DNM_GREATEYES_CCD] = SimGreatEyesCCD('SIMCCD1610-I10-02:', name=DNM_GREATEYES_CCD)
    # else:
    #     dev_dct['DETECTORS'][DNM_GREATEYES_CCD] = GreatEyesCCD('CCD1610-I10-02:', name=DNM_GREATEYES_CCD)

    dev_dct['DETECTORS'][DNM_POINT_DET] = PointDetectorDevice('%s-CI:counter:' % (prfx),
                                                              name=DNM_DEFAULT_COUNTER)
    dev_dct['DIO'][DNM_POINT_GATE] = GateDevice('%s-CO:gate:' % (prfx), name='gate_control')

    dev_dct['DETECTORS'][DNM_LINE_DET] = LineDetectorDevice('%s-CI:counter:' % (prfx),
                                                            name=DNM_DEFAULT_COUNTER)
    dev_dct['DETECTORS'][DNM_LINE_DET_FLYER] = LineDetectorFlyerDevice('%s-CI:counter:' % (prfx),
                                                                       name=DNM_DEFAULT_COUNTER,
                                                                       stream_names={'line_det_strm': 'primary'},
                                                                       monitor_attrs=['waveform_rbv'], pivot=False)

    dev_dct['PVS'][DNM_IDEAL_A0] = make_basedevice('PVS', '%s:ENERGY:zp:fbk:tr_K' % (prfx),
                                                   devcfg=devcfg)
    dev_dct['PVS'][DNM_CALCD_ZPZ] = make_basedevice('PVS', '%s:ENERGY:zp:fbk:tr_I' % (prfx),
                                                    devcfg=devcfg)
    dev_dct['PVS']['Zpz_adjust'] = make_basedevice('PVS', '%s:ENERGY:zp:adjust_zpz' % (prfx),
                                                   devcfg=devcfg)

    dev_dct['PVS'][DNM_ZONEPLATE_SCAN_MODE] = Mbbo('%s:ENERGY:zp:scanselflag' % (prfx))  # used to control which value gets sent to Zpz, fl or fl - A0
    dev_dct['PVS'][DNM_ZONEPLATE_INOUT] = Bo('%s:zp_inout' % (prfx))
    dev_dct['PVS'][DNM_ZONEPLATE_INOUT_FBK] = Mbbi('%s:zp_inout:fbk' % (prfx))  # used to convieniently move zp z in and out
    # used to adjust the current focus value, the delta represents the relative microns for zpz to move to new focus position
    dev_dct['PVS'][DNM_DELTA_A0] = make_basedevice('PVS', '%s:ENERGY:delta_A0' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_FOCAL_LEN] = make_basedevice('PVS', '%s:ENERGY:zp:FL' % (prfx), units='um',  devcfg=devcfg)
    dev_dct['PVS'][DNM_A0] = make_basedevice('PVS', '%s:ENERGY:A0' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_A0MAX] = make_basedevice('PVS', '%s:ENERGY:A0Max' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_A0_FOR_CALC] = make_basedevice('PVS', '%s:ENERGY:A0:for_calc' % (prfx),  devcfg=devcfg)

    devcfg.msg_splash("connecting to: [%s]" % 'zoneplate definitions')
    dev_dct['PVS'][DNM_ZPZ_POS] = make_basedevice('PVS', '%s:ENERGY:zp:zpz_pos' % (prfx), devcfg=devcfg)
    # dev_dct['PVS']['Zp_def'] = Transform('%sBL1610-I10:ENERGY:zp:def' % (prfx))
    # dev_dct['PVS']['OSA_def'] = Transform('%sBL1610-I10:ENERGY:%s:osa:def' % (prfx))

    dev_dct['PVS'][DNM_ZP_SELECT] = Mbbo('%s:ENERGY:zp' % (prfx))
    dev_dct['PVS'][DNM_OSA_SELECT] = Mbbo('%s:ENERGY:osa' % (prfx))

    devcfg.msg_splash("connecting to: [%s]" % 'Energy_enable')
    dev_dct['PVS'][DNM_ENERGY_ENABLE] = Bo('%s:ENERGY:enabled' % (prfx))
    dev_dct['PVS'][DNM_ENERGY_RBV] = make_basedevice('PVS', '%s:ENERGY.RBV' % (prfx), units='um', devcfg=devcfg)
    dev_dct['PVS'][DNM_ZPZ_RBV] = make_basedevice('PVS', '%sIOC:m111C.RBV' % (DEVPRFX), units='um', devcfg=devcfg)

    dev_dct['PVS'][DNM_ZP_DEF_A] = make_basedevice('PVS', '%s:ENERGY:zp:def_A' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_ZP_DEF1_A] = make_basedevice('PVS', '%s:ENERGY:zp1:def_A' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_ZP_DEF2_A] = make_basedevice('PVS', '%s:ENERGY:zp2:def_A' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_ZP_DEF3_A] = make_basedevice('PVS', '%s:ENERGY:zp3:def_A' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_ZP_DEF4_A] = make_basedevice('PVS', '%s:ENERGY:zp4:def_A' % (prfx), devcfg=devcfg)
    dev_dct['PVS'][DNM_ZP_DEF5_A] = make_basedevice('PVS', '%s:ENERGY:zp5:def_A' % (prfx), devcfg=devcfg)

    # dev_dct['PVS']['SRStatus_msgL1'] = BaseDevice('SRStatus:msg:tL1')
    # dev_dct['PVS']['SRStatus_msgL2'] = BaseDevice('SRStatus:msg:tL2')
    # dev_dct['PVS']['SRStatus_msgL3'] = BaseDevice('SRStatus:msg:tL3')

    # dev_dct['PVS']['mbbiSYSTEM:mode:fbk'] = Mbbi('SYSTEM:mode:fbk')
    dev_dct['PVS'][DNM_BEAM_DEFOCUS] = make_basedevice('PVS', '%s:ENERGY:zp:defocus' % (prfx), units='um', devcfg=devcfg)
    dev_dct['PVS_DONT_RECORD']['CX_auto_disable_power'] = make_basedevice('PVS_DONT_RECORD', '%sIOC:m112:XPS_AUTO_DISABLE_MODE' % (  DEVPRFX), devcfg=devcfg)
    dev_dct['PVS_DONT_RECORD']['CY_auto_disable_power'] = make_basedevice('PVS_DONT_RECORD','%sIOC:m113:XPS_AUTO_DISABLE_MODE' % ( DEVPRFX), devcfg=devcfg)
    dev_dct['PVS_DONT_RECORD']['DX_auto_disable_power'] = make_basedevice('PVS_DONT_RECORD','%sIOC:m114:XPS_AUTO_DISABLE_MODE' % ( DEVPRFX), devcfg=devcfg)
    dev_dct['PVS_DONT_RECORD']['DY_auto_disable_power'] = make_basedevice('PVS_DONT_RECORD','%sIOC:m115:XPS_AUTO_DISABLE_MODE' % ( DEVPRFX), devcfg=devcfg)

    dev_dct['PVS_DONT_RECORD']['accRange'] = make_basedevice('PVS_DONT_RECORD', '%s-TestSIG:signal:MaxPoints' % (prfx), devcfg=devcfg)
    # dev_dct['PVS_DONT_RECORD']['FX_force_done'] = make_basedevice(  ,'%sIOC:m100:ForceDone' % (DEVPRFX))
    # dev_dct['PVS_DONT_RECORD']['FY_force_done'] = make_basedevice(  ,'%sIOC:m101:ForceDone' % (DEVPRFX))

    dev_dct['PVS'][DNM_AX1_INTERFER_VOLTS] = make_basedevice('PVS', '%s-Ai:ai:ai0_RBV' % (prfx), rd_only=True, devcfg=devcfg)
    dev_dct['PVS'][DNM_AX2_INTERFER_VOLTS] = make_basedevice('PVS', '%s-Ai:ai:ai1_RBV' % (prfx), rd_only=True, devcfg=devcfg)

    connect_ES_devices(dev_dct, prfx, devcfg=devcfg)
    connect_BL_devices(dev_dct, prfx, devcfg=devcfg)
    connect_heartbeats(dev_dct, prfx, devcfg=devcfg)


def connect_pressures(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
    connect all pressures, subcatagorized by:
        POS_TYPE_ES for Endstation pressures
        POS_TYPE_BL for Beamline pressures

    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''
    # pressures
    # devcfg.msg_splash("connecting to PRESSURES: [FRG1610-3-I12-01:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['FRG1610-3-I12-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sFRG1610-3-I12-01:vac:p' % (
                                                                                      DEVPRFX), desc='Chamber pressure',
                                                                                  units='torr', devcfg=devcfg)
    # devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-03:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-03:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sTCG1610-3-I12-03:vac:p' % (
                                                                                      DEVPRFX),
                                                                                  desc='Turbo backing pressure',
                                                                                  units='torr', devcfg=devcfg)
    # devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-04:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-04:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sTCG1610-3-I12-04:vac:p' % (
                                                                                      DEVPRFX),
                                                                                  desc='Load lock pressure',
                                                                                  units='torr', devcfg=devcfg)
    # devcfg.msg_splash("connecting to PRESSURES: [TCG1610-3-I12-05:vac:p]")
    dev_dct['PRESSURES'][POS_TYPE_ES]['TCG1610-3-I12-05:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sTCG1610-3-I12-05:vac:p' % (
                                                                                      DEVPRFX),
                                                                                  desc='Rough line pressure',
                                                                                  units='torr', devcfg=devcfg)


def connect_temperatures(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
    connect all temperatures, subcatagorized by:
        POS_TYPE_ES for Endstation temperatures
        POS_TYPE_BL for Beamline temperatures
    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''
    # ES = endstation temperatures
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-01]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-01'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-01' % (DEVPRFX),
                                                                              desc='Turbo cooling water', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-30]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-30'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-30' % (DEVPRFX),
                                                                              desc='Sample Coarse Y', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-32]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-32'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-32' % (DEVPRFX),
                                                                              desc='Detector Y', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-21]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-21'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-21' % (DEVPRFX),
                                                                              desc='Chamber temp #1', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-22]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-22'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-22' % (DEVPRFX),
                                                                              desc='Chamber temp #2', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-23]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-23'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-23' % (DEVPRFX),
                                                                              desc='Chamber temp #3', units='deg C',
                                                                              devcfg=devcfg)
    # devcfg.msg_splash("connecting to TEMPERATURES: [TM1610-3-I12-24]")
    dev_dct['TEMPERATURES'][POS_TYPE_ES]['TM1610-3-I12-24'] = make_basedevice('TEMPERATURES',
                                                                              '%sTM1610-3-I12-24' % (DEVPRFX),
                                                                              desc='Chamber temp #4', units='deg C',
                                                                              devcfg=devcfg)


def connect_heartbeats(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
        connect application heartbeat pvs
    :param dev_dct:
    :param prfx:
    :return:
    '''
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS'] = {}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['blApi_hrtbt'] = {'dev': Bo('%s-BlApi:hrtbt:alive' % (prfx)),
                                                               'desc': 'BlApi App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['ai_hrtbt'] = {'dev': Bo('%s-AI:hrtbt:alive' % (prfx)),
                                                            'desc': 'AnalogInput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['ci_hrtbt'] = {'dev': Bo('%s-CI:hrtbt:alive' % (prfx)),
                                                            'desc': 'CounterInput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['co_hrtbt'] = {'dev': Bo('%s-CO:hrtbt:alive' % (prfx)),
                                                            'desc': 'CounterOutput App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['dio_hrtbt'] = {'dev': Bo('%s-DIO:hrtbt:alive' % (prfx)),
                                                             'desc': 'Digital IO App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_hrtbt'] = {
        'dev': Bo('%s-MTRS:hrtbt:alive' % (prfx)), 'desc': 'Main Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtr_calib_hrtbt'] = {
        'dev': Bo('%s-MTR_CALIB:hrtbt:alive' % (prfx)), 'desc': 'MotorCalibrations'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_osa_hrtbt'] = {
        'dev': Bo('%s-MTR_OSA:hrtbt:alive' % (prfx)), 'desc': 'OSA Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['mtrs_zp_hrtbt'] = {
        'dev': Bo('%s-MTR_ZP:hrtbt:alive' % (prfx)), 'desc': 'ZPz Motors App'}
    dev_dct['PVS_DONT_RECORD']['HEARTBEATS']['gate_cntr_scan_cfg'] = {
        'dev': Bo('%s-gate_cntr_scan_cfg:hrtbt:alive' % (prfx)), 'desc': 'Gate/Counter scan cfg App'}


def connect_ES_devices(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
    connect EndStation devices
    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''
    # dev_dct['TEMPERATURES'][POS_TYPE_ES]['CCTL1610-I10:temp:fbk'] = BaseDevice('CCTL1610-I10:temp:fbk', desc='Gatan rod temp')
    pass


def connect_BL_devices(dev_dct, prfx='%sBL1610-I10' % DEVPRFX, devcfg=None):
    '''
        Connect beamline devices
    :param dev_dct:
    :param prfx:
    :param devcfg:
    :return:
    '''

    dev_dct['DIO']['InterferShutter'] = PvShutter('%sDIO-2:shutter:ctl' % (prfx))

    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-01:vac:p'] = make_basedevice('PRESSURES',
                                                                            '%sCCG1410-01:vac:p' % (DEVPRFX),
                                                                            desc='Sec. 1', units='torr',
                                                                            devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-I00-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1410-I00-01:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 2',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1410-I00-02:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1410-I00-02:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 4',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-1-I00-02:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sCCG1610-1-I00-02:vac:p' % (
                                                                                      DEVPRFX), desc='Sec. 6',
                                                                                  units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['HCG1610-1-I00-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sHCG1610-1-I00-01:vac:p' % (
                                                                                      DEVPRFX), desc='Sec. 7',
                                                                                  units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-1-I00-03:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sCCG1610-1-I00-03:vac:p' % (
                                                                                      DEVPRFX), desc='Sec. 8',
                                                                                  units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1610-I10-01:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 10',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-03:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1610-I10-03:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 12',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I10-04:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1610-I10-04:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 13',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I12-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1610-I12-01:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 14',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-I12-02:vac:p'] = make_basedevice('PRESSURES',
                                                                                '%sCCG1610-I12-02:vac:p' % (
                                                                                    DEVPRFX), desc='Sec. 15',
                                                                                units='torr', devcfg=devcfg)
    dev_dct['PRESSURES'][POS_TYPE_BL]['CCG1610-3-I12-01:vac:p'] = make_basedevice('PRESSURES',
                                                                                  '%sCCG1610-3-I12-01:vac:p' % (
                                                                                      DEVPRFX), desc='Sec. 16',
                                                                                  units='torr', devcfg=devcfg)

    devcfg.msg_splash("connecting to: [%s]" % 'SRStatus_shutters')
    dev_dct['PVS']['SRStatus_shutters'] = make_basedevice('PVS', '%sSRStatus:shutters' % (DEVPRFX), devcfg=devcfg)

    dev_dct['PVS'][DNM_MONO_EV_FBK] = make_basedevice('PVS', '%sMONO1610-I10-01:energy:fbk' % (DEVPRFX), units='eV',
                                                      devcfg=devcfg)
    _pv = BaseDevice('%sMONO1610-I10-01:grating:select:fbk' % (DEVPRFX))
    _pv.get_position = _pv.get_enum_str_as_int
    dev_dct['PVS']['Mono_grating_fbk'] = _pv

    devcfg.msg_splash("connecting to: [%s]" % 'Epu_pol_fbk')
    dev_dct['PVS']['Epu_pol_fbk'] = Mbbo('%sUND1410-01:polarization' % (DEVPRFX))
    devcfg.msg_splash("connecting to: [%s]" % 'Epu_pol_angle')
    dev_dct['PVS']['Epu_pol_angle'] = make_basedevice('PVS', '%sUND1410-01:polarAngle' % (DEVPRFX), units='udeg',
                                                      devcfg=devcfg)

    devcfg.msg_splash("connecting to: [%s]" % 'Epu_gap_fbk')
    dev_dct['PVS']['Epu_gap_fbk'] = make_basedevice('PVS', '%sUND1410-01:gap:mm:fbk' % (DEVPRFX), units='mm',
                                                    devcfg=devcfg)

    # devcfg.msg_splash("connecting to: [%s]" % 'Epu_gap_fbk')
    # dev_dct['PVS']['Epu_gap_fbk'] = BaseDevice('RUSSTEST:VAL')

    dev_dct['PVS']['Epu_gap_offset'] = make_basedevice('PVS', '%sUND1410-01:gap:offset' % (DEVPRFX), units='mm',
                                                       devcfg=devcfg)
    dev_dct['PVS']['Epu_harmonic'] = make_basedevice('PVS', '%sUND1410-01:harmonic' % (DEVPRFX), devcfg=devcfg)
    dev_dct['PVS']['SYSTEM:mode:fbk'] = Mbbi('%sSYSTEM:mode:fbk' % (DEVPRFX))
    dev_dct['PVS_DONT_RECORD']['ticker'] = make_basedevice('PVS_DONT_RECORD', '%sTRG2400:cycles' % (DEVPRFX),
                                                           units='counts', devcfg=devcfg)


# Feb6	dev_dct['ACTUATORS']['SSH'] = PvValve('SSH1410-I00-01')
# Feb6	dev_dct['ACTUATORS']['PSH'] = PvValve('PSH1410-I00-02')
# Feb6	dev_dct['ACTUATORS']['SM-PSH'] = PvValve('PSH1610-1-I10-01')
# Feb6	dev_dct['ACTUATORS']['BSH'] = PvValve('VVR1610-I12-03')


def print_keys(d):
    if (isinstance(d, list)):
        print_keys(d[0])

    for key in d:
        if (isinstance(d[key], dict)):
            print_keys(d[key])
        else:
            print(key, d[key].is_active())


DEVICE_CFG = None

# ver_str = 'Version %s.%s' % (MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'))
# splash = get_splash(img_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyStxmSplash.png'), ver_str=ver_str)
splash = get_splash(img_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'pyStxmSplash.png'),
                    ver_str='VERSION YABABY')
scanning_mode = appConfig.get_value('MAIN', 'scanning_mode')

sample_mode = None
fine_sample_mode = None

# COARSE_SAMPLEFINE (formerly 'conventional') scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=SAMPLE_FINE
# scanning_mode = COARSE_SAMPLEFINE

# GONI_ZONEPLATE scanning mode = Sample_pos_mode=GONIOMETER, sample_fine_pos_mode=ZONEPLATE
# scanning_mode = GONI_ZONEPLATE

# COARSE_ZONEPLATE scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=ZONEPLATE
# scanning_mode = COARSE_ZONEPLATE

# if (scanning_mode == 'COARSE_SAMPLEFINE'):
# set coarse mode
# MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
sample_mode = sample_positioning_modes.COARSE
# MAIN_OBJ.set_sample_scanning_mode_string('COARSE_SAMPLEFINE Scanning')
# MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.SAMPLEFINE)
fine_sample_mode = sample_fine_positioning_modes.SAMPLEFINE
# else:
#    MAIN_OBJ.set_fine_sample_positioning_mode(sample_fine_positioning_modes.ZONEPLATE)
#    fine_sample_mode = sample_fine_positioning_modes.ZONEPLATE


if ((sample_mode is not None) and (fine_sample_mode is not None)):
    DEVICE_CFG = device_config(splash=splash, sample_pos_mode=sample_mode, fine_sample_pos_mode=fine_sample_mode)
    # MAIN_OBJ.set_devices(DEVICE_CFG)
    bl_config_nm = get_config_name(__file__)
    DEFAULTS = Defaults('%s_stxm_dflts.json' % bl_config_nm, new=False)
else:
    print('NO SAMPLE POSITIONING MODE SELECTED')
    exit()

# DEVICE_CFG.device_report()


if __name__ == '__main__':
    global app
    import sys

    app = QtWidgets.QApplication(sys.argv)

    app.quit()

    print('done')


