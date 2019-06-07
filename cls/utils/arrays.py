'''
Created on Jan 27, 2017

@author: bergr
'''
import numpy as np

def flip_data_upsdown(data):
    _data = np.flipud(data).copy()
    return(_data)

