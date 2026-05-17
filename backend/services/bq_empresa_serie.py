"""Série temporal de importação/exportação por empresa via BigQuery."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import bigquery

from services import bq_client as bq

_DEFAULT_UNIFIED = "liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf"
_DEFAULT_EMPRESAS_BASE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"
_DEFAULT_IMPORT = "liquid-receiver-483923-n6.Projeto_Comex.importacao_uf_ncm"
_DEFAULT_EXPORT = "liquid-receiver-483923-n6.Projeto_Comex.exportacao_uf_ncm"


def normalize_cnpj(value: str) -> str:
    d = re.sub(r"\D", "", value or "")
    return d[-14:] if len(d) >= 14 else d


def _pipeline_uses_unified() -> bool:
    src = (os.getenv("BQ_PIPELINE_SOURCE") or "").strip().lower()
    if src in ("unified", "legacy", "empresas_ncm"):
        return True
    if src in ("related", "uf", "uf_facts"):
        return False
    return not bq.use_related_model()


def _uf_ncm_fact_subquery() -> str:
    t_imp = bq.bt(bq.table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT))
    t_exp = bq.bt(bq.table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT))
    return f"""
      SELECT ano, mes, sigla_uf, id_ncm,
        SUM(imp_part) AS total_importacao_fob,
        SUM(exp_part) AS total_exportacao_fob
      FROM (
        SELECT ano, mes, sigla_uf, CAST(id_ncm AS STRING) AS id_ncm,
          COALESCE(total_importacao_fob, 0) AS imp_part, CAST(0 AS FLOAT64) AS exp_part
        FROM {t_imp}
        UNION ALL
        SELECT ano, mes, sigla_uf, CAST(id_ncm AS STRING),
          CAST(0 AS FLOAT64), COALESCE(total_exportacao_fob, 0)
        FROM {t_exp}
      )
      GROUP BY ano, mes, sigla_uf, id_ncm
    """.strip()


def _sql_ufs_from_cnpj(param: str) -> str:
    t_base = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    return f"""
      SELECT DISTINCT UPPER(TRIM(CAST(b.sigla_uf AS STRING))) AS uf
      FROM {t_base} AS b
      WHERE REGEXP_REPLACE(CAST(b.cnpj AS STRING), r'[^0-9]', '') = {param}
        AND b.sigla_uf IS NOT NULL
    """.strip()


def fetch_serie_temporal(
    cnpj: str,
    *,
    tipo: Optional[str] = None,
    ano: Optional[int] = None,
    meses: int = 36,
) -> Dict[str, Any]:
    """
    Retorna série mensal IMP/EXP para um CNPJ.
    Modo unified: valores reais por CNPJ na tabela empresas_ncm_import_export_uf.
    Modo related: proxy por UF(s) da empresa (sem CNPJ nas tabelas de fato).
    """
    c14 = normalize_cnpj(cnpj)
    if len(c14) != 14:
        return {"cnpj": cnpj, "serie": [], "fonte": "invalid_cnpj", "aviso": "CNPJ inválido"}

    client = bq.get_bigquery_client()
    if _pipeline_uses_unified():
        return _fetch_unified(client, c14, tipo=tipo, ano=ano, meses=meses)
    return _fetch_uf_proxy(client, c14, tipo=tipo, ano=ano, meses=meses)


def _fetch_unified(
    client,
    c14: str,
    *,
    tipo: Optional[str],
    ano: Optional[int],
    meses: int,
) -> Dict[str, Any]:
    tref = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_NCM", _DEFAULT_UNIFIED))
    conditions = [
        "REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') = @cnpj",
        "ano IS NOT NULL AND mes IS NOT NULL",
    ]
    params: List[object] = [bigquery.ScalarQueryParameter("cnpj", "STRING", c14)]
    if ano:
        conditions.append("ano = @ano")
        params.append(bigquery.ScalarQueryParameter("ano", "INT64", int(ano)))
    if meses and meses > 0:
        conditions.append("(ano * 100 + mes) >= @ym_min")
        from datetime import date

        today = date.today()
        y, m = today.year, today.month
        m -= max(1, min(120, meses)) - 1
        while m < 1:
            y -= 1
            m += 12
        params.append(bigquery.ScalarQueryParameter("ym_min", "INT64", y * 100 + m))

    where = " AND ".join(conditions)
    sql = f"""
    SELECT
      ano,
      mes,
      COALESCE(SUM(total_importacao_fob), 0) AS importacao_usd,
      COALESCE(SUM(total_exportacao_fob), 0) AS exportacao_usd,
      COUNT(DISTINCT id_ncm) AS qtd_ncms
    FROM {tref}
    WHERE {where}
    GROUP BY ano, mes
    ORDER BY ano, mes
    """
    rows = bq.run_query(client, sql, params)
    serie = _rows_to_serie(rows, tipo=tipo, include_peso=False)
    return {
        "cnpj": c14,
        "serie": serie,
        "fonte": "bigquery_unified",
        "aviso": None,
        "modo": "cnpj",
    }


def _fetch_uf_proxy(
    client,
    c14: str,
    *,
    tipo: Optional[str],
    ano: Optional[int],
    meses: int,
) -> Dict[str, Any]:
    ufs_sql = _sql_ufs_from_cnpj("@cnpj")
    params: List[object] = [bigquery.ScalarQueryParameter("cnpj", "STRING", c14)]
    conditions = [
        "ano IS NOT NULL AND mes IS NOT NULL",
        f"UPPER(TRIM(CAST(sigla_uf AS STRING))) IN ({ufs_sql})",
    ]
    if ano:
        conditions.append("ano = @ano")
        params.append(bigquery.ScalarQueryParameter("ano", "INT64", int(ano)))
    if meses and meses > 0:
        from datetime import date

        today = date.today()
        y, m = today.year, today.month
        m -= max(1, min(120, meses)) - 1
        while m < 1:
            y -= 1
            m += 12
        conditions.append("(ano * 100 + mes) >= @ym_min")
        params.append(bigquery.ScalarQueryParameter("ym_min", "INT64", y * 100 + m))

    u_sql = _uf_ncm_fact_subquery()
    where = " AND ".join(conditions)
    sql = f"""
    SELECT ano, mes,
      COALESCE(SUM(total_importacao_fob), 0) AS importacao_usd,
      COALESCE(SUM(total_exportacao_fob), 0) AS exportacao_usd,
      COUNT(DISTINCT id_ncm) AS qtd_ncms
    FROM ({u_sql}) AS u
    WHERE {where}
    GROUP BY ano, mes
    ORDER BY ano, mes
    """
    rows = bq.run_query(client, sql, params)
    uf_rows = bq.run_query(
        client,
        f"SELECT uf FROM ({ufs_sql}) ORDER BY uf",
        [bigquery.ScalarQueryParameter("cnpj", "STRING", c14)],
    )
    ufs = [str(r.get("uf") or "") for r in uf_rows if r.get("uf")]
    ufs_txt = ", ".join(ufs) if ufs else "nenhuma"
    aviso = (
        f"Valores agregados pela(s) UF(s) da empresa em empresas_base ({ufs_txt}). "
        "As tabelas importacao_uf_ncm/exportacao_uf_ncm não têm CNPJ — não é o total "
        "exclusivo da empresa."
    )
    serie = _rows_to_serie(rows, tipo=tipo, include_peso=False)
    return {
        "cnpj": c14,
        "serie": serie,
        "fonte": "bigquery_uf_proxy",
        "aviso": aviso,
        "modo": "uf_proxy",
        "ufs": ufs,
    }


def _rows_to_serie(
    rows: List[dict],
    *,
    tipo: Optional[str],
    include_peso: bool,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    t = (tipo or "").upper()
    for r in rows:
        periodo = f"{int(r['ano']):04d}-{int(r['mes']):02d}"
        imp = float(r.get("importacao_usd") or 0)
        exp = float(r.get("exportacao_usd") or 0)
        if t == "IMP":
            items = [{"periodo": periodo, "tipo": "IMP", "valor_usd": imp, "ano": r["ano"], "mes": r["mes"]}]
        elif t == "EXP":
            items = [{"periodo": periodo, "tipo": "EXP", "valor_usd": exp, "ano": r["ano"], "mes": r["mes"]}]
        else:
            items = [
                {"periodo": periodo, "tipo": "IMP", "valor_usd": imp, "ano": r["ano"], "mes": r["mes"]},
                {"periodo": periodo, "tipo": "EXP", "valor_usd": exp, "ano": r["ano"], "mes": r["mes"]},
            ]
        for it in items:
            it["qtd_ncms"] = int(r.get("qtd_ncms") or 0)
            it["peso_kg"] = 0.0
        out.extend(items)
    return out


def fetch_ranking_serie(
    *,
    tipo: str = "IMP",
    top_n: int = 10,
    ano: Optional[int] = None,
    meses: int = 24,
) -> Dict[str, Any]:
    """Top N empresas com série temporal (modo unified). Em modo UF, ranking por totais em empresas_base."""
    client = bq.get_bigquery_client()
    if _pipeline_uses_unified():
        return _ranking_unified(client, tipo=tipo, top_n=top_n, ano=ano, meses=meses)
    return _ranking_uf_proxy(client, tipo=tipo, top_n=top_n, ano=ano, meses=meses)


def _ranking_unified(
    client,
    *,
    tipo: str,
    top_n: int,
    ano: Optional[int],
    meses: int,
) -> Dict[str, Any]:
    tref = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_NCM", _DEFAULT_UNIFIED))
    col = "total_importacao_fob" if tipo.upper() == "IMP" else "total_exportacao_fob"
    params: List[object] = [bigquery.ScalarQueryParameter("top_n", "INT64", top_n)]
    extra = ""
    if ano:
        extra = " AND ano = @ano"
        params.append(bigquery.ScalarQueryParameter("ano", "INT64", int(ano)))

    top_sql = f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj,
      ANY_VALUE(razao_social) AS razao_social,
      SUM({col}) AS total_usd
    FROM {tref}
    WHERE cnpj IS NOT NULL {extra}
    GROUP BY cnpj
    HAVING total_usd > 0
    ORDER BY total_usd DESC
    LIMIT @top_n
    """
    top_rows = bq.run_query(client, top_sql, params)
    empresas: List[Dict[str, Any]] = []
    for tr in top_rows:
        cnpj = str(tr.get("cnpj") or "")
        if len(cnpj) != 14:
            continue
        serie_payload = fetch_serie_temporal(cnpj, tipo=tipo, ano=ano, meses=meses)
        empresas.append(
            {
                "cnpj": cnpj,
                "razao_social": tr.get("razao_social"),
                "valor_usd": float(tr.get("total_usd") or 0),
                "serie": serie_payload.get("serie") or [],
            }
        )
    return {"tipo": tipo.upper(), "items": empresas, "fonte": "bigquery_unified"}


def _ranking_uf_proxy(
    client,
    *,
    tipo: str,
    top_n: int,
    ano: Optional[int],
    meses: int,
) -> Dict[str, Any]:
    t_base = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    params: List[object] = [bigquery.ScalarQueryParameter("top_n", "INT64", top_n)]
    sql = f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj,
      ANY_VALUE(CAST(razao_social AS STRING)) AS razao_social,
      ANY_VALUE(CAST(sigla_uf AS STRING)) AS uf
    FROM {t_base}
    WHERE cnpj IS NOT NULL
    GROUP BY cnpj
    ORDER BY razao_social
    LIMIT @top_n
    """
    rows = bq.run_query(client, sql, params)
    items = []
    for r in rows:
        cnpj = str(r.get("cnpj") or "")
        if len(cnpj) != 14:
            continue
        sp = fetch_serie_temporal(cnpj, tipo=tipo, ano=ano, meses=meses)
        items.append(
            {
                "cnpj": cnpj,
                "razao_social": r.get("razao_social"),
                "uf": r.get("uf"),
                "serie": sp.get("serie") or [],
                "aviso": sp.get("aviso"),
            }
        )
    return {
        "tipo": tipo.upper(),
        "items": items,
        "fonte": "bigquery_uf_proxy",
        "aviso": "Ranking limitado; série por UF (proxy), não por valor individual da empresa.",
    }
