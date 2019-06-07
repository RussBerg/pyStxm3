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


class clsPointTool(AnnotatedPointTool):
    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _('Select Point for Spectra Scan')
    ICON = "point_shape.png"
    SHAPE_STYLE_KEY = "shape/point"
    shapeNum = 0  # used in the TITLE that is displayed to the user
    unique_id = 0  # used as the key to a dict of shapeItems, not for display
    #SHAPE_TITLE = 'PNT %d' % shapeNum
    SHAPE_TITLE = 'PNT %d' % unique_id
    spatial_type = spatial_type_prefix.PNT

    def set_enabled(self, en):
        self.action.setEnabled(en)

    def re_init_unique_id(self):
        """
        re_init_unique_id(): description

        :returns: None
        """
        self.unique_id = get_unique_roi_id()


    def create_shape(self):
        """
        create_shape(): description

        :returns: None
        """
        shape = AnnotatedPoint(0, 0)
        self.set_shape_style(shape)
        return shape, 0, 1

    def activate(self, checked=True):
        """
        activate(): description

        :returns: None
        """
        """Activate tool"""
        # This function gets called numerous times by different objects, only
        # increment the item counter if it is called by QAction (which is only called once per
        # click of the tool
        self.manager.deselect_all_shapes()
        if(isinstance(self.sender(), QtWidgets.QAction)):
            self.shapeNum += 1
            # get a new unique ID that will be assigned to the shape
            self.re_init_unique_id()

        for baseplot, start_state in list(self.start_state.items()):
            baseplot.filter.set_state(start_state, None)

        self.action.setChecked(checked)
        self.manager.set_active_tool(self)

    def setup_shape(self, shape):
        """
        setup_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        """To be reimplemented"""
        title = 'PNT %d' % self.unique_id
        shape.setTitle(title)
        # create a new property of the shape
        shape.unique_id = self.unique_id
        shape.shapeNum = self.shapeNum
        shape._parent_tool = self

        if self.setup_shape_cb is not None:
            self.setup_shape_cb(shape)
