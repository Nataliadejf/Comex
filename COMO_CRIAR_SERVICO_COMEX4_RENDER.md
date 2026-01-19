# Como Criar o Serviço comex-4 no Render

## 📋 Visão Geral

O serviço `comex-4` precisa ser criado manualmente no Render Dashboard. Este guia explica como fazer isso.

## 🚀 Passo a Passo

### Opção 1: Usar Blueprint (Recomendado)

1. **Acesse o Render Dashboard**
   - Vá para: https://dashboard.render.com
   - Faça login na sua conta

2. **Criar Novo Blueprint**
   - Clique em **"Blueprints"** no menu lateral
   - Clique em **"New Blueprint"**
   - Conecte ao repositório GitHub: `Nataliadjf/Comex`
   - O Render detectará automaticamente o arquivo `render.yaml`

3. **Aplicar Blueprint**
   - O Render criará automaticamente o serviço `comex-backend`
   - Você pode renomear o serviço para `comex-4` nas configurações

### Opção 2: Criar Manualmente

1. **Acesse o Render Dashboard**
   - Vá para: https://dashboard.render.com
   - Faça login na sua conta

2. **Criar Novo Web Service**
   - Clique em **"New +"** no canto superior direito
   - Selecione **"Web Service"**

3. **Conectar Repositório**
   - Escolha **"Connect GitHub"** ou **"Connect GitLab"**
   - Autorize o Render a acessar seus repositórios
   - Selecione o repositório: `Nataliadjf/Comex`
   - Escolha o branch: `main`

4. **Configurar Serviço**
   - **Name**: `comex-4`
   - **Region**: `Oregon` (ou sua preferência)
   - **Branch**: `main`
   - **Root Directory**: `.` (raiz do projeto)
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install --upgrade pip setuptools wheel && pip install --only-binary :all: --no-cache-dir -r backend/requirements-render-ultra-minimal.txt 2>&1 || pip install --no-build-isolation --no-cache-dir -r backend/requirements-render-ultra-minimal.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
     ```

5. **Configurar Variáveis de Ambiente**
   - Clique em **"Advanced"** > **"Environment Variables"**
   - Adicione as seguintes variáveis:
     - `PYTHON_VERSION`: `3.11.0`
     - `ENVIRONMENT`: `production`
     - `DEBUG`: `false`
     - `DATABASE_URL`: (configure após criar PostgreSQL, se necessário)
     - `SECRET_KEY`: (gere uma chave secreta)
     - `COMEX_STAT_API_URL`: `https://comexstat.mdic.gov.br`

6. **Criar Serviço**
   - Clique em **"Create Web Service"**
   - O Render iniciará o build e deploy automaticamente

## 🔧 Usar Serviço Existente

Se você preferir usar um dos serviços existentes:

### comex-backend (Python 3)
- Este é o serviço principal configurado no `render.yaml`
- Já está conectado ao GitHub
- Faz deploy automático quando você faz push

### Para Renomear um Serviço Existente

1. Acesse o serviço no Render Dashboard
2. Vá para **"Settings"**
3. Clique em **"Change Name"**
4. Digite `comex-4`
5. Salve as alterações

## ⚠️ Importante

- **Plano Free**: O serviço pode "dormir" após 15 minutos de inatividade
- **Primeira Requisição**: Pode demorar 30-60 segundos para "acordar"
- **Deploy Automático**: O Render faz deploy automático quando você faz push para o GitHub

## 🔍 Verificar Deploy

Após criar o serviço:

1. **Acompanhar Build**
   - Vá para a aba **"Events"** ou **"Logs"**
   - Você verá o progresso do build

2. **Verificar Health Check**
   - Após o deploy, teste: `https://comex-4.onrender.com/health`
   - Deve retornar: `{"status":"healthy","database":"connected"}`

3. **Verificar Logs**
   - Se houver erros, verifique a aba **"Logs"**
   - Os logs mostram erros detalhados

## 🐛 Troubleshooting

### Erro: "NameError: name 'pd' is not defined"
- ✅ **Corrigido**: pandas foi adicionado ao requirements
- ✅ **Corrigido**: type hints foram ajustados

### Erro: "Failed deploy"
- Verifique os logs do Render
- Certifique-se de que todas as dependências estão no `requirements-render-ultra-minimal.txt`
- Verifique se o `render.yaml` está correto

### Serviço não aparece
- Verifique se você está na workspace correta
- Verifique se o serviço não está suspenso
- Tente criar um novo serviço manualmente

## 📝 Arquivos Importantes

- `render.yaml` - Configuração do Blueprint
- `backend/requirements-render-ultra-minimal.txt` - Dependências Python
- `backend/main.py` - Aplicação FastAPI principal

## 🔗 Links Úteis

- **Render Dashboard**: https://dashboard.render.com
- **Documentação Render**: https://render.com/docs
- **GitHub Repositório**: https://github.com/Nataliadjf/Comex

