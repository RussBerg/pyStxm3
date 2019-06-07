#!/usr/bin/python 
import epics

class Mbbi(epics.Device):
	""" 
	Simple mbbi input device
	"""
	# attrs = ('VAL', 'INP', 'NAME','DESC',
	# 					'ZRVL','ONVL','TWVL','THVL','FRVL','FVVL','SXVL','SVVL','EIVL','NIVL','TEVL','ELVL','TVVL','TTVL','FTVL','FFVL',
	# 						'ZRST','ONST','TWST','THST','FRST','FVST','SXST','SVST','EIST','NIST','TEST','ELST','TVST','TTST','FTST','FFST')
    #
	# val_flds = ['ZRVL','ONVL','TWVL','THVL','FRVL','FVVL','SXVL','SVVL','EIVL','NIVL','TEVL','ELVL','TVVL','TTVL','FTVL','FFVL']
	# str_flds = ['ZRST','ONST','TWST','THST','FRST','FVST','SXST','SVST','EIST','NIST','TEST','ELST','TVST','TTST','FTST','FFST']

	attrs = []
	#def __init__(self,prefix):
	#	
	#	if self._fields != None:
	#		if not prefix.endswith('.'): 
	#			prefix = "%s." % prefix
	#		
	#	epics.Device.__init__(self,prefix,self._fields)
	def __init__(self, prefix, **kwargs):
		if prefix.endswith('.'):
			prefix = prefix[:-1]
		
		epics.Device.__init__(self, prefix, delim='.',
							  attrs=self.attrs, **kwargs)
	
	def get_position(self):
		return(self.get('VAL'))

	def get_name(self):
		return (self._prefix.replace(self._delim, ''))
		
		



		