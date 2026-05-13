#!/usr/bin/env python3
"""
Consulta uma lista de CNPJs na tabela BigQuery `empresas_base` (padrão do projeto)
ou, com --postgres, na tabela PostgreSQL `empresas`, e grava CSV.

Uso (BigQuery):
  cd backend
  python scripts/consultar_cnpjs_empresas_base_bq.py \\
    --input scripts/data/cnpjs_lista_usuario.txt \\
    --output data/cnpjs_resultado_empresas_base.csv

Requer: GOOGLE_APPLICATION_CREDENTIALS_JSON ou GOOGLE_APPLICATION_CREDENTIALS.
Opcional: COMEX_BQ_TABLE_EMPRESAS_BASE=projeto.dataset.empresas_base

Uso (PostgreSQL):
  python scripts/consultar_cnpjs_empresas_base_bq.py --postgres \\
    --input scripts/data/cnpjs_lista_usuario.txt --output data/cnpjs_resultado_pg.csv
Requer: DATABASE_URL
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_DEFAULT_TABLE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"


def _strip_bt(s: str) -> str:
    return (s or "").strip().strip("`")


def _bt(ref: str) -> str:
    r = _strip_bt(ref)
    return f"`{r}`" if r else ""


def _normalize_cnpj(s: str) -> str | None:
    d = re.sub(r"\D", "", (s or "").strip())
    if len(d) != 14:
        return None
    return d


def _load_cnpjs(path: Path) -> List[str]:
    out: List[str] = []
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        n = _normalize_cnpj(line)
        if not n:
            print(f"Aviso: linha ignorada (não é CNPJ de 14 dígitos): {line!r}", file=sys.stderr)
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _bq_client():
    from google.cloud import bigquery
    from google.oauth2 import service_account

    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_json:
        info = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=creds, project=info.get("project_id"))
    if credentials_path:
        if not os.path.exists(credentials_path):
            raise SystemExit(
                f"GOOGLE_APPLICATION_CREDENTIALS aponta para arquivo inexistente: {credentials_path}\n"
                "Corrija o caminho ou use GOOGLE_APPLICATION_CREDENTIALS_JSON com o JSON completo."
            )
        return bigquery.Client.from_service_account_json(credentials_path)
    raise SystemExit(
        "Credenciais Google não encontradas. Defina uma das opções:\n"
        "  - GOOGLE_APPLICATION_CREDENTIALS_JSON (conteúdo JSON da service account)\n"
        "  - GOOGLE_APPLICATION_CREDENTIALS (caminho para o arquivo .json)\n"
        "Ou use --postgres com DATABASE_URL para consultar a tabela local `empresas`."
    )


def query_bigquery(cnpjs: Sequence[str]) -> List[dict]:
    from google.cloud import bigquery

    if not cnpjs:
        return []

    tref = _bt(os.getenv("COMEX_BQ_TABLE_EMPRESAS_BASE") or _DEFAULT_TABLE)
    sql = f"""
    WITH input AS (
      SELECT REGEXP_REPLACE(c, r'[^0-9]', '') AS cnpj14
      FROM UNNEST(@cnpjs) AS c
    )
    SELECT
      i.cnpj14 AS cnpj_consulta,
      REGEXP_REPLACE(CAST(b.cnpj AS STRING), r'[^0-9]', '') AS cnpj_base,
      CAST(b.razao_social AS STRING) AS razao_social,
      CAST(b.sigla_uf AS STRING) AS sigla_uf,
      CAST(b.id_municipio AS STRING) AS id_municipio,
      CAST(b.id_municipio_nome AS STRING) AS id_municipio_nome,
      CASE WHEN b.cnpj IS NOT NULL THEN TRUE ELSE FALSE END AS encontrado_em_empresas_base
    FROM input AS i
    LEFT JOIN {tref} AS b
      ON REGEXP_REPLACE(CAST(b.cnpj AS STRING), r'[^0-9]', '') = i.cnpj14
    ORDER BY i.cnpj14
    """
    client = _bq_client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("cnpjs", "STRING", list(cnpjs))]
    )
    rows = client.query(sql, job_config=job_config).result()
    return [dict(row.items()) for row in rows]


def query_postgres(cnpjs: Sequence[str]) -> List[dict]:
    if not cnpjs:
        return []
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL não definido para --postgres")

    from sqlalchemy import create_engine, text

    engine = create_engine(url, pool_pre_ping=True)
    qmarks = ",".join([f":c{i}" for i in range(len(cnpjs))])
    params = {f"c{i}": cnpjs[i] for i in range(len(cnpjs))}
    sql = text(
        f"""
        SELECT
          e.cnpj AS cnpj_consulta,
          e.cnpj AS cnpj_base,
          e.nome AS razao_social,
          e.estado AS sigla_uf,
          CAST(NULL AS VARCHAR) AS id_municipio,
          CAST(NULL AS VARCHAR) AS id_municipio_nome,
          TRUE AS encontrado_em_empresas_base
        FROM empresas AS e
        WHERE e.cnpj IN ({qmarks})
        ORDER BY e.cnpj
        """
    )
    with engine.connect() as conn:
        r = conn.execute(sql, params)
        found = {row[0]: dict(row._mapping) for row in r}

    out: List[dict] = []
    for c in cnpjs:
        if c in found:
            out.append(found[c])
        else:
            out.append(
                {
                    "cnpj_consulta": c,
                    "cnpj_base": None,
                    "razao_social": None,
                    "sigla_uf": None,
                    "id_municipio": None,
                    "id_municipio_nome": None,
                    "encontrado_em_empresas_base": False,
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Consulta CNPJs em empresas_base (BQ) ou empresas (PG).")
    ap.add_argument("--input", type=Path, required=True, help="Arquivo texto com um CNPJ por linha")
    ap.add_argument("--output", type=Path, required=True, help="CSV de saída")
    ap.add_argument("--postgres", action="store_true", help="Usar PostgreSQL (tabela empresas) em vez de BigQuery")
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"Arquivo não encontrado: {args.input}", file=sys.stderr)
        return 1

    cnpjs = _load_cnpjs(args.input)
    if not cnpjs:
        print("Nenhum CNPJ válido no arquivo de entrada.", file=sys.stderr)
        return 1

    if args.postgres:
        rows = query_postgres(cnpjs)
    else:
        rows = query_bigquery(cnpjs)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cnpj_consulta",
        "cnpj_base",
        "razao_social",
        "sigla_uf",
        "id_municipio",
        "id_municipio_nome",
        "encontrado_em_empresas_base",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fieldnames})

    n_ok = sum(1 for r in rows if r.get("encontrado_em_empresas_base"))
    print(f"OK: {len(rows)} linhas → {args.output} ({n_ok} encontrados na base consultada)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
