"""
Rotas administrativas: sincronização BigQuery → PostgreSQL.
Proteção opcional: variável ADMIN_SYNC_TOKEN ou ADMIN_APPROVAL_TOKEN + header X-Admin-Token.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from loguru import logger
from services import sync_bigquery as syncbq
from services import bq_empresa_pipeline as bqpipe

router = APIRouter(prefix="/admin", tags=["admin-sync"])


def _require_sync_admin(request: Request) -> None:
    token = (os.getenv("ADMIN_SYNC_TOKEN") or os.getenv("ADMIN_APPROVAL_TOKEN") or "").strip()
    if not token:
        return
    hdr = (request.headers.get("X-Admin-Token") or "").strip()
    if hdr != token:
        raise HTTPException(status_code=401, detail="Token de administrador inválido ou ausente")


@router.get("/sincronizar/verificar-schema")
async def verificar_schema(request: Request):
    """Diagnóstico: anos e colunas de municipio_exportacao no BigQuery."""
    _require_sync_admin(request)
    return syncbq.verificar_municipio_exportacao()


@router.post("/sincronizar/exportadoras")
async def sinc_exportadoras(
    request: Request,
    db: Session = Depends(get_db),
    ano: int = Query(2021, ge=1997, le=2035),
):
    _require_sync_admin(request)
    try:
        return syncbq.sincronizar_empresas_exportadoras(db, ano)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar/importadoras")
async def sinc_importadoras(
    request: Request,
    db: Session = Depends(get_db),
    ano: int = Query(2021, ge=1997, le=2035),
):
    _require_sync_admin(request)
    try:
        return syncbq.sincronizar_empresas_importadoras(db, ano)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar/ncm-estado")
async def sinc_ncm_estado(
    request: Request,
    db: Session = Depends(get_db),
    ano: int = Query(2021, ge=1997, le=2035),
):
    _require_sync_admin(request)
    try:
        return syncbq.sincronizar_operacoes_ncm_estado(db, ano)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar/tudo")
async def sinc_tudo(
    request: Request,
    db: Session = Depends(get_db),
    ano: int = Query(2021, ge=1997, le=2035),
):
    _require_sync_admin(request)
    try:
        return syncbq.sincronizar_tudo(db, ano)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-empresas-bq")
async def sync_empresas_bq(
    request: Request,
    background_tasks: BackgroundTasks,
    full_refresh: bool = Query(False),
):
    """Dispara pipeline BigQuery → PostgreSQL (empresas_base + operações unificadas)."""
    _require_sync_admin(request)

    def _task():
        bqpipe.run_pipeline(full_refresh=full_refresh)

    background_tasks.add_task(_task)
    return {"ok": True, "status": "pipeline iniciado em background", "full_refresh": full_refresh}


@router.post("/run-migrations")
def run_migrations(request: Request):
    """Aplica Alembic upgrade head (protegido por INTERNAL_SECRET ou ADMIN_SYNC_TOKEN)."""
    import subprocess
    import sys
    from pathlib import Path

    _require_sync_admin(request)
    backend_dir = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=(result.stderr or result.stdout or "migration failed")[:4000],
        )
    return {"ok": True, "stdout": (result.stdout or "")[-2000:]}
