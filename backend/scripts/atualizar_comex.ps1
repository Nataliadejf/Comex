# Atualização mensal das tabelas de comex UF×NCM (MDIC) + tabelas derivadas.
# Executado pelo Agendador de Tarefas do Windows.
$ErrorActionPreference = "Continue"

$cred = "C:\Users\User\Desktop\Claude\liquid-receiver-483923-n6-c1b7eebd2b03.json"
$dir  = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend\scripts"
$log  = Join-Path $dir "atualizar_comex.log"

$env:GOOGLE_APPLICATION_CREDENTIALS = $cred
Set-Location $dir

$ano    = (Get-Date).Year
$anoAnt = $ano - 1
$inicio = Get-Date

"==== Início: $inicio | anos: $anoAnt $ano ====" | Out-File -FilePath $log -Append -Encoding utf8

# 1) Baixa e atualiza as tabelas UF×NCM (ano anterior cobre dez.; ano atual, novos meses)
python atualizar_comex_uf_ncm.py $anoAnt $ano *>> $log

# 2) Regenera as tabelas derivadas (estimativa ponderada + habilitação)
python criar_tabela_estimativa.py *>> $log

"==== Fim: $(Get-Date) (duração: $((Get-Date) - $inicio)) ====`n" | Out-File -FilePath $log -Append -Encoding utf8
