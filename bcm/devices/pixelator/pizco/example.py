from PyQt5.QtCore import pyqtSignal as Signal

class MultiplyBy(object):

    factor_changed = Signal()

    def __init__(self, factor):
        self._factor = factor

    def calculate(self, x):
        return x * self.factor

    @property
    def factor(self):
        return self._factor

    @factor.setter
    def factor(self, value):
        if self._factor == value:
            pass
        else:
            self.factor_changed.emit(value, self._factor)
            self._factor = value