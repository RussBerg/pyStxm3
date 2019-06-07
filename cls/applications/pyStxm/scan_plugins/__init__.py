'''
Created on 2013-05-13

@author: bergr
'''
import os

from .DetectorScan import DetectorScanClass
from .CoarseGoniScan import CoarseGoniScanClass
from .OsaScan import OsaScanClass
from .OsaFocusScan import OsaFocusScanClass
from .FocusScan import FocusScanClass
# from .SampleImageWithEnergySSCAN import SampleImageWithEnergySSCAN
from .SampleFineImageWithE712WavegenScan import SampleFineImageWithE712WavegenScanClass
from .PositionerScan import PositionerScanClass
# from .LineSpecSSCAN import LineSpecSSCAN
from .CoarseSampleImageScan import CoarseSampleImageScanClass
#
#
plugin_dir = os.path.dirname(os.path.realpath(__file__))
# #plugin_dir = 'C:/controls/py2.7/Beamlines/sm/stxm_control/ui/plugins/'
#
# __all__=['plugin_dir', 'DetectorScanClass', 'OsaScanClass', 'OsaFocusScanClass', 'FocusScanClass', 'SampleImageWithEnergySSCAN', 'SampleImageWithE712Wavegen', 'PositionerScanClass', 'LineSpecSSCAN','CoarseSampleImageScanClass']
__all__=['plugin_dir', 'DetectorScanClass', 'CoarseGoniScanClass','OsaScanClass','OsaFocusScanClass','FocusScanClass', \
         'SampleFineImageWithE712WavegenScanClass','PositionerScanClass', 'CoarseSampleImageScanClass']