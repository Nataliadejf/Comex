# 🚀 Configurar Deploy Automático via Git no Render

## ✅ Status Atual

- **Comex-4**: Static Site (Frontend) - ✅ Funcionando
- **Backend**: Precisa verificar se há serviço funcionando em `https://comex-4.onrender.com`

## 📋 Passo a Passo para Deploy Automático

### 1. Verificar Configuração do Comex-4 (Frontend)

No Render Dashboard → Comex-4 → Settings:

**Build & Deploy:**
- ✅ **Auto-Deploy**: `On Commit` (já configurado)
- ✅ **Root Directory**: `frontend`
- ✅ **Build Command**: `npm install && npm run build`
- ✅ **Publish Directory**: `frontend/build`

**Deploy Hook:**
- O Render já gera um hook automático para deploy manual se necessário

### 2. Criar/Configurar Serviço Backend

**Opção A: Se já existe um serviço backend funcionando**

1. No Render Dashboard, encontre o serviço backend (ex: `comex-backend` ou similar)
2. Vá em Settings → Build & Deploy
3. Verifique:
   - **Auto-Deploy**: `On Commit` ✅
   - **Root Directory**: `.` (raiz do projeto)
   - **Build Command**: 
     ```bash
     pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
     ```
   - **Python Version**: `3.11.0`

**Opção B: Criar novo serviço backend**

1. No Render Dashboard, clique em **"+ New"** → **"Web Service"**
2. Conecte ao GitHub: `Nataliadjf/Comex`
3. Configure:
   - **Name**: `comex-backend` ou `comex-api`
   - **Root Directory**: `.` (raiz)
   - **Environment**: `Python 3`
   - **Python Version**: `3.11.0`
   - **Build Command**: (mesmo acima)
   - **Start Command**: (mesmo acima)
   - **Auto-Deploy**: `On Commit` ✅

### 3. Configurar Frontend para Apontar para Backend

**Arquivo `frontend/.env`:**
```env
REACT_APP_API_URL=https://[URL_DO_BACKEND].onrender.com
```

**Exemplo:**
```env
REACT_APP_API_URL=https://comex-backend.onrender.com
```

⚠️ **IMPORTANTE**: Após alterar `.env`, você precisa fazer rebuild do frontend:
```bash
cd frontend
npm run build
```

### 4. Garantir que Dados Estão Disponíveis

Os seguintes arquivos devem estar em `backend/data/`:
- ✅ `empresas_recomendadas.xlsx`
- ✅ `resumo_dados_comexstat.json`
- ✅ `dados_ncm_comexstat.json`

**Verificar se backend está servindo os dados:**

1. Teste o endpoint:
   ```
   https://[BACKEND_URL]/dashboard/empresas-recomendadas
   ```

2. Deve retornar JSON com empresas recomendadas

3. Teste outros endpoints:
   - `/dashboard/empresas-importadoras`
   - `/dashboard/empresas-exportadoras`
   - `/dashboard/dados-comexstat`

### 5. Deploy Automático via Git

**Como funciona:**
1. Você faz commit e push para o GitHub
2. O Render detecta automaticamente as mudanças
3. O Render faz build e deploy automaticamente

**Para ativar:**
- No Render Dashboard → Serviço → Settings → Build & Deploy
- **Auto-Deploy** deve estar como `On Commit`
- Se estiver como `Manual`, altere para `On Commit`

### 6. Verificar Deploy Após Push

1. **Faça commit e push:**
   ```bash
   git add .
   git commit -m "Atualizar configurações"
   git push origin main
   ```

2. **No Render Dashboard:**
   - Vá em **Events** do serviço
   - Você verá um novo deploy iniciando automaticamente
   - Aguarde o build completar (pode levar 5-10 minutos)

3. **Verifique logs:**
   - Se houver erros, aparecerão nos logs
   - Corrija e faça novo push

## ✅ Checklist Final

- [ ] Comex-4 (Frontend) com Auto-Deploy ativado
- [ ] Serviço Backend criado e funcionando
- [ ] Backend com Auto-Deploy ativado
- [ ] Frontend `.env` apontando para backend correto
- [ ] Dados (`empresas_recomendadas.xlsx`, etc.) em `backend/data/`
- [ ] Endpoints do backend retornando dados corretamente
- [ ] Teste de deploy automático funcionando

## 🧪 Testar Após Deploy

1. **Frontend:**
   ```
   https://comex-4.onrender.com
   ```

2. **Backend Health:**
   ```
   https://[BACKEND_URL]/health
   ```

3. **Backend Empresas:**
   ```
   https://[BACKEND_URL]/dashboard/empresas-recomendadas
   ```

4. **Dashboard no Frontend:**
   - Deve mostrar empresas recomendadas
   - Deve mostrar dados de importação/exportação
   - Seções "Prováveis Importadores" e "Prováveis Exportadores" devem aparecer
