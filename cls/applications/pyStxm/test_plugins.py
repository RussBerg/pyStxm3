
import sys
import os
from PyQt5 import QtWidgets
from yapsy.PluginManager import PluginManager

from cls.scanning.base import ScanParamWidget

def setup_scan_toolbox():
    """
    setup_scan_toolbox(): description

    :returns: None
    """
    # Create plugin manager
    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    scanTypeToolBox = QtWidgets.QToolBox()
    scanTypeToolBox.layout().setContentsMargins(0, 0, 0, 0)
    scanTypeToolBox.layout().setSpacing(0)
    # scanTypeToolBox.setStyleSheet(" QToolBox::tab {padding-left: 100px;} ")
    manager = PluginManager(categories_filter={"Scans": ScanParamWidget})
    # manager.setPluginPlaces(['scan_plugins'])
    manager.setPluginPlaces([os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scan_plugins')])
    # Load plugins
    manager.locatePlugins()
    manager.loadPlugins()

    pages = 0
    num_scans = 0
    scans = {}

    # walk the plugin directory looking for plugins of category ScanParamWidget
    for plugin in manager.getPluginsOfCategory("Scans"):
        print("Found SCAN plugin [%s]" % plugin.plugin_object.name)
        scans[plugin.plugin_object.idx] = plugin.plugin_object
        num_scans += 1


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    setup_scan_toolbox()