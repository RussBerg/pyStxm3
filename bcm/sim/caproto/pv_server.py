#!/usr/bin/env python3
from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run
from textwrap import dedent


class SimpleIOC(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs

    Scalar PVs
    ----------
    A (int)
    B (float)

    Vectors PVs
    -----------
    C (vector of int)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    AA = pvproperty(value=1)
    A = pvproperty(value=1)
    B = pvproperty(value=2.0)
    C = pvproperty(value=[1, 2, 3])
    # def __init__(self, prefix, macros):
    #     super(SimpleIOC, self).__init__(prefix)
    #     self.C = pvproperty(value=[1, 2, 3])



if __name__ == '__main__':
    ioc_options, run_options = ioc_arg_parser( default_prefix='simple:',
        desc=dedent(SimpleIOC.__doc__))
    ioc = SimpleIOC(**ioc_options)
    run(ioc.pvdb, **run_options)