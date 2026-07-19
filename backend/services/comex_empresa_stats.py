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
_DEFAULT_HABILITACAO = "liquid-receiver-483923-n6.Projeto_Comex.empresas_habilitacao"
_DEFAULT_REAL_LOGCOMEX = "liquid-receiver-483923-n6.Projeto_Comex.comex_real_import_logcomex"
_STOP_TERMOS = {"ltda", "sa", "s.a", "s/a", "me", "epp", "eireli", "cia", "e", "de",
                "do", "da", "dos", "das", "&", "-", "ind", "com"}

# Fator de calibração derivado da base REAL Logcomex (importação real ÷ estimativa
# para as mesmas 265 empresas/período): a estimativa por participação-de-UF
# superestima ~17,5×. Aplicado às empresas que NÃO estão na base real.
_FATOR_CALIBRACAO_IMPORT = 0.0573
_FATOR_CALIBRACAO_EXPORT = 0.0573


def _tokens_nome(termo: str) -> list:
    raw = re.findall(r"[0-9a-zà-ÿ]+", (termo or "").lower())
    return [t for t in raw if len(t) >= 2 and t not in _STOP_TERMOS]


def empresa_filtro_ativo(empresa_importadora: Optional[str], empresa_exportadora: Optional[str]) -> bool:
    return bool((empresa_importadora or "").strip() or (empresa_exportadora or "").strip())


def resolve_cnpjs_empresa_base(client, run_query, bt, table_env, empresa_importadora, empresa_exportadora) -> List[str]:
    """Resolve a raiz CNPJ (14 díg. com sufixo 0) a partir do texto digitado,
    buscando na base de empresas comex-ativas (empresas_habilitacao) por
    CNPJ ou por razão social (todos os tokens presentes, ranqueando exato/prefixo)."""
    from google.cloud import bigquery

    termo = ""
    for t in (empresa_importadora, empresa_exportadora):
        if t and str(t).strip():
            termo = str(t).strip()
            break
    if not termo:
        return []

    t_hab = bt(table_env("COMEX_BQ_TABLE_HABILITACAO", _DEFAULT_HABILITACAO))
    digitos = "".join(c for c in termo if c.isdigit())

    # 1) Entrada é CNPJ
    if len(digitos) >= 8:
        sql = f"SELECT DISTINCT cnpj_raiz FROM {t_hab} WHERE cnpj_raiz = @r LIMIT 5"
        rows = run_query(client, sql, [bigquery.ScalarQueryParameter("r", "STRING", digitos[:8])])
        return [str(r.get("cnpj_raiz")) + "000000" for r in rows if r.get("cnpj_raiz")]

    # 2) Busca por razão social (todos os tokens presentes)
    toks = _tokens_nome(termo)
    if not toks:
        return []
    conds, params = [], []
    for i, tk in enumerate(toks):
        conds.append(f"LOWER(CAST(razao_social AS STRING)) LIKE @t{i}")
        params.append(bigquery.ScalarQueryParameter(f"t{i}", "STRING", f"%{tk}%"))
    params.append(bigquery.ScalarQueryParameter("raw", "STRING", termo.lower()))
    params.append(bigquery.ScalarQueryParameter("prefix", "STRING", f"{termo.lower()}%"))
    sql = f"""
    SELECT cnpj_raiz, razao_social
    FROM {t_hab}
    WHERE {' AND '.join(conds)}
    ORDER BY
      CASE
        WHEN LOWER(CAST(razao_social AS STRING)) = @raw THEN 0
        WHEN LOWER(CAST(razao_social AS STRING)) LIKE @prefix THEN 1
        ELSE 2
      END,
      LENGTH(CAST(razao_social AS STRING))
    LIMIT 5
    """
    try:
        rows = run_query(client, sql, params)
    except Exception as exc:
        logger.warning(f"resolve_cnpjs_empresa_base erro: {exc}")
        return []
    # melhor correspondência (uma empresa)
    if rows and rows[0].get("cnpj_raiz"):
        return [str(rows[0].get("cnpj_raiz")) + "000000"]
    return []


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


_DEFAULT_ESTIMADO = "liquid-receiver-483923-n6.Projeto_Comex.empresas_comex_estimado"
_DEFAULT_IMPORT_UF = "liquid-receiver-483923-n6.Projeto_Comex.importacao_uf_ncm"
_DEFAULT_EXPORT_UF = "liquid-receiver-483923-n6.Projeto_Comex.exportacao_uf_ncm"


def fetch_estimativa_empresa(client, run_query, bt, table_env, cnpjs: List[str]) -> Optional[Dict]:
    """Lê a estimativa de comex por empresa da tabela materializada
    empresas_comex_estimado (ponderada por porte). Casa por raiz (8 díg.).
    Retorna {total_imp, total_exp, por_uf:[{uf,imp,exp}], ano_ini, ano_fim} ou None."""
    if not cnpjs:
        return None
    from google.cloud import bigquery

    raizes = sorted({c[:8] for c in cnpjs if len(c) >= 8})
    if not raizes:
        return None
    t = bt(table_env("COMEX_BQ_TABLE_ESTIMADO", _DEFAULT_ESTIMADO))
    sql = f"""
    SELECT uf, SUM(imp_estimado) imp, SUM(exp_estimado) exp,
           ANY_VALUE(ano_ini) ano_ini, ANY_VALUE(ano_fim) ano_fim
    FROM {t} WHERE cnpj_raiz IN UNNEST(@raizes)
    GROUP BY uf ORDER BY (SUM(imp_estimado)+SUM(exp_estimado)) DESC
    """
    try:
        rows = run_query(client, sql, [bigquery.ArrayQueryParameter("raizes", "STRING", raizes)])
    except Exception as exc:
        logger.warning(f"fetch_estimativa_empresa erro: {exc}")
        return None
    if not rows:
        return None
    por_uf = [
        {"uf": r.get("uf"), "imp": float(r.get("imp") or 0), "exp": float(r.get("exp") or 0)}
        for r in rows if r.get("uf")
    ]
    total_imp = sum(u["imp"] for u in por_uf)
    total_exp = sum(u["exp"] for u in por_uf)
    if (total_imp + total_exp) <= 0:
        return None
    return {
        "total_imp": total_imp,
        "total_exp": total_exp,
        "por_uf": por_uf,
        "ano_ini": int(rows[0].get("ano_ini") or 0),
        "ano_fim": int(rows[0].get("ano_fim") or 0),
    }


_DEFAULT_ESTIMADO_TBL = "liquid-receiver-483923-n6.Projeto_Comex.empresas_comex_estimado"

# Orientação de comércio por SETOR CNAE (heurística): distribuidores/varejo são
# majoritariamente importadores; setor primário (mineração/agro) é exportador.
_ORIENTACAO_SETOR = {
    "PRIMÁRIO": (0.6, 1.25),
    "INDÚSTRIA": (1.0, 1.0),
    "DISTRIBUIDOR": (1.3, 0.35),
    "VAREJO": (1.3, 0.25),
    "SERVIÇOS": (1.1, 0.5),
}


def fatores_orientacao(setor: Optional[str]) -> tuple:
    """Retorna (fator_imp, fator_exp) conforme o setor CNAE."""
    return _ORIENTACAO_SETOR.get((setor or "").strip().upper(), (1.0, 1.0))


def stats_estimativa_periodo(
    client, run_query, bt, table_env, cnpjs: List[str],
    ym_start: int, ym_end: int, fator_imp: float = 1.0, fator_exp: float = 1.0,
) -> Optional[Dict]:
    """Estimativa período-consciente: valores da empresa = participação estrutural
    (share_uf) × mercado REAL da UF mês a mês, no período selecionado, com
    orientação de comércio por setor. Preserva sazonalidade e variação anual.

    Retorna {total_imp, total_exp, por_uf, valores_por_mes, valores_imp_por_mes,
    valores_exp_por_mes, registros_por_mes, ano_ini, ano_fim} ou None."""
    if not cnpjs:
        return None
    from google.cloud import bigquery
    raizes = sorted({c[:8] for c in cnpjs if len(c) >= 8})
    if not raizes:
        return None
    t_est = bt(table_env("COMEX_BQ_TABLE_ESTIMADO", _DEFAULT_ESTIMADO_TBL))
    t_imp = bt(table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = bt(table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))

    # 1) participação (share_uf) da empresa por UF
    sql_share = f"""
    SELECT uf, SUM(share_uf) AS share_uf, ANY_VALUE(ano_ini) ano_ini, ANY_VALUE(ano_fim) ano_fim
    FROM {t_est} WHERE cnpj_raiz IN UNNEST(@raizes) GROUP BY uf
    """
    try:
        shares_rows = run_query(client, sql_share, [bigquery.ArrayQueryParameter("raizes", "STRING", raizes)])
    except Exception as exc:
        logger.warning(f"stats_estimativa_periodo share erro: {exc}")
        return None
    shares = {r.get("uf"): float(r.get("share_uf") or 0) for r in shares_rows if r.get("uf")}
    if not shares:
        return None
    ano_ini = int(shares_rows[0].get("ano_ini") or 0)
    ano_fim = int(shares_rows[0].get("ano_fim") or 0)
    ufs = list(shares.keys())

    # 2) mercado real da UF mês a mês no período selecionado
    params = [
        bigquery.ScalarQueryParameter("a", "INT64", ym_start),
        bigquery.ScalarQueryParameter("b", "INT64", ym_end),
        bigquery.ArrayQueryParameter("ufs", "STRING", ufs),
    ]
    sql_mes = f"""
    WITH imp AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, ano, mes,
             SUM(CAST(total_importacao_fob AS FLOAT64)) v
      FROM {t_imp} WHERE (ano*100+mes) BETWEEN @a AND @b
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
      GROUP BY uf, ano, mes
    ),
    exp AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, ano, mes,
             SUM(CAST(total_exportacao_fob AS FLOAT64)) v
      FROM {t_exp} WHERE (ano*100+mes) BETWEEN @a AND @b
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
      GROUP BY uf, ano, mes
    )
    SELECT COALESCE(imp.uf, exp.uf) uf,
           COALESCE(imp.ano, exp.ano) ano, COALESCE(imp.mes, exp.mes) mes,
           COALESCE(imp.v,0) imp, COALESCE(exp.v,0) exp
    FROM imp FULL OUTER JOIN exp
      ON imp.uf=exp.uf AND imp.ano=exp.ano AND imp.mes=exp.mes
    """
    try:
        mes_rows = run_query(client, sql_mes, params)
    except Exception as exc:
        logger.warning(f"stats_estimativa_periodo mes erro: {exc}")
        return None

    valores_imp: Dict[str, float] = {}
    valores_exp: Dict[str, float] = {}
    por_uf: Dict[str, Dict[str, float]] = {}
    for r in mes_rows:
        uf = r.get("uf")
        sh = shares.get(uf, 0.0)
        if sh <= 0:
            continue
        ym = f"{int(r.get('ano') or 0):04d}-{int(r.get('mes') or 0):02d}"
        vi = float(r.get("imp") or 0) * sh * fator_imp
        ve = float(r.get("exp") or 0) * sh * fator_exp
        valores_imp[ym] = valores_imp.get(ym, 0.0) + vi
        valores_exp[ym] = valores_exp.get(ym, 0.0) + ve
        d = por_uf.setdefault(uf, {"imp": 0.0, "exp": 0.0})
        d["imp"] += vi
        d["exp"] += ve

    if not valores_imp and not valores_exp:
        return None
    todos_ym = sorted(set(valores_imp) | set(valores_exp))
    valores_por_mes = {ym: valores_imp.get(ym, 0.0) + valores_exp.get(ym, 0.0) for ym in todos_ym}
    registros_por_mes = {ym: (1 if valores_por_mes[ym] > 0 else 0) for ym in todos_ym}
    total_imp = sum(valores_imp.values())
    total_exp = sum(valores_exp.values())
    por_uf_list = sorted(
        [{"uf": k, "imp": v["imp"], "exp": v["exp"]} for k, v in por_uf.items()],
        key=lambda x: -(x["imp"] + x["exp"]),
    )
    return {
        "total_imp": total_imp,
        "total_exp": total_exp,
        "por_uf": por_uf_list,
        "valores_por_mes": {ym: valores_por_mes[ym] for ym in todos_ym},
        "valores_imp_por_mes": {ym: valores_imp.get(ym, 0.0) for ym in todos_ym},
        "valores_exp_por_mes": {ym: valores_exp.get(ym, 0.0) for ym in todos_ym},
        "registros_por_mes": registros_por_mes,
        "ano_ini": ano_ini,
        "ano_fim": ano_fim,
    }


def fetch_top_ncms_ufs(client, run_query, bt, table_env, ufs: List[str],
                       ano_ini: int, ano_fim: int, limit: int = 12) -> List[Dict]:
    """Top NCMs movimentados nas UFs da empresa (dados reais UF×NCM)."""
    if not ufs:
        return []
    from google.cloud import bigquery

    t_imp = bt(table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = bt(table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    sql = f"""
    WITH facts AS (
      SELECT CAST(id_ncm AS STRING) ncm, COALESCE(CAST(total_importacao_fob AS FLOAT64),0) v
      FROM {t_imp} WHERE ano BETWEEN @a0 AND @a1
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
      UNION ALL
      SELECT CAST(id_ncm AS STRING), COALESCE(CAST(total_exportacao_fob AS FLOAT64),0)
      FROM {t_exp} WHERE ano BETWEEN @a0 AND @a1
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
    )
    SELECT ncm, SUM(v) v_total FROM facts GROUP BY ncm ORDER BY v_total DESC LIMIT {int(limit)}
    """
    params = [
        bigquery.ArrayQueryParameter("ufs", "STRING", [u.upper() for u in ufs]),
        bigquery.ScalarQueryParameter("a0", "INT64", ano_ini or 2020),
        bigquery.ScalarQueryParameter("a1", "INT64", ano_fim or 2021),
    ]
    try:
        rows = run_query(client, sql, params)
        return [
            {"ncm": str(r.get("ncm") or ""), "descricao": "", "valor_total": float(r.get("v_total") or 0), "total_operacoes": 0}
            for r in rows if r.get("ncm")
        ]
    except Exception as exc:
        logger.warning(f"fetch_top_ncms_ufs erro: {exc}")
        return []


def _meses_no_intervalo(ym_start: int, ym_end: int) -> List[str]:
    """Lista de chaves 'YYYY-MM' entre ym_start e ym_end (YYYYMM)."""
    out: List[str] = []
    y, m = ym_start // 100, ym_start % 100
    ey, em = ym_end // 100, ym_end % 100
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
        if len(out) > 600:
            break
    return out


def fetch_serie_mensal_estimada(
    client, run_query, bt, table_env, ufs: List[str],
    ym_start: int, ym_end: int, total_imp: float, total_exp: float,
) -> tuple:
    """Distribui o total estimado (imp/exp) pelos meses do período seguindo a
    sazonalidade real das UFs da empresa.
    Retorna (valores_por_mes, registros_por_mes, valores_imp_por_mes, valores_exp_por_mes)."""
    meses = _meses_no_intervalo(ym_start, ym_end)
    if not meses:
        return {}, {}, {}, {}
    valores_por_mes: Dict[str, float] = {}
    registros_por_mes: Dict[str, int] = {}
    valores_imp_por_mes: Dict[str, float] = {}
    valores_exp_por_mes: Dict[str, float] = {}

    forma_imp: Dict[str, float] = {}
    forma_exp: Dict[str, float] = {}
    if ufs:
        from google.cloud import bigquery
        t_imp = bt(table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
        t_exp = bt(table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
        sql = f"""
        WITH facts AS (
          SELECT ano, mes, COALESCE(CAST(total_importacao_fob AS FLOAT64),0) imp, 0.0 exp
          FROM {t_imp}
          WHERE (ano*100+mes) BETWEEN @a AND @b
            AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
          UNION ALL
          SELECT ano, mes, 0.0, COALESCE(CAST(total_exportacao_fob AS FLOAT64),0)
          FROM {t_exp}
          WHERE (ano*100+mes) BETWEEN @a AND @b
            AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN UNNEST(@ufs)
        )
        SELECT FORMAT('%04d-%02d', ano, mes) ym, SUM(imp) imp, SUM(exp) exp
        FROM facts GROUP BY ano, mes
        """
        params = [
            bigquery.ScalarQueryParameter("a", "INT64", ym_start),
            bigquery.ScalarQueryParameter("b", "INT64", ym_end),
            bigquery.ArrayQueryParameter("ufs", "STRING", [u.upper() for u in ufs if u]),
        ]
        try:
            for r in run_query(client, sql, params):
                ym = str(r.get("ym") or "")
                if ym:
                    forma_imp[ym] = float(r.get("imp") or 0)
                    forma_exp[ym] = float(r.get("exp") or 0)
        except Exception as exc:
            logger.warning(f"fetch_serie_mensal_estimada erro: {exc}")

    soma_imp = sum(forma_imp.values())
    soma_exp = sum(forma_exp.values())
    n = len(meses)
    for ym in meses:
        if soma_imp > 0:
            vi = total_imp * forma_imp.get(ym, 0.0) / soma_imp
        else:
            vi = total_imp / n  # fallback: distribuição uniforme
        if soma_exp > 0:
            ve = total_exp * forma_exp.get(ym, 0.0) / soma_exp
        else:
            ve = total_exp / n
        valores_por_mes[ym] = vi + ve
        valores_imp_por_mes[ym] = vi
        valores_exp_por_mes[ym] = ve
        registros_por_mes[ym] = 1 if (vi + ve) > 0 else 0
    return valores_por_mes, registros_por_mes, valores_imp_por_mes, valores_exp_por_mes


def stats_payload_empresa_estimado(
    fonte_dados: Dict[str, str],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
    estimativa: Dict,
    cnpjs: Optional[List[str]] = None,
    principais_ncms: Optional[List[Dict]] = None,
    valores_por_mes: Optional[Dict[str, float]] = None,
    registros_por_mes: Optional[Dict[str, int]] = None,
    valores_imp_por_mes: Optional[Dict[str, float]] = None,
    valores_exp_por_mes: Optional[Dict[str, float]] = None,
) -> Dict:
    """Payload do dashboard com valores ESTIMADOS por empresa (participação × mercado real da UF)."""
    nome = (empresa_importadora or empresa_exportadora or "empresa").strip()
    total_imp = float(estimativa.get("total_imp") or 0)
    total_exp = float(estimativa.get("total_exp") or 0)
    periodo = f"{estimativa.get('ano_ini')}-{estimativa.get('ano_fim')}"
    aviso = (
        f"Valores ESTIMADOS para «{nome}». Não há registro real de comércio exterior por CNPJ "
        "na base. A estimativa aplica a participação estrutural da empresa em cada UF "
        f"(ponderada por porte, base {periodo}) sobre o mercado REAL da UF mês a mês — "
        "preservando a sazonalidade e a variação ao longo do período selecionado — com "
        "orientação de comércio por setor (importador/exportador). Use como ordem de grandeza."
    )
    principais_paises = [
        {"pais": f"UF: {u.get('uf')}", "valor_total": float(u.get("imp") or 0) + float(u.get("exp") or 0), "total_operacoes": 0}
        for u in (estimativa.get("por_uf") or [])
    ]

    # Escala os NCMs (valores de mercado da UF) para a participação estimada da
    # empresa, para ficarem na mesma ordem de grandeza dos KPIs.
    ncms_in = principais_ncms or []
    soma_ncm = sum(float(n.get("valor_total") or 0) for n in ncms_in)
    total_emp = total_imp + total_exp
    if ncms_in and soma_ncm > 0 and total_emp > 0:
        principais_ncms = [
            {
                "ncm": n.get("ncm"),
                "descricao": n.get("descricao") or "",
                "valor_total": total_emp * float(n.get("valor_total") or 0) / soma_ncm,
                "total_operacoes": 0,
            }
            for n in ncms_in
        ]
    else:
        principais_ncms = ncms_in
    return {
        "volume_importacoes": 0.0,
        "volume_exportacoes": 0.0,
        "volume_disponivel": False,
        "valor_total_usd": total_imp + total_exp,
        "valor_total_importacoes": total_imp,
        "valor_total_exportacoes": total_exp,
        "quantidade_estatistica_importacoes": 0.0,
        "quantidade_estatistica_exportacoes": 0.0,
        "quantidade_estatistica_total": 0.0,
        "principais_ncms": principais_ncms or [],
        "principais_paises": principais_paises,
        "principais_importadores": [],
        "principais_exportadores": [],
        "registros_por_mes": registros_por_mes or {},
        "valores_por_mes": valores_por_mes or {},
        "valores_imp_por_mes": valores_imp_por_mes or {},
        "valores_exp_por_mes": valores_exp_por_mes or {},
        "pesos_por_mes": {},
        "filtro_empresa_aplicado": True,
        "ufs_filtradas_por_empresa": [u.get("uf") for u in (estimativa.get("por_uf") or [])],
        "dados_empresa_reais": False,
        "kpis_empresa_indisponiveis": False,
        "fonte_valores": "estimado",
        "periodo_estimativa": periodo,
        "cnpjs_resolvidos": cnpjs or [],
        "aviso_dados_sem_empresa": aviso,
        "fonte_dados": fonte_dados,
    }


def stats_real_import_logcomex(
    client, run_query, bt, table_env, cnpjs, nome_empresa, ym_start, ym_end,
    lado: str = "importador"
) -> Optional[Dict]:
    """Valores REAIS (Logcomex, deduplicado) para a empresa/período.

    lado="importador": empresa brasileira compradora. Casa por cnpj_raiz OU por
      tokens do nome do importador. Valores vão para IMPORTAÇÃO.
    lado="exportador": empresa ESTRANGEIRA fornecedora. Casa por tokens do nome do
      exportador. Os embarques dela para o Brasil são tratados como EXPORTAÇÃO
      (visão da empresa estrangeira). Retorna None se não houver registro real.
    """
    from google.cloud import bigquery

    t_real = bt(table_env("COMEX_BQ_TABLE_REAL_LOGCOMEX", _DEFAULT_REAL_LOGCOMEX))
    y0, m0 = ym_start // 100, ym_start % 100
    y1, m1 = ym_end // 100, ym_end % 100
    params = [
        bigquery.ScalarQueryParameter("y0", "INT64", y0),
        bigquery.ScalarQueryParameter("m0", "INT64", m0),
        bigquery.ScalarQueryParameter("y1", "INT64", y1),
        bigquery.ScalarQueryParameter("m1", "INT64", m1),
    ]
    conds = ["(ano*100 + mes) BETWEEN (@y0*100 + @m0) AND (@y1*100 + @m1)"]

    is_exp = (lado == "exportador")
    campo_nome = "exportador_nome" if is_exp else "importador_nome"
    # coluna de contraparte para o ranking "principais_*"
    contraparte = "importador_nome" if is_exp else "exportador_nome"

    ors = []
    if not is_exp:
        raizes = sorted({str(c)[:8] for c in (cnpjs or []) if c})
        if raizes:
            params.append(bigquery.ArrayQueryParameter("raizes", "STRING", raizes))
            ors.append("cnpj_raiz IN UNNEST(@raizes)")
    toks = _tokens_nome(nome_empresa)
    if toks:
        tok_conds = []
        for i, tk in enumerate(toks):
            params.append(bigquery.ScalarQueryParameter(f"tk{i}", "STRING", f"%{tk}%"))
            tok_conds.append(f"LOWER({campo_nome}) LIKE @tk{i}")
        ors.append("(" + " AND ".join(tok_conds) + ")")
    if not ors:
        return None
    conds.append("(" + " OR ".join(ors) + ")")
    where = " AND ".join(conds)

    base_sql = f"FROM {t_real} WHERE {where}"
    tot = list(run_query(client,
        f"SELECT SUM(fob_import) t, SUM(qtd_estatistica) q, SUM(peso_liquido) p, "
        f"SUM(n_operacoes) n {base_sql}", params))
    if not tot or not tot[0].get("t"):
        return None
    total = float(tot[0].get("t") or 0)
    if total <= 0:
        return None

    por_mes = {}
    reg_mes = {}
    for row in run_query(client,
        f"SELECT FORMAT('%04d-%02d', ano, mes) ym, SUM(fob_import) v, SUM(n_operacoes) n "
        f"{base_sql} GROUP BY ym ORDER BY ym", params):
        por_mes[row["ym"]] = float(row.get("v") or 0)
        reg_mes[row["ym"]] = int(row.get("n") or 0)

    vkey = "exp" if is_exp else "imp"
    por_uf = []
    for row in run_query(client,
        f"SELECT sigla_uf uf, SUM(fob_import) v {base_sql} GROUP BY uf ORDER BY v DESC", params):
        por_uf.append({"uf": row.get("uf"),
                       "imp": 0.0 if is_exp else float(row.get("v") or 0),
                       "exp": float(row.get("v") or 0) if is_exp else 0.0})

    por_ncm = []
    for row in run_query(client,
        f"SELECT id_ncm ncm, SUM(fob_import) v, SUM(n_operacoes) n {base_sql} "
        f"GROUP BY ncm ORDER BY v DESC LIMIT 15", params):
        por_ncm.append({"ncm": row.get("ncm"), "descricao": "",
                        "valor_total": float(row.get("v") or 0),
                        "total_operacoes": int(row.get("n") or 0)})

    por_pais = []
    for row in run_query(client,
        f"SELECT pais_origem pais, SUM(fob_import) v, SUM(n_operacoes) n {base_sql} "
        f"GROUP BY pais ORDER BY v DESC LIMIT 15", params):
        por_pais.append({"pais": row.get("pais") or "—",
                         "valor_total": float(row.get("v") or 0),
                         "total_operacoes": int(row.get("n") or 0)})

    # Contrapartes (importadores brasileiros que compraram do exportador, ou
    # fornecedores estrangeiros do importador).
    contrapartes = []
    for row in run_query(client,
        f"SELECT {contraparte} nome, SUM(fob_import) v, SUM(n_operacoes) n {base_sql} "
        f"GROUP BY nome ORDER BY v DESC LIMIT 15", params):
        contrapartes.append({"nome": row.get("nome") or "—",
                             "valor_total": float(row.get("v") or 0),
                             "total_operacoes": int(row.get("n") or 0)})

    return {
        "total_imp": 0.0 if is_exp else total,
        "total_exp": total if is_exp else 0.0,
        "lado": lado,
        "qtd_estatistica": float(tot[0].get("q") or 0),
        "peso_liquido": float(tot[0].get("p") or 0),
        "n_operacoes": int(tot[0].get("n") or 0),
        "valores_imp_por_mes": {} if is_exp else por_mes,
        "valores_exp_por_mes": por_mes if is_exp else {},
        "registros_por_mes": reg_mes,
        "por_uf": por_uf,
        "principais_ncms": por_ncm,
        "principais_paises": por_pais,
        "principais_importadores": contrapartes if is_exp else [],
        "principais_exportadores": [] if is_exp else contrapartes,
    }


def detalhe_real_logcomex(
    client, run_query, bt, table_env, cnpjs, nome_empresa, ym_start, ym_end,
    lado: str = "importador", page: int = 1, page_size: int = 10
):
    """Linhas detalhadas REAIS (Logcomex) para a tabela do dashboard.

    Retorna (results, total). Cada linha traz importador, exportador, NCM, país,
    UF e FOB reais — agregado por (importador, exportador, ncm, uf, país, mês).
    """
    from google.cloud import bigquery

    t_real = bt(table_env("COMEX_BQ_TABLE_REAL_LOGCOMEX", _DEFAULT_REAL_LOGCOMEX))
    y0, m0 = ym_start // 100, ym_start % 100
    y1, m1 = ym_end // 100, ym_end % 100
    params = [
        bigquery.ScalarQueryParameter("y0", "INT64", y0),
        bigquery.ScalarQueryParameter("m0", "INT64", m0),
        bigquery.ScalarQueryParameter("y1", "INT64", y1),
        bigquery.ScalarQueryParameter("m1", "INT64", m1),
    ]
    conds = ["(ano*100 + mes) BETWEEN (@y0*100 + @m0) AND (@y1*100 + @m1)"]
    is_exp = (lado == "exportador")
    campo_nome = "exportador_nome" if is_exp else "importador_nome"

    ors = []
    if not is_exp:
        raizes = sorted({str(c)[:8] for c in (cnpjs or []) if c})
        if raizes:
            params.append(bigquery.ArrayQueryParameter("raizes", "STRING", raizes))
            ors.append("cnpj_raiz IN UNNEST(@raizes)")
    toks = _tokens_nome(nome_empresa)
    if toks:
        tok_conds = []
        for i, tk in enumerate(toks):
            params.append(bigquery.ScalarQueryParameter(f"tk{i}", "STRING", f"%{tk}%"))
            tok_conds.append(f"LOWER({campo_nome}) LIKE @tk{i}")
        ors.append("(" + " AND ".join(tok_conds) + ")")
    if not ors:
        return [], 0
    conds.append("(" + " OR ".join(ors) + ")")
    where = " AND ".join(conds)
    base_sql = f"FROM {t_real} WHERE {where}"

    tot = list(run_query(client, f"SELECT COUNT(*) c FROM (SELECT 1 {base_sql} "
        "GROUP BY importador_nome, exportador_nome, id_ncm, sigla_uf, pais_origem, ano, mes)", params))
    total = int(tot[0].get("c") or 0) if tot else 0
    if total <= 0:
        return [], 0

    offset = (page - 1) * page_size
    params_pg = list(params) + [
        bigquery.ScalarQueryParameter("lim", "INT64", page_size),
        bigquery.ScalarQueryParameter("off", "INT64", offset),
    ]
    rows = run_query(client,
        f"SELECT importador_nome, exportador_nome, id_ncm, sigla_uf, pais_origem, "
        f"ano, mes, SUM(fob_import) fob, SUM(peso_liquido) peso "
        f"{base_sql} GROUP BY importador_nome, exportador_nome, id_ncm, sigla_uf, "
        f"pais_origem, ano, mes ORDER BY fob DESC LIMIT @lim OFFSET @off", params_pg)

    results = []
    for i, r in enumerate(rows):
        ncm_s = re.sub(r"\D", "", str(r.get("id_ncm") or ""))[:8]
        ano, mes = int(r.get("ano") or 0), int(r.get("mes") or 0)
        results.append({
            "id": f"real-{i}-{ncm_s}-{ano}{mes}",
            "ncm": ncm_s,
            "descricao_produto": "—",
            "tipo_operacao": "Exportação" if is_exp else "Importação",
            "razao_social_importador": str(r.get("importador_nome") or "").strip(),
            "razao_social_exportador": str(r.get("exportador_nome") or "").strip(),
            "pais_origem_destino": str(r.get("pais_origem") or "—").strip() or "—",
            "uf": str(r.get("sigla_uf") or "").strip(),
            "valor_fob": float(r.get("fob") or 0),
            "peso_liquido_kg": float(r.get("peso") or 0),
            "data_operacao": f"{ano:04d}-{mes:02d}-01" if ano and mes else "",
        })
    return results, total


def stats_payload_empresa_real(
    fonte_dados: Dict[str, str],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
    real: Dict,
    cnpjs: Optional[List[str]] = None,
) -> Dict:
    """Payload do dashboard com valores REAIS (base Logcomex)."""
    nome = (empresa_importadora or empresa_exportadora or "empresa").strip()
    total_imp = float(real.get("total_imp") or 0)
    total_exp = float(real.get("total_exp") or 0)
    is_exp = (real.get("lado") == "exportador")
    if is_exp:
        aviso = (
            f"Valores REAIS dos embarques de «{nome}» para o Brasil, apurados de registros "
            "aduaneiros (Logcomex), deduplicados. «{nome}» é fornecedor estrangeiro — seus "
            "embarques ao Brasil são exibidos como EXPORTAÇÃO (visão da empresa). Abaixo, os "
            "importadores brasileiros que compraram dela.".replace("{nome}", nome)
        )
    else:
        aviso = (
            f"Valores REAIS de importação para «{nome}», apurados a partir de registros "
            "aduaneiros (Logcomex), deduplicados. Exportação não consta nesta base (é dado "
            "de importação brasileira). Fornecedores estrangeiros aparecem como exportadores "
            "das operações, não na base de exportação do Brasil."
        )
    return {
        "volume_importacoes": 0.0 if is_exp else float(real.get("peso_liquido") or 0),
        "volume_exportacoes": float(real.get("peso_liquido") or 0) if is_exp else 0.0,
        "volume_disponivel": True,
        "valor_total_usd": total_imp + total_exp,
        "valor_total_importacoes": total_imp,
        "valor_total_exportacoes": total_exp,
        "quantidade_estatistica_importacoes": 0.0 if is_exp else float(real.get("qtd_estatistica") or 0),
        "quantidade_estatistica_exportacoes": float(real.get("qtd_estatistica") or 0) if is_exp else 0.0,
        "quantidade_estatistica_total": float(real.get("qtd_estatistica") or 0),
        "principais_ncms": real.get("principais_ncms") or [],
        "principais_paises": real.get("principais_paises") or [],
        "principais_importadores": real.get("principais_importadores") or [],
        "principais_exportadores": real.get("principais_exportadores") or [],
        "registros_por_mes": real.get("registros_por_mes") or {},
        "valores_por_mes": (real.get("valores_exp_por_mes") if is_exp else real.get("valores_imp_por_mes")) or {},
        "valores_imp_por_mes": real.get("valores_imp_por_mes") or {},
        "valores_exp_por_mes": real.get("valores_exp_por_mes") or {},
        "pesos_por_mes": {},
        "filtro_empresa_aplicado": True,
        "ufs_filtradas_por_empresa": [u.get("uf") for u in (real.get("por_uf") or [])],
        "dados_empresa_reais": True,
        "kpis_empresa_indisponiveis": False,
        "fonte_valores": "real_logcomex",
        "cnpjs_resolvidos": cnpjs or [],
        "aviso_dados_sem_empresa": aviso,
        "fonte_dados": {**fonte_dados, "nome_logico": "comex_real_import_logcomex"},
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


def resolve_cnae_empresa(
    client, run_query, bt, table_env, cnpjs: List[str]
) -> tuple:
    """Retorna (cnae, uf) da empresa para uso em sugestão estatística."""
    if not cnpjs:
        return None, None
    from google.cloud import bigquery

    _DEFAULT_ESTAB = "liquid-receiver-483923-n6.Projeto_Comex.Estabelecimentos_Ativos_UltimoMes"
    t_estab = bt(table_env("COMEX_BQ_TABLE_ESTAB", _DEFAULT_ESTAB))
    cnpj_raiz = cnpjs[0][:8]
    sql = f"""
    SELECT
        CAST(cnae_fiscal_principal AS STRING) AS cnae,
        UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf
    FROM {t_estab}
    WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 8) = @cnpj_raiz
    LIMIT 1
    """
    try:
        rows = run_query(client, sql, [bigquery.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz)])
        if rows:
            return str(rows[0].get("cnae") or "").strip() or None, str(rows[0].get("uf") or "").strip() or None
    except Exception as exc:
        logger.warning(f"resolve_cnae_empresa erro: {exc}")
    return None, None


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
