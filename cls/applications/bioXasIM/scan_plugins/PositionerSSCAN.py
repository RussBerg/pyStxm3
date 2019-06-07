'''
Created on Sep 26, 2016

@author: bergr
'''

from cls.applications.bioXasIM.device_names import *

from cls.applications.bioXasIM.bl07ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan, SIMULATE_IMAGE_DATA, SIM_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get
from cls.utils.log import get_module_logger

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)


class PositionerSSCAN(BaseScan):
    """ a scan for executing a positioner line pxp scan in X, """
    
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(PositionerSSCAN, self).__init__('%s:image' % MAIN_OBJ.get_sscan_prefix(), SPDB_X, main_obj=MAIN_OBJ)

    
    def init_sscans(self):
        self.scan_prefix = MAIN_OBJ.get_sscan_prefix()
        
        self.xScan = SScanClass('%s:image:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)
        
        self.scanlist = [ self.xScan ]
        self.mtr_list = []
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device('Gate')
#         self.counter = MAIN_OBJ.device('Counter')
#         self.shutter = MAIN_OBJ.device('Shutter')  
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.xScan)
        self.set_data_level_scan(self.xScan)
    
    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        self.set_on_counter_changed_func(self.on_this_counter_changed)

        self.set_on_data_level_done_func(self.on_this_data_level_done)
        self.set_on_scan_done_func(self.on_this_scan_done)
        
    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        #stop gate and counter input tasks
#        self.gate.stop()
#        self.counter.stop()
        self.on_this_data_level_done()

        
    def configure(self, wdg_com, sp_id=0, line=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param sp_id: sp_id description
        :type sp_id: sp_id type

        :param line=False: line=False description
        :type line=False: line=False type

        :returns: None
        """
        #use base configure x y motor scan
        self.stack = False
        self.xScan.reload_base_scan_config()
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.is_point_spec = True
        x_roi = dct_get(self.sp_db, SPDB_X)
        self.xmtr = MAIN_OBJ.device(x_roi[POSITIONER])
        self.xScan.set_positioner(1, self.xmtr)
        
        #the xScan.mtr must be set before calling configure_x_scan_LINEAR()
        #self.data_shape = ('numX', 1, 1)
        self.xScan.put('P1PV', self.xmtr.get_name() + '.VAL')
        self.configure_x_scan_LINEAR(wdg_com, sp_id=sp_id, line=False)
        
        self.move_zpxy_to_its_center()
        
        self.mtr_list = [ self.xmtr ]
        self.set_sscan_rec()
    
    def set_sscan_rec(self):
        """
        set_sscan_rec(): description

        :returns: None
        """
        #reset total point counter
        self.ttl_pnts = 0
        #X
        #self.xScan.put('P1PV', self.xmtr.get_name() + '.VAL')
        self.xScan.put('NPTS', self.x_roi[NPOINTS])
        self.xScan.put('P1SP', self.x_roi[START])
        self.xScan.put('P1EP', self.x_roi[STOP])
        
        
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        # add one so that the first one which will endup being 0 because of the ediff calc will be removed
        pass
        #set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        #self.gate.start()
        #self.counter.start()
        
    #def on_this_counter_changed(self, row, (point, val)):
    def on_this_counter_changed(self, dat):
        """
        on_this_counter_changed(): description

        :param row: row description
        :type row: row type

        :param (point: (point description
        :type (point: (point type

        :param val): val) description
        :type val): val) type

        :returns: None
        """
        """
        
        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
            dct[CNTR2PLOT_SP_ID] = self.sp_ids[sp_cntr]
            dct[CNTR2PLOT_ROW] = sp_cntr
            dct[CNTR2PLOT_COL] = ev
            dct[CNTR2PLOT_VAL] = point_val
        This is a slot that is connected to the counters changed signal        
        """
        #global SIMULATE_IMAGE_DATA, SIM_DATA
        print(dat)
        return

#         if(SIMULATE_IMAGE_DATA):
#             val = SIM_DATA[row][point]
#
#         top_lvl_npts = self.top_level_scan.get('NPTS')
#         #print 'on_generic_counter_changed: [%d] row=%d point=%d val=%d' % (top_lvl_npts, row, point, val)
#         if(point >= self.numX):
#             #this is the row switch extra point so drop it
#             #print 'scan_counter_changed: SKIPPED [%d, %d] = %d' % (row, point, val)
#             return
#         if(point > -1):
#             #print 'on_x_y_counter_changed: _evidx=%d' % _evidx
#             if(row < top_lvl_npts):
#                 self.data[int(point)] = val
# #                 dct = {}
# #                 dct['img_idx'] = 0
# #                 dct['row'] = row
# #                 dct['col'] = self.x_roi[SETPOINTS][point]
# #                 dct['val'] = val
#
#                 dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#                 dct[CNTR2PLOT_SP_ID] = self._current_sp_id
#                 dct[CNTR2PLOT_ROW] = row
#                 dct[CNTR2PLOT_COL] = self.x_roi[SETPOINTS][point]
#                 dct[CNTR2PLOT_VAL] = val
#
#                 self.sigs.changed.emit(dct)
        
        
    
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
        #_logger.debug('Generic: on_data_level_done:')
        self.save_hdr()
        self.hdr.remove_tmp_file()
        
