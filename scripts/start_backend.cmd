@echo off
setlocal
cd /d "%~dp0.."
echo Iniciando backend en http://127.0.0.1:8000
echo Mantenga esta ventana abierta.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_backend.ps1"
echo.
echo El backend se detuvo. Revise el mensaje anterior.
pause
