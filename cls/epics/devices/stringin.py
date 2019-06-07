#!/usr/bin/python
import epics  

class stringin(epics.Device):
    "Simple string input device"
    _fields = ('setpoint','NAME','DESC','INP')
    def __init__(self,prefix):
        if not prefix.endswith('.'): prefix = "%s." % prefix
        epics.Device.__init__(self,prefix,self._fields)