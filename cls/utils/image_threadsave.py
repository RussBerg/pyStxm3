
import os
import threading
import numpy as np
from PIL import Image
import scipy
import copy

from cls.utils.dict_utils import dct_get
from cls.utils.arrays import flip_data_upsdown

class ThreadImageSave(threading.Thread):
    """Threaded file Save"""
    def __init__(self, data_dct, name='', verbose=False):
        threading.Thread.__init__(self, name=name)
        self.data_dct = copy.copy(data_dct)
        self.name = 'Image-SV.' + name
        self.verbose = verbose
        # jpeg thumbnail size
        self.size = (128, 128)
        # print 'ThreadImageSave: [%s] started' % self.name

    def run(self):
        import scipy
        if self.data_dct != None:
            fname = dct_get(self.data_dct, 'fpath') + '.jpg'
            data = dct_get(self.data_dct, 'data')
            if(data is None):
                return
            print(data.shape)
            _data = flip_data_upsdown(data)

            im = scipy.misc.toimage(_data, cmin=np.min(data), cmax=np.max(_data)).resize(self.size, Image.NEAREST)
            fstr = os.path.join(fname)
            im.save(fstr)
            if (self.verbose):
                print('ThreadJsonSave: [%s] saved [%s]' % (self.name, fname))



