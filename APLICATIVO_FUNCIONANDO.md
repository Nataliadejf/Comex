# Como Fazer o Aplicativo Funcionar - Passo a Passo

## ✅ Status Atual

- ✅ **Backend funcionando**: `https://comex-3.onrender.com`
- ✅ **API respondendo**: Retorna `{"message": "Comex Analyzer API", "version":"1.0.0", "status":"online"}`

## 🎯 Próximos Passos

Você tem **2 opções** para fazer o aplicativo funcionar:

### **OPÇÃO 1: Rodar Frontend Localmente (Mais Rápido)** ⚡

Esta é a opção mais rápida para testar o aplicativo.

#### Passo 1: Configurar Frontend para usar o Backend no Render

Execute o script:
```
CONFIGURAR_FRONTEND_COMEX3.bat
```

Ou configure manualmente:
1. Edite o arquivo `frontend/.env`
2. Adicione/atualize:
   ```
   REACT_APP_API_URL=https://comex-3.onrender.com
   ```

#### Passo 2: Instalar Dependências (se ainda não instalou)

```bash
cd frontend
npm install
```

#### Passo 3: Iniciar o Frontend

Execute:
```
REINICIAR_FRONTEND.bat
```

Ou manualmente:
```bash
cd frontend
npm start
```

#### Passo 4: Acessar o Aplicativo

1. O navegador abrirá automaticamente em `http://localhost:3000`
2. Você verá a tela de login
3. Faça login ou cadastre-se

---

### **OPÇÃO 2: Fazer Deploy do Frontend no Render (Produção)** 🚀

Esta opção hospeda o frontend também no Render, deixando tudo na nuvem.

#### Passo 1: Criar Serviço de Static Site no Render

1. **Acesse**: https://dashboard.render.com
2. Clique em **"+ New"**
3. Selecione **"Static Site"**

#### Passo 2: Conectar ao Repositório GitHub

1. **Connect Repository**: Selecione `Nataliadjf/Comex`
2. **Branch**: `main`
3. **Root Directory**: `frontend`

#### Passo 3: Configurar Build

- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`

#### Passo 4: Configurar Environment Variables

Adicione:
- `REACT_APP_API_URL` = `https://comex-3.onrender.com`

#### Passo 5: Criar o Serviço

1. Clique em **"Create Static Site"**
2. Aguarde o build completar (5-10 minutos)
3. Você receberá uma URL como: `https://comex-frontend.onrender.com`

---

## 🔧 Configuração Detalhada - Opção 1 (Local)

### 1. Configurar Variável de Ambiente

**Windows (PowerShell):**
```powershell
cd frontend
$env:REACT_APP_API_URL="https://comex-3.onrender.com"
npm start
```

**Ou crie/edite `frontend/.env`:**
```
REACT_APP_API_URL=https://comex-3.onrender.com
```

### 2. Verificar se está Configurado Corretamente

Abra `frontend/src/services/api.js` e verifique se está usando:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### 3. Testar Conexão

1. Inicie o frontend: `npm start`
2. Abra o navegador em `http://localhost:3000`
3. Abra o Console do Navegador (F12)
4. Verifique se não há erros de conexão

---

## 🧪 Testar se Está Funcionando

### Teste 1: Health Check do Backend

Acesse no navegador:
```
https://comex-3.onrender.com/health
```

**Deve retornar:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Teste 2: Login no Frontend

1. Acesse `http://localhost:3000` (ou URL do Render se fez deploy)
2. Tente fazer login
3. Se não tiver usuário, faça cadastro

### Teste 3: Dashboard

Após login, você deve ver:
- ✅ Cards com estatísticas
- ✅ Gráficos (mesmo que vazios se não houver dados)
- ✅ Filtros funcionando

---

## 🐛 Problemas Comuns

### Problema: "Backend não está acessível"

**Solução:**
1. Verifique se `REACT_APP_API_URL` está configurado corretamente
2. Reinicie o frontend após mudar `.env`
3. Verifique se o backend está online: `https://comex-3.onrender.com/health`

### Problema: "CORS Error"

**Solução:**
- O backend já está configurado para aceitar requisições de qualquer origem
- Se persistir, verifique os logs do backend no Render

### Problema: "Erro 401 Unauthorized"

**Solução:**
1. Faça login novamente
2. Verifique se o token está sendo salvo no localStorage
3. Limpe o cache do navegador

### Problema: Frontend não carrega dados

**Solução:**
1. Verifique se o banco de dados está configurado (PostgreSQL)
2. Verifique se há dados no banco
3. Veja os logs do backend para erros

---

## 📋 Checklist Final

### Para Opção 1 (Local):
- [ ] `REACT_APP_API_URL` configurado no `.env`
- [ ] Frontend iniciado (`npm start`)
- [ ] Backend acessível (`/health` retorna OK)
- [ ] Login funcionando
- [ ] Dashboard carregando

### Para Opção 2 (Deploy):
- [ ] Static Site criado no Render
- [ ] Repositório conectado
- [ ] Build Command configurado
- [ ] `REACT_APP_API_URL` nas variáveis de ambiente
- [ ] Deploy concluído
- [ ] URL do frontend funcionando

---

## 🎯 Recomendação

**Para começar rapidamente**: Use a **Opção 1** (rodar localmente)

**Para produção**: Use a **Opção 2** (deploy completo no Render)

---

## 📞 Próximos Passos Após Funcionar

1. ✅ Configurar PostgreSQL (se ainda não fez)
2. ✅ Popular banco com dados de exemplo
3. ✅ Testar todas as funcionalidades
4. ✅ Configurar coletas automáticas
5. ✅ Aprovar cadastros de usuários

---

**Última atualização**: 05/01/2026



