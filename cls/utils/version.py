import os
import simplejson as json

def get_version():
    filename = r'./version.json'
    if os.path.exists(filename):
        file = open(filename)
        ver_dct = json.loads(file.read())
        file.close()

    else:
        ver_dct = {}
        ver_dct['ver'] = '1.9'
        ver_dct['ver_str'] = "Version 1.9"
        ver_dct['major_ver'] = '1'
        ver_dct['minor_ver'] = '9'
        ver_dct['auth'] = 'Russ Berg'
        ver_dct['date'] = 'Jan 26 2017'

    return(ver_dct)
