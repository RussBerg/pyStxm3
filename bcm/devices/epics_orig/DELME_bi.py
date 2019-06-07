#!/usr/bin/env python
from .base import BaseDevice

class bi(BaseDevice):
    """
    Simple binary input device
    """

    attrs = ('INP', 'ZNAM', 'ONAM', 'RVAL', 'VAL', 'EGU', 'HOPR', 'LOPR',
               'PREC', 'NAME', 'DESC', 'DTYP')

    def __init__(self, prefix, **kwargs):
        if prefix.endswith('.'):
            prefix = prefix[:-1]
        epics.Device.__init__(self, prefix, delim='.',
                              attrs=self.attrs,
                              **kwargs)

    def get_name(self):
        return (self.get('NAME'))

