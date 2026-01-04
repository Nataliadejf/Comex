# 🚀 Guia Completo: Popular Dashboard com Dados

Este guia explica como popular o dashboard com dados de exportação e importação do Comex Stat.

## ✅ Pré-requisitos Verificados

- ✅ **Espaço em Disco**: Verificado automaticamente
- ✅ **Capacidade de Processamento**: Verificado automaticamente
- ✅ **Banco de Dados**: Configurado automaticamente

## 📋 Processo Completo

### Opção 1: Script Automático Completo (Recomendado)

Execute o script que faz tudo automaticamente:

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/popular_dashboard_completo.py
```

Este script:
1. ✅ Verifica espaço em disco
2. ✅ Verifica capacidade de processamento
3. ✅ Configura o banco de dados
4. ✅ Tenta download automático (se mapeado)
5. ✅ Processa arquivos existentes

### Opção 2: Download Manual + Processamento

#### Passo 1: Baixar Arquivos Manualmente

1. Acesse: https://comexstat.mdic.gov.br
2. Navegue até a seção de downloads
3. Baixe os arquivos CSV de:
   - **Exportação** (últimos 3 meses)
   - **Importação** (últimos 3 meses)
4. Salve os arquivos em uma das pastas:
   - `D:\comex\2025\`
   - `D:\NatFranca\raw\`
   - `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend\data\raw\`

**Formato de nome esperado:**
- `EXP_2025_01.csv` (Exportação de Janeiro 2025)
- `IMP_2025_01.csv` (Importação de Janeiro 2025)
- Ou: `EXP_2025.csv`, `IMP_2025.csv`

#### Passo 2: Processar Arquivos

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/process_files.py
```

### Opção 3: Download Automático (Requer Mapeamento)

#### Passo 1: Mapear Botões do Site

Consulte: `backend/scripts/MAPEAMENTO_BOTOES_COMEX.md`

#### Passo 2: Atualizar Script de Download

Edite `backend/scripts/download_comex_automatico.py` com os seletores corretos.

#### Passo 3: Executar Download

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/download_comex_automatico.py --months 3
```

## 🔧 Scripts Disponíveis

### 1. Configurar Banco
```powershell
python scripts/configurar_banco.py
```
- Inicializa o banco
- Verifica estrutura
- Conta registros existentes

### 2. Processar Arquivos CSV
```powershell
python scripts/process_files.py
```
- Procura arquivos CSV nas pastas configuradas
- Processa e importa para o banco
- Evita duplicatas

### 3. Download Automático
```powershell
python scripts/download_comex_automatico.py --months 3 --tipo Ambos
```
- Faz download automático (requer mapeamento)
- Suporta Selenium ou Playwright

### 4. Processo Completo
```powershell
python scripts/popular_dashboard_completo.py
```
- Executa todo o processo automaticamente

## 📊 Verificar Resultados

### Verificar Registros no Banco

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); print(f'Total: {db.query(func.count(OperacaoComex.id)).scalar():,}')"
```

### Acessar Dashboard

1. Inicie o backend: `python run.py`
2. Inicie o frontend: `npm start` (na pasta frontend)
3. Acesse: http://localhost:3000

## 🔄 Agendamento Mensal

### Windows Task Scheduler

1. Abra o Agendador de Tarefas
2. Criar Tarefa Básica
3. Configurar:
   - **Nome**: Popular Dashboard Comex
   - **Gatilho**: Mensalmente (dia 1, às 2h)
   - **Ação**: Executar programa
   - **Programa**: `python`
   - **Argumentos**: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend\scripts\popular_dashboard_completo.py`
   - **Iniciar em**: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend`

### PowerShell Script de Agendamento

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\popular_dashboard_completo.py" -WorkingDirectory "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend"
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 2am
Register-ScheduledTask -TaskName "PopularDashboardComex" -Action $action -Trigger $trigger
```

## ⚠️ Troubleshooting

### Erro: "Nenhum arquivo CSV encontrado"
**Solução**: Verifique se os arquivos estão nas pastas corretas:
- `D:\comex\2025\`
- `D:\NatFranca\raw\`
- `settings.data_dir / "raw"`

### Erro: "Espaço em disco insuficiente"
**Solução**: Libere espaço ou altere `DATA_DIR` no `.env`

### Erro: "Banco de dados corrompido"
**Solução**: Execute `python scripts/recriar_banco.py`

### Erro: "Download automático não funciona"
**Solução**: 
1. Verifique se Selenium/Playwright está instalado
2. Mapeie os botões do site corretamente
3. Use download manual como alternativa

## 📝 Checklist Final

- [ ] Espaço em disco verificado
- [ ] Banco de dados configurado
- [ ] Arquivos CSV baixados (manual ou automático)
- [ ] Arquivos processados
- [ ] Registros importados no banco
- [ ] Dashboard acessível e funcionando
- [ ] Agendamento mensal configurado (opcional)

## 🎯 Próximos Passos

Após popular o dashboard:

1. ✅ Acesse http://localhost:3000
2. ✅ Use os filtros para explorar os dados
3. ✅ Exporte relatórios conforme necessário
4. ✅ Configure agendamento mensal para atualizações automáticas

---

**Última atualização**: Janeiro 2025



