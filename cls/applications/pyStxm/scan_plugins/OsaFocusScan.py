'''
Created on Sep 26, 2016

@author: bergr
'''
import os
from bcm.devices.device_names import *

from bluesky.plans import count, scan, grid_scan, scan_nd
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from cycler import cycler


from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
from cls.utils.roi_dict_defs import *

from cls.types.stxmTypes import scan_sub_types, scan_types
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.log import get_module_logger
from cls.utils.json_utils import dict_to_json
from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
from cls.scan_engine.bluesky.bluesky_defs import bs_dev_modes
from cls.scan_engine.bluesky.test_gate import trig_src_types

_logger = get_module_logger(__name__)


class OsaFocusScanClass(BaseScan):
    """ a scan for executing a detector point scan in X and Y, it takes an existing instance of an XYZScan class"""
    
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        super(OsaFocusScanClass, self).__init__('%sstxm' % MAIN_OBJ.get_sscan_prefix(), 'XYZ', main_obj=MAIN_OBJ)

    def init_subscriptions(self, ew, func):
        '''
        over ride the base init_subscriptions because we need to use the number of rows from the self.zz_roi instead of
        self.y_roi
        :param ew:
        :param func:
        :return:
        '''

        self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y=DNM_ZONEPLATE_Z_BASE, x=DNM_OSA_X,
                                                scan_type=self.scan_type, bi_dir=self._bi_dir)
        self._emitter_cb.set_row_col(rows=self.zz_roi[NPOINTS], cols=self.x_roi[NPOINTS])
        self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
        self._emitter_cb.new_plot_data.connect(func)

    def configure_devs(self, dets, gate):
        gate.set_dwell(self.dwell)
        gate.set_trig_src(trig_src_types.NORMAL_PXP)
        gate.set_mode(bs_dev_modes.NORMAL_PXP)

        # need to handle this better for multiple detectors, in the future todo
        dets[0].set_dwell(self.dwell)
        dets[0].set_num_points(1)

    def make_pxp_scan_plan(self, dets, gate, md=None, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir

        if (md is None):
            md = {'metadata': dict_to_json(
                self.make_standard_metadata(entry_name='entry0', scan_type=self.scan_type))}

        @bpp.baseline_decorator(dev_list)
        #@bpp.stage_decorator(dets)
        #@bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': scan_types.OSA_FOCUS})
        def do_scan():
            mtr_x = self.main_obj.device(DNM_OSA_X)
            mtr_y = self.main_obj.device(DNM_OSA_Y)
            mtr_z = self.main_obj.device(DNM_ZONEPLATE_Z_BASE)
            shutter = self.main_obj.device(DNM_SHUTTER)

            x_traj = cycler(mtr_x, self.x_roi[SETPOINTS])
            y_traj = cycler(mtr_y, self.y_roi[SETPOINTS])
            zz_traj = cycler(mtr_z, self.zz_roi[SETPOINTS])

            yield from bps.stage(gate)
            shutter.open()
            # the detector will be staged automatically by the grid_scan plan
            yield from scan_nd(dets, zz_traj * (y_traj + x_traj), md=md)

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)

            print('OsaFocusScanClass: make_scan_plan Leaving')

        return (yield from do_scan())

    def configure(self, wdg_com, sp_id=0, line=False, restore=True, z_enabled=True):
        """
        configure(): description

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param line=False: line=False description
        :type line=False: line=False type

        :param restore=True: restore=True description
        :type restore=True: restore=True type

        :param z_enabled=True: z_enabled=True description
        :type z_enabled=True: z_enabled=True type

        :returns: None
        """

        # self.stack = False
        # self.is_pxp = True
        # self.is_lxl = False
        # call the base class configure so that all member vars can be initialized
        super(OsaFocusScanClass, self).configure(wdg_com, sp_id=sp_id, line=line, z_enabled=z_enabled)

        self.is_pxp = True
        self.sub_type = scan_sub_types.POINT_BY_POINT

        self.configure_x_y_z_arb_linescan(wdg_com, sp_id=sp_id, line=line, z_enabled=z_enabled)
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
        #_logger.debug('OsaFocus: on_data_level_done:')
        #self.on_x_y_scan_data_level_done()
        pass

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        #stop gate and counter input tasks
        #MAIN_OBJ.device( 'OX_force_done' ).put(0) #Normal
        #MAIN_OBJ.device( 'OY_force_done' ).put(0)
        # self.gate.stop()
        # self.counter.stop()
        # self.on_this_data_level_done()
        # ##self.save_master()
        pass
