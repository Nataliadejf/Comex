# =============================================================================
# Script para commit, push e deploy (Render detecta push e faz deploy)
# =============================================================================
# Uso: .\DeployCommitPush.ps1
#      .\DeployCommitPush.ps1 -Mensagem "feat: nova funcionalidade"
# =============================================================================

param(
    [string]$Mensagem = "chore: atualizacao coleta, graficos e scripts"
)

$ErrorActionPreference = "Stop"
$ProjetoDir = $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " COMMIT + PUSH + DEPLOY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Mensagem: $Mensagem" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjetoDir

Write-Host " [1/4] Status do repositorio..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host " [2/4] Adicionando alteracoes (git add -A)..." -ForegroundColor Yellow
git add -A
Write-Host ""

Write-Host " [3/4] Commit..." -ForegroundColor Yellow
git commit -m $Mensagem
if ($LASTEXITCODE -ne 0) {
    Write-Host " Nada para commitar ou commit falhou. Continuando com push..." -ForegroundColor Yellow
}
Write-Host ""

Write-Host " [4/4] Push para origin main..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host " ERRO: git push falhou (verifique remoto e branch)." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " COMMIT E PUSH CONCLUIDOS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " O Render vai detectar as mudancas e fazer deploy automaticamente." -ForegroundColor White
Write-Host " Acompanhe em: https://dashboard.render.com" -ForegroundColor White
Write-Host " Tempo estimado: Backend 5-10 min, Frontend 3-5 min." -ForegroundColor White
Write-Host ""
