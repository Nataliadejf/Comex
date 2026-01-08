# Corrigir Rotas do Frontend no Render

## 🔍 Problema

O erro "Not Found" acontece porque o Render não está configurado para servir rotas do React Router corretamente. Quando você acessa `/login`, o servidor tenta encontrar um arquivo físico `/login`, mas não existe - as rotas são gerenciadas pelo React Router no cliente.

## ✅ Solução

### Opção 1: Arquivo _redirects (Recomendado)

1. **Crie o arquivo `frontend/public/_redirects`** com:
   ```
   /*    /index.html   200
   ```

2. **Faça commit e push:**
   ```bash
   git add frontend/public/_redirects
   git commit -m "fix: Adicionar _redirects para rotas React Router"
   git push origin main
   ```

3. **Aguarde o deploy automático** ou faça deploy manual

### Opção 2: Configurar Redirects no Render Dashboard

1. **No Render Dashboard:**
   - Acesse o serviço do frontend (`comex-4` ou similar)
   - Vá em **"Redirects/Rewrites"** (menu lateral)
   - Clique em **"+ Add Redirect"**

2. **Configure:**
   - **Source Path:** `/*`
   - **Destination:** `/index.html`
   - **Status Code:** `200`
   - Clique em **"Save"**

3. **Faça um novo deploy** do frontend

## 📋 Passo a Passo Detalhado

### Método 1: Arquivo _redirects (Mais Simples)

1. **Crie o arquivo:**
   - Caminho: `frontend/public/_redirects`
   - Conteúdo: `/*    /index.html   200`

2. **Commit e Push:**
   ```bash
   git add frontend/public/_redirects
   git commit -m "fix: Adicionar _redirects para rotas React Router"
   git push origin main
   ```

3. **Aguarde o deploy automático** (2-5 minutos)

### Método 2: Via Render Dashboard

1. **Acesse o Render Dashboard:**
   - Vá para o serviço do frontend
   - Clique em **"Redirects/Rewrites"** no menu lateral

2. **Adicione Redirect:**
   - Clique em **"+ Add Redirect"**
   - **Source Path:** `/*`
   - **Destination:** `/index.html`
   - **Status Code:** `200`
   - Clique em **"Save"**

3. **Faça Deploy Manual:**
   - Clique em **"Manual Deploy"**
   - Selecione **"Deploy latest commit"**

## ✅ Verificar se Funcionou

Após aplicar a correção:

1. **Acesse:** `https://comex-4.onrender.com/login`
2. **Deve aparecer** a tela de login (não mais "Not Found")
3. **Teste outras rotas:**
   - `/dashboard`
   - `/busca`
   - Qualquer rota deve funcionar

## 🐛 Troubleshooting

### Problema: Ainda aparece "Not Found"

**Solução:**
- Verifique se o arquivo `_redirects` está em `frontend/public/`
- Verifique se o arquivo foi commitado e enviado para o GitHub
- Aguarde o deploy completar completamente
- Limpe o cache do navegador (Ctrl+Shift+R)

### Problema: Redirects não funcionam

**Solução:**
- Verifique se o redirect está configurado corretamente no Render
- Certifique-se de que o Status Code é `200` (não 301 ou 302)
- Faça um novo deploy após configurar redirects

## 📝 Notas Importantes

1. **Arquivo _redirects:**
   - Deve estar em `frontend/public/_redirects`
   - Será copiado para `build/` durante o build
   - O Render detecta automaticamente este arquivo

2. **Redirects no Dashboard:**
   - São aplicados imediatamente após salvar
   - Não requerem novo build
   - São mais fáceis de gerenciar

---

**Última atualização**: 05/01/2026



