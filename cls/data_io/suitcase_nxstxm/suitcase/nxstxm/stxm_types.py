
from enum import Enum

class scan_types(Enum):
    DETECTOR_IMAGE = 0
    OSA_IMAGE = 1
    OSA_FOCUS = 2
    SAMPLE_FOCUS = 3
    SAMPLE_POINT_SPECTRA = 4
    SAMPLE_LINE_SPECTRA = 5
    SAMPLE_IMAGE = 6
    SAMPLE_IMAGE_STACK = 7
    GENERIC_SCAN = 8
    COARSE_IMAGE_SCAN = 9
    COARSE_GONI_SCAN = 10
    TOMOGRAPHY_SCAN = 11
    PATTERN_GEN_SCAN = 12

two_posner_scans = [scan_types.DETECTOR_IMAGE.value, scan_types.OSA_IMAGE.value, scan_types.COARSE_IMAGE_SCAN.value,scan_types.COARSE_GONI_SCAN.value , scan_types.SAMPLE_IMAGE.value, scan_types.GENERIC_SCAN.value]


