# Guia de Hospedagem - Comex Analyzer

## Opções de Hospedagem

### 1. **Render.com** (Recomendado - Gratuito)
- ✅ Backend Python/FastAPI
- ✅ Frontend React
- ✅ Banco de dados PostgreSQL (gratuito)
- ✅ SSL automático
- ✅ Deploy automático via Git

**Passos:**
1. Criar conta em https://render.com
2. Conectar repositório Git
3. Criar Web Service para backend
4. Criar Static Site para frontend
5. Criar PostgreSQL Database

### 2. **Railway.app** (Gratuito com limites)
- ✅ Backend e Frontend
- ✅ PostgreSQL incluído
- ✅ Deploy simples

### 3. **Vercel** (Frontend) + **Fly.io** (Backend)
- ✅ Vercel: Excelente para React (gratuito)
- ✅ Fly.io: Backend Python (gratuito)

### 4. **Heroku** (Pago após período trial)
- ✅ Full-stack
- ✅ PostgreSQL addon

### 5. **AWS/GCP/Azure** (Mais complexo, mais controle)
- ✅ Escalável
- ✅ Mais configuração necessária

## Configuração Recomendada: Render.com

### Backend (Render.com)

1. **Criar novo Web Service**
2. **Configurações:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:**
     ```
     DATABASE_URL=postgresql://...
     SECRET_KEY=sua-chave-secreta
     COMEX_STAT_API_URL=https://comexstat.mdic.gov.br
     ```

3. **Banco de Dados PostgreSQL:**
   - Criar PostgreSQL Database no Render
   - Copiar DATABASE_URL para variáveis de ambiente

### Frontend (Render.com Static Site)

1. **Criar novo Static Site**
2. **Configurações:**
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `build`
   - **Environment Variables:**
     ```
     REACT_APP_API_URL=https://seu-backend.onrender.com
     ```

## Vantagens da Hospedagem

✅ **Sempre disponível** - Não precisa manter computador ligado
✅ **Acesso de qualquer lugar** - URL pública
✅ **SSL automático** - HTTPS seguro
✅ **Backup automático** - Banco de dados protegido
✅ **Escalável** - Suporta mais usuários
✅ **Sem problemas de firewall** - Tudo na nuvem

## Próximos Passos

1. Escolher plataforma de hospedagem
2. Preparar código para deploy
3. Configurar variáveis de ambiente
4. Fazer deploy
5. Testar aplicação hospedada

