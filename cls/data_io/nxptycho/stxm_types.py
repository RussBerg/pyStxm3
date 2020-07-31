'''
Created on Jan 4, 2019

@author: bergr
'''
from enum import Enum

class scan_types(Enum):
    DETECTOR_IMAGE = 0
    OSA_IMAGE = 1
    OSA_FOCUS = 2
    SAMPLE_FOCUS = 3
    SAMPLE_POINT_SPECTRUM = 4
    SAMPLE_LINE_SPECTRUM = 5
    SAMPLE_IMAGE = 6
    SAMPLE_IMAGE_STACK = 7
    GENERIC_SCAN = 8
    COARSE_IMAGE_SCAN = 9
    COARSE_GONI_SCAN = 10
    TOMOGRAPHY_SCAN = 11
    PATTERN_GEN_SCAN = 12
    PTYCHOGRAPHY_SCAN = 13

two_posner_scans = [scan_types.DETECTOR_IMAGE.value, scan_types.OSA_IMAGE.value, scan_types.COARSE_IMAGE_SCAN.value, \
                    scan_types.COARSE_GONI_SCAN.value , scan_types.SAMPLE_IMAGE.value, scan_types.GENERIC_SCAN.value]
single_entry_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS , scan_types.SAMPLE_FOCUS , \
                      scan_types.SAMPLE_LINE_SPECTRUM , scan_types.SAMPLE_IMAGE , scan_types.COARSE_IMAGE_SCAN, \
					  scan_types.COARSE_GONI_SCAN, scan_types.GENERIC_SCAN]
multi_entry_scans = [scan_types.SAMPLE_IMAGE_STACK , scan_types.SAMPLE_POINT_SPECTRUM]
single_2d_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.COARSE_IMAGE_SCAN, \
                           scan_types.COARSE_GONI_SCAN]
focus_scans = [ scan_types.SAMPLE_FOCUS, scan_types.OSA_FOCUS]
single_image_scans = [scan_types.SAMPLE_IMAGE]
stack_type_scans = [scan_types.SAMPLE_IMAGE_STACK, scan_types.TOMOGRAPHY_SCAN, scan_types.PTYCHOGRAPHY_SCAN]
spectra_type_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.GENERIC_SCAN]
line_spec_scans = [scan_types.SAMPLE_LINE_SPECTRUM]