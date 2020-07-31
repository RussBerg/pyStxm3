@echo on
DOSKEY ls=dir
DOSKEY cd=cd $1$Tdir
DOSKEY cdb=cd C:\controls\epics\R3.14.12.4\base
DOSKEY cdl=cd C:\controls\epics\R3.14.12.4\local\src
DOSKEY cde=cd C:\controls\epics\R3.14.12.4\extensions
DOSKEY cds=cd C:\controls\epics\R3.14.12.4\modules\support
DOSKEY cdsm=cd C:\controls\py2.7\Beamlines\sm\opi
DOSKEY cdmotor=cd C:\controls\epics\R3.14.12.4\modules\support\motor-6-8
DOSKEY cddaq=cd C:\controls\epics\R3.14.12.4\local\src\daqmx_asynPortDriver
DOSKEY cdsscan=cd C:\controls\epics\R3.14.12.4\modules\support\sscan-2-9

set PYTHONPATH=%CD%

@echo call "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcvarsall.bat"
call "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\vcvarsall.bat"
set EPICS_BASE=C:\controls\epics\R3.14.12.4\base
set PATH=%EPICS_BASE%\bin\win32-x86-debug;%PATH%
set EPICS_HOST_ARCH=win32-x86-debug

set BASE=C:\controls\epics\R3.14.12.4\base
set MODS=C:\controls\epics\R3.14.12.4\modules\support
set EXTS=C:\controls\epics\R3.14.12.4\extensions
set LOC=C:\controls\epics\R3.14.12.4\local

set PYTHON_PATH=C:\controls\github\pyStxm3

cd C:\controls\github\pyStxm3
python.exe cls\applications\pyStxm\runPyStxm.py

