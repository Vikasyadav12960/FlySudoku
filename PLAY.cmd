@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 arcade.py
goto result
:usepython
python arcade.py
:result
if errorlevel 1 (
  echo Install Python 3.11 or newer with Tcl/Tk support, then open PLAY.cmd again.
  pause
  exit /b 1
)
