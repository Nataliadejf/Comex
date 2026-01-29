# =============================================================================
# Script: Executar_Coleta_E_Cruzamento.ps1
# Uso: .\Executar_Coleta_E_Cruzamento.ps1 [ -ApenasValidar ] [ -Limite 5000 ] [ -ExecutarCruzamento ] [ -ApenasBigQuery ]
# =============================================================================

param(
    [switch]$ApenasValidar,      # Só roda validar_bigquery.py
    [int]$Limite = 5000,        # Limite de registros por fonte
    [switch]$ExecutarCruzamento, # Após integrar, executa cruzamento NCM+UF
    [switch]$ApenasBigQuery,    # Coleta só do BigQuery (não DOU)
    [switch]$SalvarCsv          # Salva resultado em CSV
)

$ErrorActionPreference = "Stop"
$projetoDir = $PSScriptRoot
if (-not $projetoDir) { $projetoDir = Get-Location }

Set-Location $projetoDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " COLETOR PUBLICO + CRUZAMENTO NCM/UF" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Pasta: $projetoDir" -ForegroundColor Gray
Write-Host ""

# 1. Verificar .env
$envPath = Join-Path $projetoDir ".env"
if (-not (Test-Path $envPath)) {
    Write-Host "[AVISO] Arquivo .env nao encontrado." -ForegroundColor Yellow
    Write-Host " Crie o arquivo .env com GOOGLE_APPLICATION_CREDENTIALS_JSON (e DATABASE_URL se for integrar no banco)." -ForegroundColor Yellow
    Write-Host " Veja PASSO_A_PASSO_COLETOR_E_CRUZAMENTO.md" -ForegroundColor Yellow
    $continuar = Read-Host " Continuar mesmo assim? (s/n)"
    if ($continuar -ne "s") { exit 1 }
} else {
    Write-Host "[OK] Arquivo .env encontrado." -ForegroundColor Green
}

# 2. Validar BigQuery (sempre ou só se -ApenasValidar)
Write-Host ""
Write-Host "--- Validando BigQuery ---" -ForegroundColor Cyan
try {
    python validar_bigquery.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] validar_bigquery.py falhou. Verifique GOOGLE_APPLICATION_CREDENTIALS_JSON no .env" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERRO] $_" -ForegroundColor Red
    exit 1
}

if ($ApenasValidar) {
    Write-Host ""
    Write-Host " Validacao concluida (modo -ApenasValidar)." -ForegroundColor Green
    exit 0
}

# 3. Montar argumentos do script Python
$argList = @()
$argList += "--limite", $Limite
$argList += "--integrar-banco"
if ($ExecutarCruzamento) { $argList += "--executar-cruzamento" }
if ($SalvarCsv)          { $argList += "--salvar-csv" }
if ($ApenasBigQuery)    { $argList += "--apenas-bigquery" }

Write-Host ""
Write-Host "--- Executando coleta ---" -ForegroundColor Cyan
Write-Host " Comando: python coletar_dados_publicos_standalone.py $($argList -join ' ')" -ForegroundColor Gray
Write-Host ""

try {
    & python coletar_dados_publicos_standalone.py @argList
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Coleta/cruzamento falhou (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "[ERRO] $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " CONCLUIDO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
