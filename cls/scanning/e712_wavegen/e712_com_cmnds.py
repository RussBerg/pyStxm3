


"""
with this module the goal is not to implement EVERY connection to the E712 only the really time consuming things
 like retrieving waveform data, currently the data recorder data ius not supported but it could be in the future,
 for that changes will be needed at teh driver level
"""
from cls.utils.enum_utils import Enum

e712_cmds = Enum('EXIT', 'GET_WAV_DATA', 'GET_ALL_WAV_DATA', 'GET_DDL_DATA', 'GET_TRIG_DATA', 'SEND_COMMANDS')


#def make_base_e712_com_dict(cmnd, arg, data, x_roi, y_roi, dwell, cb=None):
def make_base_e712_com_dict(cmnd, arg, data, cb=None):
    dct = {}
    dct['cmnd'] = cmnd
    dct['data'] = data
    dct['arg'] = arg
    dct['cb'] = cb

    #dct['x_roi'] = x_roi
    #dct['y_roi'] = y_roi
    #dct['dwell'] = dwell

    return(dct)


