$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $projectRoot "frontend"
$python = Join-Path $projectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "No existe el entorno virtual. Ejecuta .\scripts\setup_windows.ps1 primero."
}

Set-Location $frontend
& $python -m http.server 5500 --bind 127.0.0.1
