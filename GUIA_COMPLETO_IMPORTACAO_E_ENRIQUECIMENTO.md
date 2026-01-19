# 📋 Guia Completo: Importação e Enriquecimento de Dados

## 🎯 Objetivo

Este guia completo explica todo o processo de importação e enriquecimento de dados para o sistema Comex, incluindo:
1. ✅ Importação manual do arquivo Excel
2. ✅ Configuração do BigQuery no Render
3. ✅ Coleta de empresas do BigQuery (últimos 3 anos)
4. ✅ Importação de CNAE
5. ✅ Enriquecimento com relacionamentos e recomendações

---

## 📁 Passo 1: Importar Arquivo Excel Manualmente

O arquivo Excel já está em: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /importar-excel-manual`
3. **Parâmetros**:
   - `nome_arquivo`: `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
4. **Clique em**: "Try it out" → "Execute"
5. **Aguarde** alguns minutos

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/importar-excel-manual?nome_arquivo=H_EXPORTACAO_E%20IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx' \
  -H 'accept: application/json'
```

**Após importar:**
- Valide com `GET /validar-sistema` → Verifique se `operacoes_comex` tem registros

---

## 🔑 Passo 2: Configurar BigQuery no Render

**⚠️ ESSENCIAL:** BigQuery é necessário para coletar empresas importadoras e exportadoras!

### 2.1. Siga o guia completo:

Consulte: `CONFIGURAR_BIGQUERY_RENDER.md`

**Resumo rápido:**
1. Criar Service Account no Google Cloud
2. Baixar arquivo JSON de credenciais
3. No Render Dashboard → `comex-backend` → Environment
4. Adicionar variável: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
5. Colar o conteúdo completo do JSON
6. Salvar e aguardar deploy

### 2.2. Validar configuração:

```bash
GET /validar-bigquery
```

Deve retornar `"conectado": true`

---

## 📊 Passo 3: Coletar Empresas do BigQuery (Últimos 3 Anos)

Este endpoint coleta empresas dos anos **2019, 2020, 2021** da Base dos Dados.

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /coletar-empresas-bigquery-ultimos-anos`
3. **Clique em**: "Try it out" → "Execute"
4. **Aguarde** alguns minutos (pode demorar 5-10 minutos)

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/coletar-empresas-bigquery-ultimos-anos' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**
- ✅ Conecta ao BigQuery
- ✅ Executa query SQL para anos 2019, 2020, 2021
- ✅ Coleta empresas importadoras e exportadoras
- ✅ Importa para PostgreSQL
- ✅ Relaciona com CNAE automaticamente

**Após coletar:**
- Valide com `GET /validar-sistema` → Verifique se `empresas` tem registros

---

## 📋 Passo 4: Importar CNAE

O arquivo CNAE está em: `C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\CNAE.xlsx`

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `POST /importar-cnae`
3. **Parâmetros**:
   - `nome_arquivo`: `CNAE.xlsx` (padrão)
4. **Clique em**: "Try it out" → "Execute"

### Via curl:

```bash
curl -X 'POST' \
  'https://comex-backend-gecp.onrender.com/importar-cnae?nome_arquivo=CNAE.xlsx' \
  -H 'accept: application/json'
```

**O que este endpoint faz:**
- ✅ Procura arquivo CNAE em múltiplos locais
- ✅ Lê e processa todas as linhas
- ✅ Importa hierarquia CNAE (classe, grupo, divisão, seção)
- ✅ Relaciona com empresas via chave CNAE

---

## 🔗 Passo 5: Enriquecer com CNAE e Relacionamentos

Este é o passo mais importante! Cria recomendações baseadas em **estado, NCM e volume**.

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
   - Se não estiver, continua sem BigQuery

2. **Coleta empresas do BigQuery** (se disponível)
   - Busca empresas da Base dos Dados
   - Cria índice por CNPJ

3. **Carrega dados de CNAE**
   - Procura arquivo CNAE
   - Carrega hierarquia

4. **Enriquece operações**
   - Identifica empresas importadoras e exportadoras
   - Adiciona CNPJ às operações
   - Enriquece com dados de CNAE

5. **Cria recomendações inteligentes** ⭐ NOVO
   - **Baseado em estado**: Empresas do mesmo estado têm maior probabilidade
   - **Baseado em NCM**: Empresas que operam com mesmo NCM têm sinergia
   - **Baseado em volume**: Maior volume = maior probabilidade de recomendação
   - Cria registros em `empresas_recomendadas` para aparecer no dashboard

**Algoritmo de Recomendação:**
- Para cada exportador (por estado + NCM + volume):
  - Busca importadores do mesmo estado e NCM
  - Se não encontrar, busca mesmo estado com NCM diferente (complementaridade)
  - Ordena por volume (maior volume = maior score)
  - Calcula score: Volume (40%) + Quantidade de operações (30%) + Mesmo estado (30%)
  - Cria recomendações para top 5 importadores prováveis

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

## 📊 Passo 6: Validar Resultados

Após executar todos os passos, valide os resultados:

### Via Swagger:

1. **Acesse**: `https://comex-backend-gecp.onrender.com/docs`
2. **Procure**: `GET /validar-sistema`
3. **Clique em**: "Try it out" → "Execute"

### Verifique:

- ✅ `banco_dados.total_registros.operacoes_comex` > 0
- ✅ `banco_dados.total_registros.empresas` > 0
- ✅ `banco_dados.total_registros.empresas_recomendadas` > 0
- ✅ `banco_dados.total_registros.cnae_hierarquia` > 0
- ✅ `relacionamentos.empresas_recomendadas.total` > 0
- ✅ `relacionamentos.relacionamento_operacoes_empresas.cnpjs_relacionados` > 0

---

## 🎯 Ordem Recomendada de Execução

1. ✅ **Importar Excel** → `POST /importar-excel-manual?nome_arquivo=H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx`
2. ✅ **Configurar BigQuery** → Siga `CONFIGURAR_BIGQUERY_RENDER.md`
3. ✅ **Validar BigQuery** → `GET /validar-bigquery`
4. ✅ **Coletar empresas** → `POST /coletar-empresas-bigquery-ultimos-anos`
5. ✅ **Importar CNAE** → `POST /importar-cnae?nome_arquivo=CNAE.xlsx`
6. ✅ **Enriquecer dados** → `POST /enriquecer-com-cnae-relacionamentos`
7. ✅ **Validar resultados** → `GET /validar-sistema`
8. ✅ **Testar dashboard** → Acesse o frontend

---

## ⏱️ Tempo Estimado

- **Importação Excel**: 2-5 minutos
- **Configuração BigQuery**: 5-10 minutos (primeira vez)
- **Validação BigQuery**: < 1 minuto
- **Coleta empresas**: 5-10 minutos
- **Importação CNAE**: 1-2 minutos
- **Enriquecimento**: 5-10 minutos
- **Total**: ~20-40 minutos

---

## 🐛 Troubleshooting

### Problema: Arquivo Excel não encontrado

**Solução:**
- Verifique se o arquivo está em `comex_data/comexstat_csv/`
- Verifique o nome exato do arquivo (case-sensitive)

### Problema: BigQuery não conectado

**Solução:**
- Siga o guia `CONFIGURAR_BIGQUERY_RENDER.md`
- Verifique se o JSON está correto (sem aspas extras)
- Confirme que a service account tem permissões

### Problema: Nenhuma recomendação criada

**Possíveis causas:**
- Não há dados suficientes nas operações
- Empresas não foram identificadas corretamente
- Volume mínimo não atingido (R$ 10.000)

**Solução:**
- Verifique se há dados em `operacoes_comex`
- Verifique se empresas foram coletadas do BigQuery
- Execute novamente após coletar mais dados

---

## 💡 Dicas Importantes

1. **Execute na ordem**: Importar → Configurar → Coletar → Importar CNAE → Enriquecer → Validar
2. **Aguarde cada passo terminar** antes de executar o próximo
3. **Valide sempre** após cada passo para confirmar sucesso
4. **BigQuery é essencial** para recomendações precisas
5. **CNAE é importante** para relacionamentos corretos

---

## 📝 Endpoints Criados

1. **`POST /importar-excel-manual`** - Importa Excel manualmente
2. **`GET /validar-bigquery`** - Valida conexão BigQuery
3. **`POST /coletar-empresas-bigquery-ultimos-anos`** ⭐ NOVO - Coleta empresas (2019-2021)
4. **`POST /importar-cnae`** ⭐ NOVO - Importa CNAE
5. **`POST /enriquecer-com-cnae-relacionamentos`** ⭐ MELHORADO - Cria recomendações inteligentes

**Use na ordem acima!**
