
import numpy as np

from cls.utils.roi_dict_defs import *
from cls.types.stxmTypes import scan_types, single_entry_scans, multi_entry_scans, two_posner_scans, three_posner_scans
from bcm.devices.device_names import *
from suitcase.nxstxm.nxstxm_utils import (make_signal, _dataset, _string_attr, _group, make_1d_array, \
                                          get_nx_standard_epu_mode, get_nx_standard_epu_harmonic_new, translate_pol_id_to_stokes_vector, \
                                          readin_base_classes, make_NXclass, remove_unused_NXsensor_fields)
from cls.utils.dict_utils import dct_get, dct_put
import suitcase.nxstxm.nx_key_defs as nxkd

MARK_DATA = False


#     parent.modify_focus_ctrl_str_attrs(cntrl_nxgrp, doc)
#     parent.modify_focus_ctrl_data_grps(cntrl_nxgrp, doc)

def modify_focus_ctrl_data_grps(parent, nxgrp, doc, scan_type):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    resize_data = False
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(dct_get(rois, SPDB_XPOSITIONER))
    x_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_XPOSITIONER))
    # x_posnr_src = rois['X']['SRC']
    y_src = parent.get_devname(dct_get(rois, SPDB_YPOSITIONER))
    y_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_YPOSITIONER))
    # y_posnr_src = rois['Y']['SRC']

    z_src = parent.get_devname(dct_get(rois, SPDB_ZPOSITIONER))
    z_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_ZPOSITIONER))

    xnpoints = dct_get(rois, SPDB_XNPOINTS)
    ynpoints = dct_get(rois, SPDB_YNPOINTS)
    znpoints = dct_get(rois, SPDB_ZNPOINTS)
    ttlpnts = xnpoints * znpoints
    if(x_src not in parent._data['primary'].keys()):
        #use the canned setpoints
        xdata = np.array(dct_get(rois, SPDB_XSETPOINTS), dtype=np.float32)
        ydata = np.array(dct_get(rois, SPDB_YSETPOINTS), dtype=np.float32)
        zdata = np.array(dct_get(rois, SPDB_ZSETPOINTS), dtype=np.float32)
    else:
        prim_data_lst = parent._data['primary'][x_src]['data']
        if (len(prim_data_lst) < ttlpnts):
            resize_data = True
            # scan was aborted so use setpoint data here
            xdata = np.array(dct_get(rois, SPDB_XSETPOINTS), dtype=np.float32)
            ydata = np.array(dct_get(rois, SPDB_YSETPOINTS), dtype=np.float32)
            zdata = np.array(dct_get(rois, SPDB_ZSETPOINTS), dtype=np.float32)
        else:
            # use actual data
            # xdata is teh first xnpoints
            xdata = np.array(parent._data['primary'][x_src]['data'][0:xnpoints], dtype=np.float32)
            # ydata is every ynpoint
            ydata = np.array(parent._data['primary'][y_src]['data'][0::znpoints], dtype=np.float32)
            zdata = np.array(parent._data['primary'][z_src]['data'][0::ynpoints], dtype=np.float32)

    _dataset(nxgrp, y_posnr_nm, ydata, 'NX_FLOAT')
    _dataset(nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')
    _dataset(nxgrp, z_posnr_nm, zdata, 'NX_FLOAT')

    # this should be an array the same shape as the 'data' group in NXdata filled with the storagering current
    ring_cur_signame = parent.get_devname(DNM_RING_CURRENT) + '_val'
    if(ring_cur_signame not in parent._data.keys()):
        #use the baseline start/stop values and create a sequence from start to stop
        strt, stp = parent._data['baseline'][ring_cur_signame]['data']
        sr_data = np.linspace(strt, stp, ttlpnts, endpoint=True)
    else:
        sr_data = np.array(parent._data['baseline'][ring_cur_signame]['data'], dtype=np.float32)
        if (resize_data):
            sr_data = np.resize(sr_data, (ttlpnts,))

    _dataset(nxgrp, 'data', np.reshape(sr_data, (znpoints, xnpoints)), 'NX_NUMBER')

    modify_focus_ctrl_str_attrs(parent, nxgrp, doc)


def modify_focus_ctrl_str_attrs(parent, nxgrp, doc):
    '''

    :param nxgrp:
    :param doc:
    :return:
    '''
    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_XPOSITIONER))
    y_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_YPOSITIONER))
    z_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_ZPOSITIONER))

    _string_attr(nxgrp, 'axes', [z_posnr_nm, y_posnr_nm, x_posnr_nm])

def modify_focus_nxdata_group(parent, data_nxgrp, doc, scan_type):
    '''

    :param entry_nxgrp:
    :param cntr_nm:
    :param doc:
    :param scan_type:
    :return:
    '''
    resize_data = False

    rois = parent.get_rois_from_current_md(doc['run_start'])
    x_src = parent.get_devname(dct_get(rois, SPDB_XPOSITIONER))
    x_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_XPOSITIONER))
    # x_posnr_src = rois['X']['SRC']
    y_src = parent.get_devname(dct_get(rois, SPDB_YPOSITIONER))
    y_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_YPOSITIONER))
    # y_posnr_src = rois['Y']['SRC']
    z_src = parent.get_devname(dct_get(rois, SPDB_ZPOSITIONER))
    z_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_ZPOSITIONER))

    xnpoints = dct_get(rois, SPDB_XNPOINTS)
    ynpoints = dct_get(rois, SPDB_YNPOINTS)
    znpoints = dct_get(rois, SPDB_ZNPOINTS)
    ttl_pnts = xnpoints * znpoints

    if (x_src not in parent._data['primary'].keys()):
        # use the canned setpoints
        xdata = np.array(dct_get(rois, SPDB_XSETPOINTS), dtype=np.float32)
        ydata = np.array(dct_get(rois, SPDB_YSETPOINTS), dtype=np.float32)
        zdata = np.array(dct_get(rois, SPDB_ZSETPOINTS), dtype=np.float32)
    else:
        prim_data_lst = parent._data['primary'][x_src]['data']
        if (len(prim_data_lst) < ttl_pnts):
            resize_data = True
            # scan was aborted so use setpoint data here
            xdata = np.array(dct_get(rois, SPDB_XSETPOINTS), dtype=np.float32)
            ydata = np.array(dct_get(rois, SPDB_YSETPOINTS), dtype=np.float32)
            zdata = np.array(dct_get(rois, SPDB_ZSETPOINTS), dtype=np.float32)
        else:
            # use actual data
            # xdata is teh first xnpoints
            xdata = np.array(parent._data['primary'][x_src]['data'][0:xnpoints], dtype=np.float32)
            # ydata is every ynpoint
            ydata = np.array(parent._data['primary'][y_src]['data'][0::znpoints], dtype=np.float32)
            zdata = np.array(parent._data['primary'][z_src]['data'][0::ynpoints], dtype=np.float32)

    _dataset(data_nxgrp, y_posnr_nm, ydata, 'NX_FLOAT')
    _dataset(data_nxgrp, x_posnr_nm, xdata, 'NX_FLOAT')
    _dataset(data_nxgrp, z_posnr_nm, zdata, 'NX_FLOAT')

    _string_attr(data_nxgrp, 'axes', [z_posnr_nm, y_posnr_nm, x_posnr_nm])
    _string_attr(data_nxgrp, 'signal', 'data')

    det_nm = parent.get_primary_det_nm(doc['run_start'])

    three_d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS, scan_types.SAMPLE_IMAGE_STACK, \
                     scan_types.COARSE_IMAGE_SCAN, scan_types.COARSE_GONI_SCAN, scan_types.TOMOGRAPHY_SCAN]
    if(scan_type in three_d_scans):
        # det_data = np.array(parent._data['primary'][det_nm]['data'], dtype=np.float32).reshape((1, ynpoints, xnpoints))
        det_data = parent._data['primary'][det_nm]['data']
        if(len(det_data) > ttl_pnts):
            det_data = np.array(parent._data['primary'][det_nm]['data'][0:znpoints][0:xnpoints], dtype=np.float32)
        elif(len(det_data) < ttl_pnts):
            print('modify_focus_nxdata_group: NEED TO PAD THE DATA')

        if (resize_data):
            det_data = parent.fix_aborted_data(det_data, ttl_pnts)

        det_data = np.reshape(det_data, (1, znpoints, xnpoints))

    else:
        # det_data = np.array(parent._data['primary'][det_nm]['data'], dtype=np.float32).reshape((ynpoints, xnpoints))
        det_data = np.array(parent._data['primary'][det_nm]['data'], dtype=np.float32)

    _dataset(data_nxgrp, 'data', det_data, 'NX_NUMBER')


def modify_focus_instrument_group(parent, inst_nxgrp, doc, scan_type):
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

    xnpoints = dct_get(rois, SPDB_XNPOINTS)
    ynpoints = dct_get(rois, SPDB_YNPOINTS)
    znpoints = dct_get(rois, SPDB_ZNPOINTS)
    ttl_pnts = xnpoints * znpoints

    det_data = np.array(parent._data['primary'][det_nm]['data'])  # .reshape((ynpoints, xnpoints))
    parent.make_detector(inst_nxgrp, parent._primary_det_prefix, det_data, dwell, ttl_pnts, units='counts')

    sample_x_data = make_1d_array(ttl_pnts, parent.get_sample_x_data('start'))
    sample_y_data = make_1d_array(ttl_pnts, parent.get_sample_y_data('start'))
    parent.make_detector(inst_nxgrp, 'sample_x', sample_x_data, dwell, ttl_pnts, units='um')
    parent.make_detector(inst_nxgrp, 'sample_y', sample_y_data, dwell, ttl_pnts, units='um')

    x_src = parent.get_devname(dct_get(rois, SPDB_XPOSITIONER))
    x_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_XPOSITIONER))
    y_src = parent.get_devname(dct_get(rois, SPDB_YPOSITIONER))
    y_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_YPOSITIONER))
    z_src = parent.get_devname(dct_get(rois, SPDB_ZPOSITIONER))
    z_posnr_nm = parent.fix_posner_nm(dct_get(rois, SPDB_ZPOSITIONER))

    # xdata is teh first xnpoints

    if (x_src not in parent._data['primary'].keys()):
        # use the canned setpoints
        xdata = np.array(dct_get(rois, SPDB_XSETPOINTS), dtype=np.float32)
        ydata = np.array(dct_get(rois, SPDB_YSETPOINTS), dtype=np.float32)
        zdata = np.array(dct_get(rois, SPDB_ZSETPOINTS), dtype=np.float32)
    else:

        xdata = parent._data['primary'][x_src]['data'][0:xnpoints]
        # ydata is every ynpoint
        ydata = parent._data['primary'][y_src]['data'][0::znpoints]
        zdata = parent._data['primary'][z_src]['data'][0::ynpoints]

    parent.make_detector(inst_nxgrp, y_posnr_nm, np.tile(ydata, ynpoints), dwell, ttl_pnts, units='um')
    parent.make_detector(inst_nxgrp, x_posnr_nm, np.tile(xdata, xnpoints), dwell, ttl_pnts, units='um')
    parent.make_detector(inst_nxgrp, z_posnr_nm, np.tile(zdata, znpoints), dwell, ttl_pnts, units='um')