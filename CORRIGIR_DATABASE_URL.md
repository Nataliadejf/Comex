# 🔧 Como Corrigir DATABASE_URL no Render

## ❌ Problema Identificado

A `DATABASE_URL` está configurada com um valor incorreto: `89fead6465a59ed111f60b8df7b66d9c`

Este valor não é uma URL válida de conexão PostgreSQL!

## ✅ Solução: Configurar URL Correta

### Passo 1: Obter a URL do PostgreSQL

1. **No Render Dashboard**, vá em **PostgreSQL** (ou procure por "PostgreSQL" nos serviços)
2. **Clique no seu banco PostgreSQL** (ex: `comex-database`)
3. **Vá na aba "Connections"** ou "Info"
4. **Copie a "Internal Database URL"**

   ⚠️ **IMPORTANTE:** Use a **Internal Database URL**, não a External!

### Passo 2: Formato Correto da URL

A URL deve ter este formato:

```
postgresql://usuario:senha@host:porta/database
```

**Exemplo:**
```
postgresql://comex_user:abc123xyz@dpg-xxxxx-a.oregon-postgres.render.com:5432/comex_db
```

### Passo 3: Configurar no Render

1. **No Render Dashboard**, vá em **Web Service** → Seu backend (ex: `comex-backend`)
2. **Vá em "Environment"** (Variáveis de ambiente)
3. **Encontre `DATABASE_URL`** na lista
4. **Clique no campo de valor** (onde está `89fead6465a59ed111f60b8df7b66d9c`)
5. **Cole a URL completa do PostgreSQL** (formato acima)
6. **Clique em "Save Changes"** ou pressione Enter

### Passo 4: Verificar

Após salvar, verifique se a URL está correta:

- ✅ Deve começar com `postgresql://` ou `postgres://`
- ✅ Deve conter `@` (separando credenciais do host)
- ✅ Deve conter `:` após o host (porta)
- ✅ Deve ter pelo menos 50-100 caracteres

**Exemplo de URL válida:**
```
postgresql://comex_user:senha123@dpg-abc123xyz-a.oregon-postgres.render.com:5432/comex_db_abc1
```

## 🔍 Como Encontrar a URL do PostgreSQL

### Opção A: Se você já tem um PostgreSQL criado

1. Render Dashboard → **PostgreSQL** → Seu banco
2. Aba **"Connections"** ou **"Info"**
3. Copie **"Internal Database URL"**

### Opção B: Se você NÃO tem PostgreSQL ainda

1. Render Dashboard → **"+ New"** (canto superior direito)
2. Selecione **"PostgreSQL"**
3. Preencha:
   - **Name:** `comex-database`
   - **Database:** `comex_db`
   - **User:** `comex_user`
   - **Region:** `Oregon` (ou mesma região do backend)
   - **Plan:** `Free` (para testes)
4. Clique em **"Create Database"**
5. Aguarde 1-2 minutos
6. Após criar, copie a **"Internal Database URL"**

## ⚠️ Importante

- ✅ Use **Internal Database URL** (não External)
- ✅ A URL deve ter formato completo com `postgresql://`
- ✅ Não use apenas um hash ou ID
- ✅ Após alterar, faça **Manual Deploy** do backend

## 🚀 Após Configurar

1. **Faça Manual Deploy** do backend:
   - Render Dashboard → Seu backend → **"Manual Deploy"** → **"Deploy latest commit"**

2. **Verifique os logs** para confirmar conexão:
   - Render Dashboard → Seu backend → **"Logs"**
   - Procure por: `✅ Banco de dados inicializado` ou `Connected to database`

3. **Teste o endpoint:**
   ```
   https://seu-backend.onrender.com/health
   ```
   Deve retornar: `{"status": "healthy", "database": "connected"}`

## 🐛 Troubleshooting

### Erro: "could not translate host name"

- ✅ Use **Internal Database URL** (não External)
- ✅ Certifique-se de que backend e PostgreSQL estão na mesma região

### Erro: "password authentication failed"

- ✅ Verifique se copiou a URL completa corretamente
- ✅ Não adicione espaços extras

### Erro: "database does not exist"

- ✅ Verifique o nome do banco na URL
- ✅ Certifique-se de que o PostgreSQL foi criado corretamente

## 📝 Checklist

- [ ] PostgreSQL criado no Render
- [ ] Internal Database URL copiada
- [ ] `DATABASE_URL` configurada com URL completa (não hash)
- [ ] URL começa com `postgresql://` ou `postgres://`
- [ ] Manual Deploy executado
- [ ] Logs mostram conexão bem-sucedida
- [ ] Endpoint `/health` retorna `"database": "connected"`
