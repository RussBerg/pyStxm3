# -*- coding:utf-8 -*-
"""
Created on 2011-03-26

@author: bergr
"""
# -*- coding:utf-8 -*-
''' 
bergr:
This code is a modification of the pyDAQmx code by Pierre Cladé.
http://packages.python.org/PyDAQmx/ 
'''
import sys
from ctypes import *
if sys.platform.startswith('win'):
    from ctypes.wintypes import *


# New types definitions
# Correspondance between the name used in the NiDAQmx.h file and ctypes
int8 = c_byte
uInt8 = c_ubyte
int16 = c_short
uInt16 = c_ushort
int = c_int 
int32 = c_int 
uInt32 = c_uint 
float32 = c_float
double = c_double 
float64 = c_double 
int64 =c_longlong 
uInt64 = c_ulonglong 
bool32 = uInt32 
TaskHandle = uInt32
void = None
short = c_short
long = c_long
UCHAR = c_ubyte


