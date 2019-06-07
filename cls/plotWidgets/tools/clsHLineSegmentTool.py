'''
Created on Apr 29, 2011

@author: User
'''
import os

from PyQt5 import QtGui, QtWidgets

from PyQt5.QtCore import pyqtSignal 

from guiqwt.tools import *
#from guiqwt.config import _

from cls.plotWidgets.guiqwt_config import _
from cls.plotWidgets.tools.annotatedHorizontalSegment import AnnotatedHorizontalSegment

from cls.utils.roi_utils import get_unique_roi_id
from cls.types.stxmTypes import spatial_type_prefix

_dir = os.path.dirname(os.path.abspath(__file__))

class clsHLineSegmentTool(AnnotatedSegmentTool):
    TITLE = _("Select Horizontal Segment for Focus Scan")
    ICON = os.path.join(_dir, "horiz-segment.png")
    SHAPE_STYLE_KEY = "shape/segment"
    shapeNum = 0  # used in the TITLE that is displayed to the user
    unique_id = 0  # used as the key to a dict of shapeItems, not for display
    SHAPE_TITLE = 'SEG %d' % unique_id
    spatial_type = spatial_type_prefix.SEG

    def set_enabled(self, en):
        self.action.setEnabled(en)

    # def set_shape_style(self, shape):
    #     shape.set_style(self.shape_style_sect, self.shape_style_key)

    def re_init_unique_id(self):
        """
        re_init_unique_id(): description

        :returns: None
        """
        self.unique_id = get_unique_roi_id()

    def activate(self):
        """
        activate(): description

        :returns: None
        """
        """Activate tool"""
        # This function gets called numerous times by different objects, only
        # increment the item counter if it is called by QAction (which is only called once per
        # click of the tool
        if(isinstance(self.sender(), QtWidgets.QAction)):
            self.shapeNum += 1
            # get a new unique ID that will be assigned to the shape
            self.re_init_unique_id()

        for baseplot, start_state in list(self.start_state.items()):
            baseplot.filter.set_state(start_state, None)

        self.action.setChecked(True)
        self.manager.set_active_tool(self)

    def create_shape(self):
        """
        create_shape(): description

        :returns: None
        """
        shape = AnnotatedHorizontalSegment(0, 0, 1, 1)
        #shape = AnnotatedSegment(0, 0, 1, 1)
        self.set_shape_style(shape)
        return shape, 0, 1

    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        shape.setTitle('SEG %d' % self.unique_id)
        # create a new property of the shape
        shape.unique_id = self.unique_id
        shape.shapeNum = self.shapeNum
        shape._parent_tool = self

        if self.setup_shape_cb is not None:
            self.setup_shape_cb(shape)
            