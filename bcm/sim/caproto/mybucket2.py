#!/usr/bin/env python3
import os
import numpy as np
from caproto.server import pvproperty, PVGroup, template_arg_parser, run

from cls.utils.dirlist import dirlist
from cls.utils.json_utils import json_to_dict, file_to_json
import json


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

def get_rec_type(_type):
    '''
    class ChannelType(IntEnum):
        STRING = 0
        INT = 1
        FLOAT = 2
        ENUM = 3
        CHAR = 4
        LONG = 5
        DOUBLE = 6

        STS_STRING = 7
        STS_INT = 8
        STS_FLOAT = 9
        STS_ENUM = 10
        STS_CHAR = 11
        STS_LONG = 12
        STS_DOUBLE = 13

        TIME_STRING = 14
        TIME_INT = 15
        TIME_FLOAT = 16
        TIME_ENUM = 17
        TIME_CHAR = 18
        TIME_LONG = 19
        TIME_DOUBLE = 20

        GR_STRING = 21  # not implemented by EPICS
        GR_INT = 22
        GR_FLOAT = 23
        GR_ENUM = 24
        GR_CHAR = 25
        GR_LONG = 26
        GR_DOUBLE = 27

        CTRL_STRING = 28  # not implemented by EPICS
        CTRL_INT = 29
        CTRL_FLOAT = 30
        CTRL_ENUM = 31
        CTRL_CHAR = 32
        CTRL_LONG = 33
        CTRL_DOUBLE = 34

        PUT_ACKT = 35
        PUT_ACKS = 36

        STSACK_STRING = 37
        CLASS_NAME = 38

    :param _type:
    :return:
    '''
    strings = [0, 7, 14, 28]
    ints = [1, 8, 15, 22, 29]
    floats = [2, 9, 16, 23, 30]
    enums = [3, 10, 17, 24, 31]
    chars = [4, 11, 18, 25, 32]
    longs = [5, 12, 19, 26, 33]
    doubles = [6, 13, 20, 27, 34]
    motors = [99]


    if(_type in enums):
        return('bo', int)
    elif(_type in doubles):
        return('ao', float)
    elif (_type in floats):
        return ('ao', float)
    elif(_type in longs):
        return ('ao', int)
    elif (_type in ints):
        return ('ao', int)
    elif (_type in strings):
        return ('stringin', str)
    elif (_type in chars):
        return ('stringin', str)
    elif (_type in motors):
        return ('motor', None)
    else:
        print('what is this type [%s]' %_type)
        return('stringin')



def ingest_pv_dict(inp):
    type_map = {'float': float,'int': int, 'ChannelType.ENUM': int, 'ChannelType.DOUBLE': float ,'ChannelType.LONG': int, 'ChannelType.STRING': str, \
                'ChannelType.CHAR': str, 'ChannelType.FLOAT': float, 'ChannelType.INT': int, 'DoubleMotor': float}

    skip_lst = ['SIM_IOCE712:ddl:1',
                'SIM_IOCE712:ddl:2',
                'SIM_IOCE712:ddl:3',
                'SIM_IOCE712:ddl:4',
                'SIM_IOCE712:ddl:5',
                'SIM_IOCE712:ddl:6',
                'SIM_IOCE712:ddl:7',
                'SIM_IOCE712:ddl:8',
                'SIM_IOCE712:ddl:9',
                'SIM_IOCE712:wg1:npts',
                'SIM_IOCE712:wg1:startmode',
                'SIM_IOCE712:wg1:strtatend',
                'SIM_IOCE712:wg1:useddl',
                'SIM_IOCE712:wg1:usereinit',
                'SIM_IOCE712:wg1_tbl:ids',
                'SIM_IOCE712:wg2:npts',
                'SIM_IOCE712:wg2:startmode',
                'SIM_IOCE712:wg2:strtatend',
                'SIM_IOCE712:wg2:useddl',
                'SIM_IOCE712:wg2:usereinit',
                'SIM_IOCE712:wg2_tbl:ids',
                'SIM_IOCE712:wg4:useddl',
                'SIM_IOCE712:wg4:usereinit',
                'SIM_uhvCI:counter:testwave_RBV',
                'SIM_uhvPMT:ctr:Waveform_RBV',
                'SIM_uhvPMT:ctr:testwave_RBV']
    body = {}
    # for (i, (k, (dtype, rec_type))) in enumerate(inp.items()):
    #     body[str(i)] = pvproperty(name=k,
    #                               dtype=type_map[dtype],
    #                               mock_record=rec_type)
    i = 0
    for k, dct in inp.items():
        if(k in skip_lst):
            continue
        #print('ingesting [%d][%s]' % (i, k))
        if(type(dct) is dict):
            try:
                if (len(dct) == 0):
                    print('This PV [%s] does not have a dict associated with it' % k)
                    continue
                # if('type' not in dct.keys()):
                #     #print('HEY: [%s] seems to not have a [type] field in the dict???' % dct['pvname'])
                #     dct['type'] = 'ChannelType.FLOAT'
                if(k.find('SIM_IOCE712:ddl:1') > -1):
                    print()
                if(dct['count'] > 1):
                    rec_type, data_type = get_rec_type(dct['ftype'])
                    if(rec_type.find('ao') > -1):
                        rec_type = 'aao'
                    dud, data_type = get_rec_type(dct['ftype'])
                else:
                    rec_type, data_type = get_rec_type(dct['ftype'])

                if(type(dct['value']) is str):
                    if(dct['value'].find('array[') > -1):
                        val =  arrstr_to_array(rec_type, dct['value'])
                    else:
                        if(len(dct['value']) > 0):
                            if(is_mtr_str_fld(k)):
                                rec_type = 'stringin'
                                val = dct['value']
                            else:
                                val = data_type(dct['value'])
                        else:
                            val = 0
                else:
                    if(dct['count'] > 1):
                        #its an array
                        val = np.array(dct['value'])

                    else:
                        val = data_type(dct['value'])


                if(k.find('SIM_IOC:m100.DESC') > -1):
                    pass
                if(dct['count'] > 1):
                    body[str(i)] = pvproperty(name=k, dtype=data_type, max_length=dct['count'], value=val)
                else:
                    body[str(i)] = pvproperty(name=k,
                                          dtype=data_type,
                                          mock_record=rec_type,
                                          value=val)

                i += 1
            except TypeError:
                #print('what is this type:' , dct['type'])
                print('there was a problem with this one [%s] the type is weird' % k)


    return type('BucketOPVs', (PVGroup,), body)

def is_mtr_str_fld(k):
    str_flds = ['DESC', 'EGU', 'NAME', 'OUT', 'DINP', 'RDBL', 'STOO']
    for fld in str_flds:
        if (k.find(fld) > -1):
            return(True)

    return(False)


def arrstr_to_array(rec_type, arrstr):
    l = arrstr.replace('array[','')
    l = l.replace('...]', '')
    l_items = l.split(',')
    #if('unknown' in l_items):
    if(type(l_items[0]) is not str):
        pass
    elif (l_items[0].find('unknown') > -1):
        l = [0,0,0,0,0]
    elif(rec_type.find('stringin') > -1):
        l = convert_asciiarr_to_string(l_items)
    elif (rec_type.find('ao') > -1):
        l = convert_asciiarr_to_float(l_items)
    elif (rec_type.find('bo') > -1):
        l = convert_asciiarr_to_int(l_items)

    return(l)

def convert_asciiarr_to_string(ascii_lst):
    '''
    take a list of ascii code chars like ['69', '114', '114', '111', '114'] and returns the string 'Error'
    :param ascii_lst:
    :return:
    '''
    l_int = list(map(int, ascii_lst))
    s = ''.join(chr(i) for i in l_int)
    return(s)

def convert_asciiarr_to_float(ascii_lst):
    '''
    take a list of ascii code chars like ['69', '114', '114', '111', '114'] and returns the string 'Error'
    :param ascii_lst:
    :return:
    '''
    l_float = list(map(float, ascii_lst))
    return(l_float)


def convert_asciiarr_to_int(ascii_lst):
    '''
    take a list of ascii code chars like ['69', '114', '114', '111', '114'] and returns the string 'Error'
    :param ascii_lst:
    :return:
    '''
    l_int = list(map(int, ascii_lst))
    return (l_int)

def load_json_files():
    str_flds = ['DESC', 'EGU', 'NAME', 'OUT']
    none_str_flds = ['DINP', 'RDBL', 'STOO', 'TSEL', 'SDIS', 'PREM', 'POST', 'INIT', 'DOL', 'ASG','RINP','RLNK','PREM']
    #fout = open('initpvs.bat', 'w')
    mtr_dct = get_populated_motor_dict()
    fpath = r'C:\controls\epics\iocapp_pvnames'
    fnames = dirlist(fpath, 'json', remove_suffix=False)
    i = 0
    dct = {}
    for fname in fnames:
        _fpath = os.path.join(fpath, fname)
        f = open(_fpath, 'r')
        js = json.load(f)
        jdct = json_to_dict(js)

        for pv_nm in list(jdct.keys()):
            if (pv_nm in list(mtr_dct.keys())):
                #dct['SIM_' + pv_nm] = jdct[pv_nm]
                #dct['SIM_' + pv_nm]['type'] = 'DoubleMotor'
                dct[pv_nm] = jdct[pv_nm]
                dct[pv_nm]['type'] = 'DoubleMotor'
                for fld in list(mtr_dct[pv_nm].keys()):
                    if(len(fld) > 0):
                        #dct['SIM_' + pv_nm + '.%s' % fld] = {}
                        dct[pv_nm + '.%s' % fld] = {}

                        if (fld in none_str_flds):
                            #dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                            dct[pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                            mtr_dct[pv_nm][fld] = '0'
                        elif(fld in str_flds):
                            #dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                            dct[pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                        else:
                            #dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.FLOAT'
                            dct[pv_nm + '.%s' % fld]['type'] = 'ChannelType.FLOAT'

                        if (mtr_dct[pv_nm][fld] is ''):
                            mtr_dct[pv_nm][fld] = '0'

                        if(fld.find('MSTA') > -1):
                            #force it to be a good status value
                            #dct['SIM_' + pv_nm + '.%s' % fld]['value'] = 18690
                            dct[pv_nm + '.%s' % fld]['value'] = 18690
                        else:
                            #dct['SIM_' + pv_nm + '.%s' % fld]['value'] = mtr_dct[pv_nm][fld]
                            dct[pv_nm + '.%s' % fld]['value'] = mtr_dct[pv_nm][fld]
                        #print('serving MOTOR: [%s], value=[%s]' % ('SIM_' + pv_nm + '.%s' % fld, dct['SIM_' + pv_nm + '.%s' % fld]['value']))
                        print('serving MOTOR: [%s], value=[%s]' % (pv_nm + '.%s' % fld, dct[pv_nm + '.%s' % fld]['value']))
            else:
                dct['SIM_' + pv_nm] = jdct[pv_nm]
                print('serving: %s' % ('SIM_' + pv_nm))

                #fout.write('caput %s %s\n' % ('SIM_' + pv_nm, jdct[pv_nm]['value']))
    #fout.close()
    return(dct)






if __name__ == '__main__':
    parser, split_args = template_arg_parser(
        default_prefix='',
        desc='An IOC that servers a bucket of disconnected PVs.')

    inp = load_json_files()

    # parser.add_argument('--json',
    #                     help='The file to read the PVs from',
    #                     required=True, type=str)
    args = parser.parse_args()
    #args.interfaces = ['127.0.0.1']
    ioc_options, run_options = split_args(args)

    # with open(args.json, 'r') as fin:
    #     inp = json.load(fin)
    klass = ingest_pv_dict(inp)

    ioc = klass(**ioc_options)
    run(ioc.pvdb, **run_options)