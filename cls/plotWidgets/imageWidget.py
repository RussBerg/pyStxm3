'''
Created on Nov 22, 2016

@author: bergr
'''
# -*- coding:utf-8 -*-
"""
Created on 2011-03-03

@author: bergr
"""
import sys
import os
import timeit
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QPointF, QRectF
from PyQt5 import uic
import qwt as Qwt

import scipy.ndimage
#import copy

import numpy as np


#from guiqwt.builder import make
from guiqwt.plot import ImageDialog
from guiqwt.tools import *
from guiqwt.styles import AnnotationParam, ImageParam, ImageAxesParam, GridParam, CurveParam #, ItemParameters
from guiqwt.cross_section import XCrossSectionItem, YCrossSectionItem
 
#from guiqwt.config import _
from cls.plotWidgets.guiqwt_config import _
from guiqwt.label import LabelItem
from guiqwt.image import ImageItem
from guiqwt.builder import PlotItemBuilder


from guiqwt.interfaces import (
    ICSImageItemType,
    IPanel,
    IBasePlotItem,
    ICurveItemType,
    IShapeItemType,
    IDecoratorItemType)

# from cls.plotWidgets.guiqwt_qt5_sigs import (
#     SIG_MARKER_CHANGED,
#     SIG_PLOT_LABELS_CHANGED,
#     SIG_AXES_CHANGED,
#     SIG_ANNOTATION_CHANGED,
#     SIG_AXIS_DIRECTION_CHANGED,
#     SIG_VOI_CHANGED,
#     SIG_ITEMS_CHANGED,
#     SIG_ACTIVE_ITEM_CHANGED,
#     SIG_ITEM_MOVED,
#     SIG_LUT_CHANGED,
#     SIG_ITEM_SELECTION_CHANGED,
#     SIG_STOP_MOVING,
#     SIG_PLOT_AXIS_CHANGED)


#from guidata.dataset.datatypes import DataSet
from guidata.dataset.dataitems import StringItem
from guidata.dataset.qtwidgets import DataSetShowGroupBox
from guidata.utils import update_dataset

from cls.plotWidgets.tools.annotatedHorizontalSegment import AnnotatedHorizontalSegment

from cls.plotWidgets.stxm_osa_dflt_settings import make_dflt_stxm_osa_smplholder_settings_dct
from cls.utils.nextFactor import nextFactor
from cls.utils.angles import calcRectPoints
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.log import get_module_logger
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.json_utils import file_to_json
from cls.utils.cfgparser import ConfigClass
from cls.utils.time_utils import datetime_string_to_seconds

from cls.app_data.defaults import rgb_as_hex, master_colors, get_style
from cls.appWidgets.dialogs import excepthook, errorMessage
from cls.plotWidgets import tools
from cls.plotWidgets.shape_restrictions import ROILimitObj, ROILimitDef, ROI_STATE_ALARM
from cls.utils.roi_utils import get_first_sp_db_from_wdg_com, make_spatial_db_dict, widget_com_cmnd_types, get_unique_roi_id, \
    is_unique_roi_id_in_list, get_current_unique_id, set_current_unique_id, delete_unique_id
from cls.utils.roi_dict_defs import *
from cls.plotWidgets.color_def import get_normal_clr, get_alarm_clr, get_warn_clr, get_normal_fill_pattern, get_warn_fill_pattern, \
    get_alarm_fill_pattern
from cls.plotWidgets.shapes.pattern_gen import add_pattern_to_plot

import cls.types.stxmTypes as types

from cls.utils.save_settings import SaveSettings
from cls.utils.json_threadsave import mime_to_dct

from cls.data_io.stxm_data_io import STXMDataIo
from cls.scanning.dataRecorder import DataIo
from cls.plotWidgets.CLSPlotItemBuilder import clsPlotItemBuilder

from cls.utils.threaded_image_loader import ThreadpoolImageLoader

from cls.plotWidgets.shapes.utils import create_rect_centerd_at, create_rectangle, create_simple_circle


#plotDir = os.path.dirname(os.path.abspath(__file__)) + '/'
plotDir = os.path.dirname(os.path.abspath(__file__))
# define a list of VALID tools for a particular plotting type, used to
# only allow access to certain tools for cerrtain scans
PNT_tools = ['AnnotatedPointTool', 'clsPointTool']
SEG_tools = [
    'SegmentTool',
    'clsHLineSegmentTool',
    'AnnotatedSegmentTool',
    'clsSegmentTool']
ROI_tools = [
    'RectangleTool',
    'AnnotatedRectangleTool',
    'clsAverageCrossSectionTool']
CIR_tools = [
    'CircleTool',
    'EllipseTool',
    'AnnotatedCircleTool',
    'AnnotatedEllipseTool']


MAIN_TOOLS_STR = ['SelectPointTool',
    'SelectTool',
    'RectZoomTool',
    'BasePlotMenuTool',
    'ExportItemDataTool',
    'EditItemDataTool',
    'ItemCenterTool',
    'DeleteItemTool',
    'DummySeparatorTool',
    'BasePlotMenuTool',
    'DisplayCoordsTool',
    'ItemListPanelTool',
    'DummySeparatorTool',
    'ColormapTool',
    'ReverseYAxisTool',
    'AspectRatioTool',
    'ContrastPanelTool',
    'SnapshotTool',
    'ImageStatsTool',
    'XCSPanelTool',
    'YCSPanelTool',
    'CrossSectionTool',
    'AverageCrossSectionTool',
    'SaveAsTool',
    'CopyToClipboardTool',
    'PrintTool',
    'HelpTool',
    'AboutTool' ]



OSA_CRYO = 'OSA_CRYO'
OSA_AMBIENT = 'OSA_AMBIENT'
SAMPLE_GONI = 'SAMPLE_GONI'
SAMPLE_STANDARD = 'SAMPLE_STANDARD'
FILTER_STRING = "*.hdf5;*.png;*.jpg"

MAX_IMAGE_Z = 1000
# setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)

make = clsPlotItemBuilder()

class ImageParam(DataSet):
    title = StringItem(_("Title"))
    scan_time = StringItem("Scan Time")
    scan_type = StringItem("Scan Type")
    npoints = StringItem("Number of Points")

    #npoints = IntItem(_("NPoints"), default=0., unit="points", help=_("Number of Points (pts)"))
    #height = IntItem(_("Height"), default=0., unit="points", help=_("Image height (pts)"))
    #center = FloatItem(_("Center"), default=0., unit="um", help=_("Image center (um)"))
    #range = FloatItem(_("Range"), default=00., unit="um", help=_("Image range (um)"))

    energy = StringItem("Energy")
    center = StringItem("Center")
    rng = StringItem("Range")
    dwell = StringItem("Dwell")
    # current = FloatItem("Current", default=10., min=1, max=30, unit="mA",
    #               help="Threshold current")
    # floatarray = FloatArrayItem("Float array", default=np.ones( (50,5), float),
    #                            format=" %.2e ").set_pos(col=1)

def dumpObj(obj):
    """
    dumpObj(): description
    :param dumpObj(obj: dumpObj(obj description
    :type dumpObj(obj: dumpObj(obj type
    :returns: None
    """
    print('dumpObj: ')
    print(obj)
    for i in list(obj.__dict__.keys()):
        print("%s : %s" % (i, obj.__dict__[i]))


def dump_key_pressed(dct):
    for k in list(dct.keys()):
        if(k is Qt.Key_C):
            print('Key Qt.Key_C is ' , dct[k])
        if (k is Qt.Key_X):
            print('Key Qt.Key_X is ', dct[k])
        if (k is Qt.Key_Y):
            print('Key Qt.Key_Y is ', dct[k])
        if (k is Qt.Key_M):
            print('Key Qt.Key_M is ', dct[k])
        if (k is Qt.Key_Alt):
            print('Key Qt.Key_Alt is ', dct[k])


class InputState(object):

    def __init__(self):
        """
        __init__(): description

        :returns: None
        """

        self.keyisPressed = {}
        self.keyisPressed[Qt.Key_X] = False
        self.keyisPressed[Qt.Key_Y] = False
        # 'S'cribble, for controlling motors
        self.keyisPressed[Qt.Key_M] = False
        #self.keyisPressed[Qt.Key_Space] = False
        self.keyisPressed[Qt.Key_Alt] = False
        #self.keyisPressed[Qt.Key_F1] = False  # for emitting a new_roi_center
        self.keyisPressed[Qt.Key_C] = False  # for emitting a new_roi_center
        self.keyisPressed[Qt.Key_Control] = False

        self.btnisPressed = {}
        self.btnisPressed[Qt.LeftButton] = False
        self.btnisPressed[Qt.MiddleButton] = False
        self.btnisPressed[Qt.RightButton] = False

        # represents the delta values
        self.center = (0.0, 0.0)
        self.range = (0.0, 0.0)
        self.npts = (0, 0)
        self.rect = (0, 0, 0, 0)
        self.shape_outof_range = False
        self.force_out_of_range = False

        # the id of the currently selected plotItem
        self.plotitem_id = None  # a unique ID number
        self.plotitem_title = None  # the title ex: SEG 2
        self.plotitem_shape = None  # the current shape item
        # the type of the plot item, one of the types.spatial_type_prefix types (PNT,
        # SEG, ROI)
        self.plotitem_type = None

    def reset(self):
        self.keyisPressed = {}
        self.keyisPressed[Qt.Key_X] = False
        self.keyisPressed[Qt.Key_Y] = False
        self.keyisPressed[Qt.Key_M] = False  # for controlling motors
        #self.keyisPressed[Qt.Key_Space] = False
        self.keyisPressed[Qt.Key_Alt] = False
        self.keyisPressed[Qt.Key_C] = False
        self.keyisPressed[Qt.Key_Control] = False

        self.btnisPressed = {}
        self.btnisPressed[Qt.LeftButton] = False
        self.btnisPressed[Qt.MiddleButton] = False
        self.btnisPressed[Qt.RightButton] = False

        # represents the delta values
        self.center = (0.0, 0.0)
        self.range = (0.0, 0.0)
        self.npts = (0, 0)
        self.rect = (0, 0, 0, 0)

        # the id of the currently selected plotItem
        self.plotitem_id = None  # a unique ID number
        self.plotitem_title = None  # the title ex: SEG 2
        self.plotitem_shape = None  # the current shape item
        # the type of the plot item, one of the types.spatial_type_prefix types (PNT,
        # SEG, ROI)
        self.plotitem_type = None

class ImageWidget(ImageDialog):

    new_region = pyqtSignal(object)
    region_changed = pyqtSignal(object)
    region_deleted = pyqtSignal(object)
    region_selected = pyqtSignal(object)
    new_ellipse = pyqtSignal(object)
    target_moved = pyqtSignal(object)
    shape_moved = pyqtSignal(object)
    new_roi_center = pyqtSignal(object)
    scan_loaded = pyqtSignal(object)
    dropped = QtCore.pyqtSignal(QtCore.QMimeData)
    new_beam_position = QtCore.pyqtSignal(float, float)

    def __init__(
            self,
            parent,
            filtStr=FILTER_STRING,
            testing=False,
            type='basic',
            sample_pos_mode=None,
            options=None,
            settings_fname='settings.json'):
        """
        __init__(): description

        :param parent: parent description
        :type parent: parent type

        :param filtStr="*.hdf5": filtStr="*.hdf5" description
        :type filtStr="*.hdf5": filtStr="*.hdf5" type

        :param testing=False: testing=False description
        :type testing=False: testing=False type

        :param type='basic': type='basic' description
        :type type='basic': type='basic' type

        :param options=None: options=None description
        :type options=None: options=None type

        :returns: None
        background="#555555"
        background="#3e3e3e"
        """
        self.gridparam = make.gridparam(background="#3e3e3e",
                                  minor_enabled=(False, False),
                                  major_enabled=(False, False))
        #these variables are needed because they are used in function calls made by the ImageDialog constructor
        self.fileFilterStr = filtStr
        self.type = type
        self._data_dir = ""
        self.data_io = None
        self._auto_contrast = True
        self.data = None
        self.image_type = None  # used to identify what type of image is currently being displayed
        self.dataHeight = 0
        self.dataWidth = 0
        self.wPtr = 0
        self.hPtr = 0
        self.xstep = 1.0
        self.ystep = 1.0
        # scalars for non-square data
        self.htSc = 1
        self.widthSc = 1
        self.item = None
        self.dataAtMax = False
        self.image_is_new = True
        self.checkRegionEnabled = True
        self.multi_region_enabled = True
        self.show_image_params = False
        self.drop_enabled = True

        self.progbar = None

        self._cur_shape_uid = -1

        # a dict to keep track of the priority of images that are added and their relationship to which images are closure
        # to the surface and which are lower
        self.add_images_z_depth_dct = {}
        self.roiNum = 0
        self.segNum = 0
        self.shapeNum = 0
        self.pntNum = 0

        self.max_shape_size = (None, None)

        # transform factors for pixel to unit conversion
        self.xTransform = 0.0
        self.yTransform = 0.0
        self.zTransform = 0.0
        self.unitTransform = 'um'

        self.show_beam_spot = False
        self.prev_beam_pos = (0.0, 0.0)

        if (options is None):
            options = dict(
                show_xsection=True,
                show_ysection=True,
                xlabel=("um", ""),
                ylabel=("um", ""),
                zlabel=None,
                show_contrast=True,
                xsection_pos="top",
                ysection_pos="right",
                lock_aspect_ratio=True,
                gridparam=self.gridparam,
                colormap="gist_gray")


        self.sel_item_id = None

        # ImageDialog.__init__(
        #     self,
        #     parent=parent,
        #     wintitle="",
        #     edit=False,
        #     toolbar=True,
        #     options=options)


        if (self.type == 'analyze'):
            self.register_tools = self.register_analyze_tools
        elif (self.type == 'select'):
            self.register_tools = self.register_select_tools
        elif (self.type == 'calib_camera'):
            self.register_tools = self.register_camera_tools
        else:
            self.register_tools = self.register_basic_tools

        super(ImageWidget, self).__init__(wintitle="",
                                            toolbar=True, edit=False,
                                            options=options)

        self.settings_fname = os.path.join(plotDir, settings_fname)
        if(not os.path.exists(self.settings_fname)):
            osa_smplhldr_dct = make_dflt_stxm_osa_smplholder_settings_dct(self.settings_fname)

        else:
            osa_smplhldr_dct = file_to_json(self.settings_fname)

        self.ss = SaveSettings(self.settings_fname, dct_template=osa_smplhldr_dct)

        self.osa_type = OSA_AMBIENT
        self.sample_hldr_type = SAMPLE_GONI

        #init this first because the constructor for ImageDialog will call our
        #over ridden 'register_tools' function which needs this param

        self.layout().setContentsMargins(2,2,2,2)
        self.layout().setSpacing(2)

        self.setMinimumSize(400, 300)
        self.checkRegionEnabled = True
        #
        # # setup some default values
        self.max_roi = 100000
        self.max_seg_len = 1000
        self.max_shape_size = (5000, 5000)
        #
        self.roi_limit_def = None
        self.seg_limit_def = None
        self.pnt_limit_def = None
        #
        self.zoom_scale = 1.0
        self.zoom_rngx = 1.0
        self.zoom_rngy = 1.00
        #
        #
        # create an instance of InputState so that I can
        # connect key presses with mouse events
        self.inputState = InputState()
        #
        self.filtVal = 0
        self.plot = self.get_plot()
        pcan = self.plot.canvas()
        pcan.setObjectName('plotBgrnd')
        #
        xcs = self.get_xcs_panel()
        xcs.set_options(autoscale=True)
        xcs.cs_plot.toggle_perimage_mode(True)
        xcan = xcs.cs_plot.canvas()
        xcan.setObjectName('xCrossSection')

        #xcsplot = xcs.get_plot()
        #xcsplot.setObjectName('xCrossSection')

        ycs = self.get_ycs_panel()
        ycs.set_options(autoscale=True)
        ycs.cs_plot.toggle_perimage_mode(True)
        ycan = ycs.cs_plot.canvas()
        ycan.setObjectName('yCrossSection')
        #ycsplot = xcs.get_plot()
        #ycsplot.setObjectName('yCrossSection')


        #
        #self.plot.plotLayout().setContentsMargins(0,0)
        self.plot.plotLayout().setCanvasMargin(0)
        self.plot.plotLayout().setAlignCanvasToScales(True)
        #
        # set legend
        self.legend = Qwt.QwtLegend()
        self.legend.setDefaultItemMode(Qwt.QwtLegendData.Checkable)
        #self.plot.insertLegend(self.legend, Qwt.QwtPlot.RightLegend)
        self.plot.insertLegend(self.legend, Qwt.QwtPlot.BottomLegend)

        self.plot.SIG_ITEM_SELECTION_CHANGED.connect(self.selected_item_changed)
        self.plot.SIG_ITEMS_CHANGED.connect(self.items_changed)
        self.plot.SIG_ITEM_MOVED.connect(self.active_item_moved)
        self.plot.SIG_ANNOTATION_CHANGED.connect(self.annotation_item_changed)
        self.plot.SIG_MARKER_CHANGED.connect(self.marker_changed)
        #self.plot.SIG_TOOL_JOB_FINISHED.connect(self.shape_end_rect)
        self.plot.SIG_ACTIVE_ITEM_CHANGED.connect(self.on_active_item_changed)
        self.plot.SIG_PLOT_AXIS_CHANGED.connect(self.on_sig_plot_axis_changed)
        self.plot.SIG_AXES_CHANGED.connect(self.on_sig_axes_changed)
        #
        self.dropped.connect(self.updateFormatsTable)
        # force the plot axis to make vertical 0 at the bottom instead of the
        # default of top
        self.plot.set_axis_direction('left', False)
        #
        # force the plot to snap to fit the current plot in
        self.set_autoscale()
        self.plot.unselect_all()
        #
        if(testing):
            self.tstTimer = QTimer()
            self.tstTimer.timeout.connect(self.tstDataPoint)
            self.tstTimer.start(10)
        else:
            self.tstTimer = None

        self.set_grid_colors()

        self.set_center_at_0(2000, 2000)
        #
        self.param_gbox = None
        #
        self.setAcceptDrops(True)
        #
        self.init_param_cross_marker()

        self._shape_registry = {}

    #def register_shape_info(self, shape_info_dct={'shape_title': None, 'on_selected': None}):
    def register_shape_info(self, shape_info_dct={}):
        self._shape_registry[shape_info_dct['shape_title']] = shape_info_dct

    def get_shape_titles_from_registry(self):
        return(self._shape_registry.keys())


    def get_shape_from_registry(self, shape_title):
        if (shape_title in self._shape_registry.keys()):
            return(self._shape_registry[shape_title])


    def set_grid_colors(self):
        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

        # self.set_grid_parameters("#323232", "#343442", "#545454")
        # self.set_grid_parameters("#7d7d7d", "#343442", "#545454")
        self.set_grid_parameters(bg_clr, min_clr, maj_clr)
        self.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)

    def update_style(self):
        ss = get_style('dark')
        self.setStyleSheet(ss)
        self.set_grid_colors()

    def set_dataIO(self, data_io_cls):
        self.data_io = data_io_cls

    def init_param_cross_marker(self):
        '''create a marker used for adjusting the center of a scan based on pressing
         Ctrl-C and moving the mouse around on the screen over an image, this will
        cause the image plot to emit the center_changed signal
        '''
        self.param_cross_marker = Marker()
        section = "plot"
        self.param_cross_marker.set_style(section, "marker/parmcross")
        self.param_cross_marker.setVisible(False)
        self.param_cross_marker.attach(self.plot)

    def update_contrast(self):
        if(self.item is not None):
            self._select_this_item(self.item, False)

    def set_enable_drop_events(self, en):
        self.drop_enabled = en

    def dragEnterEvent(self, event):
        if(self.drop_enabled):
            event.acceptProposedAction()
            self.dropped.emit(event.mimeData())

    def dragMoveEvent(self, event):
        if(self.drop_enabled):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if(self.drop_enabled):
            #import simplejson as json
            mimeData = event.mimeData()
            if mimeData.hasImage():
                # self.setPixmap(QtGui.QPixmap(mimeData.imageData()))
                #print 'dropEvent: mime data has an IMAGE'
                pass
            elif mimeData.hasHtml():
                # self.setText(mimeData.html())
                # self.setTextFormat(QtCore.Qt.RichText)
                #print 'dropEvent: mime data has HTML'
                pass
            elif mimeData.hasText():
                # self.setText(mimeData.text())
                # self.setTextFormat(QtCore.Qt.PlainText)
                # print 'dropEvent: mime data has an TEXT = \n[%s]' %
                # mimeData.text()
                dct = mime_to_dct(mimeData)
                #print 'dropped file is : %s' % dct['file']
                self.blockSignals(True)
                self.openfile([dct['file']], addimages=True, dropped=True)
                self.blockSignals(False)
            elif mimeData.hasUrls():
                #self.setText("\n{"energy": 1078.7, "xpositioner": "GoniX", "file": "S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0516\\C190516001.hdf5", "estop": 1078.7, "estart": 1078.7, "angle": 0.0, "ypositioner": "GoniY", "polarization": "CircLeft", "start": [356.531656880734, -102.98874617737003], "dwell": 1.0, "stop": [406.531656880734, -52.98874617737003], "scan_type": "sample_image Line_Unidir", "step": [0.33557046979865773, 0.33557046979865773], "goni_theta_cntr": 0.0, "offset": 0.0, "date": "2019-05-16", "center": [374.1234, -72.66], "scan_type_num": 6, "range": [50.0, 50.0], "end_time": "09:10:55", "npoints": [150, 150], "scan_panel_idx": 5, "goni_z_cntr": 200.00643000000002}".join([url.path() for url in mimeData.urls()])){"polarity": "CircLeft", "angle": 0.0, "center": [-419.172, 5624.301], "energy": 1029.0, "step": [110.86591666666668, 114.90791666666667], "scan_type": "coarse_image_scan Line_Unidir", "range": [2660.782, 2757.79], "file": "S:\\STXM-data\\Cryo-STXM\\2017\\guest\\1207\\C171207014.hdf5", "offset": 0.0, "npoints": [25, 25], "dwell": 30.408937142857148, "scan_panel_idx": 8}
                #print 'dropEvent: mime data has URLs'
                pass
            else:
                #self.setText("Cannot display data")
                #print 'dropEvent: mime data Cannot display data'
                pass

            # self.setBackgroundRole(QtGui.QPalette.Dark)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        if(self.drop_enabled):
            event.accept()

    def updateFormatsTable(self, mimeData=None):
        # self.formatsTable.setRowCount(0)
        if(self.drop_enabled):
            if mimeData is None:
                return

            for format in mimeData.formats():
                formatItem = QtWidgets.QTableWidgetItem(format)
                formatItem.setFlags(QtCore.Qt.ItemIsEnabled)
                formatItem.setTextAlignment(
                    QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

                if format == 'text/plain':
                    text = mimeData.text()  # .strip()
                elif format == 'text/html':
                    text = mimeData.html()  # .strip()
                elif format == 'text/uri-list':
                    text = " ".join([url.toString()
                                     for url in mimeData.urls()])
                else:
                    #text = " ".join(["%02X" % ord(datum)
                    #                 for datum in mimeData.data(format)])
                    text = " ".join(["%02X" % ord(datum) for datum in str(mimeData.data(format), encoding='cp1252')])

                #row = self.formatsTable.rowCount()
                # self.formatsTable.insertRow(row)
                #self.formatsTable.setItem(row, 0, QtWidgets.QTableWidgetItem(format))
                #self.formatsTable.setItem(row, 1, QtWidgets.QTableWidgetItem(text))
                # print text

            # self.formatsTable.resizeColumnToContents(0)


    def on_sig_axes_changed(self, obj):
        """
        on_sig_axes_changed(): description
{"file": "S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0613\\C190613003.hdf5", "scan_type_num": 10, "scan_type": "coarse_goni_scan Point_by_Point", "scan_panel_idx": 4, "energy": 815.4, "estart": 815.4, "estop": 815.4, "e_npnts": 1, "polarization": "CircLeft", "offset": 0.0, "angle": 0.0, "dwell": 1.0, "npoints": [5, 5], "date": "2019-06-13", "end_time": "09:48:44", "center": [800.0, 64.0], "range": [50.0, 50.0], "step": [10.0, 10.0], "start": [775.0, 39.0], "stop": [825.0, 89.0], "xpositioner": "GoniX", "ypositioner": "GoniY"}
        :param obj: obj description
        :type obj: obj type

        :returns: None
        """
        #print 'on_sig_axes_changed'
        #print obj
        pass

    def enable_image_param_display(self, val):
        self.show_image_params = val
        if(self.show_image_params):
            self.param_gbox = DataSetShowGroupBox(
                _("Image parameters"), ImageParam)
            self.plot_layout.addWidget(self.param_gbox)
        # else:
        #    self.plot_layout.addWidget(self.param_gbox)

    ############## INTERFACE ROUTINES ####################
    # def load_file_data(self, data):
        """
        load_file_data(): description

        :param data: data description
        :type data: data type

        :returns: None
        """
    #    """ set the plotting data to data """
    #    pass

    # def add_data(self, data):
        """
        add_data(): description

        :param data: data description
        :type data: data type

        :returns: None
        """
    #    """ append data to the current plotting data """
    #    pass

    def update(self):
        """
        update(): description

        :returns: None
        """
        """ force and update to the plot """
        pass

    def get_selected_data(self, rangeX, rangeY):
        """
        get_selected_data(): description

        :param rangeX: rangeX description
        :type rangeX: rangeX type

        :param rangeY: rangeY description
        :type rangeY: rangeY type

        :returns: None
        """
        """ return the selected data as a numpy array """
        pass

    def get_data(self, flip=False):
        """
        get_data(): description

        :returns: None
        """
        """ return all of the plotting data as a numpy array"""
        if(flip):
            return(np.flipud(self.data))
        else:
            return(self.data)

    ############## End of INTERFACE ROUTINES ####################
    def register_tools(self):
        """
        register_tools(): description

        :returns: None
        """
        self.register_basic_tools()

    def on_select_tool_changed(self, filter, event):
        """
        on_select_tool_changed(): This handler fires when the user has held Ctrl-C down and
        moved the mouse overtop the plot window, the purpose of this is to emit the center_changed signal
        which can then be used by listeners to automatically modify the center of a scan parameter.

        The signal that this slot services is emitted by the tools.clsSelectTool

        :param filter: filter description
        :type filter: filter type

        :param event: event description
        :type event: event type

        :returns: None
        """

        if(event is None):
            self.param_cross_marker.setVisible(False)
            self.plot.replot()

        elif event.modifiers() & Qt.ControlModifier or self.plot.canvas_pointer:
            pos = event.pos()
            self.plot.set_marker_axes()
            self.param_cross_marker.setZ(self.plot.get_max_z() + 1)
            self.param_cross_marker.setVisible(True)
            self.param_cross_marker.move_local_point_to(0, pos)
            self.plot.replot()

            c = QPointF(pos.x(), pos.y())
            #x, y = self.plot.cross_marker.canvas_to_axes(c)
            x, y = self.plot.canvas2plotitem(self.param_cross_marker, pos.x(), pos.y())
            #print 'canvas_to_axes: x=%.1f y=%.1f' % (x, y)

            self.inputState.center = (x, y)
            self.inputState.range = (0, 0)
            self.inputState.npts = (None, None)
            self.inputState.rect = (x, y, 0, 0)
            self.inputState.plotitem_type = None
            #sept 18 2017
            self.inputState.plotitem_id = get_current_unique_id()
            self.inputState.plotitem_shape = self.param_cross_marker
            #print 'on_select_tool_changed: emitting_new_roi'
            self._emit_new_roi(self.image_type)

            #print 'x=%.1f y=%.1f' % (pos.x(), pos.y())
            #x, y = self.plot.cross_marker.axes_to_canvas(pos.x(), pos.y())


            # self.marker_changed(self.param_cross_marker)

        else:
            vis_parmcross = self.param_cross_marker.isVisible()
            self.param_cross_marker.setVisible(False)

            if vis_parmcross:
                self.plot.replot()

    def register_select_tools(self):
        """
        register_select_tools(): description

        :returns: None
        """
        self.opentool = self.add_tool(
            tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        self.opentool.openfile.connect(self.openfile)

        #self.selectTool = self.add_tool(SelectTool)
        self.selectTool = self.add_tool(tools.clsSelectTool)
        self.selectTool.changed.connect(self.on_select_tool_changed)

        self.add_tool(BasePlotMenuTool, "item")
        self.add_tool(ColormapTool)
        self.add_separator_tool()
        self.add_tool(PrintTool)
        self.add_tool(DisplayCoordsTool)

        self.plot = self.get_plot()
        clr_ac = self.get_clear_images_action()

        # clr_ac.setChecked(self._auto_contrast)
        add_actions(self.plot.manager.toolbar, [clr_ac])

        self.add_separator_tool()
        self.addTool('tools.clsSquareAspectRatioTool')
        self.add_separator_tool()

        self.add_tool(ReverseYAxisTool)

        # rt = StxmRectangleTool
        # rt.TITLE = _("2D Region")
        # rt.create_shape = self._create_rect_shape
        # at = self.add_tool(
        #     rt,
        #     setup_shape_cb=self._setup_rect_shape,
        #     handle_final_shape_cb=self._handle_final_rect_shape)

#        ast = tools.clsMeasureTool
#        #ast.create_shape = self._create_seg_shape
#        aa = self.add_tool(
#            ast,
#            setup_shape_cb=self._setupsegment,
#            handle_final_shape_cb=self._handle_final_segment_shape)
#        aa.TITLE = _("%s %d" % (types.spatial_type_prefix.SEG, self.segNum))

        #apt = AnnotatedPointTool
        apt = tools.clsPointTool
        apt.create_shape = self._create_point_shape
        ap = self.add_tool(
            apt,
            setup_shape_cb=self.setuppoint,
            handle_final_shape_cb=self._handle_final_point_shape)
        #ap.TITLE = _("selecting")



        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def register_analyze_tools(self):
        """
        register_analyze_tools(): description

        :returns: None
        """
        #opentool = self.add_tool(OpenFileTool, "*.json;*.hdr;*.tif;*.jpg")
        #opentool = self.add_tool(OpenFileTool, self.fileFilterStr)
        self.opentool = self.add_tool(
            tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        self.opentool.openfile.connect(self.openfile)
        self.add_tool(ReverseYAxisTool)
        self.add_tool(SaveAsTool)

        self.add_separator_tool()

        self.addTool('tools.clsSquareAspectRatioTool')

        self.add_separator_tool()

        #self.selectTool = self.add_tool(SelectTool)
        self.selectTool = self.add_tool(tools.clsSelectTool)
        self.selectTool.changed.connect(self.on_select_tool_changed)
        self.add_tool(BasePlotMenuTool, "item")
        self.add_tool(ColormapTool)
        # self.add_tool(XCSPanelTool)
        self.add_tool(YCSPanelTool)
        self.add_tool(SnapshotTool)
        self.add_tool(RectZoomTool)

        self.add_separator_tool()

        self.add_tool(PrintTool)
        self.add_tool(DisplayCoordsTool)

        self.plot = self.get_plot()
        clr_ac = self.get_clear_images_action()
        # clr_ac.setChecked(self._auto_contrast)
        add_actions(self.plot.manager.toolbar, [clr_ac])
        self.add_separator_tool()

        art = tools.clsAverageCrossSectionTool
        #art.TITLE = _("Select ROI")
        art.create_shape = self._create_rect_shape
        at = self.add_tool(
            art,
            setup_shape_cb=self._setup_rect_shape,
            handle_final_shape_cb=self._handle_final_rect_shape)

        self.addTool('tools.clsSegmentTool')
        self.addTool('tools.clsHLineSegmentTool')

        apt = tools.clsPointTool
        #apt.create_shape = self._create_point_shape
        ap = self.add_tool(
            apt,
            setup_shape_cb=self.setuppoint,
            handle_final_shape_cb=self._handle_final_point_shape)
        #ap.TITLE = _("selecting")

        self.add_separator_tool()

        meas = self.add_tool(tools.clsMeasureTool)
        # add an auto contrast tool button, remove the default toolbuttons, all
        # except set to full range based on data
        cpnl = self.get_contrast_panel()
        cpnl_actions = cpnl.toolbar.actions()
        cpnl.toolbar.removeAction(cpnl_actions[1])
        cpnl.toolbar.removeAction(cpnl_actions[2])
        cpnl.toolbar.removeAction(cpnl_actions[3])
        con_ac = cpnl.manager.create_action(
            'Auto Contrast',
            toggled=self.set_auto_contrast,
            icon=get_icon('csapplylut.png'),
            tip=_("Enable Auto Contrast "))
        con_ac.setChecked(self._auto_contrast)
        add_actions(cpnl.toolbar, [con_ac])

        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def register_osa_and_samplehldr_tool(self, sample_pos_mode=types.sample_positioning_modes.COARSE):
        """
        register_osa_and_samplehldr_tool(): register the osa and sample holder tools

        :returns: None
        """
        sht = self.add_tool(tools.StxmShowSampleHolderTool)
        osat = self.add_tool(tools.StxmShowOSATool)

        if(sample_pos_mode == types.sample_positioning_modes.GONIOMETER):
            osat.changed.connect(self.create_uhv_osa)
            self.osa_type = OSA_CRYO
            sht.changed.connect(self.create_goni_sample_holder)
            self.sample_hldr_type = SAMPLE_GONI

        else:
            self.osa_type = OSA_AMBIENT
            osat.changed.connect(self.create_osa)
            sht.changed.connect(self.create_stdrd_sample_holder)
            self.sample_hldr_type = SAMPLE_STANDARD

    def register_samplehldr_tool(self, sample_pos_mode=types.sample_positioning_modes.COARSE):
        """
        register_osa_and_samplehldr_tool(): register the osa and sample holder tools

        :returns: None
        """
        sht = self.add_tool(tools.StxmShowSampleHolderTool)

        if(sample_pos_mode == types.sample_positioning_modes.GONIOMETER):
            sht.changed.connect(self.create_goni_sample_holder)
            self.sample_hldr_type = SAMPLE_GONI

        else:
            sht.changed.connect(self.create_stdrd_sample_holder)
            self.sample_hldr_type = SAMPLE_STANDARD

    def register_osa_tool(self, sample_pos_mode=types.sample_positioning_modes.COARSE):
        """
        register_osa_and_samplehldr_tool(): register the osa and sample holder tools

        :returns: None
        """
        osat = self.add_tool(tools.StxmShowOSATool)

        if (sample_pos_mode == types.sample_positioning_modes.GONIOMETER):
            osat.changed.connect(self.create_uhv_osa)
            self.osa_type = OSA_CRYO

        else:
            self.osa_type = OSA_AMBIENT
            osat.changed.connect(self.create_osa)

    def register_basic_tools(self):
        """
        register_basic_tools(): description

        :returns: None
        """
        # self.plot = self.get_plot()
        # self.plot.manager.toolbar.hide()
        # toolbar = QtWidgets.QToolBar(_("Tools"))
        # self.plot.manager.add_toolbar("Basic", toolbar)
        # toolbar.show()


        self.opentool = self.add_tool(
            tools.clsOpenFileTool, formats=self.fileFilterStr)
        self.opentool.set_directory(self._data_dir)
        self.opentool.openfile.connect(self.openfile)

        #self.selectTool = self.add_tool(SelectTool)
        self.selectTool = self.add_tool(tools.clsSelectTool)
        self.selectTool.changed.connect(self.on_select_tool_changed)
        self.add_tool(BasePlotMenuTool, "item")
        self.add_tool(ColormapTool)
        self.add_tool(SnapshotTool)
        self.add_separator_tool()

        self.add_tool(PrintTool)
        self.addTool('tools.clsSquareAspectRatioTool')

        # add an auto contrast tool button, remove the default toolbuttons, all
        # except set to full range based on data
        cpnl = self.get_contrast_panel()
        cpnl_actions = cpnl.toolbar.actions()
        for i in range(1,len(cpnl_actions)):
            cpnl.toolbar.removeAction(cpnl_actions[i])
        #cpnl.toolbar.removeAction(cpnl_actions[2])
        #cpnl.toolbar.removeAction(cpnl_actions[3])
        con_ac = cpnl.manager.create_action(
            'Auto Contrast',
            toggled=self.set_auto_contrast,
            icon=get_icon('csapplylut.png'),
            tip=_("Enable Auto Contrast "))
        con_ac.setChecked(self._auto_contrast)
        add_actions(cpnl.toolbar, [con_ac])

        self.add_separator_tool()
        self.plot = self.get_plot()
        clr_ac = self.get_clear_images_action()
        #clr_ac.setChecked(self._auto_contrast)
        add_actions(self.plot.manager.toolbar, [clr_ac])

        self.add_separator_tool()
        bs_tool = self.add_tool(tools.BeamSpotTool, self.get_plot())
        bs_tool.changed.connect(self.enable_beam_spot)
        self.add_separator_tool()

        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def enable_menu_action(self, ac_name, val):
        assert type(ac_name) is str, "enable_menu_action: ac_name is not a string: %r" % ac_name
        assert type(val) is bool, "enable_menu_action: val is not a boolean:"
        tb = self.plot.manager.get_toolbar()
        actions = tb.actions()
        for ac in actions:
            #print 'enable_menu_action: checking [%s]' % ac.text()
            if(ac.text().find(ac_name) > -1):
                ac.setEnabled(val)
                break

    def get_clear_images_action(self):
        clr_ac = self.plot.manager.create_action(
            'Clear Plot',
            toggled=self.delImagePlotItems,
            icon=get_icon('trash.png'),
            tip=_("Clear Images from plot "))
        clr_ac.setCheckable(False)
        #connect it to the triggered signal otherwise it wont fire with checkable set to False which fires 'toggled'
        clr_ac.triggered.connect(self.delImagePlotItems)

        return(clr_ac)

    def register_camera_tools(self):
        """
        register_camera_tools(): description

        :returns: None
        """
                #self.selectTool = self.add_tool(SelectTool)
        self.selectTool = self.add_tool(tools.clsSelectTool)
        self.selectTool.changed.connect(self.on_select_tool_changed)
        self.add_tool(BasePlotMenuTool, "item")
        self.add_tool(ColormapTool)
        self.add_tool(SnapshotTool)

        self.add_separator_tool()

        self.add_tool(PrintTool)

        self.addTool('tools.clsHorizMeasureTool')
        self.add_separator_tool()
        self.plot = self.get_plot()
        clr_ac = self.get_clear_images_action()

        # clr_ac.setChecked(self._auto_contrast)
        add_actions(self.plot.manager.toolbar, [clr_ac])

        self.set_default_tool(self.selectTool)
        self.get_default_tool().activate()

    def enable_beam_spot(self, chkd):
        if(chkd):
            self.show_beam_spot = True
        else:
            self.show_beam_spot = False
            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)
            for shape in shapes:
                if(hasattr(shape, 'shapeparam')):
                    s = shape.shapeparam
                    title = s._title
                    if (title.find('beam_spot') > -1):
                        self.delPlotItem(shape)
            self.blockSignals(False)
            self.plot.replot()


    def get_sample_positioning_mode(self):
        return(self.sample_pos_mode)

    def set_sample_positioning_mode(self, mode):
        self.sample_pos_mode = mode

    def set_auto_contrast(self, auto):
        """
        set_auto_contrast(): description

        :param auto: auto description
        :type auto: auto type

        :returns: None
        """
        self._auto_contrast = auto
#         if(auto):
#             self.create_sample_holder()
#
#         else:
#             self.delShapePlotItems()

    def addTool(self, toolstr):
        """
        addTool(): description

        :param toolstr: toolstr description
        :type toolstr: toolstr type

        :returns: None
        """
        """ a function that allows inheriting widgets to add tools
        where tool is a valid guiqwt tool """

        if(toolstr == 'LabelTool'):
            self.add_tool(LabelTool)
        elif (toolstr == 'DummySeparatorTool'):
            self.add_tool(DummySeparatorTool)
        elif(toolstr == 'SegmentTool'):
            self.add_tool(SegmentTool)
        elif(toolstr == 'RectangleTool'):
            self.add_tool(RectangleTool)
        elif(toolstr == 'CircleTool'):
            self.add_tool(CircleTool)
        elif(toolstr == 'EllipseTool'):
            self.add_tool(EllipseTool)
        elif(toolstr == 'MultiLineTool'):
            self.add_tool(MultiLineTool)
        elif(toolstr == 'tools.clsMultiLineTool'):
            self.add_tool(tools.clsMultiLineTool)
        elif(toolstr == 'FreeFormTool'):
            self.add_tool(FreeFormTool)
        elif(toolstr == 'PlaceAxesTool'):
            self.add_tool(PlaceAxesTool)
        elif(toolstr == 'HRangeTool'):
            self.add_tool(HRangeTool)
        elif(toolstr == 'AnnotatedRectangleTool'):
            self.add_tool(AnnotatedRectangleTool)
        elif(toolstr == 'AnnotatedCircleTool'):
            self.add_tool(AnnotatedCircleTool)
        elif(toolstr == 'AnnotatedEllipseTool'):
            self.add_tool(AnnotatedEllipseTool)
        elif(toolstr == 'AnnotatedSegmentTool'):
            self.add_tool(AnnotatedSegmentTool)
        elif(toolstr == 'AnnotatedPointTool'):
            self.add_tool(AnnotatedPointTool)
        elif(toolstr == 'AspectRatioTool'):
            self.add_tool(AspectRatioTool)
        elif(toolstr == 'ReverseYAxisTool'):
            self.add_tool(ReverseYAxisTool)
        elif(toolstr == 'tools.clsMeasureTool'):
            self.add_tool(tools.clsMeasureTool)
        elif(toolstr == 'ItemCenterTool'):
            self.add_tool(ItemCenterTool)
        elif(toolstr == 'HelpTool'):
            self.add_tool(HelpTool)
        elif (toolstr == 'SelectPointTool'):
            self.add_tool(SelectPointTool)
        elif (toolstr == 'tools.StxmControlBeamTool'):
            #self.add_tool(tools.StxmControlBeamTool)
            sdbt = self.add_tool(tools.StxmControlBeamTool)
            sdbt.changed.connect(self.on_new_direct_beam_pos)
            #sdbt.show_title.connect(self.on_new_direct_beam_pos_title)
        elif (toolstr == 'tools.BeamSpotTool'):
            bs_tool = self.add_tool(tools.BeamSpotTool, self.get_plot())
            bs_tool.changed.connect(self.enable_beam_spot)

        elif(toolstr == 'tools.clsHLineSegmentTool'):
            # self.add_tool(tools.HLineSegmentTool)
            #aa = self.add_tool(tools.HLineSegmentTool, setup_shape_cb=self._setupsegment, handle_final_shape_cb=self._handle_final_segment_shape)
            hls = self.add_tool(
                tools.clsHLineSegmentTool,
                handle_final_shape_cb=self._handle_final_horiz_segment_shape)
            hls.TITLE = _("%s %d" % (types.spatial_type_prefix.SEG, self.segNum))

        elif(toolstr == 'tools.clsHorizMeasureTool'):
            shmt = tools.clsHorizMeasureTool
            a_shmt = self.add_tool(shmt)

        elif(toolstr == 'tools.clsSegmentTool'):
            # self.add_tool(tools.HLineSegmentTool)
            #aa = self.add_tool(tools.HLineSegmentTool, setup_shape_cb=self._setupsegment, handle_final_shape_cb=self._handle_final_segment_shape)
            hls = self.add_tool(
                tools.clsSegmentTool,
                handle_final_shape_cb=self._handle_final_horiz_segment_shape)
            hls.TITLE = _("%s %d" % (types.spatial_type_prefix.SEG, self.segNum))

        elif(toolstr == 'tools.clsSquareAspectRatioTool'):
            #at = self.add_tool(tools.SquareAspectRatioTool, self.get_plot())
            # at.changed.connect(self.on_set_aspect_ratio)
            sqrAsptool = self.add_tool(tools.clsSquareAspectRatioTool, self.get_plot())
            # at.changed.connect(self.on_set_aspect_ratio)
            sqrAsptool.changed.connect(self.on_set_aspect_ratio)
        elif(toolstr == 'tools.clsAverageCrossSectionTool'):
            art = tools.clsAverageCrossSectionTool
            #art.TITLE = _("selecting")
            art.create_shape = self._create_rect_shape
            at = self.add_tool(
                art,
                setup_shape_cb=self._setup_rect_shape,
                handle_final_shape_cb=self._handle_final_rect_shape)

        elif(toolstr == 'tools.StxmShowSampleHolderTool'):
            sht = self.add_tool(tools.StxmShowSampleHolderTool)
            if (sample_pos_mode == types.sample_positioning_modes.GONIOMETER):
                sht.changed.connect(self.create_goni_sample_holder)
                self.sample_hldr_type = SAMPLE_GONI
            else:
                sht.changed.connect(self.create_stdrd_sample_holder)
                self.sample_hldr_type = SAMPLE_STANDARD


        elif (toolstr == 'tools.StxmShowOSATool'):
            osat = self.add_tool(tools.StxmShowOSATool)
            if (sample_pos_mode == types.sample_positioning_modes.GONIOMETER):
                osat.changed.connect(self.create_uhv_osa)
                self.osa_type = OSA_CRYO

            else:
                self.osa_type = OSA_AMBIENT
                osat.changed.connect(self.create_osa)


    # def enable_tools_by_spatial_type(self, tp=types.spatial_type_prefix.ROI):
    def enable_tools_by_spatial_type(self, tp=None):
        """
        a function that enables or disables tools on teh toolbar depending on the spatial type

        enable_tools_by_spatial_type(): description

        :param tp: types.spatial_type_prefix. type flag
        :type tp: types.spatial_type_prefix.ROI or types.spatial_type_prefix.SEG, or types.spatial_type_prefix.PNT

        :returns: None
        """
        """  """
        en_list = []
        dis_list = []
        if(tp is None):
            # disable all
            en_list = []
            dis_list = PNT_tools + SEG_tools + ROI_tools

        elif(tp == types.spatial_type_prefix.PNT):
            # enable PNT tools and disable SEG, ROI
            en_list = PNT_tools
            dis_list = SEG_tools + ROI_tools
        elif(tp == types.spatial_type_prefix.SEG):
            # enable SEG tools and disable PNT, ROI
            en_list = SEG_tools
            dis_list = PNT_tools + ROI_tools
        elif(tp == types.spatial_type_prefix.ROI):
            # enable ROI tools and disable PNT, SEG
            #but if we are in single spatial mode then only enable ROI if there are no current ROI's
            if(self.multi_region_enabled):
                en_list = ROI_tools
            else:
                current_shape_items = self.plot.get_items(item_type=IShapeItemType)
                if(len(current_shape_items) is 0):
                    en_list = ROI_tools
                #else leave en_list blank
            dis_list = PNT_tools + SEG_tools

        for t_str in en_list:
            self.enable_tool(t_str, True)

        for t_str in dis_list:
            self.enable_tool(t_str, False)

    def enable_tools_by_shape_type(self, shape_type=None, val=True):
        """
        a function that enables or disables tools on teh toolbar depending on the shape type

        enable_tools_by_shape_type(): description

        :param tp: shape. type flag
        :type tp: shape, guiqwt shapeItem

        :returns: None
        """
        """  """
        en_list = []
        dis_list = []
        if(shape_type is None):
            # disable all
            en_list = []
            dis_list = PNT_tools + SEG_tools + ROI_tools

        elif(shape_type == AnnotatedPoint):
            # enable PNT tools and disable SEG, ROI
            en_list = PNT_tools
            dis_list = SEG_tools + ROI_tools
        elif((shape_type == AnnotatedSegment) or (shape_type == AnnotatedHorizontalSegment)):
            # enable SEG tools and disable PNT, ROI
            en_list = SEG_tools
            dis_list = PNT_tools + ROI_tools
        elif(shape_type == AnnotatedRectangle):
            # enable ROI tools and disable PNT, SEG
            en_list = ROI_tools
            dis_list = PNT_tools + SEG_tools

        if(not val):
            # then add the normally enabled list to the dislist and empty the
            # en list
            dis_list = en_list
            en_list = []

        for t_str in en_list:
            self.enable_tool(t_str, True)

        for t_str in dis_list:
            self.enable_tool(t_str, False)

    def enable_tools_by_shape_instance(self, shape_inst=None, val=True):
        """
        a function that enables or disables tools on teh toolbar depending on the shape type

        enable_tools_by_shape_type(): description

        :param shape_inst_type: an instance of a shape type
        :type shape_inst_type: shape, guiqwt shapeItem

        :returns: None
        """
        """  """
        en_list = []
        dis_list = []
        if(shape_inst is None):
            # disable all
            en_list = []
            dis_list = PNT_tools + SEG_tools + ROI_tools

        elif(isinstance(shape_inst, AnnotatedPoint)):
            # enable PNT tools and disable SEG, ROI
            en_list = PNT_tools
            dis_list = SEG_tools + ROI_tools
        elif((isinstance(shape_inst, AnnotatedSegment)) or (isinstance(shape_inst, AnnotatedHorizontalSegment))):
            # enable SEG tools and disable PNT, ROI
            en_list = SEG_tools
            dis_list = PNT_tools + ROI_tools
        elif(isinstance(shape_inst, AnnotatedRectangle)):
            # enable ROI tools and disable PNT, SEG
            en_list = ROI_tools
            dis_list = PNT_tools + SEG_tools

        if(not val):
            # then add the normally enabled list to the dislist and empty the
            # en list
            dis_list = en_list
            en_list = []

        for t_str in en_list:
            self.enable_tool(t_str, True)

        for t_str in dis_list:
            self.enable_tool(t_str, False)

    def enable_tool_by_name(self, toolstr=None, val=True):
        """
        a function that enables or disables a tool on the toolbar

        enable_tool_by_name(): description

        :param toolstr: a valid tool name like 'SegmentTool'
        :type toolstr: a string

        :returns: None
        """
        """  """
        if(toolstr is None):
            return

        self.enable_tool(toolstr, val)

    def toolclass_to_str(self, tool):
        s = str(tool)
        idx = s.find('object')
        s2 = s[0:idx - 1]
        s3 = s2.split('.')
        for _s in s3:
            if(_s.find('Tool') > -1):
                return(_s)
        return(None)

    def toolclasses_to_dct(self):
        dct = {}
        for tool in self.plot.manager.tools:
            tool_nm = self.toolclass_to_str(tool)
            dct[tool_nm] = tool

        return(dct)

    def clear_all_tools(self):

        tool_dct = self.toolclasses_to_dct()
        for REMTOOL in MAIN_TOOLS_STR:
            i = 0
            for tool in self.plot.manager.tools:
                tool_nm = self.toolclass_to_str(tool)
                if tool_nm == REMTOOL:
                    del(self.plot.manager.tools[i])
                    break
                i += 1


    def enable_delete_images(self, val):
        assert type(val) is bool, "enable_delete_images: val is not a boolean:"

        self.delete_images_enabled = val


    def enable_tool(self, toolstr, en=True):
        """
        enable_tool(): description

        :param toolstr: toolstr description
        :type toolstr: toolstr type

        :returns: None
        """
        #self.action.setEnabled(item is not None)
        toolstrs = toolstr.split('.')
        for s in toolstrs:
            if(s.find('Tool') > -1):
                toolstr = s

        dct = self.toolclasses_to_dct()
        if(toolstr in list(dct.keys())):
            tool = dct[toolstr]
            tool.set_enabled(en)
        #the following line is extremely important
        #unless set to None one of the tools could be set as "the active item"
        #which will cause an exception if you just click anywhere in the main plot
        #by setting it to None then none of the code that tries to access a selected tool
        #will execute
        self.get_active_plot().set_active_item(None)
#         tools = self.plot.manager.tools
#         for tool in tools:
#             tool_class_str = self.toolclass_to_str(tool)
#             if(tool_class_str is not None):
#                 if(toolstr == tool_class_str):
#                     tool.set_enabled(en)


    def enable_tool_by_tooltype(self, tooltype, en=True):
        """
        enable_tool_by_tooltype(): description

        :param tooltype: a valid guiqwt tool type
        :type tooltype: a valid tool type

        :returns: None
        """
        #self.action.setEnabled(item is not None)
        tools = self.plot.manager.tools
        for tool in tools:
            if(isinstance(tool, tooltype)):
                tool.set_enabled(en)

    def on_new_direct_beam_pos(self, xxx_todo_changeme):
        #print 'on_new_direct_beam_pos: %.2f, %.2f' % (cx, cy)
        (cx, cy) = xxx_todo_changeme
        self.new_beam_position.emit(cx, cy)

    def set_grid_parameters(self, bkgrnd_color, min_color, maj_color):
        """
        set_grid_parameters(): description

        :param bkgrnd_color: bkgrnd_color description
        :type bkgrnd_color: bkgrnd_color type

        :param min_color: min_color description
        :type min_color: min_color type

        :param maj_color: maj_color description
        :type maj_color: maj_color type

        :returns: None
        """
        """
        .. todo::
        there are man other image params that could be set in teh future, for now only implemented min/max
        GridParam:
            Grid:
                Background color: #eeeeee
                maj:
                  : True
                  : True
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1
                min:
                  : False
                  : False
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1

        """
        aplot = self.plot
        gparam = GridParam()
        gparam.background = bkgrnd_color
        gparam.maj_line.color = maj_color
        gparam.min_line.color = min_color
        aplot.grid.set_item_parameters({"GridParam": gparam})

        #QMouseEvent  event(QEvent.MouseButtonPress, pos, 0, 0, 0);
        #QApplication.sendEvent(mainWindow, & event);

        aplot.ensurePolished()
        #QtWidgets.QApplication.sendPostedEvents(aplot, QtCore.QEvent.PolishRequest)
        #aplot.polish()
        aplot.invalidate()
        aplot.replot()
        aplot.update_all_axes_styles()
        aplot.update()

    def set_cs_grid_parameters(
            self,
            forgrnd_color,
            bkgrnd_color,
            min_color,
            maj_color):
        """
        set_cs_grid_parameters(): description

        :param forgrnd_color: forgrnd_color description
        :type forgrnd_color: forgrnd_color type

        :param bkgrnd_color: bkgrnd_color description
        :type bkgrnd_color: bkgrnd_color type

        :param min_color: min_color description
        :type min_color: min_color type

        :param maj_color: maj_color description
        :type maj_color: maj_color type

        :returns: None
        """
        """
        .. todo::
        there are many other image params that could be set in the future, for now only implemented min/max
        GridParam:
            Grid:
                Background color: #eeeeee
                maj:
                  : True
                  : True
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1
                min:
                  : False
                  : False
                  LineStyleParam:
                    Style: Dotted line
                    Color: #121212
                    Width: 1

        """
        plot = self.plot
        xcs = self.get_xcs_panel()
        ycs = self.get_ycs_panel()
        xcs.cs_plot.label.hide()
        ycs.cs_plot.label.hide()

        # self.curve_item.update_params()
        cs_items = xcs.cs_plot.get_items()
        #csi = xcs.cs_plot.get_items(item_type=XCrossSectionItem)
        if(len(cs_items) == 3):
            csi = cs_items[2]
            cparam = csi.curveparam
            #cparam = CurveParam()
            cparam.line._color = forgrnd_color
            cparam._shade = 0.45
            xcs.cs_plot.set_item_parameters({"CurveParam": cparam})



        #csi = xcs.cs_plot.get_items(item_type=ICurveItemType)
        # print csi


        #csi.curveparam._shade = 0.75

        #cparam = CurveParam()
        #cparam.line._color = forgrnd_color
        #cparam._shade = 0.75

        # xcs.cs_plot.set_item_parameters({"CurveParam":cparam})
        # ycs.cs_plot.set_item_parameters({"CurveParam":cparam})

        gparam = GridParam()
        gparam.background = bkgrnd_color
        gparam.maj_line.color = maj_color
        gparam.min_line.color = min_color
        xcs.cs_plot.grid.set_item_parameters({"GridParam": gparam})
        ycs.cs_plot.grid.set_item_parameters({"GridParam": gparam})

        xcs.cs_plot.ensurePolished()
        ycs.cs_plot.ensurePolished()

        #xcs.cs_plot.polish()
        #ycs.cs_plot.polish()

        xcs.cs_plot.invalidate()
        ycs.cs_plot.invalidate()

        xcs.cs_plot.replot()
        ycs.cs_plot.replot()

        xcs.cs_plot.update_all_axes_styles()
        ycs.cs_plot.update_all_axes_styles()

        xcs.cs_plot.update()
        ycs.cs_plot.update()

    def get_data_dir(self):
        """
        get_data_dir(): description

        :returns: None
        """
        """
        set a durectory to use when calling openfile()
        """
        return(self._data_dir)

    def set_data_dir(self, ddir):
        """
        set_data_dir(): description

        :param ddir: ddir description
        :type ddir: ddir type

        :returns: None
        """
        """
        set a durectory to use when calling openfile()
        """
        self._data_dir = ddir
        self.opentool.set_directory(self._data_dir)

    def on_set_aspect_ratio(self, force):
        """
        on_set_aspect_ratio(): description

        :param force: force description
        :type force: force type

        :returns: None
        """

        if(hasattr(self, 'data')):
            if(hasattr(self.data, 'shape')):
                h, w = self.data.shape
                if (not hasattr(self.item, 'imageparam')):
                    return
                h = (self.item.imageparam.ymax - self.item.imageparam.ymin)
                w = (self.item.imageparam.xmax - self.item.imageparam.xmin)

                if(force):
                    # if(h > w):
                    if(w > h):
                        r = float(h / w)
                    else:
                        r = float(w / h)
                    # print 'forcing aspect ratio to square'
                    # print 'on_set_aspect_ratio: h=%d w = %d,  ratio = %f' % (h,
                    # w, r)
                    self.plot.set_aspect_ratio(ratio=r)
                    self.plot.replot()
                    self.set_autoscale()
                    # self.set_autoscale(fill_plot_window=True)

                else:
                    # print 'resetting to original aspect ratio'
                    self.plot.set_aspect_ratio(ratio=1)
                    self.set_autoscale()

                # self.plot.replot()
                # self.set_autoscale()

    def setColorMap(self, cmap_name):
        """
        setColorMap(): description

        :param cmap_name: cmap_name description
        :type cmap_name: cmap_name type

        :returns: None
        """
        self.color_map_str = cmap_name
        itemList = self.plot.get_items(item_type=ICSImageItemType)
        item = itemList[0]
        item.imageparam.colormap = cmap_name
        item.imageparam.update_image(item)
        # self.action.setText(cmap_name)
        self.plot.invalidate()
        # self.update_status(plot)

    def _toggleVisibility(self, item, on):
        """
        _toggleVisibility(): description

        :param item: item description
        :type item: item type

        :param on: on description
        :type on: on type

        :returns: None
        """
        item.setVisible(on)
        widget = self.plot.legend().find(item)
        if isinstance(widget, Qwt.QwtLegendItem):
            widget.setChecked(on)

        if(on):
            self.plot.set_active_item(self.item)

        self.plot.replot()

    def _setup_rect_shape(self, shape):
        """
        _setup_rect_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        # print 'in _setup_rect_shape'
        cur_shapes = self.getShapeItemsByShapeType(AnnotatedRectangle)
        if ((not self.multi_region_enabled) and (len(cur_shapes) > 0)):
            self.enable_tool_by_name('clsAverageCrossSectionTool', False)
        else:
            self.enable_tool_by_name('clsAverageCrossSectionTool', True)

    def setCheckRegionEnabled(self, val):
        """
        setCheckRegionEnabled(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.checkRegionEnabled = val

    def _setupsegment(self, seg):
        """
        _setupsegment(): description

        :param seg: seg description
        :type seg: seg type

        :returns: None
        """
        seg.setTitle("%s %d" % (types.spatial_type_prefix.SEG, self.segNum))

    def _drawSegment(self, rect):
        """
        _drawSegment(): description

        :param rect: rect description
        :type rect: rect type

        :returns: None
        """
        #print 'stxmImageWidget: _drawSegment'
        pass

    def _resizeItem(self, item, center, size, angle):
        """
        _resizeItem(): description

        :param item: item description
        :type item: item type

        :param center: center description
        :type center: center type

        :param size: size description
        :type size: size type

        :param angle: angle description
        :type angle: angle type

        :returns: None
        """
        A, B, C, E, F, G, I, D, H = calcRectPoints(
            center, (size[0], size[1]), angle)
        item.set_rect(E.x(), E.y(), I.x(), I.y())
        annotation = True
        if(annotation):
            item.shape.set_xdiameter(D.x(), D.y(), H.x(), H.y())
            item.shape.set_ydiameter(F.x(), F.y(), B.x(), B.y())
            dct = item.get_infos()
            self.new_ellipse.emit(dct)
            # print dct
        else:
            item.set_xdiameter(D.x(), D.y(), H.x(), H.y())
            item.set_ydiameter(F.x(), F.y(), B.x(), B.y())

        # set cross_marker to visible and place it at center
        self.plot.cross_marker.set_display_label(False)
        self.plot.cross_marker.setZ(self.plot.get_max_z() + 1)
        self.plot.cross_marker.setVisible(True)
        #r = QRectF(10,50,100,100)
#        r = QRectF(E.x(),E.y(),I.x(),I.y())
#        x,y = self.plot.cross_marker.axes_to_canvas(r.topLeft().x(), r.topLeft().y())
#        tl = QPointF(x,y)
#        x,y = self.plot.cross_marker.axes_to_canvas(r.bottomRight().x(), r.bottomRight().y())
#        br = QPointF(x,y)
#        self.plot.do_zoom_rect_view(tl, br)

        #x,y = self.plot.cross_marker.axes_to_canvas(r.center().x(), r.center().y())
        x, y = self.plot.cross_marker.axes_to_canvas(A.x(), A.y())
        c = QPointF(x, y)
        self.plot.cross_marker.move_local_point_to(0, c)
        self.plot.cross_marker.setVisible(False)
        self.plot.cross_marker.emit_changed()
        del(c)

    def create_target_circle(self, xc, yc, val):
        """
        create_target_circle(): description

        :param xc: xc description
        :type xc: xc type

        :param yc: yc description
        :type yc: yc type

        :param val: val description
        :type val: val type

        :returns: None
        """
        from guiqwt.styles import ShapeParam
        #circ = make.annotated_circle(x0, y0, x1, y1, ratio, title, subtitle)
        rad = val / 2.0
        circ = make.annotated_circle(
            xc - rad, yc + rad, xc + rad, yc - rad, 1, 'Target')
        sh = circ.shape.shapeparam
        # circ.set_resizable(False)
        # offset teh annotation so that it is not on the center
        circ.shape.shapeparam.fill = circ.shape.shapeparam.sel_fill
        circ.shape.shapeparam.line = circ.shape.shapeparam.sel_line
        circ.label.C = (50, 50)
        circ.set_label_visible(False)
        # print circ.curve_item.curveparam
        # circ.set_style(, option)
        circ.shape.set_item_parameters({"ShapeParam": circ.shape.shapeparam})
        self.plot.add_item(circ, z=999999999)

    def create_osa(self, do_it=True):
        """
        create_osa(): description

        :returns: None
        """
        if(do_it):
            #rad = 1000
            #xc = -1230
            #xc = 0.0
            #yc = 0.0
            #rect = (-1250, 500, 1250, -5500)

            xc, yc = self.ss.get('OSA_AMBIENT.CENTER')
            rect = self.ss.get('OSA_AMBIENT.RECT')

            create_rectangle(rect, title='osa_rect', plot=self.plot)

            create_simple_circle(
                rect[0] + 500, rect[1] - 500, 20, title='osa_1', plot=self.plot)
            create_simple_circle(
                rect[0] + 1000, rect[1] - 500, 25, title='osa_2', plot=self.plot)
            create_simple_circle(
                rect[0] + 1500, rect[1] - 500, 30, title='osa_3', plot=self.plot)
            create_simple_circle(
                rect[0] + 2000, rect[1] - 500, 35, title='osa_4', plot=self.plot)

        else:
            # remove the sample_holder
            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)
            for shape in shapes:
                if(hasattr(shape, 'shapeparam')):
                    s = shape.shapeparam
                    title = s._title
                    if(title.find('osa_') > -1):
                        self.delPlotItem(shape)
            self.blockSignals(False)
        self.plot.replot()

    def create_beam_spot(self, xc, yc, size=0.5):
        '''
        a function to create a beam spot shape that will show the current position of the beam on the plot
        :param rect:
        :return:
        '''
        diam = size / 2.0
        if (self.show_beam_spot):
            bsp = tools.BeamSpotShape(x1=xc, y1=yc, shapeparam=None)
            self.plot.add_item(bsp, z=999999999)
            #self.create_simple_circle(xc, yc, diam, title='beam_spot', clr='yellow', fill_alpha=0.8)

    def move_beam_spot(self, xc, yc):
        if(self.show_beam_spot):
            beam_spot_shape = self.get_shape_with_this_title('beam_spot')
            if(beam_spot_shape is None):
                self.create_beam_spot(xc, yc)
                self.prev_beam_pos = (xc, yc)
            else:
                #print 'move_beam_spot: (%.2f, %.2f)' % (xc, yc)
                beam_spot_shape.move_shape(self.prev_beam_pos, (xc,yc))
                self.prev_beam_pos = beam_spot_shape.get_center()

        self.plot.replot()



    def create_uhv_osa(self, do_it=True):
        """
        create_osa(): description

        :returns: None
        """
        if(do_it):
            xc, yc = self.ss.get('OSA_CRYO.CENTER')
            rect = self.ss.get('OSA_CRYO.RECT')
            x2 = rect[2]
            y1 = rect[1]
            create_rectangle(rect, title='osa_rect', plot=self.plot)
            # from outboard to inboard
            create_simple_circle(x2 - 250, y1 - 250, 35, title='osa_1', plot=self.plot)
            create_simple_circle(x2 - 250, y1 - 2250, 35, title='osa_2', plot=self.plot)

        else:
            # remove the sample_holder

            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)

            for shape in shapes:
                title = ''
                if(hasattr(shape, 'annotationparam')):
                    title = shape.annotationparam._title
                elif(hasattr(shape, 'shapeparam')):
                    title = shape.shapeparam._title

                if(title.find('osa_') > -1):
                    self.delPlotItem(shape)

            self.blockSignals(False)
        self.plot.replot()

    def create_stdrd_sample_holder(self, do_it=True):
        """
        create_sample_holder(): description

        :returns: None
        """
        HOLE_DIAMETER = 2500
        if(do_it):
            rad = self.ss.get('%s.RADIUS' % SAMPLE_STANDARD)
            rect = self.ss.get('%s.RECT' % SAMPLE_STANDARD)
            xc = (rect[0] + rect[2]) * 0.5
            yc = (rect[1] + rect[3] - 5000) * 0.5

            create_rectangle(rect, title='sh_rect')

            create_simple_circle(xc - 5000, yc, rad, title='sh_1', plot=self.plot)
            create_simple_circle(xc, yc, rad, title='sh_2', plot=self.plot)
            create_simple_circle(xc + 5000, yc, rad, title='sh_3', plot=self.plot)

            create_simple_circle(xc - 5000, yc + 5000, rad, title='sh_4', plot=self.plot)
            create_simple_circle(xc, yc + 5000, rad, title='sh_5', plot=self.plot)
            create_simple_circle(xc + 5000, yc + 5000, rad, title='sh_6', plot=self.plot)
        else:
            # remove the sample_holder
            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)
            for shape in shapes:
                title = ''
                if (hasattr(shape, 'annotationparam')):
                    title = shape.annotationparam._title
                elif (hasattr(shape, 'shapeparam')):
                    title = shape.shapeparam._title
                #s = shape.shapeparam
                #title = s._title
                if(title.find('sh_') > -1):
                    self.delPlotItem(shape)
            self.blockSignals(False)
        self.plot.replot()

    def create_goni_sample_holder(self, do_it=True):
        """
        create_sample_holder(): description

        :returns: None
        """
        if(do_it):
            rad = self.ss.get('%s.RADIUS' % SAMPLE_GONI)
            rect = self.ss.get('%s.RECT' % SAMPLE_GONI)
            xc, yc = self.ss.get('%s.CENTER' % SAMPLE_GONI)
            #xc = (rect[0] + rect[2]) * 0.5
            #yc = (rect[1] + rect[3] - 5000) * 0.5
            frame = (0.0, 600.0, 3000.0, -600.0)
            frame_outbrd_edge = xc - ((frame[0] + frame[2])/2.0)

            hole = (-100, 400, 100, -400)


            #self.create_rectangle(new_rect, title='sh_rect')
            create_rect_centerd_at(frame, xc , yc , title='sh_rect', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 385.0, yc, title='sh_1', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 660.0, yc , title='sh_1', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 935.0, yc , title='sh_2', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 1210.0, yc , title='sh_3', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 1485.0, yc , title='sh_4', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 1760.0, yc , title='sh_5', plot=self.plot)
            create_rect_centerd_at(hole, frame_outbrd_edge + 2035.0, yc , title='sh_6', plot=self.plot)
            #self.create_rect_centerd_at(hole, frame_outbrd_edge + 1945.0, yc , title='sh_7')
            #self.create_rect_centerd_at(hole, frame_outbrd_edge + 100.0, yc , title='sh_8')

        else:
            #        else:
            # remove the sample_holder
            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)
            for shape in shapes:
                title = ''
                if (hasattr(shape, 'annotationparam')):
                    title = shape.annotationparam._title
                elif (hasattr(shape, 'shapeparam')):
                    title = shape.shapeparam._title
                if(title.find('sh_') > -1):
                    self.delPlotItem(shape)
            self.blockSignals(False)
        self.plot.replot()

    def show_pattern(self, xc=None, yc=None, pad_size=1.0, do_show=True):
        #passing self will allow the pattern to be added to the plotter
        if(do_show):
            if((xc or yc) == None):
                (x, y) = self.plot.get_active_axes()
                xmin, xmax = self.plot.get_axis_limits(x)
                ymin, ymax = self.plot.get_axis_limits(y)
                #xc, yc = self.ss.get('PATTERN.CENTER')
                xc = (xmax + xmin) * 0.5
                yc = (ymax + ymin) * 0.5

            #need to get the current centers
            add_pattern_to_plot(self, xc, yc, pad_size)
            self.register_shape_info(shape_info_dct={'shape_title': 'pattern', 'on_selected': self.select_pattern, 'on_deselected': self.deselect_pattern})

            self.set_center_at_XY((xc, yc), (pad_size * 10, pad_size * 10))
        else:
            # remove the pattern
            self.blockSignals(True)
            shapes = self.plot.get_items(item_type=IShapeItemType)
            for shape in shapes:
                title = ''
                if (hasattr(shape, 'annotationparam')):
                    title = shape.annotationparam._title
                elif (hasattr(shape, 'shapeparam')):
                    title = shape.shapeparam._title
                if (title.find('pattern') > -1):
                    self.delPlotItem(shape)
            self.blockSignals(False)

    def select_pattern(self):
        '''
        select the pattern shape
        :return:
        '''
        selected_shapes = self.select_main_rect_of_shape('pattern')
        return(selected_shapes)

    def deselect_pattern(self):
        #self.deselect_main_rect_of_shape('pattern')
        pass

    def move_shape_to_new_center(self, title, xc, yc):
        '''
        select the shapes with name 'title' and move them based on a new center
        :param title:
        :param xc:
        :param yc:
        :return:
        '''
        selected_shapes = self.select_main_rect_of_shape(title)
        for shape in selected_shapes:
            #shape.add_point((3,3))
            old_cntr = shape.get_center()
            new_center = (xc + old_cntr[0]  , yc + old_cntr[1])
            shape.move_shape(old_cntr, new_center)




    def addPlotItem(self, item):
        """
        addPlotItem(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        plot = self.get_plot()
        plot.add_item(item)
        self.update()
        plot.replot()

    def addPlotItems(self, items):
        """
        addPlotItems(): description

        :param items: items description
        :type items: items type

        :returns: None
        """
        plot = self.get_plot()
        for item in items:
            plot.add_item(item)
        self.update()
        plot.replot()

    def _handle_final_segment_shape(self, seg):
        """
        _handle_final_segment_shape(): This is used only by the measure tool

        :param seg: seg description
        :type seg: seg type

        :returns: None
        """
        #seg.setTitle("%s %d" % (types.spatial_type_prefix.SEG, self.segNum))
#         seg.setItemAttribute(Qwt.QwtPlotItem.Legend)
#         widget = self.plot.legend().find(seg)
#         if isinstance(widget, Qwt.QwtLegendItem):
#             widget.setChecked(True)

        ret = self._anno_seg_to_region(seg)
        # self.new_region.emit(ret)
        self._select_this_item(seg)
        self.update()

    def _handle_final_horiz_segment_shape(self, seg):
        """
        _handle_final_horiz_segment_shape(): this is used by all segment roi selection tools

        :param seg: seg description
        :type seg: seg type

        :returns: None
        """
        ret = self._seg_to_region(seg)
        # print '_handle_final_horiz_segment_shape: emitting new region' , ret
        self.new_region.emit(ret)
        # self._select_this_item(seg)
        self.update()

        # check for either horiz or other segments
        cur_shapes = self.getShapeItemsByShapeType(AnnotatedHorizontalSegment)
        if(len(cur_shapes) > 0):
            if(not self.multi_region_enabled):
                self.enable_tools_by_shape_type(
                    AnnotatedHorizontalSegment, False)
            else:
                self.enable_tools_by_shape_type(
                    AnnotatedHorizontalSegment, True)
        else:
            cur_shapes = self.getShapeItemsByShapeType(AnnotatedSegment)
            if((not self.multi_region_enabled) and (len(cur_shapes) > 0)):
                self.enable_tools_by_shape_type(AnnotatedSegment, False)
            else:
                self.enable_tools_by_shape_type(AnnotatedSegment, True)

    def setuppoint(self, point):
        """
        setuppoint(): description

        :param point: point description
        :type point: point type

        :returns: None
        """
        # print 'in setuppoint'
        pass
        #point.setTitle("%s %d" % (types.spatial_type_prefix.PNT, self.shapeNum))

    def shape_end_rect(self, shape):
        """
        shape_end_rect(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        # print shape
        pass

    def _handle_final_point_shape(self, point):
        """
        _handle_final_point_shape(): description

        :param point: point description
        :type point: point type

        :returns: None
        """
        #point.setItemAttribute(Qwt.QwtPlotItem.Legend)
        #widget = self.plot.legend().find(point)
        #if isinstance(widget, Qwt.QwtLegendItem):
        #    widget.setChecked(True)

        ret = self._anno_point_to_region(point)
        self.new_region.emit(ret)
        self._select_this_item(point)
        self.update()

        cur_shapes = self.getShapeItemsByShapeType(AnnotatedPoint)
        if((not self.multi_region_enabled) and (len(cur_shapes) > 0)):
            self.enable_tools_by_shape_type(AnnotatedPoint, False)
        else:
            self.enable_tools_by_shape_type(AnnotatedPoint, True)

    def get_shape_with_this_title(self, _title):
        shapes = self.plot.get_items(item_type=IShapeItemType)
        for shape in shapes:
            title = ''
            if (hasattr(shape, 'annotationparam')):
                title = shape.annotationparam._title
            elif (hasattr(shape, 'shapeparam')):
                title = shape.shapeparam._title
            if(title == _title):
                return(shape)
        return(None)

    def select_all_shapes_with_this_title(self, _title):
        shapes = self.plot.get_items(item_type=IShapeItemType)
        for shape in shapes:
            title = ''
            if (hasattr(shape, 'annotationparam')):
                title = shape.annotationparam._title
            elif (hasattr(shape, 'shapeparam')):
                title = shape.shapeparam._title
            if(title.find(_title) > -1):
                shape.select()

    def select_sample_holder(self):
        self.select_main_rect_of_shape('sh_')

    def select_osa(self):
        self.select_main_rect_of_shape('osa_')



    def select_main_rect_of_shape(self, _title='sh_'):
        #print('select_main_rect_of_shape: looking for shapes with the name [%s] in it' % _title)
        num_found = 0
        shapes = self.plot.get_items(item_type=IShapeItemType)
        selected_shapes = []

        for shape in shapes:
            _rect = shape.get_rect()
            # QtCore.QRectF( top left, btm right)
            qrect = QtCore.QRectF(QtCore.QPointF(_rect[0], _rect[2]), QtCore.QPointF(_rect[3], _rect[1]))

            title = ''
            if (hasattr(shape, 'annotationparam')):
                title = shape.annotationparam._title
            elif (hasattr(shape, 'shapeparam')):
                title = shape.shapeparam._title
            #print('select_main_rect_of_shape: checking [%s]' % title)
            if(hasattr(shape, 'selection_name')):
                sel_name = shape.selection_name
                if(sel_name.find(_title[0:5]) > -1):
                    #shape.select()
                    selected_shapes.append(shape)
                    #print('select_main_rect_of_shape: found selection_name [%d]' % num_found)
                    num_found += 1
            elif(title.find(_title[0:5]) > -1):
                #shape.select()
                #print('select_main_rect_of_shape: found name [%d]' % num_found)
                selected_shapes.append(shape)
                num_found += 1
                # if (title.find('%srect' % _title) > -1):
                #     #main_rect = shape
                #     shape.select()
                #     #we will selct this one as the last one before we leave
                # else:
                #     #still want to select all in the shape
                #     shape.select()
                #     #_toselect.append(shape)
            # if(main_rect is None):
            #     main_rect = qrect
            # else:
            #     main_rect = main_rect.united(qrect)
            else:
                print('select_main_rect_of_shape: the shape title [%s] didnt match [%s]' % (title, _title))
        if(len(selected_shapes) > 0):
            selected_shapes.reverse()
            for sh in selected_shapes:
                #print('selecting [%s]' % sh.selection_name)
                sh.select()
        #self.target_moved.emit(main_rect)
        return(selected_shapes)


    def selected_item_changed(self, plot):
        """
        selected_item_changed():



        Note for de-selections: this function is called AFTER the guiplot has deselected all
        of the shapes and items

        :param plot: plot description
        :type plot: plot type

        :returns: None
        """
        is_regd_shape = False
        shape = None
        item = plot.get_active_item()
        #print('selected_item_changed:', item)
        if(isinstance(item, AnnotatedRectangle)):
            print('ok here is an Annotated Rect, does it have a selection name?: ', hasattr(item, 'selection_name'))

        if (hasattr(item, 'unique_id')):
            self._cur_shape_uid = item.unique_id

        if(item):
            if(hasattr(item, 'shapeparam')):
                shape = item.shapeparam
                title = shape._title
            else:
                title = item.title().text()
            if (hasattr(item, 'shape')):
                shape = item.shape

            if(title.find('sh_') > -1):
                # select all sample holder items
                self.select_sample_holder()

            if(title.find('osa_') > -1):
                # select all sample holder items
                self.select_osa()


            if (hasattr(item, 'selection_name')):
                sel_name = item.selection_name
                print('sel_name is [%s]' % sel_name)
                sel_prefix = sel_name.split('_')[0]
                regd_shape = self.get_shape_from_registry(sel_prefix)
                if (regd_shape):
                    # only look at first 5 chars
                    if (sel_prefix.find(regd_shape['shape_title'][0:5]) > -1):
                        # call teh regsitered handler
                        if (regd_shape['on_selected']):
                            regd_shape['on_selected']()
                            is_regd_shape = True
                        else:
                            _logger.error(
                                'selected_item_changed: on_selected handler registered for [%s]' % regd_shape[
                                    'shape_title'])

            #
            # regd_shape = self.get_shape_from_registry(title)
            # if(regd_shape):
            #     #only look at first 5 chars
            #
            #     if (title.find(regd_shape['shape_title'][0:5]) > -1):
            #         #call teh regsitered handler
            #         if(regd_shape['on_selected']):
            #             regd_shape['on_selected']()
            #             is_regd_shape = True
            #         else:
            #             _logger.error('selected_item_changed: on_selected handler registered for [%s]' % regd_shape['shape_title'])

            if(not is_regd_shape):
                pass
            else:
                print('is_regd_shape is True')
            self.sel_item_id = title


            if(hasattr(item, 'unique_id')):
                set_current_unique_id(item.unique_id)
                self.inputState.plotitem_id = item.unique_id
                #print 'selected_item_changed: emitting new_roi with cmnd=SELECT_ROI'
                self._emit_new_roi(self.image_type, cmnd=widget_com_cmnd_types.SELECT_ROI)

            if(hasattr(item, 'is_label_visible')):
                item.set_label_visible(True)
        else:
            #deselect all
            #print 'selected_item_changed: emitting new_roi with cmnd=DESELECT_ROI'
            self._emit_new_roi(self.image_type, cmnd=widget_com_cmnd_types.DESELECT_ROI)

    def on_sig_plot_axis_changed(self, plot):
        """
        on_sig_plot_axis_changed(): description

        :param plot: plot description
        :type plot: plot type

        :returns: None
        """
        """
        a sig handler that fires when the plot is panned and zoomed
        which will emit a noi_roi_center signal so that it can be used
        to update scan parameters
        """
        ilist = plot.get_items(item_type=IDecoratorItemType)
        grid = ilist[0]
        rngx = grid.xScaleDiv().range()

        (x1, x2) = self.plot.get_axis_limits('bottom')
        (y1, y2) = self.plot.get_axis_limits('left')

        cx = (x1 + x2) / 2
        rx = x2 - x1

        cy = (y1 + y2) / 2
        ry = y2 - y1

        self.inputState.center = (cx, cy)
        self.inputState.range = (rx, ry)
        self.inputState.rect = (x1, y1, x2, y2)

        # only emit a new_roi_center if the user has the F1 pressed
        #if(self.inputState.keyisPressed[Qt.Key_F1]):
        #    self._emit_new_roi(self.image_type)

    def items_changed(self, plot):
        """
        items_changed(): description

        :param plot: plot description
        :type plot: plot type

        :returns: None
        """
        items = plot.get_items()
        # disable region select tool
        self.get_default_tool().activate()

    def Image_changed(self, items):
        """
        Image_changed(): description

        :param items: items description
        :type items: items type

        :returns: None
        """
        for i in items:
            #print 'Image_changed:'
            #print i.title().text()
            # print i.get_rect()
            pass

    def AnnotatedRectangle_changed(self, items):
        """
        AnnotatedRectangle_changed(): description

        :param items: items description
        :type items: items type

        :returns: None
        """
        pass
        # for i in items:
        # print 'AnnotatedRectangle_changed: '
        # print i.title().text()
        # print i.get_rect()

    def active_item_moved(self, item):
        """
        active_item_moved(): description

        :param item: item description
        :type item: item type

        :returns: None
        """

        if hasattr(item, 'annotationparam'):
            title = item.annotationparam.title
            if(item.annotationparam.title == 'Target'):
                cntr = item.get_center()
                (self.zoom_scale, dud) = item.get_tr_size()
                self.zoom_scale = self.zoom_scale * 0.75
                self.target_moved.emit(cntr)
            else:
                if(self.inputState.keyisPressed[Qt.Key_Alt]):
                    self._emit_new_roi(self.image_type)

        elif hasattr(item, 'shapeparam'):
            shape = item.shapeparam
            title = shape._title
        else:
            title = ''

        #print('active_item_moved', (title, item.get_center()))

        if(title.find('osa_') > -1):
            shape = self.get_shape_with_this_title('osa_rect')
            if(shape):
                self.ss.set('%s.CENTER' % self.osa_type, shape.get_center())
                self.ss.set('%s.RECT' % self.osa_type, shape.get_rect())
                self.ss.update()

        if(title.find('sh_') > -1):
            shape = self.get_shape_with_this_title('sh_rect')
            if(shape):
                self.ss.set('%s.CENTER' % self.sample_hldr_type, shape.get_center())
                self.ss.set('%s.RECT' % self.sample_hldr_type, shape.get_rect())
                self.ss.update()

        regd_shape = self.get_shape_from_registry(title)
        if (regd_shape):
            # only look at first 5 chars
            if(title.find(regd_shape['shape_title'][0:5]) > -1):
                cntr = item.get_center()
                self.ss.set('%s.CENTER' % regd_shape['shape_title'].upper(), cntr)
                #self.ss.set('%s.RECT' % regd_shape['shape_title'].upper(), shape.get_rect())
                self.ss.update()
                self._emit_new_roi(self.image_type)


        else:
            # print 'active_item_moved: event for this item not handled' , item
            pass

    def set_transform_factors(self, x, y, z, unit):
        """
        set_transform_factors(): description

        :param x: x description
        :type x: x type

        :param y: y description
        :type y: y type

        :param z: z description
        :type z: z type

        :param unit: unit description
        :type unit: unit type

        :returns: None
        """
        self.xTransform = x
        self.yTransform = y
        self.zTransform = z
        self.unitTransform = unit

    def reset_transform_factors(self):
        """
        reset_transform_factors(): description

        :returns: None
        """
        self.xTransform = 1.0
        self.yTransform = 1.0
        self.zTransform = 1.0
        self.unitTransform = 'um'

    def _anno_point_to_region(self, item, set_id=True):
        """
        _anno_point_to_region(): description

        :param item: item description
        :type item: item type

        :param set_id=True: set_id=True description
        :type set_id=True: set_id=True type

        :returns: None
        """
        """ convert an annotated point item to a region dict"""
        (x1, y1) = item.get_pos()
        cntr = (x1, y1)
        sz = (1, 1)
        ret = {}
        ret['type'] = types.spatial_type_prefix.PNT  # types.spatial_type_prefix.PNT
        ret['name'] = str(item.title().text())
        ret['center'] = cntr
        ret['range'] = sz
        ret['rect'] = (x1, y1, x1, y1)
        return(ret)

    def _anno_seg_to_region(self, item, set_id=True):
        """
        _anno_seg_to_region(): description

        :param item: item description
        :type item: item type

        :param set_id=True: set_id=True description
        :type set_id=True: set_id=True type

        :returns: None
        """
        """ convert an annotated segment item to a region dict"""
        (x1, y1, x2, y2) = item.get_rect()
        cntr = ((x1 + x2) / 2.0, (y2 + y1) / 2.0)

        ret = {}
        ret['type'] = types.spatial_type_prefix.SEG  # types.spatial_type_prefix.SEG
        ret['name'] = str(item.title().text())
        ret['center'] = cntr
        ret['range'] = (abs(x2 - x1), abs(y2 - y1))
        ret['rect'] = (x1, y1, x2, y2)
        return(ret)

    def _anno_spatial_to_region(self, item, set_id=True):
        """
        _anno_spatial_to_region(): description

        :param item: item description
        :type item: item type

        :param set_id=True: set_id=True description
        :type set_id=True: set_id=True type

        :returns: None
        """
        """ convert an annotated rectangle item to a region dict"""
        cntr = item.get_tr_center()
        sz = item.get_tr_size()
        rect = item.get_rect()

        ret = {}
        ret['type'] = types.spatial_type_prefix.ROI  # SPATIAL_TYPE_PREFIX[TWO_D]
        ret['name'] = str(item.title().text())
        ret['center'] = cntr
        ret['range'] = sz
        ret['rect'] = rect
        return(ret)

    def _seg_to_region(self, item):
        """
        _seg_to_region(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        """ convert an annotated segment item to a region dict"""
        (x1, y1, x2, y2) = item.get_rect()
        cntr = ((x1 + x2) / 2.0, (y2 + y1) / 2.0)
        #sz = (item.get_tr_length(), item.get_tr_length())
        ret = {}
        ret['type'] = types.spatial_type_prefix.SEG  # types.spatial_type_prefix.SEG
        ret['name'] = 'HSEG'  # str(item.title().text())
        ret['center'] = cntr
        ret['range'] = (x2 - x1, y2 - y1)
        ret['rect'] = (x1, x2, y1, y2)
        return(ret)

    def _region_name_to_item(self, region_name):
        """
        _region_name_to_item(): description

        :param region_name: region_name description
        :type region_name: region_name type

        :returns: None
        """
        """
        take a region name and return the plot item it corresponds to
        """
        items = self.plot.get_items(item_type=IShapeItemType)
        #items = self.plot.get_items()
        for item in items:
            name = str(item.title().text())
            if(name == region_name):
                return(item)
        return(None)

    def select_region(self, region_name):
        """
        select_region(): description

        :param region_name: region_name description
        :type region_name: region_name type

        :returns: None
        """
        """
        used by callers to make a region selected, typically this is
        called by the gui which is managing the connection to the scan table
        so that a user can select a scan in the table and this function will make that selection
        active on the plot.
        Args:
            region_name: this is the name of the region which is also the text found in the item.title().text()

        """
        sel_item = self._region_name_to_item(region_name)
        items = self.plot.get_items(item_type=IShapeItemType)

        for item in items:
            if(item is not None):
                if(item == sel_item):
                    # print 'select_region: %s' % region_name
                    # print 'item.text() = %s' %(str(item.title().text()))
                    #
                    item.set_label_visible(True)
                else:
                    item.set_label_visible(False)

        self.plot.replot()

    def _select_this_item(self, item, set_label_visible=True):
        """
        _select_this_item(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        """
        this function is used to deselect everything on the plot
        and make the current item selected as well as make the annotation visible,
        without this the point and segment shapes do not stay selected after they have been
        created, seems to fix a bug in guiqwt
        """
        plot = self.get_plot()
        plot.unselect_all()
        plot.select_item(item)
        plot.set_active_item(item)
        if(set_label_visible):
            item.set_label_visible(True)

    def on_active_item_changed(self, item):
        """
        on_active_item_changed(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        # print 'on_active_item_changed'
        # print item
        pass

    def annotation_item_changed(self, item):
        """
        annotation_item_changed(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        """
        This function is called whwnever a annotated shapeItem is moved or resized.
        At the time is called though it may not yet have had its item_id assigned, if it hasn't then assign one (by setting set_id=True)
        """
        set_id = False
        if isinstance(item, AnnotatedPoint):
            rect = item.get_pos()
            qrect = QRectF(QPointF(rect[0], rect[1]), QPointF(1, 1))
            s = str(item.title().text()).split()
            ret = self._anno_point_to_region(item, set_id=set_id)
            self.inputState.center = ret['center']
            self.inputState.range = ret['range']
            self.inputState.rect = ret['rect']
            self.inputState.npts = (None, None)


            if(hasattr(item, 'unique_id')):
                if(item.unique_id is not get_current_unique_id()):
                    print('why dont these ids match? %d %d' % (item.unique_id, get_current_unique_id()))
                item.unique_id = get_current_unique_id()
                self.inputState.plotitem_id = item.unique_id
                #print 'annotation_item_changed: item unique_id = %d' % self.inputState.plotitem_id
            else:
                print('item has NO unique_id attr why??????')

            self.inputState.plotitem_title = str(item.title().text())
            self.inputState.plotitem_type = types.spatial_type_prefix.PNT
            self.inputState.plotitem_shape = item
            # print '<drag> %s id(item)=%d, unique=%d' %
            # (self.inputState.plotitem_title, id(item), item.unique_id)
            if(hasattr(item, 'unique_id')):
                if(item.unique_id is not -1):
                    #print 'AnnotatedPoint: annotation_item_changed: emitting new_roi '
                    self._emit_new_roi(self.image_type)

        elif isinstance(item, tools.clsMeasureTool):
            pass

        elif isinstance(item, AnnotatedHorizontalSegment):
            # if(self.checkRegionEnabled):
            #    qrect = self._check_valid_region(item)
            l = item.label
            lp = l.labelparam
            lp.yc = 50
            l.set_item_parameters({"LabelParam": lp})

            if(item.annotationparam.title == ''):
                (title, tfm, format) = self._get_seg_anno_params()
                item.annotationparam.title = title
            s = str(item.title().text()).split()
            ret = self._anno_seg_to_region(item, set_id=set_id)
            self.inputState.center = ret['center']
            self.inputState.range = ret['range']
            self.inputState.rect = ret['rect']
            self.inputState.npts = (None, None)
            # extract the plotitem_id of this AnnotatedHorizontalSegment

            if(hasattr(item, 'unique_id')):
                item.unique_id = get_current_unique_id()
                self.inputState.plotitem_id = item.unique_id

            self.inputState.plotitem_title = str(item.title().text())
            self.inputState.plotitem_type = types.spatial_type_prefix.SEG

            if(self.checkRegionEnabled):
                qrect = self._check_valid_region(item)
                self.inputState.rect = qrect.getCoords()
            else:
                self.inputState.rect = item.get_rect()

            self.inputState.plotitem_shape = item

            if(hasattr(item, 'unique_id')):
                if(item.unique_id is not -1):
                    #print 'AnnotatedHorizontalSegment: annotation_item_changed: emitting new_roi'
                    self._emit_new_roi(self.image_type)

        elif isinstance(item, AnnotatedSegment):
            # if(self.checkRegionEnabled):
            #    qrect = self._check_valid_region(item)
            l = item.label
            lp = l.labelparam
            lp.yc = 50
            l.set_item_parameters({"LabelParam": lp})
            if(item.annotationparam.title == ''):
                (title, tfm, format) = self._get_seg_anno_params()
                item.annotationparam.title = title
            s = str(item.title().text()).split()

            ret = self._anno_seg_to_region(item, set_id=set_id)
            self.inputState.center = ret['center']
            self.inputState.range = ret['range']
            #self.inputState.rect = ret['rect']
            self.inputState.npts = (None, None)
            if(hasattr(item, 'unique_id')):
                if (item.unique_id is not -1):
                    item.unique_id = get_current_unique_id()
                self.inputState.plotitem_id = item.unique_id

            self.inputState.plotitem_title = str(item.title().text())
            self.inputState.plotitem_type = types.spatial_type_prefix.SEG
            self.inputState.rect = item.get_rect()
            self.inputState.plotitem_shape = item

            # dont boundary check teh measureing tool
            if(item.get_text().find('Measure') == -1):
                if(self.checkRegionEnabled):
                    qrect = self._check_valid_region(item)
                    self.inputState.rect = qrect.getCoords()

            if(hasattr(item, 'unique_id')):
                if(item.unique_id is not -1):
                    #print 'AnnotatedSegment: annotation_item_changed: emitting new_roi'
                    self._emit_new_roi(self.image_type)

        elif isinstance(item, RectangleShape):
            #print 'Im a RectangleShape'
            pass

        elif isinstance(item, AnnotatedRectangle):

            self.inputState.center = item.get_center()
            self.inputState.range = item.get_tr_size()
            s = str(item.title().text()).split()
            if(hasattr(item, 'unique_id')):
                if (item.unique_id is None):
                    item.unique_id = get_current_unique_id()
                self.inputState.plotitem_id = item.unique_id
                #print 'annotation_item_changed: item.unique_id=%d' % item.unique_id
                #print 'annotation_item_changed: addr(item.unique_id)=%d' % id(item.unique_id)
                #had to add the following check because for some reason the tool will emit a CHANGE 2 times with the
                #previous unique_id
                if(self._cur_shape_uid is not item.unique_id):
                    #print 'THE UNIQUE_IDs DO NOT MATCH SKIPPING'
                    return
            self.inputState.plotitem_title = str(item.title().text())
            self.inputState.plotitem_type = types.spatial_type_prefix.ROI
            self.inputState.plotitem_shape = item
            # print 'annotation_item_changed: ', item.unique_id

            if(self.checkRegionEnabled):
                qrect = self._check_valid_region(item)
                self.inputState.rect = qrect.getCoords()
            else:
                self.inputState.rect = item.get_rect()

            # print 'self.inputState.rect: ', self.inputState.rect
            if(hasattr(item, 'unique_id')):
                if(item.unique_id is not -1):
                    #print 'AnnotatedRectangle: annotation_item_changed: emitting new_roi'
                    self._emit_new_roi(self.image_type)

        elif isinstance(item, AnnotatedCircle):
            if(hasattr(item, 'unique_id')):
                if(item.unique_id is None):
                    item.unique_id = get_current_unique_id()
                self.inputState.plotitem_id = item.unique_id
                self.inputState.plotitem_shape = item

            if(self.checkRegionEnabled):
                qrect = self._check_valid_region(item)
            if(hasattr(item, "get_tr_center")):
                ret = self._anno_spatial_to_region(item)
        elif isinstance(item, AnnotatedEllipse):
            self.inputState.plotitem_id = self.roiNum
            if(self.checkRegionEnabled):
                qrect = self._check_valid_region(item)
            if(hasattr(item, "get_tr_center")):
                ret = self._anno_spatial_to_region(item)
            self.inputState.plotitem_shape = item

        if(self.xTransform > 0.0):
            item.annotationparam.transform_matrix = [[self.xTransform, 0.0, 0.0], [
                0.0, self.yTransform, 0.0], [0.0, 0.0, self.zTransform]]
            item.annotationparam.format = '%5.2f ' + self.unitTransform
        else:
            item.annotationparam.transform_matrix = [
                [self.xstep, 0.0, 0.0], [0.0, self.ystep, 0.0], [0.0, 0.0, 1.0]]
            item.annotationparam.format = '%5.2f um'

        item.apply_transform_matrix(1, 1)
        item.set_label_visible(True)

    def set_shape_limits(self, shape=types.spatial_type_prefix.ROI, limit_def=None):
        if(limit_def):

            self.enable_tools_by_spatial_type(tp=shape)

            if(shape == types.spatial_type_prefix.ROI):
                self.roi_limit_def = limit_def
            elif(shape == types.spatial_type_prefix.SEG):
                self.seg_limit_def = limit_def
            elif(shape == types.spatial_type_prefix.PNT):
                self.pnt_limit_def = limit_def
        else:
            # disable all roi selection tools
            self.enable_tools_by_spatial_type(None)

#     def _restrict_rect_to_positive(self, rect):
#         """
#         _restrict_rect_to_positive(): description
#
#         :param r: r description
#         :type r: r type
#
#         :returns: None
#         """
#         (x1, y1, x2, y2) = rect
#         #if they are negative restrict them so they aren't
#         if(x2 <= x1):
#             x2 = x1 + 1
#         if(y2 >= y1):
#             y2 = y1 + 1
#
#         qrect = QRectF(QPointF(rect[0],rect[1]),QPointF(x2,y2))
#         return(qrect)
    def _restrict_rect_to_positive(self, rect):
        """
        _restrict_rect_to_positive(): description

        :param r: r description
        :type r: r type

        :returns: None
        """
        swap = False
        (x1, y1, x2, y2) = rect
        # if they are negative restrict them so they aren't
        if(x2 < x1):
            swap = True
        # if(y2 > y1):
        #    swap = True

        if(swap):
            qrect = QRectF(QPointF(x2, y2), QPointF(x1, y1))
        else:
            qrect = QRectF(QPointF(x1, y1), QPointF(x2, y2))

        return(qrect)

#     def _limit_rect(self, r):
#         """
#         _limit_rect(): echks rect against max_shape_size
#
#         :param r: r description
#         :type r: r type
#
#         :returns: None
#         """
#         x1 = r[0]
#         y1 = r[1]
#         x2 = r[2]
#         y2 = r[3]
#         wd = x2 - x1
#         ht = y2 - y1
#         #if they are negative restrict them so they aren't
#         if(wd <= self.max_shape_size[0]):
#             wd = self.max_shape_size[0]
#         if(ht <= self.max_shape_size[1]):
#             ht = self.max_shape_size[1]
#
#         rect = (x1, y1, x1+wd, y1+ht)
#         return(rect)
#
#     def _limit_qrect(self, r):
#         """
#         _restrict_rect_to_positive(): echks rect against max_shape_size
#
#         :param r: r description
#         :type r: r type
#
#         :returns: None
#         """
#         x1 = r[0]
#         y1 = r[1]
#         wd = r[2]
#         ht = r[3]
#         #if they are negative restrict them so they aren't
#         if(wd >= self.max_shape_size[0]):
#             wd = self.max_shape_size[0]
#         if(ht >= self.max_shape_size[1]):
#             ht = self.max_shape_size[1]
#
#         rect = QRectF(x1, y1, wd, ht)
#         return(rect)

    def _check_valid_region(self, item):
        """
        _check_valid_region(): description

        :param item: item description
        :type item: item type

        :returns: None
        """
        # print '_check_valid_region'
        if(self.checkRegionEnabled):

            if isinstance(item, AnnotatedPoint):
                self.inputState.shape_outof_range = False

            elif(isinstance(item, AnnotatedSegment) or isinstance(item, AnnotatedHorizontalSegment)):
                # print 'in AnnotatedSegment'
                rect = item.get_rect()
                sh = item.shape.shapeparam
                qrect = self._restrict_rect_to_positive(rect)
                if(self.seg_limit_def):
                    qrect = self.seg_limit_def.check_limits(qrect)
                    #item.setTitle(self.seg_limit_def.get_label())
                    item.setTitle(self.seg_limit_def.get_label() + ': %d' % item.unique_id)
                    if(self.seg_limit_def.state == ROI_STATE_ALARM):
                        self.inputState.shape_outof_range = True
                    else:
                        self.inputState.shape_outof_range = False
                else:
                    self.inputState.shape_outof_range = False

                if(self.inputState.shape_outof_range):
                    # print 'SEG: setting color red: #ff0000 alpha is ff'
                    lineWidth = 5
                    lineStyle = Qt.DashLine
                    lineColor = get_alarm_clr(255)
                else:
                    # print 'SEG: setting color green #00ff00 alpha is ff'
                    lineWidth = 1
                    lineStyle = Qt.SolidLine
                    lineColor = get_normal_clr(255)

                item.shape.sel_pen.setStyle(lineStyle)
                item.shape.sel_pen.setWidth(lineWidth)
                item.shape.sel_pen.setColor(lineColor)
                item.shape.pen.setStyle(lineStyle)
                item.shape.pen.setWidth(lineWidth)
                item.shape.pen.setColor(lineColor)

                # item.shape.sel_brush.setStyle(self.roi_limit_def.get_fill_pattern())
                # item.shape.sel_brush.setColor(self.roi_limit_def.get_color())

                sh.update_param(item.shape)
                return(qrect)

            elif (isinstance(item, AnnotatedRectangle)  or isinstance(item, RectangleShape)):
                #                 BRUSHSTYLE_CHOICES = [
                #                     ("NoBrush", _("No brush pattern"), "nobrush.png"),
                #                     ("SolidPattern", _("Uniform color"), "solidpattern.png"),
                #                     ("Dense1Pattern", _("Extremely dense brush pattern"), "dense1pattern.png"),
                #                     ("Dense2Pattern", _("Very dense brush pattern"), "dense2pattern.png"),
                #                     ("Dense3Pattern", _("Somewhat dense brush pattern"), "dense3pattern.png"),
                #                     ("Dense4Pattern", _("Half dense brush pattern"), "dense4pattern.png"),
                #                     ("Dense5Pattern", _("Somewhat sparse brush pattern"), "dense5pattern.png"),
                #                     ("Dense6Pattern", _("Very sparse brush pattern"), "dense6pattern.png"),
                #                     ("Dense7Pattern", _("Extremely sparse brush pattern"), "dense7pattern.png"),
                #                     ("HorPattern", _("Horizontal lines"), "horpattern.png"),
                #                     ("VerPattern", _("Vertical lines"), "verpattern.png"),
                #                     ("CrossPattern", _("Crossing horizontal and vertical lines"),
                #                      "crosspattern.png"),
                #                     ("BDiagPattern", _("Backward diagonal lines"), "bdiagpattern.png"),
                #                     ("FDiagPattern", _("Forward diagonal lines"), "fdiagpattern.png"),
                #                     ("DiagCrossPattern", _("Crossing diagonal lines"), "diagcrosspattern.png"),
                #                 #    ("LinearGradientPattern", _("Linear gradient (set using a dedicated QBrush constructor)"), "none.png"),
                #                 #    ("ConicalGradientPattern", _("Conical gradient (set using a dedicated QBrush constructor)"), "none.png"),
                #                 #    ("RadialGradientPattern", _("Radial gradient (set using a dedicated QBrush constructor)"), "none.png"),
                #                 #    ("TexturePattern", _("Custom pattern (see QBrush::setTexture())"), "none.png"),
                #                 ]
                rect = item.get_rect()
                sh = item.shape.shapeparam
                # if the area being slected is larger than max change color to
                # red
                qrect = self._restrict_rect_to_positive(rect)
                if(self.roi_limit_def):
                    qrect = self.roi_limit_def.check_limits(qrect)
                    #item.setTitle(self.roi_limit_def.get_label())
                    item.setTitle(self.roi_limit_def.get_label() + ': %d' % item.unique_id)

                    if(self.roi_limit_def.state == ROI_STATE_ALARM):
                        self.inputState.shape_outof_range = True
                    else:
                        self.inputState.shape_outof_range = False
                else:
                    self.inputState.shape_outof_range = False

                if(self.roi_limit_def):
                    item.shape.sel_brush.setStyle(
                        self.roi_limit_def.get_fill_pattern())
                    item.shape.sel_brush.setColor(
                        self.roi_limit_def.get_color())

                sh.update_param(item.shape)
                return(qrect)

    def force_shape_out_of_range(self, out_of_range=False):
        print(('imageWidget: force_shape_out_of_range: ', out_of_range))
        self.inputState.force_out_of_range = out_of_range

    def _emit_select_roi(self, img_type, cmnd=widget_com_cmnd_types.SELECT_ROI):
        """
        _emit_select_roi(): emit when a new ROI has been selected

        :param img_type: img_type description
        :type img_type: img_type type

        :param cmnd=widget_com_cmnd_types.ROI_CHANGED: cmnd=widget_com_cmnd_types.ROI_CHANGED description
        :type cmnd=widget_com_cmnd_types.ROI_CHANGED: cmnd=widget_com_cmnd_types.ROI_CHANGED type

        :returns: None
        """

        if(self.inputState.force_out_of_range or self.inputState.shape_outof_range):
            return

        # print 'emitting new roi' , self.inputState.plotitem_id
        dct = make_spatial_db_dict()
        dct_put(dct, WDGCOM_CMND, cmnd)
        #dct_put(dct, SPDB_SCAN_PLUGIN_ITEM_ID, self.inputState.plotitem_id)
        dct_put(dct, SPDB_PLOT_ITEM_ID, self.inputState.plotitem_id)
        dct_put(dct, SPDB_PLOT_ITEM_TITLE, self.inputState.plotitem_title)
        dct_put(dct, SPDB_PLOT_SHAPE_TYPE, self.inputState.plotitem_type)
        dct_put(dct, SPDB_PLOT_KEY_PRESSED, self.inputState.keyisPressed)
        dct_put(dct, SPDB_ID_VAL, self.inputState.plotitem_id)

        cntr = self.inputState.center
        rng = self.inputState.range
        rect = self.inputState.rect

        cx = cntr[0]
        cy = cntr[1]
        rx = rng[0]
        ry = rng[1]
        (x1, y1, x2, y2) = rect

        if(cntr is not None):
            dct_put(dct, SPDB_XCENTER, cx)
            dct_put(dct, SPDB_YCENTER, cy)
            dct_put(dct, SPDB_XSTART, x1)
            dct_put(dct, SPDB_YSTART, y1)
            dct_put(dct, SPDB_XSTOP, x2)
            dct_put(dct, SPDB_YSTOP, y2)

        else:
            return

        if(rx is not None):
            dct_put(dct, SPDB_XRANGE, abs(rx))
        else:
            dct_put(dct, SPDB_XRANGE, None)

        if(ry is not None):
            dct_put(dct, SPDB_YRANGE, abs(ry))
        else:
            dct_put(dct, SPDB_YRANGE, None)

        dct_put(dct, SPDB_ZRANGE, None)
        dct_put(dct, SPDB_PLOT_IMAGE_TYPE, img_type)

        # print 'emitting new roi: ', rect
        self.new_roi_center.emit(dct)

    def _emit_new_roi(self, img_type, cmnd=widget_com_cmnd_types.ROI_CHANGED):
        """
        _emit_new_roi(): description

        :param img_type: img_type description
        :type img_type: img_type type

        :param cmnd=widget_com_cmnd_types.ROI_CHANGED: cmnd=widget_com_cmnd_types.ROI_CHANGED description
        :type cmnd=widget_com_cmnd_types.ROI_CHANGED: cmnd=widget_com_cmnd_types.ROI_CHANGED type

        :returns: None
        """
        """
        emit a dict that represents all of the params that scans need
        this is so that we can use the same signal handling for configuring scans
        as well as dynamically configuring the center and range of a scan from the plotter
        """

        if (self.inputState.force_out_of_range or self.inputState.shape_outof_range):
            return

        #if((not is_unique_roi_id_in_list(self.inputState.plotitem_id)) and not(self.inputState.keyisPressed[Qt.Key_Alt]) and not(self.inputState.keyisPressed[Qt.Key_C])):
        if ((not is_unique_roi_id_in_list(self.inputState.plotitem_id)) and not (self.inputState.keyisPressed[Qt.Key_Alt])):
            #print '_emit_new_roi: oops: unique_id is not in master list, kicking out'
            #print 'self.inputState.keyisPressed' , dump_key_pressed(self.inputState.keyisPressed)
            return

        dct = make_spatial_db_dict()
        dct_put(dct, WDGCOM_CMND, cmnd)
        #dct_put(dct, SPDB_SCAN_PLUGIN_ITEM_ID, self.inputState.plotitem_id)
        dct_put(dct, SPDB_PLOT_ITEM_ID, self.inputState.plotitem_id)
        dct_put(dct, SPDB_PLOT_ITEM_TITLE, self.inputState.plotitem_title)
        dct_put(dct, SPDB_PLOT_SHAPE_TYPE, self.inputState.plotitem_type)
        dct_put(dct, SPDB_PLOT_KEY_PRESSED, self.inputState.keyisPressed)
        dct_put(dct, SPDB_ID_VAL, self.inputState.plotitem_id)

        cntr = self.inputState.center
        rng = self.inputState.range
        rect = self.inputState.rect

        cx = cntr[0]
        cy = cntr[1]
        rx = rng[0]
        ry = rng[1]
        (x1, y1, x2, y2) = rect
        #print '_emit_new_roi: emitting new roi center ', (cx,cy)


        if(self.inputState.plotitem_id is not None):
            #print '_emit_new_roi: sp_id=%d cx=%.2f cy=%.2f' % (self.inputState.plotitem_id, cx, cy)
            pass

        if(cntr is not None):
            if (self.image_type in [types.image_types.FOCUS, types.image_types.OSAFOCUS]):
            # this is a focus scan so Y is actually the ZP Z axis so copy Y to Z
                dct_put(dct, SPDB_XCENTER, cx)
                dct_put(dct, SPDB_ZZCENTER, cy)
                dct_put(dct, SPDB_YCENTER, None)
                dct_put(dct, SPDB_XSTART, x1)
                dct_put(dct, SPDB_ZZSTART, y1)
                dct_put(dct, SPDB_YSTART, None)
                dct_put(dct, SPDB_XSTOP, x2)
                dct_put(dct, SPDB_ZZSTOP, y2)
                dct_put(dct, SPDB_YSTOP, None)
            else:
                dct_put(dct, SPDB_XCENTER, cx)
                dct_put(dct, SPDB_YCENTER, cy)
                dct_put(dct, SPDB_XSTART, x1)
                dct_put(dct, SPDB_YSTART, y1)
                dct_put(dct, SPDB_XSTOP, x2)
                dct_put(dct, SPDB_YSTOP, y2)

        if(rx is not None):
            dct_put(dct, SPDB_XRANGE, abs(rx))
        else:
            dct_put(dct, SPDB_XRANGE, None)

        if(ry is not None):
            if (self.image_type in [types.image_types.FOCUS, types.image_types.OSAFOCUS]):
                # this is a focus scan so Y is actually the ZP Z axis so copy Y to Z
                dct_put(dct, SPDB_ZZRANGE, abs(ry))
            else:
                dct_put(dct, SPDB_YRANGE, abs(ry))
        else:
            dct_put(dct, SPDB_YRANGE, None)

        #dct_put(dct, SPDB_ZRANGE, None)
        dct_put(dct, SPDB_PLOT_IMAGE_TYPE, img_type)

        #print('emitting new roi: ', rect)
        self.new_roi_center.emit(dct)

    def on_update_region(self, data):
        """
        on_update_region(): description

        :param data: data description
        :type data: data type

        :returns: None
        """
        # print 'stxmImageWidget: on_update_region'
        # print data
        pass

    def set_cs_label_text(self, cs, msg):
        """
        set_cs_label_text(): description

        :param cs: cs description
        :type cs: cs type

        :param msg: msg description
        :type msg: msg type

        :returns: None
        """
        label = self.get_cs_label_item(cs)
        if(label):
            label.set_text(msg)
        else:
            label = make.label(_(msg), "TL", (0, 0), "TL")
            cs.cs_plot.add_item(label, z=999999999)
        cs.cs_plot.update_plot()

    def get_cs_label_item(self, cs):
        """
        get_cs_label_item(): description

        :param cs: cs description
        :type cs: cs type

        :returns: None
        """
        items = cs.cs_plot.get_items()
        for item in items:
            if(isinstance(item, LabelItem)):
                if(item.isVisible()):
                    return(item)
        return(None)

    def get_cs_item(self, cs):
        """
        get_cs_item(): description

        :param cs: cs description
        :type cs: cs type

        :returns: None
        """
        e = enumerate(cs.cs_plot.known_items.items())
        # if(len(e) > 0):
        for d in e:
            #d = e.next()
            #(0, (<guiqwt.image.ImageItem object at 0x053CB030>, <guiqwt.cross_section.XCrossSectionItem object at 0x05C8C660>))
            csi = d[1][1]
            #<guiqwt.cross_section.XCrossSectionItem object at 0x05C8C660>
            return(csi)
        # or if there are any then
        return(None)

    def dump_cross_section_panels(self, x, y):
        """
        dump_cross_section_panels(): description

        :param x: x description
        :type x: x type

        :param y: y description
        :type y: y type

        :returns: None
        """
        xcs = self.get_xcs_panel()
        ycs = self.get_ycs_panel()

        xcsi = self.get_cs_item(xcs)
        ycsi = self.get_cs_item(ycs)

        if(xcsi is not None):
            datx = xcsi._y
        if(ycsi is not None):
            daty = ycsi._x

    def marker_changed(self, marker):
        """
        marker_changed(): description
        if I leave this func emitting a new_roi when the alt key is held down then when I am trying to look at an image and
        only update the cross field plots I will also be updating the centerX/Y of the scan which I dont want to do.
        so for now I am leaving it as pass

        :param marker: marker description
        :type marker: marker type

        :returns: None
        """
        pass
        # cntr = marker.get_pos()
        # self.inputState.center = (cntr[0], cntr[1])
        # self.inputState.range = (0, 0)
        # self.inputState.npts = (None , None)
        # self.inputState.rect = (cntr[0], cntr[1], 0, 0)
        # self.inputState.plotitem_type = None
        #
        # if(self.inputState.keyisPressed[Qt.Key_Alt]):
        #     #if Alt key is pressed then this is not a segment or something else so make sure the
        #     # flag that plotitem_type is reset to None
        #     self._emit_new_roi(self.image_type)

    def _centersize_to_rect(self, _center, _size):
        """
        _centersize_to_rect(): description

        :param _center: _center description
        :type _center: _center type

        :param _size: _size description
        :type _size: _size type

        :returns: None
        """
        """ center and size are in units (um) """
        centX, centY = _center
        szX, szY = _size

        startX = centX - (szX * 0.5)    # Left
        stopX = centX + (szX * 0.5)     # Right
        startY = centY + (szY * 0.5)    # Top
        stopY = centY - (szY * 0.5)        # Bottom
        #print (startX, stopX, startY, stopY)
        return((startX, startY, stopX, stopY))

    def _handle_final_rect_shape(self, shape):
        """
        _handle_final_rect_shape(): description

        :param shape: shape description
        :type shape: shape type

        :returns: None
        """
        roi = types.spatial_type_prefix.ROI
        shape.setTitle('%s %d' % (types.spatial_type_prefix[roi], shape.shapeNum))
        shape.annotationparam.title = '%s %d' % (
            types.spatial_type_prefix[roi], shape.shapeNum)
        if(self.checkRegionEnabled):
            rect = self._check_valid_region(shape)
        shape.position_and_size_visible = False
#         shape.setItemAttribute(Qwt.QwtPlotItem.Legend)
#         widget = self.plot.legend().find(shape)
#         if isinstance(widget, Qwt.QwtLegendItem):
#             widget.setChecked(True)

        ret = self._anno_spatial_to_region(shape, set_id=True)
        self.new_region.emit(ret)

        cur_shapes = self.getShapeItemsByShapeType(AnnotatedRectangle)
        if((not self.multi_region_enabled) and (len(cur_shapes) > 0)):
            self.enable_tool_by_name('clsAverageCrossSectionTool', False)
        else:
            self.enable_tool_by_name('clsAverageCrossSectionTool', True)

    def _create_rect_shape(self):
        """
        _create_rect_shape(): description

        :returns: None
        """
        # print '_create_rect_shape:'
        #items = cs.cs_plot.get_items()
        # for item in items:
        #    if(isinstance(item, LabelItem)):
        ap = AnnotationParam()
        #ap.subtitle = 'my _create_rect_shape'
        #ap.title = 'selecting'
        #ap.title = '%s %d' % (SPATIAL_TYPE_PREFIX[TWO_D], self.roiNum)
        ap.transform_matrix = [[self.xstep, 0.0, 0.0],
                               [0.0, self.ystep, 0.0], [0.0, 0.0, 1.0]]
        ap.format = '%5.2f um'
        return AnnotatedRectangle(0, 0, 1, 1, annotationparam=ap), 0, 2

    def _get_seg_anno_params(self):
        """
        _get_seg_anno_params(): description

        :returns: None
        """
        title = '%s %d' % (types.spatial_type_prefix.SEG, self.segNum)
        #title = 'selecting'
        transform_matrix = [[self.xstep, 0.0, 0.0],
                            [0.0, self.ystep, 0.0], [0.0, 0.0, 1.0]]
        format = '%5.2f um'
        return(title, transform_matrix, format)

    def _create_seg_shape(self):
        """
        _create_seg_shape(): description

        :returns: None
        """
        """ this is called when the user lets go of the left mouse button at teh end if the drag """
        # print '_create_seg_shape:'
        ap = AnnotationParam()
        ap.title = '%s %d' % (types.spatial_type_prefix.SEG, self.segNum)
        #ap.title = 'selecting'
        ap.transform_matrix = [[self.xstep, 0.0, 0.0],
                               [0.0, self.ystep, 0.0], [0.0, 0.0, 1.0]]
        ap.format = '%5.2f um'
        return AnnotatedSegment(0, 0, 1, 1, annotationparam=ap), 0, 2

    def _create_point_shape(self):
        """
        _create_point_shape(): description

        :returns: None
        """
        # print '_create_point_shape:'
        ap = AnnotationParam()
        ap.title = '%s %d' % (types.spatial_type_prefix.PNT, self.shapeNum)
        #ap.title = 'selecting:'
        ap.transform_matrix = [[self.xstep, 0.0, 0.0],
                               [0.0, self.ystep, 0.0], [0.0, 0.0, 1.0]]
        ap.format = '%5.2f um'
        return AnnotatedPoint(0, 0, annotationparam=ap), 0, 0

    def _pretty(self, d, indent=1):
        """
        _pretty(): description

        :param d: d description
        :type d: d type

        :param indent=1: indent=1 description
        :type indent=1: indent=1 type

        :returns: None
        """
        for key, value in d.items():
            print('\t' * indent + str(key))
            if isinstance(value, dict):
                self._pretty(value, indent + 1)
            else:
                print('\t' * (indent + 1) + str(value))

    def initData(self, image_type, rows, cols, parms={}):
        """
        initData(): description

        :param image_type: image_type description
        :type image_type: image_type type

        :param rows: rows description
        :type rows: rows type

        :param cols: cols description
        :type cols: cols type

        :param parms={}: parms={} description
        :type parms={}: parms={} type

        :returns: None
        """
        # clear title
        #print('ImageWidget: initData called, rows=%d, cols=%d' % (rows, cols))

        plot = self.get_plot()
        plot.set_title('')
        # clear any shapes
        self.delShapePlotItems()
        # scalars for non-square data
        self.htSc = 1
        self.widthSc = 1
        items = len(self.plot.get_items(item_type=ICSImageItemType))
        array = np.empty((int(rows), int(cols)))
        array[:] = np.NAN
        array[0][0] = 0


        self.data = array
        self.image_type = image_type

        # if it is a focus image I dont want any of the tools screweing up the
        # scan params so disable them
        if(self.image_type in [types.image_types.FOCUS, types.image_types.OSAFOCUS]):
            self.enable_tools_by_spatial_type(None)

        [self.dataHeight, self.dataWidth] = self.data.shape
        self.wPtr = 0
        self.hPtr = 0
        if(self.item is None):
            #self.item = make.image(self.data, interpolation='linear',colormap='gist_gray')
            #self.item = make.image(self.data, title='', interpolation='linear')
            self.item = make.image(self.data, title='', interpolation='nearest', colormap='gist_gray')
            #self.item = make.image(self.data, interpolation='nearest', colormap='gist_gray')
            if(self.image_type == types.image_types.LINE_PLOT):
                plot.add_item(self.item, z=items+1, autoscale=False)
            else:
                plot.add_item(self.item, z=items+1)
            #plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)

        if('selectable' in list(parms.keys())):
            self.item.set_selectable(parms['selectable'])

        #self.set_image_parameters(self.item, parms['xmin'], parms['xmax'], parms['ymin'], parms['ymax'])
        (x1, y1, x2, y2) = parms['RECT']
        self.set_image_parameters(self.item, x1, y1, x2, y2)
#        self.set_center_at_XY(((x1 + x2) * 0.5, (y1 + y2) * 0.5), ((x2 - x1), (y1 - y2)))
        #self.show_data(self.data, True)
        # self.set_autoscale()
        self.image_is_new = True

        return(self.data.shape)


    def clear_data(self, image_type, rows, cols):
        """
        clear_data(): description

        :param image_type: image_type description
        :type image_type: image_type type

        :param rows: rows description
        :type rows: rows type

        :param cols: cols description
        :type cols: cols type

        :returns: None
        """
        array = np.ones((rows, cols), dtype=np.int32)
        self.data = self._makeSquareDataArray(array)
        if(self.item is None):
            #self.item = make.image(self.data, interpolation='linear',colormap='gist_gray')
            self.item = make.image(
                self.data,
                interpolation='nearest',
                colormap='gist_gray')
        self.item.load_file_data(self.data)

    def _makeSquareDataArray(self, array):
        """
        _makeSquareDataArray(): description

        :param array: array description
        :type array: array type

        :returns: None
        """
        ''' for display purposes it's easiest to have the data square so repeat
        pixels in the lesser demension, as well make sure that the demensions are 32 bit aligned
        '''
        h, w = array.shape

        if(h != w):
            if(h < w):
                # scale Height and width to something divisible by for (32 bit
                # aligned)
                self.widthSc, self.htSc = nextFactor(w, h)
                newArray = np.repeat(
                    np.repeat(
                        array,
                        self.htSc,
                        axis=0),
                    self.widthSc,
                    axis=1)
            else:
                self.htSc, self.widthSc = nextFactor(h, w)
                newArray = np.repeat(
                    np.repeat(
                        array,
                        self.htSc,
                        axis=0),
                    self.widthSc,
                    axis=1)
        else:
            newArray = array

        # print '_makeSquareDataArray: shape='
        # print newArray.shape
        return newArray

    def _convSampleToDisplay(self, x, y):
        """
        _convSampleToDisplay(): description

        :param x: x description
        :type x: x type

        :param y: y description
        :type y: y type

        :returns: None
        """
        """remember this is a 2d array array[row][column] so it is [array[y][x]
           so that it will display the data from bottom/up left to right
        """
        h, w = self.data.shape
        xscaler = self.widthSc
        yscaler = self.htSc
#         #convert
        rowStart = int((self.dataHeight - 0) + (y * yscaler)) - (h / 2.0)
        colStart = int(x * xscaler) - (w / 2.0)
        rowStop = int(rowStart - self.zoom_scale)
        colStop = int(colStart + self.zoom_scale)

        return(colStart, colStop, rowStart, rowStop)

    def showData(self):
        """
        showData(): description

        :returns: None
        """
        self.show_data(self.data)

    def addData(self, x, y, val, show=False):
        """
        addData(): description

        :param x: x description
        :type x: x type

        :param y: y description
        :type y: y type

        :param val: val description
        :type val: val type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new point to the 2d array
        kept around for backward compatability but new calls should use addPoint()
        '''
        if(not self.dataAtMax):

            # remember this is a 2d array array[row][column] so it is [array[y][x]
            # so that it will display the data from bottom/up left to right
            (colStart, colStop, rowStart, rowStop) = self._convSampleToDisplay(x, y)
            # print 'adding (%d,%d,%d,%d) = %d' % (colStart, colStop, rowStart, rowStop,val)
            # scal data
            #self.data[rowStop:rowStart, colStart:colStop] = copy.deepcopy(val)
            self.data[rowStop:rowStart, colStart:colStop] = val

            if(show):
                self.show_data(self.data)

    def addPixel(self, x, y, val, pixel_size=50, show=False):
        """
        addPoint(): description

        :param y: y description
        :type y: y type

        :param x: x description
        :type x: x type

        :param val: val description
        :type val: val type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new point to the 2d array
        '''
        # if(not self.dataAtMax):
        if(self.data is not None):
            rows, cols = self.data.shape
            if(y < rows):
                # remember this is a 2d array array[row][column] so it is [array[y][x]
                # so that it will display the data from bottom/up left to right
                #(colStart, colStop, rowStart, rowStop) = self._convSampleToDisplay( x, y)
                #self.data[rowStop:rowStart , colStart:colStop] = copy.deepcopy(val)
                #self.data[y , x] = copy.deepcopy(val)
                h, w = self.data.shape
                arr_cy = h / 2
                arr_cx = w / 2

                arr_x = arr_cx + x
                arr_y = arr_cy + y

                x1 = arr_x - (pixel_size * 0.5)
                x2 = arr_x + (pixel_size * 0.5)
                y1 = arr_y - (pixel_size * 0.5)
                y2 = arr_y + (pixel_size * 0.5)

                self.data[y1:y2, x1:x2] = val

            if(show):
                self.show_data(self.data)

    def addPoint(self, y, x, val, show=False):
        """
        addPoint(): description

        :param y: y description
        :type y: y type

        :param x: x description
        :type x: x type

        :param val: val description
        :type val: val type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new point to the 2d array
        '''
        # if(not self.dataAtMax):
        if(self.data is not None):
            rows, cols = self.data.shape
            if ((y < rows) and (x < cols)):
                # remember this is a 2d array array[row][column] so it is [array[y][x]
                # so that it will display the data from bottom/up left to right
                #(colStart, colStop, rowStart, rowStop) = self._convSampleToDisplay( x, y)
                # print 'adding (%d,%d,%d,%d) = %d' % (colStart, colStop, rowStart, rowStop,val)
                # scal data
                #self.data[rowStop:rowStart , colStart:colStop] = copy.deepcopy(val)
                #self.data[y, x] = copy.deepcopy(val)
                self.data[y, x] = val

            if(show):
                self.show_data(self.data)

    def addLine(self, startx, row, line, show=False):
        """
        addLine(): description

        :param startx: startx description
        :type startx: startx type

        :param row: row description
        :type row: row type

        :param line: line description
        :type line: line type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new line to the 2d array
        '''
        # print 'addLine: row=%d' % row
        # print 'addLine: data length = %d vals' % len(line)
        if((self.image_is_new)):
            self.image_is_new = False
            if(row != 0):
                return
        # this is a catch for a spurious previsou row being sent
        # at the start of a scan, fix this sometime

        # print 'row=%d' % row
        if(self.data is not None):
            rows, cols = self.data.shape
            if(cols != len(line)):
                line = np.resize(line, (cols,))

            if(row >= rows):
                row = rows - 1

            #AUG16 self.data[row, :] = copy.deepcopy(line)
            self.data[row, :] = line
            if(show):
                self.show_data(self.data)
        else:
            _logger.error('stxmImageWidget: addLine: self.data is None')

    def addVerticalLine(self, col, line, show=False):
        """
        addVerticalLine(): description

        :param col: column description
        :type col: col type

        :param line: line description
        :type line: line type

        :param show=False: show=False description
        :type show=False: show=False type

        :returns: None
        """
        ''' this function adds a new vertical line to the 2d array
        '''
        # print 'addLine: row=%d' % row
        # print 'addLine: data length = %d vals' % len(line)
        if((self.image_is_new)):
            self.image_is_new = False
            if(col != 0):
                return
        # this is a catch for a spurious previsou row being sent
        # at the start of a scan, fix this sometime

        # print 'row=%d' % row
        if(self.data is not None):
            rows, cols = self.data.shape
            # if(cols != len(line)):
            #    line = np.resize(line, (cols,))

            if(col >= cols):
                col = cols - 1

            #self.data[:, col] = copy.deepcopy(line)
            self.data[:, col] = line[0:rows]
            if(show):
                self.show_data(self.data)
        else:
            _logger.error(
                'stxmImageWidget: addVerticalLine: self.data is None')

    def load_file_data(self, fileName, data):
        """
        load_file_data(): description

        :param fileName: fileName description
        :type fileName: fileName type

        :param data: data description
        :type data: data type

        :returns: None
        """
        self.fileName = fileName
        self.data = data
        # self.show_data(self.data)
        if(self.filtVal > 0):
            self.apply_filter(self.filtVal)
        else:
            self.show_data(self.data)

    def set_data(self, data):
        """
        set_data(): description

        :param data: data description
        :type data: data type

        :returns: None
        """
        if(data.size is 0):
            return
        self.data = data
        # self.show_data(self.data)
        if(self.filtVal > 0):
            self.apply_filter(self.filtVal)
        else:
            self.show_data(self.data)
        self.set_autoscale()

    def set_autoscale(self, fill_plot_window=False):
        """
        set_autoscale(): description

        :param fill_plot_window=False: fill_plot_window=False description
        :type fill_plot_window=False: fill_plot_window=False type

        :returns: None
        """
        plot = self.get_plot()
        if(fill_plot_window):
            # unlock so that an autoscale will work
            self.set_lock_aspect_ratio(False)
            plot.do_autoscale()
            # lock it again
            self.set_lock_aspect_ratio(True)
        else:
            self.set_lock_aspect_ratio(True)
            plot.do_autoscale()

    def show_data(self, data, init=False):
        """
        show_data(): description

        :param data: data description
        :type data: data type

        :param init=False: init=False description
        :type init=False: init=False type

        :returns: None
        """
        if(data.size is 0):
            return
        plot = self.get_plot()
        items = len(self.plot.get_items(item_type=ICSImageItemType))
        if(self.item is None):
            #self.item = make.image(data, colormap="gist_gray")
            #self.item = make.image(data)
            #self.item = make.image(self.data, interpolation='linear', colormap='gist_gray')
            self.item = make.image(
                self.data,
                interpolation='nearest',
                colormap='gist_gray')
            # self.item.set_lut_range([1,3000])
            plot.add_item(self.item, z=items+1)
            #plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
        else:
            # self.item.set_data(data)
            # retain the current contrast tools values and pass them to
            # set_data
            if(self._auto_contrast):
                self.item.set_data(data)
            else:
                lut_range = self.item.get_lut_range()
                self.item.set_data(data, lut_range)
        plot.replot()

    def apply_filter(self, val):
        """
        apply_filter(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        if(val):
            # apply filter
            data = self.filterfunc(self.data, val)
        else:
            # no filter just display raw
            data = self.data
        self.filtVal = val
        self.show_data(data)

    def setCurFilter(self, filtName):
        """
        setCurFilter(): description

        :param filtName: filtName description
        :type filtName: filtName type

        :returns: None
        """
        self.curFilterStr = filtName
        # print 'setCurFilter: filter changed to %s' % self.curFilterStr
        self.curFilterStr = str(filtName)
        self.filterfunc = getattr(scipy.ndimage, self.curFilterStr)
        self.apply_filter(self.filtVal)
        self.get_xcs_panel().update_plot()
        self.get_ycs_panel().update_plot()

    def deselect_all_shapes(self):
        items = self.plot.get_items(item_type=IShapeItemType)
        for item in items:
            item.unselect()
        self.plot.replot()

    def enable_all_shape_labels(self, do=True):
        items = self.plot.get_items(item_type=IShapeItemType)

        for item in items:
            item.unselect()
            if(hasattr(item, "is_label_visible")):
                if(do):
                    item.set_label_visible(True)
                else:
                    item.set_label_visible(False)
            self.plot.replot()
        return

    def mousePressEvent(self, ev):
        """
        mousePressEvent(): description

        :param ev: ev description
        :type ev: ev type

        :returns: None
        """
        # print 'ImageWidget: mouse pressed'
        btn = ev.button()
        self.inputState.btnisPressed[btn] = True
        if btn == Qt.LeftButton:
            # print 'left mouse button pressed'
            # check to see if the user is using one of the selection tools, if so
            # then set the name of the active plot item, if you can
            tool = self.plot.manager.get_active_tool()
            if(isinstance(tool, AverageCrossSectionTool)):
                # print 'Average selection tool selected'
                self.roiNum = tool.shapeNum
            elif(isinstance(tool, AnnotatedSegmentTool)):
                # print 'AnnotatedSegmentTool tool selected'
                if(hasattr(tool, 'shapeNum')):
                    self.segNum = tool.shapeNum
            elif(isinstance(tool, AnnotatedPointTool)):
                # print 'AnnotatedPointTool tool selected'
                self.shapeNum = tool.shapeNum

            plot = self.get_plot()
            #pan = plot.get_itemlist_panel()
            # get all the shapes and turn off their size texts
            active_item = plot.get_active_item()
            if(active_item is not None):

                if(hasattr(active_item, 'unique_id')):
                    title = str(active_item.title().text())

                    if(title.find('ROI') > -1):
                        self.inputState.plotitem_type = types.spatial_type_prefix.ROI
                        ret = self._anno_spatial_to_region(active_item)

                    elif(title.find('SEG') > -1):
                        self.inputState.plotitem_type = types.spatial_type_prefix.SEG
                        ret = self._anno_seg_to_region(active_item)

                    elif(title.find('PNT') > -1):
                        self.inputState.plotitem_type = types.spatial_type_prefix.PNT
                        ret = self._anno_point_to_region(active_item)

                    else:
                        # dont do anything
                        return

                    self.inputState.plotitem_id = active_item.unique_id
                    self.inputState.plotitem_title = title
                    self.inputState.plotitem_shape = active_item
                    self.inputState.center = ret['center']
                    self.inputState.range = ret['range']
                    self.inputState.rect = ret['rect']
                    self.inputState.npts = (None, None)
                    # , cmnd=widget_com_cmnd_types.ADD_ROI)
                    #print 'mousePressEvent: emitting_new_roi with cmnd = SELECT_ROI'
                    self._emit_new_roi(
                        self.image_type, cmnd=widget_com_cmnd_types.SELECT_ROI)
            else:
                self.inputState.reset()

        elif btn == Qt.MiddleButton:
            # if user has spacebar pressed and they press the middle button then
            # emit a new_roi_center so that scan params can be updated
            #if(self.inputState.keyisPressed[Qt.Key_F1]):
            #    self._emit_new_roi(self.image_type)
            #    return
            pass

    def mouseReleaseEvent(self, ev):
        """
        mouseReleaseEvent(): description

        :param ev: ev description
        :type ev: ev type

        :returns: None
        """
        # print 'ImageWidget: mouse released'
        pass
        # btn = ev.button()
        # self.inputState.btnisPressed[btn] = False
        #
        # if btn == Qt.LeftButton:
        #     # print 'mouse release event'
        #     plot = self.get_plot()
        #     # get all the shapes and turn off their size texts
        #     active_item = plot.get_active_item()
        #     if(active_item is not None):
        #         title = str(active_item.title().text())
        #         # print title
        #         if(hasattr(active_item, 'unique_id')):
        #
        #             if(title.find('ROI') > -1):
        #                 self.inputState.plotitem_type = types.spatial_type_prefix.ROI
        #                 ret = self._anno_spatial_to_region(active_item)
        #
        #             elif(title.find('SEG') > -1):
        #                 self.inputState.plotitem_type = types.spatial_type_prefix.SEG
        #                 ret = self._anno_seg_to_region(active_item)
        #
        #             elif(title.find('PNT') > -1):
        #                 self.inputState.plotitem_type = types.spatial_type_prefix.PNT
        #                 ret = self._anno_point_to_region(active_item)
        #             else:
        #                 # dont do anything
        #                 return
        #
        #             self.inputState.plotitem_id = active_item.unique_id
        #             self.inputState.plotitem_title = title
        #             self.inputState.center = ret['center']
        #             self.inputState.range = ret['range']
        #             self.inputState.rect = ret['rect']
        #             self.inputState.npts = (None, None)
        #             # , cmnd=widget_com_cmnd_types.ADD_ROI)
        #             self._emit_new_roi(
        #                 self.image_type, cmnd=widget_com_cmnd_types.SELECT_ROI)
        #     # print 'active_item: ', active_item
        #     items = self.plot.get_items(item_type=IShapeItemType)
        #     for item in items:
        #         #
        #         # if teh user has deselected this plot item then hide its label
        #         if(hasattr(item, "is_label_visible")):
        #             if item.is_label_visible() and (item != active_item):
        #                 item.set_label_visible(False)
        #                 item.unselect()
        #             elif item.is_label_visible() and (item == active_item):
        #                 item.set_label_visible(True)
        #             else:
        #                 pass
        #                 #item.position_and_size_visible = False
        #                 # pass
        #     self.plot.replot()
        #     return

    # note: these handlers are using Qt4.5 syntax, it changes in Qt4.8.3
    def mouseMoveEvent(self, ev):
        """
        mouseMoveEvent(): description

        :param ev: ev description
        :type ev: ev type

        :returns: None
        """
        # print 'mouseMoveEvent', ev
        btn = ev.button()
        # self.inputState.btnisPressed[btn]
        if btn == Qt.MidButton:
            #print 'ImageWidget: mouse moved with middle button pressed'
            return
        elif btn == Qt.LeftButton:
            #print 'ImageWidget: mouse moved with left button pressed'
            # self.manager.update_cross_sections()
            pass

            return
        elif btn == Qt.RightButton:
            # print 'ImageWidget: mouse moved with right button pressed'
            return

    def wheelEvent(self, event):
        """
        wheelEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        incr = 5
        do_emit = False
        delta = event.angleDelta().y()
        if(delta > 0):
            dir = 1
        else:
            dir = -1

        (cx, cy) = self.inputState.center
        (rx, ry) = self.inputState.range
        (nx, ny) = self.inputState.npts

        if(self.inputState.keyisPressed[Qt.Key_X]):
            nx = (incr * dir)
#            do_emit = True
        else:
            nx = 0

        if(self.inputState.keyisPressed[Qt.Key_Y]):
            ny = (incr * dir)
#            do_emit = True
        else:
            ny = 0
        # print 'wheelEvent: nx,ny (%d, %d)' % (nx, ny)
        self.inputState.center = (cx, cy)
        self.inputState.range = (rx, ry)
        self.inputState.npts = (nx, ny)
        x1 = cx - (0.5 * rx)
        x2 = cx + (0.5 * rx)
        y1 = cy - (0.5 * ry)
        y2 = cy + (0.5 * ry)
        self.inputState.rect = (x1, y1, x2, y2)
        #dct = {}
        #dct['IMAGE_TYPE'] = self.image_type
        #dct[CENTER] = self.inputState.center
        #dct[RANGE] = self.inputState.range
        #dct[NPOINTS] = self.inputState.npts

        # only emit a new region if an x or y key is pressed
        if(do_emit):
            # if(not self.inputStatekey.isPressed[Qt.Key_Alt]):
            # self.new_roi_center.emit(dct)
            self._emit_new_roi(self.image_type)

        # reset the delta points
        self.inputState.npts = (0, 0)

    def keyPressEvent(self, event):
        """
        keyPressEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        key = event.key()
        if(event.isAutoRepeat()):
            event.ignore()
            return
        if key == Qt.Key_Delete:
            item = self.plot.get_active_item()
            if item:
                # self.delPlotItem(item)
                self.delShapePlotItem(item)
                cur_shapes = self.getShapeItemsByShapeType(item)
                if((self.multi_region_enabled) or (len(cur_shapes) == 0)):
                    if(hasattr(item, 'unique_id')):
                        # its a tool used to select a egion of interest
                        # if not then it is a different type of shapeItem that
                        # is NOT used to select regions of interest so dont do anything with it
                        #self.enable_tools_by_shape_type(item, True)
                        self.enable_tools_by_shape_instance(item, True)
                        # it will only require a singal to any other widget listening if
                        # it was a region of interest (has a unique_id attrib)
                        self._emit_new_roi(
                            None, cmnd=widget_com_cmnd_types.DEL_ROI)


        if(key not in list(self.inputState.keyisPressed.keys())):
            print('keyPressedEvent: key [%d] not in self.inputState.keyisPressed.keys(), ignoring' % key)
            event.ignore()
            return

        self.inputState.keyisPressed[key] = True
        # print 'key pressed', self.inputState.keyisPressed
#         if key == Qt.Key_Delete:
#             item = self.plot.get_active_item()
#             if item:
#                 self.delPlotItem(item)
#                print 'deleting %s'  % item.title().text()
#                self.plot.del_item(item)
#                self.plot.replot()
#
#        if key == QtCore.Qt.Key_Up:
#            self.centerNode.moveBy(0, -20)
#        elif key == QtCore.Qt.Key_Down:
#            self.centerNode.moveBy(0, 20)
#        elif key == QtCore.Qt.Key_Left:
#            self.centerNode.moveBy(-20, 0)
#        elif key == QtCore.Qt.Key_Right:
#            self.centerNode.moveBy(20, 0)
#        elif key == QtCore.Qt.Key_Plus:
#            self.scaleView(1.2)
#        elif key == QtCore.Qt.Key_Minus:
#            self.scaleView(1 / 1.2)
#        elif key == QtCore.Qt.Key_Space or key == QtCore.Qt.Key_Enter:
#            for item in self.scene().items():
#                if isinstance(item, Node):
#                    item.setPos(-150 + QtCore.qrand() % 300, -150 + QtCore.qrand() % 300)
#        else:
#            super(GraphWidget, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        keyReleaseEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        key = event.key()
        if(key == Qt.Key_C):
            self.selectTool.s.allow_parm_update = False


        if(event.isAutoRepeat()):
            event.ignore()
            return
        if(key not in list(self.inputState.keyisPressed.keys())):
            event.ignore()
            return

        self.inputState.keyisPressed[key] = False
        # print 'key released', self.inputState.keyisPressed

    def addShapePlotItemCENTER(
            self,
            item_id,
            cntr,
            rng,
            item_type=types.spatial_type_prefix.ROI):
        """
        addShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param cntr: cntr description
        :type cntr: cntr type

        :param rng: rng description
        :type rng: rng type

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :returns: None
        """
        # make sure item is 'selected'
        startx = cntr[0] - (0.5 * rng[0])
        starty = cntr[1] - (0.5 * rng[1])
        item = self.getShapePlotItem(item_id, item_type)
        # create one
        if(item_type == types.spatial_type_prefix.ROI):
            roi = types.spatial_type_prefix.ROI
            title = types.spatial_type_prefix[roi] + ' %d' % item_id
            item = make.annotated_rectangle(
                startx, starty, startx + rng[0], starty + rng[1], title=title)
            item.shape_id = item_id
            item.unique_id = item_id
            #(item,a,b) = tools.clsAverageCrossSectionTool(self.plot.manager).create_shape()
            #item.shape_id = 0
            #item.unique_id = item_id

        elif(item_type == types.spatial_type_prefix.SEG):
            seg = types.spatial_type_prefix.SEG
            title = types.spatial_type_prefix[seg] + ' %d' % item_id
            item = make.annotated_horiz_segment(
                startx, starty, startx + rng[0], starty, title=item_id)
            #(item,a,b) = tools.HLineSegmentTool(self.plot.manager).create_shape()
            #item.shape_id = 0
            #item.unique_id = item_id

        else:
            # assume PNT type
            startx = cntr[0]
            starty = cntr[1]
            pnt = types.spatial_type_prefix.PNT
            title = types.spatial_type_prefix[pnt] + ' %d' % item_id
            item = make.annotated_point(startx, starty, title=title)
            #(item,a,b) = tools.clsPointTool(self.plot.manager).create_shape()
            #item.shape_id = 0
            #item.unique_id = item_id

        # signal to anyone listening that we are adding this item
        #print 'addShapePlotItemCENTER: emitting_new_roi with cmnd=ADD_ROI'
        self._emit_new_roi(
            None,
            cntr,
            rng,
            None,
            cmnd=widget_com_cmnd_types.ADD_ROI)

        self.plot.add_item(item, z=999999999)
        item.invalidate_plot()
        self.plot.replot()

    def addShapePlotItem(
            self,
            item_id,
            rect,
            item_type=types.spatial_type_prefix.ROI,
            re_center=False,
            show_anno=True):
        """
        addShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param rect: cntr description
        :type rect: tuple representing the corners of a rect (x1, y1, x2, y2)

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :returns: None
        """
        # make sure item is 'selected'
        (x1, y1, x2, y2) = rect

        #(x1, y1, x2, y2) = self._limit_rect(rect)

        # print 'addShapePlotItem: item_id = %d' % item_id
        # print 'addShapePlotItem: rect = ' , rect
        item = self.getShapePlotItem(item_id, item_type)
        # create one
        if(item_type == types.spatial_type_prefix.ROI):
            roi = types.spatial_type_prefix.ROI
            self.roiNum += 1
            #title = types.spatial_type_prefix[roi] + ' %d' % self.roiNum
            title = types.spatial_type_prefix[roi] + ' %d' % item_id
            if(show_anno):
                item = make.annotated_rectangle(x1, y1, x2, y2, title=title)
            else:
                item = make.rectangle(x1, y1, x2, y2, title=title)
            item.shape_id = item_id
            item.unique_id = item_id
            item.max_range = (None, None)

        elif(item_type == types.spatial_type_prefix.SEG):
            seg = types.spatial_type_prefix.SEG
            self.segNum += 1
            #title = types.spatial_type_prefix[seg] + ' %d' % self.segNum
            title = types.spatial_type_prefix[seg] + ' %d' % item_id
            if (show_anno):
                item = make.annotated_segment(x1, y1, x2, y2, title=title)
            else:
                item = make.segment(x1, y1, x2, y2, title=title)
            item.shape_id = item_id
            item.unique_id = item_id
            item.max_range = (None, None)

        else:
            # assume PNT type
            pnt = types.spatial_type_prefix.PNT
            self.pntNum += 1
            #title = types.spatial_type_prefix[pnt] + ' %d' % self.pntNum
            title = types.spatial_type_prefix[pnt] + ' %d' % item_id
            if (show_anno):
                item = make.annotated_point(x1, y1, title=title)
            else:
                item = make.point(x1, y1, title=title)
            item.set_pos(x1, y1)
            item.shape_id = item_id
            item.unique_id = item_id
            item.max_range = (None, None)

        self.plot.add_item(item, z=999999999)

        if(re_center):
            if(item_type == types.spatial_type_prefix.PNT):
                self.set_center_at_XY((x1, y1), (50, 50))
            else:
                self.set_center_at_XY(
                    ((x1 + x2) * 0.5, (y1 + y2) * 0.5), ((x2 - x1), (y1 - y2)))

        item.invalidate_plot()
        self.plot.replot()

    def recenter_plot_to_all_items(self):
        items = self.getShapeItems()

        x1_lst = []
        x2_lst = []
        y1_lst = []
        y2_lst = []
        xc = None
        yc = None
        for item in items:
            if(isinstance(item, AnnotatedSegment)):
                r = item.get_rect()
                xc = (r[0] + r[2]) * 0.5
                xr = r[2] - r[0]
                yc = (r[1] + r[3]) * 0.5
                yr = r[1] - r[3]
            elif(isinstance(item, AnnotatedRectangle)):
                xc, yc = item.get_tr_center()
                xr, yr = item.get_tr_size()

            elif (isinstance(item, AnnotatedPoint)):
                xc, yc = item.get_pos()
                xr = 0.0
                yr = 0.0
            #else:
            #    _logger.error('houston we have a problem')

            if((xc is not None) and (yc is not None)):
                x1_lst.append(xc - (0.5 * xr))
                y1_lst.append(yc + (0.5 * yr))
                x2_lst.append(xc + (0.5 * xr))
                y2_lst.append(yc - (0.5 * yr))


        if(not (x1_lst or y1_lst or x2_lst or y2_lst)):
            #nothing to do
            return

        x1 = min(x1_lst)
        y1 = max(y1_lst)
        x2 = max(x2_lst)
        y2 = min(y2_lst)

        self.set_center_at_XY(((x1 + x2) * 0.5, (y1 + y2) * 0.5), ((x2 - x1), (y1 - y2)))
        self.plot.replot()



    def resizeShapePlotItemCENTER(
            self,
            item_id,
            cntr,
            rng,
            item=None,
            item_type=types.spatial_type_prefix.ROI):
        """
        resizeShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param cntr: cntr description
        :type cntr: cntr type

        :param rng: rng description
        :type rng: rng type

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :returns: None
        """
        # make sure item is 'selected'
        startx = cntr[0] - (0.5 * rng[0])
        starty = cntr[1] - (0.5 * rng[1])
        if(item is None):
            item = self.getShapePlotItem(item_id, item_type)

        self.plot.set_active_item(item)
        item.select()

        rect = self._restrict_rect_to_positive(QRectF())

        if(item_type == types.spatial_type_prefix.ROI):
            item.set_rect(startx, starty, startx + rng[0], starty + rng[1])

        elif(item_type == types.spatial_type_prefix.SEG):
            item.set_rect(startx, starty, startx + rng[0], starty)

        else:
            # assumne PNT type
            item.set_pos(startx, starty)

        item.invalidate_plot()
        self.plot.replot()

    def selectShapePlotItem(
            self,
            item_id,
            select=True,
            item=None,
            item_type=types.spatial_type_prefix.ROI):
        """
        resizeShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param item: shapePlotItem
        :type item:

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :returns: None
        """
        self.deselect_all_shapes()
        self.enable_all_shape_labels(False)

        if(item is None):
            item = self.getShapePlotItem(item_id, item_type)

        if(select):
            self.plot.set_active_item(item)
            item.select()
            if(hasattr(item, "is_label_visible")):
                item.set_label_visible(True)
        else:
            self.plot.set_active_item(None)
            item.deselect()
            if(hasattr(item, "is_label_visible")):
                item.set_label_visible(False)

    def set_shape_item_max_range(self, item, max_range):
        item.max_range = max_range

    def set_max_shape_sizes(self, max_size):
        self.max_shape_size = max_size

    def set_enable_multi_region(self, enable=True):
        self.multi_region_enabled = enable

    def resizeShapePlotItem(
            self,
            item_id,
            rect,
            item=None,
            item_type=types.spatial_type_prefix.ROI,
            recenter=False):
        """
        resizeShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param rect: cntr description
        :type rect: tuple representing the corners of a rect (x1, y1, x2, y2)

        :param rng: rng description
        :type rng: rng type

        :param item: item description
        :type item: item type

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :param recenter: a flag to have the plot recenter around the new shape size or not
        :type recenter: bool, default is False

        :returns: None
        """
        # make sure item is 'selected'
        (x1, y1, x2, y2) = rect
        rng = ((x2 - x1), (y1 - y2))
        # print 'resizeShapePlotItem: rect=', rect
        if(item is None):
            item = self.getShapePlotItem(item_id, item_type)

        # limit size of item to the max range that has been set for it
        wd = x2 - x1
        ht = y2 - y1

#         if(wd > item.max_range[0]):
#             x2 = x1 + item.max_range[0]
#
#         if(ht > item.max_range[1]):
#             y2 = y1 + item.max_range[1]

        if(item_type == types.spatial_type_prefix.ROI):
            item.set_rect(x1, y1, x2, y2)

        elif(item_type == types.spatial_type_prefix.SEG):
            item.set_rect(x1, y1, x2, y2)

        else:
            # assumne PNT type
            item.set_pos(x1, y1)
            rng = (5, 5)

        if(recenter):
            self.set_center_at_XY(((x1 + x2) * 0.5, (y1 + y2) * 0.5), rng)

        item.invalidate_plot()
        self.plot.replot()
        # self.on_set_aspect_ratio()

    def getShapePlotItem(self, item_id, item_type=types.spatial_type_prefix.ROI):
        """
        getShapePlotItem(): description

        :param item_id: item_id description
        :type item_id: item_id type

        :param item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI description
        :type item_type=types.spatial_type_prefix.ROI: item_type=types.spatial_type_prefix.ROI type

        :returns: None
        """
        items = self.plot.get_items(item_type=IShapeItemType)
        for item in items:
            if(item_type == types.spatial_type_prefix.ROI):
                if(isinstance(item, AnnotatedRectangle)):
                    title = str(item.title().text())
                    # print 'getShapePlotItem: Rect:', title
                    if(item_id == item.unique_id):
                        # print 'getShapePlotItem: Point:', title
                        return(item)

            elif(item_type == types.spatial_type_prefix.SEG):
                if(isinstance(item, AnnotatedHorizontalSegment)):
                    title = str(item.title().text())
                    # print 'getShapePlotItem: Segment:', title
                    if(item_id == item.unique_id):
                        # print 'getShapePlotItem: Point:', title
                        return(item)
                if(isinstance(item, AnnotatedSegment)):
                    title = str(item.title().text())
                    # print 'getShapePlotItem: Segment:', title
                    if(item_id == item.unique_id):
                        # print 'getShapePlotItem: Point:', title
                        return(item)

            elif(item_type == types.spatial_type_prefix.PNT):
                if(isinstance(item, AnnotatedPoint)):
                    title = str(item.title().text())
                    if(item_id == item.unique_id):
                        # print 'getShapePlotItem: Point:', title
                        return(item)

        return(None)

    def getShapeItems(self):
        """
        getShapeItems(): description

        :returns: a list of the current items
        """
        items = self.get_plot().get_items(item_type=IShapeItemType)
        return(items)


    def getShapeItemsByShapeType(self, shape_type=AnnotatedRectangle):
        """
        getShapeItemsByShapeType(): description

        :param shape_type: pass the type of shape you are looking for
        :type shape_type: a valid guiqwt ShapeItemType

        :returns: a list of the current items specified
        """
        items_lst = []

        items = self.get_plot().get_items(item_type=IShapeItemType)
        for item in items:
            #if(isinstance(shape_type, QtCore.pyqtWrapperType)):
            if (isinstance(shape_type, type(QtCore.QObject))):

                if(isinstance(item, shape_type)):
                    items_lst.append(item)
            else:
                # it is an instance
                if(isinstance(shape_type, type(item))):
                    items_lst.append(item)

        return(items_lst)

    def getShapeItemsByShapeInstance(self, shape_inst=None):
        """
        getShapeItemsByShapeInstance(): description

        :param shape_inst: pass the instance of shape you are looking for
        :type shape_inst: an instance of a valid guiqwt ShapeItem

        :returns: a list of the current items specified
        """
        items_lst = []

        items = self.get_plot().get_items(item_type=IShapeItemType)
        for item in items:
            if(isinstance(shape_inst, type(item))):
                items_lst.append(item)

        return(items_lst)

    def get_shape_item_types(self, item):
        if(isinstance(item, AnnotatedRectangle)):
            return({'shape_type': AnnotatedRectangle, 'spatial_type': types.spatial_type_prefix.ROI})

        if(isinstance(item, AnnotatedHorizontalSegment)):
            return({'shape_type': AnnotatedHorizontalSegment, 'spatial_type': types.spatial_type_prefix.SEG})

        if(isinstance(item, AnnotatedSegment)):
            return({'shape_type': AnnotatedSegment, 'spatial_type': types.spatial_type_prefix.SEG})

        if(isinstance(item, AnnotatedPoint)):
            return({'shape_type': AnnotatedPoint, 'spatial_type': types.spatial_type_prefix.PNT})

    def delPlotItem(self, item, replot=True):
        """
        delPlotItem(): description

        :param item: item description
        :type item: item type

        :param replot=True: replot=True description
        :type replot=True: replot=True type

        :returns: None
        """
        # Don't delete the base image
        # if(item.title().text() != 'Image #1'):
        if(not isinstance(item, ICSImageItemType)):
            title = str(item.title().text())
            # print 'deleting %s'  % title
            self.region_deleted.emit(title)
            self.plot.del_item(item)
            # print 'deleteing [%s] with unique_id [%d]' % (str(item.title().text()), item.unique_id)
            # print 'id(item)=%d, unique=%d' % (id(item), item.unique_id)
            if(hasattr(item, '_parent_tool')):
                item._parent_tool.re_init_unique_id()
            del item
            # signal to anyone listening that we are deleting this item
            #print 'delPlotItem: emitting_new_roi with cmnd=DEL_ROI'
            self._emit_new_roi(None, cmnd=widget_com_cmnd_types.DEL_ROI)

            if(replot):
                self.plot.replot()

    def delImagePlotItems(self):
        """
        delImagePlotItems(): description

        :returns: None
        """
        items = self.plot.get_items(item_type=ICSImageItemType)
        for item in items:
            # Don't delete the base image
            # if(item.title().text() != 'Image #1'):
            # print 'deleting %s'  % item.title().text()
            self.plot.del_item(item)
            del item
        self.item = None
        self.plot.replot()

    def delShapePlotItems(self):
        """
        delShapePlotItems(): description

        :returns: None
        """
        items = self.plot.get_items(item_type=IShapeItemType)
        for item in items:
            self.delShapePlotItem(item, replot=False)

        self.plot.replot()

    def delShapePlotItem(self, item, replot=True):
        """
        delShapePlotItem(): description

        :returns: None
        """
        dct = self.get_shape_item_types(item)

        if(not isinstance(item, ImageItem)):
            self.plot.del_item(item)
            del item

            if(replot):
                self.plot.replot()

    def deactivate_tools(self):
        dct = self.toolclasses_to_dct()
        for toolstr in list(dct.keys()):
            tool = dct[toolstr]
            if(hasattr(tool, 'deactivate')):
                tool.deactivate()

    def set_image_parameters(self, imgItem, x1, y1, x2, y2):
        """
        set_image_parameters(): description

        Use this function to adjust the image parameters such that the x and y axis are
        within the xmin,xmax and ymin,ymax bounds, this is an easy way to display the image
        in microns as per the scan parameters, as well as the fact that if you have a scan with
        a non-square aspect ratio you can still display the scan as a square because the image will
        repeat pixels as necessary in either direction so that the image is displayed in teh min/max
        bounds you set here

        :param imageItem: a image plot item as returned from make.image()
        :type imageItem: a image plot item as returned from make.image()

        :param x1: min x that the image will be displayed
        :type x1: int

        :param y1: max x that the image will be displayed
        :type y1: int

        :param x2: min y that the image will be displayed
        :type x2: int

        :param y2: max y that the image will be displayed
        :type y2: int

        :returns:  None

        .. todo::
        there are man other image params that could be set in teh future, for now only implemented min/max
        ImageParam:
            Image title: Image
            Alpha channel: False
            Global alpha: 1.0
            Colormap: gist_gray
            Interpolation: None (nearest pixel)
            _formats:
              X-Axis: %.1f
              Y-Axis: %.1f
              Z-Axis: %.1f
            Background color: #000000
            _xdata:
              x|min: -
              x|max: -
            _ydata:
              y|min: -
              y|max: -

        """
        iparam = ImageParam()
        iparam.colormap = imgItem.get_color_map_name()
        iparam.xmin = x1
        iparam.ymin = y1
        iparam.xmax = x2
        iparam.ymax = y2
        self.zoom_rngx = float(x2 - x1)
        self.zoom_rngy = float(y2 - y1)

        axparam = ImageAxesParam()
        axparam.xmin = x1
        axparam.ymin = y1
        axparam.xmax = x2
        axparam.ymax = y2

        imgItem.set_item_parameters({"ImageParam": iparam})
        imgItem.set_item_parameters({"ImageAxesParam": axparam})

    def set_lock_aspect_ratio(self, val):
        """
        set_lock_aspect_ratio(): description

        :param val: val description
        :type val: val type

        :returns: None
        """
        self.plot.lock_aspect_ratio = bool(val)

    def get_current_data(self):
        return(self.data)

    def get_file_loading_progbar(self, max):
        progbar = QtWidgets.QProgressBar()
        progbar.setFixedWidth(300)
        progbar.setWindowTitle("generating a composite image")
        progbar.setAutoFillBackground(True)
        progbar.setMinimum(0)
        progbar.setMaximum(max)

        ss = """QProgressBar 
              {        
                        border: 5px solid rgb(100,100,100);
                        border-radius: 1 px;
                        text-align: center;
              }
            QProgressBar::chunk
             {
                         background-color:  rgb(114, 148, 240);
                          width: 20 px;
             }"""

        progbar.setStyleSheet(ss)
        return(progbar)


    def openfile(self, fnames, addimages=True, counter='counter0', dropped=False):
        if(self.show_image_params):
            self.openfile_mod(fnames, addimages=True, counter='counter0', dropped=dropped)
        elif (len(fnames) is 1):
            self.openfile_mod(fnames, addimages=True, counter='counter0', dropped=dropped)
        else:
            num_fnames = len(fnames)
            self.progbar = self.get_file_loading_progbar(num_fnames)

            if(num_fnames > 5):
                self.progbar.show()

            thpool_im_ldr = ThreadpoolImageLoader()
            thpool_im_ldr.load_image_items(fnames, result_fn=self.load_image_items, progress_fn=self.load_images_progress, thread_complete_fn=self.hide_progbar)



    def load_images_progress(self, prog):
        self.progbar.setValue(prog)

    def load_image_items(self, items_lst):
        plot = self.get_plot()
        plot.setFocus()
        for item in items_lst:
            npts = item.data.shape
            rngx = item.bounds.size().width()
            rngy = item.bounds.size().height()
            items = self.plot.get_items(item_type=ICSImageItemType)
            #plot.add_item(item, z=len(items) + 1)
            z = self.calc_z_score(npts, (rngx, rngy))
            plot.add_item(item, z=z)

        #plot.replot()
        #self.set_autoscale()

    def hide_progbar(self):
        #print("imageWidget: threadpool image loader is done")
        self.progbar.hide()

    def calc_z_score(self, npts, rngs):
        '''
        two tuples if the images number of points and ranges
        calc a score based on a priority of:
        higher npts == higher score
        smaller range == higher score
        :param npts:
        :param rngs:
        :return:
        '''
        tpnts = npts[0] * npts[1]
        trngs = rngs[0] * rngs[1]
        score = float(tpnts / float(0.2 * trngs))
        #print 'calc_z_score: %d = R(%.1f, %.1f) , P(%d, %d)' % (score, rngs[0], rngs[1], npts[0], npts[1])
        return (score)

    # def record_image_z_dpeth(self, item, npts, rngs):
    #     self.add_images_z_depth_dct

    def add_image_from_file(self, fname):
        '''
        mainly used to load png and jpg files
        :param fname:
        :return:
        '''
        from guiqwt import io
        image = ImageParam()
        image.title = to_text_string(fname)
        image.data = io.imread(fname, to_grayscale=True)
        image.height, image.width = image.data.shape
        plot = self.get_plot()
        #add it to the top of the plot items (z=0)
        #plot.add_item(image, z=0)
        item = make.trimage(image.data, dx=.1, dy=.1, alpha=0.4, colormap='gist_gray')
        item.set_selectable(True)
        item.set_movable(True)
        item.set_resizable(True)
        item.set_rotatable(True)
        plot.add_item(item, z=MAX_IMAGE_Z-1)


    def openfile_mod(self, fnames, addimages=True, counter='counter0', dropped=False):
        """
        openfile(): description

        :param fnames: a list of filenames
        :type fnames: list

        :param addimages=False: addimages=False description
        :type addimages=False: addimages=False type

        :returns: None
        """
        num_files = len(fnames)
        idx = 0
        iidx = 0
        progbar = self.get_file_loading_progbar(num_files)

        for fname in fnames:
            fname = str(fname)
            data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
            if(data_dir is None):
                _logger.error('Problem with file [%s]' % fname)
                return

            if (fsuffix.find('jpg') > -1):
                # trying to load a jpg
                self.add_image_from_file(fname)
                continue
            elif (fsuffix.find('png') > -1):
                # trying to load a png
                self.add_image_from_file(fname)
                continue

            if (not isinstance(self.data_io, DataIo)):
                data_io = self.data_io(data_dir, fprefix)
            else:
                #we have been launched from a parent viewer
                self.data_io.update_data_dir(data_dir)
                self.data_io.update_file_prefix(fprefix)
                self.data_io.update_file_path(fname)
                data_io = self.data_io

            start_time = timeit.default_timer()

            entry_dct = data_io.load()
            ekey = list(entry_dct.keys())[0]
            nx_datas = data_io.get_NXdatas_from_entry(entry_dct, ekey)
            sp_id = list(entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'].keys())
            scan_type = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['SCAN_PLUGIN']['SCAN_TYPE']
            rng_x = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['X'][RANGE]
            rng_y = entry_dct[ekey]['WDG_COM']['SPATIAL_ROIS'][sp_id[0]]['Y'][RANGE]

            idx += 1
            iidx += 1
            progbar.setValue(iidx)
            elapsed = timeit.default_timer() - start_time
            #print 'elapsed time = ', elapsed

            if(num_files > 5):
                if(idx > 5):
                    #give the GUI something
                    QtWidgets.QApplication.processEvents()
                    idx = 0

            if(rng_x > rng_y):
                item_z = rng_x
            else:
                item_z = rng_y

            if(not (scan_type is types.scan_types.SAMPLE_IMAGE) and (num_files > 1)):
                continue

            if(counter not in list(nx_datas.keys())):
                _logger.error('counter [%s] does not exist in the datafile' % counter)
                return
            data = data_io.get_signal_data_from_NXdata(nx_datas, counter)

            if((data.ndim is 3)):
                data = data[0]

            if((data.ndim is not 2)):
                _logger.error('Data in file [%s] is of wrong dimension, is [%d] should be [2]' % (fname, data.ndim))
                print('Data in file [%s] is of wrong dimension, is [%d] should be [2]' % (fname, data.ndim))
            else:

                wdg_com = data_io.get_wdg_com_from_entry(entry_dct, ekey)
                self.load_image_data(fname, wdg_com, data, addimages, flipud=False, name_lbl=False, item_z=item_z, show=False, dropped=dropped)
                #self.on_set_aspect_ratio(True)
                #self.update_contrast()

        #if(len(fnames) > 1):
        #    items
        #    self.sort_items_z(items)
        progbar.hide()
        self.on_set_aspect_ratio(True)
        self.update_contrast()

    def sort_items_z(self, items):
        for item in items:
            #print item
            #old_item1_z, old_item2_z = item1.z(), item2.z()
            #item1.setZ(max([_it.z() for _it in self.items]) + 1)
            #item2.setZ(old_item1_z)
            #item1.setZ(old_item2_z)
            pass


    def load_image_data(self, fname, wdg_com, data, addimages=False, flipud=False, name_lbl=True, item_z=None, show=True, dropped=False):
        """
        openfile(): This function loads a nxstxm hdf5 file, if it is a multi ev scan only the first image is
        used

        :param fname: fname description
        :type fname: fname type

        :param addimages=False: addimages=False description
        :type addimages=False: addimages=False type

        :returns: None
        """

        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if(data_dir is None):
            _logger.error('Problem with file [%s]' % fname)
            return

        plot = self.get_plot()
        plot.setFocus()
        if(wdg_com is not None):
            sp_db = get_first_sp_db_from_wdg_com(wdg_com)
            # only display first energy [0]
            data = data.astype(np.float32)
            data[data==0.0] = np.nan
            self.data = data
            if(self.data.ndim == 3):
                self.data = self.data[0]
            if(flipud):
                _data = np.flipud(self.data)
            else:
                _data = self.data

            self.data = _data
            _logger.info('[%s] scan loaded' %
                             dct_get(sp_db, SPDB_SCAN_PLUGIN_SECTION_ID))

        self.image_type = dct_get(sp_db, SPDB_PLOT_IMAGE_TYPE)
        # if it is a focus image I dont want any of the tools screweing up the
        # scan params so disable them
        #if the image was dropped do NOT do anything with the tools
        if(not dropped):
            if(self.image_type in [types.image_types.FOCUS, types.image_types.OSAFOCUS]):
                self.enable_tools_by_spatial_type(None)
            else:
                self.enable_tools_by_spatial_type(
                    dct_get(sp_db, SPDB_PLOT_SHAPE_TYPE))

        dct_put(sp_db, SPDB_PLOT_IMAGE_TYPE, self.image_type)
        if(name_lbl):
            _title = str(fname)
            self.setWindowTitle(_title)
            plot.set_title('%s%s' % (fprefix, fsuffix))
        else:
            _title = None

        self.htSc = 1
        self.widthSc = 1

        if(self.data is not None):
            shape = self.data.shape
            if(len(shape) == 3):
                [e, self.dataHeight, self.dataWidth] = self.data.shape
                self.data = self.data[0]
            elif(len(shape) == 2):
                [self.dataHeight, self.dataWidth] = self.data.shape
            else:
                _logger.error('Not sure what kind of shape this is')
                return

            self.wPtr = 0
            self.hPtr = 0
            if((not addimages) or (self.item is None)):
                self.delImagePlotItems()
                self.item = make.image(self.data,interpolation='nearest',colormap='gist_gray', title=_title)
                plot = self.get_plot()
                plot.add_item(self.item, z=0)
            else:
                self.item = make.image(self.data,interpolation='nearest',colormap='gist_gray',title=_title)
                items = self.plot.get_items(item_type=ICSImageItemType)
                if(item_z is None):
                    plot.add_item(self.item, z=len(items)+1)
                else:
                    plot.add_item(self.item, z=item_z)

            (x1, y1, x2, y2) = dct_get(sp_db, SPDB_RECT)
            self.set_image_parameters(self.item, x1, y1, x2, y2)

            if(show):
                self.show_data(self.data, True)
                self.set_autoscale()

            dct_put(sp_db, SPDB_PLOT_KEY_PRESSED, self.inputState.keyisPressed)

            #wdg_com = dct_get(sp_db, ADO_CFG_WDG_COM)
            wdg_com[WDGCOM_CMND] = widget_com_cmnd_types.LOAD_SCAN
            sp_db[WDGCOM_CMND] = widget_com_cmnd_types.LOAD_SCAN

            if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) != types.scan_types.SAMPLE_POINT_SPECTRA):
                # self.on_set_aspect_ratio(True)
                pass

            self.scan_loaded.emit(wdg_com)

            if(self.show_image_params):
                self.display_image_params(fprefix, sp_db)
            else:
                self.report_image_params(fprefix, sp_db)


    def display_image_params(self, fprefix, sp_db, name_lbl=True):
        param = ImageParam()
        if(name_lbl):
            param.title = fprefix
        else:
            param.title = None
        endtime_str  = dct_get(sp_db, 'ACTIVE_DATA_OBJ.END_TIME')
        starttime_str = dct_get(sp_db, 'ACTIVE_DATA_OBJ.START_TIME')
        elapsed = datetime_string_to_seconds(endtime_str) - datetime_string_to_seconds(starttime_str)
        param.scan_time = '%.2f sec' % elapsed
        height, width = self.data.shape

        param.scan_type = types.scan_types[
            dct_get(
                sp_db,
                SPDB_SCAN_PLUGIN_TYPE)] + ' ' + types.scan_sub_types[
            dct_get(
                sp_db,
                SPDB_SCAN_PLUGIN_SUBTYPE)]
        param.energy = '%.2f eV' % sp_db[EV_ROIS][0][START]
        param.dwell = '%.2f ms' % sp_db[EV_ROIS][0][DWELL]
        param.npoints = '%d x %d' % (width, height)
        param.center = '(%.2f, %.2f) um' % (
            dct_get(sp_db, SPDB_XCENTER), dct_get(sp_db, SPDB_YCENTER))
        param.rng = '(%.2f, %.2f) um' % (
            dct_get(sp_db, SPDB_XRANGE), dct_get(sp_db, SPDB_YRANGE))

        # param.current =
        update_dataset(self.param_gbox.dataset, param)
        self.param_gbox.get()

    def report_image_params(self, fprefix, sp_db):
        #param = ImageParam()
        #param.title = fprefix
        height, width = self.data.shape
        #s = '\nFile: %s loaded \n' %  fprefix
        # s += '  # Points: %d x %d \n' % (width, height)
        #s += '  Center: (%.2f, %.2f) um\n' % (sp_db['X'][CENTER], sp_db['Y'][CENTER])
        #s += '  Range: (%.2f, %.2f) um\n' % (sp_db['X'][RANGE], sp_db['Y'][RANGE])
        #s += '  Scan Type: %s' %  types.scan_types[sp_db['SCAN_PLUGIN']['SCAN_TYPE']] + ' ' + types.scan_sub_types[sp_db['SCAN_PLUGIN']['SCAN_SUBTYPE']]

        s = fprefix
        s += '  Scan Type: %s' % types.scan_types[dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)] + ' ' + types.scan_sub_types[
            dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)]
        s += '  Energy: %.2f eV\n' % sp_db[EV_ROIS][0][START]
        s += '  Dwell: %.2f ms\n' % sp_db[EV_ROIS][0][DWELL]
        s += '  # Points: %d x %d \n' % (width, height)
        s += '  Center: (%.2f, %.2f) um\n' % (dct_get(sp_db,
                                                      SPDB_XCENTER), dct_get(sp_db, SPDB_YCENTER))
        s += '  Range: (%.2f, %.2f) um\n' % (dct_get(sp_db,
                                                     SPDB_XRANGE), dct_get(sp_db, SPDB_YRANGE))
        _logger.info(s)
        _logger.info('')

    def setZoomLimits(self):
        """
        setZoomLimits(): description

        :returns: None
        """
        if self.stxm_obj.image_obj:
            xaxis, yaxis = self.plot.get_active_axes()
            axis = self.plot.axisScaleDiv(xaxis)
            shape = self.stxm_obj.image_obj.rawData.shape
            xRange = (0, shape[0])
            yRange = (0, shape[1])
            #xMap = Qwt.QwtScaleMap(0, shape[0], *xRange)
            self.plot.setAxisScale(Qwt.QwtPlot.xBottom, *xRange)
            #yMap = Qwt.QwtScaleMap(0, shape[1], *yRange)
            self.plot.setAxisScale(Qwt.QwtPlot.yLeft, *yRange)
            self.plot.set_plot_limits(0, shape[0], 0, shape[1])

    def set_center_at_0(self, xRange, yRange):
        """
        set_center_at_0(): description

        :param xRange: xRange description
        :type xRange: xRange type

        :param yRange: yRange description
        :type yRange: yRange type

        :returns: None
        """
        """ given the ranges specified center the plot around 0
        """
        xRhalf = xRange / 2.0
        yRhalf = yRange / 2.0
        self.plot.set_plot_limits(-xRhalf, xRhalf, -yRhalf, yRhalf)

    def set_center_at_XY(self, center, rng, zoomout=0.35):
        """
        set_center_at_XY(): description

        :param center: center description
        :type center: center type

        :param rng: rng description
        :type rng: rng type

        :returns: None
        """
        """ given the center and range tuples specified center the plot around center
        """
        (cx, cy) = center
        (rx, ry) = rng

        if(rx == 0.0):
            rx = 50
        if(ry == 0.0):
            ry = 50
        bufferx = zoomout * rx
        buffery = zoomout * ry

        xstart = cx - (0.5 * rx) - bufferx
        xstop = cx + (0.5 * rx) + bufferx

        ystart = cy - (0.5 * ry) - buffery
        ystop = cy + (0.5 * ry) + buffery

        dx = xstop - xstart
        dy = ystop - ystart

        x0, x1, y0, y1 = self.plot.get_plot_limits()

        pdx = x1 - x0
        pdy = y1 - y0

        if(pdx > pdy):
            #scale y
            dy = dy * (pdy/pdx)
            ystart = cy - (0.5 * dy)
            ystop = cy + (0.5 * dy)
        else:
            #scale x
            dx = dx * (pdx / pdy)
            xstart = cx - (0.5 * dx)
            xstop = cx + (0.5 * dx)

        self.plot.set_plot_limits(xstart, xstop, ystart, ystop)

    def setPlotAxisStrs(self, ystr=None, xstr=None):
        """
        setPlotAxisStrs(): description

        :param ystr=None: ystr=None description
        :type ystr=None: ystr=None type

        :param xstr=None: xstr=None description
        :type xstr=None: xstr=None type

        :returns: None
        """
        self.plot = self.get_plot()
        # set axis titles
        if(ystr is not None):
            self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, ystr)
        if(xstr is not None):
            self.plot.setAxisTitle(Qwt.QwtPlot.xBottom, xstr)

        self.plot.setAxisTitle(Qwt.QwtPlot.xTop, '')
        self.plot.setAxisTitle(Qwt.QwtPlot.yRight, '')

        # self.plot.replot()

    def setXYStep(self, stxm_obj):
        """
        setXYStep(): description

        :param stxm_obj: stxm_obj description
        :type stxm_obj: stxm_obj type

        :returns: None
        """
        # convert to a 1/<> value as it is used to do the pixel to micron
        # conversion
        if(self.stxm_obj.header['XStep'] == 0):
            self.stxm_obj.header['XStep'] = 1
        if(self.stxm_obj.header['YStep'] == 0):
            self.stxm_obj.header['YStep'] = 1
        self.xstep = float(1.0 / self.stxm_obj.header['XStep'])
        self.ystep = float(1.0 / self.stxm_obj.header['YStep'])

    ############### TEST CODE ########################################
    def timerTestStop(self):
        """
        timerTestStop(): description

        :returns: None
        """
        self.tstTimer.stop()


def get_percentage_of_qrect(qrect, p):
    '''
    take a qrect and return another qrect that is only a percentage of the passed in qrect. This
    is used mainly to produce warning qrects for a limit_def

    :param qrect: QRectF object
    :type qrect: QRectF

    :param p: The percentage of qrect to return, value is given as a decimal where 0.5 = %50
    :type p: double

    :returns: QRectF

    '''
    (x1, y1, x2, y2) = qrect.getCoords()
    return(QtCore.QRectF(QtCore.QPointF(x1 * p, y1 * p), QtCore.QPointF(x2 * p, y2 * p)))


#def make_default_stand_alone_stxm_imagewidget(parent=None, data_io=None, _type=None, sample_positioning_mode=types.sample_positioning_modes):
def make_default_stand_alone_stxm_imagewidget(parent=None, data_io=None, _type=None, bndg_rect=None):
    #from cls.applications.pyStxm.widgets.beam_spot_fbk import BeamSpotFeedbackObjStandAlone
    #from cls.applications.pyStxm.bl10ID01 import MAIN_OBJ

    # def on_new_beamspot_fbk(cx, cy):
    #     '''
    #     the beam spot object has emitted a new center x/y so let the plotter know
    #     :param cx:
    #     :param cy:
    #     :return:
    #     '''
    #     global win
    #     print 'on_new_beamspot_fbk: (%.2f, %.2f)' % (cx, cy)
    #     win.move_beam_spot(cx, cy)

    if(data_io is None):
        from cls.data_io.stxm_data_io import STXMDataIo
        data_io = STXMDataIo

    gridparam = make.gridparam(background="#3e3e3e",
                                    minor_enabled=(False, False),
                                    major_enabled=(False, False))

    # bmspot_fbk_obj = BeamSpotFeedbackObjStandAlone()
    # bmspot_fbk_obj.new_beam_pos.connect(on_new_beamspot_fbk)

    win = ImageWidget(
        parent=parent,
        filtStr=FILTER_STRING,
        type=_type,
        options=dict(gridparam=gridparam,
            show_contrast=True,
            show_xsection=True,
            show_ysection=True,
            show_itemlist=False))

    win.set_enable_multi_region(False)
    win.enable_beam_spot(True)
    if(bndg_rect is None):
        bounding_qrect = QRectF(QPointF(-1000, 1000), QPointF(1000, -1000))
    else:
        bounding_qrect = QRectF(QPointF(bndg_rect[0], bndg_rect[1]), QPointF(bndg_rect[2], bndg_rect[3]))

    warn_qrect = get_percentage_of_qrect(bounding_qrect, 0.90)  # %80 of max
    alarm_qrect = get_percentage_of_qrect(bounding_qrect, 0.95)  # %95 of max
    #normal_qrect = QtCore.QRectF(QtCore.QPointF(-400, 400), QtCore.QPointF(400, -400))
    normal_qrect = get_percentage_of_qrect(bounding_qrect, 0.40)

    bounding = ROILimitObj(
        bounding_qrect,
        get_alarm_clr(255),
        'Range is beyond Goniometer Capabilities',
        get_alarm_fill_pattern())
    normal = ROILimitObj(
        normal_qrect,
        get_normal_clr(45),
        'Fine ZP Scan',
        get_normal_fill_pattern())
    warn = ROILimitObj(
        warn_qrect,
        get_warn_clr(65),
        'Goniometer will be required to move',
        get_warn_fill_pattern())
    alarm = ROILimitObj(
        alarm_qrect,
        get_alarm_clr(255),
        'Range is beyond ZP Capabilities',
        get_alarm_fill_pattern())

    limit_def = ROILimitDef(bounding, normal, warn, alarm)

    #win.set_shape_limits(types.spatial_type_prefix.PNT, limit_def)

    #win.clear_all_tools()
    win.setObjectName('lineByLineImageDataWidget')
    win.set_max_shape_sizes((100, 30))
    win.setCheckRegionEnabled(True)
    win.addTool('HelpTool')
    #win.addTool('SelectPointTool')

    #win.addTool('tools.StxmControlBeamTool')
    # win.enable_image_param_display(True)
    win.enable_tool_by_name('tools.clsOpenFileTool', True)
    win.addTool('tools.clsHorizMeasureTool')
    win.addTool('tools.clsMeasureTool')
    win.enable_tool_by_name('tools.clsSquareAspectRatioTool', True)

    win.addTool('DummySeparatorTool')
    #win.register_samplehldr_tool(sample_pos_mode=sample_positioning_mode)
    win.register_samplehldr_tool()
    win.addTool('DummySeparatorTool')
    # win.addTool('ItemCenterTool')
    win.resize(600, 700)


    win.set_dataIO(data_io)
    # win.enable_tool('FreeFormTool')
    #win.resizeShapePlotItem('ROI 1', (200,200), (100,100), item_type='Rect')
    #win.resizeShapePlotItem('SEG 1', (400,400), (500,400), item_type='Segment')
    #win.resizeShapePlotItem('PNT 1', (600,600), (1,1), item_type='Point')

    return(win)


def make_default_stand_alone_stxm_imagewidget_openfile(fname, parent=None):
    win = make_default_stand_alone_stxm_imagewidget(parent)

    win.openfile(fname, addimages=True)
    return(win)


def make_flea_camera_widow():
    win = ImageWidget(
        parent=None,
        filtStr=FILTER_STRING,
        type=None,
        options=dict(
            show_contrast=False,
            show_xsection=False,
            show_ysection=False,
            show_itemlist=False))
    win.set_enable_multi_region(False)
    win.enable_image_param_display(False)
    win.enable_grab_btn()
    win.enable_tool_by_name('tools.clsOpenFileTool', True)
    win.resize(900, 900)
    return(win)


def make_uhvstxm_distance_verification_window():
    win = ImageWidget(
        parent=None,
        filtStr=FILTER_STRING,
        type=None,
        options=dict(
            show_contrast=False,
            show_xsection=False,
            show_ysection=False,
            show_itemlist=False))
    win.set_enable_multi_region(False)
    win.enable_image_param_display(False)
    win.enable_grab_btn()
    win.enable_tool_by_name('tools.clsOpenFileTool', False)
    win.addTool('tools.clsMultiLineTool')
    win.resize(900, 900)
    return(win)


def make_pystxm_window():
    from cls.data_io.stxm_data_io import STXMDataIo

    fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
    bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
    min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
    maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

    win = ImageWidget(parent=None, filtStr=FILTER_STRING, type=None,
                            options=dict(lock_aspect_ratio=True, show_contrast=True, show_xsection=True, show_ysection=True,
                            xlabel=("microns", ""), ylabel=("microns", ""), colormap="gist_gray"))
    win.set_enable_multi_region(False)
    win.enable_image_param_display(False)
    win.enable_grab_btn()
    win.enable_tool_by_name('tools.clsOpenFileTool', False)
    win.addTool('tools.clsMultiLineTool')
    win.setObjectName("lineByLineImageDataWidget")
    win.set_dataIO(STXMDataIo)
    win.resize(900, 900)
    return(win)


def make_test_pattern_gen_window():
    from cls.data_io.stxm_data_io import STXMDataIo

    fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
    bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
    min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
    maj_clr = rgb_as_hex(master_colors['plot_gridmin'])

    win = ImageWidget(parent=None, filtStr=FILTER_STRING, type=None,
                            options=dict(lock_aspect_ratio=True, show_contrast=True, show_xsection=True, show_ysection=True,
                            xlabel=("microns", ""), ylabel=("microns", ""), colormap="gist_gray"))
    win.set_enable_multi_region(False)
    win.enable_image_param_display(False)
    win.enable_grab_btn()
    win.enable_tool_by_name('tools.clsOpenFileTool', False)
    win.addTool('tools.clsMultiLineTool')
    win.setObjectName("lineByLineImageDataWidget")
    win.set_dataIO(STXMDataIo)
    win.resize(900, 900)
    return(win)

class qobj_OBJ(QObject):
    new_beam_pos = pyqtSignal(float, float)
    def __init__(self):
        QObject.__init__(self)
        from bcm.devices import Motor_Qt as apsMotor
        self.zx = apsMotor('IOC:m102', name='zoneplateX')
        self.zy = apsMotor('IOC:m103', name='zoneplateY')
        self.gx = apsMotor('IOC:m107', name='goniX')
        self.gy = apsMotor('IOC:m108', name='goniX')
        self.zx.add_callback('RBV', self.on_mtr_fbk_changed)

    def on_mtr_fbk_changed(self, **kwargs):

        zxpos = self.zx.get_position()
        zypos = self.zy.get_position()
        gxpos = self.gx.get_position()
        gypos = self.gy.get_position()
        x = zxpos + gxpos
        y = zypos + gypos
        self.new_beam_pos.emit(x, y)

def test_pattern_gen(win):
    from cls.utils.roi_utils import get_base_roi



    # print 'on_scanpluggin_roi_changed: rect=' , (rect)
    centers = [0.5, 2.5, 4.5]
    item_idx = 0
    ltr_lst = ['A','B','C','D','E','F','G','H','I']
    ltr_lst.reverse()
    rois_dct = {}
    main_rect = None
    for x_center in centers:
        for y_center in centers:
            letter = ltr_lst.pop()
            x_roi = get_base_roi('pattrn_%sx' % letter, '', x_center, 1.0, 10, enable=True, is_point=False, src=None)
            y_roi = get_base_roi('pattrn_%sy' % letter, '', y_center, 1.0, 10, enable=True, is_point=False, src=None)

            x1 = float(x_roi['START'])
            y1 = float(y_roi['START'])
            x2 = float(x_roi['STOP'])
            y2 = float(y_roi['STOP'])

            # print 'on_scanpluggin_roi_changed: item_id = %d' % item_id

            rect = (x1, y1, x2, y2)

            #win.addShapePlotItem(item_idx, rect, show_anno=False)
            # if(item_idx is 4):
            #     #the middle one, will be the one that is selected
            #     title = 'patternrect'
            #     print('patternrect', rect)
            # else:
            title = 'pattern'
            #     create_rectangle(rect, title='pattern', plot=win.plot, annotated=True)
            # else:
            #     create_rectangle(rect, title='pattern', plot=win.plot, annotated=False)
            create_rectangle(rect, title=title, plot=win.plot, annotated=False)
            qrect = QtCore.QRectF(QtCore.QPointF(rect[0], rect[2]), QtCore.QPointF(rect[3], rect[1]))

            if (main_rect is None):
                main_rect = qrect
            else:
                main_rect = main_rect.united(qrect)
            item_idx += 1
            rois_dct[letter] = {'X': x_roi, 'Y': y_roi}

    shape, z = create_rectangle(main_rect.getRect(), title='pattern', plot=win.plot, annotated=True, alpha=0.01, l_style='DashLine', l_clr='#645d03')
    shape.unique_id = get_unique_roi_id()

    return(rois_dct)


def go():
    from cls.utils.roi_utils import on_centerxy_changed
    ss = get_style('dark')
    app = guidata.qapplication()
    sys.excepthook = excepthook

    qobj = qobj_OBJ()

    # win = make_default_stand_alone_stxm_imagewidget()
    # win = make_default_stand_alone_stxm_imagewidget(_type='analyze')
    #(-1000, 1000), QPointF(1000, -1000)
    bndg_rect = (-5.0, 10.0, 10.0, -5.0)
    win = make_default_stand_alone_stxm_imagewidget(bndg_rect=bndg_rect)

    # win.create_beam_spot(0.0, 0.0, size=0.35)

    def on_new_roi_center(wdg_com):
        # print wdg_com.keys()
        # print wdg_com['SPATIAL_IDS']
        # print wdg_com['RECT']
        print('on_new_roi_center', wdg_com['X'][CENTER], wdg_com['Y'][CENTER])

    def select_pattern(img_plot):
        main_rect = img_plot.select_main_rect_of_shape('pattern')

    def assign_centers(dct, cntrs):
        dct['X']['CENTER'] = cntrs[0]
        dct['Y']['CENTER'] = cntrs[1]
        on_centerxy_changed(dct['X'])
        on_centerxy_changed(dct['Y'])

    def on_target_moved(Ex, Ey):
        #Ex = main_rect.center().x()
        #Ey = main_rect.center().y()

        #row 1
        Ac = (Ex-2.0,   Ey-2.0)
        Bc = (Ex,       Ey-2.0)
        Cc = (Ex+2.0,   Ey-2.0)
        #row 2
        Dc = (Ex-2.0,   Ey)
        #Ec
        Fc = (Ex+2.0,   Ey)
        #row 3
        Gc = (Ex,       Ey+2.0)
        Hc = (Ex,       Ey+2.0)
        Ic = (Ex+2.0,   Ey+2.0)

        assign_centers(rois_dct['A'], Ac)
        assign_centers(rois_dct['B'], Bc)
        assign_centers(rois_dct['C'], Cc)
        assign_centers(rois_dct['D'], Dc)
        assign_centers(rois_dct['F'], Fc)
        assign_centers(rois_dct['G'], Gc)
        assign_centers(rois_dct['H'], Hc)
        assign_centers(rois_dct['I'], Ic)

        #print('cntr:', (Ex, Ey))
        #print('A center: (%.4f, %.4f)' % (rois_dct['A']['X']['CENTER'], rois_dct['A']['Y']['CENTER']))
        #print('I center: (%.4f, %.4f)' % (rois_dct['I']['X']['CENTER'], rois_dct['I']['Y']['CENTER']))
        #print('A setpoints: ' , rois_dct['A']['X']['SETPOINTS'])

    def on_new_roi(object):
        on_target_moved(object['X']['CENTER'], object['Y']['CENTER'])

    # win.set_data_dir(r'S:\STXM-data\Cryo-STXM\2017\guest\0201')
    win.set_data_dir(r'S:\STXM-data\Cryo-STXM\2017\guest\0922')

    win.register_osa_and_samplehldr_tool(sample_pos_mode=types.sample_positioning_modes.GONIOMETER)
    win.setStyleSheet(ss)
    #     widg = QtWidgets.QFrame()
    #     vbox = QtWidgets.QVBoxLayout()
    #     vbox.addWidget(win)
    #     widg.setLayout(vbox)
    win.show()
    # win = make_flea_camera_widow()
    # win = make_uhvstxm_distance_verification_window()
    # win.new_roi_center.connect(on_new_roi_center)
    #win.enable_image_param_display(True)

    # win.show()
    upd_styleBtn = QtWidgets.QPushButton('Update Style')
    vbox = QtWidgets.QVBoxLayout()
    vbox.addWidget(upd_styleBtn)
    upd_styleBtn.clicked.connect(win.update_style)
    win.layout().addLayout(vbox)
    # testing beam spot feedback
    # win.move_beam_spot(5, 10)
    win.enable_menu_action('Clear Plot', True)

    win.register_shape_info(shape_info_dct={'shape_title': 'pattern', 'on_selected': select_pattern})

    win.target_moved.connect(on_target_moved)
    win.new_roi_center.connect(on_new_roi)

    rois_dct = test_pattern_gen(win)
    app.exec_()


if __name__ == "__main__":
    """Test"""
    # -- Create QApplication
    import guidata
    from PyQt5 import QtWidgets
    from cls.app_data.defaults import  get_style
    from bcm.devices import Motor_Qt as apsMotor
    from PyQt5.QtCore import pyqtSignal, QObject
    from cls.utils.profiling import determine_profile_bias_val, profile_it

    #profile_it('go', bias_val=7.40181638985e-07)
    go()

