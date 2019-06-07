

from PyQt5 import QtCore, QtWidgets

def get_signals(source):
    sigs = []
    cls = source if isinstance(source, type) else type(source)
    signal = type(QtCore.pyqtSignal())
    for name in dir(source):
        if(hasattr(cls, name)):
            if isinstance(getattr(cls, name), signal):
                print(name)
                sigs.append(name)
    return(sigs)


if __name__ == '__main__':

    get_signals(QtWidgets.QWidget)
