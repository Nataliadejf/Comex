"""
Dashboard: consultas apenas ao PostgreSQL (dados sincronizados da BigQuery).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database import get_db
from database.models import EmpresaComex, OperacaoNCMEstado

router = APIRouter(prefix="/api/dashboard", tags=["dashboard-local"])


def _tipo_norm(tipo: Optional[str]) -> Optional[str]:
    if not tipo:
        return None
    t = tipo.strip().lower()
    if "import" in t:
        return "importacao"
    if "export" in t:
        return "exportacao"
    return None


def _filtros_operacao(q, ano: int, ncm: Optional[str], uf: Optional[str], tipo: Optional[str]):
    q = q.filter(OperacaoNCMEstado.ano == ano)
    if uf:
        q = q.filter(OperacaoNCMEstado.uf == uf.strip().upper()[:2])
    t = _tipo_norm(tipo)
    if t:
        q = q.filter(OperacaoNCMEstado.tipo_operacao == t)
    if ncm:
        digits = "".join(c for c in ncm if c.isdigit())
        if digits:
            q = q.filter(OperacaoNCMEstado.ncm.contains(digits[:8]))
        else:
            q = q.filter(OperacaoNCMEstado.ncm.contains(ncm.strip()[:8]))
    return q


def _join_empresa_match():
    return and_(
        EmpresaComex.uf == OperacaoNCMEstado.uf,
        EmpresaComex.ano_referencia == OperacaoNCMEstado.ano,
        OperacaoNCMEstado.razao_social.isnot(None),
        EmpresaComex.razao_social == OperacaoNCMEstado.razao_social,
    )


@router.get("/buscar")
async def dashboard_buscar(
    db: Session = Depends(get_db),
    ncm: Optional[str] = Query(None),
    uf: Optional[str] = Query(None, max_length=2),
    tipo: Optional[str] = Query(None),
    ano: int = Query(2021, ge=1997, le=2035),
    empresa: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    if empresa is not None and len((empresa or "").strip()) > 0 and len((empresa or "").strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Filtro empresa requer pelo menos 3 caracteres",
        )

    if empresa and len(empresa.strip()) >= 3:
        term = f"%{empresa.strip()}%"
        cq = (
            db.query(func.count(distinct(OperacaoNCMEstado.id)))
            .select_from(OperacaoNCMEstado)
            .outerjoin(EmpresaComex, _join_empresa_match())
        )
        cq = _filtros_operacao(cq, ano, ncm, uf, tipo)
        cq = cq.filter(
            or_(
                OperacaoNCMEstado.razao_social.ilike(term),
                EmpresaComex.razao_social.ilike(term),
            )
        )
        total = int(cq.scalar() or 0)
    else:
        cq = db.query(func.count(OperacaoNCMEstado.id))
        cq = _filtros_operacao(cq, ano, ncm, uf, tipo)
        total = int(cq.scalar() or 0)

    offset = (page - 1) * limit
    page_q = db.query(OperacaoNCMEstado, EmpresaComex).outerjoin(EmpresaComex, _join_empresa_match())
    page_q = _filtros_operacao(page_q, ano, ncm, uf, tipo)
    if empresa and len(empresa.strip()) >= 3:
        term = f"%{empresa.strip()}%"
        page_q = page_q.filter(
            or_(
                OperacaoNCMEstado.razao_social.ilike(term),
                EmpresaComex.razao_social.ilike(term),
            )
        )

    rows = (
        page_q.order_by(OperacaoNCMEstado.valor_fob_usd.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items: List[Dict[str, Any]] = []
    for o, e in rows:
        items.append(
            {
                "ano": o.ano,
                "mes": o.mes,
                "ncm": o.ncm,
                "descricao_ncm": o.descricao_ncm,
                "uf": o.uf,
                "tipo_operacao": o.tipo_operacao,
                "valor_fob_usd": o.valor_fob_usd,
                "quantidade_estatistica": o.quantidade_estatistica,
                "peso_kg": o.peso_kg,
                "razao_social_operacao": o.razao_social,
                "empresa_comex": (
                    None
                    if e is None
                    else {
                        "cnpj": e.cnpj,
                        "razao_social": e.razao_social,
                        "municipio": e.municipio,
                        "tipo": e.tipo,
                        "valor_fob_total": e.valor_fob_total,
                        "total_operacoes": e.total_operacoes,
                    }
                ),
            }
        )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "ano": ano,
        "fonte": "postgresql",
        "items": items,
    }
