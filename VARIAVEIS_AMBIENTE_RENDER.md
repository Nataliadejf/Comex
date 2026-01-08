# 🔧 Variáveis de Ambiente no Render

## ✅ O que o render.yaml JÁ CONFIGURA AUTOMATICAMENTE

Quando você usa o Blueprint (render.yaml), estas variáveis são criadas automaticamente:

### 1. **COMEX_STAT_API_URL** ✅
- **Valor**: `https://comexstat.mdic.gov.br`
- **Status**: ✅ Configurado automaticamente
- **Ação**: Nenhuma necessária

### 2. **ENVIRONMENT** ✅
- **Valor**: `production`
- **Status**: ✅ Configurado automaticamente
- **Ação**: Nenhuma necessária

### 3. **DEBUG** ✅
- **Valor**: `false`
- **Status**: ✅ Configurado automaticamente
- **Ação**: Nenhuma necessária

### 4. **PYTHON_VERSION** ✅
- **Valor**: `3.11`
- **Status**: ✅ Configurado automaticamente
- **Ação**: Nenhuma necessária

### 5. **SECRET_KEY** ✅
- **Valor**: Gerado automaticamente pelo Render
- **Status**: ✅ Render gera uma chave aleatória automaticamente
- **Ação**: Nenhuma necessária (mas você pode alterar se quiser)

---

## ⚠️ O que VOCÊ PRECISA CONFIGURAR MANUALMENTE

### 1. **DATABASE_URL** ⚠️ **OBRIGATÓRIA**

**Por que precisa configurar?**
- O render.yaml cria a variável, mas não sabe qual é a URL do seu PostgreSQL
- Você precisa criar o PostgreSQL primeiro e depois colar a URL

**Como configurar:**

1. Crie o PostgreSQL no Render:
   - Dashboard → "New +" → "PostgreSQL"
   - Configure: Name, Database, User, Plan
   - Clique em "Create Database"

2. Copie a URL:
   - No PostgreSQL criado, vá em "Connections"
   - Copie a **"Internal Database URL"**
   - Formato: `postgresql://user:password@host:5432/database`

3. Configure no serviço:
   - Vá para o serviço "comex-backend"
   - Clique em "Environment" no menu lateral
   - Encontre `DATABASE_URL`
   - Cole a URL que você copiou
   - Clique em "Save Changes"

**Exemplo de URL:**
```
postgresql://comex_user:abc123xyz@dpg-xxxxx-a.oregon-postgres.render.com/comex_db
```

---

### 2. **COMEX_STAT_API_KEY** ⚠️ **OPCIONAL**

**Por que é opcional?**
- Só precisa se você tiver uma chave de API do Comex Stat
- Se não tiver, deixe vazio (a aplicação funciona sem ela)

**Como configurar (se tiver a chave):**

1. Vá para o serviço "comex-backend"
2. Clique em "Environment"
3. Encontre `COMEX_STAT_API_KEY`
4. Cole sua chave de API
5. Clique em "Save Changes"

**Se não tiver chave:**
- Deixe vazio ou não configure
- A aplicação funcionará normalmente

---

## 📋 Checklist de Variáveis

### ✅ Já Configuradas Automaticamente (não precisa fazer nada):
- [x] COMEX_STAT_API_URL
- [x] ENVIRONMENT
- [x] DEBUG
- [x] PYTHON_VERSION
- [x] SECRET_KEY (gerado automaticamente)

### ⚠️ Precisa Configurar Manualmente:
- [ ] **DATABASE_URL** ← **OBRIGATÓRIA!**
- [ ] COMEX_STAT_API_KEY (opcional)

---

## 🎯 Resumo Rápido

**Após fazer deploy via Blueprint:**

1. ✅ 5 variáveis já estão configuradas automaticamente
2. ⚠️ Você só precisa configurar **DATABASE_URL** (obrigatória)
3. ⚠️ COMEX_STAT_API_KEY é opcional (só se tiver chave)

---

## 🚀 Passo a Passo Completo

### Passo 1: Fazer Deploy via Blueprint
- Render detecta render.yaml
- Cria serviço com variáveis pré-configuradas

### Passo 2: Criar PostgreSQL
- Dashboard → "New +" → "PostgreSQL"
- Criar banco de dados

### Passo 3: Configurar DATABASE_URL
- Ir para serviço "comex-backend"
- Environment → DATABASE_URL
- Colar URL do PostgreSQL
- Salvar

### Passo 4: (Opcional) Configurar COMEX_STAT_API_KEY
- Se tiver chave de API, configurar
- Se não tiver, deixar vazio

**PRONTO!** 🎉

---

## ❓ Dúvidas Frequentes

### Preciso configurar todas as variáveis manualmente?

**Não!** Apenas `DATABASE_URL` é obrigatória. As outras já estão configuradas pelo render.yaml.

### O SECRET_KEY precisa ser configurado?

**Não!** O Render gera automaticamente. Mas você pode alterar se quiser uma chave específica.

### E se eu não configurar DATABASE_URL?

A aplicação não funcionará. É a única variável obrigatória que você precisa configurar manualmente.

### Posso ver as variáveis configuradas?

Sim! No Render Dashboard:
- Serviço → "Environment" → Veja todas as variáveis

### Como alterar uma variável depois?

1. Vá para "Environment"
2. Clique na variável que quer alterar
3. Edite o valor
4. Clique em "Save Changes"
5. Render fará redeploy automaticamente

---

## 📝 Notas Importantes

- ✅ O render.yaml facilita muito, mas não pode criar o PostgreSQL automaticamente
- ✅ DATABASE_URL é a única variável obrigatória que você precisa configurar
- ✅ Todas as outras já estão prontas ou são opcionais
- ✅ Após configurar DATABASE_URL, a aplicação deve funcionar!






