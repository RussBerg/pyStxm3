
from PyQt5 import QtCore, QtGui


def get_pixmap(fname, w, h):
    """
    get_pixmap(): description

    :param get_pixmap(fname: get_pixmap(fname description
    :type get_pixmap(fname: get_pixmap(fname type

    :returns: None
    """
    pmap = QtGui.QPixmap(fname)
    #pmap.scaled(64, 64)#, aspectRatioMode=Qt_IgnoreAspectRatio, transformMode=Qt_FastTransformation)
    pmap = pmap.scaled(QtCore.QSize(w,h),  QtCore.Qt.KeepAspectRatio)
    return(pmap)

