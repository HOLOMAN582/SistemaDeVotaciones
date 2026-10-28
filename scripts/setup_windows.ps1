$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pythonCommand) {
    $pythonLauncher = "py"
    $pythonArguments = @("-3")
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "No se encontró Python. Instala Python 3.11 o superior desde https://www.python.org/downloads/ y activa 'Add Python to PATH'."
    }
    $pythonLauncher = "python"
    $pythonArguments = @()
}

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "[1/4] Creando el entorno virtual..." -ForegroundColor Cyan
    & $pythonLauncher @pythonArguments -m venv venv
}

$python = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python no pudo crear el entorno virtual en $python."
}

Write-Host "[2/4] Actualizando pip..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip
Write-Host "[3/4] Instalando dependencias. Esto requiere Internet y puede tardar..." -ForegroundColor Cyan
& $python -m pip install -r requirements.txt
& $python -c "import uvicorn, fastapi, sqlalchemy; print('Dependencias principales verificadas.')"

if (-not (Test-Path ".\.env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[4/4] Se creó .env a partir de .env.example." -ForegroundColor Cyan
} else {
    Write-Host "[4/4] .env ya existe; se conserva la configuración actual." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Instalación terminada."
Write-Host "Backend:   .\scripts\start_backend.ps1"
Write-Host "Frontend:  .\scripts\start_frontend.ps1"
