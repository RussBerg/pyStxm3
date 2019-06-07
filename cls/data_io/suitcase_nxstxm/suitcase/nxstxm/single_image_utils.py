
import numpy as np

from cls.utils.roi_dict_defs import *
from cls.types.stxmTypes import scan_types, single_entry_scans, multi_entry_scans, two_posner_scans, three_posner_scans
from bcm.devices.device_names import *
from suitcase.nxstxm.nxstxm_utils import (make_signal, _dataset, _string_attr, _group, make_1d_array, \
                                          get_nx_standard_epu_mode, get_nx_standard_epu_harmonic_new, translate_pol_id_to_stokes_vector, \
                                          readin_base_classes, make_NXclass, remove_unused_NXsensor_fields)

import suitcase.nxstxm.nx_key_defs as nxkd

MARK_DATA = False


#     parent.modify_single_image_ctrl_str_attrs(cntrl_nxgrp, doc)
#     parent.modify_single_image_ctrl_data_grps(cntrl_nxgrp, doc)

def modify_single_image_ctrl_data_grps(parent, nxgrp, doc, scan_type):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    resize_data = False
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(rois['X']['POSITIONER'])
    x_posnr_nm = parent.fix_posner_nm(rois['X']['POSITIONER'])
    # x_posnr_src = rois['X']['SRC']
    y_src = parent.get_devname(rois['Y']['POSITIONER'])
    y_posnr_nm = parent.fix_posner_nm(rois['Y']['POSITIONER'])
    # y_posnr_src = rois['Y']['SRC']

    xnpoints = int(rois['X']['NPOINTS'])
    ynpoints = int(rois['Y']['NPOINTS'])
    ttlpnts = xnpoints * ynpoints

    # uid = list(parent._cur_scan_md.keys())[0]
    # primary_det_nm = parent.get_primary_det_nm(uid)
    # prim_data_lst = parent._data['primary'][primary_det_nm]['data']
    # if (len(prim_data_lst) < ttlpnts):
    resize_data = True
    # scan was aborted so use setpoint data here
    xdata = np.array(rois['X']['SETPOINTS'], dtype=np.float32)
    ydata = np.array(rois['Y']['SETPOINTS'], dtype=np.float32)
    # else:
    #     # use actual data
    #     # xdata is teh first xnpoints
    #     xdata = np.array(parent._data['primary'][x_src]['data'][0:xnpoints], dtype=np.float32)
    #     # ydata is every ynpoint
    #     ydata = np.array(parent._data['primary'][y_src]['data'][0::ynpoints], dtype=np.float32)

    _dataset(nxgrp, y_posnr_nm, ydata, 'NX_FLOAT')
    _dataset(nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')

    # this should be an array the same shape as the 'data' group in NXdata filled with the storagering current
    #_sr_data = parent._data['baseline'][uid][parent.get_devname(DNM_RING_CURRENT) + '_val']['data']
    _sr_data = parent.get_baseline_all_data(parent.get_devname(DNM_RING_CURRENT) + '_val')
    sr_data = np.linspace(_sr_data[0], _sr_data[1], ttlpnts)
    #if (resize_data):
    #    sr_data = np.resize(sr_data, (ttlpnts,))
    _dataset(nxgrp, 'data', np.reshape(sr_data, (ynpoints, xnpoints)), 'NX_NUMBER')

    modify_single_image_ctrl_str_attrs(parent, nxgrp, doc)


def modify_single_image_ctrl_str_attrs(parent, nxgrp, doc):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_posnr_nm = parent.fix_posner_nm(rois['X']['POSITIONER'])
    y_posnr_nm = parent.fix_posner_nm(rois['Y']['POSITIONER'])

    _string_attr(nxgrp, 'axes', [y_posnr_nm, x_posnr_nm])

def modify_single_image_nxdata_group(parent, data_nxgrp, doc, scan_type):
    '''

    :param entry_nxgrp:
    :param cntr_nm:
    :param doc:
    :param scan_type:
    :return:
    '''
    resize_data = False

    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(rois['X']['POSITIONER'])
    x_posnr_nm = parent.fix_posner_nm(rois['X']['POSITIONER'])
    # x_posnr_src = rois['X']['SRC']
    y_src = parent.get_devname(rois['Y']['POSITIONER'])
    y_posnr_nm = parent.fix_posner_nm(rois['Y']['POSITIONER'])
    # y_posnr_src = rois['Y']['SRC']

    xnpoints = rois['X']['NPOINTS']
    ynpoints = rois['Y']['NPOINTS']
    ttlpnts = xnpoints * ynpoints
    #prim_data_lst = parent._data['primary'][x_src]['data']
    #uid = list(parent._cur_scan_md.keys())[0]
    uid = parent.get_current_uid()
    primary_det_nm = parent.get_primary_det_nm(uid)
    #prim_data_lst = parent._data['primary'][primary_det_nm]['data']
    prim_data_arr = np.array(parent._data['primary'][primary_det_nm][uid]['data'])
    rows, cols = prim_data_arr.shape

    if ((rows * cols) < ttlpnts):
        #scn had been aborted
        resize_data = True
        # scan was aborted so use setpoint data here
        xdata = np.array(rois['X']['SETPOINTS'], dtype=np.float32)
        ydata = np.array(rois['Y']['SETPOINTS'], dtype=np.float32)
    else:
        if(x_src not in parent._data['primary'].keys()):
            xdata = np.array(rois['X']['SETPOINTS'], dtype=np.float32)
            ydata = np.array(rois['Y']['SETPOINTS'], dtype=np.float32)
        else:
            # use actual data
            # xdata is teh first xnpoints
            xdata = np.array(parent._data['primary'][x_src][uid]['data'][0:xnpoints], dtype=np.float32)
            # ydata is every ynpoint
            ydata = np.array(parent._data['primary'][y_src][uid]['data'][0::ynpoints], dtype=np.float32)

    _dataset(data_nxgrp, y_posnr_nm, ydata, 'NX_FLOAT')
    _dataset(data_nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')

    _string_attr(data_nxgrp, 'axes', [y_posnr_nm, x_posnr_nm])
    _string_attr(data_nxgrp, 'signal', 'data')

    det_nm = parent.get_primary_det_nm(doc['run_start'])

    # three_d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS, scan_types.SAMPLE_IMAGE_STACK, \
    #                  scan_types.COARSE_IMAGE_SCAN, scan_types.COARSE_GONI_SCAN, scan_types.TOMOGRAPHY_SCAN]
    three_d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS, \
                     scan_types.COARSE_IMAGE_SCAN, scan_types.COARSE_GONI_SCAN, scan_types.TOMOGRAPHY_SCAN]

    if(scan_type in three_d_scans):
        # det_data = np.array(parent._data['primary'][det_nm]['data'], dtype=np.float32).reshape((1, ynpoints, xnpoints))
        det_data = np.array(parent._data['primary'][det_nm][uid]['data'], dtype=np.float32)
        if (resize_data):
            det_data = parent.fix_aborted_data(det_data, ttlpnts)

        det_data = np.reshape(det_data, (1, ynpoints, xnpoints))

        if(MARK_DATA):
            # put a black box in corner
            c = int(xnpoints / 3)
            r = int(xnpoints / 3)
            for n in range(r):
                det_data[0, n, 0:c] = 0

    else:
        # det_data = np.array(parent._data['primary'][det_nm]['data'], dtype=np.float32).reshape((ynpoints, xnpoints))
        det_data = np.array(parent._data['primary'][det_nm][uid]['data'], dtype=np.float32)

    _dataset(data_nxgrp, 'data', det_data, 'NX_NUMBER')


def modify_single_image_instrument_group(parent, inst_nxgrp, doc, scan_type):
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

    ttl_pnts = rois['X']['NPOINTS'] * rois['Y']['NPOINTS']
    uid = parent.get_current_uid()
    det_data = np.array(parent._data['primary'][det_nm][uid]['data'])  # .reshape((ynpoints, xnpoints))
    parent.make_detector(inst_nxgrp, parent._primary_det_prefix, det_data, dwell, ttl_pnts, units='counts')

    sample_x_data = make_1d_array(ttl_pnts, parent.get_sample_x_data('start'))
    sample_y_data = make_1d_array(ttl_pnts, parent.get_sample_y_data('start'))
    parent.make_detector(inst_nxgrp, 'sample_x', sample_x_data, dwell, ttl_pnts, units='um')
    parent.make_detector(inst_nxgrp, 'sample_y', sample_y_data, dwell, ttl_pnts, units='um')

    if (scan_type in two_posner_scans):
        xnpoints = rois['X']['NPOINTS']
        ynpoints = rois['Y']['NPOINTS']
        ttl_pnts = rois['X']['NPOINTS'] * rois['Y']['NPOINTS']

        x_src = parent.get_devname(rois['X']['POSITIONER'])
        x_posnr_nm = parent.fix_posner_nm(rois['X']['POSITIONER'])
        y_src = parent.get_devname(rois['Y']['POSITIONER'])
        y_posnr_nm = parent.fix_posner_nm(rois['Y']['POSITIONER'])

        # xdata is teh first xnpoints
        if(x_src not in parent._data['primary'].keys()):
            xdata = np.array(rois['X']['SETPOINTS'], dtype=np.float32)
            ydata = np.array(rois['Y']['SETPOINTS'], dtype=np.float32)
        else:
            xdata = parent._data['primary'][x_src]['data'][0:xnpoints]
            # ydata is every ynpoint
            ydata = parent._data['primary'][y_src]['data'][0::ynpoints]

        parent.make_detector(inst_nxgrp, y_posnr_nm, np.tile(ydata, ynpoints), dwell, ttl_pnts, units='um')
        parent.make_detector(inst_nxgrp, x_posnr_nm, np.tile(xdata, xnpoints), dwell, ttl_pnts, units='um')
