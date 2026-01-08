# ✅ Manter Comex-4 Funcionando - Guia Completo

## 🎯 Decisão: Usar Apenas Comex-4

**É melhor manter o comex-4 funcionando** ao invés de criar múltiplos serviços!

## 🔍 Problemas Identificados no Comex-5

1. ❌ **Python Version:** Está usando `3.13.4` (deveria ser `3.11.0`)
2. ❌ **Arquivo não encontrado:** `backend/requirements-render-ultra-minimal.txt`
   - Isso acontece porque o **Root Directory** pode estar errado
   - Ou o caminho no Build Command está incorreto

## ✅ Solução: Configurar Comex-4 Corretamente

### Passo 1: Verificar Tipo do Comex-4

No Render Dashboard:
- Se for **Static** (Frontend): Mantenha como está e crie um novo serviço Python para backend
- Se for **Python 3**: Configure como backend completo

### Passo 2: Se Comex-4 for Python 3 (Backend)

**No Render Dashboard → Comex-4 → Settings:**

#### Configurações Corretas:

**Root Directory:**
```
. (ponto - raiz do repositório)
```

**Python Version:**
```
3.11.0
```
⚠️ **CRÍTICO:** Não deixe usar 3.13!

**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
```

**Start Command:**
```bash
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
```

#### Variáveis de Ambiente:

- `PYTHON_VERSION` = `3.11.0`
- `ENVIRONMENT` = `production`
- `DEBUG` = `false`
- `DATABASE_URL` = (configure se necessário)
- `SECRET_KEY` = (gere automaticamente)
- `COMEX_STAT_API_URL` = `https://comexstat.mdic.gov.br`

### Passo 3: Remover Serviços Não Utilizados

**Remova no Render Dashboard:**
- ❌ Comex-5 (está falhando)
- ❌ Comex-3, Comex-2, Comex- (Docker - não funcionam)
- ❌ comex-backend (se não estiver funcionando)

**Mantenha apenas:**
- ✅ Comex-4 (funcionando)

## 🔧 Se Comex-4 for Static (Frontend)

Nesse caso, você precisa de **2 serviços**:

1. **Comex-4** (Static) - Frontend
2. **Novo serviço Python** - Backend

### Criar Novo Serviço Backend:

1. No Render Dashboard, clique em **"+ New"** → **"Web Service"**
2. Conecte ao GitHub: `Nataliadjf/Comex`
3. Configure:
   - **Name:** `comex-backend` ou `comex-api`
   - **Root Directory:** `.` (raiz)
   - **Python Version:** `3.11.0`
   - **Build Command:** (mesmo do Passo 2)
   - **Start Command:** (mesmo do Passo 2)

## ✅ Checklist Final

- [ ] Verificar tipo do Comex-4 (Static ou Python?)
- [ ] Configurar Python Version = 3.11.0
- [ ] Configurar Root Directory = `.` (raiz)
- [ ] Verificar Build Command usa `backend/requirements-render-ultra-minimal.txt`
- [ ] Remover serviços não utilizados
- [ ] Testar endpoints após deploy

## 🧪 Testar Após Configurar

1. **Health Check:**
   ```
   https://comex-4.onrender.com/health
   ```
   Deve retornar: `{"status": "ok"}` ou similar

2. **Dashboard Stats:**
   ```
   https://comex-4.onrender.com/dashboard/stats
   ```
   Deve retornar dados (mesmo que vazio)

3. **Verificar Logs:**
   - Não deve mostrar erros de importação
   - Não deve mostrar erros de Rust/compilação
