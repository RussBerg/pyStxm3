#!/usr/bin/env python
"""
 This module provides support for the EPICS motor record.
"""
import os
import time
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal

from .aio import aio
from cls.utils.dict_utils import dct_get, dct_put

WAIT_SLEEP = 0.002
START_TIMEOUT = 20
MOVE_TIMEOUT = 900000

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
        'dial_drive': 'DVAL',
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
        'set': 'SET',
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
        super(Motor_Qt, self).__init__()
        if name is None:
            raise MotorException("must supply motor name")

        self._name = name

        if name.endswith('.VAL'):
            name = name[:-4]
        if name.endswith('.'):
            name = name[:-1]

        self._prefix = name
        self._pos_set = pos_set
        self._collision_support = collision_support

        self.ctrl_vars = {}
        self.desc = ''
        self.egu = ''
        self._pvs = {}

        for key, val in list(self._alias.items()):
            pvname = "%s.%s" % (name, val)
            self.add_pv(pvname, attr=key)

        for key, val in list(self._extras.items()):
            pvname = "%s%s" % (name, val)
            self.add_pv(pvname, attr=key)

        if (collision_support):
            # the setpoint for this motor is the A field of a transform record :check_tr.A
            pvname = "%s:check_tr.A" % (name)
            self.add_pv(pvname, attr='check_tr.A')

        # if (pv_name is not None):
        #     self.pv = aio(pv_name)
        #     # self.changed.connect(self.count)
        #     # self.pv.changed.connect(self.count)
        #     self.connected = self.pv.connected
        #     #self.add_callback = self.pv.add_callback
        #     if(cb is None):
        #         #setup default callback for changed
        #         self.pv.add_callback(self._on_pv_changed, **cb_kwargs)
        #     else:
        #         #the user wants to override the default and setup their own handler for 'changed' signal
        #         self.pv.add_callback(cb, **cb_kwargs)
        #     self._new_data.connect(self.count)

    def add_pv(self, pvname, attr=None, **kw):
        if attr is None:
            attr = pvname
        self._pvs[attr] = aio(pvname, **kw)
        return self._pvs[attr]

    def add_callback(self, attr, func, **kwargs):
        self._pvs[attr].add_callback(func, **kwargs)

    def _on_pv_changed(self, **kwargs):
        '''
        ALWAYS return 'value' plus whatever kwargs the user passed in
        :param kwargs:
        :return:
        '''
        dct = {}
        #'value' must be a part of default kwargs
        if(len(self.cb_args) == 0):
            #only return the value by itself
            self._new_data.emit(kwargs['value'])
        else:
            #else return a dict of value plus cb_args
            dct['value'] = kwargs['value']
            for k in self.cb_args:
                dct[k] = kwargs[k]
            #emit the changed signal
            self._new_data.emit(dct)

    def get_desc(self):
        return(self._pvs['description'].get())

    def get_egu(self):
        return(self._pvs['units'].get())

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'name', self.name)
        return (dct)

    def get_name(self):
        return (self._name)

    def get_position(self):
        return (self._pvs['readback'].get())

    def count(self, val):
        #print 'count called', val
        self.changed.emit(val)
        return (val)

    def get(self, attr=None):
        if(attr is None):
            return(self._pvs['readback'].get())
        else:
            return(self._pvs[attr].get())

    def put(self, attr, val, wait=1.0, timeout=5.0):
        self._pvs[attr].put(val)

    def set_calibrated_position(self, pos):
        self.put('calibPosn', pos)

    def set_position(self, position, dial=False, step=False, raw=False):
        """
      Sets the motor position in user, dial or step coordinates.

      Inputs:
         position:
            The new motor position

      Keywords:
         dial:
            Set dial=True to set the position in dial coordinates.
            The default is user coordinates.

         raw:
            Set raw=True to set the position in raw steps.
            The default is user coordinates.

      Notes:
         The 'raw' and 'dial' keywords are mutually exclusive.

      Examples:
         m=epicsMotor('13BMD:m38')
         m.set_position(10, dial=True)   # Set the motor position to 10 in
                                      # dial coordinates
         m.set_position(1000, raw=True) # Set the motor position to 1000 steps
         """

        # Put the motor in "SET" mode
        self.put('set', 1)
        self.put('setpoint', position)
        # Put the motor back in "Use" mode
        self.put('set', 0)

    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        for field, msg in (('LVIO', 'Soft limit violation'),
                           ('HLS', 'High hard limit violation'),
                           ('LLS', 'Low  hard limit violation')):
            if self.get(field) != 0:
                raise MotorLimitException(msg)
        return

    def within_limits(self, val):
        """ returns whether a value for a motor is within drive limits
        with dial=True   dial limits are used (default is user limits)"""
        ll_name, hl_name = 'low_limit', 'high_limit'
        return (val <= self.get(hl_name) and val >= self.get(ll_name))

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
        step = step or raw

        NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
        TIMEOUT, TIMEOUT_BUTDONE = -8, -7
        UNKNOWN_ERROR = -5
        DONEW_SOFTLIM, DONEW_HARDLIM = -4, -3
        DONE_OK = 0
        MOVE_BEGUN, MOVE_BEGUN_CONFIRMED = 0, 1
        NOWAIT_SOFTLIM, NOWAIT_HARDLIM = 4, 3
        try:
            val = float(val)
        except TypeError:
            return NONFLOAT

        drv, rbv = ('setpoint', 'readback')

        if relative:
            val += self.get(drv)

        # Check for limit violations
        if not ignore_limits and not step:
            if not self.within_limits(val):
                return OUTSIDE_LIMITS

        if (self._collision_support):
            stat = self.put('check_tr.A', val, wait=wait, timeout=timeout)
        else:
            stat = self.put(drv, val, wait=wait, timeout=timeout)

        if stat is None:
            return UNCONNECTED

        if wait and stat == -1:  # move started, exceeded timeout
            if self.get('done_moving') == 0:
                return TIMEOUT
            return TIMEOUT_BUTDONE
        if 1 == stat:
            if wait:  # ... and finished OK
                if 1 == self.get('soft_limit'):
                    return DONEW_SOFTLIM
                elif 1 == self.get('high_limit_set') or 1 == self.get('low_limit_set'):
                    return DONEW_HARDLIM
                return DONE_OK
            else:
                if 1 == self.get('soft_limit') or confirm_move:
                    ca.poll(evt=1.e-2)
                moving = False
                if confirm_move:
                    t0 = time.time()
                    while self.get('moving') == 0:
                        ca.poll(evt=1.e-3)
                        if time.time() - t0 > 0.25: break
                if 1 == self.get('moving'):
                    return MOVE_BEGUN_CONFIRMED
                elif 1 == self.get('soft_limit'):
                    return NOWAIT_SOFTLIM
                elif 1 == self.get('high_limit_set') or 1 == self.get('low_limit_set'):
                    return NOWAIT_HARDLIM
                else:
                    return MOVE_BEGUN
        return UNKNOWN_ERROR

    def confirm_stopped(self):
        t = 0
        done = False
        while((not done) and (t < START_TIMEOUT) ):
            time.sleep(WAIT_SLEEP)
            QtWidgets.QApplication.processEvents()
            t += 1
            if self.get('done_moving') == 0:
                done = True
        #if(t >= START_TIMEOUT):
        #    print 'Timed out waiting to START'
        #print 'move started'
        t = 0
        done = False
        while((not done) and (t < MOVE_TIMEOUT) ):
            time.sleep(WAIT_SLEEP)
            QtWidgets.QApplication.processEvents()
            t += 1
            if self.get('done_moving') == 1:
                done = True
        if(t >= MOVE_TIMEOUT):
            print('Timed out waiting to STOP')

    def move_and_zero(self, pos):
        self.move(pos)
        # print 'waiting for %s to stop' % self._prefix
        self.confirm_stopped()
        # print '%s has now stopped' % self._prefix
        self.set_position(0.0)
        # print '%s setting zero' % self._prefix

    def wait_for_stopped_and_zero(self):
        # print 'waiting for %s to stop' % self._prefix
        self.confirm_stopped()
        # print '%s has now stopped' % self._prefix
        self.set_position(0.0)
        # print '%s setting zero' % self._prefix

    def move_and_set_position(self, pos, setpos):
        self.move(pos)
        # print 'waiting for %s to stop' % self._prefix
        self.confirm_stopped()
        # print '%s has now stopped' % self._prefix
        self.set_position(setpos)
        # print '%s setting zero' % self._prefix


    def get_low_limit(self):
        i = 0
        while ((len(self.ctrl_vars) == 0) and (i < 50)):
            self.ctrl_vars = self.pv.get_ctrlvars()
            i += 1
            time.sleep(0.001)
        if ('lower_ctrl_limit' in list(self.ctrl_vars.keys())):
            return (self.ctrl_vars['lower_ctrl_limit'])
        else:
            return (None)

    def get_high_limit(self):
        i = 0
        while ((len(self.ctrl_vars) == 0) and (i < 50)):
            self.ctrl_vars = self.pv.get_ctrlvars()
            i += 1
            time.sleep(0.001)

        if ('upper_ctrl_limit' in list(self.ctrl_vars.keys())):
            return (self.ctrl_vars['upper_ctrl_limit'])
        else:
            return (None)


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


# class Motor_Qt(QtCore.QObject):
#     """Epics Motor Class for pyepics3
#
#    This module provides a class library for the EPICS motor record.
#
#    It uses the epics.Device and epics.PV classese
#
#    Virtual attributes:
#       These attributes do not appear in the dictionary for this class, but
#       are implemented with the __getattr__ and __setattr__ methods.  They
#       simply get or putthe appropriate motor record fields.  All attributes
#       can be both read and written unless otherwise noted.
#
#       Attribute        Description                  Field
#       ---------        -----------------------      -----
#       drive            Motor Drive Value            .VAL
#       readback         Motor Readback Value         .RBV    (read-only)
#       slew_speed       Slew speed or velocity       .VELO
#       base_speed       Base or starting speed       .VBAS
#       acceleration     Acceleration time (sec)      .ACCL
#       description      Description of motor         .DESC
#       resolution       Resolution (units/step)      .MRES
#       high_limit       High soft limit (user)       .HLM
#       low_limit        Low soft limit (user)        .LLM
#       dial_high_limit  High soft limit (dial)       .DHLM
#       dial_low_limit   Low soft limit (dial)        .DLLM
#       backlash         Backlash distance            .BDST
#       offset           Offset from dial to user     .OFF
#       done_moving      1=Done, 0=Moving, read-only  .DMOV
#
#    Exceptions:
#       The check_limits() method raises an 'MotorLimitException' if a soft limit
#       or hard limit is detected.  The move() method calls
#       check_limits() unless they are called with the
#       ignore_limits=True keyword set.
#
#    Example use:
#       from epics import Motor
#       m = Motor('13BMD:m38')
#       m.move(10)               # Move to position 10 in user coordinates
#       m.move(100, dial=True)   # Move to position 100 in dial coordinates
#       m.move(1, step=True, relative=True) # Move 1 step relative to current position
#
#       m.stop()                 # Stop moving immediately
#       high = m.high_limit      # Get the high soft limit in user coordinates
#       m.dial_high_limit = 100  # Set the high limit to 100 in dial coodinates
#       speed = m.slew_speed     # Get the slew speed
#       m.acceleration = 0.1     # Set the acceleration to 0.1 seconds
#       p=m.get_position()       # Get the desired motor position in user coordinates
#       p=m.get_position(dial=1) # Get the desired motor position in dial coordinates
#       p=m.get_position(readback=1) # Get the actual position in user coordinates
#       p=m.get_position(readback=1, step=1) Get the actual motor position in steps
#       p=m.set_position(100)   # Set the current position to 100 in user coordinates
#          # Puts motor in Set mode, writes value, puts back in Use mode.
#       p=m.set_position(10000, step=1) # Set the current position to 10000 steps
#
#     """
#     # parameter name (short), PV suffix,  longer description
#
#     #
#     changed = QtCore.pyqtSignal(object)
#
#     _extras = {
#         'disabled': '_able.VAL',
#         'calibPosn': ':calibPosn'}
#
#     _alias = {
#         'acceleration': 'ACCL',
#         'back_accel': 'BACC',
#         'backlash': 'BDST',
#         'back_speed': 'BVEL',
#         'card': 'CARD',
#         'dial_high_limit': 'DHLM',
#         'direction': 'DIR',
#         'dial_low_limit': 'DLLM',
#         'settle_time': 'DLY',
#         'done_moving': 'DMOV',
#         'dial_readback': 'DRBV',
#         'description': 'DESC',
#         'dial_drive': 'DVAL',
#         'units': 'EGU',
#         'encoder_step': 'ERES',
#         'freeze_offset': 'FOFF',
#         'move_fraction': 'FRAC',
#         'hi_severity': 'HHSV',
#         'hi_alarm': 'HIGH',
#         'hihi_alarm': 'HIHI',
#         'high_limit': 'HLM',
#         'high_limit_set': 'HLS',
#         'hw_limit': 'HLSV',
#         'home_forward': 'HOMF',
#         'home_reverse': 'HOMR',
#         'high_op_range': 'HOPR',
#         'high_severity': 'HSV',
#         'integral_gain': 'ICOF',
#         'jog_accel': 'JAR',
#         'jog_forward': 'JOGF',
#         'jog_reverse': 'JOGR',
#         'jog_speed': 'JVEL',
#         'last_dial_val': 'LDVL',
#         'low_limit': 'LLM',
#         'low_limit_set': 'LLS',
#         'lo_severity': 'LLSV',
#         'lolo_alarm': 'LOLO',
#         'low_op_range': 'LOPR',
#         'low_alarm': 'LOW',
#         'last_rel_val': 'LRLV',
#         'last_dial_drive': 'LRVL',
#         'last_SPMG': 'LSPG',
#         'low_severity': 'LSV',
#         'last_drive': 'LVAL',
#         'soft_limit': 'LVIO',
#         'in_progress': 'MIP',
#         'missed': 'MISS',
#         'moving': 'MOVN',
#         'resolution': 'MRES',
#         'motor_status': 'MSTA',
#         'offset': 'OFF',
#         'output_mode': 'OMSL',
#         'output': 'OUT',
#         'prop_gain': 'PCOF',
#         'precision': 'PREC',
#         'readback': 'RBV',
#         'retry_max': 'RTRY',
#         'retry_count': 'RCNT',
#         'retry_deadband': 'RDBD',
#         'dial_difference': 'RDIF',
#         'raw_encoder_pos': 'REP',
#         'raw_high_limit': 'RHLS',
#         'raw_low_limit': 'RLLS',
#         'relative_value': 'RLV',
#         'raw_motor_pos': 'RMP',
#         'raw_readback': 'RRBV',
#         'readback_res': 'RRES',
#         'raw_drive': 'RVAL',
#         'dial_speed': 'RVEL',
#         's_speed': 'S',
#         's_back_speed': 'SBAK',
#         's_base_speed': 'SBAS',
#         's_max_speed': 'SMAX',
#         'set': 'SET',
#         'stop_go': 'SPMG',
#         's_revolutions': 'SREV',
#         'stop_command': 'STOP',
#         't_direction': 'TDIR',
#         'tweak_forward': 'TWF',
#         'tweak_reverse': 'TWR',
#         'tweak_val': 'TWV',
#         'use_encoder': 'UEIP',
#         'u_revolutions': 'UREV',
#         'use_rdbl': 'URIP',
#         'drive': 'VAL',
#         'base_speed': 'VBAS',
#         'slew_speed': 'VELO',
#         'version': 'VERS',
#         'max_speed': 'VMAX',
#         'use_home': 'ATHM',
#         'deriv_gain': 'DCOF',
#         'use_torque': 'CNEN',
#         'device_type': 'DTYP',
#         'record_type': 'RTYP',
#         'status': 'STAT'}
#
#     _init_list = ('DMOV', 'VAL', 'DESC', 'RTYP', 'RBV', 'PREC', 'TWV', 'FOFF', 'EGU')
#     _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_init_list',
#                '_alias', '_extras', '_pos_set', '_collision_support')
#
#     def __init__(self, name=None, timeout=3.0, pos_set='endstation', collision_support=False):
#         if name is None:
#             raise MotorException("must supply motor name")
#
#         if name.endswith('.VAL'):
#             name = name[:-4]
#         if name.endswith('.'):
#             name = name[:-1]
#
#         self._prefix = name
#         self._pos_set = pos_set
#         self._collision_support = collision_support
#
#         device.Device.__init__(self, name, delim='.',
#                                attrs=self._init_list,
#                                timeout=timeout)
#
#         # print 'connecting motor [%s]' % name
#         # make sure this is really a motor!
#         rectype = self.get('RTYP')
#         if rectype is None:
#             raise MotorException("%s PV does not exist" % name)
#
#         if rectype != 'motor':
#             raise MotorException("%s is not an Epics Motor" % name)
#
#         for key, val in self._extras.items():
#             pvname = "%s%s" % (name, val)
#             self.add_pv(pvname, attr=key)
#
#         if (collision_support):
#             # the setpoint for this motor is the A field of a transform record :check_tr.A
#             pvname = "%s:check_tr.A" % (name)
#             self.add_pv(pvname, attr='check_tr.A')
#
#
#             # self.put('disabled', 0)
#         self._callbacks = {}
#
#     def __repr__(self):
#         return "<epics.Motor: %s: '%s'>" % (self._prefix, self.DESC)
#
#     def __str__(self):
#         return self.__repr__()
#
#     def __getattr__(self, attr):
#         " internal method "
#         if attr in self._alias:
#             attr = self._alias[attr]
#         if attr in self._pvs:
#             return self.get(attr)
#         if not attr.startswith('__'):
#             pv = self.PV(attr, connect=True)
#             if not pv.connected:
#                 raise MotorException("EpicsMotor has no attribute %s" % attr)
#             return self.get(attr)
#
#         else:
#             return self._pvs[attr]
#
#     def __setattr__(self, attr, val):
#         # print 'SET ATTR ', attr, val
#         if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
#                     '_alias', '_nonpvs', '_extra', '_callbacks', '_pos_set', '_collision_support'):
#             self.__dict__[attr] = val
#             return
#         if attr in self._alias:
#             attr = self._alias[attr]
#         if attr in self._pvs:
#             return self.put(attr, val)
#         elif attr in self.__dict__:
#             self.__dict__[attr] = val
#         elif self._init:
#             try:
#                 self.PV(attr)
#                 return self.put(attr, val)
#             except:
#                 raise MotorException("EpicsMotor has no attribute %s" % attr)
#
#     def get_name(self):
#         return (self._prefix[:-1])
#
#     def set_calibrated_position(self, pos):
#         self.put('calibPosn', pos)
#
#     def check_limits(self):
#         """ check motor limits:
#         returns None if no limits are violated
#         raises expection if a limit is violated"""
#         for field, msg in (('LVIO', 'Soft limit violation'),
#                            ('HLS', 'High hard limit violation'),
#                            ('LLS', 'Low  hard limit violation')):
#             if self.get(field) != 0:
#                 raise MotorLimitException(msg)
#         return
#
#     def within_limits(self, val, dial=False):
#         """ returns whether a value for a motor is within drive limits
#         with dial=True   dial limits are used (default is user limits)"""
#         ll_name, hl_name = 'LLM', 'HLM'
#         if dial:
#             ll_name, hl_name = 'DLLM', 'DHLM'
#         return (val <= self.get(hl_name) and val >= self.get(ll_name))
#
#     def move(self, val=None, relative=False, wait=False, timeout=300.0,
#              dial=False, step=False, raw=False,
#              ignore_limits=False, confirm_move=False):
#         """ moves motor drive to position
#
#         arguments:
#         ==========
#          val            value to move to (float) [Must be provided]
#          relative       move relative to current position    (T/F) [F]
#          wait           whether to wait for move to complete (T/F) [F]
#          dial           use dial coordinates                 (T/F) [F]
#          raw            use raw coordinates                  (T/F) [F]
#          step           use raw coordinates (backward compat)(T/F) [F]
#          ignore_limits  try move without regard to limits    (T/F) [F]
#          confirm_move   try to confirm that move has begun   (T/F) [F]
#          timeout        max time for move to complete (in seconds) [300]
#
#         return values:
#           -13 : invalid value (cannot convert to float).  Move not attempted.
#           -12 : target value outside soft limits.         Move not attempted.
#           -11 : drive PV is not connected:                Move not attempted.
#            -8 : move started, but timed-out.
#            -7 : move started, timed-out, but appears done.
#            -5 : move started, unexpected return value from PV.put()
#            -4 : move-with-wait finished, soft limit violation seen
#            -3 : move-with-wait finished, hard limit violation seen
#             0 : move-with-wait finish OK.
#             0 : move-without-wait executed, not cpmfirmed
#             1 : move-without-wait executed, move confirmed
#             3 : move-without-wait finished, hard limit violation seen
#             4 : move-without-wait finished, soft limit violation seen
#
#         """
#         step = step or raw
#
#         NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
#         TIMEOUT, TIMEOUT_BUTDONE = -8, -7
#         UNKNOWN_ERROR = -5
#         DONEW_SOFTLIM, DONEW_HARDLIM = -4, -3
#         DONE_OK = 0
#         MOVE_BEGUN, MOVE_BEGUN_CONFIRMED = 0, 1
#         NOWAIT_SOFTLIM, NOWAIT_HARDLIM = 4, 3
#         try:
#             val = float(val)
#         except TypeError:
#             return NONFLOAT
#
#         drv, rbv = ('VAL', 'RBV')
#         if dial:
#             drv, rbv = ('DVAL', 'DRBV')
#         elif step:
#             drv, rbv = ('RVAL', 'RRBV')
#
#         if relative:
#             val += self.get(drv)
#
#         # Check for limit violations
#         if not ignore_limits and not step:
#             if not self.within_limits(val, dial=dial):
#                 return OUTSIDE_LIMITS
#
#         if (self._collision_support):
#             stat = self.put('check_tr.A', val, wait=wait, timeout=timeout)
#         else:
#             stat = self.put(drv, val, wait=wait, timeout=timeout)
#
#         if stat is None:
#             return UNCONNECTED
#
#         if wait and stat == -1:  # move started, exceeded timeout
#             if self.get('DMOV') == 0:
#                 return TIMEOUT
#             return TIMEOUT_BUTDONE
#         if 1 == stat:
#             if wait:  # ... and finished OK
#                 if 1 == self.get('LVIO'):
#                     return DONEW_SOFTLIM
#                 elif 1 == self.get('HLS') or 1 == self.get('LLS'):
#                     return DONEW_HARDLIM
#                 return DONE_OK
#             else:
#                 if 1 == self.get('LVIO') or confirm_move:
#                     ca.poll(evt=1.e-2)
#                 moving = False
#                 if confirm_move:
#                     t0 = time.time()
#                     while self.get('MOVN') == 0:
#                         ca.poll(evt=1.e-3)
#                         if time.time() - t0 > 0.25: break
#                 if 1 == self.get('MOVN'):
#                     return MOVE_BEGUN_CONFIRMED
#                 elif 1 == self.get('LVIO'):
#                     return NOWAIT_SOFTLIM
#                 elif 1 == self.get('HLS') or 1 == self.get('LLS'):
#                     return NOWAIT_HARDLIM
#                 else:
#                     return MOVE_BEGUN
#         return UNKNOWN_ERROR
#
#     def get_position(self, dial=False, readback=True, step=False, raw=False):
#         """
#         Returns the target or readback motor position in user, dial or step
#         coordinates.
#
#       Keywords:
#          readback:
#             Set readback=True to return the readback position in the
#             desired coordinate system.  The default is to return the
#             drive position of the motor.
#
#          dial:
#             Set dial=True to return the position in dial coordinates.
#             The default is user coordinates.
#
#          raw (or step):
#             Set raw=True to return the raw position in steps.
#             The default is user coordinates.
#
#          Notes:
#             The "raw" or "step" and "dial" keywords are mutually exclusive.
#             The "readback" keyword can be used in user, dial or step
#             coordinates.
#
#       Examples:
#         m=epicsMotor('13BMD:m38')
#         m.move(10)                   # Move to position 10 in user coordinates
#         p=m.get_position(dial=True)  # Read the target position in dial coordinates
#         p=m.get_position(readback=True, step=True) # Read the actual position in steps
#         """
#         pos, rbv = ('VAL', 'RBV')
#         if dial:
#             pos, rbv = ('DVAL', 'DRBV')
#         elif step or raw:
#             pos, rbv = ('RVAL', 'RRBV')
#         if readback:
#             pos = rbv
#         return self.get(pos)
#
#     def tweak(self, direction='foreward', wait=False, timeout=300.0):
#         """ move the motor by the tweak_val
#
#         takes optional args:
#          direction    direction of motion (forward/reverse)  [forward]
#                          must start with 'rev' or 'back' for a reverse tweak.
#          wait         wait for move to complete before returning (T/F) [F]
#          timeout      max time for move to complete (in seconds) [300]
#         """
#
#         ifield = 'TWF'
#         if direction.startswith('rev') or direction.startswith('back'):
#             ifield = 'TWR'
#
#         stat = self.put(ifield, 1, wait=wait, timeout=timeout)
#         ret = stat
#         if stat == 1:
#             ret = 0
#         if stat == -2:
#             ret = -1
#         try:
#             self.check_limits()
#         except MotorLimitException:
#             ret = -1
#         return ret
#
#     def set_position(self, position, dial=False, step=False, raw=False):
#         """
#       Sets the motor position in user, dial or step coordinates.
#
#       Inputs:
#          position:
#             The new motor position
#
#       Keywords:
#          dial:
#             Set dial=True to set the position in dial coordinates.
#             The default is user coordinates.
#
#          raw:
#             Set raw=True to set the position in raw steps.
#             The default is user coordinates.
#
#       Notes:
#          The 'raw' and 'dial' keywords are mutually exclusive.
#
#       Examples:
#          m=epicsMotor('13BMD:m38')
#          m.set_position(10, dial=True)   # Set the motor position to 10 in
#                                       # dial coordinates
#          m.set_position(1000, raw=True) # Set the motor position to 1000 steps
#          """
#
#         # Put the motor in "SET" mode
#         self.put('SET', 1)
#
#         # determine which drive value to use
#         drv = 'VAL'
#         if dial:
#             drv = 'DVAL'
#         elif step or raw:
#             drv = 'RVAL'
#
#         self.put(drv, position)
#
#         # Put the motor back in "Use" mode
#         self.put('SET', 0)
#
#     def get_pv(self, attr):
#         "return  PV for a field"
#         return self.PV(attr)
#
#     def clear_callback(self, attr='drive'):
#         "clears callback for attribute"
#         try:
#             index = self._callbacks.get(attr, None)
#             if index is not None:
#                 self.PV(attr).remove_callback(index=index)
#         except:
#             self.PV(attr).clear_callbacks()
#
#     def set_callback(self, attr='VAL', callback=None, kws=None):
#         "define a callback for an attribute"
#         self.get(attr)
#         kw_args = {}
#         kw_args['motor_field'] = attr
#         if kws is not None:
#             kw_args.update(kws)
#
#         index = self.PV(attr).add_callback(callback=callback, **kw_args)
#         self._callbacks[attr] = index
#
#     def refresh(self):
#         """ refresh all motor parameters currently in use:
#         make sure all used attributes are up-to-date."""
#         ca.poll()
#
#     def StopNow(self):
#         "stop motor as soon as possible"
#         self.stop()
#
#     def stop(self):
#         "stop motor as soon as possible"
#         self.STOP = 1
#
#     def make_step_list(self, minstep=0.0, maxstep=None, decades=10):
#         """ create a reasonable list of motor steps, as for a dropdown menu
#         The list is based on motor range Mand precision"""
#
#         if maxstep is None:
#             maxstep = 0.6 * abs(self.HLM - self.LLM)
#         steplist = []
#         for i in range(decades):
#             for step in [j * 10 ** (i - self.PREC) for j in (1, 2, 5)]:
#                 if (step <= maxstep and step > 0.98 * minstep):
#                     steplist.append(step)
#         return steplist
#
#     def get_info(self):
#         "return information, current field values"
#         out = {}
#         for attr in ('DESC', 'VAL', 'RBV', 'PREC', 'VELO', 'STAT',
#                      'SET', 'TWV', 'LLM', 'HLM', 'SPMG'):
#             out[attr] = self.get(attr, as_string=True)
#         return out
#
#     def show_info(self):
#         " show basic motor settings "
#         ca.poll()
#         out = []
#         out.append(repr(self))
#         out.append("--------------------------------------")
#         for nam, val in self.get_info().items():
#             if len(nam) < 16:
#                 nam = "%s%s" % (nam, ' ' * (16 - len(nam)))
#             out.append("%s = %s" % (nam, val))
#         out.append("--------------------------------------")
#         ca.write("\n".join(out))
#
#     def show_all(self):
#         """ show all motor attributes"""
#         out = []
#         add = out.append
#         add("# Motor %s" % (self._prefix))
#         add("#  field               value                 PV name")
#         add("#------------------------------------------------------------")
#         ca.poll()
#         klist = list(self._alias.keys())
#         klist.sort()
#         for attr in klist:
#             suff = self._alias[attr]
#             # pvn = self._alias[attr]
#             label = attr + ' ' * (18 - min(18, len(attr)))
#             value = self.get(suff, as_string=True)
#             pvname = self.PV(suff).pvname
#             if value is None:
#                 value = 'Not Connected??'
#             value = value + ' ' * (18 - min(18, len(value)))
#             # print " %s  %s  %s" % (label, value, pvname)
#             add(" %s  %s  %s" % (label, value, pvname))
#
#         ca.write("\n".join(out))
#
#     def confirm_stopped(self):
#         t = 0
#         done = False
#         while ((not done) and (t < START_TIMEOUT)):
#             time.sleep(WAIT_SLEEP)
#             QtWidgets.QApplication.processEvents()
#             t += 1
#             if self.get('DMOV') == 0:
#                 done = True
#         # if(t >= START_TIMEOUT):
#         #    print 'Timed out waiting to START'
#         # print 'move started'
#         t = 0
#         done = False
#         while ((not done) and (t < MOVE_TIMEOUT)):
#             time.sleep(WAIT_SLEEP)
#             QtWidgets.QApplication.processEvents()
#             t += 1
#             if self.get('DMOV') == 1:
#                 done = True
#         if (t >= MOVE_TIMEOUT):
#             print 'Timed out waiting to STOP'
#
#     def move_and_zero(self, pos):
#         self.move(pos)
#         # print 'waiting for %s to stop' % self._prefix
#         self.confirm_stopped()
#         # print '%s has now stopped' % self._prefix
#         self.set_position(0.0)
#         # print '%s setting zero' % self._prefix
#
#     def wait_for_stopped_and_zero(self):
#         # print 'waiting for %s to stop' % self._prefix
#         self.confirm_stopped()
#         # print '%s has now stopped' % self._prefix
#         self.set_position(0.0)
#         # print '%s setting zero' % self._prefix
#
#     def move_and_set_position(self, pos, setpos):
#         self.move(pos)
#         # print 'waiting for %s to stop' % self._prefix
#         self.confirm_stopped()
#         # print '%s has now stopped' % self._prefix
#         self.set_position(setpos)
#         # print '%s setting zero' % self._prefix
#
#     def is_active(self):
#         return (self._pvs['DESC'].connected)


if (__name__ == '__main__'):
    # for arg in sys.argv[1:]:
    #    m = Motor(arg)
    #    m.show_info()
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    m = Motor_Qt('IOC:m901', pos_set=1, collision_support=False)
    # m = Motor('IOC:m106',pos_set=1, collision_support=False)
    # print m.get_name()
    # m.move(-5432, ignore_limits=True)
    print('HLM', m.get_high_limit())
    print('LLM', m.get_low_limit())

    app.exec_()


