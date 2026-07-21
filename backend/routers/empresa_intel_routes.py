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


_TBL_HABILITACAO = "liquid-receiver-483923-n6.Projeto_Comex.empresas_habilitacao"
_TBL_EMPRESAS_RAZAO = "liquid-receiver-483923-n6.Projeto_Comex.empresas_razao"
_STOP_TOKENS = {
    "ltda", "ltda.", "sa", "s.a", "s.a.", "s/a", "me", "mei", "epp", "eireli",
    "cia", "cia.", "e", "de", "do", "da", "dos", "das", "em", "&", "-", "ind", "com",
}


def _deaccent(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _tokens_busca(q: str) -> list:
    import re
    raw = re.findall(r"[0-9a-zà-ÿ]+", (q or "").lower())
    out = []
    for t in raw:
        td = _deaccent(t)
        if len(td) >= 2 and td not in _STOP_TOKENS:
            out.append(td)
    return out


def _norm_sql(col: str) -> str:
    """Expressão SQL: minúsculo + sem acentos."""
    return f"REGEXP_REPLACE(NORMALIZE(LOWER(CAST({col} AS STRING)), NFD), r'\\pM', '')"


def _regex_token(tk: str) -> str:
    """Regex RE2 para casar o token como palavra inteira."""
    import re as _re
    return f"(^|[^0-9a-z]){_re.escape(tk)}([^0-9a-z]|$)"


def _buscar_empresas_geral(client, q_clean, prefixos, uf, limit):
    """Busca empresas por nome/CNPJ em DUAS fontes e mescla por raiz:
    1) empresas_habilitacao (razão social — empresas de comex)
    2) Estabelecimentos RF (nome fantasia — base completa)
    Casamento por palavra inteira (regex). Marca tem_comex."""
    from google.cloud import bigquery
    toks = _tokens_busca(q_clean)
    digitos = "".join(c for c in q_clean if c.isdigit())
    if not toks and len(digitos) < 4:
        return None
    t_estab = _bt(_env("COMEX_BQ_TABLE_ESTAB", _DEFAULT_ESTAB))
    t_hab = _bt(_env("COMEX_BQ_TABLE_HABILITACAO", _TBL_HABILITACAO))
    t_razao = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_RAZAO", _TBL_EMPRESAS_RAZAO))
    cnpj_pref = digitos[:8] if len(digitos) >= 4 else None

    def _tok_params(prefix):
        ps = []
        for i, tk in enumerate(toks):
            ps.append(bigquery.ScalarQueryParameter(f"{prefix}{i}", "STRING", _regex_token(tk)))
        return ps

    def _tok_conds(col, prefix):
        return [f"REGEXP_CONTAINS({_norm_sql(col)}, @{prefix}{i})" for i in range(len(toks))]

    # ── Query 1: base de comex por razão social ──
    def q_comex():
        p = []
        cond_or = []
        if toks:
            cond_or.append("(" + " AND ".join(_tok_conds("razao_social", "rc")) + ")")
            p += _tok_params("rc")
        if cnpj_pref:
            cond_or.append("cnpj_raiz LIKE @qc")
            p.append(bigquery.ScalarQueryParameter("qc", "STRING", f"{cnpj_pref}%"))
        w = ["(" + " OR ".join(cond_or) + ")"]
        if uf:
            w.append("UPPER(TRIM(CAST(uf AS STRING))) = @ufc")
            p.append(bigquery.ScalarQueryParameter("ufc", "STRING", uf.upper()))
        if prefixos:
            w.append("SUBSTR(REGEXP_REPLACE(CAST(cnae AS STRING), r'[^0-9]',''),1,4) IN UNNEST(@pc)")
            p.append(bigquery.ArrayQueryParameter("pc", "STRING", prefixos))
        sql = f"""
        SELECT cnpj_raiz AS raiz, razao_social, CAST(NULL AS STRING) nome_fantasia,
               uf, cnae, anos_ativos, primeiro_ano, ultimo_ano, TRUE AS tem_comex
        FROM {t_hab} WHERE {' AND '.join(w)}
        ORDER BY anos_ativos DESC, ultimo_ano DESC LIMIT {int(limit)}
        """
        return _run_query(client, sql, p)

    # ── Query 2: base completa de Estabelecimentos por nome fantasia ──
    def q_estab():
        p = []
        cond_or = []
        if toks:
            cond_or.append("(" + " AND ".join(_tok_conds("nome_fantasia", "rf")) + ")")
            p += _tok_params("rf")
        if cnpj_pref:
            cond_or.append("SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) LIKE @qe")
            p.append(bigquery.ScalarQueryParameter("qe", "STRING", f"{cnpj_pref}%"))
        w = ["(" + " OR ".join(cond_or) + ")"]
        if uf:
            w.append("UPPER(TRIM(CAST(sigla_uf AS STRING))) = @ufe")
            p.append(bigquery.ScalarQueryParameter("ufe", "STRING", uf.upper()))
        if prefixos:
            w.append("SUBSTR(REGEXP_REPLACE(CAST(cnae_fiscal_principal AS STRING), r'[^0-9]',''),1,4) IN UNNEST(@pe)")
            p.append(bigquery.ArrayQueryParameter("pe", "STRING", prefixos))
        sql = f"""
        WITH filtrado AS (
          SELECT SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) AS raiz,
                 CAST(nome_fantasia AS STRING) AS nome_fantasia,
                 UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
                 CAST(cnae_fiscal_principal AS STRING) AS cnae
          FROM {t_estab} WHERE {' AND '.join(w)}
        ),
        e AS (SELECT raiz, ANY_VALUE(nome_fantasia) nome_fantasia, ANY_VALUE(uf) uf, ANY_VALUE(cnae) cnae
              FROM filtrado GROUP BY raiz LIMIT {int(limit) * 3})
        SELECT e.raiz,
               COALESCE(h.razao_social, er.razao_social) AS razao_social,
               e.nome_fantasia, e.uf, e.cnae,
               h.anos_ativos, h.primeiro_ano, h.ultimo_ano,
               (h.cnpj_raiz IS NOT NULL) AS tem_comex
        FROM e
        LEFT JOIN {t_hab} h ON h.cnpj_raiz = e.raiz
        LEFT JOIN {t_razao} er ON er.cnpj_raiz = e.raiz
        LIMIT {int(limit)}
        """
        return _run_query(client, sql, p)

    res = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = {pool.submit(q_comex): "c", pool.submit(q_estab): "e"}
        for fut in as_completed(futs):
            try:
                res[futs[fut]] = fut.result()
            except Exception as exc:
                logger.warning(f"busca_geral {futs[fut]} erro: {exc}")
                res[futs[fut]] = []

    # Mesclar por raiz — preferir entrada com razão social (comex)
    por_raiz: Dict[str, dict] = {}
    for r in (res.get("c") or []):
        por_raiz[r.get("raiz")] = dict(r)
    for r in (res.get("e") or []):
        raiz = r.get("raiz")
        if raiz in por_raiz:
            if not por_raiz[raiz].get("nome_fantasia"):
                por_raiz[raiz]["nome_fantasia"] = r.get("nome_fantasia")
        else:
            por_raiz[raiz] = dict(r)
    merged = sorted(por_raiz.values(),
                    key=lambda r: (not r.get("tem_comex"), -(r.get("anos_ativos") or 0)))
    return merged[:int(limit)]


def _listar_empresas_cnae(client, prefixos, uf, limit):
    """Lista TODAS as empresas (base RF completa) de um conjunto de prefixos CNAE,
    com flag de comex via LEFT JOIN empresas_habilitacao. Retorna (lista, total, resumo_uf)."""
    from google.cloud import bigquery
    if not prefixos:
        return [], 0, []
    t_estab = _bt(_env("COMEX_BQ_TABLE_ESTAB", _DEFAULT_ESTAB))
    t_hab = _bt(_env("COMEX_BQ_TABLE_HABILITACAO", _TBL_HABILITACAO))
    t_razao = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_RAZAO", _TBL_EMPRESAS_RAZAO))
    where = ["SUBSTR(REGEXP_REPLACE(CAST(cnae_fiscal_principal AS STRING), r'[^0-9]',''),1,4) IN UNNEST(@pref)"]
    params: List = [bigquery.ArrayQueryParameter("pref", "STRING", prefixos)]
    if uf:
        where.append("UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf")
        params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.upper()))
    wsql = " AND ".join(where)

    sql_lista = f"""
    WITH filtrado AS (
      SELECT SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) AS raiz,
             CAST(nome_fantasia AS STRING) AS nome_fantasia,
             UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
             CAST(cnae_fiscal_principal AS STRING) AS cnae
      FROM {t_estab} WHERE {wsql}
    ),
    e AS (
      SELECT raiz, ANY_VALUE(nome_fantasia) nome_fantasia, ANY_VALUE(uf) uf, ANY_VALUE(cnae) cnae
      FROM filtrado GROUP BY raiz
    )
    SELECT e.raiz,
           COALESCE(h.razao_social, er.razao_social) AS razao_social,
           e.nome_fantasia, e.uf, e.cnae,
           h.anos_ativos, h.primeiro_ano, h.ultimo_ano,
           (h.cnpj_raiz IS NOT NULL) AS tem_comex
    FROM e
    LEFT JOIN {t_hab} h ON h.cnpj_raiz = e.raiz
    LEFT JOIN {t_razao} er ON er.cnpj_raiz = e.raiz
    ORDER BY tem_comex DESC, razao_social
    LIMIT {int(limit)}
    """
    sql_total = f"""
    SELECT COUNT(DISTINCT SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8)) n
    FROM {t_estab} WHERE {wsql}
    """
    sql_uf = f"""
    SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf,
           COUNT(DISTINCT SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8)) n
    FROM {t_estab} WHERE {wsql} GROUP BY uf ORDER BY n DESC LIMIT 15
    """
    res = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {
            pool.submit(_run_query, client, sql_lista, params): "lista",
            pool.submit(_run_query, client, sql_total, params): "total",
            pool.submit(_run_query, client, sql_uf, params): "uf",
        }
        for fut in as_completed(futs):
            res[futs[fut]] = fut.result()
    total = int((res.get("total") or [{}])[0].get("n") or 0)
    resumo_uf = [{"uf": r.get("uf"), "n": int(r.get("n") or 0)} for r in (res.get("uf") or [])]
    return res.get("lista") or [], total, resumo_uf


_BD_COMEX = "basedosdados.br_me_comex_stat"
_TBL_NCM_LISTA = "liquid-receiver-483923-n6.Projeto_Comex.ncm_lista"


@router.get("/ncm-autocomplete")
async def ncm_autocomplete(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)):
    """Autocomplete de NCM por código (prefixo)."""
    from google.cloud import bigquery
    digitos = "".join(c for c in q if c.isdigit())
    if not digitos:
        return {"items": []}
    try:
        client = _get_bq_client()
        t = _bt(_env("COMEX_BQ_TABLE_NCM_LISTA", _TBL_NCM_LISTA))
        td = _bt(_env("COMEX_BQ_TABLE_NCM_DESC", _DEFAULT_NCM_DESC))
        sql = (
            f"SELECT n.ncm AS ncm, d.descricao AS descricao "
            f"FROM {t} n LEFT JOIN {td} d ON n.ncm = d.ncm "
            f"WHERE n.ncm LIKE @p ORDER BY n.ncm LIMIT {int(limit)}"
        )
        rows = _run_query(client, sql, [bigquery.ScalarQueryParameter("p", "STRING", f"{digitos}%")])
        return {"items": [{"ncm": r.get("ncm"), "descricao": r.get("descricao") or ""} for r in rows]}
    except Exception as e:
        return {"items": [], "error": str(e)[:200]}


@router.get("/busca-comex")
async def busca_comex(
    ncms: Optional[List[str]] = Query(None),
    tipo: Optional[str] = Query(None, description="importacao | exportacao | (vazio = ambos)"),
    uf: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    fob_min: Optional[float] = Query(None),
    fob_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """Busca REAL de comércio exterior por NCM × UF × mês (tabelas oficiais
    importacao_uf_ncm / exportacao_uf_ncm, sempre atualizadas). Independente de
    importador/exportador."""
    from google.cloud import bigquery

    def _ym(s, default):
        d = "".join(c for c in (s or "") if c.isdigit())
        return int(d[:6]) if len(d) >= 6 else default
    ym_ini = _ym(data_inicio, 202001)
    ym_fim = _ym(data_fim, 209912)

    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    t = (tipo or "").lower()
    if "import" in t:
        fluxos = [("Importação", t_imp, "total_importacao_fob")]
    elif "export" in t:
        fluxos = [("Exportação", t_exp, "total_exportacao_fob")]
    else:
        fluxos = [("Importação", t_imp, "total_importacao_fob"),
                  ("Exportação", t_exp, "total_exportacao_fob")]

    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "results": [], "total": 0}

    ncms_lp = [("".join(c for c in n if c.isdigit())) for n in (ncms or []) if n]
    ncms_lp = [n for n in ncms_lp if n]
    params: List = [
        bigquery.ScalarQueryParameter("a", "INT64", ym_ini),
        bigquery.ScalarQueryParameter("b", "INT64", ym_fim),
    ]
    if ncms_lp:
        params.append(bigquery.ArrayQueryParameter("ncms", "STRING", ncms_lp))
    if uf:
        params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.upper()))

    partes = []
    for rotulo, tbl, col in fluxos:
        cond = ["(ano*100+mes) BETWEEN @a AND @b"]
        if ncms_lp:
            cond.append("CAST(id_ncm AS STRING) IN UNNEST(@ncms)")
        if uf:
            cond.append("UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf")
        partes.append(f"""
        SELECT '{rotulo}' AS tipo_operacao, ano, mes,
               CAST(id_ncm AS STRING) AS ncm,
               UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf,
               SUM(CAST({col} AS FLOAT64)) AS fob
        FROM {tbl}
        WHERE {' AND '.join(cond)}
        GROUP BY tipo_operacao, ano, mes, ncm, uf
        """)

    having = []
    if fob_min is not None:
        having.append("fob >= @fmin")
        params.append(bigquery.ScalarQueryParameter("fmin", "FLOAT64", float(fob_min)))
    if fob_max is not None:
        having.append("fob <= @fmax")
        params.append(bigquery.ScalarQueryParameter("fmax", "FLOAT64", float(fob_max)))
    having_sql = f"HAVING {' AND '.join(having)}" if having else ""

    offset = (page - 1) * page_size
    sql = f"""
    WITH base AS (
      {' UNION ALL '.join(partes)}
    ),
    filtrado AS (SELECT * FROM base {having_sql})
    SELECT (SELECT COUNT(*) FROM filtrado) AS _total,
           tipo_operacao, ano, mes, ncm, uf, fob
    FROM filtrado
    ORDER BY fob DESC
    LIMIT {int(page_size)} OFFSET {int(offset)}
    """
    try:
        rows = _run_query(client, sql, params)
        total = int(rows[0].get("_total")) if rows else 0
        results = [{
            "ncm": r.get("ncm"),
            "tipo_operacao": r.get("tipo_operacao"),
            "uf": r.get("uf"),
            "valor_fob": float(r.get("fob") or 0),
            "data_operacao": f"{int(r.get('ano') or 0):04d}-{int(r.get('mes') or 0):02d}-01",
        } for r in rows]
        return {"results": results, "total": total, "page": page, "page_size": page_size,
                "fonte": "importacao_uf_ncm / exportacao_uf_ncm (dados oficiais MDIC, por NCM×UF×mês)"}
    except Exception as e:
        return {"error": str(e)[:400], "results": [], "total": 0}


@router.get("/ncm-analise")
async def ncm_analise(
    ncm: str = Query(..., min_length=2, description="Código NCM (8 dígitos)"),
    ano_inicio: int = Query(2022, ge=2000, le=2030),
    ano_fim: int = Query(2025, ge=2000, le=2030),
):
    """Análise REAL de um NCM (BigQuery, dados oficiais MDIC por UF×mês):
    totais, evolução mensal e distribuição por UF de importação/exportação,
    mais os principais importadores/exportadores reais (base Logcomex)."""
    from google.cloud import bigquery

    dig = "".join(c for c in (ncm or "") if c.isdigit())[:8]
    if len(dig) < 2:
        return {"error": "NCM inválido", "ncm": ncm}
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "ncm": dig}

    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    t_desc = _bt(_env("COMEX_BQ_TABLE_NCM_DESC", _DEFAULT_NCM_DESC))
    t_real = _bt(_env("COMEX_BQ_TABLE_REAL_LOGCOMEX",
                      "liquid-receiver-483923-n6.Projeto_Comex.comex_real_import_logcomex"))
    ym0, ym1 = ano_inicio * 100 + 1, ano_fim * 100 + 12
    params = [
        bigquery.ScalarQueryParameter("a", "INT64", ym0),
        bigquery.ScalarQueryParameter("b", "INT64", ym1),
        bigquery.ScalarQueryParameter("ncm", "STRING", dig),
    ]

    # Descrição
    descricao = None
    try:
        drows = _run_query(client, f"SELECT descricao FROM {t_desc} WHERE ncm=@ncm LIMIT 1",
                           [bigquery.ScalarQueryParameter("ncm", "STRING", dig)])
        if drows:
            descricao = drows[0].get("descricao")
    except Exception:
        pass

    def _agg(tbl, col):
        sql = f"""
        SELECT ano, mes, UPPER(TRIM(CAST(sigla_uf AS STRING))) uf,
               SUM(CAST({col} AS FLOAT64)) fob
        FROM {tbl}
        WHERE (ano*100+mes) BETWEEN @a AND @b AND CAST(id_ncm AS STRING)=@ncm
        GROUP BY ano, mes, uf
        """
        return _run_query(client, sql, params)

    tl = {}   # ym -> {imp, exp}
    ufs = {}  # uf -> {imp, exp}
    total_imp = total_exp = 0.0
    for rows, key in ((_agg(t_imp, "total_importacao_fob"), "imp"),
                      (_agg(t_exp, "total_exportacao_fob"), "exp")):
        for r in rows:
            v = float(r.get("fob") or 0)
            ym = f"{int(r.get('ano') or 0):04d}-{int(r.get('mes') or 0):02d}"
            tl.setdefault(ym, {"v_imp": 0.0, "v_exp": 0.0})[f"v_{key}"] += v
            u = r.get("uf") or "—"
            ufs.setdefault(u, {"v_imp": 0.0, "v_exp": 0.0})[f"v_{key}"] += v
            if key == "imp":
                total_imp += v
            else:
                total_exp += v

    timeline = [{"ym": k, **tl[k]} for k in sorted(tl)]
    por_uf = sorted(
        [{"uf": u, **ufs[u]} for u in ufs],
        key=lambda x: (x["v_imp"] + x["v_exp"]), reverse=True,
    )

    # Principais importadores/exportadores reais para o NCM (base Logcomex)
    def _top_real(campo):
        try:
            sql = f"""
            SELECT {campo} nome, SUM(fob_import) v, SUM(n_operacoes) n
            FROM {t_real}
            WHERE id_ncm=@ncm AND {campo} IS NOT NULL
              AND (ano*100+mes) BETWEEN @a AND @b
            GROUP BY nome ORDER BY v DESC LIMIT 10
            """
            return [{"nome": r.get("nome"), "valor_total": float(r.get("v") or 0),
                     "total_operacoes": int(r.get("n") or 0)}
                    for r in _run_query(client, sql, params)]
        except Exception:
            return []

    return {
        "ncm": dig,
        "descricao": descricao,
        "periodo": {"ano_inicio": ano_inicio, "ano_fim": ano_fim},
        "total_imp": total_imp,
        "total_exp": total_exp,
        "saldo": total_exp - total_imp,
        "timeline": timeline,
        "por_uf": por_uf,
        "top_importadores": _top_real("importador_nome"),
        "top_exportadores": _top_real("exportador_nome"),
        "fonte": "importacao_uf_ncm / exportacao_uf_ncm (MDIC) + comex_real_import_logcomex",
    }


@router.get("/cnae-arvore")
async def cnae_arvore():
    """Árvore CNAE Setor→Segmento→Ramo→Categoria para os filtros do Painel de Empresas."""
    try:
        from services import cnae_service
        return {"arvore": cnae_service.arvore(), "setores": cnae_service.listar_setores()}
    except Exception as e:
        return {"error": str(e), "arvore": {}, "setores": []}


@router.get("/empresas-por-segmento")
async def empresas_por_segmento(
    setor: Optional[str] = Query(None),
    segmento: Optional[str] = Query(None),
    ramo: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    uf: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Busca por CNPJ, razão social ou nome fantasia"),
    limit: int = Query(100, ge=1, le=500),
):
    """Lista empresas por setor/segmento/ramo/categoria (CNAE) e/ou busca por
    CNPJ / razão social / nome fantasia. Inclui resumo por UF."""
    from services import cnae_service
    from google.cloud import bigquery

    q_clean = (q or "").strip()
    tem_cnae = bool(setor or segmento or ramo or categoria)
    if not tem_cnae and not q_clean:
        return {"filtros": {}, "total": 0, "empresas": [], "resumo_uf": [],
                "aviso": "Selecione um setor/segmento ou busque por empresa (CNPJ/nome)."}

    prefixos = cnae_service.prefixos_por_filtro(setor, segmento, ramo, categoria) if tem_cnae else []
    if tem_cnae and not prefixos:
        return {"filtros": {"setor": setor, "segmento": segmento, "ramo": ramo, "categoria": categoria},
                "total": 0, "empresas": [], "resumo_uf": [], "aviso": "Nenhum CNAE corresponde ao filtro."}
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "empresas": []}

    filtros_out = {"setor": setor, "segmento": segmento, "ramo": ramo,
                   "categoria": categoria, "uf": uf, "q": q_clean or None}

    # ─── Busca por empresa (q): base completa de Estabelecimentos + flag comex ───
    if q_clean:
        try:
            rows = _buscar_empresas_geral(client, q_clean, prefixos, uf, limit) or []
        except Exception as e:
            return {"error": str(e)[:300], "empresas": [], "filtros": filtros_out}
        empresas = []
        resumo = {}
        for r in rows:
            h = cnae_service.enriquecer_por_prefixo(
                r.get("cnae"), setor=setor, segmento=segmento, ramo=ramo, categoria=categoria
            ) or {}
            nome = (r.get("razao_social") or r.get("nome_fantasia") or "—")
            ufr = r.get("uf")
            if ufr:
                resumo[ufr] = resumo.get(ufr, 0) + 1
            empresas.append({
                "cnpj": r.get("raiz"), "razao_social": nome,
                "nome_fantasia": r.get("nome_fantasia"),
                "uf": ufr, "cnae": r.get("cnae"),
                "setor": h.get("setor"), "segmento": h.get("segmento"),
                "ramo": h.get("ramo"), "categoria": h.get("categoria"),
                "tem_comex": bool(r.get("tem_comex")),
                "primeiro_ano": int(r.get("primeiro_ano") or 0),
                "ultimo_ano": int(r.get("ultimo_ano") or 0),
                "anos_ativos": int(r.get("anos_ativos") or 0),
            })
        resumo_uf = sorted(
            [{"uf": k, "n": v} for k, v in resumo.items()], key=lambda x: -x["n"]
        )[:15]
        return {
            "filtros": filtros_out, "total": len(empresas), "exibidas": len(empresas),
            "empresas": empresas, "resumo_uf": resumo_uf, "prefixos_cnae": prefixos,
            "fonte": "Estabelecimentos RF (base completa) + flag de comex",
        }

    # ─── Filtro por CNAE apenas (sem q): TODAS as empresas da base RF ───
    try:
        rows, total, resumo_uf = _listar_empresas_cnae(client, prefixos, uf, limit)
    except Exception as e:
        return {"error": str(e)[:300], "empresas": [], "filtros": filtros_out}
    empresas = []
    for r in rows:
        h = cnae_service.enriquecer_por_prefixo(
            r.get("cnae"), setor=setor, segmento=segmento, ramo=ramo, categoria=categoria
        ) or {}
        nome = (r.get("razao_social") or r.get("nome_fantasia") or "—")
        empresas.append({
            "cnpj": r.get("raiz"), "razao_social": nome,
            "nome_fantasia": r.get("nome_fantasia"),
            "uf": r.get("uf"), "cnae": r.get("cnae"),
            "setor": h.get("setor"), "segmento": h.get("segmento"),
            "ramo": h.get("ramo"), "categoria": h.get("categoria"),
            "tem_comex": bool(r.get("tem_comex")),
            "primeiro_ano": int(r.get("primeiro_ano") or 0),
            "ultimo_ano": int(r.get("ultimo_ano") or 0),
            "anos_ativos": int(r.get("anos_ativos") or 0),
        })
    return {
        "filtros": filtros_out,
        "total": total, "exibidas": len(empresas),
        "empresas": empresas, "resumo_uf": resumo_uf,
        "prefixos_cnae": prefixos,
        "fonte": "Estabelecimentos RF (base completa) + flag de comex",
    }


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


_DEFAULT_ESTIMADO = "liquid-receiver-483923-n6.Projeto_Comex.empresas_comex_estimado"


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


_TBL_IEX = "liquid-receiver-483923-n6.Projeto_Comex.empresasimportexport"


@router.get("/habilitacao")
async def habilitacao_empresa(q: str = Query(..., min_length=2, description="CNPJ ou nome")):
    """Verifica se uma empresa tem habilitação para comex (registro de operações)."""
    try:
        client = _get_bq_client()
        cnpjs = _resolve_cnpjs(client, q)
    except Exception as e:
        return {"error": str(e)}
    if not cnpjs:
        return {"q": q, "encontrada": False, "habilitada": False, "aviso": f"Empresa '{q}' não localizada."}
    hab = _get_habilitacao(client, cnpjs)
    return {"q": q, "encontrada": True, "cnpjs": cnpjs, **hab}


@router.get("/habilitadas")
async def listar_habilitadas(
    uf: Optional[str] = Query(None, description="Sigla UF"),
    cnae_prefixo: Optional[str] = Query(None, description="Prefixo do CNAE (ex.: 4530)"),
    ano: Optional[int] = Query(None, ge=1997, le=2030),
    limit: int = Query(50, ge=1, le=500),
):
    """Lista empresas habilitadas (comex-ativas) com filtros UF/CNAE/ano."""
    try:
        client = _get_bq_client()
    except Exception as e:
        return {"error": str(e), "empresas": []}
    from google.cloud import bigquery
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_IMPEX", _TBL_IEX))
    where = ["1=1"]
    params: List = []
    if uf:
        where.append("UPPER(TRIM(CAST(sigla_uf AS STRING))) = @uf")
        params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.upper()))
    if cnae_prefixo:
        where.append("REGEXP_REPLACE(CAST(cnae_2_primaria AS STRING), r'[^0-9]','') LIKE @cnaep")
        params.append(bigquery.ScalarQueryParameter("cnaep", "STRING", f"{cnae_prefixo}%"))
    if ano:
        where.append("ano = @ano")
        params.append(bigquery.ScalarQueryParameter("ano", "INT64", ano))
    sql = f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','') AS cnpj,
      ANY_VALUE(razao_social) AS razao_social,
      UPPER(TRIM(ANY_VALUE(sigla_uf))) AS uf,
      ANY_VALUE(cnae_2_primaria) AS cnae,
      MIN(ano) AS primeiro_ano,
      MAX(ano) AS ultimo_ano,
      COUNT(DISTINCT ano) AS anos_ativos
    FROM {t}
    WHERE {' AND '.join(where)}
      AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) = 14
    GROUP BY cnpj
    ORDER BY anos_ativos DESC, ultimo_ano DESC
    LIMIT {int(limit)}
    """
    try:
        rows = _run_query(client, sql, params)
        return {
            "filtros": {"uf": uf, "cnae_prefixo": cnae_prefixo, "ano": ano},
            "total": len(rows),
            "empresas": [
                {
                    "cnpj": r.get("cnpj"), "razao_social": r.get("razao_social"),
                    "uf": r.get("uf"), "cnae": r.get("cnae"),
                    "primeiro_ano": int(r.get("primeiro_ano") or 0),
                    "ultimo_ano": int(r.get("ultimo_ano") or 0),
                    "anos_ativos": int(r.get("anos_ativos") or 0),
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"error": str(e)[:300], "empresas": []}


def _get_habilitacao(client, cnpjs: List[str]) -> Dict:
    """Verifica a 'habilitação' para comex via empresasimportexport.

    Uma empresa que aparece nessa base operou import/export no(s) ano(s) listado(s),
    o que pressupõe habilitação no RADAR/Siscomex naquele período.
    """
    if not cnpjs:
        return {"habilitada": False}
    from google.cloud import bigquery
    raizes = sorted({c[:8] for c in cnpjs if len(c) >= 8})
    if not raizes:
        return {"habilitada": False}
    params = [bigquery.ArrayQueryParameter("raizes", "STRING", raizes)]
    fonte = "empresasimportexport (operações de comércio exterior — base MDIC)"

    # Caminho rápido: tabela materializada empresas_habilitacao
    t_hab = _bt(_env("COMEX_BQ_TABLE_HABILITACAO", "liquid-receiver-483923-n6.Projeto_Comex.empresas_habilitacao"))
    sql_tab = f"""
    SELECT ANY_VALUE(razao_social) razao_social, UPPER(TRIM(ANY_VALUE(uf))) uf,
           ANY_VALUE(cnae) cnae, MIN(primeiro_ano) primeiro_ano, MAX(ultimo_ano) ultimo_ano,
           MAX(anos_ativos) anos_ativos, SUM(n_cnpjs) n_cnpjs
    FROM {t_hab} WHERE cnpj_raiz IN UNNEST(@raizes)
    """
    # Caminho ao vivo (fallback se a tabela não existir)
    t = _bt(_env("COMEX_BQ_TABLE_EMPRESAS_IMPEX", _TBL_IEX))
    sql_live = f"""
    SELECT
      ANY_VALUE(razao_social) razao_social,
      UPPER(TRIM(ANY_VALUE(sigla_uf))) uf,
      ANY_VALUE(cnae_2_primaria) cnae,
      MIN(ano) primeiro_ano,
      MAX(ano) ultimo_ano,
      COUNT(DISTINCT ano) anos_ativos,
      COUNT(DISTINCT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) n_cnpjs
    FROM {t}
    WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) IN UNNEST(@raizes)
    """

    def _fmt(r) -> Dict:
        if not r or not r.get("primeiro_ano"):
            return {"habilitada": False}
        return {
            "habilitada": True,
            "primeiro_ano": int(r.get("primeiro_ano") or 0),
            "ultimo_ano": int(r.get("ultimo_ano") or 0),
            "anos_ativos": int(r.get("anos_ativos") or 0),
            "n_cnpjs": int(r.get("n_cnpjs") or 0),
            "uf": r.get("uf"),
            "cnae": r.get("cnae"),
            "fonte": fonte,
        }

    try:
        rows = _run_query(client, sql_tab, params)
        if rows:
            return _fmt(rows[0])
    except Exception:
        pass  # tabela materializada ausente — usa cálculo ao vivo
    try:
        rows = _run_query(client, sql_live, params)
        return _fmt(rows[0] if rows else {})
    except Exception as e:
        logger.warning(f"_get_habilitacao erro: {e}")
        return {"habilitada": False, "erro": str(e)[:200]}


def _get_comex_estimado(client, cnpjs: List[str], ano_ini: int = 2020, ano_fim: int = 2021) -> Dict:
    """Estimativa de comex por CNPJ calculada ao vivo (sem tabela materializada).

    Metodologia: para cada UF onde a empresa é comex-ativa (empresasimportexport),
    rateia o total de importação/exportação da UF (tabelas UF×NCM, período de
    sobreposição) igualmente entre os CNPJs comex-ativos do estado, e soma a
    parte dos CNPJs da empresa.
    """
    if not cnpjs:
        return {}
    from google.cloud import bigquery

    raizes = sorted({c[:8] for c in cnpjs if len(c) >= 8})
    if not raizes:
        return {}

    # Se houver tabela materializada, usa-a (mais rápido); casa por raiz (8 díg.)
    # para capturar todos os estabelecimentos da empresa, igual ao cálculo ao vivo.
    t_est = _bt(_env("COMEX_BQ_TABLE_ESTIMADO", _DEFAULT_ESTIMADO))
    sql_tab = f"""
    SELECT uf, SUM(imp_estimado) imp_uf, SUM(exp_estimado) exp_uf,
           ANY_VALUE(empresas_uf) empresas_uf, ANY_VALUE(ano_ini) ano_ini,
           ANY_VALUE(ano_fim) ano_fim, COUNT(*) n_cnpjs
    FROM {t_est} WHERE cnpj_raiz IN UNNEST(@raizes)
    GROUP BY uf ORDER BY (SUM(imp_estimado)+SUM(exp_estimado)) DESC
    """
    try:
        rows = _run_query(client, sql_tab, [bigquery.ArrayQueryParameter("raizes", "STRING", raizes)])
        if rows:
            return _montar_estimado(rows, key_imp="imp_uf", key_exp="exp_uf")
    except Exception:
        pass  # tabela não existe — segue para cálculo ao vivo

    # Fallback simplificado (rateio igual, sem ponderar porte) — só usado se a
    # tabela materializada estiver ausente. A versão ponderada está na tabela.
    t_imp = _bt(_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_UF))
    t_exp = _bt(_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_UF))
    t_iex = _bt("liquid-receiver-483923-n6.Projeto_Comex.empresasimportexport")
    sql_live = f"""
    WITH
    emp AS (
      SELECT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','') cnpj14,
             UPPER(TRIM(CAST(sigla_uf AS STRING))) uf
      FROM {t_iex}
      WHERE ano BETWEEN @a0 AND @a1
        AND SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]',''),1,8) IN UNNEST(@raizes)
      GROUP BY cnpj14, uf
    ),
    ufs AS (SELECT DISTINCT uf FROM emp),
    uf_n AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf,
             COUNT(DISTINCT REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]','')) n
      FROM {t_iex}
      WHERE ano BETWEEN @a0 AND @a1
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN (SELECT uf FROM ufs)
      GROUP BY uf
    ),
    uf_imp AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_importacao_fob AS FLOAT64)) v
      FROM {t_imp} WHERE ano BETWEEN @a0 AND @a1
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN (SELECT uf FROM ufs)
      GROUP BY uf
    ),
    uf_exp AS (
      SELECT UPPER(TRIM(CAST(sigla_uf AS STRING))) uf, SUM(CAST(total_exportacao_fob AS FLOAT64)) v
      FROM {t_exp} WHERE ano BETWEEN @a0 AND @a1
        AND UPPER(TRIM(CAST(sigla_uf AS STRING))) IN (SELECT uf FROM ufs)
      GROUP BY uf
    )
    SELECT
      emp.uf,
      COUNT(*) AS n_cnpjs,
      ANY_VALUE(uf_n.n) AS empresas_uf,
      COALESCE(ANY_VALUE(uf_imp.v),0) / NULLIF(ANY_VALUE(uf_n.n),0) * COUNT(*) AS imp_uf,
      COALESCE(ANY_VALUE(uf_exp.v),0) / NULLIF(ANY_VALUE(uf_n.n),0) * COUNT(*) AS exp_uf,
      {ano_ini} AS ano_ini, {ano_fim} AS ano_fim
    FROM emp
    JOIN uf_n ON uf_n.uf = emp.uf
    LEFT JOIN uf_imp ON uf_imp.uf = emp.uf
    LEFT JOIN uf_exp ON uf_exp.uf = emp.uf
    GROUP BY emp.uf
    ORDER BY imp_uf + exp_uf DESC
    """
    params = [
        bigquery.ArrayQueryParameter("raizes", "STRING", raizes),
        bigquery.ScalarQueryParameter("a0", "INT64", ano_ini),
        bigquery.ScalarQueryParameter("a1", "INT64", ano_fim),
    ]
    try:
        rows = _run_query(client, sql_live, params)
        return _montar_estimado(rows, key_imp="imp_uf", key_exp="exp_uf")
    except Exception as e:
        logger.warning(f"_get_comex_estimado (live) erro: {e}")
        return {}


def _montar_estimado(rows, key_imp: str, key_exp: str) -> Dict:
    if not rows:
        return {}
    total_imp = sum(float(r.get(key_imp) or 0) for r in rows)
    total_exp = sum(float(r.get(key_exp) or 0) for r in rows)
    return {
        "total_imp": total_imp,
        "total_exp": total_exp,
        "ano_ini": int(rows[0].get("ano_ini") or 0),
        "ano_fim": int(rows[0].get("ano_fim") or 0),
        "por_uf": [
            {
                "uf": r.get("uf"),
                "imp": float(r.get(key_imp) or 0),
                "exp": float(r.get(key_exp) or 0),
                "empresas_uf": int(r.get("empresas_uf") or 0),
                "n_cnpjs": int(r.get("n_cnpjs") or 0),
            }
            for r in rows
        ],
    }


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

    # 2. Buscar perfil + comex + habilitação em paralelo (cada função é resiliente a erros)
    jobs = {
        "perfil": lambda: _get_estab_profile(client, cnpjs),
        "comex": lambda: _get_comex_empresa(client, cnpjs, ano_inicio, ano_fim),
        "razao": lambda: _get_razao_base(client, cnpjs),
        "habilitacao": lambda: _get_habilitacao(client, cnpjs),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
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
    habilitacao = results.get("habilitacao") or {"habilitada": False}

    total_imp = float(comex.get("total_imp") or 0)
    total_exp = float(comex.get("total_exp") or 0)
    tem_dados = (total_imp + total_exp) > 0

    # 2a. Valores REAIS de importação (base Logcomex deduplicada) — precedência.
    real_lc = None
    if not tem_dados:
        try:
            from services import comex_empresa_stats as _emp_stats
            _ym0 = ano_inicio * 100 + 1
            _ym1 = ano_fim * 100 + 12
            real_lc = _emp_stats.stats_real_import_logcomex(
                client, _run_query, _bt, _env, cnpjs, q, _ym0, _ym1, lado="importador"
            )
        except Exception as e:
            logger.warning(f"real_logcomex error: {e}")
            real_lc = None
        if real_lc and (float(real_lc.get("total_imp") or 0) + float(real_lc.get("total_exp") or 0)) > 0:
            total_imp = float(real_lc.get("total_imp") or 0)
            total_exp = float(real_lc.get("total_exp") or 0)
            tem_dados = True
            # normaliza para os mesmos campos que o restante do endpoint usa
            comex = {
                "total_imp": total_imp,
                "total_exp": total_exp,
                "timeline": [
                    {"ym": ym, "vi": v, "ve": (real_lc.get("valores_exp_por_mes") or {}).get(ym, 0)}
                    for ym, v in sorted((real_lc.get("valores_imp_por_mes") or {}).items())
                ],
                "top_ncms": [
                    {"ncm": n.get("ncm"), "vi": float(n.get("valor_total") or 0), "ve": 0}
                    for n in (real_lc.get("principais_ncms") or [])
                ],
                "top_ufs": [
                    {"uf": u.get("uf"), "vi": float(u.get("imp") or 0), "ve": float(u.get("exp") or 0)}
                    for u in (real_lc.get("por_uf") or [])
                ],
            }

    # 2b. Estimativa por CNPJ (tabela empresas_comex_estimado), usada quando não há dado real
    estimado = {}
    fonte_valores = "indisponivel"
    if not tem_dados:
        estimado = _get_comex_estimado(client, cnpjs)
        est_tot = float(estimado.get("total_imp") or 0) + float(estimado.get("total_exp") or 0)
        if estimado and est_tot > 0:
            # Calibração pela base real Logcomex (estimativa por participação-de-UF infla ~17,5×)
            _FCAL = getattr(__import__("services.comex_empresa_stats", fromlist=["_FATOR_CALIBRACAO_IMPORT"]),
                            "_FATOR_CALIBRACAO_IMPORT", 0.0573)
            for _u in (estimado.get("por_uf") or []):
                _u["imp"] = float(_u.get("imp") or 0) * _FCAL
                _u["exp"] = float(_u.get("exp") or 0) * _FCAL
            total_imp = float(estimado.get("total_imp") or 0) * _FCAL
            total_exp = float(estimado.get("total_exp") or 0) * _FCAL
            estimado["total_imp"] = total_imp
            estimado["total_exp"] = total_exp
            fonte_valores = "estimado"
    else:
        fonte_valores = "real"

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

    # 7. UFs — de dados reais ou, na ausência, do detalhamento estimado por UF
    if comex.get("top_ufs"):
        ufs_empresa = [
            {"uf": r.get("uf"), "v_imp": float(r.get("vi") or 0), "v_exp": float(r.get("ve") or 0)}
            for r in comex.get("top_ufs")
        ]
    else:
        ufs_empresa = [
            {"uf": r.get("uf"), "v_imp": float(r.get("imp") or 0), "v_exp": float(r.get("exp") or 0)}
            for r in (estimado.get("por_uf") or [])
        ]

    razao = str(perfil.get("razao_social") or razao_base.get("razao_social") or cnpjs[0]).strip()

    # Há valores a exibir (reais ou estimados)?
    tem_valores = fonte_valores in ("real", "estimado")
    periodo_est = (
        f"{estimado.get('ano_ini')}-{estimado.get('ano_fim')}"
        if fonte_valores == "estimado" and estimado.get("ano_ini") else None
    )

    if fonte_valores == "estimado":
        aviso = (
            f"Valores ESTIMADOS para {razao}. Não há registro real de comex por CNPJ na base; "
            f"a estimativa rateia o total de importação/exportação de cada UF ({periodo_est}) "
            "entre as empresas comex-ativas do estado, ponderado pelo porte (nº de "
            "estabelecimentos). Use como ordem de grandeza, não como histórico real."
        )
    elif fonte_valores == "real":
        aviso = None
    else:
        aviso = (
            f"Não há registros nem estimativa de comex por CNPJ para {razao}. "
            f"Exibindo o mercado de comércio exterior da UF {uf or '—'} como referência."
        )

    return {
        "q": q,
        "cnpjs": cnpjs,
        "razao_social": razao,
        "uf_sede": uf,
        "municipio": str(perfil.get("municipio") or razao_base.get("municipio") or "").strip() or None,
        "cnae": cnae,
        "cnae_hierarquia": cnae_hierarquia,
        "num_estabelecimentos": int(perfil.get("num_estab") or 0),
        "habilitacao": habilitacao,
        "tem_dados_comex": tem_valores,
        "fonte_valores": fonte_valores,
        "periodo_estimativa": periodo_est,
        "kpis": {
            "total_imp": total_imp,
            "total_exp": total_exp,
            "saldo": total_exp - total_imp,
            "num_ncms": int(comex.get("num_ncms") or 0),
            "num_ufs": int(comex.get("num_ufs") or 0) or len(estimado.get("por_uf") or []),
        },
        "estimado_por_uf": estimado.get("por_uf") or [],
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
        "aviso": aviso,
    }
