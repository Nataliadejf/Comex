"""Painel de empresas importadoras/exportadoras — /api/empresas (rotas complementares ao BigQuery)."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services import empresa_service as svc

router = APIRouter(prefix="/api/empresas", tags=["empresas-painel"])


@router.get("")
def listar_empresas(
    q: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    uf: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = svc.list_empresas(db, q=q, tipo=tipo, uf=uf, page=page, size=size)
    return {"page": page, "size": size, "total": total, "items": items}


@router.get("/ranking")
def ranking(
    tipo: str = Query("IMP"),
    ano: Optional[int] = Query(None),
    uf: Optional[str] = Query(None),
    n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {"items": svc.ranking_empresas(db, tipo=tipo, ano=ano, uf=uf, n=n)}


@router.get("/comparar")
def comparar(
    cnpjs: str = Query(..., description="CNPJs separados por vírgula"),
    db: Session = Depends(get_db),
):
    lista = [c.strip() for c in cnpjs.split(",") if c.strip()]
    perfis = []
    for c in lista[:5]:
        p = svc.perfil_empresa(db, c)
        if p:
            perfis.append(p)
    return {"cnpjs": lista, "perfis": perfis}


@router.get("/{cnpj}")
def perfil(cnpj: str, db: Session = Depends(get_db)):
    p = svc.perfil_empresa(db, cnpj)
    if not p:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return p


@router.get("/{cnpj}/ncm")
def ncms_empresa(
    cnpj: str,
    tipo: Optional[str] = Query(None),
    ano: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = svc.ncm_por_empresa(db, cnpj, tipo=tipo, ano=ano, page=page, size=size)
    return {"cnpj": cnpj, "page": page, "size": size, "total": total, "items": items}


@router.get("/{cnpj}/estados")
def estados(cnpj: str, tipo: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return svc.estados_por_empresa(db, cnpj, tipo=tipo)


@router.get("/{cnpj}/timeline")
def timeline(cnpj: str, db: Session = Depends(get_db)):
    return {"cnpj": cnpj, "series": svc.timeline_empresa(db, cnpj)}
