# ✅ URL Correta do PostgreSQL

## 🔑 DATABASE_URL Configurada

A URL completa e correta do PostgreSQL do Render é:

```
postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

## 📋 Como Usar

### No PowerShell (antes de executar scripts):

```powershell
$env:DATABASE_URL = "postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb"
```

### Ou criar arquivo .env:

Crie um arquivo `.env` na raiz do projeto com:

```
DATABASE_URL=postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

## ✅ Verificação

Após configurar, teste a conexão:

```powershell
python -c "import os; from pathlib import Path; import sys; sys.path.insert(0, 'backend'); from database.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); result = db.execute(text('SELECT COUNT(*) FROM operacoes_comex')); print(f'Registros: {result.scalar()}'); db.close()"
```

**Resultado esperado:** `Registros: 0` (banco vazio do Render) ou número de registros após importação.

## ⚠️ Importante

- **NÃO** compartilhe esta URL publicamente (contém senha)
- **NÃO** faça commit do arquivo `.env` no Git
- A URL já está configurada no Render (backend)
