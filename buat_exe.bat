@echo off
cd /d "%~dp0"
title Pembuat CCTV-Hub.exe Otomatis
color 0B

echo ========================================================
echo        MEMBUAT CCTV-HUB MENJADI FILE .EXE NATIVE
echo ========================================================
echo Lokasi folder: %~dp0
echo.

echo [1/4] Mencari lokasi instalasi Python resmi...

set "PYTHON_EXE="

:: 1. Cek di AppData (Instalasi User)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    goto found_python
)

:: 2. Cek di Program Files (Instalasi All Users)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"
    goto found_python
)

:: 3. Cek di PATH sistem (Pastikan BUKAN WindowsApps)
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PYTHON_EXE=%%i"
        goto found_python
    )
)

:: Jika belum ada, install otomatis menggunakan installer yang ada di folder
echo [!] Python resmi belum terdeteksi di sistem.
echo [!] Memulai instalasi Python 3.11 secara otomatis...
echo     Mohon tunggu hingga selesai (30-60 detik)...
echo.

if not exist "python-3.11.9-amd64.exe" (
    color 0C
    echo [ERROR] File python-3.11.9-amd64.exe tidak ditemukan di folder ini!
    pause
    exit /b 1
)

start /wait "" "python-3.11.9-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    goto found_python
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python311\python.exe"
    goto found_python
)

color 0C
echo [ERROR] Instalasi selesai tetapi file python.exe belum terdeteksi.
echo Silakan install manual dengan klik 2x file python-3.11.9-amd64.exe
echo dan centang [X] Add python.exe to PATH.
pause
exit /b 1

:found_python
echo [✔] Python terdeteksi di: "%PYTHON_EXE%"
"%PYTHON_EXE%" --version
echo.

echo [2/4] Memasang pustaka pendukung (Requirements & PyInstaller)...
echo Menginstall requirements.txt...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo [ERROR] Gagal memasang requirements.txt. Periksa koneksi internet!
    pause
    exit /b 1
)

echo Menginstall PyInstaller...
"%PYTHON_EXE%" -m pip install pyinstaller
if errorlevel 1 (
    color 0C
    echo [ERROR] Gagal memasang PyInstaller!
    pause
    exit /b 1
)

echo.
echo [3/4] Mengompilasi CCTV-Hub.exe menggunakan PyInstaller...
echo Mohon tunggu proses penggabungan kode dan modul...
echo.

"%PYTHON_EXE%" -m PyInstaller CCTV-Hub.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [!] Kompilasi dengan spec gagal, mencoba kompilasi langsung (fallback)...
    "%PYTHON_EXE%" -m PyInstaller --noconsole --onefile --name "CCTV-Hub" --clean --noconfirm main.py
)

if errorlevel 1 (
    color 0C
    echo.
    echo ========================================================
    echo [ERROR] Kompilasi .exe gagal.
    echo Kemungkinan penyebab:
    echo 1. Antivirus (Windows Defender/Smadav) memblokir file bootloader PyInstaller di folder Temp.
    echo 2. Sebagai alternatif yang 100%% berfungsi tanpa perlu compile,
    echo    cukup klik 2x file: "Jalankan_Tanpa_CMD.vbs"!
    echo ========================================================
    pause
    exit /b 1
)

echo.
echo [4/4] Memindahkan file CCTV-Hub.exe ke folder ini...
if exist "dist\CCTV-Hub.exe" (
    copy /y "dist\CCTV-Hub.exe" . >nul
    color 0A
    echo.
    echo ========================================================
    echo   SUKSES! File CCTV-Hub.exe BERHASIL DIBUAT!
    echo ========================================================
    echo Anda sekarang bisa langsung klik ganda (double-click)
    echo file CCTV-Hub.exe untuk menjalankan aplikasi!
    echo ========================================================
) else (
    color 0E
    echo File .exe berada di folder dist\CCTV-Hub.exe
)

echo.
pause
