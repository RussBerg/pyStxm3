'''
Created on 2012-12-21

@author: bergr
'''

from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
from PIL import ImageQt
import scipy.misc
import numpy as np

#from cls.utils.colormaps import COLORMAPS, _COLORNAMES


def array_to_jpg(fpath, data):
    scipy.misc.imsave(fpath, data)


def image_to_array(image):
    arr = np.array(image.getdata()).reshape(image.size[::-1])
    return (arr)


def array_to_image(data, suffix='tif'):
    im = Image.fromarray(data, mode="P")
    return (im)


# im.save('test.tif')

def array_to_qimage(arr):
    h, w = arr.shape
    arr = np.require(arr, np.uint32, 'C')
    qi = QtGui.QImage(arr.data, w, h, QtGui.QImage.Format_RGB32)
    qi.ndarray = arr
    # qi.setNumColors(256)
    for y in range(h):
        for x in range(w):
            val = qi.pixel(x, y)
            qi.setPixel(QtCore.QPoint(x, y), QtGui.qRgb(val, val, val))
    return (qi)


def array_to_gray_qimage(arr):
    '''
    arr is expected to be of type np.float32
    :param arr:
    :return:
    '''
    # if(arr.ptp() == 0.0):
    # 	im = np.uint8((arr - arr.min())/1.0*255.0)
    # else:
    # 	im = np.uint8((arr - arr.min())/arr.ptp()*255.0)
    #
    denom = (arr.max() - arr.min())
    if (denom <= 0):
        # print 'array_to_gray_qimage: uh oh divide by zero'
        qi = QtGui.QImage(arr.data, arr.shape[1], arr.shape[0], arr.shape[1], QtGui.QImage.Format_Indexed8)
    else:
        im = np.uint8(((arr - arr.min()) * 255 / (arr.max() - arr.min())))
        qi = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.shape[1], QtGui.QImage.Format_Indexed8)

    return (qi)


def array_to_gray_qpixmap(arr):
    qi = array_to_gray_qimage(arr)
    # convert it to a QPixmap for display:
    pmap = QtGui.QPixmap.fromImage(qi)
    return (pmap)


def array_to_qpixmap(gray):
    """Convert the 2D numpy array `gray` into a 8-bit QImage with a gray
    colormap.  The first dimension represents the vertical image axis."""

    if len(gray.shape) != 2:
        raise ValueError("gray2QImage can only convert 2D arrays")
        return

    qimg = array_to_qimage(gray)

    pixmap = QtGui.QPixmap.fromImage(qimg, QtCore.Qt.MonoOnly)
    return (pixmap)


__all__ = ['image_to_array', 'array_to_image', 'array_to_qimage', 'array_to_qpixmap']


class TestWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.button = QtWidgets.QPushButton("Do test")

        # self.listWidget = QtWidgets.QListWidget()
        # self.listWidget.setWindowTitle('Example List')
        # self.listWidget.setMinimumSize(600, 400)
        # self.model = QtWidgets.QStandardItemModel()
        # Apply the model to the list view
        # self.listWidget.setModel(self.model)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.view)
        # layout.addWidget(self.listWidget)
        self.setLayout(layout)

        self.button.clicked.connect(self.do_array_test)

    def add_to_list(self, name, widget):
        # n_item = QtWidgets.QStandardItem(name)
        # i_item = QtWidgets.QStandardItem(wdgt)

        # add a checkbox to it
        # n_item.setCheckable(True)

        # Add the item to the model
        # self.model.appendRow(n_item)
        # self.model.appendColumn([i_item])
        item = QtWidgets.QListWidgetItem("")
        # self.connect(widget, QtCore.SIGNAL("clicked(int)"), self.on_clicked)
        widget.clicked.connect(self.on_clicked)
        # self.connect(widget, QtCore.SIGNAL("favoriteChange(bool)"), self._favorite_changed)
        # self.connect(widget, QtCore.SIGNAL("deleteMe(QListWidgetItem)"), self._delete_recent_project_item)
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, widget)

    def on_clicked(self, idx):
        print('%d clicked')

    def do_test(self):
        img = Image.open('image.png')
        self.display_image(img)

    # 		enhancer = ImageEnhance.Brightness(img)
    # 		for i in range(1, 8):
    # 			img = enhancer.enhance(i)
    # 			self.display_image(img)
    # 			QtCore.QCoreApplication.processEvents()  # let Qt do his work
    # 			time.sleep(0.5)

    def do_array_test(self):
        from sm.stxm_control.widgets.imgInfo import previewImageWidget
        data = np.random.randint(0, 2 ** 16 - 1, (200, 200))
        h, w = data.shape
        pixmap = array_to_qpixmap(data)
        self.scene.addPixmap(pixmap)
        # self.view.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)
        self.scene.update()

    # prevWdgt = previewImageWidget('200 x 200 | 535.3 eV | 3.5 ms', data)
    # self.add_to_list('name1', prevWdgt)

    def display_image(self, img):
        self.scene.clear()
        w, h = img.size
        self.imgQ = ImageQt.ImageQt(img)  # we need to hold reference to imgQ, or it will crash
        pixMap = QtGui.QPixmap.fromImage(self.imgQ)
        self.scene.addPixmap(pixMap)
        self.view.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)
        self.scene.update()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    widget = TestWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())
