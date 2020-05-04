#!/usr/bin/env python3
from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run


class MyRecordMockingIOC(PVGroup):
    # Define three records, an analog input (ai) record:
    zp_inout = pvproperty(value=1.0, mock_record='bo')
    zp_inout = pvproperty(value=1.0, mock_record='bo')

class RecordMockingIOC(PVGroup):
    # Define three records, an analog input (ai) record:
    scanselflag = pvproperty(value=1.0, mock_record='mbbo')


if __name__ == '__main__':
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='SIM_BL1610-I10:ENERGY:uhv:zp:',
        desc='Run an IOC that mocks an ai (analog input) record.')

    # Instantiate the IOC, assigning a prefix for the PV names.
    #prefix, *, macros = None, parent = None, name = None
    ioc = RecordMockingIOC(**ioc_options)
    ioc2 = MyRecordMockingIOC('SIM_BL1610-I10:uhv:')

    dbase = {}
    dbase.update(ioc.pvdb)
    dbase.update(ioc2.pvdb)

    print('PVs:', list(ioc.pvdb))
    print('PVs:', list(ioc2.pvdb))



    # ... but what you don't see are all of the analog input record fields
    #print('Fields of MBBO:', list(ioc.MBBO.fields.keys()))

    # Run IOC.
    #run(ioc.pvdb, **run_options)
    run(dbase, **run_options)