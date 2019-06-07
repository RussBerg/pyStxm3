

# tw.tabBar().setStyleSheet("QTabBar::tab:selected { color: #00ff00; background-color: rgb(0,0,255);}")

from PyQt5 import QtWidgets, QtCore

from cls.utils.enum_utils import Enum
from cls.utils.log import get_module_logger

alert_lvls = Enum('NORMAL', 'WARNING', 'ERROR')

_logger = get_module_logger(__name__)

class BaseContentPanel(QtWidgets.QWidget):

    alert = QtCore.pyqtSignal(object)

    def __init__(self):
        super(BaseContentPanel, self).__init__()


    def raise_alert(self, lvl):
        '''
        a function that can be called by nheriting classes to emit an alert
        :param lvl:
        :return:
        '''

        if(lvl < alert_lvls.NORMAL):
            _logger.error('raise_alert: lvl is less than min range of alerts')
            self.alert.emit(alert_lvls.ERROR)
        if (lvl > alert_lvls.ERROR):
            _logger.error('raise_alert: lvl is greater than max range of alerts')
            self.alert.emit(alert_lvls.ERROR)
        else:
            self.alert.emit(lvl)



