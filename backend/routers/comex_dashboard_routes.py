from __future__ import annotations

import csv
import io
import json
import os
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger


router = APIRouter(prefix="/api/comex-dashboard", tags=["comex-dashboard"])

TABLE_REF = "`liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf`"
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


def _base_filtered_cte(where_clause: str) -> str:
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
      FROM {TABLE_REF}
      WHERE {where_clause}
    )
    """


@router.get("/options")
def get_filter_options():
    client = _get_bigquery_client()
    try:
        years_query = f"SELECT DISTINCT ano FROM {TABLE_REF} WHERE ano IS NOT NULL ORDER BY ano DESC"
        uf_query = f"SELECT DISTINCT sigla_uf FROM {TABLE_REF} WHERE sigla_uf IS NOT NULL ORDER BY sigla_uf"
        years = [row["ano"] for row in _run_query(client, years_query, [])]
        ufs = [row["sigla_uf"] for row in _run_query(client, uf_query, [])]
        return {"anos": years, "meses": list(range(1, 13)), "ufs": ufs}
    except Exception as exc:
        logger.exception("Erro ao carregar opcoes de filtro")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar filtros: {exc}")


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
        }
    except Exception as exc:
        logger.exception("Erro ao montar dados do dashboard Comex")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar BigQuery: {exc}")


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
    except Exception as exc:
        logger.exception("Erro ao exportar CSV do dashboard Comex")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar CSV: {exc}")
