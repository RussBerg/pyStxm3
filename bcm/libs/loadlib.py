'''
Created on 2011-03-30

@author: bergr
'''

import sys, os, os.path
import contextlib
import re, tempfile, errno
from ctypes import *
from ctypes.util import find_library

def findlib(lib_name):
    """
    find location of dynamic library
    """
    
    search_path = [os.path.split( os.path.abspath(__file__))[0]]
    search_path.extend(sys.path)
    search_path.append(':.:')
    path  = os.environ['PATH']
    path_sep = ':'
    if os.name == 'nt':
        path_sep = ';'
        search_path.append(os.path.join(sys.prefix, 'DLLs'))
        search_path.append(os.path.join(sys.prefix, 'DLLs\\bcm'))
    
    search_path.extend(os.environ['PATH'].split(path_sep))

    os.environ['PATH'] = path_sep.join(search_path)  

    if os.name == 'nt':
        dllpath  = find_library(lib_name)
    else:
        dllpath  = myfind_library(lib_name)
        
    if dllpath is not None:
        return dllpath

    print('find_lib: Cannot find %s' % lib_name) 
    print('in the following path: ' ,os.environ['PATH'])    
 

 
def myfind_library(name): 
    #returns the pathname of a library, or None.
    if(os.path.exists(name)):
        #we were passed a direct path to the lib
        return(name)
    #else try and find it
    if os.name == 'nt':
        expr = r'[^\(\)\s]*%s\.[^\(\)\s]*' % re.escape(name)
    else:
        expr = r'[^\(\)\s]*lib%s\.[^\(\)\s]*' % re.escape(name)
    fdout, ccout = tempfile.mkstemp()
    os.close(fdout)
    l_flags = ''
    ld_libpath = os.getenv('LD_LIBRARY_PATH')
    if ld_libpath:
        l_flags = ' -L ' + ' -L '.join(dir for dir in ld_libpath.split(':') if os.path.isdir(dir))
        cmd = 'if type gcc >/dev/null 2>&1; then CC=gcc; elif type cc >/dev/null 2>&1; then CC=cc;else exit 10; fi;' \
              '$CC' + l_flags + ' -Wl,-t -o ' + ccout + ' 2>&1 -l' + name
        
        #f = os.popen(cmd)
        res = re.search(expr,os.popen(cmd).read())
        if not res:
            return None
        return res.group(0)

def loadlocallib(lib_name,useCDll=False):     
    try:
        #dllname = findlib(lib_name)
        dllname = r'./' + lib_name
        if os.name == 'nt':
            if(useCDll):
                #for cdecl of the form __declspec(dllexport)
                load_dll = cdll.LoadLibrary
            else:    
                # for stdcall 
                load_dll = windll.LoadLibrary
        else:
            load_dll = cdll.LoadLibrary
            
        lib = load_dll(dllname)
        return(lib)
            
    except:
        print("lib(%s) could not be loaded!" % lib_name)   
        sys.exit(1) 
        
def loadlib(lib_name,useCDll=False):     
    try:
        dllname = findlib(lib_name)
        #dllname = r'./' + lib_name
        if os.name == 'nt':
            if(useCDll):
                #for cdecl of the form __declspec(dllexport)
                load_dll = cdll.LoadLibrary
            else:    
                # for stdcall 
                load_dll = windll.LoadLibrary
        else:
            load_dll = cdll.LoadLibrary
            
        lib = load_dll(dllname)
        return(lib)
            
    except :
        print("lib(%s) could not be loaded!" % dllname)   
        sys.exit(1)
    
if __name__ == '__main__':
    
    #l = loadlib('pmc89dvr', useCDll=True)
    l = loadlib('vcDP5', useCDll=True)
    print(l)
    
    
    