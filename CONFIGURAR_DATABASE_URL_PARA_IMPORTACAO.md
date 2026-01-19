# 🔧 Configurar DATABASE_URL para Importação no Render

## ⚠️ Problema Identificado

O script `importar_excel_local.py` está importando para o banco **SQLite local** (82.540 registros), mas o **Render usa PostgreSQL** que está vazio (0 registros).

## ✅ Solução: Configurar DATABASE_URL do Render

### Passo 1: Obter a URL do PostgreSQL do Render

1. Acesse: https://dashboard.render.com
2. Vá em **PostgreSQL** → Seu banco de dados
3. Clique em **"Connections"** ou **"Info"**
4. Copie a **"Internal Database URL"**
   - Formato: `postgresql://usuario:senha@host:porta/database`

### Passo 2: Configurar no Script

**Opção A: Variável de Ambiente (Recomendado)**

No PowerShell, antes de executar o script:

```powershell
# Substitua pela URL real do seu PostgreSQL do Render
$env:DATABASE_URL = "postgresql://usuario:senha@host:porta/database"

# Depois execute o script
python importar_excel_local.py "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
```

**Opção B: Arquivo .env**

Crie um arquivo `.env` na raiz do projeto:

```
DATABASE_URL=postgresql://usuario:senha@host:porta/database
```

O script lerá automaticamente do `.env`.

### Passo 3: Verificar Conexão

Antes de importar, teste a conexão:

```powershell
python -c "import os; from pathlib import Path; import sys; sys.path.insert(0, 'backend'); from database.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); result = db.execute(text('SELECT COUNT(*) FROM operacoes_comex')); print(f'Registros no banco: {result.scalar()}'); db.close()"
```

Se mostrar **0 registros**, está conectado ao PostgreSQL do Render (correto para primeira importação).

## 📋 Ordem de Execução Correta

1. **Configurar DATABASE_URL** (Passo 2 acima)
2. **Importar Excel Comex**
   ```powershell
   python importar_excel_local.py "comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx" --tipo comex
   ```
3. **Importar CNAE**
   ```powershell
   python importar_excel_local.py "comex_data\comexstat_csv\CNAE.xlsx" --tipo cnae
   ```
4. **Verificar no Render**
   ```powershell
   Invoke-WebRequest -Uri "https://comex-backend-gecp.onrender.com/validar-sistema" -Method GET -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select-Object -ExpandProperty banco_dados
   ```
5. **Executar Enriquecimento**
   ```powershell
   Invoke-WebRequest -Uri "https://comex-backend-gecp.onrender.com/enriquecer-com-cnae-relacionamentos" -Method POST -UseBasicParsing
   ```

## 🔍 Como Saber se Está Usando o Banco Correto

**SQLite Local:**
- Caminho: `projeto_comex/comex_data/database/comex.db`
- URL começa com: `sqlite:///`

**PostgreSQL Render:**
- URL começa com: `postgresql://` ou `postgres://`
- Contém: `@host:porta/database`
- Exemplo: `postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com:5432/comex_db`

## ⚠️ Importante

- **NÃO** compartilhe a DATABASE_URL publicamente (contém senha)
- Use variável de ambiente ou arquivo `.env` (adicione `.env` ao `.gitignore`)
- Após configurar, os dados serão importados diretamente no PostgreSQL do Render
