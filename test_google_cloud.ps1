param(
    [string]$ServiceBaseUrl = $env:SERVICE_URL
)

if (-not $ServiceBaseUrl) {
    Write-Host "ERRO: defina SERVICE_URL como 'https://<host>' ou passe como parâmetro." -ForegroundColor Red
    exit 1
}

$endpoint = "$ServiceBaseUrl/api/testar-google-cloud"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧪 TESTE DE CREDENCIAIS GOOGLE CLOUD" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 Endpoint: $endpoint" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $endpoint -Method Get -TimeoutSec 30 -ErrorAction Stop
    
    Write-Host "✅ Resposta recebida:" -ForegroundColor Green
    Write-Host ""
    
    $json = $response | ConvertTo-Json -Depth 5
    Write-Host $json -ForegroundColor White
    Write-Host ""
    
    if ($response.status -eq "ok") {
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✅ TESTE PASSOU!" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Resumo:" -ForegroundColor Cyan
        Write-Host "   - Credenciais encontradas: $($response.credenciais_encontradas)" -ForegroundColor White
        Write-Host "   - Tipo: $($response.tipo_credenciais)" -ForegroundColor White
        if ($response.projeto_bigquery) {
            Write-Host "   - Projeto BigQuery: $($response.projeto_bigquery)" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "💡 Você pode agora testar o endpoint de coleta:" -ForegroundColor Yellow
        Write-Host "   POST $ServiceBaseUrl/api/coletar-empresas-base-dados" -ForegroundColor Cyan
    } elseif ($response.status -eq "aviso") {
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "  ⚠️  AVISO" -ForegroundColor Yellow
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        Write-Host $response.mensagem -ForegroundColor Yellow
    } else {
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "  ❌ TESTE FALHOU" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host ""
        Write-Host "Erro: $($response.erro)" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Verifique:" -ForegroundColor Yellow
        Write-Host "   1. Se GOOGLE_APPLICATION_CREDENTIALS_JSON está configurada no Render" -ForegroundColor White
        Write-Host "   2. Se o JSON está completo e válido" -ForegroundColor White
        Write-Host "   3. Se a BigQuery API está habilitada no Google Cloud" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Erro na requisição:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Resposta:" -ForegroundColor Yellow
            Write-Host $responseBody -ForegroundColor White
        } catch {
            Write-Host "Não foi possível ler a resposta" -ForegroundColor Yellow
        }
    }
    
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ TESTE CONCLUÍDO" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
