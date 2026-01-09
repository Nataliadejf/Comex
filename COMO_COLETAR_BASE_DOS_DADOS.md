# 📊 Como Coletar Dados da Base dos Dados (BigQuery)

Este guia explica como executar a query SQL no BigQuery e salvar os dados de empresas exportadoras/importadoras.

## 📋 Pré-requisitos

1. ✅ Conta Google Cloud configurada
2. ✅ Projeto BigQuery criado
3. ✅ Credenciais do Google Cloud configuradas

## 🔧 Configuração Inicial

### Passo 1: Instalar Biblioteca

```bash
pip install google-cloud-bigquery
```

Ou adicione ao `requirements.txt`:
```
google-cloud-bigquery==3.13.0
```

### Passo 2: Configurar Credenciais

**Opção A: Arquivo JSON (Recomendado para desenvolvimento)**

1. Baixe o arquivo de credenciais do Google Cloud Console
2. Configure a variável de ambiente:

**Windows PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\caminho\para\credenciais.json"
```

**Windows CMD:**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\caminho\para\credenciais.json
```

**Linux/Mac:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/para/credenciais.json"
```

**Opção B: Autenticação via gcloud CLI**

```bash
gcloud auth application-default login
```

## 🚀 Executar Script

### Executar Coleta

```bash
cd C:\Users\User\Desktop\Cursor\Projetos\projeto_comex
python backend/scripts/coletar_empresas_base_dos_dados.py
```

### O que o script faz:

1. ✅ Conecta ao BigQuery
2. ✅ Executa a query SQL fornecida
3. ✅ Coleta todos os dados de empresas exportadoras/importadoras
4. ✅ Salva em Excel (`backend/data/empresas_base_dos_dados_TIMESTAMP.xlsx`)
5. ✅ Salva em CSV (`backend/data/empresas_base_dos_dados_TIMESTAMP.csv`)
6. ✅ Opcionalmente importa para PostgreSQL

## 📊 Dados Coletados

A query retorna:

- **Identificação:**
  - CNPJ
  - Razão Social
  - Ano

- **Tipo de Empresa:**
  - id_exportacao_importacao (Exportadora, Importadora, Ambos)

- **CNAE:**
  - CNAE 2.0 Primária
  - Descrições completas (Subclasse, Classe, Grupo, Divisão, Seção)

- **Localização:**
  - Estado (UF)
  - Município
  - CEP
  - Endereço completo

- **Natureza Jurídica:**
  - ID e descrição

## 💾 Arquivos Gerados

Os dados são salvos em:

- **Excel:** `backend/data/empresas_base_dos_dados_YYYYMMDD_HHMMSS.xlsx`
- **CSV:** `backend/data/empresas_base_dos_dados_YYYYMMDD_HHMMSS.csv`

## 🗄️ Importar para PostgreSQL

O script pergunta se deseja importar para PostgreSQL após coletar os dados.

**Ou importe manualmente depois:**

```bash
# Usar o script de importação existente
python backend/scripts/importar_excel_local.py
```

## ⚠️ Importante

- ⏱️ A query pode demorar **vários minutos** dependendo do volume de dados
- 💰 Verifique os **custos do BigQuery** antes de executar queries grandes
- 📊 A Base dos Dados tem **limites de uso gratuito**
- 🔒 Mantenha as **credenciais seguras** (não commite no Git)

## 🐛 Troubleshooting

### Erro: "google-cloud-bigquery não instalado"

```bash
pip install google-cloud-bigquery
```

### Erro: "Could not automatically determine credentials"

Configure a variável `GOOGLE_APPLICATION_CREDENTIALS` com o caminho do arquivo JSON de credenciais.

### Erro: "Permission denied"

Verifique se:
- O projeto BigQuery está configurado corretamente
- As credenciais têm permissão para acessar a Base dos Dados
- O projeto tem acesso à tabela `basedosdados.br_me_exportadoras_importadoras`

### Erro: "Query exceeded limit"

A query pode estar retornando muitos dados. Considere adicionar um `LIMIT` temporário:

```sql
-- Adicionar no final da query
LIMIT 10000
```

## 📝 Exemplo de Uso Completo

```bash
# 1. Configurar credenciais
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\User\credenciais.json"

# 2. Executar coleta
python backend/scripts/coletar_empresas_base_dos_dados.py

# 3. Aguardar conclusão (pode demorar vários minutos)

# 4. Dados serão salvos em backend/data/

# 5. Se escolher importar para PostgreSQL, os dados serão inseridos automaticamente
```

## 🔗 Links Úteis

- [Base dos Dados - Exportadoras/Importadoras](https://basedosdados.org/dataset/br-me-exportadoras-importadoras)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery)
- [Documentação google-cloud-bigquery](https://googleapis.dev/python/bigquery/latest/index.html)
