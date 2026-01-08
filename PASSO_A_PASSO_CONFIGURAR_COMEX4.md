# 🔧 Passo a Passo Completo - Configurar Comex-4 Manualmente

## 🎯 Objetivo

Configurar o serviço Comex-4 (Static Site) no Render Dashboard para fazer deploy corretamente.

## 📋 Passo 1: Acessar Configurações do Comex-4

1. Acesse: https://dashboard.render.com
2. Faça login na sua conta
3. Clique em **"My project"** → **"Production"** → **"Comex-4"**
4. Clique em **"Settings"** (menu lateral esquerdo)

## 📋 Passo 2: Configurar Build & Deploy

### 2.1. Root Directory

**Campo:** Root Directory (Optional)

**Valor:**
```
frontend
```

### 2.2. Build Command

**Campo:** Build Command

**Valor:**
```bash
CI=false npm install && npm run build
```

**Explicação:** 
- `CI=false` desabilita verificações que podem causar falha no build
- Garante que o build não falhe por avisos

### 2.3. Publish Directory

**Campo:** Publish Directory

**Valor:**
```
build
```

**⚠️ IMPORTANTE:** Não coloque `frontend/build`, apenas `build` (porque o Root Directory já é `frontend`)

### 2.4. Node Version (Opcional mas Recomendado)

**Campo:** Node Version (se disponível)

**Valor:**
```
18.20.0
```

Ou deixe vazio para usar a versão padrão.

## 📋 Passo 3: Configurar Environment Variables

Vá em **"Environment"** (menu lateral) ou **"Environment Variables"** nas Settings.

### Variáveis Obrigatórias:

**Nome:** `REACT_APP_API_URL`  
**Valor:** `https://[URL_DO_SEU_BACKEND].onrender.com`

**Exemplo:**
```
REACT_APP_API_URL=https://comex-backend.onrender.com
```

**⚠️ IMPORTANTE:** 
- Se você ainda não tem um backend funcionando, use uma URL temporária ou deixe vazio
- O frontend usará `http://localhost:8000` como fallback se não encontrar essa variável

### Variáveis Opcionais (para otimizar build):

**Nome:** `CI`  
**Valor:** `false`

**Nome:** `GENERATE_SOURCEMAP`  
**Valor:** `false`

**Explicação:** 
- `CI=false` evita que o build falhe por avisos
- `GENERATE_SOURCEMAP=false` reduz o tempo de build (não gera source maps)

## 📋 Passo 4: Configurar Auto-Deploy

1. Na seção **"Build & Deploy"**
2. Encontre **"Auto-Deploy"**
3. Certifique-se que está como **"On Commit"**
4. Se estiver como "Manual", altere para **"On Commit"**

## 📋 Passo 5: Configurações Adicionais (Opcional)

### 5.1. Build Filters

**Included Paths:**
```
frontend/**
```

**Ignored Paths:**
```
backend/**
node_modules/**
.git/**
*.md
```

### 5.2. Deploy Hook

O Render gera automaticamente um Deploy Hook. Você pode usar isso para fazer deploy manual via webhook se necessário.

## 📋 Passo 6: Salvar e Fazer Deploy Manual

1. **Role até o final da página**
2. Clique em **"Save Changes"** (se houver)
3. Vá em **"Manual Deploy"** (menu superior)
4. Clique em **"Deploy latest commit"**
5. Aguarde o build completar (pode levar 5-10 minutos)

## 🔍 Verificar Build

Após iniciar o deploy:

1. Vá em **"Events"** ou **"Logs"** (menu lateral)
2. Acompanhe o progresso do build
3. Verifique se não há erros

### Logs Esperados:

```
==> Cloning from https://github.com/Nataliadjf/Comex
==> Checking out commit...
==> Installing dependencies with npm...
==> Running build command 'CI=false npm install && npm run build'...
> comex-analyzer-frontend@1.0.0 build
> react-scripts build
Creating an optimized production build...
Compiled successfully!
```

## 🐛 Troubleshooting

### Problema 1: Build trava em "Creating an optimized production build..."

**Solução:**
1. Adicione `CI=false` no Build Command
2. Adicione variável `GENERATE_SOURCEMAP=false`
3. Tente aumentar o timeout (se disponível no plano pago)

### Problema 2: Erro de memória

**Solução:**
1. O plano free tem limitações de memória
2. Tente reduzir dependências desnecessárias
3. Considere fazer build local e fazer upload do `build/` diretamente

### Problema 3: Erro "Module not found"

**Solução:**
1. Verifique se todas as dependências estão no `package.json`
2. Verifique se o Root Directory está correto (`frontend`)
3. Limpe cache: adicione `npm cache clean --force` antes do build

### Problema 4: Build Command não funciona

**Solução Alternativa - Build Command Simplificado:**
```bash
npm install && CI=false npm run build
```

Ou ainda mais simples:
```bash
npm ci && CI=false npm run build
```

## ✅ Checklist Final

Antes de fazer deploy, verifique:

- [ ] Root Directory: `frontend`
- [ ] Build Command: `CI=false npm install && npm run build`
- [ ] Publish Directory: `build` (não `frontend/build`)
- [ ] Variável `REACT_APP_API_URL` configurada (se tiver backend)
- [ ] Auto-Deploy: `On Commit`
- [ ] Todas as alterações salvas

## 🧪 Testar Após Deploy

1. **Acesse:** `https://comex-4.onrender.com`
2. **Verifique:**
   - Página carrega sem erros
   - Console do navegador não mostra erros críticos
   - Se tiver backend configurado, verifique se consegue fazer requisições

## 📝 Configuração Resumida (Copy-Paste)

### Build & Deploy:
- **Root Directory:** `frontend`
- **Build Command:** `CI=false npm install && npm run build`
- **Publish Directory:** `build`
- **Auto-Deploy:** `On Commit`

### Environment Variables:
- **REACT_APP_API_URL:** `https://[SEU_BACKEND].onrender.com` (ou deixe vazio)
- **CI:** `false` (opcional)
- **GENERATE_SOURCEMAP:** `false` (opcional)

## 🆘 Se Ainda Não Funcionar

1. **Verifique os logs completos** no Render Dashboard
2. **Tente fazer build local:**
   ```bash
   cd frontend
   CI=false npm install
   CI=false npm run build
   ```
3. **Se build local funcionar**, o problema pode ser memória/timeout no Render
4. **Considere fazer upload manual** do diretório `build/` se necessário
