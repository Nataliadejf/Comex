"""Pipeline BigQuery → PostgreSQL: empresas_base + operações (tabela unificada ou proxy)."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from database import SessionLocal
from database.models import Empresa, OperacaoEmpresa
from services import bq_client as bq
from services.bq_empresa_serie import _pipeline_uses_unified, normalize_cnpj

logger = logging.getLogger(__name__)

_DEFAULT_UNIFIED = "liquid-receiver-483923-n6.Projeto_Comex.empresas_ncm_import_export_uf"
_DEFAULT_EMPRESAS_BASE = "liquid-receiver-483923-n6.Projeto_Comex.empresas_base"


def _batch_size() -> int:
    try:
        return max(500, min(10000, int(os.getenv("BQ_PIPELINE_BATCH_SIZE", "5000"))))
    except ValueError:
        return 5000


def _query_empresas_base() -> str:
    t = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_BASE", _DEFAULT_EMPRESAS_BASE))
    return f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj,
      CAST(razao_social AS STRING) AS razao_social,
      UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf
    FROM {t}
    WHERE cnpj IS NOT NULL
      AND LENGTH(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')) = 14
    """


def _query_operacoes_unified(limit: Optional[int] = None) -> str:
    t = bq.bt(bq.table_env("COMEX_BQ_TABLE_EMPRESAS_NCM", _DEFAULT_UNIFIED))
    lim = f"LIMIT {int(limit)}" if limit else ""
    return f"""
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj,
      CAST(razao_social AS STRING) AS razao_social,
      UPPER(TRIM(CAST(sigla_uf AS STRING))) AS uf_operacao,
      ano, mes,
      CAST(id_ncm AS STRING) AS ncm,
      'IMP' AS tipo,
      COALESCE(total_importacao_fob, 0) AS valor_usd,
      CAST(0 AS FLOAT64) AS peso_kg
    FROM {t}
    WHERE total_importacao_fob > 0 AND ano IS NOT NULL AND mes IS NOT NULL
    UNION ALL
    SELECT
      REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''),
      CAST(razao_social AS STRING),
      UPPER(TRIM(CAST(sigla_uf AS STRING))),
      ano, mes,
      CAST(id_ncm AS STRING),
      'EXP',
      COALESCE(total_exportacao_fob, 0),
      CAST(0 AS FLOAT64)
    FROM {t}
    WHERE total_exportacao_fob > 0 AND ano IS NOT NULL AND mes IS NOT NULL
    {lim}
    """


def _upsert_empresa(db: Session, cnpj: str, nome: str, uf: Optional[str]) -> Empresa:
    emp = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
    if emp:
        emp.nome = nome or emp.nome
        if uf:
            emp.estado = uf[:2]
        return emp
    emp = Empresa(
        nome=(nome or cnpj)[:255],
        cnpj=cnpj,
        estado=(uf or "")[:2] if uf else None,
        tipo="ambos",
    )
    db.add(emp)
    db.flush()
    return emp


def _upsert_operacao_batch(db: Session, empresa_id: int, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    values = []
    for r in rows:
        ncm = re.sub(r"\D", "", str(r.get("ncm") or ""))[:8]
        if len(ncm) < 4:
            continue
        uf = (r.get("uf_operacao") or "NA")[:2]
        values.append(
            {
                "empresa_id": empresa_id,
                "tipo": r["tipo"],
                "ncm": ncm,
                "uf_destino": uf,
                "ano": int(r["ano"]),
                "mes": int(r["mes"]),
                "valor_usd": float(r.get("valor_usd") or 0),
                "peso_kg": float(r.get("peso_kg") or 0),
            }
        )
    if not values:
        return 0
    stmt = pg_insert(OperacaoEmpresa).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_operacao_empresa_periodo",
        set_={
            "valor_usd": stmt.excluded.valor_usd,
            "peso_kg": stmt.excluded.peso_kg,
        },
    )
    try:
        db.execute(stmt)
        db.commit()
        return len(values)
    except Exception:
        db.rollback()
        for v in values:
            existing = (
                db.query(OperacaoEmpresa)
                .filter(
                    OperacaoEmpresa.empresa_id == v["empresa_id"],
                    OperacaoEmpresa.tipo == v["tipo"],
                    OperacaoEmpresa.ncm == v["ncm"],
                    OperacaoEmpresa.uf_destino == v["uf_destino"],
                    OperacaoEmpresa.ano == v["ano"],
                    OperacaoEmpresa.mes == v["mes"],
                )
                .first()
            )
            if existing:
                existing.valor_usd = v["valor_usd"]
                existing.peso_kg = v["peso_kg"]
            else:
                db.add(OperacaoEmpresa(**v))
        db.commit()
        return len(values)


def run_pipeline(
    *,
    full_refresh: bool = False,
    operacoes_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Sincroniza empresas_base e, se disponível, operações da tabela unificada BQ."""
    client = bq.get_bigquery_client()
    db = SessionLocal()
    stats = {
        "empresas_upsert": 0,
        "operacoes_upsert": 0,
        "modo": "unified" if _pipeline_uses_unified() else "empresas_only",
    }
    try:
        logger.info("Pipeline BQ empresas: iniciando (full_refresh=%s)", full_refresh)
        emp_rows = list(client.query(_query_empresas_base()).result())
        for row in emp_rows:
            cnpj = normalize_cnpj(str(row.cnpj or ""))
            if len(cnpj) != 14:
                continue
            _upsert_empresa(db, cnpj, str(row.razao_social or ""), str(row.uf or "") or None)
            stats["empresas_upsert"] += 1
        db.commit()

        if not _pipeline_uses_unified():
            logger.info("Modo related: apenas empresas_base sincronizadas (operações via API BQ ao vivo).")
            return {**stats, "ok": True}

        if full_refresh:
            db.query(OperacaoEmpresa).delete()
            db.commit()

        limit = operacoes_limit
        if os.getenv("BQ_PIPELINE_TEST_LIMIT"):
            try:
                limit = int(os.getenv("BQ_PIPELINE_TEST_LIMIT"))
            except ValueError:
                pass

        op_sql = _query_operacoes_unified(limit=limit)
        job = client.query(op_sql)
        batch: List[Dict[str, Any]] = []
        empresa_cache: Dict[str, int] = {}
        bs = _batch_size()

        for row in job.result():
            cnpj = normalize_cnpj(str(row.cnpj or ""))
            if len(cnpj) != 14:
                continue
            if cnpj not in empresa_cache:
                emp = _upsert_empresa(db, cnpj, str(row.razao_social or ""), str(row.uf_operacao or ""))
                db.commit()
                empresa_cache[cnpj] = emp.id
            batch.append(
                {
                    "empresa_id": empresa_cache[cnpj],
                    "tipo": row.tipo,
                    "ncm": row.ncm,
                    "uf_operacao": row.uf_operacao,
                    "ano": row.ano,
                    "mes": row.mes,
                    "valor_usd": row.valor_usd,
                    "peso_kg": row.peso_kg,
                }
            )
            if len(batch) >= bs:
                by_emp: Dict[int, List[Dict]] = {}
                for b in batch:
                    by_emp.setdefault(b.pop("empresa_id"), []).append(b)
                for eid, chunk in by_emp.items():
                    stats["operacoes_upsert"] += _upsert_operacao_batch(db, eid, chunk)
                batch = []

        if batch:
            by_emp = {}
            for b in batch:
                eid = b.pop("empresa_id")
                by_emp.setdefault(eid, []).append(b)
            for eid, chunk in by_emp.items():
                stats["operacoes_upsert"] += _upsert_operacao_batch(db, eid, chunk)

        logger.info("Pipeline concluído: %s", stats)
        return {**stats, "ok": True}
    except Exception as exc:
        logger.exception("Pipeline BQ empresas falhou: %s", exc)
        db.rollback()
        return {**stats, "ok": False, "erro": str(exc)}
    finally:
        db.close()
