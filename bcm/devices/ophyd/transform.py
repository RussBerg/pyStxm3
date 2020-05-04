#!/usr/bin/env python
"""Epics transform record"""

import os
from bcm.devices import BaseObject


class Transform(BaseObject):
    "Epics transfrom record"

    # 	attr_fmts = {'Value': '%s',
    # 				 'Input': 'INP%s',
    # 				 'Input_Valid': 'I%sV',
    # 				 'Expression': 'CLC%s',
    # 				 'Output':  'OUT%s',
    # 				 'Output_Valid': 'O%sV',
    # 				 'Comment': 'CMT%s',
    # 				 'Expression_Valid': 'C%sV',
    # 				 'Previous_Value': 'L%s'}


    # _init_list   = ('VAL', 'DESC', 'RTYP', 'RBV', 'PREC', 'TWV', 'FOFF', 'EGU')

    def __init__(self, base_signal_name, **kwargs):

        # self.attr_fmts = {'%s': '%s',
        #              'INP%s': 'INP%s',
        #              'I%sV': 'I%sV',
        #              'CLC%s': 'CLC%s',
        #              'OUT%s': 'OUT%s',
        #              'O%sV': 'O%sV',
        #              'CMT%s': 'CMT%s'}
        # self.attr_fmts = {'%s': '%s',
        #                   'INP%s': 'INP%s',
        #                   'CLC%s': 'CLC%s',
        #                   'OUT%s': 'OUT%s',
        #                   'CMT%s': 'CMT%s'}
        self.attr_fmts = {'%s': '%s'}
        self.attrs = ['COPT', 'PREC', 'PINI', 'DESC']
        self.rows = 'ABCDEFGHIJKLMNOP'
        self.all_rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        self._delim = '.'


        if base_signal_name.endswith('.'):
            base_signal_name = base_signal_name[:-1]

        super(Transform, self).__init__(base_signal_name)

        self.main_dev = self.add_device(base_signal_name)
        self.changed = self.main_dev.changed
        self.on_connect = self.main_dev.on_connect
        self.is_connected = self.main_dev.is_connected

        # self.attrs = ['COPT', 'PREC', 'PINI']
        for fmt in list(self.attr_fmts.values()):
            for let in self.rows:
                self.attrs.append(fmt % let)

        for _attr in self.attrs:
            # sig_name = self.base_signal_name + self._delim + '%s' % _attr
            # self.add_device(sig_name, write_pv=sig_name)
            self.add_device(_attr, is_dev_attr=True)

    def __validrow(self, row):
        return (isinstance(row, str) and
                len(row) == 1 and row in self.rows)

    def get_name(self):
        # return (self.get('NAME'))
        return (self.base_signal_name.replace(self._delim, ''))

    def get_position(self):
        """ this is an API function for all devices/pvs/detectors """
        return (self.get_all())

    def get(self, _attr):
        if (_attr in self.devs.keys()):
            return (self.devs[_attr].get())

    def put(self, _attr, val):
        if (_attr in self.devs.keys()):
            return (self.devs[_attr].put(val))


    def get_all(self):
        all = {}
        all['PINI'] = self.get('PINI')
        all['PREC'] = self.get('PREC')

        for r in self.all_rows:
            all[r] = self.get_row(r)

        return (all)

    def get_row(self, row='A'):
        """get full data for a calculation 'row' (or letter):

        returns dictionary with keywords (and PV suffix for row='B'):

        'Value':			 B
        'Input':			 INPB
        'Input_Valid':	   IBV
        'Expression':		CLCB
        'Output':			OUTB
        'Output_Valid':	  OBV
        'Comment':		   CMTB
        'Expression_Valid':  CBV
        'Previous_Value':	LB

        """
        if not self.__validrow(row):
            return None
        dat = {}
        for label, fmt in list(self.attr_fmts.items()):
            #self.base_signal_name + self._delim + '%s' % _attr
            dat[label % row] = self.devs[fmt % row].get()
        return dat

    def set_row(self, row='A', data=None):
        """set full data for a calculation 'row' (or letter):

        data should be a dictionary as returned from get_row()
        """
        if not self.__validrow(row):
            return None
        for key, value in list(data.items()):
            if key in self.attr_fmts:
                attr = self.attr_fmts[key] % row
                if self.devs[attr].write_access:
                    self.devs[attr].put(value)

    def set_calc(self, row='A', calc=''):
        """set calc for a 'row' (or letter):
        calc should be a string"""
        if not self.__validrow(row):
            return None
        self.devs[self.attr_fmts['Expression'] % row].put(calc)

    def set_comment(self, row='A', comment=''):
        """set comment for a 'row' (or letter):
        comment should be a string"""
        if not self.__validrow(row):
            return None
        self.devs[self.attr_fmts['Comment'] % row].put(calc)

    def set_input(self, row='A', input=''):
        """set input PV for a 'row' (or letter):
        input should be a string"""
        if not self.__validrow(row):
            return None
        self.devs[self.attr_fmts['Input'] % row].put(calc)

    def gen_record_row(self, r, dct):
        r_dct = dct[r]
        s = '\tfield(CMT%s, "%s")		field(INP%s, "%s")		field(CLC%s, "%s")		field(%s, "%s")		field(OUT%s, "%s")\n' % \
            (r, r_dct['CMT%s' % r], r, r_dct['INP%s' % r], r, r_dct['CLC%s' % r], r, r_dct['%s' % r], r,
             r_dct['OUT%s' % r])
        return (s)

    def gen_record(self):
        dct = self.get_all()
        s = 'record(transform, "%s")\n' % self.name
        s += '{\n'
        s += '\tfield(PINI, "%s")\n' % dct['PINI']
        s += '\tfield(PREC, "%s")\n' % dct['PREC']
        s += '\n'

        for row in self.all_rows:
            s += self.gen_record_row(row, dct)
        s += '}\n\n'
        return (s)


if __name__ == '__main__':
    import os
    import sys
    from PyQt5 import QtWidgets


    # #for i in range(1,50):
    # #	t = Transform('BL08ID1:trans_%d:tr' % i)
    # #	print t.gen_record()
    # print('starting')
    # z = Transform('BL1610-I10:ENERGY:amb:zp:def')
    # #o = Transform('BL1610-I10:ENERGY:amb:osa:def')
    # print('done')
    # #print t.get_all()
    # #print t.gen_record()


    def mycallback(kwargs):
        print(kwargs)


    app = QtWidgets.QApplication(sys.argv)
    z = Transform('BL1610-I10:ENERGY:uhv:zp:def')
    print(z.get('A'))
    print(z.get('B'))
    print(z.get('C'))
    print(z.get('D'))
    print(z.get('E'))
    print(z.get('F'))
    print(z.get('G'))

    z.put('F', 777.123)
    z.put('CMTF', 'How you doin?')
    print(z.get('F'))


    sys.exit(app.exec_())
