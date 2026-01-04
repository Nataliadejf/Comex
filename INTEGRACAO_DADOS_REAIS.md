# 🔗 Integração com Dados Reais - Guia Completo

Este guia explica como configurar a integração com dados **REAIS** do portal Comex Stat.

## ✅ O Que Foi Configurado

1. ✅ **Scripts SQL** para MySQL/PostgreSQL gerados
2. ✅ **Cliente API Real** criado (`api_real_comex.py`)
3. ✅ **Script de Integração** criado (`integrar_api_real.py`)
4. ✅ **Remoção de dados de exemplo** implementada

## 📋 Como Obter Dados Reais

### Método 1: Download Manual (Mais Confiável)

1. **Acesse o Portal:**
   - URL: https://comexstat.mdic.gov.br
   - Navegue até: **Dados Abertos > Download**

2. **Baixe os Arquivos:**
   - Exportação (últimos 3 meses)
   - Importação (últimos 3 meses)
   - Formato: CSV

3. **Salve os Arquivos:**
   ```
   C:\Users\User\Desktop\Cursor\Projetos\data\raw\
   ```
   Ou:
   ```
   D:\NatFranca\raw\
   ```

4. **Processe os Arquivos:**
   ```powershell
   cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
   .\venv\Scripts\Activate.ps1
   python scripts/process_files.py
   ```

### Método 2: Download Automático

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
.\venv\Scripts\Activate.ps1
python scripts/integrar_api_real.py
```

Este script:
- Remove dados de exemplo
- Tenta baixar dados do portal automaticamente
- Salva arquivos CSV para processamento

### Método 3: API Oficial (Se Tiver Credenciais)

1. **Configure o `.env`:**
   ```env
   COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
   COMEX_STAT_API_KEY=sua_chave_aqui
   ```

2. **Execute:**
   ```powershell
   python scripts/integrar_api_real.py
   ```

## 🗄️ Configurar MySQL Workbench

### Passo 1: Gerar Scripts SQL

```powershell
python scripts/configurar_banco_mysql.py
```

Isso cria:
- `scripts/sql/create_tables_mysql.sql`
- `scripts/sql/create_tables_postgresql.sql`

### Passo 2: No MySQL Workbench

1. Abra o MySQL Workbench
2. Conecte ao servidor MySQL
3. Abra o arquivo: `scripts/sql/create_tables_mysql.sql`
4. Execute o script (Ctrl+Shift+Enter)
5. Verifique se as tabelas foram criadas

### Passo 3: Configurar Conexão

Edite `backend/.env`:

```env
# MySQL
DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/comex_analyzer

# Ou PostgreSQL
DATABASE_URL=postgresql://usuario:senha@localhost:5432/comex_analyzer
```

### Passo 4: Instalar Driver (Se Necessário)

```powershell
pip install pymysql  # Para MySQL
pip install psycopg2-binary  # Para PostgreSQL
```

## 🔄 Processo Completo de Integração

### 1. Remover Dados de Exemplo

```powershell
python scripts/integrar_api_real.py
```

### 2. Obter Dados Reais

**Opção A - Manual:**
- Baixe CSV do portal
- Salve em `data/raw/`

**Opção B - Automático:**
- Execute `integrar_api_real.py`

### 3. Processar Arquivos

```powershell
python scripts/process_files.py
```

### 4. Verificar Dados

```powershell
python -c "from database import get_db, OperacaoComex; from sqlalchemy import func; db = next(get_db()); total = db.query(func.count(OperacaoComex.id)).scalar(); print(f'Total: {total:,}')"
```

## 📊 Estrutura dos Dados Reais

Os arquivos CSV do Comex Stat contêm:

- **CO_NCM** - Código NCM (8 dígitos)
- **CO_UNID** - Código da unidade estatística
- **CO_PAIS** - Código do país
- **SG_UF_NCM** - UF
- **CO_VIA** - Via de transporte
- **VL_FOB** - Valor FOB (USD)
- **VL_FRETE** - Valor do frete
- **VL_SEGURO** - Valor do seguro
- **QT_ESTAT** - Quantidade estatística
- **KG_LIQUIDO** - Peso líquido (kg)
- **DT_REFERENCIA** - Data de referência

## 🔧 Configuração Avançada

### Usar MySQL ao Invés de SQLite

1. Configure MySQL Workbench
2. Execute script SQL
3. Atualize `.env`:
   ```env
   DATABASE_URL=mysql+pymysql://root:senha@localhost:3306/comex_analyzer
   ```

### Agendamento Mensal

**Windows Task Scheduler:**

1. Criar tarefa básica
2. Programa: `python`
3. Argumentos: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend\scripts\integrar_api_real.py`
4. Gatilho: Mensalmente (dia 1, às 2h)

## ⚠️ Importante

- ✅ Sempre use dados oficiais do portal Comex Stat
- ✅ Verifique a estrutura dos arquivos antes de processar
- ✅ Mantenha backups regulares do banco
- ✅ Processe arquivos em ordem cronológica

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
**Solução:** Verifique se os arquivos estão em `data/raw/`

### Erro: "Formato inválido"
**Solução:** Verifique se é CSV válido do Comex Stat

### Erro: "Banco não conecta"
**Solução:** Verifique URL de conexão no `.env`

### Erro: "Selenium não instalado"
**Solução:** Não é necessário para dados reais. Use download manual.

---

**Última atualização**: Janeiro 2025



