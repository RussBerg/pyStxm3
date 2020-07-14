'''
Created on Jan 4, 2019

@author: bergr
'''
import numpy as np

from suitcase.nxstxm.device_names import *
from suitcase.nxstxm.roi_dict_defs import *
# from suitcase.nxstxm.nxstxm_utils import (make_signal, _dataset, _string_attr, _group, make_1d_array, \
#                                           get_nx_standard_epu_mode, get_nx_standard_epu_harmonic_new, translate_pol_id_to_stokes_vector, \
#                                           readin_base_classes, make_NXclass, remove_unused_NXsensor_fields)
from suitcase.nxstxm.nxstxm_utils import _dataset, _string_attr, make_1d_array
import suitcase.nxstxm.nx_key_defs as nxkd


def modify_generic_scan_ctrl_data_grps(parent, nxgrp, doc, scan_type):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    resize_data = False
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(rois[SPDB_X][POSITIONER])
    x_posnr_nm = parent.fix_posner_nm(rois[SPDB_X][POSITIONER])

    xnpoints = rois[SPDB_X][NPOINTS]
    ttlpnts = xnpoints
    uid = parent.get_current_uid()
    prim_data_lst = parent._data['primary'][x_src][uid]['data']
    if (len(prim_data_lst) < ttlpnts):
        resize_data = True
        # scan was aborted so use setpoint data here
        xdata = np.array(rois[SPDB_X]['SETPOINTS'], dtype=np.float32)
    else:
        # use actual data
        # xdata is teh first xnpoints
        xdata = np.array(parent._data['primary'][x_src][uid]['data'][0:xnpoints], dtype=np.float32)

    _dataset(nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')

    # this should be an array the same shape as the 'data' group in NXdata filled with the storagering current
    sr_data = np.array(parent._data['primary'][parent.get_devname(DNM_RING_CURRENT) + '_val'][uid]['data'], dtype=np.float32)
    if (resize_data):
        sr_data = np.resize(sr_data, (ttlpnts,))

    _dataset(nxgrp, 'data', sr_data, 'NX_NUMBER')

    modify_generic_scan_ctrl_str_attrs(parent, nxgrp, doc)



def modify_generic_scan_ctrl_str_attrs(parent, nxgrp, doc):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_posnr_nm = parent.fix_posner_nm(rois[SPDB_X][POSITIONER])

    _string_attr(nxgrp, 'axes', [x_posnr_nm])

def modify_generic_scan_nxdata_group(parent, data_nxgrp, doc, scan_type):
    '''

    :param entry_nxgrp:
    :param cntr_nm:
    :param doc:
    :param scan_type:
    :return:
    '''
    resize_data = False

    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(rois[SPDB_X][POSITIONER])
    x_posnr_nm = parent.fix_posner_nm(rois[SPDB_X][POSITIONER])

    xnpoints = rois[SPDB_X][NPOINTS]
    ttlpnts = xnpoints
    uid = parent.get_current_uid()
    prim_data_lst = parent._data['primary'][x_src][uid]['data']
    if (len(prim_data_lst) < ttlpnts):
        resize_data = True
        # scan was aborted so use setpoint data here
        xdata = np.array(rois[SPDB_X][SETPOINTS], dtype=np.float32)

    else:
        # use actual data
        # xdata is teh first xnpoints
        xdata = np.array(parent._data['primary'][x_src][uid]['data'][0:xnpoints], dtype=np.float32)

    _dataset(data_nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')

    _string_attr(data_nxgrp, 'axes', [x_posnr_nm])
    _string_attr(data_nxgrp, 'signal', 'data')

    det_nm = parent.get_primary_det_nm(doc['run_start'])

    # det_data = np.array(self._data['primary'][det_nm]['data'], dtype=np.float32).reshape((ynpoints, xnpoints))
    det_data = np.array(parent._data['primary'][det_nm][uid]['data'], dtype=np.float32)

    _dataset(data_nxgrp, 'data', det_data, 'NX_NUMBER')

def modify_generic_scan_instrument_group(parent, inst_nxgrp, doc, scan_type):
    '''

    :param nxgrp:
    :param doc:
    :param scan_type:
    :return:
    '''
    rois = parent.get_rois_from_current_md(doc['run_start'])
    dwell = parent._cur_scan_md[doc['run_start']]['dwell'] * 0.001
    det_nm = parent.get_primary_det_nm(doc['run_start'])
    scan_type = parent.get_stxm_scan_type(doc['run_start'])
    uid = parent.get_current_uid()
    ttl_pnts = rois[SPDB_X][NPOINTS] * rois[SPDB_Y][NPOINTS]

    det_data = np.array(parent._data['primary'][det_nm][uid]['data'])  # .reshape((ynpoints, xnpoints))
    parent.make_detector(inst_nxgrp, parent._primary_det_prefix, det_data, dwell, ttl_pnts, units='counts')

    sample_x_data = make_1d_array(ttl_pnts, parent.get_sample_x_data('start'))
    sample_y_data = make_1d_array(ttl_pnts, parent.get_sample_y_data('start'))
    parent.make_detector(inst_nxgrp, nxkd.SAMPLE_X, sample_x_data, dwell, ttl_pnts, units='um')
    parent.make_detector(inst_nxgrp, nxkd.SAMPLE_Y, sample_y_data, dwell, ttl_pnts, units='um')

    xnpoints = rois[SPDB_X][NPOINTS]
    ttl_pnts = rois[SPDB_X][NPOINTS]

    x_src = parent.get_devname(rois[SPDB_X][POSITIONER])
    x_posnr_nm = parent.fix_posner_nm(rois[SPDB_X][POSITIONER])

    # xdata is teh first xnpoints
    xdata = parent._data['primary'][x_src][uid]['data'][0:xnpoints]
    parent.make_detector(inst_nxgrp, x_posnr_nm, np.tile(xdata, xnpoints), dwell, ttl_pnts, units='um')
