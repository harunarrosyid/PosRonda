@echo off
cd /d "%~dp0"
title Aktifkan Auto-Start PosRonda Hub (Mati Lampu Recovery)
color 0B

echo ========================================================
echo   MENGAKTIFKAN AUTO-START SAAT WINDOWS MENYALA (BOOT)
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $startup = [Environment]::GetFolderPath('Startup'); $s = $ws.CreateShortcut($startup + '\PosRonda Hub.lnk'); $s.TargetPath = '%~dp0Jalankan_Tanpa_CMD.vbs'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll,14'; $s.Description = 'PosRonda Hub Auto-Start'; $s.Save()"

if errorlevel 1 (
    color 0C
    echo [ERROR] Gagal membuat shortcut di folder Startup Windows!
    pause
    exit /b 1
)

color 0A
echo.
echo ========================================================
echo   SUKSES! AUTO-START WINDOWS TELAH DIAKTIFKAN!
echo ========================================================
echo.
echo Setiap kali laptop ThinkPad X230 menyala / restart
echo (misal pasca listrik padam / mati lampu):
echo - Program PosRonda Hub akan OTOMATIS BERJALAN!
echo - Berjalan langsung tanpa jendela hitam CMD yang mengganggu.
echo.
echo --------------------------------------------------------
echo TIPS PENTING (Agar Otomatis Masuk Tanpa Ketik Password):
echo Jika laptop Anda memiliki password login Windows:
echo 1. Tekan tombol Windows + R, ketik: netplwiz lalu Enter.
echo 2. Hilangkan centang pada:
echo    "Users must enter a user name and password to use this computer"
echo 3. Klik Apply, masukkan password Anda sekali saja, lalu OK.
echo Dengan begitu, laptop akan otomatis login saat listrik nyala!
echo ========================================================
echo.
pause
