@echo off
title Build AutoClicker

cd /d "%~dp0"

echo ====================================
echo   AutoClicker Build Script
echo ====================================
echo.

set "PYTHON_CMD="

REM Try py launcher first
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
    goto :start
)

REM Try python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    goto :start
)

echo [ERROR] Python not found. Please install Python 3.x first.
pause
exit /b 1

:start
echo [1/3] Installing PyInstaller...
%PYTHON_CMD% -m pip install pyinstaller
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install PyInstaller. See output above.
    pause
    exit /b 1
)
echo PyInstaller installed successfully.

echo.
echo [2/3] Building executable...
%PYTHON_CMD% -m PyInstaller auto_clicker.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See output above.
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo Output: dist\AutoClicker.exe
echo.
pause
