'''
Created on Mar 7, 2019

@author: bergr
'''
# !/usr/bin/python
import xml.etree.ElementTree as ET
import glob
import os
import re
import numpy as np

import pkg_resources

from suitcase.nxstxm.utils import get_module_logger
import suitcase.nxstxm.nx_key_defs as nxkd

_logger = get_module_logger(__name__)

def readin_base_classes(desired_class=None):
    clss = get_classes('base_classes', desired_class)
    return (clss)


def readin_application_classes(desired_class=None):
    clss = get_classes('applications', desired_class)
    return (clss)


def readin_contributed_definition_classes(desired_class=None):
    clss = get_classes('contributed_definitions', desired_class)
    return (clss)


def get_classes(class_dir, desired_class=None):
    '''
    read the nexpy classes xml files and turn them into dicts, and return the desired class dict
    :param class_dir:
    :param desired_class:
    :return:
    '''
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/%s' % class_dir)
    nxdl_files = list(map(os.path.basename, glob.glob(os.path.join(base_class_path, '*.nxdl.xml'))))
    pattern = re.compile(r'[\t\n ]+')
    nxclasses = {}

    if (desired_class is not None):
        fname = desired_class + '.nxdl.xml'
        if (fname in nxdl_files):
            nxdl_files = [fname]

    for nxdl_file in nxdl_files:
        class_name = nxdl_file.split('.')[0]
        xml_root = ET.parse(os.path.join(base_class_path, nxdl_file)).getroot()
        class_doc = ''
        class_groups = {}
        class_fields = {}
        group_fields = {}
        for child in xml_root:
            name = dtype = units = doc = ''
            if child.tag.endswith('doc'):
                try:
                    class_doc = re.sub(pattern, ' ', child.text).strip()
                except TypeError:
                    pass
            if child.tag.endswith('field'):
                try:
                    name = child.attrib['name']
                    dtype = child.attrib['type']
                    units = child.attrib['units']
                except KeyError:
                    pass
                for element in child:
                    if element.tag.endswith('doc'):
                        try:
                            doc = re.sub(pattern, ' ', element.text).strip()
                        except TypeError:
                            pass
                # class_fields[name] = (dtype, units, doc)
                class_fields[name] = {'type': dtype, 'units': units, 'doc': doc}
            elif child.tag.endswith('group'):
                #
                gdoc = ''
                try:
                    dtype = child.attrib['type']
                    name = child.attrib['name']

                except KeyError:
                    pass

                for element in child:
                    if ('type' in list(element.attrib.keys())):
                        etype = element.attrib['type']
                    else:
                        etype = dtype
                    if element.tag.endswith('group'):
                        class_groups[etype] = get_group(etype, element)

                    if element.tag.endswith('doc'):
                        try:
                            gdoc = re.sub(pattern, ' ', element.text).strip()
                        except TypeError:
                            pass
                    if element.tag.endswith('field'):
                        fdoc = ''
                        for el in element:
                            if el.tag.endswith('doc'):
                                try:
                                    fdoc = re.sub(pattern, ' ', el.text).strip()
                                except TypeError:
                                    pass
                        try:
                            fname = ''
                            fdtype = ''
                            funits = ''
                            if ('name' in list(element.attrib.keys())):
                                fname = element.attrib['name']
                            if ('type' in list(element.attrib.keys())):
                                fdtype = element.attrib['type']
                            if ('units' in list(element.attrib.keys())):
                                funits = element.attrib['units']
                            group_fields[fname] = {'name': fname, 'type': fdtype, 'units': funits, 'doc': fdoc}

                        except KeyError:
                            pass

                class_groups[name] = {'name': name, 'doc': gdoc, 'type': dtype, 'fields': group_fields}

            nxclasses[class_name] = {'doc': class_doc, 'fields': class_fields, 'groups': class_groups}
            group_fields = {}
    return (nxclasses)


def get_fields(field):
    fields = {}
    for k in list(field.attrib.keys()):
        fields[k] = field.attrib[k]
    return (fields)


def get_group(class_name, root_element):
    pattern = re.compile(r'[\t\n ]+')
    nxclasses = {}
    class_doc = ''
    class_groups = {}
    class_fields = {}
    group_fields = {}
    fields = {}
    for child in root_element:
        name = dtype = units = doc = ''
        if child.tag.endswith('doc'):
            try:
                class_doc = re.sub(pattern, ' ', child.text).strip()
            except TypeError:
                pass
        group_fields[class_name] = {}
        group_fields[class_name]['doc'] = class_doc
        if child.tag.endswith('field'):
            group_fields[class_name] = get_fields(child)

        elif child.tag.endswith('group'):
            if (len(child.getchildren()) > 0):
                dtype = child.attrib['type']
                if ('name' in list(child.attrib.keys())):
                    name = child.attrib['name']
                else:
                    name = dtype
                group_fields[name] = get_group(name, child)
                # group_fields[dtype] = get_nexpy_classes('group', child)
                # classes = get_nexpy_classes('group', child)
            try:
                dtype = child.attrib['type']
                name = child.attrib['name']
            except KeyError:
                pass
            for element in child:
                if element.tag.endswith('doc'):
                    try:
                        doc = re.sub(pattern, ' ', element.text).strip()
                    except TypeError:
                        pass
            class_groups[dtype] = (doc, group_fields)

        # nxclasses[dtype] = (class_doc, class_fields, class_groups)
        # nxclasses[dtype] = group_fields
    return (group_fields)


def make_NXclass(nf, name, nxclass_name, nxclass_dct, base_grp):
    """ takes the:
        name: desired name to read as the section header in the nexus file
        nxclass_name: name of NX class ex: NXsource
        nxclass_dct: the dict returned from parsing it with ex: readin_base_classes('NXsource')
        base_grp: the hdf5 group that this class will be a child of

        and reads in the entire nxdl.xml file for the class and returns an hdf5
        representation

        [* NOTE: this works well for not nested xml but varies success on nested ones]

    """
    srcgrp = _group(base_grp, name, nxclass_name)
    groups = {}
    fields = {}
    parentgrp = srcgrp
    # walk groups
    for i in list(nxclass_dct['groups'].keys()):
        nxgrp = _group(srcgrp, nxclass_dct['groups'][i]['name'], nxclass_dct['groups'][i]['type'])
        # groups have 'doc' 'type' 'name'
        if (parentgrp is None):
            parentgrp = srcgrp

        _string_attr(nxgrp, 'doc', nxclass_dct['groups'][i]['doc'])
        groups[nxclass_dct['groups'][i]['name']] = nxgrp

        grp = nxclass_dct['groups'][i]
        if (type(grp) == dict):
            if ('fields' in list(grp.keys())):
                make_data(nxgrp, grp['fields'])

    # walk fields
    for i in list(nxclass_dct['fields'].keys()):
        # fields have ['units', 'doc', 'type'
        if ('doc' in list(nxclass_dct['fields'].keys())):
            _string_attr(parentgrp, 'doc', nxclass_dct['fields'][i]['doc'])
        name = None
        dtype = None
        units = None

        name = i
        if ('type' in list(nxclass_dct['fields'][i].keys())):
            dtype = nxclass_dct['fields'][i]['type']
        if ('units' in list(nxclass_dct['fields'][i].keys())):
            units = nxclass_dct['fields'][i]['units']

        if ((name is not None) and (dtype != '') and (units != '')):
            _dataset(parentgrp, name, 0.0, nxclass_dct['fields'][name]['type'], nxclass_dct['fields'][name]['units'],
                     nxclass_dct['fields'][name])
        elif ((name is not None) and (dtype != '')):
            _dataset(parentgrp, name, 0.0, nxclass_dct['fields'][name]['type'], nxclass_dct['fields'][name])
        else:
            _dataset(parentgrp, name, '', 'NX_CHAR')

    return (srcgrp)

def print_node(root):
    if root.childNodes:
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                # print node.tagName,"has value:",  node.nodeValue, "and is child of:", node.parentNode.tagName
                if ((node.tagName is None) or (node.tagName is None) or (node.tagName is None)):
                    print('[', node.tagName, ']', "has value: [", node.nodeValue, ']', "and is child of: [",
                          node.parentNode.tagName, ']')
                else:
                    print('[%s] has value = [%s] and is child of: [%s]' % (
                    str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper()))
                    print('[%s] has value = [%s] and is child of: [%s]' % (
                    str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper()))
                    for k in list(node.attributes.keys()):
                        print('\t\t[%s] = %s' % (k, node.attributes[k].value))

                print_node(node)

            if (node.nodeType == node.TEXT_NODE):
                print('text node value = ', node.nodeValue)
                # if((node.tagName is None) or (node.tagName is None) or (node.tagName is None)):
                #    print '[',node.tagName,']',"has value: [", node.nodeValue,']', "and is child of: [", node.parentNode.tagName, ']'
                # else:
                #    print '[%s] has value = [%s] and is child of: [%s]' % (str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper())
                # print_node(node)

            else:
                print('node [%s] is of type %d' % (node, node.nodeType))


def walk_xml():
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
    fname = 'NXstxm.nxdl.xml'

    tree = ET.parse(os.path.join(base_class_path, fname))
    # tree = ET.fromstring("""...""")
    for elt in tree.iter():
        if (elt.text is not None):
            print("%s: '%s'" % (elt.tag, elt.text.strip()))



def make_data(nxgrp, nxdata_dct):
    """
     dct contains: ['doc', 'type', 'name']
    """

    for k in list(nxdata_dct.keys()):
        grp = _dataset(nxgrp, k, nxdata_dct[k]['name'], nxdata_dct[k]['type'], maxshape=(None))
        _string_attr(grp, 'doc', nxdata_dct[k]['doc'])


def nxclass_dict_to_nx(base_grp, name, nxclass_name, nxclass_dct):
    """ takes the:
        name: desired name to read as the section header in the nexus file
        nxclass_name: name of NX class ex: NXsource
        nxclass_dct: the dict returned from parsing it with ex: readin_base_classes('NXsource')
        base_grp: the hdf5 group that this class will be a child of

        and reads in the entire nxdl.xml file for the class and returns an hdf5
        representation

        [* NOTE: this works well for not nested xml but varies success on nested ones]

    """
    srcgrp = _group(base_grp, name, nxclass_name)
    for k in list(nxclass_dct.keys()):
        _dataset(base_grp, k, nxclass_dct[k]['val'], nxclass_dct[k]['type'])


def translate_pol_id_to_stokes_vector(pol_id):
    if (pol_id is 0):
        return ([0.0, 0.0, 0.0])
    elif (pol_id is 1):
        return ([0.0, 1.0, 0.0])
    elif (pol_id is 2):
        return ([0.0, 0.0, 1.0])
    elif (pol_id is 3):
        return ([1.0, 0.0, 0.0])
    elif (pol_id is 4):
        return ([1.0, 1.0, 0.0])
    elif (pol_id is 5):
        return ([1.0, 0.0, 1.0])
    elif (pol_id is 6):
        return ([0.0, 1.0, 1.0])
    elif (pol_id is 7):
        return ([1.0, 1.0, 1.0])
    else:
        return ([-1.0, -1.0, -1.0])

def make_string_data(nf, name, sdata, size=None):
    if (size):
        num_chars = size
    else:
        num_chars = len(sdata)
    # nf.makedata(name,'char',[num_chars])
    nf.create_dataset(name=name, data=sdata)
    # nf.opendata(name)
    # nf.putdata(sdata)
    # nf.closedata()


def _string_attr(nxgrp, name, sdata):
    if (nxgrp is None):
        return

    # if (type(sdata) == str):
    #     nxgrp.attrs[name] = str(sdata, "utf-8")
    # else:
    #    nxgrp.attrs[name] = sdata
    nxgrp.attrs[name] = sdata


def _list_attr(nxgrp, name, lstdata):
    if (nxgrp is None):
        return
    if (name in list(nxgrp.attrs.keys())):
        nxgrp.attrs[name][()] = lstdata
    else:
        nxgrp.attrs[name] = lstdata


def make_float_attr(nxgrp, name, fdata):
    if (name in list(nxgrp.attrs.keys())):
        nxgrp.attrs[name][()] = fdata
    else:
        nxgrp.attrs[name] = fdata


def make_class_type_attr(nxgrp, type):
    nxgrp._string_attr('NX_class', type)


def make_date_time(nf, name, s, size=None):
    if (size):
        num_chars = size
    else:
        num_chars = len(s)
    nf.makedata(name, 'char', [num_chars])
    nf.opendata(name)
    nf.putdata(s)
    nf.closedata()


def _group(nxgrp, name, nxdata_type):
    if (name == ''):
        return
    grp = nxgrp.create_group(name)
    _string_attr(grp, 'NX_class', nxdata_type)
    return (grp)


def _dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
    '''
    apply compression if the data is an array
    '''
    # grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)
    if (type(data) == np.ndarray):
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None, compression="gzip")
    else:
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)
    _string_attr(grp, 'NX_class', nxdata_type)
    if (type(nx_units) is dict):
        _string_attr(grp, 'NX_units', nx_units['units'])
    else:
        _string_attr(grp, 'NX_units', nx_units)
    if ('doc' in list(dset.keys())):
        _string_attr(grp, 'doc', dset['doc'])
    return (grp)


def make_detector(nf, name, data=None, data_dct={}, count_time=[], unit='counts', modify=False):
    if (not modify):
        grp = _group(nf, name, 'NXdetector')

        if (data is None):
            _dataset(grp, nxkd.NXD_DATA, np.zeros(200, dtype=np.float32), 'NX_FLOAT')
        else:
            _dataset(grp, nxkd.NXD_DATA, data, 'NX_FLOAT')

        _dataset(grp, 'count_time', count_time, 'NX_FLOAT')
        _dataset(grp, 'unit', unit, 'NX_CHAR')
    else:
        grp = nf[name]
        del grp[nxkd.NXD_DATA]
        # grp[nxkd.NXD_DATA][()] = data
        _dataset(grp, nxkd.NXD_DATA, data, 'NX_FLOAT')


def get_nx_standard_epu_mode(mode):
    """
    Define polarization as either 
        cir. right, point of view of source, 
        cir. left, point of view of source, or 
        linear. If the linear case is selected, there is an additional value in degrees for 
            the angle (number is meaningless if circular is chosen, or may not be filled in, I do not know).
    """
    linear_lst = [2, 3, 4, 5]
    if (mode == 0):
        return (False, 'cir. left, point of view of source')
    elif (mode == 1):
        return (False, 'cir. right, point of view of source')
    elif (mode in linear_lst):
        return (True, 'linear')
    else:
        return (False, 'UNKNOWN')

def get_nx_standard_epu_harmonic_new(harm):
    """
    """
    ret = None
    if (harm == 0):
        ret = 1
    elif (harm == 1):
        ret = 3
    elif (harm == 2):
        ret = 5
    elif (harm == 3):
        ret = 7
    elif (harm == 4):
        ret = 9
    else:
        ret = 0
    return (ret)

def remove_unused_NXsensor_fields(nxgrp):
    # remove unused NXsensor fields
    del nxgrp['attached_to']
    del nxgrp['external_field_brief']
    del nxgrp['external_field_full']
    del nxgrp['geometry']
    del nxgrp['high_trip_value']
    del nxgrp['low_trip_value']
    del nxgrp['model']
    del nxgrp['measurement']
    del nxgrp['value_deriv1']
    del nxgrp['value_deriv1_log']
    del nxgrp['value_deriv2']
    del nxgrp['value_deriv2_log']
    del nxgrp['value_log']


def make_1d_array(numpts, val):
    arr = np.ones(int(numpts), dtype=np.float32)
    if (isinstance(val, list)):
        num_vals = len(val)
        if (num_vals == numpts):
            arr[:] = val
        else:
            mults = int(numpts / num_vals)
            arr[:] = np.tile(val, (mults))
    else:
        if (isinstance(val, float)):
            arr[:] = val

    return (arr)



def convert(data):
    import collections

    if isinstance(data, str):
        return (str(data, 'utf8'))
    elif isinstance(data, collections.Mapping):
        return dict(list(map(convert, iter(data.items()))))
    elif isinstance(data, collections.Iterable):
        return type(data)(list(map(convert, data)))
    else:
        return data


def convert_to_non_unicode(data):
    import collections

    if isinstance(data, str):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(list(map(convert, iter(data.items()))))
    elif isinstance(data, collections.Iterable):
        return type(data)(list(map(convert, data)))
    else:
        return data


def run_nexus_class_test(_class=None):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    bc = readin_base_classes()
    ac = readin_application_classes(desired_class='NXstxm')
    (stxm_doc, stxm_flds, stxm_grps) = ac['NXstxm']
    # print 'BASE CLASSES'
    # pp.pprint(bc)

    print('APPLICATION CLASSES')
    pp.pprint(ac)

    # create_NXstxm_file("positioner.hdf5")
    return (bc, ac)


def dump_xml_structure():
    dom = md.parse(r'C:\controls\nexus-definitions-development\dist\applications\NXstxm.nxdl.xml')
    root = dom.documentElement
    print_node(root)

def nx_put(d, keys, item, overwrite=True):
    '''
    nx_put: is a function that accepts a . separated string that represents the levels of a dict.
     It makes it clean to access multi level dictionaries within code because predefined strings used as standard
     throughout the rest of the code.
    Example:
        dct_put(main, 'SCAN.DATA.DETECTORS', [])
        creates the following dictionary in the dict main, main['SCAN']['DATA']['DETECTORS']
        and assigns it to equal an empty list (in this case).

    Example: use defined dict strings:
        #define the strings in a separate shared module
        SCAN_DATA_DETECTORS = 'SCAN.DATA.DETECTORS'
        ...

        dct_put(main, SCAN_DATA_DETECTORS, [])


    :param d: dictionary to put the value passed into
    :type d: dictionary

    :param keys: a "." separated string used as keys for the dict
    :type keys: a "." separated string  such as 'DATA.SCAN1.POINTS'

    :param item: item to assign
    :type item: any valid python variable

    :param overwrite: If key already exists in dictionary allow it to be over written or not (True is default)
    :type overwrite: bool

    :return: Nothing
    '''
    try:
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                d[key] = {}
            nx_put(d[key], rest, item, overwrite)
        else:
            if (keys in list(d.keys())):
                # if the key exists only overwrite val if flag is True
                if (overwrite):
                    del d[keys]
                    d[keys] = item
            else:
                # key is new so create it
                d[keys] = item
    except KeyError:
        # raise
        return (None)

if __name__ == '__main__':
    import xml.dom.minidom as  md
    import time
    import datetime
    import json
    from bcm.utils.xim2array import loadXim2Array
    import pprint
    import hdf5storage
    # from datetime import time, tzinfo, datetime, timedelta
    from sm.stxm_control.stxm_utils.nexus.nxstxm_validate.nxstxm_validate import validate


    class CST(datetime.tzinfo):
        def utcoffset(self, dt):
            return (datetime.timedelta(hours=-6))

        def dst(self, dt):
            return (datetime.timedelta(0))

        def tzname(self, dt):
            return ("Saskatchewan Canada")


    #test_saving_with_validation()
    # time_trial_update_speed()
    # time_open_updateall_close()
#    data_dct = load_single_entry_from_NXstxm_file(hdf5_fname, only_roi_and_data=False)
#     nf = h5py.File(hdf5_fname,  "r+")
#     e_lst = get_entry_names(nf)
#     #print e_lst
#     for entry in e_lst:
#         c_lst = get_counter_names(nf[entry])
#         #print c_lst
#     nf.close()    
#     data = np.array(ado_obj[nxkd.NXD_DATA]['POINTS'])    
#     update_data(hdf5_fname, e_lst[0], data, counter=c_lst[0])    
# create_standard_NXstxm_file(fname, scan_type, data_dct={'ID':None}, intermediate_file=False)
# create_standard_NXstxm_file(hdf5_fname, scan_types.SAMPLE_IMAGE, data_dct=ado_obj, intermediate_file=False)
# dct_put(data_dct, ADO_CFG_DATA_DIR, r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/')
# dct_put(data_dct, ADO_CFG_DATA_FILE_NAME, r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/C160519030.hdf5')
# spatial_roi_id = dct_get(data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX)
# create_NXstxm_file(r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/C160519099.hdf5', scan_types.SAMPLE_LINE_SPECTRUM, data_dct=data_dct, intermediate_file=False)


# try_this()
# walk_xml()
#     dtype = ['sample point spectrum', 'sample line spectrum', 'sample image' ,\
#             'sample image stack' ,'sample focus', 'osa image', 'osa focus', 'detector image',\
#             'generic scan']
#     
# #     pp = pprint.PrettyPrinter(indent=1)
#      bc_dct = nx_classes_to_dct('base_classes')
# #     print bc_dct
#     #dct = convert(make_NXstxm_dict())
#     #hdf5storage.write(dct, filename='test.hdf5')
#     dct = make_NXstxm_dict()
#     nf = h5py.File('base_NXstxm.hdf5', "w")
#     make_stxm_dct_to_file(nf, nxkd.NXD_ENTRY, dct, bc_dct)
#     nf.close()


# ac = parse_nxdef()

# print 'Base Classes'
# for k in dct.keys():
#    dump_class_dct(k, ac[k])


#     #t = datetime.datetime.time(12, 10, 30, tz=CST())
#     #t                               
#     #datetime.time(12, 10, 30, tzinfo=<GMT1 object at 0x...>)
#     t = datetime.datetime.now(tz=CST()).isoformat()
#     gmt = CST()
#     print t
#     #'12:10:30+01:00'
#     print t.dst()
#     #datetime.timedelta(0)
#     print t.tzname()
#     #'Europe/Prague'
#     print t.strftime("%H:%M:%S %Z")
# '12:10:30 Europe/Prague'
# 'The {} is {:%H:%M}.'.format("time", t)
# 'The time is 12:10.'
#     data_dir = 'C:/controls/py2.7/Beamlines/sm/data/guest/Feb27/A110213/'
# #    data_dir = 'C:/controls/py2.7/Beamlines/sm/data/guest/Feb27/'
# #    fname = 'ms1-00057.json'
# #    ximfname = 's1-00057.xim'
# #     "SCAN": {
# #         "CFG": {
# #             "ROI": {
# #                 "DATA_LEVEL": false,
# #                 "EV": {
# #                     "DATA_LEVEL": false,
# #                     "DWELL": 2.5,
# #                     "ENABLED": true,
# #                     "EV_IDX": null,
# #                     "EV_ROIS": [
#     i = 1
#     fname = 'ms1-%05d.json' % i
#     ximfname = 's1-%05d.xim' % i
#     data_dct = json.loads(file(data_dir + fname).read())
#     xim_dat = loadXim2Array(data_dir + ximfname)
#     data_dct['SCAN'][nxkd.NXD_DATA]['CHANNELS'] = []
#     data_dct['SCAN'][nxkd.NXD_DATA]['CHANNELS'].append(xim_dat.copy())
#     for i in range(2,20):
#         fname = 'ms1-%05d.json' % i
#         ximfname = 's1-%05d.xim' % i
#         xim_dat = loadXim2Array(data_dir + ximfname)
#         data_dct['SCAN'][nxkd.NXD_DATA]['CHANNELS'].append(xim_dat.copy())
#     
#     
#     #create_NXstxm_file('sample_point_spectrum.hdf5', dtype[0], data_dct)
#     #create_NXstxm_file('sample_line_spectrum.hdf5', dtype[1], data_dct)
#     #epnts = data_dct['ScanDefinition']['StackAxis']['EV']['NumPoints']
#     #xpnts = data_dct['ScanDefinition']['Regions'][1]['PAxis']['NumPoints']
#     #ypnts = data_dct['ScanDefinition']['Regions'][1]['QAxis']['NumPoints']
#     
#     data_dct['Time'] = make_timestamp_now()
#     create_NXstxm_file('sample_image.hdf5', dtype[2], data_dct)
#     
#     
#     

# create_NXstxm_file('sample_image_stack.hdf5', dtype[3], data_dct)
# create_NXstxm_file('sample_focus.hdf5', dtype[4], data_dct)
# create_NXstxm_file('osa_image.hdf5', dtype[5], data_dct)
# create_NXstxm_file('osa_focus.hdf5', dtype[6], data_dct)
# create_NXstxm_file('detector_image.hdf5', dtype[7], data_dct)

# returns tuple (class_doc, class_fields, class_groups)
#    dom = md.parse(r'C:\controls\nexus-definitions-development\dist\applications\NXstxm.nxdl.xml')
#    root = dom.documentElement
#    print_node(root)

#     bc = readin_base_classes()
#     ac = readin_application_classes()
#     (stxm_doc, stxm_flds, stxm_grps) = ac['NXstxm']
#     
#     create_NXstxm_file("positioner.hdf5")
# 
#     
#     exit
