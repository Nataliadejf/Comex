# 📥 Como Importar Dados para PostgreSQL no Render

## ✅ Status Atual

O banco PostgreSQL está **conectado corretamente**! Os logs mostram:
```
INFO sqlalchemy.engine.Engine SELECT 1
INFO sqlalchemy.engine.Engine COMMIT
```

Isso significa que a conexão está funcionando. Agora precisamos **importar os dados**.

## 🚀 Passo a Passo para Importar Dados

### Opção 1: Importar Localmente e Migrar (Recomendado)

#### Passo 1: Importar para SQLite Local

Na sua máquina local:

```powershell
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
python backend/scripts/importar_excel_local.py
```

Isso vai:
- ✅ Ler os arquivos Excel de `backend/data/`
- ✅ Criar banco SQLite local
- ✅ Importar todos os dados
- ✅ Mostrar totais de importação e exportação

#### Passo 2: Migrar para PostgreSQL

Configure a `DATABASE_URL` do PostgreSQL do Render:

```powershell
$env:DATABASE_URL="postgresql://user:password@host:port/dbname"
```

Depois execute:

```powershell
python backend/scripts/migrar_para_postgresql.py
```

Isso vai:
- ✅ Ler dados do SQLite local
- ✅ Enviar para PostgreSQL no Render
- ✅ Mostrar totais durante a migração

### Opção 2: Verificar Dados no Banco

Execute para verificar se já há dados:

```powershell
python backend/scripts/verificar_e_importar_dados.py
```

## 🔍 Verificar se Dados Foram Importados

### Via API (Recomendado)

Acesse no navegador ou via curl:

```
https://seu-backend.onrender.com/api/analise/verificar-dados
```

Deve retornar algo como:

```json
{
  "comercio_exterior": {
    "total": 100000,
    "importacoes": 50000,
    "exportacoes": 50000
  },
  "empresas": {
    "total": 500
  }
}
```

### Via Script Local

```powershell
python backend/scripts/verificar_e_importar_dados.py
```

## 🐛 Se o Dashboard Ainda Estiver Vazio

### 1. Verificar se há dados no banco

```powershell
python backend/scripts/verificar_e_importar_dados.py
```

### 2. Verificar endpoint do dashboard

Acesse:
```
https://seu-backend.onrender.com/dashboard/stats
```

Deve retornar JSON com dados ou estrutura vazia válida.

### 3. Verificar logs do backend

No Render Dashboard → Seu backend → Logs

Procure por:
- ✅ `📊 TOTAIS DE COMÉRCIO EXTERIOR`
- ✅ `💰 Total Importação (USD)`
- ✅ `💰 Total Exportação (USD)`

### 4. Verificar filtros de data

O endpoint `/dashboard/stats` busca por padrão os últimos 24 meses. Se seus dados são de 2025 e estamos em 2026, pode não encontrar nada.

**Solução:** O código já tenta buscar TODOS os dados se não encontrar com filtro de data.

## 📋 Checklist

- [ ] Arquivos Excel estão em `backend/data/`
- [ ] Executou `importar_excel_local.py` localmente
- [ ] Configurou `DATABASE_URL` do PostgreSQL
- [ ] Executou `migrar_para_postgresql.py`
- [ ] Verificou dados via `/api/analise/verificar-dados`
- [ ] Dashboard mostra dados ou estrutura vazia válida

## 💡 Dicas

1. **Sempre importe localmente primeiro** para testar
2. **Verifique os totais** durante a importação
3. **Use o script de verificação** para confirmar dados no PostgreSQL
4. **Verifique os logs** do backend para ver o que está acontecendo

## 🚨 Problemas Comuns

### "Nenhum dado encontrado"

- ✅ Verifique se os arquivos Excel estão em `backend/data/`
- ✅ Execute a importação local primeiro
- ✅ Verifique se a migração foi bem-sucedida

### "Dashboard vazio mas banco tem dados"

- ✅ Verifique os logs do backend
- ✅ Acesse `/dashboard/stats` diretamente
- ✅ Verifique se há filtros de data aplicados

### "Erro ao conectar ao PostgreSQL"

- ✅ Verifique se `DATABASE_URL` está correta
- ✅ Use Internal Database URL (não External)
- ✅ Certifique-se de que PostgreSQL está na mesma região
