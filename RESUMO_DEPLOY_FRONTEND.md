# ⚡ Resumo Rápido: Deploy Frontend no Render

## 🎯 Passos Essenciais (5 minutos)

### 1. Descobrir URL do Backend
- Render Dashboard → `comex-backend` → Copiar URL
- Exemplo: `https://comex-backend-xxxxx.onrender.com`

### 2. Criar Static Site
- Render Dashboard → "+ New" → "Static Site"
- Conectar repositório: `Nataliadjf/Comex`
- Branch: `main`

### 3. Configurar Build
```
Build Command: cd frontend && npm install && npm run build
Publish Directory: frontend/build
```

### 4. Configurar Variável de Ambiente
```
REACT_APP_API_URL=https://seu-backend.onrender.com
```
(Substitua pela URL REAL do seu backend)

### 5. Criar e Aguardar
- Clique em "Create Static Site"
- Aguarde 5-10 minutos
- Acesse a URL gerada

## ✅ Teste Rápido

1. Acesse a URL do frontend
2. Deve aparecer tela de login
3. Tente fazer login → Se funcionar, está conectado! ✅

## 🐛 Problemas Comuns

**Página em branco?**
- Verifique Console do navegador (F12)
- Confirme que `REACT_APP_API_URL` está correto
- Verifique se backend está online: `/health`

**Não conecta ao backend?**
- Confirme URL do backend está correta
- Após alterar variável, faça novo deploy
- Backend pode estar "dormindo" (plano free) → Aguarde 30s

**Rotas não funcionam?**
- Verifique se `frontend/public/_redirects` existe
- Deve conter: `/*    /index.html   200`

## 📚 Guia Completo

Veja `DEPLOY_FRONTEND_RENDER_COMPLETO.md` para detalhes completos.

## ✅ Deploy Concluído!

Se você já fez o deploy com sucesso, veja `DEPLOY_FRONTEND_SUCESSO.md` para próximos passos e testes.
