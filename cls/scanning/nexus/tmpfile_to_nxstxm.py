
import re
import sys
import os
import json
import shutil
#import nxs
import numpy as np
import h5py
import pkg_resources
import nexpy

from cls.utils.json_threadsave import dict_to_json_string
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.fileUtils import get_file_path_as_parts

from cls.types.stxmTypes import scan_image_types, scan_types, IMAGE_PXP, IMAGE_LXL
from cls.utils.roi_utils import ActiveDataObj, get_first_sp_db_from_wdg_com, get_data_status_from_wdg_com
from cls.utils.time_utils import msec_to_sec
from cls.utils.roi_dict_defs import *
from cls.scanning.scan_cfg_utils import make_timestamp_now
from bcm.devices.device_names import *

from cls.scanning.nexus.nxstxm import make_positioners, make_temperatures, make_pressures, make_instrument, _data_as_1D_new, \
    make_instrument_new, make_data_section_new, make_control_section_new, make_pvs


import cls.scanning.nexus.nx_key_defs as nxkd
from cls.scanning.nexus.cls_nx_api import nx_get, nx_put, nx_open, nx_close, nx_put_dict, \
    _group, _dataset, _string_attr, _list_attr, _dataset
from cls.utils.json_utils import *

_logger = get_module_logger(__name__)


def get_idx_strs(keys_list):

    matching = [s for s in keys_list if "idx" in s]
    new_lst = []
    for m in matching:
        if(m.find('_idx') is -1):
            new_lst.append(m)
    return(new_lst)


def export_tmp_to_nxstxm(tmp_fname, dest_fname):

    #make a copy of the tmp file for debugging later
    shutil.copyfile(tmp_fname, tmp_fname + '.idx')

    tmp_nf = nx_open(tmp_fname,rd_only=True)

    #need to verify that the temp file has all the correct keys to complete the conversion before trying
    if(not check_for_valid_tmp_file(tmp_nf)):
        _logger.error('there is a problem with the temp file [%s], it is missing required keys' % tmp_fname)
        return

    #done make a file with the full destination name yet until it has been populated with data
    dest_nf = nx_open(dest_fname + '.final', force_new=True)
    #if(os.path.exists(dest_fname)):
    #    os.remove(dest_fname)

    _string_attr(dest_nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
    _string_attr(dest_nf, nxkd.NXD_H5PY_VER, h5py.__version__)
    _string_attr(dest_nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
    _string_attr(dest_nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
    _string_attr(dest_nf, nxkd.NXD_FILE_NAME, dest_fname)
    _string_attr(dest_nf, nxkd.NXD_FILE_TIME, make_timestamp_now())

    sp_rois = json_to_dict(tmp_nf['SP_ROIS'][()])
    numEpu = tmp_nf['numEpu'][()]
    numSpids = tmp_nf['numSpids'][()]
    numE = tmp_nf['numE'][()]

    img_idx_grp = json.loads(tmp_nf['img_idx_map'][()])

    make_entries(dest_nf, tmp_nf, sp_rois, numSpids, numE, numEpu, img_idx_grp)

    nx_close(tmp_nf)
    nx_close(dest_nf)

    #now set proper name
    if(os.path.exists(dest_fname)):
        _logger.debug('Warning: [%s] exists but it will be overwritten' % (dest_fname))
        os.remove(dest_fname)

    os.rename(dest_fname + '.final', dest_fname)
    _logger.debug('Export to [%s] completed' % dest_fname)
    os.remove(tmp_fname)
    #now remove debugging file
    os.remove(tmp_fname + '.idx')

def check_for_valid_tmp_file(tf):
    required_keys = ['CFG', 'DATA_DCT', 'SP_ROIS', 'definition', 'end_time', 'idx0', 'img_idx_map', 'numE', 'numEpu', 'numSpids', 'start_time', 'title', 'version']
    tf_keys = list(tf.keys())
    diff = list(set(required_keys).difference(tf_keys))
    if(len(diff) > 0):
        _logger.debug('check_for_valid_tmp_file: missing keys are:')
        print('check_for_valid_tmp_file: missing keys are:')
        for k in diff:
            _logger.debug('\t %s'% k)
            print('\t %s'% k)

    # if(len(diff) is 0):
    #     return(True)
    # else:
    #     return(False)
    return(True)


def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def compile_data(tmp_nf, sp_rois, numSpid, numE, numEpu, img_idx_grp):
    '''
    goal here is to take a temp file, a list of sp_roi's, the number of sp_roi's, number of polarizations and the img_idx map
    and produce an nxstxm file
    :param nf:
    :param idx:
    :param sp_rois_dct:
    :param img_idx_grp:
    :return:
    '''
    entry_idx = 0
    idx_cntr = 0

    sp_ids = list(sp_rois.keys())
    sp_ids.sort()

    dct = {}
    tmp_f_keys = list(tmp_nf.keys())
    tmp_f_keys.sort(key=natural_keys)
    tmp_f_idx_keys = get_idx_strs(tmp_f_keys)

    try:
        for idx_str in tmp_f_idx_keys:
            if((idx_str.find('idx') > -1) and (idx_str.find('map') is -1)):
                _logger.debug('compile_data: processing %s' % idx_str)
                if (idx_str not in list(tmp_nf.keys())):
                    _logger.error(
                        'Looks like this is an aborted file as [%s] does not exist in tmp file, leaving' % idx_str)
                    break
                if(str(idx_cntr) not in list(img_idx_grp.keys())):
                    _logger.error(
                        'Looks like this is an aborted file as [%s] does not exist in img_idx_grp.keys(), leaving' % str(idx_cntr))
                    break
                dets_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['DETECTORS'])
                psnr_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['POSITIONERS'])
                #{'e_idx': i, 'pol_idx': k, 'sp_idx': j,'entry': 'entry%d' % entry_idx}
                imgidx_str = str(idx_cntr)

                e_idx = img_idx_grp[imgidx_str]['e_idx']
                pol_idx = img_idx_grp[imgidx_str]['pol_idx']
                sp_idx = img_idx_grp[imgidx_str]['sp_idx']
                entry = img_idx_grp[imgidx_str]['entry']

                if(entry not in list(dct.keys())):
                    dct[entry] = {}
                #organize the data into dct[entry#][counter][pol id][spatial id][energy idx]
                for counter in list(dets_dct.keys()):
                    data = dets_dct[counter][RBV]

                    if(counter not in list(dct[entry].keys())):
                        dct[entry][counter] = {}

                    if (pol_idx not in list(dct[entry][counter].keys())):
                        dct[entry][counter][pol_idx] = {}

                    if (sp_idx not in list(dct[entry][counter][pol_idx].keys())):
                        if(type(data) is np.ndarray):
                            h, w = data.shape
                            dct[entry][counter][pol_idx][sp_idx] =  np.zeros((numE, h, w), dtype=np.float32)
                        else:
                            dct[entry][counter][pol_idx][sp_idx] = np.zeros(numE, dtype=np.float32)

                    #dct[entry][counter][pol_idx][sp_idx][e_idx] = dets_dct[counter][RBV]
                    dct[entry][counter][pol_idx][sp_idx][e_idx] = data


                for posner in list(psnr_dct.keys()):
                    if(posner not in list(dct[entry].keys())):
                        dct[entry][posner] = {}

                    if (pol_idx not in list(dct[entry][posner].keys())):
                        dct[entry][posner][pol_idx] = {}

                    if (sp_idx not in list(dct[entry][posner][pol_idx].keys())):
                        dct[entry][posner][pol_idx][sp_idx] = np.zeros(numE, dtype=np.float32)

                    #dct[entry][counter][pol_idx][sp_idx][e_idx] = dets_dct[counter][RBV]
                    dct[entry][posner][pol_idx][sp_idx][e_idx] = psnr_dct[posner][RBV]

                idx_cntr += 1
        _logger.debug('compile_data: Done')
        return(dct)
    except:
        _logger.error('There was a problem saving this file')
        print(sys.exc_info()[0])

def make_entries(nf, tmp_nf, sp_rois, numSpid, numE, numEpu, img_idx_grp):
    '''
    goal here is to take
    :param nf:
    :param idx:
    :param sp_rois_dct:
    :param img_idx_grp:
    :return:
    '''

    valid_detectors_lst = [DNM_DEFAULT_COUNTER]

    time_organized_data = compile_data(tmp_nf, sp_rois, numSpid, numE, numEpu, img_idx_grp)

    _logger.debug('Exporting data ... please wait')
    entry_idx = 0
    idx_cntr = 0

    sp_ids = list(sp_rois.keys())
    sp_ids.sort()


    for pol_idx in range(numEpu):
        for sp_id in sp_ids:
            if (('entry%d' % entry_idx) not in list(time_organized_data.keys())):
                _logger.warning('[%s] does not exist in the time_organized_data: scan most likely had been aborted: skipping' % ('entry%d' % entry_idx))
                continue

            _logger.debug('Exporting sp_id[%s]' % sp_id)
            sp_idx = sp_ids.index(sp_id)
            pol_pnt = sp_rois[sp_id][EV_ROIS][0]['EPU_POL_PNTS'][pol_idx]
            scan_type = nx_get(tmp_nf, ADO_CFG_SCAN_TYPE)
            data_dct = json.loads(nx_get(tmp_nf, 'DATA_DCT'))

            if(('entry%d' % entry_idx) in list(nf.keys())):
                entry_nxgrp = nf['entry%d' % entry_idx]
            else:
                entry_nxgrp = _group(nf, 'entry%d' % entry_idx, 'NXentry')

            _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
            _dataset(entry_nxgrp, 'start_time', tmp_nf['start_time'][()], 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'end_time', tmp_nf['end_time'][()], 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'definition', 'NXstxm', 'NX_CHAR')
            _dataset(entry_nxgrp, 'version', '1.0', 'NX_CHAR')


            ### debugging
            numX = sp_rois[sp_id]['X'][NPOINTS]
            numY = sp_rois[sp_id]['Y'][NPOINTS]
            numP = numE * numEpu * numX * numY
            _string_attr(entry_nxgrp, 'spid', sp_id)
            _string_attr(entry_nxgrp, 'pol', pol_pnt)
            _string_attr(entry_nxgrp, 'numX', numX)
            _string_attr(entry_nxgrp, 'numY', numY)
            _string_attr(entry_nxgrp, 'numP', numP)

            idx_str = 'idx%d' % idx_cntr
            if(idx_str not in list(tmp_nf.keys())):
                _logger.error('%s does not exist in tmp_nf file' % idx_str)
                del data_dct
                return

            dets_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['DETECTORS'])
            psnr_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['POSITIONERS'])
            temps_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['TEMPERATURES'])
            press_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['PRESSURES'])
            pvs_dct = convert_nxgrp_to_dict(tmp_nf[idx_str]['PVS'])
            dct_put(data_dct, 'DETECTORS', dets_dct)
            dct_put(data_dct, 'POSITIONERS', psnr_dct)
            dct_put(data_dct, 'TEMPERATURES', temps_dct)
            dct_put(data_dct, 'PRESSURES', press_dct)
            dct_put(data_dct, 'PVS', pvs_dct)
            dct_put(data_dct, '_NUM_X', numX)
            dct_put(data_dct, '_NUM_Y', numY)
            dct_put(data_dct, '_NUM_P', numP)
            dct_put(data_dct, '_NUM_EPU', numEpu)
            dct_put(data_dct, '_NUM_E', numE)
            dct_put(data_dct, 'TIME_ORGANIZED_DATA', time_organized_data)
            data_1d_dct = _data_as_1D_new(data_dct, entry_name='entry%d' % entry_idx, sp_id=sp_id, sp_idx=sp_idx, pol_idx=pol_idx)
            data_dct = dict(list(data_dct.items()) + list(data_1d_dct.items()))

            ################## COLLECTION GROUP ################################
            coll_nxgrp = _group(entry_nxgrp, 'collection', 'NXcollection')
            posners_dct = tmp_nf[idx_str]['POSITIONERS']
            make_positioners(coll_nxgrp, posners_dct)

            press_dct = tmp_nf[idx_str]['PRESSURES']
            make_pressures(coll_nxgrp, press_dct)

            tmps_dct = tmp_nf[idx_str]['TEMPERATURES']
            make_temperatures(coll_nxgrp, tmps_dct)

            pvs_dct = tmp_nf[idx_str]['PVS']
            make_pvs(coll_nxgrp, pvs_dct)

            js_str_wdg_com = nx_get(tmp_nf, ADO_CFG_WDG_COM)
            scan_grp = _group(coll_nxgrp, 'scan_request', 'NXscanDefinition')
            _dataset(scan_grp, 'scan_request', js_str_wdg_com, 'NXchar')

            ################ control #############################################
            #for detector in dets_dct.keys():
            make_control_section_new(entry_nxgrp, 'counter0', data_dct=data_dct, scan_type=scan_type, modify=False, dddata=None)

            ################## counter(s) ########################################
            # make the NXdata sections for all detectrs
            for detector in list(dets_dct.keys()):
                #here limit the NXdata sections to just the default detector for now = 'counter0'
                if(detector in valid_detectors_lst):
                    make_data_section_new(entry_nxgrp, detector, data_dct=data_dct, scan_type=scan_type, modify=False, dddata=None)

            ################## instrument ########################################
            # make the NXdata sections for all detectrs in the 'instrument' section
            for detector in list(dets_dct.keys()):
                if (detector in valid_detectors_lst):
                    make_instrument_new(entry_nxgrp, data_dct, counter=detector, scan_type=scan_type, pol_pnt=pol_pnt)

            #################### sample ##########################################
            sample_nxgrp = _group(entry_nxgrp, nxkd.NXD_SAMPLE, 'NXsample')
            if(DNM_GONI_THETA in list(posners_dct.keys())):
                rot_ang = posners_dct[DNM_GONI_THETA][RBV]
            else:
                rot_ang = -999999.0

            _dataset(sample_nxgrp, 'rotation_angle', rot_ang, 'NX_FLOAT')
            ######################################################################

            entry_idx += 1
            idx_cntr += 1

            del data_dct
            del data_1d_dct



def convert_nxgrp_to_dict(nxgrp):
    dct = {}

    for k in list(nxgrp.keys()):
        if(hasattr(nxgrp[k], 'keys')):
            dct[k] = convert_nxgrp_to_dict(nxgrp[k])
        else:
            dct[k] = nxgrp[k][()]
    return(dct)



if __name__ == '__main__':
    import os

    data_dir = r'S:\STXM-data\Cryo-STXM\2018\guest\0206\test'
    data_dir = r'S:\STXM-data\Cryo-STXM\2019\guest\0129\test'
    data_dir = r'S:\STXM-data\Cryo-STXM\2019\guest\0223'
    data_dir = r'C:\tmp\aph_jul11\C190711022'
    tmp_fname = os.path.join(data_dir,'C190711022.hdf5.tmp')
    dest_fname = os.path.join(data_dir, 'EXPORTED.hdf5')
    export_tmp_to_nxstxm(tmp_fname, dest_fname)


