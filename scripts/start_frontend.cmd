@echo off
setlocal
cd /d "%~dp0.."
echo Iniciando frontend en http://127.0.0.1:5500
echo Mantenga esta ventana abierta.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_frontend.ps1"
echo.
echo El frontend se detuvo. Revise el mensaje anterior.
pause
