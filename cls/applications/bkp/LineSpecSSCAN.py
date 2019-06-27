'''
Created on Sep 26, 2016

@author: bergr
'''
import os
import numpy as np

from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan
from cls.utils.roi_dict_defs import *
from cls.utils.prog_dict_utils import make_progress_dict

from cls.types.stxmTypes import scan_types, scan_sub_types, \
                                        energy_scan_order_types, sample_positioning_modes

from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)
appConfig = ConfigClass(abs_path_to_ini_file)

class LineSpecSSCAN(BaseScan):
    '''
    This class 
    '''
    
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(LineSpecSSCAN, self).__init__('%sstxm'% MAIN_OBJ.get_sscan_prefix(),'LINESPEC', main_obj=MAIN_OBJ)

    
    def init_sscans(self):

        self.cb_idxs = []
        self.ttl_pnts = 0
        self.final_data_dir = None
        
        self.setupScan = SScanClass('%s:scan5' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
        self._scan4 = SScanClass('%s:scan4' % self.scan_prefix, SPDB_EV_EV, main_obj=MAIN_OBJ)
        self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_EV_POL, main_obj=MAIN_OBJ)
        self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, main_obj=MAIN_OBJ)
        self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)

        #self.cmd_file_pv = MAIN_OBJ.device('%s:cmd_file' % self.scan_prefix)
        
        #lxl_scan = {}
        #lxl_scan['cmd_file'] = '%s/line_spec_lxl.cmd'
        #lxl_scan['scan4_section_id'] = SPDB_EV_EV
        #lxl_scan['scan3_section_id'] = SPDB_EV_POL
        #lxl_scan['scan2_section_id'] = SPDB_Y
        #lxl_scan['scan1_section_id'] = SPDB_X
        
        lxl_scan = {}
        pxp_scan = {}
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            lxl_scan['cmd_file'] = '%s/goni_line_spec_lxl.cmd'  % self.script_dir
            pxp_scan['cmd_file'] = '%s/goni_line_spec_pxp.cmd'  % self.script_dir
        else:
            lxl_scan['cmd_file'] = '%s/line_spec_lxl.cmd'  % self.script_dir
            pxp_scan['cmd_file'] = '%s/line_spec_pxp.cmd'  % self.script_dir
        
        
        lxl_scan['ev_section_id'] = SPDB_EV_EV
        lxl_scan['pol_section_id'] = SPDB_EV_POL
        #lxl_scan['setup_scan'] = self.setupScan
        lxl_scan['setup_scan'] = None
        lxl_scan['pol_scan'] = self._scan4
        lxl_scan['ev_scan'] = self._scan3 
        lxl_scan['y_scan'] = self._scan2
        lxl_scan['x_scan'] = self._scan1
        lxl_scan['xy_scan'] = None
        lxl_scan['top_lvl_scan'] = self._scan4
        lxl_scan['data_lvl_scan'] = self._scan3
        lxl_scan['btm_lvl_scan'] = self._scan1
        lxl_scan['on_counter_changed'] = self.linespec_lxl_counter_changed
        lxl_scan['on_data_level_done'] = self.on_data_level_done
        lxl_scan['on_scan_done'] = self.chk_for_more_evregions
        lxl_scan['on_abort_scan'] = self.on_abort_scan
        lxl_scan['on_dev_cfg'] = self.on_this_dev_cfg
        #lxl_scan['modify_config'] = self.modify_line_spec_config
        lxl_scan['scanlist'] = [ self._scan1 , self._scan2, self._scan3, self._scan4]
        
        
        #pxp_scan['cmd_file'] = '%s/line_spec_pxp.cmd'
        
        #pxp_scan['scan3_section_id'] = SPDB_EV_EV
        #pxp_scan['scan2_section_id'] = SPDB_EV_POL
        #pxp_scan['scan1_section_id'] = SPDB_XY
        
        
        
        pxp_scan['ev_section_id'] = SPDB_EV_EV
        pxp_scan['pol_section_id'] = SPDB_EV_POL
        #pxp_scan['setup_scan'] = self.setupScan
        pxp_scan['setup_scan'] = None
        pxp_scan['pol_scan'] = self._scan3
        pxp_scan['ev_scan'] = self._scan2 
        pxp_scan['y_scan'] = None
        pxp_scan['x_scan'] = None
        pxp_scan['xy_scan'] = self._scan1
        pxp_scan['top_lvl_scan'] = self._scan3
        pxp_scan['data_lvl_scan'] = self._scan3
        pxp_scan['btm_lvl_scan'] = self._scan1
        pxp_scan['on_counter_changed'] = self.linespec_pxp_counter_changed
        pxp_scan['on_data_level_done'] = self.on_data_level_done
        pxp_scan['on_abort_scan'] = self.on_abort_scan
        pxp_scan['on_scan_done'] = self.chk_for_more_evregions
        pxp_scan['on_dev_cfg'] = self.on_this_dev_cfg
        pxp_scan['modify_config'] = None
        pxp_scan['scanlist'] = [ self._scan1 , self._scan2, self._scan3]
        

        
        #self.pnt_line_cmdfile_parms = [lxl_scan, pxp_scan]
        
        self.cmdfile_parms = {}
        self.cmdfile_parms['lxl_scan'] = lxl_scan
        self.cmdfile_parms['pxp_scan'] = pxp_scan
        
        zmtr = MAIN_OBJ.device(DNM_ZONEPLATE_Z)
        ymtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
        xmtr = MAIN_OBJ.device(DNM_SAMPLE_X)
        
        self.evScan = self._scan3
        self.polScan = self._scan2
        self.xyScan = self._scan1
        self.xScan = self._scan1
        self.yScan = self._scan1
        
        self.evScan.set_positioner(1, MAIN_OBJ.device('ENERGY'))
        
        self.polScan.set_positioner(1, MAIN_OBJ.device(DNM_EPU_POLARIZATION))
        self.polScan.set_positioner(2, MAIN_OBJ.device(DNM_EPU_OFFSET))
        self.polScan.set_positioner(3, MAIN_OBJ.device(DNM_EPU_ANGLE))
                
        self.xyScan.set_positioner(1, MAIN_OBJ.device(DNM_SAMPLE_X))
        self.xyScan.set_positioner(2, MAIN_OBJ.device(DNM_SAMPLE_Y))
        
        self.scanlist = [ ]
        self.mtr_list = [ ]
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device('Gate')
#         self.counter = MAIN_OBJ.device('Counter')
#         self.shutter = MAIN_OBJ.device('Shutter')  
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.evScan)
        self.set_data_level_scan(self.evScan)
        self.set_btm_level_scan(self.xyScan)
        self.set_top_level_scan(self.setupScan)
    
    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        self.set_on_counter_changed_func(self.linespec_pxp_counter_changed)
        self.set_on_scan_done_func(self.chk_for_more_evregions)

    def modify_line_spec_config(self):
        '''
        this is a handler for data_ready signal from SscanClass
        :return:
        '''
        cur_idx = self.get_consecutive_scan_idx()
        _logger.debug('LineSpecSSCAN: modify_line_spec_config() called [%d]' % cur_idx)
        _dct = self.get_img_idx_map(cur_idx)
        sp_idx = _dct['sp_idx']
        pol_idx = _dct['pol_idx']

        # for now just use the first counter
        #counter = self.counter_dct.keys()[0]
        counter = DNM_DEFAULT_COUNTER
        self._data = self.spid_data[counter][sp_idx][pol_idx]

        #self.on_save_sample_image(_data=self._data)
        self.on_save_sample_image(_data=self.img_data[sp_idx])

        #this creates the idx%d entry in the temp file
        _dct = self.get_snapshot_dict(cur_idx)
        self.main_obj.zmq_save_dict_to_tmp_file(_dct)

        self.incr_consecutive_scan_idx()



    def optimize_lxl_linespec_scan(self):
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
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_scan2_pdly'))
        
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_scan2_pdly'))
        
        c_fx_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_fy_force_done'))
        
        scan3_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'scan3_pdly'))
        scan4_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'scan4_pdly'))
        
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
        
        self.evScan.put('PDLY', scan3_pdly)
        self.polScan.put('PDLY', scan4_pdly)
    
    def optimize_pxp_linespec_scan(self):
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
        c_scan1_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_scan1_pdly'))
        c_scan2_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_scan2_pdly'))
        
        f_scan1_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_scan1_pdly'))
        f_scan2_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_scan2_pdly'))
        
        c_fx_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_fx_force_done'))
        c_fy_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'c_fy_force_done'))
        f_fx_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_fx_force_done'))
        f_fy_force_done = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'f_fy_force_done'))
        
        scan3_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'scan3_pdly'))
        scan4_pdly = float(appConfig.get_value('SAMPLE_LINE_SPEC_SCAN', 'scan4_pdly'))
        
        fx_done = MAIN_OBJ.device(DNM_FX_FORCE_DONE)
        fy_done = MAIN_OBJ.device(DNM_FY_FORCE_DONE)
        
        if(self.x_roi[SCAN_RES] == 'COARSE'):
            self.xyScan.put('PDLY', c_scan1_pdly)
            fx_done.put(c_fx_force_done)
        else:
            self.xyScan.put('PDLY', f_scan1_pdly)
            fx_done.put(f_fx_force_done)    
        
#         if(self.y_roi[SCAN_RES] == 'COARSE'):
#             self.yScan.put('PDLY', c_scan2_pdly)
#             fy_done.put(c_fy_force_done)
#         else:
#             self.yScan.put('PDLY', f_scan2_pdly)
#             fy_done.put(f_fy_force_done)
        
        self.evScan.put('PDLY', scan3_pdly)
        self.polScan.put('PDLY', scan4_pdly)
            
    def on_abort_scan(self):
        """
        on_abort_scan(): description

        :returns: None
        """
        self._abort = True
    

    def set_point_sscan_rec(self, sp_roi, e_roi):
        """
        set_point_sscan_rec(): description

        :param sp_roi: sp_roi description
        :type sp_roi: sp_roi type

        :param e_roi: e_roi description
        :type e_roi: e_roi type

        :returns: None
        """
        
        try:
            #reset total point counter
            if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                x_roi = self.zx_roi
                y_roi = self.zy_roi
            else:
                x_roi = self.x_roi
                y_roi = self.y_roi  
                
            self.ttl_pnts = 0
            #X
            self.xyScan.put('P1SM', 1)    #Table
            self.xyScan.put('NPTS', x_roi[NPOINTS])
            self.xyScan.put('P1PA', x_roi[SETPOINTS])
            
            self.xyScan.put('ASWAIT', 1) #No Wait
            self.xyScan.put('PDLY', 0.00)    

            #Y
            self.xyScan.put('P2SM', 1)    #Table
            self.xyScan.put('P2PA', y_roi[SETPOINTS])

            #pol
            self.polScan.put('NPTS', len(self.setpointsPol))
            self.polScan.put('P1PA', self.setpointsPol)
            self.polScan.put('P1SM', 1) #table
            #off
            self.polScan.put('P2PA', self.setpointsOff)
            self.polScan.put('P2SM', 1) #table
            #angle
            self.polScan.put('P3PA', self.setpointsAngle)
            self.polScan.put('P3SM', 1) #table
            
            #EV
            self.evScan.put('NPTS', e_roi[NPOINTS])
            self.evScan.put('P1SP', e_roi[START])
            self.evScan.put('P1EP', e_roi[STOP])
            
            self.setupScan.put('P4CP', e_roi[START])
            
        except:
            _logger.error('set_line_sscan_rec: failed a write to a PV')
    
    def set_line_sscan_rec(self, sp_roi, e_roi):
        """
        set_line_sscan_rec(): description

        :param sp_roi: sp_roi description
        :type sp_roi: sp_roi type

        :param e_roi: e_roi description
        :type e_roi: e_roi type

        :returns: None
        """
        try:

            #reset total point counter
            if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                x_roi = self.zx_roi
                y_roi = self.zy_roi
            else:
                x_roi = self.x_roi
                y_roi = self.y_roi

            self.ttl_pnts = 0
            #X
            self.xScan.put('P1SM', 0)    #linear
            self.xScan.put('NPTS', 2)
            self.xScan.put('P1SP', x_roi[START])
            self.xScan.put('P1EP', x_roi[STOP])
            self.xScan.put('ASWAIT', 1) #No WAIT
            self.xScan.put('T1PV', '')
            #if('scan1' in self.pdlys.keys()):
            #    self.xScan.put('PDLY', self.pdlys['scan1'])
            #else:
            #    self.xScan.put('PDLY', 0.00)


            #Y
            self.yScan.put('P1SM', 0)    #linear
            self.yScan.put('NPTS', 1)
            self.yScan.put('P1SP', y_roi[START])
            self.yScan.put('P1EP', y_roi[START])
            #if('scan2' in self.pdlys.keys()):
            #    self.yScan.put('PDLY', self.pdlys['scan2'])
            #else:
            #    self.yScan.put('PDLY', 0.000)

            #pol
            self.polScan.put('NPTS', len(self.setpointsPol))
            self.polScan.put('P1PA', self.setpointsPol)
            self.polScan.put('P1SM', 1) #table
            #off
            self.polScan.put('P2PA', self.setpointsOff)
            self.polScan.put('P2SM', 1) #table
            #angle
            self.polScan.put('P3PA', self.setpointsAngle)
            self.polScan.put('P3SM', 1) #table

            #EV
            self.evScan.put('NPTS', e_roi[NPOINTS])
            self.evScan.put('P1SP', e_roi[START])
            self.evScan.put('P1EP', e_roi[STOP])

            self.setupScan.put('P4CP', e_roi[START])

        except:
            _logger.error('set_line_sscan_rec: failed a write to a PV')
                            
    def configure(self, wdg_com, sp_id=0, ev_idx=0, line=True, spectra=False, block_disconnect_emit=False):
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
        _logger.info('configure: LineScan %d' % sp_id)
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        
        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.is_line_spec = False
        self.file_saved = False

        self.main_obj.device('e712_current_sp_id').put(sp_id)
        
        if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            self.is_lxl = True
            parms = self.cmdfile_parms['lxl_scan']
        else:
            self.is_pxp = True
            parms = self.cmdfile_parms['pxp_scan']
        
        self.set_cmdfile_params(parms)
        
        self.reload_base_scan_config()
        ########################
        
                
        if(ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            self.final_data_dir = None
            self.line_column_cntr = 0

        self.update_roi_member_vars(self.sp_db)
                    
        e_roi = self.e_rois[ev_idx]
        dct_put(self.sp_db, SPDB_RECT, ( e_roi[START], self.x_roi[START],  self.e_rois[-1][STOP], self.x_roi[STOP]))
        
        self.configure_sample_motors_for_scan()
        
        self.setpointsDwell = dct_get(e_roi, 'DWELL')
        #convert the Polarity QComboBox index values to the STXM Wrapper equivelants
        #self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, 'EPU_POL_PNTS')
        self.setpointsOff = dct_get(e_roi, 'EPU_OFF_PNTS')
        self.setpointsAngle = dct_get(e_roi, 'EPU_ANG_PNTS')
        
        self.dwell = e_roi[DWELL]
        
        #data shape for LineSPec scan = (  numEpu, numEv, numX)
        #                                  #images, #rows, #cols 
        self.numEPU = len(self.setpointsPol)
        self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
        self.numSPIDS = len(self.sp_rois)
        self.numImages = 1
        
        self.numZX = self.zx_roi[NPOINTS]
        self.numZY = self.zy_roi[NPOINTS]
        
        # NOTE! currently only arbitrary line is supported when equal number of x and e points so use E points
        #self.numY = self.e_roi[NPOINTS]
        self.numX = int(self.numE)
        self.numY = int(self.x_roi[NPOINTS])
        
        if(self.scan_type ==  scan_types.SAMPLE_LINE_SPECTRA):
            self.is_line_spec = True    
        else:
            _logger.error('LineSpecSSCAN: unable to determine scan type [%d]' % self.scan_type)
            return
        
        #reset signals so we can start clean
        if(block_disconnect_emit):
            self.blockSignals(True)
            
        self.disconnect_signals()
        
        if(block_disconnect_emit):
            self.blockSignals(False)
            
        dct = self.determine_samplexy_posner_pvs()
        
        accRange = 0
        if(self.is_lxl):
            self.set_line_sscan_rec(self.sp_db, e_roi)
            #self.set_on_counter_changed_func(self.linespec_lxl_counter_changed)
            #NOV6 self.set_optimize_scan_func(self.optimize_lxl_linespec_scan)
        else:
            self.set_point_sscan_rec(self.sp_db, e_roi)
            #self.set_on_counter_changed_func(self.linespec_pxp_counter_changed)
            #NOV6 self.set_optimize_scan_func(self.optimize_pxp_linespec_scan)
        
        #self.set_on_scan_done_func(self.chk_for_more_evregions)
        

        if(self.numImages > 1):
            self.stack = True
        else:        
            self.stack = False
            
        #self.scanlist = [ self.xScan , self.yScan, self.polScan, self.evScan]
        #self.mtr_list = [ self.xScan.P1 , self.yScan.P1, self.polScan.P1, self.polScan.P2, self.polScan.P3, self.evScan.P1]
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            self.config_for_goniometer_scan(dct)
        
        else:
            self.config_for_sample_holder_scan(dct)
        
        #self.data_shape = ('numImages', 'numY', 'numE')
        self.config_hdr_datarecorder(self.stack)
        #self.stack_scan = stack
        
        #THIS must be the last call
        self.finish_setup()
        self.new_spatial_start.emit(ev_idx)
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        if(self.is_lxl):
            #set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
            #remember that the number of points per line is plotted on the vertical axis so use numY for the number of points
            set_devices_for_line_scan(self.dwell, self.numY, self.gate, self.counter, self.shutter)
        else:    
            #set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
            #NOTE using numY to set thenumber of rows in this case the number of columns but it is "rows" according to the CI task
            set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numY, self.gate, self.counter, self.shutter)
            
    
    def linespec_pxp_counter_changed(self, col, xxx_todo_changeme, counter_name='counter0'):
        """
        linespec_counter_changed(): description

        :param row: row description
        :type row: row type

        :param (x: (x description
        :type (x: (x type

        :param y): y) description
        :type y): y) type

        :returns: None
        """
        (row, val) = xxx_todo_changeme
        """
        Used to override the sampleImageScanWithEnergy.on_changed handler.
        This is a slot that is connected to the counters changed signal        
        """
        sp_id = int(self.main_obj.device('e712_current_sp_id').get_position())
        if (sp_id not in list(self.spid_data[counter_name].keys())):
            _logger.error('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('self.spid_data.keys=', list(self.spid_data[counter_name].keys()))
            return

        self.set_spatial_id(sp_id)
        _imgidx = self.get_imgidx()
        _imgidx = 0
        _dct = self.get_img_idx_map(_imgidx)
        pol_idx = _dct['pol_idx']
        e_idx = _dct['e_idx']

        if((self.ttl_pnts % self.numY) == 0):
            if(self.ttl_pnts is not 0):
                self.line_column_cntr += 1
        #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
        #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
        self.ttl_pnts += 1
        
        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#       #sept11        self.data[_imgidx, row, self.line_column_cntr] = val

        self.spid_data[counter_name][sp_id][pol_idx][_imgidx, row, self.line_column_cntr] = val
        
        dct[CNTR2PLOT_ROW] = int(row)
        dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
        dct[CNTR2PLOT_VAL] = int(val)
        self.sigs.changed.emit(dct)
        
            

    def linespec_lxl_counter_changed(self, col, data, counter_name=DNM_DEFAULT_COUNTER):
        """
        linespec_counter_changed(): description

        :param row: row description
        :type row: row type

        :param (x: (x description
        :type (x: (x type

        :param y): y) description
        :type y): y) type

        :returns: None
        """
        """
        Used to override the sampleImageScanWithEnergy.on_changed handler.
        This is a slot that is connected to the counters changed signal        
        
        The line scan data is opposit to all the other scans in that the axis' are
            |                    |
        X/Y |            NOT  eV |
            |                    |
            |__________          |__________
                eV                    X/Y
        """
        sp_id = int(self.main_obj.device('e712_current_sp_id').get_position())
        self.set_spatial_id(sp_id)

        dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
        #print 'linespec_pxp_counter_changed: line_column_cntr=%d row=%d val=%d' % (self.line_column_cntr, row, val)
        #print 'linespec_pxp_counter_changed: ttl_pnts=%d' % (self.ttl_pnts)
        self.ttl_pnts += 1

        _imgidx = self.get_imgidx()
        _imgidx = 0

        _dct = self.get_img_idx_map(_imgidx)
        pol_idx = _dct['pol_idx']
        e_idx = _dct['e_idx']

        if(sp_id not in list(self.spid_data[counter_name].keys())):
            _logger.error('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('sp_id[%d] does not exist in self.spid_data keys' % sp_id)
            print('self.spid_data.keys=', list(self.spid_data[counter_name].keys()))
            return

        #self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = np.flipud( data[0:int(self.numY)])
        self.spid_data[counter_name][sp_id][pol_idx][_imgidx, :, self.line_column_cntr] = data[0:self.numY]

        dct[CNTR2PLOT_ROW] = None
        dct[CNTR2PLOT_COL] = int(self.line_column_cntr)
        dct[CNTR2PLOT_VAL] = data[0:self.numY]
        self.line_column_cntr += 1
        self.sigs.changed.emit(dct)


        prog = float(float(self.line_column_cntr + 0.75) / float(self.numE)) * 100.0
        prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
        self.low_level_progress.emit(prog_dct)


