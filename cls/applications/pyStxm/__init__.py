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
#from cls.appWidgets.user_account.user_acct_utils import user_accnt_mgr
            
#create a user account manager
#usr_acct_mgr = user_accnt_mgr(os.path.dirname(os.path.abspath(__file__)) + '\users.p')
abs_path_to_top = os.path.dirname(os.path.abspath(__file__))
abs_path_to_ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.ini')
abs_path_to_docs = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','docs','_build','html')

