

from cls.utils.dict_utils import dct_merge
from cls.utils.enum_utils import Enum

dev_types = Enum( 'MTR', 'AI', 'AO')




def get_motor_dct(ext_name, epics_prefix):
    dct = {}
    dct['TYPE'] = dev_types.MTR
    dct['EXT_NAME'] = ext_name
    dct['EPICS_NAME'] = epics_prefix
    dct['VAL'] = '%s.VAL' % epics_prefix
    dct['RBV'] = '%s.RBV' % epics_prefix
    dct['DMOV'] = '%s.DMOV' % epics_prefix
    dct['HLM'] = '%s.HLM' % epics_prefix
    dct['LLM'] = '%s.LLM' % epics_prefix
    return(dct)

def ai_dct(ext_name, epics_prefix):
    dct = {}
    dct['TYPE'] = dev_types.AI
    dct['EXT_NAME'] = ext_name
    dct['EPICS_NAME'] = epics_prefix
    dct['RBV'] = '%s.RBV' % epics_prefix
    return(dct)

def ao_dct(ext_name, epics_prefix):
    dct = {}
    dct['TYPE'] = dev_types.AO
    dct['EXT_NAME'] = ext_name
    dct['EPICS_NAME'] = epics_prefix
    dct['VAL'] = '%s.VAL' % epics_prefix
    return(dct)


def get_epics_name(dct, ext_name):
    return(dct[ext_name]['EPICS_NAME'])

def get_epics_rbv_name(dct, ext_name):
    return(dct[ext_name]['RBV'])


def get_motor(ext_name):
    for mtr_nm in motors:
        if(mtr_nm.find(ext_name) > -1):
            return(motors[mtr_nm])
    return({})

def get_ai(ext_name):
    for ai_nm in ais:
        if(ai_nm.find(ext_name) > -1):
            return(ais[ai_nm])
    return({})


motors = {}
motors['SampleFineX'] = get_motor_dct('sampleFineX','IOC:m900')
motors['SampleFineY'] = get_motor_dct('sampleFineY','IOC:m901')
motors['ZoneplateX'] = get_motor_dct('zoneplateX','IOC:m902')
motors['ZoneplateY'] = get_motor_dct('zoneplateY','IOC:m903')

motors['OSAX'] = get_motor_dct('OSAX','IOC:m904')
motors['OSAY'] = get_motor_dct('OSAY','IOC:m905')
motors['OSAZ'] = get_motor_dct('OSAZ','IOC:m906')

motors['GONIX'] = get_motor_dct('GONIX','IOC:m907')
motors['GONIY'] = get_motor_dct('GONIY','IOC:m908')
motors['GONIZ'] = get_motor_dct('GONIZ','IOC:m909')
motors['GONIT'] = get_motor_dct('GONIT','IOC:m910')

motors['ZPZ'] = get_motor_dct('ZPZ','IOC:m911')

motors['COARSEX'] = get_motor_dct('COARSEX','IOC:m912')
motors['COARSEY'] = get_motor_dct('COARSEY','IOC:m913')

motors['DETX'] = get_motor_dct('DETX','IOC:m914')
motors['DETY'] = get_motor_dct('DETY','IOC:m915')
motors['DETZ'] = get_motor_dct('DETZ','IOC:m916')

motors['SAMPLEX'] = get_motor_dct('SAMPLEX','IOC:m917')
motors['SAMPLEY'] = get_motor_dct('SAMPLEY','IOC:m918')



ais = {}
ais['TM1610-3-I12-01'] = ai_dct('TM1610-3-I12-01', 'TM1610-3-I12-01')
ais['TM1610-3-I12-30'] = ai_dct('TM1610-3-I12-30','TM1610-3-I12-30')
ais['TM1610-3-I12-32'] = ai_dct('TM1610-3-I12-32','TM1610-3-I12-32')
ais['TM1610-3-I12-21'] = ai_dct('TM1610-3-I12-21','TM1610-3-I12-21')
ais['TM1610-3-I12-22'] = ai_dct('TM1610-3-I12-22','TM1610-3-I12-22')
ais['TM1610-3-I12-23'] = ai_dct('TM1610-3-I12-23','TM1610-3-I12-23')
ais['TM1610-3-I12-24'] = ai_dct('TM1610-3-I12-24','TM1610-3-I12-24')


put_devs = {}
put_devs.update(motors)

get_devs = {}
get_devs.update(ais)


all_devs = dct_merge(motors, ais)