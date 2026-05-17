"""NCM — /api/ncm"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from database.models import OperacaoEmpresa
from services import ncm_service

router = APIRouter(prefix="/api/ncm", tags=["ncm"])


@router.get("/buscar/texto")
def ncm_buscar(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    return {"q": q, "items": ncm_service.buscar_texto(db, q, limit=limit)}


@router.get("/{codigo}")
def ncm_detalhe(codigo: str, db: Session = Depends(get_db)):
    return ncm_service.lookup(db, codigo, use_ia=True)


@router.get("/{codigo}/empresas")
def empresas_por_ncm(
    codigo: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ncm8 = ncm_service.normalize_ncm(codigo)
    if not ncm8:
        return {"ncm": codigo, "items": [], "total": 0}
    q = db.query(OperacaoEmpresa).filter(OperacaoEmpresa.ncm == ncm8)
    total = q.count()
    rows = q.offset((page - 1) * size).limit(size).all()
    return {
        "ncm": ncm8,
        "page": page,
        "size": size,
        "total": total,
        "items": [
            {
                "empresa_id": r.empresa_id,
                "tipo": r.tipo,
                "valor_usd": float(r.valor_usd or 0),
                "ano": r.ano,
            }
            for r in rows
        ],
    }
