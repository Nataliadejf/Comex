# 🚀 Como Fazer Deploy Manual no Render

## ⚠️ Quando Fazer Deploy Manual

- Quando você atingir o limite de minutos de pipeline do Free Tier
- Quando o deploy automático não funcionar
- Quando você quiser forçar um novo deploy

## 📋 Passo a Passo

### Opção 1: Via Botão "Manual Deploy" (Mais Rápido)

1. **Acesse o Render Dashboard:**
   ```
   https://dashboard.render.com
   ```

2. **Vá para o serviço:**
   - Clique em **"comex-backend"** na lista de serviços

3. **Clique no botão "Manual Deploy":**
   - Está no topo da página, ao lado de "Connect"
   - Um dropdown vai aparecer

4. **Selecione "Deploy latest commit":**
   - Isso vai fazer deploy do último commit do GitHub

5. **Aguarde o deploy:**
   - Você verá o progresso na página
   - Normalmente leva 2-5 minutos
   - Quando concluir, verá "Your service is live 🎉"

### Opção 2: Via Settings

1. **Acesse o Render Dashboard**

2. **Vá para o serviço:**
   - Clique em **"comex-backend"**

3. **Vá em "Settings"** (no menu lateral esquerdo)

4. **Role até a seção "Build & Deploy"**

5. **Clique em "Manual Deploy"** ou procure por opções de deploy

## ✅ Como Verificar se o Deploy Funcionou

### 1. Verificar Status

No Render Dashboard, você verá:
- ✅ **"Live"** (verde) = Serviço rodando
- ⏳ **"Deploying"** = Deploy em andamento
- ❌ **"Failed"** = Deploy falhou (verifique os logs)

### 2. Verificar Logs

1. No Render Dashboard → **"comex-backend"** → **"Logs"**
2. Procure por:
   - `✅ Router de coleta Base dos Dados incluído` = Sucesso
   - Erros de import ou sintaxe = Problema

### 3. Testar o Endpoint

Após o deploy concluir, teste:
```
https://comex-backend-wjco.onrender.com/api/testar-google-cloud
```

Ou use o script PowerShell:
```powershell
$env:SERVICE_URL="https://comex-backend-wjco.onrender.com"
.\test_google_cloud.ps1
```

## 🔍 Troubleshooting

### Deploy Falhou

1. **Verifique os logs:**
   - Render Dashboard → Backend → Logs
   - Procure por erros de sintaxe ou import

2. **Verifique se o código está no GitHub:**
   - Certifique-se de que fez `git push`

3. **Tente novamente:**
   - Às vezes um segundo deploy resolve

### Deploy Demora Muito

- Deploys normais levam 2-5 minutos
- Se demorar mais de 10 minutos, pode haver um problema
- Verifique os logs para ver onde está travado

### Limite de Pipeline

- **Deploy manual NÃO conta para o limite!**
- Você pode fazer quantos deploys manuais quiser
- Apenas deploys automáticos contam para o limite

## 💡 Dicas

1. **Faça deploys manuais quando necessário:**
   - Não há limite para deploys manuais
   - É a melhor opção quando você atingir limites

2. **Monitore os logs durante o deploy:**
   - Você pode ver o progresso em tempo real
   - Isso ajuda a identificar problemas rapidamente

3. **Use deploys manuais para testes:**
   - Mais rápido que esperar deploy automático
   - Mais controle sobre quando fazer deploy

## 📝 Checklist

Antes de fazer deploy manual:

- [ ] Código commitado no GitHub (`git commit`)
- [ ] Código enviado para GitHub (`git push`)
- [ ] Verificou se não há erros de sintaxe
- [ ] Está pronto para testar após o deploy

Após o deploy:

- [ ] Status mostra "Live"
- [ ] Logs mostram "Router de coleta Base dos Dados incluído"
- [ ] Endpoint `/api/testar-google-cloud` funciona
- [ ] Teste completo passou
