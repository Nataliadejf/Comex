param(
    [string]$ServiceBaseUrl = $env:SERVICE_URL
)

if (-not $ServiceBaseUrl) {
    Write-Host "ERRO: defina SERVICE_URL como 'https://<host>' ou passe como parâmetro." -ForegroundColor Red
    exit 1
}

$endpoint = "$ServiceBaseUrl/api/coletar-empresas-base-dados"
Write-Host "Chamando $endpoint ..."

try {
    Write-Host "⏳ Aguardando resposta (pode demorar vários minutos)..." -ForegroundColor Yellow
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -TimeoutSec 300 -ErrorAction Stop
    Write-Host "`n✅ Resposta recebida!" -ForegroundColor Green
    Write-Host "Resposta do endpoint:" -ForegroundColor Green
    if ($resp) {
        $json = $resp | ConvertTo-Json -Depth 5
        Write-Host $json
    } else {
        Write-Host "⚠️ Resposta vazia recebida" -ForegroundColor Yellow
    }
} catch {
    Write-Host "`n❌ Erro na requisição:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Detalhes:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
    }
    Write-Host "`n💡 Dica: Verifique os logs do Render para mais detalhes" -ForegroundColor Cyan
    exit 1
}

# Executa o check_db.py para verificar registros no banco
Write-Host "`nVerificando dados no banco de dados..." -ForegroundColor Cyan
if (-not $env:DATABASE_URL) {
    Write-Host "Aviso: variável DATABASE_URL não definida. O script check_db.py tentará usar o ambiente atual." -ForegroundColor Yellow
} else {
    Write-Host "Usando DATABASE_URL do ambiente." -ForegroundColor Green
}

try {
    python check_db.py
} catch {
    Write-Host "Erro ao executar check_db.py: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nFim do script." -ForegroundColor Cyan
