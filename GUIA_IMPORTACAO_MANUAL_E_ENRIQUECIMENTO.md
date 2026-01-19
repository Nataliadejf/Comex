# 📋 Guia: Importação Manual e Enriquecimento com CNAE e Relacionamentos

## 🎯 Objetivo

Este guia explica como:
1. ✅ Importar arquivo Excel manualmente
2. ✅ Validar BigQuery
3. ✅ Enriquecer dados com CNAE
4. ✅ Criar relacionamentos entre empresas importadoras e exportadoras

---

## 📁 Passo 1: Importar Arquivo Excel Manualmente

O arquivo Excel já está em: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /importar-excel-manual`
3. **Parâmetros**:
   - `nome_arquivo`: `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
4. **Clique em**: "Try it out" → "Execute"
5. **Aguarde** alguns minutos (pode demorar dependendo do tamanho do arquivo)

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/importar-excel-manual?nome_arquivo=H_EXPORTACAO_E%20IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**
- ✅ Procura o arquivo Excel em múltiplos locais (local e Render)
- ✅ Lê e processa todas as linhas
- ✅ Importa dados de importação e exportação
- ✅ Evita duplicatas
- ✅ Retorna estatísticas de importação

**Após importar:**
- Valide com `GET /validar-sistema` → Verifique se `operacoes_comex` tem registros

---

## 🔍 Passo 2: Validar BigQuery

Antes de enriquecer com dados do BigQuery, valide se está funcionando:

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `GET /validar-bigquery`
3. **Clique em**: "Try it out" → "Execute"

### Via curl:

```bash
curl -X 'GET' \
  'https://comex-backend-gecp.onrender.com/validar-bigquery' \
  -H 'accept: application/json'
```

**O que este endpoint verifica:**
- ✅ Se as credenciais estão configuradas (`GOOGLE_APPLICATION_CREDENTIALS_JSON`)
- ✅ Se as credenciais são válidas (JSON válido)
- ✅ Se consegue conectar ao BigQuery
- ✅ Se consegue executar uma query de teste

**Resposta esperada:**
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

**Se BigQuery não estiver configurado:**
- Configure `GOOGLE_APPLICATION_CREDENTIALS_JSON` no Render Environment
- Cole o JSON completo das credenciais do Google Cloud
- Faça deploy novamente

---

## 🔗 Passo 3: Enriquecer com CNAE e Relacionamentos

Este é o passo mais importante! Enriquece os dados e cria relacionamentos:

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /enriquecer-com-cnae-relacionamentos`
3. **Clique em**: "Try it out" → "Execute"
4. **Aguarde** alguns minutos (pode demorar 5-10 minutos)

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/enriquecer-com-cnae-relacionamentos' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**

1. **Valida BigQuery**
   - Verifica se está conectado
   - Se não estiver, continua sem BigQuery (usa apenas dados locais)

2. **Coleta empresas do BigQuery** (se disponível)
   - Busca empresas da Base dos Dados
   - Cria índice por CNPJ

3. **Carrega dados de CNAE**
   - Procura arquivo `NOVO CNAE.xlsx` em múltiplos locais
   - Carrega hierarquia CNAE

4. ** Enriquece operações**
   - Identifica empresas importadoras e exportadoras
   - Adiciona CNPJ às operações
   - Enriquece com dados de CNAE

5. **Analisa sinergias**
   - Identifica relacionamentos entre importadoras e exportadoras
   - Calcula potencial de sinergia
   - Cria registros em `empresas_recomendadas`

**Resposta esperada:**
```json
{
  "success": true,
  "message": "Enriquecimento com CNAE e relacionamentos concluído",
  "resultado": {
    "bigquery_validado": true,
    "empresas_coletadas": 1500,
    "empresas_enriquecidas_cnae": 500,
    "relacionamentos_criados": 200,
    "recomendacoes_geradas": 150
  }
}
```

---

## 📊 Passo 4: Validar Resultados

Após executar todos os passos, valide os resultados:

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `GET /validar-sistema`
3. **Clique em**: "Try it out" → "Execute"

### Verifique:

- ✅ `banco_dados.total_registros.operacoes_comex` > 0
- ✅ `banco_dados.total_registros.empresas_recomendadas` > 0
- ✅ `relacionamentos.empresas_recomendadas.total` > 0
- ✅ `relacionamentos.relacionamento_operacoes_empresas.cnpjs_relacionados` > 0

---

## 🎯 Ordem Recomendada de Execução

1. ✅ **Importar Excel** → `POST /importar-excel-manual?nome_arquivo=H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
2. ✅ **Validar BigQuery** → `GET /validar-bigquery`
3. ✅ **Enriquecer dados** → `POST /enriquecer-com-cnae-relacionamentos`
4. ✅ **Validar resultados** → `GET /validar-sistema`
5. ✅ **Testar dashboard** → Acesse o frontend

---

## ⏱️ Tempo Estimado

- **Importação Excel**: 2-5 minutos (depende do tamanho)
- **Validação BigQuery**: < 1 minuto
- **Enriquecimento**: 5-10 minutos
- **Total**: ~10-15 minutos

---

## 🐛 Troubleshooting

### Problema: Arquivo Excel não encontrado

**Solução:**
- Verifique se o arquivo está em `comex_data/comexstat_csv/`
- Verifique o nome exato do arquivo (case-sensitive)
- Se estiver no Render, faça upload do arquivo primeiro

### Problema: BigQuery não conectado

**Solução:**
1. Render Dashboard → `comex-backend` → Environment
2. Adicione: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
3. Cole o JSON completo das credenciais
4. Faça deploy novamente
5. Valide novamente com `GET /validar-bigquery`

### Problema: CNAE não encontrado

**Solução:**
- O arquivo `NOVO CNAE.xlsx` deve estar em um dos locais:
  - `C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx` (local)
  - `/opt/render/project/src/NOVO CNAE.xlsx` (Render)
- Se não tiver o arquivo, o enriquecimento continuará sem CNAE

### Problema: Nenhum relacionamento criado

**Possíveis causas:**
- Não há dados suficientes nas operações
- Empresas não foram identificadas corretamente
- BigQuery não retornou empresas

**Solução:**
- Verifique se há dados em `operacoes_comex`
- Execute `POST /dashboard/analisar-sinergias` como alternativa

---

## 💡 Dicas Importantes

1. **Execute na ordem**: Importar → Validar → Enriquecer → Validar
2. **Aguarde cada passo terminar** antes de executar o próximo
3. **Valide sempre** após cada passo para confirmar sucesso
4. **Se BigQuery não estiver disponível**, o enriquecimento continuará usando apenas dados locais

---

## 📝 Endpoints Criados

1. **`POST /importar-excel-manual`** ⭐ NOVO - Importa Excel manualmente
2. **`GET /validar-bigquery`** ⭐ NOVO - Valida conexão BigQuery
3. **`POST /enriquecer-com-cnae-relacionamentos`** ⭐ NOVO - Enriquece com CNAE e cria relacionamentos

**Use na ordem acima!**
