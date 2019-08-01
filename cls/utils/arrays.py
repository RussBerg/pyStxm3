'''
Created on Jan 27, 2017

@author: bergr
'''
import numpy as np

def flip_data_upsdown(data):
    _data = np.flipud(data).copy()
    return(_data)

def resize_1d_array(a, b):
    bb = np.zeros(len(b))
    if len(a) < len(bb):
        c = bb.copy()
        c[:len(a)] += a
    else:
        c = a.copy()
        c[:len(bb)] += bb

    return(c)
