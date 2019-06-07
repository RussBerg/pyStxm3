

import h5py
import numpy as np

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

    ddl_db = h5py.File(filepath, "a")
    ddl_db.swmr_mode = True
    if (ddl_db is None):
        print('error opening ddl database file [%s]' % filepath)
        return (None)
    return (ddl_db)


#def rms(x):
#    return np.sqrt(x.dot(x) / x.size)

def rms(x):
    _rms = np.sqrt(np.mean(x**2))
    return(_rms)



if __name__ == '__main__':

    fname = r'C:\controls\git_sandbox\pyStxm\cls\scanning\e712_wavegen\ddl_data\ddl_data.hdf5'
    hf = open_ddl_database(fname)
    print(hf)
    print('thr following timestamped DDL entries have a slew rate of 1000')
    for k in list(hf.keys()):

        if(k.find('SR:1000.0000D') > -1):
            e = hf[k]
            _rms = rms(e[()])
            print('DW: %.2f RNG: %.2f   %s' % (e.attrs['dwell'], e.attrs['rangeX'], e.attrs['TimeStamp']) + '  RMS: %.5f' % _rms)



