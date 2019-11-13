import numpy as np
# from cls.utils.roi_dict_defs import *
# from cls.types.stxmTypes import scan_types
#
# def get_zp_dct():
#
#     zp1 = {'a1' :-4.840 ,'D' :100.0, 'CsD' :45.0, 'OZone': 60.0}
#     zp2 = {'a1' :-6.792 ,'D' :240.0, 'CsD' :90.0, 'OZone': 35.0}
#     zp3 = {'a1' :-7.767 ,'D' :240.0, 'CsD' :90.0, 'OZone': 40.0}
#     zp4 = {'a1' :-4.524 ,'D' :140.0, 'CsD' :60.0, 'OZone': 40.0}
#     zp5 = {'a1' :-4.859 ,'D' :240.0, 'CsD' :95.0, 'OZone': 25.0}
#     zp6 = {'a1': -4.857, 'D': 240.0, 'CsD': 95.0, 'OZone': 25.0}
#     zp7 = {'a1': -5.067, 'D': 250.0, 'CsD': 100.0, 'OZone': 25.0}
#     zps = [zp1, zp2, zp3, zp4, zp5, zp6, zp7]
#     return(zps)
#
#
# def make_standard_md(entry_num, dwell, x_roi, y_roi, zp_def, plan_name, scan_type, rev_lu_dct):
#     dct = {'entry_name': 'entry%d' % entry_num, 'scan_type': scan_type,
#           'rois': {SPDB_X: x_roi, SPDB_Y: y_roi},
#           'dwell': dwell,
#           'primary_det': 'line_det',
#           'zp_def': zp_def,
#           'wdg_com': '',
#           'plan_name': plan_name,
#            'rev_lu_dct': rev_lu_dct}
#     return(dct)


def dump_args(name, doc):
    print('received this: name=[%s] ' % (name))
    print(doc)

def get_detectors(doc):
    res = doc['detectors']
    return (res)

def get_positioners(doc):
    res = doc['motors']
    return (res)

def get_positioner_setpoints(doc, pos_num=1):
    res = []
    if(doc['plan_name'] == 'scan'):
        for i in range(pos_num):
            npoints = doc['plan_pattern_args']['num']
            start = doc['plan_pattern_args']['args'][1]
            stop = doc['plan_pattern_args']['args'][2]
            res.append(np.linspace(start, stop, npoints))
    else:
        res = doc['plan_pattern_args']['object']
    return (res)

def get_num_points(doc):
    res = doc['num_points']
    return (res)

def get_datakeys(doc):
    datakeys = list(doc['data'].keys())
    return (datakeys)

def get_det_shape_from_md(md, detname):
    '''
    gets teh detector shape from the metadata
    :param md:
    :param detname:
    :return:
    '''
    shape = []
    det_lst = md['dev_parms']
    for det_dct in det_lst:
        det_name = list(det_dct.keys())[0]
        if(detname == det_name):
            shape = det_dct[det_name]['shape']
    return(shape)


# def get_base_roi(name, positionerName, center, rng, npoints, stepSize=None, max_scan_range=None, enable=True,
#                  is_point=False, src=None):
#     """ define a base Region of Interest def that is passed around
#     'center':
#     'range':
#     'npoints':
#     'stepSize':
#     """
#     roi_def = {}
#     roi_def[NAME] = name
#     roi_def[ID] = BASE_ROI
#     roi_def[ID_VAL] = -1
#     roi_def[CENTER] = center
#     roi_def[RANGE] = rng
#     roi_def[NPOINTS] = int(npoints)
#     roi_def[ENABLED] = enable
#     roi_def[IS_POINT] = is_point
#     # the following specifies an offset to the START and STOP values
#     # allowing the user to apply a correction if need be, this was added
#     # for zoneplate scanning where the Goniometer will need to be corrected as the
#     # sample rotates to account for mechanical misalignment
#     roi_def[OFFSET] = 0.0
#
#     if (rng == None):
#         roi_def[ROI_STEP] = None
#         roi_def[START] = center
#         roi_def[STOP] = center
#     elif (rng == 0.0):
#         roi_def[ROI_STEP] = 0
#         roi_def[START] = center
#         roi_def[STOP] = center
#     else:
#         roi_def[ROI_STEP] = rng / npoints
#         roi_def[START] = center - (.5 * rng)
#         roi_def[STOP] = center + (.5 * rng)
#
#     if ((roi_def[START] is not None) and (roi_def[STOP] is not None)):
#         # make sure always left to right is less to more
#         if (roi_def[START] > roi_def[STOP]):
#             t = roi_def[STOP]
#             roi_def[STOP] = roi_def[START]
#             roi_def[START] = t
#
#         determine_setpoints(roi_def, stepSize)
#
#     roi_def[POSITIONER] = positionerName
#     roi_def[SRC] = src
#     roi_def[TOP_LEVEL] = False
#     roi_def[DATA_LEVEL] = False
#     if ((rng or max_scan_range) is None):
#         # skip
#         roi_def[SCAN_RES] = None
#     else:
#         roi_def[SCAN_RES] = 'COARSE'
#
#     return (roi_def)
#
#
# def determine_setpoints(roi_def, stepSize=None):
#     if (roi_def[NPOINTS] == 1):
#         roi_def[SETPOINTS] = np.linspace(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET],
#                                          roi_def[NPOINTS], endpoint=False, retstep=False)
#         roi_def[ROI_STEP] = 0.0
#     elif ((roi_def[RANGE] == 0) and (not roi_def[IS_POINT])):
#         roi_def[SETPOINTS] = np.linspace(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET],
#                                          roi_def[NPOINTS], endpoint=False, retstep=False)
#
#     elif ((roi_def[START] == None) or (roi_def[NPOINTS] == 0)):
#         roi_def[SETPOINTS] = []
#     else:
#         if (stepSize):
#             # NOTE this produces NPOINTS + 1 points
#             # use arange
#             roi_def[ROI_STEP] = stepSize
#             roi_def[SETPOINTS] = np.arange(roi_def[START] + roi_def[OFFSET], roi_def[STOP] + roi_def[OFFSET] + stepSize,
#                                            stepSize)
#         else:
#             roi_def[SETPOINTS], roi_def[ROI_STEP] = np.linspace(roi_def[START] + roi_def[OFFSET],
#                                                                 roi_def[STOP] + roi_def[OFFSET], roi_def[NPOINTS],
#                                                                 endpoint=True, retstep=True)
