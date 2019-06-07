# -*- coding:utf-8 -*-
"""
Created on 2011-09-13

@author: bergr
"""
import os
import numpy
from cls.utils.nextFactor import nextFactor 

def loadXim2Array(fname):
        if os.path.exists(fname):
            fp = open(fname, 'r')
            lines = fp.readlines()
            dat = []
            for line in lines:
                #remove the trailing tab and newline then add the newline back
                l2 = line.rstrip('\t\n')
                l3 = l2.split('\t')
                dat.append(l3)
            
            fp.close()
            array = numpy.array(dat,dtype=numpy.int32)
            
            #xim data is stored as it appears as an image which is
            # flipped so flip it back
            array = numpy.flipud(array)

        else:
            raise ValueError("loadXim2Array unable to open XIM file: file does not exist:", fname)
            return None
        
        #array = array.swapaxes(0, 1)
        #array = numpy.rot90(array)
        
        h,w = array.shape
            
        #if(h != w):
        #    if(h < w):
        #        #scale Height and width to something divisible by for (32 bit aligned)
        #        widthSc, htSc = nextFactor(w,h) 
        #        newArray = numpy.repeat(numpy.repeat(array, htSc, axis=0), widthSc, axis=1)
        #    else:    
        #        htSc, widthSc = nextFactor(h,w) 
        #        newArray = numpy.repeat(numpy.repeat(array, htSc, axis=0), widthSc, axis=1)
        #else:
        #    newArray = array
        newArray = array
            
        #print newArray.shape
        return newArray
    