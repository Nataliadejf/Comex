# 🔍 Diagnóstico: Dashboard Vazio

Este guia ajuda a diagnosticar por que o dashboard está retornando dados vazios.

## 📋 Checklist de Verificação

### 1. Verificar se há dados no PostgreSQL

Execute o script de verificação:

```bash
# No Render Shell
cd /opt/render/project/src/backend
python scripts/verificar_dados.py
```

**Resultado esperado:**
- ✅ Total de registros em `ComercioExterior` > 0
- ✅ Total de empresas em `Empresa` > 0
- ✅ Valores totais > 0

**Se retornar 0 registros:**
- ⚠️ Os dados não foram importados ainda
- Execute: `python scripts/import_data.py`

### 2. Verificar se as tabelas existem

```bash
# No Render Shell
python -c "
from database.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\"))
    tabelas = [row[0] for row in result]
    print('Tabelas encontradas:', tabelas)
    print('comercio_exterior existe:', 'comercio_exterior' in tabelas)
    print('empresas existe:', 'empresas' in tabelas)
"
```

### 3. Verificar conexão com PostgreSQL

```bash
# No Render Shell
python -c "
import os
from database.database import engine
from sqlalchemy import text

db_url = os.getenv('DATABASE_URL', 'não configurado')
print(f'DATABASE_URL configurada: {db_url[:50] if len(db_url) > 50 else db_url}...')

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print(f'✅ Conexão OK: {result.fetchone()[0][:50]}...')
except Exception as e:
    print(f'❌ Erro de conexão: {e}')
"
```

### 4. Verificar logs do endpoint

No Render Dashboard → `comex-backend` → **Logs**, procure por:
- `"Tentando buscar dados das novas tabelas"`
- `"Dados carregados das novas tabelas"`
- Erros relacionados a `ComercioExterior`

### 5. Testar endpoint diretamente

```bash
# No Render Shell ou localmente
curl https://comex-backend-wjco.onrender.com/dashboard/stats?meses=24
```

Verifique se retorna:
- `volume_importacoes` > 0
- `volume_exportacoes` > 0
- `principais_ncms` não vazio

## 🔧 Problemas Comuns e Soluções

### Problema 1: Tabelas não existem

**Sintoma:** Erro "relation does not exist"

**Solução:**
```bash
# Executar schema SQL
psql $DATABASE_URL -f backend/database/schema.sql

# OU criar via SQLAlchemy
python -c "
from database.database import init_db
init_db()
print('✅ Tabelas criadas!')
"
```

### Problema 2: Dados não foram importados

**Sintoma:** `verificar_dados.py` retorna 0 registros

**Solução:**
1. Verificar se os arquivos Excel estão em `backend/data/`
2. Executar importação:
   ```bash
   python backend/scripts/import_data.py
   ```

### Problema 3: Filtro de data muito restritivo

**Sintoma:** Dados existem mas endpoint retorna vazio

**Solução:**
- O código já foi corrigido para buscar SEM filtro de data se não encontrar nada
- Verifique se os dados têm `data` válida (não NULL)

### Problema 4: DATABASE_URL não configurada

**Sintoma:** Erro de conexão

**Solução:**
1. Render Dashboard → `comex-backend` → **Environment**
2. Adicionar `DATABASE_URL` com a URL do PostgreSQL
3. Fazer redeploy

## 📊 Verificação Rápida

Execute este comando completo para verificar tudo de uma vez:

```bash
python -c "
from database.database import SessionLocal
from database.models import ComercioExterior, Empresa
from sqlalchemy import func

db = SessionLocal()
try:
    total_comex = db.query(func.count(ComercioExterior.id)).scalar()
    total_empresas = db.query(func.count(Empresa.id)).scalar()
    
    valor_imp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
        ComercioExterior.tipo == 'importacao'
    ).scalar() or 0.0
    
    valor_exp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
        ComercioExterior.tipo == 'exportacao'
    ).scalar() or 0.0
    
    print('='*60)
    print('DIAGNÓSTICO DO BANCO DE DADOS')
    print('='*60)
    print(f'Registros ComercioExterior: {total_comex}')
    print(f'Empresas: {total_empresas}')
    print(f'Valor Importações (USD): \${valor_imp:,.2f}')
    print(f'Valor Exportações (USD): \${valor_exp:,.2f}')
    print('='*60)
    
    if total_comex == 0:
        print('⚠️ PROBLEMA: Nenhum registro encontrado!')
        print('💡 Execute: python backend/scripts/import_data.py')
    elif valor_imp == 0 and valor_exp == 0:
        print('⚠️ PROBLEMA: Valores zerados!')
        print('💡 Verifique se os dados foram importados corretamente')
    else:
        print('✅ Dados encontrados! O endpoint deve funcionar.')
finally:
    db.close()
"
```

## 🚀 Próximos Passos

1. Execute o diagnóstico acima
2. Se não houver dados, execute a importação
3. Se houver dados mas o endpoint ainda retornar vazio, verifique os logs
4. Teste o endpoint novamente
