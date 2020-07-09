'''
Created on Sep 26, 2016

@author: bergr
'''
import copy
from bluesky.plans import count, scan, grid_scan, scan_nd
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from cycler import cycler

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from bcm.devices.device_names import *
from bcm.devices import E712WGDevice
from cls.scanning.BaseScan import BaseScan, MODE_SCAN_START
# from cls.scanning.SScanClass import SScanClass
# from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, \
#     set_devices_for_e712_wavegen_point_scan, set_devices_for_e712_wavegen_line_scan, make_timestamp_now

from cls.types.stxmTypes import scan_sub_types, sample_positioning_modes, sample_fine_positioning_modes
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.roi_dict_defs import *
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types

_logger = get_module_logger(__name__)


class FocusE712ScanClass(BaseScan):
    '''
    This scan uses the SampleX and SampleY stages which allows the scan to be done as a line by line instead of
    the point by point scan which is required by the stages that cannot trigger on position such as the OSAFocus scan
    that is why this scan is left as an X, Y, Z scan instead of an XY, Z scan
    '''

    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(FocusE712ScanClass, self).__init__(main_obj=main_obj)
        self.x_auto_ddl = True
        self.x_use_reinit_ddl = False
        self.use_hdw_accel = True

        self.img_idx_map = {}
        self.spid_data = {}
        self.e712_wg = MAIN_OBJ.device('E712ControlWidget')

    def init_subscriptions(self, ew, func):
        '''
        over ride the base init_subscriptions because we need to use the number of rows from the self.zz_roi instead of
        self.y_roi
        :param ew:
        :param func:
        :return:
        '''

        if(self.is_pxp):
            self._emitter_cb = ImageDataEmitter(DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE, x=DNM_SAMPLE_X,
                                                    scan_type=self.scan_type, bi_dir=self._bi_dir)
            self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS], seq_dct=self.seq_map_dct)
            self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            self._emitter_cb.new_plot_data.connect(func)
        else:


            # self._emitter_cb = ImageDataEmitter(DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE,
            #                                     x=DNM_SAMPLE_X,
            #                                     scan_type=self.scan_type, bi_dir=self._bi_dir)
            # self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            # self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            # self._emitter_cb.new_plot_data.connect(func)
            pass


    def get_xy_scan_motors(self):
        '''
        based on the scanning mode we are in return the correct x and y motors devices
        :return:
        '''

        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()

        mtr_x = self.main_obj.device(DNM_ZONEPLATE_X)
        mtr_y = self.main_obj.device(DNM_ZONEPLATE_Y)


    def configure_devs(self, dets, gate):
        if (self.is_pxp):
            gate.set_trig_src(trig_src_types.NORMAL_PXP)
            gate.set_num_points(1)
            gate.set_mode(bs_dev_modes.NORMAL_PXP)
        else:
            # if (self.is_lxl):
            dets[0].set_mode(1)
            gate.set_mode(1)
            gate.set_num_points(self.x_roi[NPOINTS])
            gate.set_trig_src(trig_src_types.E712)

        gate.set_dwell(self.dwell)
        gate.configure()

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        point_det = dets[0]
        # gate.set_num_points(1)
        # gate.set_mode(0)
        point_det.configure()
        #gate.set_trig_src(trig_src_types.E712)
        #the rest of the gate configuration is handled when it is staged
        skip_lst = [DNM_FINE_X, DNM_FINE_Y, DNM_FINE_ZX, DNM_FINE_ZX]
        mtr_dct = self.determine_samplexy_posner_pvs()
        e712_dev = E712WGDevice('IOCE712:', name='e712_wgenerator_flyerdev')
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list(skip_lst)
        self._bi_dir = bi_dir
        #zp_def = self.get_zoneplate_info_dct()
        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()

        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, dets=dets))}
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        def do_scan():
            #need to decide here which x and y motor we will be using for focus
            shutter = self.main_obj.device(DNM_SHUTTER)
            samplemtrx = self.main_obj.get_sample_positioner('X')
            samplemtry = self.main_obj.get_sample_positioner('Y')
            finemtrx = self.main_obj.get_sample_fine_positioner('X')
            finemtry = self.main_obj.get_sample_fine_positioner('Y')
            # if (self.is_fine_scan):
            #     mtr_x = self.main_obj.device(mtr_dct['fx_name'])
            #     mtr_y = self.main_obj.device(mtr_dct['fy_name'])
            # else:
            #     mtr_x = self.main_obj.device(mtr_dct['cx_name'])
            #     mtr_y = self.main_obj.device(mtr_dct['cy_name'])
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)

            if (self.is_zp_scan):
                # moving them to the start gets rid of a goofy first line of the scan
                #mtr_x.move(self.zx_roi[START])
                #mtr_y.move(self.zy_roi[START])
                #yield from bps.mv(mtr_x, self.zx_roi[CENTER], mtr_y, self.zx_roi[CENTER])
                x_traj = cycler(finemtrx, self.zx_roi[SETPOINTS])
                y_traj = cycler(finemtry, self.zy_roi[SETPOINTS])
                yield from bps.mv(finemtrx, self.zx_roi[CENTER], finemtry, self.zy_roi[CENTER])

            else:
                # !!! THIS NEEDS TESTING
                # moving them to the start gets rid of a goofy first line of the scan
                # finemtrx.move(self.x_roi[START])
                # finemtry.move(self.y_roi[START])
                # samplemtrx.move(self.x_roi[START], wait=True)
                # samplemtry.move(self.y_roi[START], wait=True)
                #yield from bps.mv(mtr_x, self.x_roi[START], mtr_y, self.y_roi[START])
                x_traj = cycler(finemtrx, self.x_roi[SETPOINTS])
                y_traj = cycler(finemtry, self.y_roi[SETPOINTS])
                yield from bps.mv(finemtrx, self.x_roi[CENTER], finemtry, self.y_roi[CENTER])
                ############################

            # x_traj = cycler(mtr_x, self.x_roi[SETPOINTS])
            # y_traj = cycler(mtr_y, self.y_roi[SETPOINTS])
            zz_traj = cycler(mtr_z, self.zz_roi[SETPOINTS])

            yield from bps.stage(gate)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            # the detector will be staged automatically by the grid_scan plan
            #open shutter
            shutter.open()
            yield from scan_nd(dets, zz_traj * (y_traj + x_traj), md=md)
            #close shutter
            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)

            print('FocusE712ScanClass: PXP make_scan_plan Leaving')

        return (yield from do_scan())

    # def make_lxl_scan_plan(self, dets, gate, md=None, bi_dir=False):
    #     '''
    #     :param dets:
    #     :param gate:
    #     :param bi_dir:
    #     :return:
    #     '''
    #     #config detector and gate for num points etc
    #     flyer_det = dets[0]
    #     #gate.set_num_points(self.x_roi[NPOINTS])
    #     #gate.set_mode(1) #line
    #     #gate.set_trig_src(trig_src_types.E712)
    #     flyer_det.configure(self.x_roi[NPOINTS], self.scan_type)
    #     e712_dev = self.main_obj.device(DNM_E712_OPHYD_DEV)
    #     dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
    #     self._bi_dir = bi_dir
    #
    #     if (md is None):
    #         md = {'metadata': dict_to_json(
    #             self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
    #     @bpp.baseline_decorator(dev_list)
    #     @bpp.stage_decorator(dets)
    #     @bpp.run_decorator(md=md)
    #     def do_scan():
    #
    #         mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
    #         shutter = self.main_obj.device(DNM_SHUTTER)
    #
    #         #yield from bps.open_run(md)
    #         yield from bps.kickoff(flyer_det)
    #         yield from bps.stage(gate)
    #
    #         yield from bps.sleep(0.5)
    #
    #         shutter.open()
    #         for sp in self.zz_roi[SETPOINTS]:
    #             yield from bps.mv(mtr_z, sp)
    #             #let zoneplateZ damp a little
    #             yield from bps.sleep(0.5)
    #
    #             yield from bps.mv(e712_dev.run, 1)
    #         shutter.close()
    #         yield from bps.unstage(gate)
    #
    #         yield from bps.complete(flyer_det)  # stop minting events everytime the line_det publishes new data!
    #         # the collect method on e712_flyer may just return as empty list as a formality, but future proofing!
    #         yield from bps.collect(flyer_det)
    #
    #         #yield from bps.close_run()
    #
    #         print('FocusE712ScanClass: LXL make_scan_plan Leaving')
    #
    #     return (yield from do_scan())
    def make_lxl_scan_plan(self, dets, gate, md=None, bi_dir=False):
        '''
        :param dets:
        :param gate:
        :param bi_dir:
        :return:
        '''
        # config detector and gate for num points etc
        flyer_det = dets[0]
        # gate.set_num_points(self.x_roi[NPOINTS])
        # gate.set_mode(1) #line
        # gate.set_trig_src(trig_src_types.E712)
        flyer_det.configure(self.x_roi[NPOINTS], self.scan_type)
        e712_dev = self.main_obj.device(DNM_E712_OPHYD_DEV)
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir

        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, dets=dets))}

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        @bpp.run_decorator(md=md)
        def do_scan():
            finemtrx = self.main_obj.get_sample_fine_positioner('X')
            finemtry = self.main_obj.get_sample_fine_positioner('Y')
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
            #make sure the servo for zpz is on
            mtr_z.set_power( 1)

            shutter = self.main_obj.device(DNM_SHUTTER)
            if (self.is_zp_scan):
                # moving them to the start gets rid of a goofy first line of the scan
                yield from bps.mv(finemtrx, self.zx_roi[START], finemtry, self.zy_roi[START])

            else:
                # !!! THIS NEEDS TESTING
                # moving them to the start gets rid of a goofy first line of the scan
                yield from bps.mv(finemtrx, self.x_roi[START], finemtry, self.y_roi[START])
                ############################

            #this get rid of crappy first 2 lines of scan?
            for i in range(2):
                yield from bps.mv(e712_dev.run, 1)
                #yield from bps.sleep(0.5)

            # yield from bps.open_run(md)
            yield from bps.kickoff(flyer_det)
            yield from bps.stage(gate)

            shutter.open()
            for sp in self.zz_roi[SETPOINTS]:
                yield from bps.mv(mtr_z, sp)
                # let zoneplateZ damp a little
                #yield from bps.sleep(0.5)

                yield from bps.mv(e712_dev.run, 1)
            shutter.close()
            yield from bps.unstage(gate)

            yield from bps.complete(flyer_det)  # stop minting events everytime the line_det publishes new data!
            # the collect method on e712_flyer may just return as empty list as a formality, but future proofing!
            yield from bps.collect(flyer_det)

            # yield from bps.close_run()

            print('FocusE712ScanClass: LXL make_scan_plan Leaving')

        return (yield from do_scan())

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
        # call the base class configure so that all member vars can be initialized
        super(FocusE712ScanClass, self).configure(wdg_com, sp_id=sp_id, line=line)

        self.main_obj.device('e712_current_sp_id').put(sp_id)

        dct_put(self.sp_db, SPDB_RECT,(self.x_roi[START], self.zz_roi[START], self.x_roi[STOP], self.zz_roi[STOP]))

        self.reset_evidx()
        self.reset_imgidx()
        self.init_set_scan_levels()

        dct = self.determine_samplexy_posner_pvs()

        self.stack = False

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        # self.data_shape = ('numE', 'numZ', 'numX')
        self.config_hdr_datarecorder(self.stack)
        # self.stack_scan = stack

        # setup the E712 wavtable's and other relevant params
        if(self.is_lxl):
            self.modify_config_for_hdw_accel()

        #if pxp it is done without hardware but scan_nd instead

        self.seq_map_dct = self.generate_2d_seq_image_map(1, self.zz_roi[NPOINTS], self.x_roi[NPOINTS], lxl=self.is_lxl)

        # THIS must be the last call
        self.finish_setup()



    def modify_config_for_hdw_accel(self):
        '''
        Here I need to make the calls to send the commands that generate the waveform on the E712 for the current E_roi, by the end
        of this function everything should be ready  (as far as the E712 is concerned) to just call
            IOCE712:ExecWavgen by the sscan record

        This function needs to :
         - program the E712 with all sp_roi's for each dwell time using 1 wavtable per dwell time
        and spatial region.
         - set the number of points in the sscan record that starts the E712 wavegenerator to the number of wavtables used above
         - set the P1(x) and P2(y) PxPA tables in the sscan record that starts the E712 wavegenerator with the wavtable
         numbers that were used above


        :return:
        '''
        sample_positioning_mode = self.main_obj.get_sample_positioning_mode()
        fine_sample_positioning_mode = self.main_obj.get_fine_sample_positioning_mode()
        #start gate and counters
        if (self.is_pxp):
            mode = 0
        else:
            mode = 1

        # create usetable map
        wavtable_map = self.e712_wg.create_wavgen_usetable_map(self.sp_ids)
        # clear previous wavetables
        self.e712_wg.clear_wavetables()
        self.e712_wg.clear_wavgen_use_tbl_ids()
        self.e712_wg.clear_start_modes()


        #for the current ev index
        #for each sp_db in sp_rois call sendwave() to create the wavetable on the E712 and add wavtable ID to list,
        #keep a running total of number of wavtables used starting from 1
        #set the NPTS of the btm sscan to equal the total number of wavtables used above
        #for each P1 and P2 of the bottom level sscan record write the list of each wavtable ID's to the sscan rec

        #self.img_data = {}

        IMMEDIATELY = 1

        ttl_wavtables = 0
        #the following lists are populated and then written to placeholder waveform PV's that will be used
        #by SNL code to load the next set of params for the next spatial region as they are being executed
        sp_roi_ids = []

        sp_id = self.get_spatial_id()

        sp_db = self.sp_rois[sp_id]
        e_rois = dct_get(sp_db, SPDB_EV_ROIS)
        ev_idx = self.get_evidx()
        dwell = e_rois[ev_idx][DWELL]

        # if(fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
        if (sample_positioning_mode == sample_positioning_modes.GONIOMETER):
            x_roi = dct_get(sp_db, SPDB_ZX)
            y_roi = dct_get(sp_db, SPDB_ZY)
            x_npnts = x_roi[NPOINTS]
            y_npnts = 1

        else:
            x_roi = dct_get(sp_db, SPDB_X)
            y_roi = dct_get(sp_db, SPDB_Y)
            x_npnts = x_roi[NPOINTS]
            y_npnts = 1

        x_reset_pos = x_roi[START]
        y_reset_pos = y_roi[START]
        x_axis_id = self.base_zero(self.e712_wg.get_x_axis_id())
        y_axis_id = self.base_zero(self.e712_wg.get_y_axis_id())

        sp_roi_ids.append(sp_id)
        # build a list of wavtable IDs used for this scan
        x_wavtbl_id = wavtable_map[sp_id][x_axis_id]
        y_wavtbl_id = wavtable_map[sp_id][y_axis_id]
        x_npnts = int(x_npnts)
        y_npnts = int(y_npnts)
        x_reset_posn = x_reset_pos
        y_reset_posn = y_reset_pos

        x_start_mode = IMMEDIATELY
        y_start_mode = IMMEDIATELY

        ddl_data = None
        if (self.is_pxp):
            mode = 0
            # program waveforms into tables
            self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
                                   x_force_reinit=self.x_use_reinit_ddl)
            x_useddl_flag = 0
            x_reinitddl_flag = 0
            x_startatend_flag = 0
        else:
            mode = 1
            # program waveforms into tables
            ddl_data = self.e712_wg.send_wave(sp_id, x_roi, y_roi, dwell, mode, x_auto_ddl=self.x_auto_ddl,
                                       x_force_reinit=self.x_use_reinit_ddl, do_datarecord=False)


            #ddl_data = self.e712_wg.get_stored_ddl_table()
            ddl_tbl_pv = MAIN_OBJ.device('e712_ddl_tbls')
            if(ddl_data is not None):
                print('load this ddl table into the pvs for this spatial region')

                ddl_tbl_pv[ttl_wavtables].put(ddl_data)
                x_useddl_flag = 1
                x_reinitddl_flag = 0
                x_startatend_flag = 0
            else:
                print('set the ddl pv waveform to 0s')
                ddl_tbl_pv[ttl_wavtables].put([0,0,0,0,0,0])
                x_useddl_flag = 0
                x_reinitddl_flag = 1
                x_startatend_flag = 0

        #keep running total
        ttl_wavtables += 1

        #now set the waveform generator params to execute this one scan
        #self.e712_wg.e712.num_cycles.put(1)
        self.e712_wg.set_num_cycles(1)
        self.e712_wg.e712.x_start_pos.put(x_reset_posn)
        self.e712_wg.e712.y_start_pos.put(y_reset_posn)

        #set flags
        if (fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
            x_wgen = self.e712_wg.e712.wg3
            y_wgen = self.e712_wg.e712.wg4
        else:
            x_wgen = self.e712_wg.e712.wg1
            y_wgen = self.e712_wg.e712.wg2

        #x_wgen.wavgen_usetbl_num.put(x_wavtbl_id)
        #y_wgen.wavgen_usetbl_num.put(y_wavtbl_id)

        x_wgen.start_mode.put(x_start_mode)
        y_wgen.start_mode.put(y_start_mode)

        x_wgen.use_ddl.put(x_useddl_flag)
        y_wgen.use_ddl.put(0)

        x_wgen.use_reinit_ddl.put(x_reinitddl_flag)
        y_wgen.use_reinit_ddl.put(0)

        x_wgen.start_at_end_pos.put(x_startatend_flag)
        y_wgen.start_at_end_pos.put(0)

        #this should always be 1
        #self.setupScan.put('NPTS', ttl_wavtables)


        #need to make sure that the gate and counter are running before leaving here
        _logger.info('Estemated time to complete scan is: %s' % self.e712_wg.get_new_time_estemate())

    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        this is an API method to configure the gate, shutter and counter devices for this scan
        """
        # if((self.is_pxp) or (self.is_point_spec)):
        # if (self.is_pxp):
        #     if (self.use_hdw_accel):
        #         set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numX, self.counter,
        #                                                 numE=self.numE)
        #         # set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numX, counter, numE=0)
        #     else:
        #         # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
        #         set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate,
        #                                    self.counter,
        #                                    self.shutter)
        # elif (self.is_point_spec):
        #     # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
        #     # numE is used for the number of points for a point spec, here we dont want to use Row etc because
        #     # we handle that here on hte counter handler for point spec
        #     if (self.use_hdw_accel):
        #         # set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.counter)
        #         set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, 99999999, self.numX,
        #                                                 self.counter)
        #     else:
        #         set_devices_for_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.gate, self.counter,
        #                                    self.shutter)
        # else:
        #     if (self.use_hdw_accel):
        #         set_devices_for_e712_wavegen_line_scan(self.dwell, self.numX, self.gate, self.counter)
        #     else:
        #         set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
        pass


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