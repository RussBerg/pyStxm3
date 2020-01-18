import sys
from PyQt5 import QtWidgets

# _excepthook = sys.excepthook
# def exception_hook(exctype, value, traceback):
#     _excepthook(exctype, value, traceback)
# sys.excepthook = exception_hook

class Test(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setText("hello")
        self.clicked.connect(self.buttonClicked)

    def buttonClicked(self):
        print("clicked")
        raise Exception("wow")

app = QtWidgets.QApplication(sys.argv)
t = Test()
t.show()
app.exec_()