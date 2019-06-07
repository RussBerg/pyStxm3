#!/usr/bin/env python
"""
 This module provides support for the EPICS motor record.
"""
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal

class Motor_Qt(QObject):
    """ just a convienience class so that PVs can be configured in the beamline configuration file
    and used as if they were other devices, making the rest of the code cleaner
    """
    changed = pyqtSignal(object)

    _extras = {
        'disabled': '_able.VAL',
        'calibPosn': ':calibPosn'}

    _alias = {
        'acceleration': 'ACCL',
        #'back_accel': 'BACC',
        #'backlash': 'BDST',
        #'back_speed': 'BVEL',
        #'card': 'CARD',
        #'dial_high_limit': 'DHLM',
        #'direction': 'DIR',
        #'dial_low_limit': 'DLLM',
        #'settle_time': 'DLY',
        'done_moving': 'DMOV',
        #'dial_readback': 'DRBV',
        'description': 'DESC',
        #'dial_drive': 'DVAL',
        'units': 'EGU',
        #'encoder_step': 'ERES',
        #'freeze_offset': 'FOFF',
        #'move_fraction': 'FRAC',
        #'hi_severity': 'HHSV',
        #'hi_alarm': 'HIGH',
        #'hihi_alarm': 'HIHI',
        'high_limit': 'HLM',
        #'high_limit_set': 'HLS',
        #'hw_limit': 'HLSV',
        #'home_forward': 'HOMF',
        #'home_reverse': 'HOMR',
        #'high_op_range': 'HOPR',
        #'high_severity': 'HSV',
        #'integral_gain': 'ICOF',
        #'jog_accel': 'JAR',
        #'jog_forward': 'JOGF',
        #'jog_reverse': 'JOGR',
        #'jog_speed': 'JVEL',
        #'last_dial_val': 'LDVL',
        'low_limit': 'LLM',
        #'low_limit_set': 'LLS',
        #'lo_severity': 'LLSV',
        #'lolo_alarm': 'LOLO',
        #'low_op_range': 'LOPR',
        #'low_alarm': 'LOW',
        #'last_rel_val': 'LRLV',
        #'last_dial_drive': 'LRVL',
        #'last_SPMG': 'LSPG',
        #'low_severity': 'LSV',
        #'last_drive': 'LVAL',
        'soft_limit': 'LVIO',
        #'in_progress': 'MIP',
        #'missed': 'MISS',
        'moving': 'MOVN',
        #'resolution': 'MRES',
        'motor_status': 'MSTA',
        #'offset': 'OFF',
        #'output_mode': 'OMSL',
        #'output': 'OUT',
        #'prop_gain': 'PCOF',
        #'precision': 'PREC',
        'readback': 'RBV',
        #'retry_max': 'RTRY',
        #'retry_count': 'RCNT',
        #'retry_deadband': 'RDBD',
        #'dial_difference': 'RDIF',
        #'raw_encoder_pos': 'REP',
        #'raw_high_limit': 'RHLS',
        #'raw_low_limit': 'RLLS',
        #'relative_value': 'RLV',
        #'raw_motor_pos': 'RMP',
        #'raw_readback': 'RRBV',
        #'readback_res': 'RRES',
        'raw_drive': 'RVAL',
        #'dial_speed': 'RVEL',
        #'s_speed': 'S',
        #'s_back_speed': 'SBAK',
        #'s_base_speed': 'SBAS',
        #'s_max_speed': 'SMAX',
        #'set': 'SET',
        'stop_go': 'SPMG',
        #'s_revolutions': 'SREV',
        'stop_command': 'STOP',
        #'t_direction': 'TDIR',
        #'tweak_forward': 'TWF',
        #'tweak_reverse': 'TWR',
        #'tweak_val': 'TWV',
        #'use_encoder': 'UEIP',
        #'u_revolutions': 'UREV',
        #'use_rdbl': 'URIP',
        'setpoint': 'VAL',
        #'base_speed': 'VBAS',
        'velocity': 'VELO',
        #'version': 'VERS',
        'max_speed': 'VMAX',
        #'use_home': 'ATHM',
        #'deriv_gain': 'DCOF',
        'use_torque': 'CNEN',
        #'device_type': 'DTYP',
        #'record_type': 'RTYP',
        'status': 'STAT'}

    _init_list = ('DMOV', 'VAL', 'DESC', 'RTYP', 'RBV', 'PREC', 'TWV', 'FOFF', 'EGU')
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_init_list',
               '_alias', '_extras', '_pos_set', '_collision_support')

    #def __init__(self, pv_name=None, desc=None, egu='', cb=None, **cb_kwargs):
    def __init__(self, name=None, timeout = 3.0, pos_set = 'endstation', collision_support = False):
        '''
                        prefix is the low level control system name for this bi device
                        to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
        return the low level control system name for this bi device
        to be implemented by inheriting class'''
        pass

    def add_pv(self, pvname, attr=None, **kw):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def add_callback(self, attr, func, **kwargs):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def _on_pv_changed(self, **kwargs):
        '''
        ALWAYS return 'value' plus whatever kwargs the user passed in
        :param kwargs:
        :return:
        '''
        # dct = {}
        # #'value' must be a part of default kwargs
        # if(len(self.cb_args) == 0):
        #     #only return the value by itself
        #     self._new_data.emit(kwargs['value'])
        # else:
        #     #else return a dict of value plus cb_args
        #     dct['value'] = kwargs['value']
        #     for k in self.cb_args:
        #         dct[k] = kwargs[k]
        #     #emit the changed signal
        #     self._new_data.emit(dct)
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def get_desc(self):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def get_egu(self):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        pass

    def get_position(self):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def count(self, val):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def get(self, attr=None):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def put(self, attr, val, wait=1.0, timeout=5.0):
        '''
                return the low level control system name for this device
                to be implemented by inheriting class'''
        pass

    def set_calibrated_position(self, pos):
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass
        # self.put('calibPosn', pos)



    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass
        # for field, msg in (('LVIO', 'Soft limit violation'),
        #                    ('HLS', 'High hard limit violation'),
        #                    ('LLS', 'Low  hard limit violation')):
        #     if self.get(field) != 0:
        #         raise MotorLimitException(msg)
        # return

    def within_limits(self, val):
        """ returns whether a value for a motor is within drive limits
        with dial=True   dial limits are used (default is user limits)"""
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass

    def move(self, val=None, relative=False, wait=False, timeout=300.0,
             dial=False, step=False, raw=False,
             ignore_limits=False, confirm_move=False):
        """ moves motor drive to position

        arguments:
        ==========
         val            value to move to (float) [Must be provided]
         relative       move relative to current position    (T/F) [F]
         wait           whether to wait for move to complete (T/F) [F]
         dial           use dial coordinates                 (T/F) [F]
         raw            use raw coordinates                  (T/F) [F]
         step           use raw coordinates (backward compat)(T/F) [F]
         ignore_limits  try move without regard to limits    (T/F) [F]
         confirm_move   try to confirm that move has begun   (T/F) [F]
         timeout        max time for move to complete (in seconds) [300]

        return values:
          -13 : invalid value (cannot convert to float).  Move not attempted.
          -12 : target value outside soft limits.         Move not attempted.
          -11 : drive PV is not connected:                Move not attempted.
           -8 : move started, but timed-out.
           -7 : move started, timed-out, but appears done.
           -5 : move started, unexpected return value from PV.put()
           -4 : move-with-wait finished, soft limit violation seen
           -3 : move-with-wait finished, hard limit violation seen
            0 : move-with-wait finish OK.
            0 : move-without-wait executed, not cpmfirmed
            1 : move-without-wait executed, move confirmed
            3 : move-without-wait finished, hard limit violation seen
            4 : move-without-wait finished, soft limit violation seen

        """
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass

    def get_low_limit(self):
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass

    def get_high_limit(self):
        '''
                        return the low level control system name for this device
                        to be implemented by inheriting class'''
        pass

class MotorLimitException(Exception):
    """ raised to indicate a motor limit has been reached """

    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class MotorException(Exception):
    """ raised to indicate a problem with a motor"""

    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg

    def __str__(self):
        return str(self.msg)


