import copy
import os
from cls.utils.dirlist import dirlist
from cls.utils.json_utils import dict_to_json, json_to_dict, json_to_file, file_to_json


def get_populated_motor_dict(field_path=None):
    '''
    return a dict from disk of the populated fields for all motors
    :param field_path:
    :return:
    '''
    if(field_path is None):
        field_path = r'C:\controls\epics\iocapp_pvnames\rec_fields'

    fpath = os.path.join(field_path, 'motors.json')
    js = file_to_json(fpath)
    dct = json_to_dict(js)
    return(dct)

def get_pv_db_lst():
    mtr_dct = get_populated_motor_dict()

    pvdb_list = []
    pvdb_dct = {}
    fpath = r'C:\controls\epics\iocapp_pvnames'
    fnames = dirlist(fpath, 'txt', remove_suffix=False)
    for fname in fnames:
        f = open(os.path.join(fpath, fname), 'r')
        pvnames = f.readlines()
        for pv_nm in pvnames:
            pv_nm = pv_nm.replace('\n', '')
            dct = {}
            if (pv_nm in list(mtr_dct.keys())):
                ('%s = pvproperty(value=1.0, mock_record=\'motor\')' % pv_nm)
                # for field, val in mtr_dct[pv_nm].items():
                #
                #     if (len(field) > 0):
                #         if (type(val) is float):
                #             #bf = get_base_fields(_type='float', val=val)
                #             print('%s = pvproperty(value=1.0, mock_record=\'ai\')' % pv_nm)
                #         elif (type(val) is int):
                #             #bf = get_base_fields(_type='int', val=val)
                #             print('%s = pvproperty(value=1.0, mock_record=\'ai\')' % pv_nm)
                #         elif (type(val) is str):
                #             #bf = get_base_fields(_type='char', val=val)
                #             print('%s = pvproperty(value=1.0, mock_record=\'stringin\')' % pv_nm)
                #             #bf['count'] = len(val)
                #             #bf['scan'] = 0
                #         else:
                #             print('cant determine type for [%s]' % pv_nm)
                #             continue
                #         dct = {}
                #         #dct['%s.%s' % (pv_nm, field)] = bf
                #         # print(dct)
                #         #pvdb_list.append(dct)
                #         #pvdb_dct['%s.%s' % (pv_nm, field)] = bf
            else:
                #dct[pv_nm] = copy.copy(base_fields)
                print('%s = pvproperty(value=1.0, mock_record=\'ai\')' % pv_nm)
            pvdb_list.append(dct)
            pvdb_dct[pv_nm] = dct
        f.close()
    return(pvdb_list, pvdb_dct)

if __name__ == '__main__':

    # !/usr/bin/env python
    # this creates an epics app serving the pv GILLIAN:RAND

    prefix = 'SIM_'

    #pvdb = convert_dbpr_str_to_pvdb(s, 'counter:Waveform_RBV')
    #print(pvdb_list)
    #{'RAND': {'type': 'float', 'count': 1, 'enums': [], 'states': [], 'prec': 0, 'unit': '', 'lolim': 0, 'hilim': 0, 'low': 0, 'high': 0, 'lolo': 0, 'hihi': 0, 'adel': 0, 'mdel': 0, 'scan': 0, 'asyn': False, 'asg': '', 'value': 2.3456}}

    pvdb_lst, pvdb_dct = get_pv_db_lst()