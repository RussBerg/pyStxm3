'''
This file loader.py is a standard file that must be in the directory for a scan plugin to be picked up, the two
requirements are that the following must be defined:
    mod_file = 'coarse_image_scan.py'           the module filename of the scan plugin widget
    mod_classname = 'CoarseImageScanParam'      the class in the mod_file that has all the UI stuff

'''
mod_file = 'osa_focus_scan.py'
mod_classname = 'OsaFocusScanParam'
