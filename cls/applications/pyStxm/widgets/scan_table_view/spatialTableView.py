'''
Created on Nov 16, 2016

@author: bergr
'''

from cls.applications.pyStxm.widgets.scan_table_view.arbitraryLineTableModel import ArbitraryLineScanTableModel
from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *
from cls.applications.pyStxm.widgets.scan_table_view.spatialTableModel import SpatialScanTableModel
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)


class SpatialScanTableView(BaseScanTableView):
    
    def __init__(self, scanList=[], parent=None, use_center=True, is_point=False, is_arb_line=False):
        """
        __init__(): description

        :param scanList=[]: scanList=[] description
        :type scanList=[]: scanList=[] type

        :param parent=None: parent=None description
        :type parent=None: parent=None type
        
        :param use_center=True: setup table useing center/range or start/stop
        :type use_center=None: boolean
        
        :param is_point=True: setup table with read only columnds for Range, Step, Npoints
        :type is_point=None: boolean

        :returns: None
        """
        #setup the header for the top of the table
        if(use_center):
            #self.hdrList = ['ID','CenterX', 'RangeX', 'CenterY', 'RangeY', 'StepX', 'StepY', 'PointsX', 'PointsY']
            self.hdrList = ['ID', 'CntrX', 'RngX', 'CntrY', 'RngY', 'StepX', 'StepY', 'PntsX', 'PntsY']
        else:
            #self.hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']
            self.hdrList = ['ID', 'StrtX', 'StopX', 'StrtY', 'StopY', 'StepX', 'StepY', 'PntsX', 'PntsY']
            #self.func_list = ['xy_id', 'centerX', 'rangeX','centerY', 'rangeY','stepX', 'stepY', 'NpointsX', 'NpointsY']
        
        if(is_arb_line):
            super(SpatialScanTableView, self).__init__(self.hdrList, scanList, ArbitraryLineScanTableModel, parent)
        else:    
            super(SpatialScanTableView, self).__init__(self.hdrList, scanList, SpatialScanTableModel, parent)

        self.setObjectName('SpatialScanTableView')
        self.xyNum = 0
        
        self.setStyleSheet(SPATIAL_SS)
        if(is_point):
            self.set_model_column_defaults = self.set_model_column_for_points
        if(is_arb_line):
            self.set_model_column_defaults = self.set_model_column_for_arbitrarty_line
            
        self.init_model(use_center, is_arb_line)
        
        #self.set_model_id_start_val(SPATIAL_CNTR)
    
    def init_model(self, use_center=True, is_arb_line=False):
        """
        init_model(): description

        :returns: None
        """
        if(is_arb_line):
            self.tablemodel = ArbitraryLineScanTableModel(self.hdrList, self.scans, self, use_center=use_center)
        else:    
            self.tablemodel = SpatialScanTableModel(self.hdrList, self.scans, self, use_center=use_center)
        self.set_model_column_defaults()
    
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
    
    def set_max_spatial_val(self, column_name, _max):
        '''
        this function sets the ceiling_val in the model for the specified column so that
        the user cannot enter a value that the user woants deemed "OUT of RANGE"
        '''
        col = self.tablemodel.get_column_with_name(column_name)
        if(col):
            self.tablemodel.column_map[col]['ceiling_val'] = _max
        else:
            _logger.info('%s does not exist in tablemodel.column_map' % column_name)
    
    def set_min_spatial_val(self, column_name, _min):
        '''
        this function sets the ceiling_val in the model for the specified column so that
        the user cannot enter a value that the user woants deemed "OUT of RANGE"
        '''
        col = self.tablemodel.get_column_with_name(column_name)
        if(col):
            self.tablemodel.column_map[col]['floor_val'] = _min
        else:
            _logger.info('%s does not exist in tablemodel.column_map' % column_name)
    
    def set_x_spatial_range(self, _max):
        self.set_max_spatial_val('RANGEX', _max)
        
    def set_y_spatial_range(self, _max):    
        self.set_max_spatial_val('RANGEY', _max)
        
    def set_x_spatial_startstop(self, strt_stop):    
        self.set_min_spatial_val('STARTX', strt_stop[0])    
        self.set_max_spatial_val('STARTX', strt_stop[1])
        self.set_min_spatial_val('STOPX', strt_stop[0])    
        self.set_max_spatial_val('STOPX', strt_stop[1])
        
    def set_y_spatial_startstop(self, strt_stop):    
        self.set_min_spatial_val('STARTY', strt_stop[0])    
        self.set_max_spatial_val('STARTY', strt_stop[1])
        self.set_min_spatial_val('STOPY', strt_stop[0])    
        self.set_max_spatial_val('STOPY', strt_stop[1])    
        
    def set_model_column_defaults(self):
        """
        set_model_column_defaults(): description

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        #for i in range(1,len(self.hdrList)):
        #    self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

    def resizeEvent(self, event):
        """ Resize all sections to content and user interactive """

        super(SpatialScanTableView, self).resizeEvent(event)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for column in range(1,header.count()):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)
            width = header.sectionSize(column)
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Interactive)
            header.resizeSection(column, width)

    def set_model_column_for_points(self):
        """
        set_model_column_defaults(): set columns of table to be read only for Range, Step, Npoints 
                     0       1       2        3         4        5        6         7          8
        hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        self.tablemodel.set_col_readonly(2)
        self.tablemodel.set_col_readonly(4)
        self.tablemodel.set_col_readonly(5)
        self.tablemodel.set_col_readonly(6)
        self.tablemodel.set_col_readonly(7)
        self.tablemodel.set_col_readonly(8)
        
        #for i in range(1,len(self.hdrList)):
        #    #self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        #    self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

    
    
    def set_model_column_for_arbitrarty_line(self):
        """
        set_model_column_defaults(): set columns of table to be read only for StepY, NpointsY 
                     0       1       2        3         4        5        6         7          8
        hdrList = ['ID','StartX', 'StopX', 'StartY', 'StopY', 'StepX', 'StepY', 'PointsX', 'PointsY']

        :returns: None
        """
        self.tablemodel.set_col_readonly(0)
        self.tablemodel.set_col_readonly(6)
        self.tablemodel.set_col_readonly(8)
        
        #for i in range(1,len(self.hdrList)):
        #    self.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
    
        
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
    

    





        
if __name__ == '__main__':
    import sys
    from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
    
    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    #win = EnergySelWidget()
    #win.show()
    #spatial = SpatialSelWidget()
    #spatial.show()
    
    multi = MultiRegionWidget(use_center=True, enable_multi_spatial=True)
    multi.enable_add_spatial_region_menu(True)
    multi.show_load_btn()
    multi.show_getdata_btn()
    
    ns = {'main': multi, 'g':globals() }
        #msg = "Try for example: widget.set_text('foobar') or win.close()"
    pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
    multi.layout().addWidget(pythonshell)
    
    multi.show()
    
    sys.exit(app.exec_())    
    
    
    
