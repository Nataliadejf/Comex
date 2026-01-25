# Script para testar o coletor de dados públicos via API
# Execute: .\TESTAR_COLETOR_PUBLICO.ps1

# URL do backend no Render
$url = "https://comex-backend-gecp.onrender.com/api/coletar-dados-publicos"
$body = @{
    limite_por_fonte = 50
    integrar_banco = $true
    salvar_csv = $false
    salvar_json = $false
} | ConvertTo-Json

Write-Host "🔄 Testando endpoint de coleta de dados públicos..."
Write-Host "URL: $url"
Write-Host "Body: $body"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
    Write-Host "✅ Sucesso!" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "📊 Verificando status..."
try {
    $statusUrl = "https://comex-backend-gecp.onrender.com/api/coletar-dados-publicos/status"
    $status = Invoke-RestMethod -Uri $statusUrl -Method Get
    Write-Host ($status | ConvertTo-Json)
} catch {
    Write-Host "⚠️ Erro ao verificar status: $_"
}
