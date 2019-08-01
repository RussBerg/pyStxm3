import sys
from nxstxm_validate.nxstxm_validate import validate_file

#nxstxm_validate.main('-d C:\controls\py2.7\Beamlines\sm\data\guest\May19'.split())
def validate(fpath):
    #nxstxm_validate.nxstxm_validate(fpath)
    return(validate_file(fpath))

__version__ = '1.0.1'

__requires__ = [
    'nexpy',
    'xmltodict',
    'h5py',
    'pkg_resources'
]

__all__ = ['validate']    