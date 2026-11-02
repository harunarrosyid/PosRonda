@echo off
cd /d "%~dp0"
title Buat Shortcut Desktop PosRonda Hub
color 0B

echo ========================================================
echo        MEMBUAT SHORTCUT POSRONDA HUB DI DESKTOP
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\PosRonda Hub.lnk'); $s.TargetPath = '%~dp0Jalankan_Tanpa_CMD.vbs'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll,14'; $s.Description = 'PosRonda Hub Autonomous CCTV Engine'; $s.Save()"

if errorlevel 1 (
    color 0C
    echo [ERROR] Gagal membuat shortcut di Desktop!
    pause
    exit /b 1
)

color 0A
echo.
echo ========================================================
echo   SUKSES! Shortcut 'PosRonda Hub' sudah ada di Desktop!
echo ========================================================
echo Sekarang Anda cukup klik ganda (double-click) icon
echo 'PosRonda Hub' di Desktop untuk langsung membukanya
echo tanpa jendela hitam CMD!
echo ========================================================
echo.
pause
