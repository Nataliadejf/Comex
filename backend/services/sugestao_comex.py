"""
Sugestão estatística de comércio exterior.
Quando uma empresa não tem histórico em empresas_ncm_import_export_uf,
calcula valores médios de empresas com mesmo CNAE/segmento como referência.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from loguru import logger

_PROJECT = os.getenv("BQ_PROJECT", "liquid-receiver-483923-n6")
_DATASET = os.getenv("BQ_DATASET", "Projeto_Comex")


def _tbl(nome: str) -> str:
    return f"`{_PROJECT}.{_DATASET}.{nome}`"


TBL_EMPRESAS_NCM = _tbl(os.getenv("BQ_TABLE_EMPRESAS_NCM", "empresas_ncm_import_export_uf"))
TBL_ESTAB = _tbl(os.getenv("BQ_TABLE_ESTAB", "Estabelecimentos_Ativos_UltimoMes"))


def sugerir_por_cnae(
    client,
    run_query,
    cnae_codigo: str,
    uf: Optional[str] = None,
    anos: int = 3,
    max_peers: int = 50,
) -> Dict:
    """
    Retorna sugestão de valores comex baseada em empresas com o mesmo CNAE.
    Retorna dict com:
      - valor_imp_sugerido: float (média por empresa/ano)
      - valor_exp_sugerido: float
      - ncms_tipicos: list[dict] (NCMs mais frequentes no segmento)
      - base_calculo: str (descrição da metodologia)
      - num_empresas_referencia: int
    """
    from google.cloud import bigquery as bq_lib

    cnae_str = str(cnae_codigo or "").strip().replace(".", "").replace("-", "")
    if not cnae_str:
        return _sem_dados("CNAE não informado")

    # Prefixo de 4 dígitos para ampliar a busca se necessário
    cnae4 = cnae_str[:4]

    def _consultar_peers(usar_uf: bool) -> dict:
        filtro_uf = "AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf" if (usar_uf and uf) else ""
        sql_peers = f"""
        WITH estab_cnae AS (
            SELECT DISTINCT
                SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 14) AS cnpj14
            FROM {TBL_ESTAB}
            WHERE REGEXP_REPLACE(CAST(cnae_fiscal_principal AS STRING), r'[^0-9]', '') LIKE @cnae_prefix
            {filtro_uf}
            LIMIT {max_peers * 5}
        ),
        comex AS (
            SELECT
                REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14,
                SUM(CAST(total_importacao_fob AS FLOAT64)) AS total_imp,
                SUM(CAST(total_exportacao_fob AS FLOAT64)) AS total_exp
            FROM {TBL_EMPRESAS_NCM}
            WHERE ano >= EXTRACT(YEAR FROM CURRENT_DATE()) - @anos
            GROUP BY cnpj14
            HAVING (total_imp > 0 OR total_exp > 0)
        )
        SELECT
            COUNT(DISTINCT c.cnpj14) AS n_empresas,
            AVG(c.total_imp) AS media_imp,
            AVG(c.total_exp) AS media_exp,
            APPROX_QUANTILES(c.total_imp, 2)[OFFSET(1)] AS mediana_imp,
            APPROX_QUANTILES(c.total_exp, 2)[OFFSET(1)] AS mediana_exp
        FROM estab_cnae e
        JOIN comex c ON c.cnpj14 = e.cnpj14
        """
        params = [
            bq_lib.ScalarQueryParameter("cnae_prefix", "STRING", f"{cnae4}%"),
            bq_lib.ScalarQueryParameter("anos", "INT64", anos),
        ]
        if usar_uf and uf:
            params.append(bq_lib.ScalarQueryParameter("uf", "STRING", uf.upper()))
        rows = run_query(client, sql_peers, params)
        return rows[0] if rows else {}

    # Tenta primeiro com UF (mercado local); se vazio, repete sem UF (segmento nacional)
    abrangencia = "nacional"
    try:
        row = _consultar_peers(usar_uf=bool(uf))
        if int(row.get("n_empresas") or 0) == 0 and uf:
            row = _consultar_peers(usar_uf=False)
        elif uf:
            abrangencia = f"UF {uf.upper()}"
    except Exception as exc:
        logger.warning(f"Sugestão CNAE peers erro: {exc}")
        return _sem_dados("Erro ao consultar base de referência")

    n = int(row.get("n_empresas") or 0)
    if n == 0:
        return _sem_dados(f"Nenhuma empresa com CNAE {cnae_str} encontrada na base comex")

    media_imp = float(row.get("media_imp") or 0)
    media_exp = float(row.get("media_exp") or 0)
    mediana_imp = float(row.get("mediana_imp") or 0)
    mediana_exp = float(row.get("mediana_exp") or 0)

    # NCMs mais frequentes no segmento (sem filtro de UF — segmento nacional)
    uf_ncm = uf if abrangencia != "nacional" else None
    ncms_tipicos = _ncms_tipicos_por_cnae(client, run_query, cnae4, uf_ncm, anos)

    return {
        "tem_sugestao": True,
        "valor_imp_sugerido": mediana_imp or media_imp,
        "valor_exp_sugerido": mediana_exp or media_exp,
        "media_imp": media_imp,
        "media_exp": media_exp,
        "mediana_imp": mediana_imp,
        "mediana_exp": mediana_exp,
        "ncms_tipicos": ncms_tipicos,
        "num_empresas_referencia": n,
        "anos_base": anos,
        "abrangencia": abrangencia,
        "metodologia": (
            f"Valores estimados a partir de {n} empresa(s) com CNAE similar "
            f"(prefixo {cnae4}xx, abrangência {abrangencia}) nos últimos {anos} anos. "
            "Use como referência de mercado — não representa obrigação ou histórico real da empresa."
        ),
    }


def _ncms_tipicos_por_cnae(
    client, run_query, cnae4: str, uf: Optional[str], anos: int
) -> List[dict]:
    from google.cloud import bigquery as bq_lib

    sql = f"""
    WITH estab AS (
        SELECT DISTINCT
            SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 14) AS cnpj14
        FROM {TBL_ESTAB}
        WHERE REGEXP_REPLACE(CAST(cnae_fiscal_principal AS STRING), r'[^0-9]', '') LIKE @cnae_prefix
        {'AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf' if uf else ''}
        LIMIT 500
    )
    SELECT
        CAST(n.id_ncm AS STRING) AS ncm,
        COUNT(DISTINCT n.cnpj) AS freq_empresas,
        SUM(CAST(n.total_importacao_fob AS FLOAT64)) AS total_imp,
        SUM(CAST(n.total_exportacao_fob AS FLOAT64)) AS total_exp
    FROM {TBL_EMPRESAS_NCM} n
    JOIN estab e ON REGEXP_REPLACE(CAST(n.cnpj AS STRING), r'[^0-9]', '') = e.cnpj14
    WHERE n.ano >= EXTRACT(YEAR FROM CURRENT_DATE()) - @anos
    GROUP BY ncm
    ORDER BY freq_empresas DESC, (total_imp + total_exp) DESC
    LIMIT 15
    """
    params = [
        bq_lib.ScalarQueryParameter("cnae_prefix", "STRING", f"{cnae4}%"),
        bq_lib.ScalarQueryParameter("anos", "INT64", anos),
    ]
    if uf:
        params.append(bq_lib.ScalarQueryParameter("uf", "STRING", uf.upper()))

    try:
        rows = run_query(client, sql, params)
        return [
            {
                "ncm": str(r.get("ncm") or "").strip(),
                "freq_empresas": int(r.get("freq_empresas") or 0),
                "total_imp": float(r.get("total_imp") or 0),
                "total_exp": float(r.get("total_exp") or 0),
            }
            for r in rows if r.get("ncm")
        ]
    except Exception as exc:
        logger.warning(f"NCMs típicos CNAE erro: {exc}")
        return []


def _sem_dados(motivo: str) -> Dict:
    return {
        "tem_sugestao": False,
        "valor_imp_sugerido": None,
        "valor_exp_sugerido": None,
        "ncms_tipicos": [],
        "num_empresas_referencia": 0,
        "metodologia": motivo,
    }
