$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    throw "No se encontró el launcher 'py'. Instala Python 3.11 o superior y vuelve a intentarlo."
}

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creando el entorno virtual..."
    & py -3 -m venv venv
}

$python = Join-Path $projectRoot "venv\Scripts\python.exe"
Write-Host "Instalando dependencias..."
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creó .env a partir de .env.example."
}

Write-Host ""
Write-Host "Instalación terminada."
Write-Host "Backend:   .\scripts\start_backend.ps1"
Write-Host "Frontend:  .\scripts\start_frontend.ps1"
