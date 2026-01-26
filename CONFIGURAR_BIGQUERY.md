# Como Configurar BigQuery

## ⚠️ Erro Atual

Se você está vendo:
```
❌ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada
```

Isso significa que a variável de ambiente não está configurada localmente.

## 🔧 Solução: Configurar Variável de Ambiente

### Opção 1: PowerShell (Temporário - apenas nesta sessão)

```powershell
# Substitua {SEU_JSON_AQUI} pelo conteúdo do arquivo JSON de credenciais
$env:GOOGLE_APPLICATION_CREDENTIALS_JSON = '{"type":"service_account","project_id":"...","private_key":"..."}'

# Testar
python validar_bigquery.py
```

### Opção 2: Arquivo .env (Recomendado)

1. Crie um arquivo `.env` na raiz do projeto:
```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"liquid-receiver-483923-n6",...}
```

2. O script vai carregar automaticamente se você usar `python-dotenv`

### Opção 3: Configurar no Render (Para produção)

No dashboard do Render:
1. Vá em **Environment** → **Environment Variables**
2. Adicione: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
3. Cole o JSON completo das credenciais

## 📋 Como Obter as Credenciais

1. Acesse: https://console.cloud.google.com/
2. Selecione o projeto: `liquid-receiver-483923-n6`
3. Vá em **IAM & Admin** → **Service Accounts**
4. Crie ou selecione uma service account
5. Vá em **Keys** → **Add Key** → **Create new key** → **JSON**
6. Baixe o arquivo JSON
7. Use o conteúdo completo do JSON como valor da variável

## ✅ Testar Configuração

Após configurar, teste:

```bash
python validar_bigquery.py
```

Deve mostrar:
- ✅ Conectado ao BigQuery
- ✅ Lista de tabelas
- ✅ Contagem de registros

## 🚀 Próximos Passos

Após validar BigQuery:
1. Execute: `python coletar_dados_publicos_standalone.py --apenas-bigquery --limite 1000`
2. Ou teste o endpoint no Render após deploy
