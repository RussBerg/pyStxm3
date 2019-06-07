'''
Created on 2013-05-13

@author: bergr
'''
import os

from .DetectorSSCAN import DetectorSSCAN
#from PositionerScanClass import PositionerScanClass

plugin_dir = os.path.dirname(os.path.realpath(__file__))

#__all__=['plugin_dir', 'DetectorSSCAN', 'PositionerScanClass']
__all__=['plugin_dir', 'DetectorSSCAN']
