
import sys
from PyQt5 import QtWidgets, QtCore
from bcm.devices import Motor_Qt






if __name__ == '__main__':
    import time
    def go():
        global evmtr
        print('calling evmtr.move(2.5, wait=False)')
        evmtr.move(2.5, wait=False)

    app = QtWidgets.QApplication(sys.argv)
    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(go)

    evmtr = Motor_Qt('BL1610-I10:ENERGY', name='BL1610-I10:ENERGY', abstract_mtr=True)
    #evmtr.move(1860, wait=False)

    #evmtr = Motor_Qt('IOC:m102', name='zoneX', abstract_mtr=True)
    #time.sleep(1.15)
    timer.start(3000)
    sys.exit(app.exec_())