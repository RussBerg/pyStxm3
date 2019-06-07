'''
Created on Sept 14, 2017

@author: bergr
'''
import os

from PyQt5 import QtCore, QtWidgets
from guiqwt.tools import *
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _

_dir = os.path.dirname(os.path.abspath(__file__))

class BeamSpotTool(ToggleTool):
    changed = QtCore.pyqtSignal(object)

    def __init__(self, manager, icon=None, toolbar_id=DefaultToolbarID):
        super(BeamSpotTool, self).__init__(manager, _("Show Beam Spot"), icon=os.path.join(_dir, 'beamSpot.png'), toolbar_id=toolbar_id)
        self.action.setCheckable(True)
        self.action.setChecked(False)

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def activate_command(self, plot, checked):
        """Activate tool"""
        self.changed.emit(checked)

