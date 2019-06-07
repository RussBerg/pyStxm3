'''
Created on Oct 6, 2016

@author: bergr
'''
import os

from PyQt5 import QtGui, QtWidgets

from guiqwt.tools import *
#from guiqwt.config import _

from cls.plotWidgets.guiqwt_config import _
from . import clsHLineSegmentTool
_dir = os.path.dirname(os.path.abspath(__file__))

class clsHorizMeasureTool(clsHLineSegmentTool):
    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _('Measure distance between two points')
    ICON = os.path.join(_dir, "horizmeasure.png")
    SHAPE_STYLE_KEY = "shape/segment"
    
    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        plot = self.manager.get_plot() 
        plot.unselect_all()
        plot.set_active_item(shape)
        shape._parent_tool = self
        
        if self.setup_shape_cb is not None:
            self.setup_shape_cb(shape)
    
    def set_enabled(self, en):
        self.action.setEnabled(en)
        
        