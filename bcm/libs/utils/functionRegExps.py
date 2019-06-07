'''
Created on 2011-03-31

@author: bergr

'''
import re
#from libutils.types import *
from bcm.libs.utils.types import *

local_lib_types_re = None

try:
    import numpy
except ImportError:
    def array_type(string):
        return eval('POINTER('+string+')')
else:
    # Type conversion for numpy
    def numpy_conversion(string):
        """ Convert a type given by a string to a numpy type
        """
        #This function uses the fact that the name are the same name, 
        #except that numpy uses lower case
        return eval('numpy.'+string.lower())
    
    def array_type(string):
        """ Returns the array type required by ctypes when numpy is used """
        return numpy.ctypeslib.ndpointer(dtype = numpy_conversion(string))

def loadFunctionRegExps(local_lib_types_re = []):
    '''
    The functions in a header file need to be converted from C types to 
    python ctypes, loadFunctionRegExps() loads the neccesary regular expressions
    that will be used to decide what the function return type and parameters
    are, then convert them to python ctypes
    '''
    ######################################
    # Array
    ######################################
    #Depending whether numpy is install or not, 
    #the function array_type is defined to return a numpy array or
    #a ctype POINTER
    
    
    
    allStringTypes = ['int8','uInt8','int16','uInt16','int32','uInt32','float32','float64','int64','uInt64','bool32','TaskHandle']
    type_list = ['short','long','int','double','int8','uInt8','int16','uInt16','int32','uInt32','float32','float64','int64','uInt64','bool32','TaskHandle']
    type_list_array = ['uInt8','int16','uInt16','int32','uInt32','float32','float64','int64','uInt64']

    # Each regular expression is assiciated with a ctypes type and a number giving the 
    # group in which the name of the variable is defined
    #fre_function_parser = re.compile(r'(.*) (\w\S+)\s*\((.*)\);')
    fre_const_char = re.compile(r'(const char)\s*([^\s]*)\[\]')
    fre_string_type = '|'.join(allStringTypes)

    # Each regular expression is assAciated with a ctypes type and a number giving the 
    # group in which the name of the variable is defined
    fre_const_char = [(re.compile(r'(const char)\s*([^\s]*)\[\]'), c_char_p ,2)]
    fre_simple_type = [(re.compile('('+_type+')\s*([^\*\[]*)\Z'), eval(_type),2) for _type in type_list]
    fre_pointer_type = [(re.compile('('+_type+')\s*\*([^\*]*)\Z'), eval('POINTER('+_type+')'),2) for _type in type_list]
    fre_pointer_type_array = [(re.compile('('+_type+')\s*([readArray|writeArray]*)\[\]\Z'), array_type(_type),2) for _type in type_list_array]
    fre_pointer_type_2 = [(re.compile('('+_type+')\s*([^\s]*)\[\]\Z'), eval('POINTER('+_type+')'),2) for _type in type_list]
    
    fre_char_etoile = [(re.compile(r'(char)\s*\*([^\*]*)\Z'), c_char_p, 2)] # match "char * name"
    fre_void_etoile = [(re.compile(r'(void)\s*\*([^\*]*)\Z'), c_void_p, 2)] # match "void * name"
    fre_void_etoile.append( (re.compile(r'(void)\s*\**([^\*]*)\Z'), c_void_p, 2) ) # match "void ** name"
    #fre_void_etoile.append( (re.compile(r'(HANDLE)\s*\**([^\*]*)\Z'), c_void_p, 2) ) # match "HANDLE name"
    fre_char_array = [(re.compile(r'(char)\s*([^\s]*)\[\]'), c_char_p,2)] # match "char name[]"


    # Create a list with all regular expressions
    c_to_ctype_map = []
    for l in [local_lib_types_re, fre_const_char, fre_simple_type, fre_pointer_type, fre_pointer_type_array, fre_pointer_type_array,
            fre_pointer_type_2,fre_char_etoile, fre_void_etoile, fre_char_array]: 
            #call_back_A, call_back_B, call_back_C]:
        c_to_ctype_map.extend(l)
        
    return c_to_ctype_map


def convertToCType(arg, cToCTypMap):
    new_type = None
    for (reg_expr, new_type, groug_nb) in cToCTypMap:
        reg_expr_result = reg_expr.search(arg)
        if reg_expr_result is not None:
            break # break the for loop

    return new_type


if __name__ == '__main__':
    map = loadFunctionRegExps()
    print(map)