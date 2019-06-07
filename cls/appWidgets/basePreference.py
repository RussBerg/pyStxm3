

import os
from PyQt5 import QtCore, QtGui, QtWidgets
from cls.applications.pyStxm.bl10ID01 import DEFAULTS
from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_put, dct_get

_logger = get_module_logger(__name__)

class BasePreference(QtWidgets.QWidget):
    '''
    A base preference class that contains common required preference attributes
    '''
    changed = QtCore.pyqtSignal(object)
    sections = []

    def __init__(self, name, parent=None):
        super(BasePreference, self).__init__(parent)
        self.name = name
        self.pref_dct = self.init_changed_dct()
        self.sections = {}
        #self.init_pref_section()

        # if(not self.prefs_exist()):
        #     self.create_pref_sections_in_default_mod()

    # def init_pref_section(self):
    #     '''
    #     make sure that this prefernce has an entry if it doesnt exist
    #     :return:
    #     '''
    #     DEFAULTS.update()
    #     section = 'PREFS.%s' % self.name.upper()
    #
    #     _sctn = DEFAULTS.get(section, create=False)
    #     if(_sctn is not None):
    #         # reload preference values
    #         print 'should reload the prefs here'
    #     else:
    #        DEFAULTS.set(self.sections[section] =  True



    def get_pref_sections(self):
        '''
        check the DEFAULT module (on disk) to see if the desired preferences exist if so return them all
        :return:
        '''
        DEFAULTS.update()
        section = 'PREFS.%s' % self.name.upper()
        if (section in list(self.sections.keys())):
            return(DEFAULTS.get(section))


    def add_section(self, section, val=None):
        full_section_name = 'PREFS.%s.%s' % (self.name.upper(), section.upper())
        if (not DEFAULTS.section_exists(full_section_name)):
            #self.sections['PREFS.%s.%s' % (self.name.upper(), section.upper())] =  val
            dct_put(self.sections, full_section_name, val)
            DEFAULTS.set(full_section_name, val)
            DEFAULTS.update()

    def get_section(self, section):
        val = None
        full_section_name = 'PREFS.%s.%s' % (self.name.upper(), section.upper())
        if(DEFAULTS.section_exists(full_section_name)):
            val = DEFAULTS.get(full_section_name)
        else:
            _logger.error('section does not exist [%s]' % section)
        return(val)

    def set_section(self, section, val):
        full_section_name = 'PREFS.%s.%s' % (self.name.upper(), section.upper())
        if (DEFAULTS.section_exists(full_section_name)):
            val = DEFAULTS.set(full_section_name, val)
        else:
            _logger.error('section does not exist [%s]' % full_section_name)


    def init_changed_dct(self):
        dct = {}
        dct['pref_name'] = self.name
        dct['preferences'] = {}
        return(dct)

    def do_pref_changed(self):
        '''
        call for pref widget to update the dct and then emit it
        :return:
        '''
        self.update_pref_dct()
        self.changed.emit(self.pref_dct)

    def update_pref_dct(self):
        '''
        When called, compile all preferences for the pref widget into the self.pef_dct and return it
        to be mplemented by inheriting class
        :return: updated self.pref_dct
        '''
        pass

    def load_defaults(self):
        '''
        this function should read the particular section from the DEFAULTS module and reload the settings
        that have been saved.
        to be implemented by inheriting class,
        :return:
        '''
        pass

    def create_pref_sections_in_default_mod(self):
        '''
        if the sections for this particular preference do not already exist in the defaults module then create them.
        to be implemented by the inheriting class
        :return:
        '''
        for l in self.sections:
            DEFAULTS.add_section(l)

