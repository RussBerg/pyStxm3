from PyQt5 import QtCore
import time as ttime
import ophyd
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, DeviceStatus
from bcm.devices.dev_categories import dev_categories

SIMULATE = True

class OphydQt_AIDevice(ophyd.Device):
    val = Cpt(EpicsSignal, '.VAL', kind='hinted')

    def __init__(self, prefix, name, **kwargs):
        super(OphydQt_AIDevice, self).__init__(prefix, name=name)
        #the dev category is so that the device can be categorized as a PRESSURE, POSITIONER, SIGNAL
        self._dev_category = dev_categories.SIGNALS
        if('units' in kwargs.keys()):
            self._units = kwargs['units']
        else:
            self._units = 'counts'

        if ('desc' in kwargs.keys()):
            self._desc = kwargs['desc']
        else:
            self._desc = 'Device'

    def set_dev_category(self, category):
        self._dev_category = category

    def set_dev_units(self, units):
        self._units = units

    # def stage(self):
    #     super().
    #
    # def unstage(self):
    #     pass

    def trigger(self):
        st = DeviceStatus(self)
        st.set_finished()
        return st

    def read(self):
        '''
        add _val because that is the read_attr
        :return:
        '''
        # return {self.name + '_val': {'value': self.val.get(),
        #                             'timestamp': ttime.time(),
        #                              'units': self._units}}
        return {self.name: {'value': self.val.get(),
                                     'timestamp': ttime.time(),
                                     'units': self._units}}

    def describe(self):
        '''
        on return from super().describe() res is the following:
        OrderedDict([('TM1610-3-I12-01_val',
              {'source': 'PV:TM1610-3-I12-01.VAL',
               'dtype': 'number',
               'shape': [],
               'units': None,
               'lower_ctrl_limit': None,
               'upper_ctrl_limit': None})])
        then this describe() adds 'units' and 'category'
        :return:
        '''
        #print('TestDetectorDevice: describe called')
        res = super().describe()
        d = res
        k = list(res.keys())[0]
        d[self.name] = res.pop(k)
        for key in d:
            d[key]['units'] = self._units
            d[key]['category'] = self._dev_category
            d[key]['desc'] = self._desc
        return d


        # #print('TestDetectorDevice: describe called')
        # res = super().describe()
        # #here the key is the name + _<EpicsSignal name> but I want this to be only 'name'
        # d = res
        # k = list(res.keys())[0]
        # d[self.name] = res.pop(k)
        # for key in d:
        #     d[key]['units'] = "counts"
        # return d

class OphydQt_NodeDevice(ophyd.Device):
    #Node meaning there are no fields lower than this signal

    def __init__(self, prefix, name, **kwargs):
        super(OphydQt_NodeDevice, self).__init__(prefix, name=name)
        #the dev category is so that the device can be categorized as a PRESSURE, POSITIONER, SIGNAL
        self._dev_category = dev_categories.SIGNALS
        if ('units' in kwargs.keys()):
            self._units = kwargs['units']
        else:
            self._units = 'counts'

    def set_dev_category(self, category):
        self._dev_category = category

    def set_dev_units(self, units):
        self._units = units

    def stage(self):
        pass

    def unstage(self):
        pass

    def trigger(self):
        st = DeviceStatus(self)
        st.done = True
        st.set_finished()
        return st

    def read(self):
        # return {self.name + '_val': {'value': self.get(),
        #                             'timestamp': ttime.time(),
        #                              'units': self._units}}
        return {self.name: {'value': self.get(),
                                     'timestamp': ttime.time(),
                                     'units': self._units}}

    def describe(self):
        #print('TestDetectorDevice: describe called')
        # res = super().describe()
        # for key in res:
        #     res[key]['units'] = self._units
        #     res[key]['category'] = self._dev_category
        # return res

        res = super().describe()
        d = res
        k = list(res.keys())[0]
        d[self.name] = res.pop(k)
        for key in d:
            d[key]['units'] = self._units
            d[key]['category'] = self._dev_category
            d[key]['desc'] = self._desc
        return d