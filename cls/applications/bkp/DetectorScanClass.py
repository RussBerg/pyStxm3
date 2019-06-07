'''
Created on Sep 26, 2016

@author: bergr
'''
import os
import copy
from bcm.devices.device_names import *

from bluesky.plans import count, scan, grid_scan
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
#from bluesky.plan_stubs import pause, open_run, close_run, sleep, mv

#from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.scanning.BaseScan import BaseScan
#from cls.scanning.SScanClass import SScanClass
#from cls.scanning.scan_cfg_utils import set_devices_for_point_scan
from cls.utils.roi_dict_defs import *
from cls.utils.log import get_module_logger
from cls.types.stxmTypes import scan_types, image_type_scans, spectra_type_scans
#from cls.scan_engine.bluesky.data_emitters import ImageDataEmitter
from cls.utils.json_utils import dict_to_json
#from .device_list import devs_as_list


_logger = get_module_logger(__name__)


class DetectorScan(BaseScan):
    """ a scan for executing a detector point scan in X and Y, it takes an existing instance of an XYZScan class"""
    
    def __init__(self, main_obj=None):
        """
        __init__():
        
        :returns: None
        """
        super(DetectorScan, self).__init__('%sstxm' % main_obj.get_sscan_prefix(), SPDB_XY, main_obj=main_obj)

    # def clear_subscriptions(self, ew):
    #     if(self._emitter_sub is not None):
    #         ew.unsubscribe_cb(self._emitter_sub)
    #     self._emitter_cb = None
    #
    # def init_subscriptions(self, ew, func):
    #
    #     if(self.scan_type in image_type_scans):
    #         #self._emitter_cb = ImageDataEmitter('point_det_single_value_rbv', y='mtr_y', x='mtr_x', scan_type=scan_types.DETECTOR_IMAGE, bi_dir=self._bi_dir)
    #         self._emitter_cb = ImageDataEmitter('%s_single_value_rbv' % DNM_DEFAULT_COUNTER, y='mtr_y', x='mtr_x',
    #                                             scan_type=self.scan_type, bi_dir=self._bi_dir)
    #         self._emitter_cb.set_row_col(rows=self.y_roi[NPOINTS], cols=self.x_roi[NPOINTS])
    #         self._emitter_sub = ew.subscribe_cb(self._emitter_cb)
    #         self._emitter_cb.new_plot_data.connect(func)
    #     else:
    #         _logger.error('Need to implem,ent this for Spectra scans')


    def make_scan_plan(self, dets, gate, bi_dir=False):
        dev_list = self.main_obj.main_obj[DEVICES].devs_as_list()
        self._bi_dir = bi_dir
        zp_def = self.get_zoneplate_info_dct()
        # md = {'entry_name': 'entry0', 'scan_type': self.scan_type,
        #                             'rois': {'X': x_roi, 'Y': y_roi},
        #                             'dwell': self.dwell,
        #                             'primary_det': DNM_DEFAULT_COUNTER,
        #                             'zp_def': zp_def,
        #                              'wdg_com':  dict_to_json(self.wdg_com)}
        md = {'metadata': dict_to_json(self.make_standard_data_metadata(entry_num=0, scan_type=self.scan_type))}
        @bpp.baseline_decorator(dev_list)
        @bpp.stage_decorator(dets)
        # @bpp.run_decorator(md={'entry_name': 'entry0', 'scan_type': scan_types.DETECTOR_IMAGE})
        def do_scan():
            # Declare the end of the run.

            x_roi = self.sp_db['X']
            y_roi = self.sp_db['Y']
            mtr_x = self.main_obj.device(DNM_DETECTOR_X)
            mtr_y = self.main_obj.device(DNM_DETECTOR_Y)
            shutter = self.main_obj.device(DNM_SHUTTER)
            #md = self.make_standard_data_metadata(entry_num=0, scan_type=self.scan_type)
            yield from bps.stage(gate)
            shutter.open()
            yield from grid_scan(dets,
                          mtr_y, y_roi[START], y_roi[STOP], y_roi[NPOINTS],
                          mtr_x, x_roi[START], x_roi[STOP], x_roi[NPOINTS],
                                 bi_dir,
                                 md=md)

            shutter.close()
            # yield from bps.wait(group='e712_wavgen')
            yield from bps.unstage(gate)
            print('DetectorScanClass: make_scan_plan Leaving')

        return (yield from do_scan())

    def init_sscans(self):

        pass
    
    def init_signals(self):
        # self.set_config_devices_func(self.on_this_dev_cfg)
        # self.set_on_counter_changed_func(self.on_x_y_counter_changed)
        # self.set_on_scan_done_func(self.on_this_scan_done)
        pass

    def on_this_scan_done(self):
        """
        on_this_scan_done(): description

        :returns: None
        """
        #stop gate and counter input tasks
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
        #use base configure x y motor scan
        # self.busy_saving = False
        self.stack = False
        # self.reload_base_scan_config()
        #sim = (self.xScan.P1.get('description').find('SIM') > -1)

        # if(not sim):
        #     MAIN_OBJ.device( 'DX_auto_disable_power' ).put(0)
        #     MAIN_OBJ.device( 'DY_auto_disable_power' ).put(0)
        #self.configure_x_y_z_scan_LINEAR(wdg_com, sp_id=sp_id, line=line, z_enabled=False)
        self.config_basic_2d(wdg_com, sp_id=sp_id,z_enabled=False)
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
        #_logger.debug('Detector: on_data_level_done:')
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
        #set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter, self.shutter)
        pass
        
        
        