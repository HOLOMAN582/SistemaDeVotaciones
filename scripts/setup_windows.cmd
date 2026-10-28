@echo off
setlocal
cd /d "%~dp0.."
echo.
echo ============================================
echo   Sistema de Votaciones - Instalacion
echo ============================================
echo.
echo Esta ventana mostrara cualquier error. No la cierres.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
if errorlevel 1 (
    echo.
    echo LA INSTALACION TERMINO CON ERROR.
    echo Revisa el mensaje anterior y verifica que Python e Internet funcionen.
) else (
    echo.
    echo INSTALACION TERMINADA CORRECTAMENTE.
)
echo.
pause
