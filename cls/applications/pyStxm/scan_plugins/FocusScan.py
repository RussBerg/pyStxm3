'''
Created on Sep 26, 2016

@author: bergr
'''
from bluesky.plans import count, scan, grid_scan, scan_nd
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from cycler import cycler
#from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from bcm.devices.device_names import *
from cls.scanning.BaseScan import BaseScan, MODE_SCAN_START
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan
from cls.types.stxmTypes import scan_sub_types, sample_positioning_modes
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
_logger = get_module_logger(__name__)



class FocusScanClass(BaseScan):
    '''
    This scan uses the SampleX and SampleY stages which allows the scan to be done as a line by line instead of 
    the point by point scan which is required by the stages that cannot trigger on position such as the OSAFocus scan
    that is why this scan is left as an X, Y, Z scan instead of an XY, Z scan
    '''
    def __init__(self, main_obj=None ):
        """
        __init__(): description

        :returns: None
        """
        super(FocusScanClass, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), 'FOCUS', main_obj=main_obj)

    def init_subscriptions(self, ew, func):
        '''
        over ride the base init_subscriptions because we need to use the number of rows from the self.zz_roi instead of
        self.y_roi
        :param ew:
        :param func:
        :return:
        '''

        if(self.is_pxp):
            self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE, x=DNM_SAMPLE_X,
                                                    scan_type=self.scan_type, bi_dir=self._bi_dir)
            self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)
        else:
            self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE,
                                                x=DNM_SAMPLE_X,
                                                scan_type=self.scan_type, bi_dir=self._bi_dir)
            self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''
            gate and counter need to be staged for pxp
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        # zp_def = self.get_zoneplate_info_dct()
        # md = {'entry_name': 'entry0', 'scan_type': self.scan_type,
        #       'rois': {SPDB_X: self.x_roi, SPDB_Y: self.y_roi, SPDB_Z: self.zz_roi},
        #       'dwell': self.dwell,
        #       'primary_det': DNM_DEFAULT_COUNTER,
        #       'zp_def': zp_def,
        #       'wdg_com': dict_to_json(self.wdg_com)}
        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
        mtr_dct = self.determine_samplexy_posner_pvs()

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        # @bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': scan_types.DETECTOR_IMAGE})
        def do_scan():

            #mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            #mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_x = self.main_obj.device(mtr_dct['cx_name'])
            mtr_y = self.main_obj.device(mtr_dct['cy_name'])
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
            shutter = self.main_obj.device(DNM_SHUTTER)

            x_traj = cycler(mtr_x, self.x_roi[SETPOINTS])
            y_traj = cycler(mtr_y, self.y_roi[SETPOINTS])
            zz_traj = cycler(mtr_z, self.zz_roi[SETPOINTS])

            yield from bps.stage(gate)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            yield from scan_nd(dets, zz_traj * (y_traj + x_traj),
                               md=md)

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)

            print('FocusScanClass PxP: make_scan_plan Leaving')

        return (yield from do_scan())

    def make_lxl_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''

        this needs to be adapted to be a fly scan, setup SampleX to trigger at correct location, set scan velo and acc range
        and then call scan, gate an d counter need to be staged for lxl
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        zp_def = self.get_zoneplate_info_dct()
        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        # @bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': self.scan_type,
        #                            'rois': {SPDB_X: self.x_roi, SPDB_Y: self.y_roi, SPDB_Z: self.zz_roi},
        #                            'dwell': self.dwell,
        #                            'primary_det': DNM_DEFAULT_COUNTER,
        #                            'zp_def': zp_def,
        #                            'wdg_com': dict_to_json(self.wdg_com)})
        def do_scan():

            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)

            shutter.open()
            bps.open_run(md=md)

            # go to start of line
            yield from bps.mv(mtr_x, self.x_roi[START], mtr_y, self.y_roi[CENTER])

            #now do a horizontal line for every new zoneplate Z setpoint
            for sp in self.zz_roi[SETPOINTS]:
                yield from bps.mv(mtr_z, sp)
                yield from bps.mv(mtr_x, self.x_roi[STOP])
                yield from bps.mv(mtr_x, self.x_roi[START])

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            bps.close_run()
            print('FocusScanClass LxL: make_scan_plan Leaving')

        return (yield from do_scan())

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        # stop gate and counter input tasks
        # self.gate.stop()
        # self.counter.stop()
        # self.on_this_data_level_done()
        pass

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
        
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_db = self.sp_rois[sp_id]
        self.set_spatial_id(sp_id)
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.numX = dct_get(self.sp_db, SPDB_XNPOINTS)
        self.numY = dct_get(self.sp_db, SPDB_YNPOINTS)
        self.numZZ = dct_get(self.sp_db, SPDB_ZZNPOINTS)
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
            
        self.update_roi_member_vars(self.sp_db)

        self.ensure_left_to_right(self.x_roi)
        self.ensure_left_to_right(self.y_roi)
        self.ensure_left_to_right(self.zz_roi)

        #dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.z_roi[START], self.x_roi[STOP], self.z_roi[STOP]))
        dct_put(self.sp_db, SPDB_RECT,
                (self.x_roi[START], self.zz_roi[START], self.x_roi[STOP], self.zz_roi[STOP]))
        
        #also sets the scan res for x and y as well as turns off AutoDisable
        self.configure_sample_motors_for_scan()
        
        self.dwell = self.e_rois[0][DWELL]
        self.numZX = self.zx_roi[NPOINTS]
        self.numZY = self.zy_roi[NPOINTS]
        
        self.reset_evidx()
        self.reset_imgidx()
        self.init_set_scan_levels()

        # x_posnum = 1
        # y_posnum = 2
        # z_posnum = 1
        
        dct = self.determine_samplexy_posner_pvs()

        self.stack = False
                
        # if(self.is_lxl):
        #     self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
        #     self.set_on_counter_changed_func(self.on_sample_scan_counter_changed)
        #     self.set_FocusImageLineScan_sscan_rec(self.sp_db, zp_scan=zp_scan)
        #
        # else:
        #     self.set_on_counter_changed_func(self.on_x_y_counter_changed)
        #     self.set_FocusImagePointScan_sscan_rec(self.sp_db, zp_scan=zp_scan)
        #
        # #self.scanlist = [ self.xScan , self.yScan]
        # #self.mtr_list = [ self.xScan.P1 , self.yScan.P1]
            
        # if(zp_scan):
        #     self.config_for_goniometer_scan(dct, is_focus=True)
        #     zx = self.main_obj.device(dct['fx_name'])
        #     zx.put('user_setpoint', self.zx_roi[START] - 5)
        #
        #
        # else:
        #     self.config_for_sample_holder_scan(dct)
        #
        # #Zpz
        # self._config_start_stop(self.zScan, 1, self.zz_roi[START], self.zz_roi[STOP], self.zz_roi[NPOINTS])
        # #_config_start_stop(self, sscan, posnum, start, stop, npts):
        
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
        '''

        :param dct:
        :return:
        '''
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
        # if (self.is_lxl):
        #     self.on_save_sample_image()
        #     # self.save_hdr()
        # # else:
        # self.on_x_y_scan_data_level_done()
        pass

