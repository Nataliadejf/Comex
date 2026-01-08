# 🚀 Fazer Deploy no Render AGORA (Passo a Passo)

## ⚠️ Status Atual

- ✅ Código preparado e no GitHub
- ✅ render.yaml criado
- ✅ Requirements configurados
- ❌ **Deploy ainda NÃO foi feito no Render**

## 🎯 Vamos Fazer o Deploy Agora!

### Passo 1: Acessar Render Dashboard

1. Abra seu navegador
2. Vá para: **https://dashboard.render.com**
3. Faça login (se ainda não fez)

### Passo 2: Conectar Repositório GitHub

1. No Render Dashboard, clique no botão **"New +"** (canto superior direito)
2. Selecione **"Blueprint"** (ou procure por "New from Git Repository")
3. Se ainda não conectou GitHub:
   - Clique em **"Connect GitHub"** ou **"Connect account"**
   - Autorize o Render a acessar seus repositórios
   - Selecione **"Nataliadjf/Comex"**
4. Se já conectou:
   - Selecione o repositório **"Nataliadjf/Comex"** da lista

### Passo 3: Render Detecta render.yaml

1. O Render detectará automaticamente o arquivo `render.yaml` na raiz
2. Você verá uma prévia da configuração:
   - Serviço: `comex-backend`
   - Tipo: Web Service
   - Build Command: (já configurado)
   - Start Command: (já configurado)
3. Clique em **"Apply"** ou **"Create"**

### Passo 4: Criar Banco de Dados PostgreSQL

1. No Render Dashboard, clique em **"New +"** novamente
2. Selecione **"PostgreSQL"**
3. Configure:
   ```
   Name: comex-database
   Database: comex_db
   User: comex_user
   Plan: Free
   Region: Oregon (ou mais próximo de você)
   ```
4. Clique em **"Create Database"**
5. **IMPORTANTE**: Aguarde alguns segundos e copie a **"Internal Database URL"**
   - Será algo como: `postgresql://user:pass@host:5432/dbname`

### Passo 5: Configurar Variável DATABASE_URL

1. Volte para o serviço **"comex-backend"** criado no Passo 3
2. Clique em **"Environment"** no menu lateral esquerdo
3. Role até encontrar a variável `DATABASE_URL`
4. Clique para editar
5. Cole a URL do PostgreSQL que você copiou no Passo 4
6. Clique em **"Save Changes"**

### Passo 6: Aguardar Deploy

1. O Render iniciará automaticamente o build
2. Vá para a aba **"Logs"** para acompanhar em tempo real
3. Aguarde alguns minutos (primeiro deploy pode demorar 5-10 minutos)
4. Quando concluir, você verá:
   - Status: **Live**
   - URL do serviço: `https://comex-backend.onrender.com`

### Passo 7: Testar

1. Acesse a URL do serviço
2. Teste o endpoint de health:
   ```
   https://comex-backend.onrender.com/health
   ```
3. Deve retornar: `{"status": "healthy"}`

## ✅ Pronto!

Agora o deploy está feito e **todos os pushes futuros** no GitHub dispararão deploy automático!

## 🐛 Problemas?

### Erro: "Build failed"
- Verifique os logs no Render
- Confirme que o `requirements-render-ultra-minimal.txt` está correto

### Erro: "Cannot connect to database"
- Verifique se o PostgreSQL está criado
- Confirme que `DATABASE_URL` está configurada corretamente
- Use a **"Internal Database URL"** (não a externa)

### Erro: "Module not found"
- Verifique se todas as dependências estão no requirements
- Confirme que o `rootDir` está correto no render.yaml

## 📞 Precisa de Ajuda?

Se encontrar algum problema, me envie:
1. Screenshot do erro
2. Logs do build (copie e cole)
3. Qual passo você estava fazendo

## 🎉 Depois do Deploy

Após o deploy funcionar, você pode:
- Fazer alterações no código
- Fazer commit e push: `git push origin main`
- Render fará deploy automático! ✨






