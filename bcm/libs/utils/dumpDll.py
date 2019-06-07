# -*- coding:utf-8 -*-
"""
Created on 2011-03-25

@author: bergr
"""
import string




class funcarg:
    def __init__ (self, name, type = None, isPtr = False):
        self.name = name
        self.type = type
        self.isPtr = isPtr

def remove_class_str(s):
    s = s.replace("<class '", '')
    s = s.replace("\'>",'')
    s = s.lstrip()
    return(s)

def isArgPtr(line):
    if(line.find('Types.LP_') > -1):
        return(True)
    else:
        return(False)

def gen_func_decl(dllName, funcname, fargs):
    
    #def _Memory_Read(self, Data):
    
    aStr = ''
    for a in fargs:
        aStr += ',' + a.name
    
    s = '\tdef ' + funcname + '(self' + aStr + '):\n'
    return(s)

def gen_arg_val(dllName, funcname, farg):
    #_Data = bcm.device.drivers.mic2560.mic2560_Types.LP_c_ushort(Data)
    s = '\t\t_' + farg.name + ' = ' + farg.type + '(' + farg.name + ')\n' 
    return(s)


def gen_funcall_with_args(dllName, funcname, fargs):
    #return( lib_hardware._Memory_Read(_Data))
    aStr = ''
    for a in fargs:
        aStr += '_' + a.name + ',' 
    
    #drop trailing comma
    args = aStr[0:-1]
    s = '\t\t# FUNCTION CALL\n'
    s += '\t\tlib_' + dllName + '.' + funcname + '(' + args + ')\n'
    return(s)


def gen_noarg_funcall_return(dllName, funcname, farg):
    #return( lib_hardware._Memory_Read(_Data))
    s = '\t\t# RETURN THE RESULT OF THE FUNCTION CALL\n'
    s += '\t\treturn( lib_' + dllName + '.' + funcname + '())\n'
    return(s)

def gen_val_return(dllName, funcname, farg):
    #return( lib_hardware._Memory_Read(_Data))
    s = '\t\t# RETURN THE VALUE\n'
    s += '\t\t#return( lib_' + dllName + '.' + funcname + '(_' + farg.name + '))\n'
    return(s)

def gen_argPtr_val(dllName, funcname, farg):
     
    #_Data = bcm.device.drivers.mic2560.mic2560_Types.LP_c_ushort()
    s = '\t\t_' + farg.name + ' = ' + farg.type + '()\n'
    
    #lib_hardware._Memory_Read(byref(_Data))
    #s1 = '\t\tlib_' + dllName + '.' + funcname + '(byref(_' + farg.name + '))\n'
    
    return(s)

def gen_ptr_return(dllName, funcname, farg):
    #return(_Data)
    s = '\t\t# RETURN THE REFERENCE\n'
    s += '\t\t#return(_' + farg.name + ')\n'
    return(s)


def gen_funcbody(dllName, funcname, fargs):
    
    #its a pointer arg so pass be reference
    #def _Memory_Read(self, Data):
    #    _Data = bcm.device.drivers.mic2560.mic2560_Types.LP_c_ushort()
    #    lib_hardware._Memory_Read(byref(_Data))
    #    return(_Data)
    
    #def _Memory_Read(self, Data):
    #s = '\tdef ' + funcname + '(self, ' + farg.name + '):\n'
    s = gen_func_decl(dllName, funcname, fargs)
    
    #_Data = bcm.device.drivers.mic2560.mic2560_Types.LP_c_ushort()
    #s1 = '\t\t_' + farg.name + ' = ' + farg.type + '()\n'
    s1 = ''
    s2 = ''
    s3 = ''
    for a in fargs:
        if a.isPtr:
            s1 += gen_argPtr_val(dllName, funcname, a)
            s3 += gen_ptr_return(dllName, funcname, a)
        else:
            s1 += gen_arg_val(dllName, funcname, a)
            s3 += gen_val_return(dllName, funcname, a)
    
    if(len(fargs) == 0):
        s2 += gen_noarg_funcall_return(dllName, funcname, fargs)
    else:
        s2 += gen_funcall_with_args(dllName, funcname, fargs)
    return(s+s1+s2+s3)

def print_func(dllName, funcname, args, retType, fout):
    
    functionArgs = []
    
    for a in args:
        argName = a[0].replace(' ','')
        argType = a[1]
        f = funcarg(argName, argType, isArgPtr(argType))
        
        functionArgs.append(f)
        
    s = gen_funcbody(dllName, funcname, functionArgs)
    fout.write('%s\n' % s)
    
def gen_python_class_header(dllName, constant_dict, fout, modbase):
    
    fout.write('\n\n\n')
    fout.write('import os\n')
    fout.write('import sys\n')
    fout.write('import ctypes\n')
    fout.write('from ctypes import byref\n')
    fout.write('import numpy as np\n\n\n')
    
    fout.write('import %sFunctions as lib_%s \n' % (modbase, dllName))
    fout.write('import %sTypes \n' % (modbase))
    fout.write('import %sConstants \n' % (modbase))
    
    fout.write('\n\n\n')
    
    fout.write('class ' + string.capitalize(dllName) + ':\n')
    
    fout.write('\t# DEFINES\n')
    
    for c in list(constant_dict.keys()):
        fout.write('\t%s = %s\n' % (c,constant_dict[c]))
        
    fout.write('\t#Global variables\n')
    fout.write('\t#__sockets = {}\n')
    fout.write('\t#__usedSockets = {}\n')
    fout.write('\t#__nbSockets = 0\n')

    fout.write('\t#Initialization Function\n')
    fout.write('\tdef __init__ (self):\n')
    fout.write('\t\tpass\n')
    fout.write('\t\t#place any init code here\n')
            



def gen_python_class(dllName, funcDict, constant_dict, modlist):

    keys = list(funcDict.keys())
    keys.sort()
    
    fName = dllName + '.py'
    fout = open(fName, 'w')
    
    gen_python_class_header(dllName, constant_dict, fout, modlist)
    
    for func in keys:
        f = funcDict[func]
        
        args = []      
        for i in range(0, len(f['arg_type'])):
            s = '%s' % f['arg_type'][i]
            atype = remove_class_str(s)
            args.append( (f['arg_name'][i],atype) )
        
        print_func(dllName, func, args, f['res_type'],fout)
            
    #print '\n\n\n'
    fout.close()  

def dumpDllFunctions(dllName, funcDict, level):

    keys = list(funcDict.keys())
    keys.sort()
    
    fName = dllName + '.txt'
    fout = open(fName, 'w')
    fout.write('Functions exported from %s' % dllName)
    
    for func in keys:
        f = funcDict[func]
        
        if(level > 0):
            str = '\n%s function [%s]' % (f['res_type'], func)
            if(f):
                fout.write(str)
        else:
            str = '[%s]' % (func)    
        
        print(str)
        
        
        if(level > 0):  
            args = []      
            for i in range(0, len(f['arg_type'])):
                str = '\t%s %s' % (f['arg_name'][i],f['arg_type'][i])
                print(str)
                args.append( (f['arg_name'][i],f['arg_type'][i]) )
                fout.write(str)
        
            
    #print '\n\n\n'
    fout.close()            
                
def LogToScreen(msg):
    print('LogToScreen: ' + msg)
    
    
    
    
if __name__ == '__main__':
    f = funcarg('Data', 'bcm.device.drivers.mic2560.mic2560_Types.LP_c_ushort', True)
    s = gen_pass_by_val_funcbody('hardware', '_Memory_Read', f)
    print(s)
    
    s = gen_pass_by_reference_funcbody('hardware', '_Memory_Read', f)
    print(s)
    
    
    
        