from __future__ import annotations

import csv
import io
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from services import comex_empresa_stats as emp_stats


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
    """Autocomplete a partir de empresas_base (LEFT JOIN com empresasimportexport para enriquecer).

    Mantemos um LEFT JOIN para não excluir empresas ausentes em `empresasimportexport`
    (cadastro pode estar vazio ou com CNPJ em formato divergente).
    """
    t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
    return f"""
    SELECT
      CAST(b.cnpj AS STRING) AS cnpj,
      CAST(b.razao_social AS STRING) AS razao_social,
      CAST(0 AS FLOAT64) AS total_importacao_fob,
      CAST(0 AS FLOAT64) AS total_exportacao_fob
    FROM {t_base} AS b
    WHERE {where_name}
    """


def _uf_ncm_fact_subquery_sql() -> str:
    """Fato mensal UF × NCM (import + export), sem empresas.

    UNION ALL + agregação evita FULL OUTER JOIN (shuffle pesado e limite de CPU no on-demand).
    """
    t_imp = _bt(_table_env("COMEX_BQ_TABLE_IMPORT_UF_NCM", _DEFAULT_IMPORT_TABLE))
    t_exp = _bt(_table_env("COMEX_BQ_TABLE_EXPORT_UF_NCM", _DEFAULT_EXPORT_TABLE))
    return f"""
      SELECT
        ano,
        mes,
        sigla_uf,
        id_ncm,
        SUM(imp_part) AS total_importacao_fob,
        SUM(exp_part) AS total_exportacao_fob
      FROM (
        SELECT
          ano,
          mes,
          sigla_uf,
          CAST(id_ncm AS STRING) AS id_ncm,
          COALESCE(total_importacao_fob, 0) AS imp_part,
          CAST(0 AS FLOAT64) AS exp_part
        FROM {t_imp}
        UNION ALL
        SELECT
          ano,
          mes,
          sigla_uf,
          CAST(id_ncm AS STRING) AS id_ncm,
          CAST(0 AS FLOAT64),
          COALESCE(total_exportacao_fob, 0)
        FROM {t_exp}
      )
      GROUP BY ano, mes, sigla_uf, id_ncm
    """.strip()


def _query_ufs_for_company_filter(
    client,
    empresa_imp: Optional[str],
    empresa_exp: Optional[str],
) -> List[str]:
    """Resolve em uma só query as UFs (sigla) de empresas_base associadas ao filtro."""
    from google.cloud import bigquery

    likes: List[str] = []
    if empresa_imp and empresa_imp.strip():
        likes.append(empresa_imp.strip())
    if empresa_exp and empresa_exp.strip():
        likes.append(empresa_exp.strip())
    if not likes:
        return []

    t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
    where_parts: List[str] = []
    params: List[object] = []
    for i, lk in enumerate(likes):
        p = f"like_{i}"
        where_parts.append(
            f"(LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@{p}) "
            f"OR CAST(cnpj AS STRING) LIKE @{p})"
        )
        params.append(bigquery.ScalarQueryParameter(p, "STRING", f"%{lk}%"))

    sql = f"""
    SELECT DISTINCT UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf
    FROM {t_base}
    WHERE ({' OR '.join(where_parts)})
      AND sigla_uf IS NOT NULL
      AND CAST(sigla_uf AS STRING) != ''
    ORDER BY uf
    LIMIT 50
    """
    try:
        rows = _run_query(client, sql, params)
    except Exception:
        return []
    return [str(r.get("uf") or "").strip() for r in rows if r.get("uf")]


def _sql_ufs_from_empresa_like(param_name: str) -> str:
    """Subconsulta: UFs onde existe empresa (apenas `empresas_base`) com LIKE em razão social ou CNPJ.

    `empresasimportexport` pode estar vazia/divergente; usá-la como filtro obrigatório
    zerava o resultado. Mantemos só `empresas_base` para que o filtro tenha efeito.
    """
    t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
    return f"""
      SELECT DISTINCT UPPER(TRIM(CAST(b.sigla_uf AS STRING))) AS uf
      FROM {t_base} AS b
      WHERE (LOWER(CAST(b.razao_social AS STRING)) LIKE LOWER({param_name})
         OR CAST(b.cnpj AS STRING) LIKE {param_name})
        AND b.sigla_uf IS NOT NULL
    """.strip()


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


def _build_fact_filters_comex_data(
    empresa: Optional[str],
    ano: Optional[int],
    mes: Optional[int],
    uf: Optional[str],
    ncm: Optional[str],
) -> Tuple[str, List[object]]:
    """WHERE sobre fato UF×NCM (sem coluna cnpj). Filtro `empresa` vira UF via base+impex."""
    from google.cloud import bigquery

    conditions: List[str] = ["ano IS NOT NULL AND mes IS NOT NULL"]
    params: List[object] = []
    if ano is not None:
        conditions.append("ano = @fd_ano")
        params.append(bigquery.ScalarQueryParameter("fd_ano", "INT64", int(ano)))
    if mes is not None:
        conditions.append("mes = @fd_mes")
        params.append(bigquery.ScalarQueryParameter("fd_mes", "INT64", int(mes)))
    if uf:
        conditions.append("UPPER(TRIM(CAST(sigla_uf AS STRING))) = UPPER(TRIM(@fd_uf))")
        params.append(bigquery.ScalarQueryParameter("fd_uf", "STRING", uf.strip()))
    if ncm:
        conditions.append("CAST(id_ncm AS STRING) LIKE @fd_ncm")
        params.append(bigquery.ScalarQueryParameter("fd_ncm", "STRING", f"%{ncm.strip()}%"))
    ei = (empresa or "").strip()
    if ei:
        like = f"%{ei}%"
        conditions.append(
            "UPPER(TRIM(CAST(sigla_uf AS STRING))) IN ("
            + _sql_ufs_from_empresa_like("@fd_emp_like")
            + ")"
        )
        params.append(bigquery.ScalarQueryParameter("fd_emp_like", "STRING", like))
    return " AND ".join(conditions), params


def _run_query(client, query: str, params: List[object]) -> List[dict]:
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return [dict(row.items()) for row in client.query(query, job_config=job_config).result()]


def _bq_cell(v):
    """Normaliza STRUCT/ARRAY do BigQuery para dict/list aninhados."""
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return [_bq_cell(x) for x in v]
    if hasattr(v, "items"):
        try:
            return {k: _bq_cell(x) for k, x in dict(v.items()).items()}
        except Exception:
            pass
    return v


def _raise_http_for_bigquery(exc: Exception, log_message: str) -> None:
    """Registra o erro e lança HTTPException (403 em falhas típicas de IAM no BigQuery)."""
    logger.exception(log_message)
    msg = str(exc)
    low = msg.lower()
    if "exceeded resource limits" in low or "cpu seconds" in low:
        raise HTTPException(
            status_code=503,
            detail=(
                "BigQuery limitou CPU nesta consulta (volume de junção/agregação alto). "
                "Reduza o período, use filtros de UF/NCM ou particione/clusterize as tabelas de fato. "
                "Detalhe: "
                + msg[:1200]
            ),
        )
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
    *,
    imp_col: str = "total_importacao_fob",
    exp_col: str = "total_exportacao_fob",
    empresa_filter_as_uf_subquery: bool = False,
) -> Tuple[str, List[object]]:
    """Filtros do dashboard. Com empresa_filter_as_uf_subquery=True, filtro de empresa vira UF IN (subconsulta na base impex)."""
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
        conditions.append(f"{imp_col} > 0")
    elif "export" in top:
        conditions.append(f"{exp_col} > 0")

    ncm_list = _sanitize_ncm_digits_list(ncm, ncms)
    if ncm_list:
        conditions.append("REGEXP_REPLACE(CAST(id_ncm AS STRING), r'[^0-9]', '') IN UNNEST(@ncm_list)")
        params.append(bigquery.ArrayQueryParameter("ncm_list", "STRING", ncm_list))

    ei = (empresa_importadora or "").strip()
    if ei:
        like = f"%{ei}%"
        if empresa_filter_as_uf_subquery:
            conditions.append(
                "UPPER(TRIM(CAST(sigla_uf AS STRING))) IN ("
                + _sql_ufs_from_empresa_like("@like_imp")
                + ")"
            )
        else:
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
        if empresa_filter_as_uf_subquery:
            conditions.append(
                "UPPER(TRIM(CAST(sigla_uf AS STRING))) IN ("
                + _sql_ufs_from_empresa_like("@like_exp")
                + ")"
            )
        else:
            conditions.append(
                "("
                "LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@like_exp) "
                "OR CAST(cnpj AS STRING) LIKE @like_exp"
                ")"
            )
        params.append(bigquery.ScalarQueryParameter("like_exp", "STRING", like_e))

    return " AND ".join(conditions), params


def _dashboard_stats_payload_related_one_scan(
    client,
    where_clause: str,
    params: List[object],
    tipo_operacao: Optional[str],
    empresa_importadora: Optional[str] = None,
    empresa_exportadora: Optional[str] = None,
) -> Dict:
    """Um único job BigQuery no modo relacionado (evita 4–6 scans paralelos do mesmo fato)."""
    top_l = (tipo_operacao or "").strip().lower()
    if "export" in top_l and "import" not in top_l:
        ncm_order_alias = "v_exp_ncm"
    elif "import" in top_l and "export" not in top_l:
        ncm_order_alias = "v_imp_ncm"
    else:
        ncm_order_alias = "(v_imp_ncm + v_exp_ncm)"

    u_sql = _uf_ncm_fact_subquery_sql()
    combined_sql = f"""
WITH filtered AS (
  SELECT
    ano,
    mes,
    sigla_uf,
    id_ncm,
    COALESCE(total_importacao_fob, 0) AS total_importacao_fob,
    COALESCE(total_exportacao_fob, 0) AS total_exportacao_fob
  FROM ({u_sql}) AS u
  WHERE {where_clause}
)
SELECT
  (SELECT AS STRUCT
      COALESCE(SUM(total_importacao_fob), 0) AS v_imp,
      COALESCE(SUM(total_exportacao_fob), 0) AS v_exp,
      COUNTIF(total_importacao_fob > 0) AS cnt_imp_rows,
      COUNTIF(total_exportacao_fob > 0) AS cnt_exp_rows,
      COUNT(*) AS cnt_all
    FROM filtered) AS kpi,
  ARRAY(
    SELECT AS STRUCT
      FORMAT('%04d-%02d', ano, mes) AS ym,
      COUNT(*) AS registros,
      COALESCE(SUM(total_importacao_fob + total_exportacao_fob), 0) AS valor_mes
    FROM filtered
    GROUP BY ano, mes
    ORDER BY ano, mes
  ) AS monthly,
  ARRAY(
    SELECT AS STRUCT ncm, v_imp_ncm, v_exp_ncm
    FROM (
      SELECT
        REGEXP_REPLACE(CAST(id_ncm AS STRING), r'[^0-9]', '') AS ncm,
        COALESCE(SUM(total_importacao_fob), 0) AS v_imp_ncm,
        COALESCE(SUM(total_exportacao_fob), 0) AS v_exp_ncm
      FROM filtered
      GROUP BY id_ncm
    )
    ORDER BY {ncm_order_alias} DESC
    LIMIT 15
  ) AS ncms,
  ARRAY(
    SELECT AS STRUCT
      sigla_uf AS uf_key,
      COALESCE(SUM(total_importacao_fob + total_exportacao_fob), 0) AS valor_total,
      COUNT(*) AS total_operacoes
    FROM filtered
    WHERE sigla_uf IS NOT NULL AND CAST(sigla_uf AS STRING) != ''
    GROUP BY sigla_uf
    ORDER BY valor_total DESC
    LIMIT 20
  ) AS ufs
FROM (SELECT 1 AS _x)
"""
    rows = _run_query(client, combined_sql, params)
    raw = rows[0] if rows else {}
    row = {k: _bq_cell(v) for k, v in raw.items()} if raw else {}

    kpi = row.get("kpi") or {}
    monthly = row.get("monthly") or []
    ncm_rows = row.get("ncms") or []
    uf_rows = row.get("ufs") or []

    v_imp = float(kpi.get("v_imp") or 0)
    v_exp = float(kpi.get("v_exp") or 0)
    cnt_imp = int(kpi.get("cnt_imp_rows") or 0)
    cnt_exp = int(kpi.get("cnt_exp_rows") or 0)
    cnt_all = int(kpi.get("cnt_all") or 0)

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

    if "export" in top_l and "import" not in top_l:
        valor_total_usd = v_exp
    elif "import" in top_l and "export" not in top_l:
        valor_total_usd = v_imp
    else:
        valor_total_usd = v_imp + v_exp

    filtro_empresa_aplicado = bool(
        (empresa_importadora and empresa_importadora.strip())
        or (empresa_exportadora and empresa_exportadora.strip())
    )
    ufs_filtradas: List[str] = []
    aviso_msg: Optional[str] = None
    if filtro_empresa_aplicado:
        ufs_filtradas = _query_ufs_for_company_filter(
            client, empresa_importadora, empresa_exportadora
        )
        ufs_txt = ", ".join(ufs_filtradas) if ufs_filtradas else "nenhuma UF encontrada"
        aviso_msg = (
            f"Os valores abaixo NÃO são da empresa filtrada — são totais agregados "
            f"da(s) UF(s) onde a empresa está cadastrada em empresas_base: {ufs_txt}. "
            "As tabelas de fato (importacao_uf_ncm/exportacao_uf_ncm) são agregadas por "
            "UF×NCM×mês e não contêm CNPJ, então não há como apurar o valor por empresa "
            "nesta fonte. Para visão por CNPJ, é necessário ingerir uma tabela com fato "
            "por operação (ex.: NCMImportacao_TB/NCMExportacao_TB com CNPJ ou base "
            "desagregada do MDIC/Aliceweb)."
        )

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
        "filtro_empresa_aplicado": filtro_empresa_aplicado,
        "ufs_filtradas_por_empresa": ufs_filtradas,
        "aviso_dados_sem_empresa": aviso_msg,
        "fonte_dados": _fonte_dados(),
    }


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
    rel = _use_related_model()
    fonte = _fonte_dados()

    if emp_stats.empresa_filtro_ativo(empresa_importadora, empresa_exportadora):
        unified = emp_stats.try_unified_empresa_stats(
            client,
            _run_query,
            _bt,
            _table_env,
            _get_table_ref,
            _build_main_dashboard_where,
            {
                **fonte,
                "nome_logico": "empresas_ncm_import_export_uf_por_cnpj",
                "tabela_id": _strip_bt(os.getenv("COMEX_BQ_TABLE_EMPRESAS_NCM") or _DEFAULT_BQ_TABLE),
            },
            ym_start,
            ym_end,
            tipo_operacao,
            ncm,
            ncms,
            empresa_importadora,
            empresa_exportadora,
        )
        if unified:
            return unified
        cnpjs = emp_stats.resolve_cnpjs_empresa_base(
            client, _run_query, _bt, _table_env, empresa_importadora, empresa_exportadora
        )
        # Buscar CNAE e UF para contexto no frontend
        cnae_hint, uf_hint = emp_stats.resolve_cnae_empresa(
            client, _run_query, _bt, _table_env, cnpjs
        )
        # Orientação de comércio (importador/exportador) por setor CNAE
        fator_imp, fator_exp = 1.0, 1.0
        try:
            from services import cnae_service
            h = cnae_service.enriquecer_por_prefixo(cnae_hint) if cnae_hint else None
            if h:
                fator_imp, fator_exp = emp_stats.fatores_orientacao(h.get("setor"))
        except Exception:
            pass
        # Estimativa período-consciente: participação × mercado REAL da UF mês a mês
        estimativa = emp_stats.stats_estimativa_periodo(
            client, _run_query, _bt, _table_env, cnpjs, ym_start, ym_end,
            fator_imp=fator_imp, fator_exp=fator_exp,
        )
        if estimativa:
            ufs_emp = [u.get("uf") for u in estimativa.get("por_uf", []) if u.get("uf")]
            principais_ncms = emp_stats.fetch_top_ncms_ufs(
                client, _run_query, _bt, _table_env, ufs_emp,
                estimativa.get("ano_ini") or 2020, estimativa.get("ano_fim") or 2021,
            )
            payload = emp_stats.stats_payload_empresa_estimado(
                fonte, empresa_importadora, empresa_exportadora,
                estimativa, cnpjs=cnpjs, principais_ncms=principais_ncms,
                valores_por_mes=estimativa.get("valores_por_mes"),
                registros_por_mes=estimativa.get("registros_por_mes"),
                valores_imp_por_mes=estimativa.get("valores_imp_por_mes"),
                valores_exp_por_mes=estimativa.get("valores_exp_por_mes"),
            )
            payload["cnae_hint"] = cnae_hint
            payload["uf_hint"] = uf_hint
            payload["cnpj_hint"] = cnpjs[0] if cnpjs else None
            return payload
        # Sem estimativa — payload indisponível
        payload = emp_stats.stats_payload_empresa_indisponivel(
            fonte,
            empresa_importadora,
            empresa_exportadora,
            cnpjs_tentados=cnpjs,
        )
        payload["cnae_hint"] = cnae_hint
        payload["uf_hint"] = uf_hint
        payload["cnpj_hint"] = cnpjs[0] if cnpjs else None
        return payload

    where_clause, params = _build_main_dashboard_where(
        ym_start,
        ym_end,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
        imp_col="total_importacao_fob",
        exp_col="total_exportacao_fob",
        empresa_filter_as_uf_subquery=rel,
    )
    if rel:
        return _dashboard_stats_payload_related_one_scan(
            client,
            where_clause,
            params,
            tipo_operacao,
            empresa_importadora=empresa_importadora,
            empresa_exportadora=empresa_exportadora,
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
    monthly_sql = cte + """
    SELECT
      FORMAT('%04d-%02d', ano, mes) AS ym,
      COUNT(*) AS registros,
      COALESCE(SUM(total_importacao_fob + total_exportacao_fob), 0) AS valor_mes
    FROM filtered
    GROUP BY ano, mes
    ORDER BY ano, mes
    """

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

    _jobs: List[Tuple[str, str]] = [
        ("kpi", kpi_sql),
        ("monthly", monthly_sql),
        ("ncm", ncm_sql),
        ("uf", uf_sql),
        ("imp_top", imp_top_sql),
        ("exp_top", exp_top_sql),
    ]

    def _run_job(name_sql: Tuple[str, str]) -> Tuple[str, List[dict]]:
        name, sql = name_sql
        return name, _run_query(client, sql, params)

    _agg: Dict[str, List[dict]] = {}
    with ThreadPoolExecutor(max_workers=len(_jobs)) as _pool:
        _futures = [_pool.submit(_run_job, job) for job in _jobs]
        for _fu in as_completed(_futures):
            _name, _rows = _fu.result()
            _agg[_name] = _rows

    kpi = _agg.get("kpi", [])
    monthly = _agg.get("monthly", [])
    ncm_rows = _agg.get("ncm", [])
    uf_rows = _agg.get("uf", [])
    imp_rows = _agg.get("imp_top", [])
    exp_rows = _agg.get("exp_top", [])

    row0 = kpi[0] if kpi else {}
    v_imp = float(row0.get("v_imp") or 0)
    v_exp = float(row0.get("v_exp") or 0)
    cnt_imp = int(row0.get("cnt_imp_rows") or 0)
    cnt_exp = int(row0.get("cnt_exp_rows") or 0)
    cnt_all = int(row0.get("cnt_all") or 0)

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

    rid = f"{cnpj or 'agg'}-{ncm_s}-{ano}-{mes}-{uf}-{idx}"
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
    rel = _use_related_model()

    # Filtro por empresa sem comex real → detalhamento ESTIMADO por UF
    if emp_stats.empresa_filtro_ativo(empresa_importadora, empresa_exportadora):
        try:
            client = _get_bigquery_client()
            unified = emp_stats.try_unified_empresa_stats(
                client, _run_query, _bt, _table_env, _get_table_ref,
                _build_main_dashboard_where, _fonte_dados(), ym_start, ym_end,
                tipo_operacao, ncm, ncms, empresa_importadora, empresa_exportadora,
            )
            if not unified:
                cnpjs = emp_stats.resolve_cnpjs_empresa_base(
                    client, _run_query, _bt, _table_env, empresa_importadora, empresa_exportadora
                )
                cnae_hint, _uf_hint = emp_stats.resolve_cnae_empresa(
                    client, _run_query, _bt, _table_env, cnpjs
                )
                fator_imp, fator_exp = 1.0, 1.0
                try:
                    from services import cnae_service
                    h = cnae_service.enriquecer_por_prefixo(cnae_hint) if cnae_hint else None
                    if h:
                        fator_imp, fator_exp = emp_stats.fatores_orientacao(h.get("setor"))
                except Exception:
                    pass
                estimativa = emp_stats.stats_estimativa_periodo(
                    client, _run_query, _bt, _table_env, cnpjs, ym_start, ym_end,
                    fator_imp=fator_imp, fator_exp=fator_exp,
                )
                if estimativa:
                    nome_emp = (empresa_importadora or empresa_exportadora or "").strip()
                    por_uf = estimativa.get("por_uf") or []
                    todas = [
                        {
                            "cnpj": cnpjs[0] if cnpjs else None,
                            "razao_social": nome_emp,
                            "sigla_uf": u.get("uf"),
                            "id_ncm": "",
                            "ano": estimativa.get("ano_fim") or 2021,
                            "mes": 12,
                            "total_importacao_fob": float(u.get("imp") or 0),
                            "total_exportacao_fob": float(u.get("exp") or 0),
                        }
                        for u in por_uf
                    ]
                    total = len(todas)
                    offset = (page - 1) * page_size
                    pagina = todas[offset:offset + page_size]
                    results = [_map_row_to_operacao_detalhe(r, i) for i, r in enumerate(pagina)]
                    return {
                        "results": results,
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "fonte_valores": "estimado",
                        "fonte_dados": _fonte_dados(),
                    }
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"tabela-detalhada estimativa falhou: {exc}")

    where_clause, params = _build_main_dashboard_where(
        ym_start,
        ym_end,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
        imp_col="total_importacao_fob",
        exp_col="total_exportacao_fob",
        empresa_filter_as_uf_subquery=rel,
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

        if rel:
            data_sql = cte + """
        SELECT
          CAST(NULL AS STRING) AS cnpj,
          CAST(NULL AS STRING) AS razao_social,
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
        else:
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
        bigquery.ScalarQueryParameter("q_prefix", "STRING", f"{q_strip}%"),
        bigquery.ScalarQueryParameter("q_word", "STRING", f"% {q_strip}%"),
        bigquery.ScalarQueryParameter("q_raw", "STRING", q_strip),
        bigquery.ScalarQueryParameter("limit_value", "INT64", limit),
    ]
    where_name = (
        "(LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@q_like) "
        "OR CAST(cnpj AS STRING) LIKE @q_like)"
    )

    # Score: 0=exato, 1=começa-com, 2=palavra contida, 3=substring qualquer.
    # Garante que "VALE" digitado leve "VALE", "VALE S.A.", "VALE DO RIO DOCE" ao topo,
    # mesmo havendo muitas empresas "... DO VALE ..." em ordem alfabética.
    rank_case = (
        "CASE "
        "WHEN UPPER(CAST(razao_social AS STRING)) = UPPER(@q_raw) THEN 0 "
        "WHEN UPPER(CAST(razao_social AS STRING)) LIKE UPPER(@q_prefix) THEN 1 "
        "WHEN UPPER(CAST(razao_social AS STRING)) LIKE UPPER(@q_word) THEN 2 "
        "ELSE 3 END"
    )

    if _use_related_model():
        t_base = _bt(_table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE_TABLE))
        sql = f"""
        SELECT
          CAST(cnpj AS STRING) AS cnpj,
          ANY_VALUE(CAST(razao_social AS STRING)) AS nome,
          CAST(0 AS FLOAT64) AS total_importacao_fob,
          CAST(0 AS FLOAT64) AS total_exportacao_fob,
          COUNT(*) AS total_operacoes,
          MIN({rank_case}) AS rank_score,
          MIN(LENGTH(CAST(razao_social AS STRING))) AS rank_len
        FROM {t_base}
        WHERE {where_name}
        GROUP BY cnpj
        ORDER BY rank_score ASC, rank_len ASC, nome ASC
        LIMIT @limit_value
        """
    else:
        tref = _get_table_ref()
        if tipo_l == "importacao":
            order_by = "SUM(total_importacao_fob) DESC, SUM(total_exportacao_fob) DESC"
        elif tipo_l == "exportacao":
            order_by = "SUM(total_exportacao_fob) DESC, SUM(total_importacao_fob) DESC"
        else:
            order_by = "(SUM(total_importacao_fob) + SUM(total_exportacao_fob)) DESC"
        sql = f"""
        SELECT
          cnpj,
          ANY_VALUE(razao_social) AS nome,
          SUM(total_importacao_fob) AS total_importacao_fob,
          SUM(total_exportacao_fob) AS total_exportacao_fob,
          COUNT(*) AS total_operacoes,
          MIN({rank_case}) AS rank_score
        FROM {tref}
        WHERE {where_name}
        GROUP BY cnpj
        ORDER BY rank_score ASC, {order_by}
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


def _base_facts_filtered_cte(where_clause: str) -> str:
    """Apenas fato mensal UF × NCM (import + export), sem JOIN com empresas — baixo custo de CPU."""
    u_sql = _uf_ncm_fact_subquery_sql()
    return f"""
    WITH filtered AS (
      SELECT
        ano,
        mes,
        sigla_uf,
        id_ncm,
        COALESCE(total_importacao_fob, 0) AS total_importacao_fob,
        COALESCE(total_exportacao_fob, 0) AS total_exportacao_fob
      FROM ({u_sql}) AS u
      WHERE {where_clause}
    )
    """


def _base_filtered_cte(where_clause: str) -> str:
    """
    Modo relacionado: mesmo escopo que _base_facts_filtered_cte (sem explosão de linhas).
    Modo legado: lê tabela única empresas_ncm_import_export_uf.
    """
    if _use_related_model():
        return _base_facts_filtered_cte(where_clause)
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
    rel_data = _use_related_model()
    use_unified_empresa = rel_data and (empresa or "").strip()
    if use_unified_empresa:
        cnpjs = emp_stats.resolve_cnpjs_empresa_base(
            client, _run_query, _bt, _table_env, empresa, empresa
        )
        where_clause, params = _build_filters(empresa, ano, mes, uf, ncm)
        if cnpjs:
            where_clause, params = emp_stats.append_cnpj_filter(where_clause, params, cnpjs)
        cte = emp_stats.unified_filtered_cte(_get_table_ref, where_clause)
        rel_data = False
    elif rel_data:
        where_clause, params = _build_fact_filters_comex_data(empresa, ano, mes, uf, ncm)
        cte = _base_filtered_cte(where_clause)
    else:
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
        if rel_data:
            kpi_query = cte + """
        SELECT
          COALESCE(SUM(total_importacao_fob), 0) AS total_importado,
          COALESCE(SUM(total_exportacao_fob), 0) AS total_exportado,
          COALESCE(SUM(total_exportacao_fob - total_importacao_fob), 0) AS saldo_comercial,
          CAST(0 AS INT64) AS empresas_unicas
        FROM filtered
        """
        else:
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

        if rel_data:
            top_import = []
            top_export = []
        else:
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

        if rel_data:
            table_query = cte + f"""
        SELECT
          CAST(NULL AS STRING) AS cnpj,
          CAST(NULL AS STRING) AS razao_social,
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
        else:
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
    rel_csv = _use_related_model()
    if rel_csv and (empresa or "").strip():
        cnpjs = emp_stats.resolve_cnpjs_empresa_base(
            client, _run_query, _bt, _table_env, empresa, empresa
        )
        where_clause, params = _build_filters(empresa, ano, mes, uf, ncm)
        if cnpjs:
            where_clause, params = emp_stats.append_cnpj_filter(where_clause, params, cnpjs)
        cte = emp_stats.unified_filtered_cte(_get_table_ref, where_clause)
        rel_csv = False
    elif rel_csv:
        where_clause, params = _build_fact_filters_comex_data(empresa, ano, mes, uf, ncm)
        cte = _base_filtered_cte(where_clause)
    else:
        where_clause, params = _build_filters(empresa, ano, mes, uf, ncm)
        cte = _base_filtered_cte(where_clause)
    from google.cloud import bigquery

    params_with_limit = [*params, bigquery.ScalarQueryParameter("limit_value", "INT64", 50000)]
    if rel_csv:
        query = cte + """
    SELECT
      CAST(NULL AS STRING) AS cnpj,
      CAST(NULL AS STRING) AS razao_social,
      sigla_uf,
      id_ncm,
      ano,
      mes,
      total_importacao_fob,
      total_exportacao_fob,
      (total_exportacao_fob - total_importacao_fob) AS saldo
    FROM filtered
    ORDER BY ano DESC, mes DESC, sigla_uf, id_ncm
    LIMIT @limit_value
    """
    else:
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
