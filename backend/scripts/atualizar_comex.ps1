# Atualização mensal das tabelas de comex UF×NCM (MDIC) + tabelas derivadas.
# Executado pelo Agendador de Tarefas do Windows.
$ErrorActionPreference = "Continue"

$cred = "C:\Users\User\Desktop\Claude\liquid-receiver-483923-n6-c1b7eebd2b03.json"
$dir  = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend\scripts"
$log  = Join-Path $dir "atualizar_comex.log"

$env:GOOGLE_APPLICATION_CREDENTIALS = $cred
Set-Location $dir

$inicio = Get-Date

"==== Início: $inicio ====" | Out-File -FilePath $log -Append -Encoding utf8

# 1) Atualiza as tabelas UF×NCM a partir da Base dos Dados (janela automática:
#    últimos anos disponíveis na fonte). Sem argumentos = janela automática.
python atualizar_comex_uf_ncm.py *>> $log

# 2) Regenera as tabelas derivadas (estimativa ponderada + habilitação)
python criar_tabela_estimativa.py *>> $log

"==== Fim: $(Get-Date) (duração: $((Get-Date) - $inicio)) ====`n" | Out-File -FilePath $log -Append -Encoding utf8
