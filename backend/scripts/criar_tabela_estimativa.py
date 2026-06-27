"""Cria a tabela materializada empresas_comex_estimado no BigQuery.

Metodologia: rateia o total de importação/exportação de cada UF (período de
sobreposição 2020-2021) entre os CNPJs comex-ativos do estado (empresasimportexport).

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<caminho da chave>
    python criar_tabela_estimativa.py
"""
from google.cloud import bigquery

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
DST = f"{PROJ}.empresas_comex_estimado"
ANO_INI, ANO_FIM = 2020, 2021

DDL = f"""
CREATE OR REPLACE TABLE `{DST}` AS
WITH
uf_imp AS (
  SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_importacao_fob AS FLOAT64)) v
  FROM `{PROJ}.importacao_uf_ncm`
  WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM} GROUP BY uf
),
uf_exp AS (
  SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_exportacao_fob AS FLOAT64)) v
  FROM `{PROJ}.exportacao_uf_ncm`
  WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM} GROUP BY uf
),
emp AS (
  SELECT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','') cnpj14,
         ANY_VALUE(razao_social) razao_social,
         UPPER(TRIM(ANY_VALUE(sigla_uf))) uf,
         ANY_VALUE(cnae_2_primaria) cnae
  FROM `{PROJ}.empresasimportexport`
  WHERE ano BETWEEN {ANO_INI} AND {ANO_FIM}
    AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) = 14
  GROUP BY cnpj14
),
uf_n AS (SELECT uf, COUNT(*) n FROM emp GROUP BY uf)
SELECT
  emp.cnpj14 AS cnpj, emp.razao_social, emp.uf, emp.cnae,
  uf_n.n AS empresas_uf,
  COALESCE(ui.v, 0) / NULLIF(uf_n.n, 0) AS imp_estimado,
  COALESCE(ue.v, 0) / NULLIF(uf_n.n, 0) AS exp_estimado,
  {ANO_INI} AS ano_ini, {ANO_FIM} AS ano_fim
FROM emp
JOIN uf_n ON uf_n.uf = emp.uf
LEFT JOIN uf_imp ui ON ui.uf = emp.uf
LEFT JOIN uf_exp ue ON ue.uf = emp.uf
"""


def main():
    c = bigquery.Client()
    print(f"Projeto: {c.project}")
    print("Criando tabela...")
    c.query(DDL).result()
    n = list(c.query(f"SELECT COUNT(*) n FROM `{DST}`").result())[0].n
    print(f"OK - {DST} criada com {n} linhas")

    # Validacao Vale / Hidrau
    val = f"""
    SELECT razao_social, COUNT(*) cnpjs, SUM(imp_estimado) imp, SUM(exp_estimado) exp
    FROM `{DST}`
    WHERE SUBSTR(cnpj,1,8) IN ('33592510','44357085')
    GROUP BY razao_social ORDER BY exp DESC LIMIT 5
    """
    print("\nValidacao:")
    for r in c.query(val).result():
        print(f"  {r.razao_social[:35]:35} cnpjs={r.cnpjs} imp~{r.imp:,.0f} exp~{r.exp:,.0f}")


if __name__ == "__main__":
    main()
