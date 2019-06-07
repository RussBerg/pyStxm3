@ECHO OFF

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=c:\continuum\anaconda2\scripts\sphinx-build
)
set BUILDDIR=_build
set ALLSPHINXOPTS=-d %BUILDDIR%/doctrees %SPHINXOPTS% .
set I18NSPHINXOPTS=%SPHINXOPTS% .
if NOT "%PAPER%" == "" (
	set ALLSPHINXOPTS=-D latex_paper_size=%PAPER% %ALLSPHINXOPTS%
	set I18NSPHINXOPTS=-D latex_paper_size=%PAPER% %I18NSPHINXOPTS%
)

%SPHINXBUILD% -b html %ALLSPHINXOPTS% %BUILDDIR%/html
if errorlevel 1 exit /b 1
echo.
echo.Build finished. The HTML pages are in %BUILDDIR%/html.
goto end

:end
