

import os
from importlib.machinery import SourceFileLoader
from cls.utils.cfgparser import ConfigClass
from cls.utils.log import get_module_logger


_logger = get_module_logger(__name__)

def load_beamline_device_config(bl_config_nm):
    '''
    walk a directory where the preferences are kept and load the combobox and stacked widget
    :return:
    '''
    cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bl_configs', bl_config_nm)
    if (not os.path.exists(cfgDir)):
        _logger.error('Beamline device Configuration directory [%s] does not exist' % cfgDir)
        exit()

    # get files in cfg dir
    _files = os.listdir(cfgDir)
    if ('loader.py' in _files):
        _filepath = os.path.join(cfgDir, 'loader.py')
        if (os.path.exists(_filepath)):
            # _mod = importlib.load_source('mod_classname', _filepath)
            _mod = SourceFileLoader('mod_classname', _filepath).load_module()
            _mod_filepath = os.path.join(cfgDir, _mod.mod_file)
            # create an instance of the class
            _cls = SourceFileLoader('mod_classname', _mod_filepath).load_module()

    return(_cls.DEVICE_CFG)


def load_beamline_preset(bl_config_nm):
    '''
    walk a directory where the preferences are kept and load the combobox and stacked widget
    :return:
    '''
    dct = None
    cfgDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bl_configs', bl_config_nm)
    if (not os.path.exists(cfgDir)):
        _logger.error('Beamline preset Configuration directory [%s] does not exist' % cfgDir)
        exit()

    # get files in cfg dir
    _files = os.listdir(cfgDir)
    if (('%s.ini' % bl_config_nm) in _files):
        _filepath = os.path.join(cfgDir, '%s.ini' % bl_config_nm)
        if (os.path.exists(_filepath)):
            cfg = ConfigClass(_filepath)
            dct = cfg.get_all()
    return (dct)

if __name__ == '__main__':
    global app
    import sys
    import PyQt5.QtCore as QtCore
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    load_beamline_device_config()

    app.quit()

    print('done')