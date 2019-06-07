'''
Created on Aug 9, 2016

@author: bergr
'''
import os

from PyQt5 import QtCore, QtWidgets
from guiqwt.tools import *
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _

_dir = os.path.dirname(os.path.abspath(__file__))

class StxmShowSampleHolderTool(ToggleTool):
    changed = QtCore.pyqtSignal(object)

    def __init__(
            self,
            manager,
            icon=os.path.join(_dir, "sample_holder.png"),
            toolbar_id=DefaultToolbarID):
        super(
            StxmShowSampleHolderTool,
            self).__init__(
            manager,
            _("Show Sample Holder"),
            icon=icon,
            toolbar_id=toolbar_id)

        self.action.setCheckable(True)
        self.action.setChecked(False)

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def activate_command(self, plot, checked):
        """Activate tool"""
        self.changed.emit(checked)

    def deactivate(self):
        """Deactivate tool"""
        self.action.setChecked(False)

