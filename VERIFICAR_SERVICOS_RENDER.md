# Verificar e Limpar Serviços no Render

## 🔍 Situação Atual

Você tem **4 serviços** no Render:
1. **Comex-3** - ✓ Deployed (Docker)
2. **Comex-2** - ✓ Deployed (Docker)
3. **comex-backend** - ✗ Failed deploy (Python 3) ← Este é o correto!
4. **Comex-** - ⏳ Deploying (Docker)

## ✅ Próximos Passos

### 1. Limpar Serviços Duplicados

Você precisa **deletar** os serviços duplicados e manter apenas o `comex-backend`:

1. No Render Dashboard, vá em **"My project"**
2. Para cada serviço duplicado (Comex-3, Comex-2, Comex-):
   - Clique no nome do serviço
   - Vá em **"Settings"** (no menu lateral)
   - Role até o final
   - Clique em **"Delete Service"**
   - Confirme a exclusão

**Mantenha apenas**: `comex-backend`

### 2. Verificar e Corrigir o Serviço `comex-backend`

O serviço `comex-backend` está falhando. Vamos corrigir:

1. Clique em **"comex-backend"**
2. Vá em **"Settings"**
3. Verifique as configurações:

#### Configurações Corretas:

**Build Command:**
```
pip install --upgrade pip setuptools wheel && pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

**Start Command:**
```
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

**Root Directory:**
```
. (ponto - raiz do repositório)
```

**Environment Variables:**
- `DATABASE_URL` - URL do PostgreSQL (criar PostgreSQL primeiro se não tiver)
- `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`
- `COMEX_STAT_API_KEY` = (deixe vazio)
- `SECRET_KEY` = (gerar automaticamente ou criar uma chave)
- `ENVIRONMENT` = `production`
- `DEBUG` = `false`
- `PYTHON_VERSION` = `3.11`

### 3. Criar PostgreSQL (se não tiver)

1. No Render Dashboard, clique em **"+ New"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `comex-database`
   - **Database**: `comex_db`
   - **User**: `comex_user`
   - **Region**: `Oregon` (mesmo do backend)
   - **Plan**: `Free`
4. Clique em **"Create Database"**
5. Após criar, copie a **Internal Database URL**
6. Vá no serviço `comex-backend` → **Settings** → **Environment Variables**
7. Adicione: `DATABASE_URL` = (cole a Internal Database URL)

### 4. Fazer Novo Deploy

1. No serviço `comex-backend`, clique em **"Manual Deploy"**
2. Selecione **"Deploy latest commit"**
3. Aguarde o build completar (5-10 minutos)

### 5. Verificar Logs

Após o deploy:

1. Vá em **"Logs"** (menu lateral)
2. Verifique se há erros
3. Se tudo estiver OK, você verá:
   ```
   Application startup complete.
   ```

### 6. Testar o Backend

Após deploy bem-sucedido:

1. Copie a URL do serviço (ex: `https://comex-backend.onrender.com`)
2. Teste o health check:
   ```
   https://seu-backend.onrender.com/health
   ```
3. Deve retornar:
   ```json
   {"status":"healthy","database":"connected"}
   ```

## 📋 Checklist

- [ ] Deletar serviços duplicados (Comex-3, Comex-2, Comex-)
- [ ] Verificar configurações do `comex-backend`
- [ ] Criar PostgreSQL (se necessário)
- [ ] Configurar `DATABASE_URL` no `comex-backend`
- [ ] Fazer novo deploy do `comex-backend`
- [ ] Verificar logs do deploy
- [ ] Testar endpoint `/health`
- [ ] Atualizar frontend para usar URL do Render

## 🔗 URLs Importantes

- **Render Dashboard**: https://dashboard.render.com
- **Documentação Render**: https://render.com/docs
- **Troubleshooting**: https://render.com/docs/troubleshooting-deploys

---

**Última atualização**: 05/01/2026

