#!/usr/bin/env python
# Copyright (c) 2008 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.




#from future_builtins import *

import math
import sys
#import textile
import copy
import time

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from PyQt5.QtCore import (Qt, QDate, QRectF, Qt, QSize, QRect, QPoint, pyqtSignal, QByteArray, QBuffer, QIODevice)
from PyQt5.QtWidgets import (QApplication, QDialog,
        QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
        QVBoxLayout)

from PyQt5.QtGui import (QFont, QFontMetrics, QGradient, QColor, QLinearGradient, QBrush,
        QPainter, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat,
        QTextOption, QTextTableFormat,  QFont, QFontMetrics)

from cls.utils.fileUtils import get_file_path_as_parts
from cls.appWidgets.dialogs import excepthook, errorMessage
from cls.types.stxmTypes import spectra_type_scans
sys.excepthook = excepthook



LEFT_MARGIN = 20
THMB_SIZE = 128
SP_LINE_LENGTH = 5

SPEC_THMB_WD = 200
SPEC_THMB_HT = 160

SINGLE_DATA_BOX = QSize(THMB_SIZE+125, THMB_SIZE+125)
SPEC_SINGLE_DATA_BOX = QSize(SPEC_THMB_WD+125, SPEC_THMB_HT+125)

class PrintSTXMThumbnailWidget(QDialog):
    do_print = pyqtSignal(object)
    do_preview = pyqtSignal(object)
    def __init__(self, parent=None):
        super(PrintSTXMThumbnailWidget, self).__init__(parent)

        self.printer = QPrinter()
        self.printer.setPageSize(QPrinter.Letter)
        self.do_print.connect(self.printViaQPainter)
        self.do_preview.connect(self.preview)
        self.dct = {}
        self.doc = None
        self.prev_pmap = None

    def preview(self):

        # Open preview dialog
        preview = QPrintPreviewDialog(self.printer, self)
        preview.setFixedWidth(700)
        preview.setFixedHeight(600)
        preview.paintRequested.connect(self.printPreview)

        #self.doc = self.getHtmlDoc()
        self.doc = QTextDocument()

        if(self.dct['scan_type_num'] in spectra_type_scans):
            html = self.getQPainterSpecDoc()
        else:
            html = self.getQPainterDoc()
        self.doc.setHtml(html)
        # If a print is requested, open print dialog
        # self.preview.paintRequested.connect(self.printPreview)

        preview.exec_()

    def printPreview(self, printer):
        self.doc.print_(printer)


    def print_file(self, dct):
        self.do_print.emit(dct)

    def preview_file(self, dct):
        self.dct = copy.copy(dct)
        self.do_preview.emit(dct)


    def getHtmlDoc(self, fname=None):
        fname = 'C170928046.hdf5'
        pnts = '150x150'
        scan_type = 'Image Scan'
        ev = '319.998 eV'
        dwell = '1 ms Dwell'
        pol = 'Polariz = -1.0'
        xaxis_nm = 'Sample X (um)'
        yaxis_nm = 'PMT'

        html = ""
        html += ('<p align=left>%s</p>' % fname)
        html += ('<p align=left>%s %s %s</p>' % (pnts, scan_type, ev))
        html += ('<p align=left>%s %s</p>' % (dwell, pol))
        html += ('<p align=left><img src="data.png" width = 50% height = 50%></p>')
        html += ('<p align=right><img src="hist.png" width = 50% height = 50%></p>')
        html += ('<p align=left> %s </p>' % xaxis_nm)
        document = QTextDocument()
        document.setHtml(html)
        return(document)


    def printViaHtml(self):
        document = self.getHtmlDoc()
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            document.print_(self.printer)



    def printViaQPainter(self, dct):
        '''
        this appars to paint right to the printer
        as self.printer is the parent of the QPointer instance
        dct = {'self.info_jstr': '{"polarization": "CircLeft", "angle": 0.0, "center": [-1380.3554196143814, -119.63448659429068], "energy": 714.9979576566445, "step": [0.06733267796298362, 0.0680900257534698], "scan_type": "sample_image_stack Line_Unidir", "range": [10.032569016484558, 10.145413837267], "file": "S:\\\\STXM-data\\\\Cryo-STXM\\\\2017\\\\guest\\\\0817\\\\C170817057.hdf5", "offset": 0.0, "npoints": [150, 150], "dwell": 1.0, "scan_panel_idx": 5}', 'fname': 'S:\\STXM-data\\Cryo-STXM\\2017\\guest\\0817\\C170817057.hdf5'}
        '''

        dialog = QPrintDialog(self.printer, self)
        if not dialog.exec_():
            return
        LeftMargin = LEFT_MARGIN
        sansFont = QFont("Arial", 8)
        sansLineHeight = QFontMetrics(sansFont).height()
        serifFont = QFont("Times", 11)
        serifLineHeight = QFontMetrics(sansFont).height()
        fm = QFontMetrics(serifFont)


        fname = dct['fname']
        pnts = '%dx%d' % (dct['info_dct']['npoints'][0], dct['info_dct']['npoints'][1])
        scan_type = dct['info_dct']['scan_type']
        ev = '%.3f eV' % dct['info_dct']['energy']
        dwell = '%.2f ms Dwell' % dct['info_dct']['dwell']
        pol = 'Polariz = %s' % dct['info_dct']['polarization']
        data_pm = dct['data_pmap']
        xaxis_nm = 'Sample X (um)'
        yaxis_nm = 'counter0'

        #serifLineHeight = fm.height()
        #data_pm = QPixmap("data.png")
        data_pm= data_pm.scaled(QSize(THMB_SIZE, THMB_SIZE))
        hist_pm = QPixmap("hist.png")
        hist_pm = hist_pm.scaled(QSize(THMB_SIZE/5, THMB_SIZE))
        painter = QPainter()
        painter.begin(self.printer)
        painter.setRenderHints(painter.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)

        pageRect = self.printer.pageRect()
        page = 1

        painter.save()
        y = 0
        #x = pageRect.width() - data_pm.width() - LeftMargin
        x = LeftMargin

        painter.setFont(serifFont)

        y += sansLineHeight
        y += sansLineHeight
        painter.drawText(x, y, "   %s" % fname)
        y += serifLineHeight
        painter.setFont(sansFont)
        painter.drawText(x, y, "%s " % (scan_type))
        y += sansLineHeight
        painter.drawText(x, y, "%s      %s " % (pnts, ev))
        y += sansLineHeight
        painter.drawText(x, y, "%s      %s " % (dwell, pol))
        y += sansLineHeight
        painter.drawPixmap(x, y, data_pm)
        #y += data_pm.height() + sansLineHeight

        ##############contrast gradient
        width = 20
        #QRectF(x,y,width, ht) Constructs a rectangle with (x, y) as its top-left corner and the given width and height.
        contrast_bounds = QRectF(x + data_pm.width() + 20, y, width, data_pm.height())
        #g = QLinearGradient(0.0, 0.0, 0.0, data_pm.height())
        g = QLinearGradient()
        g.setColorAt(0, Qt.white)
        g.setColorAt(1, Qt.black)

        g.setStart(contrast_bounds.topLeft())
        g.setFinalStop(contrast_bounds.bottomRight())
        # #top left
        # g.setStart(x + data_pm.width() + 10, data_pm.height())
        # #btm right
        # g.setFinalStop(width, y)
        #painter.fillRect(x + data_pm.width() + 10, y, width, data_pm.height(), QBrush(g))
        painter.fillRect(contrast_bounds, QBrush(g))
        painter.translate(x + data_pm.width(), y + 0.35 * THMB_SIZE)
        # rotate to place name of counter
        painter.rotate(90.0)
        painter.drawText(5, 0, " %s " % (yaxis_nm))
        painter.rotate(-90.0)
        painter.translate(-1.0*(x + data_pm.width()), -1.0*(y + 0.35 * THMB_SIZE))

        #########################en
        #painter.drawPixmap(x + data_pm.width() + 10, y, hist_pm)
        y += data_pm.height() + sansLineHeight
        painter.drawText(x + (0.25 * data_pm.width()), y, "%s" % xaxis_nm)
        y += sansLineHeight
        painter.setFont(serifFont)
        x = LeftMargin

        # page += 1
        # if page <= len(self.statements):
        #     self.printer.newPage()
        painter.end()
        painter.restore()



    def printViaQPainterPreview(self, dct):
        '''
        this appars to paint right to the printer
        as self.printer is the parent of the QPointer instance
        dct = {'self.info_jstr': '{"polarization": "CircLeft", "angle": 0.0, "center": [-1380.3554196143814, -119.63448659429068], "energy": 714.9979576566445, "step": [0.06733267796298362, 0.0680900257534698], "scan_type": "sample_image_stack Line_Unidir", "range": [10.032569016484558, 10.145413837267], "file": "S:\\\\STXM-data\\\\Cryo-STXM\\\\2017\\\\guest\\\\0817\\\\C170817057.hdf5", "offset": 0.0, "npoints": [150, 150], "dwell": 1.0, "scan_panel_idx": 5}', 'fname': 'S:\\STXM-data\\Cryo-STXM\\2017\\guest\\0817\\C170817057.hdf5'}
        '''

        #dialog = QPrintDialog(self.printer, self)
        #if not dialog.exec_():
        #    return
        preview = QPrintPreviewDialog(self.printer, self)


        LeftMargin = LEFT_MARGIN
        sansFont = QFont("Arial", 8)
        sansLineHeight = QFontMetrics(sansFont).height()
        serifFont = QFont("Times", 11)
        serifLineHeight = QFontMetrics(sansFont).height()
        fm = QFontMetrics(serifFont)


        fname = dct['fname']
        pnts = '%dx%d' % (dct['info_dct']['npoints'][0], dct['info_dct']['npoints'][1])
        scan_type = dct['info_dct']['scan_type']
        ev = '%.3f eV' % dct['info_dct']['energy']
        dwell = '%.2f ms Dwell' % dct['info_dct']['dwell']
        pol = 'Polariz = %s' % dct['info_dct']['polarization']
        data_pm = dct['data_pmap']
        xaxis_nm = 'Sample X (um)'
        yaxis_nm = 'counter0'

        #serifLineHeight = fm.height()
        #data_pm = QPixmap("data.png")
        data_pm= data_pm.scaled(QSize(THMB_SIZE, THMB_SIZE))
        hist_pm = QPixmap("hist.png")
        hist_pm = hist_pm.scaled(QSize(THMB_SIZE/5, THMB_SIZE))
        prev_pmap = QPixmap()
        #painter = QPainter(preview)
        painter = QPainter()
        painter.begin(prev_pmap)
        painter.setRenderHints(painter.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)

        pageRect = self.printer.pageRect()
        page = 1

        painter.save()
        y = 0
        #x = pageRect.width() - data_pm.width() - LeftMargin
        x = LeftMargin

        painter.setFont(serifFont)

        y += sansLineHeight
        y += sansLineHeight
        painter.drawText(x, y, "   %s" % fname)
        y += serifLineHeight
        painter.setFont(sansFont)
        painter.drawText(x, y, "%s " % (scan_type))
        y += sansLineHeight
        painter.drawText(x, y, "%s      %s " % (pnts, ev))
        y += sansLineHeight
        painter.drawText(x, y, "%s      %s " % (dwell, pol))
        y += sansLineHeight
        painter.drawPixmap(x, y, data_pm)
        #y += data_pm.height() + sansLineHeight

        ##############contrast gradient
        width = 20
        #QRectF(x,y,width, ht) Constructs a rectangle with (x, y) as its top-left corner and the given width and height.
        contrast_bounds = QRectF(x + data_pm.width() + 20, y, width, data_pm.height())
        #g = QLinearGradient(0.0, 0.0, 0.0, data_pm.height())
        g = QLinearGradient()
        g.setColorAt(0, Qt.white)
        g.setColorAt(1, Qt.black)

        g.setStart(contrast_bounds.topLeft())
        g.setFinalStop(contrast_bounds.bottomRight())
        # #top left
        # g.setStart(x + data_pm.width() + 10, data_pm.height())
        # #btm right
        # g.setFinalStop(width, y)
        #painter.fillRect(x + data_pm.width() + 10, y, width, data_pm.height(), QBrush(g))
        painter.fillRect(contrast_bounds, QBrush(g))
        painter.translate(x + data_pm.width(), y + 0.35 * THMB_SIZE)
        # rotate to place name of counter
        painter.rotate(90.0)
        painter.drawText(5, 0, " %s " % (yaxis_nm))
        painter.rotate(-90.0)
        painter.translate(-1.0*(x + data_pm.width()), -1.0*(y + 0.35 * THMB_SIZE))

        #########################en
        #painter.drawPixmap(x + data_pm.width() + 10, y, hist_pm)
        y += data_pm.height() + sansLineHeight
        painter.drawText(x + (0.25 * data_pm.width()), y, "%s" % xaxis_nm)
        y += sansLineHeight
        painter.setFont(serifFont)
        x = LeftMargin

        # page += 1
        # if page <= len(self.statements):
        #     self.printer.newPage()
        painter.end()
        painter.restore()

        html = ""
        document = QTextDocument()
        document.setHtml(html)
        cursor = QTextCursor(document)
        img = prev_pmap.toImage()
        cursor.insertImage(img)
        document.print_(preview)
        preview.exec_()

    def getQPainterDoc(self):
        '''
        this appars to paint right to the printer
        as self.printer is the parent of the QPointer instance
        dct = {'self.info_jstr': '{"polarization": "CircLeft", "angle": 0.0, "center": [-1380.3554196143814, -119.63448659429068], "energy": 714.9979576566445, "step": [0.06733267796298362, 0.0680900257534698], "scan_type": "sample_image_stack Line_Unidir", "range": [10.032569016484558, 10.145413837267], "file": "S:\\\\STXM-data\\\\Cryo-STXM\\\\2017\\\\guest\\\\0817\\\\C170817057.hdf5", "offset": 0.0, "npoints": [150, 150], "dwell": 1.0, "scan_panel_idx": 5}', 'fname': 'S:\\STXM-data\\Cryo-STXM\\2017\\guest\\0817\\C170817057.hdf5'}
        '''

        #dialog = QPrintDialog(self.printer, self)
        #if not dialog.exec_():
        #    return
        self.prev_pmap = None

        LeftMargin = LEFT_MARGIN
        sansFont = QFont("Arial", 8)
        sansLineHeight = QFontMetrics(sansFont).height()
        serifFont = QFont("Times", 11)
        serifLineHeight = QFontMetrics(sansFont).height()

        arialFontSmall = QFont("Arial", 7)
        arialFontSmallHeight = QFontMetrics(arialFontSmall).height()

        fm = QFontMetrics(serifFont)

        dct = self.dct
        fname = dct['fname']
        pnts = '%dx%d' % (dct['info_dct']['npoints'][0], dct['info_dct']['npoints'][1])
        scan_type = dct['scan_type']
        scan_sub_type = dct['scan_sub_type']
        ev = '%.3f eV' % dct['info_dct']['energy']
        dwell = '%.2f ms Dwell' % dct['info_dct']['dwell']
        pol = 'Polariz = %s' % dct['info_dct']['polarization']
        data_pm = dct['data_pmap']
        xaxis_nm = '%s' % dct['xpositioner']
        yaxis_nm = 'counter0'
        units_nm = 'um''s'

        #serifLineHeight = fm.height()
        #data_pm = QPixmap("data.png")
        #data_pm= data_pm.scaled(QSize(THMB_SIZE, THMB_SIZE))
        hist_pm = QPixmap("hist.png")
        hist_pm = hist_pm.scaled(QSize(THMB_SIZE/5, THMB_SIZE))

        prev_pmap = QPixmap(SINGLE_DATA_BOX)
        self.prev_pmap = prev_pmap
        prev_pmap.fill(QColor(0,0,0,0))

        painter = QPainter()
        painter.begin(self.prev_pmap)
        #
        painter.setRenderHints(painter.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)
        #
        pageRect = self.printer.pageRect()
        page = 1

        painter.save()

        painter.fillRect(QRect(QPoint(0,0), SINGLE_DATA_BOX), Qt.white)

        y = 0
        #x = pageRect.width() - data_pm.width() - LeftMargin
        x = LeftMargin

        painter.setFont(serifFont)

        y += sansLineHeight
        y += sansLineHeight
        painter.drawText(x + 25, y, "   %s" % fname)
        y += serifLineHeight
        painter.setFont(sansFont)
        painter.drawText(x + 25, y, "%s      %s " % (pnts, scan_type))
        y += sansLineHeight
        painter.drawText(x + 25, y, "%s          %s " % (scan_sub_type, ev))
        y += sansLineHeight
        painter.drawText(x + 25, y, "%s      %s " % (dwell, pol))
        y += sansLineHeight

        ############################################
        # Y scale on data image
        _x = x
        painter.drawText(x, y+5, "%3d" % (dct['yrange']))
        painter.drawLine(x + 17, y + 1, x + 15 + SP_LINE_LENGTH, y + 1)


        painter.drawText(x , y  + (THMB_SIZE/2), "%3d" % (dct['yrange']/2))
        painter.drawLine(x + 17, y + (THMB_SIZE / 2) - 2, x + 15 + SP_LINE_LENGTH, y + (THMB_SIZE / 2) - 2)


        painter.drawText(x , y + (THMB_SIZE), "%3d" % 0)
        painter.drawLine(x + 17, y + (THMB_SIZE) - 2, x + 15 + SP_LINE_LENGTH, y + (THMB_SIZE) - 2)

        _x += 25
        ###################################

        grey_pm = QPixmap(THMB_SIZE, THMB_SIZE)
        grey_pm.fill(QColor(232,232,232))
        painter.drawPixmap(_x, y, grey_pm)

        # # painter.drawPixmap(btm_rectF, self.pic, QtCore.QRectF(grey_pm.rect()))
        # pic_rectF = QRectF(data_pm.rect())
        cb = grey_pm.rect().center()
        # # now see if the aspect ratio is equal or different, if so adjust image to sit in the center with a black border
        if (data_pm.width() < data_pm.height()):
            r = float(data_pm.width()) / float(data_pm.height())
            data_pm = data_pm.scaled(QSize(r * THMB_SIZE, THMB_SIZE))
            newx = _x + float((THMB_SIZE / 2.0)) - float(data_pm.width()) / 2.0
            painter.drawPixmap(newx, y, data_pm)

        elif (data_pm.width() > data_pm.height()):
            r = float(data_pm.height()) / float(data_pm.width())
            data_pm = data_pm.scaled(QSize(THMB_SIZE, r*THMB_SIZE))
            newy = y + float((THMB_SIZE / 2.0)) - float(data_pm.height()) / 2.0
            painter.drawPixmap(_x, newy, data_pm)
        else:
            data_pm = data_pm.scaled(QSize(THMB_SIZE, THMB_SIZE))
            painter.drawPixmap(_x, y, data_pm)


        #####################################

        #painter.drawPixmap(_x, y, data_pm)
        #y += data_pm.height() + sansLineHeight

        ##############contrast gradient
        width = 20
        #QRectF(x,y,width, ht) Constructs a rectangle with (x, y) as its top-left corner and the given width and height.
        contrast_bounds = QRectF(_x + grey_pm.width() + 20, y, width, grey_pm.height())
        #g = QLinearGradient(0.0, 0.0, 0.0, data_pm.height())
        g = QLinearGradient()
        g.setColorAt(0, Qt.white)
        g.setColorAt(1, Qt.black)

        g.setStart(contrast_bounds.topLeft())
        g.setFinalStop(contrast_bounds.bottomRight())
        painter.fillRect(contrast_bounds, QBrush(g))


        painter.drawLine(contrast_bounds.right(), y + 1, contrast_bounds.right() + SP_LINE_LENGTH, y+1)
        painter.drawText(contrast_bounds.right() + 7, y + 5, "%3d" % (dct['data_max']))

        painter.drawLine(contrast_bounds.right(),       y + (THMB_SIZE) , contrast_bounds.right() + SP_LINE_LENGTH, y + (THMB_SIZE))
        painter.drawText(contrast_bounds.right() + 7,  y + (THMB_SIZE), "%3d" % (dct['data_min']))
        # end of contrast


        ###########################################
        # rotate to place name of counter
        painter.translate(_x + grey_pm.width(), y + 0.25 * THMB_SIZE)
        painter.rotate(90.0)
        painter.drawText(0, -5, " %s " % (yaxis_nm))
        #UNDO TRANSFORM
        painter.rotate(-90.0)
        painter.translate(-1.0*(_x + grey_pm.width()), -1.0*(y + 0.25 * THMB_SIZE))

        #y += grey_pm.height() + sansLineHeight
        # y += data_pm.height() + sansLineHeight

        ###########################
        #vertical bars across data image bottom
        y += grey_pm.height()

        painter.drawLine(x+26, y + 5, x + 26, y+ + 5 + SP_LINE_LENGTH)
        painter.drawText(x+23, y+23, "0")

        #painter.setFont(arialFontSmall)
        #painter.drawText(x + 10 + (THMB_SIZE / 2), y + 5 + SP_LINE_LENGTH, "%s" % xaxis_nm)

        painter.drawLine(x + 25 + (THMB_SIZE / 2), y + 5, x + 25 + (THMB_SIZE / 2), y + 5 + SP_LINE_LENGTH)
        painter.drawText(x + 16 + (THMB_SIZE / 2), y + 23, "%3d" % (dct['xrange'] / 2))

        painter.drawLine(x + 25 + (THMB_SIZE ), y + 5, x + 25 + (THMB_SIZE ), y +  + 5 + SP_LINE_LENGTH)
        painter.drawText(x + 20 + (THMB_SIZE ), y + 23, "%2d %s" % (dct['xrange'], units_nm))

        y += 27
        #########################en
        #painter.drawPixmap(x + data_pm.width() + 10, y, hist_pm)
        y += sansLineHeight
        #turn to a gray brush
        #painter.setBrush(QBrush(QColor(200, 200, 200, 50)))
        #change font
        painter.setFont(arialFontSmall)
        painter.drawText(x + 36 , y - 25, "%s" % xaxis_nm)
        #y += sansLineHeight
        painter.setFont(serifFont)
        painter.end()
        painter.restore()

        html = self.create_html_for_pmap(prev_pmap)
        document = QTextDocument()
        document.setHtml(html)
        return(html)




    def getQPainterSpecDoc(self):
        '''
        this appars to paint right to the printer
        as self.printer is the parent of the QPointer instance
        dct = {'self.info_jstr': '{"polarization": "CircLeft", "angle": 0.0, "center": [-1380.3554196143814, -119.63448659429068], "energy": 714.9979576566445, "step": [0.06733267796298362, 0.0680900257534698], "scan_type": "sample_image_stack Line_Unidir", "range": [10.032569016484558, 10.145413837267], "file": "S:\\\\STXM-data\\\\Cryo-STXM\\\\2017\\\\guest\\\\0817\\\\C170817057.hdf5", "offset": 0.0, "npoints": [150, 150], "dwell": 1.0, "scan_panel_idx": 5}', 'fname': 'S:\\STXM-data\\Cryo-STXM\\2017\\guest\\0817\\C170817057.hdf5'}
        '''

        #dialog = QPrintDialog(self.printer, self)
        #if not dialog.exec_():
        #    return



        self.prev_pmap = None

        LeftMargin = LEFT_MARGIN
        sansFont = QFont("Arial", 8)
        sansLineHeight = QFontMetrics(sansFont).height()
        serifFont = QFont("Times", 11)
        serifLineHeight = QFontMetrics(sansFont).height()

        arialFontSmall = QFont("Arial", 7)
        arialFontSmallHeight = QFontMetrics(arialFontSmall).height()

        fm = QFontMetrics(serifFont)

        dct = self.dct
        fname = dct['fname']
        pnts = '%dx%d' % (dct['info_dct']['npoints'][0], dct['info_dct']['npoints'][1])
        scan_type = dct['scan_type']
        scan_sub_type = dct['scan_sub_type']
        ev = '%.3f eV' % dct['info_dct']['energy']
        dwell = '%.2f ms Dwell' % dct['info_dct']['dwell']
        pol = 'Polariz = %s' % dct['info_dct']['polarization']
        data_pm = dct['data_pmap']
        xaxis_nm = '%s' % dct['xpositioner']
        yaxis_nm = 'counter0'
        units_nm = 'um''s'

        #serifLineHeight = fm.height()
        #data_pm = QPixmap("data.png")
        #data_pm= data_pm.scaled(QSize(THMB_SIZE, THMB_SIZE))

        prev_pmap = QPixmap(SPEC_SINGLE_DATA_BOX)
        self.prev_pmap = prev_pmap
        prev_pmap.fill(QColor(0,0,0,0))

        painter = QPainter()
        painter.begin(self.prev_pmap)
        #
        painter.setRenderHints(painter.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)
        #
        pageRect = self.printer.pageRect()
        page = 1

        painter.save()

        painter.fillRect(QRect(QPoint(0,0), SPEC_SINGLE_DATA_BOX), Qt.white)

        y = 0
        #x = pageRect.width() - data_pm.width() - LeftMargin
        x = LeftMargin

        painter.setFont(serifFont)

        y += sansLineHeight
        y += sansLineHeight
        painter.drawText(x + 25, y, "   %s" % fname)
        y += serifLineHeight
        painter.setFont(sansFont)
        painter.drawText(x + 25, y, "%s      %s " % (pnts, scan_type))
        y += sansLineHeight
        painter.drawText(x + 25, y, "%s          %s " % (scan_sub_type, ev))
        y += sansLineHeight
        painter.drawText(x + 25, y, "%s      %s " % (dwell, pol))
        y += sansLineHeight

        _x = x + 25
        ###################################

        grey_pm = QPixmap(SPEC_THMB_WD, SPEC_THMB_HT)
        #grey_pm.fill(QColor(232,232,232))
        #painter.drawPixmap(_x, y, grey_pm)

        # # painter.drawPixmap(btm_rectF, self.pic, QtCore.QRectF(grey_pm.rect()))
        # pic_rectF = QRectF(data_pm.rect())
        cb = grey_pm.rect().center()
        # # now see if the aspect ratio is equal or different, if so adjust image to sit in the center with a black border
        if (data_pm.width() < data_pm.height()):
            r = float(data_pm.width()) / float(data_pm.height())
            #data_pm = data_pm.scaled(QSize(r * SPEC_THMB_WD, SPEC_THMB_HT))
            newx = _x + float((SPEC_THMB_WD / 2.0)) - float(data_pm.width()) / 2.0
            painter.drawPixmap(newx, y, data_pm)

        elif (data_pm.width() > data_pm.height()):
            r = float(data_pm.height()) / float(data_pm.width())
            #data_pm = data_pm.scaled(QSize(SPEC_THMB_WD, r*SPEC_THMB_HT))
            newy = y + float((SPEC_THMB_HT / 2.0)) - float(data_pm.height()) / 2.0
            painter.drawPixmap(_x, newy, data_pm)
        else:
            #data_pm = data_pm.scaled(QSize(SPEC_THMB_WD, SPEC_THMB_HT))
            painter.drawPixmap(_x, y, data_pm)


        #####################################

        #painter.drawPixmap(_x, y, data_pm)
        #y += data_pm.height() + sansLineHeight

        ###########################################
        # rotate to place name of counter
        #painter.translate(_x + grey_pm.width(), y + 0.25 * SPEC_THMB_HT)
        painter.translate(_x + grey_pm.width() - 10, y + 0.25 * SPEC_THMB_HT)
        painter.rotate(90.0)
        painter.drawText(0, -5, " %s " % (yaxis_nm))
        #UNDO TRANSFORM
        painter.rotate(-90.0)
        painter.translate(-1.0*(_x + grey_pm.width()), -1.0*(y + 0.25 * SPEC_THMB_HT))

        y += grey_pm.height() + 27 + sansLineHeight

        painter.setFont(arialFontSmall)
        painter.drawText(x + (grey_pm.width()/2) , y - 25, "%s" % xaxis_nm)
        painter.setFont(serifFont)
        painter.end()
        painter.restore()


        html = self.create_html_for_pmap(prev_pmap)
        document = QTextDocument()
        document.setHtml(html)
        return(html)


    def create_html_for_pmap(self, pmap):
        text = "<html>"

        byteArray = QByteArray()
        buffer = QBuffer(byteArray)
        buffer.open(QIODevice.WriteOnly)
        pmap.save(buffer, "PNG")
        url = "<img src=\"data:image/png;base64," + byteArray.toBase64() + "\"/>"
        text += url
        text += "</html>"
        return(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = PrintSTXMThumbnailWidget(fname=r'S:\STXM-data\Cryo-STXM\2017\guest\1215\C171215077.hdf5')
    form.show()
    app.exec_()

