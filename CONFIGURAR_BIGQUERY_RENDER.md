# 🔧 Guia Passo a Passo: Configurar BigQuery no Render

## 🎯 Objetivo

Configurar as credenciais do Google Cloud BigQuery no Render para que o sistema possa coletar dados da Base dos Dados.

---

## 📋 Pré-requisitos

1. ✅ Conta Google Cloud configurada
2. ✅ Projeto BigQuery criado
3. ✅ Credenciais do Google Cloud baixadas (arquivo JSON)

---

## 🔑 Passo 1: Obter Credenciais do Google Cloud

### 1.1. Acesse o Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Selecione seu projeto (ou crie um novo)

### 1.2. Criar Service Account

1. Vá em **IAM & Admin** → **Service Accounts**
2. Clique em **+ CREATE SERVICE ACCOUNT**
3. Preencha:
   - **Service account name**: `comex-bigquery` (ou outro nome)
   - **Service account ID**: será gerado automaticamente
   - Clique em **CREATE AND CONTINUE**

### 1.3. Conceder Permissões

1. Na seção **Grant this service account access to project**:
   - Role: **BigQuery Data Viewer** (ou **BigQuery User** para mais permissões)
   - Clique em **CONTINUE**
   - Clique em **DONE**

### 1.4. Criar Chave JSON

1. Clique na service account criada
2. Vá na aba **KEYS**
3. Clique em **ADD KEY** → **Create new key**
4. Selecione **JSON**
5. Clique em **CREATE**
6. O arquivo JSON será baixado automaticamente

**⚠️ IMPORTANTE:** Guarde este arquivo em local seguro! Ele contém suas credenciais.

---

## 🚀 Passo 2: Configurar no Render

### 2.1. Acessar Render Dashboard

1. Acesse: https://dashboard.render.com/
2. Faça login na sua conta

### 2.2. Selecionar Serviço Backend

1. Clique no serviço **comex-backend** (ou nome do seu serviço)
2. Vá na aba **Environment**

### 2.3. Adicionar Variável de Ambiente

1. Clique em **Add Environment Variable**
2. Configure:
   - **Key**: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
   - **Value**: Cole o conteúdo completo do arquivo JSON baixado

**⚠️ ATENÇÃO:**
- O valor deve ser o JSON completo, começando com `{` e terminando com `}`
- Não adicione aspas extras
- O JSON deve estar em uma única linha (sem quebras)

### 2.4. Exemplo de Valor

O valor deve ser algo assim (mas com seus dados reais):

```json
{"type":"service_account","project_id":"seu-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...@....iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

### 2.5. Salvar e Fazer Deploy

1. Clique em **Save Changes**
2. O Render fará deploy automático
3. Aguarde o deploy terminar

---

## ✅ Passo 3: Validar Configuração

### 3.1. Via Swagger

1. Acesse: `https://comex-backend-gecp.onrender.com/docs`
2. Procure: `GET /validar-bigquery`
3. Clique em **Try it out** → **Execute**
4. Verifique se retorna `"conectado": true`

### 3.2. Via curl

```bash
curl -X 'GET' \
  'https://comex-backend-gecp.onrender.com/validar-bigquery' \
  -H 'accept: application/json'
```

### 3.3. Resposta Esperada

```json
{
  "conectado": true,
  "credenciais_configuradas": true,
  "credenciais_validas": true,
  "teste_query": true,
  "detalhes": {
    "project_id": "seu-project-id"
  }
}
```

---

## 🐛 Troubleshooting

### Problema: "JSON inválido"

**Solução:**
- Verifique se copiou o JSON completo
- Remova qualquer espaço ou quebra de linha extra
- Certifique-se de que começa com `{` e termina com `}`

### Problema: "Erro ao criar credenciais"

**Solução:**
- Verifique se o JSON está correto
- Confirme que o `project_id` está presente no JSON
- Verifique se a service account tem permissões no BigQuery

### Problema: "Biblioteca não instalada"

**Solução:**
- Adicione `google-cloud-bigquery` ao `requirements.txt`
- Faça commit e push
- O Render instalará automaticamente

### Problema: "Permission denied"

**Solução:**
- Verifique se a service account tem a role **BigQuery Data Viewer** ou **BigQuery User**
- Confirme que o projeto está correto

---

## 📝 Checklist Final

- [ ] Service Account criada no Google Cloud
- [ ] Chave JSON baixada
- [ ] Variável `GOOGLE_APPLICATION_CREDENTIALS_JSON` adicionada no Render
- [ ] Valor JSON colado corretamente (sem aspas extras)
- [ ] Deploy realizado
- [ ] Validação executada com sucesso (`GET /validar-bigquery`)

---

## 💡 Dicas Importantes

1. **Segurança**: Nunca compartilhe o arquivo JSON de credenciais
2. **Backup**: Guarde uma cópia segura do arquivo JSON
3. **Permissões**: Use apenas as permissões necessárias (princípio do menor privilégio)
4. **Validação**: Sempre valide após configurar para confirmar que está funcionando

---

## 🎯 Próximos Passos

Após configurar o BigQuery:

1. ✅ Validar conexão: `GET /validar-bigquery`
2. ✅ Coletar empresas: `POST /coletar-empresas-bigquery-ultimos-anos`
3. ✅ Importar CNAE: `POST /importar-cnae`
4. ✅ Enriquecer dados: `POST /enriquecer-com-cnae-relacionamentos`
