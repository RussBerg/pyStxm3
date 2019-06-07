
'''
Created on Feb 18, 2016

@author: control
'''


import os
import sys

from PyQt5 import QtCore, QtWidgets

from bcm.devices import aio
from cls.utils.excepthook import excepthook

sys.excepthook = excepthook

path_sep = ';'
epicsPath = r'C:\controls\epics\R3.14.12.4\base\bin\win32-x86;C:\controls\epics\R3.14.12.4\base\lib\win32-x86;C:\controls\git\pyStxm'
path  = [os.environ['PATH']]
path.extend(epicsPath.split(';'))
os.environ['PATH'] = path_sep.join(path)
os.environ['PYTHONPATH'] = path_sep.join(path)



def callback (task, event_type, samples, callback_data):
    print()
    data = task.read(samples, samples_per_channel=samples,
                     fill_mode='group_by_scan_number')
    print('Acquired %s samples' % (len (data)))
    print(data[:10])
    return 0

def callback_done(task, status, callback_data):
    print('callback_done, status=' ,status)
    return 0


# task.register_every_n_samples_event(callback, samples = 100)
# task.register_done_event(callback_done)
class InterferometerSignalWindow(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal(object ,float)
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setWindowTitle('Interferometer Signal Strengh Viewer [EPICS]')

        hlayout = QtWidgets.QHBoxLayout()

        self.ax1Lbl = QtWidgets.QLabel('Axis 1:')
        font = self.ax1Lbl.font()
        font.setPointSize(104)

        self.ax1Fbk = QtWidgets.QLabel('0.0 volts')

        self.ax2Lbl = QtWidgets.QLabel('Axis 2:')
        self.ax2Fbk = QtWidgets.QLabel('0.0 volts')

        self.ax1Lbl.setFont(font)
        self.ax2Lbl.setFont(font)

        font.setBold(True)
        self.ax1Fbk.setFont(font)
        self.ax2Fbk.setFont(font)

        hlayout.addWidget(self.ax1Lbl)
        hlayout.addWidget(self.ax1Fbk)

        h2layout = QtWidgets.QHBoxLayout()
        h2layout.addWidget(self.ax2Lbl)
        h2layout.addWidget(self.ax2Fbk)

        layout = QtWidgets.QVBoxLayout(self)

        layout.addLayout(hlayout)
        layout.addLayout(h2layout)

        self.axis1_volts = aio('uhvAi:ai:ai0_RBV', id=0)
        self.axis1_volts.changed.connect(self.on_new_val)

        self.axis2_volts = aio('uhvAi:ai:ai1_RBV', id=1)
        self.axis2_volts.changed.connect(self.on_new_val)

    def on_new_val(self, kwargs):
        #print kwargs
        id = kwargs['id']
        val = kwargs['value']
        if(id is 0):
            #self.changed.emit(self.ax1Fbk, val)
            self.on_changed(self.ax1Fbk, val)
        else:
            self.on_changed(self.ax2Fbk, val)

    def on_changed(self, axis, val):
        ax_str = str('\t%.4f' % val)
        if val < 0.3:
            axis.setText("<font color='red'>%s</font>" % ax_str)
        else:
            axis.setText("<font color='blue'>%s</font>" % ax_str)





# task.start()
#
# if 1:
#     from pylab import plot, show
#     data = task.read(3000, fill_mode='group_by_channel')
#     print data
#     plot (data)
#     show ()
#
# raw_input('Acquiring samples continuously. Press Enter to interrupt..')
#
# task.stop() # gives 'pure virtual method called' abort message
#
# del task


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    win = InterferometerSignalWindow()
    win.show()
    app.exec_()
