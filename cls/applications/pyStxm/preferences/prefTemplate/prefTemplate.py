'''
Created on Dec 4, 2014

@author: bergr
'''
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5 import uic

from cls.appWidgets.basePreference import BasePreference

from cls.applications.pyStxm.main_obj_init import MAIN_OBJ, DEFAULTS
from cls.devWidgets.ophydLabelWidget import assign_aiLabelWidget
from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)


widgetsUiDir = os.path.join( os.path.dirname(os.path.abspath(__file__)))


class PreferencesParams(BasePreference):

	def __init__(self, name='PreferencesParams', parent=None):
		#QtWidgets.QDialog.__init__(self)
		super(PreferencesParams, self).__init__(name, parent)
		self._parent = parent
		uic.loadUi(	os.path.join(widgetsUiDir, 'prefTemplate.ui'), self) 

		self.evFbkLbl = assign_aiLabelWidget(self.evFbkLbl, MAIN_OBJ.device(DNM_ENERGY_RBV), hdrText='Energy', egu='eV', title_color='white', var_clr='white')
		self.flFbkLbl = assign_aiLabelWidget(self.flFbkLbl, MAIN_OBJ.device(DNM_FOCAL_LEN), hdrText='Fl', egu='um', title_color='white', var_clr='white',format='%5.2f')
		self.sampleZFbkLbl = assign_aiLabelWidget(self.sampleZFbkLbl, MAIN_OBJ.device(DNM_IDEAL_A0), hdrText='Cz', egu='um', title_color='white', var_clr='white',format='%5.2f')
		self.zpzFbkLbl = assign_aiLabelWidget(self.zpzFbkLbl, MAIN_OBJ.device('Zpz_pos'), hdrText='Zpz', egu='um', title_color='white', var_clr='white',format='%5.2f')

		self.add_section('pref_1', 0)
		self.add_section('pref_2', True)
		self.add_section('auto_save_file', True)
		self.add_section('max_points', 101)
		self.add_section('max_volts', 9.456)

		#self.init_sections()


if __name__ == "__main__":
	import sys
	
	app = QtWidgets.QApplication(sys.argv)
	window = PreferencesParams()
	window.show()
	
	app.exec_()
	