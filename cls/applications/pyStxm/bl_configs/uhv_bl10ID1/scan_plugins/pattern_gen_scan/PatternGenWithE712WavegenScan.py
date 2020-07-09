# coding=utf-8
'''
Created on July 26, 2019

@author: bergr
'''
import copy
import time

from bluesky.plans import count, scan, grid_scan, scan_nd
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from bcm.devices.device_names import *
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types

from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan, SIM_SPEC_DATA, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, \
    set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan, make_timestamp_now
from cls.types.stxmTypes import scan_types, scan_sub_types, \
    energy_scan_order_types, sample_positioning_modes, sample_fine_positioning_modes
from cls.scanning.scan_cfg_utils import ensure_valid_values, calc_accRange
from cls.utils.roi_dict_defs import *
from cls.utils.dict_utils import dct_get
from cls.utils.log import get_module_logger
from cls.utils.cfgparser import ConfigClass
from cls.utils.dict_utils import dct_put, dct_get
from cls.utils.memory import get_size
from cls.types.beamline import BEAMLINE_IDS
from cls.utils.prog_dict_utils import make_progress_dict
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
from cls.scan_engine.decorators import conditional_decorator

from cls.scanning.e712_wavegen.e712 import X_WAVE_TABLE_ID
from cls.scanning.e712_wavegen.e712 import E712ControlWidget
from cls.scanning.e712_wavegen.ddl_store import gen_ddl_database_key

from cls.zeromq.epics.epics_api import *

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)




class PatternGenWithE712WavegenScanClass(BaseScan):
    '''
    This class is based on SampleImageWithEnergySSCAN and modified to support the E712 waveform generator
    for executing the low level scan and triggering, the main scan is still controlled by SSCAN records but instead of using sscan records and motor
    positioners to move the motors it uses the E712 waveform generator which must be configured first here.

    The standard BaseScan api will be followed and hte E712 wave generator will only be used if it is :
        - a fine scan
        - the E712 is available
    if the scan is a coarse scan it will not be used, this should work for both zoneplate and standard sample fine scans.

    Note: the configuration is the only thing that changes in order to execute pxp or lxl scans, the data from a pxp scans when using the
    waveform generator are received as a complete line just like lxl scans
    '''


    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(PatternGenWithE712WavegenScanClass, self).__init__(main_obj=MAIN_OBJ)
        self.x_use_reinit_ddl = False
        # self.x_use_ddl = False
        # self.x_use_reinit_ddl = False
        # self.x_start_end_pos = False
        # self.x_force_reinit = False
        self.x_auto_ddl = True
        #self.spid_data = None
        self.img_idx_map = {}
        self.spid_data = {}
        self.start_gate_and_cntr = False
        self.e712_wg = MAIN_OBJ.device('E712ControlWidget')


    def stop(self):
        e712_wdg = self.main_obj.device(DNM_E712_WIDGET)
        e712_wdg.stop_wave_generator()

        #call the parents stop
        super().stop()


    def on_scan_done(self):
        e712_wdg = self.main_obj.device(DNM_E712_WIDGET)
        e712_wdg.on_wavegen_scan_done()


    # def make_scan_plan(self, dets, gate, md=None, bi_dir=False):
    #
    #     self.configure_devs(dets, gate)
    #
    #     if(self.is_pxp):
    #         return(self.make_pxp_scan_plan(dets, gate, md=md, bi_dir=bi_dir))
    #     else:
    #         return (self.make_lxl_scan_plan(dets, gate, md=md, bi_dir=bi_dir))

    def make_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''
        override the default make_scan_plan to set the scan_type
        :param dets:
        :param gate:
        :param md:
        :param bi_dir:
        :return:
        '''
        return (self.make_pattern_generator_plan(dets, gate, md=md, bi_dir=bi_dir))




    # def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
    #     '''
    #
    #     :param dets:
    #     :param gate:
    #     :param md:
    #     :param bi_dir:
    #     :return:
    #     '''
    #     if(self.is_point_spec):
    #         self.scan_type = scan_types.SAMPLE_POINT_SPECTR
    #         return (self.make_single_image_e712_plan(dets, gate, md=md, bi_dir=bi_dir))


    # def make_single_image_e712_plan(self, dets, gate, md=None, bi_dir=False, do_baseline=True):
    #     print('entering: exec_e712_wavgen')
    #     #zp_def = self.get_zoneplate_info_dct()
    #     dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
    #     e712_dev = self.main_obj.device(DNM_E712_OPHYD_DEV)
    #     e712_wdg = self.main_obj.device(DNM_E712_WIDGET)
    #     shutter = self.main_obj.device(DNM_SHUTTER)
    #     ev_mtr = self.main_obj.device(DNM_ENERGY)
    #     pol_mtr = self.main_obj.device(DNM_EPU_POLARIZATION)
    #     e712_x_usetablenum = self.main_obj.device('e712_x_usetablenum')
    #     e712_y_usetablenum = self.main_obj.device('e712_y_usetablenum')
    #     e712_x_start_pos = self.main_obj.device('e712_x_start_pos')
    #     e712_y_start_pos = self.main_obj.device('e712_y_start_pos')
    #     stagers = []
    #     for d in dets:
    #         stagers.append(d)
    #     det = dets[0]
    #     if(self.is_lxl):
    #         stagers.append(gate)
    #         det.set_mode(1)
    #         gate.set_mode(1)
    #         gate.set_num_points(self.x_roi[NPOINTS])
    #         gate.set_trig_src(trig_src_types.E712)
    #     else:
    #         det.set_mode(0)
    #         gate.set_mode(0)
    #         gate.set_num_points(1)
    #         gate.set_trig_src(trig_src_types.E712)
    #
    #     gate.set_dwell(self.dwell)
    #     #det.set_num_points(self.x_roi[NPOINTS])
    #     det.configure(self.x_roi[NPOINTS], self.scan_type)
    #     if(md is None):
    #         md = {'metadata': dict_to_json(self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
    #     # if(not skip_baseline):
    #     #     @bpp.baseline_decorator(dev_list)
    #
    #     @conditional_decorator(bpp.baseline_decorator(dev_list), do_baseline)
    #     @bpp.stage_decorator(stagers)
    #     @bpp.run_decorator(md=md)
    #     def do_scan():
    #         print('starting: make_single_image_e712_plan:  do_scan()')
    #         # load the sp_id for wavegen
    #         x_tbl_id, y_tbl_id = e712_wdg.get_wg_table_ids(self.sp_id)
    #         print('make_single_image_e712_plan: putting x_tbl_id=%d, y_tbl_id=%d' % (x_tbl_id, y_tbl_id))
    #         e712_x_usetablenum.put(x_tbl_id)
    #         e712_y_usetablenum.put(y_tbl_id)
    #         # get the X motor reset position * /
    #         if(self.is_zp_scan):
    #             e712_x_start_pos.put(self.zx_roi[START])
    #             e712_y_start_pos.put(self.zy_roi[START])
    #         else:
    #             e712_x_start_pos.put(self.x_roi[START])
    #             e712_y_start_pos.put(self.y_roi[START])
    #
    #         e712_wdg.set_num_cycles(self.y_roi[NPOINTS])
    #
    #         #yield from bps.stage(gate)
    #         yield from bps.kickoff(det)
    #         # , starts=starts, stops=stops, npts=npts, group='e712_wavgen', wait=True)
    #         # this starts the wavgen and waits for it to finish without blocking the Qt event loop
    #         shutter.open()
    #         yield from bps.mv(e712_dev.run, 1)
    #         shutter.close()
    #         # yield from bps.wait(group='e712_wavgen')
    #         yield from bps.unstage(gate)
    #         yield from bps.complete(det)  # stop minting events everytime the line_det publishes new data!
    #         # yield from bps.unmonitor(det)
    #         # the collect method on e712_flyer may just return as empty list as a formality, but future proofing!
    #         yield from bps.collect(det)
    #         print('make_single_image_e712_plan Leaving')
    #
    #     return (yield from do_scan())


    def make_pattern_generator_plan(self, dets, gate,  md=None, bi_dir=False):
        print('entering: make_pattern_generator_plan')
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        stagers = []
        for d in dets:
            stagers.append(d)

        def do_scan():
            # yield from bps.open_run(md)
            #print('starting: make_stack_image_plan: do_scan()')
            entrys_lst = []
            entry_num = 0
            #idx = 0
            self._current_img_idx = 0
            point_spec_devs_configd = False
            prev_entry_nm = ''
            # , starts=starts, stops=stops, npts=npts, group='e712_wavgen', wait=True)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            #now load and execute each spatial region
            # mtr_y.msta_dct.msta_fields
            mtr_x = self.main_obj.get_sample_fine_positioner('X')
            mtr_y = self.main_obj.get_sample_fine_positioner('Y')
            if (not self.motor_ready_check([mtr_x, mtr_y])):
                _logger.error(
                    'The scan cannot execute because one or more motors for the scan are not in a ready state')
                return (None)

            for sp_id in self.sp_ids:
                self.sp_id = sp_id
                self.dwell = self.sp_rois[sp_id][SPDB_EV_ROIS][0][DWELL]
                gate.set_dwell(self.dwell)
                print('make_pattern_generator_plan: scanning pad %d, setting dwell=%.2f' % (sp_id+1, self.dwell))
                _logger.info('make_pattern_generator_plan: scanning pad %d, setting dwell=%.2f' % (sp_id+1, self.dwell))
                gate.set_trig_src(trig_src_types.NORMAL_PXP)
                gate.set_mode(bs_dev_modes.NORMAL_PXP)

                # need to handle this better for multiple detectors, in the future todo
                dets[0].set_dwell(self.dwell)

                #this updates member vars x_roi, y_roi, etc... with current spatial id specifics
                self.update_roi_member_vars(self.sp_rois[self.sp_id])

                # take a single image that will be saved with its own run scan id
                #img_dct = self.img_idx_map['%d' % idx]
                img_dct = self.img_idx_map['%d' % self._current_img_idx]

                md = {'metadata': dict_to_json(
                    self.make_standard_metadata(entry_name=img_dct['entry'], scan_type=self.scan_type, dets=dets))}
                #if(entry_num is 0):
                #if(img_dct['entry'] is not prev_entry_nm):
                # if(img_dct['entry'] not in entrys_lst):
                #     #only create the entry once
                #     #yield from self.make_single_image_e712_plan(dets, gate, md=md, do_baseline=True)
                #     yield from self.make_single_pxp_image_plan(dets, gate, md=md, do_baseline=True)
                #
                # else:
                #     #this data will be used to add to previously created entries
                #     #yield from self.make_single_image_e712_plan(dets, gate, md=md, do_baseline=False)
                #     yield from self.make_single_pxp_image_plan(dets, gate, md=md, do_baseline=False)
                #make sure there is a single baseline reading of devices
                if(self._current_img_idx is 0):
                    do_baseline = True
                else:
                    do_baseline = False
                yield from self.make_single_pxp_image_plan(dets, gate, md=md, do_baseline=do_baseline)
                #entry_num += 1
                #idx += 1
                self._current_img_idx += 1
                #prev_entry_nm = img_dct['entry']
                entrys_lst.append(img_dct['entry'])


            print('make_pattern_generator_plan Leaving')

            # yield from bps.close_run()

        return (yield from do_scan())

    def on_this_scan_done(self):
        # self.shutter.close()
        # self.gate.stop()
        # self.counter.stop()
        # self.save_hdr()
        # self.on_save_sample_image()
        pass

    def on_scan_done_discon_sigs(self):
        """
        on_scan_done(): fires when the top level scan is done, calls on_child_scan_done() if one has been
        configured by parent scan plugin

        :returns: None
        """

        if (self.signals_connected):
            # _logger.debug('BaseScan: on_scan_done_discon_sigs: emitted all_done sig')
            self.all_done.emit()
        else:
            _logger.debug('BaseScan: on_scan_done_discon_sigs: ELSE: sigs were not connected')
        # if(done):
        self.disconnect_signals()

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
        super(PatternGenWithE712WavegenScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        _logger.info('\n\nSampleImageWithE712Wavegen: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
#         self.set_spatial_id(sp_id)
#         self.wdg_com = wdg_com
#         self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
#         self.sp_ids = list(self.sp_rois.keys())
#         self.sp_id = sp_id
#         self.sp_db = self.sp_rois[sp_id]
#         self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
#         self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
#         self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()
#         self.sample_fine_positioning_mode = MAIN_OBJ.get_fine_sample_positioning_mode()
#
#         self.update_roi_member_vars(self.sp_db)
#
#         #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
#         # this is done in sscan2
#         # self.xyScan = self._scan2
#
#         self.determine_scan_res()
#
#         # dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))
#         # the sample motors have different modes, make a call to handle that they are setup correctly for this scan
# #        self.configure_sample_motors_for_scan()
#
#         if (ev_idx == 0):
#             self.reset_evidx()
#             self.reset_imgidx()
#             self.reset_pnt_spec_spid_idx()
#             self.final_data_dir = None
#             self.update_dev_data = []
#
#         if(len(self.sp_ids) > 1):
#             self.is_multi_spatial = True
#             #if multi spatial then just save everything without prompting
#             self.set_save_all_data(True)
#         else:
#             self.is_multi_spatial = False
#             self.set_save_all_data(False)
#
#         # get the energy and EOU related setpoints
#         e_roi = self.e_rois[ev_idx]
#         self.setpointsDwell = dct_get(e_roi, DWELL)
#         # self.setpointsPol = self.convert_polarity_points(dct_get(e_roi, 'EPU_POL_PNTS'))
#         self.setpointsPol = dct_get(e_roi, EPU_POL_PNTS)
#         self.setpointsOff = dct_get(e_roi, EPU_OFF_PNTS)
#         self.setpointsAngle = dct_get(e_roi, EPU_ANG_PNTS)
#         self.ev_pol_order = dct_get(e_roi, EV_POL_ORDER)
#
#         sps = dct_get(self.wdg_com, SPDB_SINGLE_LST_SP_ROIS)
#         evs = dct_get(self.wdg_com, SPDB_SINGLE_LST_EV_ROIS)
#         pols = dct_get(self.wdg_com, SPDB_SINGLE_LST_POL_ROIS)
#         dwells = dct_get(self.wdg_com, SPDB_SINGLE_LST_DWELLS)
#         sub_type = dct_get(self.wdg_com, SPDB_SCAN_PLUGIN_SUBTYPE)
#         if(sub_type is scan_sub_types.POINT_BY_POINT):
#             self.is_pxp = True
#             self.is_lxl = False
#         else:
#             self.is_pxp = False
#             self.is_lxl = True
#
#         self.use_hdw_accel = dct_get(self.sp_db, SPDB_HDW_ACCEL_USE)
#         if (self.use_hdw_accel is None):
#             self.use_hdw_accel = False
#             self.e712_enabled = False
#             #force the wave table rate to be 10 so that all pattern pads will be calc to use same rate
#             #self.e712_wg.set_forced_rate(10)
#
#         self.is_fine_scan = True
#         #override
#         if(not self.is_fine_scan):
#             #coarse scan so turn hdw accel flag off
#             self.use_hdw_accel = False
#
#         if(self.use_hdw_accel):
#             self.e712_enabled = True
#             # self.save_hdr = self.hdw_accel_save_hdr
#
#             #set the DDL flags
#             if(dct_get(self.sp_db, SPDB_HDW_ACCEL_AUTO_DDL)):
#                 self.x_auto_ddl = True
#                 self.x_use_reinit_ddl = False
#             else:
#                 #Reinit DDL for the current scan
#                 self.x_auto_ddl = False
#                 self.x_use_reinit_ddl = True
#
#         # setup some convienience member variables
#         self.dwell = e_roi[DWELL]
#         self.numX = int(self.x_roi[NPOINTS])
#         self.numY = int(self.y_roi[NPOINTS])
#         self.numZX = int(self.zx_roi[NPOINTS])
#         self.numZY = int(self.zy_roi[NPOINTS])
#         self.numEPU = len(self.setpointsPol)
#         self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
#
#         self.numSPIDS = len(self.sp_rois)

        if (self.scan_type != scan_types.SAMPLE_POINT_SPECTRUM):
            self.numImages = int(self.sp_db[SPDB_EV_NPOINTS] * self.numEPU * self.numSPIDS)
        else:
            # is a sample point spectrum
            self.numImages = 1

        # set some flags that are used elsewhere
        if (self.numImages > 1):
            self.stack = True
            self.save_all_data = True
        else:
            self.stack = False

        self.is_lxl = False
        self.is_pxp = False
        self.is_point_spec = False
        self.file_saved = False
        self.sim_point = 0

        if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
            # LINE_UNIDIR
            self.is_lxl = True
        else:
            # POINT_BY_POINT
            self.is_pxp = True

        if (self.fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
            self.is_zp_scan = True
        else:
            self.is_zp_scan = False
            # determine and setup for line or point by point
        self.ttl_pnts = 0

        # depending on the scan size the positioners used in the scan will be different, use a singe
        # function to find out which we are to use and return those names in a dct
        dct = self.determine_samplexy_posner_pvs(force_fine_scan=True)

        # depending on the current samplpositioning_mode perform a different configuration
        if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            if(self.use_hdw_accel):
                self.config_for_goniometer_scan_hdw_accel(dct)
            else:
                self.config_for_goniometer_scan(dct)

        else:
            if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
                # goniometer_zoneplate mode
                self.configure_for_zxzy_fine_scan_hdw_accel(dct)
            elif((self.sample_positioning_mode == sample_positioning_modes.COARSE) and (self.fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE)):
                self.configure_for_coarse_zoneplate_fine_scan_hdw_accel(dct)
            else:
                # coarse_samplefine mode
                self.configure_for_samplefxfy_fine_scan_hdw_accel(dct)
        # move Gx and Gy to center of scan, is it within a um?



        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        self.seq_map_dct = self.generate_2d_seq_image_map(1, self.y_roi[NPOINTS], self.x_roi[NPOINTS], lxl=self.is_lxl)

        # THIS must be the last call
        self.finish_setup()

        self.new_spatial_start.emit(sp_id)


    def configure_for_coarse_scan(self, dct):
        '''
        if this is executed the assumption is that the zoneplate will be stationary and the Fx Fy stages will be off
        because the scan will be accomplished by moving the sample with the coarse motors only
        :return:
        '''
        self.xScan = self._scan1
        self.yScan = self._scan2
        self.xyScan = None
        self.config_for_sample_holder_scan(dct)


    def configure_for_zxzy_fine_scan_hdw_accel(self, dct, is_focus=False):
        """
        For a goniometer scan this will always be a fine scan of max range 100x100um (actually less)
        and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
        and set the +/- scan range to be about Zoneplate XY center (0,0)

        Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

        Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
        triggering of the waveform generator, will still need to do something so that save_hdr has something to get data
        from, not sure how to handle this yet.

        """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        self.main_obj.device(DNM_ZONEPLATE_X).set_velo(1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).set_velo(1000000.0)

        self.set_config_devices_func(self.on_this_dev_cfg)

        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_ZONEPLATE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_ZONEPLATE_Y)

        # move Gx and Gy to center of scan, is it within a um?
        if (self.zx_roi[CENTER] != 0.0):
            # zx is moving to scan center
            pass
        else:
            # Gx is moving to scan center nd zx is centered around 0, so move Gx to scan center
            self.main_obj.device(dct['cx_name']).put('user_setpoint', self.gx_roi[CENTER])

        # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
        if (self.zy_roi[CENTER] != 0.0):
            # zy is moving to scan center
            pass
        else:
            # Gy is moving to scan center nd zy is centered around 0, so move Gy to scan center
            self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])

        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY

        self.sample_mtrx.put('Mode', 0)

        #setup the E712 wavtable's and other relevant params
        self.modify_config_for_hdw_accel()

    def configure_for_samplefxfy_fine_scan_hdw_accel(self, dct):
        '''
        if this is executed the assumption is that the the scan will be a sampleFx Fy fine scan, it should make sure the
        SampleX and SampleY stages are in their start positions the wavegen tables and set the starting offset (which
        will be the big difference)
        :return:
        '''
        """
                For a fine scan this will always be a scan of max range 100x100um (actually less)
                and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
                and set the +/- scan range to be about Fine XY center (0,0)

                Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

                Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
                triggering of the waveform generator.

                """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        # must be FxFy
        self.main_obj.device(DNM_SAMPLE_FINE_X).set_power( 1)
        self.main_obj.device(DNM_SAMPLE_FINE_Y).set_power( 1)

        self.main_obj.device(DNM_SAMPLE_FINE_X).set_velo(100000.0)
        self.main_obj.device(DNM_SAMPLE_FINE_Y).set_velo(100000.0)

        #this scan is used with and without the goniometer so setupScan maybe None
        # if(self.setupScan):
        #     self.setupScan.set_positioner(1, self.main_obj.device(DNM_SAMPLE_X))
        #     self.setupScan.set_positioner(2, self.main_obj.device(DNM_SAMPLE_Y))

        #these are the SampleX SampleY motors
        cx_mtr = self.main_obj.device(dct['cx_name'])
        cy_mtr = self.main_obj.device(dct['cy_name'])

        cx_mtr.put('Mode', 0)  # MODE_NORMAL
        cy_mtr.put('Mode', 0)  # MODE_NORMAL

        self.set_config_devices_func(self.on_this_dev_cfg)
        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_SAMPLE_FINE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_SAMPLE_FINE_Y)


        # move Gx and Gy to center of scan, is it within a um?
        # Sx is moving to scan center nd fx is centered around 0, so move Sx to scan center
        cx_mtr.move(self.x_roi[CENTER])
        self.sample_finex.put('user_setpoint', self.x_roi[CENTER])
        #self.main_obj.device(dct['cx_name']).put('user_setpoint', self.x_roi[CENTER])

        # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
        # Sy is moving to scan center nd fy is centered around 0, so move Sy to scan center
        #self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])
        cy_mtr.move(self.y_roi[CENTER])


        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY

        # setup the E712 wavtable's and other relevant params
        self.modify_config_for_hdw_accel()

    def configure_for_coarse_zoneplate_fine_scan_hdw_accel(self, dct):
        '''
        if this is executed the assumption is that the the scan will be a sampleFx Fy fine scan, it should make sure the
        SampleX and SampleY stages are in their start positions the wavegen tables and set the starting offset (which
        will be the big difference)
        :return:
        '''
        """
                For a fine scan this will always be a scan of max range 100x100um (actually less)
                and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
                and set the +/- scan range to be about Fine XY center (0,0)

                Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)

                Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
                triggering of the waveform generator.

                """
        ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
        # must be FxFy
        self.main_obj.device(DNM_ZONEPLATE_X).set_power( 1)
        self.main_obj.device(DNM_ZONEPLATE_Y).set_power( 1)

        self.main_obj.device(DNM_ZONEPLATE_X).set_velo(1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).set_velo(1000000.0)

        #this scan is used with and without the goniometer so setupScan maybe None
        # if(self.setupScan):
        #     self.setupScan.set_positioner(1, self.main_obj.device(DNM_SAMPLE_X))
        #     self.setupScan.set_positioner(2, self.main_obj.device(DNM_SAMPLE_Y))

        #these are the SampleX SampleY motors
        #cx_mtr = self.main_obj.device(dct['cx_name'])
        #cy_mtr = self.main_obj.device(dct['cy_name'])

        #cx_mtr.put('Mode', 0)  # MODE_NORMAL
        #cy_mtr.put('Mode', 0)  # MODE_NORMAL

        self.set_config_devices_func(self.on_this_dev_cfg)
        self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_SAMPLE_X)
        self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_SAMPLE_Y)

        self.sample_mtrx.put('Mode', 0)  # MODE_NORMAL
        self.sample_mtry.put('Mode', 0)  # MODE_NORMAL

        # Sx is moving to scan center nd fx is centered around 0, so move Sx to scan center
        #cx_mtr.move(self.x_roi[CENTER])
        #self.sample_finex.put('user_setpoint', self.x_roi[CENTER])
        #self.sample_mtrx.put('user_setpoint', self.x_roi[CENTER])
        self.sample_mtrx.put('user_setpoint', self.x_roi[START])

        #cy_mtr.move(self.y_roi[CENTER])
        #self.sample_mtry.put('user_setpoint', self.y_roi[CENTER])
        self.sample_mtry.put('user_setpoint', self.y_roi[START])


        # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
        # the setupScan will be executed as the top level but not monitored
        self.num_points = self.numY

        # setup the E712 wavtable's and other relevant params
        self.modify_config_for_hdw_accel()


