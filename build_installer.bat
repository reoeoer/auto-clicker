@echo off
title Build Installer - AutoClicker

cd /d "%~dp0"

echo ====================================
echo   Build AutoClicker Installer
echo ====================================
echo.

REM Check if exe exists
if not exist "dist\AutoClicker.exe" (
    echo [ERROR] dist\AutoClicker.exe not found.
    echo Please run build_exe.bat first.
    pause
    exit /b 1
)

REM Check Inno Setup
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :build
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :build
)

echo [INFO] Inno Setup not found.
echo Download from: https://jrsoftware.org/isdl.php
echo.
echo Install it and run this script again.
pause
exit /b 1

:build
echo [1/1] Building installer...
"%ISCC%" installer.iss
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to build installer. See output above.
    pause
    exit /b 1
)

echo.
echo Installer built successfully!
echo Output: Output\AutoClicker-Setup.exe
echo.
echo This installer can be copied to other Windows computers.
echo No Python required on target machine.
echo.
pause
