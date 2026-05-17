"""Cliente BigQuery compartilhado (credenciais Render / local)."""
from __future__ import annotations

import json
import os
from typing import List, Optional

from fastapi import HTTPException


def strip_bt(s: str) -> str:
    return (s or "").strip().strip("`")


def bt(ref: str) -> str:
    r = strip_bt(ref)
    return f"`{r}`" if r else ""


def table_env(key: str, default_full_id: str) -> str:
    return strip_bt(os.getenv(key) or default_full_id)


def use_related_model() -> bool:
    v = (os.getenv("COMEX_BQ_RELATED_MODEL") or "").strip().lower()
    return v not in ("0", "false", "no", "off")


def get_bigquery_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dependências BigQuery indisponíveis: {exc}")

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


def run_query(client, query: str, params: Optional[List[object]] = None) -> List[dict]:
    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    return [dict(row.items()) for row in client.query(query, job_config=job_config).result()]
