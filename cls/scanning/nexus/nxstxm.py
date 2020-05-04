'''
Created on Jun 23, 2016

@author: bergr
'''
'''
Created on Mar 2, 2015

@author: bergr
'''
#!/usr/bin/python
import datetime
import xml.etree.ElementTree as ET
import glob
import os
import re
import sys
import json
#import nxs
import numpy as np
import h5py
import pkg_resources
import nexpy

from cls.utils.json_threadsave import dict_to_json_string
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.fileUtils import get_file_path_as_parts

import cls.scanning.nexus.nx_key_defs as nxkd
from cls.scanning.nexus.cls_nx_api import nx_get, nx_put
from cls.types.stxmTypes import scan_image_types, scan_types, IMAGE_PXP, IMAGE_LXL
from cls.utils.roi_utils import ActiveDataObj, get_first_sp_db_from_wdg_com, get_data_status_from_wdg_com
from cls.utils.time_utils import msec_to_sec
from cls.utils.roi_dict_defs import *
from bcm.devices.device_names import *


_logger = get_module_logger(__name__)

def readin_base_classes(desired_class=None):
    clss = get_classes('base_classes', desired_class)
    return(clss)

def readin_application_classes(desired_class=None):
    clss = get_classes('applications', desired_class)
    return(clss)


def readin_contributed_definition_classes(desired_class=None):
    clss = get_classes('contributed_definitions', desired_class)
    return(clss)

def get_classes(class_dir, desired_class=None):
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/%s'%class_dir)
    nxdl_files = list(map(os.path.basename, glob.glob(os.path.join(base_class_path,'*.nxdl.xml'))))
    pattern = re.compile(r'[\t\n ]+')
    nxclasses = {}
    
    if(desired_class is not None):
        fname = desired_class + '.nxdl.xml'
        if(fname in nxdl_files):
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
                #class_fields[name] = (dtype, units, doc)
                class_fields[name] = {'type':dtype, 'units':units, 'doc':doc}
            elif child.tag.endswith('group'):
                #
                gdoc = ''
                try:
                    dtype = child.attrib['type']
                    name = child.attrib['name']
                    
                except KeyError:
                    pass
                
                for element in child:
                    if('type' in list(element.attrib.keys())):
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
                            if('name' in list(element.attrib.keys())):
                                fname = element.attrib['name']
                            if('type' in list(element.attrib.keys())):
                                fdtype = element.attrib['type']
                            if('units' in list(element.attrib.keys())):
                                funits = element.attrib['units']
                            group_fields[fname] = {'name':fname, 'type':fdtype, 'units':funits, 'doc': fdoc}
                            
                        except KeyError:
                            pass
                        
                class_groups[name] = {'name':name, 'doc': gdoc, 'type':dtype, 'fields':group_fields}
            
            nxclasses[class_name] = {'doc':class_doc, 'fields':class_fields, 'groups': class_groups}
            group_fields = {}
    return(nxclasses)

def get_fields(field):
    
    fields = {}
    for k in list(field.attrib.keys()):
        fields[k] = field.attrib[k] 
    return(fields)

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
            if(len(child.getchildren()) > 0):
                dtype = child.attrib['type']
                if('name' in list(child.attrib.keys())):
                    name = child.attrib['name']
                else:
                    name = dtype
                group_fields[name] = get_group(name, child)
                #group_fields[dtype] = get_nexpy_classes('group', child)
                #classes = get_nexpy_classes('group', child)
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
            
        
        #nxclasses[dtype] = (class_doc, class_fields, class_groups)
        #nxclasses[dtype] = group_fields
    return(group_fields)

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
    #walk groups
    for i in list(nxclass_dct['groups'].keys()):
        nxgrp = _group(srcgrp, nxclass_dct['groups'][i]['name'], nxclass_dct['groups'][i]['type'])
        # groups have 'doc' 'type' 'name'
        if(parentgrp is None ):
            parentgrp = srcgrp
            
        _string_attr(nxgrp, 'doc', nxclass_dct['groups'][i]['doc'])
        groups[nxclass_dct['groups'][i]['name']] = nxgrp
        
        grp = nxclass_dct['groups'][i]
        if(type(grp) == dict):
            if('fields' in list(grp.keys())):
                make_data(nxgrp, grp['fields'])
                
    #walk fields
    for i in list(nxclass_dct['fields'].keys()):
        # fields have ['units', 'doc', 'type'
        if('doc' in list(nxclass_dct['fields'].keys())):
            _string_attr(parentgrp, 'doc', nxclass_dct['fields'][i]['doc'])
        name = None
        dtype = None
        units = None
        
        name = i
        if('type' in list(nxclass_dct['fields'][i].keys())):
            dtype = nxclass_dct['fields'][i]['type']
        if('units' in list(nxclass_dct['fields'][i].keys())):
            units = nxclass_dct['fields'][i]['units']    
            
        if((name is not None) and (dtype != '') and (units != '')):
            _dataset(parentgrp, name, 0.0, nxclass_dct['fields'][name]['type'], nxclass_dct['fields'][name]['units'], nxclass_dct['fields'][name])
        elif((name is not None) and (dtype != '')):
            _dataset(parentgrp, name, 0.0, nxclass_dct['fields'][name]['type'], nxclass_dct['fields'][name])
        else:
            _dataset(parentgrp, name, '', 'NX_CHAR')
    
    return(srcgrp)
def translate_scan_type(old_type):
    """
    old scan_types = Enum('Detector_Scan','OSA_Scan','OSA_Focus_Scan','Focus_Scan','Point_Scan', 'ImagePointByPoint','ImageLineByLine')
    
    new scan_types = Enum('Detector_Image','OSA_Image','OSA_Focus','Sample_Focus','Sample_Point_Spectrum', 'Sample_Line_Spectrum', 'Sample_Image', 'Sample_Line_Spectrum', 'Sample_Image_Stack', 'Generic_Scan')
    
    """
    
    if(old_type == 'Detector_Scan'):
        return(scan_types.DETECTOR_IMAGE)
    
    elif(old_type == 'OSA_Scan'):
        return(scan_types.OSA_IMAGE)
    
    elif(old_type == 'OSA_Focus_Scan'):
        return(scan_types.OSA_FOCUS)
    
    elif(old_type == 'Focus_Scan'):
        return(scan_types.SAMPLE_FOCUS)
    
    elif(old_type == 'Point_Scan'):
        return(scan_types.SAMPLE_POINT_SPECTRUM)
    
    elif(old_type == 'ImagePointByPoint'):
        return(scan_types.SAMPLE_IMAGE)
    
    elif(old_type == 'ImageLineByLine'):
        return(scan_types.SAMPLE_IMAGE)
    else:
        return(None)
    

def print_node(root):
    if root.childNodes:
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                #print node.tagName,"has value:",  node.nodeValue, "and is child of:", node.parentNode.tagName
                if((node.tagName is None) or (node.tagName is None) or (node.tagName is None)):
                    print('[',node.tagName,']',"has value: [", node.nodeValue,']', "and is child of: [", node.parentNode.tagName, ']')
                else:
                    print('[%s] has value = [%s] and is child of: [%s]' % (str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper()))
                    print('[%s] has value = [%s] and is child of: [%s]' % (str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper()))
                    for k in list(node.attributes.keys()):
                        print('\t\t[%s] = %s' % (k, node.attributes[k].value))
                    
                print_node(node)
            
            if(node.nodeType == node.TEXT_NODE):
                print('text node value = ' , node.nodeValue)
                #if((node.tagName is None) or (node.tagName is None) or (node.tagName is None)):
                #    print '[',node.tagName,']',"has value: [", node.nodeValue,']', "and is child of: [", node.parentNode.tagName, ']'
                #else:
                #    print '[%s] has value = [%s] and is child of: [%s]' % (str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper())
                #print_node(node)
                
            else:
                print('node [%s] is of type %d' % (node, node.nodeType))

def walk_xml():
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
    fname = 'NXstxm.nxdl.xml'
    
    tree = ET.parse(os.path.join(base_class_path, fname))
    #tree = ET.fromstring("""...""")
    for  elt in tree.iter():
        if(elt.text is not None):
            print("%s: '%s'" % (elt.tag, elt.text.strip()))

def try_this():
    from xmlutils.xml2json import xml2json
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
    fname = 'NXstxm.nxdl.xml'
    #converter = xml2json(base_class_path+ '/' + fname, "samples/fruits.sql", encoding="utf-8")
    #converter.convert()
    
    # to get a json string
    fstr = os.path.join(base_class_path, fname)
    converter = xml2json(fstr, encoding="utf-8")
    print(converter.get_json())

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
                
                
def make_bens_file(filepath='tester'):
     #Write NeXus
        NXfile = h5py.File(filepath+".hdf5", 'w')
        NXfile.attrs[nxkd.NXD_HDF_VER] = np.array([bnxkd.HDF5_VER])
        NXfile.attrs[nxkd.NXD_NX_VER] = np.array([bnxkd.NEXUS_VER])
        NXfile.attrs[nxkd.NXD_FILE_NAME] = np.array([b'/home/homersimpson/PLV_now.hdf5'])
        NXfile.attrs[nxkd.NXD_FILE_TIME] = np.array([b'2012-01-01T12:00:00+01:00'])
        NXfile.create_group('entry1')
        NXfile['entry1'].attrs['NX_class'] = np.array([b'NXentry'])
        NXfile['entry1'].create_dataset('definition',data=np.array([b'NXstxm ']))
        NXfile['entry1'].create_dataset('title',data=np.array([b'Sample ']))
        NXfile['entry1'].create_dataset('start_time',data=np.array([b'2012-01-01T12:00:00+100 ']))
        NXfile['entry1'].create_group('Camera')
        NXfile['entry1']['Camera'].attrs['NX_class'] = np.array([b'NXdata'])

# New style
        NXfile['entry1']['Camera'].create_dataset(nxkd.NXD_DATA,data=np.array(NXim,np.float32).reshape(NXim.size[1],NXim.size[0]))
        NXfile['entry1']['Camera'].create_dataset('sample_x',data=np.linspace(X_MinMax[0],X_MinMax[1],num=NXim.size[0]))
        NXfile['entry1']['Camera']['sample_x'].attrs['axes'] = 2
        NXfile['entry1']['Camera'].create_dataset('sample_y',data=np.linspace(Y_MinMax[0],Y_MinMax[1],num=NXim.size[1]))
        NXfile['entry1']['Camera']['sample_y'].attrs['axes'] = 1
        NXfile['entry1']['Camera'].create_dataset('energy',data=np.array([0.1]))
        sc = NXfile['entry1']['Camera'].create_dataset('stxm_scan_type',data=np.array([b'sample image ']))
        
        NXfile['entry1']['Camera'].create_dataset('count_time',data=np.array([self.ExposureTime]))
        NXfile.close()

# def _data_as_1D(data_dct):
#     """ takes the standard data_dct from the scan configuration and creates 1D [numP]
#     versions of :
#         energy
#         count_time
#         polarization
#         offset
#     also creates the 1D versions of all data for use in the /instrument section <data>[numP]
#     and the normal NXdata section <data>[numE]
#
#     The data is converted once here in this function then used in the rest of the make_ functions as is
#     so if data needs to be converted, do it here to keep the confusion of what happens to the data to a minimum
#     """
#
#     numE = 0
#     numPolarities = 0
#     epnts = None
#     dpnts = None
#     pol_pnts = None
#     off_pnts = None
#     angle_pnts = None
#     scan_type = dct_get(data_dct, ADO_CFG_SCAN_TYPE)
#     x_roi = dct_get(data_dct, ADO_CFG_X)
#     y_roi = dct_get(data_dct,ADO_CFG_Y)
#     z_roi = dct_get(data_dct,ADO_CFG_Z)
#     e_rois = dct_get(data_dct, ADO_CFG_EV_ROIS)
#     numX = int(x_roi[NPOINTS])
#     numY = int(y_roi[NPOINTS])
#     numZ = int(z_roi[NPOINTS])
#
#     if(numZ > 0):
#         zp1ra = dct_get(data_dct,'DATA.SSCANS.Z.P1RA')
#         if (zp1ra is None):
#             zpnts = np.linspace(z_roi[START], z_roi[STOP], numZ)
#         else:
#             zpnts = zp1ra[: numZ ]
#
#     positioners_dct = dct_get(data_dct,'POSITIONERS')
#     detectors_dct = dct_get(data_dct,'DETECTORS')
#     temps_dct = dct_get(data_dct, 'TEMPERATURES')
#     sr_current = detectors_dct[DNM_RING_CURRENT][RBV]
#
#     for e_roi in e_rois:
#         #elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
#         _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
#         if(epnts is not None):
#             epnts = np.concatenate((epnts, _e1), axis=0)
#         else:
#             epnts = _e1
#         numE += e_roi[NPOINTS]
#
#         #count_time
#         _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
#         if(dpnts is not None):
#             dpnts = np.concatenate((dpnts, _d1), axis=0)
#         else:
#             dpnts = _d1
#         count_time = dpnts
#
#         num_pol_pnts = len(e_roi['EPU_POL_PNTS'])
#
#         _p1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_POL_PNTS'])
#         _o1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_OFF_PNTS'])
#         _a1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_ANG_PNTS'])
#         #numPolarities += 1
#         numPolarities += len(e_roi['EPU_POL_PNTS'])
#         if(pol_pnts is not None):
#             pol_pnts = np.concatenate((pol_pnts, _p1), axis=0)
#             off_pnts = np.concatenate((pol_pnts, _o1), axis=0)
#             angle_pnts = np.concatenate((pol_pnts, _a1), axis=0)
#         else:
#             pol_pnts = _p1
#             off_pnts = _o1
#             angle_pnts = _a1
#
#     data_numE = dct_get(data_dct,ADO_DATA_POINTS)
#     if(isinstance(data_numE, list)):
#         data_numE = np.array(data_numE)
#         data_numP = data_numE.flatten()
#     else:
#         data_numP = data_numE.flatten()
#
#     #make the array for the line_position used in Line Spectrum Scans
#     #ls_dat = np.linspace(e_roi[START], e_roi[STOP] + e_roi[STEP], num=e_roi[NPOINTS] + 1, endpoint=True)
#     ls_dat = np.linspace(x_roi[START], x_roi[STOP] + x_roi[STEP], num=x_roi[NPOINTS] + 1, endpoint=True)
#     line_position = np.cumsum(np.diff(ls_dat))
#
#     #get relevant positioner data
#     EPUGap = positioners_dct[DNM_EPU_GAP][RBV]
#     EPUHarmonic = positioners_dct[DNM_EPU_HARMONIC][RBV]
#     #Epu_pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]
#
#     SlitX = positioners_dct[DNM_SLIT_X][RBV]
#     SlitY = positioners_dct[DNM_SLIT_Y][RBV]
#     M3STXMPitch = positioners_dct[DNM_M3_PITCH][RBV]
#     if(DNM_GONI_THETA in positioners_dct.keys()):
#         GoniTheta = positioners_dct[DNM_GONI_THETA][RBV]
#
#     x_sscan_npnts = dct_get(data_dct,'DATA.SSCANS.X.NPTS')
#     #check if the sscan was a line scan (2 points start and stop) or a point by point scan
#     if(x_sscan_npnts == 2):
#         xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
#     else:
#         #point by point so read out the points
#         xp1ra = dct_get(data_dct,'DATA.SSCANS.X.P1RA')
#         if(xp1ra is None):
#             xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
#         else:
#             xpnts = xp1ra[: numX ]
#
#     if(numY > 0):
#         yp1ra = dct_get(data_dct,'DATA.SSCANS.Y.P1RA')
#         if(yp1ra is None):
#             ypnts = np.linspace(y_roi[START], y_roi[STOP], numY)
#         else:
#             ypnts = yp1ra[: numY ]
#     else:
#         if(scan_type == scan_types.GENERIC_SCAN):
#             numY = numX
#             arr = np.ones(numY, dtype=np.float32)
#             yp1ra = arr*positioners_dct['SampleY'][RBV]
#             ypnts = arr*positioners_dct['SampleY'][RBV]
#         else:
#             yp1ra = []
#             ypnts = []
#
#
#     if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
#         #the order of the data shape is different than other scans
#         # (numPol, numEv, numX) or ( # images, # rows per image, #cols per image)
#         # so translate so that the shape will be standard, where numEV typically is # images
#         numY = int(e_roi[NPOINTS])
#         numE = numPolarities
#         if(numZ <= 0):
#             numP = numE * numY * numX
#         else:
#             numP = numE * numY * numX * numZ
#     else:
#         numE = numE * numPolarities
#         if(numZ <= 0):
#             numP = numE * numY * numX
#         else:
#             numP = numE * numY * numX * numZ
#
#     #with multiple energy regions the value of numP can get into the millions which will cauwse a numpy error
#     #until I can figure out a work around only use 10 points for numP
#     if(numP > 100000):
#         #if it is more than a million setup numP for only a single energy
#         if (numZ <= 0):
#             numP = numY * numX
#         else:
#             numP = numY * numX * numZ
#
#             #pull these out because they are required in EVERY NXData group
#     if(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
#         #cant use the RBV positions because they will be from teh last sp_db and not from THIS sp_db
#         #so use the setpoint for this sp_db
#         sx_pnts = x_roi[START]
#         sy_pnts = y_roi[START]
#     else:
#         sx_pnts = positioners_dct['SampleX'][RBV]
#         sy_pnts = positioners_dct['SampleY'][RBV]
#
#     dct = {}
#     dct_put(dct, 'SYMBOLS.numP', numP)
#     dct_put(dct, 'SYMBOLS.numX', numX)
#     dct_put(dct, 'SYMBOLS.numY', numY)
#     dct_put(dct, 'SYMBOLS.numE', numE)
#
#     #create numE and numP versions of data so they can just be pulled out later in
#     #[numE] versions
#     dct_put(dct, 'NUM_E.EV', epnts )
#     dct_put(dct, 'NUM_E.COUNT_TIME', count_time)
#     dct_put(dct, 'NUM_E.EPU_GAP',make_1d_array(numE, EPUGap))
#     dct_put(dct, 'NUM_E.EPU_POL',pol_pnts)
#     dct_put(dct, 'NUM_E.EPU_OFFSET',off_pnts)
#     dct_put(dct, 'NUM_E.EPU_POL_ANGLE',angle_pnts)
#     dct_put(dct, 'NUM_E.EPU_HARMONIC', make_1d_array(numE, EPUHarmonic))
#     dct_put(dct, 'NUM_E.MOTOR_X', xpnts)
#     dct_put(dct, 'NUM_E.MOTOR_Y', ypnts)
#     if(numZ > 0):
#         dct_put(dct, 'NUM_E.MOTOR_Z', zpnts)
#     dct_put(dct, 'NUM_E.SLIT_X',make_1d_array(numE, SlitX))
#     dct_put(dct, 'NUM_E.SLIT_Y',make_1d_array(numE, SlitY))
#     dct_put(dct, 'NUM_E.M3_PITCH',make_1d_array(numE, M3STXMPitch))
#
#     dct_put(dct, 'NUM_E.SAMPLE_X', sx_pnts)
#     dct_put(dct, 'NUM_E.SAMPLE_Y', sy_pnts)
#
#     dct_put(dct, 'NUM_E.DATA', data_numE)
#
#     #dct_put(dct, 'NUM_E.SR_CURRENT', make_1d_array(numE, sr_current))
#
#     #make 1d and 2d versions of data used in the /control/data section
#     oned_sdata = []
#     twod_sdata = []
#     thrd_sdata = []
#
#     data_E = dct_get(dct, 'NUM_E.DATA')
#     data_E_shape = data_E.shape
#     if(len(data_E_shape) == 1):
#         cols = data_E_shape[0]
#         oned_sdata = np.zeros(cols, dtype=np.float32)
#         oned_sdata.fill(sr_current)
#     elif(len(data_E_shape) == 2):
#         rows = data_E_shape[0]
#         cols = data_E_shape[1]
#         twod_sdata = np.zeros((rows, cols), dtype=np.float32)
#         twod_sdata.fill(sr_current)
#
#     elif(len(data_E_shape) == 3):
#         #print '_data_as_1D: 3D data not totally supported yet'
#         if((scan_type == scan_types.SAMPLE_POINT_SPECTRUM) or (scan_type == scan_types.GENERIC_SCAN)):
#             cols = data_E_shape[0]
#             oned_sdata = np.zeros(cols, dtype=np.float32)
#             oned_sdata.fill(sr_current)
#         else:
#             #numI = data_E_shape[0]
#             #setting the following to 1 for now because for stacks I larger numI will generate a memory exception because the
#             #array would be too large
#             numI = 1
#
#             rows = data_E_shape[1]
#             cols = data_E_shape[2]
#             twod_sdata = np.zeros((rows, cols), dtype=np.float32)
#             twod_sdata.fill(sr_current)
#
#             thrd_sdata = np.zeros((numI, rows, cols), dtype=np.float32)
#             thrd_sdata.fill(sr_current)
#
#     dct_put(dct, 'NUM_E.SR_CURRENT.ONE_D', oned_sdata)
#     dct_put(dct, 'NUM_E.SR_CURRENT.TWO_D', twod_sdata)
#     dct_put(dct, 'NUM_E.SR_CURRENT.THREE_D', thrd_sdata)
#
#     #dct_put(dct, 'NUM_E.ROTATION_ANGLE', make_1d_array(numE, GoniTheta))
#
#     xpnts2 =  np.tile(xpnts, numY)
#     sample_x =  np.tile(xpnts2, numE)
#
#     ypnts2 = np.repeat(ypnts, numX)
#     sample_y = np.tile(ypnts2, numE)
#
#     #now [numP] versions
#     #dct_put(dct, 'NUM_P.EV', np.tile(epnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EV', np.repeat(epnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.COUNT_TIME', np.repeat(count_time, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_POL', np.repeat(pol_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_OFFSET', np.repeat(off_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_POL_ANGLE',np.repeat(angle_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_GAP',make_1d_array(numP, EPUGap))
#     dct_put(dct, 'NUM_P.EPU_HARMONIC',make_1d_array(numP, EPUHarmonic))
#
#     if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
#         xpnts2 =  np.tile(xpnts, numY)
#         sample_x =  np.tile(xpnts2, numE)
#         ypnts2 = np.tile(ypnts, numX)
#         sample_y = np.tile(ypnts2, numE)
#         dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
#         dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
#
#         dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
#         dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
#     else:
#         dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
#         dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
#
#         dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
#         dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
#
#     if(numZ > 0):
#         dct_put(dct, 'NUM_P.MOTOR_Z', np.repeat(zpnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.SLIT_X',make_1d_array(numP, SlitX))
#     dct_put(dct, 'NUM_P.SLIT_Y',make_1d_array(numP, SlitY))
#     dct_put(dct, 'NUM_P.M3_PITCH',make_1d_array(numP, M3STXMPitch))
#     dct_put(dct, 'NUM_P.DATA', data_numP)
#     dct_put(dct, 'NUM_P.SR_CURRENT', make_1d_array(numP, sr_current))
#     #dct_put(dct, 'NUM_P.ROTATION_ANGLE', make_1d_array(numP, GoniTheta))
#
#     dct_put(dct, 'NUM_P.LINE_POSITION', line_position)
#
#
#     return(dct)

# def _data_as_1D(data_dct):
#     """ takes the standard data_dct from the scan configuration and creates 1D [numP]
#     versions of :
#         energy
#         count_time
#         polarization
#         offset
#     also creates the 1D versions of all data for use in the /instrument section <data>[numP]
#     and the normal NXdata section <data>[numE]
#
#     The data is converted once here in this function then used in the rest of the make_ functions as is
#     so if data needs to be converted, do it here to keep the confusion of what happens to the data to a minimum
#     """
#
#     numE = 0
#     numPolarities = 0
#     epnts = None
#     dpnts = None
#     pol_pnts = None
#     off_pnts = None
#     angle_pnts = None
#     scan_type = dct_get(data_dct, ADO_CFG_SCAN_TYPE)
#     x_roi = dct_get(data_dct, ADO_CFG_X)
#     y_roi = dct_get(data_dct, ADO_CFG_Y)
#     z_roi = dct_get(data_dct, ADO_CFG_Z)
#     e_rois = dct_get(data_dct, ADO_CFG_EV_ROIS)
#     numX = int(x_roi[NPOINTS])
#     numY = int(y_roi[NPOINTS])
#     numZ = int(z_roi[NPOINTS])
#
#     if (numZ > 0):
#         zp1ra = dct_get(data_dct, 'DATA.SSCANS.Z.P1RA')
#         if (zp1ra is None):
#             zpnts = np.linspace(z_roi[START], z_roi[STOP], numZ)
#         else:
#             zpnts = zp1ra[: numZ]
#
#     positioners_dct = dct_get(data_dct, 'POSITIONERS')
#     detectors_dct = dct_get(data_dct, 'DETECTORS')
#     temps_dct = dct_get(data_dct, 'TEMPERATURES')
#     sr_current = detectors_dct[DNM_RING_CURRENT][RBV]
#
#     for e_roi in e_rois:
#         # elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
#         _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
#         if (epnts is not None):
#             epnts = np.concatenate((epnts, _e1), axis=0)
#         else:
#             epnts = _e1
#         numE += e_roi[NPOINTS]
#
#         # count_time
#         _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
#         if (dpnts is not None):
#             dpnts = np.concatenate((dpnts, _d1), axis=0)
#         else:
#             dpnts = _d1
#         count_time = dpnts
#
#         num_pol_pnts = len(e_roi['EPU_POL_PNTS'])
#
#         _p1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_POL_PNTS'])
#         _o1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_OFF_PNTS'])
#         _a1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_ANG_PNTS'])
#         # numPolarities += 1
#         numPolarities += len(e_roi['EPU_POL_PNTS'])
#         if (pol_pnts is not None):
#             pol_pnts = np.concatenate((pol_pnts, _p1), axis=0)
#             off_pnts = np.concatenate((pol_pnts, _o1), axis=0)
#             angle_pnts = np.concatenate((pol_pnts, _a1), axis=0)
#         else:
#             pol_pnts = _p1
#             off_pnts = _o1
#             angle_pnts = _a1
#
#     data_numE = dct_get(data_dct, ADO_DATA_POINTS)
#     if (isinstance(data_numE, list)):
#         data_numE = np.array(data_numE)
#         data_numP = data_numE.flatten()
#     else:
#         data_numP = data_numE.flatten()
#
#     # make the array for the line_position used in Line Spectrum Scans
#     # ls_dat = np.linspace(e_roi[START], e_roi[STOP] + e_roi[STEP], num=e_roi[NPOINTS] + 1, endpoint=True)
#     ls_dat = np.linspace(x_roi[START], x_roi[STOP] + x_roi[STEP], num=x_roi[NPOINTS] + 1, endpoint=True)
#     line_position = np.cumsum(np.diff(ls_dat))
#
#     # get relevant positioner data
#     EPUGap = positioners_dct[DNM_EPU_GAP][RBV]
#     EPUHarmonic = positioners_dct[DNM_EPU_HARMONIC][RBV]
#     # Epu_pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]
#
#     SlitX = positioners_dct[DNM_SLIT_X][RBV]
#     SlitY = positioners_dct[DNM_SLIT_Y][RBV]
#     M3STXMPitch = positioners_dct[DNM_M3_PITCH][RBV]
#     if (DNM_GONI_THETA in positioners_dct.keys()):
#         GoniTheta = positioners_dct[DNM_GONI_THETA][RBV]
#
#     x_sscan_npnts = dct_get(data_dct, 'DATA.SSCANS.X.NPTS')
#     # check if the sscan was a line scan (2 points start and stop) or a point by point scan
#     if (x_sscan_npnts == 2):
#         xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
#     else:
#         # point by point so read out the points
#         xp1ra = dct_get(data_dct, 'DATA.SSCANS.X.P1RA')
#         if (xp1ra is None):
#             xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
#         else:
#             xpnts = xp1ra[: numX]
#
#     if (numY > 0):
#         yp1ra = dct_get(data_dct, 'DATA.SSCANS.Y.P1RA')
#         if (yp1ra is None):
#             ypnts = np.linspace(y_roi[START], y_roi[STOP], numY)
#         else:
#             ypnts = yp1ra[: numY]
#     else:
#         if (scan_type == scan_types.GENERIC_SCAN):
#             numY = numX
#             arr = np.ones(numY, dtype=np.float32)
#             yp1ra = arr * positioners_dct['SampleY'][RBV]
#             ypnts = arr * positioners_dct['SampleY'][RBV]
#         else:
#             yp1ra = []
#             ypnts = []
#
#     if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
#         # the order of the data shape is different than other scans
#         # (numPol, numEv, numX) or ( # images, # rows per image, #cols per image)
#         # so translate so that the shape will be standard, where numEV typically is # images
#         numY = int(e_roi[NPOINTS])
#         numE = numPolarities
#         if (numZ <= 0):
#             numP = numE * numY * numX
#         else:
#             numP = numE * numY * numX * numZ
#     else:
#         numE = numE * numPolarities
#         if (numZ <= 0):
#             numP = numE * numY * numX
#         else:
#             numP = numE * numY * numX * numZ
#
#             # with multiple energy regions the value of numP can get into the millions which will cauwse a numpy error
#     # until I can figure out a work around only use 10 points for numP
#     if (numP > 100000):
#         # if it is more than a million setup numP for only a single energy
#         if (numZ <= 0):
#             numP = numY * numX
#         else:
#             numP = numY * numX * numZ
#
#             # pull these out because they are required in EVERY NXData group
#     if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
#         # cant use the RBV positions because they will be from teh last sp_db and not from THIS sp_db
#         # so use the setpoint for this sp_db
#         sx_pnts = x_roi[START]
#         sy_pnts = y_roi[START]
#     else:
#         sx_pnts = positioners_dct['SampleX'][RBV]
#         sy_pnts = positioners_dct['SampleY'][RBV]
#
#     dct = {}
#     dct_put(dct, 'SYMBOLS.numP', numP)
#     dct_put(dct, 'SYMBOLS.numX', numX)
#     dct_put(dct, 'SYMBOLS.numY', numY)
#     dct_put(dct, 'SYMBOLS.numE', numE)
#
#     # create numE and numP versions of data so they can just be pulled out later in
#     # [numE] versions
#     dct_put(dct, 'NUM_E.EV', epnts)
#     dct_put(dct, 'NUM_E.COUNT_TIME', count_time)
#     dct_put(dct, 'NUM_E.EPU_GAP', make_1d_array(numE, EPUGap))
#     dct_put(dct, 'NUM_E.EPU_POL', pol_pnts)
#     dct_put(dct, 'NUM_E.EPU_OFFSET', off_pnts)
#     dct_put(dct, 'NUM_E.EPU_POL_ANGLE', angle_pnts)
#     dct_put(dct, 'NUM_E.EPU_HARMONIC', make_1d_array(numE, EPUHarmonic))
#     dct_put(dct, 'NUM_E.MOTOR_X', xpnts)
#     dct_put(dct, 'NUM_E.MOTOR_Y', ypnts)
#     if (numZ > 0):
#         dct_put(dct, 'NUM_E.MOTOR_Z', zpnts)
#     dct_put(dct, 'NUM_E.SLIT_X', make_1d_array(numE, SlitX))
#     dct_put(dct, 'NUM_E.SLIT_Y', make_1d_array(numE, SlitY))
#     dct_put(dct, 'NUM_E.M3_PITCH', make_1d_array(numE, M3STXMPitch))
#
#     dct_put(dct, 'NUM_E.SAMPLE_X', sx_pnts)
#     dct_put(dct, 'NUM_E.SAMPLE_Y', sy_pnts)
#
#     dct_put(dct, 'NUM_E.DATA', data_numE)
#
#     # dct_put(dct, 'NUM_E.SR_CURRENT', make_1d_array(numE, sr_current))
#
#     # make 1d and 2d versions of data used in the /control/data section
#     oned_sdata = []
#     twod_sdata = []
#     thrd_sdata = []
#
#     data_E = dct_get(dct, 'NUM_E.DATA')
#     data_E_shape = data_E.shape
#     if (len(data_E_shape) == 1):
#         cols = data_E_shape[0]
#         oned_sdata = np.zeros(cols, dtype=np.float32)
#         oned_sdata.fill(sr_current)
#     elif (len(data_E_shape) == 2):
#         rows = data_E_shape[0]
#         cols = data_E_shape[1]
#         twod_sdata = np.zeros((rows, cols), dtype=np.float32)
#         twod_sdata.fill(sr_current)
#
#     elif (len(data_E_shape) == 3):
#         # print '_data_as_1D: 3D data not totally supported yet'
#         if ((scan_type == scan_types.SAMPLE_POINT_SPECTRUM) or (scan_type == scan_types.GENERIC_SCAN)):
#             cols = data_E_shape[0]
#             oned_sdata = np.zeros(cols, dtype=np.float32)
#             oned_sdata.fill(sr_current)
#         else:
#             numI = data_E_shape[0]
#             # setting the following to 1 for now because for stacks I larger numI will generate a memory exception because the
#             # array would be too large
#             #numI = 1
#
#             rows = data_E_shape[1]
#             cols = data_E_shape[2]
#             twod_sdata = np.zeros((rows, cols), dtype=np.float32)
#             twod_sdata.fill(sr_current)
#
#             thrd_sdata = np.zeros((numI, rows, cols), dtype=np.float32)
#             thrd_sdata.fill(sr_current)
#
#     dct_put(dct, 'NUM_E.SR_CURRENT.ONE_D', oned_sdata)
#     dct_put(dct, 'NUM_E.SR_CURRENT.TWO_D', twod_sdata)
#     dct_put(dct, 'NUM_E.SR_CURRENT.THREE_D', thrd_sdata)
#
#     # dct_put(dct, 'NUM_E.ROTATION_ANGLE', make_1d_array(numE, GoniTheta))
#
#     xpnts2 = np.tile(xpnts, numY)
#     sample_x = np.tile(xpnts2, numE)
#
#     ypnts2 = np.repeat(ypnts, numX)
#     sample_y = np.tile(ypnts2, numE)
#
#     # now [numP] versions
#     # dct_put(dct, 'NUM_P.EV', np.tile(epnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EV', np.repeat(epnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.COUNT_TIME', np.repeat(count_time, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_POL', np.repeat(pol_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_OFFSET', np.repeat(off_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_POL_ANGLE', np.repeat(angle_pnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.EPU_GAP', make_1d_array(numP, EPUGap))
#     dct_put(dct, 'NUM_P.EPU_HARMONIC', make_1d_array(numP, EPUHarmonic))
#
#     if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
#         xpnts2 = np.tile(xpnts, numY)
#         sample_x = np.tile(xpnts2, numE)
#         ypnts2 = np.tile(ypnts, numX)
#         sample_y = np.tile(ypnts2, numE)
#         dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
#         dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
#
#         dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
#         dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
#     else:
#         dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
#         dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
#
#         dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
#         dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
#
#     if (numZ > 0):
#         dct_put(dct, 'NUM_P.MOTOR_Z', np.repeat(zpnts, (numY * numX)))
#     dct_put(dct, 'NUM_P.SLIT_X', make_1d_array(numP, SlitX))
#     dct_put(dct, 'NUM_P.SLIT_Y', make_1d_array(numP, SlitY))
#     dct_put(dct, 'NUM_P.M3_PITCH', make_1d_array(numP, M3STXMPitch))
#     dct_put(dct, 'NUM_P.DATA', data_numP)
#     dct_put(dct, 'NUM_P.SR_CURRENT', make_1d_array(numP, sr_current))
#     # dct_put(dct, 'NUM_P.ROTATION_ANGLE', make_1d_array(numP, GoniTheta))
#
#     dct_put(dct, 'NUM_P.LINE_POSITION', line_position)
#
#     return (dct)

def _data_as_1D(data_dct, sp_id=None):
    """ takes the standard data_dct from the scan configuration and creates 1D [numP]
    versions of :
        energy
        count_time
        polarization
        offset
    also creates the 1D versions of all data for use in the /instrument section <data>[numP]
    and the normal NXdata section <data>[numE]

    The data is converted once here in this function then used in the rest of the make_ functions as is
    so if data needs to be converted, do it here to keep the confusion of what happens to the data to a minimum
    """

    numE = 0
    numPolarities = 0
    epnts = None
    dpnts = None
    pol_pnts = None
    off_pnts = None
    angle_pnts = None
    scan_type = dct_get(data_dct, ADO_CFG_SCAN_TYPE)

    if(sp_id is not None):
        sp_rois = dct_get(data_dct, ADO_SP_ROIS)
        sp_db = sp_rois[sp_id]
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        z_roi = dct_get(sp_db, SPDB_Z)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
    else:
        x_roi = dct_get(data_dct, ADO_CFG_X)
        y_roi = dct_get(data_dct, ADO_CFG_Y)
        z_roi = dct_get(data_dct, ADO_CFG_Z)
        e_rois = dct_get(data_dct, ADO_CFG_EV_ROIS)

    numX = int(x_roi[NPOINTS])
    numY = int(y_roi[NPOINTS])
    numZ = int(z_roi[NPOINTS])

    #if (numZ > 0):
    if ((numZ > 0) and (dct_get(data_dct, SPDB_ZENABLED))):
        zp1ra = dct_get(data_dct, 'DATA.SSCANS.Z.P1RA')
        if (zp1ra is None):
            zpnts = np.linspace(z_roi[START], z_roi[STOP], numZ)
        else:
            zpnts = zp1ra[: numZ]
    # else:
    #     numZ = 0

    positioners_dct = dct_get(data_dct, 'POSITIONERS')
    detectors_dct = dct_get(data_dct, 'DETECTORS')
    temps_dct = dct_get(data_dct, 'TEMPERATURES')
    sr_current = detectors_dct[DNM_RING_CURRENT][RBV]

    for e_roi in e_rois:
        # elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
        _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
        if (epnts is not None):
            epnts = np.concatenate((epnts, _e1), axis=0)
        else:
            epnts = _e1
        numE += e_roi[NPOINTS]

        # count_time
        _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
        if (dpnts is not None):
            dpnts = np.concatenate((dpnts, _d1), axis=0)
        else:
            dpnts = _d1
        count_time = dpnts

        num_pol_pnts = len(e_roi['EPU_POL_PNTS'])

        _p1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_POL_PNTS'])
        _o1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_OFF_PNTS'])
        _a1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_ANG_PNTS'])
        # numPolarities += 1
        numPolarities += len(e_roi['EPU_POL_PNTS'])
        if (pol_pnts is not None):
            pol_pnts = np.concatenate((pol_pnts, _p1), axis=0)
            off_pnts = np.concatenate((pol_pnts, _o1), axis=0)
            angle_pnts = np.concatenate((pol_pnts, _a1), axis=0)
        else:
            pol_pnts = _p1
            off_pnts = _o1
            angle_pnts = _a1

    data_numE = dct_get(data_dct, ADO_DATA_POINTS)
    if (isinstance(data_numE, list)):
        data_numE = np.array(data_numE)
        data_numP = data_numE.flatten()
    else:
        data_numP = data_numE.flatten()

    # make the array for the line_position used in Line Spectrum Scans
    # ls_dat = np.linspace(e_roi[START], e_roi[STOP] + e_roi[STEP], num=e_roi[NPOINTS] + 1, endpoint=True)
    ls_dat = np.linspace(x_roi[START], x_roi[STOP] + x_roi[STEP], num=x_roi[NPOINTS] + 1, endpoint=True)
    line_position = np.cumsum(np.diff(ls_dat))

    # get relevant positioner data
    EPUGap = positioners_dct[DNM_EPU_GAP][RBV]
    EPUHarmonic = positioners_dct[DNM_EPU_HARMONIC][RBV]
    # Epu_pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]

    SlitX = positioners_dct[DNM_SLIT_X][RBV]
    SlitY = positioners_dct[DNM_SLIT_Y][RBV]
    M3STXMPitch = positioners_dct[DNM_M3_PITCH][RBV]
    if (DNM_GONI_THETA in list(positioners_dct.keys())):
        GoniTheta = positioners_dct[DNM_GONI_THETA][RBV]

    x_sscan_npnts = dct_get(data_dct, 'DATA.SSCANS.X.NPTS')
    # check if the sscan was a line scan (2 points start and stop) or a point by point scan

    if (x_sscan_npnts == 2):
        xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
    else:
        # point by point so read out the points
        #xp1ra = dct_get(data_dct, 'DATA.SSCANS.X.P1RA')
        #if (xp1ra is None):
        xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
        #else:
        #    xpnts = xp1ra[: numX]
    if (numY > 0):
        #yp1ra = dct_get(data_dct, 'DATA.SSCANS.Y.P1RA')
        #if (yp1ra is None):
        ypnts = np.linspace(y_roi[START], y_roi[STOP], numY)
        #else:
        #    ypnts = yp1ra[: numY]
    else:
        if (scan_type == scan_types.GENERIC_SCAN):
            numY = numX
            arr = np.ones(numY, dtype=np.float32)
            yp1ra = arr * positioners_dct['SampleY'][RBV]
            ypnts = arr * positioners_dct['SampleY'][RBV]
        else:
            yp1ra = []
            ypnts = []

    if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        # the order of the data shape is different than other scans
        # (numPol, numEv, numX) or ( # images, # rows per image, #cols per image)
        # so translate so that the shape will be standard, where numEV typically is # images
        #numY = int(e_roi[NPOINTS])
        numY = int(numX)
        numX = int(numE)
        #numE = int(numPolarities)
        #only support single polarity linespec scans for now
        numE = 1
        if (numZ <= 0):
            numP = int(numE * numY * numX)
        else:
            numP = int(numE * numY * numX * numZ)
    else:
        numE = int(numE * numPolarities)
        if (numZ <= 0):
            numP = int(numE * numY * numX)
        else:
            numP = int(numE * numY * numX * numZ)

            # with multiple energy regions the value of numP can get into the millions which will cauwse a numpy error
    # until I can figure out a work around only use 10 points for numP
    if (numP > 100000):
        # if it is more than a million setup numP for only a single energy
        if (numZ <= 0):
            numP = int(numY * numX)
        else:
            numP = int(numY * numX * numZ)

            # pull these out because they are required in EVERY NXData group
    if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        # cant use the RBV positions because they will be from teh last sp_db and not from THIS sp_db
        # so use the setpoint for this sp_db
        sx_pnts = x_roi[START]
        sy_pnts = y_roi[START]
    else:
        sx_pnts = positioners_dct['SampleX'][RBV]
        sy_pnts = positioners_dct['SampleY'][RBV]

    dct = {}
    dct_put(dct, 'SYMBOLS.numP', numP)
    dct_put(dct, 'SYMBOLS.numX', numX)
    dct_put(dct, 'SYMBOLS.numY', numY)
    dct_put(dct, 'SYMBOLS.numE', numE)

    # create numE and numP versions of data so they can just be pulled out later in
    # [numE] versions
    dct_put(dct, 'NUM_E.EV', epnts)
    dct_put(dct, 'NUM_E.COUNT_TIME', count_time)
    dct_put(dct, 'NUM_E.EPU_GAP', make_1d_array(numE, EPUGap))
    dct_put(dct, 'NUM_E.EPU_POL', pol_pnts)
    dct_put(dct, 'NUM_E.EPU_OFFSET', off_pnts)
    dct_put(dct, 'NUM_E.EPU_POL_ANGLE', angle_pnts)
    dct_put(dct, 'NUM_E.EPU_HARMONIC', make_1d_array(numE, EPUHarmonic))
    dct_put(dct, 'NUM_E.MOTOR_X', xpnts)
    dct_put(dct, 'NUM_E.MOTOR_Y', ypnts)
    if (numZ > 0):
        dct_put(dct, 'NUM_E.MOTOR_Z', zpnts)
    dct_put(dct, 'NUM_E.SLIT_X', make_1d_array(numE, SlitX))
    dct_put(dct, 'NUM_E.SLIT_Y', make_1d_array(numE, SlitY))
    dct_put(dct, 'NUM_E.M3_PITCH', make_1d_array(numE, M3STXMPitch))

    dct_put(dct, 'NUM_E.SAMPLE_X', sx_pnts)
    dct_put(dct, 'NUM_E.SAMPLE_Y', sy_pnts)

    dct_put(dct, 'NUM_E.DATA', data_numE)

    # dct_put(dct, 'NUM_E.SR_CURRENT', make_1d_array(numE, sr_current))

    # make 1d and 2d versions of data used in the /control/data section
    oned_sdata = []
    twod_sdata = []
    thrd_sdata = []

    data_E = dct_get(dct, 'NUM_E.DATA')
    data_E_shape = data_E.shape
    if (len(data_E_shape) == 1):
        cols = data_E_shape[0]
        oned_sdata = np.zeros(cols, dtype=np.float32)
        oned_sdata.fill(sr_current)
    elif (len(data_E_shape) == 2):
        rows = data_E_shape[0]
        cols = data_E_shape[1]
        twod_sdata = np.zeros((rows, cols), dtype=np.float32)
        twod_sdata.fill(sr_current)

    elif (len(data_E_shape) == 3):
        # print '_data_as_1D: 3D data not totally supported yet'
        if ((scan_type == scan_types.SAMPLE_POINT_SPECTRUM) or (scan_type == scan_types.GENERIC_SCAN)):
            cols = data_E_shape[0]
            oned_sdata = np.zeros(cols, dtype=np.float32)
            oned_sdata.fill(sr_current)
        else:
            numI = data_E_shape[0]
            # setting the following to 1 for now because for stacks I larger numI will generate a memory exception because the
            # array would be too large
            #numI = 1

            rows = data_E_shape[1]
            cols = data_E_shape[2]
            twod_sdata = np.zeros((rows, cols), dtype=np.float32)
            twod_sdata.fill(sr_current)

            thrd_sdata = np.zeros((numI, rows, cols), dtype=np.float32)
            thrd_sdata.fill(sr_current)

    dct_put(dct, 'NUM_E.SR_CURRENT.ONE_D', oned_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.TWO_D', twod_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.THREE_D', thrd_sdata)

    # dct_put(dct, 'NUM_E.ROTATION_ANGLE', make_1d_array(numE, GoniTheta))

    xpnts2 = np.tile(xpnts, numY)
    sample_x = np.tile(xpnts2, numE)

    ypnts2 = np.repeat(ypnts, numX)
    sample_y = np.tile(ypnts2, numE)

    # now [numP] versions
    # dct_put(dct, 'NUM_P.EV', np.tile(epnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EV', np.repeat(epnts, (numY * numX)))
    dct_put(dct, 'NUM_P.COUNT_TIME', np.repeat(count_time, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_POL', np.repeat(pol_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_OFFSET', np.repeat(off_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_POL_ANGLE', np.repeat(angle_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_GAP', make_1d_array(numP, EPUGap))
    dct_put(dct, 'NUM_P.EPU_HARMONIC', make_1d_array(numP, EPUHarmonic))

    if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        xpnts2 = np.tile(xpnts, numY)
        sample_x = np.tile(xpnts2, numE)
        ypnts2 = np.tile(ypnts, numX)
        sample_y = np.tile(ypnts2, numE)
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)

        dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
        dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
    else:
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)

        dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
        dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)

    if (numZ > 0):
        dct_put(dct, 'NUM_P.MOTOR_Z', np.repeat(zpnts, (numY * numX)))
    dct_put(dct, 'NUM_P.SLIT_X', make_1d_array(numP, SlitX))
    dct_put(dct, 'NUM_P.SLIT_Y', make_1d_array(numP, SlitY))
    dct_put(dct, 'NUM_P.M3_PITCH', make_1d_array(numP, M3STXMPitch))
    dct_put(dct, 'NUM_P.DATA', data_numP)
    dct_put(dct, 'NUM_P.SR_CURRENT', make_1d_array(numP, sr_current))
    # dct_put(dct, 'NUM_P.ROTATION_ANGLE', make_1d_array(numP, GoniTheta))

    dct_put(dct, 'NUM_P.LINE_POSITION', line_position)

    return (dct)

def translate_pol_id_to_stokes_vector(pol_id):
    if(pol_id is 0):
        return([0.0,0.0,0.0])
    elif(pol_id is 1):
        return([0.0,1.0,0.0])
    elif(pol_id is 2):
        return([0.0,0.0,1.0])
    elif(pol_id is 3):
        return([1.0,0.0,0.0])
    elif(pol_id is 4):
        return([1.0,1.0,0.0])
    elif(pol_id is 5):
        return([1.0,0.0,1.0])
    elif(pol_id is 6):
        return([0.0,1.0,1.0])
    elif(pol_id is 7):
        return([1.0,1.0,1.0])
    else:
        return([-1.0,-1.0,-1.0])


def _data_as_1D_new(data_dct, entry_name=None, sp_id=None,  sp_idx=None, pol_idx=None):
    """ takes the standard data_dct from the scan configuration and creates 1D [numP]
    versions of :
        energy
        count_time
        polarization
        offset
    also creates the 1D versions of all data for use in the /instrument section <data>[numP]
    and the normal NXdata section <data>[numE]

    The data is converted once here in this function then used in the rest of the make_ functions as is
    so if data needs to be converted, do it here to keep the confusion of what happens to the data to a minimum
    """

    numE = 0
    numPolarities = 0
    epnts = None
    dpnts = None
    pol_pnts = None
    off_pnts = None
    angle_pnts = None
    #sp_idx = int(sp_id)
    scan_type = dct_get(data_dct, ADO_CFG_SCAN_TYPE)

    if(sp_id is not None):
        sp_rois = dct_get(data_dct, ADO_SP_ROIS)
        sp_db = sp_rois[sp_id]
        x_roi = dct_get(sp_db, SPDB_X)
        y_roi = dct_get(sp_db, SPDB_Y)
        #z_roi = dct_get(sp_db, SPDB_Z)
        #zoneplate z
        z_roi = dct_get(sp_db, SPDB_ZZ)
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
    else:
        x_roi = dct_get(data_dct, ADO_CFG_X)
        y_roi = dct_get(data_dct, ADO_CFG_Y)
        #z_roi = dct_get(data_dct, ADO_CFG_Z)
        z_roi = dct_get(data_dct, ADO_CFG_ZZ)
        e_rois = dct_get(data_dct, ADO_CFG_EV_ROIS)

    numX = int(x_roi[NPOINTS])
    numY = int(y_roi[NPOINTS])
    numZ = int(z_roi[NPOINTS])


    if (numZ > 0):
        zp1ra = dct_get(data_dct, 'DATA.SSCANS.Z.P1RA')
        if (zp1ra is None):
            zpnts = np.linspace(z_roi[START], z_roi[STOP], numZ)
        else:
            zpnts = zp1ra[: numZ]

    positioners_dct = dct_get(data_dct, 'POSITIONERS')
    detectors_dct = dct_get(data_dct, 'DETECTORS')
    temps_dct = dct_get(data_dct, 'TEMPERATURES')
    sr_current = detectors_dct[DNM_RING_CURRENT][RBV]
    tod = data_dct['TIME_ORGANIZED_DATA']
    entry = tod[entry_name]

    for e_roi in e_rois:
        # elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
        _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
        if (epnts is not None):
            epnts = np.concatenate((epnts, _e1), axis=0)
        else:
            epnts = _e1
        numE += int(e_roi[NPOINTS])

        # count_time
        _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
        if (dpnts is not None):
            dpnts = np.concatenate((dpnts, _d1), axis=0)
        else:
            dpnts = _d1
        count_time = dpnts

    # num_pol_pnts = len(e_roi['EPU_POL_PNTS'])
    # len_rois = len(e_rois)
    #
    # _p1 = make_1d_array(e_roi[NPOINTS] * len_rois, e_roi['EPU_POL_PNTS'])
    # _o1 = make_1d_array(e_roi[NPOINTS] * len_rois, e_roi['EPU_OFF_PNTS'])
    # _a1 = make_1d_array(e_roi[NPOINTS] * len_rois, e_roi['EPU_ANG_PNTS'])
    # # numPolarities += 1
    # if(numPolarities is 0):
    #     numPolarities = len(e_roi['EPU_POL_PNTS'])
    # if (pol_pnts is None):
    #     pol_pnts = _p1
    #     off_pnts = _o1
    #     angle_pnts = _a1

    pol_pnts = entry[DNM_EPU_POLARIZATION][pol_idx][sp_idx]
    epugap_pnts = entry[DNM_EPU_GAP][pol_idx][sp_idx]
    off_pnts = entry[DNM_EPU_OFFSET][pol_idx][sp_idx]
    angle_pnts = entry[DNM_EPU_ANGLE][pol_idx][sp_idx]
    harm_pnts = entry[DNM_EPU_HARMONIC][pol_idx][sp_idx]
    stokes = translate_pol_id_to_stokes_vector(int(pol_pnts[pol_idx]))

    srcurrent_pnts = entry[DNM_RING_CURRENT][pol_idx][sp_idx]

    #data_numE = dct_get(data_dct, ADO_DATA_POINTS)
    data_numE = tod[entry_name][DNM_DEFAULT_COUNTER][pol_idx][sp_idx]

    if (isinstance(data_numE, list)):
        data_numE = np.array(data_numE)
        data_numP = data_numE.flatten()
    else:
        data_numP = data_numE.flatten()

    # make the array for the line_position used in Line Spectrum Scans
    # ls_dat = np.linspace(e_roi[START], e_roi[STOP] + e_roi[STEP], num=e_roi[NPOINTS] + 1, endpoint=True)
    ls_dat = np.linspace(x_roi[START], x_roi[STOP] + x_roi[STEP], num=x_roi[NPOINTS] + 1, endpoint=True)
    line_position = np.cumsum(np.diff(ls_dat))

    # get relevant positioner data
    EPUGap = positioners_dct[DNM_EPU_GAP][RBV]
    EPUHarmonic = positioners_dct[DNM_EPU_HARMONIC][RBV]
    # Epu_pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]

    SlitX = positioners_dct[DNM_SLIT_X][RBV]
    SlitY = positioners_dct[DNM_SLIT_Y][RBV]
    M3STXMPitch = positioners_dct[DNM_M3_PITCH][RBV]
    if (DNM_GONI_THETA in list(positioners_dct.keys())):
        GoniTheta = positioners_dct[DNM_GONI_THETA][RBV]

    x_sscan_npnts = dct_get(data_dct, 'DATA.SSCANS.X.NPTS')
    # check if the sscan was a line scan (2 points start and stop) or a point by point scan
    if (x_sscan_npnts == 2):
        xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
    else:
        # point by point so read out the points
        #xp1ra = dct_get(data_dct, 'DATA.SSCANS.X.P1RA')
        #if (xp1ra is None):
        xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
        #else:
        #    xpnts = xp1ra[: numX]

    if (numY > 0):
        #yp1ra = dct_get(data_dct, 'DATA.SSCANS.Y.P1RA')
        #if (yp1ra is None):
        ypnts = np.linspace(y_roi[START], y_roi[STOP], numY)
        #else:
        #    ypnts = yp1ra[: numY]
    else:
        if (scan_type == scan_types.GENERIC_SCAN):
            numY = numX
            arr = np.ones(numY, dtype=np.float32)
            yp1ra = arr * positioners_dct['SampleY'][RBV]
            ypnts = arr * positioners_dct['SampleY'][RBV]
        else:
            yp1ra = []
            ypnts = []

    if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        # the order of the data shape is different than other scans
        # (numPol, numEv, numX) or ( # images, # rows per image, #cols per image)
        # so translate so that the shape will be standard, where numEV typically is # images
        numY = int(e_roi[NPOINTS])
        numE = int(numPolarities)
        if (numZ <= 0):
            numP = int(numE * numY * numX)
        else:
            numP = int(numE * numY * numX * numZ)
    else:
        #numE = int(numE * numPolarities)
        numE = int(numE)
        if (numZ <= 0):
            numP = int(numE * numY * numX)
        else:
            numP = int(numE * numY * numX * numZ)

            # with multiple energy regions the value of numP can get into the millions which will cauwse a numpy error
    # until I can figure out a work around only use 10 points for numP
    if (numP > 100000):
        # if it is more than a million setup numP for only a single energy
        if (numZ <= 0):
            numP = int(numY * numX)
        else:
            numP = int(numY * numX * numZ)

            # pull these out because they are required in EVERY NXData group
    if (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        # cant use the RBV positions because they will be from teh last sp_db and not from THIS sp_db
        # so use the setpoint for this sp_db
        sx_pnts = x_roi[START]
        sy_pnts = y_roi[START]
    else:
        sx_pnts = positioners_dct['SampleX'][RBV]
        sy_pnts = positioners_dct['SampleY'][RBV]

    dct = {}
    dct_put(dct, 'SYMBOLS.numP', numP)
    dct_put(dct, 'SYMBOLS.numX', numX)
    dct_put(dct, 'SYMBOLS.numY', numY)
    dct_put(dct, 'SYMBOLS.numE', numE)



    dets_dct = data_dct['DETECTORS']
    dct['DETECTORS'] = {}
    for detector in list(dets_dct.keys()):
        data = entry[detector][pol_idx][sp_idx]
        dct_put(dct, 'DETECTORS.%s.DATA_E' % detector, data)
        if(data.ndim is 3):
            dct_put(dct, 'DETECTORS.%s.DATA_P' % detector, data.flatten('F'))
        else:
            dct_put(dct, 'DETECTORS.%s.DATA_P' % detector, np.repeat(data, numX * numY))

    # create numE and numP versions of data so they can just be pulled out later in
    # [numE] versions
    dct_put(dct, 'NUM_E.EV', epnts)
    dct_put(dct, 'NUM_E.COUNT_TIME', count_time)

    dct_put(dct, 'NUM_E.EPU_GAP', make_1d_array(numE, EPUGap))
    dct_put(dct, 'NUM_E.EPU_POL', pol_pnts)
    dct_put(dct, 'NUM_E.EPU_OFFSET', off_pnts)
    dct_put(dct, 'NUM_E.EPU_POL_ANGLE', angle_pnts)
    dct_put(dct, 'NUM_E.EPU_HARMONIC', make_1d_array(numE, EPUHarmonic))
    dct_put(dct, 'NUM_E.MOTOR_X', xpnts)
    dct_put(dct, 'NUM_E.MOTOR_Y', ypnts)
    dct_put(dct, 'NUM_E.STOKES', np.tile(stokes, (1,1)))

    if (numZ > 0):
        dct_put(dct, 'NUM_E.MOTOR_Z', zpnts)
    dct_put(dct, 'NUM_E.SLIT_X', make_1d_array(numE, SlitX))
    dct_put(dct, 'NUM_E.SLIT_Y', make_1d_array(numE, SlitY))
    dct_put(dct, 'NUM_E.M3_PITCH', make_1d_array(numE, M3STXMPitch))

    dct_put(dct, 'NUM_E.SAMPLE_X', sx_pnts)
    dct_put(dct, 'NUM_E.SAMPLE_Y', sy_pnts)

    #do all counters
    dct_put(dct, 'NUM_E.DATA', data_numE)

    # dct_put(dct, 'NUM_E.SR_CURRENT', make_1d_array(numE, sr_current))

    # make 1d and 2d versions of data used in the /control/data section
    oned_sdata = []
    twod_sdata = []
    thrd_sdata = []

    data_E = dct_get(dct, 'NUM_E.DATA')
    data_E_shape = data_E.shape
    if (len(data_E_shape) == 1):
        cols = data_E_shape[0]
        oned_sdata = np.zeros(cols, dtype=np.float32)
        oned_sdata.fill(sr_current)
    elif (len(data_E_shape) == 2):
        rows = data_E_shape[0]
        cols = data_E_shape[1]
        twod_sdata = np.zeros((rows, cols), dtype=np.float32)
        twod_sdata.fill(sr_current)

    elif (len(data_E_shape) == 3):
        # print '_data_as_1D: 3D data not totally supported yet'
        if ((scan_type == scan_types.SAMPLE_POINT_SPECTRUM) or (scan_type == scan_types.GENERIC_SCAN)):
            cols = data_E_shape[0]
            oned_sdata = np.zeros(cols, dtype=np.float32)
            oned_sdata.fill(sr_current)
        else:
            numI = data_E_shape[0]
            # setting the following to 1 for now because for stacks I larger numI will generate a memory exception because the
            # array would be too large
            #numI = 1

            rows = data_E_shape[1]
            cols = data_E_shape[2]
            twod_sdata = np.zeros((rows, cols), dtype=np.float32)
            twod_sdata.fill(sr_current)

            thrd_sdata = np.zeros((numI, rows, cols), dtype=np.float32)
            thrd_sdata.fill(sr_current)

    dct_put(dct, 'NUM_E.SR_CURRENT.ONE_D', oned_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.TWO_D', twod_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.THREE_D', thrd_sdata)

    # dct_put(dct, 'NUM_E.ROTATION_ANGLE', make_1d_array(numE, GoniTheta))

    xpnts2 = np.tile(xpnts, numY)
    sample_x = np.tile(xpnts2, numE)

    ypnts2 = np.repeat(ypnts, numX)
    sample_y = np.tile(ypnts2, numE)

    # now [numP] versions



    #stokes params
    # (w,) = pol_pnts.shape
    # s0 = np.zeros((w,), dtype=np.float32)
    # s1 = np.zeros((w,), dtype=np.float32)
    # s2 = np.zeros((w,), dtype=np.float32)
    # s3 = np.zeros((w,), dtype=np.float32)


    # dct_put(dct, 'NUM_P.EV', np.tile(epnts, (numY * numX)))
    _numXY = int(numY * numX)
    dct_put(dct, 'NUM_P.EV', np.repeat(epnts, _numXY))
    dct_put(dct, 'NUM_P.COUNT_TIME', np.repeat(count_time, _numXY))
    dct_put(dct, 'NUM_P.EPU_POL', np.repeat(pol_pnts, _numXY ))
    dct_put(dct, 'NUM_P.EPU_OFFSET', np.repeat(off_pnts, _numXY ))
    dct_put(dct, 'NUM_P.EPU_POL_ANGLE', np.repeat(angle_pnts, _numXY ))
    dct_put(dct, 'NUM_P.EPU_GAP', np.repeat(epugap_pnts, _numXY))
    dct_put(dct, 'NUM_P.EPU_HARMONIC', np.repeat(harm_pnts, _numXY))

    dct_put(dct, 'NUM_P.STOKES', np.tile(stokes, (numE, 1)))
    #dct_put(dct, 'NUM_P.STOKES_S0', np.repeat(s0, _numXY))
    #dct_put(dct, 'NUM_P.STOKES_S1', np.repeat(s1, _numXY))
    #dct_put(dct, 'NUM_P.STOKES_S2', np.repeat(s2, _numXY))
    #dct_put(dct, 'NUM_P.STOKES_S3', np.repeat(s3, _numXY))


    if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        xpnts2 = np.tile(xpnts, numY)
        sample_x = np.tile(xpnts2, numE)
        ypnts2 = np.tile(ypnts, numX)
        sample_y = np.tile(ypnts2, numE)
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)

        dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
        dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)
    else:
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)

        dct_put(dct, 'NUM_P.SAMPLE_X', sample_x)
        dct_put(dct, 'NUM_P.SAMPLE_Y', sample_y)

    if (numZ > 0):
        dct_put(dct, 'NUM_P.MOTOR_Z', np.repeat(zpnts, (numY * numX)))
    dct_put(dct, 'NUM_P.SLIT_X', make_1d_array(numP, SlitX))
    dct_put(dct, 'NUM_P.SLIT_Y', make_1d_array(numP, SlitY))
    dct_put(dct, 'NUM_P.M3_PITCH', make_1d_array(numP, M3STXMPitch))
    dct_put(dct, 'NUM_P.DATA', data_numP)
    dct_put(dct, 'NUM_P.SR_CURRENT', np.repeat(srcurrent_pnts, _numXY))
    # dct_put(dct, 'NUM_P.ROTATION_ANGLE', make_1d_array(numP, GoniTheta))

    dct_put(dct, 'NUM_P.LINE_POSITION', line_position)

    return (dct)


def _data_as_1D_polarities_are_entries(data_dct):
    """ takes the standard data_dct from the scan configuration and creates 1D [numP]
    versions of :
        energy
        count_time
        polarization
        offset
    also creates the 1D versions of all data for use in the /instrument section <data>[numP]
    and the normal NXdata section <data>[numE]
    
    The data is converted once here in this function then used in the rest of the make_ functions as is
    so if data needs to be converted, do it here
    """
    
    numE = 0
    numPolarities = 0
    epnts = None
    dpnts = None
    pol_pnts = None
    off_pnts = None
    angle_pnts = None
    scan_type = dct_get(data_dct, ADO_CFG_SCAN_TYPE)
    x_roi = dct_get(data_dct, ADO_CFG_X)
    y_roi = dct_get(data_dct,ADO_CFG_Y)
    z_roi = dct_get(data_dct,ADO_CFG_Z)
    e_rois = dct_get(data_dct, ADO_CFG_EV_ROIS)
    pol_roi = dct_get(data_dct, ADO_CFG_POL_ROI)
    numX = int(x_roi[NPOINTS])
    numY = int(y_roi[NPOINTS])
    numZ = int(z_roi[NPOINTS])
    
    if(numZ > 0):
        zp1ra = dct_get(data_dct,'DATA.SSCANS.Z.P1RA')
        zpnts = zp1ra[: numZ ]
    
    positioners_dct = dct_get(data_dct,'POSITIONERS')
    detectors_dct = dct_get(data_dct,'DETECTORS')
    sr_current = detectors_dct[DNM_RING_CURRENT][RBV]
    
#     for e_roi in e_rois:
#         #elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
#         _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
#         if(epnts is not None):
#             epnts = np.concatenate((epnts, _e1), axis=0)
#         else:
#             epnts = _e1
#         numE += e_roi[NPOINTS]
#         
#         #count_time
#         _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
#         if(dpnts is not None):
#             dpnts = np.concatenate((dpnts, _d1), axis=0)
#         else:
#             dpnts = _d1
#         count_time = dpnts
#         
#         num_pol_pnts = len(e_roi['EPU_POL_PNTS'])
#         
#         _p1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_POL_PNTS'])
#         _o1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_OFF_PNTS'])
#         _a1 = make_1d_array(e_roi[NPOINTS] * num_pol_pnts, e_roi['EPU_ANG_PNTS'])
#         #numPolarities += 1
#         numPolarities += len(e_roi['EPU_POL_PNTS'])
#         if(pol_pnts is not None):
#             pol_pnts = np.concatenate((pol_pnts, _p1), axis=0)
#             off_pnts = np.concatenate((pol_pnts, _o1), axis=0)
#             angle_pnts = np.concatenate((pol_pnts, _a1), axis=0)
#         else:
#             pol_pnts = _p1
#             off_pnts = _o1
#             angle_pnts = _a1
    #elst.append(np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS]))
    e_roi = e_rois[0]
    _e1 = np.linspace(e_roi[START], e_roi[STOP], e_roi[NPOINTS])
    if(epnts is not None):
        epnts = np.concatenate((epnts, _e1), axis=0)
    else:
        epnts = _e1
    numE += e_roi[NPOINTS]
    
    #count_time
    _d1 = make_1d_array(e_roi[NPOINTS], msec_to_sec(e_roi[DWELL]))
    if(dpnts is not None):
        dpnts = np.concatenate((dpnts, _d1), axis=0)
    else:
        dpnts = _d1
    count_time = dpnts
    
    #num_pol_pnts = len(e_roi['EPU_POL_PNTS'])
    
    _p1 = make_1d_array(e_roi[NPOINTS] , pol_roi['POL'])
    _o1 = make_1d_array(e_roi[NPOINTS] , pol_roi['OFF'])
    _a1 = make_1d_array(e_roi[NPOINTS] , pol_roi['ANGLE'])
    #numPolarities += 1
    #numPolarities += len(e_roi['EPU_POL_PNTS'])
    if(pol_pnts is not None):
        pol_pnts = np.concatenate((pol_pnts, _p1), axis=0)
        off_pnts = np.concatenate((pol_pnts, _o1), axis=0)
        angle_pnts = np.concatenate((pol_pnts, _a1), axis=0)
    else:
        pol_pnts = _p1
        off_pnts = _o1
        angle_pnts = _a1
    ###                
    data_numE = dct_get(data_dct,ADO_DATA_POINTS)
    data_numP = data_numE.flatten()
    
    #make the array for the line_position used in Line Spectrum Scans
    ls_dat = np.linspace(e_roi[START], e_roi[STOP] + e_roi[STEP], num=e_roi[NPOINTS] + 1, endpoint=True)
    line_position = np.cumsum(np.diff(ls_dat))
    
    #get relevant positioner data
    EPUGap = positioners_dct[DNM_EPU_GAP][RBV]
    EPUHarmonic = positioners_dct[DNM_EPU_HARMONIC][RBV]
    #Epu_pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]
    
    SlitX = positioners_dct[DNM_SLIT_X][RBV]
    SlitY = positioners_dct[DNM_SLIT_Y][RBV]
    M3STXMPitch = positioners_dct[DNM_M3_PITCH][RBV]
    if(DNM_GONI_THETA in list(positioners_dct.keys())):
        GoniTheta = positioners_dct[DNM_GONI_THETA][RBV]
    
    x_sscan_npnts = dct_get(data_dct,'DATA.SSCANS.X.NPTS')
    #check if the sscan was a line scan (2 points start and stop) or a point by point scan
    if(x_sscan_npnts == 2):
        xpnts = np.linspace(x_roi[START], x_roi[STOP], numX)
    else:
        #point by point so read out the points
        xp1ra = dct_get(data_dct,'DATA.SSCANS.X.P1RA')
        xpnts = xp1ra[: numX ]
    
    if(numY > 0):
        yp1ra = dct_get(data_dct,'DATA.SSCANS.Y.P1RA')
        ypnts = yp1ra[: numY ]
    else:
        yp1ra = []
        ypnts = []    
    
    if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        #the order of the data shape is different than other scans
        # (numPol, numEv, numX) or ( # images, # rows per image, #cols per image)
        # so translate so that the shape will be standard, where numEV typically is # images
        numY = int(e_roi[NPOINTS])
        numE = numPolarities
        if(numZ <= 0):
            numP = numE * numY * numX 
        else:
            numP = numE * numY * numX * numZ
    else:    
        #numE = numE * numPolarities
        if(numZ <= 0):
            numP = numE * numY * numX 
        else:
            numP = numE * numY * numX * numZ 
    
    
    
    images_data = np.zeros((numPolarities, numE, numY, numX), dtype=np.int32)
    image_idxs = []
    for i in range(numPolarities):
        image_idxs.append(np.arange(i, numE, numPolarities))
        
    #for idxs in image_idxs:
    for i in range(numPolarities):
        idxs = image_idxs[i]
        y = 0
        for j in idxs:
            images_data[i][y] = data_numE[j]
            y += 1
    
    
    dct = {}
    dct_put(dct, 'SYMBOLS.numP', numP)
    dct_put(dct, 'SYMBOLS.numX', numX)
    dct_put(dct, 'SYMBOLS.numY', numY)
    dct_put(dct, 'SYMBOLS.numE', numE)
    
    dct_put(dct, 'POLARITY.IMAGES', images_data)
    dct_put(dct, 'POLARITY.NUM_POLS', numPolarities)
    
    #create numE and numP versions of data so they can just be pulled out later in 
    #[numE] versions
    dct_put(dct, 'NUM_E.EV', epnts )
    dct_put(dct, 'NUM_E.COUNT_TIME', count_time)
    dct_put(dct, 'NUM_E.EPU_GAP',make_1d_array(numE, EPUGap))
    dct_put(dct, 'NUM_E.EPU_POL',pol_pnts)
    dct_put(dct, 'NUM_E.EPU_OFFSET',off_pnts)
    dct_put(dct, 'NUM_E.EPU_POL_ANGLE',angle_pnts)
    dct_put(dct, 'NUM_E.EPU_HARMONIC', make_1d_array(numE, EPUHarmonic))
    dct_put(dct, 'NUM_E.MOTOR_X', xpnts)
    dct_put(dct, 'NUM_E.MOTOR_Y', ypnts)
    if(numZ > 0):
        dct_put(dct, 'NUM_E.MOTOR_Z', zpnts)
    dct_put(dct, 'NUM_E.SLIT_X',make_1d_array(numE, SlitX))
    dct_put(dct, 'NUM_E.SLIT_Y',make_1d_array(numE, SlitY))
    dct_put(dct, 'NUM_E.M3_PITCH',make_1d_array(numE, M3STXMPitch))
    dct_put(dct, 'NUM_E.DATA', data_numE)
    
    
    
    
    #dct_put(dct, 'NUM_E.SR_CURRENT', make_1d_array(numE, sr_current))
    
    #make 1d and 2d versions of data used in the /control/data section
    oned_sdata = []
    twod_sdata = []
    thrd_sdata = []
    
    data_E = dct_get(dct, 'NUM_E.DATA')
    data_E_shape = data_E.shape
    if(len(data_E_shape) == 1):
        cols = data_E_shape[0]
        oned_sdata = np.zeros(cols, dtype=np.float32)
        oned_sdata.fill(sr_current)
    elif(len(data_E_shape) == 2):
        rows = data_E_shape[0]    
        cols = data_E_shape[1]
        twod_sdata = np.zeros((rows, cols), dtype=np.float32)
        twod_sdata.fill(sr_current)
        
    elif(len(data_E_shape) == 3):
        print('_data_as_1D: 3D data not totally supported yet')
        if(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            cols = data_E_shape[0]    
            oned_sdata = np.zeros(cols, dtype=np.float32)
            oned_sdata.fill(sr_current)
        else:
            numI = data_E_shape[0]    
            rows = data_E_shape[1]    
            cols = data_E_shape[2]
            twod_sdata = np.zeros((rows, cols), dtype=np.float32)
            twod_sdata.fill(sr_current)
            
            thrd_sdata = np.zeros((numI, rows, cols), dtype=np.float32)
            thrd_sdata.fill(sr_current)

    dct_put(dct, 'NUM_E.SR_CURRENT.ONE_D', oned_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.TWO_D', twod_sdata)
    dct_put(dct, 'NUM_E.SR_CURRENT.THREE_D', thrd_sdata)
        
    #dct_put(dct, 'NUM_E.ROTATION_ANGLE', make_1d_array(numE, GoniTheta))
    
    xpnts2 =  np.tile(xpnts, numY)
    sample_x =  np.tile(xpnts2, numE)
    
    ypnts2 = np.repeat(ypnts, numX)
    sample_y = np.tile(ypnts2, numE)
    
    #now [numP] versions
    #dct_put(dct, 'NUM_P.EV', np.tile(epnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EV', np.repeat(epnts, (numY * numX)))
    dct_put(dct, 'NUM_P.COUNT_TIME', np.repeat(count_time, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_POL', np.repeat(pol_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_OFFSET', np.repeat(off_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_POL_ANGLE',np.repeat(angle_pnts, (numY * numX)))
    dct_put(dct, 'NUM_P.EPU_GAP',make_1d_array(numP, EPUGap))
    dct_put(dct, 'NUM_P.EPU_HARMONIC',make_1d_array(numP, EPUHarmonic))
    
    if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
        xpnts2 =  np.tile(xpnts, numY)
        sample_x =  np.tile(xpnts2, numE)
        ypnts2 = np.tile(ypnts, numX)
        sample_y = np.tile(ypnts2, numE)
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
    else:
        dct_put(dct, 'NUM_P.MOTOR_X', sample_x)
        dct_put(dct, 'NUM_P.MOTOR_Y', sample_y)
    
    if(numZ > 0):
        dct_put(dct, 'NUM_P.MOTOR_Z', np.repeat(zpnts, (numY * numX)))
    dct_put(dct, 'NUM_P.SLIT_X',make_1d_array(numP, SlitX))
    dct_put(dct, 'NUM_P.SLIT_Y',make_1d_array(numP, SlitY))
    dct_put(dct, 'NUM_P.M3_PITCH',make_1d_array(numP, M3STXMPitch))
    dct_put(dct, 'NUM_P.DATA', data_numP)
    dct_put(dct, 'NUM_P.SR_CURRENT', make_1d_array(numP, sr_current))
    #dct_put(dct, 'NUM_P.ROTATION_ANGLE', make_1d_array(numP, GoniTheta))
    
    dct_put(dct, 'NUM_P.LINE_POSITION', line_position)
    
    
    return(dct)

def make_string_data(nf, name, sdata, size=None):
    if(size):
        num_chars = size
    else:
        num_chars = len(sdata)
    #nf.makedata(name,'char',[num_chars])
    nf.create_dataset(name=name, data=sdata)
    #nf.opendata(name)
    #nf.putdata(sdata)
    #nf.closedata()

def _string_attr(nxgrp, name, sdata):
    if(nxgrp is None):
        return
    
    if(type(sdata) == str):
        nxgrp.attrs[name] = str(sdata, "utf-8")
    else:    
        nxgrp.attrs[name] = sdata
    
def _list_attr(nxgrp, name, lstdata):
    if(nxgrp is None):
        return
    if(name in list(nxgrp.attrs.keys())):
        nxgrp.attrs[name][()] = lstdata
    else:
        nxgrp.attrs[name] = lstdata

def make_float_attr(nxgrp, name, fdata):
    if(name in list(nxgrp.attrs.keys())):
        nxgrp.attrs[name][()] = fdata
    else:
        nxgrp.attrs[name] = fdata    

def make_class_type_attr(nxgrp, type):
    nxgrp._string_attr('NX_class',type)    

def make_date_time(nf, name, s, size=None):
    if(size):
        num_chars = size
    else:
        num_chars = len(s)
    nf.makedata(name,'char',[num_chars])
    nf.opendata(name)
    nf.putdata(s)
    nf.closedata()
    
def _group(nxgrp, name, nxdata_type):
    if(name == ''):
        return
    grp = nxgrp.create_group(name)
    _string_attr(grp, 'NX_class', nxdata_type)
    return(grp)

def _dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
    '''
    apply compression if the data is an array
    '''
    #grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)    
    if(type(data) == np.ndarray):
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None, compression="gzip")
    else:    
        grp = nxgrp.create_dataset(name=name, data=data, maxshape=None)
    _string_attr(grp, 'NX_class', nxdata_type)
    if(type(nx_units) is dict):
        _string_attr(grp, 'NX_units', nx_units['units'])
    else:
        _string_attr(grp, 'NX_units', nx_units)
    if('doc' in list(dset.keys())):
        _string_attr(grp, 'doc', dset['doc'])
    return(grp)

def make_data_section(nf, name, data_dct={}, scan_type=scan_types.SAMPLE_IMAGE, modify=False, dddata=None):
    """
    supported scan types from NXstxm def
    sample point spectrum: (photon_energy,)
    sample line spectrum: (photon_energy, sample_y/sample_x)
    sample image: (sample_y, sample_x)
    sample image stack: (photon_energy, sample_y, sample_x)
    sample focus: (zoneplate_z, sample_y/sample_x)
    osa image: (osa_y, osa_x)
    osa focus: (zoneplate_z, osa_y/osa_x)
    detector image: (detector_y, detector_x)

    because the /control section is required to be closely tied to the data section we also build the /control group here

    NOTE: the axis2000 read_nexus.pro file assumes that the axis '_indices' are in the following order:
        2D data: y,  x or 0, 1
        3D data: e, y, x or 0, 1, 2

    Also NOTE that every NXdata group MUST contain:
        _string_attr(src_grp, 'sample_y_indices', '1')
        _string_attr(src_grp, 'sample_x_indices', '2')

        as per Ben's email from March 30 2016
        Hi Russ,
       Sorry to take so long to reply (email got buried). The 'sample_x' and 'sample_y' fields will contain
       what it says, not a copy of what is being scanned. If the sample is not being scanned, then there will
       only be a single value in each, as the position of the sample will be fixed.

        Cheers,
        Ben



    """
    nume_pnts = dct_get(data_dct, 'SYMBOLS.numE')
    #if((scan_type == scan_types.SAMPLE_IMAGE + IMAGE_PXP) or (scan_type == scan_types.SAMPLE_IMAGE + IMAGE_LXL)):
    if(scan_type == scan_types.SAMPLE_IMAGE):
        if(nume_pnts > 1):
            scan_type = scan_types.SAMPLE_IMAGE_STACK
        else:
            scan_type = scan_types.SAMPLE_IMAGE

    x_roi = dct_get(data_dct, ADO_CFG_X)
    y_roi = dct_get(data_dct, ADO_CFG_Y)
    z_roi = dct_get(data_dct, ADO_CFG_Z)

    data_E = dct_get(data_dct, 'NUM_E.DATA')
    e_pnts_E = dct_get(data_dct, 'NUM_E.EV')
    pol_pnts_E = dct_get(data_dct, 'NUM_E.EPU_POL')
    off_pnts_E = dct_get(data_dct, 'NUM_E.EPU_OFFSET')
    count_time_E = dct_get(data_dct, 'NUM_E.COUNT_TIME')
    xpnts_E = dct_get(data_dct,'NUM_E.MOTOR_X')
    ypnts_E = dct_get(data_dct,'NUM_E.MOTOR_Y')
    zpnts_E = dct_get(data_dct,'NUM_E.MOTOR_Z')

    sxpnts_E = dct_get(data_dct,'NUM_E.SAMPLE_X')
    sypnts_E = dct_get(data_dct,'NUM_E.SAMPLE_Y')

    data_P = dct_get(data_dct, 'NUM_P.DATA')
    e_pnts_P = dct_get(data_dct, 'NUM_P.EV')
    pol_pnts_P = dct_get(data_dct, 'NUM_P.EPU_POL')
    off_pnts_P = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
    count_time_P = dct_get(data_dct, 'NUM_P.COUNT_TIME')
    xpnts_P = dct_get(data_dct,'NUM_P.MOTOR_X')
    ypnts_P = dct_get(data_dct,'NUM_P.MOTOR_Y')
    sxpnts_P = dct_get(data_dct,'NUM_P.SAMPLE_X')
    sypnts_P = dct_get(data_dct,'NUM_P.SAMPLE_Y')

    line_position_P = dct_get(data_dct,'NUM_P.LINE_POSITION')

    oneD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.ONE_D')
    twoD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.TWO_D')
    thrD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.THREE_D')

    if(z_roi[NPOINTS] > 0):
        zpnts = dct_get(data_dct,'NUM_E.MOTOR_Z')

    #type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK] #, scan_types.SAMPLE_FOCUS]
    type_a_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY] #, scan_types.SAMPLE_FOCUS]

    if(name not in list(nf.keys())):
        src_grp = _group(nf, name, 'NXdata')
        _dataset(src_grp, 'stxm_scan_type', scan_types[scan_type].replace('_', ' '), 'NX_CHAR')
    else:
        src_grp = nf[name]

    if('control' not in list(nf.keys())):
        ctrl_grp = _group(nf, 'control', 'NXmonitor')
    else:
        ctrl_grp = nf['control']
        modify = True

    #
    # if(not modify):
    #     src_grp = _group(nf, name, 'NXdata')
    #     _dataset(src_grp, 'stxm_scan_type', scan_types[scan_type].replace('_', ' '), 'NX_CHAR')
    #     ctrl_grp = _group(nf, 'control', 'NXmonitor')
    # else:
    #     src_grp = nf[name]
    #     ctrl_grp = nf['control']

    if(scan_type in type_a_scans):
        if(modify):
            #modify existing nexus file
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            #src_grp['signal'][()] = nxkd.NXD_DATA
            #replace_string_data(src_grp, 'src_grp', 'zone plate #%d' % zp_sel[RBV])

            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            #ctrl_grp['signal'][()] = nxkd.NXD_DATA

        else:
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)

            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

        #set attributes
        if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            if(modify):
                #src_grp['axes'][()] = ['energy','line_position']
                src_grp['line_position'][()] = line_position_P
                src_grp[nxkd.NXD_DATA][()] = data_E
                #the shape for a line spec scan that is for a line that has 150x150 points and is over 40 eV
                # has the shape 1x150x40 so set the indices accordingly
                #src_grp['energy_indices'][()] = '0'
                #src_grp['line_position_indices'][()] = '1'
                #src_grp['sample_y_indices'][()] = '1'
                #src_grp['sample_x_indices'][()] = '1'
                #src_grp['sample_x'] = sxpnts_E
                #src_grp['sample_y'] = sypnts_E

                ctrl_grp[nxkd.NXD_DATA][()] = data_E
                ctrl_grp['line_position'][()] = line_position_P
                #ctrl_grp['sample_x'] = sxpnts_E
                #ctrl_grp['sample_y'] = sypnts_E
                #ctrl_grp['axes'][()] = ['energy','line_position']
                #ctrl_grp['energy_indices'][()] = '0'
                #ctrl_grp['line_position_indices'][()] = '1'
                #ctrl_grp['sample_y_indices'][()] = '1'
                #ctrl_grp['sample_x_indices'][()] = '1'
            else:
                _list_attr(src_grp, 'axes', ['energy','line_position'])
#                _dataset(src_grp, 'line_position', line_position_P, 'NX_FLOAT')
                _dataset(src_grp, 'line_position', list(range(xpnts_E.shape[0])), 'NX_FLOAT')
                _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
                #the shape for a line spec scan that is for a line that has 150x150 points and is over 40 eV
                # has the shape 1x150x40 so set the indices accordingly
                _string_attr(src_grp, 'energy_indices', '0')
#                _string_attr(src_grp, 'line_position_indices', '1')
                _string_attr(src_grp, 'sample_y_indices', '1')
                _string_attr(src_grp, 'sample_x_indices', '1')

                _dataset(ctrl_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
                _dataset(ctrl_grp, 'line_position', line_position_P, 'NX_FLOAT')
                _list_attr(ctrl_grp, 'axes', ['energy','line_position'])
                _string_attr(ctrl_grp, 'energy_indices', '0')
#                _string_attr(ctrl_grp, 'line_position_indices', '1')
                _string_attr(ctrl_grp, 'sample_y_indices', '1')
                _string_attr(ctrl_grp, 'sample_x_indices', '1')



        elif(scan_type == scan_types.SAMPLE_IMAGE):
            if(modify):
                src_grp[nxkd.NXD_DATA][()] = data_E
                #src_grp['axes'][()] =  ['sample_y', 'sample_x']
                #src_grp['sample_y_indices'][()] = '0'
                #src_grp['sample_x_indices'][()] = '1'

                #ctrl_grp[nxkd.NXD_DATA][()] =  twoD_srdata
                ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
                #ctrl_grp['axes'][()] =  ['sample_y', 'sample_x']
                #ctrl_grp['sample_y_indices'][()] =  '0'
                #ctrl_grp['sample_x_indices'][()] =  '1'
            else:
                _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
                _list_attr(src_grp, 'axes', ['sample_y', 'sample_x'])
                _string_attr(src_grp, 'sample_y_indices', '0')
                _string_attr(src_grp, 'sample_x_indices', '1')

                _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
                _list_attr(ctrl_grp, 'axes', ['sample_y', 'sample_x'])
                _string_attr(ctrl_grp, 'sample_y_indices', '0')
                _string_attr(ctrl_grp, 'sample_x_indices', '1')

        elif((scan_type == scan_types.SAMPLE_IMAGE_STACK)or (scan_type == scan_types.TOMOGRAPHY)):
            if(modify):
                if (dddata is not None):
                    src_grp[nxkd.NXD_DATA][()] = dddata
                else:
                    src_grp[nxkd.NXD_DATA][()] =  data_E
                #src_grp['axes'][()] =  ['energy', 'sample_y', 'sample_x']
                #src_grp['energy_indices'][()] = '0'
                #src_grp['sample_y_indices'][()] = '1'
                #src_grp['sample_x_indices'][()] = '2'
                src_grp['sample_x'][()] = sxpnts_E
                src_grp['sample_y'][()] = sypnts_E

                if(dddata is not None):
                    ctrl_grp[nxkd.NXD_DATA][()] = dddata
                else:
                    ctrl_grp[nxkd.NXD_DATA][()] =  thrD_srdata

                #ctrl_grp['sample_x'][()] = sxpnts_E
                #ctrl_grp['sample_y'][()] = sypnts_E
                #ctrl_grp['axes'][()] =  ['energy', 'sample_y', 'sample_x']
                #ctrl_grp['energy_indices'][()] = '0'
                #ctrl_grp['sample_y_indices'][()] = '1'
                #ctrl_grp['sample_x_indices'][()] = '2'
            else:
                if (dddata is not None):
                    _dataset(src_grp, nxkd.NXD_DATA, dddata, 'NX_NUMBER')
                else:
                    _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')

                _list_attr(src_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
                _string_attr(src_grp, 'energy_indices', '0')
                _string_attr(src_grp, 'sample_y_indices', '1')
                _string_attr(src_grp, 'sample_x_indices', '2')
                #_dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
                #_dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')

                if (dddata is not None):
                    _dataset(ctrl_grp, nxkd.NXD_DATA, dddata, 'NX_NUMBER')
                else:
                    _dataset(ctrl_grp, nxkd.NXD_DATA, thrD_srdata, 'NX_NUMBER')

                _list_attr(ctrl_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
                _string_attr(ctrl_grp, 'energy_indices', '0')
                _string_attr(ctrl_grp, 'sample_y_indices', '1')
                _string_attr(ctrl_grp, 'sample_x_indices', '2')
                #_dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
                #_dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')

    elif(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        if(modify):
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            src_grp[nxkd.NXD_DATA][()] = data_P
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            #src_grp['axes'][()] = ['energy']
            #src_grp['energy_indices'][()] = '0'
            #src_grp['sample_y_indices'][()] = '1'
            #src_grp['sample_x_indices'][()] = '2'

            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = oneD_srdata
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            #ctrl_grp['axes'][()] = ['energy']
            #ctrl_grp['energy_indices'][()] = '0'
        else:
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, nxkd.NXD_DATA, data_P, 'NX_NUMBER')
            _list_attr(src_grp, 'axes', ['energy'])
            _string_attr(src_grp, 'energy_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')


            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
            _dataset(ctrl_grp, nxkd.NXD_DATA, oneD_srdata, 'NX_NUMBER')
            _list_attr(ctrl_grp, 'axes', ['energy'])
            _string_attr(ctrl_grp, 'energy_indices', '0')

    elif(scan_type == scan_types.OSA_IMAGE):
        if(modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['osa_x'][()] = xpnts_E
            src_grp['osa_y'][()] = ypnts_E
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            #src_grp['axes'][()] = ['osa_y', 'osa_x']
            #src_grp['osa_y_indices'][()] = '0'
            #src_grp['osa_x_indices'][()] = '1'
            #src_grp['signal'][()] =  nxkd.NXD_DATA
            #src_grp['sample_y_indices'][()] = '1'
            #src_grp['sample_x_indices'][()] = '2'
            src_grp['energy'][()] =  e_pnts_E

            ctrl_grp['energy'][()] =  e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] =  twoD_srdata
            ctrl_grp['osa_x'][()] =  xpnts_E
            ctrl_grp['osa_y'][()] =  ypnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            #ctrl_grp['axes'][()] =  ['osa_y', 'osa_x']
            #ctrl_grp['osa_y_indices'][()] = '0'
            #ctrl_grp['osa_x_indices'][()] = '1'
            #ctrl_grp['signal'][()] = nxkd.NXD_DATA
            #ctrl_grp['sample_y_indices'][()] = '1'
            #ctrl_grp['sample_x_indices'][()] = '2'
            ctrl_grp['energy'][()] =  e_pnts_E

        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['osa_y', 'osa_x'])
            _string_attr(src_grp, 'osa_y_indices', '0')
            _string_attr(src_grp, 'osa_x_indices', '1')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
#            _string_attr(src_grp, 'sample_y_indices', '1')
#            _string_attr(src_grp, 'sample_x_indices', '2')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')

            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['osa_y', 'osa_x'])
            _string_attr(ctrl_grp, 'osa_y_indices', '0')
            _string_attr(ctrl_grp, 'osa_x_indices', '1')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif(scan_type == scan_types.OSA_FOCUS):
        if(modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['osa_x'][()] = xpnts_E
            src_grp['osa_y'][()] = ypnts_E
            src_grp['zoneplate_z'][()] = zpnts_E
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            #src_grp['axes'][()] = ['zoneplate_z', 'osa_y', 'osa_x']
            #src_grp['zoneplate_z_indices'][()] = '0'
            #src_grp['osa_y_indices'][()] = '1'
            #src_grp['osa_x_indices'][()] = '2'
            #src_grp['signal'][()] = nxkd.NXD_DATA
            #src_grp['sample_y_indices'][()] = '1'
            #src_grp['sample_x_indices'][()] = '2'
            src_grp['energy'][()] =  e_pnts_E


            ctrl_grp['energy'][()] =  e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['osa_x'][()] = xpnts_E
            ctrl_grp['osa_y'][()] = ypnts_E
            ctrl_grp['zoneplate_z'][()] = zpnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            #ctrl_grp['axes'][()] = ['zoneplate_z', 'osa_y', 'osa_x']
            #ctrl_grp['zoneplate_z_indices'][()] = '0'
            #ctrl_grp['osa_y_indices'][()] = '1'
            #ctrl_grp['osa_x_indices'][()] =  '2'
            #ctrl_grp['signal'][()] =  nxkd.NXD_DATA


        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['zoneplate_z', 'osa_y', 'osa_x'])
            _string_attr(src_grp, 'zoneplate_z_indices', '0')
            _string_attr(src_grp, 'osa_y_indices', '1')
            _string_attr(src_grp, 'osa_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')

            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')

            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')

            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['zoneplate_z', 'osa_y', 'osa_x'])
            _string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            _string_attr(ctrl_grp, 'osa_y_indices', '1')
            _string_attr(ctrl_grp, 'osa_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif(scan_type == scan_types.SAMPLE_FOCUS):
        if(modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['zoneplate_z'][()] =  zpnts_E
            #src_grp['axes'] = ['zoneplate_z', 'sample_y', 'sample_x']
            #_string_attr(src_grp, 'zoneplate_z_indices', '0')
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')
            #_string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            src_grp['energy'][()] = e_pnts_E
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')

            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['zoneplate_z'][()] = zpnts_E
            #ctrl_grp['axes'] = ['zoneplate_z', 'sample_y', 'sample_x']
            #_string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            #_string_attr(ctrl_grp, 'sample_y_indices', '1')
            #_string_attr(ctrl_grp, 'sample_x_indices', '2')
            #_string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['zoneplate_z', 'sample_y', 'sample_x'])
            _string_attr(src_grp, 'zoneplate_z_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')

            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['zoneplate_z', 'sample_y', 'sample_x'])
            _string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            _string_attr(ctrl_grp, 'sample_y_indices', '1')
            _string_attr(ctrl_grp, 'sample_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif(scan_type == scan_types.DETECTOR_IMAGE):
        if(modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['detector_x'][()] = xpnts_E
            src_grp['detector_y'][()] = ypnts_E
            #src_grp['axes'] = ['detector_y', 'detector_x']
            #_string_attr(src_grp, 'detector_y_indices', '0')
            #_string_attr(src_grp, 'detector_x_indices', '1')
            #_string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()]= sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')

            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['detector_x'][()] = xpnts_E
            ctrl_grp['detector_y'][()] = ypnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            #ctrl_grp['axes'] = ['detector_y', 'detector_x']
            #_string_attr(ctrl_grp, 'detector_y_indices', '0')
            #_string_attr(ctrl_grp, 'detector_x_indices', '1')
            #_string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'detector_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'detector_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['detector_y', 'detector_x'])
            _string_attr(src_grp, 'detector_y_indices', '0')
            _string_attr(src_grp, 'detector_x_indices', '1')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')


            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'detector_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'detector_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['detector_y', 'detector_x'])
            _string_attr(ctrl_grp, 'detector_y_indices', '0')
            _string_attr(ctrl_grp, 'detector_x_indices', '1')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
    else:
        if(modify):
            #'generic scan'
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            #src_grp['axes'] = ['energy', 'sample_y', 'sample_x']
            #_string_attr(src_grp, 'energy_indices', '0')
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')
            #_string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')

            ctrl_grp[nxkd.NXD_DATA][()] = oneD_srdata
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            #ctrl_grp['axes'] = ['energy', 'sample_y', 'sample_x']
            #_string_attr(ctrl_grp, 'energy_indices', '0')
            #_string_attr(ctrl_grp, 'sample_y_indices', '1')
            #_string_attr(ctrl_grp, 'sample_x_indices', '2')
            #_string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            #'generic scan'
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
            _string_attr(src_grp, 'energy_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)

            _dataset(ctrl_grp, nxkd.NXD_DATA, oneD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
            _string_attr(ctrl_grp, 'energy_indices', '0')
            _string_attr(ctrl_grp, 'sample_y_indices', '1')
            _string_attr(ctrl_grp, 'sample_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)


def make_data_section_new(nf, name, data_dct={}, scan_type=scan_types.SAMPLE_IMAGE, modify=False, dddata=None):
    """
    supported scan types from NXstxm def
    sample point spectrum: (photon_energy,)
    sample line spectrum: (photon_energy, sample_y/sample_x)
    sample image: (sample_y, sample_x)
    sample image stack: (photon_energy, sample_y, sample_x)
    sample focus: (zoneplate_z, sample_y/sample_x)
    osa image: (osa_y, osa_x)
    osa focus: (zoneplate_z, osa_y/osa_x)
    detector image: (detector_y, detector_x)

    because the /control section is required to be closely tied to the data section we also build the /control group here

    NOTE: the axis2000 read_nexus.pro file assumes that the axis '_indices' are in the following order:
        2D data: y,  x or 0, 1
        3D data: e, y, x or 0, 1, 2

    Also NOTE that every NXdata group MUST contain:
        _string_attr(src_grp, 'sample_y_indices', '1')
        _string_attr(src_grp, 'sample_x_indices', '2')

        as per Ben's email from March 30 2016
        Hi Russ,
       Sorry to take so long to reply (email got buried). The 'sample_x' and 'sample_y' fields will contain
       what it says, not a copy of what is being scanned. If the sample is not being scanned, then there will
       only be a single value in each, as the position of the sample will be fixed.

        Cheers,
        Ben



    """
    nume_pnts = dct_get(data_dct, 'SYMBOLS.numE')

    if (scan_type == scan_types.SAMPLE_IMAGE):
        if (nume_pnts > 1):
            scan_type = scan_types.SAMPLE_IMAGE_STACK
        else:
            scan_type = scan_types.SAMPLE_IMAGE

    x_roi = dct_get(data_dct, ADO_CFG_X)
    y_roi = dct_get(data_dct, ADO_CFG_Y)
    z_roi = dct_get(data_dct, ADO_CFG_Z)

    data_E = dct_get(data_dct, 'DETECTORS.%s.DATA_E' % name)
    data_P = dct_get(data_dct, 'DETECTORS.%s.DATA_P' % name)
    stokes_P = dct_get(data_dct, 'NUM_P.STOKES')


    #data_E = dct_get(data_dct, 'NUM_E.DATA')
    e_pnts_E = dct_get(data_dct, 'NUM_E.EV')
    pol_pnts_E = dct_get(data_dct, 'NUM_E.EPU_POL')
    off_pnts_E = dct_get(data_dct, 'NUM_E.EPU_OFFSET')
    count_time_E = dct_get(data_dct, 'NUM_E.COUNT_TIME')
    xpnts_E = dct_get(data_dct, 'NUM_E.MOTOR_X')
    ypnts_E = dct_get(data_dct, 'NUM_E.MOTOR_Y')
    zpnts_E = dct_get(data_dct, 'NUM_E.MOTOR_Z')
    stokes_E = dct_get(data_dct, 'NUM_E.STOKES')

    sxpnts_E = dct_get(data_dct, 'NUM_E.SAMPLE_X')
    sypnts_E = dct_get(data_dct, 'NUM_E.SAMPLE_Y')

    # #data_P = dct_get(data_dct, 'NUM_P.DATA')
    # e_pnts_P = dct_get(data_dct, 'NUM_P.EV')
    # pol_pnts_P = dct_get(data_dct, 'NUM_P.EPU_POL')
    # off_pnts_P = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
    # count_time_P = dct_get(data_dct, 'NUM_P.COUNT_TIME')
    # xpnts_P = dct_get(data_dct, 'NUM_P.MOTOR_X')
    # ypnts_P = dct_get(data_dct, 'NUM_P.MOTOR_Y')
    # sxpnts_P = dct_get(data_dct, 'NUM_P.SAMPLE_X')
    # sypnts_P = dct_get(data_dct, 'NUM_P.SAMPLE_Y')

    line_position_P = dct_get(data_dct, 'NUM_P.LINE_POSITION')

    # oneD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.ONE_D')
    # twoD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.TWO_D')
    # thrD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.THREE_D')

    if (z_roi[NPOINTS] > 0):
        zpnts = dct_get(data_dct, 'NUM_E.MOTOR_Z')

    # type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK] #, scan_types.SAMPLE_FOCUS]
    type_a_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK]  # , scan_types.SAMPLE_FOCUS]

    if (name not in list(nf.keys())):
        src_grp = _group(nf, name, 'NXdata')
        _dataset(src_grp, 'stxm_scan_type', scan_types[scan_type].replace('_', ' '), 'NX_CHAR')
    else:
        src_grp = nf[name]


    if (scan_type in type_a_scans):
        if (modify):
            # modify existing nexus file
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            src_grp['stokes'][()] = stokes_E

            # src_grp['signal'][()] = nxkd.NXD_DATA
            # replace_string_data(src_grp, 'src_grp', 'zone plate #%d' % zp_sel[RBV])
        else:
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'stokes', stokes_E, 'NX_FLOAT')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)

        # set attributes
        if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            if (modify):
                # src_grp['axes'][()] = ['energy','line_position']
                src_grp['line_position'][()] = line_position_P
                src_grp[nxkd.NXD_DATA][()] = data_E
                # the shape for a line spec scan that is for a line that has 150x150 points and is over 40 eV
                # has the shape 1x150x40 so set the indices accordingly
                # src_grp['energy_indices'][()] = '0'
                # src_grp['line_position_indices'][()] = '1'
                # src_grp['sample_y_indices'][()] = '1'
                # src_grp['sample_x_indices'][()] = '1'
                # src_grp['sample_x'] = sxpnts_E
                # src_grp['sample_y'] = sypnts_E


            else:
                # NOTE that the order that the axes appear in the folling list determines what is in teh shape of the data
                # axes = [ axis0, axis1, axis2, axis3, ...]
                # data.shape = (axis0, axis1, axis2, axis3, ...)
                # so for default numpy it uses C type-style which is (row, column)
                # Fortran is (column, row)
                # anyway the following defines the data to be (rows=line_position, columns=energy)
                _list_attr(src_grp, 'axes', ['line_position', 'energy'])
                # the shape for a line spec scan that is for a line that has 150x150 points and is over 40 eV
                # has the shape 1x150x40 so set the indices accordingly
                # BUT it should only be two D so it should be 150x40
                _dataset(src_grp, 'line_position', line_position_P, 'NX_FLOAT')
                #_dataset(src_grp, 'line_position', range(xpnts_E.shape[0]), 'NX_FLOAT')
                #_dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
                _dataset(src_grp, nxkd.NXD_DATA, data_E[0], 'NX_NUMBER')

                # these appear to be ignored by axis2000 but make sure they are correct anyway
                _string_attr(src_grp, 'line_position_indices', '0')
                _string_attr(src_grp, 'sample_y_indices', '0')
                _string_attr(src_grp, 'sample_x_indices', '0')
                _string_attr(src_grp, 'energy_indices', '1')




        elif (scan_type == scan_types.SAMPLE_IMAGE):
            if (modify):
                src_grp[nxkd.NXD_DATA][()] = data_E
                # src_grp['axes'][()] =  ['sample_y', 'sample_x']
                # src_grp['sample_y_indices'][()] = '0'
                # src_grp['sample_x_indices'][()] = '1'


            else:
                _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
                _list_attr(src_grp, 'axes', ['sample_y', 'sample_x'])
                _string_attr(src_grp, 'sample_y_indices', '0')
                _string_attr(src_grp, 'sample_x_indices', '1')



        elif (scan_type == scan_types.SAMPLE_IMAGE_STACK):
            if (modify):
                if (dddata is not None):
                    src_grp[nxkd.NXD_DATA][()] = dddata
                else:
                    src_grp[nxkd.NXD_DATA][()] = data_E
                # src_grp['axes'][()] =  ['energy', 'sample_y', 'sample_x']
                # src_grp['energy_indices'][()] = '0'
                # src_grp['sample_y_indices'][()] = '1'
                # src_grp['sample_x_indices'][()] = '2'
                src_grp['sample_x'][()] = sxpnts_E
                src_grp['sample_y'][()] = sypnts_E


            else:
                if (dddata is not None):
                    _dataset(src_grp, nxkd.NXD_DATA, dddata, 'NX_NUMBER')
                else:
                    _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')

                _list_attr(src_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
                _string_attr(src_grp, 'energy_indices', '0')
                _string_attr(src_grp, 'sample_y_indices', '1')
                _string_attr(src_grp, 'sample_x_indices', '2')
                # _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
                # _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')



    elif (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        if (modify):
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            src_grp[nxkd.NXD_DATA][()] = data_P
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            # src_grp['axes'][()] = ['energy']
            # src_grp['energy_indices'][()] = '0'
            # src_grp['sample_y_indices'][()] = '1'
            # src_grp['sample_x_indices'][()] = '2'

        else:
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, nxkd.NXD_DATA, data_P, 'NX_NUMBER')
            _list_attr(src_grp, 'axes', ['energy'])
            _string_attr(src_grp, 'energy_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')


    elif (scan_type == scan_types.OSA_IMAGE):
        if (modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['osa_x'][()] = xpnts_E
            src_grp['osa_y'][()] = ypnts_E
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            # src_grp['axes'][()] = ['osa_y', 'osa_x']
            # src_grp['osa_y_indices'][()] = '0'
            # src_grp['osa_x_indices'][()] = '1'
            # src_grp['signal'][()] =  nxkd.NXD_DATA
            # src_grp['sample_y_indices'][()] = '1'
            # src_grp['sample_x_indices'][()] = '2'
            src_grp['energy'][()] = e_pnts_E

        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['osa_y', 'osa_x'])
            _string_attr(src_grp, 'osa_y_indices', '0')
            _string_attr(src_grp, 'osa_x_indices', '1')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            #            _string_attr(src_grp, 'sample_y_indices', '1')
            #            _string_attr(src_grp, 'sample_x_indices', '2')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')

    elif (scan_type == scan_types.OSA_FOCUS):
        if (modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['osa_x'][()] = xpnts_E
            src_grp['osa_y'][()] = ypnts_E
            src_grp['zoneplate_z'][()] = zpnts_E
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            # src_grp['axes'][()] = ['zoneplate_z', 'osa_y', 'osa_x']
            # src_grp['zoneplate_z_indices'][()] = '0'
            # src_grp['osa_y_indices'][()] = '1'
            # src_grp['osa_x_indices'][()] = '2'
            # src_grp['signal'][()] = nxkd.NXD_DATA
            # src_grp['sample_y_indices'][()] = '1'
            # src_grp['sample_x_indices'][()] = '2'
            src_grp['energy'][()] = e_pnts_E

        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['zoneplate_z', 'osa_y', 'osa_x'])
            _string_attr(src_grp, 'zoneplate_z_indices', '0')
            _string_attr(src_grp, 'osa_y_indices', '1')
            _string_attr(src_grp, 'osa_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')

            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')


    elif (scan_type == scan_types.SAMPLE_FOCUS):
        if (modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['zoneplate_z'][()] = zpnts_E
            # src_grp['axes'] = ['zoneplate_z', 'sample_y', 'sample_x']
            # _string_attr(src_grp, 'zoneplate_z_indices', '0')
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')
            # _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            src_grp['energy'][()] = e_pnts_E
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')

        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['zoneplate_z', 'sample_y', 'sample_x'])
            _string_attr(src_grp, 'zoneplate_z_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')

    elif (scan_type == scan_types.DETECTOR_IMAGE):
        if (modify):
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['detector_x'][()] = xpnts_E
            src_grp['detector_y'][()] = ypnts_E
            # src_grp['axes'] = ['detector_y', 'detector_x']
            # _string_attr(src_grp, 'detector_y_indices', '0')
            # _string_attr(src_grp, 'detector_x_indices', '1')
            # _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = sxpnts_E
            src_grp['sample_y'][()] = sypnts_E
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')
        else:
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'detector_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'detector_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['detector_y', 'detector_x'])
            _string_attr(src_grp, 'detector_y_indices', '0')
            _string_attr(src_grp, 'detector_x_indices', '1')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')

    elif (scan_type == scan_types.GENERIC_SCAN):
        posner_nm = dct_get(data_dct, 'CFG.ROI.X.POSITIONER')
        _setpoints = dct_get(data_dct, 'CFG.ROI.X.SETPOINTS')
        if (modify):
            src_grp['count_time'][()] = count_time_E
            #src_grp['energy'][()] = e_pnts_E
            #src_grp['sample_x'][()] = xpnts_E
            #src_grp['sample_y'][()] = ypnts_E
            #src_grp['epu_polarization'][()] = pol_pnts_E
            #src_grp['epu_offset'][()] = off_pnts_E
            src_grp[nxkd.NXD_DATA][()] = data_P
            #src_grp['sample_x'][()] = sxpnts_E
            #src_grp['sample_y'][()] = sypnts_E
            src_grp['axes'][()] = [posner_nm]
            src_grp['%s_indices' %posner_nm ][()] = '0'
            # src_grp['sample_y_indices'][()] = '1'
            # src_grp['sample_x_indices'][()] = '2'

        else:
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, posner_nm, _setpoints, 'NX_FLOAT')
            #_dataset(src_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            #_dataset(src_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            #_dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            #_dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', [posner_nm])
            _string_attr(src_grp, '%s_indices' % posner_nm, '0')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            _dataset(src_grp, nxkd.NXD_DATA, data_P, 'NX_NUMBER')

            #_string_attr(src_grp, 'energy_indices', '0')
            #_string_attr(src_grp, 'sample_y_indices', '1')
            #_string_attr(src_grp, 'sample_x_indices', '2')


    else:
        if (modify):
            # 'generic scan'
            src_grp[nxkd.NXD_DATA][()] = data_E
            src_grp['count_time'][()] = count_time_E
            src_grp['energy'][()] = e_pnts_E
            src_grp['sample_x'][()] = xpnts_E
            src_grp['sample_y'][()] = ypnts_E
            src_grp['epu_polarization'][()] = pol_pnts_E
            src_grp['epu_offset'][()] = off_pnts_E
            # src_grp['axes'] = ['energy', 'sample_y', 'sample_x']
            # _string_attr(src_grp, 'energy_indices', '0')
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')
            # _string_attr(src_grp, 'signal', nxkd.NXD_DATA)
            # _string_attr(src_grp, 'sample_y_indices', '1')
            # _string_attr(src_grp, 'sample_x_indices', '2')

        else:
            # 'generic scan'
            _dataset(src_grp, nxkd.NXD_DATA, data_E, 'NX_NUMBER')
            _dataset(src_grp, 'count_time', count_time_E, 'NX_FLOAT')
            _dataset(src_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(src_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _list_attr(src_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
            _string_attr(src_grp, 'energy_indices', '0')
            _string_attr(src_grp, 'sample_y_indices', '1')
            _string_attr(src_grp, 'sample_x_indices', '2')
            _string_attr(src_grp, 'signal', nxkd.NXD_DATA)


def make_control_section_new(nf, name, data_dct={}, scan_type=scan_types.SAMPLE_IMAGE, modify=False, dddata=None):
    """

    """
    nume_pnts = dct_get(data_dct, 'SYMBOLS.numE')
    # if((scan_type == scan_types.SAMPLE_IMAGE + IMAGE_PXP) or (scan_type == scan_types.SAMPLE_IMAGE + IMAGE_LXL)):
    if (scan_type == scan_types.SAMPLE_IMAGE):
        if (nume_pnts > 1):
            scan_type = scan_types.SAMPLE_IMAGE_STACK
        else:
            scan_type = scan_types.SAMPLE_IMAGE

    x_roi = dct_get(data_dct, ADO_CFG_X)
    y_roi = dct_get(data_dct, ADO_CFG_Y)
    z_roi = dct_get(data_dct, ADO_CFG_Z)

    data_E = dct_get(data_dct, 'DETECTORS.%s.DATA_E' % name)
    data_P = dct_get(data_dct, 'DETECTORS.%s.DATA_P' % name)


    e_pnts_E = dct_get(data_dct, 'NUM_E.EV')
    pol_pnts_E = dct_get(data_dct, 'NUM_E.EPU_POL')
    off_pnts_E = dct_get(data_dct, 'NUM_E.EPU_OFFSET')
    count_time_E = dct_get(data_dct, 'NUM_E.COUNT_TIME')
    xpnts_E = dct_get(data_dct, 'NUM_E.MOTOR_X')
    ypnts_E = dct_get(data_dct, 'NUM_E.MOTOR_Y')
    zpnts_E = dct_get(data_dct, 'NUM_E.MOTOR_Z')

    sxpnts_E = dct_get(data_dct, 'NUM_E.SAMPLE_X')
    sypnts_E = dct_get(data_dct, 'NUM_E.SAMPLE_Y')

    line_position_P = dct_get(data_dct, 'NUM_P.LINE_POSITION')

    oneD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.ONE_D')
    twoD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.TWO_D')
    thrD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.THREE_D')

    if (z_roi[NPOINTS] > 0):
        zpnts = dct_get(data_dct, 'NUM_E.MOTOR_Z')

    # type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK] #, scan_types.SAMPLE_FOCUS]
    type_a_scans = [scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE,
                    scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY]  # , scan_types.SAMPLE_FOCUS]

    if ('control' not in list(nf.keys())):
        ctrl_grp = _group(nf, 'control', 'NXmonitor')
    else:
        ctrl_grp = nf['control']
        modify = True

    if (scan_type in type_a_scans):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            # ctrl_grp['signal'][()] = nxkd.NXD_DATA

        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

        # set attributes
        if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            if (modify):
                ctrl_grp[nxkd.NXD_DATA][()] = data_E[0]
                ctrl_grp['line_position'][()] = line_position_P
                # ctrl_grp['sample_x'] = sxpnts_E
                # ctrl_grp['sample_y'] = sypnts_E
                # ctrl_grp['axes'][()] = ['energy','line_position']
                # ctrl_grp['energy_indices'][()] = '0'
                # ctrl_grp['line_position_indices'][()] = '1'
                # ctrl_grp['sample_y_indices'][()] = '1'
                # ctrl_grp['sample_x_indices'][()] = '1'
            else:

                _dataset(ctrl_grp, nxkd.NXD_DATA, data_E[0], 'NX_NUMBER')
                _dataset(ctrl_grp, 'line_position', line_position_P, 'NX_FLOAT')
                _list_attr(ctrl_grp, 'axes', [ 'line_position','energy'])
                _string_attr(ctrl_grp, 'energy_indices', '1')
                _string_attr(ctrl_grp, 'line_position_indices', '0')
                _string_attr(ctrl_grp, 'sample_y_indices', '0')
                _string_attr(ctrl_grp, 'sample_x_indices', '0')



        elif (scan_type == scan_types.SAMPLE_IMAGE):
            if (modify):
                # ctrl_grp[nxkd.NXD_DATA][()] =  twoD_srdata
                ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
                # ctrl_grp['axes'][()] =  ['sample_y', 'sample_x']
                # ctrl_grp['sample_y_indices'][()] =  '0'
                # ctrl_grp['sample_x_indices'][()] =  '1'
            else:
                _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
                _list_attr(ctrl_grp, 'axes', ['sample_y', 'sample_x'])
                _string_attr(ctrl_grp, 'sample_y_indices', '0')
                _string_attr(ctrl_grp, 'sample_x_indices', '1')

        #elif (scan_type == scan_types.SAMPLE_IMAGE_STACK):
        elif ((scan_type == scan_types.SAMPLE_IMAGE_STACK) or (scan_type == scan_types.TOMOGRAPHY)):
            if (modify):
                if (dddata is not None):
                    ctrl_grp[nxkd.NXD_DATA][()] = dddata
                else:
                    ctrl_grp[nxkd.NXD_DATA][()] = thrD_srdata

                    # ctrl_grp['sample_x'][()] = sxpnts_E
                    # ctrl_grp['sample_y'][()] = sypnts_E
                    # ctrl_grp['axes'][()] =  ['energy', 'sample_y', 'sample_x']
                    # ctrl_grp['energy_indices'][()] = '0'
                    # ctrl_grp['sample_y_indices'][()] = '1'
                    # ctrl_grp['sample_x_indices'][()] = '2'
            else:

                if (dddata is not None):
                    _dataset(ctrl_grp, nxkd.NXD_DATA, dddata, 'NX_NUMBER')
                else:
                    _dataset(ctrl_grp, nxkd.NXD_DATA, thrD_srdata, 'NX_NUMBER')

                _list_attr(ctrl_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
                _string_attr(ctrl_grp, 'energy_indices', '0')
                _string_attr(ctrl_grp, 'sample_y_indices', '1')
                _string_attr(ctrl_grp, 'sample_x_indices', '2')
                # _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
                # _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')

    elif (scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = oneD_srdata
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            # ctrl_grp['axes'][()] = ['energy']
            # ctrl_grp['energy_indices'][()] = '0'
        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
            _dataset(ctrl_grp, nxkd.NXD_DATA, oneD_srdata, 'NX_NUMBER')
            _list_attr(ctrl_grp, 'axes', ['energy'])
            _string_attr(ctrl_grp, 'energy_indices', '0')

    elif (scan_type == scan_types.OSA_IMAGE):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['osa_x'][()] = xpnts_E
            ctrl_grp['osa_y'][()] = ypnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            # ctrl_grp['axes'][()] =  ['osa_y', 'osa_x']
            # ctrl_grp['osa_y_indices'][()] = '0'
            # ctrl_grp['osa_x_indices'][()] = '1'
            # ctrl_grp['signal'][()] = nxkd.NXD_DATA
            # ctrl_grp['sample_y_indices'][()] = '1'
            # ctrl_grp['sample_x_indices'][()] = '2'
            ctrl_grp['energy'][()] = e_pnts_E

        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['osa_y', 'osa_x'])
            _string_attr(ctrl_grp, 'osa_y_indices', '0')
            _string_attr(ctrl_grp, 'osa_x_indices', '1')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif (scan_type == scan_types.OSA_FOCUS):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['osa_x'][()] = xpnts_E
            ctrl_grp['osa_y'][()] = ypnts_E
            ctrl_grp['zoneplate_z'][()] = zpnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            # ctrl_grp['axes'][()] = ['zoneplate_z', 'osa_y', 'osa_x']
            # ctrl_grp['zoneplate_z_indices'][()] = '0'
            # ctrl_grp['osa_y_indices'][()] = '1'
            # ctrl_grp['osa_x_indices'][()] =  '2'
            # ctrl_grp['signal'][()] =  nxkd.NXD_DATA


        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')

            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'osa_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'osa_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['zoneplate_z', 'osa_y', 'osa_x'])
            _string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            _string_attr(ctrl_grp, 'osa_y_indices', '1')
            _string_attr(ctrl_grp, 'osa_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif (scan_type == scan_types.SAMPLE_FOCUS):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['zoneplate_z'][()] = zpnts_E
            # ctrl_grp['axes'] = ['zoneplate_z', 'sample_y', 'sample_x']
            # _string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            # _string_attr(ctrl_grp, 'sample_y_indices', '1')
            # _string_attr(ctrl_grp, 'sample_x_indices', '2')
            # _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'zoneplate_z', zpnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['zoneplate_z', 'sample_y', 'sample_x'])
            _string_attr(ctrl_grp, 'zoneplate_z_indices', '0')
            _string_attr(ctrl_grp, 'sample_y_indices', '1')
            _string_attr(ctrl_grp, 'sample_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif (scan_type == scan_types.DETECTOR_IMAGE):
        if (modify):
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp[nxkd.NXD_DATA][()] = twoD_srdata
            ctrl_grp['detector_x'][()] = xpnts_E
            ctrl_grp['detector_y'][()] = ypnts_E
            ctrl_grp['sample_x'][()] = sxpnts_E
            ctrl_grp['sample_y'][()] = sypnts_E
            # ctrl_grp['axes'] = ['detector_y', 'detector_x']
            # _string_attr(ctrl_grp, 'detector_y_indices', '0')
            # _string_attr(ctrl_grp, 'detector_x_indices', '1')
            # _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, nxkd.NXD_DATA, twoD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'detector_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'detector_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', sxpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', sypnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['detector_y', 'detector_x'])
            _string_attr(ctrl_grp, 'detector_y_indices', '0')
            _string_attr(ctrl_grp, 'detector_x_indices', '1')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)

    elif (scan_type == scan_types.GENERIC_SCAN):
        posner_nm = dct_get(data_dct, 'CFG.ROI.X.POSITIONER')
        _setpoints = dct_get(data_dct, 'CFG.ROI.X.SETPOINTS')
        _units = dct_get(data_dct, 'CFG.ROI.X.UNITS')
        if(_units is None):
            _units = 'um'

        if (modify):
            # ctrl_grp[nxkd.NXD_DATA][()] = data_P
            # ctrl_grp['axes'][()] = [posner_nm]
            # ctrl_grp['%s_indices' %posner_nm ][()] = '0'
            pass

        else:
            _evpoints = np.repeat(e_pnts_E, len(_setpoints))
            _dataset(ctrl_grp, 'energy', _evpoints, 'NX_FLOAT')
            _datapoints = np.repeat(oneD_srdata, len(_setpoints))
            _list_attr(ctrl_grp, 'axes', [posner_nm])
            _string_attr(ctrl_grp, '%s_indices' % posner_nm, '0')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
            _dataset(ctrl_grp, nxkd.NXD_DATA, _datapoints, 'NX_NUMBER')
            posner_grp = _dataset(ctrl_grp, posner_nm, _setpoints, 'NX_NUMBER')
            _string_attr(posner_grp, 'units', _units)

    else:
        if (modify):
            ctrl_grp[nxkd.NXD_DATA][()] = oneD_srdata
            ctrl_grp['energy'][()] = e_pnts_E
            ctrl_grp['sample_x'][()] = xpnts_E
            ctrl_grp['sample_y'][()] = ypnts_E
            ctrl_grp['epu_polarization'][()] = pol_pnts_E
            ctrl_grp['epu_offset'][()] = off_pnts_E
            # ctrl_grp['axes'] = ['energy', 'sample_y', 'sample_x']
            # _string_attr(ctrl_grp, 'energy_indices', '0')
            # _string_attr(ctrl_grp, 'sample_y_indices', '1')
            # _string_attr(ctrl_grp, 'sample_x_indices', '2')
            # _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)
        else:
            _dataset(ctrl_grp, nxkd.NXD_DATA, oneD_srdata, 'NX_NUMBER')
            _dataset(ctrl_grp, 'energy', e_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_x', xpnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'sample_y', ypnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_polarization', pol_pnts_E, 'NX_FLOAT')
            _dataset(ctrl_grp, 'epu_offset', off_pnts_E, 'NX_FLOAT')
            _list_attr(ctrl_grp, 'axes', ['energy', 'sample_y', 'sample_x'])
            _string_attr(ctrl_grp, 'energy_indices', '0')
            _string_attr(ctrl_grp, 'sample_y_indices', '1')
            _string_attr(ctrl_grp, 'sample_x_indices', '2')
            _string_attr(ctrl_grp, 'signal', nxkd.NXD_DATA)


def update_data_section(fname, entry_str, counter_str='counter0', data_dct={}, scan_type=scan_types.SAMPLE_IMAGE):
    """
    supported scan types from NXstxm def
    sample point spectrum: (photon_energy,)
    sample line spectrum: (photon_energy, sample_y/sample_x)
    sample image: (sample_y, sample_x)
    sample image stack: (photon_energy, sample_y, sample_x)
    sample focus: (zoneplate_z, sample_y/sample_x)
    osa image: (osa_y, osa_x)
    osa focus: (zoneplate_z, osa_y/osa_x)
    detector image: (detector_y, detector_x)
     
    because the /control section is required to be closely tied to the data section we also build the /control group here
     
    NOTE: the axis2000 read_nexus.pro file assumes that the axis '_indices' are in the following order:
        2D data: y,  x or 0, 1
        3D data: e, y, x or 0, 1, 2
         
    Also NOTE that every NXdata group MUST contain: 
        _string_attr(src_grp, 'sample_y_indices', '1')
        _string_attr(src_grp, 'sample_x_indices', '2')    
    
    fname : the nexus file that has been opened for writing
    entry_str : the entry string that is to receive this data
    counter_str : the name of the counter to use to place the data in the 'counter' NXData section
    data_dct : the incoming data
    scan_type : the type of the scan data being saved
          
     
    """
    nf = h5py.File(fname, "r+")
    if(nf  is None):
        _logger.error('unable to open file [%s]' % fname)
    
        
    data_dct = _data_as_1D(data_dct)
    nume_pnts = dct_get(data_dct, 'SYMBOLS.numE')
    #if((scan_type == scan_types.SAMPLE_IMAGE + IMAGE_PXP) or (scan_type == scan_types.SAMPLE_IMAGE + IMAGE_LXL)):
    if(scan_type == scan_types.SAMPLE_IMAGE):
        if(nume_pnts > 1):
            scan_type = scan_types.SAMPLE_IMAGE_STACK
        else:
            scan_type = scan_types.SAMPLE_IMAGE
     
    x_roi = dct_get(data_dct, ADO_CFG_X)
    y_roi = dct_get(data_dct, ADO_CFG_Y)
    z_roi = dct_get(data_dct, ADO_CFG_Z)
     
    data_E = dct_get(data_dct, 'NUM_E.DATA')
    e_pnts_E = dct_get(data_dct, 'NUM_E.EV')
    pol_pnts_E = dct_get(data_dct, 'NUM_E.EPU_POL')
    off_pnts_E = dct_get(data_dct, 'NUM_E.EPU_OFFSET')
    count_time_E = dct_get(data_dct, 'NUM_E.COUNT_TIME')
    xpnts_E = dct_get(data_dct,'NUM_E.MOTOR_X')
    ypnts_E = dct_get(data_dct,'NUM_E.MOTOR_Y')
    zpnts_E = dct_get(data_dct,'NUM_E.MOTOR_Z')
     
    data_P = dct_get(data_dct, 'NUM_P.DATA')
    e_pnts_P = dct_get(data_dct, 'NUM_P.EV')
    pol_pnts_P = dct_get(data_dct, 'NUM_P.EPU_POL')
    off_pnts_P = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
    count_time_P = dct_get(data_dct, 'NUM_P.COUNT_TIME')
    xpnts_P = dct_get(data_dct,'NUM_P.MOTOR_X')
    ypnts_P = dct_get(data_dct,'NUM_P.MOTOR_Y')
     
    line_position_P = dct_get(data_dct,'NUM_P.LINE_POSITION')
     
    oneD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.ONE_D')
    twoD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.TWO_D')
    thrD_srdata = dct_get(data_dct, 'NUM_E.SR_CURRENT.THREE_D')
    
    if(z_roi[NPOINTS] > 0):
        zpnts = dct_get(data_dct,'NUM_E.MOTOR_Z')
    
    type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK] #, scan_types.SAMPLE_FOCUS]
    
    if entry_str in list(nf.keys()):
        if counter_str in list(nf[entry_str].keys()):
            src_grp = nf[entry_str]['control'][nxkd.NXD_DATA]
            ctrl_grp = nf[entry_str][counter_str][nxkd.NXD_DATA]
        else:
            _logger.error('update_data_section: counter string [%s] does not exist in nexus entry' % counter_str)     
            nf.close()
            return(False)
    else:
        _logger.error('update_data_section: entry string [%s] does not exist in nexus file' % entry_str)
        nf.close()
        return(False)    
            
    if(scan_type in type_a_scans):

        if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            src_grp[()] = data_E
            ctrl_grp[()] = data_E
            
        elif(scan_type == scan_types.SAMPLE_POINT_SPECTRUM):
            src_grp[()] = data_P
            ctrl_grp[()] = oneD_srdata
                            
        elif(scan_type == scan_types.SAMPLE_IMAGE):
            src_grp[()] = data_E
            ctrl_grp[()] = twoD_srdata
        elif(scan_type == scan_types.SAMPLE_IMAGE_STACK):
            src_grp[()] = data_E
            ctrl_grp[()] = thrD_srdata
        else:
            #modify existing nexus file
            src_grp[()] = data_P
        
    elif(scan_type == scan_types.OSA_IMAGE):
        src_grp[()] = data_E
        ctrl_grp[()] = twoD_srdata
        
    elif(scan_type == scan_types.OSA_FOCUS):
        src_grp[()] = data_E
        ctrl_grp[()] = twoD_srdata
        
    elif(scan_type == scan_types.SAMPLE_FOCUS):
        src_grp[()] = data_E
        ctrl_grp[()] = twoD_srdata
        
    elif(scan_type == scan_types.DETECTOR_IMAGE):
        src_grp[()] = data_E
        ctrl_grp[()] = twoD_srdata
        
    else:
        #'generic scan'
        src_grp[()] = data_E
        ctrl_grp[()] = oneD_srdata
    
    nf.close()    
    
    return(True)

    
def make_detector(nf, name, data=None, data_dct={}, count_time=[], unit='counts', modify=False):
    if(not modify):
        grp = _group(nf, name, 'NXdetector')
        
        if(data is None):
            _dataset(grp, nxkd.NXD_DATA, np.zeros(200, dtype=np.float32), 'NX_FLOAT')
        else:
            _dataset(grp, nxkd.NXD_DATA, data, 'NX_FLOAT')
        
        _dataset(grp, 'count_time', count_time, 'NX_FLOAT')
        _dataset(grp, 'unit', unit, 'NX_CHAR')
    else:
        grp = nf[name]
        del grp[nxkd.NXD_DATA]
        #grp[nxkd.NXD_DATA][()] = data
        _dataset(grp, nxkd.NXD_DATA, data, 'NX_FLOAT')

def make_source(nf, data_dct={}, modify=False):
    if(not modify):
        src_grp = _group(nf, 'source', 'NXsource')
        _dataset(src_grp, 'type', 'Synchrotron X-ray Source', 'NX_CHAR')
        _dataset(src_grp, 'name', 'Canadian Lightsource Inc.', 'NX_CHAR')
        _dataset(src_grp, 'probe', 'x-ray', 'NX_CHAR')
        #devices = dct_get(data_dct,ADO_DEVICES)
        detectors = dct_get(data_dct,'DETECTORS')
        d = detectors[DNM_RING_CURRENT]
        _dataset(src_grp, 'current', d[RBV], 'NX_FLOAT', 'NX_CURRENT')

    else:
        #nothing to modify
        pass

def make_source_new(nf, data_dct={}, modify=False):
    if(not modify):
        src_grp = _group(nf, 'source', 'NXsource')
        _dataset(src_grp, 'type', 'Synchrotron X-ray Source', 'NX_CHAR')
        _dataset(src_grp, 'name', 'Canadian Lightsource Inc.', 'NX_CHAR')
        _dataset(src_grp, 'probe', 'x-ray', 'NX_CHAR')
        #devices = dct_get(data_dct,ADO_DEVICES)
        sr_current = dct_get(data_dct, 'NUM_P.SR_CURRENT')
        _dataset(src_grp, 'current', sr_current, 'NX_FLOAT', 'NX_CURRENT')
    else:
        #nothing to modify
        pass

def make_monochromator(nf, data_dct={}, modify=False):
    epnts = dct_get(data_dct, 'NUM_P.EV')
    
    if(modify):
        del nf['monochromator']['energy']
        grp = nf['monochromator']
    else:
        grp = _group(nf, 'monochromator', 'NXmonochromator')
        
    _dataset(grp, 'energy', epnts, 'NX_FLOAT')

def make_epu(nf, data_dct={}, modify=False, pol_pnt=0):
    """
    The epu polaraization is a confusing situation, the implementation of the polarization number 
    """
    pvs = dct_get(data_dct,'PVS')
#     pol_pnts = dct_get(data_dct, 'NUM_P.EPU_POL')
#     off_pnts = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
#     angle_pnts = dct_get(data_dct, 'NUM_P.EPU_POL_ANGLE')
#     gap_pnts = dct_get(data_dct, 'NUM_P.EPU_GAP')
#     harmonic_pnts = dct_get(data_dct, 'NUM_P.EPU_HARMONIC')
    s0 = 0
    s1 = 0
    s2 = 0
    s3 = 0
    
    #(use_pol_angle, mode_str) = get_nx_standard_epu_mode(pvs[DNM_EPU_POL_FBK][RBV])
    (use_pol_angle, mode_str) = get_nx_standard_epu_mode(pol_pnt)
    if(use_pol_angle):
        pol_angle = pvs[DNM_EPU_POL_ANGLE][RBV]
    else:
        pol_angle = 0.0
        
    epu_gap_fbk = pvs[DNM_EPU_GAP_FBK][RBV]
    epu_gap_offset = pvs[DNM_EPU_GAP_OFFSET][RBV]
    epu_harmonic = get_nx_standard_epu_harmonic(pvs[DNM_EPU_HARMONIC_PV][RBV])
    
    if(not modify):
        grp = _group(nf, 'epu', 'NXinsertion_device')
        #_dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
        _dataset(grp, 'type', 'elliptically polarizing undulator', 'NX_CHAR')
        _dataset(grp, 'mode', mode_str, 'NX_CHAR')
        _dataset(grp, 'linear_inclined_angle', pol_angle, 'NX_ANGLE')
        _dataset(grp, 'gap', epu_gap_fbk, 'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'gap_offset', epu_gap_offset, 'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'harmonic', epu_harmonic, 'NX_INT', nx_units='NX_UNITLESS')

        # stokes_grp = _group(grp, 'stokes', 'NXstokes_parameters')
        # _dataset(stokes_grp, 's0', s0, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's1', s1, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's2', s2, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's3', s3, 'NX_INT', nx_units='NX_UNITLESS')
    else:
        #only modify the fields that would have changed
        grp = nf['epu']
        # stokes_grp = nf['epu']['stokes']
        #grp['mode'][()] = mode_str
        replace_string_data(grp, 'mode', mode_str)
        grp['linear_inclined_angle'][()] = pol_angle
        grp['gap'][()] = epu_gap_fbk
        grp['gap_offset'][()] = epu_gap_offset
        grp['harmonic'][()] = epu_harmonic
        # stokes_grp['s0'][()] = s0
        # stokes_grp['s1'][()] = s1
        # stokes_grp['s2'][()] = s2
        # stokes_grp['s3'][()] = s3


def make_epu_new(nf, data_dct={}, modify=False, pol_pnt=0):
    """
    The epu polaraization is a confusing situation, the implementation of the polarization number
    """
    pvs = dct_get(data_dct, 'PVS')
    #     pol_pnts = dct_get(data_dct, 'NUM_P.EPU_POL')
    #     off_pnts = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
    #     angle_pnts = dct_get(data_dct, 'NUM_P.EPU_POL_ANGLE')
    #     gap_pnts = dct_get(data_dct, 'NUM_P.EPU_GAP')
    #     harmonic_pnts = dct_get(data_dct, 'NUM_P.EPU_HARMONIC')

    ang = dct_get(data_dct, 'NUM_P.EPU_POL')
    epu_gap_offset = dct_get(data_dct, 'NUM_P.EPU_OFFSET')
    ang = dct_get(data_dct, 'NUM_P.EPU_POL_ANGLE')
    epu_gap_fbk = dct_get(data_dct, 'NUM_P.EPU_GAP')
    harm = dct_get(data_dct, 'NUM_P.EPU_HARMONIC')

    stokes = dct_get(data_dct, 'NUM_P.STOKES')
    # s0 = dct_get(data_dct, 'NUM_P.STOKES_S0')
    # s1 = dct_get(data_dct, 'NUM_P.STOKES_S1')
    # s2 = dct_get(data_dct, 'NUM_P.STOKES_S2')
    # s3 = dct_get(data_dct, 'NUM_P.STOKES_S3')

    # (use_pol_angle, mode_str) = get_nx_standard_epu_mode(pvs[DNM_EPU_POL_FBK][RBV])
    (use_pol_angle, mode_str) = get_nx_standard_epu_mode(pol_pnt)
    if (use_pol_angle):
        pol_angle = ang
    else:
        pol_angle = ang
        pol_angle.fill(0.0)

    epu_harmonic = get_nx_standard_epu_harmonic_new(harm)

    if (not modify):
        grp = _group(nf, 'epu', 'NXinsertion_device')
        # _dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
        _dataset(grp, 'type', 'elliptically polarizing undulator', 'NX_CHAR')
        _dataset(grp, 'mode', mode_str, 'NX_CHAR')
        _dataset(grp, 'linear_inclined_angle', pol_angle, 'NX_ANGLE')
        _dataset(grp, 'gap', epu_gap_fbk, 'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'gap_offset', epu_gap_offset, 'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'harmonic', epu_harmonic, 'NX_INT', nx_units='NX_UNITLESS')

        _dataset(grp, 'stokes', stokes, 'NX_FLOAT', nx_units='NX_UNITLESS')
        # stokes_grp = _group(grp, 'stokes', 'NXstokes_parameters')
        # _dataset(stokes_grp, 's0', s0, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's1', s1, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's2', s2, 'NX_INT', nx_units='NX_UNITLESS')
        # _dataset(stokes_grp, 's3', s3, 'NX_INT', nx_units='NX_UNITLESS')
    else:
        # only modify the fields that would have changed
        grp = nf['epu']
        stokes_grp = nf['epu']['stokes']
        # grp['mode'][()] = mode_str
        replace_string_data(grp, 'mode', mode_str)
        grp['linear_inclined_angle'][()] = pol_angle
        grp['gap'][()] = epu_gap_fbk
        grp['gap_offset'][()] = epu_gap_offset
        grp['harmonic'][()] = epu_harmonic
        grp['stokes'][()] = stokes
        # stokes_grp['s0'][()] = s0
        # stokes_grp['s1'][()] = s1
        # stokes_grp['s2'][()] = s2
        # stokes_grp['s3'][()] = s3

def replace_string_data(grp, fld_str, data_str):
    del grp[fld_str]
    grp[fld_str] = data_str
    
def make_zoneplate(nf, data_dct={}, modify=False):
    """
    The fresnel zoneplate definition, only a subset of standard used because
    I don't not have all the info to populate all fields
     
    fields:
    central_stop_diameter:NX_FLOAT
                central_stop_material:NX_CHAR
              central_stop_thickness:NX_FLOAT
    fabrication:NX_CHAR
              focus_parameters:NX_FLOAT[]
              mask_material:NX_CHAR
              mask_thickness:NX_FLOAT
    outer_diameter:NX_FLOAT
    outermost_zone_width:NX_FLOAT
              support_membrane_material:NX_CHAR
              support_membrane_thickness:NX_FLOAT
              zone_height:NX_FLOAT
              zone_material:NX_CHAR
              zone_support_material:NX_CHAR
  

    
    
    """
    pvs = dct_get(data_dct,'PVS')
    # get the epics trasnform record for the zoneplate definiiton
    zp_pvs = pvs[DNM_ZP_DEF]
    zp_sel = pvs[DNM_ZP_SELECT]
    
    #these zp_pvs are a transform record
    zp_B = zp_pvs[RBV]['B']
    zp_C = zp_pvs[RBV]['C']
    zp_D = zp_pvs[RBV]['D']
    
    if(not modify):
        grp = _group(nf, 'zoneplate', 'NXfresnel_zone_plate')
        _dataset(grp, 'name', 'zone plate #%d' % zp_sel[RBV], 'NX_CHAR')
        #_dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY', dset={}):
        _dataset(grp, 'outer_diameter', zp_B['B'] ,'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'central_stop_diameter', zp_C['C'] ,'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'outermost_zone_width',  zp_D['D'],'NX_FLOAT', nx_units='NX_LENGTH')
        _dataset(grp, 'fabrication', 'etched' ,'NX_CHAR')
        
        # these are part of the standard but I do not have the info to populate them
#         _dataset(grp, 'central_stop_diameter', -1, 'NX_FLOAT')
#         _dataset(grp, 'central_stop_material', 'Pb', 'NX_CHAR')
#         _dataset(grp, 'central_stop_thickness', -1, 'NX_FLOAT')
#         _dataset(grp, 'focus_parameters', 0.0, 'NX_FLOAT[]')
#         _dataset(grp, 'mask_material', 0.0, 'NX_CHAR')
#         _dataset(grp, 'mask_thickness', 0.0, 'NX_FLOAT')
#         _dataset(grp, 'support_membrane_material', 0.0, 'NX_CHAR')
#         _dataset(grp, 'support_membrane_thickness', 0.0, 'NX_FLOAT')
#         _dataset(grp, 'zone_height', 0.0, 'NX_FLOAT')
#         _dataset(grp, 'zone_material', 0.0, 'NX_CHAR')
#         _dataset(grp, 'zone_support_material', 0.0, 'NX_CHAR')
        
        
        
        
    else:
        #only modify the fields that would have changed
        grp = nf['zoneplate']
        #grp['name'][()] = 'zone plate #%d' % zp_sel[RBV]
        replace_string_data(grp, 'name', 'zone plate #%d' % zp_sel[RBV])
        
        grp['outer_diameter'][()] = zp_B['B']
        grp['central_stop_diameter'][()] = zp_C['C']
        grp['outermost_zone_width'][()] = zp_D['D']

def get_nx_standard_epu_mode(mode):
    """
    Define polarization as either 
        cir. right, point of view of source, 
        cir. left, point of view of source, or 
        linear. If the linear case is selected, there is an additional value in degrees for 
            the angle (number is meaningless if circular is chosen, or may not be filled in, I do not know).
    """
    linear_lst = [2, 3, 4, 5]
    if(mode == 0):
        return(False, 'cir. left, point of view of source')
    elif(mode == 1):
        return(False, 'cir. right, point of view of source')
    elif(mode in linear_lst):
        return(True, 'linear')
    else:
        return(False, 'UNKNOWN')

def get_nx_standard_epu_harmonic(harm):
    """ map the epics mbbo enumeration to the actual harmonic num
    """
    if(harm == 0):
        return(1)
    elif(harm == 1):
        return(3)
    elif(harm == 2):
        return(5)
    elif(harm == 3):
        return(7)
    elif(harm == 4):
        return(9)
    else:
        return(0)

def get_nx_standard_epu_harmonic_new(harm_arr):
    """ map the epics mbbo enumeration to the actual harmonic num
    harm_lst is an array
    """
    l = []
    for harm in harm_arr[::-1]:
        if(harm == 0):
            l.append(1)
        elif(harm == 1):
            l.append(3)
        elif(harm == 2):
            l.append(5)
        elif(harm == 3):
            l.append(7)
        elif(harm == 4):
            l.append(9)
        else:
            l.append(0)
    return(l)

def make_monitor(nf, data_dct={}):
    grp = _group(nf, 'control', 'NXmonitor')
    _dataset(grp, nxkd.NXD_DATA, -1.0, 'NX_FLOAT')

def make_sample(nf, data_dct={}, modify=False):
    """
    
    """
    positioners_dct = dct_get(data_dct,'POSITIONERS')
    if(DNM_GONI_THETA in list(positioners_dct.keys())):
        rotation_angle = positioners_dct[DNM_GONI_THETA][RBV]
    else:
        rotation_angle = 0.0
        
    if(not modify):
        grp = _group(nf, nxkd.NXD_SAMPLE, 'NXsample')
        _dataset(grp, 'rotation_angle', rotation_angle, 'NX_FLOAT')
    else:
        grp = nf[nxkd.NXD_SAMPLE]
        grp['rotation_angle'][()] = rotation_angle

def make_counter(nf, name, data_dct, nx_class_name, nx_dtype, modify=False):
    if(nx_class_name == 'NXdetector'):
        # all data stored as a a single dimension array
        #epnts = dct_get(data_dct, 'NUM_E.EV')
        count_time = dct_get(data_dct, 'NUM_P.COUNT_TIME')
        data = dct_get(data_dct, 'NUM_P.DATA')
        make_detector(nf, name, data, count_time=count_time, unit='counts', modify=modify)
        
    else:
        #assume its for the NXdata section
        # all data stored as a normal ExYxX array
        count_time = dct_get(data_dct, 'NUM_E.COUNT_TIME')
        data = dct_get(data_dct, 'NUM_E.DATA')
        make_nxdata(nf, name, data, count_time, nx_dtype, modify=modify)


def make_counter_new(nf, name, data_dct, nx_class_name, nx_dtype, modify=False):
    if (nx_class_name == 'NXdetector'):
        # all data stored as a a single dimension array
        # epnts = dct_get(data_dct, 'NUM_E.EV')
        count_time = dct_get(data_dct, 'NUM_P.COUNT_TIME')
        #data = dct_get(data_dct, 'NUM_P.DATA')
        data = dct_get(data_dct, 'DETECTORS.%s.DATA_P' % name)
        make_detector(nf, name, data, count_time=count_time, unit='counts', modify=modify)

    else:
        # assume its for the NXdata section
        # all data stored as a normal ExYxX array
        count_time = dct_get(data_dct, 'NUM_E.COUNT_TIME')
        #data = dct_get(data_dct, 'NUM_E.DATA')
        data = dct_get(data_dct, 'DETECTORS.%s.DATA_E' % name)
        make_nxdata(nf, name, data, count_time, nx_dtype, modify=modify)


def make_nxdata(nf, name, data, count_time, nx_dtype, modify=False):
    if(not modify):
        grp = _group(nf, name, 'NXdata')
        _dataset(grp, nxkd.NXD_DATA, data, nx_dtype)
        _dataset(grp, 'count_time', count_time, 'NX_FLOAT')
    else:
        grp = nf[name]
        grp[nxkd.NXD_DATA][()] = data
        grp['count_time'][()] = count_time




    
def make_instrument(nf, data_dct={}, scan_type=scan_types.SAMPLE_IMAGE, modify=False, pol_pnt=0):
    """ 
    The data stored under each instrument is of the form <data>[numP]
    
    The modify parameter determines if the data is to be created in a new
    Nexus file or if it is to simply modify data to an existing Nexus file, HDF5
    does not allow the creation of a group or dataset that already exists in an HDF5 file
    """
    if(not modify):
        nx_inst_grp = _group(nf, nxkd.NXD_INSTRUMENT, 'NXinstrument')
    else:
        nx_inst_grp = nf[nxkd.NXD_INSTRUMENT]    
    
    #make source entry 
    make_source(nx_inst_grp, data_dct=data_dct, modify=modify)
    #make mono
    make_monochromator(nx_inst_grp, data_dct=data_dct, modify=modify)
    make_epu(nx_inst_grp, data_dct=data_dct, modify=modify, pol_pnt=pol_pnt)
    make_zoneplate(nx_inst_grp, data_dct=data_dct, modify=modify)
    count_time = dct_get(data_dct, 'NUM_P.COUNT_TIME')
    
    make_counter(nx_inst_grp, 'counter0', data_dct, 'NXdetector', 'NX_FLOAT', modify=modify)
    
    type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_IMAGE_STACK, scan_types.SAMPLE_FOCUS]
    
    xpnts = dct_get(data_dct,'NUM_P.MOTOR_X')
    ypnts = dct_get(data_dct,'NUM_P.MOTOR_Y')
    
    zmtr_name = None
    
    if(scan_type in type_a_scans):
        if(scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
            xmtr_name = 'sample_x'
            ymtr_name = 'sample_y'
            #_dataset(src_grp, 'line_position', np.linspace(ystart, ystop, num=numy_pnts), 'NX_FLOAT')
            #_string_attr(src_grp, 'axes', '"energy","line_position"')
        else:
            xmtr_name = 'sample_x'
            ymtr_name = 'sample_y'
            #_string_attr(src_grp, 'axes', '"energy","sample_y","sample_x"')
    elif(scan_type == scan_types.OSA_IMAGE):
        xmtr_name = 'osa_x'
        ymtr_name = 'osa_y'
        make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
        make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
        #Ben says every scan type requires a sample_x sample_y section
    
    elif(scan_type == scan_types.OSA_FOCUS):
        zpnts = dct_get(data_dct,'NUM_P.MOTOR_Z')
        xmtr_name = 'osa_x'
        ymtr_name = 'osa_y'
        zmtr_name = 'zoneplate_z'
        make_detector(nx_inst_grp, zmtr_name, zpnts, count_time=count_time, unit='um', modify=modify)
        make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
        make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
        #Ben says every scan type requires a sample_x sample_y section
    
        
    elif(scan_type == scan_types.DETECTOR_IMAGE):
        xmtr_name = 'detector_x'
        ymtr_name = 'detector_y'
        make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
        make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
        #Ben says every scan type requires a sample_x sample_y section
    
        
    else:
        xmtr_name = 'sample_x'
        ymtr_name = 'sample_y'
        
    make_detector(nx_inst_grp, xmtr_name, xpnts, count_time=count_time, unit='um', modify=modify)
    make_detector(nx_inst_grp, ymtr_name, ypnts, count_time=count_time, unit='um', modify=modify)


def make_instrument_new(nf, data_dct={}, counter='counter0', scan_type=scan_types.SAMPLE_IMAGE, modify=False, pol_pnt=0):
    """
    The data stored under each instrument is of the form <data>[numP]

    The modify parameter determines if the data is to be created in a new
    Nexus file or if it is to simply modify data to an existing Nexus file, HDF5
    does not allow the creation of a group or dataset that already exists in an HDF5 file
    """
    if(nxkd.NXD_INSTRUMENT in list(nf.keys())):
        modify = True
    if (not modify):
        nx_inst_grp = _group(nf, nxkd.NXD_INSTRUMENT, 'NXinstrument')
        make_source_new(nx_inst_grp, data_dct=data_dct, modify=modify)
        # make mono
        make_monochromator(nx_inst_grp, data_dct=data_dct, modify=modify)
        make_epu_new(nx_inst_grp, data_dct=data_dct, modify=modify, pol_pnt=pol_pnt)
        make_zoneplate(nx_inst_grp, data_dct=data_dct, modify=modify)
        count_time = dct_get(data_dct, 'NUM_P.COUNT_TIME')
        type_a_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM, scan_types.SAMPLE_IMAGE,
                        scan_types.SAMPLE_IMAGE_STACK, scan_types.SAMPLE_FOCUS]

        xpnts = dct_get(data_dct, 'NUM_P.MOTOR_X')
        ypnts = dct_get(data_dct, 'NUM_P.MOTOR_Y')

        zmtr_name = None

        if (scan_type in type_a_scans):
            if (scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
                xmtr_name = 'sample_x'
                ymtr_name = 'sample_y'
                # _dataset(src_grp, 'line_position', np.linspace(ystart, ystop, num=numy_pnts), 'NX_FLOAT')
                # _string_attr(src_grp, 'axes', '"energy","line_position"')
            else:
                xmtr_name = 'sample_x'
                ymtr_name = 'sample_y'
                # _string_attr(src_grp, 'axes', '"energy","sample_y","sample_x"')
        elif (scan_type == scan_types.OSA_IMAGE):
            xmtr_name = 'osa_x'
            ymtr_name = 'osa_y'
            make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
            make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
            # Ben says every scan type requires a sample_x sample_y section

        elif (scan_type == scan_types.OSA_FOCUS):
            zpnts = dct_get(data_dct, 'NUM_P.MOTOR_Z')
            xmtr_name = 'osa_x'
            ymtr_name = 'osa_y'
            zmtr_name = 'zoneplate_z'
            make_detector(nx_inst_grp, zmtr_name, zpnts, count_time=count_time, unit='um', modify=modify)
            make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
            make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
            # Ben says every scan type requires a sample_x sample_y section


        elif (scan_type == scan_types.DETECTOR_IMAGE):
            xmtr_name = 'detector_x'
            ymtr_name = 'detector_y'
            make_detector(nx_inst_grp, 'sample_x', xpnts, count_time=count_time, unit='um', modify=modify)
            make_detector(nx_inst_grp, 'sample_y', ypnts, count_time=count_time, unit='um', modify=modify)
            # Ben says every scan type requires a sample_x sample_y section


        else:
            xmtr_name = 'sample_x'
            ymtr_name = 'sample_y'

        make_detector(nx_inst_grp, xmtr_name, xpnts, count_time=count_time, unit='um', modify=modify)
        make_detector(nx_inst_grp, ymtr_name, ypnts, count_time=count_time, unit='um', modify=modify)


    else:
        nx_inst_grp = nf[nxkd.NXD_INSTRUMENT]

        # make source entry

    if(counter in list(nx_inst_grp.keys())):
        modify = True
    else:
        modify = False

    make_counter_new(nx_inst_grp, counter, data_dct, 'NXdetector', 'NX_FLOAT', modify=modify)


def make_positioner(nf, name, mtr): #name, desc, pos, softmin, softmax):

    nxgrp = _group(nf, name, 'NXpositioner')
    #_string_attr(nxgrp, 'description',desc)
    make_string_data(nxgrp, 'description',mtr.get('description'))
    make_string_data(nxgrp, 'name',name)
    #_string_attr(nxgrp, 'name', name)
    _dataset(nxgrp, 'value', mtr.get('VAL'), 'NX_NUMBER')
    _dataset(nxgrp, 'raw_value', mtr.get(RBV), 'NX_NUMBER')
    _dataset(nxgrp, 'target_value', mtr.get('VAL'), 'NX_NUMBER')
    _dataset(nxgrp, 'soft_limit_min', mtr.get_low_limit(), 'NX_NUMBER')
    _dataset(nxgrp, 'soft_limit_max', mtr.get_high_limit(), 'NX_NUMBER')
    
    _dataset(nxgrp, 'tolerance', mtr.get('RDBD'), 'NX_NUMBER')
    _dataset(nxgrp, 'velocity', mtr.get('velocity'), 'NX_NUMBER')
    _dataset(nxgrp, 'acceleration_time', mtr.get('ACCL'), 'NX_NUMBER')
    _string_attr(nxgrp, 'controller_record', name)

def make_positioners(nxgrp, posners_dct={}, modify=False):
    #try:
    if(not modify):
        nx_dct = readin_base_classes('NXpositioner')

    for k in list(posners_dct.keys()):
        #print posners_dct[k]
        if(not modify):
            posgrp = make_NXclass(nxgrp, k, 'NXpositioner', nx_dct['NXpositioner'], nxgrp)
        else:
            posgrp = nxgrp[k]

        posgrp['velocity'][()] = posners_dct[k]['VELO']
        posgrp['value'][()] = posners_dct[k]['VAL']
        posgrp['target_value'][()] = posners_dct[k]['VAL']
        posgrp['description'][()] = posners_dct[k]['DESC']
        posgrp['controller_record'][()] = posners_dct[k]['NAME']
        posgrp['name'][()] = posners_dct[k]['NAME']
        posgrp['acceleration_time'][()] = posners_dct[k]['ACCL']
        posgrp['raw_value'][()] = posners_dct[k]['RRBV']
        posgrp['soft_limit_min'][()] = posners_dct[k]['LLM']
        posgrp['soft_limit_max'][()] = posners_dct[k]['HLM']
        posgrp['tolerance'][()] = posners_dct[k]['RDBD']
    # except:
    #     pass


def make_temperatures(nxgrp, temps_dct={}, modify=False):
    #try:
    if (not modify):
        nx_dct = readin_base_classes('NXsensor')

    for k in list(temps_dct.keys()):
        # print temps_dct[k]
        if (not modify):
            tmgrp = make_NXclass(nxgrp, k, 'NXsensor', nx_dct['NXsensor'], nxgrp)
        else:
            tmgrp = nxgrp[k]

        tmgrp['value'][()] = temps_dct[k][RBV]
        tmgrp['name'][()] = temps_dct[k]['DESC']
        tmgrp['measurement'][()] = 'temperature'
        tmgrp['short_name'][()] = k
        tmgrp['type'][()] = temps_dct[k]['EGU']
        tmgrp['run_control'][()] = 1 #Is data collection controlled or synchronised to this quantity: 1=no

        remove_unused_NXsensor_fields(tmgrp)

    #except:
    #    pass

def make_pressures(nxgrp, press_dct={}, modify=False):
    #try:
    if (not modify):
        nx_dct = readin_base_classes('NXsensor')

    for k in list(press_dct.keys()):
        # print temps_dct[k]
        if (not modify):
            prssgrp = make_NXclass(nxgrp, k, 'NXsensor', nx_dct['NXsensor'], nxgrp)
        else:
            prssgrp = nxgrp[k]

        prssgrp['value'][()] = press_dct[k][RBV]
        prssgrp['name'][()] = press_dct[k]['DESC']
        prssgrp['measurement'][()] = 'pressure'
        prssgrp['short_name'][()] = k
        prssgrp['type'][()] = press_dct[k]['EGU']
        prssgrp['run_control'][()] = 1 #Is data collection controlled or synchronised to this quantity: 1=no

        remove_unused_NXsensor_fields(prssgrp)

def make_pvs(nxgrp, pvs_dct={}, modify=False):
    #try:
    if (not modify):
        nx_dct = readin_base_classes('NXsensor')

    for k in list(pvs_dct.keys()):
        # print temps_dct[k]
        if (not modify):
            pvgrp = make_NXclass(nxgrp, k, 'NXsensor', nx_dct['NXsensor'], nxgrp)
        else:
            pvgrp = nxgrp[k]

        if(hasattr(pvs_dct[k][RBV], 'shape')):
            #print 'make_pvs: [%s]=', (k, pvs_dct[k][RBV], type(pvs_dct[k][RBV]), pvs_dct[k][RBV].shape)
            if('RBV' not in list(pvs_dct[k].keys())):
                continue
            if(pvs_dct[k][RBV][()] == 'null'):
                pvgrp['value'][()] = 0.0
            else:
                pvgrp['value'][()] = pvs_dct[k][RBV][()]
            pvgrp['name'][()] = pvs_dct[k]['PVNAME'][()]
            pvgrp['short_name'][()] = k
            remove_unused_NXsensor_fields(pvgrp)
            del pvgrp['measurement']
            del pvgrp['run_control']
            del pvgrp['type']
        else:
            #print 'this has no shape so removing: ', (k, pvs_dct[k][RBV], type(pvs_dct[k][RBV]))
            del pvgrp

def remove_unused_NXsensor_fields(nxgrp):
    # remove unused NXsensor fields
    del nxgrp['attached_to']
    del nxgrp['external_field_brief']
    del nxgrp['external_field_full']
    del nxgrp['geometry']
    del nxgrp['high_trip_value']
    del nxgrp['low_trip_value']
    del nxgrp['model']
    del nxgrp['value_deriv1']
    del nxgrp['value_deriv1_log']
    del nxgrp['value_deriv2']
    del nxgrp['value_deriv2_log']
    del nxgrp['value_log']


def nx_class_dict_to_nexus(nf, nx_class_dct):
    
    for k in nx_class_dct:
        dct[k] = nx_class_dct[k]

def make_1d_array(numpts, val):
    arr = np.ones(int(numpts), dtype=np.float32)
    if(isinstance(val, list)):
        num_vals = len(val)
        if(num_vals == numpts):
            arr[:] = val
        else:
            mults = int(numpts/num_vals)
            arr[:] = np.tile(val, (mults))
    else:
        if(isinstance(val, float)):
            arr[:] = val

    return(arr)


def get_roi_and_data(entry_dct, counter):
    """ take entry_dct and pull out only the ROI and DATA parts for use when loading scan params into the GUI
    """
    dct = {}
    dct_put(dct, ADO_CFG_WDG_COM, entry_dct['WDG_COM'])
    dct_put(dct, nxkd.NXD_DATA, entry_dct['COUNTERS'][counter][nxkd.NXD_DATA])
    return(dct)

def new_get_roi_and_data(entry_dct, counter):
    """ take entry_dct and pull out only the ROI and DATA parts for use when loading scan params into the GUI
    """
    dct = {}
    dct_put(dct, ADO_CFG_WDG_COM, entry_dct['WDG_COM'])
    dct_put(dct, nxkd.NXD_DATA, entry_dct['COUNTERS'][counter][nxkd.NXD_DATA])
    return(dct)

def get_entry_data_status(entry_grp):
    sts = entry_grp[nxkd.NXD_COLLECTION]['scan_request']['data_status'][()]
    return(sts)

def fix_start_time_and_other_fields(nx_src, dest):
    tm_str = nx_src['end_time'][()]

    dest[SPDB_ACTIVE_DATA_OBJECT][ADO_START_TIME] = nx_src['start_time'][()]
    dest[SPDB_ACTIVE_DATA_OBJECT][ADO_END_TIME] = nx_src['end_time'][()]
    dest[SPDB_ACTIVE_DATA_OBJECT][ADO_VERSION] = nx_src['version'][()]



def get_NXstxm_entry(entry_grp):
    """
        the goal is to load a nexus file and return an entry dict that contains:
         - DATA        The data that represents the entry
         - WDG_COM     The WDG_COM used to configure the scan
         
        so what should be returned is a dict with 2 keys ['WDGCOM', nxkd.NXD_DATA]
            
    """
    from cls.utils.roi_utils import get_ado_obj_from_wdg_com
    try:
        dct = {}
        
        
        #dct_put(dct, 'CFG.ROI.THETA', entry_dct['numE']['rotation_angle'])
        js_str = entry_grp[nxkd.NXD_COLLECTION]['scan_request']['scan_request'][()]


        if(isinstance(js_str, (list, np.ndarray))):
            js_str = js_str[0]
            
        wdg_dct = json.loads(js_str)

        #a place to keep the indiv ev_rois for each spatial ID
        #spid_ev_rois = {}
        for sp_id in wdg_dct['SPATIAL_ROIS']:
            fix_start_time_and_other_fields(entry_grp, wdg_dct['SPATIAL_ROIS'][sp_id])
            # erois = []
            # spid_ev_rois = wdg_dct['SPATIAL_ROIS'][sp_id]['EV_ROIS']
            # for eroi in  spid_ev_rois:
            #     erois.append(eroi)

        dct_put(dct, 'WDG_COM', wdg_dct)
        
        ado = get_ado_obj_from_wdg_com(wdg_dct)
        
        #wdg_dct['SPATIAL_ROIS']['0']['ACTIVE_DATA_OBJ']['CFG']['DATA_STATUS']
        #d_sts= get_entry_data_status(entry_grp)
        
        #dct_put(dct, 'DATA_STATUS', d_sts)

        datas = {}
        nxkd.NXD_grps = find_NXdata_groups(entry_grp)
        for nxkd.NXD_grp in nxkd.NXD_grps:
            datas[nxkd.NXD_grp] = get_axes_data_from_NXdata(entry_grp[nxkd.NXD_grp]) 
        
        dct_put(dct, nxkd.NXD_DATA, datas)
        return(dct)

    except ValueError:
        _logger.error('Datafile appears to be corrupt or non standard')
        
             
# def get_NXstxm_entry(entry_grp):
#     """
#         the goal is to load a nexus file and return an entry dict that contains:
#          - DATA        The data that represents the entry
#          - WDG_COM     The WDG_COM used to configure the scan
#          
#         so what should be returned is a dict with 2 keys ['WDGCOM', nxkd.NXD_DATA]
#             
#     """
#     
#     try:
#         dct = {}
#         
#         #dct_put(dct, 'CFG.ROI.THETA', entry_dct['numE']['rotation_angle'])
#         js_str = entry_grp[nxkd.NXD_COLLECTION]['scan_request']['scan_request'][()]
#         if(isinstance(js_str, (list, np.ndarray))):
#             js_str = js_str[0]
#             
#         wdg_dct = json.loads(js_str)
#         #dct_put(dct, 'CFG', cfg_dct)
#         #dct_put(dct, 'WDG_COM', wdg_dct)
#         
# #         cntr_str = None
# #         counter_dct = {}
# #         for k in entry_dct.keys():
# #             if((k.find('counter') > -1) or (k.find('Counter') > -1)):
# #                 cntr_str = k
# # #                 counter_dct[k] = {}
# # #                 counter_dct[k]['COUNT_TIME'] = entry_dct[k]['count_time'][()]
# # #                 counter_dct[k]['STXM_SCAN_TYPE'] = entry_dct[k]['stxm_scan_type'][()]
# # #                 #get attributes
# # #                 attrs = entry_dct[k].attrs
# # #                 axes = attrs['axes'] #a string ex: energy,sample_y,sample_x
# # #                 signal_name = attrs['signal']
# # #                 
# # #                 counter_dct[k]['SIGNAL'] = signal_name.upper() #a string ex: signal=data
# # #                 #the actual signal data
# # #                 counter_dct[k][signal_name.upper()] = entry_dct[k][signal_name][()]
# # #                 #now get the indices and their repsective data
# # #                 for ax in axes:
# # #                     counter_dct[k][ax.upper() + '_INDICES'] = attrs[ax + '_indices']
# # #                     counter_dct[k][ax.upper()] = entry_dct[k][ax][()]
# # #                
# # #        dct_put(dct, 'COUNTERS', counter_dct)
# # 
# #         
# #         if(cntr_str is not None):
# #             #return(new_get_roi_and_data(dct, cntr_str))
# #             dct_put(dct, 'WDG_COM', wdg_dct)
# #             dct_put(dct, nxkd.NXD_DATA, entry_dct[cntr_str][nxkd.NXD_DATA][()])
# #             return(dct)
#         
#         dct_put(dct, 'WDG_COM', wdg_dct)
#         
#         
#         datas = {}
#         nxkd.NXD_grps = find_NXdata_groups(entry_grp)
#         for nxkd.NXD_grp in nxkd.NXD_grps:
#             datas[nxkd.NXD_grp] = get_axes_data_from_NXdata(entry_grp[nxkd.NXD_grp]) 
#         
#         dct_put(dct, nxkd.NXD_DATA, datas)
# #         else:
# #             _logger.error('this entry_dct contains no data')
# #       
#         return(dct)
#       
#         #return(None)
#     
#     except ValueError:
#         _logger.error('Datafile appears to be corrupt or non standard')        


# def get_NXstxm_entry(entry_dct, only_roi_and_data=False):
#     """
#         the goal is to load a nexus file and return an entry dict that contains:
#          - DATA        The data that represents the entry
#          - WDG_COM     The WDG_COM used to configure the scan
#          
#         so what should be returned is a dict with 2 keys ['WDGCOM', nxkd.NXD_DATA]
#             
#     """
#     
#     try:
#         dct = {}
#         #everything below will be a child of 'SCAN' in teh dict
#         dct_put(dct, ADO_START_TIME, entry_dct['start_time'])
#         dct_put(dct, ADO_END_TIME, entry_dct['end_time'])
#         #dct_put(scan_dct, 'DEFINITION', entry_dct['definition'])
#         #dct_put(scan_dct, 'TITLE', entry_dct['title'])
#         #dct_put(dct, ADO_VERSION, entry_dct['version'])
#         
#         #dct_put(dct, 'CFG.ROI.THETA', entry_dct['numE']['rotation_angle'])
#         js_str = entry_dct[nxkd.NXD_COLLECTION]['scan_request']['scan_request'][()]
#         if(isinstance(js_str, (list, np.ndarray))):
#             js_str = js_str[0]
#             
#         wdg_dct = json.loads(js_str)
#         #dct_put(dct, 'CFG', cfg_dct)
#         dct_put(dct, 'WDG_COM', wdg_dct)
#         
#         cntr_str = None
#         counter_dct = {}
#         for k in entry_dct.keys():
#             if((k.find('counter') > -1) or (k.find('Counter') > -1)):
#                 cntr_str = k
#                 counter_dct[k] = {}
#                 counter_dct[k]['COUNT_TIME'] = entry_dct[k]['count_time'][()]
#                 counter_dct[k]['STXM_SCAN_TYPE'] = entry_dct[k]['stxm_scan_type'][()]
#                 #get attributes
#                 attrs = entry_dct[k].attrs
#                 axes = attrs['axes'] #a string ex: energy,sample_y,sample_x
#                 signal_name = attrs['signal']
#                 
#                 counter_dct[k]['SIGNAL'] = signal_name.upper() #a string ex: signal=data
#                 #the actual signal data
#                 counter_dct[k][signal_name.upper()] = entry_dct[k][signal_name][()]
#                 #now get the indices and their repsective data
#                 for ax in axes:
#                     counter_dct[k][ax.upper() + '_INDICES'] = attrs[ax + '_indices']
#                     counter_dct[k][ax.upper()] = entry_dct[k][ax][()]
#                 
#         dct_put(dct, 'COUNTERS', counter_dct)
#         
#         if(only_roi_and_data):
#             if(cntr_str is not None):
#                 return(get_roi_and_data(dct, cntr_str))
#         
#         return(dct)
#     
#     except ValueError:
#         _logger.error('Datafile appears to be corrupt or non standard')        
        
def make_stxm_entry(nf, name, scan_type, data_dct={}):
    """ create the basic entry group and the main sub groups
    that make up the NXstxm structure
    
    MAIN_OBJ.set('TIME', make_timestamp_now())
    MAIN_OBJ.set(ADO_CFG_CUR_EV_IDX, _ev_idx)
    MAIN_OBJ.set(ADO_CFG_CUR_SAMPLE_POS, sample_pos)
    MAIN_OBJ.set(ADO_CFG_CUR_SEQ_NUM, seq_num)
    MAIN_OBJ.set(ADO_CFG_DATA_DIR, datadir)
    MAIN_OBJ.set(ADO_CFG_DATA_FILE_NAME, 's%d-%05d' % (sample_pos, seq_num))
    MAIN_OBJ.set(ADO_CFG_UNIQUEID, 'ms%d-%05d' % (sample_pos, seq_num))

    for sample image, point spec and line spc scans the data is in
        ADO_STACK_DATA_POINTS
    organized into following shape:
        ADO_STACK_DATA_POINTS [sp_id: an integer] [polarization: an integer index] [energy: an integer index] [y] [x]

    The format of the data in teh nxstxm file however needs to be of the format below:
    in speaking with Ben Watts, the following represents version 1.0 of nxstxm in regards to how to handle multi polarization data
            given 3 spatial regions, 3 polarizations and 10 energy's
        NexusFile:
            - entry0 -> Pol 1 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry1 -> Pol 1 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry2 -> Pol 1 ->Sp 3 -> (10, Y, X) #images for all 10 energies
            - entry3 -> Pol 2 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry4 -> Pol 2 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry5 -> Pol 2 ->Sp 3 -> (10, Y, X) #images for all 10 energies
            - entry6 -> Pol 3 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry7 -> Pol 3 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry8 -> Pol 3 ->Sp 3 -> (10, Y, X) #images for all 10 energies

    so given the data in the ADO_STACK_DATA_POINTS create the required nxstxm structure
    """
    
    data_1d_dct = _data_as_1D(data_dct)
    data_dct = dict(list(data_dct.items()) + list(data_1d_dct.items()))
    
    entry_nxgrp = _group(nf, name, 'NXentry')
    _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
    _dataset(entry_nxgrp, 'start_time', dct_get(data_dct,ADO_START_TIME), 'NX_DATE_TIME')
    _dataset(entry_nxgrp, 'end_time', dct_get(data_dct,ADO_END_TIME), 'NX_DATE_TIME')
    _dataset(entry_nxgrp, 'definition','NXstxm', 'NX_CHAR')
    _dataset(entry_nxgrp, 'version','1.0', 'NX_CHAR')
    #_dataset(entry_nxgrp, 'data_status', dct_get(data_dct, ADO_CFG_DATA_STATUS), 'NX_CHAR')
    
    make_instrument(entry_nxgrp, data_dct, scan_type=scan_type)
    make_sample(entry_nxgrp, data_dct)
    make_data_section(entry_nxgrp, 'counter0', data_dct=data_dct, scan_type=scan_type)
            
    positioners_dct = dct_get(data_dct,'POSITIONERS')
    col_grp = _group(entry_nxgrp, nxkd.NXD_COLLECTION, 'NXcollection')
    make_positioners(col_grp, positioners_dct)

    #todo
    temperatures_dct = dct_get(data_dct,'TEMPERATURES')
    make_temperatures(col_grp, temperatures_dct)
    pressures_dct = dct_get(data_dct,'PRESSURES')
    make_pressures(col_grp, pressures_dct)
    
    wdg_com = dct_get(data_dct,ADO_CFG_WDG_COM)

    # update start/stop times as well as other base items
    wdg_com['title'] = 'NeXus sample'
    wdg_com['start_time'] = dct_get(data_dct, ADO_START_TIME)
    wdg_com['end_time'] = dct_get(data_dct, ADO_END_TIME)
    wdg_com['definition'] =  'NXstxm'
    wdg_com['version'] =  '1.0'
    #end update

    js_str = dict_to_json_string(wdg_com, to_unicode=True)
    scan_grp = _group(col_grp, 'scan_request', 'NXscanDefinition')
    _dataset(scan_grp, 'scan_request', js_str, 'NXchar')
    
    #sts = get_data_status_from_wdg_com(wdg_com)
    ##sts = wdg_com['SPATIAL_ROIS'][0]['ACTIVE_DATA_OBJ']['CFG']['DATA_STATUS']
    #_dataset(scan_grp, 'data_status', sts, 'NXchar')
    
    return(entry_nxgrp)


def make_stxm_stack_entries(nf, name, scan_type, data_dct={}):
    """ create the basic entry group and the main sub groups
    that make up the NXstxm structure

    MAIN_OBJ.set('TIME', make_timestamp_now())
    MAIN_OBJ.set(ADO_CFG_CUR_EV_IDX, _ev_idx)
    MAIN_OBJ.set(ADO_CFG_CUR_SAMPLE_POS, sample_pos)
    MAIN_OBJ.set(ADO_CFG_CUR_SEQ_NUM, seq_num)
    MAIN_OBJ.set(ADO_CFG_DATA_DIR, datadir)
    MAIN_OBJ.set(ADO_CFG_DATA_FILE_NAME, 's%d-%05d' % (sample_pos, seq_num))
    MAIN_OBJ.set(ADO_CFG_UNIQUEID, 'ms%d-%05d' % (sample_pos, seq_num))

    for sample image, point spec and line spc scans the data is in
        ADO_STACK_DATA_POINTS
    organized into following shape:
        ADO_STACK_DATA_POINTS [sp_id: an integer] [polarization: an integer index] [energy: an integer index] [y] [x]

    The format of the data in teh nxstxm file however needs to be of the format below:
    in speaking with Ben Watts, the following represents version 1.0 of nxstxm in regards to how to handle multi polarization data
            given 3 spatial regions, 3 polarizations and 10 energy's
        NexusFile:
            - entry0 -> Pol 1 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry1 -> Pol 1 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry2 -> Pol 1 ->Sp 3 -> (10, Y, X) #images for all 10 energies
            - entry3 -> Pol 2 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry4 -> Pol 2 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry5 -> Pol 2 ->Sp 3 -> (10, Y, X) #images for all 10 energies
            - entry6 -> Pol 3 ->Sp 1 -> (10, Y, X) #images for all 10 energies
            - entry7 -> Pol 3 ->Sp 2 -> (10, Y, X) #images for all 10 energies
            - entry8 -> Pol 3 ->Sp 3 -> (10, Y, X) #images for all 10 energies

    so given the data in the ADO_STACK_DATA_POINTS create the required nxstxm structure
    """



    stack_data = dct_get(data_dct, ADO_STACK_DATA_POINTS)

    counter_lst = list(stack_data.keys())

    #num_spids = len(spid_data)
    num_pols = len(stack_data[counter_lst[0]][0])
    sp_rois = dct_get(data_dct, ADO_SP_ROIS)
    entry_idx = 0

    for p in range(num_pols):
        for sp_id in sp_rois:

            pol_pnt = sp_rois[sp_id][EV_ROIS][0]['EPU_POL_PNTS'][p]

            _data_dct = {}
            data_1d_dct = {}
            data_1d_dct = _data_as_1D(data_dct, sp_id=sp_id)
            _data_dct = dict(list(data_dct.items()) + list(data_1d_dct.items()))

            #data = spid_data[sp_id][p]
            entry_nxgrp = _group(nf, 'entry%d' % entry_idx, 'NXentry')
            _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
            _dataset(entry_nxgrp, 'start_time', dct_get(_data_dct, ADO_START_TIME), 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'end_time', dct_get(_data_dct, ADO_END_TIME), 'NX_DATE_TIME')
            _dataset(entry_nxgrp, 'definition', 'NXstxm', 'NX_CHAR')
            _dataset(entry_nxgrp, 'version', '1.0', 'NX_CHAR')
            # _dataset(entry_nxgrp, 'data_status', dct_get(data_dct, ADO_CFG_DATA_STATUS), 'NX_CHAR')


            make_instrument(entry_nxgrp, _data_dct, scan_type=scan_type, pol_pnt=pol_pnt)
            make_sample(entry_nxgrp, _data_dct)

            #for counter in counter_lst:
            #    data = spid_data[counter][sp_id][p]
            #    make_data_section(entry_nxgrp, counter, data_dct=_data_dct, scan_type=scan_type, dddata=data)
            counter = counter_lst[0]
            data = stack_data[counter][sp_id][p]
            make_data_section(entry_nxgrp, counter, data_dct=_data_dct, scan_type=scan_type, dddata=data)

            positioners_dct = dct_get(_data_dct, 'POSITIONERS')
            col_grp = _group(entry_nxgrp, nxkd.NXD_COLLECTION, 'NXcollection')
            make_positioners(col_grp, positioners_dct)

            # todo
            temperatures_dct = dct_get(_data_dct, 'TEMPERATURES')
            make_temperatures(col_grp, temperatures_dct)
            pressures_dct = dct_get(_data_dct, 'PRESSURES')
            make_pressures(col_grp, pressures_dct)

            wdg_com = dct_get(_data_dct, ADO_CFG_WDG_COM)
            js_str = dict_to_json_string(wdg_com, to_unicode=True)
            scan_grp = _group(col_grp, 'scan_request', 'NXscanDefinition')
            _dataset(scan_grp, 'scan_request', js_str, 'NXchar')

            # sts = get_data_status_from_wdg_com(wdg_com)
            ##sts = wdg_com['SPATIAL_ROIS'][0]['ACTIVE_DATA_OBJ']['CFG']['DATA_STATUS']
            # _dataset(scan_grp, 'data_status', sts, 'NXchar')
            entry_idx += 1

    return (entry_nxgrp)



def make_polarization_stxm_entry(nf, name, scan_type, data_dct={}):
    """ create the basic entry group and the main sub groups
    that make up the NXstxm structure
    
    MAIN_OBJ.set('TIME', make_timestamp_now())
    MAIN_OBJ.set(ADO_CFG_CUR_EV_IDX, _ev_idx)
    MAIN_OBJ.set(ADO_CFG_CUR_SAMPLE_POS, sample_pos)
    MAIN_OBJ.set(ADO_CFG_CUR_SEQ_NUM, seq_num)
    MAIN_OBJ.set(ADO_CFG_DATA_DIR, datadir)
    MAIN_OBJ.set(ADO_CFG_DATA_FILE_NAME, 's%d-%05d' % (sample_pos, seq_num))
    MAIN_OBJ.set(ADO_CFG_UNIQUEID, 'ms%d-%05d' % (sample_pos, seq_num))
    
    """
    
    data_1d_dct = _data_as_1D_polarities_are_entries(data_dct)
    data_dct = dict(list(data_dct.items()) + list(data_1d_dct.items()))
    
    entry_nxgrp = _group(nf, name, 'NXentry')
    _dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
    _dataset(entry_nxgrp, 'start_time', dct_get(data_dct,ADO_START_TIME), 'NX_DATE_TIME')
    _dataset(entry_nxgrp, 'end_time', dct_get(data_dct,ADO_END_TIME), 'NX_DATE_TIME')
    _dataset(entry_nxgrp, 'definition','NXstxm', 'NX_CHAR')
    _dataset(entry_nxgrp, 'version','1.0', 'NX_CHAR')
    #_dataset(entry_nxgrp, 'data_status', dct_get(data_dct, ADO_CFG_DATA_STATUS), 'NX_CHAR')
    
    make_instrument(entry_nxgrp, data_dct, scan_type=scan_type)
    make_sample(entry_nxgrp, data_dct)
    make_data_section(entry_nxgrp, 'counter0', data_dct=data_dct, scan_type=scan_type)
            
    positioners_dct = dct_get(data_dct,'POSITIONERS')
    col_grp = _group(entry_nxgrp, nxkd.NXD_COLLECTION, 'NXcollection')
    make_positioners(col_grp, positioners_dct)
    
    cfg_dict = dct_get(data_dct,ADO_CFG_WDG_COM)
    js_str = dict_to_json_string(cfg_dict,to_unicode=True)
    scan_grp = _group(col_grp, 'scan_request', 'NXscanDefinition')
    _dataset(scan_grp, 'scan_request', js_str, 'NXchar')
    
    return(entry_nxgrp)


def modify_stxm_entry(nf, name, scan_type, data_dct={}):
    """ 
    """
    data_1d_dct = _data_as_1D(data_dct)
    data_dct = dict(list(data_dct.items()) + list(data_1d_dct.items()))
    
    entry_nxgrp = nf[name]
    #del entry_nxgrp['end_time']
    #entry_nxgrp['end_time'] = dct_get(data_dct,ADO_END_TIME)
    replace_string_data(entry_nxgrp, 'end_time', dct_get(data_dct,ADO_END_TIME))
    #replace_string_data(entry_nxgrp, 'data_status', dct_get(data_dct, ADO_CFG_DATA_STATUS))
    
    make_instrument(entry_nxgrp, data_dct, modify=True)
    make_sample(entry_nxgrp, data_dct, modify=True)
    make_data_section(entry_nxgrp, 'counter0', data_dct=data_dct, scan_type=scan_type, modify=True)
    
    positioners_dct = dct_get(data_dct,'POSITIONERS')
    col_grp = entry_nxgrp[nxkd.NXD_COLLECTION]
    make_positioners(col_grp, positioners_dct, modify=True)
    #sts = dct_get(data_dct, ADO_CFG_DATA_STATUS)
    #col_grp['scan_request']['data_status'][()] = sts
    #dct_put(self.data_dct, ADO_CFG_DATA_STATUS, DATA_STATUS_FINISHED)
    
    return(entry_nxgrp)

def make_stxm_dct_to_file(nf, name, stxm_dct, nx_dct):
    """ create the basic entry group and the main sub groups
    that make up the NXstxm structure
    nxkd.HDF5_VER = nxkd.HDF5_VER
nxkd.NEXUS_VER = nxkd.NEXUS_VER

nxkd.NXD_COLLECTION = nxkd.NXD_COLLECTION
nxkd.NXD_ENTRY = 'NXentry'
nxkd.NXD_HDF_VER = nxkd.NXD_HDF_VER
nxkd.NXD_NX_VER = nxkd.NXD_NX_VER
nxkd.NXD_ENTRY = nxkd.NXD_ENTRY
nxkd.NXD_INSTRUMENT = nxkd.NXD_INSTRUMENT
nxkd.NXD_SAMPLE = nxkd.NXD_SAMPLE
nxkd.NXD_DATA = nxkd.NXD_DATA
    
    
    """
    entry_nxgrp = _group(nf, name, 'NXentry')
    _string_attr(entry_nxgrp, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
    _string_attr(entry_nxgrp, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
    
    nxclass_dict_to_nx(entry_nxgrp, nxkd.NXD_ENTRY, 'NXentry', nx_dct['NXentry'])
    nxclass_dict_to_nx(entry_nxgrp, nxkd.NXD_INSTRUMENT, 'NXinstrument', nx_dct['NXinstrument'])
    nxclass_dict_to_nx(entry_nxgrp, nxkd.NXD_SAMPLE, 'NXsample', nx_dct['NXsample'])
    nxclass_dict_to_nx(entry_nxgrp, nxkd.NXD_DATA, 'NXdata', nx_dct['NXdata'])
    nxclass_dict_to_nx(entry_nxgrp, nxkd.NXD_COLLECTION, 'NXcollection', nx_dct['NXcollection'])
    
    return(entry_nxgrp)

def nx_class_to_dct(name, c):
    #print 'NEXUS_MAP["%s"] = {' % name
    dct = dump_fields(c['fields'])
    #print '\t}'
    return(dct)
    

def nx_classes_to_dct(class_dir='base_classes'):
    if(class_dir == 'base_classes'):
        nxclss = readin_base_classes()
    elif(class_dir == 'application_classes'):
        nxclss = readin_application_classes()
    elif(class_dir == 'contributed_definition_classes'):
        nxclss = readin_contributed_definition_classes()
        
    classes_dct = {}
    print('Base Classes')
    for k in list(nxclss.keys()):
        classes_dct[k] = nx_class_to_dct(k, nxclss[k])
    
    return(classes_dct)

def convert(data):
    import collections
    
    if isinstance(data, str):
        return(str(data, 'utf8'))
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
    
test_polarization_entries = False
    
def create_NXstxm_file(fname, scan_type, data_dct={'ID':None}, intermediate_file=False):

    if(test_polarization_entries):
        return(create_polarization_entries_NXstxm_file(fname, scan_type, data_dct=data_dct, intermediate_file=intermediate_file))
    else:
        return(create_standard_NXstxm_file(fname, scan_type, data_dct=data_dct, intermediate_file=intermediate_file))


def create_entry_in_NXstxm_file(fname, scan_type, data_dct={'ID':None}, intermediate_file=False, entry_num=1):
    """
    
    """
    
    #import json
    #js = json.loads(file('NXstxm.json').read())
    if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
        _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        return((False, ''))
    
    #_logger.info('create_NXstxm_file: saving [%s]' % fname)
    save_success = True
    #data_dir = dct_get(data_dct, ADO_CFG_DATA_DIR)
    #fprefix = dct_get(data_dct, ADO_CFG_DATA_FILE_NAME)
    spatial_roi_id = dct_get(data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX)
    #fname = data_dir + '/' + fprefix + '.hdf5'
    
    modify_file = False
    
    #if(os.path.exists(fname)):
    # 'a' Read/write if exists, create otherwise (default)
    nf = h5py.File(fname, "a")
    
    if(('entry%d' % entry_num) in list(nf.keys())):
        modify_file = True
    
    #if os.path.exists(fname):
    if(modify_file):
        _logger.info('Updating existing file')
        #nf = h5py.File(fname, "a")
        entry_grp = modify_stxm_entry(nf, 'entry%d' % entry_num, scan_type, data_dct)
    else:
        #nf = h5py.File(fname, "a")
        entry_grp = make_stxm_entry(nf, 'entry%d' % entry_num, scan_type, data_dct)
    nf.flush()    
    nf.close()
    #_logger.debug('[%s] is now closed' % fname)
    return((save_success, fname))
       
###############################################################################
###############################################################################
def create_standard_NXstxm_file(fname, scan_type, data_dct={'ID':None}, intermediate_file=False):
    """
    This function should probably endup in an NX class that implements an Exporter API
    for now it accepts a filename, scan_type and the data_dct that comes from pyStxm, 
    it pulls out of the data_dct the required information and writes it into a Nexus
    NXstxm defined file. If the file is successfully saved then return a tuple of
    (<save success>, <filename>)
    
    """
    
    #import json
    #js = json.loads(file('NXstxm.json').read())
    if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
        _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        return((False, ''))
    
    #_logger.info('create_NXstxm_file: saving [%s]' % fname)
    save_success = True
#    data_dir = dct_get(data_dct, ADO_CFG_DATA_DIR)
#    fprefix = dct_get(data_dct, ADO_CFG_DATA_FILE_NAME)
    spatial_roi_id = dct_get(data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX)
#    fname = data_dir + '/' + fprefix + '.hdf5'
    modify_file = False
    
    #_logger.info('create_NXstxm_file: fname=[%s]' % fname)
    
    # 'a' Read/write if exists, create otherwise (default)
    nf = h5py.File(fname, "a")
    
    if(('entry%d' % spatial_roi_id) in list(nf.keys())):
        modify_file = True
    
    #if os.path.exists(fname):
    if(modify_file):
        #nf = h5py.File(fname, "r+")
        entry_grp = modify_stxm_entry(nf, 'entry%d' % spatial_roi_id, scan_type, data_dct)
    else:
        #nf = h5py.File(fname, "a")
        _string_attr(nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
        _string_attr(nf, nxkd.NXD_H5PY_VER, h5py.__version__)
        _string_attr(nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
        _string_attr(nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
        _string_attr(nf, nxkd.NXD_FILE_NAME, fname)
        _string_attr(nf, nxkd.NXD_FILE_TIME, dct_get(data_dct,'TIME'))
        if(scan_type is scan_types.SAMPLE_IMAGE_STACK):
            entry_grp = make_stxm_stack_entries(nf, 'entry%d' % spatial_roi_id, scan_type, data_dct)
        else:
            entry_grp = make_stxm_entry(nf, 'entry%d' % spatial_roi_id, scan_type, data_dct)
    nf.flush()    
    nf.close()
    return((save_success, fname))

def update_attrs(fname, attr_dct):
    '''
    attr_path is the path in the nx file to the item we want to update, it is a series of strings
    that are connected by dots (.) that delineate the levels of the path

    dct[devname] = {'val':val, 'nxattr_path': nxattr_path, 'idx':len(self.update_dev_data), 'e_idx': img_idx_map_dct['e_idx']}



    :param attr_path: entry0.instrument.epu.gap
    :param val: the value to assign or append
    :return:
    '''
    #print attr_dct
    nf = h5py.File(fname, "a")

    #while the file is open update multiple of attrs
    for devname in list(attr_dct.keys()):
        nxattr_path = attr_dct[devname]['nxattr_path']
        val = attr_dct[devname]['val']
        nx_put(nf, nxattr_path, val)
        #print 'update_attrs: updating (file, attr, val)' , (fname, nxattr_path, val)

    nf.flush()
    nf.close()

def update_data(fname, entry, data, counter='counter0'):

    nf = h5py.File(fname,  "r+")
    nf.swmr_mode = True

    del nf[entry][counter][nxkd.NXD_DATA]
    nf[entry][counter][nxkd.NXD_DATA] = data
    print('nxstxm:update_data: fname=%s' % (fname))
    print('nxstxm:update_data: entry=%s, counter=%s' % (entry, counter))
    print('nxstxm:update_data: data.shape' , data.shape)
    nf.close()



def update_tmp_data(fname, idx, tmp_data_dct):
    '''
    This function takes an index value that represents the  current stack scan index as well  as
    a tmp_data_dct that contains a single instance of all dev's and detectors that have data to be recorded
        tmp_data_dct = {}
            tmp_data_dct['devs']['energy'] = 685.0
            tmp_data_dct['devs']['epu_gap'] = 235.8
            tmp_data_dct['devs']['epu_polarization'] = 1
            tmp_data_dct['devs']['epu_offset'] = 0.0
            tmp_data_dct['devs']['epu_angle'] = 0.0
            ...
            tmp_data_dct['dets']['counter0'] = [[356, 403 ...]]  # a numpy arrray of shape (100,100) for a 100x100 pt image
            tmp_data_dct['dets']['ring_current'] = 221.56  # a single value
            tmp_data_dct['dets']['ccd0'] = [[[356, 403 ...]]]  # a numpy arrray of shape (480,640) for a 640x480 pt image
            ...


    :param fname:
    :param idx:
    :param tmp_data_dct:
    :return:
    '''

    nf = h5py.File(fname,  "r+")
    nf.swmr_mode = True
    idx_str = 'idx%d' % idx
    idx_nxgrp = _group(nf, idx_str, 'idx_grp')
    i = 0
    for dev_name in list(tmp_data_dct['devs'].keys()):
        _dataset(idx_nxgrp, 'dev%d' % i, tmp_data_dct[dev_name], 'NX_tbd')
        print('nxstxm:update_tmp_data: [%s] dev%d' % (idx_str, i))
        i += 1
    i = 0
    for det_name in list(tmp_data_dct['dets'].keys()):
        _dataset(idx_nxgrp, 'det%d' % i, tmp_data_dct[det_name], 'NX_tbd')
        print('nxstxm:update_tmp_data: [%s] det%d' % (idx_str, i))
        i += 1
    nf.close()


###############################################################################
###############################################################################
def create_polarization_entries_NXstxm_file(fname, scan_type, data_dct={}, intermediate_file=False):
    """
    This function should probably endup in an NX class that implements an Exporter API
    for now it accepts a filename, scan_type and the data_dct that comes from pyStxm, 
    it pulls out of the data_dct the required information and writes it into a Nexus
    NXstxm defined file. If the file is successfully saved then return a tuple of
    (<save success>, <filename>)
    nxkd.NXD_H5PY_VER = nxkd.NXD_H5PY_VER
nxkd.NXD_NXPY_VER = nxkd.NXD_NXPY_VER
nxkd.NXD_FILE_NAME = nxkd.NXD_FILE_NAME
nxkd.NXD_FILE_TIME = nxkd.NXD_FILE_TIME
    
    """
    #import json
    #js = json.loads(file('NXstxm.json').read())
    if(data_dct['ID'] != 'ACTIVE_DATA_DICT'):
        _logger.error('Invalid data dictionary type [%s] should be type ACTIVE_DATA_DICT' % data_dct['ID'])
        return((False, ''))
    
    #_logger.info('create_NXstxm_file: saving [%s]' % fname)
    save_success = True
    data_dir = dct_get(data_dct, ADO_CFG_DATA_DIR)
    fprefix = dct_get(data_dct, ADO_CFG_DATA_FILE_NAME)
    spatial_roi_id = dct_get(data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX)
    fname = os.path.join(data_dir , fprefix,'.hdf5')
    modify_file = False
    
    #_logger.info('create_NXstxm_file: fname=[%s]' % fname)
    
    if((intermediate_file) and (os.path.exists(fname))):
        modify_file = True
    
    #if os.path.exists(fname):
    if(modify_file):
        nf = h5py.File(fname, "r+")
        entry_grp = modify_stxm_entry(nf, 'entry%d' % spatial_roi_id, scan_type, data_dct)
    else:
        nf = h5py.File(fname, "a")
        #_string_attr(nf, nxkd.NXD_HDF_VER, nxkd.HDF5_VER)
        _string_attr(nf, nxkd.NXD_H5PY_VER, h5py.__version__)
        _string_attr(nf, nxkd.NXD_NXPY_VER, nexpy.__version__)
        _string_attr(nf, nxkd.NXD_NX_VER, nxkd.NEXUS_VER)
        _string_attr(nf, nxkd.NXD_FILE_NAME, fname)
        _string_attr(nf, nxkd.NXD_FILE_TIME, dct_get(data_dct,'TIME'))
        for e_key in list(data_dct.keys()):
            if(e_key.find('entry_') > -1):
                entry_grp = make_polarization_stxm_entry(nf, e_key, scan_type, data_dct[e_key])
        
    nf.close()
    return((save_success, fname))


def load_single_entry_from_NXstxm_file(filename, only_roi_and_data=False):
    """
    read in a nexus h5 file and return a standard dict
    goal is to reproduce this, it is assumed that each file contains a single nxkd.NXD_ENTRY field only:
    
        dct_put(dct, 'ID', 'ACTIVE_DATA_DICT')    #the id of this dict type
        dct_put(dct, ADO_START_TIME, None)
        dct_put(dct, ADO_END_TIME, None)
        dct_put(dct, ADO_DEVICES, None)
        dct_put(dct, ADO_VERSION, None)
        
        dct_put(dct, ADO_DATA_SSCANS, {})
        dct_put(dct, ADO_DATA_POINTS, None)
        
        dct_put(dct, ADO_CFG_WDG_COM, None)
        dct_put(dct, ADO_CFG_SCAN_TYPE, None) 
        dct_put(dct, ADO_CFG_ROI, None)
        dct_put(dct, ADO_CFG_CUR_EV_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SAMPLE_POS, None)
        dct_put(dct, ADO_CFG_CUR_SEQ_NUM, None)
        dct_put(dct, ADO_CFG_DATA_DIR, None)
        dct_put(dct, ADO_CFG_DATA_FILE_NAME, None)     #the data file name WITHOUT the extension, that is determined by the
        dct_put(dct, ADO_CFG_UNIQUEID, None)
    """
    #create a standard active object, then load h5 file and populate the active object dict 
    active_data_obj = ActiveDataObj()
    active_data_obj.reset_data_dct()
    
    dct = active_data_obj.get_data_dct() 
    nf = None
    try:
        nf = h5py.File(filename,  "r")
        
        fname = nf.attrs[nxkd.NXD_FILE_NAME]
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(data_dir is None):
            return
        
        dct_put(dct, nxkd.NXD_HDF_VER, nf.attrs[nxkd.NXD_HDF_VER])
        dct_put(dct, nxkd.NXD_NX_VER, nf.attrs[nxkd.NXD_NX_VER])
        
        dct_put(dct, 'TIME', nf.attrs[nxkd.NXD_FILE_TIME])
        #now for each entry where its NXclass attr is of type NXentry, create a new spatial region dict entry
        entries = {}
        ekeys =list(nf.keys())
        for ekey in ekeys:
            if('NX_class' in list(nf[ekey].attrs.keys())):
                if(nf[ekey].attrs['NX_class'] == 'NXentry'):
                    #walk the entry 
                    #ADO_CFG_ROI
                    #each entry is returned from get_NXstxm_entry() as a 
                    # dift of ['CFG', nxkd.NXD_DATA]
                    entries[ekey] = get_NXstxm_entry(nf[ekey], only_roi_and_data)
                    dct_put(dct, '%s' % ekey, entries[ekey])
                    
                else:
                    print('[%s] is not of type NXentry' % ekey)
        
        dct_put(dct, 'DATA_DIR', data_dir)
        dct_put(dct, 'DATA_FILE_NAME', fprefix)
        ekey = ekeys[0]
        dct_put(dct, 'ENTRIES', {ekey: entries[ekey]})
        
        nf.close()
        
        if(only_roi_and_data):
            ekeys = list(entries.keys())
            #just return the first one for now
            return(entries[ekeys[0]])
        else:
            return(dct)
    
    except:
        if(nf is not None):
            nf.close()
        _logger.info('load_single_entry_from_NXstxm_file: opening file failed [%s]' % filename)  
        return(None)  

def get_data_from_NXdatas(nx_datas, counter_nm):
    data = nx_datas[counter_nm]['signal']
    return(data)
    

def get_NXdatas_from_entry(entry_dct, entry_nm=None):
    """ a convienience function to get the nxkd.NXD_DATA section from an entry
    """ 
    if(entry_nm):
        if(entry_nm in list(entry_dct.keys())):
            #print 'get_NXdatas_from_entry: keys', entry_dct[entry_nm][nxkd.NXD_DATA].keys()
            return(entry_dct[entry_nm][nxkd.NXD_DATA])
        else:
            _logger.error('entry name [%s] does not exist in entry_dct' % entry_nm)
            return(None)
    else:
        ekeys = list(entry_dct.keys())
        if(len(ekeys) > 0):
            return(entry_dct[ekeys[0]][nxkd.NXD_DATA])
        else:
            _logger.error('no entries exist in entry_dct' % entry_nm)
            return(None)
    
def get_wdg_com_from_entry(entry_dct, entry_nm=None):
    if(entry_nm):
        if(entry_nm in list(entry_dct.keys())):
            return(entry_dct[entry_nm]['WDG_COM'])
        else:
            _logger.error('entry name [%s] does not exist in entry_dct' % entry_nm)
            return(None)
    else:
        ekeys = list(entry_dct.keys())
        if(len(ekeys) > 0):
            return(entry_dct[ekeys[0]]['WDG_COM'])
        else:
            _logger.error('no entries exist in entry_dct' % entry_nm)
            return(None)
    
def load_NXstxm_file(filename, only_roi_and_data=False):
    """
    read in a nexus h5 file and return a standard dict
    goal is to reproduce this, it is assumed that each file contains a single nxkd.NXD_ENTRY field only:
    
        dct_put(dct, 'ID', 'ACTIVE_DATA_DICT')    #the id of this dict type
        dct_put(dct, ADO_START_TIME, None)
        dct_put(dct, ADO_END_TIME, None)
        dct_put(dct, ADO_DEVICES, None)
        dct_put(dct, ADO_VERSION, None)
        
        dct_put(dct, ADO_DATA_SSCANS, {})
        dct_put(dct, ADO_DATA_POINTS, None)
        
        dct_put(dct, ADO_CFG_WDG_COM, None)
        dct_put(dct, ADO_CFG_SCAN_TYPE, None) 
        dct_put(dct, ADO_CFG_ROI, None)
        dct_put(dct, ADO_CFG_CUR_EV_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SAMPLE_POS, None)
        dct_put(dct, ADO_CFG_CUR_SEQ_NUM, None)
        dct_put(dct, ADO_CFG_DATA_DIR, None)
        dct_put(dct, ADO_CFG_DATA_FILE_NAME, None)     #the data file name WITHOUT the extension, that is determined by the
        dct_put(dct, ADO_CFG_UNIQUEID, None)
    """
    #create a standard active object, then load h5 file and populate the active object dict 
    active_data_obj = ActiveDataObj()
    active_data_obj.reset_data_dct()
    
    #dct = active_data_obj.get_data_dct()
    dct = {} 
    nf = None
    try:
        nf = h5py.File(filename,  "r")
        
        
        #fname = nf.attrs[nxkd.NXD_FILE_NAME]
        data_dir, fprefix, fsuffix = get_file_path_as_parts(filename)
        if(data_dir is None):
            return
        
        entries = {}
        ekeys =list(nf.keys())
        for ekey in ekeys:
            ekey = str(ekey)
            if('NX_class' in list(nf[ekey].attrs.keys())):
                if(nf[ekey].attrs['NX_class'] == 'NXentry'):
                    
                    entries[ekey] = get_NXstxm_entry(nf[ekey])
                    dct_put(dct, '%s' % ekey, entries[ekey])
                    
                else:
                    print('[%s] is not of type NXentry' % ekey)
        
#        dct_put(dct, 'DATA_DIR', data_dir)
#        dct_put(dct, 'DATA_FILE_NAME', fprefix)
#        ekey = ekeys[0]
#        dct_put(dct, 'ENTRIES', {ekey: entries[ekey]})
        nf.close()
        
#         if(only_roi_and_data):
#             ekeys = entries.keys()
#             #just return the first one for now
#             return(entries[ekeys[0]])
#         else:
        return(dct)
    
    except:
        if(nf is not None):
            nf.close()
        _logger.info('load_NXstxm_file: opening file failed [%s]' % filename)
        return(None)  

def find_NXdata_groups(nf):
    """ searvh the nexus file for groups that have NXdata as their NX_CLASS
    """
    lst = []
    for k in list(nf.keys()):
        if(len(list(nf[k].attrs.keys())) > 0):
            if('NX_class' in list(nf[k].attrs.keys())):
                nx_class = nf[k].attrs['NX_class']
                if(nx_class == 'NXdata'):
                    lst.append(k)
    return(lst)         

def get_axes_data_from_NXdata(nf):
    """
    nf is the pointer to an NXdata group, read attributes and return the X, Y and Z data
    """    
    axes = nf.attrs['axes']
    ax_ind_dct = get_axes_name_indices(nf, axes)
    ax_ind_dct['axes'] = nf.attrs['axes']
    ax_ind_dct['axes_data'] = []
    for ax_nm in axes:
        ax_ind_dct[ax_nm]['signal'] = nf[ax_nm][()]
        ax_ind_dct['axes_data'].append(nf[ax_nm][()])
    ax_ind_dct['signal'] = nf[nxkd.NXD_DATA][()]
    
    return(ax_ind_dct)

def get_axes_name_indices(nf, ax_lst):
    """
    assuming ['energy','sample_y','sample_x']
    
    """
    indices_dct = {}
    # for ax_nm in ax_lst:
    #     indices_dct[ax_nm] = {'indices': int(nf.attrs['%s_indices' % ax_nm]), 'signal': None}
    for i, ax_nm in enumerate(ax_lst, 0):
        indices_dct[ax_nm] = {'indices': i, 'signal': None}
    return(indices_dct)
    

    
def load_all_entries_from_NXstxm_file(filename, only_roi_and_data=False):
    """
    read in a nexus h5 file and return a standard dict
    goal is to reproduce this, it is assumed that each file contains a single nxkd.NXD_ENTRY field only:
    
        dct_put(dct, 'ID', 'ACTIVE_DATA_DICT')    #the id of this dict type
        dct_put(dct, ADO_START_TIME, None)
        dct_put(dct, ADO_END_TIME, None)
        dct_put(dct, ADO_DEVICES, None)
        dct_put(dct, ADO_VERSION, None)
        
        dct_put(dct, ADO_DATA_SSCANS, {})
        dct_put(dct, ADO_DATA_POINTS, None)
        
        dct_put(dct, ADO_CFG_WDG_COM, None)
        dct_put(dct, ADO_CFG_SCAN_TYPE, None) 
        dct_put(dct, ADO_CFG_ROI, None)
        dct_put(dct, ADO_CFG_CUR_EV_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, None)
        dct_put(dct, ADO_CFG_CUR_SAMPLE_POS, None)
        dct_put(dct, ADO_CFG_CUR_SEQ_NUM, None)
        dct_put(dct, ADO_CFG_DATA_DIR, None)
        dct_put(dct, ADO_CFG_DATA_FILE_NAME, None)     #the data file name WITHOUT the extension, that is determined by the
        dct_put(dct, ADO_CFG_UNIQUEID, None)
    """
    #create a standard active object, then load h5 file and populate the active object dict 
    active_data_obj = ActiveDataObj()
    active_data_obj.reset_data_dct()
    
    dct = active_data_obj.get_data_dct() 
    nf = None
    try:
        nf = h5py.File(filename,  "r")
        
        fname = nf.attrs[nxkd.NXD_FILE_NAME]
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(data_dir is None):
            return
        
        dct_put(dct, nxkd.NXD_HDF_VER, nf.attrs[nxkd.NXD_HDF_VER])
        dct_put(dct, nxkd.NXD_NX_VER, nf.attrs[nxkd.NXD_NX_VER])
        
        dct_put(dct, 'TIME', nf.attrs[nxkd.NXD_FILE_TIME])
        #now for each entry where its NXclass attr is of type NXentry, create a new spatial region dict entry
        entries = {}
        for ekey in list(nf.keys()):
            if('NX_class' in list(nf[ekey].attrs.keys())):
                if(nf[ekey].attrs['NX_class'] == 'NXentry'):
                    #walk the entry 
                    #ADO_CFG_ROI
                    #each entry is returned from get_NXstxm_entry() as a 
                    # dift of ['CFG', nxkd.NXD_DATA]
                    entries[ekey] = get_NXstxm_entry(nf[ekey], only_roi_and_data)
                    #dct_put(dct, '%s' % ekey, entries[ekey])
                    
                else:
                    print('[%s] is not of type NXentry' % ekey)
        
        dct_put(dct, 'DATA_DIR', data_dir)
        dct_put(dct, 'DATA_FILE_NAME', fprefix)
        dct_put(dct, 'ENTRIES', entries)
        
        nf.close()
        
        if(only_roi_and_data):
            ekeys = list(entries.keys())
            #just return the first one for now
            return(entries[ekeys[0]])
        else:
            return(dct)
    
    except:
        if(nf is not None):
            nf.close()
        _logger.info('load_all_entries_from_NXstxm_file: opening file failed [%s]' % filename)
        return(None)     



def get_entry_names(nf):
    l = get_names(nf, nxkd.NXD_ENTRY)
    return(l)        

def get_counter_names(nf):
    l = get_names(nf, 'counter')
    return(l) 

def get_names(nf, name):
    lst = []
    for k in list(nf.keys()):
        if(k.find(name) > -1):
            lst.append(k)
    return(lst)        

def run_nexus_class_test(_class=None):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    bc = readin_base_classes()
    ac = readin_application_classes(desired_class='NXstxm')
    (stxm_doc, stxm_flds, stxm_grps) = ac['NXstxm']
    #print 'BASE CLASSES'
    #pp.pprint(bc)
    
    print('APPLICATION CLASSES')
    pp.pprint(ac)
     
     
    #create_NXstxm_file("positioner.hdf5")
    return(bc, ac)
 
def dump_xml_structure():
    dom = md.parse(r'C:\controls\nexus-definitions-development\dist\applications\NXstxm.nxdl.xml')
    root = dom.documentElement
    print_node(root)

def test_nexus_save(ado_obj, fname):
        from cls.scanning.dataRecorder import STXMDataIo
#         dct_put(self.data_dct,'TIME', make_timestamp_now())
#         dct_put(self.data_dct,'POSITIONERS', self.take_positioner_snapshot(devices['POSITIONERS']))
#         dct_put(self.data_dct,'DETECTORS', self.take_detectors_snapshot(devices['DETECTORS']))
#         dct_put(self.data_dct,'PVS', self.take_pvs_snapshot(devices['PVS']))
#         #_logger.info('DONE grabbing devices snapshot')
#         dct_put(self.data_dct, ADO_CFG_SCAN_TYPE, self.scan_type)    
#         dct_put(self.data_dct, ADO_CFG_CUR_EV_IDX, _ev_idx)
#         dct_put(self.data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, _spatial_roi_idx)
#         dct_put(self.data_dct, ADO_CFG_CUR_SAMPLE_POS, sample_pos)
#         dct_put(self.data_dct, ADO_CFG_CUR_SEQ_NUM, 0)
#         dct_put(self.data_dct, ADO_CFG_DATA_DIR, datadir)
#         dct_put(self.data_dct, ADO_CFG_DATA_FILE_NAME, fname)
#         dct_put(self.data_dct, ADO_CFG_UNIQUEID, unique_id)
#         dct_put(self.data_dct, ADO_CFG_X, self.x_roi)
#         dct_put(self.data_dct, ADO_CFG_Y, self.y_roi)
#         dct_put(self.data_dct, ADO_CFG_Z, self.z_roi)
#         dct_put(self.data_dct, ADO_CFG_EV_ROIS, self.e_rois)
#         dct_put(self.data_dct, ADO_DATA_POINTS, self.data )
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        dct_put(ado_obj, ADO_CFG_DATA_DIR, data_dir)
        dct_put(ado_obj, ADO_CFG_DATA_FILE_NAME, fprefix)
        #dct_put(ado_obj, ADO_DATA_POINTS, np.array(ado_obj[nxkd.NXD_DATA]['POINTS']))   
       
        data_io = STXMDataIo(data_dir, fprefix)
        data_io.save(ado_obj)
        
def test_saving_with_validation():
    json_fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/C160323001.json'
    hdf5_fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/gzip.hdf5'
    ado_obj = json.loads(file(json_fname).read())
    #test saving a file
    test_nexus_save(ado_obj, hdf5_fname)
    #now check its validity
    validate(['-f','%s'% hdf5_fname] )


def update_point_with_openclose(fname, entry, point, val, counter='counter0'):
    row, col = point
    nf = h5py.File(fname,  "a")
    nf.swmr_mode = True
    if(entry in list(nf.keys())):
        e_grp = nf[entry]
        if(counter in list(e_grp.keys())):
            data = e_grp[counter][nxkd.NXD_DATA][()]
            data[row][col] = val
        else:
            _logger.error('counter [%s] does not exist in entry [%s]' % (counter, entry))
    else:
        _logger.error('entry [%s] does not exist in file [%s]' % (entry, fname))    
    nf.close()

def update_data_with_openclose(fname, entry, data, counter='counter0'):
    nf = h5py.File(fname,  "r+")
    nf.swmr_mode = True
    nf[entry][counter][nxkd.NXD_DATA][()] = data
    nf.close()

def update_data_whileopen(nf, entry, data, counter='counter0'):
    nf[entry][counter][nxkd.NXD_DATA][()] = data
    nf.flush()

def get_data_whileopen(nf, entry, counter='counter0'):
    data = None
    if(entry in list(nf.keys())):
        if(counter in list(nf[entry].keys())):
            if(nxkd.NXD_DATA in list(nf[entry][counter].keys())):
                data = nf[entry][counter][nxkd.NXD_DATA][()]
    return(data)


    
def time_open_updateall_close(): 
    fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/testswmr.hdf5'
    arr = np.random.rand(250,250)
    start_time = time.clock()
    nf = h5py.File(fname,  "w+")
    nf.swmr_mode = True
    for i in range(200):
        update_data_whileopen(nf,'entry1458838195411', arr)
    # your code
    nf.close()
    elapsed_time = time.clock() - start_time
    print('time_open_updateall_close: Elapsed time for updating the data %d times is %.4f seconds' % (i, elapsed_time))


def time_trial_update_speed():
    fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/testupdate.hdf5'
    arr = np.random.rand(250,250)
    start_time = time.clock()
    
    for i in range(200):
        update_data_with_openclose(fname, 'entry1458838195411', arr)
       
    # your code
    elapsed_time = time.clock() - start_time
    
    print('time_trial_update_speed: Elapsed time for updating the data %d times is %.4f seconds' % (i, elapsed_time))

if __name__ == '__main__':
    import xml.dom.minidom as  md
    import time
    import datetime
    import json
    from bcm.utils.xim2array import loadXim2Array
    import pprint
    import hdf5storage
    #from datetime import time, tzinfo, datetime, timedelta
    from sm.stxm_control.stxm_utils.nexus.nxstxm_validate.nxstxm_validate import validate
    class CST(datetime.tzinfo):
        def utcoffset(self, dt):
            return(datetime.timedelta(hours=-6))
        def dst(self, dt):
            return(datetime.timedelta(0))
        def tzname(self,dt):
            return("Saskatchewan Canada")
    
    test_saving_with_validation()
    #time_trial_update_speed()
    #time_open_updateall_close()
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
    #create_standard_NXstxm_file(fname, scan_type, data_dct={'ID':None}, intermediate_file=False)
    #create_standard_NXstxm_file(hdf5_fname, scan_types.SAMPLE_IMAGE, data_dct=ado_obj, intermediate_file=False)
    #dct_put(data_dct, ADO_CFG_DATA_DIR, r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/')
    #dct_put(data_dct, ADO_CFG_DATA_FILE_NAME, r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/C160519030.hdf5')
    #spatial_roi_id = dct_get(data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX)
    #create_NXstxm_file(r'C:/controls/py2.7/Beamlines/sm/data/guest/May19/C160519099.hdf5', scan_types.SAMPLE_LINE_SPECTRUM, data_dct=data_dct, intermediate_file=False)
    
    
    #try_this()
    #walk_xml()
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
    
    
    
    
    #ac = parse_nxdef()
    
    #print 'Base Classes'
    #for k in dct.keys():
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
    #'12:10:30 Europe/Prague'
    #'The {} is {:%H:%M}.'.format("time", t)
    #'The time is 12:10.'
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
#     #create_NXstxm_file('sample_point_spectra.hdf5', dtype[0], data_dct)
#     #create_NXstxm_file('sample_line_spectra.hdf5', dtype[1], data_dct)
#     #epnts = data_dct['ScanDefinition']['StackAxis']['EV']['NumPoints']
#     #xpnts = data_dct['ScanDefinition']['Regions'][1]['PAxis']['NumPoints']
#     #ypnts = data_dct['ScanDefinition']['Regions'][1]['QAxis']['NumPoints']
#     
#     data_dct['Time'] = make_timestamp_now()
#     create_NXstxm_file('sample_image.hdf5', dtype[2], data_dct)
#     
#     
#     
    
    #create_NXstxm_file('sample_image_stack.hdf5', dtype[3], data_dct)
    #create_NXstxm_file('sample_focus.hdf5', dtype[4], data_dct)
    #create_NXstxm_file('osa_image.hdf5', dtype[5], data_dct)
    #create_NXstxm_file('osa_focus.hdf5', dtype[6], data_dct)
    #create_NXstxm_file('detector_image.hdf5', dtype[7], data_dct)

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
