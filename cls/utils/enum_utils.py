import re

def simple_enum(**enums):
	return type('Enum', (), enums)

class Enum(object):
	"""
	An Enumerated data type class for django models.
	
	Usage::
	
		>>> e = Enum('One','Two','Three') # create an enumerated type with strings
		>>> e
		<Enum: [ONE=0, TWO=1, THREE=2]>
		>>> e.get_choices()
		[(0, 'One'), (1, 'Two'), (2, 'Three')]
		>>> e.ONE, e.TWO, e.THREE
		(0, 1, 2)
		>>> e[0], e[1], e[2] # get the descriptions by their values
		('One', 'Two', 'Three')
		>>> e = Enum(one=1,two=2,three=3)
		>>> print e
		<Enum: [ONE=1, TWO=2, THREE=3]>
		>>> e.get_choices()
		[(1, 'one'), (2, 'two'), (3, 'three')]
		>>> e = Enum('One','Two','Three', Three=6, Four='1')
		>>> e
		<Enum: [ONE=0, FOUR=1, THREE=2, THREE=6]> 
	"""
	
	def __init__(self, *entries, **kw_entries):
		"""
		Initialized with an ordered list of string arguments and/or
		keyworded arguments. 
		
		The interger values of a list of strings are zero-based and assigned in
		the order of the strings. For keyworded arguments any integer values can 
		be given. The values of keyworded arguments must be integers or 
		convertable to integers. When duplicate values are encountered, the last
		value defined overwrites all previous entries.
		
		If using a list of strings, attributes will be created for each string
		corresponding to the uppercase version with all spaces and hyphens
		replaced by underscores. Any string which can not be converted into a 
		valid python variable name will be ignored. 
		
		"""
		
		self._dict = {}
		self._reverse_dict = {}
		self._attr_dict = {}
		
		if entries:
			for i, p in enumerate(entries):
				attr, descr = p.upper(), p
				for c in [' ','-',]:
					attr = attr.replace(c,'_')
				if re.compile('^[a-zA-Z_]+[\w]+$').match(attr):
					self.__setattr__(attr, i)
					self._attr_dict[i] = attr
					self._dict[i] = descr
					self._reverse_dict[descr] = i

		if kw_entries:
			for k, i  in list(kw_entries.items()):
				attr = k.upper()
				descr = k.replace('_',' ')
				i = int(i)
				if re.compile('^[a-zA-Z_]+[\w]+$').match(attr):
					self.__setattr__(attr, i)
					self._dict[i] = descr
					self._reverse_dict[descr] = i
					self._attr_dict[i] = attr

	def __repr__(self):
		items = list(self._attr_dict.items())
		items.sort()
		args = ["%s=%s" % (k, v) for v, k in items]
		return '<%s: [%s]>' % (self.__class__.__name__, ', '.join(args))

	
	def __getitem__(self, key):
		if key in self._dict:
			return self._dict.get(key)
		else:
			raise KeyError

	def __iter__(self):
		return iter(self._dict.items())

	def get_choices(self):
		""" 
		Get an ordered list where each element is a 2-tuple. The first item
		in the tuple is the integer value and the second item is a string
		description of the element
		"""
		choices = list(self._dict.items())
		choices.sort()
		return choices
	
	def get_value_by_name(self, name):
		"""
		"""
		return self._reverse_dict[name]
	
	def get_str_by_num(self, num):
		return(self._dict[num])
	
	
