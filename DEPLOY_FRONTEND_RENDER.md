# Deploy do Frontend no Render - Passo a Passo

## 🎯 Objetivo

Fazer deploy completo do frontend React no Render usando o `render.yaml` atualizado.

## 📋 Passo a Passo

### PASSO 1: Atualizar o Repositório GitHub

O `render.yaml` já foi atualizado para incluir o frontend. Agora precisamos fazer commit e push:

```bash
git add render.yaml
git commit -m "feat: Adicionar configuração do frontend no render.yaml"
git push origin main
```

### PASSO 2: Aplicar Blueprint no Render

1. **Acesse o Render Dashboard:**
   - Vá para: https://dashboard.render.com
   - Faça login

2. **Aplicar Blueprint:**
   - Clique em **"+ New"** (canto superior direito)
   - Selecione **"Blueprint"**
   - Cole a URL do repositório: `https://github.com/Nataliadjf/Comex`
   - Clique em **"Apply"**

3. **Ou criar manualmente via Dashboard:**
   - Se já tiver serviços criados, você pode criar o frontend manualmente

### PASSO 3: Criar Static Site Manualmente (Alternativa)

Se preferir criar manualmente:

1. **No Render Dashboard:**
   - Clique em **"+ New"**
   - Selecione **"Static Site"**

2. **Conectar Repositório:**
   - **Connect Repository**: Selecione `Nataliadjf/Comex`
   - **Branch**: `main`
   - **Root Directory**: `frontend`

3. **Configurar Build:**
   - **Name**: `comex-frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Region**: `Oregon`
   - **Plan**: `Free`

4. **Configurar Environment Variables:**
   - Clique em **"Advanced"** → **"Environment Variables"**
   - Adicione:
     - **Key**: `REACT_APP_API_URL`
     - **Value**: `https://comex-3.onrender.com` (ou a URL do seu backend)

5. **Criar o Serviço:**
   - Clique em **"Create Static Site"**
   - Aguarde o build completar (5-10 minutos)

### PASSO 4: Verificar Deploy

Após o deploy:

1. **Copie a URL do frontend:**
   - Você receberá uma URL como: `https://comex-frontend.onrender.com`

2. **Teste o frontend:**
   - Acesse a URL no navegador
   - Você deve ver a tela de login

3. **Verificar se está conectado ao backend:**
   - Tente fazer login
   - Se funcionar, significa que está conectado ao backend

### PASSO 5: Atualizar URL do Backend (se necessário)

Se você criou um novo serviço de backend via Blueprint:

1. **No serviço do frontend:**
   - Vá em **"Environment"**
   - Atualize `REACT_APP_API_URL` com a URL correta do backend
   - Faça um novo deploy manual

## ✅ Checklist

- [ ] `render.yaml` atualizado e commitado
- [ ] Push para GitHub realizado
- [ ] Blueprint aplicado no Render (ou Static Site criado manualmente)
- [ ] `REACT_APP_API_URL` configurada corretamente
- [ ] Deploy do frontend concluído
- [ ] Frontend acessível via URL
- [ ] Login funcionando
- [ ] Dashboard carregando dados

## 🔧 Configuração Detalhada

### Variáveis de Ambiente do Frontend

No Render, configure:

| Key | Value | Descrição |
|-----|-------|-----------|
| `REACT_APP_API_URL` | `https://comex-3.onrender.com` | URL do backend (use a que está funcionando) |

### Build Command

```
cd frontend && npm install && npm run build
```

### Publish Directory

```
frontend/build
```

## 🐛 Troubleshooting

### Problema: Build falha

**Possíveis causas:**
1. Dependências não instaladas
2. Erro de sintaxe no código
3. Variáveis de ambiente não configuradas

**Solução:**
- Verifique os logs do build no Render
- Teste o build localmente: `cd frontend && npm run build`
- Verifique se todas as dependências estão no `package.json`

### Problema: Frontend não conecta ao backend

**Solução:**
1. Verifique se `REACT_APP_API_URL` está configurada corretamente
2. Use a URL completa do backend (com `https://`)
3. Verifique se o backend está online
4. Faça um novo deploy após alterar variáveis de ambiente

### Problema: Página em branco

**Solução:**
1. Abra o Console do Navegador (F12)
2. Verifique erros no console
3. Verifique se o build foi concluído com sucesso
4. Verifique se o `index.html` está sendo servido corretamente

## 📝 Notas Importantes

1. **Variáveis de Ambiente:**
   - Variáveis que começam com `REACT_APP_` são injetadas no build
   - Após alterar variáveis, é necessário fazer novo build

2. **Build Time:**
   - O build do React pode levar 5-10 minutos
   - Seja paciente durante o primeiro deploy

3. **URLs:**
   - O Render gera URLs automáticas
   - Você pode configurar um domínio customizado depois

## 🎯 Próximos Passos Após Deploy

1. ✅ Testar login no frontend hospedado
2. ✅ Testar dashboard
3. ✅ Verificar se dados estão carregando
4. ✅ Configurar PostgreSQL (se ainda não fez)
5. ✅ Popular banco com dados
6. ✅ Configurar domínio customizado (opcional)

---

**Última atualização**: 05/01/2026

