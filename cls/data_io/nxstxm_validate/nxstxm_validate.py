#!python
'''
Created on Jun 29, 2016

# 
#  * Copyright 2016 Canadian Light Source Inc. (CLSI) All rights reserved.
# 
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee or royalty is hereby granted,
#  provided that the full text of this NOTICE appears on ALL copies of the
#  software and documentation or portions thereof, including modifications,
#  that you make.
# 
#  THIS SOFTWARE IS PROVIDED BY CLSI "AS IS" AND CLSI EXPRESSLY DISCLAIMS
#  LIABILITY FOR ANY AND ALL DAMAGES AND LOSSES (WHETHER DIRECT, INCIDENTAL,
#   CONSEQUENTIAL OR OTHERWISE) ARISING FROM OR IN ANY WAY RELATED TO THE
#  USE OF SOFTWARE, INCLUDING, WITHOUT LIMITATION, DAMAGES TO ANY COMPUTER,
#  SOFTWARE OR DATA ARISING OR RESULTING FROM USE OF THIS SOFTWARE.
#  BY WAY OF EXAMPLE, BUT NOT LIMITATION, CLSI MAKE NO REPRESENTATIONS OR
#  WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR
#  THAT THE USE OF THE SOFTWARE  OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD
#  PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS. CLSI WILL BEAR NO
#  LIABILITY FOR ANY USE OF THIS SOFTWARE OR DOCUMENTATION.
# 
#  Title to copyright in this software and any associated documentation will
#  at all times remain with CLSI. The reproduction of CLSI and its trademarks
# is strictly prohibited, except with the prior written consent of CLSI.
# 
# * -----------------------------------------------------------------------------
# 

@author: Russ Berg
'''


import xml.etree.ElementTree as ET
import xmltodict
import glob
import os
import re
import sys

import numpy as np
import h5py
import pkg_resources


def dct_merge(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

def dirlist(path, suffix, fname = None, remove_suffix=False):
    """
    Takes a path and a file suffix as a filter and returns a list of the files in 
    that path that match the filter
    ex: alist = dirlist(r'C:\pythonxy\workspace\PyQtStxmViewer\src\data\101207\A101207022', '.xim')
    """
    ret = []
    containsStr = suffix
    dirList=os.listdir(path)

    for f in dirList:
        #if(f.find(containsStr) > -1):
        #get the last 4 characters of filename as they are the file extension
        extension = f[-(len(suffix)):]
        if(suffix == extension):
            if(remove_suffix):
                f = f.replace(extension,'')
            if(fname):
                if(f.find(fname) > -1):
                    ret.append(f)
            else:
                ret.append(f)
                
    return ret

def get_file_path_as_parts(fname):
    """ fname is a python string of the full path to a data file, 
    then return the data_dir, file prefix and file suffix
    """
    fnameidx1 = fname.rfind('\\') + 1
    if(fnameidx1 == 0):
        fnameidx1 = fname.rfind('/') + 1
    fnameidx2 = fname.rfind('.')
    data_dir = fname[0 : fnameidx1]
    fprefix = fname[fnameidx1 : fnameidx2]
    fsuffix = fname[fnameidx2 :]
    return(data_dir, fprefix, fsuffix)

def readin_base_classes(desired_class=None):
    clss = get_classes('base_classes', desired_class)
    return(clss[desired_class])

def readin_application_classes(desired_class=None):
    clss = get_classes('applications', desired_class)
    return(clss[desired_class])


def readin_contributed_definition_classes(desired_class=None):
    clss = get_classes('contributed_definitions', desired_class)
    return(clss)

def get_classes(class_dir, desired_class=None):
    base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/%s'%class_dir)
    nxdl_files = map(os.path.basename, glob.glob(os.path.join(base_class_path,'*.nxdl.xml')))
    pattern = re.compile(r'[\t\n ]+')
    nxclasses = {}
    
    if(desired_class != None):
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
            name = dtype = units = nxstxm_nxdl = ''
            enumerations = []
            if child.tag.endswith('nxstxm_nxdl'):
                try:
                    class_doc = re.sub(pattern, ' ', child.text).strip()
                except TypeError:
                    pass
            if child.tag.endswith('field'):
                try:
                    if(len(child.attrib) > 1):
                        name = child.attrib['name']
                        dtype = child.attrib['type']
                        units = child.attrib['units']
                    else:
                        name = child.attrib['name']    
                except KeyError:
                    pass
                for element in child:
                    if element.tag.endswith('nxstxm_nxdl'):
                        try:
                            nxstxm_nxdl = re.sub(pattern, ' ', element.text).strip()
                        except TypeError:
                            pass
                    
                    if element.tag.endswith('enumeration'):
                        #for e_ch in list(element.getchildren()):
                        for e_ch in list(element):
                            try:
                                k = e_ch.attrib.keys()[0]
                                enumerations.append(e_ch.attrib[k]) 
                            except TypeError:
                                pass    
                #class_fields[name] = (dtype, units, nxstxm_nxdl)
                class_fields[name] = {'type':dtype, 'units':units, 'nxstxm_nxdl':nxstxm_nxdl, 'enumerations':enumerations}
            
            elif(child.tag.endswith('group') and (child.attrib['type'] == 'NXentry')):
                gtype = child.attrib['type'] 
                class_groups[gtype] = get_group(gtype, child) 
            
            elif child.tag.endswith('group'):
                #
                gdoc = ''
                try:
                    dtype = child.attrib['type']
                    if(dtype.find('NXentry') > -1):
                        name = dtype
                    else:
                        name = child.attrib['name']    
                    
                except KeyError:
                    pass
                
                for element in child:
                    if('type' in element.attrib.keys()):
                        etype = element.attrib['type']
                    else:
                        etype = dtype
                    if element.tag.endswith('group'):
                        class_groups[etype] = get_group(etype, element)
                        

                    if element.tag.endswith('nxstxm_nxdl'):
                        try:
                            gdoc = re.sub(pattern, ' ', element.text).strip()
                        except TypeError:
                            pass
                    if element.tag.endswith('field'):
                        fdoc = ''
                        for el in element:
                            if el.tag.endswith('nxstxm_nxdl'):
                                try:
                                    fdoc = re.sub(pattern, ' ', el.text).strip()
                                except TypeError:
                                    pass
                        try:
                            fname = ''
                            fdtype = ''
                            funits = ''
                            if('name' in element.attrib.keys()):
                                fname = element.attrib['name']
                            if('type' in element.attrib.keys()):
                                fdtype = element.attrib['type']
                            if('units' in element.attrib.keys()):
                                funits = element.attrib['units']
                            group_fields[fname] = {'name':fname, 'type':fdtype, 'units':funits, 'nxstxm_nxdl': fdoc}
                            
                        except KeyError:
                            pass
                        
                class_groups[name] = {'name':name, 'nxstxm_nxdl': gdoc, 'type':dtype, 'fields':group_fields}
            
            nxclasses[class_name] = {'nxstxm_nxdl':class_doc, 'fields':class_fields, 'groups': class_groups}
            group_fields = {}
    return(nxclasses)

def get_fields(field):
    
    fields = {}
    for k in field.attrib.keys():
        fields[k] = field.attrib[k] 
    return(fields)

def get_field(field):
    
    fields = {}
    k = list(field.attrib.keys())[0]
    fields[k] = field.attrib[k] 
    return(k, fields)

def get_group(class_name, root_element):
    pattern = re.compile(r'[\t\n ]+')
    nxclasses = {}
    class_doc = ''
    class_groups = {}
    class_fields = {}
    group_fields = {}
    fields = {}
    #walk the group looking for fields and groups
    #when a group is found call this again recursively
    for child in root_element:
        name = units = nxstxm_nxdl = ''
        dtype = class_name
         
        #is there a nxstxm_nxdl section?
        if child.tag.endswith('nxstxm_nxdl'):
            try:
                class_doc = re.sub(pattern, ' ', child.text).strip()
            except TypeError:
                pass
        group_fields[class_name] = {}
        group_fields[class_name]['nxstxm_nxdl'] = class_doc    
         
         
        #now check for fields and groups
        if child.tag.endswith('field'):
            fld_name, fld_dct = get_field(child)
            group_fields[fld_name] = fld_dct
 
        elif child.tag.endswith('group'):
            if(len(list(child)) > 0):
                dtype = child.attrib['type']
                if('name' in child.attrib.keys()):
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
                if element.tag.endswith('nxstxm_nxdl'):
                    try:
                        nxstxm_nxdl = re.sub(pattern, ' ', element.text).strip()
                    except TypeError:
                        pass
                if child.tag.endswith('field'):
                    group_fields[class_name] = get_fields(child)
                 
                if child.tag.endswith('group'):
                    group_fields[name] = get_group(name, child)        
            class_groups[dtype] = (nxstxm_nxdl, group_fields)
             
         
        #nxclasses[dtype] = (class_doc, class_fields, class_groups)
        nxclasses[dtype] = group_fields
    return(group_fields)
 

def get_entry_names(nf):
    l = get_names(nf, 'entry')
    return(l)        

def get_counter_names(nf):
    l = get_names(nf, 'ounter')
    return(l) 

def get_names(nf, name):
    lst = []
    for k in nf.keys():
        if(k.find(name) > -1):
            lst.append(k)
    return(lst)        

def is_entry_nx_type(entry, typ='NXstxm'):
    ''' this funtion contains a check to see if the entry type that has been stored was done using
    the string or numpy array, I think this should be a string by the standard
    '''
    ret = False 
    if(isinstance(entry['definition'][()], str)):
        if(entry['definition'][()] == typ):
            ret = True
    elif(isinstance(entry['definition'][()], np.ndarray)):
        if(entry['definition'][()][0] == typ):
            ret = True
             
    return(ret)
            

def print_check_warning(entry_str, msg):
    num_tabs = 1
    tprint(num_tabs+1,'Warning: in entry %s: %s' %(entry_str, msg) )
    
def print_check_error(entry_str, msg):
    num_tabs = 1
    tprint(num_tabs+1,'ERROR in entry %s: %s' %(entry_str, msg) )

def check_for_entry(nf, entry_str):
    ret = False
    if(hasattr(nf[entry_str], 'attrs')):
        if('NX_class' in nf[entry_str].attrs.keys()):
            if(nf[entry_str].attrs['NX_class'] == 'NXentry'):
                ret = True
    return(ret)
                
        
def check_grp_and_nxclass(nxgrp, grp_str, nxclass_str):
    res = False
    inlist, k = str_in_lst(grp_str, nxgrp.keys())
    if(inlist):
        res = check_for_nxclass(nxgrp[k], nxclass_str)
    return(res)    
                    
def check_for_nxclass(nxgrp, nxclass_str):
    ret = False
    if(hasattr(nxgrp, 'attrs')):
        if('NX_class' in nxgrp.attrs.keys()):
            if(nxgrp.attrs['NX_class'] == nxclass_str):
                ret = True
    return(ret)    

def str_in_lst(s, lst):
    ret = False
    for l in lst:
        if(equals_ignore_case(s, l)):
            ret = True
            break
    return(ret, l)

def equals_ignore_case(str1, str2):
    import re
    return (re.match(re.escape(str1) + r'\Z', str2, re.I) is not None)

def lst_as_lowercase(lst):
    l2 = []
    for l in lst:
        l2.append(l.lower())
    return(l2)

def dct_keys_as_lowercase(d):
    result = {}
    for key, value in d.items():
        lower_key = key.lower()
        result[lower_key] = result.get(lower_key, 0) + value
    return result


def tprint(num_tabs, msg):
    s = ''
    for i in range(num_tabs):
        s += '\t'
    s+= msg
    print(s)

def get_NXstxm_NXentry_fieldnames(fld_lst):
    ''' take a list of field dicts and return a dict that is key'd by the _name'''
    dct = {}
    if(not isinstance(fld_lst, list)):
        fld_lst = [ fld_lst ]
        
    for fld in fld_lst:
        if('@name' in fld.keys()):
            if('@type' in fld.keys()):
                dct[fld['@name']] = fld['@type']
            else:
                #assume it is a string
                dct[fld['@name']] = 'NX_CHAR'
    return(dct)

def get_fieldnames_from_dict(fld_dct):
    ''' take a dict of fields and return a dict that is key'd by the _name'''
    dct = {}
    for k in fld_dct.keys():
        if('NX_class' in fld_dct[k].attrs.keys()):
            dct[k] = fld_dct[k].attrs['NX_class']
    return(dct)


def get_NXclass_attr_and_types(fld_lst):
    ''' take a list of field dicts and return a dict that is key'd by the _name'''
    dct = {}
    for fld in fld_lst:
        if('@name' in fld.keys()):
            if('@type' in fld.keys()):
                dct[fld['@name']] = fld['@type']
            else:
                #assume it is a string
                dct[fld['@name']] = 'NX_CHAR'
    return(dct)


def get_group_NXclassnames(grp_lst):
    l = []
    for fld in grp_lst:
        if('@type' in fld.keys()):
            l.append(fld['@type'])
    return(l)

def get_nxclass_of_group(grp):
    if('NX_class' in grp.attrs.keys()):
        nx_class = grp.attrs['NX_class']
        if(nx_class.find('_') > -1):
            #this is a NX type and not a class name so ignore
            return(None)
        
        return(grp.attrs['NX_class'])
    else:
        return(None)


def check_nxentry_group(nf, entry_str, nxstxm_nxdl):
    """
    <group type="NXentry">
        <field name="title"/>
        <field name="start_time" type="NX_DATE_TIME"/>
        <field name="end_time" type="NX_DATE_TIME"/>
        <field name="definition" type="NX_CHAR" minOccurs="1" maxOccurs="1">
        <group type="NXinstrument" minOccurs="1" maxOccurs="1"> 
        <group type="NXsample">
        <group type="NXdata">
        <group type="NXmonitor" name="control" minOccurs="0" maxOccurs="1">
    
    """
    num_tabs = 1
    res = True
    
    tprint(num_tabs, '### checking for nxentry group called <%s>:' % entry_str)
    if(not check_grp_and_nxclass(nf, entry_str, 'NXentry')):
        tprint(num_tabs, 'NXstxm file has no or non-standard NXentry group named [%s]' % entry_str)
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXentry')
                
    #check keys of collection group
    fld_dct = get_NXstxm_NXentry_fieldnames(nxstxm_nxdl['definition']['group']['field'])
    tprint(num_tabs+2, '### checking <%s> fields:' % entry_str)
    if(not check_fields_of_nxclass(nf[entry_str], nexus_grp_dct=fld_dct)):
        tprint(num_tabs+3, 'NXentry group does not contain correct set of fields')
        res = False
    
    nxgrp_class_lst = get_group_NXclassnames(nxstxm_nxdl['definition']['group']['group'])
    tprint(num_tabs+2, '### checking <%s> groups:' % entry_str)
    #if(not check_fields_of_nxclass(nf[entry_str], fld_lst=fld_lst)):
    #print nf[entry_str].keys()
    if(not check_NXclassnames_of_nxclass(nf[entry_str], nxgrp_class_lst=nxgrp_class_lst)):
        tprint(num_tabs+3, 'NXentry group does not contain correct set of fields')
        res = False    
        
    return(res)    

def check_nxcollection_group(nf):
    """
    This Group is apparently optional
    """
    num_tabs = 1
    res = True
    tprint(num_tabs, '### checking for NXcollection group')
    col_nam, col_grp = get_nx_group_from_entry(nf, 'NXcollection')
    if(col_grp is None):
        tprint(num_tabs, 'an NXcollection group does not exist in the entry')
        return
    
    tprint(num_tabs, 'found NXcollection group called <%s>' % col_nam)
    
    if(not check_grp_and_nxclass(nf, col_nam, 'NXcollection')):
        tprint(num_tabs, 'NXstxm file has no or non-standard NXcollection group named [collection]')
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXcollection')    

    #check keys of collection group
    tprint(num_tabs+2, '### checking <collection> fields:')
    if(not check_fields_of_nxclass(nf['collection'], nexus_grp_dct={'scan_request': 'NXscanDefinition'})):
        tprint(num_tabs+3, 'NXcollection group does not contain correct set of fields')
        res = False
    
    return(res)

def get_control_axes_indices_names(attrs, remove_indices=False):
    lst = []
    for f in attrs.keys():
        if(f.find('_indices') > -1):
            if(remove_indices):
                lst.append(f.replace('_indices',''))
            else:
                lst.append(f)
    return(lst)
    

def check_nxcontrol_group(nf, nxstxm_nxdl=None):
    """
        <group type="NXmonitor" name="control" minOccurs="0" maxOccurs="1">
            <field name="data" type="NX_FLOAT">
              <doc> Values to use to normalise for time-variations in photon flux. Typically, the synchrotron storage ring
              electron beam current is used as a proxy for the X-ray beam intensity. Array must have same shape as the
              NXdata groups.</doc>
            </field>
        </group>
    </group>
    """
    num_tabs = 1
    res = True
    
    #cntrl_grp = nxstxm_nxdl['definition']['group']['group'][3]
    cntrl_nam, cntrl_grp = get_nx_group_from_entry(nf, 'NXmonitor')
    if(cntrl_grp is None):
        tprint(num_tabs, 'an NXmonitor group does not exist in the entry')
        return
    
    tprint(num_tabs, '### checking OPTIONAL NXmonitor group called <%s>:' % cntrl_nam)
    if(not check_grp_and_nxclass(nf, cntrl_nam, 'NXmonitor')):
        tprint(num_tabs, 'NXstxm file has no or non-standard NXmonitor group named [%s]' % cntrl_nam )
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXmonitor')    
    #check attrs of NXcollection
    fld_lst = get_control_axes_indices_names(nf[cntrl_nam].attrs) + ['axes', 'signal']
    tprint(num_tabs+2, '### checking <%s> attributes:' % cntrl_nam)
    #attr_lst contains the minnimum attributes required
    if(not check_attrs_of_nxclass(nf[cntrl_nam], attr_lst=fld_lst)):
        tprint(num_tabs+3, 'NXmonitor group does not contain correct set of attrs')
        res = False
    #check keys of collection group
    #fld_dct = get_NXstxm_NXentry_fieldnames(cntrl_grp)
    fld_lst = get_control_axes_indices_names(nf[cntrl_nam].attrs, remove_indices=True) + ['data', 'energy']
    tprint(num_tabs+2, '### checking <%s> fields:' % cntrl_nam)
    #fld_dct = get_NXstxm_NXentry_fieldnames(cntrl_grp)
    fld_dct = get_fieldnames_from_dict(cntrl_grp)
    #if(not check_fields_of_nxclass_list(nf[cntrl_nam], nexus_grp_lst=fld_lst)):
    if(not check_fields_of_nxclass(nf[cntrl_nam], nexus_grp_dct=fld_dct)):
    #if(not check_fields_of_nxclass(nf['control'], nexus_grp_dct=fld_dct)):
        tprint(num_tabs+3, 'NXmonitor group does not contain correct set of fields')
        res = False
    
    return(res)

def get_enumerations(item_lst):
    dct = {}
    x = 0
    for i in item_lst:
        dct[i['@value']] = x
        x += 1
    return(dct)     

def check_nxdata_group(nf, cntr_lst=[], nxstxm_nxdl=None):
    """
        <group type="NXdata">
            <field name="stxm_scan_type" minOccurs="1" maxOccurs="1">
                <doc> Label for typical scan types as a convenience for humans. 
                Each label corresponds to a specific set of axes being scanned 
                to produce a data array of shape:
                
                * sample point spectrum: (photon_energy,)
                * sample line spectrum: (photon_energy, sample_y/sample_x)
                * sample image: (sample_y, sample_x)
                * sample image stack: (photon_energy, sample_y, sample_x)
                * sample focus: (zoneplate_z, sample_y/sample_x)
                * osa image: (osa_y, osa_x)
                * osa focus: (zoneplate_z, osa_y/osa_x)
                * detector image: (detector_y, detector_x)
                
                The "generic scan" string is to be used when none of the 
                other choices are appropriate.
                </doc>
                <enumeration>
                    <item value="sample point spectrum"/>
                    <item value="sample line spectrum"/>
                    <item value="sample image"/>
                    <item value="sample image stack"/>
                    <item value="sample focus"/>
                    <item value="osa image"/>
                    <item value="osa focus"/>
                    <item value="detector image"/>
                    <item value="generic scan"/>
                </enumeration>
            </field>
            <field name="data" type="NX_NUMBER" signal="1">
              <doc> Detectors that provide more than one value per scan point should be summarised
              to a single value per scan point for this array in order to simplify plotting.
              
              Note that 'Line scans' and focus type scans measure along one spatial dimension
              but are not restricted to being parallel to the X or Y axes. Such scans 
              should therefore use a single dimension for the positions along the spatial
              line. The 'sample_x' and 'sample_y' fields should then contain lists of the
              x- and y-positions and should both have the 'axes' attribute pointing to the same dimension.</doc>
            </field>
            <field name="energy" type="NX_FLOAT" minOccurs="1" maxOccurs="1">
              <doc> List of photon energies of the X-ray beam. If scanned through multiple values,
              then an 'axes' attribute will be required to link the field to the appropriate data array dimension.</doc>
              <dimensions rank="1">
                <dim index="1" value="NumE" />
              </dimensions>
            </field>
            <field name="sample_y" type="NX_FLOAT" minOccurs="1" maxOccurs="1">
              <doc> List of Y positions on the sample. If scanned through multiple values,
              then an 'axes' attribute will be required to link the field to the appropriate data array dimension.</doc>
              <dimensions rank="1">
                <dim index="1" value="NumY" />
              </dimensions>
            </field>
            <field name="sample_x" type="NX_FLOAT" minOccurs="1" maxOccurs="1">
              <doc> List of X positions on the sample. If scanned through multiple values,
              then an 'axes' attribute will be required to link the field to the appropriate data array dimension.</doc>
              <dimensions rank="1">
                <dim index="1" value="NumX" />
              </dimensions>
            </field>
        </group>
    """
    num_tabs = 1
    res = True
    
    #this is hardcoded for now
    data_grp = nxstxm_nxdl['definition']['group']['group'][2]
    stxm_sc_type = data_grp['field'][0]
    nxstxm_scan_type_lst = get_enumerations(stxm_sc_type['enumeration']['item'])
    ###
    for cntr in cntr_lst:
        tprint(num_tabs, '### checking for NXdata group called <%s>:' % cntr)
        if(not check_grp_and_nxclass(nf, cntr, 'NXdata')):
            tprint(num_tabs, 'NXstxm file has no or non-standard NXdata group named [%s]' % cntr)
            res = False
            break
        else:
            tprint(num_tabs+1, '> it exists and type=NXdata')
        
        #check attrs of NXcollection
        tprint(num_tabs+2, '### checking <%s> attributes:' % cntr)
        fld_lst = get_control_axes_indices_names(nf[cntr].attrs) + ['axes', 'signal']
        #if(not check_attrs_of_nxclass(nxentry[cntr], attr_lst=['NX_class', 'axes', 'sample_x_indices', 'sample_y_indices', 'signal'])):
        if(not check_attrs_of_nxclass(nf[cntr], attr_lst=fld_lst)):
            tprint(num_tabs+3, 'NXdata group does not contain correct set of attrs')
            res = False
        #check keys of collection group
        
        tprint(num_tabs+2, '### checking <%s> fields:' % cntr)
        cntr_grp = nxstxm_nxdl['definition']['group']['group'][2]
        fld_dct = get_NXstxm_NXentry_fieldnames(cntr_grp['field'])
        #fld_dct = dct_merge(_dct, {'source': 'NXsource'})
        #fld_lst = get_control_axes_names(nf[cntr].attrs, remove_indices=True) + ['count_time', 'data', 'energy','stxm_scan_type']
        #if(not check_fields_of_nxclass_list(nxentry[cntr], nexus_grp_lst=lst_as_lowercase(['count_time', 'data', 'energy','sample_x', 'sample_y','stxm_scan_type']))):
        #if(not check_fields_of_nxclass_list(nxentry[cntr], nexus_grp_lst=fld_lst)):
        if(not check_fields_of_nxclass(nf[cntr], nexus_grp_dct=fld_dct)):
            tprint(num_tabs+3, 'NXdata group does not contain correct set of fields')
            res = False
        else:
            #check that the stxm_scan_type is correct
            tprint(num_tabs+2, '### checking <%s> stxm_scan_type:' % cntr)
            nf_stxm_scan_type = nf[cntr]['stxm_scan_type'][()]
            if(isinstance(nf_stxm_scan_type, str)):
                nf_stxm_scan_type = nf_stxm_scan_type.lower()
                if(str_in_lst(nf_stxm_scan_type, nxstxm_scan_type_lst)):
                    tprint(num_tabs+3, 'stxm_scan_type = <%s> is a valid type' % nf_stxm_scan_type)
                else:
                    tprint(num_tabs+3, 'Error: stxm_scan_type = <%s> is an invalid stxm_scan type' % nf_stxm_scan_type)    
            else:
                tprint(num_tabs+3, 'Error: stxm_scan_type is not of type NX_CHAR')        
                
        
    return(res)

def check_nxinstrument_group(nf, cntr_lst=[], nxstxm_nxdl=None):
    """
        <group type="NXinstrument" minOccurs="1" maxOccurs="1"> 
            <group type="NXsource" minOccurs="1" maxOccurs="1">
                <field name="type" minOccurs="1" maxOccurs="1"/>
                <field name="name" minOccurs="1" maxOccurs="1"/>
                <field name="probe" minOccurs="1" maxOccurs="1"/>
            </group>
            <group type="NXmonochromator" name="monochromator" minOccurs="1" maxOccurs="1">
              <field name="energy" minOccurs="1" maxOccurs="1">
                <dimensions rank="1">
                  <dim index="1" value="NumP" />
                </dimensions>
              </field>
            </group>
            <group type="NXdetector" minOccurs="1">
                <field name="data" type="NX_NUMBER">
                  <dimensions>
                    <doc> Detector data should be presented with the first dimension corresponding to the
                    scan point and subsequent dimensions corresponding to the output of the detector.
                    Detectors that provide more than one value per scan point should have
                    a data array of rank 1+d, where d is the dimensions of the array provided per
                    scan point. For example, an area detector should have an NXdetector data array
                    of 3 dimensions, with the first being the set of scan points and the latter 
                    two being the x- and y- extent of the detector </doc>
                    <dim index="1" value="NumP" />
                  </dimensions>
                </field>
            </group>
            <group type="NXdetector" name="sample_x" minOccurs="0" maxOccurs="1">
                <doc> Measurements of the sample position from the x-axis interferometer.</doc>
                <field name="data" type="NX_FLOAT">
                  <dimensions rank="1">
                    <dim index="1" value="NumP" />
                  </dimensions>
                </field>
            </group>
            <group type="NXdetector" name="sample_y" minOccurs="0" maxOccurs="1">
                <doc> Measurements of the sample position from the y-axis interferometer.</doc>
                <field name="data" type="NX_FLOAT">
                  <dimensions rank="1">
                    <dim index="1" value="NumP" />
                  </dimensions>
                </field>
            </group>
            <group type="NXdetector" name="sample_z" minOccurs="0" maxOccurs="1">
                <doc> Measurements of the sample position from the z-axis interferometer.</doc>
                <field name="data" type="NX_FLOAT">
                  <dimensions rank="1">
                    <dim index="1" value="NumP" />
                  </dimensions>
                </field>
            </group>
        </group>

    """
    num_tabs = 1
    res = True
    
    optional = {'sample_x':'NXdetector', 'sample_y':'NXdetector', 'sample_z':'NXdetector'} 
    
    inst_grp = nxstxm_nxdl['definition']['group']['group'][0]
    
    tprint(num_tabs, '### checking for NXinstrument group called <instrument>:')
    if(not check_grp_and_nxclass(nf, 'instrument', 'NXinstrument')):
        tprint(num_tabs, ' !! NXstxm file has no or non-standard NXinstrument group named [instrument]')
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXinstrument')    

    #check keys of collection group
    tprint(num_tabs+2, '### checking <instrument> fields:')
    _dct = get_NXstxm_NXentry_fieldnames(inst_grp['group'])
    fld_dct = dct_merge(_dct, {'source': 'NXsource'})
    
    if(not check_fields_of_nxclass(nf['instrument'], nexus_grp_dct=fld_dct, optional_flds=optional)):
        tprint(num_tabs+3, ' !! NXmonitor group does not contain correct set of fields')
        res = False
        #return(res)
    
    #now finally check the <source> group of the NXinstrument group
    if(not check_nxsource_group(nf['instrument'], nxstxm_nxdl=nxstxm_nxdl)):
        tprint(num_tabs+2, ' !! NXsource group does not contain correct set of fields')
        res = False
        
    return(res)



def check_nxsample_group(nf, nxstxm_nxdl=None):
    """
        <group type="NXsample">
            <field name="rotation_angle" type="NX_FLOAT" />
        </group> 

    """
    num_tabs = 1
    res = True
    
    smpl_grp = nxstxm_nxdl['definition']['group']['group'][1]
    
    tprint(num_tabs, '### checking for NXsample group called <sample>:')
    if(not check_grp_and_nxclass(nf, 'sample', 'NXsample')):
        tprint(num_tabs, 'NXstxm file has no or non-standard NXsample group named [collection]')
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXsample')    
    #check keys of collection group
    tprint(num_tabs+2, '### checking <sample> fields:')
    fld_dct = get_NXstxm_NXentry_fieldnames(smpl_grp['field'])
    #if(not check_fields_of_nxclass_list(nf['sample'], nexus_grp_lst=lst_as_lowercase(['rotation_angle']))):
    if(not check_fields_of_nxclass(nf['sample'], nexus_grp_dct=fld_dct)):
        tprint(num_tabs+3, 'NXsample group does not contain correct set of fields')
        res = False
    
    return(res)


def check_nxsource_group(nf, nxstxm_nxdl=None):
    """
            <group type="NXsource" minOccurs="1" maxOccurs="1">
                <field name="type" minOccurs="1" maxOccurs="1"/>
                <field name="name" minOccurs="1" maxOccurs="1"/>
                <field name="probe" minOccurs="1" maxOccurs="1"/>
            </group>
    
    """
    nxsource = readin_base_classes(desired_class='NXsource')
    nxstxm_stndrd = readin_application_classes(desired_class='NXstxm')
    
    inst_grp = nxstxm_nxdl['definition']['group']['group'][0]
    src_grp = inst_grp['group'][0]
    
    num_tabs = 2
    res = True
    tprint(num_tabs, '### checking for NXsource group called <source>:')
    if(not check_grp_and_nxclass(nf, 'source', 'NXsource')):
        tprint(num_tabs, 'NXstxm file has no or non-standard NXsample group named [collection]')
        res = False
        return(res)
    else:
        tprint(num_tabs+1, '> it exists and type=NXsource')    
    #check keys of collection group
    tprint(num_tabs+2, '### checking <source> fields:')
    #if(not check_fields_of_nxclass(nxentry['instrument'], nexus_grp_dct=fld_dct)):
    #    tabbed_print(num_tabs+3, ' !! NXmonitor group does not contain correct set of fields')
    #    res = False
    
    fld_dct = get_NXstxm_NXentry_fieldnames(src_grp['field'])
    #if(not check_fields_of_nxclass_list(nxgrp['source'], nexus_grp_lst=lst_as_lowercase(['type', 'name', 'probe']))):
    if(not check_fields_of_nxclass(nf['source'], nexus_grp_dct=fld_dct)):
        tprint(num_tabs+3, 'NXsource group does not contain correct set of fields')
        res = False
    
    return(res)

def check_attrs_of_nxclass(nxgrp, attr_lst=[]):
    num_tabs = 4
    ret = True
    if(hasattr(nxgrp, 'attrs')):
        for a in attr_lst:
            if a not in nxgrp.attrs.keys():
                tprint(num_tabs, 'ATTR[%s] > DOES NOT EXIST' % (a))
                ret = False
            else:    
                tprint(num_tabs, 'attr[%s] > it exists' % a)
    return(ret)
    
def check_fields_of_nxclass(nf, nexus_grp_dct={}, optional_flds={}):
    num_tabs = 4
    ret = True
    nf_keys = nf.keys()
    nexus_grp_lst = nexus_grp_dct.keys()
    nexus_grp_opt_lst = optional_flds.keys()
    for f in nexus_grp_lst:
        if f not in nf_keys:
            if(f in nexus_grp_opt_lst):
                tprint(num_tabs, 'field[%s] > DOES NOT EXIST but it is optional' % (f))
            else:
                tprint(num_tabs, 'FIELD[%s] > DOES NOT EXIST' % (f))
                ret = False
        else:    
            fld_typ = get_field_NX_class_type(nf[f])
            if(fld_typ == nexus_grp_dct[f]):
                tprint(num_tabs, 'field[%s] exists and type=%s is correct' % (f, fld_typ))
            else:
                tprint(num_tabs, 'field[%s] exists but type=%s is INCORRECT it should be %s' % (f, str(type(nf[f][()])), nexus_grp_dct[f]))  
                  
            #here check that the tiypes are also correct
              
    return(ret)

def check_fields_of_nxclass_list(nf, nexus_grp_lst=[]):
    num_tabs = 4
    ret = True
    nf_keys = nf.keys()
    for f in nexus_grp_lst:
        if f not in nf_keys:
            tprint(num_tabs, 'FIELD[%s] > DOES NOT EXIST' % (f))
            ret = False
        else:    
            tprint(num_tabs, 'field[%s] it exists' % (f))
              
    return(ret)

def get_nx_group_from_entry(nf, nx_grp_type):
    
    for grp in nf.keys():
        if('NX_class' in nf[grp].attrs.keys()):
            if(nf[grp].attrs['NX_class'] == nx_grp_type):
                return(grp, nf[grp])
    return('', {})     
    #smpl_grp = nxstxm_nxdl['definition']['group']['group'][1]

def get_field_NX_class_type(fld):
    if('NX_class' in fld.attrs.keys()):
        ftype = fld.attrs['NX_class']
        if(ftype == None):
            ftype = 'NX_CHAR'
    else:
        ftype = None        
    return(ftype)    

def check_NXclassnames_of_nxclass(nf, nxgrp_class_lst=[], optional_classes = ['NXcollection', 'NXmonitor']):
    num_tabs = 4
    ret = True
    nf_class_names = []
    for nfgrp_key in nf.keys():
        nm = get_nxclass_of_group(nf[nfgrp_key])
        if(nm):
            nf_class_names.append(nm)
    
    for nexus_cname in nf_class_names:        
        if nexus_cname not in nxgrp_class_lst:
        #if nexus_cname not in nf_class_names:
            if nexus_cname in optional_classes:
                tprint(num_tabs, 'NX_class[%s] > EXISTS but it is OPTIONAL' % (nexus_cname))
            else:    
                tprint(num_tabs, 'NX_class[%s] > DOES NOT EXIST' % (nexus_cname))
                ret = False
        else:    
            tprint(num_tabs, 'NX_class[%s] > it exists' % nexus_cname)    
    return(ret)

def check_stxm_file(stxm_file, nxstxm_nxdl):
    """
    This is the main funtion to call in order to run a validation for nxstxm on a file
    """
    #import pprint
    num_tabs = 1
    res = True
    nf = h5py.File(stxm_file,  "r")
    e_lst = get_entry_names(nf)
    
    print('\n\nValidating nxstxm file [%s]:' % stxm_file)
        
    for entry in e_lst:
        res = True
        if(not is_entry_nx_type(nf[entry], typ='NXstxm')):
            print_check_error(entry, 'entry[%s] is not an NXstxm type ' % entry)
            break
        
        #tabbed_print(num_tabs, 'entry[%s] is an NXstxm type ' % entry)
        if(not check_nxentry_group(nf, entry, nxstxm_nxdl)):
            print_check_error(entry, 'NXstxm file has non-standard NXentry group named [%s]' % entry)
            #break
        print('')
        nxentry = nf[entry]
        if(not check_nxcollection_group(nxentry)):
            print_check_warning(entry, 'NXstxm file has non-standard NXcollection group named [collection]')
            #res = False
            #break
            #the collection group is an optional group so dont calv
        
        print('')
        if(not check_nxcontrol_group(nxentry, nxstxm_nxdl=nxstxm_nxdl)):
            print_check_error(entry, 'NXstxm file has non-standard NXmonitor group')
            #break
            #the control group is an optional group so dont calv
        
        print('')
        c_lst = get_counter_names(nxentry)
        if(not check_nxdata_group(nxentry, c_lst, nxstxm_nxdl=nxstxm_nxdl)):
            print_check_error(entry, 'NXstxm file has non-standard NXdata group')
            res = False
            #break
                
        print('')    
        if(not check_nxinstrument_group(nxentry, cntr_lst=c_lst, nxstxm_nxdl=nxstxm_nxdl)):
            print_check_error(entry, 'NXstxm file has non-standard NXinstrument group named [instrument]')
            res = False
            #break
        
        print('')
        if(not check_nxsample_group(nxentry, nxstxm_nxdl=nxstxm_nxdl)):
            print_check_error(entry, 'NXstxm file has non-standard NXsample group named [sample]')
            res = False
            #break
            
    if(res):    
        print('File: %s contains a valid nxstxm structure' % stxm_file)
    else:
        print('FAIL! File: %s contains an invalid nxstxm structure' % stxm_file)
    nf.close()
    return(res)

#############################################################################################
#############################################################################################
#############################################################################################
# #  testing routines
#
# def test_one():
#     hdf5_fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/C160323001.hdf5'
#     check_stxm_file(hdf5_fname)
#
def check_dir_test(dir):
    hdf_files = dirlist(dir, 'hdf5', remove_suffix=False)
    for f in hdf_files:
        check_stxm_file(dir + f)

def get_NXstxm_nxdl():
    desired_class='NXstxm' 
    app_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
    nxdl_files = map(os.path.basename, glob.glob(os.path.join(app_class_path,'*.nxdl.xml')))
    if(desired_class != None):
        fname = desired_class + '.nxdl.xml'
        if(fname in nxdl_files):
            nxdl_file = [fname][0]
    fd = open(os.path.join(app_class_path, nxdl_file))
    nxstxm_nxdl = xmltodict.parse(fd.read())
    return(nxstxm_nxdl)


def validate_filesin_dir(dir):
    
    nxstxm_nxdl = get_NXstxm_nxdl()
    dir = dir.strip()
    if(os.path.isdir(dir)):
        files = dirlist(dir, 'hdf5')
        
        for f in files:
            check_stxm_file(dir + '//' + f, nxstxm_nxdl)
    else:
        print('Directory [%s] does not exist' % dir)
            
    print('Done')

def validate_file(fpath):
    res = True
    nxstxm_nxdl = get_NXstxm_nxdl()
    if(os.path.exists(fpath)):
        res = check_stxm_file(fpath, nxstxm_nxdl)
    else:
        print('File [%s] does not exist' % fpath)
            
    print('Done')
    return(res)

def nxstxm_validate(argv):
    import sys, getopt

    try:
        opts, args = getopt.getopt(argv,'f:d:',["file=","dir="])
    except getopt.GetoptError:
        print('\t USAGE: nxstxm_validate [-f <file> -d <directory>]')
        sys.exit(2)
    if(len(opts) == 0):
        print('invalid arguments given')
        print('\t USAGE: nxstxm_validate [-f <file> -d <directory>]')
        sys.exit(2)    
    for opt, arg in opts:
        if opt == '-h':
            print('\t USAGE: nxstxm_validate [-f <file> or -d <directory>]')
            sys.exit()
        elif opt in ("-f", "--file"):
            validate_file(arg)
        elif opt in ("-d", "--dir"):
            validate_filesin_dir(arg)
    
    

if __name__ == "__main__":

    #nxstxm_validate(sys.argv[1:])
    #nxstxm_validate('-d C:\controls\py2.7\Beamlines\sm\data\guest\May19'.split())
    #nxstxm_validate(r'-f C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\testdir\\C160810039.hdf5'.split())
    nxstxm_validate(r'-f C:\Continuum\Anaconda3\Lib\site-packages\suitcase\nxstxm\tests\test_results\CTEST000.hdf5'.split())
    #nxstxm_validate('-d C:\controls\py2.7\Beamlines\sm\data\SLS_pixelator_files'.split())
