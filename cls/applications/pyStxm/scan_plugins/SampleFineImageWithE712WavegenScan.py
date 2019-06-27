# coding=utf-8
'''
Created on Dec 8, 2017

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
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
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




class SampleFineImageWithE712WavegenScanClass(BaseScan):
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
        super(SampleFineImageWithE712WavegenScanClass, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), 'SAMPLEXY_EV_WG',
                                                                      main_obj=MAIN_OBJ)
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
        self.e712_enabled = True
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
            # self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE, x=DNM_SAMPLE_X,
            #                                         scan_type=self.scan_type, bi_dir=self._bi_dir)
            # self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            # self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            # self._emitter_cb.new_plot_data.connect(func)
            pass
        else:


            # self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE,
            #                                     x=DNM_SAMPLE_X,
            #                                     scan_type=self.scan_type, bi_dir=self._bi_dir)
            # self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
            # self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
            # self._emitter_cb.new_plot_data.connect(func)
            pass

    # def config_e712_for_lxl(self, sp_ids_lst, x_roi, y_roi, dwell):
    #     self.e712_wg.clear_wavetables()
    #     self.e712_wg.clear_wavgen_use_tbl_ids()
    #     self.e712_wg.clear_start_modes()
    #     self.e712_wg.create_wavgen_usetable_map(sp_ids_lst)
    #     if(self.is_lxl):
    #         self.e712_wg.send_wave(sp_ids_lst[0], x_roi, y_roi, dwell=dwell, mode=1, x_auto_ddl=True, x_force_reinit=False)
    #     else:
    #         self.e712_wg.send_wave(sp_ids_lst[0], x_roi, y_roi, dwell=dwell, mode=0, x_auto_ddl=False,x_force_reinit=False)

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
        if(self.is_point_spec):
            self.scan_type = scan_types.SAMPLE_POINT_SPECTRA
            return (self.make_stack_image_plan(dets, gate, md=md, bi_dir=bi_dir))
        elif(self.numImages is 1):
            self.scan_type = scan_types.SAMPLE_IMAGE
            return (self.make_single_image_e712_plan(dets, gate, md=md, bi_dir=bi_dir))
        else:
            self.scan_type = scan_types.SAMPLE_IMAGE_STACK
            return (self.make_stack_image_plan(dets, gate, md=md, bi_dir=bi_dir))

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

    def make_single_point_spec_plan(self, dets, gate, md=None, bi_dir=False, do_baseline=True):

        print('entering: make_single_point_spec_plan')
        #zp_def = self.get_zoneplate_info_dct()
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        e712_dev = self.main_obj.device(DNM_E712_OPHYD_DEV)
        e712_wdg = self.main_obj.device(DNM_E712_WIDGET)
        shutter = self.main_obj.device(DNM_SHUTTER)
        ev_mtr = self.main_obj.device(DNM_ENERGY)
        pol_mtr = self.main_obj.device(DNM_EPU_POLARIZATION)
        e712_x_usetablenum = self.main_obj.device('e712_x_usetablenum')
        e712_y_usetablenum = self.main_obj.device('e712_y_usetablenum')
        e712_x_start_pos = self.main_obj.device('e712_x_start_pos')
        e712_y_start_pos = self.main_obj.device('e712_y_start_pos')
        stagers = []

        det = dets[0]
        # det.set_mode(0)
        # gate.set_mode(0)
        # gate.set_num_points(1)
        # gate.set_trig_src(trig_src_types.E712)
        #gate.set_dwell(self.dwell)
        #det.set_num_points(self.x_roi[NPOINTS])
        #det.configure(self.x_roi[NPOINTS], self.scan_type)

        if(md is None):
            md = {'metadata': dict_to_json(self.make_standard_data_metadata(entry_name='entry0', scan_type=self.scan_type))}
        # if(not skip_baseline):
        #     @bpp.baseline_decorator(dev_list)

        @conditional_decorator(bpp.baseline_decorator(dev_list), do_baseline)
        @bpp.stage_decorator(stagers)
        @bpp.run_decorator(md=md)
        def do_scan():
            print('starting: make_single_point_spec_plan:  do_scan()')
            # load the sp_id for wavegen
            x_tbl_id, y_tbl_id = e712_wdg.get_wg_table_ids(self.sp_id)
            print('make_single_point_spec_plan: putting x_tbl_id=%d, y_tbl_id=%d' % (x_tbl_id, y_tbl_id))
            e712_x_usetablenum.put(x_tbl_id)
            e712_y_usetablenum.put(y_tbl_id)
            # get the X motor reset position * /
            if(self.is_zp_scan):
                e712_x_start_pos.put(self.zx_roi[START])
                e712_y_start_pos.put(self.zy_roi[START])
            else:
                e712_x_start_pos.put(self.x_roi[START])
                e712_y_start_pos.put(self.y_roi[START])

            e712_wdg.set_num_cycles(self.y_roi[NPOINTS])

            yield from bps.stage(gate)
            yield from bps.stage(det)
            # , starts=starts, stops=stops, npts=npts, group='e712_wavgen', wait=True)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            shutter.open()
            yield from bps.mv(e712_dev.run, 1)
            yield from bps.read(det)
            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            yield from bps.unstage(det)  # stop minting events everytime the line_det publishes new data!
            # yield from bps.unmonitor(det)
            # the collect method on e712_flyer may just return as empty list as a formality, but future proofing!
            #yield from bps.collect(det)
            print('make_single_point_spec_plan Leaving')

        return (yield from do_scan())

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
    #         md = {'metadata': dict_to_json(self.make_standard_data_metadata(entry_name='entry0', scan_type=self.scan_type))}
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


    def make_stack_image_plan(self, dets, gate,  md=None, bi_dir=False):
        print('entering: make_stack_image_plan')
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        stagers = []
        for d in dets:
            stagers.append(d)

        #@bpp.baseline_decorator(dev_list)
        #@bpp.stage_decorator(stagers)
        #@bpp.run_decorator(md=md)
        def do_scan():
            # yield from bps.open_run(md)
            ev_mtr = self.main_obj.device(DNM_ENERGY)
            pol_mtr = self.main_obj.device(DNM_EPU_POLARIZATION)

            print('starting: make_stack_image_plan: do_scan()')
            entrys_lst = []
            entry_num = 0
            idx = 0
            point_spec_devs_configd = False
            prev_entry_nm = ''
            # , starts=starts, stops=stops, npts=npts, group='e712_wavgen', wait=True)
            # this starts the wavgen and waits for it to finish without blocking the Qt event loop
            for ev_roi in self.e_rois:
                #switch to new energy
                for ev_sp in ev_roi[SETPOINTS]:
                    yield from bps.mv(ev_mtr, ev_sp)
                    self.dwell = ev_roi[DWELL]
                    pol_setpoints = ev_roi[EPU_POL_PNTS]
                    for pol in pol_setpoints:
                        # switch to new polarization
                        yield from bps.mv(pol_mtr, pol)

                        #now load and execute each spatial region
                        for sp_id in self.sp_ids:
                            self.sp_id = sp_id
                            #this updates member vars x_roi, y_roi, etc... with current spatial id specifics
                            self.update_roi_member_vars(self.sp_rois[self.sp_id])
                            if(self.is_point_spec and (not point_spec_devs_configd)):
                                #config the det and gate
                                dets[0].set_mode(bs_dev_modes.NORMAL_PXP)
                                gate.set_mode(bs_dev_modes.NORMAL_PXP)
                                gate.set_num_points(1)
                                gate.set_trig_src(trig_src_types.E712)
                                gate.set_dwell(self.dwell)
                                dets[0].configure()
                                point_spec_devs_configd = True

                            # take a single image that will be saved with its own run scan id
                            img_dct = self.img_idx_map['%d'%idx]
                            md = {'metadata': dict_to_json(
                                self.make_standard_data_metadata(entry_name=img_dct['entry'], scan_type=self.scan_type))}
                            #if(entry_num is 0):
                            #if(img_dct['entry'] is not prev_entry_nm):
                            if(img_dct['entry'] not in entrys_lst):
                                #only create the entry once
                                if(self.is_point_spec):
                                    yield from self.make_single_point_spec_plan(dets, gate, md=md, do_baseline=True)
                                else:
                                    yield from self.make_single_image_e712_plan(dets, gate, md=md, do_baseline=True)

                            else:
                                #this data will be used to add to previously created entries
                                if (self.is_point_spec):
                                    yield from self.make_single_point_spec_plan(dets, gate, md=md, do_baseline=False)
                                else:
                                    yield from self.make_single_image_e712_plan(dets, gate, md=md, do_baseline=False)

                            #entry_num += 1
                            idx += 1
                            #prev_entry_nm = img_dct['entry']
                            entrys_lst.append(img_dct['entry'])

            print('make_stack_image_plan Leaving')

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

    # def on_single_image_scan_done(self):
    #     '''
    #     THis is called on_scan_done if there are only 1 images being acquired
    #     :return:
    #     '''
    #     self.shutter.close()
    #     self.gate.stop()
    #     self.counter.stop()
    #
    #     #counter = self.counter_dct.keys()[0]
    #     counter = DNM_DEFAULT_COUNTER
    #     _sp_id = list(self.spid_data[counter].keys())[0]
    #     sp_db = self.sp_rois[_sp_id]
    #     self.data_dct = self.data_obj.get_data_dct()
    #
    #     ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
    #     data_file_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
    #     datadir = dct_get(ado_obj, ADO_CFG_DATA_DIR)
    #     datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)
    #     thumb_name = dct_get(ado_obj, ADO_CFG_DATA_THUMB_NAME)
    #
    #     if (not self.check_if_save_all_data(datafile_name)):
    #         self.on_scan_done_discon_sigs()
    #         return
    #     else:
    #         cur_idx = self.get_consecutive_scan_idx()
    #         _logger.debug('SampleImageWithE712Wavegen: on_single_image_scan_done() called [%d]' % cur_idx)
    #
    #         _dct = self.get_img_idx_map(cur_idx)
    #         sp_id = _dct['sp_id']
    #         sp_idx = _dct['sp_idx']
    #         pol_idx = _dct['pol_idx']
    #
    #         # for now just use the first counter
    #         #counter = self.counter_dct.keys()[0]
    #         counter = DNM_DEFAULT_COUNTER
    #         self._data = self.spid_data[counter][sp_id][pol_idx]
    #
    #         # self.on_save_sample_image(_data=self._data)
    #         self.on_save_sample_image(_data=self.img_data[sp_id])
    #
    #         _dct = self.get_snapshot_dict(cur_idx)
    #         self.main_obj.zmq_save_dict_to_tmp_file(_dct)
    #
    #         #added this conditional when working on coarse scans
    #         # not sure why I would need this incremented for fine scans
    #         if(self.is_fine_scan):
    #             self.incr_consecutive_scan_idx()
    #
    #         # THIS IS CRITICAL
    #         # now that we have all of the data from all of the detectors, tell the sscan rec to continue
    #         self._scan2.sscan.put('WAIT', 0)
    #         ###############################
    #
    #         self.save_hdr(do_check=False)
    #         self.on_scan_done_discon_sigs()

    # def on_sampleimage_data_level_done(self):
    #     # _logger.debug('SampleImageWithEnergySSCAN: SampleImageWithEnergySSCAN() called')
    #     self.on_save_sample_image()
    #     if (self.stack):
    #         self.update_data(stack=True)
    #     #self.incr_consecutive_scan_idx()


    # def on_done_save_jpg_and_tmp_file(self):
    #     '''
    #     this is a handler for data_ready signal from SscanClass if there are more than one images being acquired
    #     the done here is for data_level_done, where we want to save a jpg, update the tmp file and continue IFF
    #     the current image idx does not qual the last image index
    #     :return:
    #     '''
    #     cur_idx = self.get_consecutive_scan_idx()
    #
    #     _logger.info('SampleImageWithE712Wavegen: on_done_save_jpg_and_tmp_file() called [%d]' % cur_idx)
    #
    #     _dct = self.get_img_idx_map(cur_idx)
    #     sp_id = _dct['sp_id']
    #     sp_idx = _dct['sp_idx']
    #     pol_idx = _dct['pol_idx']
    #
    #     # for now just use the first counter
    #     #counter = self.counter_dct.keys()[0]
    #     counter = DNM_DEFAULT_COUNTER
    #     self._data = self.spid_data[counter][sp_id][pol_idx]
    #
    #     #self.on_save_sample_image(_data=self._data)
    #     self.on_save_sample_image(_data=self.img_data[sp_id])
    #
    #     if (cur_idx >= self.numImages):
    #         print('update_tmp_file: cur_idx[%d] >= self.numImages[%d]: I dont this this is right' % (cur_idx, self.numImages))
    #     else:
    #         print('creating a snapshot for idx%d' % cur_idx)
    #         _dct = self.get_snapshot_dict(cur_idx)
    #         self.main_obj.zmq_save_dict_to_tmp_file(_dct)
    #
    #     # added this conditional when working on coarse scans
    #     # not sure why I would need this incremented for fine scans
    #     if (self.is_fine_scan):
    #         self.incr_consecutive_scan_idx()
    #
    #     # THIS IS CRITICAL
    #     # now that we have all of the data from all of the detectors, tell the sscan rec to continue
    #     self._scan2.sscan.put('WAIT', 0)
    #     ###############################
    #     if (cur_idx == self.numImages - 1):
    #         print('hey! I think this is the scan_done')
    #         self.shutter.close()
    #         self.on_scan_done_discon_sigs()
    #         self.save_hdr()
    #
    # def on_done_save_jpg_and_tmp_file_no_check_for_done(self):
    #     '''
    #     this is a handler for data_ready signal from SscanClass if there are more than one images being acquired
    #     the done here is for data_level_done, where we want to save a jpg, update the tmp file and continue IFF
    #     the current image idx does not qual the last image index
    #     :return:
    #     '''
    #     cur_idx = self.get_consecutive_scan_idx()
    #
    #     _logger.debug('SampleImageWithE712Wavegen: on_done_save_jpg_and_tmp_file_no_check_for_done() called [%d]' % cur_idx)
    #
    #     _dct = self.get_img_idx_map(cur_idx)
    #     sp_id = _dct['sp_id']
    #     sp_idx = _dct['sp_idx']
    #     pol_idx = _dct['pol_idx']
    #
    #     # for now just use the first counter
    #     #counter = self.counter_dct.keys()[0]
    #     counter = DNM_DEFAULT_COUNTER
    #     self._data = self.spid_data[counter][sp_id][pol_idx]
    #
    #     #self.on_save_sample_image(_data=self._data)
    #     self.on_save_sample_image(_data=self.img_data[sp_id])
    #
    #     _dct = self.get_snapshot_dict(cur_idx)
    #     self.main_obj.zmq_save_dict_to_tmp_file(_dct)
    #
    #     if (cur_idx < self.numImages - 1):
    #         self.incr_consecutive_scan_idx()
    #
    #     # THIS IS CRITICAL
    #     # now that we have all of the data from all of the detectors, tell the sscan rec to continue
    #     self._scan2.sscan.put('WAIT', 0)
    #
    #
    # def update_tmp_file(self):
    #     '''
    #                 this is a handler for data_ready signal from SscanClass
    #                 :return:
    #
    #                 tmp_data_dct = {}
    #         tmp_data_dct['devs']['energy'] = 685.0
    #         tmp_data_dct['devs']['epu_gap'] = 235.8
    #         tmp_data_dct['devs']['epu_polarization'] = 1
    #         tmp_data_dct['devs']['epu_offset'] = 0.0
    #         tmp_data_dct['devs']['epu_angle'] = 0.0
    #         ...
    #         tmp_data_dct['dets']['counter0'] = [[356, 403 ...]]  # a numpy arrray of shape (100,100) for a 100x100 pt image
    #         tmp_data_dct['dets']['ring_current'] = 221.56  # a single value
    #         tmp_data_dct['dets']['ccd0'] = [[[356, 403 ...]]]  # a numpy arrray of shape (480,640) for a 640x480 pt image
    #
    #     '''
    #     tmp_data_dct = {}
    #
    #     # if (self.stack):
    #     cur_idx = self.get_consecutive_scan_idx()
    #
    #
    #     _logger.debug('SampleImageWithEnergySSCAN: update_tmp_file() called [%d]' % cur_idx)
    #     # print 'self.do_update_devs:'
    #     attr_dct = self.update_dev_data[cur_idx]
    #     print(attr_dct)
    #
    #     # print self.img_idx_map
    #     # only support one detector for now
    #     for counter in list(self.counter_dct.keys()):
    #         # for each configured counter, get the data and send it to the dataIO
    #         _dct = self.get_img_idx_map(cur_idx)
    #         entry = _dct['entry']
    #         sp_id = _dct['sp_id']
    #         sp_idx = _dct['sp_idx']
    #         pol_idx = _dct['pol_idx']
    #         data = self.spid_data[counter][sp_id][pol_idx]
    #         self.hdr.update_tmp_data(cur_idx, tmp_data_dct)
    #     # if(not self.stack):
    #     #    self.save_hdr()
    #
    #
    #
    #
    #
    # def optimize_sample_line_scan(self):
    #     '''
    #     To be implemented by the inheriting class
    #     This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
    #     and any other settings required to optimize the scan for speed.
    #     Typically this is used by the scans that move the fine piezo stages as their status response can greatly
    #     mprove the performance if it is optimized.
    #
    #     appConfig.get_value('SAMPLE_IMAGE', 'whatever')
    #     c_scan1_pdly=0.0
    #     c_scan2_pdly=0.0
    #     f_scan2_pdly=0.0
    #     f_scan1_pdly=0.15
    #     # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
    #     f_fx_force_done=2
    #     f_fy_force_done=1
    #     '''
    #     appConfig.update()
    #     c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan1_pdly'))
    #     c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_scan2_pdly'))
    #     f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan1_pdly'))
    #     f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_scan2_pdly'))
    #     c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fx_force_done'))
    #     c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'c_fy_force_done'))
    #     f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fx_force_done'))
    #     f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_LXL', 'f_fy_force_done'))
    #     fx_done = MAIN_OBJ.device('FX_force_done')
    #     fy_done = MAIN_OBJ.device('FY_force_done')
    #
    #     if (self.x_roi[SCAN_RES] == COARSE):
    #         self.xScan.put('PDLY', c_scan1_pdly)
    #         fx_done.put(c_fx_force_done)
    #     else:
    #         self.xScan.put('PDLY', f_scan1_pdly)
    #         fx_done.put(f_fx_force_done)
    #
    #     if (self.y_roi[SCAN_RES] == COARSE):
    #         self.yScan.put('PDLY', c_scan2_pdly)
    #         fy_done.put(c_fy_force_done)
    #     else:
    #         self.yScan.put('PDLY', f_scan2_pdly)
    #         fy_done.put(f_fy_force_done)
    #
    # def optimize_sample_point_scan(self):
    #     '''
    #     To be implemented by the inheriting class
    #     This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
    #     and any other settings required to optimize the scan for speed.
    #     Typically this is used by the scans that move the fine piezo stages as their status response can greatly
    #     mprove the performance if it is optimized.
    #
    #     appConfig.get_value('SAMPLE_IMAGE', 'whatever')
    #     c_scan1_pdly=0.0
    #     c_scan2_pdly=0.0
    #     f_scan2_pdly=0.0
    #     f_scan1_pdly=0.15
    #     # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
    #     f_fx_force_done=2
    #     f_fy_force_done=1
    #     '''
    #     appConfig.update()
    #     c_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan1_pdly'))
    #     c_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_scan2_pdly'))
    #     f_scan1_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan1_pdly'))
    #     f_scan2_pdly = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_scan2_pdly'))
    #     c_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fx_force_done'))
    #     c_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'c_fy_force_done'))
    #     f_fx_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fx_force_done'))
    #     f_fy_force_done = float(appConfig.get_value('SAMPLE_IMAGE_PXP', 'f_fy_force_done'))
    #     fx_done = MAIN_OBJ.device('FX_force_done')
    #     fy_done = MAIN_OBJ.device('FY_force_done')
    #
    #     if (self.x_roi[SCAN_RES] == COARSE):
    #         # self.xyScan.put('PDLY', c_scan1_pdly)
    #         self.xScan.put('PDLY', c_scan1_pdly)
    #         fx_done.put(c_fx_force_done)
    #     else:
    #         # self.xyScan.put('PDLY', f_scan1_pdly)
    #         self.xScan.put('PDLY', f_scan1_pdly)
    #         fx_done.put(f_fx_force_done)
    #
    #     if (self.y_roi[SCAN_RES] == COARSE):
    #         self.yScan.put('PDLY', c_scan2_pdly)
    #         fy_done.put(c_fy_force_done)
    #     else:
    #         self.yScan.put('PDLY', f_scan2_pdly)
    #         fy_done.put(f_fy_force_done)
    #
    # def optimize_sample_pointspec_scan(self):
    #     '''
    #     To be implemented by the inheriting class
    #     This function is meant to retrieve from the ini file the section for its scan and set any PDLY's
    #     and any other settings required to optimize the scan for speed.
    #     Typically this is used by the scans that move the fine piezo stages as their status response can greatly
    #     mprove the performance if it is optimized.
    #
    #     appConfig.get_value('SAMPLE_IMAGE', 'whatever')
    #     c_scan1_pdly=0.0
    #     c_scan2_pdly=0.0
    #     f_scan2_pdly=0.0
    #     f_scan1_pdly=0.15
    #     # force done values are: 0=NORMAL, 1=FORCED, 2=INTERNAL_TIMED
    #     f_fx_force_done=2
    #     f_fy_force_done=1
    #     '''
    #     appConfig.update()
    #     c_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan1_pdly'))
    #     c_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_scan2_pdly'))
    #     f_scan1_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan1_pdly'))
    #     f_scan2_pdly = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_scan2_pdly'))
    #     c_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fx_force_done'))
    #     c_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'c_fy_force_done'))
    #     f_fx_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fx_force_done'))
    #     f_fy_force_done = float(appConfig.get_value('SAMPLE_POINT_SPEC_SCAN', 'f_fy_force_done'))
    #     fx_done = MAIN_OBJ.device('FX_force_done')
    #     fy_done = MAIN_OBJ.device('FY_force_done')
    #
    #     if (self.x_roi[SCAN_RES] == COARSE):
    #         self.xyScan.put('PDLY', c_scan1_pdly)
    #         fx_done.put(c_fx_force_done)
    #         fy_done.put(c_fy_force_done)
    #     else:
    #         self.xyScan.put('PDLY', f_scan1_pdly)
    #         fx_done.put(f_fx_force_done)
    #         fy_done.put(f_fy_force_done)
    #
    #
    # def optimize_hdw_accel_scan(self):
    #     pass
    #
    # def on_abort_scan(self):
    #     """
    #     on_abort_scan(): description
    #
    #     :returns: None
    #     """
    #     if (self.main_obj.device('Shutter').is_auto()):
    #         self.main_obj.device('Shutter').close()
    #     self._abort = True
    #     if(self.use_hdw_accel):
    #         #tell E712 wavegen to stop
    #         self.e712_wg.stop_wave_generator()
    #
    #
    # def validate_scan_assignments(self):
    #     """ a simple checker to verify that the scans are assigned to the correct epics sscan records
    #     """
    #
    #     pass_tst = True
    #     if (self.scan_type == scan_types.SAMPLE_POINT_SPECTRA):
    #         if (self.evScan.get_name() != '%s:scan3' % self.scan_prefix):
    #             pass_tst = False
    #         if (self.polScan.get_name() != '%s:scan2' % self.scan_prefix):
    #             pass_tst = False
    #         if (self.xyScan.get_name() != '%s:scan1' % self.scan_prefix):
    #             pass_tst = False
    #     return (pass_tst)

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
        _logger.info('\n\nSampleImageWithE712Wavegen: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_ids = list(self.sp_rois.keys())
        self.sp_id = sp_id
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()
        self.sample_fine_positioning_mode = MAIN_OBJ.get_fine_sample_positioning_mode()

        self.update_roi_member_vars(self.sp_db)

        #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
        # this is done in sscan2
        # self.xyScan = self._scan2

        self.determine_scan_res()

        # dct_put(self.sp_db, SPDB_RECT, (self.x_roi[START], self.y_roi[START], self.x_roi[STOP], self.y_roi[STOP]))
        # the sample motors have different modes, make a call to handle that they are setup correctly for this scan
#        self.configure_sample_motors_for_scan()

        if (ev_idx == 0):
            self.reset_evidx()
            self.reset_imgidx()
            self.reset_pnt_spec_spid_idx()
            self.final_data_dir = None
            self.update_dev_data = []

        if(len(self.sp_ids) > 1):
            self.is_multi_spatial = True
            #if multi spatial then just save everything without prompting
            self.set_save_all_data(True)
        else:
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
        sub_type = dct_get(self.wdg_com, SPDB_SCAN_PLUGIN_SUBTYPE)
        if(sub_type is scan_sub_types.POINT_BY_POINT):
            self.is_pxp = True
            self.is_lxl = False
        else:
            self.is_pxp = False
            self.is_lxl = True

        self.use_hdw_accel = dct_get(self.sp_db, SPDB_HDW_ACCEL_USE)
        if (self.use_hdw_accel is None):
            self.use_hdw_accel = True

        self.is_fine_scan = True
        #override
        if(not self.is_fine_scan):
            #coarse scan so turn hdw accel flag off
            self.use_hdw_accel = False

        if(self.use_hdw_accel):
            # self.save_hdr = self.hdw_accel_save_hdr

            #set the DDL flags
            if(dct_get(self.sp_db, SPDB_HDW_ACCEL_AUTO_DDL)):
                self.x_auto_ddl = True
                self.x_use_reinit_ddl = False
            else:
                #Reinit DDL for the current scan
                self.x_auto_ddl = False
                self.x_use_reinit_ddl = True

        # setup some convienience member variables
        self.dwell = e_roi[DWELL]
        self.numX = int(self.x_roi[NPOINTS])
        self.numY = int(self.y_roi[NPOINTS])
        self.numZX = int(self.zx_roi[NPOINTS])
        self.numZY = int(self.zy_roi[NPOINTS])
        self.numEPU = len(self.setpointsPol)
        self.numE = int(self.sp_db[SPDB_EV_NPOINTS])

        self.numSPIDS = len(self.sp_rois)

        if (self.scan_type != scan_types.SAMPLE_POINT_SPECTRA):
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
        self.use_hdw_accel = True

        if ((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
            if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
                # LINE_UNIDIR
                self.is_lxl = True
            else:
                # POINT_BY_POINT
                self.is_pxp = True

        elif (self.scan_type == scan_types.SAMPLE_POINT_SPECTRA):
            self.is_point_spec = True

        else:
            _logger.error('SampleImageWithEnergySSCAN: unable to determine scan type [%d]' % self.scan_type)
            return

        # users can request that the the ev and polarity portions of the scan can be executed in different orders
        # based on the order that requires a certain what for the sscan clases to be assigned in terms of their "level" so handle that in
        # another function
        # self.set_ev_pol_order(self.ev_pol_order)
        # if (self.ev_pol_order == energy_scan_order_types.EV_THEN_POL):
        #
        #     if (self.is_point_spec):
        #         if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        #             _id = 'goni_ev_pol_pnt_spec'
        #         else:
        #             _id = 'ev_pol_pnt_spec'
        #     elif (self.is_lxl):
        #         if(self.use_hdw_accel):
        #             #use the wavegen config
        #             if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        #                 _id = 'ev_pol_wg_gt'
        #             else:
        #                 _id = 'ev_pol_wg'
        #         else:
        #             _id = 'ev_pol_lxl'
        #     else:
        #         if (self.use_hdw_accel):
        #             # use the wavegen config
        #             if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        #                 _id = 'ev_pol_wg_gt'
        #             else:
        #                 _id = 'ev_pol_wg'
        #         else:
        #             # _id = 'ev_pol_pxp'
        #             _id = 'ev_pol_pxp_2recs'
        #
        # elif (self.ev_pol_order == energy_scan_order_types.POL_THEN_EV):
        #     if (self.is_point_spec):
        #         _id = 'pol_ev_pnt_spec'
        #     elif (self.is_lxl):
        #         if (self.use_hdw_accel):
        #             # use the wavegen config
        #             _id = 'pol_ev_wg'
        #         else:
        #             _id = 'pol_ev_lxl'
        #     else:
        #         _id = 'pol_ev_pxp'
        #
        # else:
        #     _logger.error('unsupported ev polarity order [%d]' % self.ev_pol_order)
        #     return

        # parms = self.cmdfile_parms[_id]

        #adjust params so that the data_done and scan_done signals work properly
        #only change the image params leave point spec as default
        # if(not self.is_point_spec):
        #     if(self.stack or (self.numSPIDS > 1)):
        #         if (self.is_fine_scan):
        #             parms['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
        #             parms['on_scan_done'] = self.on_single_image_scan_done
        #         else:
        #             # coarse scan, dont change defaults
        #             parms['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file_no_check_for_done
        #             parms['on_scan_done'] = self.chk_for_more_evregions
        #     else:
        #         if(self.is_fine_scan):
        #             #single image scan
        #             parms['on_data_level_done'] = self.on_single_image_scan_done
        #             #parms['on_scan_done'] = self.on_scan_done_discon_sigs
        #             parms['on_scan_done'] = None
        #         else:
        #             #coarse scan, dont change defaults
        #             parms['on_data_level_done'] = self.on_single_image_scan_done
        #             #parms['on_data_level_done'] = self.save_hdr
        #             #parms['on_data_level_done'] = self.chk_for_more_evregions
        #             #parms['on_scan_done'] = self.chk_for_more_evregions
        #             parms['on_scan_done'] = None
        #
        #
        # self.set_cmdfile_params(parms)

        # if (not self.validate_scan_assignments()):
        #     _logger.error('Scans are not correctly assigned')
        #     return

        # cause the low level sscan records to clear their previous values and reload their common settings
        #self.setupScan.reload_base_scan_config()
        # self.reload_base_scan_config()

        # set the function that will be called to make fine adjustments to the scan performance before scan starts
        # these optimization values are taken dynamically from tehj stxmMain.ini file so that they can be tested without restarting pySTXM

        # reset to the default then decide if to change it
        # self.set_optimize_scan_func(None)

        # if (self.use_hdw_accel):
        #     self.set_optimize_scan_func(self.optimize_hdw_accel_scan)
        #
        # elif((self.scan_type == scan_types.SAMPLE_IMAGE) or (self.scan_type == scan_types.SAMPLE_IMAGE_STACK)):
        #     if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
        #         # LINE_UNIDIR
        #         # if(self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        #         #    self.set_optimize_scan_func(self.optimize_goni_scan)
        #         # else:
        #         self.set_optimize_scan_func(self.optimize_sample_line_scan)
        #     else:
        #         # POINT_BY_POINT
        #         self.set_optimize_scan_func(self.optimize_sample_point_scan)
        #
        # elif (self.scan_type == scan_types.SAMPLE_POINT_SPECTRA):
        #     # self.pdlys = {'scan2': 0.05, 'scan1': 0.05}
        #     self.set_optimize_scan_func(self.optimize_sample_pointspec_scan)
        #
        # else:
        #     _logger.error(
        #         'SampleImageWithEnergySSCAN: set optimize:  unable to determine scan type [%d]' % self.scan_type)
        #     return

        #if (self.sample_positioning_mode == sample_positioning_modes.GONIOMETER):
        if (self.fine_sample_positioning_mode == sample_fine_positioning_modes.ZONEPLATE):
            self.is_zp_scan = True
        else:
            self.is_zp_scan = False
            # determine and setup for line or point by point
        # if (self.is_lxl):
        #     if (self.use_hdw_accel):
        #         #self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan)
        #         self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan, single_lsts={'sps':sps, 'evs':evs, 'pols':pols, 'dwells':dwells})
        #     else:
        #         self.set_ImageLineScan_line_sscan_rec(self.sp_db, e_roi, zp_scan)
        # else:
        #     if (self.is_point_spec):
        #         self.set_sample_point_spec_sscan_rec(self.sp_db, e_roi, zp_scan)
        #     else:
        #         if (self.use_hdw_accel):
        #             #self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan)
        #             self.set_ImageLineScan_use_hdw_accel_sscan_rec(self.sp_db, e_roi, zp_scan,
        #                                                            single_lsts={'sps': sps, 'evs': evs, 'pols': pols,
        #                                                                         'dwells': dwells})
        #         else:
        #             self.set_ImageLineScan_point_sscan_rec(self.sp_db, e_roi, zp_scan)

        self.ttl_pnts = 0
        # reset signals so we can start clean
        # if (block_disconnect_emit):
        #     self.blockSignals(True)
        #
        # self.disconnect_signals()
        #
        # if (block_disconnect_emit):
        #     self.blockSignals(False)

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


        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        # THIS must be the last call
        self.finish_setup()

        #only turn on the gate if lxl because triggers are generatoed by the E712 for point by point
        # if(self.is_lxl):
        #     #this needs to be part of a standard pluggin API call
        #     self.gate.start()
        #     time.sleep(0.25)
        #     # here the gate is the clock src so make sure its running
        #     self.gate.soft_trigger.put(1)
        #     self.gate.wait_till_running()
        #
        # self.counter.start()
        # self.counter.wait_till_running()
        ######################################################


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
        self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)

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
        self.main_obj.device(DNM_SAMPLE_FINE_X).put('ServoPower', 1)
        self.main_obj.device(DNM_SAMPLE_FINE_Y).put('ServoPower', 1)

        self.main_obj.device(DNM_SAMPLE_FINE_X).put('velocity', 100000.0)
        self.main_obj.device(DNM_SAMPLE_FINE_Y).put('velocity', 100000.0)

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
        self.main_obj.device(DNM_ZONEPLATE_X).put('ServoPower', 1)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('ServoPower', 1)

        self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
        self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)

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

    # def on_this_dev_cfg(self):
    #     """
    #     on_this_dev_cfg(): description
    #
    #     :returns: None
    #     this is an API method to configure the gate, shutter and counter devices for this scan
    #     """
    #     # if((self.is_pxp) or (self.is_point_spec)):
    #     if (self.is_pxp):
    #         if(self.use_hdw_accel):
    #             set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numX, self.counter, numE=self.numE)
    #             #set the trig src for the gate to an input that is not used so that the gate is essentially disabled
    #             self.gate.trig_src_select.put(9)
    #             #set_devices_for_e712_wavegen_point_scan(scan_type, dwell, numX, counter, numE=0)
    #         else:
    #             # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
    #             set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter,
    #                                    self.shutter)
    #     elif (self.is_point_spec):
    #         # set_devices_for_point_scan(self.roi, self.gate, self.counter, self.shutter)
    #         # numE is used for the number of points for a point spec, here we dont want to use Row etc because
    #         # we handle that here on hte counter handler for point spec
    #         if(self.use_hdw_accel):
    #             #set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.counter)
    #             set_devices_for_e712_wavegen_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.counter)
    #         else:
    #             set_devices_for_point_scan(self.scan_type, self.dwell, 99999999, self.numX, self.gate, self.counter,
    #                                    self.shutter)
    #     else:
    #         if(self.use_hdw_accel):
    #             set_devices_for_e712_wavegen_line_scan(self.dwell, self.numX, self.gate, self.counter)
    #         else:
    #             set_devices_for_line_scan(self.dwell, self.numX, self.gate, self.counter, self.shutter)
    #
    # def on_point_spec_scan_counter_changed(self, row, data):
    #     """
    #     on_sample_scan_counter_changed(): Used by SampleImageWithEnergySSCAN
    #     :param row: row
    #     :type row: row integer
    #
    #     :param data: data is a tuple of 2 values (x, counts)
    #     :type data: data tuple
    #
    #     :returns: None
    #
    #             The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
    #             The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
    #             The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
    #             slot during a point scan will receive a point+1 and in that case it should be ignored.
    #
    #             LIne scan data arrives in the form data[row, < number of x points of values >]
    #
    #             This slot has to handle
    #
    #     """
    #     num_spids = len(self.sp_rois)
    #     sp_cntr = self.get_pnt_spec_spid_idx()
    #     # print point_val[0:10]
    #     point_val = data[1]
    #     if (self.ttl_pnts < self.numE):
    #         # ev = self.evScan.P1.get('RBV')
    #         ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
    #         # print 'pointscan_counter_changed: on_counter_changed:[%d] x=%.2f point_val=%d len(data)=%d' % (self.ttl_pnts, ev, point_val, len(self.data))
    #
    #         # self.data[self.ttl_pnts, 0] = point_val
    #         self.data[0, sp_cntr, self.ttl_pnts] = point_val
    #         #             dct = {}
    #         #             dct['sp_id'] = self.sp_ids[sp_cntr]
    #         #             dct['img_idx'] = 0
    #         #             dct['row'] = sp_cntr
    #         #             dct['col'] = ev
    #         #             dct['val'] = point_val
    #
    #         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
    #         dct[CNTR2PLOT_SP_ID] = self.sp_ids[sp_cntr]
    #         dct[CNTR2PLOT_ROW] = sp_cntr
    #         dct[CNTR2PLOT_COL] = ev
    #         dct[CNTR2PLOT_VAL] = point_val
    #
    #         # print 'pointscan_counter_changed: on_counter_changed: num_spids = %d' % num_spids
    #         print('pointscan_counter_changed: on_counter_changed: [%d] row=%.2f col=%d val=%d' % (self.ttl_pnts, sp_cntr, self.ttl_pnts, point_val))
    #
    #         # self.sigs.changed.emit(int(0), (ev, y))
    #         self.sigs.changed.emit(dct)
    #         # self.ttl_pnts += 1
    #
    #         prog = float(float(self.ttl_pnts + 0.75) / float(self.numE)) * 100.0
    #         prog_dct = make_progress_dict(sp_id=dct[CNTR2PLOT_SP_ID], percent=prog)
    #         self.low_level_progress.emit(prog_dct)
    #
    #         self.incr_pnt_spec_spid_idx()
    #
    #         if (self.get_pnt_spec_spid_idx() >= num_spids):
    #             # print 'resetting get_spec_spid_idx() [%d]' % self.get_pnt_spec_spid_idx()
    #             self.reset_pnt_spec_spid_idx()
    #             self.ttl_pnts += 1
    #
    # # def set_ImageLineScan_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False):
    # #     """
    # #     set_ImageLineScan_line_sscan_rec(): description
    # #
    # #     :param sp_roi: sp_roi description
    # #     :type sp_roi: sp_roi type
    # #
    # #     :param e_roi: e_roi description
    # #     :type e_roi: e_roi type
    # #
    # #     :returns: None
    # #     """
    # #     # pol
    # #     self.polScan.put('NPTS', len(self.setpointsPol))
    # #     self.polScan.put('P1PA', self.setpointsPol)
    # #     self.polScan.put('P1SM', 1)  # table
    # #     # off
    # #     self.polScan.put('P2PA', self.setpointsOff)
    # #     self.polScan.put('P2SM', 1)  # table
    # #     # angle
    # #     self.polScan.put('P3PA', self.setpointsAngle)
    # #     self.polScan.put('P3SM', 1)  # table
    # #
    # #     # EV
    # #     self.evScan.put('NPTS', e_roi[NPOINTS])
    # #     self.evScan.put('P1SP', e_roi[START])
    # #     self.evScan.put('P1EP', e_roi[STOP])
    #
    # def set_ImageLineScan_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False, single_lsts={}):
    #     """
    #     set_ImageLineScan_line_sscan_rec(): description
    #
    #     :param sp_roi: sp_roi description
    #     :type sp_roi: sp_roi type
    #
    #     :param e_roi: e_roi description
    #     :type e_roi: e_roi type
    #
    #     :returns: None
    #     """
    #     evs = single_lsts['evs']
    #     pols = single_lsts['pols']
    #     dwells = single_lsts['dwells']
    #     sps = single_lsts['sps']
    #
    #     self.setupScan.put('NPTS', 1)
    #     self.setupScan.put('P1SM', 0)  # Linear
    #     self.setupScan.put('P2SM', 0)  # Linear
    #     #SampleX
    #     self.setupScan.put('P1CP', self.x_roi[CENTER])
    #     self.setupScan.put('P1SP', self.x_roi[CENTER])
    #     self.setupScan.put('P1EP', self.x_roi[CENTER])
    #     #SampleY
    #     self.setupScan.put('P2CP', self.y_roi[CENTER])
    #     self.setupScan.put('P2SP', self.y_roi[CENTER])
    #     self.setupScan.put('P2EP', self.y_roi[CENTER])
    #
    #     # pol
    #     self.polScan.put('NPTS', len(self.setpointsPol))
    #     self.polScan.put('P1PA', self.setpointsPol)
    #     self.polScan.put('P1SM', 1)  # table
    #     # off
    #     self.polScan.put('P2PA', self.setpointsOff)
    #     self.polScan.put('P2SM', 1)  # table
    #     # angle
    #     self.polScan.put('P3PA', self.setpointsAngle)
    #     self.polScan.put('P3SM', 1)  # table
    #
    #     #     # EV
    #     #     self.evScan.put('NPTS', e_roi[NPOINTS])
    #     #     self.evScan.put('P1SP', e_roi[START])
    #     #     self.evScan.put('P1EP', e_roi[STOP])
    #
    #     # EV
    #     #here write all energies to table of setpoints
    #     self.evScan.put('NPTS', len(evs))
    #     self.evScan.put('P1PA', evs)
    #     self.evScan.put('P1SM', 1)  # table
    #
    #     #load the wavefr
    #     MAIN_OBJ.device('e712_dwells').put(dwells)
    #
    #
    # # def set_ImageLineScan_point_use_hdw_accel_sscan_rec(self, sp_roi, e_roi, zp_scan=False):
    # #     """
    # #     set_ImageLineScan_line_sscan_rec(): description
    # #
    # #     :param sp_roi: sp_roi description
    # #     :type sp_roi: sp_roi type
    # #
    # #     :param e_roi: e_roi description
    # #     :type e_roi: e_roi type
    # #
    # #     :returns: None
    # #     """
    # #     # XY
    # #     # only 1 points because X is only calling IOCE712:ExecWavgen for an entire image
    # #     self.xScan.put('NPTS', 1)
    # #
    # #     # pol
    # #     self.polScan.put('NPTS', len(self.setpointsPol))
    # #     self.polScan.put('P1PA', self.setpointsPol)
    # #     self.polScan.put('P1SM', 1)  # table
    # #     # off
    # #     self.polScan.put('P2PA', self.setpointsOff)
    # #     self.polScan.put('P2SM', 1)  # table
    # #     # angle
    # #     self.polScan.put('P3PA', self.setpointsAngle)
    # #     self.polScan.put('P3SM', 1)  # table
    # #
    # #     # EV
    # #     self.evScan.put('NPTS', e_roi[NPOINTS])
    # #     self.evScan.put('P1SP', e_roi[START])
    # #     self.evScan.put('P1EP', e_roi[STOP])

    # def config_for_goniometer_scan_hdw_accel(self, dct, is_focus=False):
    #     """
    #     For a goniometer scan this will always be a fine scan of max range 100x100um (actually less)
    #     and the sequence to configure a scan is to position the goniometer at teh center of the scan everytime
    #     and set the +/- scan range to be about Zoneplate XY center (0,0)
    #
    #     Need to take into account that this could be a LxL scan (uses xScan, yScan, zScan) or a PxP (uses xyScan, zScan)
    #
    #     Because this scan uses the waveform generator on the E712 there are no positioners set for X and Y scan only the
    #     triggering of the waveform generator, will still need to do something so that save_hdr has something to get data
    #     from, not sure how to handle this yet.
    #
    #     """
    #     ### VERY IMPORTANT the current PID tune for ZX is based on a velo (SLew Rate) of 1,000,000
    #     self.main_obj.device(DNM_ZONEPLATE_X).put('velocity', 1000000.0)
    #     self.main_obj.device(DNM_ZONEPLATE_Y).put('velocity', 1000000.0)
    #
    #     # self.setupScan.set_positioner(1, self.main_obj.device(DNM_GONI_X))
    #     # self.setupScan.set_positioner(2, self.main_obj.device(DNM_GONI_Y))
    #     # self.setupScan.set_positioner(3, self.main_obj.device(DNM_OSA_X))
    #     # # self.setupScan.set_positioner(4,  self.main_obj.device(DNM_OSA_Y))
    #     #
    #     # gx_mtr = self.main_obj.device(dct['cx_name'])
    #     # gy_mtr = self.main_obj.device(dct['cy_name'])
    #     #
    #     # self.set_config_devices_func(self.on_this_dev_cfg)
    #     #
    #     self.sample_mtrx = self.sample_finex = self.main_obj.device(DNM_ZONEPLATE_X)
    #     self.sample_mtry = self.sample_finey = self.main_obj.device(DNM_ZONEPLATE_Y)
    #     #
    #     # move Gx and Gy to center of scan, is it within a um?
    #     if (self.zx_roi[CENTER] != 0.0):
    #         # zx is moving to scan center
    #         pass
    #     else:
    #         # Gx is moving to scan center nd zx is centered around 0, so move Gx to scan center
    #         self.main_obj.device(dct['cx_name']).put('user_setpoint', self.gx_roi[CENTER])
    #
    #     # if(self.is_within_dband( gy_mtr.get_position(), self.gy_roi[CENTER], 15.0)):
    #     if (self.zy_roi[CENTER] != 0.0):
    #         # zy is moving to scan center
    #         pass
    #     else:
    #         # Gy is moving to scan center nd zy is centered around 0, so move Gy to scan center
    #         self.main_obj.device(dct['cy_name']).put('user_setpoint', self.gy_roi[CENTER])
    #     #
    #     # # config the sscan that makes sure to move goni xy and osa xy to the correct position for scan
    #     # # the setupScan will be executed as the top level but not monitored
    #     # # self.setupScan.put('NPTS', 1)
    #     # # self.setupScan.put('P1PV', '%s.VAL' % self.main_obj.device(DNM_GONI_X).get_name())
    #     # # self.setupScan.put('R1PV', '%s.RBV' % self.main_obj.device(DNM_GONI_X).get_name())
    #     # # self.setupScan.put('P1SP', self.gx_roi[CENTER])
    #     # # self.setupScan.put('P1EP', self.gx_roi[CENTER])
    #     # #
    #     # #
    #     # # self.setupScan.put('P2PV', '%s.VAL' % self.main_obj.device(DNM_GONI_Y).get_name())
    #     # # self.setupScan.put('R2PV', '%s.RBV' % self.main_obj.device(DNM_GONI_Y).get_name())
    #     # # self.setupScan.put('P2SP', self.gy_roi[CENTER])
    #     # # self.setupScan.put('P2EP', self.gy_roi[CENTER])
    #     # #
    #     # #
    #     # # self.setupScan.put('P3PV', '%s.VAL' % self.main_obj.device(DNM_OSA_X).get_name())
    #     # # self.setupScan.put('R3PV', '%s.RBV' % self.main_obj.device(DNM_OSA_X).get_name())
    #     # # self.setupScan.put('P3SP', self.ox_roi[CENTER])
    #     # # self.setupScan.put('P3EP', self.ox_roi[CENTER])
    #
    #     self.num_points = self.numY
    #
    #     self.sample_mtrx.put('Mode', 0)
    #
    #     #setup the E712 wavtable's and other relevant params
    #     self.modify_config_for_hdw_accel()


#     def on_sample_scan_counter_changed_hdw_accel(self, row, data, counter_name='counter0'):
#         """
#         on_sample_scan_counter_changed_hdw_accel(): Used by SampleImageWithEnergySSCAN
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
#         The on counter_changed slot will take data cquired by line and point scans but it must treat each differently.
#         The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
#         The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
#         slot during a point scan will receive a point+1 and in that case it should be ignored.
#
#         LIne scan data arrives in the form data[row, < number of x points of values >]
#
#         This slot has to handle
#
#         """
#
#         if(row < 0):
#             row = 0
#
#         sp_id =  int(MAIN_OBJ.device('e712_current_sp_id').get_position())
#         self.set_spatial_id(sp_id)
#
#         if ((self.scan_type == scan_types.OSA_FOCUS) or (self.scan_type == scan_types.SAMPLE_FOCUS)):
#             nptsy = self.numZ
#         else:
#             nptsy = self.numY
#
#         _evidx = self.get_evidx()
#         _imgidx = MAIN_OBJ.device('e712_image_idx').get_position()
#         #print 'on_sample_scan_counter_changed_hdw_accel: _imgidx=%d row=%d' % (_imgidx, row)
#
#         if (self.is_pxp and (not self.use_hdw_accel)):
#             # Image point by point
#             point = int(data[0])
#             val = data[1]
#
#             # print 'SampleImageWithEnergySSCAN: on_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
#             self.data[_imgidx, row, point] = val
#         elif (self.is_pxp and self.use_hdw_accel):
#             point = 0
#             (wd,) = data.shape
#             #print data
#             val = data[0:wd]
#         else:
#             # print 'SampleImageWithEnergySSCAN: LXL on_counter_changed: _imgidx, row and data[0:10]=', (_imgidx, row, data[0:10])
#             point = 0
#             (wd,) = data.shape
#             val = data[0:(wd - 1)]
#
#         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#         dct[CNTR2PLOT_ROW] = int(row)
#         dct[CNTR2PLOT_COL] = int(point)
#         dct[CNTR2PLOT_VAL] = val
#         #because we could be multi spatial override the default
#         dct[CNTR2PLOT_SP_ID] = sp_id
#
#         _dct = self.get_img_idx_map(_imgidx)
#         _sp_id = _dct['sp_id']
#         pol_idx = _dct['pol_idx']
#         e_idx = _dct['e_idx']
#
#         #print 'on_sample_scan_counter_changed_hdw_accel: counter_name=[%s] _imgidx=%d, sp_id=%d' % (counter_name, _imgidx, _sp_id)
#         #print 'self.img_data[0].shape',self.img_data[_sp_id].shape
#         #print 'val.shape', val.shape
#         img_ht, img_wd = self.img_data[_sp_id].shape
#         row_wd, = val.shape
#
#         if(img_wd == row_wd):
#             self.img_data[_sp_id][int(row), :] = val
#             self.spid_data[counter_name][sp_id][pol_idx][e_idx, int(row), :] = val
#             self.sigs.changed.emit(dct)
#
#         #now emit progress information
#         prog = float(float(row + 0.75) / float(img_ht)) * 100.0
#         if (self.stack):
#             prog_dct = make_progress_dict(sp_id=sp_id, percent=prog, cur_img_idx=_imgidx)
#         else:
#             prog_dct = make_progress_dict(sp_id=sp_id, percent=prog, cur_img_idx=_imgidx)
#
#         self.low_level_progress.emit(prog_dct)
#
#
#     def on_coarse_sample_scan_counter_changed(self, row, data, counter_name='counter0'):
#         """
#         on_sample_scan_counter_changed_hdw_accel(): Used by SampleImageWithEnergySSCAN
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
#         The on counter_changed slot will take data acquired by line and point scans but it must treat each differently.
#         The point scan still arrives as a one demensiotnal array but there are only 3 elements, data[row, point, value].
#         The point scan has been programmed to acquire num_x_points + 1 so that the counter can increment the row value, thus this
#         slot during a point scan will receive a point+1 and in that case it should be ignored.
#
#         LIne scan data arrives in the form data[row, < number of x points of values >]
#
#         This slot has to handle
#
#         """
#
#         if(row < 0):
#             print()
#             row = 0
#
#         sp_id =  int(MAIN_OBJ.device('e712_current_sp_id').get_position())
#         self.set_spatial_id(sp_id)
#
#         if ((self.scan_type == scan_types.OSA_FOCUS) or (self.scan_type == scan_types.SAMPLE_FOCUS)):
#             nptsy = self.numZ
#         else:
#             nptsy = self.numY
#
#         _evidx = self.get_evidx()
#         #_imgidx = MAIN_OBJ.device('e712_image_idx').get_position()
#         _imgidx = self.base_zero(self.get_imgidx())
#         _dct = self.get_img_idx_map(_imgidx)
#         _sp_id = _dct['sp_id']
#         pol_idx = _dct['pol_idx']
#         e_idx = _dct['e_idx']
#
#         #set the spatial id so that save_hdr can use it
#         self.set_spatial_id(_sp_id)
#         #print 'on_sample_scan_counter_changed_hdw_accel: _imgidx=%d row=%d' % (_imgidx, row)
#
#         if (self.is_pxp and (not self.use_hdw_accel)):
#             # Image point by point
#             point = int(data[0])
#             val = data[1]
#
#             # print 'SampleImageWithEnergySSCAN: on_counter_changed: _imgidx=%d row=%d point=%d, data = %d' % (_imgidx, row, point, val)
#             self.data[_imgidx, row, point] = val
#
#         else:
#             # print 'SampleImageWithEnergySSCAN: LXL on_counter_changed: _imgidx, row and data[0:10]=', (_imgidx, row, data[0:10])
#             point = 0
#             (wd,) = data.shape
#             val = data[0:(wd - 1)]
#
#         dct = self.init_counter_to_plotter_com_dct(make_counter_to_plotter_com_dct())
#         dct[CNTR2PLOT_ROW] = int(row)
#         dct[CNTR2PLOT_COL] = int(point)
#         dct[CNTR2PLOT_VAL] = val
#         #because we could be multi spatial override the default
#         dct[CNTR2PLOT_SP_ID] = _sp_id
#
#         self.img_data[_sp_id][int(row), :] = val
#
#         #print 'self.spid_data[%s][%d][%d][%d, %d, :]' % (counter_name,_sp_id,pol_idx,e_idx, int(row))
#         self.spid_data[counter_name][_sp_id][pol_idx][e_idx, int(row), :] = val
#         self.sigs.changed.emit(dct)
#
#         #now emit progress information
#         prog = float(float(row + 0.75) / float(nptsy)) * 100.0
#         if (self.stack):
#             prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)
#         else:
#             prog_dct = make_progress_dict(sp_id=_sp_id, percent=prog)
#
#         self.low_level_progress.emit(prog_dct)
#
#     def hdw_accel_save_hdr(self, update=False, do_check=True):
#         """
#         save_hdr(): This is the main datafile savinf function, it is called at the end of every completed scan
#
#         :param update: update is a flag set to True when save_hdr() is first called during the configure() portion of the scan
#                     it allows the data file to be created before data collection has started and then updated as the data is collected,
#                     when the scan has finished this flag is False which indicates that all final processing of the save should take place
#                     (ie: prompt the user if they want to save this data etc)
#
#         :returns: None
#
#         If this function takes a long time due to grabbing a snapshot of all
#         the positioners it should maybe be moved to its own thread and just have the
#         GUI wait until it is finished, that seems reasonable for the user to wait a couple secondsù
#         for the file to save as long as the GUI is not hung
#
#
#         This function is used by:
#             - sample Image PXP
#             - sample Image LXL
#             - sample Image point Spectra
#         None stack scans should yield the following per scan:
#             one header file
#             one image thumbnail (jpg)
#
#         Stack scans should yield:
#             one header file
#             numE * numEpu thumbnail images per stack
#
#         The image thumbnails are saved in the on_sampleImage_data_done signal handler
#
#         The header file is saved on the scan_done signal of the top level scan
#         """
#         if (update):
#             _logger.info('Skipping save_hdr() update = True')
#             return
#         upside_dwn_scans = [scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_IMAGE]
#         # _logger.info('save_hdr: starting')
#         if (self.is_point_spec):
#             self.save_point_spec_hdr(update)
#             return
#
#
#
#         # self.gate.stop()
#         # self.counter.stop()
#         self.data_obj.set_scan_end_time()
#
#         # self.main_obj.update_zmq_posner_snapshot()
#         # self.main_obj.update_zmq_detector_snapshot()
#         # self.main_obj.update_zmq_pv_snapshot()
#         upd_list = []
#         for s in self.scanlist:
#             upd_list.append(s.get_name())
#         # self.main_obj.update_zmq_sscan_snapshot(upd_list)
#
#         _ev_idx = self.get_evidx()
#         _img_idx = self.get_imgidx() - 1
#         _spatial_roi_idx = self.get_spatial_id()
#         sp_db = self.sp_rois[_spatial_roi_idx]
#         sample_pos = 1
#
#         # data_name_dct = master_get_seq_names(datadir, prefix_char=data_file_prfx, thumb_ext=thumb_file_sffx, dat_ext='hdf5', stack_dir=self.stack)
#         # hack
#         if (_img_idx < 0):
#             _img_idx = 0
#         self.data_dct = self.data_obj.get_data_dct()
#
#         ado_obj = dct_get(sp_db, SPDB_ACTIVE_DATA_OBJECT)
#         #        data_file_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
#         #        thumb_file_ext = dct_get(ado_obj, ADO_CFG_THUMB_EXT)
#         datadir = dct_get(ado_obj, ADO_CFG_DATA_DIR)
#         datafile_name = dct_get(ado_obj, ADO_CFG_DATA_FILE_NAME)
#         datafile_prfx = dct_get(ado_obj, ADO_CFG_PREFIX)
#         #        thumb_name = dct_get(ado_obj, ADO_CFG_DATA_THUMB_NAME)
#         stack_dir = dct_get(ado_obj, ADO_CFG_STACK_DIR)
#
# #        if (not update):
# #            if (not self.check_if_save_all_data(datafile_name)):
# #                return
#         if(self.use_hdw_accel):
#             if (self.e712_wg.save_this_ddl()):
#                 self.e712_wg.get_ddl_table(X_WAVE_TABLE_ID, cb=self.e712_wg.save_ddl_data)
#
#         self.saving_data.emit('Saving...')
#
#         if (self.stack):
#             datadir = stack_dir
#
#         # alldata = self.main_obj.get_zmq_sscan_snapshot(upd_list)
#         for scan in self.scanlist:
#             sname = scan.get_name()
#             #    #ask each scan to get its data and store it in scan.scan_data
#             if (scan.section_name == SPDB_XY):
#                 # this is a sscan where P1 is X and P2 is Y, separate them such that they look like two separate scans
#                 # alldata = self.take_sscan_snapshot(scan.name)
#
#                 if(self.use_hdw_accel):
#                     alldata = {}
#                     alldata['P1RA'] = self.x_roi[SETPOINTS]
#                     alldata['P2RA'] = self.y_roi[SETPOINTS]
#                     alldata['NPTS'] = self.x_roi[NPOINTS]
#                     alldata['CPT'] = self.x_roi[NPOINTS]
#                     p1data = alldata['P1RA']
#                     npts = alldata['NPTS']
#                     cpt = alldata['CPT']
#                     p2data = alldata['P2RA']
#                 else:
#                     alldata = scan.get_all_data()
#                     p1data = alldata['P1RA']
#                     npts = alldata['NPTS']
#                     cpt = alldata['CPT']
#                     p2data = alldata['P2RA']
#                     dct_put(self.data_dct, 'DATA.SSCANS.XY', alldata)
#
#                 dct_put(self.data_dct, 'DATA.SSCANS.XY', alldata)
#                 dct_put(self.data_dct, 'DATA.SSCANS.X', {'P1RA': p1data, 'NPTS': npts, 'CPT': cpt})
#                 dct_put(self.data_dct, 'DATA.SSCANS.Y', {'P1RA': p2data, 'NPTS': npts, 'CPT': cpt})
#             else:
#                 all_data = scan.get_all_data()
#                 if (self.use_hdw_accel and (scan.section_name == (SPDB_X or SPDB_Y))):
#                     # there will not be any P1RA key in all_data because there are no positioners specified so
#                     # the data must be generated for X and Y in
#                     p1data = np.linspace(self.x_roi[START], self.x_roi[STOP], self.x_roi[NPOINTS])
#                     p2data = np.linspace(self.y_roi[START], self.y_roi[STOP], self.y_roi[NPOINTS])
#                     all_data['P1RA'] = p1data
#                     all_data['P2RA'] = p2data
#                     xnpts = self.x_roi[NPOINTS]
#                     ynpts = self.y_roi[NPOINTS]
#                     xcpt = xnpts
#                     ycpt = ynpts
#                     all_data['NPTS'] = self.x_roi[NPOINTS]
#                     all_data['CPT'] = self.x_roi[NPOINTS]
#                     dct_put(self.data_dct, 'DATA.SSCANS.XY', all_data)
#                     dct_put(self.data_dct, 'DATA.SSCANS.X', {'P1RA': p1data, 'NPTS': xnpts, 'CPT': xcpt})
#                     dct_put(self.data_dct, 'DATA.SSCANS.Y', {'P1RA': p2data, 'NPTS': ynpts, 'CPT': ycpt})
#                 else:
#                     dct_put(self.data_dct, 'DATA.SSCANS.' + scan.section_name, scan.get_all_data())
#                     # dct_put(self.data_dct,'DATA.SSCANS.' + scan.section_name, alldata[sname])
#
#         # if (self.scan_type in upside_dwn_scans and not update):
#         #     # the data for these scans needs to be flipped upside down, but because this function is called multiple times
#         #     #depending on where the scan is at we need to make sure we are only flipping the data 1 time, so here
#         #     #we are doing it at the end (the last time it is called) when update is False
#         #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
#         #     self.data[_img_idx - 1] = np.copy(_data)
#         #
#         # elif(self.scan_type is scan_types.SAMPLE_IMAGE_STACK and not update):
#         #     #stack scan save individual images during an update, so flip during an update for a stack scan
#         #     #but then the issue is the very last image because it will get flipped multiple times
#         #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
#         #     self.data[_img_idx - 1] = np.copy(_data)
#         #
#         # elif (self.scan_type is scan_types.SAMPLE_IMAGE_STACK and update):
#         #     # stack scan save individual images during an update, so flip during an update for a stack scan
#         #     # but then the issue is the very last image because it will get flipped multiple times
#         #     _data = self.flip_data_upsdown(self.data[_img_idx - 1])
#         #     self.data[_img_idx - 1] = np.copy(_data)
#
#         # _logger.info('grabbing devices snapshot')
#         devices = self.main_obj.get_devices()
#
#         # get the current spatial roi and put it in the dct as a dict with its sp_id as the key
#         _wdgcom = {}
#         dct_put(_wdgcom, WDGCOM_CMND, self.wdg_com[CMND])
#         _sprois = {}
#         _sprois[_spatial_roi_idx] = self.wdg_com['SPATIAL_ROIS'][_spatial_roi_idx]
#         dct_put(_wdgcom, SPDB_SPATIAL_ROIS, _sprois)
#         dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)
#
#         testing_polarity_entries = False
#         if (testing_polarity_entries):
#             t_dct = {}
#
#             dct_put(t_dct, 'POSITIONERS', self.take_positioner_snapshot(devices['POSITIONERS']))
#             dct_put(t_dct, 'DETECTORS', self.take_detectors_snapshot(devices['DETECTORS']))
#             dct_put(t_dct, 'TEMPERATURES', self.take_temps_snapshot(devices['TEMPERATURES']))
#             dct_put(t_dct, 'PRESSURES', self.take_pressures_snapshot(devices['PRESSURES']))
#             dct_put(t_dct, 'PVS', self.take_pvs_snapshot(devices['PVS']))
#             # _logger.info('DONE grabbing devices snapshot')
#             # dct_put(t_dct, ADO_CFG_WDG_COM, self.wdg_com)
#             dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)
#
#             dct_put(t_dct, ADO_CFG_SCAN_TYPE, self.scan_type)
#             dct_put(t_dct, ADO_CFG_CUR_EV_IDX, _ev_idx)
#             dct_put(t_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, _spatial_roi_idx)
#             dct_put(t_dct, ADO_CFG_CUR_SAMPLE_POS, sample_pos)
#             dct_put(t_dct, ADO_CFG_CUR_SEQ_NUM, 0)
#             dct_put(t_dct, ADO_CFG_DATA_DIR, datadir)
#             dct_put(t_dct, ADO_CFG_DATA_FILE_NAME, datafile_prfx)
#             dct_put(t_dct, ADO_CFG_UNIQUEID, datafile_prfx)
#             dct_put(t_dct, ADO_CFG_X, self.x_roi)
#             dct_put(t_dct, ADO_CFG_Y, self.y_roi)
#             dct_put(t_dct, ADO_CFG_Z, self.z_roi)
#             dct_put(t_dct, ADO_CFG_EV_ROIS, self.e_rois)
#             dct_put(t_dct, ADO_DATA_POINTS, self.data)
#             #dct_put(t_dct, ADO_CFG_IMG_IDX_MAP, self.img_idx_map)
#
#             images_data = np.zeros((self.numEPU, self.numE, self.numY, self.numX))
#             image_idxs = []
#             for i in range(self.numEPU):
#                 image_idxs.append(np.arange(i, self.numImages, self.numEPU))
#
#             # for idxs in image_idxs:
#             for i in range(self.numEPU):
#                 idxs = image_idxs[i]
#                 y = 0
#                 for j in idxs:
#                     images_data[i][y] = self.data[j]
#                     y += 1
#
#             new_e_rois = self.turn_e_rois_into_polarity_centric_e_rois(self.e_rois)
#             pol_rois = []
#             for e_roi in self.e_rois:
#                 for pol in range(self.numEPU):
#                     pol_rois.append(e_roi['POL_ROIS'][pol])
#
#             for pol in range(self.numEPU):
#                 self.data_dct['entry_%d' % pol] = copy.deepcopy(t_dct)
#                 dct_put(self.data_dct['entry_%d' % pol], ADO_DATA_POINTS, copy.deepcopy(images_data[pol]))
#                 dct_put(self.data_dct['entry_%d' % pol], ADO_DATA_SSCANS,
#                         copy.deepcopy(self.data_dct['DATA']['SSCANS']))
#                 dct_put(self.data_dct['entry_%d' % pol], ADO_CFG_EV_ROIS, [new_e_rois[pol]])
#         else:
#
#             if ((self.data_dct['TIME'] != None) and update):
#                 # we already have already set these and its not the end of the scan sp skip
#                 pass
#             else:
#                 dct_put(self.data_dct, 'TIME', make_timestamp_now())
#                 dct_put(self.data_dct, 'POSITIONERS', self.take_positioner_snapshot(devices['POSITIONERS']))
#                 dct_put(self.data_dct, 'DETECTORS', self.take_detectors_snapshot(devices['DETECTORS']))
#                 dct_put(self.data_dct, 'TEMPERATURES', self.take_temps_snapshot(devices['TEMPERATURES']))
#                 dct_put(self.data_dct, 'PRESSURES', self.take_pressures_snapshot(devices['PRESSURES']))
#                 dct_put(self.data_dct, 'PVS', self.take_pvs_snapshot(devices['PVS']))
#
#             # _logger.info('DONE grabbing devices snapshot')
#             # dct_put(self.data_dct, ADO_CFG_WDG_COM, self.wdg_com)
#             dct_put(self.data_dct, ADO_CFG_WDG_COM, _wdgcom)
#
#             if (update):
#                 dct_put(self.data_dct, ADO_CFG_DATA_STATUS, DATA_STATUS_NOT_FINISHED)
#             else:
#                 dct_put(self.data_dct, ADO_CFG_DATA_STATUS, DATA_STATUS_FINISHED)
#
#             dct_put(self.data_dct, ADO_CFG_SCAN_TYPE, self.scan_type)
#             dct_put(self.data_dct, ADO_CFG_CUR_EV_IDX, _ev_idx)
#             dct_put(self.data_dct, ADO_CFG_CUR_SPATIAL_ROI_IDX, _spatial_roi_idx)
#             dct_put(self.data_dct, ADO_CFG_CUR_SAMPLE_POS, sample_pos)
#             dct_put(self.data_dct, ADO_CFG_CUR_SEQ_NUM, 0)
#             dct_put(self.data_dct, ADO_CFG_DATA_DIR, datadir)
#             dct_put(self.data_dct, ADO_CFG_DATA_FILE_NAME, datafile_prfx)
#             dct_put(self.data_dct, ADO_CFG_UNIQUEID, datafile_prfx)
#             dct_put(self.data_dct, ADO_CFG_X, self.x_roi)
#             dct_put(self.data_dct, ADO_CFG_Y, self.y_roi)
#             dct_put(self.data_dct, ADO_CFG_Z, self.z_roi)
#             dct_put(self.data_dct, ADO_CFG_ZZ, self.zz_roi)
#             dct_put(self.data_dct, ADO_CFG_EV_ROIS, self.e_rois)
#             #dct_put(self.data_dct, ADO_DATA_POINTS, self.data)
#             #dct_put(self.data_dct, ADO_CFG_IMG_IDX_MAP, self.img_idx_map)
#
#             cur_idx = self.get_consecutive_scan_idx()
#             _dct = self.get_img_idx_map(cur_idx)
#
#             # sp_idx = _dct['sp_idx']
#             sp_id = _dct['sp_id']
#             pol_idx = _dct['pol_idx']
#
#             #for now just use the first counter
#             #counter = self.counter_dct.keys()[0]
#             counter = DNM_DEFAULT_COUNTER
#             if(sp_id not in list(self.spid_data[counter].keys())):
#                 _logger.error('hdw_accel_save_hdr: sp_id[%d] does not exist in self.spid_data[counter].keys()' % sp_id)
#                 return
#             #self._data = self.spid_data[counter][sp_idx][pol_idx]
#             self._data = self.spid_data[counter][sp_id][pol_idx]
#             dct_put(self.data_dct, ADO_DATA_POINTS, self._data)
#
#             dct_put(self.data_dct, ADO_STACK_DATA_POINTS, self.spid_data)
#             dct_put(self.data_dct, ADO_STACK_DATA_UPDATE_DEV_POINTS, self.update_dev_data)
#
#             dct_put(self.data_dct, ADO_SP_ROIS, self.sp_rois)
#
#
#         if (update):
#             self.hdr.save(self.data_dct, use_tmpfile=True)
#         else:
#             pass
#             #Sept 8
#             # if(self.stack or (len(self.sp_rois) > 1)):
#             #     self.hdr.save(self.data_dct, allow_tmp_rename=True)
#             #     self.clean_up_data()
#             # else:
#             #     self.hdr.save(self.data_dct)
#             #end Sept 8
#
#             #update stop time in tmp file
#             self.main_obj.zmq_stoptime_to_tmp_file()
#
#             #now send the Active Data Object (ADO) to the tmp file under the section 'ADO'
#             dct = {}
#             dct['cmd'] = CMD_SAVE_DICT_TO_TMPFILE
#             wdct = {'WDG_COM':dict_to_json(_wdgcom), 'SCAN_TYPE': self.scan_type}
#
#             #try deleting datapoints
#             del self.data_dct['DATA']['POINTS']
#             self.data_dct['DATA']['POINTS'] = []
#             del self.data_dct['STACK_DATA']['POINTS']
#             self.data_dct['STACK_DATA']['POINTS'] = {}
#
#             data_dct_str = dict_to_json(self.data_dct)
#             dct['dct'] = {'SP_ROIS': dict_to_json(self.sp_rois), 'CFG': wdct, 'numEpu': self.numEPU, 'numSpids':self.numSPIDS, 'numE':self.numE, \
#                           'DATA_DCT':data_dct_str}
#
#             #debugging
#             print('hdw_accel_save_hdr: SIZES: _wdgcom=%d wdct=%d' % (get_size(_wdgcom), get_size(wdct)))
#             print('hdw_accel_save_hdr: SIZES: self.data_dct=%d data_dct_str=%d' % (get_size(self.data_dct), get_size(data_dct_str)))
#             print('hdw_accel_save_hdr: SIZES: dct=%d ' % (get_size(dct)))
#
#             self.main_obj.zmq_save_dict_to_tmp_file(dct)
#
#             dct = {}
#             dct['cmd'] = CMD_EXPORT_TMP_TO_NXSTXMFILE
#             self.main_obj.zmq_save_dict_to_tmp_file(dct)
#
#         self.on_save_sample_image(_data=self.img_data[_spatial_roi_idx])
#
#         # _logger.info('save_hdr: done')
#         if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
#             self.main_obj.device('CX_auto_disable_power').put(1)  # enabled
#             self.main_obj.device('CY_auto_disable_power').put(1)  # enabled

    def hdw_accel_chk_for_more_evregions(self):
        """
        chk_for_more_evregions(): description

        :returns: None
        """
        """
        this slot handles the end of scan, when the default on_scan_done() is called in the
        base scan class it will check for an installed child on_scan_done slot (this one)
        once this has been called it returns True or False
            return True if there are no more ev regions and you want the default on_scan_done(0) to finish and clean everything up

            return False if there are more ev Regions and you dont want everything stopped and cleaned up
        """
        multi_ev_single_image_scans = [scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_POINT_SPECTRA]

        _logger.info('hdw_accel_chk_for_more_evregions: checking')

        if (self._abort):
            _logger.info('hdw_accel_chk_for_more_evregions: scan aborting')
            # make sure to save current scan
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()
            # self.on_save_sample_image()
            self.on_data_level_done()
            self.save_hdr()
            self.hdr.remove_tmp_file()

            return (True)

        # increment the index into ev regions
        self.incr_evidx()

        # if(self._current_ev_idx < len(self.e_rois)):
        if (self.get_evidx() < len(self.e_rois)):
            _logger.info('hdw_accel_chk_for_more_evregions: yes there is, loading and starting')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                if(not self.is_point_spec):
                    self.gate.stop()
                    self.counter.stop()

            if (self.scan_type not in multi_ev_single_image_scans):
                # signal plotter to start a new image
                # sp_id = self.get_next_spatial_id()
                # self.new_spatial_start.emit(sp_id)
                self.new_spatial_start.emit(self.sp_db[SPDB_ID_VAL])

            e_roi = self.e_rois[self._current_ev_idx]
            # configure next ev sscan record with next ev region start/stop
            self._config_start_stop(self.evScan, 1, e_roi[START], e_roi[STOP], e_roi[NPOINTS])

            # prev_dwell = self.dwell
            self.dwell = e_roi[DWELL]

            if (self.use_hdw_accel):
            #     # need to check to see if dwell changed, if it did we need to re-configure the wavetables
            #     # if(prev_dwell != self.dwell):
            #     # _logger.debug('dwell changed [%.2f] so reconfiguring the hardware accel' % self.dwell)
                 self.modify_config()
                 # wait for gate and counter to start
            #     time.sleep(2.0)
            #    pass


            # need to determine the scan velocity if there is a change in Dwell for this next ev region
            elif (not self.is_point_spec):
                # the dwell ime for the new ev region could have changed so determine the scan velo and accRange
                # need to determine the scan velocity if there is a change in Dwell for this next ev region
                if (self.is_line_spec and self.is_pxp):
                    scan_velo = self.get_mtr_max_velo(self.xyScan.P1)
                    # vmax = self.get_mtr_max_velo(self.xyScan.P1)
                else:
                    vmax = self.get_mtr_max_velo(self.xScan.P1)
                    (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                                   self.numX, vmax, do_points=True)
                    # need the range of scan to be passed to calc_accRange()
                    rng = self.x_roi[STOP] - self.x_roi[START]
                    accRange = calc_accRange('SampleX', 'Fine', rng, scan_velo, dwell, accTime=0.04)
                    # reassign dwell because it ay have changed on return from ensure_valid_values()
                    self.dwell = dwell
                    _logger.debug('set_sample_scan_velocity Image scan: scan_velo=%.2f um/s accRange=%.2f um' % (
                    scan_velo, accRange))

                self.set_x_scan_velo(scan_velo)
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()


            elif (self.is_point_spec):
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()

            self.start()
            # let caller know were not done
            return (False)
        else:
            _logger.info('chk_for_more_evregions: Nope no more')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()

            # ok scan is all done now, so save final header file
            if (not self.file_saved):
                _logger.debug('chk_for_more_evregions: calling on_save_sample_image()')
                self.on_save_sample_image()
            self.save_hdr()

            # ok there are no more ev regions to execute
            return (True)

    def coarse_chk_for_more_evregions(self):
        """
        chk_for_more_evregions(): description

        :returns: None
        """
        """
        this slot handles the end of scan, when the default on_scan_done() is called in the 
        base scan class it will check for an installed child on_scan_done slot (this one)
        once this has been called it returns True or False
            return True if there are no more ev regions and you want the default on_scan_done(0) to finish and clean everything up

            return False if there are more ev Regions and you dont want everything stopped and cleaned up 
        """
        multi_ev_single_image_scans = [scan_types.SAMPLE_LINE_SPECTRA, scan_types.SAMPLE_POINT_SPECTRA]

        # Sept 6 if(TEST_SAVE_INITIAL_FILE):
        # Sept 6     self.save_hdr(update=True)
        _logger.info('chk_for_more_evregions: checking')

        if (self._abort):
            _logger.info('chk_for_more_evregions: scan aborting')
            # make sure to save current scan
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                self.gate.stop()
                self.counter.stop()
            # self.on_save_sample_image()
            # self.on_data_level_done()
            self.save_hdr()
            self.hdr.remove_tmp_file()

            return (True)

        # increment the index into ev regions
        self.incr_evidx()

        # if(self._current_ev_idx < len(self.e_rois)):
        if (self.get_evidx() < len(self.e_rois)):
            _logger.info('chk_for_more_evregions: yes there is, loading and starting')
            if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                if (not self.is_point_spec):
                    self.gate.stop()
                    self.counter.stop()

                    # sept 11
                    self.counter.wait_till_stopped()

            if (self.scan_type not in multi_ev_single_image_scans):
                # signal plotter to start a new image
                # sp_id = self.get_next_spatial_id()
                # self.new_spatial_start.emit(sp_id)
                self.new_spatial_start.emit(self.sp_db[SPDB_ID_VAL])

            e_roi = self.e_rois[self._current_ev_idx]
            # configure next ev sscan record with next ev region start/stop
            self._config_start_stop(self.evScan, 1, e_roi[START], e_roi[STOP], e_roi[NPOINTS])

            # prev_dwell = self.dwell
            self.dwell = e_roi[DWELL]

            if (self.use_hdw_accel):
                # need to check to see if dwell changed, if it did we need to re-configure the wavetables
                # if(prev_dwell != self.dwell):
                # _logger.debug('dwell changed [%.2f] so reconfiguring the hardware accel' % self.dwell)
                self.modify_config()
                # wait for gate and counter to start
                time.sleep(2.0)

            # need to determine the scan velocity if there is a change in Dwell for this next ev region
            elif (not self.is_point_spec):
                # the dwell ime for the new ev region could have changed so determine the scan velo and accRange
                # need to determine the scan velocity if there is a change in Dwell for this next ev region
                if (self.is_line_spec and self.is_pxp):
                    scan_velo = self.get_mtr_max_velo(self.xyScan.P1)
                    # vmax = self.get_mtr_max_velo(self.xyScan.P1)
                else:
                    vmax = self.get_mtr_max_velo(self.xScan.P1)
                    (scan_velo, npts, dwell) = ensure_valid_values(self.x_roi[START], self.x_roi[STOP], self.dwell,
                                                                   self.numX, vmax, do_points=True)
                    # need the range of scan to be passed to calc_accRange()
                    rng = self.x_roi[STOP] - self.x_roi[START]
                    accRange = calc_accRange('SampleX', 'Fine', rng, scan_velo, dwell, accTime=0.04)
                    # reassign dwell because it ay have changed on return from ensure_valid_values()
                    self.dwell = dwell
                    _logger.debug('set_sample_scan_velocity Image scan: scan_velo=%.2f um/s accRange=%.2f um' % (
                    scan_velo, accRange))

                self.set_x_scan_velo(scan_velo)
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.start()
                    self.counter.start()
                    # sept 11
                    self.counter.wait_till_running()


            elif (self.is_point_spec):
                # ok now finish configuration and start it
                self.on_this_dev_cfg()
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    if (not self.is_point_spec):
                        self.gate.start()
                        self.counter.start()
                        # sept 11
                        self.counter.wait_till_running()

            self.start()
            # let caller know were not done
            return (False)
        else:
            _logger.info('chk_for_more_evregions: Nope no more')
            if ((not self.is_point_spec) and self.coarse_chk_for_more_spatial_regions()):
                # were not done
                return (False)
            else:
                if (self.main_obj.get_beamline_id() is BEAMLINE_IDS.STXM):
                    self.gate.stop()
                    self.counter.stop()

                # ok scan is all done now, so save final header file
                if (not self.file_saved):
                    _logger.debug('chk_for_more_evregions: calling on_save_sample_image()')
                    self.on_save_sample_image()
                self.save_hdr()

                # ok there are no more spatial regions to execute
                return (True)

    def coarse_chk_for_more_spatial_regions(self):
        """
        chk_for_more_spatial_regions(): this slot handles the end of scan, when the default on_scan_done() is called in the
            base scan class it will check for an installed child on_scan_done slot (this one)
            once this has been called it returns True or False

            return True if there are more spatial Regions and you dont want everything stopped and cleaned up

            return False if there are no more spatial regions and you want the default on_scan_done(0 to finish and clean everything up

        :returns: True if there are more spatial Regions and you dont want everything stopped and cleaned up
                return False if there are no more spatial regions and you want the default on_scan_done(0 to finish and clean everything up

        """
        _logger.info('chk_for_more_spatial_regions: checking')

        if (self._abort):
            _logger.info('chk_for_more_spatial_regions: scan aborting')
            self.save_hdr()
            self.hdr.remove_tmp_file()
            return (True)

        # get the next spatial ID in the list of spatial regions we are to scan
        sp_id = self.get_next_spatial_id()
        if (sp_id is not None):
            # save the current one and then go again
            self.save_hdr()

            _logger.info('chk_for_more_spatial_regions: found sp_id=%d, loading and starting' % sp_id)

            # because we will be starting a new scan that will have new self.data created we need to reinit the index to the data
            # because imgidx is what is used as the first dimension of the data
            _logger.info('chk_for_more_spatial_regions: resetting the data image index')
            self.reset_imgidx()

            if (self.is_lxl):
                self.configure(self.wdg_com, sp_id, ev_idx=0, line=True, block_disconnect_emit=True)
            else:
                if (self.is_point_spec):
                    self.configure(self.wdg_com, sp_id, ev_idx=0, line=False, block_disconnect_emit=True)
                else:
                    self.configure(self.wdg_com, sp_id, ev_idx=0, line=False, block_disconnect_emit=True)
            self.start()
            return (True)
        else:
            _logger.info('chk_for_more_spatial_regions: nope all done')
            return (False)