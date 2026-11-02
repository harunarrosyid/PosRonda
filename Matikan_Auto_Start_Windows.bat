@echo off
cd /d "%~dp0"
title Matikan Auto-Start PosRonda Hub
color 0E

echo ========================================================
echo   MENONAKTIFKAN AUTO-START POSRONDA HUB SAAT WINDOWS MENYALA
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$startup = [Environment]::GetFolderPath('Startup'); $p1 = $startup + '\PosRonda Hub.lnk'; if (Test-Path $p1) { Remove-Item $p1 -Force }; $p2 = $startup + '\CCTV YouTube Hub.lnk'; if (Test-Path $p2) { Remove-Item $p2 -Force }; Write-Host 'Shortcut berhasil dihapus dari Startup.'"

color 0A
echo.
echo ========================================================
echo   SUKSES! Auto-Start saat Windows boot telah dimatikan.
echo ========================================================
echo.
pause
