"""Cria tabelas materializadas no BigQuery para o dashboard de comex.

1) empresas_comex_estimado — estimativa de importação/exportação por empresa
   (raiz CNPJ × UF). Metodologia: rateia o total de comex de cada UF (período de
   sobreposição 2020-2021) entre as empresas comex-ativas do estado, PONDERANDO
   por porte (nº de estabelecimentos da empresa na base RF).

2) empresas_habilitacao — registro consolidado de habilitação para comex
   (uma linha por raiz CNPJ): anos ativos, período e nº de estabelecimentos.

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<caminho da chave>
    python criar_tabela_estimativa.py
"""
from google.cloud import bigquery

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
ANO_INI, ANO_FIM = 2020, 2021

DDL_ESTIMADO = f"""
CREATE OR REPLACE TABLE `{PROJ}.empresas_comex_estimado` AS
WITH
uf_imp AS (
  SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_importacao_fob AS FLOAT64)) v
  FROM `{PROJ}.importacao_uf_ncm` WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM} GROUP BY uf
),
uf_exp AS (
  SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_exportacao_fob AS FLOAT64)) v
  FROM `{PROJ}.exportacao_uf_ncm` WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM} GROUP BY uf
),
emp AS (
  SELECT
    SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) AS cnpj_raiz,
    UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
    ANY_VALUE(razao_social) AS razao_social,
    ANY_VALUE(cnae_2_primaria) AS cnae
  FROM `{PROJ}.empresasimportexport`
  WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM}
    AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) = 14
  GROUP BY cnpj_raiz, uf
),
peso AS (
  SELECT SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) AS cnpj_raiz, COUNT(*) AS peso
  FROM `{PROJ}.Estabelecimentos_Ativos_UltimoMes` GROUP BY cnpj_raiz
),
emp_p AS (
  SELECT e.cnpj_raiz, e.uf, e.razao_social, e.cnae, COALESCE(p.peso, 1) AS peso
  FROM emp e LEFT JOIN peso p ON p.cnpj_raiz = e.cnpj_raiz
),
uf_w AS (SELECT uf, SUM(peso) AS total_peso, COUNT(*) AS empresas_uf FROM emp_p GROUP BY uf)
SELECT
  emp_p.cnpj_raiz, emp_p.razao_social, emp_p.uf, emp_p.cnae,
  emp_p.peso, uf_w.empresas_uf,
  emp_p.peso / NULLIF(uf_w.total_peso, 0) AS share_uf,
  COALESCE(ui.v, 0) * emp_p.peso / NULLIF(uf_w.total_peso, 0) AS imp_estimado,
  COALESCE(ue.v, 0) * emp_p.peso / NULLIF(uf_w.total_peso, 0) AS exp_estimado,
  {ANO_INI} AS ano_ini, {ANO_FIM} AS ano_fim
FROM emp_p
JOIN uf_w ON uf_w.uf = emp_p.uf
LEFT JOIN uf_imp ui ON ui.uf = emp_p.uf
LEFT JOIN uf_exp ue ON ue.uf = emp_p.uf
"""

DDL_HABILITACAO = f"""
CREATE OR REPLACE TABLE `{PROJ}.empresas_habilitacao` AS
SELECT
  SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) AS cnpj_raiz,
  ANY_VALUE(razao_social) AS razao_social,
  UPPER(TRIM(ANY_VALUE(sigla_uf))) AS uf,
  ANY_VALUE(cnae_2_primaria) AS cnae,
  MIN(ano) AS primeiro_ano,
  MAX(ano) AS ultimo_ano,
  COUNT(DISTINCT ano) AS anos_ativos,
  COUNT(DISTINCT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) AS n_cnpjs
FROM `{PROJ}.empresasimportexport`
WHERE LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) = 14
GROUP BY cnpj_raiz
"""


def main():
    c = bigquery.Client()
    print(f"Projeto: {c.project}")

    print("Criando empresas_comex_estimado (ponderado por porte)...")
    c.query(DDL_ESTIMADO).result()
    n1 = list(c.query(f"SELECT COUNT(*) n FROM `{PROJ}.empresas_comex_estimado`").result())[0].n
    print(f"  OK - {n1} linhas (raiz x UF)")

    print("Criando empresas_habilitacao...")
    c.query(DDL_HABILITACAO).result()
    n2 = list(c.query(f"SELECT COUNT(*) n FROM `{PROJ}.empresas_habilitacao`").result())[0].n
    print(f"  OK - {n2} empresas")

    print("\nValidacao estimativa (Vale/Hidrau):")
    val = f"""
    SELECT razao_social, SUM(imp_estimado) imp, SUM(exp_estimado) exp
    FROM `{PROJ}.empresas_comex_estimado`
    WHERE cnpj_raiz IN ('33592510','44357085')
    GROUP BY razao_social ORDER BY exp DESC LIMIT 5
    """
    for r in c.query(val).result():
        print(f"  {r.razao_social[:30]:30} imp~{r.imp:,.0f} exp~{r.exp:,.0f}")


if __name__ == "__main__":
    main()
