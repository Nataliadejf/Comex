tenparam(
    [string]$ServiceBaseUrl = $env:SERVICE_URL
)

if (-not $ServiceBaseUrl) {
    Write-Host "ERRO: defina SERVICE_URL como 'https://<host>' ou passe como parâmetro." -ForegroundColor Red
    exit 1
}

$endpoint = "$ServiceBaseUrl/api/coletar-empresas-base-dados"
Write-Host "Chamando $endpoint ..."

try {
    $resp = Invoke-RestMethod -Method Post -Uri $endpoint -TimeoutSec 120
    Write-Host "Resposta do endpoint:" -ForegroundColor Green
    $json = $resp | ConvertTo-Json -Depth 5
    Write-Host $json
} catch {
    Write-Host "Erro na requisição: $($_.Exception.Message)" -ForegroundColor Red
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
