
'''
Created on Apr 26, 2017

@author: bergr
'''
#import os
import copy
#import atexit
#import numpy as np
#import time

from bluesky.plans import count, scan, grid_scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from bcm.devices.device_names import *

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ

from cls.scanning.BaseScan import BaseScan, SIM_SPEC_DATA, SIMULATE_SPEC_DATA
#from cls.scanning.SScanClass import SScanClass
#from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, \
#    set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan, make_timestamp_now
from cls.types.stxmTypes import scan_types, scan_sub_types, \
    energy_scan_order_types, sample_positioning_modes, sample_fine_positioning_modes
from cls.scanning.scan_cfg_utils import ensure_valid_values, calc_accRange
from cls.utils.roi_dict_defs import *
#from cls.utils.dict_utils import dct_get
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass
from cls.utils.dict_utils import dct_put, dct_get
#from cls.types.beamline import BEAMLINE_IDS
#from cls.utils.prog_dict_utils import make_progress_dict
from cls.utils.json_utils import dict_to_json
#from cls.utils.qt5_utils import get_signals
#from cls.zeromq.epics.epics_api import *
from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)

#get the accel disstance for now from the app configuration
ACCEL_DISTANCE = MAIN_OBJ.get_preset_as_float('coarse_accel_distance')


class CoarseSampleImageScanClass(BaseScan):
    '''
    This class is used to implement Coarse scans for conventional mode scanning
    '''


    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(CoarseSampleImageScanClass, self).__init__(main_obj=main_obj)
        # self.x_use_reinit_ddl = False
        # self.x_auto_ddl = True
        #self.spid_data = None
        self.img_idx_map = {}
        self.spid_data = {}

    def make_pxp_scan_plan(self, dets, gate, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        #zp_def = self.get_zoneplate_info_dct()
        mtr_dct = self.determine_samplexy_posner_pvs()
        md = copy.deepcopy(self.make_standard_metadata(entry_num=0, scan_type=self.scan_type, dets=dets))
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        # @bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': scan_types.DETECTOR_IMAGE})
        def do_scan():
            # Declare the end of the run.

            x_roi = self.sp_db['X']
            y_roi = self.sp_db['Y']
            mtr_x = self.main_obj.device(mtr_dct['cx_name'])
            mtr_y = self.main_obj.device(mtr_dct['cy_name'])
            shutter = self.main_obj.device(DNM_SHUTTER)

            det = dets[0]
            #md = self.make_standard_metadata(entry_num=0, scan_type=self.scan_type)
            #md['x_roi'] = x_roi
            #md['y_roi'] = y_roi
            yield from bps.stage(gate)
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            yield from grid_scan(dets,
                                 mtr_y, y_roi[START], y_roi[STOP], y_roi[NPOINTS],
                                 mtr_x, x_roi[START], x_roi[STOP], x_roi[NPOINTS],
                                 self._bi_dir,
                                 md=md)

            shutter.close()
            yield from bps.unstage(gate)

            print('CoarseSampleImageScanClass: make_pxp_scan_plan Leaving')

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
        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, dets=dets))}
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        @bpp.run_decorator(md=md)
        def do_scan():
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            #bps.open_run(md=md)

            # go to start of line
            yield from bps.mv(mtr_x, self.x_roi[START] - ACCEL_DISTANCE, mtr_y, self.y_roi[START])

            # now do a horizontal line for every new Y setpoint
            for y_sp in self.y_roi[SETPOINTS]:
                yield from bps.mv(mtr_y, y_sp)
                yield from bps.mv(mtr_x, self.x_roi[STOP] + ACCEL_DISTANCE)
                #return
                yield from bps.mv(mtr_x, self.x_roi[START] - ACCEL_DISTANCE)

            shutter.close()

            yield from bps.unstage(gate)
            #bps.close_run()
            print('CoarseSampleImageScanClass LxL: make_scan_plan Leaving')

        return (yield from do_scan())


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
        super(CoarseSampleImageScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        _logger.info('\n\nCoarseSampleImageScanClass: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
        self.set_spatial_id(sp_id)
        # self.wdg_com = wdg_com
        # self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        # self.sp_ids = list(self.sp_rois.keys())
        # self.sp_db = self.sp_rois[sp_id]
        # self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        # self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        # self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()

        #self.update_roi_member_vars(self.sp_db)

        #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
        # this is done in sscan2
        # self.xScan = self._scan1
        # self.yScan = self._scan2
        # self.xyScan = None

        self.determine_scan_res()
        if(self.is_fine_scan):
            _logger.error('Scan is a fine scan, use Image Scan for this')
            return(None)

        # dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))
        # the sample motors have different modes, make a call to handle that they are setup correctly for this scan
        self.configure_sample_motors_for_scan()

        if (ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            #self.reset_pnt_spec_spid_idx()
            self.final_data_dir = None
            self.update_dev_data = []

        self.is_multi_spatial = False
        self.set_save_all_data(False)

        # get the energy and EOU related setpoints
        e_roi = self.e_rois[ev_idx]
        self.setpointsDwell = dct_get(e_roi, DWELL)
        # self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
        self.setpointsPol = dct_get(e_roi, EPU_POL_PNTS)
        self.setpointsOff = dct_get(e_roi, EPU_OFF_PNTS)
        self.setpointsAngle = dct_get(e_roi, EPU_ANG_PNTS)
        self.ev_pol_order = dct_get(e_roi, EV_POL_ORDER)

        sps = dct_get(self.wdg_com, SPDB_SINGLE_LST_SP_ROIS)
        evs = dct_get(self.wdg_com, SPDB_SINGLE_LST_EV_ROIS)
        pols = dct_get(self.wdg_com, SPDB_SINGLE_LST_POL_ROIS)
        dwells = dct_get(self.wdg_com, SPDB_SINGLE_LST_DWELLS)

        self.use_hdw_accel = False
        self.x_auto_ddl = False
        self.x_use_reinit_ddl = False

        # setup some convienience member variables
        self.dwell = e_roi[DWELL]
        self.numX = int(self.x_roi[NPOINTS])
        self.numY = int(self.y_roi[NPOINTS])
        self.numZX = int(self.zx_roi[NPOINTS])
        self.numZY = int(self.zy_roi[NPOINTS])
        self.numEPU = len(self.setpointsPol)
        # self.numE = self.sp_db[SPDB_EV_NPOINTS] * len(self.setpointsPol)
        self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
        self.numSPIDS = len(self.sp_rois)
        self.numImages = 1

        # set some flags that are used elsewhere
        self.stack = False
        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.file_saved = False
        self.sim_point = 0

        # users can request that the the ev and polarity portions of the scan can be executed in different orders
        # based on the order that requires a certain what for the sscan clases to be assigned in terms of their "level" so handle that in
        # another function
        # self.set_ev_pol_order(self.ev_pol_order)
        if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            # LINE_UNIDIR
            self.is_lxl = True

        else:
            # POINT_BY_POINT
            self.is_pxp = True


        # parms = self.cmdfile_parms[_id]
        # self.set_cmdfile_params(parms)
        #
        # # cause the low level sscan records to clear their previous values and reload their common settings
        # #self.setupScan.reload_base_scan_config()
        # self.reload_base_scan_config()
        #
        # # set the function that will be called to make fine adjustments to the scan performance before scan starts
        # # these optimization values are taken dynamically from tehj stxmMain.ini file so that they can be tested without restarting pySTXM
        #
        # # reset to the default then decide if to change it
        # self.set_optimize_scan_func(None)
        #
        # self.set_optimize_scan_func(self.optimize_sample_line_scan)

        # zp_scan = False
        #     # determine and setup for line or point by point
        # if(self.is_pxp):
        #     self.set_ImageLineScan_point_sscan_rec(self.sp_db, e_roi, zp_scan)
        # else:
        #     self.set_ImageLineScan_line_sscan_rec(self.sp_db, e_roi, zp_scan)
        #
        # self.ttl_pnts = 0
        # # reset signals so we can start clean
        # if (block_disconnect_emit):
        #     self.blockSignals(True)
        #
        # self.disconnect_signals()
        #
        # if (block_disconnect_emit):
        #     self.blockSignals(False)
        #
        # # depending on the scan size the positioners used in the scan will be different, use a singe
        # # function to find out which we are to use and return those names in a dct
        dct = self.determine_samplexy_posner_pvs()

        self.config_for_sample_holder_scan(dct)

        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        self.seq_map_dct = self.generate_2d_seq_image_map(1, self.y_roi[NPOINTS], self.x_roi[NPOINTS], lxl=self.is_lxl)

        # THIS must be the last call
        self.finish_setup()
        # self.new_spatial_start.emit(sp_id)

    def config_for_sample_holder_scan(self, dct):
        """
        this function accomplishes the following:
            - set the positoners for X and Y
            - set the sample X and Y positioners to self.sample_mtrx etc
            - determine and set the fine positioners to sample_finex etc
            - move the sample_mtrx/y to start by setting scan Mode too ScanStart then moving and waiting until stopped
            - determine if coarse or fine scan and PxP or LxL and:
                - get max velo of the x positioner
                - Determine if scan is Line Spectra
                    - if LineSpectra the number of points is Y not X
                    - calc ScanVelo, Npts and Dwell, adjusting Npts to match velo and dwell
                - Depending on coarse or fine scans calc accel/deccel range or get straight from blConfig
                - Set the MarkerStart,ScanStart/Stop etc by calling config_samplex_start_stop
                - set the X positioner velocity to the scan velo
                - set the driver Mode to LINE_UNIDIR or COARSE or whatever it needs
                - if Fine scan make sure the servo power is on
        """
        self.sample_mtrx = self.main_obj.get_sample_positioner('X')
        self.sample_mtry = self.main_obj.get_sample_positioner('Y')
        self.sample_finex = self.main_obj.get_sample_fine_positioner('X')
        self.sample_finey = self.main_obj.get_sample_fine_positioner('Y')

        # setup X positioner
        self.sample_mtrx.set_mode(self.sample_mtrx.MODE_SCAN_START)
        self.sample_mtrx.move(dct['xstart'])
        _logger.info('Waiting for SampleX to move to start')
        self.confirm_stopped([self.sample_mtrx])

        # setup Y positioner
        self.sample_mtry.set_mode(self.sample_mtrx.MODE_SCAN_START)
        self.sample_mtry.move(dct['ystart'])
        _logger.info('Waiting for SampleY to move to start')
        self.confirm_stopped([self.sample_mtry])

        # setup X
        if (self.is_pxp or self.is_point_spec):
            if (self.x_roi[SCAN_RES] == COARSE):
                #scan_velo = self.get_mtr_max_velo(self.xScan.P1)
                scan_velo = self.sample_mtrx.get_max_velo()
            else:
                #scan_velo = self.get_mtr_max_velo(self.main_obj.device(DNM_SAMPLE_FINE_X))
                scan_velo = self.sample_finex.get_max_velo()

            # x needs one extra to switch the row
            npts = self.numX
            dwell = self.dwell
            accRange = 0
            deccRange = 0
            line = False
        else:
            _ev_idx = self.get_evidx()
            e_roi = self.e_rois[_ev_idx]
            vmax = self.sample_mtrx.get_max_velo()
            # its not a point scan so determine the scan velo and accRange
            if (self.scan_type == scan_types.SAMPLE_LINE_SPECTRUM):
                # for line spec scans the number of points is saved in self.numY
                (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                               self.numY, vmax, do_points=True)
            else:
                (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                               self.numX, vmax, do_points=True)

            if (self.x_roi[SCAN_RES] == COARSE):
                accRange = calc_accRange(dct['sx_name'], self.x_roi[SCAN_RES], self.x_roi[RANGE], scan_velo, dwell,
                                         accTime=0.04)
                deccRange = accRange
            else:
                #pick up any changes from disk from the app config file
                #appConfig.update()
                section = 'SAMPLE_IMAGE_PXP'
                if (self.is_lxl):
                    section = 'SAMPLE_IMAGE_LXL'

                #accRange = float(appConfig.get_value(section, 'f_acc_rng'))
                #deccRange = float(appConfig.get_value(section, 'f_decc_rng'))
                accRange = self.main_obj.get_preset(section, 'f_acc_rng')
                deccRange = self.main_obj.get_preset(section, 'f_decc_rng')

            # the number of points may have changed in order to satisfy the dwell the user wants
            # so update the number of X points and dwell
            # self.numX = npts
            # self.x_roi[NPOINTS] = npts

            line = True
            e_roi[DWELL] = dwell
            self.dwell = dwell

        print('accRange=%.2f um' % (accRange))
        print('deccRange=%.2f um' % (deccRange))

        # move X to start
        # self.sample_mtrx.put('Mode', MODE_SCAN_START)
        # self.sample_mtrx.put('Mode', MODE_NORMAL)
        if (self.is_lxl):
            # self.config_samplex_start_stop(dct['xpv'], self.x_roi[START], self.x_roi[STOP], self.numX, accRange=accRange, line=line)
            if (self.x_roi[SCAN_RES] == COARSE):
                self.sample_mtrx.config_start_stop(self.x_roi[START], self.x_roi[STOP], self.numX, accRange=accRange, deccRange=deccRange, line=line)
                self.sample_mtrx.set_velo(scan_velo)
                #self.config_samplex_start_stop(dct['sample_pv_nm']['X'], self.x_roi[START], self.x_roi[STOP], self.numX,
                # accRange=accRange, deccRange=deccRange, line=line)
            else:
                # if it is a fine scan then dont use the abstract motor for the actual scanning
                # because the status fbk timing is currently not stable
                self.sample_finex.config_start_stop(self.x_roi[START], self.x_roi[STOP], self.numX, accRange=accRange,
                                                   deccRange=deccRange, line=line)
                self.sample_finex.set_velo(scan_velo)
                # self.config_samplex_start_stop(dct['fine_pv_nm']['X'], self.x_roi[START], self.x_roi[STOP],
                #                                self.numX, accRange=accRange, deccRange=deccRange, line=line)

        #self.set_x_scan_velo(scan_velo)
        # self.confirm_stopped([self.sample_mtrx, self.sample_mtry])

        self.num_points = self.numY

        # self.confirm_stopped(self.mtr_list)
        # set teh velocity in teh sscan rec for X
        if (self.is_pxp or self.is_point_spec):
            # force it to toggle, not sure why this doesnt just work
            if (self.x_roi[SCAN_RES] == COARSE):
                #self.sample_mtrx.put('Mode', MODE_COARSE)
                self.sample_mtrx.set_mode(self.sample_mtrx.MODE_COARSE)

            else:
                #self.sample_mtrx.put('Mode', MODE_POINT)
                #self.sample_finex.set_power( 1)
                self.sample_mtrx.set_mode(self.sample_mtrx.MODE_POINT)
                self.sample_finex.set_power(self.sample_mtrx.POWER_ON)

            if (self.y_roi[SCAN_RES] == COARSE):
                #self.sample_mtry.put('Mode', MODE_COARSE)
                self.sample_mtry.set_mode(self.sample_mtry.MODE_COARSE)
            else:
                #self.sample_mtry.put('Mode', MODE_LINE_UNIDIR)
                #self.sample_finey.set_power( 1)
                self.sample_mtry.set_mode(self.sample_mtry.MODE_LINE_UNIDIR)
                self.sample_finey.set_power(self.sample_mtry.POWER_ON)


        else:
            # force it to toggle, not sure why this doesnt just work
            if (self.x_roi[SCAN_RES] == COARSE):
                #self.sample_mtrx.put('Mode', MODE_COARSE)
                self.sample_mtrx.set_mode(self.sample_mtrx.MODE_COARSE)
                #self.xScan.put('P1PV', dct['coarse_pv_nm']['X'] + '.VAL')
                #self.xScan.put('R1PV', dct['coarse_pv_nm']['X'] + '.RBV')
            #                self.xScan.put('BSPV', dct['sample_pv_nm']['X'] + '.VELO')
            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(0) #disabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)
            else:
                #self.sample_mtrx.put('Mode', MODE_LINE_UNIDIR)
                self.sample_mtrx.set_mode(self.sample_mtrx.MODE_LINE_UNIDIR)

                #self.xScan.put('P1PV', dct['fine_pv_nm']['X'] + '.VAL')
                #self.xScan.put('R1PV', dct['fine_pv_nm']['X'] + '.RBV')
                #self.sample_finex.set_power( 1)
                self.sample_finex.set_power(self.sample_mtrx.POWER_ON)

            # self.main_obj.device( DNM_CX_AUTO_DISABLE_POWER ).put(1) #enabled
            # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_LINE_UNIDIR)

            # set Y's scan mode
            if (self.y_roi[SCAN_RES] == COARSE):
                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_COARSE)
                #self.sample_mtry.put('Mode', MODE_COARSE)
                self.sample_mtry.set_mode(self.sample_mtrx.MODE_COARSE)

                #self.yScan.put('P1PV', dct['coarse_pv_nm']['Y'] + '.VAL')
                #self.yScan.put('R1PV', dct['coarse_pv_nm']['Y'] + '.RBV')

            else:

                # self.set_sample_posner_mode(self.sample_mtrx, self.sample_finex, MODE_LINE_UNIDIR)
                # self.sample_mtry.put('Mode', MODE_NORMAL)
                #self.sample_mtry.put('Mode', MODE_LINE_UNIDIR)
                self.sample_mtry.set_mode(self.sample_mtrx.MODE_LINE_UNIDIR)
                #self.yScan.put('P1PV', dct['fine_pv_nm']['Y'] + '.VAL')
                #self.yScan.put('R1PV', dct['fine_pv_nm']['Y'] + '.RBV')
                #self.sample_finey.set_power( 1)
                self.sample_finey.set_power(self.sample_mtry.POWER_ON)

            # self.main_obj.device( DNM_CY_AUTO_DISABLE_POWER ).put(1) #enabled

    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        # if(self.is_pxp):
        #     set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter,
        #                                self.shutter)
        # else:
        #     set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
        pass


    # def on_coarse_sample_scan_counter_changed(self, row, data, counter_name='counter0'):
    #     """
    #     on_sample_scan_counter_changed_hdw_accel(): Used by SampleImageWithEnergySSCAN
    #
    #     :param row: row description
    #     :type row: row type
    #
    #     :param data: data description
    #     :type data: data type
    #
    #     :returns: None
    #     """
    #     """
    #     The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
    #     The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
    #     The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
    #     slot during a point scan will receive a point+1 and in that case it should be ignored.
    #
    #     LIne scan data arrives in the form data[row, < number of x points of values >]
    #
    #     This slot has to handle
    #
    #     """
    #
    #     if(row < 0):
    #         print()
    #         row = 0
    #
    #     sp_id =  int(MAIN_OBJ.device('e712_current_sp_id').get_position())
    #     self.set_spatial_id(sp_id)
    #
    #     if ((self.scan_type == scan_types.OSA_FOCUS) or (self.scan_type == scan_types.SAMPLE_FOCUS)):
    #         nptsy = self.numZ
    #     else:
    #         nptsy = self.numY
    #
    #     _evidx = self.get_evidx()
    #     #_imgidx = MAIN_OBJ.device('e712_image_idx').get_position()
    #     _imgidx = self.base_zero(self.get_imgidx())
    #     _dct = self.get_img_idx_map(_imgidx)
    #     _sp_id = _dct['sp_id']
    #     pol_idx = _dct['pol_idx']
    #     e_idx = _dct['e_idx']
    #
    #     #set the spatial id so that save_hdr can use it
    #     self.set_spatial_id(_sp_id)
    #     #print 'on_sample_scan_counter_changed_hdw_accel: _imgidx=%d row=%d' % (_imgidx, row)
    #
    #     if (self.is_pxp and (not self.use_hdw_accel)):
    #         # Image point by point
    #         point = int(data[0])
    #         val = data[1]
    #
    #         # print 'SampleImageWithEnergySSCAN: on_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
    #         self.data[_imgidx, row, point] = val
    #
    #     else:
    #         # print 'SampleImageWithEnergySSCAN: LXL on_counter_changed: _imgidx, row and data[0:10]=', (_imgidx, row, data[0:10])
    #         point = 0
    #         (wd,) = data.shape
    #         val = data[0:(wd - 1)]
    #
    #     dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
    #     dct[CNTR2PLOT_ROW] = int(row)
    #     dct[CNTR2PLOT_COL] = int(point)
    #     dct[CNTR2PLOT_VAL] = val
    #     #because we could be multi spatial override the default
    #     dct[CNTR2PLOT_SP_ID] = _sp_id
    #
    #     self.img_data[_sp_id][int(row), :] = val
    #
    #     #print 'self.spid_data[%s][%d][%d][%d, %d, :]' % (counter_name,_sp_id,pol_idx,e_idx, int(row))
    #     self.spid_data[counter_name][_sp_id][pol_idx][e_idx, int(row), :] = val
    #     self.sigs.changed.emit(dct)
    #
    #     #now emit progress information
    #     prog = float(float(row + 0.75) / float(nptsy)) * 100.0
    #     if (self.stack):
    #         prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)
    #     else:
    #         prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)
    #
    #     self.low_level_progress.emit(prog_dct)



