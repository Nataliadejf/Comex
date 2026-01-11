# 🗑️ Como Limpar o Banco de Dados no Render

## ⚠️ ATENÇÃO: Isso vai DELETAR TODOS OS DADOS!

Use apenas se:
- O banco está em estado inconsistente
- As migrations estão falhando
- Você quer começar do zero

## 📋 Passo a Passo

### 1️⃣ Acessar o Shell do PostgreSQL no Render

1. No Render Dashboard, vá para seu **PostgreSQL**
2. Clique em **"Connect"** ou **"Shell"**
3. Escolha **"psql Shell"** ou **"Connect via psql"**

### 2️⃣ Conectar ao Banco

Se não conectar automaticamente, use:
```sql
\c comexdb
```
(Substitua `comexdb` pelo nome do seu banco)

### 3️⃣ Limpar Tabelas e Estado do Alembic

Execute estes comandos **UM POR VEZ**:

```sql
-- Limpar tabela de versão do Alembic
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Limpar todas as tabelas (se necessário)
DROP TABLE IF EXISTS operacoes_comex CASCADE;
DROP TABLE IF EXISTS ncm_info CASCADE;
DROP TABLE IF EXISTS coleta_log CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS aprovacao_cadastro CASCADE;
DROP TABLE IF EXISTS comercio_exterior CASCADE;
DROP TABLE IF EXISTS empresas CASCADE;
DROP TABLE IF EXISTS cnae_hierarquia CASCADE;
DROP TABLE IF EXISTS empresas_recomendadas CASCADE;

-- Verificar se limpou tudo
\dt
```

### 4️⃣ Verificar Limpeza

Execute:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

Deve retornar vazio ou apenas tabelas do sistema.

### 5️⃣ Fazer Deploy Novamente

Após limpar, faça um novo deploy no Render:
- Render Dashboard → "comex-backend" → "Manual Deploy" → "Deploy latest commit"

As migrations serão executadas automaticamente e criarão todas as tabelas do zero.

## 🔄 Alternativa: Limpar Apenas Estado do Alembic

Se você só quer resetar as migrations mas manter os dados:

```sql
DROP TABLE IF EXISTS alembic_version CASCADE;
```

Depois faça deploy novamente. O Alembic vai pensar que nunca rodou migrations e tentará criar tudo de novo (mas vai falhar se as tabelas já existem - por isso a migration tem try/except).

## ✅ Após Limpar

1. Faça deploy no Render
2. Verifique os logs para ver se as migrations rodaram
3. Teste o endpoint `/health` para confirmar que está funcionando
