# -*- coding:utf-8 -*-
"""
Created on 2011-03-04

@author: bergr
"""
import os, sys


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


def dirlist_withdirs(path, suffix, fname=None, remove_suffix=False, exclude=['.tmp']):
	"""
	Takes a path and a file suffix as a filter and returns a list of the files in
	that path that match the filter
	ex: alist = dirlist(r'C:\pythonxy\workspace\PyQtStxmViewer\src\data\101207\A101207022', '.xim')
	"""
	ret = []
	containsStr = suffix
	dirList = os.listdir(path)
	files = []
	dirs = []

	for f in dirList:
		skip = False
		for e in exclude:
			if(f.find(e) > -1):
				#we want to skip anything in the exclude list
				skip = True
		if(skip):
			continue
		# if(f.find(containsStr) > -1):
		# get the last 4 characters of filename as they are the file extension
		if (f.find('.') > -1):
			# its a file
			if(f.find(suffix) > -1):
				#its a file we want
				if (remove_suffix):
					f = f.replace(suffix, '')
				files.append(f)
			else:
				#its a file but we dont want these kinds
				pass
		else:
			#its a directory
			dirs.append(f)

	# for f in files:
	# 	extension = f[-(len(suffix)):]
	# 	if (suffix == extension):
	# 		if (remove_suffix):
	# 			f = f.replace(extension, '')
	# 		if (fname):
	# 			if (f.find(fname) > -1):
	# 				ret.append(f)
	# 		else:
	# 			ret.append(f)

	return dirs, files


if __name__ == "__main__":
	#dirlist(sys.argv[1:])
	# dirlist(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', '.hdf5')
	# dirlist(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', 'C180111004')
	# dirlist(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', '.hdf5', fname = 'C180111004')

	dirs, files = dirlist_withdirs(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', '.hdf5')
	dirs, files = dirlist_withdirs(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', 'C180111004')
	dirs, files = dirlist_withdirs(r'S:\STXM-data\Cryo-STXM\2018\guest\0111', '.hdf5', fname='C180111004')
	




#__all__ = ['dirlist']