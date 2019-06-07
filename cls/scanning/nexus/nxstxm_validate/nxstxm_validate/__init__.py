import sys
from . import nxstxm_validate

#nxstxm_validate.main('-d C:\controls\py2.7\Beamlines\sm\data\guest\May19'.split())
def validate(fpath):
    nxstxm_validate.nxstxm_validate(fpath)

__version__ = '1.0.1'

__requires__ = [
    'nexpy',
    'xmltodict',
    'h5py',
    'pkg_resources'
]

__all__ = ['validate']    