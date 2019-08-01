
from PyQt5 import QtWidgets, QtCore
from PIL import Image


import simplejson as json
import h5py
from cls.utils.arrays import flip_data_upsdown
from cls.utils.images import array_to_image
from cls.utils.dirlist import dirlist, dirlist_withdirs
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.list_utils import sort_str_list

class StxmDataToTif(QtCore.QObject):

    def __init__(self, fname, is_tmp_file=False):
        QtCore.QObject.__init__(self)
        self.fname = fname
        if(is_tmp_file):
            self.process_tmp_file()
        else:
            self.data_dir, self.fprefix, self.suff  = get_file_path_as_parts(self.fname)
            self.nf = h5py.File(fname, "r+")
            #self.data_io = STXMDataIo(self.data_dir, self.fprefix, options={'def': 'nxstxm'})
            self.entries = self.nf.keys()
            self.num_images, self.rows, self.cols = self.nf['entry0']['counter0']['data'].shape
            self.data = self.nf['entry0']['counter0']['data'][()]
            fname = fname.replace('.hdf5','')
            for i in range(self.num_images):
                self.save_tif(fname + '_%03d.tif' % i, self.data[i])


    def process_tmp_file(self):
        skip_list = ['counter0', 'OSA_def','Zp_def']
        self.data_dir, self.fprefix, self.suff = get_file_path_as_parts(self.fname)
        self.nf = h5py.File(self.fname, "r+")
        self.report_file = open(self.fname + '.rprt', 'w')
        # self.data_io = STXMDataIo(self.data_dir, self.fprefix, options={'def': 'nxstxm'})
        img_idx_map = json.loads(bytes(self.nf['img_idx_map'][()]).decode('utf-8'))
        nf_keys = self.nf.keys()
        idx = 0
        img_keys = list(img_idx_map.keys())
        img_keys = sort_str_list(img_keys)
        for k in img_keys:
            e_idx = img_idx_map[k]['e_idx']
            entry = img_idx_map[k]['entry']
            sp_id = img_idx_map[k]['sp_id']
            sp_idx = img_idx_map[k]['pol_idx']
            idx_keys = ['DETECTORS', 'POSITIONERS', 'PVS', 'PRESSURES', 'TEMPERATURES']
            fname = self.fname.replace('.hdf5.tmp','')
            if(('idx%s' % k) in list(nf_keys)):

                data = self.nf['idx%s' % k]['DETECTORS']['counter0']['RBV'][()]
                ev = self.nf['idx%s' % k]['POSITIONERS']['ENERGY']['RBV'][()]
                self.report_file.write('idx%s: \n' % k)

                for ikey in idx_keys:
                    if(ikey in list(self.nf['idx%s' % k].keys())):
                        self.report_file.write('\t%s: \n' % (ikey))
                        for key in list(self.nf['idx%s' % k][ikey].keys()):
                            if(not key in skip_list):
                                print('getting [%s]' % key)
                                rbv = self.nf['idx%s' % k][ikey][key]['RBV'][()]
                                self.report_file.write('\t\t %s = %.4f\n' % (key, rbv))
                    else:
                        print('[%s] does not exist in tmp file' % ikey)


                # self.report_file.write('\tDETECTORS: \n')
                # for posner in list(self.nf['idx%s' % k]['DETECTORS'].keys()):
                #     rbv = self.nf['idx%s' % k]['DETECTORS'][posner]['RBV'][()]
                #     self.report_file.write('\t %s = %.4f\n' % (posner, rbv))
                #
                # self.report_file.write('\tPOSITIONERS: \n')
                # for key in list(self.nf['idx%s' % k]['POSITIONERS'].keys()):
                #     rbv = self.nf['idx%s' % k]['POSITIONERS'][key]['RBV'][()]
                #     self.report_file.write('\t %s = %.4f\n' % (key, rbv))
                #
                # self.report_file.write('\tPVS: \n')
                # for key in list(self.nf['idx%s' % k]['PVS'].keys()):
                #     rbv = self.nf['idx%s' % k]['PVS'][key]['RBV'][()]
                #     self.report_file.write('\t %s = %.4f\n' % (key, rbv))
                #
                # self.report_file.write('\tPRESSURES: \n')
                # for key in list(self.nf['idx%s' % k]['PRESSURES'].keys()):
                #     rbv = self.nf['idx%s' % k]['PRESSURES'][key]['RBV'][()]
                #     self.report_file.write('\t %s = %.4f\n' % (key, rbv))
                #
                # self.report_file.write('\tTEMPERATURES: \n')
                # for key in list(self.nf['idx%s' % k]['TEMPERATURES'].keys()):
                #     rbv = self.nf['idx%s' % k]['TEMPERATURES'][key]['RBV'][()]
                #     self.report_file.write('\t %s = %.4f\n' % (key, rbv))

                self.save_tif(fname + '_spid_%d' % sp_id + '_ev_%02f' % ev +'_%03d.tif' % int(k), data)
            else:
                print('no idx%s in the file' % k)

        self.report_file.close()

    def save_tif(self, fname, data):
        '''
        call PrintSTXMThumbnailWidget()
        :param sender:
        :return:
        '''
        size = 512
        _data = flip_data_upsdown(data)
        im = array_to_image(_data)
        im = im.resize([size, size], Image.NEAREST)  # Image.ANTIALIAS)  # resizes to 256x512 exactly
        im.save(fname)



if __name__ == '__main__':
    #StxmDataToTif(r'C:\tmp\data_to_tif\C190711109\C190711109.hdf5')
    StxmDataToTif(r'C:\tmp\aph_jul11\C190711022\C190711022.hdf5.tmp', is_tmp_file=True)
    #StxmDataToTif(r'S:\STXM-data\Cryo-STXM\2019\guest\0711\C190711009\C190711009.hdf5')
