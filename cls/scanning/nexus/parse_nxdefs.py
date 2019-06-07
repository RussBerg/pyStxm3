'''
Created on Mar 3, 2015

@author: bergr
'''
'''
Created on Mar 2, 2015

@author: bergr
'''
#!/usr/bin/python
import xml.etree.ElementTree as ET
import glob
import os
import re
import sys
#import nxs
import numpy
import h5py
import pkg_resources

#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.utils.dict_utils import dct_get, dct_put

def input_base_classes():
	clss = get_classes('base_classes')
	return(clss)

def input_application_classes():
	clss = get_classes('applications')
	return(clss)

def input_contributed_definition_classes():
	clss = get_classes('contributed_definitions')
	return(clss)



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

def make_string_attr(nxgrp, name, sdata):
	nxgrp.attrs[name] = sdata

def make_float_attr(nxgrp, name, fdata):
	nxgrp.attrs[name] = fdata

def make_class_type_attr(nxgrp, type):
	nxgrp.make_string_attr('NX_class',type)	

def make_date_time(nf, name, s, size=None):
	if(size):
		num_chars = size
	else:
		num_chars = len(s)
	nf.makedata(name,'char',[num_chars])
	nf.opendata(name)
	nf.putdata(s)
	nf.closedata()
	
def make_group(nxgrp, name, nxdata_type):
	grp = nxgrp.create_group(name)
	make_string_attr(grp, 'NX_class', nxdata_type)
	return(grp)

def make_dataset(nxgrp, name, data, nxdata_type, nx_units='NX_ANY'):
	grp = nxgrp.create_dataset(name=name, data=data)
	make_string_attr(grp, 'NX_class', nxdata_type)
	make_string_attr(grp, 'NX_units', nx_units)
	return(grp)


def make_instrument(nf, name, desc, pos, softmin, softmax):
	nxgrp = nf.create_group(name)
	make_string_attr(nxgrp, 'description',desc)
	make_string_attr(nxgrp, 'name', name)
	make_dataset(nxgrp, 'value', pos)
	make_dataset(nxgrp, 'soft_limit_min', softmin)
	make_dataset(nxgrp, 'soft_limit_max', softmax)


def make_positioner(nf, name, desc, pos, softmin, softmax):
	nxgrp = make_group(nf, name, 'NXpositioner')
	#make_string_attr(nxgrp, 'description',desc)
	make_string_data(nxgrp, 'description',desc)
	make_string_data(nxgrp, 'name',name)
	#make_string_attr(nxgrp, 'name', name)
	make_dataset(nxgrp, 'value', pos, 'NX_NUMBER')
	make_dataset(nxgrp, 'raw_value', pos, 'NX_NUMBER')
	make_dataset(nxgrp, 'target_value', pos, 'NX_NUMBER')
	make_dataset(nxgrp, 'soft_limit_min', softmin, 'NX_NUMBER')
	make_dataset(nxgrp, 'soft_limit_max', softmax, 'NX_NUMBER')
	
	make_dataset(nxgrp, 'tolerance', 0.0, 'NX_NUMBER')
	make_dataset(nxgrp, 'velocity', 0.0, 'NX_NUMBER')
	make_dataset(nxgrp, 'acceleration_time', 0.0, 'NX_NUMBER')
	make_string_attr(nxgrp, 'controller_record', name)
    
	
	
	
	

def make_entry(nf, name):
	""" create the basic entry group and the main sub groups
	that make up the NXstxm structure
	"""
	entry_nxgrp = make_group(nf, name, 'NXentry')
	make_string_attr(entry_nxgrp, 'HDF5_Version', '1.8.4')
	make_string_attr(entry_nxgrp, 'NeXus_version', '4.3.0')
	make_string_attr(entry_nxgrp, 'file_name', '/home/homersimpson/PLV_now.hdf5')
	make_string_attr(entry_nxgrp, 'file_time', '2012-01-01T12:00:00+01:00')
	
	make_dataset(entry_nxgrp, 'title', 'NeXus sample', 'NX_CHAR')
	make_dataset(entry_nxgrp, 'start_time', '2012-01-01T12:00:00+01:00', 'NX_DATE_TIME')
	make_dataset(entry_nxgrp, 'end_time', '2012-01-01T12:00:00+01:55', 'NX_DATE_TIME')
	#nf.makedata('start_time', 'NX_DATE_TIME')
	#f.makedata('end_time', 'NX_DATE_TIME')
	make_dataset(entry_nxgrp, 'definition','NSstxm', 'NX_CHAR')
	
	make_group(entry_nxgrp, 'instrument', 'NXinstrument')
	make_group(entry_nxgrp, 'sample', 'NXsample')
	make_group(entry_nxgrp, 'data', 'NXdata')
	make_group(entry_nxgrp, 'control', 'NXmonitor')
	return(entry_nxgrp)

	
	
def make_positioners(nxgrp, posners_dct={}):
	for k in list(posners_dct.keys()):
		#make_positioner(nxgrp, posner['name'], posner['desc'], posner['fbk'], posner['softmin'], posner['softmax'])
		make_positioner(nxgrp, k, '%s motor' % k, 0.0, 1000.0, 1000.0)

def make_NXstxm_file(fname):
	nf = h5py.File(fname, "w")
	entry_grp = make_entry(nf, 'entry1')
	devices = {}
	devices['POSITIONERS'] = {}
	devices['POSITIONERS']['SampleFineX'] = {}                                      
	devices['POSITIONERS']['SampleFineY'] = {}                                      
	devices['POSITIONERS']['CoarseX.X'] = {}                                      
	devices['POSITIONERS']['CoarseY.Y'] = {}                                      
	devices['POSITIONERS']['OSAX.X'] = {}                                      
	devices['POSITIONERS']['OSAY.Y'] = {}                                      
	devices['POSITIONERS']['DetectorX.X'] = {}                                      
	devices['POSITIONERS']['DetectorY.Y'] = {}                                      
	devices['POSITIONERS']['DetectorZ.Z'] = {}                                      
	devices['POSITIONERS']['ZonePlateZ.Z'] = {}                                     
	devices['POSITIONERS']['SampleX'] = {}                                     
	devices['POSITIONERS']['SampleY'] = {}                                     
	devices['POSITIONERS']['CoarseZ.Z'] = {}
	devices['POSITIONERS'][ENERGY] = {}                                      
	devices['POSITIONERS']['SlitX'] = {}                                      
	devices['POSITIONERS']['SlitY'] = {}                                      
	devices['POSITIONERS']['M3STXMPitch'] = {}                                      
	devices['POSITIONERS']['EPUGap'] = {}                                      
	devices['POSITIONERS']['EPUOffset'] = {}                                      
	devices['POSITIONERS']['EPUHarmonic'] = {}                                      
	devices['POSITIONERS']['EPUPolarization'] = {}               
	
	make_positioners(entry_grp, devices['POSITIONERS'])
	
	nf.close()
	



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
				#	print '[',node.tagName,']',"has value: [", node.nodeValue,']', "and is child of: [", node.parentNode.tagName, ']'
				#else:
				#	print '[%s] has value = [%s] and is child of: [%s]' % (str(node.tagName).upper(), str(node.nodeValue).upper(), str(node.parentNode.tagName).upper())
				#print_node(node)
				
			else:
				print('node [%s] is of type %d' % (node, node.nodeType))

def walk_xml():
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	fname = 'NXstxm.nxdl.xml'
	
	tree = ET.parse(os.path.join(base_class_path, fname))
	#tree = ET.fromstring("""...""")
	for  elt in tree.iter():
		if(elt.text != None):
			print("%s: '%s'" % (elt.tag, elt.text.strip()))

def try_this():
	from xmlutils.xml2json import xml2json
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	fname = 'NXstxm.nxdl.xml'
	#converter = xml2json(base_class_path+ '/' + fname, "samples/fruits.sql", encoding="utf-8")
	#converter.convert()
	
	# to get a json string
	converter = xml2json(os.path.join(base_class_path, fname), encoding="utf-8")
	print(converter.get_json())

def get_class_root(class_subdir, desired_class_name):
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/%s' % class_subdir)
	nxdl_files = list(map(os.path.basename, glob.glob(os.path.join(base_class_path,'*.nxdl.xml'))))
	for nxdl_file in nxdl_files:
		class_name = nxdl_file.split('.')[0]
		if(desired_class_name == class_name):
			return(ET.parse(os.path.join(base_class_path, nxdl_file)).getroot())
	return(None)	

def get_class_tree(class_subdir, desired_class_name):
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/%s' % class_subdir)
	nxdl_files = list(map(os.path.basename, glob.glob(os.path.join(base_class_path,'*.nxdl.xml'))))
	for nxdl_file in nxdl_files:
		class_name = nxdl_file.split('.')[0]
		if(desired_class_name == class_name):
			return(ET.parse(os.path.join(base_class_path, nxdl_file)))
	return(None)	

def get_classes_orig(class_name, root_element):
	pattern = re.compile(r'[\t\n ]+')
	nxclasses = {}
	class_doc = ''
	class_groups = {}
	class_fields = {}
	fields = {}
	for child in root_element:
		name = dtype = units = doc = ''
		if child.tag.endswith('doc'):
			try:
				class_doc = re.sub(pattern, ' ', child.text).strip()
			except TypeError:
				pass
		if child.tag.endswith('field'):
			
			if(len(child.getchildren()) > 0):
				fields = get_classes('field', child)
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
			class_fields[name] = (dtype, units, doc, fields)
		elif child.tag.endswith('group'):
			if(len(child.getchildren()) > 0):
				dtype = child.attrib['type']
				classes = get_classes('group', child)
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
			class_groups[name] = (doc, classes)
			
		elif child.tag.endswith('symbols'):
			if(len(child.getchildren()) > 0):
				classes = get_classes('symbols', child, )
#			try:
#				doc = child.attrib['doc']
#				name = child.attrib['name']
#			except KeyError:
#				pass
			for element in child:
				if element.tag.endswith('doc'):
					try:
						doc = re.sub(pattern, ' ', element.text).strip()
					except TypeError:
						pass
			
			class_groups['symbols'] = (doc, classes)
			
		elif child.tag.endswith('symbol'):
			try:
				#doc = child.attrib['doc']
				name = child.attrib['name']
			except KeyError:
				pass
			for element in child:
				if element.tag.endswith('doc'):
					try:
						doc = re.sub(pattern, ' ', element.text).strip()
					except TypeError:
						pass
			class_groups[name] = doc
		nxclasses[class_name] = (class_doc, class_fields, class_groups)
	return(nxclasses)

def get_fields(field):
	
	fields = {}
	for k in list(field.attrib.keys()):
		fields[k] = field.attrib[k] 
	return(fields)


def get_classes(class_name, root_element):
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
# 			if(len(child.getchildren()) > 0):
# 				fields = get_classes('field', child)
# 			try:
# 				name = child.attrib['name']
# 				dtype = child.attrib['type']
# 				units = child.attrib['units']
# 			except KeyError:
# 				pass
# 			for element in child:
# 				if element.tag.endswith('doc'):
# 					try:
# 						doc = re.sub(pattern, ' ', element.text).strip()
# 					except TypeError:
# 						pass
# 			#class_fields[name] = (dtype, units, doc, fields)
# 			group_fields[name] = {}
# 			
# 			for k in child.attrib.keys():
# 				group_fields[name][k] = child.attrib[k] 
# 			
# 			group_fields['doc'] = doc
		elif child.tag.endswith('group'):
			if(len(child.getchildren()) > 0):
				dtype = child.attrib['type']
				if('name' in list(child.attrib.keys())):
					name = child.attrib['name']
				else:
					name = dtype
				group_fields[name] = get_classes(name, child)
				#group_fields[dtype] = get_classes('group', child)
				#classes = get_classes('group', child)
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


def visit_symbols(tree, num_tabs):
	
# 	for node in tree:
# 		name = node.tag[node.tag.find('}')+1:]
# 		if(num_tabs < 0):
# 			num_tabs = 0
# 		s = ''
# 		for i in range(num_tabs):
# 			s += '\t' 
# 		
# 		print '%s'%s , name, node.attrib,node.text
	
	for node in tree.iter('symbols'):
		name = node.attrib.get('name')
		doc = node.attrib.get('doc')
		if name and doc:
			print('  %s :: %s' % (name, doc))
		else:
			print(name)

def visit_every_node(nodes, num_tabs):
	
	for node in nodes.iter():
		name = node.tag[node.tag.find('}')+1:]
		if(len(node.getchildren()) > 0):
			num_tabs += 1
			if(name == 'symbols'):
				visit_symbols(nodes, num_tabs)
			#visit_children(node.getchildren(), num_tabs)
			
		else:
			num_tabs -= 1
			if(num_tabs < 0):
				num_tabs = 0
			s = ''
			for i in range(num_tabs):
				s += '\t' 
			
			print('%s'%s , name, node.attrib,node.text)
		#print node.tag, node.attrib
# 		if(len(node.getchildren()) > 0):
# 			print 
# 			or ch in node.getchildren():
# 				visit_every_node(ch)
		
def sigh():
	from xml.etree import ElementTree
	class_def = {}
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	fname = 'NXstxm.nxdl.xml'
	#base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/base_classes')
	#fname = 'NXsource.nxdl.xml'
	fstr = os.path.join(base_class_path, fname)
	with open(fstr, 'rt') as f:
		tree = ElementTree.parse(f)
		
	definition_str = tree.find('.').tag
	i = definition_str.find('}')
	definition_str = definition_str[:i+1]
	class_def['definition'] = {}
	
	new_group = class_def['definition']
	root = tree.getroot()
	#for node in tree.iter():
	for node in root.getchildren():
		name = node.tag.replace(definition_str,'')
		if(name == 'group'):
			new_grp = walk_group(definition_str, node)
			if('name' in list(node.attrib.keys())):
				name = node.attrib['name']
			elif('NXentry' == node.attrib['type']):
				name = node.attrib['type']
			else:
				continue
			#type = node.attrib['type']
			#name = type
			#print '\n new Group [%s]' % name
			#print name, node.attrib
		else:
			new_grp = node.attrib
			
		new_group[name] = new_grp 
	return(class_def)

def walk_group(definition_str, tree):
	dct = {}
	for node in tree.getchildren():
		name = node.tag.replace(definition_str,'')
		if(name == 'group'):
			type = node.attrib['type']
			if('name' in list(node.attrib.keys())):
				name = node.attrib['name']
			else:
				if(type == 'NXinstrument'):
					name = 'instrument'
					dct[name] = {'type':type}
				
			dct[name] = walk_group(definition_str, node)
			#name = type
			print('\n new Group [%s]' % name)
		else:
			if(name == 'doc'):
				continue
			if('name' in list(node.attrib.keys())):
				name = node.attrib['name']
			else:
				continue
				#name = node.attrib['type']
			print(name, node.attrib)
			dct[name] = node.attrib
	return(dct) 	

def walk_grp(root):
	for node in root.findall('.'):
		type = node.attrib.get('type')
		#url = node.attrib.get('xmlUrl')
		#if name and url:
		#	print '  %s :: %s' % (name, url)
		#else:
		print(type)

def sigh2():
	from xml.etree import ElementTree

	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	fname = 'NXstxm.nxdl.xml'
	fstr = os.path.join(base_class_path, fname)
	with open(fstr, 'rt') as f:
		tree = ElementTree.parse(f)
		root = tree.getroot()
	
	#for node in root.findall('group'):
	for node in root.findall('.'):
		walk_grp(node)
		type = node.attrib.get('type')
		#url = node.attrib.get('xmlUrl')
		#if name and url:
		#	print '  %s :: %s' % (name, url)
		#else:
		print(type)

if __name__ == '__main__':
	import xml.dom.minidom as  md
	
	#try_this()
	#walk_xml()
	
	#make_NXstxm_file('positioner.hdf5')

	# returns tuple (class_doc, class_fields, class_groups)
#	dom = md.parse(r'C:\controls\nexus-definitions-development\dist\applications\NXstxm.nxdl.xml')
#	root = dom.documentElement
#	print_node(root)
	all = sigh()
	#sigh2()
	#base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	#fname = 'NXstxm.nxdl.xml'
# 	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/base_classes')
# 	fname = 'NXsource.nxdl.xml'
# 	#ET.register_namespace("xmlns", "huh")
# 	#ET.register_namespace("xsi", "huh2")
# 	f = open(base_class_path+'/'+fname, 'rt')
# 	tree = ET.parse(f)
# 	root = tree.getroot()
# 	
# 	#root = ET.fromstring(countrydata)
# 	
# 	# Top-level elements
# 	node = root.findall(".")
# 	print node	
# 	tree = get_class_tree('applications', 'NXstxm')
# 	visit_every_node(tree, 0)
# # 	bc = input_base_classes()
# 	root = get_class_root('applications', 'NXstxm')
# 	ac = get_classes('NXstxm', root)
# 	print ac.keys()
#  	ac = input_application_classes()
#  	(stxm_doc, stxm_flds, stxm_grps) = ac['NXstxm']
# 	
# 	make_NXstxm_file("positioner.hdf5")
# 
# 	
# 	exit