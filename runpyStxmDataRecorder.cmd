@echo on
DOSKEY ls=dir
DOSKEY cd=cd $1$Tdir
DOSKEY cdb=cd C:\controls\epics\R3.15.5\base
DOSKEY cdl=cd C:\controls\epics\R3.15.5\local\src
DOSKEY cde=cd C:\controls\epics\R3.15.5\extensions
DOSKEY cds=cd C:\controls\epics\R3.15.5\modules\support
DOSKEY cdsm=cd C:\controls\py2.7\Beamlines\sm\opi
DOSKEY cdmotor=cd C:\controls\epics\R3.15.5\modules\support\motor-6-8
DOSKEY cddaq=cd C:\controls\epics\R3.15.5\local\src\daqmx_asynPortDriver
DOSKEY cdsscan=cd C:\controls\epics\R3.15.5\modules\support\sscan-2-9

set PYTHONPATH=C:\controls\git_sandbox\latest\pyStxm

set EPICS_BASE=C:\controls\epics\R3.15.5\base
set PATH=%EPICS_BASE%\bin\windows-x64-debug;%PATH%
set EPICS_HOST_ARCH=windows-x64-debug

set BASE=C:\controls\epics\R3.15.5\base
set MODS=C:\controls\epics\R3.15.5\modules\support
set EXTS=C:\controls\epics\R3.15.5\extensions
set LOC=C:\controls\epics\R3.15.5\local

set C:\GnuWin32\bin;C:\Perl\bin;%EXTS%\bin\windows-x64;%LOC%\bin\windows-x64;C:\controls\EPICS Windows Tools;%PATH%
set PATH=%MODS%/asyn-4-21/bin/windows-x64;%PATH%

cd %CD%\cls\zeromq\epics
C:\Continuum\Anaconda2\python.exe %CD%\epics_server_pubSub.py 10.52.35.212 5555 S:\STXM-data\Cryo-STXM\2019\guest

