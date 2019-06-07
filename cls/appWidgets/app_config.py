
import sys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal

from cls.app_data.defaults import master_colors, get_style, rgb_as_hex
from cls.utils.cfgparser import ConfigClass
from cls.scanning.paramLineEdit import charLineEditParamObj

class AppConfigWidget(QtWidgets.QWidget):
    changed = pyqtSignal(float)

    def __init__(self, abs_path_to_ini_file):
        super(AppConfigWidget, self).__init__()
        self.app_def = ConfigClass(abs_path_to_ini_file + '.def')
        self.app_config = ConfigClass(abs_path_to_ini_file + '.ini')
        self.data = {}
        self.defs = {}
        self.dflt_dct = self.app_def.cfgDict['DEFAULT']
        self.sect_dct = self.app_def.config._sections
        self.tab_widget = QtWidgets.QTabWidget()
        #self.tab_widget.setTabPosition(QtWidgets.QTabWidget.West)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tab_widget)
        self.build_definition_dct(self.dflt_dct)
        for sect_k in self.sect_dct:
            self.build_definition_dct(self.sect_dct[sect_k])

        self.load_config_file()
        self.setLayout(vbox)
        ss = get_style('dark')
        self.setStyleSheet(ss)

    def gen_dflt_def_dct(self, _type):
        dct = {}
        dct['type'] = _type
        dct['vals'] = None
        return(dct)

    def str_to_int_range(self, in_str):
        l2 = in_str.replace('int_range,', '')
        l2 = l2.split(',')
        dct = self.gen_dflt_def_dct('int_range')
        dct['vals'] = [int(l2[0]), int(l2[1])]
        return(dct)

    def str_to_int(self, in_str):
        l2 = in_str.replace('int,', '')
        l2 = l2.split(',')
        dct = self.gen_dflt_def_dct('int')
        dct['vals'] = [int(l2[0])]
        return(dct)
    
    def str_to_float_range(self, in_str):
        l2 = in_str.replace('float_range,', '')
        l2 = l2.split(',')
        dct = self.gen_dflt_def_dct('float_range')
        dct['vals'] = [float(l2[0]), float(l2[1])]
        return(dct)

    def str_to_float(self, in_str):
        l2 = in_str.replace('float,', '')
        l2 = l2.split(',')
        dct = self.gen_dflt_def_dct('float')
        dct['vals'] = [float(l2[0])]
        return(dct)

    def str_to_dirpath(self, in_str):
        dct = self.gen_dflt_def_dct('dir_path')
        return(dct)

    def str_to_chars(self, in_str):
        dct = self.gen_dflt_def_dct('chars')
        return(dct)

    def str_to_char(self, in_str):
        dct = self.gen_dflt_def_dct('char')
        return(dct)

    def str_to_bool(self, in_str):
        dct = self.gen_dflt_def_dct('bool')
        dct['vals'] = [False, True]
        return(dct)

    def build_definition_dct(self, dct):
        for k in list(dct.keys()):
            def_val = dct[k]
            if (k is '__name__'):
                continue
            if(def_val.find('list,') > -1):
                self.defs[k] = self.str_to_list(def_val)
            elif(def_val.find('list,') > -1):
                self.defs[k] = self.str_to_list(def_val)
            elif (def_val.find('int_range,') > -1):
                self.defs[k] = self.str_to_int_range(def_val)
            elif (def_val.find('int,') > -1):
                self.defs[k] = self.str_to_int(def_val)
            elif (def_val.find('str,') > -1):
                #determine chars or dirpath
                if(def_val.find('dir_path') > -1):
                    self.defs[k] = self.str_to_dirpath(def_val)
                elif(def_val.find('chars') > -1):
                    self.defs[k] = self.str_to_chars(def_val)
                elif (def_val.find('char') > -1):
                    self.defs[k] = self.str_to_char(def_val)

            elif (def_val.find('bool,') > -1):
                self.defs[k] = self.str_to_bool(def_val)
            elif (def_val.find('float_range,') > -1):
                self.defs[k] = self.str_to_float_range(def_val)
            elif (def_val.find('float_range,') > -1):
                self.defs[k] = self.str_to_float(def_val)
            
            else:
                print('type unsupported')


    def str_to_list(self, in_str):
        l2 = in_str.split('list,')
        l3 = l2[1]
        l3 = l3.replace(' ', '')
        l3 = l3.replace('[', '')
        l3 = l3.replace(']', '')
        l4 = l3.split(',')
        dct = {}
        dct['type'] = 'list'
        dct['val'] = l4
        return(dct)

    def load_config_file(self):
        if(self.app_config):
            self.section_data = self.app_config.config._sections
            self.default_data = self.app_config.cfgDict
            tab = QtWidgets.QWidget()
            self.tab_widget.addTab(tab, 'DEFAULT')
            gridlayout = self.populate_tab('DEFAULT', self.default_data)
            tab.setLayout(gridlayout)
            for k in list(self.section_data.keys()):
                tab = QtWidgets.QWidget()
                self.tab_widget.addTab(tab, k)
                vbox = QtWidgets.QVBoxLayout()

                gridlayout = self.populate_tab(k, self.section_data)
                vbox.addLayout(gridlayout)
                spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                vbox.addItem(spacer)
                tab.setLayout(vbox)

    def populate_tab(self, tab_name, dct):
        gridlayout = QtWidgets.QGridLayout()
        row = 0
        rows = len(list(dct[tab_name].keys()))
        #gridlayout.setColumnStretch(rows, 2)
        for dk in list(dct[tab_name].keys()):
            if (dk is not '__name__'):
                lbl = QtWidgets.QLabel(dk)
                te = QtWidgets.QLineEdit(dct[tab_name][dk])
                te.dpo = charLineEditParamObj('%s-%s' % (tab_name, dk), parent=te)
                te.dpo.valid_returnPressed.connect(self.update_app_config)

                gridlayout.addWidget(lbl, row, 0)
                gridlayout.addWidget(te, row, 1)
                row += 1
        return(gridlayout)

    def update_app_config(self):
        sender = self.sender()
        #set_value(self, section, option, value):
        section, attr = sender.id.split('-')
        print('updating app config for section[%s] and attribute[%s] = %s' % (section, attr, sender.cur_val))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    appwidg = AppConfigWidget(r'C:\controls\git_sandbox\pyStxm\cls\applications\pyStxm\app')
    appwidg.show()
    app.exec_()

