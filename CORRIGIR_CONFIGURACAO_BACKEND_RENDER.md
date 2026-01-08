# 🔧 Corrigir Configuração do Backend no Render

## ❌ Problemas Identificados na Configuração Atual

### 1. Root Directory
**Atual:** `backend`  
**Correto:** `.` (raiz do projeto)

### 2. Build Command
**Atual:** `pip install -r requirements-render-minimal.txt`  
**Correto:** 
```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

**Problemas:**
- Usa `requirements-render-minimal.txt` (pode ter problemas de compilação)
- Deveria usar `requirements-render-ultra-minimal.txt` (wheels pré-compilados)
- Falta comando completo de instalação

### 3. Start Command
**Atual:** `uvicorn main:app --host 0.0.0.0 --port $PORT`  
**Correto:** `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info`

**Problemas:**
- Não tem `cd backend` (necessário se Root Directory for `.`)
- Não tem `python -m` (melhor prática)
- Falta `--log-level info`

### 4. Health Check Path
**Atual:** `/healthz`  
**Correto:** `/health`

---

## ✅ Correções Necessárias no Render Dashboard

### Passo 1: Root Directory

1. Render Dashboard → comex-backend → Settings → Build & Deploy
2. Clique em **"Edit"** ao lado de **"Root Directory"**
3. Altere de `backend` para `.` (ponto - raiz do projeto)
4. Clique em **"Save"**

### Passo 2: Build Command

1. Clique em **"Edit"** ao lado de **"Build Command"**
2. Altere para:
   ```bash
   pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
   ```
3. Clique em **"Save"**

### Passo 3: Start Command

1. Clique em **"Edit"** ao lado de **"Start Command"**
2. Altere para:
   ```bash
   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
   ```
3. Clique em **"Save"**

### Passo 4: Health Check Path

1. Vá em **"Health Checks"** (menu lateral)
2. Clique em **"Edit"** ao lado de **"Health Check Path"**
3. Altere de `/healthz` para `/health`
4. Clique em **"Save"**

---

## 📋 Configuração Final Correta

### Build & Deploy:
- **Root Directory:** `.` (raiz do projeto)
- **Build Command:** (comando completo acima)
- **Start Command:** `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info`
- **Auto-Deploy:** `On Commit` ✅

### Health Checks:
- **Health Check Path:** `/health`

### Environment Variables:
- `DATABASE_URL` - Configure manualmente
- `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`
- `COMEX_STAT_API_KEY` = (deixe vazio)
- `SECRET_KEY` - Gere automaticamente
- `ENVIRONMENT` = `production`
- `DEBUG` = `false`
- `PYTHON_VERSION` = `3.11.0`

---

## 🚀 Após Corrigir

1. **Salve todas as alterações**
2. **Vá em "Manual Deploy"** → **"Deploy latest commit"**
3. **Aguarde o build completar** (5-10 minutos)
4. **Verifique em "Events" ou "Logs"** se funcionou
5. **Teste:** `https://comex-backend-knjm.onrender.com/health`

---

## ✅ Checklist

- [ ] Root Directory alterado para `.`
- [ ] Build Command atualizado com comando completo
- [ ] Start Command atualizado com `cd backend && python -m`
- [ ] Health Check Path alterado para `/health`
- [ ] Environment Variables configuradas
- [ ] Manual Deploy feito após correções
- [ ] Health check funcionando (`/health` retorna OK)

---

## 💡 Nota sobre render.yaml

O arquivo `render.yaml` já está correto! Ele será usado se você criar um novo serviço via Blueprint. Mas como o serviço já existe, você precisa corrigir manualmente no Dashboard.
