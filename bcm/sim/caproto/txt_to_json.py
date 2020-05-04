
import os
import time
from cls.utils.dirlist import dirlist
from cls.utils.json_utils import dict_to_json, json_to_file
from epics import PV

def rd_txt_gen_json_files():

    # 'IOC:m118_able.VAL': {'pvname': 'IOC:m118_able.VAL',
    #                       'value': 0,
    #                       'char_value': '0',
    #                       'status': 0,
    #                       'ftype': 17,
    #                       'chid': c_longlong(1962002854920),
    #                       'host': 'IOC1610-303.clsi.ca:5064',
    #                       'count': 1,
    #                       'access': 'read/write',
    #                       'write_access': True,
    #                       'read_access': True,
    #                       'severity': 0,
    #                       'timestamp': 1583512435.066766,
    #                       'posixseconds': 1583512435.0,
    #                       'nanoseconds': 66766756,
    #                       'precision': None,
    #                       'units': None,
    #                       'enum_strs': ('Enable', 'Disable'),
    #                       'upper_disp_limit': None,
    #                       'lower_disp_limit': None,
    #                       'upper_alarm_limit': None,
    #                       'lower_alarm_limit': None,
    #                       'lower_warning_limit': None,
    #                       'upper_warning_limit': None,
    #                       'upper_ctrl_limit': None,
    #                       'lower_ctrl_limit': None}}

    str_flds = ['DESC', 'EGU', 'NAME', 'OUT']
    none_str_flds = ['DINP', 'RDBL', 'STOO', 'TSEL', 'SDIS', 'PREM', 'POST', 'INIT', 'DOL', 'ASG', 'RINP', 'RLNK',
                     'PREM']
    # fout = open('initpvs.bat', 'w')
    fpath = r'C:\controls\epics\iocapp_pvnames'
    fnames = dirlist(fpath, 'txt', remove_suffix=False)
    i = 0
    fdct = {}
    for fname in fnames:
        print('processing [%s]' % fname)
        _fpath = os.path.join(fpath, fname)
        f = open(_fpath, 'r')
        fdct[fname] = {}
        lines = f.readlines()
        for pvname in lines:
            pvname = pvname.strip()
            if(len(pvname) < 5):
                continue
            if (pvname.find('#') > -1):
                continue
            print('\tpulling fields for [%s]' % pvname)
            fdct[fname][pvname] = {}
            p = PV(pvname)
            time.sleep(0.05)
            if(p.connected):
                for f in p._fields:
                    #if(type(p.value) is not dbr.c_ubyte_Array_1):
                    _value = str(p.value)
                    if(_value.find('c_ubyte_Array') == -1):
                        fdct[fname][pvname][f] = getattr(p, f)
                p.disconnect()
                del(p)
            else:
                print('\t\t ################## looks like [%s] does not exist on the network ###########' % pvname)
        js = dict_to_json(fdct[fname])
        json_to_file(_fpath + '.json', js)
        print('Saving json file [%s]' % (_fpath + '.json'))



if __name__ == '__main__':
    rd_txt_gen_json_files()
