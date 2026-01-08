# 🔧 Corrigir Configuração do Comex-4 - Passo a Passo

## ❌ Problemas Identificados na Configuração Atual

### Problema 1: Build Command incorreto
**Atual:** `frontend/ $ CI=false npm install && npm run build`  
**Correto:** `CI=false npm install && npm run build`

⚠️ O `frontend/ $` não deve estar no Build Command!

### Problema 2: Publish Directory incorreto
**Atual:** `frontend/build`  
**Correto:** `build`

⚠️ Como o Root Directory já é `frontend`, o Publish Directory deve ser apenas `build` (sem `frontend/`)

---

## ✅ Correções Necessárias

### 1. Corrigir Build Command

**No Render Dashboard:**
1. Vá em **Comex-4 → Settings → Build & Deploy**
2. Clique em **"Edit"** ao lado de **"Build Command"**
3. **Remova** o `frontend/ $` do início
4. Deixe apenas:
   ```
   CI=false npm install && npm run build
   ```
5. Clique em **"Save"**

### 2. Corrigir Publish Directory

**No Render Dashboard:**
1. Vá em **Comex-4 → Settings → Build & Deploy**
2. Clique em **"Edit"** ao lado de **"Publish Directory"**
3. Altere de `frontend/build` para apenas:
   ```
   build
   ```
4. Clique em **"Save"**

---

## 🔧 Configurar Environment Variables (Static Site)

Para **Static Sites** no Render, as variáveis de ambiente são configuradas de forma diferente:

### Opção 1: Via arquivo `.env` no repositório

Crie um arquivo `frontend/.env.production` no seu repositório:

```env
REACT_APP_API_URL=https://[URL_DO_BACKEND].onrender.com
```

**⚠️ IMPORTANTE:** 
- O arquivo deve estar em `frontend/.env.production`
- Faça commit e push para o GitHub
- O React vai usar essas variáveis durante o build

### Opção 2: Via Build Command (temporário)

Você pode adicionar a variável diretamente no Build Command:

```bash
REACT_APP_API_URL=https://[BACKEND_URL].onrender.com CI=false npm install && npm run build
```

**⚠️ Não recomendado:** Variáveis sensíveis não devem estar no Build Command.

### Opção 3: Verificar se existe seção Environment

Alguns Static Sites no Render têm uma seção "Environment" nas Settings. Verifique:
1. Vá em **Comex-4 → Settings**
2. Procure por **"Environment"** ou **"Environment Variables"** no menu lateral
3. Se existir, adicione lá:
   - **Nome:** `REACT_APP_API_URL`
   - **Valor:** `https://[URL_DO_BACKEND].onrender.com`

---

## ✅ Configuração Final Correta

### Build & Deploy:

- **Root Directory:** `frontend` ✅ (já está correto)
- **Build Command:** `CI=false npm install && npm run build` (remover `frontend/ $`)
- **Publish Directory:** `build` (remover `frontend/`)
- **Auto-Deploy:** `On Commit` ✅ (já está correto)

### Environment Variables:

**Criar arquivo `frontend/.env.production`:**
```env
REACT_APP_API_URL=https://[URL_DO_SEU_BACKEND].onrender.com
```

---

## 📋 Checklist de Correção

- [ ] Remover `frontend/ $` do Build Command
- [ ] Alterar Publish Directory de `frontend/build` para `build`
- [ ] Criar arquivo `frontend/.env.production` com `REACT_APP_API_URL`
- [ ] Fazer commit e push do `.env.production`
- [ ] Fazer Manual Deploy após correções

---

## 🚀 Após Corrigir

1. **Salve todas as alterações** no Render Dashboard
2. **Faça commit e push** do arquivo `.env.production` (se criou)
3. **Vá em "Manual Deploy"** → **"Deploy latest commit"**
4. **Aguarde o build completar** (5-10 minutos)
5. **Verifique em "Events" ou "Logs"** se funcionou

---

## 🐛 Se Ainda Não Funcionar

1. **Verifique os logs completos** no Render Dashboard
2. **Certifique-se** que o Build Command está exatamente como:
   ```
   CI=false npm install && npm run build
   ```
3. **Certifique-se** que o Publish Directory está exatamente como:
   ```
   build
   ```
4. **Verifique** se o arquivo `.env.production` foi commitado e está em `frontend/.env.production`

---

## 💡 Explicação

- **Root Directory = `frontend`**: O Render já está dentro do diretório `frontend`
- **Build Command**: Não precisa de `frontend/ $` porque já está no diretório correto
- **Publish Directory = `build`**: Relativo ao Root Directory (`frontend`), então `build` significa `frontend/build`
