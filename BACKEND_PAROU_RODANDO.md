# Backend Parou de Rodar - Como Resolver

## 🔍 Verificar Status

1. **No Render Dashboard:**
   - Vá para o serviço `comex-backend`
   - Verifique o status na lista de serviços:
     - ✅ **Live** = Funcionando
     - ⏳ **Deploying** = Em deploy
     - ❌ **Failed** = Falhou
     - ⏸️ **Suspended** = Suspenso

## ✅ Soluções

### Solução 1: Aguardar Deploy Completar

Se o status é **"Deploying"**:

1. **Aguarde alguns minutos** (5-10 minutos)
2. **Monitore os logs:**
   - Clique em **"Logs"** no menu lateral
   - Veja se há erros ou se está progredindo
3. **Verifique se completou:**
   - Status deve mudar para **"Live"**
   - Logs devem mostrar "Application startup complete"

### Solução 2: Fazer Deploy Manual

Se o deploy falhou ou está travado:

1. **No serviço `comex-backend`:**
   - Clique em **"Manual Deploy"** (canto superior direito)
   - Selecione **"Deploy latest commit"**
   - Aguarde o deploy completar

### Solução 3: Verificar Logs de Erro

1. **Clique em "Logs"** no menu lateral
2. **Procure por erros:**
   - Mensagens em vermelho
   - "Error", "Failed", "Exception"
3. **Copie o erro** e me envie para ajudar a corrigir

### Solução 4: Verificar Variáveis de Ambiente

1. **Vá em "Environment"** no menu lateral
2. **Verifique se todas estão configuradas:**
   - `DATABASE_URL` (se estiver usando PostgreSQL)
   - `SECRET_KEY`
   - `COMEX_STAT_API_URL`
   - Outras variáveis necessárias

### Solução 5: Reiniciar o Serviço

1. **No serviço `comex-backend`:**
   - Clique em **"Manual Deploy"**
   - Selecione **"Deploy latest commit"**
   - Isso reinicia o serviço

## 🐛 Problemas Comuns

### Problema: "Deploying" há muito tempo

**Causa:** Build travado ou demorando muito

**Solução:**
- Aguarde até 15 minutos
- Se passar disso, cancele e faça deploy manual
- Verifique os logs para ver onde está travado

### Problema: "Failed" após deploy

**Causa:** Erro no código ou configuração

**Solução:**
- Veja os logs para identificar o erro
- Verifique se todas as dependências estão instaladas
- Verifique se as variáveis de ambiente estão corretas

### Problema: Serviço Suspenso

**Causa:** Plano Free pode suspender após inatividade

**Solução:**
- Clique em **"Resume"** ou **"Manual Deploy"**
- O serviço será reativado

## 📋 Checklist

- [ ] Status do serviço verificado
- [ ] Logs verificados para erros
- [ ] Variáveis de ambiente verificadas
- [ ] Deploy manual tentado (se necessário)
- [ ] Aguardado tempo suficiente para deploy

## 🎯 Próximos Passos

Após o backend voltar a funcionar:

1. ✅ Verificar health check: `https://comex-backend-wjco.onrender.com/health`
2. ✅ Criar usuário via Shell (quando estiver rodando)
3. ✅ Testar login no frontend

---

**Última atualização**: 05/01/2026

