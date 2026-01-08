# Deploy na Render.com - Guia Atualizado

## ✅ Alterações Enviadas para o GitHub

As seguintes melhorias foram commitadas e enviadas para o repositório:

1. **Cards do Dashboard com tamanho uniforme**
2. **Autocomplete para empresas importadoras e exportadoras**
3. **Suporte para múltiplos NCMs na busca**
4. **Busca de dados dos últimos 2 anos (24 meses)**
5. **Atualização diária automática via scheduler**
6. **Tabela detalhada com todos os dados ao final da página**
7. **Scripts para popular banco de dados com dados de exemplo**

## 📋 Passo a Passo para Deploy na Render

### 1. Acessar o Render Dashboard

1. Acesse: https://dashboard.render.com
2. Faça login com sua conta

### 2. Conectar Repositório GitHub

1. No Dashboard do Render, clique em **"New +"**
2. Selecione **"Blueprint"** (se já tiver um serviço, pode usar "New Web Service")
3. Conecte seu repositório GitHub: `Nataliadjf/Comex`
4. O Render detectará automaticamente o arquivo `render.yaml` na raiz

### 3. Configurar Variáveis de Ambiente

Após criar o serviço, configure as seguintes variáveis no Render Dashboard:

#### Variáveis Obrigatórias:

```
DATABASE_URL=postgresql://usuario:senha@host:porta/database
```

**Como obter:**
- Se já tiver um PostgreSQL no Render, copie a Internal Database URL
- Ou crie um novo PostgreSQL no Render:
  - Clique em "New +" → "PostgreSQL"
  - Escolha nome: `comex-database`
  - Plano: Free
  - Copie a Internal Database URL

#### Variáveis Opcionais (já configuradas no render.yaml):

```
COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
COMEX_STAT_API_KEY= (deixe vazio se não tiver)
SECRET_KEY= (será gerado automaticamente)
ENVIRONMENT=production
DEBUG=false
PYTHON_VERSION=3.11
```

### 4. Deploy Automático

O Render fará deploy automático quando você:

1. **Conectar o repositório** - O Render detecta o `render.yaml`
2. **Fazer push para o GitHub** - Cada push aciona um novo deploy
3. **Aguardar o build** - O processo leva cerca de 5-10 minutos

### 5. Verificar Deploy

Após o deploy:

1. Acesse a URL do serviço (ex: `https://comex-backend.onrender.com`)
2. Teste o endpoint de health: `https://seu-backend.onrender.com/health`
3. Deve retornar: `{"status":"healthy","database":"connected"}`

### 6. Atualizar Frontend (se necessário)

Se você também quiser fazer deploy do frontend:

1. No Render Dashboard, clique em "New +" → "Static Site"
2. Conecte o mesmo repositório
3. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/build`
   - **Environment Variable**: `REACT_APP_API_URL=https://seu-backend.onrender.com`

## 🔄 Atualizar Deploy Existente

Se você já tem um serviço rodando no Render:

### Opção 1: Deploy Automático (Recomendado)

1. O Render detecta automaticamente novos commits no GitHub
2. Vá em **"Manual Deploy"** → **"Deploy latest commit"**
3. Aguarde o build completar

### Opção 2: Via Blueprint

1. No Render Dashboard, vá em **"Blueprints"**
2. Selecione seu blueprint
3. Clique em **"Update"**
4. O Render lerá o `render.yaml` atualizado

### Opção 3: Manual

1. Vá no serviço do backend
2. Clique em **"Manual Deploy"**
3. Selecione **"Deploy latest commit"**

## 📝 Arquivo render.yaml

O arquivo `render.yaml` na raiz do projeto está configurado com:

- ✅ Build command usando `requirements-render-ultra-minimal.txt`
- ✅ Start command correto para o backend
- ✅ Health check path configurado
- ✅ Variáveis de ambiente básicas
- ✅ Python 3.11

## ⚠️ Importante

1. **Primeira vez**: Configure manualmente a variável `DATABASE_URL` no Render Dashboard
2. **SECRET_KEY**: Será gerado automaticamente pelo Render
3. **Build pode demorar**: Primeira vez leva cerca de 10-15 minutos
4. **Free tier**: Serviços free "dormem" após 15 minutos de inatividade

## 🐛 Troubleshooting

### Erro de Build

- Verifique os logs no Render Dashboard
- Confirme que `requirements-render-ultra-minimal.txt` existe
- Verifique se o Python 3.11 está disponível

### Erro de Conexão com Banco

- Verifique se `DATABASE_URL` está configurada corretamente
- Confirme que o PostgreSQL está rodando
- Teste a conexão usando o endpoint `/health`

### Deploy não atualiza

- Force um novo deploy manualmente
- Verifique se o commit foi feito no branch `main`
- Confirme que o `render.yaml` está na raiz do projeto

## 📞 Próximos Passos

Após o deploy:

1. ✅ Teste o endpoint `/health`
2. ✅ Teste o endpoint `/dashboard/stats`
3. ✅ Configure o frontend para apontar para a URL do Render
4. ✅ Teste todas as funcionalidades

---

**Última atualização**: 05/01/2026
**Status**: ✅ Pronto para deploy



