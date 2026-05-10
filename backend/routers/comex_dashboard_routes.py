from __future__ import annotations

import csv
import io
import json
import os
import re
from datetime import date
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger


router = APIRouter(prefix="/api/comex-dashboard", tags=["comex-dashboard"])

# Tabela única legada (grão CNPJ × NCM × UF). Use quando COMEX_BQ_RELATED_MODEL não estiver ativo.
_DEFAULT_BQ_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf"

# Modelo relacionado: fatos UF×NCM (import + export) × empresas (base + empresasimportexport), sem super-tabela física.
_DEFAULT_IMPORT_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.importacao_uf_ncm"
_DEFAULT_EXPORT_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.exportacao_uf_ncm"
_DEFAULT_EMPRESAS_BASE_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"
_DEFAULT_EMPRESAS_IMPEX_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.empresasimportexport"


def _strip_bt(s: str) -> str:
    return (s or "").strip().strip("`")


def _bt(ref: str) -> str:
    r = _strip_bt(ref)
    return f"`{r}`" if r else ""


def _get_table_ref() -> str:
    """Referência SQL BigQuery (com backticks) para empresas_ncm_import_export_uf (modo legado)."""
    raw = (os.getenv("COMEX_BQ_TABLE_EMPRESAS_NCM") or _DEFAULT_BQ_TABLE).strip().strip("`")
    if not raw:
        raw = _DEFAULT_BQ_TABLE
    return f"`{raw}`"


def _use_related_model() -> bool:
    """
    JOIN lógico import/export UF×NCM + empresas (opcional, mesmo UF).
    Padrão: ativo (tabelas separadas). Defina COMEX_BQ_RELATED_MODEL=false para usar só
    COMEX_BQ_TABLE_EMPRESAS_NCM (tabela única legada).
    """
    v = (os.getenv("COMEX_BQ_RELATED_MODEL") or "").strip().lower()
    return v not in ("0", "false", "no", "off")


def _table_env(key: str, default_full_id: str) -> str:
    return _strip_bt(os.getenv(key) or default_full_id)


def _empresas_impex_autocomplete_sql(where_name: str) -> str:
    """Lista empresas com cadastro em empresasimportexport (sem cruzar fatos UF×NCM — autocomplete rápido)."""
    t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
    t_ie = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_IMPEX", _DEFAULT_EMPRESAS_IMPEX_TABLE))
    return f"""
    SELECT
      b.cnpj,
      b.razao_social,
      CAST(0 AS FLOAT64) AS total_importacao_fob,
      CAST(0 AS FLOAT64) AS total_exportacao_fob
    FROM {t_base} AS b
    INNER JOIN {t_ie} AS x
      ON REGEXP_REPLACE(CAST(b.cnpj AS STRING), r'[^0-9]', '')
       = REGEXP_REPLACE(CAST(x.cnpj AS STRING), r'[^0-9]', '')
    WHERE {where_name}
    """


def _related_joined_select_sql() -> str:
    """
    Mesmo grão do dashboard: cnpj, razao_social, ano, mes, sigla_uf, id_ncm, totais FOB.
    Fatos vêm de import/export UF×NCM. Empresas: LEFT JOIN (se não houver match, cnpj/razao NULL
    mas totais UF×NCM seguem — evita dashboard zerado quando a tabela impex/base não cruza).
    Há match: volume UF×NCM repetido por empresa do mesmo UF (impex ∩ base).
    """
    t_imp = _bt(_table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_TABLE))
    t_exp = _bt(_table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_TABLE))
    t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
    t_ie = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_IMPEX", _DEFAULT_EMPRESAS_IMPEX_TABLE))
    return f"""
    SELECT
      e.cnpj,
      e.razao_social,
      u.ano,
      u.mes,
      u.sigla_uf,
      u.id_ncm,
      u.total_importacao_fob,
      u.total_exportacao_fob
    FROM (
      SELECT
        COALESCE(i.ano, e.ano) AS ano,
        COALESCE(i.mes, e.mes) AS mes,
        COALESCE(i.sigla_uf, e.sigla_uf) AS sigla_uf,
        CAST(COALESCE(i.id_ncm, e.id_ncm) AS STRING) AS id_ncm,
        COALESCE(i.total_importacao_fob, 0) AS total_importacao_fob,
        COALESCE(e.total_exportacao_fob, 0) AS total_exportacao_fob
      FROM {t_imp} AS i
      FULL OUTER JOIN {t_exp} AS e
        ON i.ano = e.ano
       AND i.mes = e.mes
       AND i.sigla_uf = e.sigla_uf
       AND CAST(i.id_ncm AS STRING) = CAST(e.id_ncm AS STRING)
    ) AS u
    LEFT JOIN (
      SELECT
        b.cnpj,
        b.razao_social,
        b.sigla_uf
      FROM {t_base} AS b
      INNER JOIN {t_ie} AS x
        ON REGEXP_REPLACE(CAST(b.cnpj AS STRING), r'[^0-9]', '')
         = REGEXP_REPLACE(CAST(x.cnpj AS STRING), r'[^0-9]', '')
    ) AS e
      ON UPPER(TRIM(CAST(u.sigla_uf AS STRING))) = UPPER(TRIM(CAST(e.sigla_uf AS STRING)))
    """


def _fonte_dados() -> Dict[str, str]:
    if _use_related_model():
        imp = _table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_TABLE)
        exp = _table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_TABLE)
        base = _table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE)
        ie = _table_env("COMEX_BQ_TABLE_EMPRESAS_IMPEX", _DEFAULT_EMPRESAS_IMPEX_TABLE)
        desc = f"{imp} + {exp} JOIN {base} + {ie} (UF)"
        return {
            "motor": "bigquery",
            "tabela_id": desc,
            "tabela_sql": desc,
            "nome_logico": "related_uf_ncm_x_empresas_impex",
        }
    ref = _get_table_ref()
    return {
        "motor": "bigquery",
        "tabela_id": ref.strip("`"),
        "tabela_sql": ref,
        "nome_logico": "empresas_ncm_import_export_uf",
    }


SORTABLE_COLUMNS = {
    "cnpj": "cnpj",
    "razao_social": "razao_social",
    "sigla_uf": "sigla_uf",
    "id_ncm": "id_ncm",
    "ano": "ano",
    "mes": "mes",
    "total_importacao_fob": "total_importacao_fob",
    "total_exportacao_fob": "total_exportacao_fob",
    "saldo": "saldo",
}


def _get_bigquery_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dependencias BigQuery indisponiveis: {exc}")

    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    try:
        if credentials_json:
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=credentials, project=info.get("project_id"))
        if credentials_path and os.path.exists(credentials_path):
            return bigquery.Client.from_service_account_json(credentials_path)
        return bigquery.Client()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao inicializar cliente BigQuery: {exc}")


def _build_filters(
    empresa: Optional[str],
    ano: Optional[int],
    mes: Optional[int],
    uf: Optional[str],
    ncm: Optional[str],
):
    from google.cloud import bigquery

    conditions = ["1=1"]
    params: List[object] = []

    if empresa:
        conditions.append("(LOWER(cnpj) LIKE LOWER(@empresa) OR LOWER(razao_social) LIKE LOWER(@empresa))")
        params.append(bigquery.ScalarQueryParameter("empresa", "STRING", f"%{empresa.strip()}%"))
    if ano:
        conditions.append("ano = @ano")
        params.append(bigquery.ScalarQueryParameter("ano", "INT64", int(ano)))
    if mes:
        conditions.append("mes = @mes")
        params.append(bigquery.ScalarQueryParameter("mes", "INT64", int(mes)))
    if uf:
        conditions.append("UPPER(sigla_uf) = UPPER(@uf)")
        params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.strip().upper()))
    if ncm:
        conditions.append("CAST(id_ncm AS STRING) LIKE @ncm")
        params.append(bigquery.ScalarQueryParameter("ncm", "STRING", f"%{ncm.strip()}%"))

    return " AND ".join(conditions), params


def _run_query(client, query: str, params: List[object]) -> List[dict]:
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return [dict(row.items()) for row in client.query(query, job_config=job_config).result()]


def _raise_http_for_bigquery(exc: Exception, log_message: str) -> None:
    """Registra o erro e lança HTTPException (403 em falhas típicas de IAM no BigQuery)."""
    logger.exception(log_message)
    msg = str(exc)
    low = msg.lower()
    if (
        "access denied" in low
        or "does not have permission" in low
        or "permission denied" in low
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "BigQuery recusou leitura (IAM). No Google Cloud, conceda à conta de serviço do backend "
                "(campo client_email do JSON em GOOGLE_APPLICATION_CREDENTIALS_JSON no Render): "
                "(1) BigQuery Data Viewer no dataset/tabelas usadas (COMEX_BQ_TABLE_EMPRESAS_NCM ou, em modo relacionado, "
                "import/export UF×NCM + empresas_base + empresasimportexport); "
                "(2) BigQuery Job User no projeto em que as consultas são executadas (o do próprio JSON costuma bastar). "
                "Se a tabela estiver noutro projeto, defina COMEX_BQ_TABLE_EMPRESAS_NCM=projeto.dataset.tabela e "
                "conceda as mesmas funções nesse projeto. Detalhe: "
                + msg
            ),
        )
    raise HTTPException(status_code=500, detail=msg)


def _shift_months(y: int, m: int, delta: int) -> Tuple[int, int]:
    m += delta
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    return y, m


def _ym_bounds_from_meses(meses: int) -> Tuple[int, int]:
    today = date.today()
    y2, m2 = today.year, today.month
    y1, m1 = _shift_months(y2, m2, -(max(1, min(120, int(meses) or 24)) - 1))
    return y1 * 100 + m1, y2 * 100 + m2


def _parse_ym_bounds(
    data_inicio: Optional[str],
    data_fim: Optional[str],
    meses: int,
) -> Tuple[int, int]:
    """Retorna (ym_start, ym_end) como inteiros YYYYMM para filtro (ano*100+mes)."""
    di = (data_inicio or "").strip()
    df = (data_fim or "").strip()
    m1 = re.match(r"^(\d{4})-(\d{2})-\d{2}$", di)
    m2 = re.match(r"^(\d{4})-(\d{2})-\d{2}$", df)
    if m1 and m2:
        y1, mo1 = int(m1.group(1)), int(m1.group(2))
        y2, mo2 = int(m2.group(1)), int(m2.group(2))
        ym_start = y1 * 100 + mo1
        ym_end = y2 * 100 + mo2
        if ym_start > ym_end:
            ym_start, ym_end = ym_end, ym_start
        return ym_start, ym_end
    return _ym_bounds_from_meses(meses)


def _sanitize_ncm_digits_list(ncm: Optional[str], ncms: Optional[List[str]]) -> List[str]:
    out: List[str] = []

    def one(s: Optional[str]) -> Optional[str]:
        d = re.sub(r"\D", "", str(s or ""))[:8]
        return d if len(d) == 8 else None

    if ncms:
        for x in ncms:
            v = one(x)
            if v and v not in out:
                out.append(v)
    v = one(ncm)
    if v and v not in out:
        out.append(v)
    return out[:50]


def _build_main_dashboard_where(
    ym_start: int,
    ym_end: int,
    tipo_operacao: Optional[str],
    ncm: Optional[str],
    ncms: Optional[List[str]],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
) -> Tuple[str, List[object]]:
    """Filtros sobre a tabela empresas_ncm_import_export_uf (mesmo escopo do dashboard principal)."""
    from google.cloud import bigquery

    conditions: List[str] = [
        "ano IS NOT NULL AND mes IS NOT NULL",
        "(ano * 100 + mes) >= @ym_start",
        "(ano * 100 + mes) <= @ym_end",
    ]
    params: List[object] = [
        bigquery.ScalarQueryParameter("ym_start", "INT64", int(ym_start)),
        bigquery.ScalarQueryParameter("ym_end", "INT64", int(ym_end)),
    ]

    top = (tipo_operacao or "").strip().lower()
    if "import" in top:
        conditions.append("total_importacao_fob > 0")
    elif "export" in top:
        conditions.append("total_exportacao_fob > 0")

    ncm_list = _sanitize_ncm_digits_list(ncm, ncms)
    if ncm_list:
        conditions.append("REGEXP_REPLACE(CAST(id_ncm AS STRING), r'[^0-9]', '') IN UNNEST(@ncm_list)")
        params.append(bigquery.ArrayQueryParameter("ncm_list", "STRING", ncm_list))

    ei = (empresa_importadora or "").strip()
    if ei:
        like = f"%{ei}%"
        conditions.append(
            "("
            "LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@like_imp) "
            "OR CAST(cnpj AS STRING) LIKE @like_imp"
            ")"
        )
        params.append(bigquery.ScalarQueryParameter("like_imp", "STRING", like))

    ee = (empresa_exportadora or "").strip()
    if ee:
        like_e = f"%{ee}%"
        conditions.append(
            "("
            "LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@like_exp) "
            "OR CAST(cnpj AS STRING) LIKE @like_exp"
            ")"
        )
        params.append(bigquery.ScalarQueryParameter("like_exp", "STRING", like_e))

    return " AND ".join(conditions), params


def _dashboard_stats_payload_from_bq(
    client,
    ym_start: int,
    ym_end: int,
    tipo_operacao: Optional[str],
    ncm: Optional[str],
    ncms: Optional[List[str]],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
) -> Dict:
    where_clause, params = _build_main_dashboard_where(
        ym_start,
        ym_end,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
    )
    cte = _base_filtered_cte(where_clause)
    top_l = (tipo_operacao or "").strip().lower()
    ncm_metric_imp = "COALESCE(SUM(total_importacao_fob), 0)"
    ncm_metric_exp = "COALESCE(SUM(total_exportacao_fob), 0)"
    if "export" in top_l and "import" not in top_l:
        ncm_order_metric = ncm_metric_exp
    elif "import" in top_l and "export" not in top_l:
        ncm_order_metric = ncm_metric_imp
    else:
        ncm_order_metric = f"({ncm_metric_imp} + {ncm_metric_exp})"

    kpi_sql = cte + """
    SELECT
      COALESCE(SUM(total_importacao_fob), 0) AS v_imp,
      COALESCE(SUM(total_exportacao_fob), 0) AS v_exp,
      COUNTIF(total_importacao_fob > 0) AS cnt_imp_rows,
      COUNTIF(total_exportacao_fob > 0) AS cnt_exp_rows,
      COUNT(*) AS cnt_all
    FROM filtered
    """
    kpi = _run_query(client, kpi_sql, params)
    row0 = kpi[0] if kpi else {}
    v_imp = float(row0.get("v_imp") or 0)
    v_exp = float(row0.get("v_exp") or 0)
    cnt_imp = int(row0.get("cnt_imp_rows") or 0)
    cnt_exp = int(row0.get("cnt_exp_rows") or 0)
    cnt_all = int(row0.get("cnt_all") or 0)

    monthly_sql = cte + """
    SELECT
      FORMAT('%04d-%02d', ano, mes) AS ym,
      COUNT(*) AS registros,
      COALESCE(SUM(total_importacao_fob + total_exportacao_fob), 0) AS valor_mes
    FROM filtered
    GROUP BY ano, mes
    ORDER BY ano, mes
    """
    monthly = _run_query(client, monthly_sql, params)
    registros_por_mes: Dict[str, int] = {}
    valores_por_mes: Dict[str, float] = {}
    pesos_por_mes: Dict[str, float] = {}
    for r in monthly:
        ym = str(r.get("ym") or "")
        if not ym:
            continue
        registros_por_mes[ym] = int(r.get("registros") or 0)
        valores_por_mes[ym] = float(r.get("valor_mes") or 0)
        pesos_por_mes[ym] = 0.0

    ncm_sql = cte + f"""
    SELECT
      REGEXP_REPLACE(CAST(id_ncm AS STRING), r'[^0-9]', '') AS ncm,
      {ncm_metric_imp} AS v_imp_ncm,
      {ncm_metric_exp} AS v_exp_ncm
    FROM filtered
    GROUP BY id_ncm
    ORDER BY {ncm_order_metric} DESC
    LIMIT 15
    """
    ncm_rows = _run_query(client, ncm_sql, params)
    principais_ncms: List[dict] = []
    for r in ncm_rows:
        ncm_s = str(r.get("ncm") or "").strip()
        if not ncm_s:
            continue
        vi = float(r.get("v_imp_ncm") or 0)
        ve = float(r.get("v_exp_ncm") or 0)
        if "export" in top_l and "import" not in top_l:
            vtot = ve
        elif "import" in top_l and "export" not in top_l:
            vtot = vi
        else:
            vtot = vi + ve
        if vtot <= 0:
            continue
        principais_ncms.append(
            {
                "ncm": ncm_s,
                "descricao": "",
                "valor_total": vtot,
                "total_operacoes": 0,
            }
        )

    uf_sql = cte + """
    SELECT
      sigla_uf AS uf_key,
      COALESCE(SUM(total_importacao_fob + total_exportacao_fob), 0) AS valor_total,
      COUNT(*) AS total_operacoes
    FROM filtered
    WHERE sigla_uf IS NOT NULL AND CAST(sigla_uf AS STRING) != ''
    GROUP BY sigla_uf
    ORDER BY valor_total DESC
    LIMIT 20
    """
    uf_rows = _run_query(client, uf_sql, params)
    principais_paises: List[dict] = []
    for r in uf_rows:
        uf_k = str(r.get("uf_key") or "").strip()
        if not uf_k:
            continue
        principais_paises.append(
            {
                "pais": f"UF: {uf_k}",
                "valor_total": float(r.get("valor_total") or 0),
                "total_operacoes": int(r.get("total_operacoes") or 0),
            }
        )

    imp_top_sql = cte + """
    SELECT
      ANY_VALUE(razao_social) AS nome,
      cnpj,
      COALESCE(SUM(total_importacao_fob), 0) AS valor_total,
      COUNT(*) AS total_operacoes
    FROM filtered
    WHERE total_importacao_fob > 0 AND cnpj IS NOT NULL
    GROUP BY cnpj
    ORDER BY valor_total DESC
    LIMIT 10
    """
    imp_rows = _run_query(client, imp_top_sql, params)
    principais_importadores = [
        {
            "nome": str(r.get("nome") or "N/A").strip() or "N/A",
            "valor_total": float(r.get("valor_total") or 0),
            "total_operacoes": int(r.get("total_operacoes") or 0),
            "peso_total": 0.0,
        }
        for r in imp_rows
        if r.get("cnpj") is not None
    ]

    exp_top_sql = cte + """
    SELECT
      ANY_VALUE(razao_social) AS nome,
      cnpj,
      COALESCE(SUM(total_exportacao_fob), 0) AS valor_total,
      COUNT(*) AS total_operacoes
    FROM filtered
    WHERE total_exportacao_fob > 0 AND cnpj IS NOT NULL
    GROUP BY cnpj
    ORDER BY valor_total DESC
    LIMIT 10
    """
    exp_rows = _run_query(client, exp_top_sql, params)
    principais_exportadores = [
        {
            "nome": str(r.get("nome") or "N/A").strip() or "N/A",
            "valor_total": float(r.get("valor_total") or 0),
            "total_operacoes": int(r.get("total_operacoes") or 0),
            "peso_total": 0.0,
        }
        for r in exp_rows
        if r.get("cnpj") is not None
    ]

    if "export" in top_l and "import" not in top_l:
        valor_total_usd = v_exp
    elif "import" in top_l and "export" not in top_l:
        valor_total_usd = v_imp
    else:
        valor_total_usd = v_imp + v_exp
    return {
        "volume_importacoes": 0.0,
        "volume_exportacoes": 0.0,
        "valor_total_usd": valor_total_usd,
        "valor_total_importacoes": v_imp,
        "valor_total_exportacoes": v_exp,
        "quantidade_estatistica_importacoes": float(cnt_imp),
        "quantidade_estatistica_exportacoes": float(cnt_exp),
        "quantidade_estatistica_total": float(cnt_all),
        "principais_ncms": principais_ncms,
        "principais_paises": principais_paises,
        "principais_importadores": principais_importadores,
        "principais_exportadores": principais_exportadores,
        "registros_por_mes": registros_por_mes,
        "valores_por_mes": valores_por_mes,
        "pesos_por_mes": pesos_por_mes,
        "aviso_dados_sem_empresa": None,
        "fonte_dados": _fonte_dados(),
    }


@router.get("/dashboard-stats")
def get_main_dashboard_stats_bq(
    meses: int = Query(24, ge=1, le=120),
    tipo_operacao: Optional[str] = Query(None),
    ncm: Optional[str] = Query(None),
    ncms: Optional[List[str]] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    empresa_importadora: Optional[str] = Query(None),
    empresa_exportadora: Optional[str] = Query(None),
):
    """
    Estatísticas no formato do dashboard principal (cards e gráficos) via BigQuery:
    tabela única `empresas_ncm_import_export_uf` ou modelo relacionado (env COMEX_BQ_RELATED_MODEL).
    """
    ym_start, ym_end = _parse_ym_bounds(data_inicio, data_fim, meses)
    try:
        client = _get_bigquery_client()
        payload = _dashboard_stats_payload_from_bq(
            client,
            ym_start,
            ym_end,
            tipo_operacao,
            ncm,
            ncms,
            empresa_importadora,
            empresa_exportadora,
        )
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro em /api/comex-dashboard/dashboard-stats")


def _map_row_to_operacao_detalhe(row: dict, idx: int) -> dict:
    imp = float(row.get("total_importacao_fob") or 0)
    exp = float(row.get("total_exportacao_fob") or 0)
    razao = str(row.get("razao_social") or "").strip()
    cnpj = row.get("cnpj")
    ano = int(row.get("ano") or 0)
    mes = int(row.get("mes") or 0)
    uf = str(row.get("sigla_uf") or "").strip()
    id_ncm = row.get("id_ncm")
    ncm_s = re.sub(r"\D", "", str(id_ncm or ""))[:8] or str(id_ncm or "")

    if imp > 0 and exp > 0:
        tipo = "Importação" if imp >= exp else "Exportação"
    elif imp > 0:
        tipo = "Importação"
    elif exp > 0:
        tipo = "Exportação"
    else:
        tipo = "Importação"

    rid = f"{cnpj}-{ncm_s}-{ano}-{mes}-{uf}-{idx}"
    return {
        "id": rid,
        "ncm": ncm_s,
        "descricao_produto": "—",
        "tipo_operacao": tipo,
        "razao_social_importador": razao if imp > 0 else "",
        "razao_social_exportador": razao if exp > 0 else "",
        "pais_origem_destino": "—",
        "uf": uf,
        "valor_fob": imp + exp,
        "peso_liquido_kg": 0,
        "data_operacao": f"{ano:04d}-{mes:02d}-01" if ano and mes else "",
    }


@router.get("/tabela-detalhada")
def get_tabela_detalhada_bq(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    meses: int = Query(24, ge=1, le=120),
    tipo_operacao: Optional[str] = Query(None),
    ncm: Optional[str] = Query(None),
    ncms: Optional[List[str]] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    empresa_importadora: Optional[str] = Query(None),
    empresa_exportadora: Optional[str] = Query(None),
):
    """Linhas detalhadas para a tabela do dashboard principal (formato legado), só BigQuery."""
    ym_start, ym_end = _parse_ym_bounds(data_inicio, data_fim, meses)
    where_clause, params = _build_main_dashboard_where(
        ym_start,
        ym_end,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
    )
    cte = _base_filtered_cte(where_clause)
    offset = (page - 1) * page_size
    from google.cloud import bigquery

    params_page = [
        *params,
        bigquery.ScalarQueryParameter("limit_value", "INT64", page_size),
        bigquery.ScalarQueryParameter("offset_value", "INT64", offset),
    ]
    try:
        client = _get_bigquery_client()
        total_sql = cte + "SELECT COUNT(*) AS total_rows FROM filtered"
        total_rows = _run_query(client, total_sql, params)
        total = int(total_rows[0]["total_rows"]) if total_rows else 0

        data_sql = cte + """
        SELECT
          cnpj,
          razao_social,
          sigla_uf,
          id_ncm,
          ano,
          mes,
          total_importacao_fob,
          total_exportacao_fob
        FROM filtered
        ORDER BY ano DESC, mes DESC, total_importacao_fob + total_exportacao_fob DESC
        LIMIT @limit_value OFFSET @offset_value
        """
        raw = _run_query(client, data_sql, params_page)
        results = [_map_row_to_operacao_detalhe(r, i) for i, r in enumerate(raw)]
        return {
            "results": results,
            "page": page,
            "page_size": page_size,
            "total": total,
            "fonte_dados": _fonte_dados(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro em /api/comex-dashboard/tabela-detalhada")


@router.get("/autocomplete/empresa")
def autocomplete_empresa_ncm_uf(
    q: str = Query("", description="Trecho de razão social ou CNPJ"),
    tipo: str = Query(
        "",
        description="importacao | exportacao | vazio (ambos com movimento)",
    ),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Sugestões para os campos Provável Importador / Exportador, lidas da tabela
    empresas_ncm_import_export_uf no BigQuery (agrupado por CNPJ).
    """
    from google.cloud import bigquery

    q_strip = (q or "").strip()
    if len(q_strip) < 1:
        return {"items": [], "fonte_dados": _fonte_dados()}

    raw_tipo = (tipo or "").strip().lower()
    if raw_tipo in ("importacao", "importação", "import"):
        tipo_l = "importacao"
    elif raw_tipo in ("exportacao", "exportação", "export"):
        tipo_l = "exportacao"
    else:
        tipo_l = ""

    params: List[object] = [
        bigquery.ScalarQueryParameter("q_like", "STRING", f"%{q_strip}%"),
        bigquery.ScalarQueryParameter("limit_value", "INT64", limit),
    ]
    where_name = (
        "(LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@q_like) "
        "OR CAST(cnpj AS STRING) LIKE @q_like)"
    )
    # Sem HAVING: empresas só exportadoras/importadoras ainda aparecem na sugestão (ordenamos por relevância ao campo).
    if _use_related_model():
        order_by = "ANY_VALUE(razao_social) ASC"
    elif tipo_l == "importacao":
        order_by = "SUM(total_importacao_fob) DESC, SUM(total_exportacao_fob) DESC"
    elif tipo_l == "exportacao":
        order_by = "SUM(total_exportacao_fob) DESC, SUM(total_importacao_fob) DESC"
    else:
        order_by = "(SUM(total_importacao_fob) + SUM(total_exportacao_fob)) DESC"

    if _use_related_model():
        from_sql = _empresas_impex_autocomplete_sql(where_name).strip()
    else:
        tref = _get_table_ref()
        from_sql = f"""
        SELECT cnpj, razao_social, total_importacao_fob, total_exportacao_fob
        FROM {tref}
        WHERE {where_name}
        """

    sql = f"""
    SELECT
      cnpj,
      ANY_VALUE(razao_social) AS nome,
      SUM(total_importacao_fob) AS total_importacao_fob,
      SUM(total_exportacao_fob) AS total_exportacao_fob,
      COUNT(*) AS total_operacoes
    FROM ({from_sql.strip()})
    GROUP BY cnpj
    ORDER BY {order_by}
    LIMIT @limit_value
    """

    try:
        client = _get_bigquery_client()
        rows = _run_query(client, sql, params)
        items = []
        for row in rows:
            nome = str(row.get("nome") or "").strip()
            if not nome:
                continue
            items.append(
                {
                    "nome": nome,
                    "cnpj": row.get("cnpj"),
                    "total_operacoes": int(row.get("total_operacoes") or 0),
                    "valor_total": 0.0,
                    "fonte": "bigquery_empresas_ncm_uf",
                }
            )
        return {"items": items, "fonte_dados": _fonte_dados()}
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro no autocomplete empresa (BigQuery)")


def _base_filtered_cte(where_clause: str) -> str:
    if _use_related_model():
        inner = _related_joined_select_sql().strip()
        from_clause = f"({inner})"
    else:
        from_clause = _get_table_ref()
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


@router.get("/options")
def get_filter_options():
    client = _get_bigquery_client()
    try:
        if _use_related_model():
            t_imp = _bt(_table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_TABLE))
            years_query = f"SELECT DISTINCT ano FROM {t_imp} WHERE ano IS NOT NULL ORDER BY ano DESC"
            uf_query = f"SELECT DISTINCT sigla_uf FROM {t_imp} WHERE sigla_uf IS NOT NULL ORDER BY sigla_uf"
        else:
            tref = _get_table_ref()
            years_query = f"SELECT DISTINCT ano FROM {tref} WHERE ano IS NOT NULL ORDER BY ano DESC"
            uf_query = f"SELECT DISTINCT sigla_uf FROM {tref} WHERE sigla_uf IS NOT NULL ORDER BY sigla_uf"
        years = [row["ano"] for row in _run_query(client, years_query, [])]
        ufs = [row["sigla_uf"] for row in _run_query(client, uf_query, [])]
        return {
            "anos": years,
            "meses": list(range(1, 13)),
            "ufs": ufs,
            "fonte_dados": _fonte_dados(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro ao carregar opcoes de filtro")


@router.get("/data")
def get_dashboard_data(
    empresa: Optional[str] = Query(default=None),
    ano: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    uf: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort_by: str = Query(default="total_importacao_fob"),
    sort_order: str = Query(default="desc"),
):
    client = _get_bigquery_client()
    where_clause, params = _build_filters(empresa, ano, mes, uf, ncm)
    cte = _base_filtered_cte(where_clause)

    direction = "DESC" if sort_order.lower() == "desc" else "ASC"
    safe_sort_col = SORTABLE_COLUMNS.get(sort_by, "total_importacao_fob")
    offset = (page - 1) * page_size

    from google.cloud import bigquery

    params_with_page = [
        *params,
        bigquery.ScalarQueryParameter("limit_value", "INT64", page_size),
        bigquery.ScalarQueryParameter("offset_value", "INT64", offset),
    ]

    try:
        kpi_query = cte + """
        SELECT
          COALESCE(SUM(total_importacao_fob), 0) AS total_importado,
          COALESCE(SUM(total_exportacao_fob), 0) AS total_exportado,
          COALESCE(SUM(total_exportacao_fob - total_importacao_fob), 0) AS saldo_comercial,
          COUNT(DISTINCT cnpj) AS empresas_unicas
        FROM filtered
        """
        kpi_rows = _run_query(client, kpi_query, params)
        kpis = kpi_rows[0] if kpi_rows else {
            "total_importado": 0,
            "total_exportado": 0,
            "saldo_comercial": 0,
            "empresas_unicas": 0,
        }

        timeline_query = cte + """
        SELECT
          ano,
          mes,
          COALESCE(SUM(total_importacao_fob), 0) AS total_importacao_fob,
          COALESCE(SUM(total_exportacao_fob), 0) AS total_exportacao_fob
        FROM filtered
        GROUP BY ano, mes
        ORDER BY ano, mes
        """
        timeline = _run_query(client, timeline_query, params)

        top_import_query = cte + """
        SELECT
          cnpj,
          razao_social,
          COALESCE(SUM(total_importacao_fob), 0) AS total_importacao_fob
        FROM filtered
        GROUP BY cnpj, razao_social
        ORDER BY total_importacao_fob DESC
        LIMIT 10
        """
        top_import = _run_query(client, top_import_query, params)

        top_export_query = cte + """
        SELECT
          cnpj,
          razao_social,
          COALESCE(SUM(total_exportacao_fob), 0) AS total_exportacao_fob
        FROM filtered
        GROUP BY cnpj, razao_social
        ORDER BY total_exportacao_fob DESC
        LIMIT 10
        """
        top_export = _run_query(client, top_export_query, params)

        heatmap_query = cte + """
        SELECT
          sigla_uf,
          COALESCE(SUM(total_importacao_fob), 0) AS total_importacao_fob,
          COALESCE(SUM(total_exportacao_fob), 0) AS total_exportacao_fob
        FROM filtered
        GROUP BY sigla_uf
        ORDER BY sigla_uf
        """
        heatmap = _run_query(client, heatmap_query, params)

        total_query = cte + "SELECT COUNT(*) AS total_rows FROM filtered"
        total_rows = _run_query(client, total_query, params)
        total = int(total_rows[0]["total_rows"]) if total_rows else 0

        table_query = cte + f"""
        SELECT
          cnpj,
          razao_social,
          sigla_uf,
          id_ncm,
          ano,
          mes,
          total_importacao_fob,
          total_exportacao_fob,
          (total_exportacao_fob - total_importacao_fob) AS saldo
        FROM filtered
        ORDER BY {safe_sort_col} {direction}
        LIMIT @limit_value OFFSET @offset_value
        """
        rows = _run_query(client, table_query, params_with_page)

        return {
            "kpis": kpis,
            "timeline": timeline,
            "top_import": top_import,
            "top_export": top_export,
            "heatmap": heatmap,
            "table": rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            },
            "fonte_dados": _fonte_dados(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro ao montar dados do dashboard Comex")


@router.get("/export-csv")
def export_csv(
    empresa: Optional[str] = Query(default=None),
    ano: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    uf: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None),
):
    client = _get_bigquery_client()
    where_clause, params = _build_filters(empresa, ano, mes, uf, ncm)
    cte = _base_filtered_cte(where_clause)
    from google.cloud import bigquery

    params_with_limit = [*params, bigquery.ScalarQueryParameter("limit_value", "INT64", 50000)]
    query = cte + """
    SELECT
      cnpj,
      razao_social,
      sigla_uf,
      id_ncm,
      ano,
      mes,
      total_importacao_fob,
      total_exportacao_fob,
      (total_exportacao_fob - total_importacao_fob) AS saldo
    FROM filtered
    ORDER BY ano DESC, mes DESC, razao_social
    LIMIT @limit_value
    """

    try:
        rows = _run_query(client, query, params_with_limit)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "cnpj",
                "razao_social",
                "sigla_uf",
                "id_ncm",
                "ano",
                "mes",
                "total_importacao_fob",
                "total_exportacao_fob",
                "saldo",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("cnpj"),
                    row.get("razao_social"),
                    row.get("sigla_uf"),
                    row.get("id_ncm"),
                    row.get("ano"),
                    row.get("mes"),
                    row.get("total_importacao_fob"),
                    row.get("total_exportacao_fob"),
                    row.get("saldo"),
                ]
            )

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=comex_dashboard_export.csv"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        _raise_http_for_bigquery(exc, "Erro ao exportar CSV do dashboard Comex")
