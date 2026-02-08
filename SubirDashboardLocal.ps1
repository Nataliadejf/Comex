# =============================================================================
# Sobe o BACKEND local (este terminal). NAO coleta dados - usa o banco existente.
# Em outro terminal, suba o frontend: cd frontend; npm start
# =============================================================================
# Uso: .\SubirDashboardLocal.ps1
#      Se a porta 8000 estiver em uso: $env:PORT=8001; .\SubirDashboardLocal.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjetoDir = $PSScriptRoot
$BackendDir = Join-Path $ProjetoDir "backend"
$FrontendDir = Join-Path $ProjetoDir "frontend"
$ComexDataDir = Join-Path $ProjetoDir "comex_data"
$ComexDbDir = Join-Path $ComexDataDir "database"
$Port = if ($env:PORT) { $env:PORT } else { "8000" }

# Se executado de dentro de backend/, voltar para a raiz
if ((Split-Path -Leaf (Get-Location)) -eq "backend") {
    Set-Location (Split-Path -Parent (Get-Location))
}
# Garantir diretório do banco (backend usa projeto_comex/comex_data/database/)
if (-not (Test-Path $ComexDbDir)) {
    New-Item -ItemType Directory -Path $ComexDbDir -Force | Out-Null
    Write-Host "Criado diretorio: $ComexDbDir" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BACKEND LOCAL (porta $Port)" -ForegroundColor Cyan
Write-Host " Banco: $ComexDbDir\comex.db" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Em OUTRO terminal, para o frontend:" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm start" -ForegroundColor White
Write-Host " Depois acesse: http://localhost:3000/dashboard" -ForegroundColor Green
Write-Host " Para atualizar dependencias do frontend: .\AtualizarDashboardLocal.ps1" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Se a porta $Port estiver em uso, feche o processo ou use:" -ForegroundColor Gray
Write-Host "   `$env:PORT=8001; .\SubirDashboardLocal.ps1" -ForegroundColor Gray
Write-Host "   (e no frontend .env.development use REACT_APP_API_URL=http://localhost:8001)" -ForegroundColor Gray
Write-Host " Se estiver na pasta backend, execute antes: cd .." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $BackendDir
$env:PORT = $Port
if (-not (Test-Path "run.py")) {
    Write-Host "ERRO: run.py nao encontrado. Execute este script na pasta projeto_comex." -ForegroundColor Red
    exit 1
}
python run.py
