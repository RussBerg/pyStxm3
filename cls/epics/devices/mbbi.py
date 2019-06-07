#!/usr/bin/python 
import epics

class mbbi(epics.Device):
    """ 
    Simple mbbi input device
    """
    #_fields = ('setpoint', 'INP', 'NAME','DESC',
    #					'ZRVL','ONVL','TWVL','THVL','FRVL','FVVL','SXVL','SVVL','EIVL','NIVL','TEVL','ELVL','TVVL','TTVL','FTVL','FFVL',
		#					'ZRST','ONST','TWST','THST','FRST','FVST','SXST','SVST','EIST','NIST','TEST','ELST','TVST','TTST','FTST','FFST')
    _fields = None

    def __init__(self,prefix):
        
        if self._fields != None:
            if not prefix.endswith('.'): 
                prefix = "%s." % prefix
            
        epics.Device.__init__(self,prefix,self._fields)


        