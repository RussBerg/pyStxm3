
# tw.tabBar().setStyleSheet("QTabBar::tab:selected { color: #00ff00; background-color: rgb(0,0,255);}")

from PyQt5 import QtWidgets

from cls.appWidgets.base_content_panel import BaseContentPanel
from cls.utils.log import get_module_logger
from cls.app_data.defaults import master_colors
from cls.devWidgets.ophydLabelWidget import ophyd_biLabelWidget
from cls.appWidgets.base_content_panel import alert_lvls


_logger = get_module_logger(__name__)

class IOCAppsPanel(BaseContentPanel):
    '''
            add a list of IOC application heart beat dev's to the 'Status' tab of the main application. The status
            of each heart beat will update based on wether the app is running or not
            :return:
            '''
    def __init__(self, main_obj=None):
        super(IOCAppsPanel, self).__init__()
        self.setObjectName('ioc_apps_panel')
        vlayout = QtWidgets.QVBoxLayout()
        if(main_obj is None):
            _logger.error('main_obj cannot be None')
            return

        dev_obj = main_obj.get_device_obj()
        hrt_bt_dct = dev_obj.get_all_pvs_of_type('HEARTBEATS')
        app_names = list(hrt_bt_dct.keys())

        for app_hrtbt_name in app_names:
            app_pv = hrt_bt_dct[app_hrtbt_name]['dev']
            app_name = hrt_bt_dct[app_hrtbt_name]['desc']
            vlayout.addWidget(self.make_app_sts_lbl(app_pv, app_name))

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        vlayout.addItem(spacer)
        self.setLayout(vlayout)

        #self.IOCSwStatusGrpBx.setLayout(vlayout)

    def make_app_sts_lbl(self, dev, hdr_txt):

        app_ltgreen = master_colors['app_ltgreen']
        app_red = master_colors['app_red']
        white = master_colors['white']

        stsLbl = ophyd_biLabelWidget(dev,
                                  hdrText=hdr_txt, title_color=white,
                                  options=dict(state_clrs=[app_red, app_ltgreen]))
        stsLbl.binary_change.connect(self.on_binary_changed)

        return (stsLbl)

    def on_binary_changed(self, dct):
        '''
        depending on the text, emit the alert level and also the panel that is raising the alert
        :param dct:
        :return:
        '''
        new_dct = {}
        new_dct['panel'] = self
        #the ioc_apps panel is the second tab on the mainTabWidget so set the tab_idx to 2
        new_dct['tab_idx'] = 2
        new_dct['obj_name'] = 'ioc_apps_panel'

        if('val_str' in list(dct.keys())):
            if(type(dct['val_str']) is str):
                if(dct['val_str'].find('DEAD') > -1):
                    new_dct['lvl'] = alert_lvls.ERROR
                    self.alert.emit(new_dct)
                if (dct['val_str'].find('ALIVE') > -1):
                    new_dct['lvl'] = alert_lvls.NORMAL
                    self.alert.emit(new_dct)
        #print('ioc_apps on_binary_changed ', dct)



