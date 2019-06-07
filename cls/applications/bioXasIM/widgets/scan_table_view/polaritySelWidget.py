'''
Created on Nov 16, 2016

@author: bergr
'''
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *

from cls.applications.pyStxm.widgets.scan_table_view.polarityTableView import PolarityTableView

class PolaritySelWidget(BaseSelectionWidget):
    """
    A QWidget that contains an PolarityTableView
    """
    def __init__(self,*args):
        """
        __init__(): description

        :param *args: *args description
        :type *args: *args type

        :returns: None
        """
        BaseSelectionWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 870, 450)
        self.setWindowTitle("Click on column title to sort")
        self.editable = False
        rois = [get_epu_pol_dct(0, 0.0, angle=0.0)]
        
        
        self.scan_id = 0
        self.table_view = PolarityTableView()
        #self.scan_id = self.table_view.get_model_id_start_val()
        self.table_view.resizeColumnsToContents()
        self.table_view.setSortingEnabled(False)
        self.table_view.create_new_model()
        self.table_view.set_model_column_defaults()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.clearFocus()
        
        self.table_view.add_region.connect(self.on_new_region)
        self.table_view.del_region.connect(self.on_delete_region)
        self.table_view.row_selected.connect(self.on_row_selected)
        
        self.table_view.scan_changed.connect(self.changed)
        
        #self.table_view.model().scan_changed.connect(self.on_pol_scan_changed)
    def enable_add_region_menu(self, do=True):
        self.add_region_enabled = do
        
    def select_row(self, row_idx):
        self.table_view.select_row(row_idx)
    
    def get_row_data(self, item_id):
        return(self.table_view.get_scan(item_id))
                
    def delete_model(self, pol_model_id=None):
        """
        delete_model(): description

        :param pol_model_id=None: pol_model_id=None description
        :type pol_model_id=None: pol_model_id=None type

        :returns: None
        """
        """
        This function is called by the EV widget delete_model() as well as delete_row(), depends on
        why and how the row waws to be deleted.
        
        this function takes the model_id of the desired POL model_id
        that needs to be deleted. For POL models the sequence for deletion is as folows:
            - get the list of scans in the model with the same id as pol_model_id 
            - delete every scan in the list 
            - call 'remove_model(model_id)'
        """
        if(pol_model_id is None):
            scan = self.table_view.get_cur_selected_scan()
            pol_model_id = scan[SPDB_ID_VAL]
            
        pol_scans = self.table_view.get_scan_list(pol_model_id)
        for pol in pol_scans:
            self.on_delete_region(pol[SPDB_ID_VAL])
        self.table_view.remove_model(pol_model_id)
        
    def get_data(self, model_id=None):
        """
        get_data(): description

        :param model_id=None: model_id=None description
        :type model_id=None: model_id=None type

        :returns: None
        """
        return(self.table_view.get_scan_list(model_id))
    
    def update_table(self):
        """
        update_table(): description

        :returns: None
        """
        self.table_view.update_table()
    
    def get_cur_model_id(self):
        """
        get_cur_model_id(): description

        :returns: None
        """
        return(self.table_view.model_id)
        
    def on_row_selected(self, scan):
        """
        on_row_selected(): description

        :param scan: scan description
        :type scan: scan type

        :returns: None
        """
        #print '\t\t\t\tPOLARITY model_ID %d selected' % (scan[SPDB_ID_VAL])
        #self.table_view.dump_model_keys()
        #_logger.debug('PolaritySelWidget: on_row_selected, emitting model_change')
        self.model_change.emit(scan[SPDB_ID_VAL])
        
        
    
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
    
    def get_regions(self):
        """
        get_regions(): description

        :returns: None
        """
        rois = self.table_view.model().get_scans() 
        return(rois)
    
    def on_new_region(self, scan=None):
        """
        on_new_region(): on new Polarity region

        :param scan=None: scan=None description
        :type scan=None: scan=None type

        :returns: None
        """
        if(not self.add_region_enabled):
            return
        
        if(scan is None):
            #use previous scans vals for new range
            cur_scan = copy.deepcopy(self.table_view.get_cur_selected_scan())
            slist = self.table_view.get_scan_list()
            if((cur_scan is None) and (len(slist) == 0)):
                #create a default
                scan = get_epu_pol_dct(0, 0.0, angle=0.0)
            else:    
                #get the last one
                if(len(slist) > 0):
                    cur_scan = slist[-1]
                #else use cur_scan
                scan = get_epu_pol_dct(cur_scan['POL'], cur_scan['OFF'], angle=cur_scan['ANGLE'])
                
        self.scan_id += 1
        self.table_view.add_scan(scan, self.scan_id)
        
        #so that any changes will be picked up by any listening widgets
        self.changed.emit()
            
    def load_scan(self, pol_rois=[]):
        for cur_scan in pol_rois:
            scan = get_epu_pol_dct(cur_scan['POL'], cur_scan['OFF'], angle=cur_scan['ANGLE'])
            
            self.on_new_region(scan)
    
    def on_delete_region(self, scan_id=None):
        """
        on_delete_region(): description

        :param scan_id=None: scan_id=None description
        :type scan_id=None: scan_id=None type

        :returns: None
        """
        if(scan_id is None):
            scan = self.table_view.get_cur_selected_scan()
            scan_id = scan[SPDB_ID_VAL]
            
        print('\t\tpol deleting[%d]' % scan_id)
        self.table_view.remove_scan(scan_id)
    
    def on_single_region(self):
        """
        on_single_region(): description

        :returns: None
        """
        self.table_view.model().remove_all_except_first(self.scan_id)

