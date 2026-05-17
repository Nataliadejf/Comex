"""
Estatísticas de comércio exterior filtradas por CNPJ (tabela unificada BQ).
Evita o bug de somar totais de UF inteiras quando o usuário filtra por empresa.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from loguru import logger

_DEFAULT_EMPRESAS_BASE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"
_DEFAULT_UNIFIED = "liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf"


def empresa_filtro_ativo(empresa_importadora: Optional[str], empresa_exportadora: Optional[str]) -> bool:
    return bool((empresa_importadora or "").strip() or (empresa_exportadora or "").strip())


def resolve_cnpjs_empresa_base(client, run_query, bt, table_env, empresa_importadora, empresa_exportadora) -> List[str]:
    """Resolve CNPJ(s) em empresas_base a partir do texto digitado."""
    from google.cloud import bigquery

    termos: List[str] = []
    for t in (empresa_importadora, empresa_exportadora):
        if t and str(t).strip():
            termos.append(str(t).strip())
    if not termos:
        return []

    t_base = bt(table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    termo = termos[0]

    sql_exact = f"""
    SELECT DISTINCT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14
    FROM {t_base}
    WHERE LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')) = 14
      AND UPPER(TRIM(CAST(razao_social AS STRING))) = UPPER(TRIM(@q))
    LIMIT 3
    """
    rows = run_query(client, sql_exact, [bigquery.ScalarQueryParameter("q", "STRING", termo)])
    out = [str(r["cnpj14"]) for r in rows if r.get("cnpj14") and len(str(r["cnpj14"])) == 14]
    if out:
        return out

    like = f"%{termo}%"
    sql_like = f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj14,
      MIN(LENGTH(CAST(razao_social AS STRING))) AS nome_len
    FROM {t_base}
    WHERE LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')) = 14
      AND (
        LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@like)
        OR CAST(cnpj AS STRING) LIKE @like
      )
    GROUP BY cnpj14
    ORDER BY nome_len ASC
    LIMIT 5
    """
    rows = run_query(
        client,
        sql_like,
        [bigquery.ScalarQueryParameter("like", "STRING", like)],
    )
    return [str(r["cnpj14"]) for r in rows if r.get("cnpj14") and len(str(r["cnpj14"])) == 14]


def append_cnpj_filter(where_clause: str, params: List[object], cnpjs: List[str]) -> Tuple[str, List[object]]:
    from google.cloud import bigquery

    if not cnpjs:
        return where_clause, params
    extra = "REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') IN UNNEST(@cnpj_list)"
    if where_clause and where_clause != "1=1":
        where_clause = f"({where_clause}) AND {extra}"
    else:
        where_clause = extra
    params = [*params, bigquery.ArrayQueryParameter("cnpj_list", "STRING", cnpjs)]
    return where_clause, params


def unified_filtered_cte(get_table_ref, where_clause: str) -> str:
    from_clause = get_table_ref()
    return f"""
    WITH filtered AS (
      SELECT
        cnpj,
        razao_social,
        ano,
        mes,
        sigla_uf,
        id_ncm,
        COALESCE(total_importacao_fob, 0) AS total_importacao_fob,
        COALESCE(total_exportacao_fob, 0) AS total_exportacao_fob
      FROM {from_clause} AS src
      WHERE {where_clause}
    )
    """


def stats_payload_unified(
    client,
    run_query,
    cte: str,
    params: List[object],
    tipo_operacao: Optional[str],
    fonte_dados: Dict[str, str],
    *,
    cnpjs_resolvidos: Optional[List[str]] = None,
    razao_resolvida: Optional[str] = None,
) -> Dict:
    """Agrega KPIs/gráficos a partir da tabela unificada (filtro por CNPJ)."""
    top_l = (tipo_operacao or "").strip().lower()
    ncm_metric_imp = "COALESCE(SUM(total_importacao_fob), 0)"
    ncm_metric_exp = "COALESCE(SUM(total_exportacao_fob), 0)"
    if "export" in top_l and "import" not in top_l:
        ncm_order_metric = ncm_metric_exp
    elif "import" in top_l and "export" not in top_l:
        ncm_order_metric = ncm_metric_imp
    else:
        ncm_order_metric = f"({ncm_metric_imp} + {ncm_metric_exp})"

    kpi_sql = cte + " SELECT COALESCE(SUM(total_importacao_fob),0) AS v_imp, COALESCE(SUM(total_exportacao_fob),0) AS v_exp, COUNTIF(total_importacao_fob>0) AS cnt_imp_rows, COUNTIF(total_exportacao_fob>0) AS cnt_exp_rows, COUNT(*) AS cnt_all FROM filtered"
    monthly_sql = cte + " SELECT FORMAT('%04d-%02d', ano, mes) AS ym, COUNT(*) AS registros, COALESCE(SUM(total_importacao_fob+total_exportacao_fob),0) AS valor_mes FROM filtered GROUP BY ano, mes ORDER BY ano, mes"
    ncm_sql = cte + f" SELECT REGEXP_REPLACE(CAST(id_ncm AS STRING), r'[^0-9]', '') AS ncm, {ncm_metric_imp} AS v_imp_ncm, {ncm_metric_exp} AS v_exp_ncm FROM filtered GROUP BY id_ncm ORDER BY {ncm_order_metric} DESC LIMIT 15"
    uf_sql = cte + " SELECT sigla_uf AS uf_key, COALESCE(SUM(total_importacao_fob+total_exportacao_fob),0) AS valor_total, COUNT(*) AS total_operacoes FROM filtered WHERE sigla_uf IS NOT NULL GROUP BY sigla_uf ORDER BY valor_total DESC LIMIT 20"

    jobs = [("kpi", kpi_sql), ("monthly", monthly_sql), ("ncm", ncm_sql), ("uf", uf_sql)]
    agg: Dict[str, List[dict]] = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(lambda j=j: (j[0], run_query(client, j[1], params))) for j in jobs]
        for fu in as_completed(futures):
            name, rows = fu.result()
            agg[name] = rows

    row0 = agg.get("kpi", [{}])[0] if agg.get("kpi") else {}
    v_imp = float(row0.get("v_imp") or 0)
    v_exp = float(row0.get("v_exp") or 0)
    cnt_imp = int(row0.get("cnt_imp_rows") or 0)
    cnt_exp = int(row0.get("cnt_exp_rows") or 0)
    cnt_all = int(row0.get("cnt_all") or 0)

    registros_por_mes: Dict[str, int] = {}
    valores_por_mes: Dict[str, float] = {}
    pesos_por_mes: Dict[str, float] = {}
    for r in agg.get("monthly", []):
        ym = str(r.get("ym") or "")
        if ym:
            registros_por_mes[ym] = int(r.get("registros") or 0)
            valores_por_mes[ym] = float(r.get("valor_mes") or 0)
            pesos_por_mes[ym] = 0.0

    principais_ncms: List[dict] = []
    for r in agg.get("ncm", []):
        ncm_s = str(r.get("ncm") or "").strip()
        if not ncm_s:
            continue
        vi, ve = float(r.get("v_imp_ncm") or 0), float(r.get("v_exp_ncm") or 0)
        if "export" in top_l and "import" not in top_l:
            vtot = ve
        elif "import" in top_l and "export" not in top_l:
            vtot = vi
        else:
            vtot = vi + ve
        if vtot > 0:
            principais_ncms.append({"ncm": ncm_s, "descricao": "", "valor_total": vtot, "total_operacoes": 0})

    principais_paises: List[dict] = []
    for r in agg.get("uf", []):
        uf_k = str(r.get("uf_key") or "").strip()
        if uf_k:
            principais_paises.append(
                {
                    "pais": f"UF: {uf_k}",
                    "valor_total": float(r.get("valor_total") or 0),
                    "total_operacoes": int(r.get("total_operacoes") or 0),
                }
            )

    if "export" in top_l and "import" not in top_l:
        valor_total_usd = v_exp
    elif "import" in top_l and "export" not in top_l:
        valor_total_usd = v_imp
    else:
        valor_total_usd = v_imp + v_exp

    return {
        "volume_importacoes": 0.0,
        "volume_exportacoes": 0.0,
        "volume_disponivel": False,
        "valor_total_usd": valor_total_usd,
        "valor_total_importacoes": v_imp,
        "valor_total_exportacoes": v_exp,
        "quantidade_estatistica_importacoes": float(cnt_imp),
        "quantidade_estatistica_exportacoes": float(cnt_exp),
        "quantidade_estatistica_total": float(cnt_all),
        "principais_ncms": principais_ncms,
        "principais_paises": principais_paises,
        "principais_importadores": [],
        "principais_exportadores": [],
        "registros_por_mes": registros_por_mes,
        "valores_por_mes": valores_por_mes,
        "pesos_por_mes": pesos_por_mes,
        "filtro_empresa_aplicado": True,
        "ufs_filtradas_por_empresa": [],
        "dados_empresa_reais": True,
        "kpis_empresa_indisponiveis": False,
        "cnpjs_resolvidos": cnpjs_resolvidos or [],
        "empresa_resolvida": razao_resolvida,
        "aviso_dados_sem_empresa": None,
        "fonte_dados": fonte_dados,
    }


def stats_payload_empresa_indisponivel(
    fonte_dados: Dict[str, str],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
    cnpjs_tentados: Optional[List[str]] = None,
) -> Dict:
    nome = (empresa_importadora or empresa_exportadora or "empresa").strip()
    aviso = (
        f"Não foi possível obter valores reais de importação/exportação para «{nome}». "
        "As tabelas importacao_uf_ncm e exportacao_uf_ncm são agregadas por UF×NCM (sem CNPJ) — "
        "somar por UF inflaria os totais (ex.: centenas de bilhões). "
        "Os cards abaixo foram ocultados. Para dados por empresa, use a tabela "
        "empresas_ncm_import_export_uf no BigQuery (COMEX_BQ_TABLE_EMPRESAS_NCM) ou ingira "
        "microdados MDIC com CO_EMP/CNPJ."
    )
    if cnpjs_tentados:
        aviso += f" CNPJ(s) consultados na base: {', '.join(cnpjs_tentados)}."

    return {
        "volume_importacoes": 0.0,
        "volume_exportacoes": 0.0,
        "volume_disponivel": False,
        "valor_total_usd": 0.0,
        "valor_total_importacoes": 0.0,
        "valor_total_exportacoes": 0.0,
        "quantidade_estatistica_importacoes": 0.0,
        "quantidade_estatistica_exportacoes": 0.0,
        "quantidade_estatistica_total": 0.0,
        "principais_ncms": [],
        "principais_paises": [],
        "principais_importadores": [],
        "principais_exportadores": [],
        "registros_por_mes": {},
        "valores_por_mes": {},
        "pesos_por_mes": {},
        "filtro_empresa_aplicado": True,
        "ufs_filtradas_por_empresa": [],
        "dados_empresa_reais": False,
        "kpis_empresa_indisponiveis": True,
        "cnpjs_resolvidos": cnpjs_tentados or [],
        "aviso_dados_sem_empresa": aviso,
        "fonte_dados": fonte_dados,
    }


def try_unified_empresa_stats(
    client,
    run_query,
    bt,
    table_env,
    get_table_ref,
    build_main_dashboard_where,
    fonte_dados,
    ym_start: int,
    ym_end: int,
    tipo_operacao: Optional[str],
    ncm: Optional[str],
    ncms: Optional[List[str]],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
) -> Optional[Dict]:
    """Tenta stats pela tabela unificada filtrada por CNPJ. None se falhar ou vazio."""
    if not empresa_filtro_ativo(empresa_importadora, empresa_exportadora):
        return None

    cnpjs = resolve_cnpjs_empresa_base(
        client, run_query, bt, table_env, empresa_importadora, empresa_exportadora
    )
    where_clause, params = build_main_dashboard_where(
        ym_start,
        ym_end,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
        imp_col="total_importacao_fob",
        exp_col="total_exportacao_fob",
        empresa_filter_as_uf_subquery=False,
    )
    if cnpjs:
        where_clause, params = append_cnpj_filter(where_clause, params, cnpjs)

    cte = unified_filtered_cte(get_table_ref, where_clause)
    try:
        payload = stats_payload_unified(
            client,
            run_query,
            cte,
            params,
            tipo_operacao,
            fonte_dados,
            cnpjs_resolvidos=cnpjs,
        )
        total = (payload.get("valor_total_importacoes") or 0) + (payload.get("valor_total_exportacoes") or 0)
        if total <= 0 and cnpjs:
            logger.info("Unified empresa stats zerados para CNPJs %s", cnpjs)
            return None
        if total > 0:
            return payload
        if not cnpjs:
            return None
        return None
    except Exception as exc:
        logger.warning("Falha stats unified por empresa: {}", exc)
        return None
