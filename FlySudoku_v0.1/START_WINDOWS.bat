@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m flysudoku
) else (
  python -m flysudoku
)
if errorlevel 1 (
  echo.
  echo FlySudoku could not start. Install Python 3.11+ from python.org
  echo Make sure "tcl/tk and IDLE" is selected in the Python installer.
  pause
)
