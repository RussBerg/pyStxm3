#!/usr/bin/env python
"""
 This module provides support for the EPICS motor record.
"""
import time
import copy
import numpy

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from collections import OrderedDict

from ophyd import EpicsMotor
from ophyd.signal import (EpicsSignal, EpicsSignalRO)
from ophyd.device import (Device, Component as Cpt)
from ophyd.utils.epics_pvs import (data_type, data_shape)

from bcm.devices.dev_categories import dev_categories
from bcm.devices import BaseDevice
from cls.utils.dict_utils import dct_get, dct_put

WAIT_SLEEP = 0.002
START_TIMEOUT = 20
MOVE_TIMEOUT = 900000

class Motor_Qt(EpicsMotor):
    """ just a convienience class so that PVs can be configured in the beamline configuration file
    and used as if they were other devices, making the rest of the code cleaner
    """
    description = Cpt(EpicsSignal, '.DESC', kind='omitted')
    units = Cpt(EpicsSignal, '.EGU', kind='omitted')
    high_limit_val = Cpt(EpicsSignal, '.HLM', kind='omitted')
    low_limit_val = Cpt(EpicsSignal, '.LLM', kind='omitted')
    use_torque = Cpt(EpicsSignal, '.CNEN', kind='omitted')


    def __init__(self, *args, **kwargs):

        stripped_kwargs = copy.copy(kwargs)
        if('pos_set' in kwargs.keys()):
            del(stripped_kwargs['pos_set'])
        else:
            kwargs['pos_set'] = 'endstation'

        if('collision_support' in kwargs.keys()):
            del (stripped_kwargs['collision_support'])
        else:
            kwargs['collision_support'] = False

        if ('abstract_mtr' in kwargs.keys()):
            del (stripped_kwargs['abstract_mtr'])
        else:
            kwargs['abstract_mtr'] = False

        super(Motor_Qt, self).__init__(*args, **stripped_kwargs)

        if kwargs['name'] is None:
            raise MotorException("must supply motor name")

        self._name = kwargs['name']

        if kwargs['name'].endswith('.VAL'):
            kwargs['name'] = kwargs['name'][:-4]
        if kwargs['name'].endswith('.'):
            kwargs['name'] = kwargs['name'][:-1]

        self.signal_name = args[0]
        self._pos_set = kwargs['pos_set']
        self._collision_support = kwargs['collision_support']

        self._ctrl_vars = {}
        self._devs = {}

        if ('units' in kwargs.keys()):
            self._egu = kwargs['units']
        else:
            self._egu = 'um'

        if ('desc' in kwargs.keys()):
            self._desc = kwargs['desc']
        else:
            self._desc = 'mtr'

        # for key, val in list(self._alias.items()):
        #     devname = "%s.%s" % (self.signal_name, val)
        #     self.add_dev(devname, attr=key)

        if (kwargs['collision_support']):
            # the setpoint for this motor is the A field of a transform record :check_tr.A
            devname = "%s:check_tr.A" % (self.signal_name)
            #self.add_dev(devname, attr='check_tr.A')
            self.check_tr_A = EpicsSignal(devname, kind='omitted')

        if(not kwargs['abstract_mtr']):
            # for key, val in list(self._extras.items()):
            #     devname = "%s%s" % (self.signal_name, val)
            #     self.add_dev(devname, attr=key)
            self.disabled = EpicsSignal('%s_able.VAL' % self.signal_name, kind='omitted')
            self.calibPosn = EpicsSignal('%s:calibPosn' % self.signal_name, kind='omitted')

        # for _attr in self.attrs:
        #     self.add_attr_dev(_attr)

        self._dev_category = dev_categories.SIGNALS
        self.set_dev_units('um')

    #def limits(self):
    #    return (self.get_low_limit(), self.get_high_limit())

    def describe(self):
        """Return the description as a dictionary

        Returns
        -------
        dict
            Dictionary of name and formatted description string
        """
        # if(self.low_limit is None):
        #     self.get_low_limit()
        # if(self.high_limit is None):
        #     self.get_high_limit()
        # description
        # MUST CALL THE BASE CLASS DESCRIBE() FIRST!!!!!!
        desc = super().describe()
        #desc = OrderedDict()
        #print('describe for name[%s] signal_name[%s]' % (self.name, self.signal_name))
        for key in desc:
            desc[key]['units'] = self._egu
            desc[key]['lower_ctrl_limit'] = self.get_low_limit()
            desc[key]['upper_ctrl_limit'] = self.get_high_limit()
            desc[key]['desc'] = self.description.get()

        return desc

    def set_dev_category(self, category):
        self._dev_category = category


    def set_dev_units(self, units):
        self.units.put(units)

    # def stop(self):
    #     self.motor_stop.put(1, wait=False)
    #
    def add_dev(self, devname, attr=None, **kw):
        if attr is None:
            attr = devname
        self._devs[attr] = BaseDevice(devname, **kw)
        return self._devs[attr]

    def get_dev(self, attr):
        if(attr in self._devs.keys()):
            return(self._devs[attr])
        else:
            return(None)


    def add_attr_dev(self, attr, **kw):
        devname = self.signal_name + '.' + attr
        self._devs[attr] = BaseDevice(devname, **kw)
        return self._devs[attr]


    def assign_exiting_attr(self, attr):
        self._devs[attr] = getattr(self, attr)


    def add_callback(self, attr, func, **kwargs):
        if(hasattr(self, attr)):
            dev = getattr(self, attr)
            dev.subscribe(func, **kwargs)
        else:
            print('motor_qt: add_callback: ERROR! [%s] does not exist' % attr)

    # def _on_pv_changed(self, **kwargs):
    #     '''
    #     ALWAYS return 'value' plus whatever kwargs the user passed in
    #     :param kwargs:
    #     :return:
    #     '''
    #     dct = {}
    #     #'value' must be a part of default kwargs
    #     if(len(self.cb_args) == 0):
    #         #only return the value by itself
    #         self._new_data.emit(kwargs['value'])
    #     else:
    #         #else return a dict of value plus cb_args
    #         dct['value'] = kwargs['value']
    #         for k in self.cb_args:
    #             dct[k] = kwargs[k]
    #         #emit the changed signal
    #         self._new_data.emit(dct)
    #
    def get_desc(self):
        desc = self.description.get()
        if(type(desc) is numpy.ndarray):
            #convert it to a string
            desc = "".join([chr(item) for item in desc])
        return(desc)

    def get_units(self):
        units = self.units.get()
        if (type(units) is numpy.ndarray):
            # convert it to a string
            units = "".join([chr(item) for item in units])
        return(units)
    #
    def report(self):
        """ return a dict that reresents all of the settings for this device """
        print('name = %s, type = %s' % (str(self.__class__), self.name))


    def get_name(self):
        return (self.signal_name)
    #
    def get_position(self):
        return (self.user_readback.get())

    def get_low_limit(self):
        if (self.connected):
            return(self.low_limit_val.get())
        else:
            print('get_low_limit: motor not connected')
            return (None)

    def get_high_limit(self):
        if(self.connected):
            return(self.high_limit_val.get())
        else:
            print('get_high_limit: motor not connected')
            return(None)

    #
    # def count(self, val):
    #     #print 'count called', val
    #     self.changed.emit(val)
    #     return (val)
    #
    # def get(self, attr=None):
    #     if(attr is None):
    #         return(self._devs['RBV'].get())
    #     else:
    #         return(self._devs[attr].get())
    def get(self, attr=None):
        if(attr is None):
            return(getattr(self, 'user_readback').get())
            #return(self._devs['RBV'].get())
        else:
            if(hasattr(self, attr)):
                return(getattr(self, attr).get())
            else:
                print('motor_qt: get: ERROR! attr [%s] does not exist' % attr)
    #
    def put(self, attr, val, wait=1.0, timeout=5.0):
        if (attr is None):
            print('motor_qt: put: ERROR! attr [%s] cannot be None')
            return
        if (hasattr(self, attr)):
            sig = getattr(self, attr)
            sig.put(val, wait=wait, timeout=timeout)
        else:
            print('motor_qt: put: ERROR! attr [%s] does not exist' % attr)
    #    self._devs[attr].put(val)
    #
    # def set_calibrated_position(self, pos):
    #     self.put('calibPosn', pos)
    #
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
        #self.put('set', 1)
        self.set_use_switch.put(1)
        #self.put('setpoint', position)
        self.user_setpoint.put(position)
        # Put the motor back in "Use" mode
        #self.put('set', 0)
        self.set_use_switch.put(0)
    #
    # def check_limits(self):
    #     """ check motor limits:
    #     returns None if no limits are violated
    #     raises expection if a limit is violated"""
    #     for field, msg in (('LVIO', 'Soft limit violation'),
    #                        ('HLS', 'High hard limit violation'),
    #                        ('LLS', 'Low  hard limit violation')):
    #         if self.get(field) != 0:
    #             raise MotorLimitException(msg)
    #     return
    #
    # def within_limits(self, val):
    #     """ returns whether a value for a motor is within drive limits
    #     with dial=True   dial limits are used (default is user limits)"""
    #     ll_name, hl_name = 'LLM', 'HLM'
    #     return (val <= self.get(hl_name) and val >= self.get(ll_name))
    #
    # def move(self, val=None, relative=False, wait=False, timeout=300.0,
    #          dial=False, step=False, raw=False,
    #          ignore_limits=False, confirm_move=False):
    #     """ moves motor drive to position
    #
    #     arguments:
    #     ==========
    #      val            value to move to (float) [Must be provided]
    #      relative       move relative to current position    (T/F) [F]
    #      wait           whether to wait for move to complete (T/F) [F]
    #      dial           use dial coordinates                 (T/F) [F]
    #      raw            use raw coordinates                  (T/F) [F]
    #      step           use raw coordinates (backward compat)(T/F) [F]
    #      ignore_limits  try move without regard to limits    (T/F) [F]
    #      confirm_move   try to confirm that move has begun   (T/F) [F]
    #      timeout        max time for move to complete (in seconds) [300]
    #
    #     return values:
    #       -13 : invalid value (cannot convert to float).  Move not attempted.
    #       -12 : target value outside soft limits.         Move not attempted.
    #       -11 : drive PV is not connected:                Move not attempted.
    #        -8 : move started, but timed-out.
    #        -7 : move started, timed-out, but appears done.
    #        -5 : move started, unexpected return value from PV.put()
    #        -4 : move-with-wait finished, soft limit violation seen
    #        -3 : move-with-wait finished, hard limit violation seen
    #         0 : move-with-wait finish OK.
    #         0 : move-without-wait executed, not cpmfirmed
    #         1 : move-without-wait executed, move confirmed
    #         3 : move-without-wait finished, hard limit violation seen
    #         4 : move-without-wait finished, soft limit violation seen
    #
    #     """
    #     step = step or raw
    #
    #     NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
    #     TIMEOUT, TIMEOUT_BUTDONE = -8, -7
    #     UNKNOWN_ERROR = -5
    #     DONEW_SOFTLIM, DONEW_HARDLIM = -4, -3
    #     DONE_OK = 0
    #     MOVE_BEGUN, MOVE_BEGUN_CONFIRMED = 0, 1
    #     NOWAIT_SOFTLIM, NOWAIT_HARDLIM = 4, 3
    #     try:
    #         val = float(val)
    #     except TypeError:
    #         return NONFLOAT
    #
    #     drv, rbv = ('setpoint', 'readback')
    #
    #     if relative:
    #         val += self.get(drv)
    #
    #     # Check for limit violations
    #     if not ignore_limits and not step:
    #         if not self.within_limits(val):
    #             return OUTSIDE_LIMITS
    #
    #     if (self._collision_support):
    #         stat = self.put('check_tr.A', val, wait=wait, timeout=timeout)
    #     else:
    #         stat = self.put(drv, val, wait=wait, timeout=timeout)
    #
    #     if stat is None:
    #         return UNCONNECTED
    #
    #     if wait and stat == -1:  # move started, exceeded timeout
    #         if self.get('DMOV') == 0:
    #             return TIMEOUT
    #         return TIMEOUT_BUTDONE
    #     if 1 == stat:
    #         if wait:  # ... and finished OK
    #             if 1 == self.get('soft_limit'):
    #                 return DONEW_SOFTLIM
    #             elif 1 == self.get('high_limit_set') or 1 == self.get('low_limit_set'):
    #                 return DONEW_HARDLIM
    #             return DONE_OK
    #         else:
    #             if 1 == self.get('soft_limit') or confirm_move:
    #                 ca.poll(evt=1.e-2)
    #             moving = False
    #             if confirm_move:
    #                 t0 = time.time()
    #                 while self.get('MOVN') == 0:
    #                     ca.poll(evt=1.e-3)
    #                     if time.time() - t0 > 0.25: break
    #             if 1 == self.get('MOVN'):
    #                 return MOVE_BEGUN_CONFIRMED
    #             elif 1 == self.get('soft_limit'):
    #                 return NOWAIT_SOFTLIM
    #             elif 1 == self.get('high_limit_set') or 1 == self.get('low_limit_set'):
    #                 return NOWAIT_HARDLIM
    #             else:
    #                 return MOVE_BEGUN
    #     return UNKNOWN_ERROR
    #
    def confirm_stopped(self):
        t = 0
        done = False
        while((not done) and (t < START_TIMEOUT) ):
            time.sleep(WAIT_SLEEP)
            QtWidgets.QApplication.processEvents()
            t += 1
            if self.motor_done_move.get() == 0:
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
            if self.motor_done_move.get() == 1:
                done = True
        if(t >= MOVE_TIMEOUT):
            print('Timed out waiting to STOP')

    def move_and_zero(self, pos):
        self.move(pos)
        # print 'waiting for %s to stop' % self.signal_name
        self.confirm_stopped()
        # print '%s has now stopped' % self.signal_name
        self.set_position(0.0)
        # print '%s setting zero' % self.signal_name

    def wait_for_stopped_and_zero(self):
        # print 'waiting for %s to stop' % self.signal_name
        self.confirm_stopped()
        # print '%s has now stopped' % self.signal_name
        self.set_position(0.0)
        # print '%s setting zero' % self.signal_name

    # def move_and_set_position(self, pos, setpos):
    #     self.move(pos)
    #     # print 'waiting for %s to stop' % self.signal_name
    #     self.confirm_stopped()
    #     # print '%s has now stopped' % self.signal_name
    #     self.set_position(setpos)
    #     # print '%s setting zero' % self.signal_name
    #


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




if (__name__ == '__main__'):
    # for arg in sys.argv[1:]:
    #    m = Motor(arg)
    #    m.show_info()
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    m = Motor_Qt('IOC:m901', name='m901', pos_set=1, collision_support=False)
    # m = Motor('IOC:m106',pos_set=1, collision_support=False)
    # print m.get_name()
    # m.move(-5432, ignore_limits=True)
    print('HLM', m.m.high_limit)
    print('LLM', m.low_limit)

    app.exec_()


