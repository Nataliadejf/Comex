# 🚀 Passo a Passo Completo - Deploy na Render.com

## 📋 Pré-requisitos

- [ ] Conta no GitHub (gratuita)
- [ ] Código do projeto commitado no GitHub
- [ ] Conta na Render.com (gratuita)

---

## PASSO 1: Preparar o Código no GitHub

### 1.1. Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Nome do repositório: `comex-analyzer` (ou outro nome)
3. Marque como **Público** (para plano gratuito) ou **Privado**
4. Clique em **Create repository**

### 1.2. Fazer Upload do Código

**Opção A: Via GitHub Desktop (Mais Fácil)**
1. Baixe GitHub Desktop: https://desktop.github.com/
2. Instale e faça login
3. Clique em **File > Add Local Repository**
4. Selecione a pasta `projeto_comex`
5. Faça commit e push

**Opção B: Via Git no Terminal**
```bash
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
git init
git add .
git commit -m "Primeiro commit"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/comex-analyzer.git
git push -u origin main
```

**Opção C: Via Interface Web do GitHub**
1. No GitHub, clique em **uploading an existing file**
2. Arraste toda a pasta `projeto_comex`
3. Faça commit

---

## PASSO 2: Criar Conta na Render.com

1. Acesse: https://render.com
2. Clique em **Get Started for Free**
3. Faça login com GitHub (recomendado) ou email
4. Confirme seu email se necessário

---

## PASSO 3: Criar Banco de Dados PostgreSQL

1. No dashboard da Render, clique em **New +**
2. Selecione **PostgreSQL**
3. Configure:
   - **Name**: `comex-db`
   - **Database**: `comex`
   - **User**: `comex_user`
   - **Region**: Escolha mais próxima (ex: `Oregon (US West)`)
   - **Plan**: **Free** (para começar)
4. Clique em **Create Database**
5. ⚠️ **IMPORTANTE**: Copie a **Internal Database URL** (você vai precisar depois)
   - Exemplo: `postgresql://comex_user:senha@dpg-xxxxx-a.oregon-postgres.render.com/comex`

---

## PASSO 4: Deploy do Backend

### 4.1. Criar Web Service

1. No dashboard, clique em **New +**
2. Selecione **Web Service**
3. Conecte seu repositório GitHub:
   - Se não aparecer, clique em **Configure account**
   - Autorize acesso ao repositório `comex-analyzer`
   - Selecione o repositório

### 4.2. Configurar Backend

**Configurações Básicas:**
- **Name**: `comex-backend`
- **Region**: Mesma do banco de dados
- **Branch**: `main` (ou `master`)
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables** (clique em **Advanced**):
```
DATABASE_URL=<cole a Internal Database URL do passo 3>
SECRET_KEY=<gere uma chave aleatória>
COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
```

**Como gerar SECRET_KEY:**
- Acesse: https://randomkeygen.com/
- Copie uma chave da seção "CodeIgniter Encryption Keys"
- Ou use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 4.3. Deploy

1. Clique em **Create Web Service**
2. Aguarde o build (pode levar 5-10 minutos)
3. ✅ Quando aparecer "Your service is live", anote a URL:
   - Exemplo: `https://comex-backend.onrender.com`

---

## PASSO 5: Deploy do Frontend

### 5.1. Criar Static Site

1. No dashboard, clique em **New +**
2. Selecione **Static Site**
3. Conecte o mesmo repositório GitHub

### 5.2. Configurar Frontend

**Configurações:**
- **Name**: `comex-frontend`
- **Branch**: `main` (ou `master`)
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`

**Environment Variables**:
```
REACT_APP_API_URL=https://comex-backend.onrender.com
```
⚠️ **Use a URL do backend que você anotou no passo 4.3**

### 5.3. Deploy

1. Clique em **Create Static Site**
2. Aguarde o build (pode levar 5-10 minutos)
3. ✅ Quando aparecer "Your site is live", anote a URL:
   - Exemplo: `https://comex-frontend.onrender.com`

---

## PASSO 6: Atualizar Backend com URL do Frontend (CORS)

### 6.1. Atualizar CORS no Backend

1. No dashboard da Render, vá em **comex-backend**
2. Clique em **Environment**
3. Adicione nova variável:
   ```
   FRONTEND_URL=https://comex-frontend.onrender.com
   ```
4. Clique em **Save Changes**
5. O backend vai reiniciar automaticamente

### 6.2. Atualizar código (opcional, para melhor segurança)

Edite `backend/main.py`:
```python
# Linha 35, substitua:
allow_origins=["*"],

# Por:
allow_origins=[
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://comex-frontend.onrender.com")
],
```

Faça commit e push:
```bash
git add backend/main.py
git commit -m "Atualizar CORS para produção"
git push
```

---

## PASSO 7: Inicializar Banco de Dados

### 7.1. Via Render Shell

1. No dashboard, vá em **comex-backend**
2. Clique na aba **Shell**
3. Execute:
```bash
cd backend
python -c "from database import init_db; init_db()"
```

### 7.2. Ou via Script Local

1. Atualize `.env` local com a URL do banco:
```
DATABASE_URL=postgresql://comex_user:senha@dpg-xxxxx-a.oregon-postgres.render.com/comex
```

2. Execute localmente:
```bash
cd backend
python -c "from database import init_db; init_db()"
```

---

## PASSO 8: Testar Aplicação

1. Acesse a URL do frontend: `https://comex-frontend.onrender.com`
2. Teste login/cadastro
3. Teste busca de dados
4. Verifique se está conectando ao backend

---

## ✅ Checklist Final

- [ ] Repositório no GitHub criado e código enviado
- [ ] Conta Render.com criada
- [ ] Banco PostgreSQL criado
- [ ] Backend deployado e funcionando
- [ ] Frontend deployado e funcionando
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados inicializado
- [ ] Aplicação testada e funcionando

---

## 🔧 Troubleshooting

### Erro: "Build failed"
- Verifique se `requirements.txt` está correto
- Verifique logs do build na Render

### Erro: "Database connection failed"
- Verifique se `DATABASE_URL` está correto
- Use a **Internal Database URL** (não a externa)

### Erro: "Frontend não conecta ao backend"
- Verifique se `REACT_APP_API_URL` está correto
- Verifique CORS no backend
- Limpe cache do navegador (Ctrl+F5)

### Aplicação "dorme" após inatividade (plano gratuito)
- Render.com "suspende" serviços gratuitos após 15min de inatividade
- Primeira requisição pode demorar ~30s para "acordar"
- Solução: Upgrade para plano pago ou usar serviço de "keep-alive"

---

## 💰 Custos

**Plano Gratuito:**
- ✅ Backend: 750 horas/mês (suficiente para desenvolvimento)
- ✅ Frontend: Ilimitado
- ✅ PostgreSQL: 90 dias grátis, depois $7/mês
- ⚠️ Serviços "dormem" após 15min de inatividade

**Plano Pago (Starter - $7/mês):**
- ✅ Sem "sleep"
- ✅ Mais recursos
- ✅ Melhor performance

---

## 📞 Suporte

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Status: https://status.render.com

---

## 🎉 Pronto!

Sua aplicação está no ar! Compartilhe a URL com quem precisar acessar.

