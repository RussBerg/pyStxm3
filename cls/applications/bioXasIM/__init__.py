# -*- coding: utf-8 -*-
#
"""
cls:
This will house all of the Canadian Lightsource specific modules 
"""
import os
import time
from datetime import date
import bz2

from cls.utils.log import get_module_logger, log_to_console, log_to_qt
from cls.appWidgets.enum import Enum

abs_path_to_top = os.path.dirname(os.path.abspath(__file__))
abs_path_to_ini_file = os.path.join( os.path.dirname(os.path.abspath(__file__)),  'app.ini')

