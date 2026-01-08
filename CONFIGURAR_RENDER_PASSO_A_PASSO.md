# 🚀 Guia Passo a Passo para Configurar Render.com

## ⚠️ IMPORTANTE: Siga EXATAMENTE estes passos

### 1️⃣ Acessar o Render.com

1. Abra seu navegador e vá para: https://dashboard.render.com
2. Faça login na sua conta
3. Clique no serviço **"comex-backend"** na lista de serviços

### 2️⃣ Ir para Settings (Configurações)

1. No menu lateral esquerdo, clique em **"Settings"** (Configurações)
2. Você verá várias seções de configuração

### 3️⃣ Alterar o Build Command (CRÍTICO!)

1. Role a página até encontrar a seção **"Build & Deploy"**
2. Procure o campo **"Build Command"**
3. **APAGUE TUDO** que está escrito lá
4. Digite EXATAMENTE isto (copie e cole):

```
pip install -r requirements-render-ultra-minimal.txt
```

### 4️⃣ Verificar Start Command

1. Na mesma seção, procure o campo **"Start Command"**
2. Deve estar assim (se não estiver, corrija):

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 5️⃣ Verificar Root Directory

1. Procure o campo **"Root Directory"** ou **"Working Directory"**
2. Deve estar assim:

```
backend
```

Se não estiver, digite: `backend`

### 6️⃣ Verificar Python Version

1. Procure a seção **"Environment"** ou **"Python"**
2. Verifique se está configurado para Python 3.11 ou 3.12
3. Se não estiver, altere para: `python-3.11` ou `python-3.12`

### 7️⃣ Salvar e Aguardar Deploy

1. Role até o final da página
2. Clique no botão **"Save Changes"** (Salvar Alterações)
3. O Render iniciará automaticamente um novo deploy
4. Vá para a aba **"Logs"** para acompanhar o progresso

### 8️⃣ Verificar Variáveis de Ambiente

1. Na seção **"Environment Variables"**, verifique se estão configuradas:
   - `DATABASE_URL` - URL do banco PostgreSQL do Render
   - `COMEX_STAT_API_URL` - (opcional) URL da API externa
   - `COMEX_STAT_API_KEY` - (opcional) Chave da API
   - `SECRET_KEY` - Uma chave secreta aleatória (gere uma se não tiver)

### 9️⃣ Se o Deploy Falhar

Se ainda falhar, verifique os logs e me envie:
1. A mensagem de erro completa
2. Em qual etapa falhou (build ou start)
3. Uma captura de tela se possível

## 📋 Checklist Final

Antes de salvar, verifique:

- [ ] Build Command: `pip install -r requirements-render-ultra-minimal.txt`
- [ ] Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Root Directory: `backend`
- [ ] Python Version: 3.11 ou 3.12
- [ ] DATABASE_URL configurada
- [ ] SECRET_KEY configurada

## 🔧 Comandos Alternativos (se necessário)

Se ainda houver problemas, tente estes Build Commands alternativos:

**Opção 1 (mais básica):**
```
pip install --upgrade pip && pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings psycopg2-binary httpx python-dotenv python-multipart loguru
```

**Opção 2 (com versões específicas):**
```
pip install fastapi==0.104.1 uvicorn==0.24.0 sqlalchemy==2.0.23 pydantic==2.5.0 pydantic-settings==2.1.0 psycopg2-binary==2.9.9 httpx==0.25.2 python-dotenv==1.0.0 python-multipart==0.0.6 loguru==0.7.2
```






