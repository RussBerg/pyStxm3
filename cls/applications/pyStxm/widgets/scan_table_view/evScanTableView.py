
from PyQt5 import QtCore, QtGui, QtWidgets
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *

from cls.applications.pyStxm.widgets.scan_table_view.evScanTableModel import EnergyScanTableModel


class EnergyScanTableView(BaseScanTableView):
    
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
        hdrList = ['ID','Start', 'End', 'Range\n(eV)', '#Points', 'Step\n(eV)', 'Dwell\n(ms)']
        #self.func_list = ['ev_id', 'center', 'range', 'step','Npoints', 'dwell', 'pol1', 'pol2', 'off1', 'off2', 'xmcd']
        super(EnergyScanTableView, self).__init__(hdrList, scanList, EnergyScanTableModel, parent)
        self.setStyleSheet(EV_SS)
        self.setObjectName('EnergyScanTableView')
        self.evNum = 0

        #self.init_model()
        #self.set_model_id_start_val(EV_CNTR)
        #self.table_view.horizontalHeader().setSectionResizeMode(QtGui.QHeaderView.ResizeToContents)
        
    
    def init_model(self):
        """
        init_model(): description

        :returns: None
        """
        self.tablemodel = EnergyScanTableModel(self.hdrList, self.scans, self)
        self.set_model_column_defaults()

    def resizeEvent(self, event):
        """ Resize all sections to content and user interactive """

        super(EnergyScanTableView, self).resizeEvent(event)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for column in range(1,header.count()):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)
            width = header.sectionSize(column)
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Interactive)
            header.resizeSection(column, width)

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
    
    
    def modify_scan(self, scan_id, newscan, do_step_npts=False):
        """
        modify_scan(): description

        :param scan_id: scan_id description
        :type scan_id: scan_id type

        :param newscan: newscan description
        :type newscan: newscan type

        :param do_step_npts=False: do_step_npts=False description
        :type do_step_npts=False: do_step_npts=False type

        :returns: None
        """
        ''' '''
        scan = self.tablemodel.get_scan(scan_id)
        if(scan is not None):
            self.tablemodel.modify_data(scan_id, newscan, do_step_npts)
            