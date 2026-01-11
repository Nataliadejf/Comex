# 🚀 Guia Completo: Deploy do Frontend no Render

## ✅ Pré-requisitos

- ✅ Backend funcionando no Render (você já tem isso!)
- ✅ Repositório GitHub conectado ao Render
- ✅ URL do backend no Render (ex: `https://comex-backend-xxxxx.onrender.com`)

## 📋 Passo a Passo Completo

### 1️⃣ Descobrir a URL do Backend

1. **Acesse**: https://dashboard.render.com
2. **Encontre o serviço**: `comex-backend` (ou o nome que você deu)
3. **Copie a URL**: Ela estará no topo da página do serviço
   - Formato: `https://comex-backend-xxxxx.onrender.com`
   - **Anote essa URL!** Você precisará dela no passo 4

### 2️⃣ Criar Static Site no Render

1. **No Render Dashboard**, clique em **"+ New"** (canto superior direito)
2. **Selecione**: **"Static Site"**
3. **Conecte o repositório**:
   - **Connect Repository**: Selecione seu repositório (`Nataliadjf/Comex`)
   - **Branch**: `main`
   - **Root Directory**: Deixe vazio ou coloque `frontend` (se o Render não detectar automaticamente)

### 3️⃣ Configurar Build

Preencha os campos:

#### **Name**
```
comex-frontend
```
(ou qualquer nome que você preferir)

#### **Build Command**
```bash
cd frontend && npm install && npm run build
```

#### **Publish Directory**
```
frontend/build
```

**⚠️ IMPORTANTE**: 
- O `Publish Directory` deve ser o caminho **relativo ao root do repositório**
- Se você colocou `frontend` no Root Directory, use apenas `build`
- Se deixou vazio, use `frontend/build`

### 4️⃣ Configurar Variáveis de Ambiente

**ANTES de clicar em "Create Static Site"**, vá na seção **"Environment Variables"** e adicione:

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `https://comex-backend-xxxxx.onrender.com` |

**⚠️ IMPORTANTE**: 
- Substitua `comex-backend-xxxxx.onrender.com` pela URL REAL do seu backend
- Use `https://` (não `http://`)
- Não coloque barra no final (`/`)

**Exemplo correto:**
```
REACT_APP_API_URL=https://comex-backend-wjco.onrender.com
```

**Exemplo ERRADO:**
```
REACT_APP_API_URL=https://comex-backend-wjco.onrender.com/  ❌ (barra no final)
REACT_APP_API_URL=http://comex-backend-wjco.onrender.com     ❌ (sem https)
REACT_APP_API_URL=comex-backend-wjco.onrender.com           ❌ (sem https://)
```

### 5️⃣ Criar o Serviço

1. **Clique em**: **"Create Static Site"**
2. **Aguarde o build** (5-10 minutos na primeira vez)
3. **Você receberá uma URL** como: `https://comex-frontend.onrender.com`

### 6️⃣ Verificar Deploy

1. **Acesse a URL** do frontend no navegador
2. **Você deve ver**: A tela de login do aplicativo
3. **Teste o login**: Se funcionar, está conectado ao backend! ✅

## 🔧 Configuração Detalhada

### Estrutura de Arquivos

```
projeto_comex/
├── frontend/
│   ├── public/
│   │   ├── _redirects          ✅ Arquivo para SPA routing
│   │   └── index.html
│   ├── src/
│   │   ├── services/
│   │   │   └── api.js          ✅ Usa REACT_APP_API_URL
│   │   └── ...
│   ├── package.json
│   └── build/                  ✅ Gerado pelo npm run build
└── backend/
    └── ...
```

### Arquivo `_redirects`

O arquivo `frontend/public/_redirects` já está configurado:
```
/*    /index.html   200
```

Isso garante que o React Router funcione corretamente no Render.

## 🧪 Testar Localmente Antes do Deploy

Antes de fazer deploy, teste localmente:

### 1. Criar arquivo `.env` no frontend

Crie `frontend/.env`:
```env
REACT_APP_API_URL=https://seu-backend.onrender.com
```

### 2. Build local

```bash
cd frontend
npm install
npm run build
```

### 3. Testar build

```bash
# Instalar serve globalmente (se não tiver)
npm install -g serve

# Servir o build
serve -s build -l 3000
```

Acesse `http://localhost:3000` e teste se está funcionando.

## 🐛 Troubleshooting

### Problema 1: Build falha

**Sintomas:**
- Logs mostram erro de compilação
- Build não completa

**Soluções:**
1. **Verifique os logs** do build no Render
2. **Teste localmente**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
3. **Verifique erros de sintaxe** no código
4. **Verifique dependências** no `package.json`

### Problema 2: Página em branco

**Sintomas:**
- Frontend abre mas mostra tela branca
- Console do navegador mostra erros

**Soluções:**
1. **Abra o Console do navegador** (F12)
2. **Verifique erros**:
   - Se aparecer erro de CORS → Backend precisa permitir origem do frontend
   - Se aparecer erro 404 → Verifique se `REACT_APP_API_URL` está correto
   - Se aparecer erro de rede → Backend pode estar "dormindo" (plano free)
3. **Verifique se o backend está online**:
   ```
   https://seu-backend.onrender.com/health
   ```

### Problema 3: Frontend não conecta ao backend

**Sintomas:**
- Login não funciona
- Erro "Network Error" ou "CORS Error"

**Soluções:**
1. **Verifique `REACT_APP_API_URL`**:
   - Vá em: Render Dashboard → Static Site → Environment
   - Confirme que está correto
   - **IMPORTANTE**: Após alterar, faça um novo deploy!
2. **Verifique CORS no backend**:
   - O backend deve permitir requisições do frontend
   - Já está configurado para `*` (qualquer origem)
3. **Teste a URL do backend diretamente**:
   ```
   https://seu-backend.onrender.com/health
   ```
   Deve retornar JSON válido

### Problema 4: Rotas não funcionam (404 ao navegar)

**Sintomas:**
- Ao clicar em links, aparece 404
- URL muda mas página não carrega

**Soluções:**
1. **Verifique se `_redirects` existe** em `frontend/public/_redirects`
2. **Conteúdo do arquivo deve ser**:
   ```
   /*    /index.html   200
   ```
3. **Faça commit e push** do arquivo
4. **Faça novo deploy** no Render

### Problema 5: Variáveis de ambiente não funcionam

**Sintomas:**
- `REACT_APP_API_URL` não está sendo usada
- Frontend ainda usa `localhost:8000`

**Soluções:**
1. **Variáveis de ambiente** no React precisam começar com `REACT_APP_`
2. **Após alterar variáveis**, faça um novo deploy
3. **Verifique se está no formato correto**:
   ```
   REACT_APP_API_URL=https://seu-backend.onrender.com
   ```
   (sem espaços, sem aspas)

## 📝 Checklist Final

Antes de considerar o deploy completo:

- [ ] Backend está funcionando e acessível
- [ ] URL do backend copiada corretamente
- [ ] Static Site criado no Render
- [ ] Build Command configurado: `cd frontend && npm install && npm run build`
- [ ] Publish Directory configurado: `frontend/build`
- [ ] `REACT_APP_API_URL` configurada com URL correta do backend
- [ ] Deploy concluído sem erros
- [ ] Frontend acessível via URL
- [ ] Tela de login aparece
- [ ] Login funciona (conecta ao backend)
- [ ] Dashboard carrega dados
- [ ] Navegação entre páginas funciona

## 🔄 Atualizar URL do Backend (se necessário)

Se você mudar a URL do backend:

1. **No Render Dashboard** → Static Site → Environment
2. **Atualize** `REACT_APP_API_URL` com a nova URL
3. **Clique em**: "Save Changes"
4. **Faça um novo deploy**: "Manual Deploy" → "Deploy latest commit"

## ✅ Próximos Passos

Após o deploy bem-sucedido:

1. **Teste todas as funcionalidades**:
   - Login/Cadastro
   - Dashboard
   - Busca Avançada
   - Análise por NCM
   - Exportação de dados

2. **Configure domínio personalizado** (opcional):
   - Render Dashboard → Static Site → Settings → Custom Domain
   - Adicione seu domínio

3. **Monitore os logs**:
   - Render Dashboard → Static Site → Logs
   - Verifique se há erros

## 🎉 Pronto!

Seu frontend está no ar! 🚀

**URLs importantes:**
- **Frontend**: `https://comex-frontend.onrender.com`
- **Backend**: `https://comex-backend-xxxxx.onrender.com`
- **Health Check**: `https://comex-backend-xxxxx.onrender.com/health`
