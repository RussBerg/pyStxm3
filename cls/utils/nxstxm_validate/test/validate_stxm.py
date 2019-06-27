import sys
import nxstxm_validate as nxv

#nxstxm_validate.main('-d C:\controls\py2.7\Beamlines\sm\data\guest\May19'.split())
nxv.validate(sys.argv[1:])


