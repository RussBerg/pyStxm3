'''
Created on Sep 26, 2016

@author: bergr
'''
import os
from bcm.devices.device_names import *

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)


class CoarseGoniSSCAN(BaseScan):
    """ a scan for executing a detector point scan in X and Y, it takes an existing instance of an XYZScan class"""
    
    def __init__(self, main_obj=None):
        """
        __init__():
        
        :returns: None
        """
        super(CoarseGoniSSCAN, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), SPDB_XY, main_obj=MAIN_OBJ)

    
    def init_sscans(self):

        self.yScan = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, main_obj=MAIN_OBJ)
        self.xScan = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)

        self.cmd_file = '%s/goni_pxp.cmd' % self.script_dir
        #self.cmd_file_pv = MAIN_OBJ.device('%s:cmd_file' % self.scan_prefix)
        
        xmtr = MAIN_OBJ.device(DNM_GONI_X)
        ymtr = MAIN_OBJ.device(DNM_GONI_Y)
        
        self.xScan.set_positioner(1, xmtr)
        self.yScan.set_positioner(1, ymtr)
        
        self.scanlist = [self.xScan , self.yScan]
        self.mtr_list = [ xmtr , ymtr]
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device(DNM_GATE)
#         self.counter = MAIN_OBJ.device(DNM_COUNTER_APD)
#         self.shutter = MAIN_OBJ.device(DNM_SHUTTER)      
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.yScan)
        self.set_data_level_scan(self.yScan)
        self.set_btm_level_scan(self.xScan)
    
    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        self.set_on_counter_changed_func(self.on_x_y_counter_changed)
        self.set_on_scan_done_func(self.on_this_scan_done)

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        #stop gate and counter input tasks
        self.gate.stop()
        self.counter.stop()
        self.on_this_data_level_done()

        
    def configure(self, wdg_com, sp_id=0, line=True, restore=True, z_enabled=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param line=True: line=True description
        :type line=True: line=True type

        :param restore=True: restore=True description
        :type restore=True: restore=True type

        :param z_enabled=False: z_enabled=False description
        :type z_enabled=False: z_enabled=False type

        :returns: None
        """
        #use base configure x y motor scan
        self.busy_saving = False
        self.stack = False
        self.reload_base_scan_config()
        sim = (self.xScan.P1.get('description').find('SIM') > -1)
        #if( not SIMULATE_IMAGE_DATA or not sim):

        #self.configure_x_y_z_scan(sp_db, line=line, z_enabled=False)
        #self.data_shape = ('numE', 'numY', 'numX')
        self.configure_x_y_z_scan_LINEAR(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        
        self.move_zpxy_to_its_center()
        
        
    def on_this_data_level_done(self):
        """
        on_this_data_level_done(): description

        :returns: None
        """
        """
        this is an API slot that gets fired when the data level scan_done signal
        
        The final data dict should have the main keys of:
            all_data['SSCANS']      - all fields of each sscan record, this will be a list of sscans
            all_data['SCAN_CFG']    - all params from the GUI for this scan, center, range etc, also any flags such as XMCD=True that relate to how to execute this scan
            all_data['DATA']        - counter data collected during scan, for images this will be a 2d array, for point scans this will be a 1d array
            
        The goal of all_data dict is to write the dict out to disk in <data dir>/master.json. Once it has been recorded to disk the data recorder
        module can open it as a json object and export it based on the scan type so that it can pick and choose what to pull out and write to the header file.   
        
        """
        #_logger.debug('Detector: on_data_level_done:')
        self.on_x_y_scan_data_level_done()
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        
        
        