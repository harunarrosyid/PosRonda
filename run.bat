@echo off
cd /d "%~dp0"
title PosRonda Hub v4.4.7 - Autonomous CCTV Engine
color 0B

set "PYTHON_EXE="

:: 1. Cek di AppData (Instalasi User)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    goto run_app
)

:: 2. Cek di Program Files (Instalasi All Users)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"
    goto run_app
)

:: 3. Cek di PATH sistem (Pastikan BUKAN WindowsApps)
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PYTHON_EXE=%%i"
        goto run_app
    )
)

:run_app
if "%PYTHON_EXE%"=="" set "PYTHON_EXE=python"

echo Menjalankan PosRonda Hub v4.4.7...
"%PYTHON_EXE%" run.py
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Program tertutup dengan error.
    pause
)
