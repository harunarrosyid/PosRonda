@echo off
cd /d "%~dp0"
title Update Otomatis PosRonda Hub
color 0B

echo ========================================================
echo        UPDATE OTOMATIS POSRONDA HUB v4.4.6
echo ========================================================
echo.

set "ZIP_FILE="
:: Cari berkas update terbaru baik berawalan update_cctv maupun update_posronda
for /f "tokens=*" %%f in ('dir /b /o-d update_cctv*.zip update_posronda*.zip update_*.zip 2^>nul') do (
    set "ZIP_FILE=%%f"
    goto found_zip
)

color 0C
echo [ERROR] File zip update (seperti update_cctv_v4.4.6.zip atau update_cctv.zip) tidak ditemukan!
echo.
echo Pastikan Anda sudah meletakkan file zip update ke dalam folder ini.
echo.
pause
exit /b 1

:found_zip
echo [OK] Berkas update terdeteksi: "%ZIP_FILE%"
echo [1/2] Mengekstrak dan memperbarui file sistem PosRonda...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '.' -Force"

if errorlevel 1 (
    color 0C
    echo [ERROR] Gagal mengekstrak %ZIP_FILE%!
    pause
    exit /b 1
)

echo [2/2] Memverifikasi berkas...
color 0A
echo.
echo ========================================================
echo   SUKSES! Semua file PosRonda berhasil diperbarui!
echo ========================================================
echo Anda bisa langsung menjalankan aplikasi seperti biasa
echo lewat 'run.bat' atau 'Jalankan_Tanpa_CMD.vbs'.
echo ========================================================
echo.
pause
