'''
Created on Aug 9, 2016

@author: bergr
'''
import os
from PyQt5 import QtGui, QtWidgets

from guiqwt.tools import *
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _

_dir = os.path.dirname(os.path.abspath(__file__))

class clsMeasureTool(AnnotatedSegmentTool):
    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _('Measure distance between two points')
    ICON = os.path.join(_dir, "measure.png")
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
        # self.manager._select_this_item(self)
        super(clsMeasureTool, self).setup_shape(shape)

    def set_enabled(self, en):
        self.action.setEnabled(en)