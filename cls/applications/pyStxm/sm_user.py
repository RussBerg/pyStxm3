# -*- coding: utf-8 -*-
#
"""
"""
import os
from cls.appWidgets.user_account.user_acct_utils import user_accnt_mgr
			
#create a user account manager
usr_acct_manager = user_accnt_mgr(os.path.dirname(os.path.abspath(__file__)))

__all__ = ['usr_acct_mgr']

