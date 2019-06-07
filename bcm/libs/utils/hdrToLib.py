# -*- coding:utf-8 -*-
"""
Created on 2011-04-01

@author: bergr
"""
# -*- coding:utf-8 -*-
''' 
bergr:
This code is a modification of the pyDAQmx code by Pierre Cladé.
http://packages.python.org/PyDAQmx/ 
'''

import re
import sys, os
from libutils.loadlib import loadlib
from libutils.functionRegExps import loadFunctionRegExps, convertToCType
from libutils.types import *
from .dumpDll import dumpDllFunctions

################################################################################
# Don't touche anything below
#dot_h_file = os.path.dirname(os.path.abspath(__file__)) + r'\testDll.h'
#lib_name = "testDll"
#driverTypesFile = 'tstDll.tstDll_Types'
#func_search_str = 'TESTDLL_API'
#strip_list = ['']
#useCDll = True

def parseHeader(dot_h_file, lib_name,func_search_str, strip_list, useCDll):
    LIB = loadlib(lib_name, useCDll)
    c_to_ctype_map = loadFunctionRegExps()
    function_list = [] 
    function_dict = {} 
    function_parser = re.compile(r'(.*) (\w\S+)\s*\((.*)\);')

    include_file = open(dot_h_file,'r') 
    
    for line in include_file:
        line = line[0:-1]
        if func_search_str in line and function_parser.match(line):
            retStr = function_parser.match(line).group(1)
            retStr = retStr.strip(func_search_str)
            for stripStr in strip_list:
                retStr = retStr.rstrip(stripStr)
            retType = convertToCType(retStr, c_to_ctype_map)

            name = function_parser.match(line).group(2)
            function_list.append(name)
            arg_string = function_parser.match(line).group(3)
            arg_list=[]
            arg_name = []
            for arg in re.split(',',arg_string):
                arg = arg.strip()
                for (reg_expr, new_type, groug_nb) in c_to_ctype_map:
                    reg_expr_result = reg_expr.search(arg)
                    if reg_expr_result is not None:
                        arg_list.append(new_type)
                        arg_name.append(reg_expr_result.group(groug_nb))
                        break # break the for loop
            
            function_dict[name] = {'res_type':retType,'arg_type':arg_list, 'arg_name':arg_name}
            # Fetch C function and apply argument checks
            cfunc = getattr(LIB, name)
            setattr(cfunc, 'argtypes', arg_list)
            setattr(cfunc, 'restype', retType)
            func = cfunc
            func.__name__ = name
            func.__doc__ = '%s(%s) -> error.' % (name, ','.join(arg_name))
            globals()[name] = func
            
    dumpDllFunctions(lib_name, function_dict, 1)
    include_file.close()

if __name__ == '__main__':
    
    parseHeader()
    
    print('\nTESTING: import of testDll')
    
    h = HANDLE()
    addr = c_short(0x260)
    
    ret = SrvoOpen('pmc007',byref(h), byref(addr)) 
    if (ret != 0) :
        print("Servo X Open failed")
        sys.exit()
    
    del parseHeader

