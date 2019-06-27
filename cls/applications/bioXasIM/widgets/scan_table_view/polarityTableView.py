'''
Created on Nov 16, 2016

@author: bergr
'''
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *

from cls.applications.pyStxm.widgets.scan_table_view.polarizationTableModel import PolarizationTableModel
from cls.applications.pyStxm.widgets.scan_table_view.polarizationCmboBoxDelegate import PolComboBoxDelegate, POLARIZATION_COLUMN

class PolarityTableView(BaseScanTableView):
    
    #changed = QtCore.pyqtSignal()
    
    def __init__(self, scanList=[], parent=None):
        """
        __init__(): description

        :param scanList=[]: scanList=[] description
        :type scanList=[]: scanList=[] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type

        :returns: None
        """
        #setup the header for the top of the table
        hdrList = ['ID','Polarity', 'Offset', 'Linear Angle']
        #self.func_list = ['pol_id', 'polarity', 'offset','linearAngle']
        
        super(PolarityTableView, self).__init__(hdrList, scanList, PolarizationTableModel, parent)
        self.setStyleSheet(POL_SS)
        self.xyNum = 0
        #self.set_model_id_start_val(POL_CNTR)
        self.setItemDelegateForColumn(POLARIZATION_COLUMN, PolComboBoxDelegate(self))
        
        #turn bold off
        font = self.horizontalHeader().font()
        font.setBold(False)
        font.setPointSize(8)
        self.horizontalHeader().setFont(font)
        #self.init_model()
    
    def init_model(self):
        """
        init_model(): description

        :returns: None
        """
        self.tablemodel = PolarizationTableModel(self.hdrList, self.scans, self)
        self.set_model_column_defaults()
        
    
    def get_polarity_combobox(self):
        """
        get_polarity_combobox(): description

        :returns: None
        """
        cbox = QtWidgets.QComboBox()
        # the values that need to be pushed out for these are (in order) 
        #             [-1, 0, 1]
        cbox.addItems(['Circ Left','Circ Right','Linear'])
        return(cbox)
    
        
    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
#        for i in range(1,len(self.hdrList)):
#                self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
    def sizeHintForColumn(self, column):
        """
        sizeHintForColumn(): description

        :param column: column description
        :type column: column type

        :returns: None
        """
        fm = self.fontMetrics()
        max_width = 0
        for i in range(self.model().rowCount()):
            width = fm.width(self.model().get_cell(i,column)) + 10
            if  width > max_width:
                max_width = width
        return max_width

    def update_table(self):
        """
        update_table(): description

        :returns: None
        """
        if(self.tablemodel is not None):
            for row in range(0, self.tablemodel.rowCount()):
                #table_view.openPersistentEditor(table_model.index(row, 0))
                self.openPersistentEditor(self.tablemodel.index(row, POLARIZATION_COLUMN))
    
    def add_scan(self, scan, scan_id):
        """
        add_scan(): description

        :param scan: scan description
        :type scan: scan type

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :returns: None
        """
        """ add a scan to the current model that is owned by scan_id"""
        success = False
        if(self.switch_models(self.model_id)):
            #scan[SPDB_ID_VAL] = self.model_id_start_val + self.get_num_scans()
            scan[SPDB_ID_VAL] = scan_id
            success = self.tablemodel.add_scan(scan)
            self._cur_selected_scan = scan
            self.select_row(scan[SPDB_ID_VAL])
            self.set_model_column_defaults()
            success = True
        
        self.update_table()
            
        return(success)
