@echo off & python -x "%~f0" %* & goto :eof 

import sys
import nxstxm_validate as nxv

nxv.validate(sys.argv[1:])
