
import copy
from PyQt5 import QtWidgets

from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from bcm.devices.device_names import *
from cls.utils.roi_dict_defs import *

from cls.applications.pyStxm.widgets.scan_table_view.evScanTableView import EnergyScanTableView
from cls.applications.pyStxm.widgets.scan_table_view.polaritySelWidget import PolaritySelWidget
from cls.types.stxmTypes import energy_scan_order_types
from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ
from cls.utils.roi_utils import get_base_energy_roi
from cls.utils.roi_utils import BASE_EV

NUM_DEFAULT_MULTI_EV_PNTS = 10

class EnergySelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an EnergyScanTableView
    """

    def __init__(self, pol_sel_widget=None, enable_polarity_order=False, single_pol_model=True):
        """
        __init__(): description

        :param pol_sel_widget=None: pol_sel_widget=None description
        :type pol_sel_widget=None: pol_sel_widget=None type
        
        :returns: None
        """
        super(EnergySelWidget, self).__init__()
        # BaseSelectionWidget.__init__(self)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        self.setWindowTitle("Click on column title to sort")
        self.editable = False
        self.pol_sel_widget = pol_sel_widget
        self.single_ev_model = False
        self.single_pol_model = single_pol_model
        self.single_pol_model_id = None
        # self.pol_sel_widget.changed.connect(self.on_pol_table_changed)



        self.table_view = EnergyScanTableView()
        self.table_view.scan_changed.connect(self.changed)
        self.scan_id = 0  # self.table_view.get_model_id_start_val()

        self.table_view.create_new_model()
        self.table_view.set_model_column_defaults()
        # set font
        # set column width to fit contents (set font first!)
        self.table_view.resizeColumnsToContents()
        # enable sorting
        self.table_view.setSortingEnabled(False)

        if (enable_polarity_order):
            self.scanorderComboBox = QtWidgets.QComboBox()
            self.scanorderComboBox.addItem('1. For each Energy step scan all Polarities')
            self.scanorderComboBox.addItem('2. For each Polarity step scan all Energies')
            lbl = QtWidgets.QLabel('Ev/Polarity Sequencing for scan')
            f = lbl.font()
            f.setBold(True)
            lbl.setFont(f)
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(lbl)
            h_layout.addWidget(self.scanorderComboBox)
            hspacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            h_layout.addItem(hspacer)

        # disconnect for now
        # self.scanorderComboBox.currentIndexChanged.connect(self.scan_order_changed)
        self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if (enable_polarity_order):
            layout.addLayout(h_layout)

        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.clearFocus()

        self.table_view.remove_all_models()

        self.table_view.add_region.connect(self.on_new_region)
        self.table_view.del_region.connect(self.delete_row)
        self.table_view.row_selected.connect(self.on_row_selected)



    def set_single_ev_model(self, val):
        self.single_ev_model = val

    def enable_add_region(self, do=True):
        self.enable_add_region_menu(do)
        # no guarantee that there is a polarity sel widget so check first
        if (self.pol_sel_widget):
            self.pol_sel_widget.enable_add_region_menu(do)

    def enable_add_region_menu(self, do=True):
        self.add_region_enabled = do

    def on_pol_table_changed(self):
        '''EnergySelWidget'''
        # scan = self.get_row_data_by_item_id(self.scan_id)
        # _logger.debug('EnergySelWidget: on_pol_table_changed, emitting changed sig')
        self.changed.emit()

    def modify_row_data(self, item_id, scan):
        self.table_view.modify_scan(item_id, scan)

    def get_row_idx(self, item_id):
        return (self.table_view.tablemodel.get_scan_rowidx(item_id))

    def get_row_data_by_item_id(self, item_id):
        return (self.table_view.get_scan(item_id))

    def scan_order_changed(self, idx):
        if (idx == 0):
            # 1. For each Energy step scan all Polarities'
            self.ev_polarity_scan_order = energy_scan_order_types.EV_THEN_POL
        else:
            # 2. For each Polarity step scan all Energies
            self.ev_polarity_scan_order = energy_scan_order_types.POL_THEN_EV

    def get_ev_polarity_scan_order(self):
        return (self.ev_polarity_scan_order)

    def select_row(self, row_idx):
        self.table_view.select_row(row_idx)

    def get_row_data(self, item_id):
        return (self.table_view.get_scan(item_id))

    def delete_row(self, scan_id=None):
        """
        delete_row(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :returns: None
        """
        """
        This function os called by the right click menu action for deleting a row.
        never delete the polarity model because they service all energy regions so dont delete
        the polarity regions because you want to delete 1 energy region
        """
        if (scan_id is None):
            scan = self.table_view.get_cur_selected_scan()
            if(scan is None):
                return
            scan_id = scan[SPDB_ID_VAL]

        if(isinstance(self.sender(), EnergyScanTableView) and (len(self.get_regions()) == 1)):
            #if delete was called from the energy roi's tableview and there is only 1 roi left
            # then don't delete anything
            return

        del_pol_model = False
        if (self.single_pol_model):
            # only delete pol region if we are deleting the last of the spatial regions
            if (len(self.get_regions()) == 1):
                self.pol_sel_widget.delete_model(scan[POL_ID])
                del_pol_model = True
        else:
            self.pol_sel_widget.delete_model(scan[POL_ID])

        self.on_delete_region(scan_id, del_pol_model=del_pol_model)



    def delete_model(self, ev_model_id=None):
        """
        delete_model(): description

        :param ev_model_id=None: ev_model_id=None description
        :type ev_model_id=None: ev_model_id=None type

        :returns: None
        """
        """
        This function is called by the Spatial widget delete_model().
        
        this function takes the model_id of the desired ev model_id
        that needs to be deleted. For ev models the sequence for deletion is as folows:
            - get the POL model_id used by the parent EV scan, ([POL_ID]
            - get the list of POL scans in the model
            - for every scan in the model returned from 
            - call the self.ev_sel_widget 'delete_model' with the POL model_id, ([POL_ID])
            - call 'remove_model(model_id)'
        """
        if (ev_model_id is None):
            scan = self.table_view.get_cur_selected_scan()
            ev_model_id = scan[SPDB_ID_VAL]

        ev_scans = self.table_view.get_scan_list(ev_model_id)
        # for scan in ev_scans:
        #    self.pol_sel_widget.delete_model(scan[POL_ID])
        for scan in ev_scans:
            self.on_delete_region(scan[SPDB_ID_VAL])
        self.table_view.remove_model(ev_model_id)

    def reset_single_pol_mode_id(self):
        self.single_pol_model_id = None

    def get_data(self, model_id=None):
        """
        get_data(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        ev_rois = self.table_view.get_scan_list(model_id)
        self.update_ev_pol_scan_order(ev_rois)
        return (ev_rois)

    def get_cur_model_id(self):
        """
        get_cur_model_id(): description

        :returns: None
        """
        return (self.table_view.model_id)

    def on_row_selected(self, scan):
        """
        on_row_selected(): description

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        # print '\t\tEV model_ID %d selected: POL_ID == [%d]' % (scan[SPDB_ID_VAL], scan[POL_ID])
        # _logger.debug('EnergySelWidget: on_row_selected, emitting model_change')
        self.model_change.emit(scan[SPDB_ID_VAL])
        # no guarantee that there is a polarity widget so check first
        if (self.pol_sel_widget):
            self.pol_sel_widget.switch_view_model(scan[POL_ID])
            self.pol_sel_widget.blockSignals(True)
            self.pol_sel_widget.table_view.select_row()
            self.pol_sel_widget.blockSignals(False)
            self.pol_sel_widget.update_table()

    def switch_view_model(self, model_id):
        """
        switch_view_model(): description

        :param model_id: model_id description
        :type model_id: model_id type

        :returns: None
        """
        self.table_view.switch_models(model_id)

    def clear_table(self):
        """
        clear_table(): description

        :returns: None
        """
        self.table_view.remove_all(self.scan_id)

    def set_editable(self, ed):
        """
        set_editable(): description

        :param ed: ed description
        :type ed: ed type

        :returns: None
        """
        self.table_view.set_model_editable(ed)

    def get_ev_regions(self):
        """
        get_ev_regions(): description

        :returns: None
        """
        ev_rois = self.table_view.model().get_scans()
        self.update_ev_pol_scan_order(ev_rois)
        return (ev_rois)

    def get_regions(self):
        """
        get_regions(): description

        :returns: None
        """
        rois = self.table_view.model().get_scans()
        return(rois)

    def update_ev_pol_scan_order(self, ev_rois):
        ev_order = self.get_ev_polarity_scan_order()
        for e_roi in ev_rois:
            e_roi[EV_POL_ORDER] = ev_order

    def on_new_region(self, scan=None, add_epu_roi=True):
        """
        on_new_region(): EnergySelWidget

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        # num_ev_rois = len(self.get_ev_regions())
        if (not self.add_region_enabled):
            return

        # let the polarity widget know that its iok to add new regions
        if (self.pol_sel_widget):
            self.pol_sel_widget.enable_add_region_menu(True)

        init_ev = MAIN_OBJ.device(DNM_ENERGY).get_position()
        #init_ev = BASE_EV
        # scan = get_base_energy_roi('EV', DNM_ENERGY, 370, 395, 25.0, 10, 2.5, self.pol_roi, self.off_roi, stepSize=None, enable=True)
        if (scan is None):
            # use previous scans vals for new range
            ev_order = self.get_ev_polarity_scan_order()
            cur_scan = copy.deepcopy(self.table_view.get_cur_selected_scan())
            slist = self.table_view.get_scan_list()
            if ((cur_scan is None) and (len(slist) == 0)):
                # create a default
                scan = get_base_energy_roi(EV, ENERGY, init_ev, init_ev, 0.0, 1, 1.0, None, stepSize=None,
                                           enable=True, energy_scan_order=ev_order)
            else:
                # get the last one
                if (len(slist) > 0):
                    cur_scan = slist[-1]
                #else use cur_scan
                # scan = get_base_energy_roi(EV, ENERGY, cur_scan[START], cur_scan[STOP],
                #                            cur_scan[RANGE] + EV_SCAN_EDGE_RANGE, cur_scan[NPOINTS],
                #                            cur_scan[DWELL], None, stepSize=None, enable=True,
                #                            energy_scan_order=ev_order)
                if(cur_scan[NPOINTS] == 1):
                    n_ev_pts = NUM_DEFAULT_MULTI_EV_PNTS
                else:
                    n_ev_pts = cur_scan[NPOINTS]

                scan = get_base_energy_roi(EV, ENERGY, cur_scan[START], cur_scan[STOP],
                                       cur_scan[RANGE] + EV_SCAN_EDGE_RANGE, n_ev_pts,
                                       cur_scan[DWELL], None, stepSize=None, enable=True,
                                       energy_scan_order=ev_order)

        # if(self.pol_sel_widget is not None):
        # if((add_epu_roi) and (self.pol_sel_widget is not None)):
        #     scan[POL_ID] = self.pol_sel_widget.table_view.create_new_model()
        #     #print '\t\tEV[%d] creating POL_MODEL[%d]' % (scan[SPDB_ID_VAL], scan[POL_ID])
        #     if(self.pol_sel_widget):
        #         self.pol_sel_widget.on_new_region()
        #         self.pol_sel_widget.update_table()

        ############################
        if (self.single_pol_model):
            #if (self.single_pol_model_id is None):
            if(len(self.pol_sel_widget.get_regions()) == 0):
                scan[POL_ID] = self.pol_sel_widget.table_view.create_new_model(single_model=True)
                self.single_pol_model_id = scan[POL_ID]
                self.pol_sel_widget.enable_add_region_menu(True)
                self.pol_sel_widget.on_new_region()
                self.pol_sel_widget.update_table()
            else:
                scan[POL_ID] = self.single_pol_model_id
        else:
            scan[POL_ID] = self.pol_sel_widget.table_view.create_new_model()
            self.single_pol_model_id = scan[POL_ID]
            self.pol_sel_widget.on_new_region()
            self.pol_sel_widget.update_table()
        ######################

        # self.table_view.add_scan(scan, scan[POL_ID])
        #self.scan_id += 1
        #self.scan_id = self.table_view.get_num_rows() + 1
        self.scan_id = self.table_view.get_num_rows()
        self.table_view.add_scan(scan, self.scan_id)
        new_row = self.table_view.get_num_rows()
        self.table_view.model().recalc_params(new_row - 1)

        # so that any changes will be picked up by any listening widgets
        if (self.pol_sel_widget):
            self.on_pol_table_changed()

    def load_scan(self, ev_rois=[]):
        for cur_scan in ev_rois:

            scan = get_base_energy_roi(EV, ENERGY, cur_scan[START], cur_scan[STOP],
                                       cur_scan[RANGE] + EV_SCAN_EDGE_RANGE, cur_scan[NPOINTS], cur_scan[DWELL],
                                       None, stepSize=None, enable=True)
            scan[SPDB_ID_VAL] = cur_scan[SPDB_ID_VAL]
            scan[POL_ID] = cur_scan[POL_ID]
            scan[POL_ROIS] = cur_scan[POL_ROIS]

            if (self.pol_sel_widget):
                self.pol_sel_widget.table_view.create_new_model(model_id=scan[POL_ID])
                # print '\t\tEV[%d] creating POL_MODEL[%d]' % (scan[SPDB_ID_VAL], scan[POL_ID])
                self.pol_sel_widget.load_scan(scan[POL_ROIS])
                self.pol_sel_widget.update_table()

            self.table_view.add_scan(scan, scan[SPDB_ID_VAL])
            self.single_pol_model_id = self.get_cur_model_id()

    def on_delete_region(self, scan_id=None, del_pol_model=True):
        """
        on_delete_region(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :returns: None
        """
        if (scan_id is None):
            scan = self.table_view.get_cur_selected_scan()
            scan_id = scan[SPDB_ID_VAL]
        scan = self.table_view.get_scan(scan_id)
        if (scan):
            if(del_pol_model):
                if (self.pol_sel_widget):
                    self.pol_sel_widget.delete_model(scan[POL_ID])
                    print('\tev deleting[%d]' % scan_id)
            self.table_view.remove_scan(scan_id)

    def on_single_ev(self):
        """
        on_single_ev(): description

        :returns: None
        """
        self.table_view.model().remove_all_except_first(self.scan_id)
