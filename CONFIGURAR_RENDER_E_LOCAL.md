# 📋 Guia Completo: Configurar Variáveis de Ambiente - Render + Local

## 📌 Resumo Rápido

Você precisa configurar:
- **Backend** (FastAPI) no Render → 5 variáveis de ambiente
- **Frontend** (React) no Render → 1 variável de ambiente + 1 build env
- **Banco de dados** PostgreSQL no Render → URL de conexão
- **Local** (para testes) → arquivo `.env` no backend

---

## 🔧 PARTE 1: Banco de Dados PostgreSQL no Render

### Passo 1: Criar Database PostgreSQL no Render

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **+ New** → **PostgreSQL**
3. Preencha:
   - **Name**: `comex-db` (ou seu projeto)
   - **Database**: `comexdb`
   - **User**: `comexuser` (anote bem!)
   - **Region**: Escolha a mesma do backend
   - **PostgreSQL Version**: 16 (ou a mais recente)
4. Clique em **Create Database**

### Passo 2: Copiar a URL de Conexão

Após criação, você terá algo como:
```
postgresql://comexuser:SEU_PASSWORD_ALEATORIO@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb
```

⚠️ **Guarde esta URL** - você usará em:
- Backend (`DATABASE_URL`)
- Scripts de importação local

---

## 🚀 PARTE 2: Configurar Backend no Render

### Passo 1: Criar Web Service Backend

1. No Render Dashboard, clique **+ New** → **Web Service**
2. Conecte ao seu repositório GitHub (`Nataliadejf/comex`)
3. Preencha:
   - **Name**: `comex-backend` (ou similar)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r backend/requirements-render-ultra-minimal.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region**: Escolha uma próxima à DB
   
   ⚠️ *Se o serviço já existir e estiver usando outra buildCommand, atualize-o manualmente
   no painel Render (Settings → Build & Deploy → Build Command).  Caso você não consiga
   alterar, a presença de `loguru` no arquivo `requirements.txt` na raiz garante que ele
   seja instalado mesmo que o comando esteja errado.*
4. Clique **Create Web Service**

### Passo 2: Adicionar Variáveis de Ambiente no Render

Após criação, acesse **Settings** → **Environment** do serviço backend

Adicione estas variáveis (**obrigatórias**):

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `DATABASE_URL` | `postgresql://comexuser:PASSWORD@dpg-xxxxx...` | URL do PostgreSQL (copiada no Passo anterior) |
| `SECRET_KEY` | Gere com: `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Chave secreta para JWT/sessões |
| `ENVIRONMENT` | `production` | Modo de produção |
| `DEBUG` | `False` | Desabilitar debug em produção |
| `COMEX_STAT_API_URL` | `https://api-comexstat.mdic.gov.br` | API oficial MDIC (opcional) |
| `COMEX_STAT_API_KEY` | *(deixe em branco se não tiver)* | Chave da API MDIC (opcional) |
| `AUTO_IMPORT_EXCEL_ON_START` | `true` | Auto-importar arquivo Excel na inicialização |
| `AUTO_IMPORT_EXCEL_ONLY_IF_EMPTY` | `true` | Só importar se banco vazio |
| `AUTO_IMPORT_EXCEL_CLEAR_BY_FILE` | `true` | Limpar dados do arquivo antes de reimportar |
| `AUTO_IMPORT_EXCEL_FILENAME` | `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx` | Nome do arquivo Excel a importar |

✅ **Clique em "Save"**

### Passo 3: Deploy automático

- Qualquer push para branch `main` vai triggerar build automático
- Aguarde ~5 minutos para deploy completar
- Acesse: `https://comex-backend-xxxx.onrender.com/docs` (Swagger)

---

## 🎨 PARTE 3: Configurar Frontend no Render

### Passo 1: Criar Static Site Frontend

1. No Render Dashboard, clique **+ New** → **Static Site**
2. Conecte ao mesmo repositório GitHub
3. Preencha:
   - **Name**: `comex-frontend` (ou similar)
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish directory**: `frontend/build`
   - **Region**: Mesma do backend
4. Clique **Create Static Site**

### Passo 2: Adicionar Variáveis de Ambiente do Build

Acesse **Settings** → **Environment** do frontend

Adicione:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `REACT_APP_API_URL` | `https://comex-backend-xxxx.onrender.com` | URL do seu backend no Render |

⚠️ Substitua `comex-backend-xxxx` pelo nome real do seu backend

✅ **Clique em "Save"**

### Passo 3: Verificar Deploy

- Frontend será deployado automaticamente em `https://comex-frontend-xxxx.onrender.com`
- Demora ~2-3 minutos para build completar
- Verá na tela inicial da app os dados sendo carregados do seu backend

---

## 💻 PARTE 4: Configurar Local (para testes)

### Passo 1: Criar arquivo `.env` no backend

Crie/edite `backend/.env`:

```dotenv
# Ambiente
ENVIRONMENT=development
DEBUG=True

# Database - IMPORTANTE: Use a URL do PostgreSQL do Render aqui também em desenvolvimento
DATABASE_URL=postgresql://comexuser:PASSWORD@dpg-xxxxx-a.oregon-postgres.render.com:5432/comexdb

# Ou para testes locais com SQLite (sem PostgreSQL instalado):
# DATABASE_URL=sqlite:///./comex.db

# API
COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br
COMEX_STAT_API_KEY=

# Autenticação
SECRET_KEY=sua-chave-secreta-local-pode-ser-qualquer-coisa

# Diretório de dados
DATA_DIR=./comex_data

# Logging
LOG_LEVEL=INFO
LOG_DIR=./comex_data/logs

# Auto-import
AUTO_IMPORT_EXCEL_ON_START=true
AUTO_IMPORT_EXCEL_ONLY_IF_EMPTY=true
AUTO_IMPORT_EXCEL_FILENAME=H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx
```

### Passo 2: Criar arquivo `.env` no frontend

Crie/edite `frontend/.env`:

```dotenv
REACT_APP_API_URL=http://localhost:8000
```

(Para apontar para backend local)

### Passo 3: Testar Localmente

```powershell
# Terminal 1 - Backend
cd c:\Users\User\Desktop\Cursor\Projetos\projeto_comex\backend
python -m pip install -r requirements.txt
python run.py

# Terminal 2 - Frontend
cd c:\Users\User\Desktop\Cursor\Projetos\projeto_comex\frontend
npm install
npm start
```

- Backend roda em: `http://localhost:8000`
- Frontend roda em: `http://localhost:3000`
- Swagger (API docs): `http://localhost:8000/docs`

---

## 🔐 Variáveis Secretas - Valores Recomendados

### SECRET_KEY (use para ambos local e Render)

```powershell
# Gerar uma chave segura:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Saída será algo como: `abcdefg1234567890_ABCDEFGhijklmnop`

Use **o mesmo valor** em:
- `.env` local
- Render Backend → `SECRET_KEY` environment variable

---

## 📊 Checklist de Configuração

### Backend ✅
- [ ] Database PostgreSQL criado no Render
- [ ] Web Service backend criado no Render
- [ ] `DATABASE_URL` configurada
- [ ] `SECRET_KEY` configurada
- [ ] `ENVIRONMENT=production` e `DEBUG=False`
- [ ] Auto-import Excel configurado
- [ ] Backend rodando e acessível em `https://comex-backend-xxxx.onrender.com`

### Frontend ✅
- [ ] Static Site frontend criado no Render
- [ ] `REACT_APP_API_URL` apontando para backend do Render
- [ ] Frontend deployado e acessível em `https://comex-frontend-xxxx.onrender.com`

### Local ✅
- [ ] Arquivo `backend/.env` criado
- [ ] Arquivo `frontend/.env` criado
- [ ] `DATABASE_URL` local configurada
- [ ] Backend roda localmente sem erros
- [ ] Frontend roda localmente sem erros

---

## 🚨 Troubleshooting

### Git push retorna 403 Forbidden

Se você recebe um erro como:

```
fatal: unable to access 'https://github.com/Nataliadejf/comex.git/': The requested URL returned error: 403
```

Significa que as credenciais usadas pelo Git não estão autorizadas. As causas
mais comuns são:

1. **Token expirado/errado**: crie um novo Personal Access Token (PAT) no GitHub
   com escopo `repo`, então atualize o remoto:
   ```powershell
   git remote set-url origin "https://<USER>:<NEW_TOKEN>@github.com/Nataliadejf/comex.git"
   ```
2. **Cache de credenciais do Windows**: limpe com `git credential-manager reject https://github.com`
   ou use `git config --global credential.helper manager-core` e repita o push.
3. **Prefira SSH**: gere e adicione sua chave pública em GitHub e então use
   `git@github.com:Nataliadejf/comex.git` como remote.

Nunca execute `buildCommand:` no PowerShell – aquilo faz parte da configuração
do serviço no Render, não é um comando de terminal. O erro que aparece
após tentar executar `buildCommand:` é normal e não tem relação com o deploy.

### Erro durante deploy: módulo não encontrado (ex.: loguru)

O log do deploy indica:

```
ModuleNotFoundError: No module named 'loguru'
```

Isso quer dizer que o `pip install` executado pelo Render não instalou
`loguru`. confirme que:

- O `requirements-render-ultra-minimal.txt` (ou o ficheiro que você está
  referenciando na build) contém a linha `loguru==0.6.0`.
- O **Build Command** do serviço backend está definido para instalar esse
  ficheiro dentro de `backend/`:
  ```yaml
  buildCommand: cd backend && pip install -r requirements-render-ultra-minimal.txt
  ```

Após corrigir, faça push e o deploy vai disparar novamente.


### Frontend não consegue fazer chamadas ao backend

**Problema**: CORS error ou 404 nas requisições

**Solução**:
```powershell
# Verificar que REACT_APP_API_URL está correto:
# No Render: frontend/.env ou build environment
# REACT_APP_API_URL devem ser exatamente o URL do backend

# Lembrete: After changing .env, rebuild: npm run build
```

### Backend não consegue conectar ao banco de dados

**Problema**: `ERROR: could not connect to server: timeout`

**Solução**:
1. Confirme `DATABASE_URL` está correta
2. Aguarde 1 minuto após criar o Database (toma tempo para iniciar)
3. Teste conexão localmente:

```powershell
# Instalar psycopg2
pip install psycopg2-binary

# Testar:
python -c "import psycopg2; conn = psycopg2.connect('DATABASE_URL'); print('OK')"
```

### Auto-import não está funcionando

**Problema**: Dados não aparecem após deploy

**Solução**:
1. Verifique `AUTO_IMPORT_EXCEL_FILENAME` está igual ao arquivo atual
2. Confirme arquivo Excel existe em `backend/data/`
3. Check logs no Render:
   - Menu **Logs** do serviço backend
   - Procure por `Auto-import` ou mensagens de erro

---

## 📝 Arquivos Importantes a Manter

Certifique-se que NÃO estão no `.gitignore`:
- `backend/.env.example` ✅
- `frontend/.env*` (os reais podem estar ignorados)

⚠️ Nunca commite arquivos `.env` com senhas reais!

---

## ✅ Próximas Ações

1. **Configure tudo acima** → Backend + Frontend + DB no Render
2. **Teste em produção** → Acesse `https://comex-frontend-xxxx.onrender.com`
3. **Monitore logs** → Render Dashboard → Logs aba
4. **Commite mudanças** → Git push dispara novo deploy automático

---

## 📞 Referências

- **Render Docs**: https://render.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **PostgreSQL em Render**: https://render.com/docs/databases
- **React Environment Variables**: https://create-react-app.dev/docs/adding-custom-environment-variables/

---

**Última atualização**: 28/02/2026 — Deploy trigger com endpoint /dashboard/stats (filtros plenamente funcionais)
