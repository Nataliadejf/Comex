# 🚀 Deploy Automático na Render.com via Git

Este guia mostra como fazer deploy automático do projeto na Render.com conectando diretamente ao GitHub.

## 📋 Pré-requisitos

- ✅ Conta no GitHub (você já tem: https://github.com/Nataliadjf/Comex)
- ✅ Conta no Render.com
- ✅ Código já commitado e pushado no GitHub

## 🎯 Método 1: Deploy via render.yaml (Recomendado)

### Passo 1: Verificar arquivo render.yaml

O arquivo `render.yaml` já está criado na raiz do projeto. Ele contém toda a configuração necessária.

### Passo 2: Conectar GitHub ao Render

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** no topo
3. Selecione **"Blueprint"** (ou procure por "New from Git Repository")
4. Conecte sua conta GitHub (se ainda não conectou)
5. Selecione o repositório: **Nataliadjf/Comex**
6. Render detectará automaticamente o arquivo `render.yaml`
7. Clique em **"Apply"**

### Passo 3: Configurar Banco de Dados

1. No Render Dashboard, clique em **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `comex-database`
   - **Database**: `comex_db`
   - **User**: `comex_user`
   - **Plan**: Free (ou outro de sua escolha)
4. Clique em **"Create Database"**
5. **Copie a "Internal Database URL"** (será algo como: `postgresql://user:pass@host:5432/dbname`)

### Passo 4: Configurar Variáveis de Ambiente

1. Vá para o serviço **"comex-backend"**
2. Clique em **"Environment"** no menu lateral
3. Configure as variáveis:

```
DATABASE_URL = [cole a URL do PostgreSQL que você copiou]
SECRET_KEY = [Render já gerou automaticamente, mas você pode alterar]
COMEX_STAT_API_URL = https://comexstat.mdic.gov.br
COMEX_STAT_API_KEY = [deixe vazio se não tiver]
ENVIRONMENT = production
DEBUG = false
```

### Passo 5: Aguardar Deploy

1. O Render iniciará automaticamente o build
2. Acompanhe os logs em tempo real
3. Quando concluir, você verá a URL do serviço (ex: `https://comex-backend.onrender.com`)

## 🎯 Método 2: Deploy Manual (Alternativo)

Se o método via Blueprint não funcionar:

### Passo 1: Criar Web Service

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** → **"Web Service"**
3. Conecte GitHub e selecione o repositório **Nataliadjf/Comex**
4. Configure:

```
Name: comex-backend
Region: Oregon (ou mais próximo de você)
Branch: main
Root Directory: (deixe vazio)
Runtime: Python 3
Build Command: pip install --upgrade pip && pip install -r backend/requirements-render-ultra-minimal.txt
Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Passo 2: Configurar Environment Variables

Na mesma página, role até **"Environment Variables"** e adicione:

```
DATABASE_URL = [URL do PostgreSQL]
SECRET_KEY = [gere uma chave aleatória]
COMEX_STAT_API_URL = https://comexstat.mdic.gov.br
ENVIRONMENT = production
DEBUG = false
```

### Passo 3: Criar PostgreSQL

1. Clique em **"New +"** → **"PostgreSQL"**
2. Configure e copie a URL
3. Volte ao Web Service e cole a URL em `DATABASE_URL`

## 🔄 Deploy Automático (CI/CD)

Após configurar, **todos os pushes para a branch `main`** no GitHub **dispararão automaticamente um novo deploy** no Render!

### Como funciona:

1. Você faz alterações no código
2. Commit e push para GitHub:
   ```bash
   git add .
   git commit -m "Minhas alterações"
   git push origin main
   ```
3. Render detecta automaticamente o push
4. Inicia build e deploy automaticamente
5. Você recebe notificação quando concluir

## 🧪 Testar o Deploy

Após o deploy concluir:

1. Acesse: `https://comex-backend.onrender.com`
2. Teste o endpoint de health:
   ```
   https://comex-backend.onrender.com/health
   ```
3. Deve retornar: `{"status": "healthy"}`

## 📝 Estrutura do render.yaml

O arquivo `render.yaml` na raiz do projeto contém:

- ✅ Configuração do serviço web (FastAPI)
- ✅ Build e Start commands
- ✅ Variáveis de ambiente
- ✅ Health check path
- ✅ Configurações de Python

## 🐛 Troubleshooting

### Erro: "Build failed"

- Verifique os logs no Render Dashboard
- Confirme que o `requirements-render-ultra-minimal.txt` está correto
- Verifique se todas as dependências estão listadas

### Erro: "Cannot connect to database"

- Verifique se o PostgreSQL está criado
- Confirme que `DATABASE_URL` está configurada corretamente
- Use a "Internal Database URL" (não a externa)

### Erro: "Module not found"

- Verifique se todas as dependências estão no `requirements-render-ultra-minimal.txt`
- Confirme que o `rootDir` está correto

## 📚 Links Úteis

- Render Dashboard: https://dashboard.render.com
- Render Docs: https://render.com/docs
- Seu Repositório: https://github.com/Nataliadjf/Comex

## ✅ Checklist Final

- [ ] Repositório conectado ao Render
- [ ] PostgreSQL criado
- [ ] Variáveis de ambiente configuradas
- [ ] Build concluído com sucesso
- [ ] Health check retornando OK
- [ ] Deploy automático funcionando

