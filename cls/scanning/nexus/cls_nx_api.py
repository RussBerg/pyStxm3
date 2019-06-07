import os
import numpy as np
import h5py
import hdfdict



def _group(nxgrp, name, nxdata_type):
    if (name == ''):
        return
    grp = nxgrp.create_group(name)
    _string_attr(grp, 'NX_class', nxdata_type)
    return (grp)


def _dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
    '''
    apply compression if the data is an array
    '''
    # grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)
    if (type(data) == np.ndarray):
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None, compression="gzip")
    else:
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)
    _string_attr(grp, 'NX_class', nxdata_type)
    _string_attr(grp, 'NX_units', nx_units)
    if ('doc' in list(dset.keys())):
        _string_attr(grp, 'doc', dset['doc'])
    return (grp)


def _string_attr(nxgrp, name, sdata):
    if (nxgrp is None):
        return

    #if (type(sdata) == str):
    #    nxgrp.attrs[name] = str(sdata, "utf-8")
    #else:
    #    nxgrp.attrs[name] = sdata
    nxgrp.attrs[name] = sdata


def _list_attr(nxgrp, name, lstdata):
    if (nxgrp is None):
        return
    if (name in list(nxgrp.attrs.keys())):
        nxgrp.attrs[name][()] = lstdata
    else:
        nxgrp.attrs[name] = lstdata


def check_dir_path(fname):
    import os
    import errno

    if not os.path.exists(os.path.dirname(fname)):
        try:
            os.makedirs(os.path.dirname(fname))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    return

def nx_open(fname, force_new=False, rd_only=False):
    check_dir_path(fname)
    if(force_new):
        flg = "w"
    elif(rd_only):
        flg = "r"
    else:
        flg = "a"

    nf = h5py.File(fname,  flg)
    nf.swmr_mode = True

    return(nf)

def nx_close(nf):
    nf.close()

def nx_put_dict(fname, dct):
    #if os.path.isfile(fname):
    #    os.unlink(fname)

    hdfdict.dump(dct, fname)

def nx_put(d, keys, item, overwrite=True):
    '''
    nx_put: is a function that accepts a . separated string that represents the levels of a dict.
     It makes it clean to access multi level dictionaries within code because predefined strings used as standard
     throughout the rest of the code.
    Example:
        dct_put(main, 'SCAN.DATA.DETECTORS', [])
        creates the following dictionary in the dict main, main['SCAN']['DATA']['DETECTORS']
        and assigns it to equal an empty list (in this case).

    Example: use defined dict strings:
        #define the strings in a separate shared module
        SCAN_DATA_DETECTORS = 'SCAN.DATA.DETECTORS'
        ...

        dct_put(main, SCAN_DATA_DETECTORS, [])


    :param d: dictionary to put the value passed into
    :type d: dictionary

    :param keys: a "." separated string used as keys for the dict
    :type keys: a "." separated string  such as 'DATA.SCAN1.POINTS'

    :param item: item to assign
    :type item: any valid python variable

    :param overwrite: If key already exists in dictionary allow it to be over written or not (True is default)
    :type overwrite: bool

    :return: Nothing
    '''
    try:
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                d[key] = {}
            nx_put(d[key], rest, item, overwrite)
        else:
            if (keys in list(d.keys())):
                # if the key exists only overwrite val if flag is True
                if (overwrite):
                    del d[keys]
                    d[keys] = item
            else:
                # key is new so create it
                d[keys] = item
    except KeyError:
        # raise
        return (None)


def nx_get(d, keys):
    '''
    nx_get: is a function that accepts a . separated string that represents the levels of a dict.
     It makes it clean to access multi level dictionaries within code because predefined strings used as standard
     throughout the rest of the code.
    Example:
        nx_get(main, 'SCAN.DATA.DETECTORS')
        returns the following from the dictionary main, main['SCAN']['DATA']['DETECTORS']

    Example: use defined dict strings:
        #define the strings in a separate shared module
        SCAN_DATA_DETECTORS = 'SCAN.DATA.DETECTORS'
        ...

        detector_lst = dct_get(main, SCAN_DATA_DETECTORS)


    :param d: dictionary to put the value passed into
    :type d: dictionary

    :param keys: a "." separated string used as keys for the dict
    :type keys: a "." separated string  such as 'DATA.SCAN1.POINTS'

    :return: The item located in the dictionary path given in the keys param
    '''
    try:
        if "." in keys:
            key, rest = keys.split(".", 1)
            return nx_get(d[key], rest)
        else:
            if (keys in list(d.keys())):
                return d[keys][()]
            else:
                return (None)
    except KeyError:
        # raise
        return (None)

if __name__ == '__main__':
    import datetime
    import time
    idx_dct = {}
    for i in range(5):
        idx_str = 'idx%d'%i
        idx_dct[idx_str] = {}
        idx_dct[idx_str]['positioners'] = {'ENERGY': {'value':123.456, 'rrbv':123456, 'desc':'the energy positioner'}, 'EPUOffset': {'value':3.4, 'rrbv':34, 'desc':'the EPU offset for the gap'} }
        idx_dct[idx_str]['temperatures'] = {'TM123': {'value':56.78,'desc':'gatan rod temp'}, 'TM993': {'value':42, 'rrbv':42, 'desc':'tank temp'} }
        idx_dct[idx_str]['time'] = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
        time.sleep(1.0)

    fname = r'C:\controls\git_sandbox\pyStxm\cls\zeromq\epics\test.hdf5'
    nx_put_dict(fname, idx_dct)

