#!/usr/bin/python
import epics

class Waveform(epics.Device):
    "Simple string input device"
    _fields = ('NAME', 'INP','NELM','DESC','FTVL', 'RARM', 'VAL', 'NORD', 'BUSY')
    def __init__(self,prefix):
        if not prefix.endswith('.'): prefix = "%s." % prefix
        epics.Device.__init__(self,prefix,self._fields)

    def get_name(self):
        return (self.get('NAME'))