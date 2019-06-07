'''
Created on Mar 4, 2015

@author: bergr
'''
import xmltodict
import os
import pkg_resources

def get_val(s):
	idx = s.find('=')
	s = s[idx+2:]
	idx2 = s.find('"')
	s = s[:idx2]
	
	return(s)

def get_type(s):
	sz = len('type="')
	idx = s.find('type=')
	if(idx == -1):
		return(None)
	s = s[idx+sz:]
	idx2 = s.find('"')
	s = s[:idx2]
	
	return(s)

def get_name(s):
	sz = len('name="')
	idx = s.find('name=')
	if(idx == -1):
		return(None)
	s = s[idx+sz:]
	idx2 = s.find('"')
	s = s[:idx2]
	
	return(s)



if __name__ == '__main__':
	
	import deepdish as dd
	
	#base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/applications')
	#fname = base_class_path + '/NXstxm.nxdl.xml'
	
	base_class_path = pkg_resources.resource_filename('nexpy', 'definitions/base_classes')
	fname = base_class_path + '/NXsource.nxdl.xml'
	
	
	num_tabs = 0
	filename = os.path.join(fname)
	xmlstring = open(filename).read()
	xmls = xmlstring.split('\n')
	for l in xmls:
		s = ''
		if(l.find('definition') > 0):
			#new group
			type = get_val(l.strip())
			name = get_name(l.strip())
			#print 'create_group(%s)' % type
			
			for i in range(num_tabs):
				s += '\t' 
			
			
			if(name != None):
				print('%screate_group(%s)  type=%s' % (s, name, type))
			else:
				print('%screate_group(%s)' % (s, type)) 
			
			if(type == 'NXentry'):
				num_tabs = 1
		elif(l.find('group') > 0):
			#new group
			type = get_val(l.strip())
			name = get_name(l.strip())
			#print 'create_group(%s)' % type
			
			for i in range(num_tabs):
				s += '\t' 
			
			
			if(name != None):
				print('%screate_group(%s)  type=%s' % (s, name, type))
			else:
				print('%screate_group(%s)' % (s, type)) 
			
			if(type == 'NXentry'):
				num_tabs = 1
		
		elif(l.find('field') > 0):
			#new group
			name = get_val(l.strip())
			type = get_type(l.strip())
			if(type != None):
				print('%s\t name=%s  type=%s' % (s, name, type))
			else:
				print('%s\t name=%s' % (s, name)) 
	
	
#	doc = xmltodict.parse(xmlstring)
#	#dd.io.save('test.h5', {'data': X, 'label': y}, compress=False)
#	dd.io.save('test.hdf5', doc, compress=False)
	#doc['definition']['group']['@type']
	