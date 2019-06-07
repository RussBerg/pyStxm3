'''
Created on Aug 9, 2016

@author: bergr
'''

from PyQt5 import QtWidgets
#from guiqwt.config import _
from guiqwt.tools import *

from cls.plotWidgets.guiqwt_config import _
from cls.types.stxmTypes import spatial_type_prefix
from cls.utils.roi_utils import get_unique_roi_id


class clsSegmentTool(AnnotatedSegmentTool):
    TITLE = _("Select Segment for line Scan")
    ICON = "segment.png"
    SHAPE_STYLE_KEY = "shape/segment"
    shapeNum = 0  # used in the TITLE that is displayed to the user
    unique_id = 0  # used as the key to a dict of shapeItems, not for display
    #SHAPE_TITLE = 'SEG %d' % shapeNum
    SHAPE_TITLE = 'SEG %d' % unique_id
    spatial_type = spatial_type_prefix.SEG

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def re_init_unique_id(self):
        """
        re_init_unique_id(): description

        :returns: None
        """
        self.unique_id = get_unique_roi_id()

    def activate(self, checked=True):
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

        self.action.setChecked(checked)
        self.manager.set_active_tool(self)

    def create_shape(self):
        """
        create_shape(): description

        :returns: None
        """
        shape = AnnotatedSegment(0, 0, 1, 1)
        self.set_shape_style(shape)
        return shape, 0, 1

    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        """To be reimplemented"""
        shape.setTitle('SEG %d' % self.unique_id)
        # create a new property of the shape
        shape.unique_id = self.unique_id
        shape.shapeNum = self.shapeNum
        shape._parent_tool = self

        if self.setup_shape_cb is not None:
            self.setup_shape_cb(shape)
            
            