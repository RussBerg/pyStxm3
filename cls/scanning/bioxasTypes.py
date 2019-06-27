'''
Created on 2017-02-10

@author: bergr
'''
from cls.utils.enum_utils import Enum

endstation_id_types = Enum('SPEC', 'IMAG')

spatial_type_prefix = Enum('ROI', 'SEG', 'PNT')

IMAGE_LXL = 100
IMAGE_PXP = 200

scan_status_types = Enum('STOPPED', 'RUNNING', 'PAUSED', 'DONE', 'ABORTED')
energy_scan_order_types = Enum('EV_THEN_POL', 'POL_THEN_EV')
#the following positioning modes for the sample are mutually exclusive, the sample positioning mode will be set 
#int the MAIN_OBJ configuration and used to select the positioners used for scanning samples
sample_positioning_modes = Enum('Goniometer', 'SampleXY', 'CoarseXY')
sample_fine_positioning_modes = Enum('Sample', 'Zoneplate')

#scan_panel_order = Enum('Detector_Scan','OSA_Scan','OSA_Focus_Scan','Focus_Scan','Point_Scan', 'Image_Scan', 'ZP_Image_Scan', 'Positioner_Scan', 'Line_Scan', 'Image_Scan_Mainobj')
#NOTE: that if a new scan pluggin is added to teh plugins directory there must be a corresponding entry into this enumeration so that
# its params page will appear in the gui scan toolbox
scan_panel_order = Enum('detector_scan', \
                    'positioner_scan')

scan_types = Enum('detector_image', \
                'osa_image', \
                'osa_focus', \
                'sample_focus', \
                'sample_point_spectra', \
                'sample_line_spectra', \
                'sample_image', \
                'sample_image_stack', \
                'generic_scan', \
                'zp_image_scan')


positioner_sub_types = Enum('SampleXY', 'GoniometerXY')
scan_sub_types = Enum('Point_by_Point', 'Line_Unidir')
scans_with_energy = [scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_POINT_SPECTRA, scan_types.GENERIC_SCAN]
image_types = Enum('focus', 'osafocus','image', 'line_plot')

image_scan_secids = Enum('SAMPLE_LXL', 'SAMPLE_PXP')


scan_image_types = {scan_types.DETECTOR_IMAGE: image_types.IMAGE, \
                scan_types.OSA_IMAGE: image_types.IMAGE, \
                scan_types.OSA_FOCUS: image_types.OSAFOCUS, \
                scan_types.SAMPLE_FOCUS: image_types.FOCUS, \
                scan_types.SAMPLE_IMAGE+IMAGE_LXL: image_types.IMAGE, \
                scan_types.SAMPLE_IMAGE+IMAGE_PXP: image_types.IMAGE, \
                scan_types.SAMPLE_IMAGE: image_types.IMAGE, \
                scan_types.SAMPLE_POINT_SPECTRA: image_types.LINE_PLOT, \
                scan_types.GENERIC_SCAN: image_types.LINE_PLOT, \
                scan_types.SAMPLE_LINE_SPECTRA: image_types.LINE_PLOT, \
                scan_types.ZP_IMAGE_SCAN+IMAGE_LXL: image_types.IMAGE, \
                scan_types.ZP_IMAGE_SCAN+IMAGE_PXP: image_types.IMAGE, \
                scan_types.ZP_IMAGE_SCAN: image_types.IMAGE, \
                scan_types.SAMPLE_IMAGE_STACK: image_types.IMAGE
                }

        
__all__ = ['SPATIAL_TYPE_PREFIX', 'TWO_D', 'SEG', 'PNT', scan_types, scans_with_energy]
