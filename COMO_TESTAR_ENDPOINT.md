# 🧪 Como Testar o Endpoint de Coleta da Base dos Dados

## ✅ Pré-requisitos

- [x] Google Cloud configurado
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` configurada no Render Dashboard
- [ ] Manual Deploy feito no Render

## 🔧 Configurar Credenciais no Render

### Passo 1: Obter JSON de Credenciais

1. No Google Cloud Console, vá em **"IAM & Admin"** → **"Service Accounts"**
2. Clique na conta de serviço criada
3. Vá em **"Keys"** → **"Add Key"** → **"Create new key"**
4. Escolha **"JSON"** e baixe o arquivo

### Passo 2: Configurar no Render

1. **Render Dashboard** → Seu backend → **"Environment"**
2. Clique em **"+ Add Environment Variable"**
3. Preencha:
   - **Key:** `GOOGLE_APPLICATION_CREDENTIALS`
   - **Value:** Abra o arquivo JSON baixado e **cole TODO o conteúdo** (deve começar com `{` e terminar com `}`)
4. Clique em **"Save Changes"**

**⚠️ IMPORTANTE:**
- Cole o JSON completo, não apenas o caminho do arquivo
- O JSON deve estar em uma única linha ou formato válido
- Não adicione aspas extras

### Passo 3: Fazer Deploy

1. **Render Dashboard** → Seu backend → **"Manual Deploy"**
2. Clique em **"Deploy latest commit"**
3. Aguarde o deploy completar

## 🚀 Testar o Endpoint

### Opção 1: PowerShell (Recomendado)

```powershell
# Configurar URL do serviço
$env:SERVICE_URL="https://comex-4.onrender.com"

# Executar teste
.\test_endpoint.ps1
```

O script vai:
1. ✅ Chamar o endpoint `/api/coletar-empresas-base-dados`
2. ✅ Mostrar a resposta
3. ✅ Executar `check_db.py` para verificar dados no banco

### Opção 2: cURL

```bash
curl -X POST https://comex-4.onrender.com/api/coletar-empresas-base-dados \
  -H "Content-Type: application/json" \
  --max-time 300
```

### Opção 3: Postman/Insomnia

1. **Método:** `POST`
2. **URL:** `https://comex-4.onrender.com/api/coletar-empresas-base-dados`
3. **Headers:** `Content-Type: application/json`
4. **Body:** (vazio)
5. **Timeout:** 300 segundos (a query pode demorar)

### Opção 4: Navegador (apenas para verificar se endpoint existe)

```
https://comex-4.onrender.com/docs
```

Procure por `/api/coletar-empresas-base-dados` na documentação interativa.

## 📊 Resposta Esperada

### Sucesso:

```json
{
  "success": true,
  "message": "Dados coletados e importados com sucesso",
  "total_registros_coletados": 50000,
  "empresas_inseridas": 45000,
  "empresas_atualizadas": 5000,
  "total_empresas_no_banco": 50000,
  "estatisticas": {
    "por_tipo": {
      "Exportadora": 20000,
      "Importadora": 25000,
      "Ambos": 5000
    },
    "top_10_estados": {
      "SP": 15000,
      "RJ": 8000,
      ...
    }
  }
}
```

### Erro:

```json
{
  "detail": "Erro ao executar query no BigQuery: ..."
}
```

## ⏱️ Tempo de Execução

- ⏱️ **Query BigQuery:** 2-10 minutos (dependendo do volume)
- ⏱️ **Importação PostgreSQL:** 1-5 minutos
- ⏱️ **Total:** 3-15 minutos

**⚠️ IMPORTANTE:** O endpoint pode demorar vários minutos. Não feche a conexão!

## 🔍 Verificar Logs

Durante a execução, verifique os logs no Render:

1. **Render Dashboard** → Seu backend → **"Logs"**
2. Procure por:
   - `🔌 Conectando ao BigQuery...`
   - `📊 Executando query no BigQuery...`
   - `⏳ Aguardando resultados...`
   - `✅ Query executada com sucesso!`
   - `🗄️ Importando dados para PostgreSQL...`
   - `✅ X empresas inseridas`

## 🐛 Troubleshooting

### Erro: "google-cloud-bigquery não instalado"

1. Verifique se `google-cloud-bigquery==3.13.0` está no `requirements-render-ultra-minimal.txt`
2. Faça Manual Deploy novamente

### Erro: "Could not automatically determine credentials"

1. Verifique se `GOOGLE_APPLICATION_CREDENTIALS` está configurada no Render
2. Verifique se o JSON está completo e válido
3. Tente fazer deploy novamente

### Erro: "Permission denied"

1. Verifique se a conta de serviço tem as roles:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`
2. Verifique se a BigQuery API está habilitada

### Erro: "Query exceeded limit"

A query pode estar processando muitos dados. Considere:
1. Adicionar `LIMIT` temporário na query
2. Filtrar por estado específico
3. Processar em lotes menores

### Timeout

Se o endpoint der timeout:
1. A query pode estar rodando em background
2. Verifique os logs do Render
3. Tente novamente após alguns minutos

## ✅ Verificar Dados Após Importação

### Via API:

```
https://comex-4.onrender.com/api/validar-dados-banco
```

### Via Script Local:

```powershell
python check_db.py
```

### Via Dashboard:

```
https://comex-4.onrender.com
```

## 📝 Checklist Final

- [ ] Google Cloud configurado
- [ ] Conta de serviço criada com permissões corretas
- [ ] JSON de credenciais baixado
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` configurada no Render
- [ ] Manual Deploy feito
- [ ] Endpoint testado
- [ ] Dados verificados no banco
- [ ] Dashboard mostrando dados
