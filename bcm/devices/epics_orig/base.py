'''Basic Beamline device

This module defines functions and classes for basic beamline devices which
implement generic housekeeping required by all devices.

'''

from PyQt5.QtCore import QObject, pyqtSignal
import re

from epics import PV

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
    #__qtsignals__ =  { 
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
        QObject.__init__(self)
        self.pending_devs = [] # used for EPICS devices and device groups
        self.health_manager = HealthManager()
        self.state_info = {'active': False, 'busy': False, 
                             'health': (0,''), 'message': ''}
        self.name = self.__class__.__name__ + ' Device'
        self._dev_state_patt = re.compile('^(\w+)_state$')
        #self._check_id = gobject.timeout_add(30000, self._check_active)
        
    
    def __repr__(self):
        state_txts = []
        for k,v in list(self.state_info.items()):
            state_txts.append(' %12s: %s' % (k, str(v)))
        state_txts.sort()
        txt = "<%s: %s\n%s\n>" % (self.__class__.__name__, self.name, '\n'.join(state_txts))
        return txt
        
    def _check_active(self):
        if len(self.pending_devs) > 0:
            inactive_devs = [dev.name for dev in self.pending_devs]
            msg = '\n\t'.join(inactive_devs)
            #msg = '[%d] inactive children:\n\t%s' % (len(inactive_devs), msg)
            msg = '[%d] inactive children.' % (len(inactive_devs))
            logger.warning( "(%s) %s" % (self.name, msg))
        return True
    
    def do_active(self, st):
        _k = {True: 'active', False: 'inactive'}
        logger.info( "(%s) is now %s." % (self.name, _k[st]))
        if not st:
            if len(self.pending_devs) > 0:
                inactive_devs = [dev.name for dev in self.pending_devs]
                msg = '[%d] inactive children.' % (len(inactive_devs))
                logger.warning( "(%s) %s" % (self.name, msg))
            
        
            
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
        for st, val in list(kwargs.items()):
            if st != 'health':
                # only signal a state change if it actually changes for non
                # health signals
                #sid = gobject.signal_lookup(st, self)
                #if sid == 0: break
                if self.state_info.get(st, None) != val:
                    self.state_info.update({st: val})
                    #RUSSemitThisWhenNothingElseIsRunning RUSS gobject.idle_add(self.emit, st, val)
                    if st == 'active':
                        #self.emit(SIGNAL("active(PyQt_PyObject)"), val)
                        self.active.emit(val)
                    if st == 'busy':
                        #self.emit(SIGNAL("busy(PyQt_PyObject)"), val)
                        self.busy.emit(val)
                        

            elif st == 'health':
                sev, cntx = val[:2]
                if sev != 0:          
                    self.health_manager.add(*val)
                else:
                    self.health_manager.remove(cntx)
                _health = self.health_manager.get_health()
                self.state_info.update({st: _health})
                #RUSSemitThisWhenNothingElseIsRunning RUSS gobject.idle_add(self.emit, st, *_health)
                #self.emit(SIGNAL("health(PyQt_PyObject)"), _health)
                self.health.emit(_health)
            
    def add_pv(self, *args, **kwargs):
        """ Add a process variable (PV) to the device and return its reference. 
        Keeps track of added PVs. Keyworded 
        arguments should be the same as those expected for instantiating a
        ``bcm.protocol.ca.PV`` object.
        
        This method also connects the PVs 'active' signal to the ``on_pv_active`` method.
        """

        
        dev = PV(*args, **kwargs)
        self.pending_devs.append(dev)
        #dev.connect('active', self.on_device_active)
        #QObject.connect(dev, SIGNAL('active(PyQt_PyObject)'), self.on_device_active)
        #dev.active.connect(self.on_device_active)
        
        return dev
    
    def add_devices(self, *args):
        """ Add one or more devices to the device. 
                
        This method also connects the devices' 'active' signal to the ``on_device_active`` method.
        """
        
        for dev in args:
            self.pending_devs.append(dev)
            #dev.connect('active', self.on_device_active)
            #QObject.connect(dev, SIGNAL('active(PyQt_PyObject)'), self.on_device_active)
            dev.active.connect(self.on_device_active)

    def on_device_active(self, dev, state):
        """I am called every time a device becomes active or inactive.
        I expect to receive a reference to the device and a boolean 
        state flag which is True on connect and False on disconnect. If it is
        a connection, I add the device to the pending device list
        otherwise I remove the device from the list. When ever the list goes to
        zero, I set the group state to active and inactive otherwise.
        """
        
        if state and dev in self.pending_devs:
            self.pending_devs.remove(dev)
        elif not state and dev not in self.pending_devs:
            self.pending_devs.append(dev)
        if len(self.pending_devs) == 0:
            self.set_state(active=True)
        else:
            self.set_state(active=False)

    def __getattr__(self, key):
        m = self._dev_state_patt.match(key)
        if m:
            key = m.group(1)
            return self.state_info.get(key, None)
        else:
            raise AttributeError("%s has no attribute '%s'" % (self.__class__.__name__, key))
        



class BaseDeviceGroup(BaseDevice):
    """A generic device container for convenient grouping of multiple devices, with 
    a single state reflecting combined states of individual devices."""

    pass

class HealthManager(object):
    """An object which manages the health state of a device.
    
    The object enables registration and removal of error states and consistent
    reporting of health based on all currently active health issues.
    """
    
    def __init__(self, **kwargs):
        """Takes key worded arguments. The keyword name is the context, and
        the value is an error string to be returned instead of the context name
        with all health information for the given context. 
        """
        self.msg_dict = kwargs
        self.health_states = set()
    
    def register_messages(self, **kwargs):
        """Update or add entries to the context message register"""
        self.msg_dict.update(kwargs)

        
    def add(self, severity, context, msg=None):
        """Adds an error state of the given context as a string
        and a severity value as a integer. If a message is given, it will be 
        stored and used instead of the context name. Only one message per context
        type is allowed. Use a different context if you want different messages.
        """
        if msg is not None:
            self.msg_dict.update({context: msg})
        self.health_states.add((severity, context))
    
    def remove(self, context):
        """Remove all errors of the given context as a string.
        """
        err_list = [e for e in self.health_states if e[1] == context]
        for e in err_list:
            self.health_states.remove(e)
    
    def get_health(self):
        """Generate an error code and string based on all the currently registered
        errors within the health registry
        """
        severity = 0
        msg_list = set()
        for sev, cntx in self.health_states:
            severity = severity | sev
            msg_list.add(self.msg_dict.get(cntx, cntx))
        msg = ' '.join(msg_list)
        return severity, msg
            
            
        
        