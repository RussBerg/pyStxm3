# -*- coding:utf-8 -*-
"""
Created on 2011-03-26

@author: bergr
"""
import re
from .Types import *

def convertToCtype(arg, extraTypesModule):
    
    
    if(extraTypesModule):
        exec("from %s import *" % extraTypesModule)
    
    const_char = re.compile(r'(const char)\s*([^\s]*)\[\]')
    string_type = '|'.join(['WORD','HANDLE','int','double','int8','uInt8','int16','uInt16','int32','uInt32','float32','float64','int64','uInt64','bool32','TaskHandle'])
    
    simple_type = re.compile('('+string_type+')\s*([^\*\[]*)\Z')
    pointer_type = re.compile('('+string_type+')\s*\*([^\*]*)\Z')
    pointer_type2 = re.compile('('+string_type+')\s*([^\s]*)\[\]\Z')
    char_etoile = re.compile(r'(char)\s*\*([^\*]*)\Z') # match "char * name"
    void_etoile = re.compile(r'(void)\s*\*([^\*]*)\Z') # match "void * name"
    char_array = re.compile(r'(char)\s*([^\s]*)\[\]') # match "char name[]"
    dots = re.compile('\.\.\.')
    call_back = re.compile(r'([^\s]*CallbackPtr)\s*([^\s]*)') # Match "DAQmxDoneEventCallbackPtr callbackFunction"
    if const_char.search(arg):
        return(c_char_p)
            
    elif simple_type.search(arg): 
        return( eval(simple_type.search(arg).group(1)))
            
    elif pointer_type.search(arg): 
        return( eval('POINTER('+pointer_type.search(arg).group(1)+')') )
            
    elif pointer_type2.search(arg):
        if pointer_type2.search(arg).group(2) == 'readArray' or pointer_type2.search(arg).group(2) == 'writeArray':
            return(array_type(pointer_type2.search(arg).group(1)))
        else:    
            return( eval('POINTER('+pointer_type2.search(arg).group(1)+')') )
            
    elif char_etoile.search(arg):
        return(c_char_p)
            
    elif void_etoile.search(arg):
        return(c_void_p)
            
    elif char_array.search(arg):
        return(c_char_p)
            
    elif call_back.search(arg):
        return( eval(call_back.search(arg).group(1)) )
                                    
    elif dots.search(arg):
        pass
    else:
        return(eval(arg))


if __name__ == '__main__':
    str = 'char *'
    print(convertToCtype(str, None))
    str = 'WORD *'
    print(convertToCtype(str, None))
    str = 'HANDLE'
    print(convertToCtype(str, None))
    
    

