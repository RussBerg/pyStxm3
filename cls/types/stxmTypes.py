'''
Created on 2013-08-02

@author: bergr
'''
from cls.utils.enum_utils import Enum

endstation_id_types = Enum('AMBIENT', 'UHV')

# the following definitions are taken from the NXstxm data/stxm_scan_type section
#dtype = ['sample point spectrum', 'sample line spectrum', 'sample image' ,\
#			'sample image stack' ,'sample focus', 'osa image', 'osa focus', 'detector image',\
#			'generic scan']


spatial_type_prefix = Enum('ROI', 'SEG', 'PNT')

IMAGE_LXL = 100
IMAGE_PXP = 200

scan_status_types = Enum('STOPPED', 'RUNNING', 'PAUSED', 'DONE', 'ABORTED')
energy_scan_order_types = Enum('EV_THEN_POL', 'POL_THEN_EV')
#the following positioning modes for the sample are mutually exclusive, the sample positioning mode will be set 
#int the MAIN_OBJ configuration and used to select the positioners used for scanning samples
sample_positioning_modes = Enum('Coarse', 'Goniometer')
sample_fine_positioning_modes = Enum('SampleFine', 'Zoneplate')
scanning_mode = Enum('COARSE_SAMPLEFINE', 'GONI_ZONEPLATE', 'COARSE_ZONEPLATE')

#scan_panel_order = Enum('Detector_Scan','OSA_Scan','OSA_Focus_Scan','Focus_Scan','Point_Scan', 'Image_Scan', 'ZP_Image_Scan', 'Positioner_Scan', 'Line_Scan', 'Image_Scan_Mainobj')
#NOTE: that if a new scan pluggin is added to teh plugins directory there must be a corresponding entry into this enumeration so that
# its params page will appear in the gui scan toolbox
scan_panel_order = Enum('detector_scan', \
					'osa_scan', \
					'osa_focus_scan', \
					'coarse_image_scan', \
					'coarse_goni_image_scan', \
					'image_scan', \
					'tomography_scan', \
					'focus_scan', \
					'point_scan', \
					'line_scan', \
					'positioner_scan', \
					'pattern_gen_scan', \
					'ptychography_scan'
					)

scan_types = Enum('detector_image', \
				'osa_image', \
				'osa_focus', \
				'sample_focus', \
				'sample_point_spectra', \
				'sample_line_spectra', \
				'sample_image', \
				'sample_image_stack', \
				'generic_scan', \
				'coarse_image_scan', \
				'coarse_goni_scan', \
				'tomography_scan', \
				'pattern_gen_scan', \
				'ptychography_scan')

spectra_type_scans = [scan_types.SAMPLE_POINT_SPECTRA, scan_types.GENERIC_SCAN]
image_type_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS , scan_types.SAMPLE_FOCUS , scan_types.SAMPLE_LINE_SPECTRA , scan_types.SAMPLE_IMAGE , scan_types.SAMPLE_IMAGE_STACK , \
					scan_types.COARSE_IMAGE_SCAN, scan_types.COARSE_GONI_SCAN, scan_types.TOMOGRAPHY_SCAN, scan_types.PATTERN_GEN_SCAN, scan_types.PTYCHOGRAPHY_SCAN]
single_entry_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.OSA_FOCUS , scan_types.SAMPLE_FOCUS , scan_types.SAMPLE_LINE_SPECTRA , scan_types.SAMPLE_IMAGE , scan_types.COARSE_IMAGE_SCAN, \
					  scan_types.COARSE_GONI_SCAN, scan_types.GENERIC_SCAN, scan_types.PTYCHOGRAPHY_SCAN]
multi_entry_scans = [scan_types.SAMPLE_IMAGE_STACK , scan_types.SAMPLE_POINT_SPECTRA, scan_types.TOMOGRAPHY_SCAN]

two_posner_scans = [scan_types.DETECTOR_IMAGE, scan_types.OSA_IMAGE, scan_types.COARSE_IMAGE_SCAN,scan_types.COARSE_GONI_SCAN , scan_types.SAMPLE_IMAGE, scan_types.GENERIC_SCAN, scan_types.PTYCHOGRAPHY_SCAN]
three_posner_scans = [scan_types.OSA_FOCUS , scan_types.SAMPLE_FOCUS, scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_POINT_SPECTRA, scan_types.TOMOGRAPHY_SCAN,  scan_types.SAMPLE_IMAGE_STACK]

positioner_sub_types = Enum('SampleXY', 'GoniometerXY')
#scan_sub_types = Enum( 'Line_Unidir','Point_by_Point')
scan_sub_types = Enum( 'Point_by_Point','Line_Unidir')
scans_with_energy = [scan_types.SAMPLE_IMAGE, scan_types.SAMPLE_POINT_SPECTRA, scan_types.GENERIC_SCAN]
image_types = Enum('focus', 'osafocus','image', 'line_plot')

image_scan_secids = Enum('SAMPLE_LXL', 'SAMPLE_PXP', 'TOMO')


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
				scan_types.COARSE_IMAGE_SCAN+IMAGE_LXL: image_types.IMAGE, \
				scan_types.COARSE_IMAGE_SCAN+IMAGE_PXP: image_types.IMAGE, \
				scan_types.COARSE_IMAGE_SCAN: image_types.IMAGE, \
				scan_types.SAMPLE_IMAGE_STACK: image_types.IMAGE, \
				scan_types.TOMOGRAPHY_SCAN: image_types.IMAGE, \
				scan_types.COARSE_GONI_SCAN: image_types.IMAGE, \
				scan_types.PATTERN_GEN_SCAN: image_types.IMAGE, \
				scan_types.PTYCHOGRAPHY_SCAN: image_types.IMAGE
				}

		
__all__ = ['SPATIAL_TYPE_PREFIX', 'TWO_D', 'SEG', 'PNT', scan_types, scans_with_energy]
