# 📘 Como Usar o render.yaml para Deploy Automático

## 🎯 O que é o render.yaml?

O `render.yaml` é um arquivo de configuração que permite fazer deploy automático na Render.com diretamente do GitHub, sem precisar configurar manualmente no dashboard.

## 📍 Onde está o arquivo?

O arquivo `render.yaml` está na **raiz do projeto** (mesmo nível que `README.md`).

## 🚀 Como Usar (3 Passos Simples)

### Passo 1: Conectar GitHub ao Render

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** no topo
3. Selecione **"Blueprint"** (ou "New from Git Repository")
4. Se ainda não conectou, clique em **"Connect GitHub"** e autorize
5. Selecione o repositório: **Nataliadjf/Comex**
6. Render detectará automaticamente o arquivo `render.yaml` ✅
7. Clique em **"Apply"**

### Passo 2: Criar Banco de Dados PostgreSQL

1. No Render Dashboard, clique em **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `comex-database`
   - **Database**: `comex_db`
   - **User**: `comex_user`
   - **Plan**: Free
4. Clique em **"Create Database"**
5. **IMPORTANTE**: Copie a **"Internal Database URL"**

### Passo 3: Configurar Variável DATABASE_URL

1. Vá para o serviço **"comex-backend"** criado pelo Blueprint
2. Clique em **"Environment"** no menu lateral
3. Encontre a variável `DATABASE_URL`
4. Cole a URL do PostgreSQL que você copiou
5. Clique em **"Save Changes"**

**PRONTO!** O deploy será iniciado automaticamente! 🎉

## 🔄 Deploy Automático

Após configurar uma vez, **todos os pushes para GitHub** disparam deploy automático:

```bash
git add .
git commit -m "Minhas alterações"
git push origin main
```

O Render detecta automaticamente e faz deploy! ✨

## 📋 O que o render.yaml faz?

O arquivo `render.yaml` configura automaticamente:

- ✅ Nome do serviço: `comex-backend`
- ✅ Runtime: Python 3.11
- ✅ Build Command: Instala dependências
- ✅ Start Command: Inicia o servidor FastAPI
- ✅ Health Check: `/health`
- ✅ Variáveis de ambiente básicas
- ✅ Região e plano (free)

## 🛠️ Personalizar o render.yaml

Se quiser alterar algo, edite o arquivo `render.yaml` na raiz e faça commit:

```yaml
services:
  - type: web
    name: comex-backend
    env: python
    region: oregon  # Mude para: frankfurt, singapore, etc.
    plan: free      # Mude para: starter, standard, pro
    # ... resto da configuração
```

## ❓ Dúvidas Frequentes

### Preciso criar o render.yaml manualmente?

Não! Já está criado na raiz do projeto. ✅

### O render.yaml cria o banco de dados automaticamente?

Não, você precisa criar o PostgreSQL manualmente uma vez e configurar a URL.

### Posso ter múltiplos ambientes?

Sim! Crie diferentes branches no Git e configure no Render para fazer deploy de cada branch.

### Como vejo os logs do deploy?

No Render Dashboard, clique no serviço → **"Logs"** → Veja em tempo real!

## 📚 Mais Informações

- Guia completo: `DEPLOY_RENDER_VIA_GIT.md`
- Render Docs: https://render.com/docs/blueprint-spec






