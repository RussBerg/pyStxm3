#!/usr/bin/env python3
import os
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
    if(_type.find('ChannelType.ENUM') > -1):
        return('bo')
    elif(_type.find('ChannelType.DOUBLE') > -1):
        return('ao')
    elif (_type.find('ChannelType.FLOAT') > -1):
        return ('ao')
    elif(_type.find('ChannelType.LONG') > -1):
        return ('ao')
    elif (_type.find('ChannelType.INT') > -1):
        return ('ao')
    elif (_type.find('ChannelType.STRING') > -1):
        return ('stringin')
    elif (_type.find('ChannelType.CHAR') > -1):
        return ('stringin')
    elif (_type.find('DoubleMotor') > -1):
        return ('motor')
    else:
        print('what is this type [%s]' %_type)
        return('stringin')



def ingest_pv_dict(inp):
    type_map = {'float': float,'int': int, 'ChannelType.ENUM': int, 'ChannelType.DOUBLE': float ,'ChannelType.LONG': int, 'ChannelType.STRING': str, \
                'ChannelType.CHAR': str, 'ChannelType.FLOAT': float, 'ChannelType.INT': int, 'DoubleMotor': float}

    body = {}
    # for (i, (k, (dtype, rec_type))) in enumerate(inp.items()):
    #     body[str(i)] = pvproperty(name=k,
    #                               dtype=type_map[dtype],
    #                               mock_record=rec_type)
    i = 0
    for k, dct in inp.items():
        #print('ingesting [%d][%s]' % (i, k))
        if(type(dct) is dict):
            try:
                rec_type = get_rec_type(dct['type'])
                if(type(dct['value']) is str):
                    if(dct['value'].find('array[') > -1):
                        val =  arrstr_to_array(rec_type, dct['value'])
                    else:
                        if(len(dct['value']) > 0):
                            if(is_mtr_str_fld(k)):
                                rec_type = 'stringin'
                                val = dct['value']
                            else:
                                val = type_map[dct['type']](dct['value'])
                        else:
                            val = 0
                else:
                    val = type_map[dct['type']](dct['value'])


                if(k.find('SIM_IOC:m100.DESC') > -1):
                    pass
                body[str(i)] = pvproperty(name=k,
                                          dtype=type_map[dct['type']],
                                          mock_record=rec_type,
                                          value=val)
                i += 1
            except TypeError:
                print('what is this type:' , dct['type'])


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
        for fname in list(jdct.keys()):
            for pv_nm in list(jdct[fname].keys()):
                if (pv_nm in list(mtr_dct.keys())):
                    dct['SIM_' + pv_nm] = jdct[fname][pv_nm]
                    dct['SIM_' + pv_nm]['type'] = 'DoubleMotor'
                    for fld in list(mtr_dct[pv_nm].keys()):
                        if(len(fld) > 0):
                            dct['SIM_' + pv_nm + '.%s' % fld] = {}

                            if (fld in none_str_flds):
                                dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                                mtr_dct[pv_nm][fld] = '0'
                            elif(fld in str_flds):
                                dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.STRING'
                            else:
                                dct['SIM_' + pv_nm + '.%s' % fld]['type'] = 'ChannelType.FLOAT'

                            if (mtr_dct[pv_nm][fld] is ''):
                                mtr_dct[pv_nm][fld] = '0'

                            if(fld.find('MSTA') > -1):
                                #force it to be a good status value
                                dct['SIM_' + pv_nm + '.%s' % fld]['value'] = 18690
                            else:
                                dct['SIM_' + pv_nm + '.%s' % fld]['value'] = mtr_dct[pv_nm][fld]
                            print('serving MOTOR: [%s], value=[%s]' % ('SIM_' + pv_nm + '.%s' % fld, dct['SIM_' + pv_nm + '.%s' % fld]['value']))
                else:
                    dct['SIM_' + pv_nm] = jdct[fname][pv_nm]

                #fout.write('caput %s %s\n' % ('SIM_' + pv_nm, jdct[fname][pv_nm]['value']))
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