import os
import numpy as np
import h5py
import hdfdict
import datetime


# d = {
#     'a': np.random.randn(10),
#     'b': [1, 2, 3],
#     'c': 'Hallo',
#     'd': np.array(['a', 'b']).astype('S'),
#     'e': True,
#     'f': (True, False),
# }
d = {'positioners':{'ENERGY': {'value':123.456, 'rrbv':123456, 'desc':'the energy positioner'}}, 'EPUOffset': {'value':3.4, 'rrbv':34, 'desc':'the EPU offset for the gap'}}
d['temperatures'] = {'TM123': {'value':56.78,'desc':'gatan rod temp'}, 'TM993': {'value':42, 'rrbv':42, 'desc':'tank temp'} }
d['time'] = '12:34:66'
fname = 'test_hdfdict.h5'


def test_dict_to_hdf():
    if os.path.isfile(fname):
        os.unlink(fname)
    hdfdict.dump(d, fname)
    hf = h5py.File(fname)
    res = hdfdict.load(hf)
    #assert np.all(d['a'] == res['a'])
    #assert np.all(d['b'] == res['b'])
    #assert np.all(d['c'] == res['c'])
    #assert d.keys() == res.keys()
    hf.close()


def test_dict_to_hdf_with_datetime():
    d = {
        'e': [datetime.datetime.now() for i in range(5)],
        'f': datetime.datetime.utcnow(),
        'g': [('Hello', 5), (6, 'No HDF but json'), {'foo': True}]
    }
    fname = 'test_hdfdict.h5'
    if os.path.isfile(fname):
        os.unlink(fname)
    hf = h5py.File(fname)
    hdfdict.dump(d, hf)
    res = hdfdict.load(hf)

    def equaldt(a, b):
        d = a - b
        return d.total_seconds() < 1e-3

    assert all([equaldt(a, b) for (a, b) in zip(d['e'], res['e'])])
    assert equaldt(d['f'], res['f'])
    assert d['g'][0][0] == 'Hello'
    assert d['g'][1][0] == 6
    assert list(d.keys()) == list(res.keys())
    hf.close()

    if os.path.isfile(fname):
        os.unlink(fname)


if __name__ == '__main__':
    test_dict_to_hdf()