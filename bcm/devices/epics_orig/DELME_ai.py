#!/usr/bin/env python
"""Epics analog input record"""
from .base import BaseDevice

class ai(BaseDevice):
	"Simple analog input device"

	attrs = ('VAL', 'EGU', 'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC',
			 'DTYP', 'INP', 'LINR', 'RVAL', 'ROFF', 'EGUF', 'EGUL',
			 'AOFF', 'ASLO', 'ESLO', 'EOFF', 'SMOO', 'HIHI', 'LOLO',
			 'HIGH', 'LOW', 'HHSV', 'LLSV', 'HSV', 'LSV', 'HYST')

	def __init__(self, prefix, **kwargs):
		if prefix.endswith('.'):
			prefix = prefix[:-1]
		#kwargs['connect'] = False
		if ('desc' in list(kwargs.keys())):
			desc = kwargs['desc']
			kwargs.pop("desc", None)
		else:
			desc = ''

		epics.Device.__init__(self, prefix, delim='.',
							  attrs=self.attrs, **kwargs)


	def get_position(self):
		return(self.get('VAL'))

	def get_name(self):
		return(self._prefix.replace(self._delim,''))

	def put_desc(self, desc):
		self.put('DESC', desc)
		
	
if __name__ == '__main__':
	import sys
	from PyQt5 import QtWidgets	
	def on_cpt(**kw):
		print(kw)
		
	app = QtWidgets.QApplication(sys.argv)
	#aa = ai('TRG2400:cycles')
	#aa.add_callback('VAL', on_cpt)
	aa = ai('uhvAi:ai:aio_RBV', desc='Interferometer signal voltage X axis')
	#print aa.DESC
	print(aa.get_position())
	app.exec_()
	
