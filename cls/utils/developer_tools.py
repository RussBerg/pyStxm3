'''
Created on 2014-04-10

@author: bergr
'''
""" the point of this class is to be a one stop module that can be loaded by all other modules
and export tools that I might need during development, like DONT FORGET TO DO THIS type messages etc
that can easily be searched for (as opposed to simple print statements) and removed when development is more or less finished
"""

def DONT_FORGET(mod, msg):
	print('DONT_FORGET: [%s]  %s' % (mod, msg))


__all__ = ['DONT_FORGET']