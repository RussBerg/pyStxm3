
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
from cls.applications.pyStxm.main_obj_init import MAIN_OBJ

from cls.scanning.BaseScan import BaseScan, SIM_SPEC_DATA, SIMULATE_SPEC_DATA
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan, set_devices_for_line_scan, make_timestamp_now
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

#appConfig = ConfigClass(abs_path_to_ini_file)

#get the accel distance for now from the app configuration
ACCEL_DISTANCE = MAIN_OBJ.get_preset_as_float('fine_accel_distance')

class FineSampleImageScanClass(BaseScan):
    '''
    This class is used to implement Coarse scans for conventional mode scanning
    '''


    def __init__(self, main_obj=None):
        """
        __init__(): description

        :returns: None
        """
        super(FineSampleImageScanClass, self).__init__(main_obj=main_obj)
        self.x_use_reinit_ddl = False
        self.x_auto_ddl = True
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
            mtr_x = self.main_obj.device(mtr_dct['fx_name'])
            mtr_y = self.main_obj.device(mtr_dct['fy_name'])
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
        # md = {'entry_name': 'entry0', 'scan_type': self.scan_type,
        #       'rois': {SPDB_X: self.x_roi, SPDB_Y: self.y_roi},
        #       'dwell': self.dwell,
        #       'primary_det': DNM_DEFAULT_COUNTER,
        #       'zp_def': zp_def,
        #       'wdg_com': dict_to_json(self.wdg_com)}
        md = {'metadata': dict_to_json(self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type, dets=dets))}

        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        def do_scan():
            mtr_x = self.main_obj.device(DNM_SAMPLE_X)
            mtr_y = self.main_obj.device(DNM_SAMPLE_Y)
            shutter = self.main_obj.device(DNM_SHUTTER)

            yield from bps.stage(gate)
            # the detector will be staged automatically by the grid_scan plan
            shutter.open()
            bps.open_run(md=md)

            # go to start of line
            yield from bps.mv(mtr_x, self.x_roi[START] - ACCEL_DISTANCE, mtr_y, self.y_roi[START])

            # now do a horizontal line for every new zoneplate Z setpoint
            for y_sp in self.y_roi[SETPOINTS]:
                yield from bps.mv(mtr_y, y_sp, mtr_x, self.x_roi[START] - ACCEL_DISTANCE)
                yield from bps.mv(mtr_x, self.x_roi[STOP] + ACCEL_DISTANCE)

            shutter.close()

            yield from bps.unstage(gate)
            bps.close_run()
            print('CoarseSampleImageScanClass LxL: make_scan_plan Leaving')

        return (yield from do_scan())


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
        super(FineSampleImageScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        _logger.info('\n\nFineSampleImageScanClass: configuring sp_id [%d]' % sp_id)
        self.new_spatial_start_sent = False
        # initial setup and retrieval of common scan information
        # self.set_spatial_id(sp_id)
        # self.wdg_com = wdg_com
        # self.sp_rois = wdg_com[WDGCOM_SPATIAL_ROIS]
        # self.sp_ids = list(self.sp_rois.keys())
        # self.sp_db = self.sp_rois[sp_id]
        # self.scan_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_TYPE)
        # self.scan_sub_type = dct_get(self.sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)
        # self.sample_positioning_mode = MAIN_OBJ.get_sample_positioning_mode()
        #
        # self.update_roi_member_vars(self.sp_db)
        #
        # #the wavegenerator does both axis in one sscan record by calling the wavegenerator to execute,
        # # this is done in sscan2
        # self.xScan = self._scan1
        # self.yScan = self._scan2
        # self.xyScan = None
        #
        # self.determine_scan_res()
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

        # # setup some convienience member variables
        # self.dwell = e_roi[DWELL]
        # self.numX = int(self.x_roi[NPOINTS])
        # self.numY = int(self.y_roi[NPOINTS])
        # self.numZX = int(self.zx_roi[NPOINTS])
        # self.numZY = int(self.zy_roi[NPOINTS])
        # self.numEPU = len(self.setpointsPol)
        # # self.numE = self.sp_db[SPDB_EV_NPOINTS] * len(self.setpointsPol)
        # self.numE = int(self.sp_db[SPDB_EV_NPOINTS])
        # self.numSPIDS = len(self.sp_rois)
        # self.numImages = 1

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
        # if (self.scan_sub_type == scan_sub_types.LINE_UNIDIR):
        #     # LINE_UNIDIR
        #     self.is_lxl = True
        #     _id = 'ev_pol_lxl'
        # else:
        #     # POINT_BY_POINT
        #     self.is_pxp = True
        #     _id = 'ev_pol_pxp'

        self.config_for_sample_holder_scan(dct)

        self.final_data_dir = self.config_hdr_datarecorder(self.stack, self.final_data_dir)
        # self.stack_scan = stack

        # make sure OSA XY is in its center
        self.move_osaxy_to_its_center()

        self.seq_map_dct = self.generate_2d_seq_image_map(self.numE, self.y_roi[NPOINTS], self.x_roi[NPOINTS], lxl=self.is_lxl)

        # THIS must be the last call
        self.finish_setup()
        # self.new_spatial_start.emit(sp_id)

