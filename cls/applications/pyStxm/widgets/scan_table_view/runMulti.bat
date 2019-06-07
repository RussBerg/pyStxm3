@echo on

set PYTHONPATH=C:\pyStxm\qt5\pyStxm

set EPICS_BASE=C:\controls\epics\R3.14.12.4\base
set PATH=%EPICS_BASE%\bin\win32-x86-debug;%PATH%
set EPICS_HOST_ARCH=win32-x86-debug

set BASE=C:\controls\epics\R3.14.12.4\base
set MODS=C:\controls\epics\R3.14.12.4\modules\support
set EXTS=C:\controls\epics\R3.14.12.4\extensions
set LOC=C:\controls\epics\R3.14.12.4\local

set C:\GnuWin32\bin;C:\Perl\bin;%EXTS%\bin\win32-x86;%LOC%\bin\win32-x86;C:\controls\EPICS Windows Tools;%PATH%
set PATH=%SQUISH_PREFIX%\bin\;%MODS%/asyn-4-21/bin/win32-x86;%PATH%;C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT

cd C:\pyStxm\qt5\pyStxm\cls\applications\pyStxm\widgets\scan_table_view
dllpreload.exe %SQUISH_PREFIX%\python\python.exe multiRegionWidget.py 

