# 🔧 Solução para 404 do Dashboard

## 🔍 Problema Identificado

O erro `GET https://comex-jhmg.onrender.com/dashboard 404` acontece porque:

1. **Frontend React Router**: O React Router gerencia rotas no cliente (`/dashboard`, `/busca`, etc.)
2. **Render Static Site**: O Render está tentando encontrar um arquivo físico `/dashboard` que não existe
3. **Arquivo _redirects**: Pode não estar sendo copiado corretamente para o build

## ✅ Solução Implementada

### 1. Melhorado script `postbuild`
- Agora usa Node.js para criar o arquivo `_redirects` de forma mais confiável
- Garante que o arquivo seja criado no diretório `build/`

### 2. Verificar Configuração no Render

**IMPORTANTE**: No Render Dashboard, você precisa configurar:

1. **Acesse seu Static Site no Render**:
   - Vá para: https://dashboard.render.com
   - Selecione seu serviço de frontend (`comex-jhmg` ou similar)

2. **Configure Redirects/Rewrites**:
   - Clique em **"Settings"** no menu lateral
   - Vá para a seção **"Redirects & Rewrites"** ou **"Headers"**
   - Adicione um redirect:
     - **Source Path**: `/*`
     - **Destination**: `/index.html`
     - **Status Code**: `200`
   - Clique em **"Save"**

3. **Ou verifique o arquivo _redirects**:
   - Após o deploy, verifique se o arquivo `_redirects` está em `build/`
   - Você pode verificar fazendo: `curl https://comex-jhmg.onrender.com/_redirects`

## 🔄 Próximos Passos

1. **Commit e Push** das mudanças:
   ```bash
   git add frontend/package.json backend/main.py
   git commit -m "fix: Corrige 404 do dashboard e tratamento BigQuery"
   git push origin main
   ```

2. **Aguardar deploy automático** ou fazer deploy manual

3. **Verificar se funcionou**:
   - Acesse: `https://comex-jhmg.onrender.com/dashboard`
   - Deve redirecionar para o dashboard do React

## 📋 Checklist

- [ ] Commit e push feito
- [ ] Deploy completo no Render
- [ ] Verificar se `/dashboard` carrega o React
- [ ] Verificar se `/_redirects` está acessível
- [ ] Se não funcionar, adicionar redirect manual no Render Dashboard

## 🚨 Se Ainda Não Funcionar

Se após o deploy ainda der 404:

1. **Adicione redirect manual no Render**:
   - Settings → Redirects & Rewrites
   - Adicione: `/*` → `/index.html` (200)

2. **Verifique Build Directory**:
   - O "Publish Directory" deve ser: `frontend/build`

3. **Verifique Root Directory**:
   - O "Root Directory" deve ser: `frontend`
