# =============================================================================
# Atualiza o ambiente do dashboard local (dependências do frontend e dicas).
# Execute na pasta projeto_comex: .\AtualizarDashboardLocal.ps1
# =============================================================================
$ErrorActionPreference = "Stop"
$ProjetoDir = $PSScriptRoot
$FrontendDir = Join-Path $ProjetoDir "frontend"
$BackendDir = Join-Path $ProjetoDir "backend"

if ((Split-Path -Leaf (Get-Location)) -eq "backend") {
    Set-Location $ProjetoDir
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ATUALIZAR DASHBOARD LOCAL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1) Frontend: npm install
if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Host "ERRO: frontend\package.json nao encontrado. Execute na pasta projeto_comex." -ForegroundColor Red
    exit 1
}
Write-Host "Instalando/atualizando dependencias do frontend..." -ForegroundColor Green
Set-Location $FrontendDir
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: npm install retornou erro." -ForegroundColor Yellow
}
Set-Location $ProjetoDir

# 2) Verificar .env.development
$envDev = Join-Path $FrontendDir ".env.development"
if (Test-Path $envDev) {
    $content = Get-Content $envDev -Raw
    if ($content -match "REACT_APP_API_URL=http://localhost:8000") {
        Write-Host "OK: .env.development aponta para backend local (porta 8000)." -ForegroundColor Green
    } else {
        Write-Host "Dica: em frontend\.env.development use REACT_APP_API_URL=http://localhost:8000 para o backend local." -ForegroundColor Yellow
    }
} else {
    Write-Host "Criando frontend\.env.development com REACT_APP_API_URL=http://localhost:8000" -ForegroundColor Yellow
    Set-Content -Path $envDev -Value "# Backend local`nREACT_APP_API_URL=http://localhost:8000" -Encoding UTF8
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Para subir o dashboard:" -ForegroundColor White
Write-Host "   .\SubirDashboardLocalCompleto.ps1" -ForegroundColor Yellow
Write-Host " Ou em dois terminais:" -ForegroundColor White
Write-Host "   Terminal 1: .\SubirDashboardLocal.ps1        (backend)" -ForegroundColor Gray
Write-Host "   Terminal 2: cd frontend; npm start           (frontend)" -ForegroundColor Gray
Write-Host " Acesse: http://localhost:3000/dashboard" -ForegroundColor Green
Write-Host " Debug empresas: http://localhost:8000/dashboard/debug/empresas" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
