Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "INICIANDO BACKEND - COMEX ANALYZER" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir

if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✅ Ambiente virtual ativado" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Iniciando servidor na porta 8000..." -ForegroundColor Yellow
    Write-Host ""
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
} else {
    Write-Host "❌ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "Execute: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
}



