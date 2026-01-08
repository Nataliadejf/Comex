# ⚡ Configuração Rápida - Comex-4 (Copy & Paste)

## 🎯 Configurações Exatas para Render Dashboard

### 📍 Localização no Render:
**Render Dashboard → My project → Production → Comex-4 → Settings → Build & Deploy**

---

## ✅ Configurações (Copy-Paste)

### 1. Root Directory
```
frontend
```

### 2. Build Command
```bash
CI=false npm install && npm run build
```

### 3. Publish Directory
```
build
```
⚠️ **NÃO** coloque `frontend/build`, apenas `build`

---

## 🔧 Environment Variables

**Render Dashboard → Comex-4 → Settings → Environment**

### Variável 1:
**Nome:** `REACT_APP_API_URL`  
**Valor:** `https://[URL_DO_SEU_BACKEND].onrender.com`

**Exemplo:**
```
REACT_APP_API_URL=https://comex-backend.onrender.com
```

### Variável 2 (Opcional - Otimiza Build):
**Nome:** `CI`  
**Valor:** `false`

### Variável 3 (Opcional - Otimiza Build):
**Nome:** `GENERATE_SOURCEMAP`  
**Valor:** `false`

---

## ✅ Checklist Rápido

- [ ] Root Directory = `frontend`
- [ ] Build Command = `CI=false npm install && npm run build`
- [ ] Publish Directory = `build` (sem `frontend/`)
- [ ] Variável `REACT_APP_API_URL` configurada
- [ ] Auto-Deploy = `On Commit`
- [ ] Salvar alterações
- [ ] Fazer Manual Deploy

---

## 🚀 Após Configurar

1. **Salve todas as alterações**
2. **Vá em "Manual Deploy"** (menu superior)
3. **Clique em "Deploy latest commit"**
4. **Aguarde 5-10 minutos**
5. **Verifique em "Events" ou "Logs"**

---

## 🐛 Se Build Travar

O build pode travar em "Creating an optimized production build..." por:
- Limitações de memória (plano free)
- Timeout do build

**Solução:**
1. Use o Build Command com `CI=false`
2. Adicione variáveis `CI=false` e `GENERATE_SOURCEMAP=false`
3. Se ainda travar, pode ser limitação do plano free

---

## 📚 Documentação Completa

Para mais detalhes, consulte: `PASSO_A_PASSO_CONFIGURAR_COMEX4.md`
