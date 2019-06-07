import os, sys

from PyQt5 import QtGui, QtCore, uic

class Window(QtWidgets.QWidget):
    """
    classdocs
    """
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        #uic.loadUi('C:/controls/py2.7/Beamlines/sm/stxm_control/ui/videoTest.ui', self)
        self.setGeometry(550,550,500,500)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = Window()
    window.show()
    sys.exit(app.exec_())