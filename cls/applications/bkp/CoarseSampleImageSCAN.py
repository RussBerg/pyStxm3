
'''
Created on Apr 26, 2017

@author: bergr
'''
import os
import copy
import atexit
import numpy as np
import time

from bluesky.plans import count, scan, grid_scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp

from bcm.devices.device_names import *

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
from cls.types.beamline import BEAMLINE_IDS
from cls.utils.prog_dict_utils import make_progress_dict
from cls.utils.json_utils import dict_to_json
from cls.utils.qt5_utils import get_signals

from cls.zeromq.epics.epics_api import *

from cls.plotWidgets.utils import *

_logger = get_module_logger(__name__)

appConfig = ConfigClass(abs_path_to_ini_file)


class CoarseSampleImageSCAN(BaseScan):
    '''
    This class is used to implement Coarse scans for conventional mode scanning
    '''


    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(CoarseSampleImageSSCAN, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), 'SAMPLEXY_EV_WG',
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

    def make_pxp_scan_plan(self, dets, gate, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        #zp_def = self.get_zoneplate_info_dct()
        mtr_dct = self.determine_samplexy_posner_pvs()
        md = copy.deepcopy(self.make_standard_data_metadata(entry_num=0, scan_type=self.scan_type))
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
            #md = self.make_standard_data_metadata(entry_num=0, scan_type=self.scan_type)
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

    def make_lxl_scan_plan(self, dets, gate, bi_dir=False):
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
        mtr_dct = self.determine_samplexy_posner_pvs()
        zp_def = self.get_zoneplate_info_dct()
        md = {'entry_name': 'entry0', 'scan_type': self.scan_type,
              'rois': {SPDB_X: self.x_roi, SPDB_Y: y_roi, SPDB_Z: zz_roi},
              'dwell': self.dwell,
              'primary_det': DNM_DEFAULT_COUNTER,
              'zp_def': zp_def,
              'wdg_com': dict_to_json(self.wdg_com)}

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        def do_scan():
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            bps.open_run(md=md)

            # go to start of line
            yield from bps.mv(mtr_x, self.x_roi[START], mtr_y, self.y_roi[CENTER])

            # now do a horizontal line for every new zoneplate Z setpoint
            for sp in self.zz_roi[SETPOINTS]:
                yield from bps.mv(mtr_z, sp)
                yield from bps.mv(mtr_z, self.x_roi[STOP])
                yield from bps.mv(mtr_z, self.x_roi[START])

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            bps.close_run()
            print('CoarseSampleImageScanClass LxL: make_scan_plan Leaving')

        return (yield from do_scan())

    # def init_update_dev_lst(self):
    #     '''
    #      populate the list of devices I want snapshotted on each data_level_done signal, I dont like that the nexus path
    #      is specified here, needs to be handled in a more standard way
    #     :return:
    #     '''
    #     self.update_dev_lst = []
    #     self.update_dev_lst.append(DNM_ENERGY)
    #
    #     self.update_dev_lst.append(DNM_EPU_POLARIZATION)
    #     self.update_dev_lst.append(DNM_EPU_ANGLE)
    #     self.update_dev_lst.append(DNM_EPU_GAP)
    #     self.update_dev_lst.append(DNM_EPU_HARMONIC)
    #     self.update_dev_lst.append(DNM_EPU_OFFSET)
    #
    #     self.update_dev_lst.append(DNM_PMT)
    #     self.update_dev_lst.append(DNM_RING_CURRENT)
    #     self.update_dev_lst.append(DNM_TYCHO_CAMERA)
    #
    #     #self.main_obj.zmq_register_upd_list(self.update_dev_lst)
    #
    #
    # def init_sscans(self):
    #
    #     self.cb_idxs = []
    #     self.ttl_pnts = 0
    #     self.final_data_dir = None
    #
    #     self.setupScan = SScanClass('%s:scan5' % self.scan_prefix, 'SETUP', main_obj=MAIN_OBJ)
    #     self._scan5 = SScanClass('%s:scan5' % self.scan_prefix, 'SSETUP', main_obj=MAIN_OBJ)
    #     self._scan4 = SScanClass('%s:scan4' % self.scan_prefix, SPDB_EV_EV, main_obj=MAIN_OBJ)
    #     self._scan3 = SScanClass('%s:scan3' % self.scan_prefix, SPDB_EV_POL, main_obj=MAIN_OBJ)
    #
    #     self._scan2 = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, posner=MAIN_OBJ.device(DNM_SAMPLE_Y),
    #                              main_obj=MAIN_OBJ)
    #     self._scan1 = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, posner=MAIN_OBJ.device(DNM_SAMPLE_X),
    #                              main_obj=MAIN_OBJ)
    #
    #     self.evScan = self._scan4
    #     self.evScan.set_positioner(1, MAIN_OBJ.device('ENERGY'))
    #
    #     self.polScan = self._scan3
    #     self.polScan.set_positioner(1, MAIN_OBJ.device(DNM_EPU_POLARIZATION))
    #     self.polScan.set_positioner(2, MAIN_OBJ.device(DNM_EPU_OFFSET))
    #     self.polScan.set_positioner(3, MAIN_OBJ.device(DNM_EPU_ANGLE))
    #
    #     ev_pol_lxl = {}
    #     ev_pol_lxl['cmd_file'] = '%s/coarseimage_ev_then_pol.cmd' % self.script_dir
    #     ev_pol_lxl['ev_section_id'] = SPDB_EV_EV
    #     ev_pol_lxl['pol_section_id'] = SPDB_EV_POL
    #     ev_pol_lxl['setup_scan'] = self.setupScan
    #     ev_pol_lxl['ev_scan'] = self._scan4
    #     ev_pol_lxl['pol_scan'] = self._scan3
    #     ev_pol_lxl['y_scan'] = self._scan2
    #     ev_pol_lxl['x_scan'] = self._scan1
    #     ev_pol_lxl['xy_scan'] = None
    #     ev_pol_lxl['top_lvl_scan'] = self._scan4
    #     ev_pol_lxl['data_lvl_scan'] = self._scan2
    #     ev_pol_lxl['btm_lvl_scan'] = self._scan1
    #     ev_pol_lxl['on_counter_changed'] = self.on_coarse_sample_scan_counter_changed
    #     ev_pol_lxl['on_data_level_done'] = self.on_this_scan_done
    #     ev_pol_lxl['on_abort_scan'] = self.on_abort_scan
    #     ev_pol_lxl['on_scan_done'] = None
    #     ev_pol_lxl['on_dev_cfg'] = self.on_this_dev_cfg
    #     ev_pol_lxl['modify_config'] = None
    #     ev_pol_lxl['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]
    #
    #     ev_pol_pxp = {}
    #     ev_pol_pxp['cmd_file'] = '%s/coarseimage_ev_then_pol_pxp.cmd' % self.script_dir
    #     ev_pol_pxp['ev_section_id'] = SPDB_EV_EV
    #     ev_pol_pxp['pol_section_id'] = SPDB_EV_POL
    #     ev_pol_pxp['setup_scan'] = self.setupScan
    #     ev_pol_pxp['ev_scan'] = self._scan4
    #     ev_pol_pxp['pol_scan'] = self._scan3
    #     ev_pol_pxp['y_scan'] = self._scan2
    #     ev_pol_pxp['x_scan'] = self._scan1
    #     ev_pol_pxp['xy_scan'] = None
    #     ev_pol_pxp['top_lvl_scan'] = self._scan4
    #     ev_pol_pxp['data_lvl_scan'] = self._scan2
    #     ev_pol_pxp['btm_lvl_scan'] = self._scan1
    #     ev_pol_pxp['on_counter_changed'] = self.on_sample_scan_counter_changed
    #     ev_pol_pxp['on_data_level_done'] = self.on_done_save_jpg_and_tmp_file
    #     ev_pol_pxp['on_abort_scan'] = self.on_abort_scan
    #     ev_pol_pxp['on_scan_done'] = None
    #     ev_pol_pxp['on_dev_cfg'] = self.on_this_dev_cfg
    #     ev_pol_pxp['modify_config'] = None
    #     ev_pol_pxp['scanlist'] = [self._scan1, self._scan2, self._scan3, self._scan4]
    #
    #     self.cmdfile_parms = {}
    #     self.cmdfile_parms['ev_pol_lxl'] = ev_pol_lxl
    #     self.cmdfile_parms['ev_pol_pxp'] = ev_pol_pxp
    #
    #     self.xyScan = self._scan1
    #
    #     self.lxl_yScan = self._scan2
    #     self.lxl_xScan = self._scan1
    #
    #     self.pxp_yScan = self._scan2
    #     self.pxp_xScan = self._scan1
    #
    #     self.pnt_yScan = self._scan2
    #     self.pnt_xScan = self._scan1

    def on_this_scan_done(self):
        # self.shutter.close()
        # self.gate.stop()
        # self.counter.stop()
        # #Jan 9 2018
        # self.ensure_data()
        #
        # self.save_hdr()
        # #self.on_save_sample_image()
        # self.on_scan_done_discon_sigs()
        pass

    # def ensure_data(self):
    #     _img_idx = self.get_imgidx() - 1
    #     # this is a temp hack to fix CoarseImageSSCAN
    #     if (not (hasattr(self, '_data'))):
    #         t_img_idx = _img_idx
    #         if (t_img_idx < 0):
    #             t_img_idx = 0
    #         _dct = self.get_img_idx_map(t_img_idx)
    #         sp_id = _dct['sp_id']
    #         sp_idx = _dct['sp_idx']
    #         pol_idx = _dct['pol_idx']
    #
    #         # for now just use the default counter
    #         counter = DNM_DEFAULT_COUNTER
    #         self._data = self.spid_data[counter][sp_id][pol_idx]
    #
    # def on_done_save_jpg_and_tmp_file(self):
    #     '''
    #     this is a handler for data_ready signal from SscanClass if there are more than one images being acquired
    #     the done here is for data_level_done, where we want to save a jpg, update the tmp file and continue IFF
    #     the current image idx does not qual the last image index
    #     :return:
    #     '''
    #     cur_idx = self.get_consecutive_scan_idx()
    #
    #     _logger.debug('CoarseSampleImageScanClass: on_done_save_jpg_and_tmp_file() called [%d]' % cur_idx)
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
    #
    # def on_scan_done_discon_sigs(self):
    #     """
    #     on_scan_done(): fires when the top level scan is done, calls on_child_scan_done() if one has been
    #     configured by parent scan plugin
    #
    #     :returns: None
    #     """
    #
    #     if (self.signals_connected):
    #         # _logger.debug('BaseScan: on_scan_done_discon_sigs: emitted all_done sig')
    #         self.all_done.emit()
    #     else:
    #         _logger.debug('BaseScan: on_scan_done_discon_sigs: ELSE: sigs were not connected')
    #     # if(done):
    #     self.disconnect_signals()
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
    #     if (self.x_roi[SCAN_RES] == 'COARSE'):
    #         self.xScan.put('PDLY', c_scan1_pdly)
    #         fx_done.put(c_fx_force_done)
    #     else:
    #         self.xScan.put('PDLY', f_scan1_pdly)
    #         fx_done.put(f_fx_force_done)
    #
    #     if (self.y_roi[SCAN_RES] == 'COARSE'):
    #         self.yScan.put('PDLY', c_scan2_pdly)
    #         fy_done.put(c_fy_force_done)
    #     else:
    #         self.yScan.put('PDLY', f_scan2_pdly)
    #         fy_done.put(f_fy_force_done)
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
        _logger.info('\n\nCoarseSampleImageScanClass: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
        self.set_spatial_id(sp_id)
        self.wdg_com = wdg_com
        self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        self.sp_ids = list(self.sp_rois.keys())
        self.sp_db = self.sp_rois[sp_id]
        self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()

        self.update_roi_member_vars(self.sp_db)

        #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
        # this is done in sscan2
        self.xScan = self._scan1
        self.yScan = self._scan2
        self.xyScan = None

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
            self.reset_pnt_spec_spid_idx()
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
            _id = 'ev_pol_lxl'
        else:
            # POINT_BY_POINT
            self.is_pxp = True
            _id = 'ev_pol_pxp'

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
        # dct = self.determine_samplexy_posner_pvs()

        self.config_for_sample_holder_scan(dct)

        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        # THIS must be the last call
        self.finish_setup()
        # self.new_spatial_start.emit(sp_id)

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



