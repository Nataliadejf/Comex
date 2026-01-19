param(
    [string]$ServiceUrl = "https://comex-backend-gecp.onrender.com",
    [string]$ExcelPath = "",
    [int]$TimeoutSeconds = 300
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTE DE DEPLOY - COMEX BACKEND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ================================================================
# 1. AGUARDAR ANTES DE TESTAR (Warm-up)
# ================================================================
Write-Host "Aguardando 120 segundos para warm-up do serviço..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

# ================================================================
# 2. VALIDAR SISTEMA (Health Check)
# ================================================================
Write-Host "`n[1/3] Validando conexão ao banco de dados..." -ForegroundColor Blue

try {
    $validationUrl = "$ServiceUrl/validar-sistema"
    Write-Host "GET $validationUrl" -ForegroundColor Gray
    
    $response = Invoke-WebRequest -Uri $validationUrl -Method GET -UseBasicParsing -TimeoutSec $TimeoutSeconds
    $json = $response.Content | ConvertFrom-Json
    
    if ($json.status -eq "ok") {
        Write-Host "✅ Sistema validado com sucesso!" -ForegroundColor Green
        Write-Host "   Total de operações: $($json.banco_dados.total_registros.operacoes)" -ForegroundColor Green
        Write-Host "   Total de CNAE: $($json.banco_dados.total_registros.cnae)" -ForegroundColor Green
        Write-Host "   Exportações: $($json.banco_dados.total_registros.exportacoes)" -ForegroundColor Green
        Write-Host "   Importações: $($json.banco_dados.total_registros.importacoes)" -ForegroundColor Green
    } else {
        Write-Host "❌ Sistema retornou erro: $($json.status)" -ForegroundColor Red
        Write-Host $json | ConvertTo-Json
    }
} catch {
    Write-Host "❌ Erro ao validar sistema: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ================================================================
# 3. IMPORTAR EXCEL LOCAL (se fornecido)
# ================================================================
if ($ExcelPath -and (Test-Path $ExcelPath)) {
    Write-Host "`n[2/3] Importando dados localmente..." -ForegroundColor Blue
    Write-Host "Arquivo: $ExcelPath" -ForegroundColor Gray
    
    $env:DATABASE_URL = $env:DATABASE_URL
    if (-not $env:DATABASE_URL) {
        Write-Host "⚠️ Aviso: DATABASE_URL não está definido" -ForegroundColor Yellow
        Write-Host "   Use: `$env:DATABASE_URL = 'postgresql://...'" -ForegroundColor Yellow
    } else {
        try {
            $output = python importar_excel_local.py "$ExcelPath" --tipo comex 2>&1
            $lines = @($output) | Select-Object -First 30
            Write-Host $lines -ForegroundColor Green
            Write-Host "✅ Importação concluída" -ForegroundColor Green
        } catch {
            Write-Host "❌ Erro na importação: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "`n[2/3] Importação local não solicitada (--ExcelPath não fornecido)" -ForegroundColor Yellow
}

# ================================================================
# 4. VALIDAR NOVAMENTE
# ================================================================
Write-Host "`n[3/3] Validando sistema novamente..." -ForegroundColor Blue

try {
    $validationUrl = "$ServiceUrl/validar-sistema"
    $response = Invoke-WebRequest -Uri $validationUrl -Method GET -UseBasicParsing -TimeoutSec $TimeoutSeconds
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Validação final:" -ForegroundColor Green
    Write-Host "   Total de operações: $($json.banco_dados.total_registros.operacoes)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro na validação final: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "FIM DO TESTE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
