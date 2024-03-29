'''
Created on Sep 26, 2016

@author: bergr
'''
import copy
from bcm.devices.device_names import *

from bluesky.plans import count, scan, grid_scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv

from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
from cls.scanning.SScanClass import SScanClass
from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger
from cls.types.stxmTypes import scan_types
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types

_logger = get_module_logger(__name__)


class CoarseGoniScanClass(BaseScan):
    """ a scan for executing a coarse goni point scan in X and Y, it takes an existing instance of an XYZScan class"""

    def __init__(self, main_obj=None):
        """
        __init__():

        :returns: None
        """
        super(CoarseGoniScanClass, self).__init__('%sstxm' % main_obj.get_sscan_prefix(), SPDB_XY, main_obj=main_obj)


    def configure_devs(self, dets, gate):
        gate.set_dwell(self.dwell)
        gate.set_trig_src(trig_src_types.NORMAL_PXP)
        gate.set_mode(bs_dev_modes.NORMAL_PXP)

        # need to handle this better for multiple detectors, in the future todo
        dets[0].set_dwell(self.dwell)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        def do_scan():
            # Declare the end of the run.

            x_roi = self.sp_db['X']
            y_roi = self.sp_db['Y']
            mtr_x = MAIN_OBJ.device(DNM_GONI_X)
            mtr_y = MAIN_OBJ.device(DNM_GONI_Y)
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
            print('CoarseGoniScanClass: make_scan_plan Leaving')

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

    def configure(self, wdg_com, sp_id=0, line=True, restore=True, z_enabled=False):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param line=True: line=True description
        :type line=True: line=True type

        :param restore=True: restore=True description
        :type restore=True: restore=True type

        :param z_enabled=False: z_enabled=False description
        :type z_enabled=False: z_enabled=False type

        :returns: None
        """
        # use base configure x y motor scan
        # self.busy_saving = False
        # self.stack = False
        # self.is_pxp = True
        # self.is_lxl = False
        # call the base class configure so that all member vars can be initialized
        super(CoarseGoniScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=z_enabled)

        self.is_pxp = True

        self.config_basic_2d(wdg_com, sp_id=sp_id, z_enabled=False)
        # THIS must be the last call
        self.finish_setup()

        self.move_zpxy_to_its_center()

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
        # _logger.debug('Detector: on_data_level_done:')
        # MAIN_OBJ.device( 'DX_auto_disable_power' ).put(1) #enable again
        # MAIN_OBJ.device( 'DY_auto_disable_power' ).put(1)
        # self.on_x_y_scan_data_level_done()
        pass

    def on_this_dev_cfg(self):
        """
        on_this_dev_cfg(): description

        :returns: None
        """
        """
        this  is an API method to configure the gate, shutter and counter devices for this scan
        """
        # set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        pass


