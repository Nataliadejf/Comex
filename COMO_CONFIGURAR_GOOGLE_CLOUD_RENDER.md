# 🔧 Como Configurar Google Cloud no Render para Coletar Base dos Dados

## 📋 Pré-requisitos

1. ✅ Conta Google Cloud (gratuita)
2. ✅ Projeto BigQuery criado
3. ✅ BigQuery API habilitada

## 🚀 Passo a Passo Completo

### Passo 1: Criar Projeto no Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Clique em **"Select a project"** → **"New Project"**
3. Preencha:
   - **Project name:** `comex-base-dados` (ou outro nome)
   - **Organization:** (deixe padrão)
   - **Location:** (deixe padrão)
4. Clique em **"Create"**
5. Aguarde alguns segundos para o projeto ser criado

### Passo 2: Ativar BigQuery API

1. No Google Cloud Console, vá em **"APIs & Services"** → **"Library"**
2. Busque por **"BigQuery API"**
3. Clique em **"BigQuery API"**
4. Clique em **"Enable"**
5. Aguarde alguns segundos para ativação

### Passo 3: Criar Conta de Serviço

1. Vá em **"IAM & Admin"** → **"Service Accounts"**
2. Clique em **"Create Service Account"**
3. Preencha:
   - **Service account name:** `comex-bigquery`
   - **Service account ID:** (será gerado automaticamente)
   - **Description:** `Conta para acessar Base dos Dados via BigQuery`
4. Clique em **"Create and Continue"**

### Passo 4: Atribuir Permissões

Na tela de permissões:

1. **Role:** Selecione:
   - `BigQuery Data Viewer` (para ler dados)
   - `BigQuery Job User` (para executar queries)
2. Clique em **"Continue"**
3. Clique em **"Done"**

### Passo 5: Criar Chave JSON

1. Clique na conta de serviço criada (`comex-bigquery`)
2. Vá na aba **"Keys"**
3. Clique em **"Add Key"** → **"Create new key"**
4. Escolha **"JSON"**
5. Clique em **"Create"**
6. O arquivo JSON será baixado automaticamente

### Passo 6: Configurar no Render

**Opção A: Variável de Ambiente (Recomendado)**

1. No Render Dashboard, vá em seu **backend** → **Environment**
2. Adicione nova variável:
   - **Key:** `GOOGLE_APPLICATION_CREDENTIALS`
   - **Value:** Cole o conteúdo completo do arquivo JSON baixado
   - ⚠️ **IMPORTANTE:** Cole o JSON completo (começa com `{` e termina com `}`)
3. Clique em **"Save Changes"**

**Opção B: Arquivo de Credenciais (Alternativo)**

Se preferir usar arquivo:

1. Copie o arquivo JSON para `backend/credentials/google-credentials.json`
2. Adicione ao `.gitignore`:
   ```
   backend/credentials/
   *.json
   ```
3. Configure no código para ler do arquivo

### Passo 7: Instalar Biblioteca no Render

A biblioteca `google-cloud-bigquery` já está no `requirements-render-ultra-minimal.txt`, então será instalada automaticamente no deploy.

### Passo 8: Testar Endpoint

Após configurar, teste o endpoint:

**Via PowerShell:**
```powershell
$env:SERVICE_URL="https://comex-4.onrender.com"
.\test_endpoint.ps1
```

**Via cURL:**
```bash
curl -X POST https://comex-4.onrender.com/api/coletar-empresas-base-dados
```

**Via Navegador (não funciona para POST, mas pode testar GET):**
```
https://comex-4.onrender.com/api/validar-dados-banco
```

## ⚠️ Importante

### Segurança

- ✅ **NUNCA** commite o arquivo JSON de credenciais no Git
- ✅ Use variável de ambiente no Render Dashboard
- ✅ Mantenha as credenciais seguras

### Custos

- ⚠️ BigQuery tem **limite gratuito** de 1 TB processado por mês
- ⚠️ A query pode processar vários GB de dados
- ⚠️ Verifique os custos antes de executar queries grandes

### Timeout

- ⏱️ A query pode demorar **vários minutos**
- ⏱️ O endpoint tem timeout de 120 segundos (pode precisar aumentar)
- ⏱️ Verifique os logs do Render para acompanhar o progresso

## 🐛 Troubleshooting

### Erro: "google-cloud-bigquery não instalado"

A biblioteca já está no `requirements-render-ultra-minimal.txt`. Se ainda der erro:
1. Verifique se o deploy foi feito após adicionar a biblioteca
2. Verifique os logs do deploy no Render

### Erro: "Could not automatically determine credentials"

1. Verifique se `GOOGLE_APPLICATION_CREDENTIALS` está configurada no Render
2. Verifique se o JSON está completo e válido
3. Verifique se não há espaços extras no JSON

### Erro: "Permission denied"

1. Verifique se a conta de serviço tem as roles corretas:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`
2. Verifique se o projeto BigQuery está correto
3. Verifique se a BigQuery API está habilitada

### Erro: "Query exceeded limit"

A query pode estar processando muitos dados. Considere:
1. Adicionar `LIMIT` temporário na query
2. Filtrar por estado ou região específica
3. Processar em lotes menores

## 📝 Exemplo de JSON de Credenciais

O arquivo JSON deve ter este formato:

```json
{
  "type": "service_account",
  "project_id": "seu-projeto-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "comex-bigquery@seu-projeto.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## ✅ Checklist

- [ ] Projeto Google Cloud criado
- [ ] BigQuery API habilitada
- [ ] Conta de serviço criada
- [ ] Permissões atribuídas (BigQuery Data Viewer + Job User)
- [ ] Chave JSON baixada
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` configurada no Render
- [ ] Deploy feito após configuração
- [ ] Endpoint testado e funcionando

## 🎯 Próximos Passos

Após configurar:

1. **Teste o endpoint:**
   ```powershell
   $env:SERVICE_URL="https://comex-4.onrender.com"
   .\test_endpoint.ps1
   ```

2. **Verifique os dados:**
   ```
   https://comex-4.onrender.com/api/validar-dados-banco
   ```

3. **Verifique o dashboard:**
   ```
   https://comex-4.onrender.com
   ```
