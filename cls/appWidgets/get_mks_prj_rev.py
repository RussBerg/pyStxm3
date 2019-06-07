'''
Created on Sep 28, 2016

@author: bergr
'''

import os
import simplejson as json
from subprocess import Popen
from subprocess import PIPE

def get_mks_project_rev(sandbox_path):
    
    my_env = os.environ
    my_env["PATH"] = "C:\\Program Files (x86)\\MKS\\IntegrityClient\\bin;" + my_env["PATH"]
    #subprocess.Popen(my_command, env=my_env)
    #pipe = Popen('si viewprojecthistory --sandbox="%s"' % sys.argv[1], shell=True, bufsize=1024, stdin=PIPE, stdout=PIPE, close_fds=True)
    pipe = Popen('si viewprojecthistory --sandbox="%s"' % sandbox_path, shell=True, bufsize=1024, stdin=PIPE, stdout=PIPE, env=my_env)
    
    versions = pipe.stdout.read().split('\n')
    versions = versions[1].split('\t')
    # ['1.7', 'Russ Berg (bergr)', 'Sep 26, 2016 4:37:09 PM', 'Exp', '', 'pyStxm v1.0 Sept 2016', 'project as of Sept 26 2016']
    dct = {}
    dct['ver'] = versions[0]
    dct['major_ver'] = dct['ver'].split('.')[0]
    dct['minor_ver'] = dct['ver'].split('.')[1]
    dct['auth'] = versions[1]
    dct['date'] = versions[2]
    dud = versions[3]
    dct['ver_str'] = versions[5]
    dct['comments_str'] = versions[6]
    
    return(dct)
     

def update_local_version_file(sandbox_path):
    fdir = sandbox_path.replace('project.pj', '')
    if os.path.exists(fdir):
        dct = get_mks_project_rev(sandbox_path)
        j=json.dumps(dct, sort_keys=True, indent=4)
        f=open(fdir + '/version.json',"w")
        f.write(j)
        f.close()
    else:
        print('update_local_version_file: path [%s] does not exist' % fdir)
        
    


if __name__ == '__main__':
    
#     dct = get_mks_project_rev(r'C:/controls/py2.7/project.pj')
#     
#     for k in dct.keys():
#         print '%s = %s' % (k, dct[k])
#     
    update_local_version_file(r'C:/controls/py2.7/project.pj')

