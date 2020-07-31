"""
Created on Sep 26, 2016

@author: bergr
"""
import os
from bcm.devices.device_names import *

from bluesky.plans import count, scan, grid_scan
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
from cls.scan_engine.decorators import conditional_decorator
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.types.stxmTypes import scan_types, image_type_scans, spectra_type_scans
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types
from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get
from cls.appWidgets.dialogs import warn


_logger = get_module_logger(__name__)

class PtychographyScanClass(BaseScan):
    """ a scan for executing a detector point scan in X and Y, it takes an existing instance of an XYZScan class"""
    
    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(PtychographyScanClass, self).__init__(main_obj=MAIN_OBJ)
        self.inner_pts = []
        self.outer_pnts = []
        self.inner_posner = None
        self.outer_posner = None
        self.ev_first_flg = True # a flag so that the user can decide if they want the polarization to change every ev or vice versa

    def configure_devs(self, dets, gate):
        gate.set_dwell(self.dwell)
        gate.set_trig_src(trig_src_types.NORMAL_PXP)
        gate.set_mode(bs_dev_modes.NORMAL_PXP)

        for d in dets:
            if (hasattr(d, 'set_dwell')):
                d.set_dwell(self.dwell)

    def set_ev_first_flg(self, val):
        '''
        set the flag, 0 == EV then Pol, 1 == Pol then EV
        :param val:
        :return:
        '''
        self.ev_first_flg = val


    # def make_single_pxp_image_plan(self, dets, gate, md=None, bi_dir=False, do_baseline=True):
    #     '''
    #     self explanatory
    #     :param dets:
    #     :param gate:
    #     :param md:
    #     :param bi_dir:
    #     :param do_baseline:
    #     :return:
    #     '''
    #     dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
    #     self._bi_dir = bi_dir
    #     if (md is None):
    #         md = {'metadata': dict_to_json(
    #             self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
    #
    #
    #     @conditional_decorator(bpp.baseline_decorator(dev_list), do_baseline)
    #     #@bpp.stage_decorator(dets)
    #     #@bpp.run_decorator(md=md)
    #     def do_scan():
    #         # Declare the end of the run.
    #         mtr_x = self.main_obj.get_sample_fine_positioner('X')
    #         mtr_y = self.main_obj.get_sample_fine_positioner('Y')
    #         shutter = self.main_obj.device(DNM_SHUTTER)
    #         ccd = self.main_obj.device(DNM_GREATEYES_CCD)
    #
    #         #yield from bps.stage(gate)
    #
    #         #shutter.open()
    #
    #         #yield from bps.open_run(md)
    #         #start a new event document
    #         #yield from bps.create()
    #         for y in self.y_roi[SETPOINTS]:
    #             yield from bps.mv(mtr_y, y)
    #             #print('PtychographyScanClass: moving Y to [%.3f]' % y)
    #             for x in self.x_roi[SETPOINTS]:
    #                 #print('PtychographyScanClass: moving X to [%.3f]' % x)
    #                 yield from bps.mv(mtr_x, x)
    #                 #print('PtychographyScanClass: calling ccd.acquire()')
    #
    #
    #                 img_dct = self.img_idx_map['%d' % self._current_img_idx]
    #                 _meta = self.make_standard_metadata(entry_name=img_dct['entry'], scan_type=self.scan_type)
    #                 _meta['det_fname'] = ccd.file_plugin.file_name
    #                 # md = {'metadata': dict_to_json(
    #                 #     self.make_standard_metadata(entry_name=img_dct['entry'], scan_type=self.scan_type))}
    #                 md = {'metadata': dict_to_json( _meta )}
    #
    #                 yield from bps.open_run(md)
    #                 yield from bps.trigger_and_read(dets)
    #                 yield from bps.close_run()
    #                 print('PtychographyScanClass: img_counter = [%d]' % self._current_img_idx)
    #                 self._current_img_idx += 1
    #
    #         #closes current event document
    #         #yield from bps.save()
    #         #shutter.close()
    #         # yield from bps.wait(group='e712_wavgen')
    #         #yield from bps.unstage(gate)
    #         #print('BaseScan: make_pxp_scan_plan: Leaving')
    #
    #     return (yield from do_scan())
    #
    # def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
    #     self._bi_dir = bi_dir
    #
    #     def do_scan():
    #         cntr = 0
    #         dwell_sec = self.dwell * 0.001
    #         outer_posner = self.main_obj.device(self.outer_posner)
    #         inner_posner = self.main_obj.device(self.inner_posner)
    #         mtr_x = self.main_obj.get_sample_fine_positioner('X')
    #         mtr_y = self.main_obj.get_sample_fine_positioner('Y')
    #         shutter = self.main_obj.device(DNM_SHUTTER)
    #         ccd = self.main_obj.device(DNM_GREATEYES_CCD)
    #         #set the output file path and configure ccd
    #         ccd.file_plugin.file_path.put('/home/bergr/SM/test_data/')
    #         ccd.file_plugin.file_name.put('Ctest_')
    #         ccd.file_plugin.file_number.put(0)
    #
    #         ccd.cam.image_mode.put(0) # single
    #         ccd.cam.trigger_mode.put(0)  # internal
    #         ccd.cam.acquire_time.put(dwell_sec)
    #         #Ru says the acquire period should be a tad longer than exposer time
    #         ccd.cam.acquire_period.put(dwell_sec + 0.002)
    #
    #         dets = [ccd, mtr_x, mtr_y]
    #         yield from bps.stage(gate)
    #         yield from bps.stage(ccd)
    #
    #         shutter.open()
    #
    #         for op in self.outer_pnts:
    #             #print('PtychographyScanClass: moving outter posner [%s] to [%.2f]' % (outer_posner.get_name(), op))
    #             yield from bps.mv(outer_posner, op)
    #
    #             for ip in self.inner_pts:
    #                 #print('PtychographyScanClass: moving inner posner [%s] to [%.2f]' % (inner_posner.get_name(), ip))
    #                 yield from bps.mv(inner_posner, ip)
    #
    #                 img_dct = self.img_idx_map['%d' % self._current_img_idx]
    #                 md = {'metadata': dict_to_json(
    #                     self.make_standard_metadata(entry_name=img_dct['entry'], scan_type=self.scan_type))}
    #
    #                 if(self._current_img_idx == 0):
    #                     do_baseline = True
    #                 else:
    #                     do_baseline = False
    #
    #                 yield from self.make_single_pxp_image_plan(dets, gate, do_baseline=do_baseline)
    #
    #         print('PtychographyScanClass: done closing shutter')
    #         shutter.close()
    #         # yield from bps.wait(group='e712_wavgen')
    #         yield from bps.unstage(gate)
    #         yield from bps.unstage(ccd)
    #         print('PtychographyScanClass: make_scan_plan Leaving')
    #
    #     return (yield from do_scan())

    # def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
    #     dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
    #     self._bi_dir = bi_dir
    #     num_ttl_imgs = len(self.inner_pts) * len(self.outer_pnts) * self.y_roi[NPOINTS] * self.x_roi[NPOINTS]
    #
    #     if (md is None):
    #         _meta = self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type)
    #         _meta['num_ttl_imgs'] = num_ttl_imgs
    #         _meta['img_idx_map'] = dict_to_json(self.img_idx_map)
    #         md = {'metadata': dict_to_json(_meta)}
    #
    #         # md = {'metadata': dict_to_json(
    #         #     self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
    #
    #     @bpp.run_decorator(md=md)
    #     @bpp.baseline_decorator(dev_list)
    #     #@bpp.stage_decorator(dets)
    #     def do_scan():
    #         img_cntr = 0
    #         dwell_sec = self.dwell * 0.001
    #         outer_posner = self.main_obj.device(self.outer_posner)
    #         inner_posner = self.main_obj.device(self.inner_posner)
    #         mtr_x = self.main_obj.get_sample_fine_positioner('X')
    #         mtr_y = self.main_obj.get_sample_fine_positioner('Y')
    #         shutter = self.main_obj.device(DNM_SHUTTER)
    #         ccd = self.main_obj.device(DNM_GREATEYES_CCD)
    #         #set the output file path and configure ccd
    #         ccd.file_plugin.file_path.put('/home/bergr/SM/test_data/')
    #         ccd.file_plugin.file_name.put('Ctest_')
    #         ccd.file_plugin.file_number.put(img_cntr)
    #
    #         ccd.cam.image_mode.put(0) # single
    #         ccd.cam.trigger_mode.put(0)  # internal
    #         ccd.cam.acquire_time.put(dwell_sec)
    #         #Ru says the acquire period should be a tad longer than exposer time
    #         ccd.cam.acquire_period.put(dwell_sec + 0.002)
    #
    #         yield from bps.stage(gate)
    #         yield from bps.stage(ccd)
    #
    #         shutter.open()
    #
    #         for op in self.outer_pnts:
    #             #print('PtychographyScanClass: moving outter posner [%s] to [%.2f]' % (outer_posner.get_name(), op))
    #             yield from bps.mv(outer_posner, op)
    #
    #             for ip in self.inner_pts:
    #                 #print('PtychographyScanClass: moving inner posner [%s] to [%.2f]' % (inner_posner.get_name(), ip))
    #                 yield from bps.mv(inner_posner, ip)
    #
    #                 for y in self.y_roi[SETPOINTS]:
    #                     yield from bps.mv(mtr_y, y)
    #                     #print('PtychographyScanClass: moving Y to [%.3f]' % y)
    #                     for x in self.x_roi[SETPOINTS]:
    #                         #print('PtychographyScanClass: moving X to [%.3f]' % x)
    #                         yield from bps.mv(mtr_x, x)
    #                         #print('PtychographyScanClass: calling ccd.acquire()')
    #                         yield from bps.trigger_and_read([ccd, mtr_y, mtr_x])
    #                         img_cntr += 1
    #                         print('PtychographyScanClass: img_counter = [%d]' % img_cntr)
    #
    #
    #         print('PtychographyScanClass: done closing shutter')
    #         shutter.close()
    #         # yield from bps.wait(group='e712_wavgen')
    #         yield from bps.unstage(gate)
    #         yield from bps.unstage(ccd)
    #
    #         print('PtychographyScanClass: make_scan_plan Leaving')
    #
    #     return (yield from do_scan())

    def pre_flight_chk(self):
        '''
        before the scan plan is configured and executed it must first pass a pre flight check,
        to be implemented by inheriting class
        :return:
        '''
        ccd = self.main_obj.device(DNM_GREATEYES_CCD)
        temp = ccd.get_temperature()

        #make sure temperature is -20 before allowing scan to execute
        if(temp > -20.0):
            _logger.warn('CCD temperature [%.2f C] is too warm to execute scan, must be -20.0C or less' % temp)
            self.display_message('CCD temperature [%.2f C] is too warm to execute scan, must be -20.0C or less' % temp)
            return(False)
        else:
            return(True)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()

        dwell_sec = self.dwell * 0.001
        self._bi_dir = bi_dir
        num_ttl_imgs = len(self.inner_pts) * len(self.outer_pnts) * self.y_roi[NPOINTS] * self.x_roi[NPOINTS]
        ccd = self.main_obj.device(DNM_GREATEYES_CCD)
        # set the output file path and configure ccd
        #ccd.file_plugin.file_path.put('/home/bergr/SM/test_data/')
        _rpath = dct_get(self.sp_db[SPDB_ACTIVE_DATA_OBJECT], ADO_CFG_STACK_DIR)
        ccd.file_plugin.read_path_template = _rpath
        _cur_datadir = _rpath.replace('/', '')
        _cur_datadir = _cur_datadir.replace('G:\\', '/home/bergr/')
        _cur_datadir = _cur_datadir.replace('\\', '/')
        #ccd.file_plugin.reg_root.put('/home/bergr/SM')
        ccd.file_plugin.file_path.put(_cur_datadir)
        #ccd.file_plugin.read_path_template = ccd.file_plugin.write_path_template = _cur_datadir
        ccd.file_plugin.write_path_template = _cur_datadir


        #ccd.file_plugin.file_path.put('/opt/test_data/')
        # ccd.file_plugin.file_name.put('Ctest_')
        ccd.file_plugin.file_number.put(0)
        ccd.file_plugin.auto_save.put(1)
        #ccd.file_plugin.create_directory.put(-2) # this will create at least 2 levels of directories if they do not already exist
        # self.file_plugin.compression.put(6)  # set to LZ4
        #ccd.file_plugin.compression.put(0)  # set to NONE

        ccd.cam.image_mode.put(0)  # single
        ccd.cam.trigger_mode.put(0)  # internal
        ccd.cam.acquire_time.put(dwell_sec)
        # Ru says the acquire period should be a tad longer than exposer time
        ccd.cam.acquire_period.put(dwell_sec + 0.002)

        ccd.stage()

        if (md is None):
            _meta = self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, dets=dets)

            # hack, need to do this the proper way once all is working
            #modify the det names list
            l = []
            for n in _meta['detector_names']:
                if n.find(DNM_DEFAULT_COUNTER) > -1:
                    pass
                elif n.find('GE_CCD') > -1:
                    #the name GE_CCD_image shows up in data streeam not GE_CCD
                    l.append('GE_CCD_image')
                else:
                    l.append(n)
            _meta['detector_names'] = l
            _meta['num_ttl_imgs'] = num_ttl_imgs
            _meta['img_idx_map'] = dict_to_json(self.img_idx_map)
            _meta['det_filepath'] = ccd.file_plugin.file_path.get() + ccd.file_plugin.file_name.get() + '_000000.h5'
            md = {'metadata': dict_to_json(_meta)}

            # md = {'metadata': dict_to_json(
            #     self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}


        @bpp.baseline_decorator(dev_list)
        #@bpp.stage_decorator(dets)
        @bpp.run_decorator(md=md)
        def do_scan():
            # img_cntr = 0
            # dwell_sec = self.dwell * 0.001
            outer_posner = self.main_obj.device(self.outer_posner)
            inner_posner = self.main_obj.device(self.inner_posner)
            mtr_x = self.main_obj.get_sample_fine_positioner('X')
            mtr_y = self.main_obj.get_sample_fine_positioner('Y')
            shutter = self.main_obj.device(DNM_SHUTTER)
            ring_cur = self.main_obj.device(DNM_RING_CURRENT).get_ophyd_device()
            ccd = self.main_obj.device(DNM_GREATEYES_CCD)
            #pmt = self.main_obj.device(DNM_DEFAULT_COUNTER)
            # #Ru says the acquire period should be a tad longer than exposer time
            # ccd.cam.acquire_period.put(dwell_sec + 0.002)

            yield from bps.stage(gate)

            shutter.open()
            img_cntr = 0
            for op in self.outer_pnts:
                #print('PtychographyScanClass: moving outter posner [%s] to [%.2f]' % (outer_posner.get_name(), op))
                yield from bps.mv(outer_posner, op)

                for ip in self.inner_pts:
                    #print('PtychographyScanClass: moving inner posner [%s] to [%.2f]' % (inner_posner.get_name(), ip))
                    yield from bps.mv(inner_posner, ip)

                    for y in self.y_roi[SETPOINTS]:
                        yield from bps.mv(mtr_y, y)
                        #print('PtychographyScanClass: moving Y to [%.3f]' % y)
                        for x in self.x_roi[SETPOINTS]:
                            #print('PtychographyScanClass: moving X to [%.3f]' % x)
                            yield from bps.mv(mtr_x, x)
                            #print('PtychographyScanClass: calling ccd.acquire()')
                            #yield from bps.trigger_and_read(dets + [ccd, mtr_y, mtr_x])
                            #yield from bps.trigger_and_read(dets + [mtr_y, mtr_x])
                            # yield from bps.trigger_and_read(dets)
                            yield from bps.trigger_and_read([ccd, ring_cur, mtr_y, mtr_x])
                            img_cntr += 1
                            print('PtychographyScanClass: img_counter = [%d]' % img_cntr)


            print('PtychographyScanClass: done closing shutter')
            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            yield from bps.unstage(ccd)

            print('PtychographyScanClass: make_scan_plan Leaving')

        return (yield from do_scan())

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        pass
        # #stop gate and counter input tasks
        # #MAIN_OBJ.device( 'OX_force_done' ).put(0) #force
        # #MAIN_OBJ.device( 'OY_force_done' ).put(0)
        # self.gate.stop()
        # self.counter.stop()
        # self.on_this_data_level_done()
        # #self.save_master()
        
    def configure(self, wdg_com, sp_id=0, line=False, restore=True, z_enabled=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param line=False: line=False description
        :type line=False: line=False type

        :param restore=True: restore=True description
        :type restore=True: restore=True type

        :param z_enabled=False: z_enabled=False description
        :type z_enabled=False: z_enabled=False type

        :returns: None
        """
        #self.busy_saving = False
        # self.stack = False
        # self.is_pxp = True
        # self.is_lxl = False
        # call the base class configure so that all member vars can be initialized
        super(PtychographyScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=z_enabled)

        self.is_pxp = True

        self.config_basic_2d(wdg_com, sp_id=sp_id, z_enabled=False)

        ######################## NEW ######################################################################
        # this img_idx_map is used in teh on_counter_changed handler to put the data in the correct array
        self.inner_pts = []
        self.outer_pnts = []

        if (self.ev_first_flg == 0):
            # ev is on the outer loop
            outer_nm = 'e_idx'
            inner_nm = 'pol_idx'
            self.outer_pnts = []
            for ev_roi in self.e_rois:
                for ev_sp in ev_roi[SETPOINTS]:
                    self.outer_pnts.append(ev_sp)
            pol_setpoints = self.e_rois[0][EPU_POL_PNTS]
            self.dwell = self.e_rois[0][DWELL]
            for pol in pol_setpoints:
                self.inner_pts.append(pol)
            self.outer_posner = DNM_ENERGY
            self.inner_posner = DNM_EPU_POLARIZATION
        else:
            # polarization is on the outer loop
            inner_nm = 'e_idx'
            outer_nm = 'pol_idx'
            for ev_roi in self.e_rois:
                for ev_sp in ev_roi[SETPOINTS]:
                    self.inner_pts.append(ev_sp)

            pol_setpoints = self.e_rois[0][EPU_POL_PNTS]
            self.dwell = self.e_rois[0][DWELL]
            for pol in pol_setpoints:
                self.outer_pnts.append(pol)
            self.outer_posner = DNM_EPU_POLARIZATION
            self.inner_posner = DNM_ENERGY

        self.img_idx_map = {}
        indiv_img_idx = 0
        spid = list(self.sp_rois.keys())[0]
        sp_idx = 0
        offset = 0
        gt_mtr = self.main_obj.device(DNM_GONI_THETA)
        if (gt_mtr):
            gt_sp = gt_mtr.get_position()
        else:
            gt_sp = 0.0

        # for future Ptycho/Tomo
        # for gt_sp in self.gt_roi[SETPOINTS]:
        #     for i in range(len(self.outer_pnts)):
        #         for j in range(self.inner_pts):
        #             for y in self.y_roi[SETPOINTS]:
        #                 for x in self.x_roi[SETPOINTS]:
        #                     self.img_idx_map['%d' % indiv_img_idx] = {outer_nm: i, inner_nm: j, 'sp_idx': sp_idx, 'sp_id': spid,
        #                                                               'entry': 'entry%d' % (sp_idx),
        #                                                               'rotation_angle': gt_sp}
        #
        #                     indiv_img_idx += 1

        finex_nm = self.main_obj.get_sample_fine_positioner('X').get_name()
        finey_nm = self.main_obj.get_sample_fine_positioner('Y').get_name()
        self.x_roi[POSITIONER] = finex_nm
        self.y_roi[POSITIONER] = finey_nm


        for i in range(len(self.outer_pnts)):
            for j in range(len(self.inner_pts)):
                for y in self.y_roi[SETPOINTS]:
                    for x in self.x_roi[SETPOINTS]:
                        self.img_idx_map['%d' % indiv_img_idx] = {outer_nm: i, inner_nm: j, 'sp_idx': sp_idx, 'sp_id': spid,
                                                                  'entry': 'entry%d' % (sp_idx),
                                                                  'rotation_angle': gt_sp}

                        indiv_img_idx += 1
            # if (self.numEPU is 1):
            #     offset += 1
            # else:
            #     offset += 2

        #####################################################################################

        self.seq_map_dct = self.generate_2d_seq_image_map(1, self.y_roi[NPOINTS], self.x_roi[NPOINTS], lxl=False)

        self.move_zpxy_to_its_center()
        
        
        
    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        # add one so that the first one which will endup being 0 because of the ediff calc will be removed

        #set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
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
        #_logger.debug('Osa: on_data_level_done:')
        #self.on_x_y_scan_data_level_done()
        pass
        
        
        