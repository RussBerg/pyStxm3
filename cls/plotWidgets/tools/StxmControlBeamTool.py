'''
Created on Sept 18, 2017

@author: bergr
'''
import os

from PyQt5 import QtCore, QtWidgets
from guiqwt.tools import *
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _

_dir = os.path.dirname(os.path.abspath(__file__))

class StxmControlBeamTool(SelectPointTool):
    changed = QtCore.pyqtSignal(object)

    TITLE = _("Drag beam to new location")
    #ICON = "point_selection.png"
    MARKER_STYLE_SECT = "plot"
    MARKER_STYLE_KEY = "marker/curve"
    CURSOR = Qt.PointingHandCursor

    def __init__(self, manager, icon=os.path.join(_dir, 'directBeam.png'), toolbar_id=DefaultToolbarID):
        # def __init__(self, manager, mode="reuse", on_active_item=False,
        #              title=None, icon=None, tip=None, end_callback=None,
        #              toolbar_id=DefaultToolbarID, marker_style=None,
        #              switch_to_default_tool=None):

        super(StxmControlBeamTool, self).__init__(manager, tip=_("Drag beam to new location"),
                                          icon=icon,
                                          toolbar_id=toolbar_id)
        #assert icon in ("reuse", "create")
        self.action.setCheckable(True)
        self.action.setChecked(False)
        #self.SIG_TOOL_JOB_FINISHED.connect(self.on_job_finished)
        #self.SIG_VALIDATE_TOOL.connect(self.on_validate_tool)

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def activate_command(self, plot, checked):
        """Activate tool"""
        #self.changed.emit(checked)
        pass

    def activate(self):
        """Activate tool"""
        for baseplot, start_state in list(self.start_state.items()):
            baseplot.filter.set_state(start_state, None)

        self.action.setChecked(True)
        self.manager.set_active_tool(self)
        if (self.marker is not None):
            self.marker.setVisible(True)

    def deactivate(self):
        """Deactivate tool"""
        self.action.setChecked(False)
        #self.show_title.emit(False, self)
        if(self.marker is not None):
            self.marker.setVisible(False)

    def move(self, filter, event):
        if self.marker is None:
            return # something is wrong ...
        self.marker.move_local_point_to( 0, event.pos() )
        filter.plot.replot()
        self.last_pos = self.marker.xValue(), self.marker.yValue()
        self.changed.emit(self.last_pos)






