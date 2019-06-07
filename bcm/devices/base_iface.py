'''Basic Beamline device

This module defines functions and classes for basic beamline devices which
implement generic housekeeping required by all devices.

'''

from PyQt5.QtCore import QObject, pyqtSignal
import re

from cls.utils.log import get_module_logger

logger = get_module_logger('devices')


class BaseDevice(QObject):
    """A generic device object class.
        
    All devices should be derived from this class. Objects of this class are instances of
    ``gobject.GObject``. Objects have the following additional ``signals`` defined.
    
    Attributes:
    ----------
    In addition to all attributes defined by ``gobject.GObject``, a device also has the
    following attributes
        
        - ``health_manager``: A ``HealthManager`` object.
        - ``name``:  the name of the device
        
    
    Signals:
    --------
    
        - ``active``: emitted when the state of the device changes from inactive to active
           and vice-versa. Passes a single boolean value as a parameter. ``True`` represents
           a change from inactive to active, and ``False`` represents the opposite.
        - ``busy``: emitted to notify listeners of a change in the busy state of the device.
          A single boolean parameter is passed along with the signal. ``True`` means busy,
          ``False`` means not busy.
        - ``health``: signals an device sanity/error condition. Passes two parameters, an integer error code
          and a string description. The integer error codes are the following:
              - 0 : No error
              - 1 : MINOR, no impact to device functionality. No attention needed.
              - 2 : MARGINAL, no immediate impact to device functionality but may impact future
                functionality. Attention may soon be needed.
              - 4 : SERIOUS, functionality impacted but recovery is possible. Attention needed.
              - 8 : CRITICAL, functionality broken, recovery is not possible. Attention needed.
        - ``message``: signal for sending messages from the device to any listeners. Messages are
          passed as a single string parameter.
        
    """
    # signals
    # __qtsignals__ =  {
    #    "active": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
    #    "busy": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,)),
    #    "health": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
    #    "message": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    #    }

    active = pyqtSignal(bool)
    busy = pyqtSignal(bool)
    health = pyqtSignal(object)
    message = pyqtSignal(str)

    def __init__(self, name=None):
        '''
                        prefix is the low level control system name for this bi device
                        to be implemented by inheriting class'''
        pass

    def get_name(self):
        '''
        return the low level control system name for this bi device
        to be implemented by inheriting class'''
        pass

    # def __repr__(self):
    #     state_txts = []
    #     for k,v in self.state_info.items():
    #         state_txts.append(' %12s: %s' % (k, str(v)))
    #     state_txts.sort()
    #     txt = "<%s: %s\n%s\n>" % (self.__class__.__name__, self.name, '\n'.join(state_txts))
    #     return txt

    # def _check_active(self):
    #     if len(self.pending_devs) > 0:
    #         inactive_devs = [dev.name for dev in self.pending_devs]
    #         msg = '\n\t'.join(inactive_devs)
    #         #msg = '[%d] inactive children:\n\t%s' % (len(inactive_devs), msg)
    #         msg = '[%d] inactive children.' % (len(inactive_devs))
    #         logger.warning( "(%s) %s" % (self.name, msg))
    #     return True
    #
    # def do_active(self, st):
    #     _k = {True: 'active', False: 'inactive'}
    #     logger.info( "(%s) is now %s." % (self.name, _k[st]))
    #     if not st:
    #         if len(self.pending_devs) > 0:
    #             inactive_devs = [dev.name for dev in self.pending_devs]
    #             msg = '[%d] inactive children.' % (len(inactive_devs))
    #             logger.warning( "(%s) %s" % (self.name, msg))
    #
    #

    def get_position(self):
        """part of the API, to be implemented by the inheriting class"""
        pass

    def is_active(self):
        """Convenience function for active state"""
        return self.active_state

    def is_busy(self):
        """Convenience function for busy state"""
        return self.busy_state

    def get_state(self):
        """ Returns the state of the device as a dictionary. The entries of the
        state dictionary are:
        
            - ``active`` : Boolean
            - ``busy``: Boolean
            - ``health``: tuple(int, string)
            - ``message``: string
        
        """
        return self.state_info.copy()

    def set_state(self, **kwargs):
        """ Set the state of the device based on the specified keyworded arguments.
        Also emits the state signals in the process . Keyworded arguments follow 
        the same conventions as the state dictionary and the following are recognized:
                
            - ``active`` : Boolean
            - ``busy``: Boolean
            - ``health``: tuple(int, string, [string])
            - ``message``: string
        
        Signals will be emitted the specified keyworded arguments, which must have been
        defined as supported signals of the device.
        """
        pass

    def add_pv(self, *args, **kwargs):
        """ Add a process variable (PV) to the device and return its reference. 
        Keeps track of added PVs. Keyworded 
        arguments should be the same as those expected for instantiating a
        ``bcm.protocol.ca.PV`` object.
        
        This method also connects the PVs 'active' signal to the ``on_pv_active`` method.
        """
        pass

    def add_devices(self, *args):
        """ Add one or more devices to the device. 
                
        This method also connects the devices' 'active' signal to the ``on_device_active`` method.
        """

        pass

    def on_device_active(self, dev, state):
        """I am called every time a device becomes active or inactive.
        I expect to receive a reference to the device and a boolean 
        state flag which is True on connect and False on disconnect. If it is
        a connection, I add the device to the pending device list
        otherwise I remove the device from the list. When ever the list goes to
        zero, I set the group state to active and inactive otherwise.
        """
        pass

        # def __getattr__(self, key):
        #     m = self._dev_state_patt.match(key)
        #     if m:
        #         key = m.group(1)
        #         return self.state_info.get(key, None)
        #     else:
        #         raise AttributeError("%s has no attribute '%s'" % (self.__class__.__name__, key))
