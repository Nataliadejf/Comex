"""
Consultas à Base dos Dados (BigQuery) — comex_stat.
Tenta SQL legada (NO_EXP / VL_FOB); se falhar, usa o schema atual (valor_fob_dolar, município).
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger


def get_bigquery_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except ImportError:
        return None

    creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_env and str(creds_env).strip().startswith("{"):
        try:
            creds_dict = json.loads(creds_env)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            project_id = creds_dict.get("project_id")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            logger.warning("BigQuery: falha ao parsear JSON de credenciais: {}", e)
            return bigquery.Client()

    return bigquery.Client()


def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        d = dict(row.items()) if hasattr(row, "items") else {k: row[k] for k in row.keys()}
        out.append(d)
    return out


def _run_query(client, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig()
    if params:
        qp = []
        for k, v in params.items():
            if isinstance(v, int):
                qp.append(bigquery.ScalarQueryParameter(k, "INT64", v))
            elif isinstance(v, str):
                qp.append(bigquery.ScalarQueryParameter(k, "STRING", v))
            else:
                qp.append(bigquery.ScalarQueryParameter(k, "STRING", str(v)))
        job_config = bigquery.QueryJobConfig(query_parameters=qp)
    job = client.query(sql, job_config=job_config)
    return _rows_to_dicts(job.result())


def empresas_exportadoras(ano: int = 2021, limit: int = 100) -> List[Dict[str, Any]]:
    client = get_bigquery_client()
    if not client:
        return []

    legacy_sql = f"""
    SELECT
        NO_EXP AS nome_empresa,
        CO_UF AS estado,
        SUM(VL_FOB) AS valor_total_fob,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_exportacao`
    WHERE ano = @ano
    GROUP BY NO_EXP, CO_UF
    ORDER BY valor_total_fob DESC
    LIMIT {int(limit)}
    """
    modern_sql = f"""
    SELECT
        COALESCE(mun.nome, CAST(e.id_municipio AS STRING)) AS nome_empresa,
        e.sigla_uf AS estado,
        SUM(e.valor_fob_dolar) AS valor_total_fob,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_exportacao` AS e
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON e.id_municipio = mun.id_municipio
    WHERE e.ano = @ano
    GROUP BY COALESCE(mun.nome, CAST(e.id_municipio AS STRING)), e.sigla_uf
    ORDER BY valor_total_fob DESC
    LIMIT {int(limit)}
    """
    params = {"ano": int(ano)}
    try:
        return _run_query(client, legacy_sql, params)
    except Exception as e:
        logger.info("BigQuery exportadoras: SQL legada indisponível ({}), usando schema atual", e)
    try:
        return _run_query(client, modern_sql, params)
    except Exception as e:
        logger.error("BigQuery exportadoras falhou: {}", e)
        return []


def empresas_importadoras(ano: int = 2021, limit: int = 100) -> List[Dict[str, Any]]:
    client = get_bigquery_client()
    if not client:
        return []

    legacy_sql = f"""
    SELECT
        NO_IMP AS nome_empresa,
        CO_UF AS estado,
        SUM(VL_FOB) AS valor_total_fob,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_importacao`
    WHERE ano = @ano
    GROUP BY NO_IMP, CO_UF
    ORDER BY valor_total_fob DESC
    LIMIT {int(limit)}
    """
    modern_sql = f"""
    SELECT
        COALESCE(mun.nome, CAST(i.id_municipio AS STRING)) AS nome_empresa,
        i.sigla_uf AS estado,
        SUM(i.valor_fob_dolar) AS valor_total_fob,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_importacao` AS i
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON i.id_municipio = mun.id_municipio
    WHERE i.ano = @ano
    GROUP BY COALESCE(mun.nome, CAST(i.id_municipio AS STRING)), i.sigla_uf
    ORDER BY valor_total_fob DESC
    LIMIT {int(limit)}
    """
    params = {"ano": int(ano)}
    try:
        return _run_query(client, legacy_sql, params)
    except Exception as e:
        logger.info("BigQuery importadoras: SQL legada indisponível ({}), usando schema atual", e)
    try:
        return _run_query(client, modern_sql, params)
    except Exception as e:
        logger.error("BigQuery importadoras falhou: {}", e)
        return []


def agregado_municipio_ncm_exportacao(ano: int) -> List[Dict[str, Any]]:
    """UF + id_sh4 + município + valor (para popular empresa_ncm_estado)."""
    client = get_bigquery_client()
    if not client:
        return []

    sql = """
    SELECT
        e.sigla_uf AS estado,
        e.ano AS ano,
        CAST(e.id_sh4 AS STRING) AS id_sh4,
        COALESCE(mun.nome, CAST(e.id_municipio AS STRING)) AS nome_empresa,
        SUM(e.valor_fob_dolar) AS valor_total_fob
    FROM `basedosdados.br_me_comex_stat.municipio_exportacao` AS e
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON e.id_municipio = mun.id_municipio
    WHERE e.ano = @ano
    GROUP BY e.sigla_uf, e.ano, e.id_sh4, COALESCE(mun.nome, CAST(e.id_municipio AS STRING))
    """
    try:
        return _run_query(client, sql, {"ano": int(ano)})
    except Exception as e:
        logger.error("BigQuery agregado exportação: {}", e)
        return []


def agregado_municipio_ncm_importacao(ano: int) -> List[Dict[str, Any]]:
    client = get_bigquery_client()
    if not client:
        return []

    sql = """
    SELECT
        i.sigla_uf AS estado,
        i.ano AS ano,
        CAST(i.id_sh4 AS STRING) AS id_sh4,
        COALESCE(mun.nome, CAST(i.id_municipio AS STRING)) AS nome_empresa,
        SUM(i.valor_fob_dolar) AS valor_total_fob
    FROM `basedosdados.br_me_comex_stat.municipio_importacao` AS i
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON i.id_municipio = mun.id_municipio
    WHERE i.ano = @ano
    GROUP BY i.sigla_uf, i.ano, i.id_sh4, COALESCE(mun.nome, CAST(i.id_municipio AS STRING))
    """
    try:
        return _run_query(client, sql, {"ano": int(ano)})
    except Exception as e:
        logger.error("BigQuery agregado importação: {}", e)
        return []


def sh4_para_ncm_display(id_sh4: str) -> str:
    """Formata id SH4 para chave estilo NCM (8 dígitos)."""
    digits = re.sub(r"\D", "", str(id_sh4 or ""))
    if not digits:
        return "0000.00.00"
    d = (digits + "00000000")[:8]
    return f"{d[:4]}.{d[4:6]}.{d[6:8]}"
