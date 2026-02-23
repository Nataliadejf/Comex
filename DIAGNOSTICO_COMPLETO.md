# DIAGNÓSTICO COMPLETO: Por que os cards mostram valores iguais / vazios

## 📊 RESUMO EXECUTIVO

Os cards do dashboard mostram valores iguais/vazios porque **79% dos registros da base (510.000 de 643.701) possuem `valor_fob=0.0` e `ncm='00000000'`** — dados de baixa qualidade importados do BigQuery sem acompanhamento de valores reais.

**Empresas testadas:**
- **VALE S.A.**: 3.242 registros, **todos com `valor_fob=0.0`** (não há dados financeiros para essa empresa na base)
- **HIDRAU**: 1.087 registros, **todos com `valor_fob=0.0`** (mesma situação)

---

## 1️⃣ ANÁLISE DOS REGISTROS

### Distribuição de Qualidade de Dados

| Origem | Total | Zeros | Não-zeros | Valor Total |
|--------|-------|-------|-----------|-------------|
| **BigQuery** | 510.000 | 510.000 (100%) | 0 | $0.0 Mi |
| **Importação Excel 2025** | 133.201 | 0 | 133.201 (100%) | $10.041,24 Mi |
| **Outros (NULL)** | 500 | 0 | 500 (100%) | $254,56 Mi |
| **TOTAL** | **643.701** | **510.000 (79%)** | **133.701 (21%)** | **$10.295,80 Mi** |

### Distribuição de valor_fob

```
0.0 (ZERO)           510.000 registros (79%)   = $0.00 Mi
Acima de 10k         46.041 registros          = $10.129,16 Mi
1k a 9.9k            39.439 registros          = $153,07 Mi
100 a 999.99         30.369 registros          = $12,91 Mi
0.01 a 99.99         17.852 registros          = $0,65 Mi
```

---

## 2️⃣ SITUAÇÃO ESPECÍFICA: VALE S.A. e HIDRAU

### VALE S.A. (razão social importador)

#### Contagem por CNPJ:
```
33592510037821  →  35 registros (estado: MA)
33592510042400  →  35 registros (estado: MA)
22016026000160  →  32 registros (estado: MA)
34733618000182  →  31 registros (estado: RO)
... (total ~3.242 registros)
```

#### Estados onde opera:
- MA (Maranhão)
- RO (Rondônia)
- PB (Paraíba)
- BA (Bahia)
- ES (Espírito Santo)
- MG (Minas Gerais)

#### NCM (Código de Nomenclatura Comum)
- **Todos os registros possuem NCM = '00000000'** (inválido/incompleto)
- Isso significa: produtos não foram classificados adequadamente no import

#### Valores:
- **Todos os 3.242 registros têm `valor_fob=0.0`** (sem valor financeiro)
- **Arquivo de origem: 'BigQuery'** (dados históricos, não validados)

**Amostra de 1 linha:**
```
ID: 134117
CNPJ Importador: 33592510037821
Razão Social: VALE S.A.
UF: MA
Tipo: IMPORTAÇÃO
Data Operação: 2002-01-01
NCM: 00000000
Descrição Produto: (vazio)
Valor FOB: 0.0
Arquivo: BigQuery
```

### HIDRAU TORQUE

#### Contagem por CNPJ:
```
19502657000185  →  25 registros (estado: MG)
23194194000109  →  25 registros (estado: MG)
03366075000189  →  23 registros (estado: PR)
00805870000138  →  22 registros (estado: RS)
... (total ~1.087 registros, nenhum com razão social exata)
```

**⚠️ Nota importante:** O CNPJ 19502657000185 está associado a **"EMH ELETROMECANICA E HIDRAULICA LTDA"**, não a "HIDRAU TORQUE INDUSTRIA COMERCIO...". Os registros foram encontrados por LIKE '%HIDRAU%' mas o nome exato não está na base.

#### Estados onde opera:
- MG (Minas Gerais)
- PR (Paraná)
- RS (Rio Grande do Sul)

#### NCM:
- Todos '00000000' (mesma situação que VALE)

#### Valores:
- Todos 1.087 registros têm `valor_fob=0.0`
- **Arquivo: 'BigQuery'**

---

## 3️⃣ CAUSA RAIZ

### Por que os cards mostram "0" ou valores iguais?

1. **Dados de BigQuery (79% da base) são de baixa qualidade:**
   - `valor_fob = 0.0` (não agregam valor)
   - `ncm = '00000000'` (produto não classificado)
   - Descrição do produto: vazia
   - Data de operação: muito antiga (1999-2010)

2. **Dashboard filtrando por empresa VALE/HIDRAU:**
   - Queryback retorna 3.242 (VALE) e 1.087 (HIDRAU) registros, mas **todos com valor=0**
   - SUM(valor_fob) = 0 para ambas
   - Cards exibem "0" ou ficam vazios

3. **Ausência de mapeamento robusto empresa-operação:**
   - Tabela `empresas` (cadastro oficial com CNPJ) não está vinculada a `operacoes_comex`
   - Só há match por `razao_social_importador` (string, sujeita a variações)
   - Muitos registros têm o CNPJ correto, mas razão social diferente ou incompleta

---

## 4️⃣ SOLUÇÃO RECOMENDADA

### 🔴 CURTO PRAZO (Quick Fix)

1. **Limpar registros inúteis:**
   ```sql
   DELETE FROM operacoes_comex 
   WHERE arquivo_origem = 'BigQuery' 
   AND valor_fob = 0 
   AND ncm = '00000000';
   ```
   → Remove 510.000 registros de baixa qualidade

2. **Verificar se há dados válidos sem arquivo_origem:**
   - 500 registros com arquivo_origem=NULL possuem NCMs válidos e valores reais ($254 Mi)
   - Esses dados devem ser mantidos e catalogados

3. **Resultado esperado:**
   - Base passa de 643.701 para ~133.701 registros (apenas dados de qualidade)
   - VALE e HIDRAU desaparecem dos cards (0 registros com valor real)
   - **OU** aparecem com valores reais se tiverem operações no Excel 2025

### 🟡 MÉDIO PRAZO (Data Quality)

1. **Criar foreign key CNPJ:**
   - Adicionar coluna `id_empresa` em `operacoes_comex`
   - Relacionar por CNPJ com tabela `empresas`
   - Eliminar dependência de match por `razao_social` (string)

2. **Validar/catalogar NCMs:**
   - Substituir `ncm=00000000` por valores reais
   - Se há fonte original (arquivo CSV), re-importar com parsing correto
   - Senão, marcar como "não classificado" e filtrar do dashboard

3. **Importação de dados 2025:**
   - Arquivo `H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx` tem dados bom s
   - Contém operações de 133.201 registros com $10.041 Mi
   - **Verificar:** se VALE e HIDRAU aparecem aqui com dados válidos

### 🟢 LONGO PRAZO (Arquitetura)

1. **Source of Truth para empresas:**
   - Integração com base pública (CNPJ.js, Receita Federal, etc.)
   - Sincronizar `empresas` com fontes confiáveis

2. **Pipeline de importação robusto:**
   - Validação de schema antes de insert
   - Detecção de duplicatas
   - Rastreabilidade de fonte (arquivo, data, versão)

3. **Dashboard adaptado:**
   - Se empresa não tem dados, mostrar mensagem: "Nenhuma operação com dados financeiros cadastrada"
   - Filtros por CNPJ (além de razão social)
   - Período selecionável (ex.: últimos 2 anos)

---

## 5️⃣ SCRIPTS CRIADOS PARA DIAGNÓSTICO

- `backend/check_cnpj_operations.py` → Lista CNPJs, operações por UF e NCMs
- `backend/sample_raw_rows.py` → Amostra linhas brutas com todos os campos
- `backend/diagnose_data_quality.py` → Distribuição de valor_fob e análise por arquivo_origem
- `backend/check_companies.py` → (existente) Busca exato/LIKE para empresas

---

## 6️⃣ PRÓXIMOS PASSOS IMEDIATOS

**Você quer que eu:**

A. [ ] **Delete os registros BigQuery zerados** (remove 510k registros, libera espaço)
B. [ ] **Verifique se Excel 2025 tem VALE e HIDRAU** (procuro nomes nele)
C. [ ] **Crie migration para foreign key CNPJ** (relaciona `empresas` à `operacoes_comex`)
D. [ ] **Ajuste o dashboard para esconder empresas com 0 registros** de qualidade

Recomendo: **B + D** primeiro, depois **A** se confirmado que Excel 2025 não tem esses nomes.
