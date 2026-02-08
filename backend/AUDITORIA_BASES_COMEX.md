# Auditoria: Relacionamento entre bases e empresas importadoras/exportadoras

## 1. Resumo do fluxo de dados

| Fonte | Tabela destino | Campos empresa (razao_social/cnpj) |
|-------|----------------|-------------------------------------|
| **BigQuery** `basedosdados.br_me_exportadoras_importadoras.estabelecimentos` | PostgreSQL `empresas` (via script coletar_empresas_base_dos_dados.py) | `razao_social`, `cnpj` → `Empresa.nome`, `Empresa.cnpj` |
| **Excel** ComexStat (NCM/UF/País) | PostgreSQL `operacoes_comex` (via main.py importação ou scripts) | **Não preenchidos** – Excel agregado não traz empresa por operação |
| **Dados exemplo** (popular_dados_exemplo.py) | PostgreSQL `operacoes_comex` | `razao_social_importador`, `razao_social_exportador` preenchidos |
| **BigQuery** comex_stat (municipio_importacao, municipio_exportacao, ncm_*) | – | **Não há loader atual** que grave em `operacoes_comex` com empresa |

**Conclusão:** Hoje, `operacoes_comex.razao_social_importador` e `razao_social_exportador` só são preenchidos quando os dados vêm de **dados de exemplo** ou de um pipeline que popule esses campos. A importação a partir do **Excel** ComexStat **não** preenche empresa; a coleta da **Base dos Dados** (estabelecimentos) alimenta a tabela **Empresa**, não **OperacaoComex**.

---

## 2. Queries de auditoria – PostgreSQL

### 2.1 Contagens gerais

```sql
-- Total de registros em operacoes_comex
SELECT COUNT(*) AS total_registros FROM operacoes_comex;

-- Empresas importadoras distintas (com nome preenchido)
SELECT COUNT(DISTINCT razao_social_importador) AS total_importadoras
FROM operacoes_comex
WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> '';

-- Empresas exportadoras distintas (com nome preenchido)
SELECT COUNT(DISTINCT razao_social_exportador) AS total_exportadoras
FROM operacoes_comex
WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> '';

-- Registros sem importador
SELECT COUNT(*) AS registros_sem_importador
FROM operacoes_comex
WHERE razao_social_importador IS NULL OR TRIM(razao_social_importador) = '';

-- Registros sem exportador
SELECT COUNT(*) AS registros_sem_exportador
FROM operacoes_comex
WHERE razao_social_exportador IS NULL OR TRIM(razao_social_exportador) = '';
```

### 2.2 Amostras de empresas

```sql
-- Top 10 importadoras por quantidade de operações
SELECT razao_social_importador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
FROM operacoes_comex
WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> ''
GROUP BY razao_social_importador
ORDER BY total_operacoes DESC
LIMIT 10;

-- Top 10 exportadoras por quantidade de operações
SELECT razao_social_exportador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
FROM operacoes_comex
WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> ''
GROUP BY razao_social_exportador
ORDER BY total_operacoes DESC
LIMIT 10;
```

### 2.3 Testar filtro por empresa (ex.: VALE)

**PostgreSQL (ILIKE):**
```sql
-- Operações onde o importador contém 'VALE' (case-insensitive)
SELECT COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total
FROM operacoes_comex
WHERE razao_social_importador ILIKE '%VALE%';
```

**SQLite (LOWER + LIKE):** no script `run_audit_queries.py` a mesma lógica usa `LOWER(razao_social_importador) LIKE '%vale%'`.

**Como testar:**
1. **Script de auditoria:** `python run_audit_queries.py` — imprime a seção "Teste filtro por empresa: importador contém 'VALE'" com total de operações e soma de valor_fob.
2. **API:** com o backend rodando, `GET /dashboard/stats?empresa_importadora=Vale` deve refletir os mesmos dados (totais de importação/exportação filtrados por esse termo).
3. **Pytest:** `pytest tests/test_dashboard_stats.py -k filtro_empresa -v` — valida que o filtro por empresa_importadora retorna apenas linhas cujo `razao_social_importador` contém o termo (case-insensitive, por palavras).

---

## 3. Queries de auditoria – BigQuery (Base dos Dados)

### 3.1 Estabelecimentos (empresas importadoras/exportadoras)

```sql
-- Total de estabelecimentos e amostra de razão social
SELECT COUNT(*) AS total FROM `basedosdados.br_me_exportadoras_importadoras.estabelecimentos` WHERE ano = 2021;
SELECT cnpj, razao_social, id_exportacao_importacao FROM `basedosdados.br_me_exportadoras_importadoras.estabelecimentos` WHERE ano = 2021 LIMIT 20;
```

### 3.2 Comex Stat – municipio_importacao / municipio_exportacao

(Se as tabelas forem `basedosdados.br_me_comex_stat.municipio_importacao` e `municipio_exportacao`, verificar na documentação da Base dos Dados os nomes exatos das colunas de empresa/CNPJ.)

```sql
-- Exemplo: listar colunas disponíveis (ajustar nome do dataset/tabela conforme documentação)
-- SELECT * FROM `basedosdados.br_me_comex_stat.municipio_importacao` LIMIT 5;
-- SELECT * FROM `basedosdados.br_me_comex_stat.municipio_exportacao` LIMIT 5;
```

### 3.3 Cruzamento estabelecimentos x comex (quando houver chave comum)

Quando existir uma tabela de operações no BigQuery com CNPJ ou identificador de empresa:

```sql
-- Exemplo conceitual (ajustar nomes de tabelas/colunas conforme schema real):
-- SELECT e.cnpj, e.razao_social, COUNT(*) AS operacoes
-- FROM basedosdados.br_me_comex_stat.municipio_importacao m
-- JOIN basedosdados.br_me_exportadoras_importadoras.estabelecimentos e
--   ON e.cnpj = m.cnpj AND e.ano = 2021
-- GROUP BY e.cnpj, e.razao_social;
```

---

## 4. Endpoint de debug no backend

- **GET** `/dashboard/debug/empresas`
  - **Query params:** `tipo` (opcional: `importador` | `exportador`), `limite` (default 100), `busca` (opcional: substring no nome).
  - **Resposta:** totais em `operacoes_comex`, contagens de importadoras/exportadoras distintas, registros sem importador/exportador, e listas de empresas (nome, total_operacoes, valor_total_fob).

Use para:
- Listar empresas únicas e validar se o filtro por nome deve retornar dados.
- Verificar quantos registros têm `razao_social_importador`/`razao_social_exportador` preenchidos.

---

## 5. Teste do filtro no dashboard

1. **Sem filtro:** `GET /dashboard/stats` → totais gerais.
2. **Com filtro:** `GET /dashboard/stats?empresa_importadora=VALE` → totais apenas de operações cujo importador contém "VALE" (case-insensitive, por palavras).
3. Comparar `valor_total_importacoes` e `valor_total_exportacoes` entre (1) e (2); com filtro, os valores devem ser ≤ aos sem filtro e diferentes por empresa.

---

## 6. Recomendações

1. **Operacoes_comex sem empresa:** Se a maior parte dos registros vier do Excel ComexStat (agregado por NCM/UF/País), `razao_social_importador`/`razao_social_exportador` ficarão nulos. Nesse cenário, o filtro por empresa só terá efeito nos registros que tiverem esses campos preenchidos (ex.: dados exemplo ou outro pipeline).
2. **Pipeline BigQuery → operacoes_comex:** Para ter filtro por empresa com dados reais, é necessário um processo (script ou job) que:
   - Leia operações (ou agregados) das tabelas comex_stat que tenham identificação de empresa (CNPJ ou nome);
   - Faça o JOIN com estabelecimentos (ou equivalente) para obter `razao_social`;
   - Insira/atualize em `operacoes_comex` com `razao_social_importador` e `razao_social_exportador` preenchidos.
3. **Fallback no dashboard:** Quando `razao_social` for nulo, pode-se exibir "Empresa não identificada" ou usar CNPJ se estiver disponível em outra coluna.
4. **Cruzamento empresas_recomendadas:** O script `analisar_empresas_recomendadas.py` usa apenas `OperacaoComex`; ele já filtra por `razao_social_importador.isnot(None)` etc. Garantir que, após um eventual pipeline BigQuery→operacoes_comex, o script seja reexecutado para atualizar `empresas_recomendadas`.

---

## 7. Checklist de validação

- [ ] Rodar queries de auditoria no PostgreSQL e anotar totais (registros, importadoras/exportadoras distintas, sem importador/sem exportador).
- [ ] Chamar `GET /dashboard/debug/empresas` e conferir listas e contagens.
- [ ] Testar `GET /dashboard/stats?empresa_importadora=<nome>` para pelo menos 5 empresas que apareçam em `/dashboard/debug/empresas`.
- [ ] Se usar BigQuery, rodar queries de contagem nas tabelas comex_stat e estabelecimentos e documentar schema (nomes de colunas de empresa/CNPJ) para desenhar o JOIN.
- [ ] Se for criado pipeline BigQuery→operacoes_comex, documentar e rodar; em seguida repetir o checklist acima.
