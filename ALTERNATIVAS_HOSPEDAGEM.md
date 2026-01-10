# 🌐 Alternativas de Hospedagem para o Projeto Comex

## ⚠️ Situação Atual: Render Free Tier com Limites

O Render Free Tier tem limites de:
- ✅ 750 horas/mês de pipeline (builds)
- ✅ 512 MB RAM
- ✅ 0.1 CPU
- ⚠️ Deploy manual bloqueado quando limite é atingido

---

## 🆓 Opções Gratuitas Recomendadas

### 1. Railway ⭐ MELHOR OPÇÃO

**Preço:** $5 crédito grátis/mês (suficiente para projetos pequenos)

**Vantagens:**
- ✅ PostgreSQL incluído (gratuito até certo limite)
- ✅ Deploy automático via GitHub
- ✅ Interface muito simples
- ✅ Sem limites rígidos no free tier
- ✅ Upgrade fácil quando precisar
- ✅ Suporta variáveis de ambiente grandes (JSON de credenciais)
- ✅ Logs em tempo real
- ✅ SSL automático

**Limites Gratuitos:**
- 500 horas/mês de uso
- $5 crédito/mês
- PostgreSQL até 5GB (gratuito)

**Como Migrar:**
1. Criar conta em https://railway.app
2. Conectar GitHub
3. Criar novo projeto
4. Adicionar PostgreSQL
5. Configurar variáveis de ambiente
6. Deploy automático

**URL:** https://railway.app

---

### 2. Fly.io

**Preço:** Grátis (com limites generosos)

**Vantagens:**
- ✅ 3 VMs grátis
- ✅ 3GB RAM cada VM
- ✅ PostgreSQL incluído
- ✅ Deploy via CLI ou GitHub
- ✅ Global edge network
- ✅ Muito rápido

**Limites Gratuitos:**
- 3 VMs compartilhadas
- 3GB RAM por VM
- 160GB egress/mês

**Como Migrar:**
1. Instalar Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Criar conta: `fly auth signup`
3. Criar app: `fly launch`
4. Adicionar PostgreSQL: `fly postgres create`

**URL:** https://fly.io

---

### 3. Supabase (Backend + Database)

**Preço:** Grátis (500MB database, 2GB bandwidth)

**Vantagens:**
- ✅ PostgreSQL gerenciado (muito rápido)
- ✅ API auto-gerada a partir do schema
- ✅ Dashboard completo
- ✅ Autenticação incluída
- ✅ Storage incluído
- ✅ Real-time subscriptions

**Limites Gratuitos:**
- 500MB database
- 2GB bandwidth
- 2GB storage
- 50,000 monthly active users

**Como Migrar:**
1. Criar conta em https://supabase.com
2. Criar novo projeto
3. Executar schema SQL no SQL Editor
4. Configurar variáveis de ambiente no backend
5. Deploy backend separadamente (Railway/Fly.io)

**URL:** https://supabase.com

**Nota:** Supabase é principalmente para database. Você ainda precisaria hospedar o backend FastAPI em outro lugar.

---

### 4. Neon (Apenas PostgreSQL)

**Preço:** Grátis (0.5GB storage)

**Vantagens:**
- ✅ PostgreSQL serverless (muito rápido)
- ✅ Branching de database (como Git)
- ✅ Auto-scaling
- ✅ Muito fácil de usar

**Limites Gratuitos:**
- 0.5GB storage
- 1 projeto
- Branching limitado

**Como Migrar:**
1. Criar conta em https://neon.tech
2. Criar projeto
3. Executar schema SQL
4. Copiar connection string
5. Usar com backend em Railway/Fly.io

**URL:** https://neon.tech

**Nota:** Neon é apenas para database. Você precisaria hospedar o backend separadamente.

---

## 💰 Opções Pagas (Baratas)

### 1. Railway (Plano Pago)

**Preço:** $5/mês (Developer plan)

**Vantagens:**
- ✅ Tudo do free tier +
- ✅ Sem limites de horas
- ✅ Mais recursos
- ✅ Suporte prioritário

**Total:** $5/mês (inclui PostgreSQL até certo limite)

---

### 2. DigitalOcean App Platform

**Preço:** $5/mês (Basic plan) + $15/mês (PostgreSQL)

**Vantagens:**
- ✅ Escalável
- ✅ Muito confiável
- ✅ Fácil deploy
- ✅ Documentação excelente

**Total:** ~$20/mês

**URL:** https://www.digitalocean.com/products/app-platform

---

### 3. Heroku

**Preço:** $7/mês (Eco dyno) + $5/mês (PostgreSQL Mini)

**Vantagens:**
- ✅ Muito fácil de usar
- ✅ Add-ons disponíveis
- ✅ Documentação extensa
- ✅ Comunidade grande

**Total:** ~$12/mês

**URL:** https://www.heroku.com

---

### 4. Render (Plano Pago)

**Preço:** $7/mês (Starter) + $7/mês (PostgreSQL)

**Vantagens:**
- ✅ Mesma interface que você já conhece
- ✅ Sem limites de pipeline
- ✅ Mais recursos

**Total:** ~$14/mês

**URL:** https://render.com

---

## ⭐ RECOMENDAÇÃO FINAL

### Para Começar (Gratuito):
**Railway** é a melhor opção porque:
- ✅ $5 crédito grátis/mês (suficiente para começar)
- ✅ PostgreSQL incluído
- ✅ Deploy automático via GitHub
- ✅ Interface simples
- ✅ Sem limites rígidos
- ✅ Upgrade fácil

### Para Produção (Pago):
**Railway Developer Plan ($5/mês)** ou **DigitalOcean ($20/mês)** dependendo do orçamento.

---

## 📋 Como Migrar para Railway

### Passo 1: Criar Conta
1. Acesse: https://railway.app
2. Clique em "Start a New Project"
3. Conecte sua conta GitHub
4. Selecione o repositório `Nataliadjf/Comex`

### Passo 2: Adicionar PostgreSQL
1. No projeto Railway, clique em "+ New"
2. Selecione "Database" → "Add PostgreSQL"
3. Railway criará automaticamente e configurará `DATABASE_URL`

### Passo 3: Configurar Variáveis de Ambiente
1. Vá em "Variables"
2. Adicione:
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON` = (seu JSON completo)
   - `SECRET_KEY` = (sua chave secreta)
   - Outras variáveis necessárias

### Passo 4: Configurar Deploy
1. Railway detecta automaticamente que é Python
2. Configure:
   - **Root Directory:** `backend`
   - **Start Command:** `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Build Command:** `pip install -r backend/requirements-render-ultra-minimal.txt`

### Passo 5: Deploy
- Railway faz deploy automático a cada push no GitHub
- Ou clique em "Deploy" para forçar deploy manual

### Passo 6: Migrar Dados (Opcional)
Se você já tem dados no Render PostgreSQL:
1. Exportar do Render: `pg_dump`
2. Importar no Railway: `psql`

---

## 🔄 Comparação Rápida

| Serviço | Preço | PostgreSQL | Deploy | Limites Free Tier |
|---------|-------|------------|--------|-------------------|
| **Railway** ⭐ | $5 crédito/mês | ✅ Incluído | ✅ GitHub | 500h/mês |
| **Fly.io** | Grátis | ✅ Incluído | ✅ CLI/GitHub | 3 VMs, 3GB RAM |
| **Supabase** | Grátis | ✅ Gerenciado | ❌ Apenas DB | 500MB DB |
| **Neon** | Grátis | ✅ Serverless | ❌ Apenas DB | 0.5GB |
| **DigitalOcean** | $20/mês | ✅ Incluído | ✅ GitHub | - |
| **Heroku** | $12/mês | ✅ Incluído | ✅ Git | - |
| **Render** | $14/mês | ✅ Incluído | ✅ GitHub | - |

---

## 💡 Dica Final

Se você está começando, use **Railway**:
- É grátis para começar ($5 crédito/mês)
- Muito fácil de usar
- PostgreSQL incluído
- Deploy automático
- Upgrade fácil quando precisar

Quando o projeto crescer e precisar de mais recursos, você pode:
- Upgrade no Railway ($5/mês)
- Ou migrar para DigitalOcean ($20/mês) para mais recursos
