# Criar Frontend Manualmente no Render

## ⚠️ Importante

O Render **não suporta** `type: static` no Blueprint (`render.yaml`). Por isso, você precisa criar o frontend manualmente.

## 📋 Passo a Passo

### PASSO 1: Acessar Render Dashboard

1. Vá para: https://dashboard.render.com
2. Faça login

### PASSO 2: Criar Static Site

1. Clique em **"+ New"** (canto superior direito)
2. Selecione **"Static Site"**

### PASSO 3: Conectar Repositório GitHub

1. **Connect Repository**: 
   - Selecione `Nataliadjf/Comex`
   - Ou cole: `https://github.com/Nataliadjf/Comex`

2. **Branch**: `main`

3. **Root Directory**: `frontend`

### PASSO 4: Configurar Build

Preencha os campos:

- **Name**: `comex-frontend` (ou outro nome de sua preferência)
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`
- **Plan**: `Free`

### PASSO 5: Configurar Environment Variables

1. Clique em **"Advanced"** → **"Environment Variables"**
2. Clique em **"+ Add Environment Variable"**
3. Adicione:
   - **Key**: `REACT_APP_API_URL`
   - **Value**: `https://comex-3.onrender.com` (ou a URL do seu backend)

### PASSO 6: Criar o Serviço

1. Clique em **"Create Static Site"**
2. Aguarde o build completar (5-10 minutos)

### PASSO 7: Verificar Deploy

Após o deploy:

1. Você receberá uma URL como: `https://comex-frontend.onrender.com`
2. Acesse a URL no navegador
3. Você deve ver a tela de login

## ✅ Checklist

- [ ] Static Site criado no Render
- [ ] Repositório GitHub conectado
- [ ] Root Directory configurado como `frontend`
- [ ] Build Command: `npm install && npm run build`
- [ ] Publish Directory: `build`
- [ ] `REACT_APP_API_URL` configurada com URL do backend
- [ ] Deploy concluído
- [ ] Frontend acessível via URL

## 🔧 Configuração Detalhada

### Build Command
```
npm install && npm run build
```

### Publish Directory
```
build
```

### Environment Variables

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `https://comex-3.onrender.com` |

**Nota**: Use a URL do backend que está funcionando. Se você criou um novo backend via Blueprint, use essa URL.

## 🐛 Troubleshooting

### Problema: Build falha

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

