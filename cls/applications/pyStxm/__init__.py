# -*- coding: utf-8 -*-
#
"""
cls:
This will house all of the Canadian Lightsource specific modules 
"""
import os
import subprocess
from cls.utils.json_utils import json_to_file, dict_to_json

#create a user account manager
#usr_acct_mgr = user_accnt_mgr(os.path.dirname(os.path.abspath(__file__)) + '\users.p')
abs_path_to_top = os.path.dirname(os.path.abspath(__file__))
abs_path_to_ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.ini')
abs_path_to_docs = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','docs','_build','html')
abs_path_to_top = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..')
abs_path_of_ddl_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','..','scanning','e712_wavegen','ddl_data','ddl_data.hdf5')

def gen_version_json():
    wd = os.getcwd()
    os.chdir(abs_path_to_top)
    commit_uid = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
    commit_uid = commit_uid.decode('utf-8')
    #commit_date = subprocess.check_output(["git", "show", "-s", "--format=%ci", str(commit_uid)])
    commit_date = str(subprocess.check_output(["git", "show", "-s", commit_uid])).split('\\n')[2]
    commit_date = commit_date.replace('Date: ','')

    commit_branch = subprocess.check_output(["git", "status"]).decode('utf-8')
    commit_branch = commit_branch.split('\n')[0]
    commit_branch = commit_branch.replace('On branch ','')

    dct = {
        "ver": "3.0",
        "ver_str": "Version 3.0",
        "major_ver": "3",
        "minor_ver": "0",
        "commit": str(commit_uid),
        "auth": "Russ Berg",
        "date": commit_date,
        "branch": commit_branch
    }
    os.chdir(wd)

    js = dict_to_json(dct)
    json_to_file('version.json', js)

gen_version_json()