# Script PowerShell para iniciar o frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comex Analyzer - Iniciando Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$frontendDir = Join-Path $PSScriptRoot "frontend"

if (-not (Test-Path $frontendDir)) {
    Write-Host "[ERRO] Diretório frontend não encontrado!" -ForegroundColor Red
    exit 1
}

Set-Location $frontendDir

# Verificar node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] Instalando dependências..." -ForegroundColor Yellow
    npm install
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Falha ao instalar dependências!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando aplicação React..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend estará disponível em: " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Certifique-se de que o backend está rodando em: " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione CTRL+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Iniciar servidor React
npm start



