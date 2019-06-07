
#NOTE: this device assumes that the waveform has already been programmed into the generator on the E712
from ophyd import (Component as Cpt, EpicsSignal, Device)



class E712WGDevice(Device):
    run = Cpt(EpicsSignal, 'ExecWavgen', kind='omitted', put_complete=True)
    num_cycles = Cpt(EpicsSignal, 'NumCycles', kind='omitted', put_complete=True)

    def __init__(self, prefix, name):
        super(E712WGDevice, self).__init__(prefix, name=name)

    def report(self):
        print('name = %s, type = %s' % (str(self.__class__), self.name))

    def trigger(self):
        st = super().trigger()
        #self.run.put(1, wait=True, callback=st._finished)

        #this put doesnt return until it is complete (the waveform generator is done)
        self.run.put(1, callback=st._finished)
        return st

    def unstage(self):
        st = super().unstage()
        self.run.put(0)
        st._finished = True
        return(st)
