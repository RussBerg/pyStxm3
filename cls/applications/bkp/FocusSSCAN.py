'''
Created on Sep 26, 2016

@author: bergr
'''
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.scanning.BaseScan import BaseScan, MODE_SCAN_START
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan
from cls.types.stxmTypes import scan_sub_types, sample_positioning_modes
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *

_logger = get_module_logger(__name__)



class FocusSSCAN(BaseScan):
    '''
    This scan uses the SampleX and SampleY stages which allows the scan to be done as a line by line instead of 
    the point by point scan which is required by the stages that cannot trigger on position such as the OSAFocus scan
    that is why this scan is left as an X, Y, Z scan instead of an XY, Z scan
    '''
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(FocusSSCAN, self).__init__('%sstxm'% MAIN_OBJ.get_sscan_prefix(),'FOCUS', main_obj=MAIN_OBJ)

    
        
    def init_sscans(self):

        self.cb_idxs = []
        self.ttl_pnts = 0
        
        #self.setupScan = SScanClass('%s:scan4' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
        self.setupScan = None
        self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_Z, main_obj=MAIN_OBJ)
        self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_XY, main_obj=MAIN_OBJ)
        self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)

        line_focus_zp = {}
        line_focus_zp['cmd_file'] = '%s/line_focus_zp.cmd'  % self.script_dir
        line_focus_zp['scan3_section_id'] = SPDB_Z
        line_focus_zp['scan2_section_id'] = SPDB_Y
        line_focus_zp['scan1_section_id'] = SPDB_X
        
        line_focus_smpl = {}
        line_focus_smpl['cmd_file'] = '%s/line_focus_smpl.cmd'  % self.script_dir
        line_focus_smpl['scan3_section_id'] = SPDB_Z
        line_focus_smpl['scan2_section_id'] = SPDB_Y
        line_focus_smpl['scan1_section_id'] = SPDB_X
        
        pnt_focus_zp = {}
        pnt_focus_zp['cmd_file'] = '%s/pnt_focus_zp.cmd'  % self.script_dir
        pnt_focus_zp['scan2_section_id'] = SPDB_Z
        pnt_focus_zp['scan1_section_id'] = SPDB_XY
        
        pnt_focus_smpl = {}
        pnt_focus_smpl['cmd_file'] = '%s/pnt_focus_smpl.cmd'  % self.script_dir
        pnt_focus_smpl['scan2_section_id'] = SPDB_Z
        pnt_focus_smpl['scan1_section_id'] = SPDB_XY
        
        self.cmd_file_pv = MAIN_OBJ.device( '%s:cmd_file' % self.scan_prefix )
        
        self.pnt_line_cmdfile_parms = {'line_zp': line_focus_zp, 'pnt_zp': pnt_focus_zp, 'line_smpl': line_focus_smpl, 'pnt_smpl': pnt_focus_smpl }
        
        zmtr = MAIN_OBJ.device(DNM_ZONEPLATE_Z)
        ymtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
        xmtr = MAIN_OBJ.device(DNM_SAMPLE_X)
        
        self.zScan = self._scan3
        self.yScan = self._scan2
        self.xyScan = self._scan1
        self.xScan = self._scan1
            
        
        self.zScan.set_positioner(1, zmtr)
        self.xyScan.set_positioner(1, xmtr)
        self.xyScan.set_positioner(2, ymtr)
        
        #self.scanlist = [ self.xyScan , self.zScan]
        self.scanlist = []
        self.mtr_list = [ zmtr, ymtr, xmtr]
    
#     def init_devices(self):
#         self.gate = MAIN_OBJ.device('Gate')
#         self.counter = MAIN_OBJ.device('Counter')
#         self.shutter = MAIN_OBJ.device('Shutter')  
    
    def init_set_scan_levels(self):
        self.set_top_level_scan(self.zScan)
        self.set_data_level_scan(self.zScan)
        self.set_btm_level_scan(self.xyScan)
    
    # def init_signals(self):
    #     self.set_config_devices_func(self.on_this_dev_cfg)
    #     #self.set_on_counter_changed_func(self.on_this_counter_changed)
    #     self.set_on_counter_changed_func(self.on_x_y_counter_changed)
    #     #self.set_on_scan_done_func(self.on_this_scan_done)
    #     #self.set_on_scan_done_func(self.on_x_y_scan_data_level_done)
    #     self.set_on_scan_done_func(self.on_this_data_level_done)
    #
    # # def on_this_scan_done(self):
    # #     """
    # #     on_this_scan_done(): description
    # #
    # #     :returns: None
    # #     """
    # #     #stop gate and counter input tasks
    # #     self.gate.stop()
    # #     self.counter.stop()
    # #     self.on_this_data_level_done()

    def init_signals(self):
        self.set_config_devices_func(self.on_this_dev_cfg)
        # self.set_on_counter_changed_func(self.on_this_counter_changed)
        self.set_on_counter_changed_func(self.on_x_y_counter_changed)
        self.set_on_scan_done_func(self.on_this_scan_done)

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        # stop gate and counter input tasks
        self.gate.stop()
        self.counter.stop()
        self.on_this_data_level_done()

    def set_line_or_pnt_cmd_file(self, zp_scan=False):
        '''
        the levels for each scan are:
            line and goniometer:
                goniometer setup in setupScan
                setupScan->zScan->yScan->xScan
                    topLevel = zScan
                    dataLevel = zScan
                    btnLevel = xScan
            point and goniometer:
                goniometer setup in setupScan
                setupScan->zScan->xyScan
                    topLevel = zScan
                    dataLevel = zScan
                    btnLevel = xyScan
                            
            line and sample:
                SampleXY setup in setupScan
                setupScan->zScan->yScan->xScan
                    topLevel = zScan
                    dataLevel = zScan
                    btnLevel = xScan 
            point and sample:
                SampleXY setup in setupScan
                setupScan->zScan->xyScan
                    topLevel = zScan
                    dataLevel = zScan
                    btnLevel = xyScan               
        '''
        zmtr = MAIN_OBJ.device(DNM_ZONEPLATE_Z)
        ymtr = MAIN_OBJ.device(DNM_SAMPLE_Y)
        xmtr = MAIN_OBJ.device(DNM_SAMPLE_X)

        if(self.is_lxl):
            if(zp_scan):
                parms = self.pnt_line_cmdfile_parms['line_zp']
            else:
                parms = self.pnt_line_cmdfile_parms['line_smpl']
                
            self.zScan = self._scan3
            self.yScan = self._scan2
            self.xScan = self._scan1
            self.zScan.set_positioner(1, zmtr)
            self.xScan.set_positioner(1, xmtr)
            self.yScan.set_positioner(1, ymtr)

            self.zScan.set_section_name(parms['scan3_section_id'])
            self.yScan.set_section_name(parms['scan2_section_id'])
            self.xScan.set_section_name(parms['scan1_section_id'])
            self.scanlist = [ self.xScan , self.yScan, self.zScan]
            self.set_top_level_scan(self.zScan)
            self.set_data_level_scan(self.zScan)
            self.set_btm_level_scan(self.xScan)
             
            
        elif(self.is_pxp):
            if(zp_scan):
                parms = self.pnt_line_cmdfile_parms['pnt_zp']
            else:
                parms = self.pnt_line_cmdfile_parms['pnt_smpl']
                       
            self.zScan = self._scan2
            self.xyScan = self._scan1
            self.zScan.set_positioner(1, zmtr)
            self.xyScan.set_positioner(1, xmtr)
            self.xyScan.set_positioner(2, ymtr)

            self.zScan.set_section_name(parms['scan2_section_id'])
            self.xyScan.set_section_name(parms['scan1_section_id'])
            self.scanlist = [ self.xyScan , self.zScan]
            self.set_top_level_scan(self.zScan)
            self.set_data_level_scan(self.zScan)
            self.set_btm_level_scan(self.xyScan)

        self.cmd_file = parms['cmd_file']
        
        
    def configure(self, wdg_com, sp_id=0, line=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param line=False: line=False description
        :type line=False: line=False type

        :returns: None
        """
        """ here if line == True then it is a line scan else config for point by point """
        
        self.toggle_psuedomotor_start_stop(self.zScan.P1)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.set_spatial_id(sp_id)
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.numX = dct_get(self.sp_db, SPDB_XNPOINTS)
        self.numY = dct_get(self.sp_db, SPDB_YNPOINTS)
        self.numZ = dct_get(self.sp_db, SPDB_ZNPOINTS)
        self.numE = dct_get(self.sp_db, SPDB_EV_NPOINTS)
        self.numSPIDS = len(self.sp_rois)
        self.e_rois = dct_get(self.sp_db, SPDB_EV_ROIS)
        e_roi = self.e_rois[0]
        self.numEPU = len(dct_get(e_roi, EPU_POL_PNTS))

        self.main_obj.device('e712_current_sp_id').put(sp_id)
        
        #if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
        #    self.is_lxl = True
        
        if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            zp_scan = True
        else:
            zp_scan = False  
        
        if(self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            #LINE_UNIDIR
            self.is_lxl = True
            self.is_pxp = False
            #self.pdlys = {}
        else:
            #POINT_BY_POINT
            self.is_pxp = True
            self.is_lxl = False
            #self.pdlys = {}    
            
        #self.set_top_level_scan(self.setupScan)
        #self.set_top_level_scan(self._scan3)
        #self.setupScan.put('T4PV', '%s:scan3.EXSC' % self.scan_prefix)
        #self.setupScan.put('T4CD', '1')
            
        self.set_line_or_pnt_cmd_file(zp_scan)
        
        self.reload_base_scan_config()
        
        self.x_roi = dct_get(self.sp_db, SPDB_X)
        self.y_roi = dct_get(self.sp_db,SPDB_Y)
        self.z_roi = dct_get(self.sp_db,SPDB_Z)
        
        self.gx_roi = dct_get(self.sp_db, SPDB_GX)
        self.gy_roi = dct_get(self.sp_db, SPDB_GY)
        self.gz_roi = dct_get(self.sp_db, SPDB_GZ)
        self.gt_roi = dct_get(self.sp_db, SPDB_GT)
        
        self.zx_roi = dct_get(self.sp_db, SPDB_ZX)
        self.zy_roi = dct_get(self.sp_db, SPDB_ZY)
        self.zz_roi = dct_get(self.sp_db, SPDB_ZZ)
        
        self.ox_roi = dct_get(self.sp_db, SPDB_OX)
        self.oy_roi = dct_get(self.sp_db, SPDB_OY)
        self.oz_roi = dct_get(self.sp_db, SPDB_OZ)
        
        self.ensure_left_to_right(self.x_roi)
        self.ensure_left_to_right(self.y_roi)
        self.ensure_left_to_right(self.z_roi)

        dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.z_roi[START], self.x_roi[STOP], self.z_roi[STOP]))
        
        #also sets the scan res for x and y as well as turns off AutoDisable
        self.configure_sample_motors_for_scan()
        
        #self.e_rois = dct_get(self.sp_db, SPDB_EV_ROIS)
        self.dwell = self.e_rois[0][DWELL]
        self.numZX = self.zx_roi[NPOINTS]
        self.numZY = self.zy_roi[NPOINTS]
        
        self.reset_evidx()
        self.reset_imgidx()

        x_posnum = 1
        y_posnum = 2
        z_posnum = 1
        
        dct = self.determine_samplexy_posner_pvs()

        self.stack = False
                
        if(self.is_lxl):
            self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            self.set_on_counter_changed_func(self.on_sample_scan_counter_changed)
            self.set_FocusImageLineScan_sscan_rec(self.sp_db, zp_scan=zp_scan)
        
        else:
            self.set_on_counter_changed_func(self.on_x_y_counter_changed)
            self.set_FocusImagePointScan_sscan_rec(self.sp_db, zp_scan=zp_scan)
        
        #self.scanlist = [ self.xScan , self.yScan]
        #self.mtr_list = [ self.xScan.P1 , self.yScan.P1]    
            
        if(zp_scan):
            self.config_for_goniometer_scan(dct, is_focus=True)
            zx = self.main_obj.device(dct['fx_name'])
            zx.put('user_setpoint', self.zx_roi[START] - 5)


        else:
            self.config_for_sample_holder_scan(dct)
        
        #Zpz
        self._config_start_stop(self.zScan, 1, self.z_roi[START], self.z_roi[STOP], self.z_roi[NPOINTS])
        #_config_start_stop(self, sscan, posnum, start, stop, npts):
        
        #self._assign_positioner_setpoints(self.zScan, z_posnum, self.z_roi[SETPOINTS], self.z_roi[NPOINTS])    

        #make sure OSA XY is in its center
        self.move_osaxy_to_its_center()
        
        #self.data_shape = ('numE', 'numZ', 'numX')
        self.config_hdr_datarecorder(self.stack)
        #self.stack_scan = stack
        
        #THIS must be the last call
        self.finish_setup()

        #added this to try and stabalize the start of the scan (sends lines before proper start)
        self.gate.wait_till_running_polling()
        self.counter.wait_till_running_polling()
        
    
    def goto_scan_start(self, dct):
        x_posnum = 1
        y_posnum = 2
        z_posnum = 1
        
        self.sample_mtry.put('Mode', MODE_SCAN_START)
        #self.xyScan.put('P%dPV' % y_posnum, dct['ypv'] + '.VAL') #positioner pv
        #self.xyScan.put('R%dPV' % y_posnum, dct['ypv'] + '.RBV') #positioner pv
        self.xyScan.put('P%dPV' % y_posnum, dct['sample_pv_nm']['Y'] + '.VAL') #positioner pv
        self.xyScan.put('R%dPV' % y_posnum, dct['sample_pv_nm']['Y'] + '.RBV') #positioner pv
        self._assign_positioner_setpoints(self.xyScan, y_posnum, self.y_roi[SETPOINTS], self.numY)
        MAIN_OBJ.device( dct['sy_name'] ).put('user_setpoint', self.y_roi[CENTER])
            
        line = False
        self.sample_mtrx.put('Mode', MODE_SCAN_START)
        #self.config_samplex_start_stop(dct['xpv'], self.x_roi[CENTER], self.x_roi[RANGE], self.numX, accRange=0, line=line)
        self.config_samplex_start_stop(dct['sample_pv_nm']['X'], self.x_roi[CENTER], self.x_roi[RANGE], self.numX, accRange=0, line=line)
        #posner = getattr(self.xyScan, 'P%d' % x_posnum)
    
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        if(self.is_lxl):
            set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
        else:    
            set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        
            
    
    # def on_this_data_level_done(self):
    #     """
    #     on_this_data_level_done(): description
    #
    #     :returns: None
    #     """
    #     """
    #     this is an API slot that gets fired when the data level scan_done signal
    #
    #     The final data dict should have the main keys of:
    #         all_data['SSCANS']      - all fields of each sscan record, this will be a list of sscans
    #         all_data['SCAN_CFG']    - all params from the GUI for this scan, center, range etc, also any flags such as XMCD=True that relate to how to execute this scan
    #         all_data['DATA']        - counter data collected during scan, for images this will be a 2d array, for point scans this will be a 1d array
    #
    #     The goal of all_data dict is to write the dict out to disk in <data dir>/master.json. Once it has been recorded to disk the data recorder
    #     module can open it as a json object and export it based on the scan type so that it can pick and choose what to pull out and write to the header file.
    #
    #     """
    #     _logger.debug('Focus: on_data_level_done:')
    #     #     if(self.is_lxl):
    #     #         self.on_save_sample_image()
    #     #         #self.save_hdr()
    #     #     #else:
    #     #     self.on_x_y_scan_data_level_done()
    #     #
    #     self.on_x_y_scan_data_level_done()
    #     if (self.signals_connected):
    #         _logger.debug('BaseScan: on_scan_done_discon_sigs: emitted all_done sig')
    #         self.all_done.emit()
    #     else:
    #         _logger.debug('FocusScan: on_scan_done_discon_sigs: ELSE: sigs were not connected')
    #     # if(done):
    #     self.disconnect_signals()

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
        # _logger.debug('Focus: on_data_level_done:')
        if (self.is_lxl):
            self.on_save_sample_image()
            # self.save_hdr()
        # else:
        self.on_x_y_scan_data_level_done()
