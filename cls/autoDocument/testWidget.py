'''
Created on Jan 22, 2015

@author: bergr
'''
# -*- coding:utf-8 -*-
"""
Created on 2011-03-03

@author: bergr
"""
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import SIGNAL, pyqtSignal, QObject, QTimer, QPoint, QRect
from PyQt5 import uic

import os
import scipy.ndimage
import copy

import numpy as np

from zope.interface import implements


from bcm.utils.nextFactor import *
from bcm.utils.angles import calcRectPoints, foci

import PyQt4.Qwt5 as Qwt

#from guiqwt.io import pil_to_array
from guiqwt.builder import make
from guiqwt.plot import ImageDialog, ImageWidget
from guiqwt.tools import *
from guiqwt.styles import AnnotationParam, ItemParameters, ImageParam, ImageAxesParam, GridParam, CurveParam
from guiqwt.cross_section import XCrossSectionItem, YCrossSectionItem
from guiqwt.annotations import AnnotatedPoint, AnnotatedRectangle
from guiqwt.config import _
from guiqwt.shapes import EllipseShape
from guiqwt.label import LabelItem

from guiqwt.interfaces import (ICSImageItemType, IPanel, IBasePlotItem,
							   ICurveItemType, IShapeItemType, IDecoratorItemType)
from guiqwt.signals import (SIG_MARKER_CHANGED, SIG_PLOT_LABELS_CHANGED,
							SIG_ANNOTATION_CHANGED, SIG_AXIS_DIRECTION_CHANGED,
							SIG_ITEMS_CHANGED, SIG_ACTIVE_ITEM_CHANGED, SIG_ITEM_MOVED,
							SIG_LUT_CHANGED, SIG_ITEM_SELECTION_CHANGED, SIG_STOP_MOVING, SIG_PLOT_AXIS_CHANGED)

from sm.stxm_control.scanning.stxmTypes import TWO_D, SEG, PNT, SPATIAL_TYPE_PREFIX
from sm.stxm_control.stxm_utils.stxmDataObj import *
from sm.stxm_control.plotters.IPlotter import IPlotter
from cls.utils.log import get_module_logger

#setup module logger with a default do-nothing handler
_logger = get_module_logger(__name__)


# the relative dir to the filterPanel ui file 
uiDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui')


class StxmAverageCrossSectionTool(AverageCrossSectionTool):
	SWITCH_TO_DEFAULT_TOOL = True
	TITLE = _('')
	ICON = "csection_a.png"
	SHAPE_STYLE_KEY = "shape/average_cross_section"
	SHAPE_TITLE = TITLE


class StxmRectangleTool(AverageCrossSectionTool):
	SWITCH_TO_DEFAULT_TOOL = True
	TITLE = _('')
	ICON = "rectangle.png"
	SHAPE_STYLE_KEY = "shape/average_cross_section"
	SHAPE_TITLE = TITLE
	#PANEL_IDS = []


class StxmSegmentTool(AnnotatedSegmentTool):
	SWITCH_TO_DEFAULT_TOOL = True
	TITLE = _('SEG')
	ICON = "segment.png"
	SHAPE_STYLE_KEY = "shape/segment"


class StxmPointTool(AnnotatedPointTool):
	SWITCH_TO_DEFAULT_TOOL = True
	TITLE = _('PNT')
	ICON = "point.png"
	SHAPE_STYLE_KEY = "shape/point"


class SquareAspectRatioTool(ToggleTool):
	changed = QtCore.pyqtSignal(bool)
	
	def __init__(self, manager, plot, icon="aspect.png", tip="Force aspect Ratio to be square"):
		super(SquareAspectRatioTool, self).__init__(manager, _("Force aspect ratio to a square"), icon)
		self.plot = plot
		self.ischecked = False
		self.manager = plot.manager
		self.action = self.manager.create_action(_("SquareAspectRatioTool"),toggled=self.toggle_ischecked, icon=get_icon(icon), tip=tip)
		self.toolbar = plot.manager.get_default_toolbar()
		self.toolbar.addAction(self.action)
		self.action.setEnabled(False)
		self.action.setIconText("")
		#self.default_icon = build_icon_from_cmap(get_cmap("gist_gray"), width=16, height=16)
		self.default_icon = get_icon(icon)
		self.action.setIcon(self.default_icon)

	def toggle_ischecked(self, checked):
		print('SquareAspectRatioTool: toggle_ischecked: item is ' , checked) 
		self.ischecked = checked
		self.changed.emit(checked)

	def activate_command(self, plot, checked):
		print('SquareAspectRatioTool: activate_command: item is ' , checked) 
		self.ischecked = checked

	#def update_status(self, plot):
	#	self.action.setChecked(self.ischecked)
	
	def update_status(self, plot):
		if update_image_tool_status(self, plot):
			item = plot.get_items(item_type=ICSImageItemType)
			#icon = self.default_icon
			if item:
				self.action.setEnabled(True)
			#if item.get_color_map_name():
			#	icon = build_icon_from_cmap(item.get_color_map(),width=16, height=16)
			else:
				self.action.setEnabled(False)
		#self.action.setIcon(icon)

class StxmOpenFileTool(CommandTool):
	def __init__(self, manager, formats='*.*', toolbar_id=DefaultToolbarID):
		CommandTool.__init__(self, manager, _("Open..."),
							 get_std_icon("DialogOpenButton", 16),
							 toolbar_id=toolbar_id)
		self.formats = formats
		self.directory = ""
	
	def set_directory(self, dirname):
		self.directory = dirname
		
	def get_filename(self, plot):
		saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
		sys.stdout = None
		filename, _f = getopenfilename(plot, _("Open"),
									   self.directory, self.formats)
		sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
		filename = str(filename)
		if filename:
			self.directory = osp.dirname(filename)
		return filename
		
	def activate_command(self, plot, checked):
		"""Activate tool"""
		filename = self.get_filename(plot)
		if filename:
			self.emit(SIGNAL("openfile(QString*)"), filename)

class ximImageParams(object):
	"""
	A class to represent an XIM image, the min/max values are in units and are used for the plotting axis information
	"""
	def __init__(self, data, xmin, xmax, ymin, ymax, units='um'):
		super(ximImageParams, self).__init__()
		self.data = data
		self.datashape = data.shape
		self.xmin = xmin
		self.xmax = xmax
		self.ymin = ymin
		self.ymax = ymax
	
		


 
def dumpObj(obj):
	print('dumpObj: ') 
	print(obj)
	for i in list(obj.__dict__.keys()):
		print("%s : %s" % (i, obj.__dict__[i]))


class InputState(object):
	def __init__(self):
		
		self.keyisPressed = {}
		self.keyisPressed[Qt.Key_X] = False
		self.keyisPressed[Qt.Key_Y] = False
		#self.keyisPressed[Qt.Key_Space] = False
		self.keyisPressed[Qt.Key_Alt] = False
		self.keyisPressed[Qt.Key_F1] = False	#for emitting a new_roi_center
		
		
		self.btnisPressed = {}
		self.btnisPressed[Qt.LeftButton] = False
		self.btnisPressed[Qt.MiddleButton] = False
		self.btnisPressed[Qt.RightButton] = False
		
		
		#represents the delta values
		self.center = (0.0, 0.0)
		self.range = (0.0, 0.0)
		self.npts = (0, 0)
		
		
class StxmImageWidget(ImageDialog):
	
	implements(IPlotter)
	
	new_region = pyqtSignal(object)
	region_changed = pyqtSignal(object)
	region_deleted = pyqtSignal(object)
	region_selected = pyqtSignal(object)
	new_ellipse =  pyqtSignal(object)
	target_moved =  pyqtSignal(object)
	new_roi_center =  pyqtSignal(object)
	
	
	#def __init__(self, parent, filtStr = "*.json;*.hdr",ht=200, wd=200, testing=False, type='basic', options=None):
	def __init__(self, parent, filtStr = "*.json;*.hdr", testing=False, type='basic', options=None):
		
		#init this first because the constructor for ImageDialog will call our 
		#over ridden 'register_tools' function which needs this param
		self.type = type
		if(self.type == 'basic'):
			self.register_tools = self.register_basic_tools
		elif(self.type == 'select'):
			self.register_tools = self.register_select_tools
		else:
			self.register_tools = self.register_analyze_tools
			
		self.fileFilterStr = filtStr
		self.data = None 
		self.dataHeight = 0
		self.dataWidth = 0
		self.wPtr = 0
		self.hPtr = 0
		self.xstep = 1.0
		self.ystep = 1.0
		self._data_dir = ""
		
		#scalars for non-square data
		self.htSc = 1
		self.widthSc = 1
		self.item = None
		self.dataAtMax = False		
		self.image_is_new = True
		
		self.roiNum = 0
		self.segNum = 0
		self.pntNum = 0

		# transform factors for pixel to unit conversion		
		self.xTransform = 0.0
		self.yTransform = 0.0
		self.zTransform = 0.0
		self.unitTransform = 'um'
		
		#gridparam = make.gridparam(background="#6b6b6b", 
		#						   minor_enabled=(False, False), 
		#						   major_enabled=(False,False))
		
		gridparam = make.gridparam(background="#555555", 
								   minor_enabled=(False, False), 
								   major_enabled=(False,False))
		
		if(options is None):
			options=dict(show_xsection=True, show_ysection=True,
				xlabel=("um", ""), ylabel=("um", ""), zlabel=None, 
				show_contrast=True, xsection_pos="top", ysection_pos="right",
				lock_aspect_ratio=True, gridparam=gridparam, colormap="gist_gray")
		
		self.sel_item_id = None
		
		ImageDialog.__init__(self, parent = parent,  wintitle="", edit = False, toolbar=True, options=options)
		
		self.layout().setContentsMargins(2)
		self.layout().setSpacing(2)
		
		self.setMinimumSize(400,300)
		self.checkRegionEnabled = True
		#setup some default values
		self.max_roi = 100000
		self.max_seg_len = 1000
		
		self.zoom_scale = 1.0
		self.zoom_rngx = 1.0
		self.zoom_rngy = 1.0
		
		#create an instance of InputState so that I can 
		#connect key presses with mouse events
		self.inputState = InputState()
		
		self.filtVal = 0
#		self.curFilterStr = 'gaussian_filter'
#		self.filterfunc = getattr(scipy.ndimage, self.curFilterStr)
#		self.filterPanel = self.loadFilterPanel(self)
#		self.layout().addWidget(self.filterPanel)
		self.plot = self.get_plot()
		
		xcs = self.get_xcs_panel()
		xcs.set_options(autoscale=True)
		xcs.cs_plot.toggle_perimage_mode(True)
		ycs = self.get_ycs_panel()
		ycs.set_options(autoscale=True)
		ycs.cs_plot.toggle_perimage_mode(True)
			
		self.plot.plotLayout().setContentsMargins(0,0,0,0)
		self.plot.plotLayout().setCanvasMargin(0)
		self.plot.plotLayout().setAlignCanvasToScales(True)
		
		# set legend
		self.legend = Qwt.QwtLegend()
		self.legend.setItemMode(Qwt.QwtLegend.CheckableItem)
		#self.plot.insertLegend(self.legend, Qwt.QwtPlot.RightLegend)
		self.plot.insertLegend(self.legend, Qwt.QwtPlot.BottomLegend)
		
		#the base image is already created, just make the legend item looked clicked on
		#here I need to normalize the data such that it is a square for display purposes
		#self.initData(ht, wd)
		#imageItem = self.plot.get_items(item_type=ICSImageItemType)
		#self.image = imageItem
		#self._toggleVisibility(imageItem[0], True)
		
		self.connect(self.plot, SIG_ITEM_SELECTION_CHANGED, self.selected_item_changed)
		self.connect(self.plot, SIG_ITEMS_CHANGED, self.items_changed)
		self.connect(self.plot, SIG_ITEM_MOVED, self.active_item_moved)
		self.connect(self.plot, SIG_ANNOTATION_CHANGED, self.annotation_item_changed)
		self.connect(self.plot, SIG_MARKER_CHANGED, self.marker_changed)
		self.connect(self.plot, SIG_TOOL_JOB_FINISHED, self.shape_end_rect)
		self.connect(self.plot, SIG_ACTIVE_ITEM_CHANGED, self.on_active_item_changed)
		self.connect(self.plot,	SIG_PLOT_AXIS_CHANGED, self.on_sig_plot_axis_changed)
		
		self.connect(self.plot, SIGNAL('legendChecked(QwtPlotItem*, bool)'), self._toggleVisibility)
		self.connect(self.plot, SIGNAL('MouseButtonRelease(QMouseEvent)'), self.mouseReleaseEvent)
		
		#force the plot axis to make vertical 0 at the bottom instead of the default of top
		self.plot.set_axis_direction('left', False)
		
		# force the plot to snap to fit the current plot in 
		self.set_autoscale()
		self.plot.unselect_all()
		
		if(testing):
			self.tstTimer = QTimer()
			self.connect(self.tstTimer, SIGNAL("timeout()"), self.tstDataPoint)
			self.tstTimer.start(10)
		else:
			self.tstTimer = None
			
		self.set_grid_parameters("#323232","#343442","#545454")
			
		
			
	############## INTERFACE ROUTINES ####################		
	#def load_file_data(self, data):
	#	""" set the plotting data to data """
	#	pass
		
	#def add_data(self, data):
	#	""" append data to the current plotting data """
	#	pass
	def update(self):
		""" force and update to the plot """
		pass
		
	def get_selected_data(self, rangeX, rangeY):
		""" return the selected data as a numpy array """
		pass
	
	def get_data(self):
		""" return all of the plotting data as a numpy array"""
		return(self.data)
	
	
	############## End of INTERFACE ROUTINES ####################
#	 def register_tools(self):
#		 self.register_select_tools()  
		
	def register_select_tools(self):
		self.opentool = self.add_tool(StxmOpenFileTool, formats=self.fileFilterStr)
		self.opentool.set_directory(self._data_dir)
		self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)

		self.selectTool = self.add_tool(SelectTool)
		self.add_tool(BasePlotMenuTool, "item")
		self.add_tool(ColormapTool)
		self.add_separator_tool()
		self.add_tool(PrintTool)
		self.add_tool(DisplayCoordsTool)
		self.add_separator_tool()
		self.addTool('SquareAspectRatioTool')
		self.add_separator_tool()
		
		self.add_tool(ReverseYAxisTool)
		
		rt = StxmRectangleTool
		rt.TITLE = _("2D Region")
		rt.create_shape = self._create_rect_shape
		at = self.add_tool(rt, setup_shape_cb=self._setup_rect_shape, handle_final_shape_cb=self._handle_final_rect_shape)
		
		ast = StxmSegmentTool
		#ast.create_shape = self._create_seg_shape
		aa = self.add_tool(ast, setup_shape_cb=self._setupsegment, handle_final_shape_cb=self.newsegment)
		aa.TITLE = _("%s %d" % (SPATIAL_TYPE_PREFIX[SEG], self.segNum))
		
		
		#apt = AnnotatedPointTool
		apt = StxmPointTool
		#apt.create_shape = self._create_point_shape
		ap = self.add_tool(apt, setup_shape_cb=self.setuppoint,handle_final_shape_cb=self.newpoint)
		ap.TITLE = _("selecting")
		
		self.set_default_tool(self.selectTool)
		self.get_default_tool().activate()

	def register_analyze_tools(self):
		#opentool = self.add_tool(OpenFileTool, "*.json;*.hdr;*.tif;*.jpg")
		#opentool = self.add_tool(OpenFileTool, self.fileFilterStr)
		self.opentool = self.add_tool(StxmOpenFileTool, formats=self.fileFilterStr)
		self.opentool.set_directory(self._data_dir)
		self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)
		self.add_tool(ReverseYAxisTool)
		self.add_tool(SaveAsTool)

		self.add_separator_tool()
		
		self.addTool('SquareAspectRatioTool')
		
		self.add_separator_tool()
		
		self.selectTool = self.add_tool(SelectTool)
		self.add_tool(BasePlotMenuTool, "item")
		self.add_tool(ColormapTool)
		#self.add_tool(XCSPanelTool)
		self.add_tool(YCSPanelTool)
		self.add_tool(SnapshotTool)
		self.add_tool(RectZoomTool)

		self.add_separator_tool()
		
		self.add_tool(PrintTool)
		self.add_tool(DisplayCoordsTool)
		self.add_separator_tool()

		art = StxmAverageCrossSectionTool
		art.TITLE = _("selecting")
		art.create_shape = self._create_rect_shape
		at = self.add_tool(art, setup_shape_cb=self._setup_rect_shape, handle_final_shape_cb=self._handle_final_rect_shape)
	
		ast = AnnotatedSegmentTool
		#ast.create_shape = self._create_seg_shape
		aa = self.add_tool(ast, setup_shape_cb=self._setupsegment, handle_final_shape_cb=self.newsegment)
		aa.TITLE = _("selecting")
		
		self.set_default_tool(self.selectTool)
		self.get_default_tool().activate()
	
	def register_basic_tools(self):
		self.opentool = self.add_tool(StxmOpenFileTool, formats=self.fileFilterStr)
		self.opentool.set_directory(self._data_dir)
		self.connect(self.opentool, SIGNAL("openfile(QString*)"), self.openfile)
		
		self.selectTool = self.add_tool(SelectTool)
		self.add_tool(BasePlotMenuTool, "item")
		self.add_tool(ColormapTool)
		self.add_tool(SnapshotTool)
		self.add_separator_tool()
		
		self.add_tool(PrintTool)
		
		self.set_default_tool(self.selectTool)
		self.get_default_tool().activate()
	
	def addTool(self, toolstr):
		""" a function that allows inheriting widgets to add tools
		where tool is a valid guiqwt tool """
		
		if(toolstr == 'LabelTool'):
			self.add_tool(LabelTool)
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
		elif(toolstr == 'SquareAspectRatioTool'):
			#at = self.add_tool(SquareAspectRatioTool, self.get_plot())
			#at.changed.connect(self.on_set_aspect_ratio)
			sqrAsptool = self.add_tool(SquareAspectRatioTool, self.get_plot())
			#at.changed.connect(self.on_set_aspect_ratio)
			self.connect(sqrAsptool, SIGNAL("changed(bool)"), self.on_set_aspect_ratio)
		elif(toolstr == 'StxmAverageCrossSectionTool'):	
			art = StxmAverageCrossSectionTool
			art.TITLE = _("selecting")
			art.create_shape = self._create_rect_shape
			at = self.add_tool(art, setup_shape_cb=self._setup_rect_shape, handle_final_shape_cb=self._handle_final_rect_shape)
	
	def set_grid_parameters(self, bkgrnd_color, min_color, maj_color):
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
		aplot.grid.set_item_parameters({"GridParam":gparam})
		
		aplot.ensurePolished()
		aplot.polish()
		aplot.invalidate()
		aplot.replot()
		aplot.update_all_axes_styles()
		aplot.update()
	
	def set_cs_grid_parameters(self, forgrnd_color, bkgrnd_color, min_color, maj_color):
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
		plot = self.plot
		xcs = self.get_xcs_panel()
		ycs = self.get_ycs_panel()
		xcs.cs_plot.label.hide()
		ycs.cs_plot.label.hide()
		
		#self.curve_item.update_params()
		#csi = xcs.cs_plot.get_items(item_type=XCrossSectionItem)
		
		#csi = xcs.cs_plot.get_items(item_type=ICurveItemType)
		#print csi
		
		#csi.curveparam._shade = 0.75
		
		
		#cparam = CurveParam()
		#cparam.line._color = forgrnd_color
		#cparam._shade = 0.75
		
		#xcs.cs_plot.set_item_parameters({"CurveParam":cparam})
		#ycs.cs_plot.set_item_parameters({"CurveParam":cparam})
		
		gparam = GridParam()
		gparam.background = bkgrnd_color
		gparam.maj_line.color = maj_color
		gparam.min_line.color = min_color
		xcs.cs_plot.grid.set_item_parameters({"GridParam":gparam})
		ycs.cs_plot.grid.set_item_parameters({"GridParam":gparam})
		
		xcs.cs_plot.ensurePolished()
		ycs.cs_plot.ensurePolished()
		
		xcs.cs_plot.polish()
		ycs.cs_plot.polish()
		
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
		set a durectory to use when calling openfile()
		"""
		return(self._data_dir)
	
	def set_data_dir(self, ddir):
		"""
		set a durectory to use when calling openfile()
		"""
		self._data_dir = ddir
		self.opentool.set_directory(self._data_dir)
	
	def on_set_aspect_ratio(self, force):
		print('on_set_aspect_ratio: called')
		if(hasattr(self, 'data')):
			h, w = self.data.shape
			if(force):
				if(h > w):
					r = float(h/w)
				else:
					r = float(w/h)					
				#print 'forcing aspect ratio to square'
				print('on_set_aspect_ratio: h=%d w = %d,  ratio = %f' % (h, w, r))
				self.plot.set_aspect_ratio(ratio=r)
			else:
				#print 'resetting to original aspect ratio'
				self.plot.set_aspect_ratio(ratio=1)
			#self.plot.replot()
			self.set_autoscale()
		
	def setColorMap(self, cmap_name):
		self.color_map_str = cmap_name
		itemList = self.plot.get_items(item_type=ICSImageItemType)
		item = itemList[0]
		item.imageparam.colormap = cmap_name
		item.imageparam.update_image(item)
		#self.action.setText(cmap_name)
		self.plot.invalidate()
		#self.update_status(plot)
	
	def _toggleVisibility(self, item, on):
		item.setVisible(on)
		widget = self.plot.legend().find(item)
		if isinstance(widget, Qwt.QwtLegendItem):
			widget.setChecked(on)
			
		if(on):
			self.plot.set_active_item(self.item)
			
		self.plot.replot()
			
	def _setup_rect_shape(self,shape):
		#print 'in _setup_rect_shape'
		pass

	def setCheckRegionEnabled(self, val):
		self.checkRegionEnabled = val
		
	def _setupsegment(self,seg):
		seg.setTitle("%s %d" % (SPATIAL_TYPE_PREFIX[SEG], self.segNum))
		
	def _drawSegment(self, rect):
		print('stxmImageWidget: _drawSegment')

	def _resizeItem(self, item, center, size, angle):
		A,B,C,E,F,G,I,D,H = calcRectPoints(center, (size[0],size[1]), angle)
		item.set_rect(E.x(), E.y(), I.x(), I.y())
		annotation = True
		if(annotation):
			item.shape.set_xdiameter(D.x(), D.y(), H.x(), H.y())
			item.shape.set_ydiameter(F.x(), F.y(), B.x(), B.y())
			dct = item.get_infos()
			self.new_ellipse.emit(dct)
			#print dct
		else:
			item.set_xdiameter(D.x(), D.y(), H.x(), H.y())
			item.set_ydiameter(F.x(), F.y(), B.x(), B.y())
		
		#set cross_marker to visible and place it at center 
		self.plot.cross_marker.set_display_label(False)
		self.plot.cross_marker.setZ(self.plot.get_max_z()+1)
		self.plot.cross_marker.setVisible(True)
		#r = QRect(10,50,100,100)
#		r = QRect(E.x(),E.y(),I.x(),I.y())
#		x,y = self.plot.cross_marker.axes_to_canvas(r.topLeft().x(), r.topLeft().y())
#		tl = QPoint(x,y)
#		x,y = self.plot.cross_marker.axes_to_canvas(r.bottomRight().x(), r.bottomRight().y())
#		br = QPoint(x,y)
#		self.plot.do_zoom_rect_view(tl, br)
		
		#x,y = self.plot.cross_marker.axes_to_canvas(r.center().x(), r.center().y())
		x,y = self.plot.cross_marker.axes_to_canvas(A.x(), A.y())
		c = QPoint(x,y)
		self.plot.cross_marker.move_local_point_to(0,c)
		self.plot.cross_marker.setVisible(False)
		self.plot.cross_marker.emit_changed()
		del(c)

	def create_target_circle(self, xc, yc, val):
		from guiqwt.styles import ShapeParam
		#circ = make.annotated_circle(x0, y0, x1, y1, ratio, title, subtitle)
		rad = val/2.0
		circ = make.annotated_circle(xc-rad, yc+rad, xc+rad, yc-rad, 1, 'Target')
		sh = circ.shape.shapeparam
		#circ.set_resizable(False)
		#offset teh annotation so that it is not on the center
		circ.shape.shapeparam.fill = circ.shape.shapeparam.sel_fill
		circ.shape.shapeparam.line = circ.shape.shapeparam.sel_line
		circ.label.C = (50,50)
		circ.set_label_visible(False)
		#print circ.curve_item.curveparam
		#circ.set_style(, option)
		circ.shape.set_item_parameters({"ShapeParam":circ.shape.shapeparam})
		self.plot.add_item(circ)
		
	
	
	def addPlotItem(self, item):
		plot = self.get_plot()
		plot.add_item(item)
		self.update()
		plot.replot()
		
	def addPlotItems(self, items):
		plot = self.get_plot()
		for item in items:
			plot.add_item(item)
		self.update()
		plot.replot()


	def newsegment(self,seg):
		seg.setTitle("%s %d" % (SPATIAL_TYPE_PREFIX[SEG], self.segNum))
		seg.setItemAttribute(Qwt.QwtPlotItem.Legend);
		widget = self.plot.legend().find(seg)
		if isinstance(widget, Qwt.QwtLegendItem):
			widget.setChecked(True)
		
		ret = self._anno_seg_to_region(seg)
		self.new_region.emit(ret)
		self._select_this_item(seg)
		self.update()
		
		
	def setuppoint(self,point):
		#print 'in setuppoint'
		pass 
		#point.setTitle("%s %d" % (SPATIAL_TYPE_PREFIX[PNT], self.pntNum))

	def shape_end_rect(self, shape):
		#print shape
		pass	
		
	def newpoint(self,point):
		#print 'in new point: %s' % point.annotationparam.title
		#point.setTitle("Point %d" % self.pntNum)
		point.setTitle("%s %d" % (SPATIAL_TYPE_PREFIX[PNT], self.pntNum))
		#point.position_and_size_visible = False
		point.setItemAttribute(Qwt.QwtPlotItem.Legend);
		widget = self.plot.legend().find(point)
		if isinstance(widget, Qwt.QwtLegendItem):
			widget.setChecked(True)

		ret = self._anno_point_to_region(point)
		self.new_region.emit(ret)
		self._select_this_item(point)
		self.update()
		
	def selected_item_changed(self, plot):
		#print 'selected_item_changed: '
		item = plot.get_active_item()
		if(item): 
			#this is often the last event fired so just double check that the 
			#colors are set right
			rect = self._check_valid_region(item)
			#print item.title().text()
			self.sel_item_id = str(item.title().text())
			self.region_selected.emit(self.sel_item_id)
			
			if(hasattr(item, 'is_label_visible')):
				item.set_label_visible(True)
				#if not item.is_label_visible():
				#	item.set_label_visible(True)
	
	def on_sig_plot_axis_changed(self, plot):
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
		
		cx = (x1 + x2)/2
		rx = x2 - x1
		
		cy = (y1 + y2)/2
		ry = y2 - y1
		
		self.inputState.center = (cx , cy)
		self.inputState.range = (rx , ry)
		
		#print 'Center: ', self.inputState.center
		#print 'Range:',self.inputState.range
		
		dct = {}
		dct['center'] = (cx , cy)
		dct['size'] = (rx , ry)
		dct['npts'] = (None , None)
		
		#only emit a new_roi_center if the user has the F1 pressed
		
		if(self.inputState.keyisPressed[Qt.Key_F1]):
			self.new_roi_center.emit(dct)
		
		#rngy = grid.yScaleDiv().range()
		#self.zoom_scale = (self.zoom_rngx/rngx) 
		#print 'Zoom Scale = %.2f' % self.zoom_scale
			
	def items_changed(self, plot):
		items = plot.get_items()
		#disable region select tool
		self.get_default_tool().activate()
	
	def Image_changed(self, items):
		for i in items:
			print('Image_changed:')
			print(i.title().text())
			#print i.get_rect()
	
	def AnnotatedRectangle_changed(self, items):
		pass
		#for i in items:
			#print 'AnnotatedRectangle_changed: '
			#print i.title().text()
			#print i.get_rect()
		
	def active_item_moved(self, item):
		if hasattr(item, 'annotationparam'):
			if(item.annotationparam.title == 'Target'):
				cntr = item.get_center()
				(self.zoom_scale, dud) = item.get_tr_size()
				self.zoom_scale = self.zoom_scale*0.75
				self.target_moved.emit(cntr)
			else:
				dct = {}
				dct['center'] = item.get_center()
				dct['size'] = item.get_tr_size()
				dct['npts'] = (None , None)
				self.inputState.center = dct['center']
				self.inputState.range = dct['size']
				if(self.inputState.keyisPressed[Qt.Key_Alt]):
					self.new_roi_center.emit(dct)
		else:
			print('active_item_moved: event for this item not handled' , item)
		

	def set_transform_factors(self, x, y, z, unit):
		self.xTransform = x
		self.yTransform = y
		self.zTransform = z
		self.unitTransform = unit
		
	def reset_transform_factors(self):
		self.xTransform = 1.0
		self.yTransform = 1.0
		self.zTransform = 1.0
		self.unitTransform = 'um'
	
	def _anno_point_to_region(self, item):
		""" convert an annotated point item to a region dict"""
		(x1,y1) =  item.get_pos()
		cntr = (x1, y1)
		sz = (1,1)
		ret = {}
		ret['type'] = SPATIAL_TYPE_PREFIX[PNT]
		ttl = str(item.title().text())
		if(ttl == 'selecting'):
			ttl = '%s %d' % (SPATIAL_TYPE_PREFIX[PNT], self.pntNum)
			item.setTitle(ttl)
		ret['name'] = ttl
		ret['center'] = cntr
		ret['size'] = sz
		ret['startstop'] = (x1, x1, y1, y1)
		return(ret)
	
	def _anno_seg_to_region(self, item):
		""" convert an annotated segment item to a region dict"""
		(x1,y1,x2,y2) =  item.get_rect()
		cntr = ((x1+x2)/2.0, (y2+y1)/2.0)
		sz = (item.get_tr_length(), item.get_tr_length())
		ret = {}
		ret['type'] = SPATIAL_TYPE_PREFIX[SEG]
		ret['name'] = str(item.title().text())
		ret['center'] = cntr
		ret['size'] = sz
		ret['startstop'] = (x1, x2, y1, y2)
		return(ret)
	
	def _anno_spatial_to_region(self, item):
		""" convert an annotated rectangle item to a region dict""" 
		cntr = item.get_tr_center()
		sz = item.get_tr_size()
		strtstop = self._centersize_to_startstop(cntr, sz)
		ret = {}
		ret['type'] = SPATIAL_TYPE_PREFIX[TWO_D]
		ret['name'] = str(item.title().text())
		ret['center'] = cntr
		ret['range'] = sz
		ret['startstop'] = strtstop
		return(ret)
	
	def _region_name_to_item(self, region_name):
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
					#print 'select_region: %s' % region_name
					#print 'item.text() = %s' %(str(item.title().text()))
					#
					item.set_label_visible(True)
				else:
					item.set_label_visible(False)
		
		self.plot.replot()
	
	def _select_this_item(self, item):
		""" 
		this function is used to deselect everything on the plot
		and make the current item selected as well as make the annotation visible, 
		without this the point and segment shapes do not stay selected after they have been
		created, seems to fix a bug in guiqwt
		"""
		self.plot.unselect_all()
		self.plot.select_item(item)
		self.plot.set_active_item(item)
		item.set_label_visible(True)		
	
	
	def on_active_item_changed(self, item):
		#print 'on_active_item_changed'
		#print item
		pass
	
	
	def annotation_item_changed(self, item):
		#print 'annotation_item_changed'
# 		dct = {}
# 		dct['center'] = item.get_center()
# 		dct['size'] = item.get_tr_size()
# 		self.new_roi_center.emit(dct)
		
		if isinstance(item, AnnotatedPoint):
			rect = item.get_pos()
			qrect = QRect(QPoint(rect[0],rect[1]),QPoint(1, 1))
			ret = self._anno_point_to_region(item)
		
		elif isinstance(item, AnnotatedSegment):
			qrect = self._check_valid_region(item)
			if(item.annotationparam.title == ''):
				(title, tfm, format) = self._get_seg_anno_params()
				item.annotationparam.title = title
			ret = self._anno_seg_to_region(item)

		elif isinstance(item, RectangleShape):
			print('Im a RectangleShape')
		elif isinstance(item, AnnotatedRectangle):
			#handle the user selecting a new ROI for a coarse scan
			dct = {}
			dct['center'] = item.get_center()
			dct['size'] = item.get_tr_size()
			dct['npts'] = (None , None)
			self.inputState.center = dct['center']
			self.inputState.range = dct['size']
			self.inputState.npts = dct['npts']
			self.new_roi_center.emit(dct)

			qrect = self._check_valid_region(item)
			if(hasattr(item, "get_tr_center")):
				ret = self._anno_spatial_to_region(item)
		elif isinstance(item, AnnotatedCircle):
			qrect = self._check_valid_region(item)
			if(hasattr(item, "get_tr_center")):
				ret = self._anno_spatial_to_region(item)
		elif isinstance(item, AnnotatedEllipse):
			qrect = self._check_valid_region(item)
			if(hasattr(item, "get_tr_center")):
				ret = self._anno_spatial_to_region(item)
		
		if(self.xTransform > 0.0):
			item.annotationparam.transform_matrix = [[ self.xTransform,  0.0,  0.0],[ 0.0, self.yTransform,  0.0],[ 0.0,  0.0,  self.zTransform]]
			item.annotationparam.format = '%5.2f ' + self.unitTransform
		else:
			item.annotationparam.transform_matrix = [[ self.xstep,  0.0,  0.0],[ 0.0, self.ystep,  0.0],[ 0.0,  0.0,  1.0]]
			item.annotationparam.format = '%5.2f um'
		
		item.apply_transform_matrix(1, 1)	
		item.set_label_visible(True)
		
		self.region_changed.emit(ret)
		
		
		
	def _restrict_rect(self, r):
		x2 = r[2]
		y2 = r[3]
		#if they are negative restrict them so they aren't
		if(r[2] <= r[0]):
			x2 = r[0] + 1
		if(r[3] <= r[1]):
			y2 = r[1] + 1
		
		rect = QRect(QPoint(r[0],r[1]),QPoint(x2,y2))
		return(rect)
	
	def _check_valid_region(self, item):
		#print '_check_valid_region'
		if(self.checkRegionEnabled):
			
			if isinstance(item, AnnotatedPoint):
				pass  
			elif isinstance(item, AnnotatedSegment):
				#print 'in AnnotatedSegment'
				r = item.get_rect()
				sh = item.shape.shapeparam
				qrect = self._restrict_rect(r)
				#get the distance measurement straight from the item.get_infos()
				#{'distance': (u'Distance:', '%5.2f um', 139.13994758083288)}
				#sel_len = item.get_infos()['distance'][2]
				sel_len = item.get_tr_length()
				
				if(sel_len > self.max_seg_len):
					#print 'SEG: setting color red: #ff0000 alpha is ff'
					lineWidth = 5
					lineStyle = Qt.DashLine
					lineColor = QtGui.QColor(255, 0, 0, 255)
					
				else:
					#print 'SEG: setting color green #00ff00 alpha is ff'
					lineWidth = 1
					lineStyle = Qt.SolidLine
					lineColor = QtGui.QColor(0, 255, 0, 255)
	
				item.shape.sel_pen.setStyle(lineStyle)
				item.shape.sel_pen.setWidth(lineWidth)
				item.shape.sel_pen.setColor(lineColor)
				item.shape.pen.setStyle(lineStyle)
				item.shape.pen.setWidth(lineWidth)
				item.shape.pen.setColor(lineColor)
					
				sh.update_param(item.shape)
				return(qrect)
			
			elif isinstance(item, AnnotatedRectangle):
				r = item.get_rect()
				sh = item.shape.shapeparam
				#if the area being slected is larger than max change color to red
				qrect = self._restrict_rect(r)
				sel_area = qrect.width() * qrect.height()
				if(sel_area > self.max_roi):
					#print 'setting color red: #ff0000 alpha is ff'
					item.shape.sel_brush.setColor(QtGui.QColor(255, 0, 0, 255))
				else:
					#print 'setting color green #14ff00 alpha is 42'
					item.shape.sel_brush.setColor(QtGui.QColor(20, 255, 0, 66))
					
				sh.update_param(item.shape)
				return(qrect)
	
	def on_update_region(self, data):
		#print 'stxmImageWidget: on_update_region'
		#print data
		pass
		
	def set_cs_label_text(self, cs, msg):
		label = self.get_cs_label_item(cs)
		if(label):
			label.set_text(msg)
		else:
			label = make.label(_(msg), "TL", (0,0), "TL")
			cs.cs_plot.add_item(label)
		cs.cs_plot.update_plot()

	def get_cs_label_item(self, cs):
		items = cs.cs_plot.get_items()
		for item in items:
			if(isinstance(item, LabelItem)):
				if(item.isVisible()):
					return(item)
		return(None)
	
	def get_cs_item(self, cs):
		e = enumerate(cs.cs_plot.known_items.items())
		#if(len(e) > 0):
		for d in e:
			#d = e.next()
			#(0, (<guiqwt.image.ImageItem object at 0x053CB030>, <guiqwt.cross_section.XCrossSectionItem object at 0x05C8C660>))
			csi = d[1][1]
			#<guiqwt.cross_section.XCrossSectionItem object at 0x05C8C660>
			return(csi)
		#or if there are any then
		return(None)	
			
	def dump_cross_section_panels(self, x, y):
		xcs = self.get_xcs_panel()
		ycs = self.get_ycs_panel()
		
		xcsi = self.get_cs_item(xcs)
		ycsi = self.get_cs_item(ycs)
		
		if(xcsi != None):
			datx = xcsi._y
		if(ycsi != None):
			daty = ycsi._x
		
	def marker_changed(self, marker):
		dct = {}
		dct['center'] = marker.get_pos()
		dct['size'] = (None, None)
		dct['npts'] = (None , None)
		self.inputState.center = dct['center']
		
		if(self.inputState.keyisPressed[Qt.Key_Alt]):
			self.new_roi_center.emit(dct)
		

	def _centersize_to_startstop(self, _center, _size):
		""" center and size are in units (um) """
		centX, centY = _center
		szX, szY = _size
		
		startX = centX - (szX * 0.5)
		stopX = centX + (szX * 0.5)
		startY = centY - (szY * 0.5)
		stopY = centY + (szY * 0.5)
		#print (startX, stopX, startY, stopY)
		return((startX, stopX, startY, stopY))

	def _handle_final_rect_shape(self,shape):
		#print '_handle_final_rect_shape: %s' % shape.annotationparam.title
		#print shape.shape.shapeparam
		#shape.annotationparam.subtitle = 'my _handle_final_rect_shape'
		shape.setTitle('%s %d' % (SPATIAL_TYPE_PREFIX[TWO_D], self.roiNum))
		shape.annotationparam.title = '%s %d' % (SPATIAL_TYPE_PREFIX[TWO_D], self.roiNum)
		
		rect = self._check_valid_region(shape)
		shape.position_and_size_visible = False
		shape.setItemAttribute(Qwt.QwtPlotItem.Legend);
		widget = self.plot.legend().find(shape)
		if isinstance(widget, Qwt.QwtLegendItem):
			widget.setChecked(True)
		
		ret = self._anno_spatial_to_region(shape)
		self.new_region.emit(ret)
	
	
	def _create_rect_shape(self):
		#print '_create_rect_shape:'
		ap = AnnotationParam()
		#ap.subtitle = 'my _create_rect_shape'
		ap.title = 'selecting'
		#ap.title = '%s %d' % (SPATIAL_TYPE_PREFIX[TWO_D], self.roiNum)
		ap.transform_matrix = [[ self.xstep,  0.0,  0.0],[ 0.0, self.ystep,  0.0],[ 0.0,  0.0,  1.0]]
		ap.format = '%5.2f um'
		return AnnotatedRectangle(0, 0, 1, 1, annotationparam = ap), 0, 2  

	def _get_seg_anno_params(self):
		title = '%s %d' % (SPATIAL_TYPE_PREFIX[SEG], self.segNum)
		#title = 'selecting'
		transform_matrix = [[ self.xstep,  0.0,  0.0],[ 0.0, self.ystep,  0.0],[ 0.0,  0.0,  1.0]]
		format = '%5.2f um'
		return(title, transform_matrix, format)
		
	def _create_seg_shape(self):
		""" this is called when the user lets go of the left mouse button at teh end if the drag """
		#print '_create_seg_shape:'
		ap = AnnotationParam()
		ap.title = '%s %d' % (SPATIAL_TYPE_PREFIX[SEG], self.segNum)
		#ap.title = 'selecting'
		ap.transform_matrix = [[ self.xstep,  0.0,  0.0],[ 0.0, self.ystep,  0.0],[ 0.0,  0.0,  1.0]]
		ap.format = '%5.2f um'
		return AnnotatedSegment(0, 0, 1, 1, annotationparam = ap), 0, 2  

	def _create_point_shape(self):
		#print '_create_point_shape:'
		ap = AnnotationParam()
		ap.title = '%s %d' % (SPATIAL_TYPE_PREFIX[PNT], self.pntNum)
		#ap.title = 'selecting:'
		ap.transform_matrix = [[ self.xstep,  0.0,  0.0],[ 0.0, self.ystep,  0.0],[ 0.0,  0.0,  1.0]]
		ap.format = '%5.2f um'
		return AnnotatedPoint(0, 0, annotationparam = ap), 0, 0 

	def _pretty(self, d, indent=1):
		for key, value in d.items():
			print('\t' * indent + str(key))
			if isinstance(value, dict):
				self._pretty(value, indent+1)
			else:
				print('\t' * (indent+1) + str(value))

	
	def initData(self, prefix, rows, cols, parms={}):
		#scalars for non-square data
		self.htSc = 1
		#print 'stxmImageWidget: initData(%d, %d)' % (cols, rows)
		self.widthSc = 1
		array = np.ones((rows,cols), dtype=np.int32)
		self.data = array
		[self.dataHeight, self.dataWidth] = self.data.shape
		self.wPtr = 0
		self.hPtr = 0
		if(self.item is None):
			#self.item = make.image(self.data, interpolation='linear',colormap='gist_gray')
			self.item = make.image(self.data, title='', interpolation='linear')
			#self.item = make.image(self.data, interpolation='nearest', colormap='gist_gray')
			plot = self.get_plot()
			plot.add_item(self.item, z=0)
			plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
		
		if('selectable' in list(parms.keys())):
			self.item.set_selectable(parms['selectable'])
			
		self.set_image_parameters(self.item, parms['xmin'], parms['xmax'], parms['ymin'], parms['ymax'])
		self.show_data(self.data, True)
		self.set_autoscale()
		self.image_is_new = True
		
		return(self.data.shape)
	
	def clear_data(self, prefix, rows, cols):
		array = np.ones((rows,cols), dtype=np.int32)
		self.data = self._makeSquareDataArray(array)
		if(self.item is None):
			self.item = make.image(self.data, interpolation='linear',colormap='gist_gray')
			#self.item = make.image(self.data, interpolation='nearest', colormap='gist_gray')
		self.item.load_file_data(self.data)


	def _makeSquareDataArray(self, array):
		''' for display purposes it's easiest to have the data square so repeat
		pixels in the lesser demension, as well make sure that the demensions are 32 bit aligned
		'''
		h,w = array.shape
		
		if(h != w):
			if(h < w):
				#scale Height and width to something divisible by for (32 bit aligned)
				self.widthSc, self.htSc = nextFactor(w,h) 
				newArray = np.repeat(np.repeat(array, self.htSc, axis=0), self.widthSc, axis=1)
			else:	
				self.htSc, self.widthSc = nextFactor(h,w) 
				newArray = np.repeat(np.repeat(array, self.htSc, axis=0), self.widthSc, axis=1)
		else:
			newArray = array
		
		#print '_makeSquareDataArray: shape=' 
		#print newArray.shape
		return newArray
		

	def _convSampleToDisplay(self, x, y):
		"""remember this is a 2d array array[row][column] so it is [array[y][x]
		   so that it will display the data from bottom/up left to right 
		"""
		h,w = self.data.shape
		xscaler = self.widthSc
		yscaler = self.htSc
# 		#convert 
		rowStart = int((self.dataHeight-0) + (y * yscaler)) - (h/2.0)
		colStart = int(x * xscaler) - (w/2.0)
		rowStop = int(rowStart - self.zoom_scale)
		colStop = int(colStart + self.zoom_scale)
		
 		return(colStart, colStop, rowStart, rowStop)

	def showData(self):
		self.show_data(self.data)

	def addData(self, x, y, val, show=False):
		''' this function adds a new point to the 2d array
		kept around for backward compatability but new calls should use addPoint()
		'''
		if(not self.dataAtMax):
			
			#remember this is a 2d array array[row][column] so it is [array[y][x]
			#so that it will display the data from bottom/up left to right 
			(colStart, colStop, rowStart, rowStop) = self._convSampleToDisplay( x, y)
			#print 'adding (%d,%d,%d,%d) = %d' % (colStart, colStop, rowStart, rowStop,val)
			#scal data
			self.data[rowStop:rowStart , colStart:colStop] = copy.deepcopy(val)
			
			if(show):
				self.show_data(self.data)
				
	def addPoint(self, y, x, val, show=False):
		''' this function adds a new point to the 2d array 
		'''
		#if(not self.dataAtMax):
		if(self.data is not None):
			rows,cols = self.data.shape
			if(y < rows):
				#remember this is a 2d array array[row][column] so it is [array[y][x]
				#so that it will display the data from bottom/up left to right 
				#(colStart, colStop, rowStart, rowStop) = self._convSampleToDisplay( x, y)
				#print 'adding (%d,%d,%d,%d) = %d' % (colStart, colStop, rowStart, rowStop,val)
				#scal data
				#self.data[rowStop:rowStart , colStart:colStop] = copy.deepcopy(val)
				self.data[y , x] = copy.deepcopy(val)
			
			if(show):
				self.show_data(self.data)
	
	def addLine(self, startx, row, line, show=False):
		''' this function adds a new line to the 2d array
		'''
		#print 'addLine: row=%d' % row
		#print 'addLine: data length = %d vals' % len(line)
		if((self.image_is_new==True)):
			self.image_is_new = False
			if(row != 0):
				return
		#this is a catch for a spurious previsou row being sent
		#at the start of a scan, fix this sometime
		
		#print 'row=%d' % row	 
		if(self.data is not None):
			rows,cols = self.data.shape
			if(cols != len(line)):
				line = np.resize(line, (cols,))
			
			if(row >= rows):
				row = rows-1
					
			self.data[row,:] = copy.deepcopy(line)
			if(show):
				self.show_data(self.data)
		else:
			_logger.error('stxmImageWidget: addLine: self.data is None')
			

	def load_file_data(self, fileName, data):
		self.fileName = fileName
		self.data = data
		#self.show_data(self.data)
		if(self.filtVal > 0):
			self.apply_filter(self.filtVal)
		else:
			self.show_data(self.data)
	
	def set_data(self, data):
		self.data = data
		#self.show_data(self.data)
		if(self.filtVal > 0):
			self.apply_filter(self.filtVal)
		else:
			self.show_data(self.data)
		self.set_autoscale()
					
	def set_autoscale(self):
		plot = self.get_plot()
		#self.set_lock_aspect_ratio(False)
		plot.do_autoscale()
		#self.set_lock_aspect_ratio(True)


	def show_data(self, data, init=False):
		plot = self.get_plot()
		if(self.item is None):
			#self.item = make.image(data, colormap="gist_gray")
			#self.item = make.image(data)
			self.item = make.image(self.data, interpolation='linear', colormap='gist_gray')
			plot.add_item(self.item, z=0)
			plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
		else:
			self.item.set_data(data)
		plot.replot()
	

	def apply_filter(self, val):
		if(val):
			#apply filter
			data = self.filterfunc(self.data, val)
		else:
			#no filter just display raw
			data = self.data
		self.filtVal = val		
		self.show_data(data)

	def setCurFilter(self, filtName):
		self.curFilterStr = filtName
		#print 'setCurFilter: filter changed to %s' % self.curFilterStr
		self.curFilterStr = str(filtName)
		self.filterfunc = getattr(scipy.ndimage, self.curFilterStr)
		self.apply_filter(self.filtVal)
		self.get_xcs_panel().update_plot()
		self.get_ycs_panel().update_plot()
 

	def mousePressEvent(self, ev):
		#print 'StxmImageWidget: mouse pressed'
		btn = ev.button()
		self.inputState.btnisPressed[btn] = True
		if btn == Qt.LeftButton:
			#print 'left mouse button pressed'
			#check to see if the user is using one of the selection tools, if so
			# then set the name of the active plot item, if you can
			tool = self.plot.manager.get_active_tool()
			if(isinstance(tool, AverageCrossSectionTool)):
				#print 'Average selection tool selected'
				self.roiNum += 1
			elif(isinstance(tool, AnnotatedSegmentTool)):
				#print 'AnnotatedSegmentTool tool selected'
				self.segNum += 1
			elif(isinstance(tool, AnnotatedPointTool)):
				#print 'AnnotatedPointTool tool selected'
				self.pntNum += 1
				
		elif btn == Qt.MiddleButton:
			#if user has spacebar pressed and they press the middle button then
			#emit a new_roi_center so that scan params can be updated
			if(self.inputState.keyisPressed[Qt.Key_F1]):
				dct = {}
				dct['center'] = self.inputState.center
				dct['size'] = self.inputState.range
				dct['npts'] = self.inputState.npts
				self.new_roi_center.emit(dct)
				return

	def mouseReleaseEvent(self, ev):
		#print 'StxmImageWidget: mouse released'
		btn = ev.button()
		self.inputState.btnisPressed[btn] = False

		if btn == Qt.LeftButton:
			#print 'StxmImageWidget: mouse moved with left button pressed'
			plot = self.get_plot()
			#pan = plot.get_itemlist_panel()
			#get all the shapes and turn off their size texts
			active_item = plot.get_active_item()
			#print 'active_item: ', active_item
			items = self.plot.get_items(item_type=IShapeItemType)
			for item in items:
				#if teh user has deselected this plot item then hide its label
				if(hasattr(item, "is_label_visible")):
					if item.is_label_visible() and (item != active_item):
						item.set_label_visible(False)
						
					elif item.is_label_visible() and (item == active_item):
						item.set_label_visible(True)
					else:
						pass
						#item.position_and_size_visible = False
						#pass
			self.plot.replot()
			return

	
	#note: these handlers are using Qt4.5 syntax, it changes in Qt4.8.3
	def mouseMoveEvent(self, ev):
		btn = ev.button()
		#self.inputState.btnisPressed[btn]
		if btn == Qt.MidButton:
			print('StxmImageWidget: mouse moved with middle button pressed')
			return
		elif btn == Qt.LeftButton:
			#print 'StxmImageWidget: mouse moved with left button pressed'
			#self.manager.update_cross_sections()
			
			return
		elif btn == Qt.RightButton:
			#print 'StxmImageWidget: mouse moved with right button pressed'
			return
		
		
	def wheelEvent(self, event):
		incr = 5
		do_emit = False
		if(event.delta() > 0):
			dir = 1
		else:
			dir = -1
			
		(cx, cy) = self.inputState.center
		(rx, ry) = self.inputState.range
		(nx, ny) = self.inputState.npts
		
		if(self.inputState.keyisPressed[Qt.Key_X]):
			nx = (incr * dir)
			do_emit = True
		else:
			nx = 0
			
		if(self.inputState.keyisPressed[Qt.Key_Y]):
			ny = (incr * dir)
			do_emit = True
		else:
			ny = 0
		#print 'wheelEvent: nx,ny (%d, %d)' % (nx, ny)
		self.inputState.center = (cx, cy)
		self.inputState.range = (rx, ry)
		self.inputState.npts = (nx, ny)
		dct = {}
		dct['center'] = self.inputState.center
		dct['size'] = self.inputState.range
		dct['npts'] = self.inputState.npts
		
		#only emit a new region if an x or y key is pressed
		if(do_emit):
			#if(not self.inputStatekey.isPressed[Qt.Key_Alt]):
			self.new_roi_center.emit(dct)
			
		
		#reset the delta points
		self.inputState.npts = (0, 0)
		
	def keyPressEvent(self, event):
		key = event.key()
		if(event.isAutoRepeat()):
			event.ignore()
			return
		if key == Qt.Key_Delete:
			item = self.plot.get_active_item()
			if item:
				self.delPlotItem(item)
			
		if(key not in list(self.inputState.keyisPressed.keys())):
			event.ignore()
			return
		
		self.inputState.keyisPressed[key] = True
		#print 'key pressed', self.inputState.keyisPressed
# 		if key == Qt.Key_Delete:
# 			item = self.plot.get_active_item()
# 			if item:
# 				self.delPlotItem(item)
#				print 'deleting %s'  % item.title().text()
#				self.plot.del_item(item)
#				self.plot.replot()
#			
#		if key == QtCore.Qt.Key_Up:
#			self.centerNode.moveBy(0, -20)
#		elif key == QtCore.Qt.Key_Down:
#			self.centerNode.moveBy(0, 20)
#		elif key == QtCore.Qt.Key_Left:
#			self.centerNode.moveBy(-20, 0)
#		elif key == QtCore.Qt.Key_Right:
#			self.centerNode.moveBy(20, 0)
#		elif key == QtCore.Qt.Key_Plus:
#			self.scaleView(1.2)
#		elif key == QtCore.Qt.Key_Minus:
#			self.scaleView(1 / 1.2)
#		elif key == QtCore.Qt.Key_Space or key == QtCore.Qt.Key_Enter:
#			for item in self.scene().items():
#				if isinstance(item, Node):
#					item.setPos(-150 + QtCore.qrand() % 300, -150 + QtCore.qrand() % 300)
#		else:
#			super(GraphWidget, self).keyPressEvent(event)

	
	def keyReleaseEvent(self, event):
		key = event.key()
		if(event.isAutoRepeat()):
			event.ignore()
			return
		if(key not in list(self.inputState.keyisPressed.keys())):
			event.ignore()
			return
		
		self.inputState.keyisPressed[key] = False
		#print 'key released', self.inputState.keyisPressed			

	def delPlotItem(self, item, replot=True):
		#Don't delete the base image
		#if(item.title().text() != 'Image #1'):
		title = str(item.title().text())
		if(title.find('Image') < 0):
			print('deleting %s'  % title)
			self.region_deleted.emit( title )
			self.plot.del_item(item)
			if(replot):
				self.plot.replot()
	
	def delImagePlotItems(self):
		items = self.plot.get_items(item_type=ICSImageItemType)
		for item in items:
			#Don't delete the base image
			#if(item.title().text() != 'Image #1'):
			print('deleting %s'  % item.title().text())
			self.plot.del_item(item)
			del item
	
		self.plot.replot()



	def loadFilterPanel(self, plotter):
		#create a panel and put the filter related stuff in it
		filterPanel = uic.loadUi(uiDir + 'filtersGrpBox.ui')
		self.connect(filterPanel.filterSlider, SIGNAL("valueChanged(int)"), self.apply_filter)
		self.connect(filterPanel.filterComboBox, SIGNAL("currentIndexChanged(int)"), self.onFilterIndexChanged)
		return filterPanel
		
		#return filterPanel
	def onFilterIndexChanged(self, index):
		filtStr = str(self.filterPanel.filterComboBox.itemText(index))   
		self.setCurFilter(filtStr) 

	
	def set_image_parameters(self, imgItem, xmin, xmax, ymin, ymax):
		""" 
		Use this function to adjust the image parameters such that the x and y axis are
		within the xmin,xmax and ymin,ymax bounds, this is an easy way to display the image
		in microns as per the scan parameters, as well as the fact that if you have a scan with
		a non-square aspect ratio you can still display the scan as a square because the image will
		repeat pixels as necessary in either direction so that the image is displayed in teh min/max
		bounds you set here 
		
		:param imageItem: a image plot item as returned from make.image()
		:type imageItem: a image plot item as returned from make.image() 
		
		:param xmin: min x that the image will be displayed
		:type xmin: int
		
		:param xmax: max x that the image will be displayed
		:type xmax: int
		
		:param ymin: min y that the image will be displayed
		:type ymin: int
		
		:param ymax: max y that the image will be displayed
		:type ymax: int
		
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
		iparam.xmin = xmin
		iparam.ymin = ymin
		iparam.xmax = xmax
		iparam.ymax = ymax
		self.zoom_rngx = float(xmax - xmin)
		self.zoom_rngy = float(ymax - ymin)
		
		axparam = ImageAxesParam()
		axparam.xmin = xmin
		axparam.ymin = ymin
		axparam.xmax = xmax
		axparam.ymax = ymax
		
		imgItem.set_item_parameters({"ImageParam":iparam})
		imgItem.set_item_parameters({"ImageAxesParam":axparam})
	
	def set_lock_aspect_ratio(self, val):
		self.plot.lock_aspect_ratio = bool(val)		

	def openfile(self, fileName, addimages=True):
		#print 'openfile called for file: %s' % fileName	   
			self.imageFilename = fileName	   
			#turn teh QString into a regular python string
			self.stxm_obj = stxmDataObj(str(fileName))
			self.setWindowTitle(fileName)
			#self.rawData = self.stxm_obj.image_obj.rawData
			self.htSc = 1
			self.widthSc = 1

			
			self.data = self.stxm_obj.image_obj.rawData
			[self.dataHeight, self.dataWidth] = self.data.shape
			self.wPtr = 0
			self.hPtr = 0
			if((not addimages) or (self.item is None)):
				#self.item = make.image(self.data, interpolation='linear')
				#self.item = make.image(self.data, interpolation='nearest', colormap='gist_gray')
				self.item = make.image(self.data, interpolation='linear', colormap='jet', title=str(fileName))
				plot = self.get_plot()
				plot.add_item(self.item, z=0)
				#plot.set_plot_limits(0.0, 740.0, 0.0, 800.0)
			else:
				self.item = make.image(self.data, interpolation='linear', colormap='jet', title=str(fileName))
				plot = self.get_plot()
				items = self.plot.get_items(item_type=ICSImageItemType)
				plot.add_item(self.item, z=len(items))
			
			self.set_image_parameters(self.item,self.stxm_obj.get_min_x(),self.stxm_obj.get_max_x(), self.stxm_obj.get_min_y(), self.stxm_obj.get_max_y())
			self.show_data(self.data, True)
			self.set_autoscale()
			
			return(self.data.shape)

	
	def setZoomLimits(self):
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
		""" given the ranges specified center the plot around 0
		"""
		xRhalf = xRange/2.0
		yRhalf = yRange/2.0
		self.plot.set_plot_limits(-xRhalf, xRhalf, -yRhalf, yRhalf)
	
	def set_center_at_XY(self, center, rng):
		""" given the center and range tuples specified center the plot around center
		"""
		(cx, cy) = center
		(rx, ry) = rng
		xstart = cx - (0.5 * rx)
		xstop = cx + (0.5 * rx)
		ystart = cy- (0.5 * ry)
		ystop = cy + (0.5 * ry)
		
		self.plot.set_plot_limits(xstart, xstop, ystart, ystop)

	def setPlotAxisStrs(self, ystr=None, xstr=None):
		self.plot = self.get_plot()
		# set axis titles
		if(ystr != None):
			self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, ystr)
		if(xstr != None):
			self.plot.setAxisTitle(Qwt.QwtPlot.xBottom,xstr)
			
		
		self.plot.setAxisTitle(Qwt.QwtPlot.xTop, '')	
		self.plot.setAxisTitle(Qwt.QwtPlot.yRight, '')	
				
		#self.plot.replot()
	
	def setXYStep(self, stxm_obj):
		#convert to a 1/<> value as it is used to do the pixel to micron conversion
		if(self.stxm_obj.header['XStep'] == 0):
			self.stxm_obj.header['XStep'] = 1
		if(self.stxm_obj.header['YStep'] == 0):
			self.stxm_obj.header['YStep'] = 1
		self.xstep = float(1.0/self.stxm_obj.header['XStep'])
		self.ystep = float(1.0/self.stxm_obj.header['YStep'])


	############### TEST CODE ########################################
	def timerTestStop(self):
		self.tstTimer.stop()

# 	def tstDataPoint(self):
# 		for i in range(0,200):
# 			val = np.random.random_integers(0,high=200)
# 			[x,y] = self.incrWidthPtr()
# 			#self.addData(x,y,val)
# 			if(not self.dataAtMax):
# 				#print 'adding [%d,%d] = %d' % (x,y,val)
# 				self.data[x][y] = val
# 			else:
# 				#self.done.emit(True)
# 				self.timerTestStop()
# 				
# 		self.show_data(self.data)


	

if __name__ == "__main__":
	"""Test"""
	# -- Create QApplication
	import guidata

	app = guidata.qapplication()
	# --	

	# here ht and wd are the scan point numbers, the scaling will be handled automatically
	#win = StxmImageWidget(parent = None, type='select' , testing=False)
	win = StxmImageWidget(parent = None, options=dict(show_xsection=True, show_ysection=True,show_itemlist=True))
	win.addTool('SegmentTool')
	win.addTool('MultiLineTool')
	win.addTool('FreeFormTool')
	win.resize(900,900)

	win.show()
	

	
	
	app.exec_()


		

