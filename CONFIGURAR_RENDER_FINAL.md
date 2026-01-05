# Configuração Final do Render - Passo a Passo

## 🎯 Objetivo

Manter os serviços funcionando (Comex-3 e Comex-2) e configurar o frontend para usar o serviço correto.

## ✅ Serviços que DEVEM ser mantidos

- ✅ **Comex-3** - Deployed (Docker) - **MANTER**
- ✅ **Comex-2** - Deployed (Docker) - **MANTER**

## 🗑️ Serviços que podem ser deletados (opcional)

- ❌ **comex-backend** - Failed deploy (Python 3) - Se não estiver funcionando
- ❌ **Comex-** - Deploying (Docker) - Se não for necessário

## 📋 Passo a Passo Completo

### PASSO 1: Verificar qual serviço usar

1. Teste o endpoint `/health` de cada serviço:
   - Comex-3: `https://comex-3.onrender.com/health`
   - Comex-2: `https://comex-2.onrender.com/health`

2. O serviço correto deve retornar JSON válido (ex: `{"status":"healthy"}` ou `{"message":"Comex Analyzer API"}`)

3. **Recomendação**: Use **Comex-3** como backend principal (parece estar mais estável)

### PASSO 2: Configurar Frontend para usar o serviço correto

**Opção A: Usar Comex-3 (Recomendado)**

1. Edite o arquivo `frontend/.env`:
   ```
   REACT_APP_API_URL=https://comex-3.onrender.com
   ```

2. Reinicie o frontend:
   - Execute `REINICIAR_FRONTEND.bat`
   - Ou pare e inicie novamente o servidor React

**Opção B: Usar Comex-2**

1. Edite o arquivo `frontend/.env`:
   ```
   REACT_APP_API_URL=https://comex-2.onrender.com
   ```

2. Reinicie o frontend

### PASSO 3: Criar Banco de Dados PostgreSQL (se necessário)

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

### PASSO 4: Configurar o Serviço (se precisar atualizar)

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

### PASSO 5: Conectar ao Repositório GitHub (se necessário)

1. No serviço `comex-backend`, vá em **"Settings"**
2. Em **"Repository"**, verifique se está conectado a:
   - **Repository**: `Nataliadjf/Comex`
   - **Branch**: `main`
   - **Root Directory**: `.` (raiz)
3. Se não estiver conectado, clique em **"Connect Repository"** e selecione o repositório

### PASSO 6: Fazer Deploy (quando houver atualizações)

1. No serviço `comex-backend`, clique em **"Manual Deploy"** (canto superior direito)
2. Selecione **"Deploy latest commit"**
3. Aguarde o build completar (5-10 minutos)
4. Monitore os logs em tempo real

### PASSO 7: Verificar Deploy

Após o deploy:

1. Vá em **"Logs"** (menu lateral)
2. Procure por:
   - ✅ `Successfully installed` - Dependências instaladas
   - ✅ `Application startup complete` - Aplicação iniciada
   - ✅ `Banco de dados inicializado` - Banco conectado
   - ❌ Se houver erros, copie a mensagem completa

### PASSO 8: Testar Backend

1. Copie a URL do serviço (ex: `https://comex-backend-xxxx.onrender.com`)
2. Teste o health check:
   ```
   https://seu-backend.onrender.com/health
   ```
3. Deve retornar:
   ```json
   {"status":"healthy","database":"connected"}
   ```

### PASSO 9: Testar Frontend

1. Acesse o frontend no navegador
2. Teste o login
3. Teste o dashboard
4. Verifique se os dados estão sendo carregados corretamente

## ✅ Checklist Final

- [ ] Serviços funcionando verificados (Comex-3 e Comex-2)
- [ ] Frontend configurado com URL do serviço correto
- [ ] Frontend reiniciado após mudança de URL
- [ ] Login testado no frontend
- [ ] Dashboard testado no frontend
- [ ] Dados sendo carregados corretamente

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

