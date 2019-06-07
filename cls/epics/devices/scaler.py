#!/usr/bin/python 
"""Epics Scaler"""
import epics

class Scaler(epics.Device):
    """ 
    Simple implementation of SynApps Scaler Record.   
    """
    attrs = ('CNT', 'CONT', 'TP', 'T')
    attr_kws = {'calc_enable': '%s_calcEnable.VAL'}
    chan_attrs = ('NM%i', 'S%i')
    calc_attrs = {'calc%i': '%s_calc%i.VAL', 'expr%i': '%s_calc%i.CALC'}
    
    _fields = ('_prefix', '_pvs', '_delim', '_nchan', '_chans')
    
    def __init__(self, prefix, nchan=8):
        self._nchan  = nchan
        self._chans = list(range(1, nchan+1))
        
        attrs = list(self.attrs)
        for i in self._chans:
            for att in self.chan_attrs:
                attrs.append(att % i)
                
        epics.Device.__init__(self, prefix, delim='.', attrs=attrs)

        for key, val in list(self.attr_kws.items()):
            self.add_pv(val % prefix, attr= key)
            
        for i in self._chans:
            for key, val in list(self.calc_attrs.items()):
                self.add_pv(val % (prefix, i), attr = key % i)

        
    def AutoCountMode(self):
        "set to autocount mode"
        self.put('CONT', 1)

    def OneShotMode(self):
        "set to one shot mode"        
        self.put('CONT', 0)

    def CountTime(self, ctime):
        "set count time"
        self.put('TP', ctime)
        
    def Count(self, ctime=None):
        "set count, with optional counttime"
        if ctime is not None:
            self.CountTime(ctime)
        self.put('CNT', 1)

    def EnableCalcs(self):
        " enable calculations"
        self.put('calc_enable', 1)

    def setCalc(self, i, calc):
        "set the calculation for scaler i"
        attr = 'expr%i'  % i
        self.put(attr, calc)

    def getNames(self):
        "get all names"
        return [self.get('NM%i' % i) for i in self._chans]

    def Read(self, use_calc=False):
        "read all values"
        attr = 'S%i'
        if use_calc:
            attr = 'calc%i'
        return [self.get(attr % i) for i in self._chans]
