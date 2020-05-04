'''
Created on May 16, 2019

@author: bergr
'''

# BCM GLOBAL Settings for stxm
import os

import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets

from cls.appWidgets.main_object import main_object_base
from cls.appWidgets.splashScreen import get_splash
from cls.app_data.defaults import Defaults
from cls.applications.pyStxm import abs_path_to_ini_file
from cls.types.beamline import BEAMLINE_IDS
from cls.types.stxmTypes import sample_positioning_modes, sample_fine_positioning_modes
from cls.utils.cfgparser import ConfigClass
from cls.utils.log import get_module_logger
from cls.applications.pyStxm.bl_config_loader import load_beamline_device_config
# from twisted.python.components import globalRegistry
_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)

#when simulating un comment the next line
DEVPRFX = 'SIM_'
#and comment this one
#DEVPRFX = ''

# #Feb6	dev_dct['ACTUATORS']['SSH'] = PvValve('SSH1410-I00-01')
# #Feb6	dev_dct['ACTUATORS']['PSH'] = PvValve('PSH1410-I00-02')
# #Feb6	dev_dct['ACTUATORS']['SM-PSH'] = PvValve('PSH1610-1-I10-01')
# #Feb6	dev_dct['ACTUATORS']['BSH'] = PvValve('VVR1610-I12-03')
# def print_keys(d):
#     if(isinstance(d, list)):
#         print_keys(d[0])
#
#     for key in d:
#         if(isinstance(d[key], dict)):
#             print_keys(d[key])
#         else:
#             print(key, d[key].is_active())

MAIN_OBJ = None
DEVICE_CFG = None


MAIN_OBJ = main_object_base('CLS SM 10ID1','UHV STXM', BEAMLINE_IDS.STXM)
#MAIN_OBJ.set_sample_positioning_mode(sample_positioning_modes.COARSE)
MAIN_OBJ.set_datafile_prefix('C')
MAIN_OBJ.set_thumbfile_suffix('jpg')
MAIN_OBJ.set_endstation_prefix('uhv')
ver_str = 'Version %s.%s' % (MAIN_OBJ.get('APP.MAJOR_VER'), MAIN_OBJ.get('APP.MINOR_VER'))
splash = get_splash(img_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyStxmSplash.png'),
                    ver_str=ver_str)

#get teh current scanning mode from teh app.ini configuration
scanning_mode = appConfig.get_value('DEFAULT', 'scanning_mode')
sample_mode = None
fine_sample_mode = None
bl_config_nm = appConfig.get_value('DEFAULT', 'bl_config')

# COARSE_SAMPLEFINE (formerly 'conventional') scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=SAMPLE_FINE
# GONI_ZONEPLATE scanning mode = Sample_pos_mode=GONIOMETER, sample_fine_pos_mode=ZONEPLATE
# COARSE_ZONEPLATE scanning mode = Sample_pos_mode=COARSE, sample_fine_pos_mode=ZONEPLATE

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

# DEVICE CONECTION
if ((sample_mode is not None) and (fine_sample_mode is not None)):
    # connect to all teh devices for the desired beamline configuration
    DEVICE_CFG = load_beamline_device_config(bl_config_nm)
    MAIN_OBJ.set_devices(DEVICE_CFG)
    DEFAULTS = Defaults('uhvstxm_dflts.json', new=False)
else:
    print('NO SAMPLE POSITIONING MODE SELECTED')
    exit()

#DEVICE_CFG.device_report()

# class cfgReader(QtCore.QObject):
#     new_message = QtCore.pyqtSignal(object)
#
#     def __init__(self):
#         super(cfgReader, self).__init__()
#     #globalRegistry.register([], IBeamline, '', self)
#
#     def read_devices(self):
#         devcfg = dev_config()
#         DEVICES = devcfg.get_devices()
#         for dev in list(DEVICES.keys()):
#             (hlth,hstr) = DEVICES[dev].state_info['health']
#             if(hlth):
#                 conStr = 'GOOD'
#             else:
#                 conStr = 'NOT_GOOD'
#             s = 'Connection to : [%s] is %s' % (dev, conStr)
#             self.new_message.emit(s)


if __name__ == '__main__':
    global app
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # def on_dev_status(msg):
    #     print(msg)
    #
    # cfgRdr = cfgReader()
    # cfgRdr.new_message.connect(on_dev_status)
    # cfgRdr.read_devices()
    load_beamline_device_config()


    app.quit()

    print('done')
	

