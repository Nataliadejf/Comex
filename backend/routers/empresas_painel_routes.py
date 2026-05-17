"""Painel de empresas importadoras/exportadoras — /api/empresas (rotas complementares ao BigQuery)."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services import empresa_service as svc
from services import bq_empresa_serie as bqserie
from services import projecao_service as proj

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


@router.get("/ranking/serie")
def ranking_serie(
    tipo: str = Query("IMP"),
    ano: Optional[int] = Query(None),
    n: int = Query(10, ge=1, le=20),
    meses: int = Query(24, ge=6, le=120),
):
    """Top N empresas com série temporal (BigQuery)."""
    try:
        return bqserie.fetch_ranking_serie(tipo=tipo, top_n=n, ano=ano, meses=meses)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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


@router.get("/{cnpj}/serie-temporal")
def serie_temporal(
    cnpj: str,
    tipo: Optional[str] = Query(None, description="IMP, EXP ou vazio para ambos"),
    ano: Optional[int] = Query(None),
    meses: int = Query(36, ge=6, le=120),
    db: Session = Depends(get_db),
):
    """Série mensal IMP/EXP — BigQuery (unificado ou proxy UF) com fallback PostgreSQL."""
    try:
        payload = bqserie.fetch_serie_temporal(cnpj, tipo=tipo, ano=ano, meses=meses)
        if payload.get("serie"):
            return payload
    except Exception:
        pass
    pg_series = svc.timeline_empresa(db, cnpj)
    serie = []
    for row in pg_series:
        periodo = row.get("periodo", "")
        if tipo in (None, "", "AMBOS"):
            if row.get("importacao_usd"):
                serie.append(
                    {
                        "periodo": periodo,
                        "tipo": "IMP",
                        "valor_usd": row["importacao_usd"],
                        "peso_kg": 0,
                    }
                )
            if row.get("exportacao_usd"):
                serie.append(
                    {
                        "periodo": periodo,
                        "tipo": "EXP",
                        "valor_usd": row["exportacao_usd"],
                        "peso_kg": 0,
                    }
                )
        elif tipo.upper() == "IMP":
            serie.append(
                {"periodo": periodo, "tipo": "IMP", "valor_usd": row.get("importacao_usd", 0), "peso_kg": 0}
            )
        else:
            serie.append(
                {"periodo": periodo, "tipo": "EXP", "valor_usd": row.get("exportacao_usd", 0), "peso_kg": 0}
            )
    return {
        "cnpj": cnpj,
        "serie": serie,
        "fonte": "postgresql",
        "aviso": "Dados locais (operacoes_empresa / operacoes_comex). Rode /admin/sync-empresas-bq para sincronizar BQ.",
    }


@router.get("/{cnpj}/projecao")
def projecao_empresa(
    cnpj: str,
    tipo: str = Query("IMP"),
    n_meses: int = Query(6, ge=1, le=24),
    meses: int = Query(36, ge=12, le=120),
    db: Session = Depends(get_db),
):
    """Histórico + projeção dos próximos n_meses."""
    hist: list = []
    try:
        payload = bqserie.fetch_serie_temporal(cnpj, tipo=tipo, meses=meses)
        for s in payload.get("serie") or []:
            if s.get("tipo") == tipo.upper():
                parts = str(s.get("periodo", "")).split("-")
                if len(parts) >= 2:
                    hist.append(
                        {
                            "periodo": s["periodo"],
                            "ano": int(parts[0]),
                            "mes": int(parts[1]),
                            "valor_usd": float(s.get("valor_usd") or 0),
                        }
                    )
    except Exception:
        pass
    if not hist:
        for row in svc.timeline_empresa(db, cnpj):
            parts = str(row.get("periodo", "")).split("-")
            if len(parts) < 2:
                continue
            val = row.get("importacao_usd") if tipo.upper() == "IMP" else row.get("exportacao_usd")
            hist.append(
                {
                    "periodo": row["periodo"],
                    "ano": int(parts[0]),
                    "mes": int(parts[1]),
                    "valor_usd": float(val or 0),
                }
            )
    projecao = proj.projetar_serie(hist, n_meses=n_meses)
    return {"cnpj": cnpj, "tipo": tipo.upper(), "historico": hist, "projecao": projecao}
