

from PyQt5 import QtGui, QtCore, uic, QtWidgets

from cls.applications.pyStxm.widgets.scan_table_view.baseScanTable import *

from cls.applications.pyStxm.widgets.scan_table_view.multiRegionWidget import MultiRegionWidget
from cls.applications.pyStxm.widgets.scan_table_view.spatialSelWidget import SpatialSelWidget
from cls.applications.pyStxm.widgets.scan_table_view.evSelWidget import EnergySelWidget
from cls.applications.pyStxm.widgets.scan_table_view.polaritySelWidget import PolaritySelWidget

from cls.scanning.plugins import plugin_dir


class A0_ConfigWidget(QtWidgets.QFrame):
    """
    A QWidget that contains an EnergyScanTableView
    """
    
    def __init__(self, spsel, evsel, polsel):
        """
        __init__(): description

        :param pol_sel_widget=None: pol_sel_widget=None description
        :type pol_sel_widget=None: pol_sel_widget=None type

        :returns: None
        """
        QtWidgets.QFrame.__init__(self)
        uic.loadUi( plugin_dir + '\\twopoint_point_spec.ui', self)
        
        self.multi = MultiRegionWidget(use_center=False, is_point=True, enable_multi_spatial=True, single_ev_model=True)
        self.multi.enable_add_spatial_region_menu(True)
        self.multi.show_load_btn()
        self.multi.show_getdata_btn()
        
        self.sp_model = self.multi.get_spatial_model()
        self.ev_model = self.multi.get_energy_model()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.multi)
        
        self.spatialGrpBox.setLayout(vbox)
    
    def on_sel_btn_clicked(self, chkd):
        btn = self.sender()
        print(btn)   
        if(chkd):
            print('btn is checked')       
        else:
            print('btn is NOT checked')
        
if __name__ == '__main__':
    import sys
    from cls.appWidgets.spyder_console import ShellWidget#, ShellDock
    
    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    
    polsel = PolaritySelWidget()
    evsel = EnergySelWidget(pol_sel_widget=polsel)
    evsel.enable_add_region(True)
    spsel = SpatialSelWidget(ev_sel_widget=evsel)
    main = A0_ConfigWidget(spsel, evsel, polsel)
    
    ns = {'evsel': evsel, 'polsel': polsel, 'main': main, 'g':globals() }
        #msg = "Try for example: widget.set_text('foobar') or win.close()"
    pythonshell = ShellWidget(parent=None, namespace=ns,commands=[], multithreaded=True)
    
    #main.layout().addWidget(pythonshell)
    
    main.show()
    
    sys.exit(app.exec_())    
    