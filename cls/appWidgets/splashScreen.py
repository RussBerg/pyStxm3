'''
Created on 2012-05-16

@author: bergr
'''
import os
import sys

from time import time, sleep, strftime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

_splash_screen = None
#splashPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','applications','pyStxm', 'pyStxmSplash.png')
#splashPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splash_v2.png')
if(strftime("%Y%m%d")[-4:] == '0504'):
    splashPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'applications', 'pyStxm',
                                  'splash_maythefourth.png')
else:
    splashPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'applications', 'pyStxm',
                                  'pyStxmSplash.png')

class CSplashScreen(QtWidgets.QFrame):
    def __init__(self, msg, pixmap_path=splashPath):
        super(CSplashScreen, self).__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint)
        #QtWidgets.QFrame(parent=None, flags=QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.itsPixmap = pixmap_path
        self.itsMessage = msg
        self.itsAlignment = QtCore.Qt.AlignLeft
        self.itsColor = QtCore.Qt.white
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #self.setFixedSize(len(self.itsPixmap))

    def clearMessage(self):
        self.itsMessage.clear()
        self.repaint()

    def showMessage(self, theMessage, theAlignment=QtCore.Qt.AlignLeft, theColor=QtCore.Qt.black):
        self.itsMessage  = theMessage
        self.itsAlignment = theAlignment
        self.itsColor  = theColor
        self.repaint()


    def paintEvent(self, pe):
        aTextRect = QtCore.QRect(self.rect())
        aTextRect.setRect(aTextRect.x() + 5, aTextRect.y() + 5, aTextRect.width() - 10, aTextRect.height() - 10)
        aPainter = QtGui.QPainter(self)
        aPainter.drawPixmap(self.rect(), self.itsPixmap)
        aPainter.setPen(self.itsColor)
        aPainter.drawText(aTextRect, self.itsAlignment, self.itsMessage)

#to use, create a function similar to the one below for updating the messages
def show_splash(path):
    image = QtGui.QPixmap(path)
    splashScreen = CSplashScreen(image)
    font = QtGui.QFont(splashScreen.font())
    font.setPointSize(font.pointSize() + 5)
    splashScreen.setFont(font)
    splashScreen.show()
    QtWidgets.QApplication.processEvents()
    for count in range(1, 6):
        splashScreen.showMessage(splashScreen.tr('Processing %1...').arg(count),
                           QtCore.Qt.AlignCenter, QtCore.Qt.white)
        QtWidgets.QApplication.processEvents()
        QtCore.QThread.msleep(1000)
    splashScreen.hide()
    splashScreen.close()


class SplashScreen(QSplashScreen):

    def __init__(self, img_path=splashPath, ver_str='Version 0.0'):
        splash_pix = QPixmap(img_path)
        super(SplashScreen, self).__init__(splash_pix, Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setMask(splash_pix.mask())
        self.version_lbl = QtWidgets.QLabel(ver_str, self)

        font = QtGui.QFont("Arial", 9)
        font.setBold(True)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.version_lbl.setFont(font)
        self.version_lbl.setStyleSheet('color: white;')
        #layout = QtWidgets.QVBoxLayout()
        #layout.addWidget(self.version_lbl)

        #self.setLayout(layout)

        #self.hide()
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

        self.version_lbl.setObjectName("SplashNotice")
        self.version_lbl.setWordWrap(True)
        #self.version_lbl.setText(Localize(my_text))
        #self.version_lbl.resize(200, 50)
        self.version_lbl.move(400, 255)

        #self.raise()
        self.show()



        #self.show()
        self.version_lbl.show()

    def show_msg(self, msg):
        self.showMessage(self.tr(msg), QtCore.Qt.AlignBottom,QtCore.Qt.white)
        #QtWidgets.QApplication.processEvents()
        #time.sleep(0.05)


def get_splash(img_path=splashPath, ver_str='Version 0.0'):
    global _splash_screen

    if(_splash_screen is None):
        _splash_screen = SplashScreen(img_path= img_path, ver_str=ver_str)

    return(_splash_screen)

def del_splash():
    global _splash_screen
    if (_splash_screen is not None):
        del(_splash_screen)


def simple_test():
    app = QtWidgets.QApplication(sys.argv)
    pixmap = QPixmap(splashPath)
    splash = QSplashScreen(pixmap)
    splash.show()
    app.exec_()

def main():
    app = QtWidgets.QApplication(sys.argv)
    start = time()
    splash = QSplashScreen(QPixmap(splashPath))
    splash.show()
    while time() - start < 5:
        sleep(0.001)
        app.processEvents()
    win = QtWidgets.QMainWindow()
    splash.finish(win)
    win.show()
    app.exec_()

if __name__ == "__main__":
    #main()
    simple_test()