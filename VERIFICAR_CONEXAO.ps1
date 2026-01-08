# Script PowerShell para verificar e corrigir conexão
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERIFICAÇÃO E CORREÇÃO DE CONEXÃO COM BACKEND" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar arquivo .env
Write-Host "[1/4] Verificando arquivo .env do frontend..." -ForegroundColor Yellow
$envPath = "frontend\.env"
if (Test-Path $envPath) {
    Write-Host "   ✅ Arquivo .env encontrado" -ForegroundColor Green
    Write-Host "   Conteúdo:" -ForegroundColor Gray
    Get-Content $envPath
} else {
    Write-Host "   ⚠️ Arquivo .env não encontrado. Criando..." -ForegroundColor Yellow
    "REACT_APP_API_URL=https://comex-tsba.onrender.com" | Out-File -FilePath $envPath -Encoding UTF8
    Write-Host "   ✅ Arquivo .env criado" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/4] Verificando se backend está acessível no Render..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://comex-tsba.onrender.com/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "   ✅ Backend está acessível (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "   Resposta:" -ForegroundColor Gray
    $response.Content
} catch {
    Write-Host "   ❌ Backend não está acessível" -ForegroundColor Red
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Verifique:" -ForegroundColor Yellow
    Write-Host "      - Se o serviço está rodando no Render Dashboard" -ForegroundColor Gray
    Write-Host "      - Se há erros nos logs do Render" -ForegroundColor Gray
    Write-Host "      - Se o health check está funcionando" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[3/4] Verificando configuração do frontend..." -ForegroundColor Yellow
if (Test-Path $envPath) {
    $content = Get-Content $envPath -Raw
    if ($content -match "REACT_APP_API_URL") {
        Write-Host "   ✅ Variável REACT_APP_API_URL encontrada" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Variável não encontrada. Adicionando..." -ForegroundColor Yellow
        "REACT_APP_API_URL=https://comex-tsba.onrender.com" | Add-Content -Path $envPath -Encoding UTF8
        Write-Host "   ✅ Variável adicionada" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[4/4] Verificando se frontend está rodando..." -ForegroundColor Yellow
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "   ⚠️ Porta 3000 já está em uso" -ForegroundColor Yellow
    Write-Host "   💡 Pare o processo antes de iniciar novamente" -ForegroundColor Gray
} else {
    Write-Host "   ✅ Porta 3000 está livre" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "1. Se o backend não está acessível:" -ForegroundColor White
Write-Host "   - Acesse: https://dashboard.render.com" -ForegroundColor Gray
Write-Host "   - Verifique se o serviço 'comex-backend' está rodando" -ForegroundColor Gray
Write-Host "   - Verifique os logs para erros" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Para iniciar o frontend localmente:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Ou execute: INICIAR_FRONTEND.bat" -ForegroundColor White
Write-Host ""
Write-Host "4. Se ainda não funcionar, tente usar backend local:" -ForegroundColor White
Write-Host "   - Execute: INICIAR_BACKEND.bat" -ForegroundColor Gray
Write-Host "   - Altere frontend\.env para: REACT_APP_API_URL=http://localhost:8000" -ForegroundColor Gray
Write-Host ""


