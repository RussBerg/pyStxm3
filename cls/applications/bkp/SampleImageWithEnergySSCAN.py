'''
Created on Sep 26, 2016

@author: bergr
'''
import os
from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ

from cls.scanning.BaseScan import BaseScan, SIM_SPEC_DATA, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan
from cls.types.stxmTypes import scan_types, scan_sub_types, \
                                        energy_scan_order_types, sample_positioning_modes
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)

class SampleImageWithEnergySSCAN(BaseScan):
    '''
    This class 
    '''
    #_chk_for_more_evregions = QtCore.pyqtSignal(object)
    
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(SampleImageWithEnergySSCAN, self).__init__('%sstxm'% MAIN_OBJ.get_sscan_prefix(),'SAMPLEXY_EV', main_obj=MAIN_OBJ)

    
    def init_sscans(self):

        self.cb_idxs = []
        self.ttl_pnts = 0
        self.final_data_dir = None
        
        self.setupScan = SScanClass('%s:scan5' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
        self._scan4 = SScanClass('%s:scan4' % self.scan_prefix, SPDB_EV_EV, main_obj=MAIN_OBJ)
        self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_EV_POL, main_obj=MAIN_OBJ)
        self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, posner=MAIN_OBJ.device(DNM_SAMPLE_Y), main_obj=MAIN_OBJ)
        self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, posner=MAIN_OBJ.device(DNM_SAMPLE_X), main_obj=MAIN_OBJ)
        #self.evScan = SScanClass('%simage:scan4' % self.scan_prefix, SPDB_EV_EV)
        #self.cmd_file_pv = MAIN_OBJ.device('%s:cmd_file' % self.scan_prefix)

        self.evScan = self._scan4
        self.evScan.set_positioner(1, MAIN_OBJ.device(DNM_ENERGY))
        
        #self.polScan = SScanClass('%simage:scan3' % self.scan_prefix, SPDB_EV_POL)
        self.polScan = self._scan3
        self.polScan.set_positioner(1, MAIN_OBJ.device(DNM_EPU_POLARIZATION))
        self.polScan.set_positioner(2, MAIN_OBJ.device(DNM_EPU_OFFSET))
        self.polScan.set_positioner(3, MAIN_OBJ.device(DNM_EPU_ANGLE))
        
        ev_pol_lxl = {}
        ev_pol_lxl['cmd_file'] = '%s/image_ev_then_pol.cmd'  % self.script_dir
        ev_pol_lxl['ev_section_id'] = SPDB_EV_EV
        ev_pol_lxl['pol_section_id'] = SPDB_EV_POL
        ev_pol_lxl['ev_scan'] = self._scan4 
        ev_pol_lxl['pol_scan'] = self._scan3 
        ev_pol_lxl['y_scan'] = self._scan2
        ev_pol_lxl['x_scan'] = self._scan1
        ev_pol_lxl['xy_scan'] = None
        ev_pol_lxl['top_lvl_scan'] = self._scan4
        ev_pol_lxl['data_lvl_scan'] = self._scan2
        ev_pol_lxl['btm_lvl_scan'] = self._scan1
        ev_pol_lxl['on_counter_changed'] = self.on_sample_scan_counter_changed
#        ev_pol_lxl['on_data_level_done'] = self.on_save_sample_image
        ev_pol_lxl['on_data_level_done'] = self.on_sampleimage_data_level_done
        ev_pol_lxl['on_abort_scan'] = self.on_abort_scan
        ev_pol_lxl['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_lxl['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_lxl['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
            
        
        pol_ev_lxl = {}
        pol_ev_lxl['cmd_file'] = '%s/image_pol_then_ev.cmd'  % self.script_dir
        pol_ev_lxl['pol_section_id'] = SPDB_EV_POL
        pol_ev_lxl['ev_section_id'] = SPDB_EV_EV
        pol_ev_lxl['pol_scan'] = self._scan4 
        pol_ev_lxl['ev_scan'] = self._scan3 
        pol_ev_lxl['y_scan'] = self._scan2
        pol_ev_lxl['x_scan'] = self._scan1
        pol_ev_lxl['xy_scan'] = None
        pol_ev_lxl['top_lvl_scan'] = self._scan4
        pol_ev_lxl['data_lvl_scan'] = self._scan2
        pol_ev_lxl['btm_lvl_scan'] = self._scan1
        pol_ev_lxl['on_counter_changed'] = self.on_sample_scan_counter_changed
        pol_ev_lxl['on_data_level_done'] = self.on_sampleimage_data_level_done
        pol_ev_lxl['on_abort_scan'] = self.on_abort_scan
        pol_ev_lxl['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_lxl['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_lxl['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]

        #E712 Wavegenerator
        ev_pol_lxl_wg = {}
        ev_pol_lxl_wg['cmd_file'] = '%s/image_ev_then_pol_wg.cmd'  % self.script_dir
        ev_pol_lxl_wg['ev_section_id'] = SPDB_EV_EV
        ev_pol_lxl_wg['pol_section_id'] = SPDB_EV_POL
        ev_pol_lxl_wg['ev_scan'] = self._scan3
        ev_pol_lxl_wg['pol_scan'] = self._scan2
        ev_pol_lxl_wg['y_scan'] = self._scan1
        ev_pol_lxl_wg['x_scan'] = self._scan1
        ev_pol_lxl_wg['xy_scan'] = None
        ev_pol_lxl_wg['top_lvl_scan'] = self._scan3
        ev_pol_lxl_wg['data_lvl_scan'] = self._scan1
        ev_pol_lxl_wg['btm_lvl_scan'] = self._scan1
        ev_pol_lxl_wg['on_counter_changed'] = self.on_sample_scan_counter_changed
        #        ev_pol_lxl['on_data_level_done'] = self.on_save_sample_image
        ev_pol_lxl_wg['on_data_level_done'] = self.on_sampleimage_data_level_done
        ev_pol_lxl_wg['on_abort_scan'] = self.on_abort_scan
        ev_pol_lxl_wg['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_lxl_wg['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_lxl_wg['scanlist'] = [self._scan1, self._scan2, self._scan3]
        
        ev_pol_pxp = {}
        ev_pol_pxp['cmd_file'] = '%s/image_ev_then_pol_pxp.cmd'  % self.script_dir
        ev_pol_pxp['ev_section_id'] = SPDB_EV_EV
        ev_pol_pxp['pol_section_id'] = SPDB_EV_POL
        ev_pol_pxp['ev_scan'] = self._scan3 
        ev_pol_pxp['pol_scan'] = self._scan2 
        ev_pol_pxp['xy_scan'] = self._scan1
        ev_pol_pxp['x_scan'] = None
        ev_pol_pxp['y_scan'] = None
        ev_pol_pxp['top_lvl_scan'] = self._scan3
        ev_pol_pxp['data_lvl_scan'] = self._scan1
        ev_pol_pxp['btm_lvl_scan'] = None
        ev_pol_pxp['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_pxp['on_data_level_done'] = self.on_sampleimage_data_level_done
        ev_pol_pxp['on_abort_scan'] = self.on_abort_scan
        ev_pol_pxp['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pxp['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_pxp['scanlist'] = [ self._scan1 , self._scan2, self._scan3]
        
        
        ev_pol_pxp_2recs = {}
        ev_pol_pxp_2recs['cmd_file'] = '%s/image_evpol_pxp_2recs.cmd'  % self.script_dir
        ev_pol_pxp_2recs['ev_section_id'] = SPDB_EV_EV
        ev_pol_pxp_2recs['pol_section_id'] = SPDB_EV_POL
        ev_pol_pxp_2recs['ev_scan'] = self._scan4 
        ev_pol_pxp_2recs['pol_scan'] = self._scan3 
        ev_pol_pxp_2recs['xy_scan'] = None
        ev_pol_pxp_2recs['y_scan'] = self._scan2 
        ev_pol_pxp_2recs['x_scan'] = self._scan1
        ev_pol_pxp_2recs['top_lvl_scan'] = self._scan4
        ev_pol_pxp_2recs['data_lvl_scan'] = self._scan2
        ev_pol_pxp_2recs['btm_lvl_scan'] = self._scan1
        ev_pol_pxp_2recs['on_counter_changed'] = self.on_sample_scan_counter_changed
        ev_pol_pxp_2recs['on_data_level_done'] = self.on_sampleimage_data_level_done
        ev_pol_pxp_2recs['on_abort_scan'] = self.on_abort_scan
        ev_pol_pxp_2recs['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pxp_2recs['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_pxp_2recs['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
        
        pol_ev_pxp = {}
        pol_ev_pxp['cmd_file'] = '%s/image_pol_then_ev_pxp.cmd'  % self.script_dir
        pol_ev_pxp['pol_section_id'] = SPDB_EV_POL
        pol_ev_pxp['ev_section_id'] = SPDB_EV_EV
        pol_ev_pxp['pol_scan'] = self._scan3
        pol_ev_pxp['ev_scan'] = self._scan2 
        pol_ev_pxp['xy_scan'] = self._scan1
        pol_ev_pxp['x_scan'] = None
        pol_ev_pxp['y_scan'] = None
        pol_ev_pxp['top_lvl_scan'] = self._scan3
        pol_ev_pxp['data_lvl_scan'] = self._scan1
        pol_ev_pxp['btm_lvl_scan'] = None
        pol_ev_pxp['on_counter_changed'] = self.on_sample_scan_counter_changed
        pol_ev_pxp['on_data_level_done'] = self.on_sampleimage_data_level_done
        pol_ev_pxp['on_abort_scan'] = self.on_abort_scan
        pol_ev_pxp['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_pxp['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_pxp['scanlist'] = [ self._scan1 , self._scan2, self._scan3]
        
        ev_pol_pnt_spec = {} 
        ev_pol_pnt_spec['cmd_file'] = '%s/point_spec_V2.cmd'  % self.script_dir
        ev_pol_pnt_spec['ev_section_id'] = SPDB_EV_EV
        ev_pol_pnt_spec['pol_section_id'] = SPDB_EV_POL
        ev_pol_pnt_spec['y_scan'] = None
        ev_pol_pnt_spec['x_scan'] = None
        ev_pol_pnt_spec['ev_scan'] = self._scan3
        ev_pol_pnt_spec['pol_scan'] = self._scan2
        ev_pol_pnt_spec['xy_scan'] = self._scan1
        ev_pol_pnt_spec['top_lvl_scan'] = self._scan3
        ev_pol_pnt_spec['data_lvl_scan'] = self._scan2
        ev_pol_pnt_spec['btm_lvl_scan'] = self._scan1
        ev_pol_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        ev_pol_pnt_spec['on_data_level_done'] = self.on_data_level_done
        ev_pol_pnt_spec['on_abort_scan'] = self.on_abort_scan
        ev_pol_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        ev_pol_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        ev_pol_pnt_spec['scanlist'] = [ self._scan1 , self._scan2, self._scan3]
        
        goni_ev_pol_pnt_spec = {} 
        goni_ev_pol_pnt_spec['cmd_file'] = '%s/goni_point_spec.cmd'  % self.script_dir
        goni_ev_pol_pnt_spec['ev_section_id'] = SPDB_EV_EV
        goni_ev_pol_pnt_spec['pol_section_id'] = SPDB_EV_POL
        goni_ev_pol_pnt_spec['y_scan'] = None
        goni_ev_pol_pnt_spec['x_scan'] = None
        goni_ev_pol_pnt_spec['ev_scan'] = self._scan3
        goni_ev_pol_pnt_spec['pol_scan'] = self._scan2
        goni_ev_pol_pnt_spec['xy_scan'] = self._scan1
        goni_ev_pol_pnt_spec['top_lvl_scan'] = self._scan3
        goni_ev_pol_pnt_spec['data_lvl_scan'] = self._scan2
        goni_ev_pol_pnt_spec['btm_lvl_scan'] = self._scan1
        goni_ev_pol_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        goni_ev_pol_pnt_spec['on_data_level_done'] = self.on_data_level_done
        goni_ev_pol_pnt_spec['on_abort_scan'] = self.on_abort_scan
        goni_ev_pol_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        goni_ev_pol_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        goni_ev_pol_pnt_spec['scanlist'] = [ self._scan1 , self._scan2, self._scan3]
        
        pol_ev_pnt_spec = {}
        pol_ev_pnt_spec['cmd_file'] = '%s/pol_ev_pnt_spec.cmd'  % self.script_dir
        pol_ev_pnt_spec['ev_section_id'] = SPDB_EV_EV
        pol_ev_pnt_spec['pol_section_id'] = SPDB_EV_POL
        pol_ev_pnt_spec['y_scan'] = self._scan4
        pol_ev_pnt_spec['x_scan'] = self._scan3
        pol_ev_pnt_spec['pol_scan'] = self._scan2
        pol_ev_pnt_spec['ev_scan'] = self._scan1 
        pol_ev_pnt_spec['xy_scan'] = None
        pol_ev_pnt_spec['top_lvl_scan'] = self._scan4
        pol_ev_pnt_spec['data_lvl_scan'] = self._scan2
        pol_ev_pnt_spec['btm_lvl_scan'] = self._scan1
        pol_ev_pnt_spec['on_counter_changed'] = self.on_point_spec_scan_counter_changed
        pol_ev_pnt_spec['on_data_level_done'] = self.on_data_level_done
        pol_ev_pnt_spec['on_abort_scan'] = self.on_abort_scan
        pol_ev_pnt_spec['on_scan_done'] = self.chk_for_more_evregions
        pol_ev_pnt_spec['on_dev_cfg'] = self.on_this_dev_cfg
        pol_ev_pnt_spec['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
        

        
        self.cmdfile_parms = {}
        self.cmdfile_parms['ev_pol_lxl'] = ev_pol_lxl
        self.cmdfile_parms['pol_ev_lxl'] = pol_ev_lxl
        self.cmdfile_parms['ev_pol_pxp'] = ev_pol_pxp
        self.cmdfile_parms['pol_ev_pxp'] = pol_ev_pxp
        self.cmdfile_parms['ev_pol_pnt_spec'] = ev_pol_pnt_spec
        self.cmdfile_parms['pol_ev_pnt_spec'] = pol_ev_pnt_spec
        self.cmdfile_parms['goni_ev_pol_pnt_spec'] = goni_ev_pol_pnt_spec
        self.cmdfile_parms['ev_pol_pxp_2recs'] = ev_pol_pxp_2recs

        self.cmdfile_parms['ev_pol_lxl_wg'] = ev_pol_lxl_wg
        
        self.xyScan = self._scan1
        
        self.lxl_yScan = self._scan2
        self.lxl_xScan = self._scan1
        
        self.pxp_yScan = self._scan2
        self.pxp_xScan = self._scan1
        
        self.pnt_yScan = self._scan2
        self.pnt_xScan = self._scan1
    
    def on_sampleimage_data_level_done(self):
        #_logger.debug('SampleImageWithEnergySSCAN: SampleImageWithEnergySSCAN() called')
        #self.pause()
        self.on_save_sample_image()
        if(self.stack):
            self.update_data(stack=True)
        self.incr_consecutive_scan_idx()
        #self.resume()
        
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device(DNM_GATE)
#         self.counter = MAIN_OBJ.device(DNM_COUNTER_APD)
#         self.shutter = MAIN_OBJ.device(DNM_SHUTTER)  
    
    def optimize_sample_line_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly 
        mprove the performance if it is optimized.
         
        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)
        
        if(self.x_roi[SCAN_RES] == 'COARSE'):
            self.xScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
        else:
            self.xScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)    
        
        if(self.y_roi[SCAN_RES] == 'COARSE'):
            self.yScan.put('PDLY', c_scan2_pdly)
            fy_done.put(c_fy_force_done)
        else:
            self.yScan.put('PDLY', f_scan2_pdly)
            fy_done.put(f_fy_force_done)    
    
    
    def optimize_sample_point_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly 
        mprove the performance if it is optimized.
         
        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)
        
        if(self.x_roi[SCAN_RES] == 'COARSE'):
            #self.xyScan.put('PDLY', c_scan1_pdly)
            self.xScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
        else:
            #self.xyScan.put('PDLY', f_scan1_pdly)
            self.xScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)    
        
        if(self.y_roi[SCAN_RES] == 'COARSE'):
            self.yScan.put('PDLY', c_scan2_pdly)
            fy_done.put(c_fy_force_done)
        else:
            self.yScan.put('PDLY', f_scan2_pdly)
            fy_done.put(f_fy_force_done) 
        
#     def optimize_sample_pointspec_scan(self):
#         '''
#         To be implemented by the inheriting class
#         This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
#         and any other settings required to optimize the scan for speed.
#         Typically this is used by the scans that move the fine piezo stages as their status response can greatly 
#         mprove the performance if it is optimized.
#          
#         appConfig.get_value('SAMPLE_IMAGE', 'whatever')
#         c_scan1_pdly=0.0
#         c_scan2_pdly=0.0
#         f_scan2_pdly=0.0
#         f_scan1_pdly=0.15
#         # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
#         f_fx_force_done=2
#         f_fy_force_done=1
#         '''
#         appConfig.update()
#         c_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan1_pdly'))
#         c_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan2_pdly'))
#         f_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan1_pdly'))
#         f_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan2_pdly'))
#         c_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fx_force_done'))
#         c_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fy_force_done'))
#         f_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fx_force_done'))
#         f_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fy_force_done'))
#         fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
#         fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)
#         
#         if(self.x_roi[SCAN_RES] == 'COARSE'):
#             self.xScan.put('PDLY', c_scan1_pdly)
#             fx_done.put(c_fx_force_done)
#         else:
#             self.xScan.put('PDLY', f_scan1_pdly)
#             fx_done.put(f_fx_force_done)    
#         
#         if(self.y_roi[SCAN_RES] == 'COARSE'):
#             self.yScan.put('PDLY', c_scan2_pdly)
#             fy_done.put(c_fy_force_done)
#         else:
#             self.yScan.put('PDLY', f_scan2_pdly)
#             fy_done.put(f_fy_force_done)    
    
    def optimize_sample_pointspec_scan(self):
        '''
        To be implemented by the inheriting class
        This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
        and any other settings required to optimize the scan for speed.
        Typically this is used by the scans that move the fine piezo stages as their status response can greatly 
        mprove the performance if it is optimized.
         
        appConfig.get_value('SAMPLE_IMAGE', 'whatever')
        c_scan1_pdly=0.0
        c_scan2_pdly=0.0
        f_scan2_pdly=0.0
        f_scan1_pdly=0.15
        # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
        f_fx_force_done=2
        f_fy_force_done=1
        '''
        appConfig.update()
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan2_pdly'))
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan2_pdly'))
        c_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fy_force_done'))
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)
        
        if(self.x_roi[SCAN_RES] == 'COARSE'):
            self.xyScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
            fy_done.put(c_fy_force_done)
        else:
            self.xyScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)
            fy_done.put(f_fy_force_done)    
        
                
    def on_abort_scan(self):
        """
        on_abort_scan(): description

        :returns: None
        """
        self._abort = True
        
    def validate_scan_assignments(self):
        """ a simple checker to verify that the scans are assigned to the correct epics sscan records
        """
        
        pass_tst = True
        if(self.scan_type == scan_types.SAMPLE_POINT_SPECTRA):
            if(self.evScan.get_name() != '%s:scan3' % self.scan_prefix):
                pass_tst = False
            if(self.polScan.get_name() != '%s:scan2' % self.scan_prefix):
                pass_tst = False
            if(self.xyScan.get_name() != '%s:scan1' % self.scan_prefix):
                pass_tst = False
        return(pass_tst)
    
    def configure(self, wdg_com, sp_id=0, ev_idx=0, line=True, block_disconnect_emit=False):
        """
        configure(): This is the configure routine that is required to be defined by every scan plugin. the main goal of the configure function is to 
            - extract into member variables the scan param data from the wdg_com (widget communication) dict
            - configure the sample motors for the correct Mode for the upcoming scan
            - reset any relevant member variable counters
            - decide if it is a line by line, point by point or point spectrum scan
            - set the optimization function for this scan (which is used later to fine tune some key params of the sscan record before scan)
            - decide if this is a goniometer scan and set a flag accordingly
            - set the start/stop/npts etc fields of the relevant sscan records for a line or point scan by calling either:
                set_ImageLineScan_line_sscan_rec() or set_ImageLineScan_point_sscan_rec()
            - determine the positioners that will be used in this scan (they depend on the size of the scan range, coarse or fine etc)
            - call either config_for_goniometer_scan() or config_for_sample_holder_scan() depending on if a goniometer scan or not
            - create the numpy array in self.data by calling config_hdr_datarecorder()
            - then call final_setup() which must be called at the end of every configure() function 

        :param wdg_com: wdg_com is a "widget Communication dictionary" and it is used to relay information to/from widgets regarding current regions of interest
        :type wdg_com: wdg_com is a dictionary comprised of 2 keys: WDGCOM_CMND and SPDB_SPATIAL_ROIS, both of which are strings defined in roi_dict_defs.py
                WDGCOM_CMND       : is a command that identifys what should be done with the rois listed in the next field
                SPDB_SPATIAL_ROIS : is a list of spatial roi's or spatial databases (sp_db)

        :param sp_id: sp_id is the "spatial ID" of the sp_db
        :type sp_id: integer

        :param ev_idx: ev_idx is the index into the e_rois[] list of energy regions of interest, this configure() function could be called again repeatedly if there are more than one
                energy regions of interest, this index is the index into that list, when the scan is first configured/called the index is always the first == 0
        :type ev_idx: integer

        :param line: line is a boolean flag indicating if the scan to be configured is a line by line scan or not
        :type line: bool
        
        :param block_disconnect_emit: because configure() can be called repeatedly by check_more_spatial_regions() I need to be able to control
                how the main GUI will react to a new scan being executed in succession, this flag if False will not blocking the emission of the 'disconnect' signals signal
                and if True it will block teh emission of the 'disconnect' that the main GUI is listening to
        :type block_disconnect_emit: bool

        :returns: None
        
        """
        _logger.info('\n\nSampleImageWithEnergy: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        #initial setup and retrieval of common scan information
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_ids = list(self.sp_rois.keys()) 
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()
        
        self.update_roi_member_vars(self.sp_db)

        #dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))
        # the sample motors have different modes, make a call to handle that they are setup correctly for this scan
        self.configure_sample_motors_for_scan()

        if(ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            self.reset_pnt_spec_spid_idx()
            self.final_data_dir = None
        
        #get the energy and EOU related setpoints
        e_roi = self.e_rois[ev_idx]
        self.setpointsDwell = dct_get(e_roi, 'DWELL')
        #self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, 'EPU_POL_PNTS')
        self.setpointsOff = dct_get(e_roi, 'EPU_OFF_PNTS')
        self.setpointsAngle = dct_get(e_roi, 'EPU_ANG_PNTS')
        self.ev_pol_order = dct_get(e_roi, 'EV_POL_ORDER')
        
        #setup some convienience member variables
        self.dwell = e_roi[DWELL]
        self.numX = self.x_roi[NPOINTS]
        self.numY = self.y_roi[NPOINTS]
        self.numZX = self.zx_roi[NPOINTS]
        self.numZY = self.zy_roi[NPOINTS]
        self.numEPU = len(self.setpointsPol)
        #self.numE = self.sp_db[SPDB_EV_NPOINTS] * len(self.setpointsPol)
        self.numE = self.sp_db[SPDB_EV_NPOINTS]
        self.numSPIDS = len(self.sp_rois)
        
        if(self.scan_type != scan_types.SAMPLE_POINT_SPECTRA):
            self.numImages = self.sp_db[SPDB_EV_NPOINTS] * self.numEPU
        else:
            #is a sample point spectrum
            self.numImages = 1
        
        #set some flags that are used elsewhere
        if(self.numImages > 1):
            self.stack = True
        else:
            self.stack = False
        
        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.file_saved = False
        self.sim_point = 0
        
        if((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
            if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
                #LINE_UNIDIR
                self.is_lxl = True
            else:
                #POINT_BY_POINT
                self.is_pxp = True
                
        elif(self.scan_type ==  scan_types.SAMPLE_POINT_SPECTRA):
            self.is_point_spec = True
            
        else:
            _logger.error('SampleImageWithEnergySSCAN: unable to determine scan type [%d]' % self.scan_type)
            return
        
        #users can request that the the ev and polarity portions of the scan can be executed in different orders
        #based on the order that requires a certain what for the sscan clases to be assigned in terms of their "level" so handle that in 
        #another function         
        #self.set_ev_pol_order(self.ev_pol_order)
        if(self.ev_pol_order == energy_scan_order_types.EV_THEN_POL):
            if(self.is_point_spec):
                if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                    _id = 'goni_ev_pol_pnt_spec'
                else:
                    _id = 'ev_pol_pnt_spec'
            elif(self.is_lxl):
                _id = 'ev_pol_lxl'
            else:
                #_id = 'ev_pol_pxp'
                _id = 'ev_pol_pxp_2recs'
                
        elif(self.ev_pol_order == energy_scan_order_types.POL_THEN_EV):
            if(self.is_point_spec):
                _id = 'pol_ev_pnt_spec'
            elif(self.is_lxl):
                _id = 'ev_pol_lxl'
            else:
                _id = 'ev_pol_pxp'
        
        else:
            _logger.error('unsupported ev polarity order [%d]' % ordr)        
            return
        
        parms = self.cmdfile_parms[_id]
        
        self.set_cmdfile_params(parms)
        
        if(not self.validate_scan_assignments()):
            _logger.error('Scans are not correctly assigned')
            return
        
        #cause the low level sscan records to clear their previous values and reload their common settings
        #self.setupScan.reload_base_scan_config()
        self.reload_base_scan_config()
        
        #set the function that will be called to make fine adjustments to the scan performance before scan starts
        # these optimization values are taken dynamically from tehj stxmMain.ini file so that they can be tested without restarting pySTXM
        if((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
            if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
                #LINE_UNIDIR
                #if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                #    self.set_optimize_scan_func(self.optimize_goni_scan)
                #else:    
                self.set_optimize_scan_func(self.optimize_sample_line_scan)
            else:
                #POINT_BY_POINT
                self.set_optimize_scan_func(self.optimize_sample_point_scan)
            
        elif(self.scan_type ==  scan_types.SAMPLE_POINT_SPECTRA):
            #self.pdlys = {'scan2': 0.05, 'scan1': 0.05}
            self.set_optimize_scan_func(self.optimize_sample_pointspec_scan)
        
        else:
            _logger.error('SampleImageWithEnergySSCAN: set optimize:  unable to determine scan type [%d]' % self.scan_type)
            return
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            zp_scan = True
        else:
            zp_scan = False    
        #determine and setup for line or point by point
        if(self.is_lxl):
            self.set_ImageLineScan_line_sscan_rec(self.sp_db, e_roi, zp_scan)
        else:
            if(self.is_point_spec):
                self.set_sample_point_spec_sscan_rec(self.sp_db, e_roi, zp_scan)
            else:
                self.set_ImageLineScan_point_sscan_rec(self.sp_db, e_roi, zp_scan)
                
        self.ttl_pnts = 0
        #reset signals so we can start clean
        if(block_disconnect_emit):
            self.blockSignals(True)
            
        self.disconnect_signals()
        
        if(block_disconnect_emit):
            self.blockSignals(False)
        
        #depending on the scan size the positioners used in the scan will be different, use a singe
        #function to find out which we are to use and return those names in a dct
        dct = self.determine_samplexy_posner_pvs()
        
        #depending on the current samplpositioning_mode perform a different configuration
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.config_for_goniometer_scan(dct)
        
        else:
            self.config_for_sample_holder_scan(dct)
        
        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        #self.stack_scan = stack
        
        #make sure OSA XY is in its center
        self.move_osaxy_to_its_center()
        
        #THIS must be the last call
        self.finish_setup()    
        self.new_spatial_start.emit(sp_id)
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        #if((self.is_pxp) or (self.is_point_spec)):
        if(self.is_pxp):
            #set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
            set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        elif(self.is_point_spec):
            #set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
            # numE is used for the number of points for a point spec, here we dont want to use Row etc because
            #we handle that here on hte counter handler for point spec
            set_devices_for_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.gate, self.counter, self.shutter)
        else:
            set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)

    def on_point_spec_scan_counter_changed(self, row, data):
        """
        on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN
        :param row: row 
        :type row: row integer
        
        :param data: data is a tuple of 2 values (x, counts)
        :type data: data tuple
        
        :returns: None
        
                The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
                The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
                The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
                slot during a point scan will receive a point+1 and in that case it should be ignored.
                
                LIne scan data arrives in the form data[row, < number of x points of values >]
                
                This slot has to handle 
                        
        """
        num_spids = len(self.sp_rois)
        sp_cntr = self.get_pnt_spec_spid_idx()
        #print point_val[0:10]
        point_val = data[1]        
        if(self.ttl_pnts < self.numE):
            #ev = self.evScan.P1.get('RBV')
            ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
            #print 'pointscan_counter_changed: on_counter_changed:[%d] x=%.2f point_val=%d len(data)=%d' % (self.ttl_pnts, ev, point_val, len(self.data))
            
            #self.data[self.ttl_pnts, 0] = point_val
            self.data[0, sp_cntr, self.ttl_pnts] = point_val
#             dct = {}
#             dct['sp_id'] = self.sp_ids[sp_cntr]
#             dct['img_idx'] = 0
#             dct['row'] = sp_cntr
#             dct['col'] = ev
#             dct['val'] = point_val
            
            dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
            dct[CNTR2PLOT_SP_ID] = self.sp_ids[sp_cntr]
            dct[CNTR2PLOT_ROW] = sp_cntr
            dct[CNTR2PLOT_COL] = ev
            dct[CNTR2PLOT_VAL] = point_val
            
            #print 'pointscan_counter_changed: on_counter_changed: num_spids = %d' % num_spids
            print('pointscan_counter_changed: on_counter_changed: [%d] row=%.2f col=%d val=%d' % (self.ttl_pnts, sp_cntr, self.ttl_pnts, point_val))
            
            #self.sigs.changed.emit(int(0), (ev, y))
            self.sigs.changed.emit(dct)
            #self.ttl_pnts += 1    
            
            self.incr_pnt_spec_spid_idx()
            
            if(self.get_pnt_spec_spid_idx() >= num_spids):
                #print 'resetting get_spec_spid_idx() [%d]' % self.get_pnt_spec_spid_idx()
                self.reset_pnt_spec_spid_idx()
                self.ttl_pnts += 1
            

#     def on_point_spec_scan_counter_changed(self, row, data):
#         """
#         on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN
#         :param row: row 
#         :type row: row integer
#         
#         :param data: data is a tuple of 2 values (x, counts)
#         :type data: data tuple
#         
#         :returns: None
#         
#                 The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
#                 The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
#                 The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
#                 slot during a point scan will receive a point+1 and in that case it should be ignored.
#                 
#                 LIne scan data arrives in the form data[row, < number of x points of values >]
#                 
#                 This slot has to handle 
#                         
#         """
#         #print point_val[0:10]
#         point_val = data[1]        
#         if(self.ttl_pnts < self.numE):
#             #ev = self.evScan.P1.get('RBV')
#             ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
#             #print 'pointscan_counter_changed: on_counter_changed:[%d] x=%.2f point_val=%d len(data)=%d' % (self.ttl_pnts, ev, point_val, len(self.data))
#             self.data[self.ttl_pnts, 0] = point_val
#             dct = {}
#             dct['img_idx'] = 0
#             dct['row'] = 0
#             dct['col'] = ev
#             dct['val'] = point_val
#             #self.sigs.changed.emit(int(0), (ev, y))
#             self.sigs.changed.emit(dct)
#             self.ttl_pnts += 1    

    
  
        
#     def on_pxp_counter_changed(self, row, data):
#         """
#         on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN
# 
#         :param row: row description
#         :type row: row type
# 
#         :param data: data description
#         :type data: data type
# 
#         :returns: None
#         """
#         """
#         The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
#         The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
#         slot during a point scan will receive a point+1 and in that case it should be ignored.
#         
#                 
#         """
#         _evidx = self.get_evidx()
#         #make imgidx zero based
#         _imgidx = self.get_imgidx()
#         
#         #Image point by point
#         point = int(data[0])
#         val = data[1]
#             
#         if(row >= self.numY):
#             self.incr_imgidx()
#             row = 0
#             
#         print 'SampleImageWithEnergySSCAN: on_pxp_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
#         self.data[_imgidx, row, point] = val
#             
#         dct = {}
#         dct['img_idx'] = _imgidx
#         dct['row'] = row
#         dct['col'] = point 
#         dct['val'] = val
#         #self.sigs.changed.emit(row, data)
#         self.sigs.changed.emit(dct)            
                            
#     def on_point_data_level_done(self):
#         """
#         on_point_data_level_done(): description
# 
#         :returns: None
#         """
#         """
#         Record the data points here so that at the end of the scan the data can be written out to disk
#         """
#         _logger.debug('PointSSCAN: on_data_level_done:')
#         if(not self.busy_saving):
#             self.busy_saving = True
#             #first copy evidx and increment main evidx so that the on_counter_changed handler will not overwrite 
#             _ev_idx = self.get_evidx()
#             _spatial_roi_idx = self.get_spatial_id()
#             #flip upside down
#             #make a copy of the data so that it will not be overwritten (reinitialized) before it has been saved to disk
#             _data = self.data.copy()
#             for scan in self.scanlist:
#                 #ask each scan to get its data and store it in scan.scan_data
#                 MAIN_OBJ.set('DATA.SSCANS.' + scan.section_name, scan.get_all_data())
#                 
#             MAIN_OBJ.set(ADO_CFG_WDG_COM, self.roi)
#             MAIN_OBJ.set('DATA.CHANNELS', self.data_level_scan.get_all_detector_data())
#                             
#             sample_pos = 1
#             datadir = self.get_data_dir()
#             hdf_name = self.get_next_hdf5_name(datadir)
#             #MAIN_OBJ.set(ADO_CFG_UNIQUEID, 'ms%d-%05d' % (sample_pos, seq_num))
#             MAIN_OBJ.set(ADO_CFG_UNIQUEID, 'ms%s' % (hdf_name))
#             #print 'data_rdy: seq_num=%d' % seq_num
#             
#             #self.hdr.save_image_jpg_xim(self._current_ev_idx, sample_pos, datadir, seq_num, MAIN_OBJ.get('SCAN.DATA.POINTS.' + str(self._current_ev_idx)))
#             #self.hdr.save_xsp(_ev_idx, sample_pos, datadir, seq_num, _data)
#             self.busy_saving = False
            
            