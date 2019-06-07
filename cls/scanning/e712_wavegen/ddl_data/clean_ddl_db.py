
import os
import h5py
import numpy as np
from cls.utils.log import get_module_logger
from cls.scanning.nexus.cls_nx_api import _dataset, _string_attr
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)
ddl_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ddl_data')

def open_ddl_database(filepath):
    '''
    open ddl database file from disk,
    h5py flags:
        r	Readonly, file must exist
        r+	Read/write, file must exist
        w	Create file, truncate if exists
        w- or x	Create file, fail if exists
        a	Read/write if exists, create otherwise (default)
    :return:
    '''

    nf = h5py.File(filepath, "a")
    nf.swmr_mode = True
    if (nf is None):
        _logger.error('error opening ddl database file [%s]' % filepath)
        return (nf)
    return (nf)

def clean_empty_ddl_tables(nf):

    for k in list(nf.keys()):
        data = nf[k][()]
        if np.prod(data) == 0.0:
            print('found a flat line ddl entry [%s] ' % k)
            print('deleted it')
            del nf[k]



if __name__ == '__main__':

    nf = open_ddl_database(ddl_data_dir + '.hdf5')
    clean_empty_ddl_tables(nf)
    nf.close()