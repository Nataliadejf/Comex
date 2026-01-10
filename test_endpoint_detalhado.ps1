param(
    [string]$ServiceBaseUrl = $env:SERVICE_URL
)

if (-not $ServiceBaseUrl) {
    Write-Host "ERRO: defina SERVICE_URL como 'https://<host>' ou passe como parâmetro." -ForegroundColor Red
    exit 1
}

$endpoint = "$ServiceBaseUrl/api/coletar-empresas-base-dados"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧪 TESTE DETALHADO DO ENDPOINT" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 Endpoint: $endpoint" -ForegroundColor Yellow
Write-Host "⏱️  Timeout: 300 segundos (5 minutos)" -ForegroundColor Yellow
Write-Host ""

# Testar se o endpoint está acessível primeiro
Write-Host "1️⃣ Verificando se o endpoint está acessível..." -ForegroundColor Cyan
try {
    $testResp = Invoke-WebRequest -Uri "$ServiceBaseUrl/docs" -Method Get -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ Servidor está online" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Não foi possível verificar o servidor: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2️⃣ Chamando endpoint de coleta..." -ForegroundColor Cyan
Write-Host "   ⏳ Isso pode demorar vários minutos..." -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date

try {
    # Usar Invoke-WebRequest para ter mais controle sobre a resposta
    $response = Invoke-WebRequest -Uri $endpoint -Method Post -TimeoutSec 300 -ErrorAction Stop
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "   ✅ Resposta recebida em $([math]::Round($duration, 2)) segundos" -ForegroundColor Green
    Write-Host ""
    Write-Host "   📊 Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    Write-Host "   📋 Content Length: $($response.Content.Length) bytes" -ForegroundColor Cyan
    Write-Host ""
    
    if ($response.Content) {
        Write-Host "   📄 Conteúdo da resposta:" -ForegroundColor Green
        Write-Host "   " -NoNewline
        try {
            $json = $response.Content | ConvertFrom-Json
            $json | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor White
        } catch {
            Write-Host $response.Content -ForegroundColor White
        }
    } else {
        Write-Host "   ⚠️  Resposta vazia recebida" -ForegroundColor Yellow
    }
    
} catch {
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "   ❌ Erro após $([math]::Round($duration, 2)) segundos" -ForegroundColor Red
    Write-Host ""
    Write-Host "   🔴 Tipo de erro: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "   🔴 Mensagem: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   🔴 Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "   📄 Resposta do servidor:" -ForegroundColor Yellow
            Write-Host "   $responseBody" -ForegroundColor White
        } catch {
            Write-Host "   ⚠️  Não foi possível ler a resposta do servidor" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "   💡 Dicas:" -ForegroundColor Cyan
    Write-Host "      - Verifique os logs do Render" -ForegroundColor White
    Write-Host "      - Verifique se GOOGLE_APPLICATION_CREDENTIALS está configurada" -ForegroundColor White
    Write-Host "      - A query pode estar demorando mais que 5 minutos" -ForegroundColor White
    
    exit 1
}

Write-Host ""
Write-Host "3️⃣ Verificando dados no banco..." -ForegroundColor Cyan
Write-Host ""

if (-not $env:DATABASE_URL) {
    Write-Host "   ⚠️  DATABASE_URL não definida. Usando configuração padrão." -ForegroundColor Yellow
} else {
    Write-Host "   ✅ DATABASE_URL configurada" -ForegroundColor Green
}

try {
    Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
    python check_db.py
    Pop-Location
} catch {
    Write-Host "   ❌ Erro ao executar check_db.py: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ TESTE CONCLUÍDO" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
