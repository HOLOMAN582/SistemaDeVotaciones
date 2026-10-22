$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$python = Join-Path $projectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "No existe el entorno virtual. Ejecuta .\scripts\setup_windows.ps1 primero."
}

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
