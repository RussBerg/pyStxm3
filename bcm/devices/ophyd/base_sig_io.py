
from bcm.devices import BaseDevice

from cls.utils.dict_utils import dct_get, dct_put

class BaseSignalIO_DEL(BaseDevice):

    """ This class is meant to be a single connection to a pv

    """
        #write_pv=None, val_only=False, val_kw='value', backend='epics'
    def __init__(self, signal_name=None, desc=None, egu='', cb=None, ret_kwarg='value', **cb_kwargs):
        super(BaseSignalIO_DEL, self).__init__(signal_name, **cb_kwargs)
        self.signal_name = signal_name
        self.value = None
        self.ctrl_vars = {}
        self.cb_args = {}
        #the key word to use in the kwargs dict
        self.return_kwarg = ret_kwarg

        for k in cb_kwargs:
            self.cb_args[k] = cb_kwargs[k]

        if(len(cb_kwargs) < 1):
            self.cb_args

        if (desc is not None):
            self.desc = desc
        else:
            self.desc = signal_name

        self.egu = egu

        if (signal_name is not None):

            if(cb is not None):
                #the user wants to override the default and setup their own handler for 'changed' signal
                self.changed.connect(cb)

    # def is_connected(self):
    #     return(self.pv.connected)

    # def _on_pv_changed(self, val):
    #     self._new_data.emit(val)
    #

    def get_desc(self):
        return(self.desc)

    def get_egu(self):
        return(self.egu)

    def get_report(self):
        """ return a dict that reresents all of the settings for this device """
        dct = {}
        dct_put(dct, 'name', self.signal_name)
        return (dct)

    def get_name(self):
        return (self.signal_name)

    def get_position(self):
        return (self.get())

    # def count(self, val):
    #     #print 'count called', val
    #     self.changed.emit(val)
    #     return (val)

    def get_low_limit(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        return (None)

    def get_high_limit(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        return (None)

    def get_enum_str(self):
        '''
        can be overridded by inheriting class
        :return:
        '''
        print('get_enum_str: NEED TO IMPLEMENT THIS')
        return([])

    def get_enum_str_as_int(self):
        '''

        :return:
        '''
        # val = self.pv.get()
        # if (type(val) is int):
        #     final = val
        # else:
        #     final = int(self.pv.enum_strs[val])
        # return (final)
        print('get_enum_str_as_int: NEED TO IMPLEMENT THIS')
        return([])


if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets


    def on_new_pmt(**kwargs):
        print('MY CALLBACK IS BEING CALLED:')
        print(kwargs)


    def on_new_pmt_val(val):
        print(val)


    #
    app = QtWidgets.QApplication(sys.argv)

    from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
    from bcm.devices import BaseDevice

    MAIN_OBJ.device('test')
    #ai3 = EpicsPv('uhvAi:ai:ai3_RBV', cb=on_new_pmt, cb_arg1='Hey man', id=234, mydct={'id':23, 'desc':'the fake description'})
    #ai1 = EpicsPv('uhvAi:ai:ai1_RBV', id=234, mydct={'id': 23, 'desc': 'the fake description'})
    #ai0 = BaseSignalIO('uhvAi:ai:ai0_RBV', id=554)
    ai0 = BaseDevice('uhvAi:ai:ai0_RBV', val_only=True, val_kw='value', backend='epics')
    ai0.changed.connect(on_new_pmt_val)
    sp = BaseDevice('IOC:m913.VAL', write_pv='IOC:m913.VAL')
    sp.put(-1234.567)
    #ai1.changed.connect(on_new_pmt_val)
    #ai3.changed.connect(on_new_pmt_val)
    app.exec_()
