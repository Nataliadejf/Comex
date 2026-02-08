# =============================================================================
# Sobe BACKEND em nova janela e FRONTEND neste terminal.
# Uso: na pasta projeto_comex execute: .\SubirDashboardLocalCompleto.ps1
#      Se estiver em backend/, execute antes: cd ..
# =============================================================================
$ErrorActionPreference = "Stop"
$ProjetoDir = $PSScriptRoot
$BackendDir = Join-Path $ProjetoDir "backend"
$FrontendDir = Join-Path $ProjetoDir "frontend"
$ComexDataDir = Join-Path $ProjetoDir "comex_data"
$ComexDbDir = Join-Path $ComexDataDir "database"
$Port = if ($env:PORT) { $env:PORT } else { "8000" }

if ((Split-Path -Leaf (Get-Location)) -eq "backend") {
    Set-Location $ProjetoDir
}

# Garantir diretório do banco
if (-not (Test-Path $ComexDbDir)) {
    New-Item -ItemType Directory -Path $ComexDbDir -Force | Out-Null
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DASHBOARD LOCAL - Backend + Frontend" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1) Iniciar backend em nova janela (cwd deve ser backend para imports)
if (-not (Test-Path (Join-Path $BackendDir "run.py"))) {
    Write-Host "ERRO: backend\run.py nao encontrado. Execute na pasta projeto_comex." -ForegroundColor Red
    exit 1
}
Write-Host "Iniciando BACKEND em nova janela (porta $Port)..." -ForegroundColor Green
$backendCmd = "Set-Location '$BackendDir'; `$env:PORT='$Port'; python run.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Write-Host "Aguardando 6 segundos para o backend iniciar..." -ForegroundColor Gray
Start-Sleep -Seconds 6

# 2) Iniciar frontend
if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Host "ERRO: Frontend nao encontrado em: $FrontendDir" -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando FRONTEND (porta 3000)..." -ForegroundColor Green
Write-Host " Dashboard:  http://localhost:3000/dashboard" -ForegroundColor Yellow
Write-Host " Backend:   http://localhost:${Port}/docs" -ForegroundColor Gray
Write-Host " Debug:     http://localhost:${Port}/dashboard/debug/empresas" -ForegroundColor Gray
Write-Host " (Frontend usa REACT_APP_API_URL do .env.development = localhost:8000)" -ForegroundColor DarkGray
Write-Host ""

Set-Location $FrontendDir
npm start
