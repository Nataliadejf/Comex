# Configuração Final do Render - Passo a Passo

## 🎯 Objetivo

Configurar corretamente o serviço `comex-backend` no Render e remover serviços duplicados.

## 📋 Passo a Passo Completo

### PASSO 1: Limpar Serviços Duplicados

1. Acesse: https://dashboard.render.com
2. Vá em **"My project"**
3. Na lista de serviços, **delete**:
   - ❌ Comex-3
   - ❌ Comex-2
   - ❌ Comex-
   
   **Como deletar:**
   - Clique no nome do serviço
   - Vá em **"Settings"** (menu lateral esquerdo)
   - Role até o final da página
   - Clique em **"Delete Service"**
   - Confirme a exclusão

**Mantenha apenas**: ✅ `comex-backend`

### PASSO 2: Criar Banco de Dados PostgreSQL

1. No Render Dashboard, clique em **"+ New"** (canto superior direito)
2. Selecione **"PostgreSQL"**
3. Preencha:
   - **Name**: `comex-database`
   - **Database**: `comex_db`
   - **User**: `comex_user`
   - **Region**: `Oregon` (mesmo do backend)
   - **Plan**: `Free`
4. Clique em **"Create Database"**
5. Aguarde a criação (1-2 minutos)
6. Após criar, copie a **Internal Database URL** (formato: `postgresql://usuario:senha@host:porta/database`)

### PASSO 3: Configurar o Serviço `comex-backend`

1. Clique no serviço **"comex-backend"**
2. Vá em **"Settings"** (menu lateral)

#### 3.1. Verificar Build & Start Commands

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

#### 3.2. Configurar Environment Variables

Vá em **"Environment"** (menu lateral) e adicione/verifique:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | (cole a Internal Database URL do PostgreSQL) |
| `COMEX_STAT_API_URL` | `https://comexstat.mdic.gov.br` |
| `COMEX_STAT_API_KEY` | (deixe vazio) |
| `SECRET_KEY` | (clique em "Generate" ou use uma chave aleatória) |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `PYTHON_VERSION` | `3.11` |

### PASSO 4: Conectar ao Repositório GitHub

1. No serviço `comex-backend`, vá em **"Settings"**
2. Em **"Repository"**, verifique se está conectado a:
   - **Repository**: `Nataliadjf/Comex`
   - **Branch**: `main`
   - **Root Directory**: `.` (raiz)
3. Se não estiver conectado, clique em **"Connect Repository"** e selecione o repositório

### PASSO 5: Fazer Deploy

1. No serviço `comex-backend`, clique em **"Manual Deploy"** (canto superior direito)
2. Selecione **"Deploy latest commit"**
3. Aguarde o build completar (5-10 minutos)
4. Monitore os logs em tempo real

### PASSO 6: Verificar Deploy

Após o deploy:

1. Vá em **"Logs"** (menu lateral)
2. Procure por:
   - ✅ `Successfully installed` - Dependências instaladas
   - ✅ `Application startup complete` - Aplicação iniciada
   - ✅ `Banco de dados inicializado` - Banco conectado
   - ❌ Se houver erros, copie a mensagem completa

### PASSO 7: Testar Backend

1. Copie a URL do serviço (ex: `https://comex-backend-xxxx.onrender.com`)
2. Teste o health check:
   ```
   https://seu-backend.onrender.com/health
   ```
3. Deve retornar:
   ```json
   {"status":"healthy","database":"connected"}
   ```

### PASSO 8: Atualizar Frontend

1. Edite `frontend/.env`:
   ```
   REACT_APP_API_URL=https://seu-backend.onrender.com
   ```
2. Reinicie o frontend:
   - Execute `REINICIAR_FRONTEND.bat`
   - Ou pare e inicie novamente

## ✅ Checklist Final

- [ ] Serviços duplicados deletados
- [ ] PostgreSQL criado
- [ ] `DATABASE_URL` configurada no backend
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Repositório GitHub conectado
- [ ] Deploy realizado com sucesso
- [ ] Health check funcionando
- [ ] Frontend atualizado com URL do Render

## 🐛 Troubleshooting

### Erro: "Build failed"
- Verifique os logs do build
- Confirme que `requirements-render-ultra-minimal.txt` existe
- Verifique se não há erros de compilação Rust

### Erro: "Database connection failed"
- Verifique se `DATABASE_URL` está configurada corretamente
- Use a **Internal Database URL** (não a External)
- Confirme que o PostgreSQL está rodando

### Erro: "Application failed to start"
- Verifique os logs de runtime
- Confirme que o `startCommand` está correto
- Verifique se todas as dependências foram instaladas

## 📞 Próximos Passos Após Deploy Bem-Sucedido

1. ✅ Testar login no frontend
2. ✅ Testar cadastro de novos usuários
3. ✅ Verificar se notificações aparecem nos logs
4. ✅ Aprovar cadastros via API
5. ✅ Testar dashboard com dados reais

---

**Última atualização**: 05/01/2026

