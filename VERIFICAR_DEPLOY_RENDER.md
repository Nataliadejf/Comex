# 🔍 Como Verificar se o Deploy no Render Foi Concluído

## ✅ Verificação Rápida

### 1. Verificar Status do Deploy

1. Acesse: https://dashboard.render.com
2. Vá em **"My Services"** → **"comex-backend"**
3. Verifique se o status está **"Live"** (verde)
4. Veja o último deploy na seção **"Events"**

### 2. Verificar Logs do Render

1. No Render Dashboard → **"comex-backend"** → **"Logs"**
2. Procure por:
   - ✅ `✅ Router de coleta Base dos Dados incluído`
   - ❌ Erros de import ou sintaxe
   - ⚠️ Warnings sobre módulos não encontrados

### 3. Verificar Documentação da API

Acesse no navegador:
```
https://comex-backend-wjco.onrender.com/docs
```

Procure por:
- `/api/testar-google-cloud` (GET)
- `/api/coletar-empresas-base-dados` (POST)

Se esses endpoints **não aparecerem**, o deploy ainda não foi concluído ou há um erro.

## 🔧 Solução de Problemas

### Problema: Endpoint retorna 404

**Causas possíveis:**
1. Deploy ainda em andamento (aguarde 2-5 minutos)
2. Erro no import do módulo `api.coletar_base_dados`
3. Router não foi incluído corretamente

**Solução:**
1. Verifique os logs do Render
2. Procure por erros de import
3. Faça um **Manual Deploy** novamente:
   - Render Dashboard → Backend → **"Manual Deploy"** → **"Deploy latest commit"**

### Problema: Erro de import no log

Se você ver algo como:
```
ImportError: cannot import name 'router' from 'api.coletar_base_dados'
```

**Solução:**
1. Verifique se o arquivo `backend/api/coletar_base_dados.py` existe
2. Verifique se há erros de sintaxe no arquivo
3. Faça commit e push novamente

### Problema: Router não aparece na documentação

**Solução:**
1. Verifique se o router está sendo incluído no `main.py`:
   ```python
   from api.coletar_base_dados import router as coletar_router
   app.include_router(coletar_router)
   ```
2. Verifique se não há erros de sintaxe no `main.py`
3. Faça commit e push novamente

## 🧪 Teste Passo a Passo

### Passo 1: Verificar se o servidor está online

```powershell
curl https://comex-backend-wjco.onrender.com/
```

Deve retornar:
```json
{"message":"Comex Analyzer API", "version":"1.0.0", "status": "online"}
```

### Passo 2: Verificar documentação

Acesse:
```
https://comex-backend-wjco.onrender.com/docs
```

Procure pelos endpoints `/api/testar-google-cloud` e `/api/coletar-empresas-base-dados`

### Passo 3: Testar endpoint de teste

```powershell
$env:SERVICE_URL="https://comex-backend-wjco.onrender.com"
.\test_google_cloud.ps1
```

Ou no navegador:
```
https://comex-backend-wjco.onrender.com/api/testar-google-cloud
```

### Passo 4: Se ainda retornar 404

1. Verifique os logs do Render
2. Faça um Manual Deploy
3. Aguarde 3-5 minutos
4. Tente novamente

## 📋 Checklist de Deploy

- [ ] Código commitado e pushed para GitHub
- [ ] Render detectou o novo commit
- [ ] Build concluído com sucesso
- [ ] Deploy concluído (status "Live")
- [ ] Logs mostram "Router de coleta Base dos Dados incluído"
- [ ] Endpoints aparecem em `/docs`
- [ ] Teste do endpoint funciona

## 🚨 Se Nada Funcionar

1. Verifique se o repositório GitHub está correto no Render
2. Verifique se o branch está correto (deve ser `main`)
3. Tente fazer um **Manual Deploy** forçado
4. Verifique se há limites de quota no Render (free tier tem limites)
5. Entre em contato com o suporte do Render se necessário
