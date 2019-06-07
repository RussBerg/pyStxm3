#!/usr/bin/python
import epics 

class Stringin(epics.Device):
    "Simple string input device"
    _fields = ('VAL','NAME','DESC','INP')
    def __init__(self,prefix):
        if not prefix.endswith('.'): prefix = "%s." % prefix
        epics.Device.__init__(self,prefix,self._fields)

    def get_name(self):
        return (self.get('NAME'))
