
import sys
import os
import random

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtCore import (QDate, QRectF, Qt, QSize, QRect, QPoint, pyqtSignal, QByteArray, QBuffer, QIODevice)

import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')

#font = {'family' : 'normal', 'size'   : 6}
font = {'family' : 'sans-serif', 'size'   : 6}

matplotlib.rc('font', **font)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from cls.data_io.stxm_data_io import STXMDataIo
from cls.utils.arrays import resize_1d_array

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

THMB_SIZE = 90
AXES_BACKGROUND_COLOR = '#C0C0C0'

SPEC_THMB_WD = 200
SPEC_THMB_HT = 160

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).
    width and height are in inches, dpi is dots per inch
    """

    def __init__(self, parent=None, width=3, height=2, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor=AXES_BACKGROUND_COLOR)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        # We change the fontsize of minor ticks label
        self.axes.tick_params(axis='both', which='major', labelsize=3)
        self.axes.tick_params(axis='both', which='minor', labelsize=3)


        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class OneD_MPLCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def __init__(self, xdata, ydatas, width=5, height=4, dpi=100, axes_bgrnd_color=AXES_BACKGROUND_COLOR):
        super(OneD_MPLCanvas, self).__init__(width=width, height=height, dpi=dpi)
        self.xdata = xdata
        self.ydatas = ydatas
        self.axes_bgrnd_color = axes_bgrnd_color
        self.gen_figure()

    def gen_figure(self):
        for ydata in self.ydatas:
            if(ydata.ndim is 3):
                ydata = ydata[0][0]
            elif(ydata.ndim is 2):
                ydata = ydata[0]

            if(len(self.xdata) != len(ydata)):
                ydata = resize_1d_array(ydata, self.xdata)

            self.axes.set_facecolor(self.axes_bgrnd_color)
            self.axes.plot(self.xdata, ydata, linewidth=1)

    def get_pixmap(self, as_grayscale=False, as_thumbnail=False):
        # can call self.show() here if I want to see the plot from matplotlib
        size = self.figure.canvas.size()
        width, height = size.width(), size.height()
        #in order for the call to : self.figure.canvas.buffer_rgba() to work 'draw() ' must be called FIRST
        self.figure.canvas.draw()
        #im = QtGui.QImage(self.figure.canvas.buffer_rgba(), width, height, QtGui.QImage.Format_ARGB32)
        im = QtGui.QImage(self.figure.canvas.buffer_rgba(), width, height, QtGui.QImage.Format_ARGB32)
        if(not as_thumbnail):
            #im = im.scaled(SPEC_THMB_WD,SPEC_THMB_HT,Qt.KeepAspectRatio, Qt.SmoothTransformation)
            #im = im.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            im = im.scaled(SPEC_THMB_WD + 15, SPEC_THMB_HT , Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if(as_grayscale):
            im = im.convertToFormat(QtGui.QImage.Format_Grayscale8, Qt.AutoColor)
        pmap = QtGui.QPixmap(im)
        return(pmap)

    def get_printable_pmap(self):
        pmap = self.get_pixmap()
        return (pmap)

    def get_thumbnail_pmap(self):
        pmap = self.get_pixmap()
        pmap = pmap.scaled(QSize(THMB_SIZE, THMB_SIZE))
        return (pmap)

    def save_fig_as_jpg(self):
        self.axes.savefig('%s.jpg' % self.fprefix)


if __name__ == '__main__':
    qApp = QtWidgets.QApplication(sys.argv)

    data_dir = r'S:\STXM-data\Cryo-STXM\2017\guest\1220'
    fprefix = 'C171220003'


    #aw = LinePlotThumbnailWidget(data_dir=data_dir, fprefix=fprefix)
    #aw.show()

    data_io = STXMDataIo(data_dir, fprefix)
    entry_dct = data_io.load()
    ekey = list(entry_dct.keys())[0]
    xdata = entry_dct[ekey]['data']['counter0']['energy']['signal']
    ydatas = []
    for ekey in list(entry_dct.keys()):
        ydatas.append(entry_dct[ekey]['data']['counter0']['signal'])

    qt_mpl = OneD_MPLCanvas(xdata, ydatas, width=2, height=1.75, dpi=150)
    pmap = qt_mpl.get_pixmap()

    sys.exit(qApp.exec_())
