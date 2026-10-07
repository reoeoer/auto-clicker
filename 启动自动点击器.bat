@echo off
title Auto Clicker

set "PYTHON_CMD="
set "PYTHONW_CMD="

REM Try py launcher first (Windows Python installer)
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
    set "PYTHONW_CMD=pyw -3"
    goto :python_found
)

REM Try python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    set "PYTHONW_CMD=pythonw"
    goto :python_found
)

REM Neither found
echo Python not found. Please install Python 3.x first.
pause
exit /b 1

:python_found
REM Check pyautogui
%PYTHON_CMD% -c "import pyautogui" >nul 2>&1
if errorlevel 1 (
    echo Installing pyautogui...
    %PYTHON_CMD% -m pip install pyautogui
)

REM Run the auto clicker
cd /d "%~dp0"

REM Try pythonw first (no console window)
%PYTHONW_CMD% --version >nul 2>&1
if %errorlevel%==0 (
    start "" %PYTHONW_CMD% auto_clicker.py
    exit /b 0
)

REM Fallback: run with console
%PYTHON_CMD% auto_clicker.py

if errorlevel 1 (
    echo.
    echo Program exited with error. Code: %errorlevel%
    pause
)
