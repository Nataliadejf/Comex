"""
Endpoint de inteligência empresarial estilo Logcomex.
Combina: perfil RF + comex real por CNPJ + mercado por UF + sugestão por CNAE.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from fastapi import APIRouter, Query
from loguru import logger

router = APIRouter(prefix="/api/empresa-intel", tags=["empresa-intel"])

_DEFAULT_UNIFIED = "liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf"
_DEFAULT_IMPORT_UF = "liquid-receiver-483923-n6.Projeto_Comex.importacao_uf_ncm"
_DEFAULT_EXPORT_UF = "liquid-receiver-483923-n6.Projeto_Comex.exportacao_uf_ncm"
_DEFAULT_EMPRESAS_BASE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"
_DEFAULT_ESTAB = "liquid-receiver-483923-n6.Projeto_Comex.Estabelecimentos_Ativos_UltimoMes"
_DEFAULT_NCM_DESC = "liquid-receiver-483923-n6.Projeto_Comex.ncm_descricao"


def _bt(s: str) -> str:
    r = (s or "").strip().strip("`")
    return f"`{r}`" if r else ""


def _env(key: str, default: str) -> str:
    return (os.getenv(key) or default).strip().strip("`")


def _get_bq_client():
    from services.bq_client import get_bigquery_client
    return get_bigquery_client()


def _run_query(client, sql: str, params=None):
    from services.bq_client import run_query
    return run_query(client, sql, params)


_PROJECT_DATASET = "liquid-receiver-483923-n6.Projeto_Comex"


@router.get("/inspecionar")
async def inspecionar_tabelas(
    tabelas: str = Query(..., description="Nomes de tabelas separados por vírgula"),
):
    """Diagnóstico: schema + 1 amostra + contagem de linhas para cada tabela."""
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e)}

    out = {}
    for nome in [t.strip() for t in tabelas.split(",") if t.strip()]:
        full = nome if "." in nome else f"{_PROJECT_DATASET}.{nome}"
        info: Dict = {"tabela": full}
        try:
            from google.cloud import bigquery
            proj, ds, tbl = full.split(".")
            cols = _run_query(
                client,
                f"SELECT column_name, data_type FROM `{proj}.{ds}.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = @t ORDER BY ordinal_position",
                [bigquery.ScalarQueryParameter("t", "STRING", tbl)],
            )
            info["colunas"] = [{"nome": c.get("column_name"), "tipo": c.get("data_type")} for c in cols]
        except Exception as e:
            info["colunas_erro"] = str(e)[:300]
        try:
            cnt = _run_query(client, f"SELECT COUNT(*) AS n FROM `{full}`", None)
            info["num_linhas"] = int(cnt[0].get("n") or 0) if cnt else 0
        except Exception as e:
            info["count_erro"] = str(e)[:300]
        try:
            amostra = _run_query(client, f"SELECT * FROM `{full}` LIMIT 1", None)
            info["amostra"] = {k: str(v)[:80] for k, v in (amostra[0].items() if amostra else {})}
        except Exception as e:
            info["amostra_erro"] = str(e)[:300]
        out[nome] = info
    return out


def _resolve_cnpjs(client, termo: str) -> List[str]:
    """Resolve CNPJs a partir de nome ou CNPJ direto via empresas_base."""
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    # Limpar dígitos
    digits_only = "".join(c for c in termo if c.isdigit())
    if len(digits_only) >= 8:
        sql = f"""
        SELECT DISTINCT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14
        FROM {t}
        WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, {len(digits_only)}) = @digits
          AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')) = 14
        LIMIT 10
        """
        rows = _run_query(client, sql, [bigquery.ScalarQueryParameter("digits", "STRING", digits_only)])
        cnpjs = [str(r["cnpj14"]) for r in rows if r.get("cnpj14")]
        if cnpjs:
            return cnpjs

    # Busca por nome
    like = f"%{termo.strip()}%"
    sql_like = f"""
    SELECT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14,
           MIN(LENGTH(CAST(razao_social AS STRING))) AS len_rs
    FROM {t}
    WHERE LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@like)
      AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')) = 14
    GROUP BY cnpj14 ORDER BY len_rs LIMIT 10
    """
    rows = _run_query(client, sql_like, [bigquery.ScalarQueryParameter("like", "STRING", like)])
    return [str(r["cnpj14"]) for r in rows if r.get("cnpj14")]


def _get_razao_base(client, cnpjs: List[str]) -> Dict:
    """Razão social + UF a partir de empresas_base (fonte garantida)."""
    if not cnpjs:
        return {}
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    sql = f"""
    SELECT
        CAST(razao_social AS STRING) AS razao_social,
        UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
        CAST(id_municipio_nome AS STRING) AS municipio
    FROM {t}
    WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') = @cnpj14
    LIMIT 1
    """
    try:
        rows = _run_query(client, sql, [bigquery.ScalarQueryParameter("cnpj14", "STRING", cnpjs[0])])
        return rows[0] if rows else {}
    except Exception as e:
        logger.warning(f"_get_razao_base erro: {e}")
        return {}


def _estab_columns(client, t_ref: str) -> set:
    """Descobre colunas reais da tabela de estabelecimentos (schema varia)."""
    try:
        bare = t_ref.strip().strip("`")
        parts = bare.split(".")
        if len(parts) != 3:
            return set()
        proj, ds, tbl = parts
        sql = f"SELECT column_name FROM `{proj}.{ds}.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = @t"
        from google.cloud import bigquery
        rows = _run_query(client, sql, [bigquery.ScalarQueryParameter("t", "STRING", tbl)])
        return {str(r.get("column_name") or "").lower() for r in rows}
    except Exception as e:
        logger.warning(f"_estab_columns erro: {e}")
        return set()


def _get_estab_profile(client, cnpjs: List[str]) -> Dict:
    """Perfil da empresa via Estabelecimentos_Ativos_UltimoMes (colunas detectadas em runtime)."""
    if not cnpjs:
        return {}
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_ESTAB", _DEFAULT_ESTAB))
    cnpj_raiz = cnpjs[0][:8]
    cols = _estab_columns(client, t)

    # Monta SELECT seguro usando apenas colunas existentes
    def pick(*names, default="NULL"):
        for n in names:
            if n.lower() in cols:
                return f"CAST({n} AS STRING)"
        return default

    razao_expr = pick("razao_social", "nome_empresarial", default="NULL")
    cnae_expr = pick("cnae_fiscal_principal", "cnae_fiscal", default="NULL")
    uf_expr = pick("sigla_uf", "uf", default="NULL")
    mun_expr = pick("nome_municipio", "municipio", "id_municipio_nome", default="NULL")
    sit_expr = pick("situacao_cadastral", default="NULL")
    has_sit = sit_expr != "NULL"

    order_clause = (
        "ORDER BY CASE WHEN CAST(situacao_cadastral AS STRING) IN ('2','02','ATIVA') THEN 0 ELSE 1 END"
        if has_sit else ""
    )
    sql = f"""
    SELECT
        REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14,
        {razao_expr} AS razao_social,
        {cnae_expr} AS cnae,
        UPPER(TRIM({uf_expr})) AS uf,
        {mun_expr} AS municipio,
        {sit_expr} AS situacao,
        COUNT(*) OVER (PARTITION BY SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 8)) AS num_estab
    FROM {t}
    WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 8) = @cnpj_raiz
    {order_clause}
    LIMIT 1
    """
    try:
        rows = _run_query(client, sql, [bigquery.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz)])
        return rows[0] if rows else {}
    except Exception as e:
        logger.warning(f"_get_estab_profile erro: {e}")
        return {}


def _get_comex_empresa(client, cnpjs: List[str], ano_inicio: int, ano_fim: int) -> Dict:
    """Dados reais de comex por CNPJ — queries separadas para evitar ARRAY_AGG aninhado."""
    if not cnpjs:
        return {}
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_NCM", _DEFAULT_UNIFIED))
    params = [
        bigquery.ArrayQueryParameter("cnpj_list", "STRING", cnpjs),
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    cte = f"""
    WITH base AS (
      SELECT
        CAST(sigla_uf AS STRING) AS uf,
        CAST(id_ncm AS STRING) AS ncm,
        CAST(ano AS INT64) AS ano,
        CAST(mes AS INT64) AS mes,
        COALESCE(CAST(total_importacao_fob AS FLOAT64), 0) AS v_imp,
        COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0) AS v_exp
      FROM {t}
      WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') IN UNNEST(@cnpj_list)
        AND CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
    )
    """
    try:
        kpi_sql = cte + "SELECT SUM(v_imp) AS total_imp, SUM(v_exp) AS total_exp, COUNT(DISTINCT ncm) AS num_ncms, COUNT(DISTINCT uf) AS num_ufs FROM base"
        ncm_sql = cte + "SELECT ncm, SUM(v_imp) AS vi, SUM(v_exp) AS ve FROM base GROUP BY ncm ORDER BY SUM(v_imp+v_exp) DESC LIMIT 15"
        uf_sql = cte + "SELECT uf, SUM(v_imp) AS vi, SUM(v_exp) AS ve FROM base GROUP BY uf ORDER BY SUM(v_imp+v_exp) DESC LIMIT 10"
        tl_sql = cte + "SELECT FORMAT('%04d-%02d', ano, mes) AS ym, SUM(v_imp) AS vi, SUM(v_exp) AS ve FROM base GROUP BY ano, mes ORDER BY ano, mes"

        results: Dict = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = {
                pool.submit(_run_query, client, kpi_sql, params): "kpi",
                pool.submit(_run_query, client, ncm_sql, params): "ncm",
                pool.submit(_run_query, client, uf_sql, params): "uf",
                pool.submit(_run_query, client, tl_sql, params): "tl",
            }
            for fut in as_completed(futs):
                results[futs[fut]] = fut.result()

        kpi = (results.get("kpi") or [{}])[0]
        return {
            "total_imp": float(kpi.get("total_imp") or 0),
            "total_exp": float(kpi.get("total_exp") or 0),
            "num_ncms": int(kpi.get("num_ncms") or 0),
            "num_ufs": int(kpi.get("num_ufs") or 0),
            "top_ncms": results.get("ncm") or [],
            "top_ufs": results.get("uf") or [],
            "timeline": results.get("tl") or [],
        }
    except Exception as e:
        logger.warning(f"_get_comex_empresa error: {e}")
        return {}


def _get_market_uf(client, uf: str, ano_inicio: int, ano_fim: int) -> Dict:
    """Dados de mercado (importação+exportação) para a UF da empresa."""
    if not uf:
        return {}
    from google.cloud import bigquery
    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    params = [
        bigquery.ScalarQueryParameter("uf", "STRING", uf.upper()),
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    tl_sql = f"""
    WITH facts AS (
      SELECT ano, mes, COALESCE(CAST(total_importacao_fob AS FLOAT64), 0) AS v_imp, 0.0 AS v_exp
      FROM {t_imp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
      UNION ALL
      SELECT ano, mes, 0.0, COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)
      FROM {t_exp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
    )
    SELECT FORMAT('%04d-%02d', ano, mes) AS ym, SUM(v_imp) AS v_imp, SUM(v_exp) AS v_exp
    FROM facts GROUP BY ano, mes ORDER BY ano, mes
    """
    try:
        # KPI separado e timeline separado
        kpi_sql = f"""
        SELECT
          SUM(COALESCE(CAST(total_importacao_fob AS FLOAT64), 0)) AS total_imp_uf
        FROM {t_imp}
        WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
          AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
        """
        kpe_sql = f"""
        SELECT
          SUM(COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)) AS total_exp_uf
        FROM {t_exp}
        WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
          AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
        """
        results_: Dict = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = {
                pool.submit(_run_query, client, kpi_sql, params): "ki",
                pool.submit(_run_query, client, kpe_sql, params): "ke",
                pool.submit(_run_query, client, tl_sql, params): "tl",
            }
            for fut in as_completed(futs):
                results_[futs[fut]] = fut.result()
        total_imp_uf = float((results_.get("ki") or [{}])[0].get("total_imp_uf") or 0)
        total_exp_uf = float((results_.get("ke") or [{}])[0].get("total_exp_uf") or 0)
        timeline_uf = [
            {"ym": r.get("ym"), "v_imp": float(r.get("v_imp") or 0), "v_exp": float(r.get("v_exp") or 0)}
            for r in (results_.get("tl") or [])
        ]
        return {"total_imp_uf": total_imp_uf, "total_exp_uf": total_exp_uf, "timeline_uf": timeline_uf}
    except Exception as e:
        logger.warning(f"_get_market_uf error: {e}")
        return {}


def _get_top_empresas(client, ano_inicio: int, ano_fim: int) -> Dict:
    """Top importadores e exportadores do Brasil — queries separadas."""
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_NCM", _DEFAULT_UNIFIED))
    params = [
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    cte = f"""
    WITH base AS (
      SELECT
        CAST(razao_social AS STRING) AS razao_social,
        SUM(COALESCE(CAST(total_importacao_fob AS FLOAT64), 0)) AS v_imp,
        SUM(COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)) AS v_exp
      FROM {t}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
        AND razao_social IS NOT NULL
      GROUP BY razao_social
    )
    """
    top_imp_sql = cte + "SELECT razao_social, v_imp FROM base ORDER BY v_imp DESC LIMIT 10"
    top_exp_sql = cte + "SELECT razao_social, v_exp FROM base ORDER BY v_exp DESC LIMIT 10"
    try:
        results: Dict = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = {
                pool.submit(_run_query, client, top_imp_sql, params): "imp",
                pool.submit(_run_query, client, top_exp_sql, params): "exp",
            }
            for fut in as_completed(futs):
                results[futs[fut]] = fut.result()
        return {
            "top_imp": results.get("imp") or [],
            "top_exp": results.get("exp") or [],
        }
    except Exception as e:
        logger.warning(f"_get_top_empresas error: {e}")
        return {}


def _get_market_brasil(client, ano_inicio: int, ano_fim: int) -> Dict:
    """Totais e timeline do Brasil (UF agregado) — queries separadas."""
    from google.cloud import bigquery
    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    params = [
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    kpi_sql = f"""
    SELECT
      SUM(COALESCE(CAST(total_importacao_fob AS FLOAT64), 0)) AS total_imp
    FROM {t_imp} WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
    """
    kpe_sql = f"""
    SELECT
      SUM(COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)) AS total_exp
    FROM {t_exp} WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
    """
    tl_sql = f"""
    WITH facts AS (
      SELECT ano, mes, COALESCE(CAST(total_importacao_fob AS FLOAT64), 0) AS v_imp, 0.0 AS v_exp
      FROM {t_imp} WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
      UNION ALL
      SELECT ano, mes, 0.0, COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)
      FROM {t_exp} WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
    )
    SELECT FORMAT('%04d-%02d', ano, mes) AS ym, SUM(v_imp) AS v_imp, SUM(v_exp) AS v_exp
    FROM facts GROUP BY ano, mes ORDER BY ano, mes
    """
    try:
        results: Dict = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = {
                pool.submit(_run_query, client, kpi_sql, params): "ki",
                pool.submit(_run_query, client, kpe_sql, params): "ke",
                pool.submit(_run_query, client, tl_sql, params): "tl",
            }
            for fut in as_completed(futs):
                results[futs[fut]] = fut.result()
        total_imp = float((results.get("ki") or [{}])[0].get("total_imp") or 0)
        total_exp = float((results.get("ke") or [{}])[0].get("total_exp") or 0)
        return {
            "total_imp": total_imp,
            "total_exp": total_exp,
            "timeline": results.get("tl") or [],
        }
    except Exception as e:
        logger.warning(f"_get_market_brasil error: {e}")
        return {}


def _get_heatmap_uf(client, ano_inicio: int, ano_fim: int) -> List[Dict]:
    """Importação e exportação por UF."""
    from google.cloud import bigquery
    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    sql = f"""
    WITH facts AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
             COALESCE(CAST(total_importacao_fob AS FLOAT64), 0) AS v_imp, 0.0 AS v_exp
      FROM {t_imp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim AND sigla_uf IS NOT NULL
      UNION ALL
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))),
             0.0, COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)
      FROM {t_exp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim AND sigla_uf IS NOT NULL
    )
    SELECT uf, SUM(v_imp) AS total_imp, SUM(v_exp) AS total_exp
    FROM facts GROUP BY uf ORDER BY SUM(v_imp+v_exp) DESC LIMIT 30
    """
    params = [
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    try:
        return _run_query(client, sql, params)
    except Exception as e:
        logger.warning(f"_get_heatmap_uf error: {e}")
        return []


def _get_top_ncms_uf(client, uf: str, ano_inicio: int, ano_fim: int, limit: int = 15) -> List[Dict]:
    """Top NCMs movimentados na UF (dados reais das tabelas UF×NCM)."""
    if not uf:
        return []
    from google.cloud import bigquery
    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    sql = f"""
    WITH facts AS (
      SELECT CAST(id_ncm AS STRING) AS ncm,
             COALESCE(CAST(total_importacao_fob AS FLOAT64), 0) AS v_imp,
             CAST(0 AS FLOAT64) AS v_exp
      FROM {t_imp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
      UNION ALL
      SELECT CAST(id_ncm AS STRING),
             CAST(0 AS FLOAT64),
             COALESCE(CAST(total_exportacao_fob AS FLOAT64), 0)
      FROM {t_exp}
      WHERE CAST(ano AS INT64) BETWEEN @ano_ini AND @ano_fim
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf
    )
    SELECT
      ncm,
      SUM(v_imp) AS v_imp,
      SUM(v_exp) AS v_exp,
      SUM(v_imp + v_exp) AS v_total
    FROM facts
    GROUP BY ncm
    ORDER BY v_total DESC
    LIMIT {int(limit)}
    """
    params = [
        bigquery.ScalarQueryParameter("uf", "STRING", uf.upper()),
        bigquery.ScalarQueryParameter("ano_ini", "INT64", ano_inicio),
        bigquery.ScalarQueryParameter("ano_fim", "INT64", ano_fim),
    ]
    try:
        return _run_query(client, sql, params)
    except Exception as e:
        logger.warning(f"_get_top_ncms_uf error: {e}")
        return []


@router.get("/mercado")
async def mercado_overview(
    ano_inicio: int = Query(2022, ge=2000, le=2030),
    ano_fim: int = Query(2024, ge=2000, le=2030),
):
    """Visão geral do mercado brasileiro: totais, timeline, top empresas, heatmap UF."""
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "timeline": [], "heatmap": [], "top_imp": [], "top_exp": []}

    jobs = {
        "brasil": lambda: _get_market_brasil(client, ano_inicio, ano_fim),
        "top": lambda: _get_top_empresas(client, ano_inicio, ano_fim),
        "heatmap": lambda: _get_heatmap_uf(client, ano_inicio, ano_fim),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(fn): key for key, fn in jobs.items()}
        for fut in as_completed(futs):
            results[futs[fut]] = fut.result()

    brasil = results.get("brasil") or {}
    top = results.get("top") or {}
    heatmap = results.get("heatmap") or []

    timeline = brasil.get("timeline") or []
    top_imp = top.get("top_imp") or []
    top_exp = top.get("top_exp") or []

    return {
        "total_imp": float(brasil.get("total_imp") or 0),
        "total_exp": float(brasil.get("total_exp") or 0),
        "saldo": float((brasil.get("total_exp") or 0) - (brasil.get("total_imp") or 0)),
        "timeline": [
            {"ym": r.get("ym"), "v_imp": float(r.get("v_imp") or 0), "v_exp": float(r.get("v_exp") or 0)}
            for r in timeline
        ],
        "top_importadores": [
            {"nome": r.get("razao_social"), "valor": float(r.get("v_imp") or 0)}
            for r in top_imp
        ],
        "top_exportadores": [
            {"nome": r.get("razao_social"), "valor": float(r.get("v_exp") or 0)}
            for r in top_exp
        ],
        "heatmap": [
            {"uf": r.get("uf"), "v_imp": float(r.get("total_imp") or 0), "v_exp": float(r.get("total_exp") or 0)}
            for r in heatmap
        ],
    }


@router.get("/empresa")
async def empresa_inteligencia(
    q: str = Query(..., min_length=2, description="Nome ou CNPJ da empresa"),
    ano_inicio: int = Query(2022, ge=2000, le=2030),
    ano_fim: int = Query(2024, ge=2000, le=2030),
):
    """Inteligência completa de uma empresa: perfil RF + comex real + mercado UF + sugestão CNAE."""
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "tem_dados_comex": False}

    # 1. Resolver CNPJs
    try:
        cnpjs = _resolve_cnpjs(client, q)
    except Exception as e:
        logger.warning(f"resolve_cnpjs error: {e}")
        cnpjs = []

    if not cnpjs:
        return {
            "tem_dados_comex": False,
            "cnpjs": [],
            "perfil": None,
            "aviso": f"Empresa '{q}' não encontrada na base de dados.",
        }

    # 2. Buscar perfil + comex em paralelo (cada função é resiliente a erros)
    jobs = {
        "perfil": lambda: _get_estab_profile(client, cnpjs),
        "comex": lambda: _get_comex_empresa(client, cnpjs, ano_inicio, ano_fim),
        "razao": lambda: _get_razao_base(client, cnpjs),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(fn): key for key, fn in jobs.items()}
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                results[key] = fut.result()
            except Exception as e:
                logger.warning(f"empresa_intel job '{key}' falhou: {e}")
                results[key] = {}

    perfil = results.get("perfil") or {}
    comex = results.get("comex") or {}
    razao_base = results.get("razao") or {}

    total_imp = float(comex.get("total_imp") or 0)
    total_exp = float(comex.get("total_exp") or 0)
    tem_dados = (total_imp + total_exp) > 0

    uf = str(perfil.get("uf") or razao_base.get("uf") or "").strip() or None

    # 3. Se tem UF, buscar mercado UF
    market_uf: Dict = {}
    if uf:
        try:
            market_uf = _get_market_uf(client, uf, ano_inicio, ano_fim)
        except Exception as e:
            logger.warning(f"market_uf error: {e}")

    cnae = str(perfil.get("cnae") or razao_base.get("cnae") or "").strip() or None

    # 3b. Enriquecer CNAE com hierarquia proprietária (Setor→Segmento→Ramo→Categoria)
    cnae_hierarquia = None
    if cnae:
        try:
            from services import cnae_service
            cnae_hierarquia = cnae_service.enriquecer(cnae)
        except Exception as e:
            logger.warning(f"cnae_service error: {e}")

    # 4. Potencial via mercado UF+NCM (quando não há dados por CNPJ).
    #    A tabela CNPJ→comex está vazia; usamos os NCMs reais movimentados na
    #    UF da empresa como proxy do mercado endereçável do segmento/estado.
    potencial = None
    if not tem_dados and uf:
        try:
            top_ncms_uf = _get_top_ncms_uf(client, uf, ano_inicio, ano_fim, limit=15)
            potencial = {
                "tipo": "mercado_uf_ncm",
                "uf": uf,
                "mercado_imp_uf": float(market_uf.get("total_imp_uf") or 0),
                "mercado_exp_uf": float(market_uf.get("total_exp_uf") or 0),
                "top_ncms_uf": [
                    {"ncm": r.get("ncm"), "v_imp": float(r.get("v_imp") or 0), "v_exp": float(r.get("v_exp") or 0)}
                    for r in top_ncms_uf if r.get("ncm")
                ],
                "cnae_hierarquia": cnae_hierarquia,
                "metodologia": (
                    "Sem registros de importação/exportação por CNPJ na base disponível. "
                    f"O potencial é estimado pelo mercado de comércio exterior da UF {uf} "
                    "(valores FOB reais por NCM), contextualizado pelo segmento CNAE da empresa. "
                    "Representa o mercado endereçável do estado — não o histórico real da empresa."
                ),
            }
        except Exception as e:
            logger.warning(f"potencial UF+NCM error: {e}")

    # 5. Montar timeline
    timeline_empresa = [
        {"ym": r.get("ym"), "v_imp": float(r.get("vi") or 0), "v_exp": float(r.get("ve") or 0)}
        for r in (comex.get("timeline") or [])
    ]
    timeline_uf = [
        {"ym": r.get("ym"), "v_imp": float(r.get("v_imp") or 0), "v_exp": float(r.get("v_exp") or 0)}
        for r in (market_uf.get("timeline_uf") or [])
    ]

    # 6. NCMs
    ncms = [
        {"ncm": r.get("ncm"), "v_imp": float(r.get("vi") or 0), "v_exp": float(r.get("ve") or 0)}
        for r in (comex.get("top_ncms") or [])
    ]

    # 7. UFs
    ufs_empresa = [
        {"uf": r.get("uf"), "v_imp": float(r.get("vi") or 0), "v_exp": float(r.get("ve") or 0)}
        for r in (comex.get("top_ufs") or [])
    ]

    razao = str(perfil.get("razao_social") or razao_base.get("razao_social") or cnpjs[0]).strip()

    return {
        "q": q,
        "cnpjs": cnpjs,
        "razao_social": razao,
        "uf_sede": uf,
        "municipio": str(perfil.get("municipio") or razao_base.get("municipio") or "").strip() or None,
        "cnae": cnae,
        "cnae_hierarquia": cnae_hierarquia,
        "num_estabelecimentos": int(perfil.get("num_estab") or 0),
        "tem_dados_comex": tem_dados,
        "kpis": {
            "total_imp": total_imp,
            "total_exp": total_exp,
            "saldo": total_exp - total_imp,
            "num_ncms": int(comex.get("num_ncms") or 0),
            "num_ufs": int(comex.get("num_ufs") or 0),
        },
        "timeline": timeline_empresa,
        "ncms": ncms,
        "ufs": ufs_empresa,
        "mercado_uf": {
            "uf": uf,
            "total_imp": float(market_uf.get("total_imp_uf") or 0),
            "total_exp": float(market_uf.get("total_exp_uf") or 0),
            "timeline": timeline_uf,
        },
        "potencial": potencial,
        "aviso": None if tem_dados else (
            f"Não há registros de importação/exportação por CNPJ para {razao} na base disponível. "
            f"Exibindo o mercado de comércio exterior da UF {uf or '—'} e os NCMs mais movimentados "
            "no estado como estimativa do mercado endereçável do segmento."
        ),
    }
