# Script PowerShell para iniciar o backend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comex Analyzer - Iniciando Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"

if (-not (Test-Path $backendDir)) {
    Write-Host "[ERRO] Diretório backend não encontrado!" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir

# Verificar ambiente virtual
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[INFO] Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv
    
    if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
        Write-Host "[ERRO] Falha ao criar ambiente virtual!" -ForegroundColor Red
        exit 1
    }
}

# Ativar ambiente virtual
Write-Host "[INFO] Ativando ambiente virtual..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

# Instalar dependências se necessário
Write-Host "[INFO] Verificando dependências..." -ForegroundColor Green
pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando servidor FastAPI..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend estará disponível em: " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Green
Write-Host "Documentação da API: " -NoNewline
Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione CTRL+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Iniciar servidor
python run.py



