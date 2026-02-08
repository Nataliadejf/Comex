# =============================================================================
# Script de atualização mensal - Coleta BigQuery + integração + cruzamento
# Usa ESCALA DE TEMPO (ano início a ano fim), não limite de linhas.
# =============================================================================
# Uso: .\AtualizarDadosMensal.ps1
#      .\AtualizarDadosMensal.ps1 -AnoInicio 2024 -AnoFim 2030
# =============================================================================

param(
    [int]$AnoInicio = 2024,
    [int]$AnoFim = 0   # 0 = ano atual
)

$ErrorActionPreference = "Stop"
$ProjetoDir = $PSScriptRoot
if ($AnoFim -le 0) { $AnoFim = [int](Get-Date -Format "yyyy") }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ATUALIZACAO MENSAL - COLETOR DE DADOS PUBLICOS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Escala de tempo: $AnoInicio a $AnoFim (sem limite de linhas)" -ForegroundColor White
Write-Host " Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjetoDir

# Executar coletor por escala de tempo (sem --limite)
python coletar_dados_publicos_standalone.py --ano-inicio $AnoInicio --ano-fim $AnoFim --integrar-banco --executar-cruzamento

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host " ERRO: Script de coleta retornou codigo $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " ATUALIZACAO MENSAL CONCLUIDA" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Proximo passo: validar no dashboard local ou no Render." -ForegroundColor White
Write-Host ""
