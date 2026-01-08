# 🗄️ Como Configurar PostgreSQL no Render

Este guia explica como criar e configurar o PostgreSQL no Render e conectá-lo ao backend.

## 📋 Passo 1: Criar Banco PostgreSQL no Render

1. **No Render Dashboard**, clique em **"New +"** → **"PostgreSQL"**
2. **Configure o banco:**
   - **Name:** `comex-database` (ou outro nome de sua escolha)
   - **Database:** `comex` (ou outro nome)
   - **User:** Será gerado automaticamente
   - **Region:** Escolha a mesma região do seu backend
   - **Plan:** Free (para testes) ou Starter (recomendado para produção)
3. **Clique em "Create Database"**

## 📋 Passo 2: Obter a URL de Conexão

Após criar o banco:

1. **No Dashboard do PostgreSQL**, vá em **"Connections"**
2. **Copie a "Internal Database URL"** (para uso dentro do Render)
   - Formato: `postgres://user:password@host:port/dbname`
3. **OU copie a "External Database URL"** (se precisar acessar de fora)

## 📋 Passo 3: Configurar no Backend

### Opção A: Via Render Dashboard (Recomendado)

1. **No Render Dashboard**, vá em **"comex-backend"** → **"Settings"** → **"Environment"**
2. **Adicione a variável:**
   - **Key:** `DATABASE_URL`
   - **Value:** Cole a URL do PostgreSQL (Internal Database URL)
   - **IMPORTANTE:** Se a URL começar com `postgres://`, o código já converte automaticamente para `postgresql://`
3. **Clique em "Save Changes"**
4. **Faça um Manual Deploy** para aplicar as mudanças

### Opção B: Via render.yaml (GitHub)

Se você quiser configurar via `render.yaml`:

1. **Edite o arquivo `render.yaml`**
2. **Descomente e substitua a linha:**
   ```yaml
   - key: DATABASE_URL
     value: postgresql://user:password@host:port/dbname
   ```
3. **⚠️ ATENÇÃO:** Não commite a senha diretamente no Git!
   - Use `sync: false` para configurar manualmente no Dashboard
   - OU use variáveis de ambiente seguras do Render

## 📋 Passo 4: Verificar Conexão

Após configurar:

1. **No Render Dashboard**, vá em **"comex-backend"** → **"Shell"**
2. **Execute:**
   ```bash
   python -c "
   import os
   from database.database import engine
   from sqlalchemy import text
   
   db_url = os.getenv('DATABASE_URL', 'não configurado')
   print(f'DATABASE_URL: {db_url[:50]}...' if len(db_url) > 50 else f'DATABASE_URL: {db_url}')
   
   try:
       with engine.connect() as conn:
           result = conn.execute(text('SELECT version()'))
           print(f'✅ Conexão OK: {result.fetchone()[0][:50]}...')
   except Exception as e:
       print(f'❌ Erro: {e}')
   "
   ```

## 📋 Passo 5: Criar Tabelas

Após verificar a conexão, crie as tabelas:

```bash
python -c "
from database.database import init_db
init_db()
print('✅ Tabelas criadas!')
"
```

## 🔒 Segurança

- ✅ **NUNCA** commite senhas ou URLs completas no Git
- ✅ Use `sync: false` no `render.yaml` para variáveis sensíveis
- ✅ Configure manualmente no Render Dashboard
- ✅ Use "Internal Database URL" quando possível (mais seguro)

## 🐛 Troubleshooting

### Erro: "could not translate host name"

- Verifique se está usando a **Internal Database URL** (não External)
- Certifique-se de que o backend e o PostgreSQL estão na mesma região

### Erro: "password authentication failed"

- Verifique se a URL está correta
- Certifique-se de que não há espaços extras na URL

### Erro: "database does not exist"

- Verifique o nome do banco na URL
- Certifique-se de que o banco foi criado corretamente

## 📝 Exemplo de URL

Formato da URL:
```
postgresql://usuario:senha@dpg-xxxxx-a.oregon-postgres.render.com:5432/comex_xxxx
```

O código já converte automaticamente `postgres://` para `postgresql://` se necessário.
