
from bcm.devices.device_names import *
from cls.utils.log import get_module_logger, log_to_qt
import numpy as np

_logger = get_module_logger(__name__)

def get_first_entry_key(entries_dct):
	return(list(entries_dct['entries'].keys())[0])

def get_first_sp_db_from_entry(entry_dct):
    sp_id = list(entry_dct['WDG_COM']['SPATIAL_ROIS'].keys())[0]
    sp_db = entry_dct['WDG_COM']['SPATIAL_ROIS'][sp_id]
    return(sp_db)

def get_first_sp_db_from_wdg_com(wdg_com):
    sp_id = list(wdg_com['SPATIAL_ROIS'].keys())[0]
    sp_db = wdg_com['SPATIAL_ROIS'][sp_id]
    return (sp_db)


def get_axis_setpoints_from_sp_db(sp_db, axis='X'):
    if(axis in list(sp_db.keys())):
        data = sp_db[axis][SETPOINTS]
    else:
        data = None
    return(data)

def get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    '''
    return 3D generic scan data as 1D list
    :param entry_dct:
    :param counter:
    :return:
    '''
    datas = [entry_dct['data'][counter]['signal'][0][0]]
    return(datas)

def get_point_spec_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    data = entry_dct['data'][counter]['signal']
    return(data)

def get_point_spec_energy_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    data = entry_dct['data'][counter]['energy']['signal']
    return(data)


def test_eq(a, b):
    if (a == b):
        return (True)
    else:
        return (False)


def check_roi_for_match(a_roi, b_roi, skip_list=[], verbose=False):
    '''
    compare 2 roi dicts and report any differences
    :param a_roi:
    :param b_roi:
    :return:
    '''
    res = True
    a_keys = list(a_roi.keys())
    for fld in a_keys:
        if(fld in skip_list):
            continue
        if(isinstance(a_roi[fld], np.ndarray)):
            res = np.array_equal(a_roi[fld], b_roi[fld])
            if(not res):
                _logger.error('check_roi_for_match: [%s] doesnt match' % fld)

        elif (not (a_roi[fld] == b_roi[fld]) ):
            _logger.error('check_roi_for_match: [%s] doesnt match' % fld)
            res = False
        else:
            if (verbose):
                _logger.info('check_roi_for_match: [%s] matches' % fld)
            pass

    return(res)