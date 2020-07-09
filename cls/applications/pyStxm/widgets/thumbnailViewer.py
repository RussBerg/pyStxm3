'''
Created on 2016-10-11

@author: bergr

'''
import sys
import os
import itertools
import math
import queue
import numpy as np
import simplejson as json

from PyQt5 import QtCore, QtGui, QtWidgets

from PIL import Image

from bcm.devices.epu import convert_wrapper_epu_to_str
from bcm.devices.device_names import *

from cls.utils.arrays import flip_data_upsdown
from cls.utils.images import array_to_gray_qpixmap
from cls.utils.images import array_to_image
from cls.applications.pyStxm import abs_path_to_ini_file
from cls.applications.pyStxm.widgets.print_stxm_thumbnail import PrintSTXMThumbnailWidget
from cls.app_data.defaults import master_colors, get_style, rgb_as_hex

from cls.appWidgets.dialogs import setExistingDirectory
from cls.appWidgets.thread_worker import Worker
from cls.utils.arrays import flip_data_upsdown
from cls.utils.dirlist import dirlist, dirlist_withdirs
from cls.utils.fileUtils import get_file_path_as_parts
from cls.utils.log import get_module_logger, log_to_qt
from cls.utils.cfgparser import ConfigClass
from cls.utils.dict_utils import dct_get, dct_put
from cls.utils.roi_utils import make_base_wdg_com, widget_com_cmnd_types
from cls.utils.pixmap_utils import get_pixmap
from cls.plotWidgets.lineplot_thumbnail import OneD_MPLCanvas
from cls.plotWidgets.curveWidget import get_next_color, get_basic_line_style, make_spectra_viewer_window, \
    reset_color_idx

from cls.applications.pyStxm.widgets.print_stxm_thumbnail import SPEC_THMB_WD, SPEC_THMB_HT

from cls.types.stxmTypes import spatial_type_prefix, image_types, scan_image_types, scan_types, scan_sub_types, \
    sample_positioning_modes, spectra_type_scans, image_type_scans

from cls.plotWidgets.imageWidget import make_default_stand_alone_stxm_imagewidget
from cls.utils.roi_dict_defs import *
from cls.utils.fileSystemMonitor import DirectoryMonitor

from cachetools import cached, \
    TTLCache  # 1 - let's import the "cached" decorator and the "TTLCache" object from cachetools

cache = TTLCache(maxsize=100, ttl=300)  # 2 - let's create the cache object.

# appConfig = ConfigClass(abs_path_to_ini_file)
icoDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'icons')

_logger = get_module_logger(__name__)

MAX_THUMB_COLUMNS = 3
THMB_SIZE = 90
SCENE_WIDTH = 290.0
THUMB_WIDTH = 150.0
THUMB_HEIGHT = 130.0

THUMB_ACTIVE_AREA_WD = 90
THUMB_ACTIVE_AREA_HT = 112

ICONSIZE = 21
BTNSIZE = 25

COLORTABLE = []
for i in range(256): COLORTABLE.append(QtGui.qRgb(i / 4, i, i / 2))


def make_thumb_widg_dct(data_dir, fname, entry_dct, counter=DNM_DEFAULT_COUNTER):
    '''
    a convienience function to create a 'standard' dict for use by thumb widgets
    :param data_dir:
    :param fname:
    :param entry_dct:
    :param counter:
    :return:
    '''
    dct = {}
    dct['id'] = 'temp_thumb_widg_dct'
    dct['data_dir'] = data_dir
    dct['fprefix'] = fname
    dct['counter'] = counter
    dct['entries'] = entry_dct
    return (dct)


def get_first_entry_key(entries_dct):
    '''
    use the default attribute to return the default entry name to use
    :param entries_dct:
    :return:
    '''
    # return (entries_dct['entries'].keys()[0])
    #return (list(entries_dct['entries'])[0])
    return(entries_dct['entries']['default'])


def get_first_sp_db_from_entry(entry_dct):
    # sp_id = entry_dct['WDG_COM']['SPATIAL_ROIS'].keys()[0]
    sp_id = list(entry_dct['WDG_COM']['SPATIAL_ROIS'])[0]
    sp_db = entry_dct['WDG_COM']['SPATIAL_ROIS'][sp_id]
    return (sp_db)


def get_first_sp_db_from_wdg_com(wdg_com):
    # sp_id = wdg_com['SPATIAL_ROIS'].keys()[0]
    sp_id = list(wdg_com['SPATIAL_ROIS'])[0]
    sp_db = wdg_com['SPATIAL_ROIS'][sp_id]
    return (sp_db)


def get_axis_setpoints_from_sp_db(sp_db, axis='X'):
    if (axis in sp_db.keys()):
        data = sp_db[axis][SETPOINTS]
    else:
        data = None
    return (data)


def get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    '''
    return 3D generic scan data as 1D list
    :param entry_dct:
    :param counter:
    :return:
    '''
    # datas = [entry_dct['data'][counter]['signal'][0][0]]
    datas = [entry_dct['data'][counter]['signal']]
    return (datas)


def get_point_spec_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    data = entry_dct['data'][counter]['signal']
    return (data)


def get_point_spec_energy_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER):
    if (counter not in list(entry_dct['data'])):
        print('oops')
    data = entry_dct['data'][counter]['energy']['signal']
    return (data)


class ThumbnailWidget(QtWidgets.QGraphicsWidget):
    update_view = QtCore.pyqtSignal()
    select = QtCore.pyqtSignal(object)
    launch_viewer = QtCore.pyqtSignal(object)
    print_thumb = QtCore.pyqtSignal(object)
    preview_thumb = QtCore.pyqtSignal(object)
    drag = QtCore.pyqtSignal(object, object)
    dbl_clicked = QtCore.pyqtSignal(object)

    def __init__(self, fname, sp_db, data, title, info_dct, scan_type=None, dct={}, is_folder=False, parent=None):
        """
        __init__(): description

        :param fname: fname description
        :type fname: fname type

        :param sp_db: sp_db description
        :type sp_db: sp_db type

        :param data: data description
        :type data: data type

        :param title: title description
        :type title: title type

        :param info_dct: info_dct description
        :type info_dct: info_dct type

        :param scan_type=scan_types.SAMPLE_IMAGE one of the defined scan_types
        :type scan_type=int:  integer enumeration

        :param entry_dct= dictionary of entries
        :type entry_dct=int:  dict

        :param is_folder=False: is this a folder icond thumbnail
        :type is_folder=False: bool type

        :param parent=None: parent=None description
        :type parent=None: parent=None type



        :returns: None
        """
        '''
        This class is used to create a single graphics widget that displays a thumbnail of
        a stxm image data, the thumbnail is created from the data section of the hdf5 file
        '''
        QtWidgets.QGraphicsWidget.__init__(self, parent=None)
        self.parent = parent
        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)

        if (title is None):
            self.title = str(fprefix)
        else:
            self.title = title

        self.data = data
        self.sp_db = sp_db
        self.dct = dct
        self.labelheight = 20
        self.bordersize = 1
        self.is_folder = is_folder

        self.launchAction = None

        self.hdf5_path = fname
        self.data_dir = data_dir
        self.fname = fname
        self.fprefix = fprefix
        self.fpref_and_suff = fprefix + fsuffix
        self.scan_type = scan_type
        self.counter = DNM_DEFAULT_COUNTER

        self.pen = QtGui.QPen()
        self.pen.setWidth(2)
        self.pen.setBrush(QtCore.Qt.black)
        self.pen.setStyle(QtCore.Qt.SolidLine)
        self.is_selected = False
        self.valid_file = False
        self.pic = None
        self.info_str = info_dct['info_str']
        self.info_jstr = info_dct['info_jstr']

        if (is_folder):
            self.getpic = self.get_folder_pic

        elif (self.scan_type in spectra_type_scans):
            if (self.scan_type is scan_types.GENERIC_SCAN):
                self.getpic = self.get_generic_scan_pic
            else:
                self.getpic = self.get_specplot_pic
        else:
            self.getpic = self.get_2dimage_pic

        self.valid_file = True
        self.pic = self.getpic()
        self.setToolTip(self.info_str)
        self.setAcceptHoverEvents(True)

    def contextMenuEvent(self, event):
        """
        contextMenuEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        menu = QtWidgets.QMenu()
        launchAction = QtWidgets.QAction("Send to Viewer", self)
        # launchAction.triggered.connect(self.launch_vwr)
        #
        # printAction = QtWidgets.QAction("Print", self)
        # printAction.triggered.connect(self.print_it)

        prevAction = QtWidgets.QAction("Print Preview", self)
        # prevAction.triggered.connect(self.preview_it)

        saveTiffAction = QtWidgets.QAction("Save as Tiff file", self)

        menu.addAction(prevAction)
        # menu.addAction(printAction)
        menu.addAction(launchAction)
        menu.addAction(saveTiffAction)

        selectedAction = menu.exec_(event.screenPos())
        # if(printAction == selectedAction):
        #    self.print_it(self)
        # elif(launchAction == selectedAction):
        if (launchAction == selectedAction):
            self.launch_vwr(self)
        elif (prevAction == selectedAction):
            self.preview_it(self)
        elif (saveTiffAction == selectedAction):
            self.save_tif(self)

    def print_it(self, sender):
        '''
        call PrintSTXMThumbnailWidget()
        :param sender:
        :return:
        '''
        self = sender
        info_dct = json.loads(self.info_jstr)

        dct = {}
        dct['fpath'] = self.fname
        dct['fname'] = self.fpref_and_suff
        dct['data_pmap'] = self.getpic(scale_it=False)
        dct['contrast_pmap'] = None
        dct['xstart'] = 0
        dct['ystart'] = 0
        dct['xstop'] = info_dct['range'][0]
        dct['ystop'] = info_dct['range'][1]
        dct['xpositioner'] = info_dct['xpositioner']
        dct['ypositioner'] = info_dct['ypositioner']
        type_tpl = info_dct['scan_type'].split()
        dct['scan_type'] = type_tpl[0]
        dct['scan_type_num'] = info_dct['scan_type_num']
        dct['scan_sub_type'] = type_tpl[1]
        dct['data_dir'] = self.data_dir

        dct['data_min'] = self.data.min()
        dct['data_max'] = self.data.max()

        dct['info_dct'] = info_dct

        self.print_thumb.emit(dct)

    def preview_it(self, sender):
        '''
        call PrintSTXMThumbnailWidget()
        :param sender:
        :return:
        '''
        self = sender
        info_dct = json.loads(self.info_jstr)
        dct = {}
        dct['fpath'] = self.fname
        dct['fname'] = self.fpref_and_suff
        # dct['data_pmap'] = self.getpic(scale_it=False, as_thumbnail=False)
        dct['data_pmap'] = self.getpic(scale_it=True, as_thumbnail=False)
        dct['contrast_pmap'] = None
        dct['xstart'] = info_dct['start'][0]
        dct['ystart'] = info_dct['start'][1]
        dct['xstop'] = info_dct['stop'][0]
        dct['ystop'] = info_dct['stop'][1]
        dct['xcenter'] = info_dct['center'][0]
        dct['ycenter'] = info_dct['center'][1]
        dct['xrange'] = info_dct['range'][0]
        dct['yrange'] = info_dct['range'][1]
        dct['xpositioner'] = info_dct['xpositioner']
        dct['ypositioner'] = info_dct['ypositioner']

        type_tpl = info_dct['scan_type'].split()
        dct['scan_type'] = type_tpl[0]
        dct['scan_type_num'] = info_dct['scan_type_num']
        dct['scan_sub_type'] = type_tpl[1]
        dct['data_dir'] = self.data_dir

        if (dct['scan_type'] == scan_types[scan_types.SAMPLE_POINT_SPECTRUM]):
            dct['data_min'] = self.data.min()
            dct['data_max'] = self.data.max()
        else:

            if (self.data is not None):
                dct['data_min'] = self.data.min()
                dct['data_max'] = self.data.max()
            else:
                _logger.error('self.data cannot be None')
                return

        dct['info_dct'] = info_dct

        # print 'print_it called: %s'% self.fname

        self.preview_thumb.emit(dct)

    def save_tif(self, sender):
        '''
        call save_tif(), when saving a tif file keep the dimensions the same as the data, only thunmbnails
        are square
        :param sender:
        :return:
        '''
        self = sender
        _data = flip_data_upsdown(self.data)
        rows, cols = _data.shape
        im = array_to_image(_data)
        # make sure tifs are at least 100x100
        if (rows < cols):
            # scale by rows
            if (rows < 100):
                _fctr = int(100 / rows)
                rows = int(_fctr * rows)
                cols = int(_fctr * cols)
        else:
            if (cols < 100):
                _fctr = int(100 / cols)
                rows = int(_fctr * rows)
                cols = int(_fctr * cols)
        # im = im.resize([rows, cols], Image.NEAREST)  # Image.ANTIALIAS)  # resizes to 256x512 exactly
        im = im.resize([cols, rows], Image.NEAREST)  # Image.ANTIALIAS)  # resizes to 256x512 exactly
        im.save(self.fname.replace('.hdf5', '.tif'))

    def create_gradient_pmap(self, _min, _max):
        box = QtCore.QSize(20, THUMB_HEIGHT)
        self.maskPixmap = QtGui.QPixmap(box)
        self.maskPixmap.fill(QtCore.Qt.transparent)
        g = QtGui.QLinearGradient()
        g.setStart(0, 0)
        g.setFinalStop(0, box.height())
        # white at top
        g.setColorAt(0, QtGui.QColor(255, 255, 255, 0))
        # black at bottom
        g.setColorAt(1.0, QtGui.QColor(0, 0, 0, 255))

    def is_valid(self):
        """
        is_valid(): description

        :returns: None
        """
        return (self.valid_file)

    def boundingRect(self):
        """
        boundingRect(): this returns the rect for the entire thumbwidget, so base it on total
        size not the size ofthe data pixmap

        :returns: None
        black_pm = QtGui.QPixmap(THMB_SIZE, THMB_SIZE)
        """
        # if(self.pic is not None):
        #     width = self.pic.rect().width() + (self.bordersize * 2)
        #     #height = self.pic.rect().height() + self.labelheight + self.bordersize * 2
        #     height = THMB_SIZE + self.labelheight + self.bordersize * 2
        #     thumb_widget_rect = QtCore.QRectF(0.0, 0.0, width, height)
        #
        # else:
        #     thumb_widget_rect = QtCore.QRectF(0.0, 0.0, THUMB_WIDTH, THUMB_HEIGHT)
        #     #thumb_widget_rect = QtCore.QRectF()

        # self._boundingRect = thumb_widget_rect
        thumb_widget_rect = QtCore.QRectF(0.0, 0.0, THUMB_ACTIVE_AREA_WD, THUMB_ACTIVE_AREA_HT)
        return thumb_widget_rect

    def sizeHint(self, which, constraint=QtCore.QSizeF()):
        """
        sizeHint(): description

        :param which: which description
        :type which: which type

        :param constraint=QtCore.QSizeF(): constraint=QtCore.QSizeF() description
        :type constraint=QtCore.QSizeF(): constraint=QtCore.QSizeF() type

        :returns: None
        """
        br = self.boundingRect()
        return br.size()

    def get_generic_scan_pic(self, scale_it=True, as_thumbnail=True):
        """

        :param scale_it:
        :return:
        """
        ekey = get_first_entry_key(self.dct)
        entry_dct = self.dct['entries'][ekey]
        sp_db = get_first_sp_db_from_entry(entry_dct)
        xdata = get_axis_setpoints_from_sp_db(sp_db, axis='X')
        ydatas = get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER)

        if (len(xdata) <= 1):
            pmap = QtGui.QPixmap()
        else:
            if (as_thumbnail):
                # return a lower res pmap for use as a thumbnail image
                qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=2, height=1.65, dpi=200, axes_bgrnd_color='#FFFFFF')
                pmap = qt_mpl.get_pixmap(as_grayscale=True, as_thumbnail=True)
            else:
                # return a higher res pixmap for eventual printing
                qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=2, height=1.65, dpi=2000)
                pmap = qt_mpl.get_pixmap(as_grayscale=False, as_thumbnail=False)
                pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(SPEC_THMB_WD, SPEC_THMB_HT)), QtCore.Qt.KeepAspectRatio)

        if (as_thumbnail):
            pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.KeepAspectRatio)

        return (pmap)

    def get_folder_pic(self, scale_it=True, as_thumbnail=True):
        """
        pmap = get_pixmap(os.path.join(icoDir, 'reload.ico'), ICONSIZE, ICONSIZE)
        :param scale_it:
        :type scale_it: bool
        :parm as_thumbnail:
        :type as_thumbnail: bool
        :parm fldr_type:
        :type fldr_type: a string either 'stack' or 'tomo'
        :return:
        """
        sz_x = 222
        sz_y = 164

        if (self.title.find('.') > -1):
            #image_fname = 'updir.png'
            #image_fname = 'open-folder-icon-png.png'
            image_fname = 'directory_up_bw.png'

        else:
            if(self.scan_type is scan_types.SAMPLE_IMAGE_STACK):
                image_fname = 'stack.bmp'
            elif(self.scan_type is scan_types.TOMOGRAPHY):
                #image_fname = 'tomo.png'
                image_fname = 'folder_bw_tomo.png'
            else:
                image_fname = 'folder_bw.ico'

        if (as_thumbnail):
            # return a lower res pmap for use as a thumbnail image
            pmap = get_pixmap(os.path.join(icoDir, image_fname), sz_x, sz_y)
        else:
            # return a higher res pixmap for eventual printing
            pmap = get_pixmap(os.path.join(icoDir, image_fname), sz_x, sz_y)
            pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(SPEC_THMB_WD, SPEC_THMB_HT)), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        if (as_thumbnail):
            pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        return (pmap)

    # def get_spec_folder_pic(self, scale_it=True, as_thumbnail=True):
    #     """
    #     pmap = get_pixmap(os.path.join(icoDir, 'reload.ico'), ICONSIZE, ICONSIZE)
    #     :param scale_it:
    #     :return:
    #     """
    #     if (as_thumbnail):
    #        # return a lower res pmap for use as a thumbnail image
    #        pmap = get_pixmap(os.path.join(icoDir, 'spec_folder.png'), 222, 164)
    #     else:
    #        # return a higher res pixmap for eventual printing
    #        pmap = get_pixmap(os.path.join(icoDir, 'spec_folder.png'), 222, 164)
    #        pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(SPEC_THMB_WD, SPEC_THMB_HT)), QtCore.Qt.KeepAspectRatio)
    #
    #     if (as_thumbnail):
    #         pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.KeepAspectRatio)
    #
    #     return (pmap)

    # def get_specplot_pic(self, scale_it=True):
    #     """
    #
    #     :param scale_it:
    #     :return:
    #     """
    #     ekey = get_first_entry_key(self.dct)
    #     entry_dct = self.dct['entries'][ekey]
    #     xdata = get_point_spec_energy_data_from_entry(entry_dct, counter=self.counter)
    #     #xdata = self.dct['entries'][ekey]['data'][self.counter]['energy']['signal']
    #
    #     ydatas = []
    #     for ekey in self.dct['entries'].keys():
    #         entry_dct = self.dct['entries'][ekey]
    #         #ydatas.append(self.dct['entries'][ekey]['data'][self.counter]['signal'])
    #         ydatas.append(get_point_spec_data_from_entry(entry_dct, counter=self.counter))
    #
    #     if(len(xdata) <= 1):
    #         pmap = QtGui.QPixmap()
    #     else:
    #         qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=1, height=0.75, dpi=120)
    #         pmap = qt_mpl.get_pixmap(as_grayscale=True)
    #         #rect = QtCore.QRect(0, 0, pmap.width()+50, pmap.height()+50)
    #         #pmap = QtGui.QPixmap(pmap.copy(rect))
    #         #trans = QtGui.QTransform(pmap)
    #         #trans.translate(0.0,-25.0)
    #         #pmap = pmap.transformed((trans))
    #
    #     pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.KeepAspectRatio)
    #     return(pmap)
    def get_specplot_pic(self, scale_it=True, as_thumbnail=True):
        """

        :param scale_it:
        :return:
        """
        ekey = get_first_entry_key(self.dct)
        entry_dct = self.dct['entries'][ekey]
        xdata = get_point_spec_energy_data_from_entry(entry_dct, counter=self.counter)
        # xdata = self.dct['entries'][ekey]['data'][self.counter]['energy']['signal']
        counter_nm = entry_dct['default']
        ydatas = []
        # for ekey in self.dct['entries'].keys():
        ekeys = [k for k,v in self.dct['entries'].items() if k.find('entry') > -1]
        for ekey in ekeys:
            entry_dct = self.dct['entries'][ekey]
            # ydatas.append(self.dct['entries'][ekey]['data'][self.counter]['signal'])
            ydatas.append(get_point_spec_data_from_entry(entry_dct, counter=counter_nm))

        if (len(xdata) <= 1):
            pmap = QtGui.QPixmap()
        else:
            if (as_thumbnail):
                # return a lower res pmap for use as a thumbnail image
                # use a white background
                qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=2, height=1.65, dpi=50, axes_bgrnd_color='#FFFFFF')
                pmap = qt_mpl.get_pixmap(as_grayscale=True, as_thumbnail=True)
            else:
                # return a higher res pixmap for eventual printing
                # qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=2, height=1.65, dpi=2000, axes_bgrnd_color='#FFFFFF')
                # qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=1.5, height=0.68, dpi=1000, axes_bgrnd_color='#FFFFFF')
                qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=6.2, height=5.5, dpi=1500, axes_bgrnd_color='#FFFFFF')
                pmap = qt_mpl.get_pixmap(as_grayscale=False, as_thumbnail=False)

        if (as_thumbnail):
            pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.KeepAspectRatio)

        return (pmap)

    def get_2dimage_pic(self, scale_it=True, as_thumbnail=True):
        """
        getpic(): description

        :returns: None
        """
        if (self.data is not None):
            if (len(self.data.shape) == 2):
                wd, ht = self.data.shape
                # data = np.flipud(self.data)
                # data = self.data
                data = flip_data_upsdown(self.data)
                shape = data.shape

            elif (len(self.data.shape) == 3):
                img_seq, wd, ht = self.data.shape
                # data = np.flipud(self.data[0])
                # data = self.data[0]
                data = flip_data_upsdown(self.data[0])
                shape = data.shape

            else:
                # _logger.error('unsupported data shape')
                return (None)
        else:
            _logger.error('data is None in [%s]' % self.hdf5_path)
            return (None)

        # convert it to a QPixmap for display:
        pmap = array_to_gray_qpixmap(data)
        if (scale_it):
            # pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)),  QtCore.Qt.KeepAspectRatio)
            pmap = pmap.scaled(QtCore.QSize(QtCore.QSize(THMB_SIZE, THMB_SIZE)), QtCore.Qt.IgnoreAspectRatio)
        else:
            ht, wd = self.data.shape
            # pmap.scaled(QtCore.QSize(QtCore.QSize(wd, ht)), QtCore.Qt.KeepAspectRatio)
            pmap.scaled(QtCore.QSize(QtCore.QSize(wd, ht)), QtCore.Qt.IgnoreAspectRatio)

        return pmap

    def paint(self, painter, option, widget):
        """
        paint(): description

        :param painter: painter description
        :type painter: painter type

        :param option: option description
        :type option: option type

        :param widget: widget description
        :type widget: widget type

        :returns: None
        """
        black_pm = QtGui.QPixmap(THMB_SIZE, THMB_SIZE)
        black_pm.fill(QtCore.Qt.black)
        if (self.pic is not None):
            if (self.is_selected):
                self.pen.setBrush(QtCore.Qt.blue)
            else:
                self.pen.setBrush(QtCore.Qt.black)
                self.pen.setStyle(QtCore.Qt.SolidLine)

            painter.setPen(self.pen)
            # Draw border
            painter.drawRect(QtCore.QRect(0,
                                          0,
                                          black_pm.rect().width() + self.bordersize,
                                          black_pm.rect().height() + self.labelheight + self.bordersize))

            # Fill label
            painter.fillRect(QtCore.QRect(self.bordersize,
                                          self.bordersize + black_pm.rect().height(),
                                          black_pm.rect().width(),
                                          self.labelheight),
                             QtCore.Qt.gray)

            btm_rectF = QtCore.QRectF(0, 0, THMB_SIZE, THMB_SIZE)  # the left half

            # drawPixmap(const  QRectF & target, const QPixmap & pixmap, const QRectF & source)
            painter.drawPixmap(btm_rectF, black_pm, QtCore.QRectF(black_pm.rect()))

            # painter.drawPixmap(btm_rectF, self.pic, QtCore.QRectF(black_pm.rect()))
            pic_rectF = QtCore.QRectF(self.pic.rect())
            cb = black_pm.rect().center()
            # now see if the aspect ratio is equal or different, if so adjust image to sit in the center with a black border
            if (self.pic.width() < self.pic.height()):
                cb.setY(1)
                cp = self.pic.rect().center()
                x = (THMB_SIZE / 2) - cp.x()
                cb.setX(x)

                painter.drawPixmap(cb, self.pic, pic_rectF)
            elif (self.pic.width() > self.pic.height()):
                cb.setX(1)
                cp = self.pic.rect().center()
                y = (THMB_SIZE / 2) - cp.y()
                cb.setY(y)
                # cb is the 0,0, origin point for the drawing
                painter.drawPixmap(cb, self.pic, pic_rectF)
            else:
                painter.drawPixmap(btm_rectF, self.pic, QtCore.QRectF(black_pm.rect()))

            # Draw text
            # QRect(x, y, width, height)
            text_rect = QtCore.QRect(0,  # x
                                     black_pm.rect().y() + black_pm.rect().height(),  # y
                                     black_pm.rect().width(),  # width
                                     self.labelheight)  # height
            font = painter.font()
            font.setPixelSize(11)
            painter.setFont(font)
            painter.drawText(text_rect, QtCore.Qt.AlignCenter, self.title)

    def mouseDoubleClickEvent(self, event):
        if (self.is_folder):
            path = self.fname
            if (self.fname.find('..') > -1):
                # we want an updir path emittted here
                path, folder = os.path.split(self.fname)
                path, folder = os.path.split(path)
                # print('DoubleClicked: [%s]' % path)
            self.dbl_clicked.emit(path)

    def mousePressEvent(self, event):
        """
        mousePressEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        btn = event.button()

        if (self.is_selected):
            self.is_selected = False
        else:
            self.is_selected = True

        self.select.emit(self)
        if (self.pic is not None):
            self.update(QtCore.QRectF(0.0,
                                      0.0,
                                      self.pic.rect().width() + self.bordersize,
                                      self.pic.rect().height() + self.labelheight + self.bordersize))
        QtWidgets.QGraphicsItem.mousePressEvent(self, event)

        if btn == QtCore.Qt.LeftButton:
            self.drag.emit(self, event)

    def load_scan(self):
        """
        load_scan(): description

        :returns: None
        """
        print('loading %s.hdf5' % self.hdf5_path)

    def launch_vwr(self, sender):
        """
        launch_vwr(): description
        need to decide in here what teh scan_type is and create the data such that all data is passed that is needed to recreat e the plot by cureveViewer widget
        self.sp_db contains everything
        :returns: None
        """
        # print 'launch_viewer %s.hdf5' % self.hdf5_path
        self = sender

        if (self.scan_type is scan_types.GENERIC_SCAN):
            ekey = get_first_entry_key(self.dct)
            entry_dct = self.dct['entries'][ekey]
            sp_db = get_first_sp_db_from_entry(entry_dct)
            xdata = get_axis_setpoints_from_sp_db(sp_db, axis='X')
            ydatas = get_generic_scan_data_from_entry(entry_dct, counter=DNM_DEFAULT_COUNTER)
            dct = {}
            # because the data in the StxmImageWidget is displayed with 0Y at the btm
            # and maxY at the top I must flip it before sending it
            # dct['data'] = np.flipud(data)
            dct['data'] = None
            dct['xdata'] = xdata
            dct['ydatas'] = ydatas
            dct['path'] = self.hdf5_path
            dct['sp_db'] = self.sp_db
            dct['scan_type'] = self.scan_type
            dct['title'] = None
            if (self.sp_db is not None):
                dct['title'] = self.title
            self.launch_viewer.emit(dct)


        elif (self.scan_type is scan_types.SAMPLE_POINT_SPECTRUM):
            ekey = get_first_entry_key(self.dct)
            entry_dct = self.dct['entries'][ekey]
            xdata = get_point_spec_energy_data_from_entry(entry_dct, counter=self.counter)
            # xdata = self.dct['entries'][ekey]['data'][self.counter]['energy']['signal']

            ydatas = []
            # it matters that the data is in sequential entry order
            # ekeys = sorted(self.dct['entries'].keys())
            ekeys = sorted([k for k,v in self.dct['entries'].items() if k.find('entry') > -1])
            for ekey in ekeys:
                entry_dct = self.dct['entries'][ekey]
                # ydatas.append(self.dct['entries'][ekey]['data'][self.counter]['signal'])
                ydatas.append(get_point_spec_data_from_entry(entry_dct, counter=self.counter))
            dct = {}
            dct['data'] = None
            dct['xdata'] = xdata
            dct['ydatas'] = ydatas
            dct['path'] = self.hdf5_path
            dct['sp_db'] = self.sp_db
            dct['scan_type'] = self.scan_type
            dct['title'] = None
            if (self.sp_db is not None):
                dct['title'] = self.title
            self.launch_viewer.emit(dct)


        else:

            if (self.data.ndim == 3):

                l = len(self.title.split('.')[0].split('_'))
                if (l > 1):
                    # found a '_' character indicating its a stack image
                    i = int(self.title.split('.')[0].split('_')[1])
                    data = self.data[i]
                else:
                    # its a single image
                    data = self.data[0]

            # if(self.data.ndim == 2):
            if (self.data.ndim in [1, 2]):
                data = self.data

                dct = {}
                # because the data in the StxmImageWidget is displayed with 0Y at the btm
                # and maxY at the top I must flip it before sending it
                # dct['data'] = np.flipud(data)
                dct['data'] = data
                dct['path'] = self.hdf5_path
                dct['sp_db'] = self.sp_db
                dct['scan_type'] = self.scan_type
                dct['title'] = None
                if (self.sp_db is not None):
                    dct['title'] = self.title
                self.launch_viewer.emit(dct)

    def mouseHoverEvent(self, event):
        """
        mouseHoverEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        print('Widget enter')

    def mouseReleaseEvent(self, event):
        """
        mouseReleaseEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        pass
        # self.pen.setStyle(QtCore.Qt.DotLine)
        # QtWidgets.QGraphicsWidget.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """
        hoverLeaveEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """
        pass
        # self.pen.setStyle(QtCore.Qt.SolidLine)
        # QtWidgets.QGraphicsWidget.hoverLeaveEvent(self, event)


# def get_pixmap(fname):
#     """
#     get_pixmap(): description
#
#     :param get_pixmap(fname: get_pixmap(fname description
#     :type get_pixmap(fname: get_pixmap(fname type
#
#     :returns: None
#     """
#     pmap = QtGui.QPixmap(fname)
#     #pmap.scaled(64, 64)#, aspectRatioMode=Qt_IgnoreAspectRatio, transformMode=Qt_FastTransformation)
#     pmap = pmap.scaled(QtCore.QSize(16,16),  QtCore.Qt.KeepAspectRatio)
#     return(pmap)
#

class MainGraphicsWidget(QtWidgets.QGraphicsWidget):
    def __init__(self):
        """
        __init__(): description

        :returns: None
        """
        QtWidgets.QGraphicsWidget.__init__(self)
        self.gridlayout = None
        self.cur_row = 0
        self.cur_column = 0

        self.init_layout()

    def incr_row(self):
        self.cur_row += 1

    def incr_column(self):
        self.cur_column += 1

    def reset_row(self):
        self.cur_row = 0

    def reset_column(self):
        self.cur_column = 0

    def set_cur_row(self, val):
        self.cur_row = val

    def set_cur_column(self, val):
        self.cur_column = val

    def init_layout(self):
        if (self.gridlayout is not None):
            del self.gridlayout
        self.gridlayout = QtWidgets.QGraphicsGridLayout()
        self.gridlayout.setContentsMargins(0, 5, 5, 0)
        self.setLayout(self.gridlayout)

    def set_layout_size(self, qr):
        """
        set_layout_size(): description

        :param qr: qr description
        :type qr: qr type

        :returns: None
        """
        gwl = self.layout()
        gwl.setGeometry(QtCore.QRectF(qr.x(), qr.y(), qr.width(), THUMB_HEIGHT))
        gwl.updateGeometry()

    def boundingRect(self):
        """
        boundingRect(): description

        :returns: None
        """
        # print self.gridlayout.contentsRect()
        return (self.gridlayout.contentsRect())

    def clear_layout(self):
        """
        clear_layout(): description

        :returns: None
        """

        if ((self.gridlayout.rowCount() == 0) and (self.gridlayout.columnCount() == 0)):
            return
        for row in range(self.gridlayout.count()):
            # the count() will change as the items are removed
            # so just keep pulling them from teh top [0]
            item = self.gridlayout.itemAt(self.gridlayout.count() - 1)
            self.gridlayout.removeAt(self.gridlayout.count() - 1)
            # this call makes the thumbwidget dissappear
            item.close()
            # now delete it
            del item

        self.set_layout_size(QtCore.QRectF(self.rect().x(), self.rect().y(), self.rect().width(), THUMB_HEIGHT))


class ContactSheet(QtWidgets.QWidget):
    def __init__(self, data_dir="", data_io=None, counter=DNM_DEFAULT_COUNTER, parent=None):
        """
        __init__(): description

        :param data_dir="": data_dir="" description
        :type data_dir="": data_dir="" type

        :returns: None
        """
        super(ContactSheet, self).__init__(parent)
        # QtWidgets.QWidget.__init__(parent)

        # self.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
        # self.setStyleSheet("QToolTip { color: #ffffff; background-color: rgb(26, 106, 255); border: 1px solid white; }")
        self.setStyleSheet(
            "QToolTip { color: rgb(20, 20, 20); background-color: rgb(181, 179, 181); border: 1px solid grey; }")
        self.counter_nm = counter
        self.data_io_class = data_io
        self.data_io = None
        self.appname = "Contact Sheet"
        self.setObjectName('contactSheet')
        # self.image_win = None
        self.image_win = self.create_image_viewer()

        self.spec_win = None
        self.drag_enabled = True
        self.image_thumbs = []
        self.spectra_thumbs = []
        self.setWindowTitle(self.appname)

        self.progbar = None
        self.threadpool = QtCore.QThreadPool()

        self.tabs = QtWidgets.QTabWidget()
        font = self.tabs.font()
        font.setPixelSize(11)
        self.tabs.setFont(font)

        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)

        self.images_scene = QtWidgets.QGraphicsScene()
        self.spectra_scene = QtWidgets.QGraphicsScene()

        self.images_scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(50, 50, 50)))
        self.spectra_scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(50, 50, 50)))
        # self.data_dir = r'C:/controls/py2.7/Beamlines/sm/data/guest/Apr29'
        self.data_dir = data_dir
        self.image_file_extension = '.jpg'
        self.data_file_extension = '.hdf5'
        self.formats = '*' + self.image_file_extension

        self.dir_lbl = QtWidgets.QLabel('')
        self.dir_lbl.setAlignment(QtCore.Qt.AlignHCenter)
        font = self.dir_lbl.font()
        font.setPixelSize(11)
        font.setBold(True)
        self.dir_lbl.setFont(font)
        self.dir_lbl.contextMenuEvent = self.dirLabelContextMenuEvent
        # s = '<a style="background-color: transparent; color: %s"><b>%s</b>\t <a border-width: 50px; style="background-color: %s; color: %s"><b>%s</b> </a>' % (title_color, title, bgcolor, var_color, var)

        # self.refreshBtn = QtWidgets.QPushButton("rld")
        # self.refreshBtn.setToolTip('Reload current directory')
        # self.refreshBtn.clicked.connect(self.reload_dir)

        self.refreshBtn = QtWidgets.QToolButton()
        ico_dir = icoDir
        ico_psize = '/64x64/'
        ico_clr = 'gray'

        # pmap = get_pixmap(os.path.join(ico_dir + ico_clr + ico_psize + 'reload.png')

        pmap = get_pixmap(os.path.join(icoDir, 'reload.ico'), ICONSIZE, ICONSIZE)

        self.refreshBtn.setIcon(QtGui.QIcon(QtGui.QPixmap(pmap)))  # .scaled(48,48, QtCore.Qt.KeepAspectRatio)))
        self.refreshBtn.setIconSize(QtCore.QSize(ICONSIZE, ICONSIZE))
        self.refreshBtn.setFixedSize(BTNSIZE, BTNSIZE)
        self.refreshBtn.setToolTip('Reload current directory')
        self.refreshBtn.clicked.connect(self.reload_dir)

        self.images_view = QtWidgets.QGraphicsView(self.images_scene)
        self.spectra_view = QtWidgets.QGraphicsView(self.spectra_scene)

        self.f_queue = queue.Queue()

        self.fsys_mon = DirectoryMonitor(self.f_queue)
        # self.fsys_mon.set_file_extension_filter(self.image_file_extension)
        self.fsys_mon.set_file_extension_filter('hdf5')
        self.fsys_mon.set_data_dir(self.data_dir)
        # self.fsys_mon.changed.connect(self.on_dir_changed)
        self.fsys_mon.changed.connect(self.update_file_list)
        # set QGraphicsView attributes
        # self.images_view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.HighQualityAntialiasing)
        # self.images_view.setViewportUpdateMode(QtWidgets.QGraphicsView.MinimalViewportUpdate)
        hlayout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setContentsMargins(2, 1, 1, 1)
        hlayout.addWidget(self.refreshBtn)
        hlayout.addWidget(self.dir_lbl)
        # hlayout.addWidget(self.refreshBtn)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.images_view)
        self.setLayout(vlayout)

        self.images_graphics_wdg = MainGraphicsWidget()
        self.images_scene.addItem(self.images_graphics_wdg)

        self.spectra_graphics_wdg = MainGraphicsWidget()
        self.spectra_scene.addItem(self.spectra_graphics_wdg)

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.update_file_list)
        self.set_data_dir(data_dir, hide=True)
        self.ptnw = PrintSTXMThumbnailWidget()

        self.tabs.addTab(self.images_view, 'Images')
        self.tabs.addTab(self.spectra_view, 'Spectra')
        vlayout.addWidget(self.tabs)

    def create_image_viewer(self):
        fg_clr = rgb_as_hex(master_colors['plot_forgrnd'])
        bg_clr = rgb_as_hex(master_colors['plot_bckgrnd'])
        min_clr = rgb_as_hex(master_colors['plot_gridmaj'])
        maj_clr = rgb_as_hex(master_colors['plot_gridmin'])
        image_win = make_default_stand_alone_stxm_imagewidget(data_io=self.data_io)
        image_win.setWindowTitle('Image Viewer')
        qssheet = get_style('dark')
        image_win.setStyleSheet(qssheet)
        image_win.set_grid_parameters(bg_clr, min_clr, maj_clr)
        image_win.set_cs_grid_parameters(fg_clr, bg_clr, min_clr, maj_clr)
        image_win.closeEvent = self.on_viewer_closeEvent

        return (image_win)

    def set_drag_enabled(self, val):
        self.drag_enabled = val

    def get_drag_enabled(self):
        return (self.drag_enabled)

    def update_file_list(self):
        call_task_done = False
        f_added = []
        f_removed = []
        while not self.f_queue.empty():
            resp = self.f_queue.get()
            # if ('added' in resp.keys()):
            if ('added' in list(resp)):
                f_added = resp['added']
                call_task_done = True

            if ('removed' in list(resp)):
                f_removed = resp['removed']
                call_task_done = True

        if (call_task_done):
            self.on_dir_changed((f_added, f_removed))
            self.f_queue.task_done()

    def dirLabelContextMenuEvent(self, event):
        """
        dirLabelContextMenuEvent(): description

        :param event: event description
        :type event: event type

        :returns: None
        """

        menu = QtWidgets.QMenu()
        chgdirAction = QtWidgets.QAction("Change Directory", self)
        chgdirAction.triggered.connect(self.on_change_dir)

        menu.addAction(chgdirAction)
        menu.exec_(event.globalPos())

    def is_stack_dir(self, data_dir):
        """
        is_stack_dir(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :returns: None
        """
        if (len(data_dir) > 0):
            d_lst = self.split_data_dir(data_dir)
            dname = d_lst[-1]
            fstr = os.path.join(data_dir, dname + '.hdf5')
            if (os.path.exists(fstr)):
                return (True)
            else:
                return (False)
        else:
            _logger.error('Invalid data directory')
            return (False)

    def get_stack_file_name(self, data_dir):
        """
        get_stack_file_name(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :returns: None
        """
        d_lst = self.split_data_dir(data_dir)
        dname = d_lst[-1]
        return (dname + '.hdf5')

    def get_stack_data(self, fname):
        """
        get_stack_data(): description

        :param fname: fname description
        :type fname: fname type

        :returns: None
        """
        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        self.ensure_instance_of_data_io_class(fname)
        if (data_dir is None):
            # _logger.info('Problem with file [%s]' % fname)
            return (None, None)

        # ado_obj = self.get_entries(data_dir, fprefix, fsuffix)
        # if(ado_obj is None):
        #    #_logger.info('Problem with file [%s]' % fname)
        #    return('', '')
        entry_dct = self.get_entries(data_dir, fprefix, fsuffix)
        if (entry_dct is None):
            _logger.info('Problem with file [%s]' % fname)
            return (None, None)

        # wdg_com = dct_get(ado_obj, ADO_CFG_WDG_COM)
        # ekey = entry_dct.keys()[0]
        ekey = list(entry_dct)[0]
        wdg_com = self.data_io.get_wdg_com_from_entry(entry_dct, ekey)
        sp_db = get_first_sp_db_from_wdg_com(wdg_com)
        # data = ado_obj['DATA']
        data = self.get_data_from_entry(entry_dct, ekey, stack_dir=True, fname=fname)

        return (sp_db, data)

    def get_sp_db_and_data(self, fname, stack_dir=False):
        """
        get_sp_db_and_data(): description

        :param fname: fname description
        :type fname: fname type

        :returns: None
        """
        from cls.utils.roi_utils import get_ado_obj_from_wdg_com
        sp_db = data = None
        fname = str(fname)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        if (data_dir is None):
            _logger.info('Problem with file [%s]' % fname)
            return (sp_db, data)

        entry_dct = self.get_entries(data_dir, fprefix, fsuffix)
        if (entry_dct is None):
            _logger.info('Problem with file [%s]' % fname)
            return (sp_db, data)

        ekeys = [k for k,v in entry_dct.items() if k.find('entry') > -1]

        num_entries = len(ekeys)
        sp_db_lst = []
        data_lst = []

        if (num_entries > 1):
            # for ekey in entry_dct.keys():
            for ekey in ekeys:
                wdg_com = self.data_io.get_wdg_com_from_entry(entry_dct, ekey)
                _sp_db = get_first_sp_db_from_wdg_com(wdg_com)
                _scan_type = dct_get(_sp_db, SPDB_SCAN_PLUGIN_TYPE)
                _data = self.get_data_from_entry(entry_dct, ekey, stack_dir=stack_dir, fname=fname, stype=_scan_type)
                sp_db_lst.append(_sp_db)
                data_lst.append(_data)
        else:
            if(num_entries == 0):
                #there is a problem,
                _logger.error('get_sp_db_and_data: there is aproblem with the file [%s]' % fprefix)
                return([],[])
            ekey = ekeys[0]
            wdg_com = self.data_io.get_wdg_com_from_entry(entry_dct, ekey)
            sp_db = get_first_sp_db_from_wdg_com(wdg_com)
            _scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
            data = self.get_data_from_entry(entry_dct, ekey, stack_dir=stack_dir, fname=fname, stype=_scan_type)
            if(sp_db['EV_NPOINTS'] > 1):
                sp_db_lst.append(sp_db)
                data_lst.append(data)

        try:
            if (len(data_lst) > 0):
                stack_dir = 1
                # dl = len(data_lst[0])
                dl_shape = data_lst[0].shape
                if (data_lst[0].ndim == 1):
                    data = np.zeros((num_entries, dl_shape[0]))
                elif (data_lst[0].ndim == 2):
                    data = np.zeros((num_entries, dl_shape[0], dl_shape[1]))
                elif (data_lst[0].ndim == 3):
                    data = np.zeros((num_entries, dl_shape[0], dl_shape[1], dl_shape[2]))

                # data = np.zeros((num_entries, dl_shape[0], dl_shape[1]))
                for i in range(num_entries):
                    data[i] = data_lst[i]
                sp_db = sp_db_lst[0]

        except:
            _logger.error('get_sp_db_and_data: problem with [%s]' % fname)
        if (stack_dir):
            return (sp_db_lst, data_lst)
        else:
            return (sp_db, data)

    def ensure_instance_of_data_io_class(self, fname):
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        self.data_io = self.data_io_class(data_dir, fprefix)

    def get_entries(self, data_dir, fprefix, fsuffix):
        """
        get_entries(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :param fprefix: fprefix description
        :type fprefix: fprefix type

        :param fsuffix: fsuffix description
        :type fsuffix: fsuffix type

        :returns: None
        """
        fname = data_dir + fprefix + fsuffix
        self.ensure_instance_of_data_io_class(fname)
        entry_dct = self.data_io.load()
        return (entry_dct)

    def get_data_from_entry(self, entry_dct, ekey, spid_idx=0, stack_dir=False, fname=None, stype=None):
        """
        get_data_from_entry(): description

        :param ado_obj: ado_obj description
        :type ado_obj: ado_obj type

        :param spid_idx: spid_idx index into list of sp_ids
        :type spid_idx: integer


        :returns: None
        """
        if (entry_dct is None):
            _logger.error('entry_dct cannot be None')
            return

        # ekey = entry_dct.keys()[0]
        if(self.data_io is None):
            self.ensure_instance_of_data_io_class(fname)
        nx_datas = self.data_io.get_NXdatas_from_entry(entry_dct, ekey)
        # currently only support 1 counter
        # counter_name = nx_datas.keys()[0]
        ## IN THE FUTURE THIS NEEDS TO BE CONFIGURABLE GIVEN THE EXISTANCE OF MULTI DETECTORS
        # counter_name = self.counter_nm

        data = self.data_io.get_signal_data_from_NXdata(nx_datas, self.counter_nm)
        if (data is not None):
            if ((data.ndim is 3)):
                if (stack_dir):
                    return (data)
                if (stype is not None):
                    if (stype is scan_types.GENERIC_SCAN):
                        return (data[0][0])

                if (len(data) > 0):
                    data = data[0]
                else:
                    return (None)

            # if((data.ndim is not 2)):
            #     #_logger.error('Data  is of wrong dimension, is [%d] should be [2]' % (data.ndim))
            #     #print 'Data is of wrong dimension, is [%d] should be [2]' % (data.ndim)
            #     return(None)

        return (data)

    def set_image_report(self, info_str, info_jstr):
        """
        set_image_report(): description

        :param info_str: info_str description
        :type info_str: info_str type

        :param info_jstr: info_jstr description
        :type info_jstr: info_jstr type

        :returns: None
        """
        self.image_info_str = info_str
        self.image_info_jstr = info_jstr

    def extract_date_time_from_nx_time(self, nx_time):
        dt = nx_time.split('T')[0]
        _tm = nx_time.split('T')[1]
        tm = _tm.split('.')[0]
        return (dt, tm)

    def build_image_params(self, fpath, sp_db, data, ev_idx=0, ev_pnt=0, pol_idx=0, pol_pnt=0, is_folder=False):
        """
        build_image_params(): create a string and json string that represents the key bits of information
            on this image. The json string is used for drag and drop events so that the widget that receives the 'drop' has
            enough info to load the image, scan or display the relevant information.

        :param fpath: the filename
        :type fpath: string

        :param sp_db:  This is the standard spatial database dict that is used throughout the application, refer to
                        make_spatial_db_dict() in stxm_control/stxm_utils/roi_utils.py for a detailed look at the structure
                        of an sp_db
        :type sp_db: sp_db type

        :param data: A numpy array that contains the image data
        :type data: data type

        :param ev_idx: the index into the correct ev_roi for this image
        :type ev_idx: integer

        :param ev_pnt: the index into the correct energy point in the ev_roi for this image
        :type ev_pnt: integer

        :param pol_idx: the index into the correct polarization_roi for this image
        :type pol_idx: integer

        :param pol_pnt: the index into the correct polarization point in the pol_roi for this image
        :type pol_pnt: integer

        :returns:  a tuple consisting of a string used for the tooltip data and a json string used for drag and drop operations

        scan_types = Enum('detector_image', \
				'osa_image', \
				'osa_focus', \
				'sample_focus', \
				'sample_point_spectra', \
				'sample_line_spectra', \
				'sample_image', \
				'sample_image_stack', \
				'generic_scan', \
				'coarse_image')


        """
        if (sp_db is None):
            return (None, None)
        focus_scans = [scan_types.OSA_FOCUS, scan_types.SAMPLE_FOCUS]
        spectra_scans = [scan_types.SAMPLE_POINT_SPECTRUM, scan_types.SAMPLE_LINE_SPECTRUM]
        stack_scans = [scan_types.SAMPLE_IMAGE_STACK]
        _scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)

        if (data is None):
            if (_scan_type is scan_types.SAMPLE_POINT_SPECTRUM):
                data = np.ones((2, 2))
            else:
                return (None, None)

        if (data.size == 0):
            if (_scan_type is scan_types.SAMPLE_POINT_SPECTRUM):
                data = np.ones((2, 2))
            else:
                return (None, None)

        if (data.ndim == 3):
            data = data[0]

        # if(data.ndim == 2):
        if (data.ndim in [1, 2]):
            # hack
            e_pnt = sp_db[EV_ROIS][ev_idx][SETPOINTS][ev_pnt]
            e_npts = 0
            for e in sp_db['EV_ROIS']:
                if (len(e[SETPOINTS]) > 1):
                    e_npts += len(e[SETPOINTS])
                else:
                    e_npts = 1

            if (type(e_pnt) is list):
                e_pnt = e_pnt[0]

            if (data.ndim is 1):
                height = 1
                width, = data.shape
            else:
                height, width = data.shape

            # s = 'File: %s  \n' %  (fprefix + '.hdf5')
            #if (fpath.find('12162') > -1):
            #    print()
            dct = {}
            dct['file'] = fpath
            dct['scan_type_num'] = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)
            dct['scan_type'] = scan_types[dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)] + ' ' + scan_sub_types[
                dct_get(sp_db, SPDB_SCAN_PLUGIN_SUBTYPE)]
            dct['scan_panel_idx'] = dct_get(sp_db, SPDB_SCAN_PLUGIN_PANEL_IDX)
            dct['energy'] = e_pnt
            dct['estart'] = sp_db[EV_ROIS][ev_idx][START]
            dct['estop'] = sp_db[EV_ROIS][ev_idx][STOP]
            dct['e_npnts'] = e_npts
            dct['polarization'] = convert_wrapper_epu_to_str(sp_db[EV_ROIS][ev_idx][POL_ROIS][pol_idx][POL])
            dct['offset'] = sp_db[EV_ROIS][ev_idx][POL_ROIS][pol_idx][OFF]
            dct['angle'] = sp_db[EV_ROIS][ev_idx][POL_ROIS][pol_idx][ANGLE]
            dct['dwell'] = sp_db[EV_ROIS][ev_idx][DWELL]
            # dct['npoints'] = (width, height)
            dct['npoints'] = (dct_get(sp_db, SPDB_XNPOINTS), dct_get(sp_db, SPDB_YNPOINTS))
            if (width != dct_get(sp_db, SPDB_XNPOINTS)):
                _logger.debug('[%s] The data doesnt match the scan params for X npoints' % fpath)
                width = dct_get(sp_db, SPDB_XNPOINTS)

            if (height != dct_get(sp_db, SPDB_YNPOINTS)):
                _logger.debug('[%s] The data doesnt match the scan params for Y npoints' % fpath)
                height = dct_get(sp_db, SPDB_YNPOINTS)

            if (type(sp_db[SPDB_ACTIVE_DATA_OBJECT][ADO_END_TIME]) is bytes):
                date_str = sp_db[SPDB_ACTIVE_DATA_OBJECT][ADO_END_TIME].decode("utf-8")
            else:
                date_str = sp_db[SPDB_ACTIVE_DATA_OBJECT][ADO_END_TIME]

            # dt, tm = self.extract_date_time_from_nx_time(sp_db[SPDB_ACTIVE_DATA_OBJECT][ADO_END_TIME])
            dt, tm = self.extract_date_time_from_nx_time(date_str)
            dct['date'] = dt
            dct['end_time'] = tm

            if (_scan_type in focus_scans):

                zzcntr = dct_get(sp_db, SPDB_ZZCENTER)
                if (zzcntr is None):
                    zzcntr = dct_get(sp_db, SPDB_ZCENTER)
                # dct['center'] = (dct_get(sp_db, SPDB_XCENTER), dct_get(sp_db, SPDB_ZZCENTER))
                dct['center'] = (dct_get(sp_db, SPDB_XCENTER), zzcntr)
                zzrng = dct_get(sp_db, SPDB_ZZRANGE)
                if (zzrng is None):
                    zzrng = dct_get(sp_db, SPDB_ZRANGE)
                dct['range'] = (dct_get(sp_db, SPDB_XRANGE), zzrng)

                zzstep = dct_get(sp_db, SPDB_ZZSTEP)
                if (zzstep is None):
                    zzstep = dct_get(sp_db, SPDB_ZSTEP)
                dct['step'] = (dct_get(sp_db, SPDB_XSTEP), zzstep)

                zzstrt = dct_get(sp_db, SPDB_ZZSTART)
                if (zzstrt is None):
                    zzstrt = dct_get(sp_db, SPDB_ZSTART)
                dct['start'] = (dct_get(sp_db, SPDB_XSTART), zzstrt)

                zzstop = dct_get(sp_db, SPDB_ZZSTOP)
                if (zzstop is None):
                    zzstop = dct_get(sp_db, SPDB_ZSTOP)
                dct['stop'] = (dct_get(sp_db, SPDB_XSTOP), zzstop)

                zzposner = dct_get(sp_db, SPDB_ZZPOSITIONER)
                if (zzposner is None):
                    zzposner = dct_get(sp_db, SPDB_ZPOSITIONER)
                dct['ypositioner'] = zzposner

                dct['xpositioner'] = dct_get(sp_db, SPDB_XPOSITIONER)
            else:
                dct['center'] = (dct_get(sp_db, SPDB_XCENTER), dct_get(sp_db, SPDB_YCENTER))
                dct['range'] = (dct_get(sp_db, SPDB_XRANGE), dct_get(sp_db, SPDB_YRANGE))
                dct['step'] = (dct_get(sp_db, SPDB_XSTEP), dct_get(sp_db, SPDB_YSTEP))
                dct['start'] = (dct_get(sp_db, SPDB_XSTART), dct_get(sp_db, SPDB_YSTART))
                dct['stop'] = (dct_get(sp_db, SPDB_XSTOP), dct_get(sp_db, SPDB_YSTOP))
                dct['xpositioner'] = dct_get(sp_db, SPDB_XPOSITIONER)
                dct['ypositioner'] = dct_get(sp_db, SPDB_YPOSITIONER)

            # if ('GONI' in sp_db.keys()):
            if ('GONI' in list(sp_db)):
                if (dct_get(sp_db, SPDB_GT) is None):
                    pass
                if (dct_get(sp_db, SPDB_GZCENTER) is not None):
                    # pass
                    dct['goni_z_cntr'] = dct_get(sp_db, SPDB_GZCENTER)
                if (dct_get(sp_db, SPDB_GTCENTER) is not None):
                    dct['goni_theta_cntr'] = dct_get(sp_db, SPDB_GTCENTER)

            jstr = json.dumps(dct)
            # construct the tooltip string using html formatting for bold etc
            s = '%s' % self.format_info_text('File:', dct['file'], start_preformat=True)
            s += '%s %s' % (
                self.format_info_text('Date:', dct['date'], newline=False),
                self.format_info_text('Time:', dct['end_time']))

            if (_scan_type is scan_types.GENERIC_SCAN):
                # add the positioner name
                # s += '%s' % self.format_info_text('Scan Type:', dct['scan_type'] + ' %s' % dct_get(sp_db, SPDB_XPOSITIONER))
                s += '%s' % self.format_info_text('Scan Type:', dct['scan_type'], newline=False)
                s += ' %s' % self.format_info_text(dct_get(sp_db, SPDB_XPOSITIONER), '')

            else:
                s += '%s' % self.format_info_text('Scan Type:', dct['scan_type'])

            # s += '%s' % self.format_info_text('Scan Type:', dct['scan_type'])
            # if (is_folder and ( (_scan_type in spectra_scans) or (_scan_type in stack_scans)) ):
            if ((_scan_type in spectra_scans) or (_scan_type in stack_scans)):
                # s += '%s' % self.format_info_text('Energy:', '[%.2f ---> %.2f] eV' % (dct['estart'], dct['estop']))
                # s += '%s' % self.format_info_text('Num Energy Points:', '%d' % dct['e_npnts'])
                # s += '%s' % self.format_info_text('Energy:', '[%.2f ---> %.2f] eV   %s' % (dct['estart'], dct['estop'],
                #                                    self.format_info_text('Num Energy Points:', '%d' % dct['e_npnts'])))
                s += '%s %s' % (
                self.format_info_text('Energy:', '[%.2f ---> %.2f] eV \t' % (dct['estart'], dct['estop']),
                                      newline=False),
                self.format_info_text('Num Energy Points:', '%d' % dct['e_npnts']))
            else:
                s += '%s' % self.format_info_text('Energy:', '%.2f eV' % (e_pnt))

            _s1 = '%s' % (self.format_info_text('Polarization:', '%s' % convert_wrapper_epu_to_str(
                sp_db[EV_ROIS][ev_idx][EPU_POL_PNTS][pol_idx]), newline=False))
            _s2 = '%s' % (self.format_info_text('Offset:', '%.2f mm' % sp_db[EV_ROIS][ev_idx][EPU_OFF_PNTS][pol_idx],
                                                newline=False))
            _s3 = '%s' % (self.format_info_text('Angle:', '%.2f deg' % sp_db[EV_ROIS][ev_idx][EPU_ANG_PNTS][pol_idx]))
            s += '%s %s %s' % (_s1, _s2, _s3)
            s += '%s' % self.format_info_text('Dwell:', '%.2f ms' % (sp_db[EV_ROIS][ev_idx][DWELL]))
            s += '%s' % self.format_info_text('Points:', '%d x %d ' % (width, height))
            s += '%s' % self.format_info_text('Center:', '(%.2f, %.2f) um' % dct['center'])
            s += '%s' % self.format_info_text('Range:', '(%.2f, %.2f) um' % dct['range'])

            # if (_scan_type in focus_scans):
            #     s += '%s' % self.format_info_text('ZPZ Range:', '(%.2f, %.2f) um' % dct['range'])
            # if ('goni_theta_cntr' in dct.keys()):
            if ('goni_theta_cntr' in list(dct)):
                s += '%s' % self.format_info_text('StepSize:', '(%.3f, %.3f) um' % dct['step'])
                # if ('goni_z_cntr' in dct.keys()):
                if ('goni_z_cntr' in list(dct)):
                    s += '%s' % self.format_info_text('Goni Z:', '%.3f um' % dct['goni_z_cntr'])
                s += '%s' % self.format_info_text('Goni Theta:', '%.2f deg' % (dct['goni_theta_cntr']), newline=False,
                                                  end_preformat=True)
            else:
                s += '%s' % self.format_info_text('StepSize:', '(%.3f, %.3f) um' % dct['step'], newline=False,
                                                  end_preformat=True)

            return (s, jstr)
        else:
            # print 'build_image_params: Unsupported dimensions of data ->[%d]'% data.ndim
            return (None, None)

    def format_info_text(self, title, msg, title_clr='blue', newline=True, start_preformat=False, end_preformat=False):
        '''
        take arguments and create an html string used for tooltips
        :param title: The title will be bolded
        :param msg: The message will be simple black text
        :param title_clr: The Title will use this color
        :param newline: A flag to add a newline at the end of the string or not
        :param start_preformat: If this is the first string we need to start the PREformat tag
        :param end_preformat: If this is the last string we need to stop the PREformat tag
        :return:
        '''
        s = ''
        if (start_preformat):
            s += '<pre>'

        if (newline):
            s += '<font size="3" color="%s"><b>%s</b></font> %s<br>' % (title_clr, title, msg)
        else:
            s += '<font size="3" color="%s"><b>%s</b></font> %s' % (title_clr, title, msg)

        if (end_preformat):
            s += '</pre>'
        return (s)

    def reload_dir(self):
        # reload the current directory
        self.change_dir(dir=self.data_dir)

    def on_change_dir(self, dud):
        '''
        a handler for the menuContext
        :param dud:
        :return:
        '''
        self.change_dir()

    def change_dir(self, dir=None):
        """
        change_dir(): description

        :returns: None
        """
        if (dir is None):
            dir = setExistingDirectory("Pick Directory", init_dir=self.data_dir)

        prev_cursor = self.cursor()
        # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

        self.setCursor(QtCore.Qt.WaitCursor)
        # tWidgets.QApplication.processEvents()
        # check if directory contains a stack
        if (self.is_stack_dir(dir)):
            self.set_data_dir(dir, is_stack_dir=True)
            # data_fnames = dirlist(dir, self.data_file_extension, remove_suffix=False)
            dirs, data_fnames = dirlist_withdirs(dir, self.data_file_extension)
            fname = os.path.join(dir, data_fnames[0])
            sp_db, data = self.get_stack_data(fname)
            # self.load_stack_into_view(data_fnames[0])
            self.load_entries_into_view(data_fnames[0])

            self.fsys_mon.set_data_dir(self.data_dir)
            # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(prev_cursor))
            self.unsetCursor()
            # QtWidgets.QApplication.processEvents()
            return

        if (len(dir) > 0):
            self.set_data_dir(dir, is_stack_dir=False)
            self.fsys_mon.set_data_dir(self.data_dir)

        self.unsetCursor()
        # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(prev_cursor))
        # QtWidgets.QApplication.processEvents()

    # def on_dir_changed(self, (f_added, f_removed)):
    def on_dir_changed(self, f_added_removed):
        """
        on_dir_changed(): this handler needs to discern between files that are not finished writing and those that are ready to be read

        :param (f_added: (f_added description
        :type (f_added: (f_added type

        :param f_removed): f_removed) description
        :type f_removed): f_removed) type

        :returns: None
        """
        # print('on_dir_changed: added: ' , f_added)
        # print('on_dir_changed: removed: ' , f_removed)
        f_added, f_removed = f_added_removed
        prev_cursor = self.cursor()
        # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.setCursor(QtCore.Qt.WaitCursor)
        # QtWidgets.QApplication.processEvents()

        if (len(f_added) > 0):
            # self.add_to_view(f_added)
            # ROWS = (len(self.image_thumbs) + len(f_added)) / MAX_THUMB_COLUMNS
            for fname in f_added:

                fstr = os.path.join(self.data_dir, fname)
                sp_db, data = self.get_sp_db_and_data(fstr)
                # we dont support stack or multi spatials yet so just load it as a single
                if (type(sp_db) is list):
                    if(len(sp_db) == 0):
                        _logger.error('on_dir_changed: problem with [%s]' % fname)
                        return

                    sp_db = sp_db[0]
                    data = data[0]

                if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) in spectra_type_scans):
                    graphics_wdg = self.spectra_graphics_wdg
                    graphics_view = self.spectra_view
                    graphics_scene = self.spectra_scene
                else:
                    graphics_wdg = self.images_graphics_wdg
                    graphics_view = self.images_view
                    graphics_scene = self.images_scene

                if (graphics_wdg.cur_column >= MAX_THUMB_COLUMNS):
                    graphics_wdg.incr_row()
                    graphics_wdg.reset_column()

                status = self.add_to_view(fname, sp_db, data, ev_idx=0, ev_pnt=0, pol_idx=0, pol_pnt=0, row=None,
                                          col=None, update_scene=False, graphics=graphics_wdg, view=graphics_view,
                                          scene=graphics_scene)
                if (status is not None):
                    graphics_wdg.incr_column()

                # QtWidgets.QApplication.processEvents()

            self.update_scenes()
        # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(prev_cursor))
        self.unsetCursor()
        # QtWidgets.QApplication.processEvents()

    def get_file_loading_progbar(self, max):
        progbar = QtWidgets.QProgressBar()
        progbar.setFixedWidth(300)
        progbar.setWindowTitle("Loading image thumbnails")
        progbar.setAutoFillBackground(True)
        progbar.setMinimum(0)
        progbar.setMaximum(max)
        # progbar.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
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
        return (progbar)

    def load_image_items(self, is_stack_dir=False, hide=False):
        # assert isinstance(xdata, (tuple, list)) and len(xdata) == 2
        # assert isinstance(ydata, (tuple, list)) and len(ydata) == 2
        # print 'load_image_items: called'
        self.clear_grid_layout(self.images_graphics_wdg, self.images_view, self.images_scene)

        row = 0
        column = 0
        if (self.data_dir is None):
            return

        if (not os.path.exists(self.data_dir)):
            _logger.error('Data directory does not exist: [%s]' % self.data_dir)
            return

        dirs, data_fnames = dirlist_withdirs(self.data_dir, '.hdf5')
        # data_fnames = dirlist(self.data_dir, self.data_file_extension, remove_suffix=False)
        thumb_fnames = sorted(data_fnames)

        num_fnames = len(thumb_fnames)
        self.progbar = self.get_file_loading_progbar(num_fnames)

        if ((num_fnames > 10) and not hide):
            self.progbar.show()
        # ref: https://www.twobitarcade.net/article/multithreading-pyqt-applications-with-qthreadpool/
        worker = Worker(self.reload_view, self.data_dir,
                        is_stack_dir)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.load_thumbs)

        worker.signals.progress.connect(self.progress_fn)

        worker.signals.finished.connect(self.thread_complete)

        # Execute
        self.threadpool.start(worker)

    def progress_fn(self, n):
        # print("%d%% done" % n)
        self.progbar.setValue(n)

    def thread_complete(self):
        # print("THREAD COMPLETE!")
        self.progbar.hide()

    def hide_progbar(self):
        self.progbar.hide()

    def load_images_progress(self, prog):
        self.progbar.setValue(prog)

    def get_next_row_and_col(self, graphics_wdg):
        ROWS = (len(self.image_thumbs) + 1) / MAX_THUMB_COLUMNS
        if (graphics_wdg.cur_column >= MAX_THUMB_COLUMNS):
            graphics_wdg.incr_cur_row()
            rows = graphics_wdg.cur_row
            graphics_wdg.set_cur_column(0)

        return (graphics_wdg.cur_row, graphics_wdg.cur_column)

    def on_drag(self, obj, event):
        """
        on_drag(): description

        :param obj: obj description
        :type obj: obj type

        :param event: event description
        :type event: event type

        :returns: None
        """
        event.accept()

        if (self.get_drag_enabled()):
            itemData = QtCore.QByteArray()
            dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
            # dataStream << QtCore.QByteArray(obj.info_jstr) << (event.pos() - obj.rect().topLeft())
            dataStream << QtCore.QByteArray(bytearray(obj.info_jstr.encode())) << (event.pos() - obj.rect().topLeft())

            # dataStream << QtCore.QByteArray(obj.data.tobytes()) << QtCore.QByteArray(obj.info_str) << (event.pos() - obj.rect().topLeft())

            mimeData = QtCore.QMimeData()
            mimeData.setData('application/x-stxmscan', itemData)
            mimeData.setText(obj.info_jstr)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            pos = event.pos() - obj.rect().topLeft()
            drag.setHotSpot(QtCore.QPoint(pos.x(), pos.y()))
            if (obj.pic is not None):
                drag.setPixmap(obj.pic)

            if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
                pass
            else:
                pass

    def make_thumbWidget(self, data_dir, fname, info_dct, title=None, sp_db=None, data=None,
                         stype=scan_types.SAMPLE_POINT_SPECTRUM, is_folder=False):
        """
        make_thumbWidget(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :param fname: fname description
        :type fname: fname type

        :param info_dct: info_dct description
        :type info_dct: info_dct type

        :param title=None: title=None description
        :type title=None: title=None type

        :param sp_db=None: sp_db=None description
        :type sp_db=None: sp_db=None type

        :param data=None: data=None description
        :type data=None: data=None type

        :returns: None

        """
        if (fname.find('..') > -1):
            thumb_widget = ThumbnailWidget(os.path.join(data_dir, '..'), None, data, '..', info_dct, scan_type=None,
                                           is_folder=is_folder,
                                           parent=None)

        fstr = os.path.join(data_dir, fname)
        if (is_folder):
            fname = fname.split('.')[0]
            thumb_widget = ThumbnailWidget(fstr, sp_db, data, title, info_dct, scan_type=stype, is_folder=is_folder,
                                           parent=None)

        elif (stype in spectra_type_scans):
            from cls.data_io.stxm_data_io import STXMDataIo
            fname = fname.split('.')[0]
            data_io = STXMDataIo(data_dir, fname)
            entry_dct = data_io.load()
            dct = make_thumb_widg_dct(data_dir=data_dir, fname=fname, entry_dct=entry_dct, counter=DNM_DEFAULT_COUNTER)
            thumb_widget = ThumbnailWidget(fstr, sp_db, data, title, info_dct, dct=dct, scan_type=stype, parent=None)
        else:
            thumb_widget = ThumbnailWidget(fstr, sp_db, data, title, info_dct, scan_type=stype, parent=None)

        if (thumb_widget.is_valid()):

            if (is_folder):
                # thumb_widget.doubleClicked.connect(self.do_select)
                thumb_widget.dbl_clicked.connect(self.change_dir)

            else:
                # thumb_widget.update_view.connect(self.update_view)
                thumb_widget.select.connect(self.do_select)
                thumb_widget.launch_viewer.connect(self.launch_viewer)
                thumb_widget.print_thumb.connect(self.print_thumbnail)
                thumb_widget.preview_thumb.connect(self.preview_thumbnail)
                thumb_widget.drag.connect(self.on_drag)

            return (thumb_widget)
        else:
            return (None)

    def add_thumb_widget(self, data_dir, fname, info_dct, row, column, title=None, sp_db=None, data=None,
                         graphics=None, is_folder=False):
        '''

        :param data_dir:
        :param fname:
        :param info_dct:
        :param row:
        :param column:
        :param title:
        :param sp_db:
        :param data:
        :param graphics:
        :param is_folder:
        :return:
        '''
        if (graphics is None):
            graphics = self.images_graphics_wdg

        if (data_dir.find('..') > -1):
            # create a directory widget to go UP a directory
            thumb_widget = self.make_updir_thumbwidget(self.data_dir)
        else:
            thumb_widget = self.make_thumbWidget(data_dir, fname, info_dct, title=title, sp_db=sp_db, data=data,
                                                 stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
        if (thumb_widget):
            graphics.gridlayout.addItem(thumb_widget, row, column, 1, 1)
            graphics.gridlayout.setColumnSpacing(column, 20)
            graphics.gridlayout.setRowSpacing(row, 15)

            self.image_thumbs.append(thumb_widget)
            return (True)
        else:
            return (False)

    def clear_grid_layout(self, graphics=None, view=None, scene=None):
        """
        clear_grid_layout(): description

        :returns: None
        """
        if (graphics is None):
            graphics = self.images_graphics_wdg

        if (scene is None):
            scene = self.images_scene

        if (view is None):
            view = self.images_view

        if ((graphics.gridlayout.rowCount() == 0) and (graphics.gridlayout.columnCount() == 0)):
            return
        i = 0
        graphics.clear_layout()

        ir = scene.itemsBoundingRect()
        qr = QtCore.QRectF(ir.x(), ir.y(), ir.width(), THUMB_HEIGHT)

        scene.setSceneRect(qr)
        view.setSceneRect(qr)
        graphics.set_layout_size(qr)
        del self.image_thumbs
        self.image_thumbs = []
        graphics.set_cur_row(0)
        graphics.set_cur_column(0)
        view.viewport().update()

    def add_to_view(self, fname, sp_db, data, image_num=None, ev_idx=0, ev_pnt=0, pol_idx=0, pol_pnt=0, row=None,
                    col=None, update_scene=False, graphics=None, view=None, scene=None):
        """
        load_stack_into_view(): description

        :param fname: fname description
        :type fname: fname type

        :returns: None

        """
        # print 'add_to_view: row=%d col=%d' % (row, col)
        if (graphics is None):
            graphics = self.images_graphics_wdg

        if (scene is None):
            scene = self.images_scene

        if (view is None):
            view = self.images_view

        if (fname.find('..') > -1):
            # is an updir widget
            status = self.add_thumb_widget(fname, fname, {}, row, col, title='..', sp_db=sp_db, data=data,
                                           graphics=graphics)
            return (status)

        if (data is None):
            return (False)

        if (data.ndim == 3):
            data = data[0]
        elif (data.ndim == 2):
            # its a single image
            data = data
        elif (data.ndim == 1):
            # its a spectra
            data = data
        else:
            # its unknown
            return (None)

        # rows, cols = data.shape

        if ((sp_db is not None) and (data is not None)):
            # if(dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.GENERIC_SCAN, scan_types.SAMPLE_POINT_SPECTRUM]):
            # if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.GENERIC_SCAN]):
            #     fstr = os.path.join(self.data_dir, fname)
            #     info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=ev_idx, ev_pnt=ev_pnt, pol_idx=pol_idx, pol_pnt=0)
            #     info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
            #     lfn = len(fname)
            #     title = fname[0:lfn-5]
            # else:
            #     #its not a supported scan type
            #     return

            fstr = os.path.join(self.data_dir, fname)
            info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=ev_idx, ev_pnt=ev_pnt,
                                                          pol_idx=pol_idx, pol_pnt=0)
            info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
            lfn = len(fname)
            title = fname[0:lfn - 5]

        if ((row is None) and (col is None)):
            row, col = self.get_next_row_and_col(graphics)

        num_rows = graphics.gridlayout.rowCount()
        column = 0
        if (image_num is None):
            ttl = title
        else:
            ttl = title + '_%d' % image_num

        status = self.add_thumb_widget(self.data_dir, fname, info_dct, row, col, title=ttl, sp_db=sp_db, data=data,
                                       graphics=graphics)
        # print('add_to_view: add_thumb_widget [%s] at rowcol (%d, %d)' % (ttl, row, col))

        if (update_scene and status):
            # self.update_scenes(graphics, scene, view)
            self.update_scenes()

        return (status)

    def update_scenes(self):
        '''

        :return:
        '''
        self.do_update_scene(self.images_graphics_wdg, self.images_scene, self.images_view)
        self.do_update_scene(self.spectra_graphics_wdg, self.spectra_scene, self.spectra_view)

    def do_update_scene(self, grphcs_wdg, scene, view):
        '''
        overloaded function
        :param grphcs_wdg:
        :param scene:
        :param view:
        :return:
        '''
        num_rows = grphcs_wdg.gridlayout.rowCount() + 1  # make sure there is always enough room at the bottom
        # qr = QtCore.QRectF(0.0, 0.0, 290.0, num_rows * 170.0)
        qr = QtCore.QRectF(0.0, 0.0, SCENE_WIDTH, num_rows * THUMB_HEIGHT)
        # print 'num_rows = %d, ht = %d' % (num_rows, num_rows * 170.0)
        grphcs_wdg.set_layout_size(qr)
        scene.setSceneRect(qr)
        view.setSceneRect(qr)
        yPos = view.verticalScrollBar()
        if (num_rows > 3):
            yPos.setValue(yPos.maximum())
        else:
            yPos.setValue(yPos.minimum())

    def load_stack_into_view(self, fname):
        """
        load_stack_into_view(): description

        :param fname: fname description
        :type fname: fname type

        :returns: None
        """
        fstr = os.path.join(self.data_dir, fname)
        sp_db, data = self.get_sp_db_and_data(fstr, stack_dir=True)
        self.clear_grid_layout(self.images_graphics_wdg, self.images_view, self.images_scene)
        self.clear_grid_layout(self.spectra_graphics_wdg, self.spectra_view, self.spectra_scene)

        # num_images, rows, cols = data.shape
        num_images, rows, cols = data.shape
        num_images += 1  # because we are adding an updir thumbnailwidget

        ROWS = math.ceil(num_images / MAX_THUMB_COLUMNS)
        # rowcol = itertools.product(range(ROWS),range(MAX_THUMB_COLUMNS))
        rowcol = list(itertools.product(range(ROWS + 1), range(MAX_THUMB_COLUMNS)))
        rowcol_iter = 0
        ev_idx = 0
        i = 0
        row, column = rowcol[rowcol_iter]
        status = self.add_to_view(os.path.join(self.data_dir, '..'), None, None, image_num=0, ev_idx=ev_idx, ev_pnt=0.0,
                                  pol_idx=0, pol_pnt=0, row=row, col=column, update_scene=False)
        rowcol_iter += 1
        for ev_roi in sp_db[EV_ROIS]:
            # ev_idx = 0
            enpnts = int(ev_roi[NPOINTS])
            polnpnts = len(ev_roi[POL_ROIS])
            ev_pol_idxs = list(itertools.product(range(enpnts), range(polnpnts)))
            ev_pol_iter = 0

            # for ev_pol_idxs in itertools.product(range(enpnts), range(polnpnts) ):
            for x in range(enpnts):
                # for row, column in itertools.product(range(ROWS),range(MAX_THUMB_COLUMNS)):
                # print 'load_stack_into_view: %d of %d' % (x, enpnts)
                for p in range(polnpnts):
                    row, column = rowcol[rowcol_iter]
                    ev_pnt, pol_idx = ev_pol_idxs[ev_pol_iter]
                    # print('load_stack_into_view: calling add_to_view for next_iter=%d, i=%d at rowcol (%d, %d)' % (rowcol_iter, i, row, column))
                    ev_pol_iter += 1
                    rowcol_iter += 1
                    status = self.add_to_view(fname, sp_db, data[i], image_num=i, ev_idx=ev_idx, ev_pnt=ev_pnt,
                                              pol_idx=pol_idx, pol_pnt=0, row=row, col=column, update_scene=False)

                    if (not status):
                        continue
                    i += 1
                # pol_idx += 1
            ev_idx += 1
            self.spectra_graphics_wdg.set_cur_row(row + 1)
            self.spectra_graphics_wdg.set_cur_column(column + 1)

        self.update_scenes()

    def load_entries_into_view(self, fname):
        """
        load_stack_into_view(): description

        :param fname: fname description
        :type fname: fname type

        :returns: None
        """
        fstr = os.path.join(self.data_dir, fname)
        sp_db_lst, data_lst = self.get_sp_db_and_data(fstr, stack_dir=True)
        self.clear_grid_layout(self.images_graphics_wdg, self.images_view, self.images_scene)
        self.clear_grid_layout(self.spectra_graphics_wdg, self.spectra_view, self.spectra_scene)

        # num_images, rows, cols = data.shape
        num_ev, rows, cols = data_lst[0].shape
        num_images = len(sp_db_lst) * num_ev
        num_images += 1  # because we are adding an updir thumbnailwidget

        ROWS = math.ceil(num_images / MAX_THUMB_COLUMNS)
        # rowcol = itertools.product(range(ROWS),range(MAX_THUMB_COLUMNS))
        rowcol = list(itertools.product(range(ROWS + 1), range(MAX_THUMB_COLUMNS)))
        rowcol_iter = 0
        ev_idx = 0
        i = 0
        row, column = rowcol[rowcol_iter]
        status = self.add_to_view(os.path.join(self.data_dir, '..'), None, None, image_num=0, ev_idx=ev_idx, ev_pnt=0.0,
                                  pol_idx=0, pol_pnt=0, row=row, col=column, update_scene=False)
        rowcol_iter += 1
        sp_id_idx = 0
        for sp_db in sp_db_lst:
            for ev_roi in sp_db[EV_ROIS]:
                # ev_idx = 0
                enpnts = int(ev_roi[NPOINTS])
                polnpnts = len(ev_roi[POL_ROIS])
                ev_pol_idxs = list(itertools.product(range(enpnts), range(polnpnts)))
                ev_pol_iter = 0

                # for ev_pol_idxs in itertools.product(range(enpnts), range(polnpnts) ):
                for x in range(enpnts):
                    # for row, column in itertools.product(range(ROWS),range(MAX_THUMB_COLUMNS)):
                    # print 'load_stack_into_view: %d of %d' % (x, enpnts)
                    for p in range(polnpnts):
                        row, column = rowcol[rowcol_iter]
                        ev_pnt, pol_idx = ev_pol_idxs[ev_pol_iter]
                        # print('load_stack_into_view: calling add_to_view for next_iter=%d, i=%d at rowcol (%d, %d)' % (rowcol_iter, i, row, column))
                        ev_pol_iter += 1
                        rowcol_iter += 1
                        if (i < num_ev):
                            status = self.add_to_view(fname, sp_db, data_lst[sp_id_idx][i], image_num=i, ev_idx=ev_idx,
                                                      ev_pnt=ev_pnt,
                                                      pol_idx=pol_idx, pol_pnt=0, row=row, col=column,
                                                      update_scene=False)

                        if (not status):
                            continue
                        i += 1
                    # pol_idx += 1
                ev_idx += 1
                self.spectra_graphics_wdg.set_cur_row(row + 1)
                self.spectra_graphics_wdg.set_cur_column(column + 1)
            sp_id_idx += 1
        self.update_scenes()

    # def create_directory_thumbs(self, dirs, progress_callback=None):
    #     dirs = sorted(dirs)
    #     reversed(dirs)
    #     dirs_thwdg_lst = []
    #     iidx = 0
    #     for i in range(len(dirs)):
    #         iidx += 1
    #         if (i >= len(dirs)):
    #             # if it is less than 1 full row
    #             break
    #         fstr = os.path.join(self.data_dir, dirs[i])
    #         th_wdg = self.make_dir_thumbWidget(self.data_dir, dirs[i], info_dct=None, sp_db=None, data=None)
    #
    #         if (not th_wdg):
    #             continue
    #         dirs_thwdg_lst.append(th_wdg)
    #         if (progress_callback is not None):
    #             progress_callback.emit((float(iidx) / float(len(dirs))) * 100.0)
    #
    #         i += 1
    #     return (dirs_thwdg_lst)

    def make_updir_thumbwidget(self, data_dir):
        info_dct = {'info_str': 'up a directory', 'info_jstr': 'info_jstr'}
        th_wdg = self.make_thumbWidget(data_dir, '..', info_dct, sp_db={}, data=None, stype=None, is_folder=True)
        return (th_wdg)

    @cached(cache)
    def reload_view(self, datadir, is_stack_dir=False, progress_callback=None):
        """
        reload_view(): walk the self.data_dir and try to load every .hdf5 file, display only the ones that are valid
        skip the ones that are not

        :param is_stack_dir=False: is_stack_dir=False description
        :type is_stack_dir=False: is_stack_dir=False type

        :returns: None
        self.images_graphics_wdg.set_layout_size(qr)
        self.images_scene.setSceneRect(qr)
        self.images_view
        """
        self.data_dir = datadir
        self.clear_grid_layout(self.images_graphics_wdg, self.images_view, self.images_scene)
        self.clear_grid_layout(self.spectra_graphics_wdg, self.spectra_view, self.spectra_scene)
        row = 0
        column = 0
        if (self.data_dir is None):
            return

        if (not os.path.exists(self.data_dir)):
            _logger.error('Data directory does not exist: [%s]' % self.data_dir)
            return

        stack_dirs, data_fnames = dirlist_withdirs(self.data_dir, self.data_file_extension)
        # data_fnames = dirlist(self.data_dir, self.data_file_extension, remove_suffix=False)
        # only look at files that have an image and data file, then turn to list, then sort ascending
        # thumb_fnames = sorted( list(set(image_fnames) & set(data_fnames)) )
        if (len(stack_dirs) > 0):
            data_fnames = data_fnames + stack_dirs

        thumb_fnames = sorted(data_fnames)
        # dirs = sorted(stack_dirs)
        image_thumb_lst = []
        spectra_thumb_lst = []
        iidx = 0

        # create a directory widget to go UP a directory
        th_wdg = self.make_updir_thumbwidget(self.data_dir)
        image_thumb_lst.append(th_wdg)

        if (len(thumb_fnames) < 1):
            return
        elif (len(thumb_fnames) == 1):
            # there is only a single file in directory
            fstr = os.path.join(self.data_dir, thumb_fnames[0])
            #print(fstr)
            sp_db, data = self.get_sp_db_and_data(fstr)
            is_spec = False
            if ((sp_db is not None) and (data is not None)):
                # if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in [scan_types.GENERIC_SCAN,scan_types.SAMPLE_POINT_SPECTRUM]):
                if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in spectra_type_scans):
                    info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=0, pol_idx=0)
                    info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
                    th_wdg = self.make_thumbWidget(self.data_dir, thumb_fnames[0], info_dct, sp_db=sp_db, data=data,
                                                   stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))
                else:
                    is_spec = True
                    fstr = os.path.join(self.data_dir, thumb_fnames[0])
                    info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=0, pol_idx=0)
                    info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
                    th_wdg = self.make_thumbWidget(self.data_dir, thumb_fnames[0], info_dct, sp_db=sp_db, data=data,
                                                   stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))

                if (not th_wdg):
                    # file must have had a problem with it
                    yPos = self.images_view.verticalScrollBar()
                    yPos.setValue(yPos.minimum())
                    return

                if (is_spec):
                    spectra_thumb_lst.append(th_wdg)
                else:
                    image_thumb_lst.append(th_wdg)

        else:
            # there are multiple fnames and or directories
            for i in range(len(thumb_fnames)):
                iidx += 1
                if (i >= len(thumb_fnames)):
                    # if it is less than 1 full row
                    break
                is_folder = False
                fstr = os.path.join(self.data_dir, thumb_fnames[i])
                #print(fstr)
                if (os.path.isdir(fstr)):
                    # this is likely a stack directory
                    data_dir, fprefix, fsuffix = get_file_path_as_parts(fstr)
                    _fname = os.path.join(fstr, fprefix + self.data_file_extension)
                    #dont say this is a stack dir because we are not creating all of the thumbnails for the stack here
                    #that is done elsewhere, so just return the first sp_db and data
                    sp_db, data = self.get_sp_db_and_data(_fname, stack_dir=False)

                    if ((sp_db is None) or (data is None)):
                        _logger.error('reload_view: problem loading [%s]' % fstr)
                        continue
                    #there may have been multi entries in the file, only support 1 for now
                    if(type(sp_db) is list):
                        sp_db = sp_db[0]
                        data = data[0]
                    info_str, info_jstr = self.build_image_params(_fname, sp_db, data, ev_idx=0, pol_idx=0,
                                                                  is_folder=True)
                    info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
                    th_wdg = self.make_thumbWidget(self.data_dir, thumb_fnames[i], info_dct, sp_db={}, data=None,
                                                   stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE), is_folder=True)
                    if ((not th_wdg) or (not info_str)):
                        continue
                    image_thumb_lst.append(th_wdg)

                    if (progress_callback is not None):
                        progress_callback.emit((float(iidx) / float(len(thumb_fnames))) * 100.0)
                else:
                    # its files
                    sp_db, data = self.get_sp_db_and_data(fstr)
                    if ((sp_db is None) or (data is None)):
                        _logger.error('reload_view: problem loading [%s]' % fstr)
                        continue
                    if (type(sp_db) is list):
                        # _scan_type = dct_get(sp_db[0], SPDB_SCAN_PLUGIN_TYPE)
                        sp_db = sp_db[0]
                        data = data[0]
                    # else:
                    #     _scan_type = dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE)

                    # if (_scan_type not in spectra_type_scans):
                    if (dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE) not in spectra_type_scans):
                        fstr = os.path.join(self.data_dir, thumb_fnames[i])
                        info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=0, pol_idx=0)
                        info_dct = {'info_str': info_str, 'info_jstr': info_jstr}
                        th_wdg = self.make_thumbWidget(self.data_dir, thumb_fnames[i], info_dct, sp_db=sp_db, data=data,
                                                       stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE))

                        if (not th_wdg):
                            continue
                        image_thumb_lst.append(th_wdg)

                        if (progress_callback is not None):
                            progress_callback.emit((float(iidx) / float(len(thumb_fnames))) * 100.0)
                    else:
                        fstr = os.path.join(self.data_dir, thumb_fnames[i])
                        info_str, info_jstr = self.build_image_params(fstr, sp_db, data, ev_idx=0, pol_idx=0)
                        info_dct = {'info_str': info_str, 'info_jstr': info_jstr}

                        th_wdg = self.make_thumbWidget(self.data_dir, thumb_fnames[i], info_dct, sp_db=sp_db, data=data,
                                                       stype=dct_get(sp_db, SPDB_SCAN_PLUGIN_TYPE), is_folder=is_folder)

                        if (not th_wdg):
                            continue
                        spectra_thumb_lst.append(th_wdg)

                        if (progress_callback is not None):
                            progress_callback.emit((float(iidx) / float(len(thumb_fnames))) * 100.0)

        return (image_thumb_lst, spectra_thumb_lst)

    def load_thumbs(self, image_thumb_lst_spectra_thumb_lst):
        '''

        :param image_thumb_lst_spectra_thumb_lst:
        :return:
        '''
        image_thumb_lst, spectra_thumb_lst = image_thumb_lst_spectra_thumb_lst
        if (image_thumb_lst):
            n_fnames = len(image_thumb_lst)
            if (n_fnames is 0):
                return

            ROWS = int(round(float(n_fnames / float(MAX_THUMB_COLUMNS)))) + 1
            if (ROWS == 0):
                ROWS = 1
            i = 0
            rowcol = list(itertools.product(range(ROWS), range(MAX_THUMB_COLUMNS)))
            next_iter = 0
            for thumb_widget in image_thumb_lst:
                if (thumb_widget):
                    # print 'thumb_widget.launchAction.receivers(thumb_widget.launchAction.triggered) = %d' % thumb_widget.launchAction.receivers(thumb_widget.launchAction.triggered)
                    row, column = rowcol[next_iter]
                    next_iter += 1
                    self.images_graphics_wdg.gridlayout.addItem(thumb_widget, row, column, 1, 1)
                    self.images_graphics_wdg.gridlayout.setColumnSpacing(column, 20)
                    self.images_graphics_wdg.gridlayout.setRowSpacing(row, 15)
                    self.image_thumbs.append(thumb_widget)

            self.images_graphics_wdg.set_cur_row(row)
            self.images_graphics_wdg.set_cur_column(column + 1)

            self.do_update_scene(self.images_graphics_wdg, self.images_scene, self.images_view)

        # now spectra
        if (spectra_thumb_lst):
            n_fnames = len(spectra_thumb_lst)
            if (n_fnames is 0):
                return

            ROWS = int(round(float(n_fnames / float(MAX_THUMB_COLUMNS)))) + 1
            if (ROWS == 0):
                ROWS = 1
            i = 0
            rowcol = list(itertools.product(range(ROWS), range(MAX_THUMB_COLUMNS)))
            next_iter = 0
            for thumb_widget in spectra_thumb_lst:
                if (thumb_widget):
                    # print 'thumb_widget.launchAction.receivers(thumb_widget.launchAction.triggered) = %d' % thumb_widget.launchAction.receivers(thumb_widget.launchAction.triggered)
                    row, column = rowcol[next_iter]
                    next_iter += 1
                    self.spectra_graphics_wdg.gridlayout.addItem(thumb_widget, row, column, 1, 1)
                    self.spectra_graphics_wdg.gridlayout.setColumnSpacing(column, 20)
                    self.spectra_graphics_wdg.gridlayout.setRowSpacing(row, 15)
                    self.image_thumbs.append(thumb_widget)

            self.spectra_graphics_wdg.set_cur_row(row)
            self.spectra_graphics_wdg.set_cur_column(column + 1)

            self.do_update_scene(self.spectra_graphics_wdg, self.spectra_scene, self.spectra_view)

    def split_data_dir(self, data_dir):
        """
        split_data_dir(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :returns: None
        """
        if (data_dir is None):
            return
        data_dir = data_dir.replace('\\', '/')
        sep = '/'
        if (data_dir.find('/') > -1):
            sep = '/'
        elif (data_dir.find('\\') > -1):
            sep = '\\'
        else:
            _logger.error('Unsupported directory string [%s]' % data_dir)

        d_lst = data_dir.split(sep)
        return (d_lst)

    def set_data_dir(self, data_dir, is_stack_dir=False, hide=False):
        """
        set_data_dir(): description

        :param data_dir: data_dir description
        :type data_dir: data_dir type

        :param is_stack_dir=False: is_stack_dir=False description
        :type is_stack_dir=False: is_stack_dir=False type

        :returns: None
        """
        # print 'set_data_dir: called'
        if (len(data_dir) > 0):
            self.data_dir = data_dir
            d = self.split_data_dir(data_dir)
            num_dirs = len(d) - 1
            fstr = os.path.join(d[num_dirs - 1], d[num_dirs])
            self.dir_lbl.setText(fstr)
            self.fsys_mon.set_data_dir(data_dir)
            if (not is_stack_dir):
                # self.reload_view(is_stack_dir)
                self.load_image_items(is_stack_dir, hide=hide)

    def do_select(self, thumb):
        """
        do_select(): description

        :param thumb: thumb description
        :type thumb: thumb type

        :returns: None
        """
        for t in self.image_thumbs:
            if (id(thumb) != id(t)):
                t.is_selected = False
            else:
                t.is_selected = True
        self.update_view()

    def update_view(self):
        """
        update_view(): description

        :returns: None
        """
        self.images_view.update()
        # self.images_scene.update(rect=QtCore.QRectF(0,0,1500,1500))
        rect = self.images_scene.sceneRect()
        self.images_scene.update(rect=QtCore.QRectF(rect.left(), rect.top(), rect.width(), rect.height()))

    def print_thumbnail(self, dct):
        self.ptnw.print_file(dct)

    def preview_thumbnail(self, dct):
        self.ptnw.preview_file(dct)

    def launch_viewer(self, dct):
        """
        launch_viewer(): description

        :param dct: dct description
        :type dct: dct type

        :returns: None
        """
        if (dct['scan_type'] in spectra_type_scans):
            self.launch_spectra_viewer(dct)
        else:
            self.launch_image_viewer(dct)

    def launch_spectra_viewer(self, dct):
        fname = dct['path']
        xdata = dct['xdata']
        ydatas = dct['ydatas']
        sp_db = dct['sp_db']
        title = dct['title']
        num_specs = len(ydatas)
        num_spec_pnts = len(xdata)
        data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
        print('sending to Spectra Viewer')
        if (self.spec_win is None):
            self.spec_win = make_spectra_viewer_window()
            self.spec_win.setWindowTitle('Spectra Viewer')
            # win.set_data_dir(r'S:\STXM-data\Cryo-STXM\2017\guest\0106')
            qssheet = get_style('dark')
            self.spec_win.setStyleSheet(qssheet)
            self.spec_win.add_legend("TL")
            self.spec_win.closeEvent = self.on_spec_viewer_closeEvent
            reset_color_idx()
            for i in range(num_specs):
                clr = get_next_color(use_dflt=False)
                style = get_basic_line_style(clr)
                self.spec_win.create_curve('point_spectra_%d' % i, curve_style=style)
                self.spec_win.setXYData('point_spectra_%d' % i, xdata, ydatas[i])

            self.spec_win.show()
        else:
            self.spec_win.clear_plot()
            for i in range(num_specs):
                clr = get_next_color(use_dflt=False)
                style = get_basic_line_style(clr)
                self.spec_win.create_curve('point_spectra_%d' % i, curve_style=style)
                self.spec_win.setXYData('point_spectra_%d' % i, xdata, ydatas[i])
            # rect = dct_get(sp_db, SPDB_RECT)
            # (x1, y1, x2, y2) = rect
            # self.image_win.set_image_parameters(self.image_win.item, x1, y1, x2, y2)
            # self.image_win.on_set_aspect_ratio(True)
            self.spec_win.update()
            self.spec_win.set_autoscale()
            self.spec_win.raise_()

    # def get_image_data(self, dct):
    #     if(dct['scan_type'] is scan_types.SAMPLE_LINE_SPECTRUM):
    #         ev_rois = dct['sp_db']['EV_ROIS']
    #     else:
    #         data = dct['data']
    #     return(data)

    def launch_image_viewer(self, dct):
        import traceback
        # fname, data, title=None):
        try:
            # fname = dct['path']
            # data = dct['data']
            # sp_db = dct['sp_db']
            # title = dct['title']
            # img_idx = 0
            # data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
            # self.image_win.set_data(img_idx, data)
            # rect = dct_get(sp_db, SPDB_RECT)
            # (x1, y1, x2, y2) = rect
            # #self.image_win.set_image_parameters(self.image_win.item, x1, y1, x2, y2)
            # self.image_win.set_image_parameters(img_idx, x1, y1, x2, y2)
            # self.image_win.on_set_aspect_ratio(True, img_idx)
            # self.image_win.update_contrast(img_idx)
            # self.image_win.show()
            # self.image_win.raise_()
            #
            # if (title is not None):
            #     self.image_win.plot.set_title('%s' % title)
            # else:
            #     self.image_win.plot.set_title('%s%s' % (fprefix, fsuffix))

            fname = dct['path']
            data = dct['data']
            sp_db = dct['sp_db']
            title = dct['title']
            if (dct['scan_type'] is scan_types.SAMPLE_LINE_SPECTRUM):
                # sample line spec data may have different ev region resolutions so its special
                wdg_com = make_base_wdg_com()
                dct_put(wdg_com, WDGCOM_CMND, widget_com_cmnd_types.LOAD_SCAN)
                dct_put(wdg_com, SPDB_SPATIAL_ROIS, {sp_db[ID_VAL]: sp_db})
                self.image_win.do_load_linespec_file(fname, wdg_com, data, dropped=False)
                self.image_win.show()
                self.image_win.set_autoscale(fill_plot_window=True)
                self.image_win.raise_()

            else:
                img_idx = 0
                data_dir, fprefix, fsuffix = get_file_path_as_parts(fname)
                self.image_win.set_data(img_idx, data)
                rect = dct_get(sp_db, SPDB_RECT)
                (x1, y1, x2, y2) = rect
                # self.image_win.set_image_parameters(self.image_win.item, x1, y1, x2, y2)
                self.image_win.set_image_parameters(img_idx, x1, y1, x2, y2)
                self.image_win.on_set_aspect_ratio(True, img_idx)
                self.image_win.update_contrast(img_idx)
                self.image_win.show()
                self.image_win.raise_()

            if (title is not None):
                self.image_win.plot.set_title('%s' % title)
            else:
                self.image_win.plot.set_title('%s%s' % (fprefix, fsuffix))

        except:
            traceback.print_exc()

    def on_viewer_closeEvent(self, event):
        # print 'viewer closed'
        # self.image_win = None
        # event.accept() # let the window close
        self.image_win.hide()
        event.ignore()

    def on_spec_viewer_closeEvent(self, event):
        self.spec_win = None
        event.accept()  # let the window close


if __name__ == "__main__":
    #from cls.data_io.bioxas_im_data_io import BioxasDataIo
    from cls.data_io.stxm_data_io import STXMDataIo

    log_to_qt()
    app = QtWidgets.QApplication(sys.argv)
    # app.setApplicationName("Pyqt Image gallery example")
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\test'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\0314'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\test\single'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\0323'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\0614'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\0812'
    dir = r'S:\STXM-data\Cryo-STXM\2018\guest\1214'
    dir = r'S:\STXM-data\Cryo-STXM\2019\guest\test\0215'
    dir = r'C:\controls\stxm-data\guest\0515'
    dir = r'C:\controls\stxm-data\2020\guest\0110'
    dir = r'C:\controls\stxm-data\2020\guest\0529'
    # dir = r'/home/bergr/git/testing/py27_qt5/py2.7/cls/data/guest'
    # main = ContactSheet(r'S:\STXM-data\Cryo-STXM\2016\guest\test')
    # main = ContactSheet(dir, BioxasDataIo)
    main = ContactSheet(data_dir=dir, data_io=STXMDataIo)

    # main.set_data_dir(dir)
    main.show()
    main.resize(385, 700)

    sys.exit(app.exec_())
