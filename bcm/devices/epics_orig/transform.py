#!/usr/bin/env python
"""Epics transform record"""

import os 
#path_sep = ';'
#epicsPath = r'C:\controls\epics\R3.14.12.4\base\bin\win32-x86;C:\controls\epics\R3.14.12.4\lib\win32-x86;C:\controls\py2.7\cls;C:\controls\py2.7\blctl'
#mypypath = r'C:\\controls\\py2.7\\cls;C:\\controls\\py2.7\\blctl;C:\\eclipse\\plugins\\org.python.pydev_3.4.1.201403181715\\pysrc\\pydev_sitecustomize;C:\\controls\\py2.7\\blctl;C:\\controls\\py2.7\\Beamlines;C:\\controls\\py2.7\\cls;C:\\Python27\\DLLs;C:\\Python27\\lib;C:\\Python27\\lib\\lib-tk;C:\\Python27;C:\\Python27\\lib\\site-packages;C:\\Python27\\lib\\site-packages\\PIL;C:\\Python27\\lib\\site-packages\\win32;C:\\Python27\\lib\\site-packages\\win32\\lib;C:\\Python27\\lib\\site-packages\\Pythonwin;C:\\Python27\\lib\\site-packages\\setuptools-0.6c11-py2.7.egg-info;c:\\nix-mapsaw-ed43276;C:\\Python27\\lib\\site-packages\\yapsy-1.10.423-py2.7.egg;C:\\Python27\\lib\\site-packages\\nexpy-0.5.4-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\matplotlib-1.4.3-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\mayavi-4.3.0-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\traitsui-4.3.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\traits-4.3.0-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\apptools-4.2.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\pyface-4.3.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\configobj-4.7.2-py2.7.egg;C:\\Python27\\lib\\site-packages\\pydaqmx-1.2.5.2-py2.7.egg;C:\\Python27\\lib\\site-packages\\sqlalchemy-0.7.11dev-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pyepics-3.2.4-py2.7.egg;C:\\Python27\\lib\\site-packages\\pyside-1.2.2-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pyparsing-2.0.3-py2.7-win32.egg;C:\\Python27\\lib\\site-packages\\pytz-2014.10-py2.7.egg;C:\\Python27\\lib\\site-packages\\python_dateutil-2.4.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\six-1.9.0-py2.7.egg;C:\\Python27\\lib\\site-packages\\xmlutils-1.1-py2.7.egg;C:\\Program Files\\NeXus Data Format\\bin;C:\\Python27\\lib\\site-packages\\ipython-3.0.0-py2.7.egg'

#path  = [os.environ['PATH']]
#path.extend(epicsPath.split(';'))
#os.environ['PATH'] = path_sep.join(path)

#pypath = os.environ['PYTHONPATH'] + ';' + mypypath
#os.environ['PYTHONPATH'] = pypath
#print os.environ['PYTHONPATH']

import epics

class Transform(epics.Device):
	"Epics transfrom record"

# 	attr_fmts = {'Value': '%s',
# 				 'Input': 'INP%s',
# 				 'Input_Valid': 'I%sV',
# 				 'Expression': 'CLC%s',
# 				 'Output':  'OUT%s',
# 				 'Output_Valid': 'O%sV',
# 				 'Comment': 'CMT%s',
# 				 'Expression_Valid': 'C%sV',
# 				 'Previous_Value': 'L%s'}
	attr_fmts = {'%s': '%s',
				 'INP%s': 'INP%s',
				 'I%sV': 'I%sV',
				 'CLC%s': 'CLC%s',
				 'OUT%s':  'OUT%s',
				 'O%sV': 'O%sV',
				 'CMT%s': 'CMT%s',
				 'C%sV': 'C%sV',
				 'L%s': 'L%s'}
	attrs = ['COPT', 'PREC', 'PINI']
	rows = 'ABCDEFGHIJKLMNOP'
	all_rows = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
	#_init_list   = ('VAL', 'DESC', 'RTYP', 'RBV', 'PREC', 'TWV', 'FOFF', 'EGU')
	
	def __init__(self, prefix, **kwargs):
		if prefix.endswith('.'):
			prefix = prefix[:-1]
		
		self.name = prefix
		#self.attrs = ['COPT', 'PREC', 'PINI']
		for fmt in list(self.attr_fmts.values()):
			for let in self.rows:
				self.attrs.append(fmt %  let)
		
		
		epics.Device.__init__(self, prefix, delim='.',
							  attrs=self.attrs,
							  **kwargs)
	
	
	
	def __validrow(self, row):
		return (isinstance(row, str) and
				len(row)==1 and row in self.rows)
	
	def get_name(self):
		#return (self.get('NAME'))
		return(self._prefix.replace(self._delim,''))
	
	def get_position(self):
		""" this is an API function for all devices/pvs/detectors """
		return(self.get_all())
	
	def get_all(self):
		all = {}
		all['PINI'] = self.get('PINI')
		all['PREC'] = self.get('PREC')
		
		for r in self.all_rows:
			all[r] = self.get_row(r)
		
		return(all)
	
	def get_row(self, row='A'):
		"""get full data for a calculation 'row' (or letter):

		returns dictionary with keywords (and PV suffix for row='B'):

		'Value':			 B
		'Input':			 INPB
		'Input_Valid':	   IBV
		'Expression':		CLCB
		'Output':			OUTB
		'Output_Valid':	  OBV
		'Comment':		   CMTB
		'Expression_Valid':  CBV
		'Previous_Value':	LB

		"""
		if not self.__validrow(row):
			return None
		dat = {}
		for label, fmt in list(self.attr_fmts.items()):
			dat[label % row] = self._pvs[fmt % row].get()
		return dat

	def set_row(self, row='A', data=None):
		"""set full data for a calculation 'row' (or letter):

		data should be a dictionary as returned from get_row()
		"""
		if not self.__validrow(row):
			return None
		for key, value in list(data.items()):
			if key in self.attr_fmts:
				attr = self.attr_fmts[key] % row
				if self._pvs[attr].write_access:
					self._pvs[attr].put(value)

	def set_calc(self, row='A', calc=''):
		"""set calc for a 'row' (or letter):
		calc should be a string"""
		if not self.__validrow(row):
			return None
		self._pvs[self.attr_fmts['Expression'] % row].put(calc)

	def set_comment(self, row='A', comment=''):
		"""set comment for a 'row' (or letter):
		comment should be a string"""
		if not self.__validrow(row):
			return None
		self._pvs[self.attr_fmts['Comment'] % row].put(calc)

	def set_input(self, row='A', input=''):
		"""set input PV for a 'row' (or letter):
		input should be a string"""
		if not self.__validrow(row):
			return None
		self._pvs[self.attr_fmts['Input'] % row].put(calc)
	
	def gen_record_row(self, r, dct):
		r_dct = dct[r]
		s = '\tfield(CMT%s, "%s")		field(INP%s, "%s")		field(CLC%s, "%s")		field(%s, "%s")		field(OUT%s, "%s")\n' % \
			  (r, r_dct['CMT%s'%r], r, r_dct['INP%s'%r], r, r_dct['CLC%s'%r], r, r_dct['%s'%r], r, r_dct['OUT%s'%r])
		return(s)
	
	def gen_record(self):
		dct = self.get_all()
		s = 'record(transform, "%s")\n' % self.name 
		s += '{\n' 		
		s += '\tfield(PINI, "%s")\n' % dct['PINI']
		s += '\tfield(PREC, "%s")\n' % dct['PREC']
		s += '\n'
		
		for row in self.all_rows:
			s += self.gen_record_row(row, dct) 		  
		s += '}\n\n'
		return(s)



if __name__ == '__main__':
	import os

	
	#for i in range(1,50):
	#	t = Transform('BL08ID1:trans_%d:tr' % i)
	#	print t.gen_record()
	print('starting')
	z = Transform('BL1610-I10:ENERGY:amb:zp:def')
	#o = Transform('BL1610-I10:ENERGY:amb:osa:def')
	print('done') 
	#print t.get_all()
	#print t.gen_record()
	
