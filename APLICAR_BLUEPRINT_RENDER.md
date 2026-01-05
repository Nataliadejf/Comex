# Como Aplicar Blueprint no Render - Passo a Passo

## 📋 Passo a Passo Completo

### PASSO 1: Acessar Blueprint

1. Acesse: https://dashboard.render.com
2. Clique em **"+ New"** (canto superior direito)
3. Selecione **"Blueprint"**

### PASSO 2: Preencher Blueprint Name

No campo **"Blueprint Name"**, digite um nome único para seu projeto:

**Sugestões de nomes:**
- `comex-project`
- `comex-analyzer`
- `comex-app`
- `projeto-comex`
- `comex-deployment`

**Exemplo:** `comex-project`

### PASSO 3: Verificar Branch

O campo **"Branch"** deve estar como `main` (já vem preenchido automaticamente).

### PASSO 4: Configurar DATABASE_URL

Você verá uma seção **"Specified configurations"** com:
- **Create web service comex-backend**
- **Environment Variables** → `DATABASE_URL` (vazio)

**IMPORTANTE:** Você tem 2 opções:

#### Opção A: Configurar agora (se já tem PostgreSQL)

1. Se você já criou um PostgreSQL no Render:
   - Clique no campo **"Value"** ao lado de `DATABASE_URL`
   - Cole a **Internal Database URL** do seu PostgreSQL
   - Formato: `postgresql://usuario:senha@host:porta/database`

#### Opção B: Configurar depois (recomendado)

1. Deixe o campo `DATABASE_URL` vazio por enquanto
2. Após criar o Blueprint, você pode:
   - Criar o PostgreSQL no Render
   - Configurar `DATABASE_URL` nas variáveis de ambiente do serviço

### PASSO 5: Aplicar Blueprint

1. Clique no botão **"Apply"** (ou **"Create Blueprint"**)
2. Aguarde o deploy do backend (5-10 minutos)

### PASSO 6: Verificar Deploy

Após o deploy:

1. Você verá o serviço `comex-backend` criado
2. Clique no serviço para ver os logs
3. Verifique se está funcionando: `https://comex-backend.onrender.com/health`

## ✅ Checklist

- [ ] Blueprint Name preenchido (ex: `comex-project`)
- [ ] Branch: `main` (verificado)
- [ ] DATABASE_URL configurado (ou deixado vazio para configurar depois)
- [ ] Blueprint aplicado com sucesso
- [ ] Backend deployado e funcionando

## 🔧 Configurar DATABASE_URL Depois

Se você deixou `DATABASE_URL` vazio:

1. **Criar PostgreSQL:**
   - No Render Dashboard, clique em **"+ New"**
   - Selecione **"PostgreSQL"**
   - Configure e crie o banco

2. **Configurar no Backend:**
   - Acesse o serviço `comex-backend`
   - Vá em **"Environment"**
   - Adicione `DATABASE_URL` com a Internal Database URL
   - Faça um novo deploy

## 📝 Notas Importantes

1. **Blueprint Name:**
   - Deve ser único no seu workspace
   - Pode usar letras, números e hífens
   - Não pode ter espaços

2. **DATABASE_URL:**
   - Pode ser configurado agora ou depois
   - Se deixar vazio, o backend ainda funcionará (mas sem banco de dados)
   - Você pode configurar depois nas variáveis de ambiente

3. **Após aplicar:**
   - O Render criará automaticamente o serviço `comex-backend`
   - Você receberá uma URL como: `https://comex-backend.onrender.com`
   - O deploy pode levar 5-10 minutos

## 🎯 Próximos Passos Após Blueprint

1. ✅ Verificar se o backend está funcionando
2. ✅ Criar PostgreSQL (se ainda não criou)
3. ✅ Configurar `DATABASE_URL` no backend
4. ✅ Criar frontend manualmente (veja `CRIAR_FRONTEND_MANUAL.md`)
5. ✅ Testar aplicativo completo

---

**Última atualização**: 05/01/2026

