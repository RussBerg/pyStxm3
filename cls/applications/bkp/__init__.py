'''
Created on 2013-05-13

@author: bergr
'''
import os

from .DetectorSSCAN import DetectorSSCAN
from .OsaSSCAN import OsaSSCAN
from .OsaFocusSSCAN import OsaFocusSSCAN
from .FocusSSCAN import FocusSSCAN
from .SampleImageWithEnergySSCAN import SampleImageWithEnergySSCAN
from .SampleImageWithE712Wavegen import SampleImageWithE712Wavegen
from .PositionerSSCAN import PositionerSSCAN
from .LineSpecSSCAN import LineSpecSSCAN
from .CoarseSampleImageSCAN import CoarseSampleImageSCAN

plugin_dir = os.path.dirname(os.path.realpath(__file__))
#plugin_dir = 'C:/controls/py2.7/Beamlines/sm/stxm_control/ui/plugins/'

__all__=['plugin_dir', 'DetectorSSCAN', 'OsaSSCAN', 'OsaFocusSSCAN', 'FocusSSCAN', 'SampleImageWithEnergySSCAN', \
         'SampleImageWithE712Wavegen', 'PositionerSSCAN', 'LineSpecSSCAN','CoarseSampleImageScanClass']