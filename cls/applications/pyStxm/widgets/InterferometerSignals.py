'''
Created on Feb 18, 2016

@author: control
'''


from PyQt5 import QtGui, QtCore, QtWidgets
from bcm.pylibdaqmx.nidaqmx.libnidaqmx import AnalogInputTask
import numpy as np

import os
    
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
    print('callback_done, status=',status)
    return 0

#task.register_every_n_samples_event(callback, samples = 100)
#task.register_done_event(callback_done)
class InterferometerSignalWindow(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal(float,float)
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        
        self.setWindowTitle('Interferometer Signal Strengh Viewer')
        
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
        
        self.task_axis1 = AnalogInputTask()
        #self.task_axis2 = AnalogInputTask()
        self.task_axis1.create_voltage_channel('Dev3/ai0', terminal = 'rse', min_val=0.0, max_val=3.0)
        self.task_axis1.create_voltage_channel('Dev3/ai1', terminal = 'rse', min_val=0.0, max_val=3.0)
        
        self.task_axis1.configure_timing_sample_clock(rate = 10000.0)
        #self.task_axis2.configure_timing_sample_clock(rate = 1000.0)
        
        self.task_axis1.start()
        #self.task_axis2.start()
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(50)
        
    def on_timer(self):
        #from pylab import plot, show
        data = self.task_axis1.read(1000, fill_mode='group_by_channel')
        #print data.shape
        #data2 = self.task_axis2.read(10, fill_mode='group_by_channel')
        av1 = np.average(data[0][0:50])
        #av1 = data[0][0]
        av2 = np.average(data[1][0:50])
        #av2 = data[1][0]
        
        ax1_str = str('\t%.4f' % av1)
        ax2_str = str('\t%.4f' % av2)
        if av1 < 0.3:
            self.ax1Fbk.setText("<font color='red'>%s</font>" % ax1_str)
        else:
            self.ax1Fbk.setText("<font color='blue'>%s</font>" % ax1_str)    
        
        if av2 < 0.3:
            self.ax2Fbk.setText("<font color='red'>%s</font>" % ax2_str)
        else:
            self.ax2Fbk.setText("<font color='blue'>%s</font>" % ax2_str)

        self.changed.emit(av1, av2)
                
        
        
        
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
    