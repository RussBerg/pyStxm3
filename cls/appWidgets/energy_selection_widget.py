'''
Created on 2013-05-29

@author: bergr
'''

from PyQt5 import QtGui, QtCore
import numpy as np

from guiqwt.builder import make
from guiqwt.signals import SIG_RANGE_CHANGED

from cls.applications.pyStxm.widgets.scan_table_view.evSelWidget import EnergySelWidget

from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.roi_utils import on_start_changed, on_stop_changed

from cls.app_data.defaults import get_style

from cls.plotWidgets.curveWidget import CurveViewerWidget, get_next_color, get_basic_line_style

#try:
#    _fromUtf8 = QtCore.QString.fromUtf8
#except AttributeError:
_fromUtf8 = lambda s: s

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

class EnergySelector(CurveViewerWidget):
    new_range = QtCore.pyqtSignal(object, float, float)
    
    def __init__(self,winTitleStr = "Energy Selector", toolbar = False, show_table=False, options = {'gridparam': {'rgb_color': 'rgb( 255, 255, 255)'}}):
        super(EnergySelector, self).__init__(winTitleStr = winTitleStr, toolbar = toolbar, options = options)
        self.setMinimumSize(1300,1000)
        ss = get_style('dark')
        self.setStyleSheet(ss)
        
        self.connect(self.plot, SIG_RANGE_CHANGED, self.on_range_changed)
        #self.setPlotAxisStrs(title=None, xstr="eV", ystr=None)
        
        self.addTool('HRangeTool')
        self.model = None

        self._rng_min = 300 
        self._rng_max = 590
        
        self.create_test_plot(self._rng_min, self._rng_max)
        self.region_name = 'None'
        self.scan_id = 0
        
        self.addRngBtn = QtWidgets.QPushButton("   Add Ev Range   ")
        self.addRngBtn.clicked.connect(self.on_new_range)
        
        #self.scanEvTable = EnergyScanTableView()
        self.evSelWidget = EnergySelWidget(enable_polarity_order=False)
        self.evSelWidget.enable_add_region(True)
        #self.scanEvTable.range_changed.connect(self.on_model_changed)
        self.startEdit = QtWidgets.QLineEdit()
        self.stopEdit = QtWidgets.QLineEdit()
        self.stepsEdit = QtWidgets.QLineEdit()
        #stopEdit.textEdited.connect(self.on_stop_edited)
        self.startEdit.returnPressed.connect(self.on_start_changed)
        self.stopEdit.returnPressed.connect(self.on_stop_changed)
        self.stepsEdit.returnPressed.connect(self.on_steps_changed)
        
        self.cur_energy_id = 0
        self.cur_scan_id = 0
        
        self.tableView = QtWidgets.QTableView()
        self.tableView.setModel(self.model)
        self.tableView.setColumnWidth(0,100)
        self.tableView.setColumnWidth(1,100)
        self.tableView.setColumnWidth(2,100)
        #self.tableView.resizeColumnsToContents()
        self.tableView.setWindowTitle("my view")
        
        
        spacer = QtWidgets.QSpacerItem(5000,100,QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        #self.selPeriodicTableBtn = QtWidgets.QToolButton()

        self.startLbl = QtWidgets.QLabel('Start:')
        self.stopLbl = QtWidgets.QLabel('Stop:')
        self.stepsLbl = QtWidgets.QLabel('Steps:')
        
        self.startLbl.setBuddy(self.startEdit)
        self.stopLbl.setBuddy(self.stopEdit)
        self.stepsLbl.setBuddy(self.stepsEdit)
        
        vlayout = self.layout()
#        vlayout.setContentsMargins(QtCore.QMargins(2,2,2,2))
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.addRngBtn)
        hlayout.addItem(spacer)
        vlayout.addLayout(hlayout)
        if(show_table):
            #vlayout.addWidget(self.scanEvTable)
            vlayout.addWidget(self.evSelWidget)
            self.setMinimumSize(100,200)
            self.setMinimumHeight(200)
            self.setMaximumHeight(800)
            
            #self.scanEvTable.setMinimumHeight(400)
            self.plot.setMinimumHeight(500)
            self.evSelWidget.setMinimumHeight(200)
            self.evSelWidget.setMaximumHeight(200)
        else:
            self.setMinimumSize(100,150)
            self.setMinimumHeight(150)
            self.setMaximumHeight(150)
            hlayout2 = QtWidgets.QHBoxLayout()
            hlayout2.addWidget(self.startLbl)
            hlayout2.addWidget(self.startEdit)
            
            hlayout2.addWidget(self.stopLbl)
            hlayout2.addWidget(self.stopEdit)
            hlayout2.addItem(spacer)
            hlayout2.addWidget(self.stepsLbl)
            hlayout2.addWidget(self.stepsEdit)
            #vlayout.addLayout(hlayout1)
            vlayout.addLayout(hlayout2)
            #vlayout.addWidget(self.tableView)
    
    def on_range_changed(self, xrange_obj, xmin, xmax):
        if(xmin >= xmax):
            return
        sp_id = int(xrange_obj.title().text())
        #print 'ev id[%d], %.2f, %.2f' % (sp_id, xmin, xmax)
        e_roi = self.evSelWidget.get_row_data_by_item_id(sp_id)
        e_roi[START] = xmin
        on_start_changed(e_roi)
        e_roi[STOP] = xmax
        on_stop_changed(e_roi)
        row = self.evSelWidget.get_row_idx(sp_id)
        self.evSelWidget.select_row(row)
        self.evSelWidget.modify_row_data(sp_id, e_roi)
            
    def on_new_range(self):
        from cls.utils.roi_utils import get_base_energy_roi
        scan = get_base_energy_roi('EV', DNM_ENERGY, self._rng_min, self._rng_max, 0.0, 1, 2.5, None, stepSize=None, enable=True)
        self.add_energy(scan)
        
        rng_item = make.range(self._rng_min, self._rng_max)
        rng_item.setTitle('%d' % scan['ID_VAL'])
        
        self.plot.add_item(rng_item)
        self.cur_energy_id = scan['ID_VAL']
        self.update_curve()
        
    def on_start_changed(self):
        edt = self.sender()
        self._rng_min, ok = edt.text().toFloat()
        print('start changed to %f eV' % (self._rng_min))  
        self.modify_range(self._rng_min, self._rng_max, dosignal=False)
    
    def on_stop_changed(self):
        edt = self.sender()
        self._rng_max, ok = edt.text().toFloat()
        print('stop changed to %f eV ' % (self._rng_max))
        self.modify_range(self._rng_min, self._rng_max, dosignal=False)
        
    def on_steps_changed(self):
        edt = self.sender()
        val, ok = edt.text().toInt()
        print('steps changed to %d ' % (val))
        
    def set_region_name(self, region_name):
        self.region_name = region_name
    
    def set_cur_scan_id(self, scan_id):
        self.cur_scan_id = scan_id

    def on_model_changed(self, row, scan):
        ev_scandef = scan.get_ev_regions()[row]             
#        self._rng_min = ev_scandef.get_start()
#        self._rng_max = ev_scandef.get_stop()
#        #mofify the visual of the range for the new values
#        self.adjust_range(self._rng_min, self._rng_max)
        self.update_plot(ev_scandef)
           
    def zoom_to_range(self):
        x = np.linspace(self._rng_min-20, self._rng_max+20)
        y = np.zeros(len(x))
        self.setXYData('bckgrnd', x, y, update=False)
        self.set_autoscale()
    
    def range_changed(self, rng, _min, _max):
        print('range changed: %s: %f, %f' % (self.region_name, _min, _max))
        self._rng_min = _min
        self._rng_max = _max
        self.startEdit.setText('%.2f' % self._rng_min)
        self.stopEdit.setText('%.2f' % self._rng_max)
        #self.mapper.submit()
        self.new_range.emit(self.region_name, self._rng_min, self._rng_max)
        
    def create_test_plot(self, start, stop):
        x = np.linspace(start, stop, 1000)
        y = np.sin(np.sin(np.sin(x)))
        clr = get_next_color(use_dflt=True)
        style = get_basic_line_style(clr)
        self.create_curve('bckgrnd',x, y, curve_style=style)
    
    def create_base_line(self, start, stop):
        x = np.linspace(start, stop)
        y = np.zeros(len(x))
        clr = get_next_color(use_dflt=True)
        style = get_basic_line_style(clr)
        self.create_curve('bckgrnd',x, y, curve_style=style)
    
    def add_energy(self, scan=None):
        self.set_region_name = 'EV%d' % self.cur_energy_id
        #scan.set_scan_name(self.set_region_name)
        self.evSelWidget.on_new_region(scan=scan, add_epu_roi=False)
        #self.scanEvTable.add_scan(self.cur_energy_id, scan)
        self.update_plot(scan)
        self.cur_energy_id += 1
        
    def update_plot(self, scan=None):
        self._rng_min = scan[START]
        self._rng_max = scan[STOP]
        #mofify the visual of the range for the new values
        #self.adjust_range(self._rng_min, self._rng_max)

    

if __name__ == "__main__":

    import sys

    def on_new_range(rng, min, max):
        #print 'range = %.2f,%.2f' % (min,max)
        pass

    app = QtWidgets.QApplication(sys.argv)
    win = EnergySelector(show_table=True)
    win.new_range.connect(on_new_range)
    win.show()
    
    sys.exit(app.exec_())
    #print "all done"
        