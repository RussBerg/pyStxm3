
import os
from tifffile import imsave
import numpy as np
from PIL import Image
import scipy
from cls.utils.arrays import flip_data_upsdown
from cls.data_io.stxm_data_io import STXMDataIo
from cls.utils.images import array_to_image
fprefix = 'C190621104'
data_dir = r'S:\STXM-data\Cryo-STXM\2019\guest\0621'
data_io = STXMDataIo(data_dir, fprefix)
entry_dct = data_io.load()
ekey = list(entry_dct.keys())[0]
nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
data = nx_datas['counter0']['signal']

if(data.ndim is 3):
    data = data[0]

# #must normalize to 0->255
# data *= 255.0/data.max()
# #must be dtype uint8
# data = np.array(data, dtype=np.uint8)
# #must flip it upside down
# data = flip_data_upsdown(data)
# #turn array into image
# im = Image.fromarray(data, mode="L")
# #save it
# fstr = os.path.join('test.tif')
# im.save(fstr)

im = array_to_image(data)
#save it
#fstr = os.path.join('test.jpg')
fstr = os.path.join('test.tif')
im.save(fstr)
