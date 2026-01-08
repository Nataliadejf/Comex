# Criar Frontend no Render - Passo a Passo Detalhado

## 🎯 Objetivo

Criar o frontend React como Static Site no Render e conectá-lo ao backend que já está funcionando.

## 📋 Passo a Passo Completo

### PASSO 1: Acessar Render Dashboard

1. **Abra o navegador** e acesse: https://dashboard.render.com
2. **Faça login** na sua conta
3. Você deve ver o dashboard com seus serviços

### PASSO 2: Criar Novo Static Site

1. **Clique no botão "+ New"** (canto superior direito)
2. **Selecione "Static Site"** na lista de opções
3. Você será redirecionado para a página de configuração

### PASSO 3: Conectar Repositório GitHub

Na seção **"Connect a repository"**:

1. **Selecione o repositório:**
   - Se já tiver conectado antes, selecione `Nataliadjf/Comex` da lista
   - Se não tiver, clique em **"Connect account"** e autorize o Render a acessar seu GitHub
   - Depois selecione `Nataliadjf/Comex`

2. **Branch:**
   - Deixe como `main` (já vem preenchido)

3. **Root Directory:**
   - **IMPORTANTE:** Digite `frontend` (sem aspas)
   - Isso indica que o código do frontend está na pasta `frontend/`

### PASSO 4: Configurar Build

Preencha os campos:

1. **Name:**
   - Digite: `comex-frontend` (ou outro nome de sua preferência)

2. **Build Command:**
   - Digite: `npm install && npm run build`
   - Isso instala as dependências e compila o React

3. **Publish Directory:**
   - Digite: `build`
   - Isso indica onde o React gera os arquivos estáticos após o build

4. **Plan:**
   - Selecione: `Free` (plano gratuito)

### PASSO 5: Configurar Environment Variables

1. **Clique em "Advanced"** (abaixo dos campos de build)
2. **Clique em "+ Add Environment Variable"**
3. **Adicione a variável:**
   - **Key:** `REACT_APP_API_URL`
   - **Value:** `https://comex-backend-wjco.onrender.com`
   - Clique em **"Save"**

### PASSO 6: Criar o Static Site

1. **Revise todas as configurações:**
   - ✅ Repositório: `Nataliadjf/Comex`
   - ✅ Branch: `main`
   - ✅ Root Directory: `frontend`
   - ✅ Build Command: `npm install && npm run build`
   - ✅ Publish Directory: `build`
   - ✅ Environment Variable: `REACT_APP_API_URL` = `https://comex-backend-wjco.onrender.com`

2. **Clique em "Create Static Site"** (botão no final da página)

### PASSO 7: Aguardar o Build

1. **Você será redirecionado** para a página do serviço
2. **Aguarde o build completar** (5-10 minutos)
3. **Monitore os logs** clicando em "Logs" no menu lateral

### PASSO 8: Verificar Deploy

Após o build:

1. **Você receberá uma URL** como: `https://comex-frontend.onrender.com`
2. **Acesse a URL** no navegador
3. **Você deve ver** a tela de login do aplicativo

## ✅ Checklist Final

- [ ] Static Site criado no Render
- [ ] Repositório GitHub conectado
- [ ] Root Directory configurado como `frontend`
- [ ] Build Command: `npm install && npm run build`
- [ ] Publish Directory: `build`
- [ ] `REACT_APP_API_URL` configurada com URL do backend
- [ ] Deploy concluído
- [ ] Frontend acessível via URL
- [ ] Tela de login aparecendo

## 🐛 Troubleshooting

### Problema: Build falha

**Solução:**
- Verifique os logs do build
- Confirme que o Root Directory está como `frontend`
- Verifique se o Build Command está correto

### Problema: Frontend não conecta ao backend

**Solução:**
- Verifique se `REACT_APP_API_URL` está configurada corretamente
- Use a URL completa: `https://comex-backend-wjco.onrender.com`
- Faça um novo deploy após alterar variáveis

### Problema: Página em branco

**Solução:**
- Abra o Console do Navegador (F12)
- Verifique erros no console
- Verifique se o build foi concluído com sucesso

## 📝 Notas Importantes

1. **Variáveis de Ambiente:**
   - Variáveis que começam com `REACT_APP_` são injetadas no build
   - Após alterar variáveis, é necessário fazer novo build

2. **Build Time:**
   - O build do React pode levar 5-10 minutos
   - Seja paciente durante o primeiro deploy

3. **URLs:**
   - O Render gera URLs automáticas
   - Você pode configurar um domínio customizado depois

---

**Última atualização**: 05/01/2026



