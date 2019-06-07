'''
Created on Sep 26, 2016

@author: bergr
'''

from cls.applications.bioXasIM.device_names import *

from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger

from cls.plotWidgets.utils import *


_logger = get_module_logger(__name__)


class DetectorSSCAN(BaseScan):
    """ a scan for executing a imageector point scan in X and Y, it takes an existing instance of an XYZScan class"""
    
    def __init__(self):
        """
        __init__():
        
        :returns: None
        """
        super(DetectorSSCAN, self).__init__('%s:image' % MAIN_OBJ.get_sscan_prefix(), SPDB_XY, main_obj=MAIN_OBJ)
        
    
    def init_sscans(self):
        self.scan_prefix = MAIN_OBJ.get_sscan_prefix()
        self.yScan = SScanClass('%s:image:scan2' % self.scan_prefix, SPDB_Y, main_obj=MAIN_OBJ)
        self.xScan = SScanClass('%s:image:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)
        
        xmtr = MAIN_OBJ.device(DNM_DETECTOR_X)
        ymtr = MAIN_OBJ.device(DNM_DETECTOR_Y)
        
        self.xScan.set_positioner(1, xmtr)
        self.yScan.set_positioner(1, ymtr)
        
        self.scanlist = [self.xScan , self.yScan]
        self.mtr_list = [ xmtr , ymtr]
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.yScan)
        self.set_data_level_scan(self.yScan)
        self.set_btm_level_scan(self.xScan)
    
    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        #self.set_on_counter_changed_func(self.on_x_y_counter_changed)
        self.set_on_counter_changed_func(self.on_det_counter_changed)
        self.set_on_scan_done_func(self.on_this_scan_done)    
            
    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        #stop gate and counter input tasks
        #self.gate.stop()
        #self.counter.stop()
        self.on_this_data_level_done()
        #self.save_master()
        
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
        self.yScan.reload_base_scan_config()
#        sim = (self.xScan.P1.get('description').find('SIM') > -1)
#        #if( not SIMULATE_IMAGE_DATA or not sim):
#         if(not sim):
#             MAIN_OBJ.device( DNM_DX_AUTO_DISABLE_POWER ).put(0) 
#             MAIN_OBJ.device( DNM_DY_AUTO_DISABLE_POWER ).put(0)
        self.configure_x_y_z_scan_LINEAR(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        
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
        #MAIN_OBJ.device( DNM_DX_AUTO_DISABLE_POWER ).put(1) #enable again 
        #MAIN_OBJ.device( DNM_DY_AUTO_DISABLE_POWER ).put(1)
        self.on_x_y_scan_data_level_done()    
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        #set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        pass

    #def on_x_y_counter_changed(self, row, (point, val)):
    def on_det_counter_changed(self, val):

        """
        on_x_y_counter_changed(): Used in FocusScanClass, OsaFocusScanClass and OsaScanClass

        :param row: row description
        :type row: row type

        :param (point: (point description
        :type (point: (point type

        :param val): val) description
        :type val): val) type

        :returns: None
        """

#        global SIMULATE_IMAGE_DATA, SIM_DATA
#        print dat
	#here row, point and val are what are passed to this handler from the counter signal
	row = 0	
	point = 0
	dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(point)
        dct[CNTR2PLOT_VAL] = int(val)
        self.sigs.changed.emit(dct)

#         if(SIMULATE_IMAGE_DATA):
#             val = SIM_DATA[row][point]
#
#         top_lvl_npts = self.top_level_scan.get('NPTS')
#         #print 'on_x_y_counter_changed: [%d] row=%d point=%d val=%d' % (top_lvl_npts, row, point, val)
#         if((self.scan_type ==  scan_types.OSA_FOCUS) or (self.scan_type ==  scan_types.SAMPLE_FOCUS)):
#             nptsy = self.numZ
#         else:
#             nptsy = self.numY
#
#         _evidx = self.get_evidx()
#         if(point >= self.numX):
#             #this is the row switch extra point so drop it
#             #print 'scan_counter_changed: SKIPPED [%d, %d] = %d' % (row, point, val)
#             return
#         if(point > -1):
#             #print 'on_x_y_counter_changed: _evidx=%d' % _evidx
#             if(row < top_lvl_npts):
#                 self.data[_evidx, row,point] = val
# #                 dct = {}
# #                 dct['sp_id'] = self.get_spatial_id()
# #                 dct['img_idx'] = _evidx
# #                 dct['row'] = row
# #                 dct['col'] = point
# #                 dct['val'] = val
#                 dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#                 dct[CNTR2PLOT_ROW] = int(row)
#                 dct[CNTR2PLOT_COL] = int(point)
#                 dct[CNTR2PLOT_VAL] = int(val)
#                 #self.sigs.changed.emit(row, (point, val))
#                 self.sigs.changed.emit(dct)
#
#             if(row >= nptsy):
#                 self.incr_evidx()
#
        
