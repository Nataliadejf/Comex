# Redireciona para o script na raiz do projeto (para rodar a partir da pasta backend)
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentScript = Join-Path (Split-Path -Parent $ScriptRoot) "SubirDashboardLocal.ps1"
if (Test-Path $ParentScript) {
    Set-Location (Split-Path -Parent $ScriptRoot)
    & $ParentScript
} else {
    Write-Host "Execute a partir da pasta do projeto: cd projeto_comex; .\SubirDashboardLocal.ps1" -ForegroundColor Yellow
    Write-Host "Ou suba o backend aqui: python run.py" -ForegroundColor Yellow
}
