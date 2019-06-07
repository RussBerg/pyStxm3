
from zope.interface import Interface, Attribute, invariant

class IBaseScan(Interface):
    """@Interface for a BaseScan derived class"""

    def init_sscans(self):
        """
        This is where:
          - the sscan class's that are needed for the scan are instanciated
          - the sscan self.cmd_file is assigned
          - the positioners are assigned to the P<#> of each sscan class instance
          - the self.scanlist is created from the sscan class instances, this is used when the data is saved in save_hdr()
          - the self.mtr_list is created, this is used when a function wants to move one or more positioners and then call
            confirmed_stopped() to wait until all the motors in the list are stopped.

        here is an example from DetectorSScan.py:

        def init_sscans(self):
            self.yScan = SScanClass('%s:scan2' % self.scan_prefix, SPDB_Y, main_obj=MAIN_OBJ)
            self.xScan = SScanClass('%s:scan1' % self.scan_prefix, SPDB_X, main_obj=MAIN_OBJ)

            self.cmd_file = '%s/detector.cmd' % self.script_dir
            # self.cmd_file_pv = MAIN_OBJ.device('%s:cmd_file' % self.scan_prefix)

            xmtr = MAIN_OBJ.device(DNM_DETECTOR_X)
            ymtr = MAIN_OBJ.device(DNM_DETECTOR_Y)

            self.xScan.set_positioner(1, xmtr)
            self.yScan.set_positioner(1, ymtr)

            self.scanlist = [self.xScan, self.yScan]
            self.mtr_list = [xmtr, ymtr]

            #     def init_devices(self):
            #         self.gate = MAIN_OBJ.device(DNM_GATE)
            #         self.counter = MAIN_OBJ.device(DNM_COUNTER_APD)
            #         self.shutter = MAIN_OBJ.device(DNM_SHUTTER)

        :return:
        """

    def init_set_scan_levels(self):
        """
            This is where: the different levels of the scan are assigned, mainly TOP and DATA levels, because all
            SScanClass instances emit:
                    started = QtCore.pyqtSignal(object)
                    stopped = QtCore.pyqtSignal(object)
                    done = QtCore.pyqtSignal()
                    data_ready = QtCore.pyqtSignal()
                    status = QtCore.pyqtSignal(object) #roi object, data
                    progress = QtCore.pyqtSignal(object) #progress
                    aborted = QtCore.pyqtSignal(object) #True
                    changed = QtCore.pyqtSignal(object) #dct
                    abort_scan = QtCore.pyqtSignal()
            we can see then when any sscan is done etc, so by assigning a particular sscan as "the data level" we can
            execute saving the data when that level emits 'done' etc.

        here is an example from DetectorSScan.py:

        def init_set_scan_levels(self):
            self.set_top_level_scan(self.yScan)
            self.set_data_level_scan(self.yScan)
            self.set_btm_level_scan(self.xScan)

        """


    def init_signals(self):
        """
                    This is where:

        here is an example from DetectorSScan.py:

        def init_signals(self):
            self.set_config_devices_func(self.on_this_dev_cfg)
            self.set_on_counter_changed_func(self.on_x_y_counter_changed)
            self.set_on_scan_done_func(self.on_this_scan_done)
        """


    def configure(self, wdg_com, sp_id=0, line=True, restore=True, z_enabled=False):
        """
                    This is where:

            here is an example from DetectorSScan.py:

            def configure(self, wdg_com, sp_id=0, line=True, restore=True, z_enabled=False):
                # use base configure x y motor scan
                self.busy_saving = False
                self.stack = False
                self.reload_base_scan_config()
                sim = (self.xScan.P1.get('description').find('SIM') > -1)
                # if( not SIMULATE_IMAGE_DATA or not sim):
                if (not sim):
                    MAIN_OBJ.device(DNM_DX_AUTO_DISABLE_POWER).put(0)
                    MAIN_OBJ.device(DNM_DY_AUTO_DISABLE_POWER).put(0)
                # self.configure_x_y_z_scan(sp_db, line=line, z_enabled=False)
                # self.data_shape = ('numE', 'numY', 'numX')
                self.configure_x_y_z_scan_LINEAR(wdg_com, sp_id=sp_id, line=line, z_enabled=False)

                self.move_zpxy_to_its_center()

        """


        def on_this_data_level_done(self):
            """
                    this is an API slot that gets fired when the data level scan_done signal

            The final data dict should have the main keys of:
                all_data['SSCANS']      - all fields of each sscan record, this will be a list of sscans
                all_data['SCAN_CFG']    - all params from the GUI for this scan, center, range etc, also any flags such as XMCD=True that relate to how to execute this scan
                all_data['DATA']        - counter data collected during scan, for images this will be a 2d array, for point scans this will be a 1d array

            The goal of all_data dict is to write the dict out to disk in <data dir>/master.json. Once it has been recorded to disk the data recorder
            module can open it as a json object and export it based on the scan type so that it can pick and choose what to pull out and write to the header file.

            here is an example from DetectorSScan.py:

            def on_this_data_level_done(self):
                # _logger.debug('Detector: on_data_level_done:')
                MAIN_OBJ.device(DNM_DX_AUTO_DISABLE_POWER).put(1)  # enable again
                MAIN_OBJ.device(DNM_DY_AUTO_DISABLE_POWER).put(1)
                self.on_x_y_scan_data_level_done()

            """


        def on_this_dev_cfg(self):
            """
                this  is an API method to configure the gate, shutter and counter devices for this scan

            here is an example from DetectorSScan.py:

            def on_this_dev_cfg(self):
                set_devices_for_point_scan(self.scan_type, self.dwell, self.numE, self.numX, self.gate, self.counter,

            """

