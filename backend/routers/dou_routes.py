"""Diário Oficial — /api/dou"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from database.models import DOURegistro
from services import dou_scraper

router = APIRouter(prefix="/api/dou", tags=["dou"])


def _require_internal(request: Request) -> None:
    secret = (os.getenv("INTERNAL_SECRET") or os.getenv("ADMIN_SYNC_TOKEN") or "").strip()
    if not secret:
        return
    hdr = (request.headers.get("X-Internal-Secret") or request.headers.get("X-Admin-Token") or "").strip()
    if hdr != secret:
        raise HTTPException(status_code=401, detail="Credencial interna inválida")


@router.get("")
def feed_dou(
    cnpj: Optional[str] = Query(None),
    tipo_ato: Optional[str] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(DOURegistro)
    if cnpj:
        c14 = "".join(ch for ch in cnpj if ch.isdigit())[-14:]
        q = q.filter(DOURegistro.cnpj == c14)
    if tipo_ato:
        q = q.filter(DOURegistro.tipo_ato.ilike(f"%{tipo_ato}%"))
    if data_inicio:
        q = q.filter(DOURegistro.data_pub >= data_inicio)
    if data_fim:
        q = q.filter(DOURegistro.data_pub <= data_fim)
    total = q.count()
    rows = (
        q.order_by(DOURegistro.data_pub.desc().nullslast(), DOURegistro.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    items = [
        {
            "id": r.id,
            "cnpj": r.cnpj,
            "razao_social": r.razao_social,
            "data_pub": r.data_pub.isoformat() if r.data_pub else None,
            "secao": r.secao,
            "tipo_ato": r.tipo_ato,
            "resumo": r.resumo,
            "url": r.url,
        }
        for r in rows
    ]
    return {"page": page, "size": size, "total": total, "items": items}


@router.get("/{cnpj}")
def dou_por_empresa(
    cnpj: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return feed_dou(cnpj=cnpj, page=page, size=size, db=db)


@router.post("/scrape")
async def scrape_manual(request: Request, db: Session = Depends(get_db)):
    _require_internal(request)
    stats = await dou_scraper.scrape_todas_empresas(db)
    return {"ok": True, **stats}
