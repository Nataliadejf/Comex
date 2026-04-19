"""
Rotas BigQuery (Base dos Dados), relatório estado/NCM/empresa e consulta DOU.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from database.models import EmpresaNCMEstado, OperacaoComex
from data_collector.diario_oficial import buscar_ncms_dou_por_empresa
from loguru import logger
from services import basedosdados_bigquery as bqbd

router = APIRouter(prefix="/api", tags=["bigquery-dashboard"])


def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


@router.get("/empresas/exportadoras")
async def api_empresas_exportadoras(
    ano: int = Query(2025, ge=1997, le=2035),
    limit: int = Query(100, ge=1, le=500),
):
    """Ranking exportador (BigQuery comex_stat — município / legado NO_EXP)."""
    rows = bqbd.empresas_exportadoras(ano=ano, limit=limit)
    return {"ano": ano, "fonte": "bigquery", "total": len(rows), "dados": rows}


@router.get("/empresas/importadoras")
async def api_empresas_importadoras(
    ano: int = Query(2025, ge=1997, le=2035),
    limit: int = Query(100, ge=1, le=500),
):
    rows = bqbd.empresas_importadoras(ano=ano, limit=limit)
    return {"ano": ano, "fonte": "bigquery", "total": len(rows), "dados": rows}


@router.get("/empresas/{cnpj}/ncms")
async def api_empresas_cnpj_ncms(cnpj: str, db: Session = Depends(get_db)):
    """
    NCMs distintos ligados ao CNPJ nas operações importadas no PostgreSQL (operacoes_comex).
    """
    digits = _only_digits(cnpj)
    if len(digits) < 8 or len(digits) > 14:
        raise HTTPException(status_code=400, detail="CNPJ inválido (8 a 14 dígitos)")

    c14 = digits.zfill(14)[-14:]

    q = (
        db.query(OperacaoComex.ncm)
        .filter(
            or_(
                OperacaoComex.cnpj_importador == c14,
                OperacaoComex.cnpj_exportador == c14,
            )
        )
        .distinct()
    )
    ncms = [r[0] for r in q.all() if r[0]]
    # Formatar 8 dígitos -> ####.##.##
    out = []
    for raw in ncms:
        d = re.sub(r"\D", "", str(raw))
        if len(d) >= 8:
            d = d[:8]
            fmt = f"{d[:4]}.{d[4:6]}.{d[6:8]}"
        else:
            fmt = str(raw)
        if fmt not in out:
            out.append(fmt)
    return {"cnpj": c14, "fonte": "postgresql", "total": len(out), "ncms": out}


@router.get("/diario-oficial/ncms")
async def api_dou_ncms(q: str = Query(..., min_length=2, description="CNPJ ou razão social")):
    return {"q": q, "ncms": buscar_ncms_dou_por_empresa(q)}


def _agrupar_relatorio(rows: List[EmpresaNCMEstado]) -> Dict[str, Any]:
    tree: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        uf = (r.estado or "XX").upper()[:2]
        ncm = r.ncm or "0000.00.00"
        tree[uf][ncm].append(
            {
                "nome": r.nome_empresa,
                "tipo": r.tipo,
                "valor_fob": float(r.valor_fob) if r.valor_fob is not None else None,
            }
        )
    return {k: dict(v) for k, v in tree.items()}


@router.get("/relatorio/estado-ncm-empresa")
async def api_relatorio_estado_ncm_empresa(
    ano: Optional[int] = Query(None, description="Filtra por ano gravado na tabela"),
    db: Session = Depends(get_db),
):
    q = db.query(EmpresaNCMEstado)
    if ano is not None:
        q = q.filter(EmpresaNCMEstado.ano == ano)
    rows = q.all()
    return _agrupar_relatorio(rows)


@router.post("/relatorio/popular-estado-ncm-bq")
async def api_popular_estado_ncm_bq(
    ano: int = Query(2025, ge=1997, le=2035),
    db: Session = Depends(get_db),
):
    """
    Lê agregados municipio_exportacao / municipio_importacao no BigQuery e grava em empresa_ncm_estado.
    """
    try:
        db.query(EmpresaNCMEstado).filter(EmpresaNCMEstado.ano == ano).delete(synchronize_session=False)
        now = datetime.utcnow()
        batch: List[EmpresaNCMEstado] = []

        for row in bqbd.agregado_municipio_ncm_exportacao(ano):
            vf = row.get("valor_total_fob")
            try:
                vf_f = float(vf) if vf is not None else None
            except (TypeError, ValueError):
                vf_f = None
            ncm = bqbd.sh4_para_ncm_display(str(row.get("id_sh4") or ""))
            batch.append(
                EmpresaNCMEstado(
                    nome_empresa=str(row.get("nome_empresa") or "")[:255],
                    cnpj=None,
                    tipo="exportadora",
                    estado=str(row.get("estado") or "")[:2],
                    ncm=ncm[:20],
                    valor_fob=vf_f,
                    ano=int(row.get("ano") or ano),
                    atualizado_em=now,
                )
            )

        for row in bqbd.agregado_municipio_ncm_importacao(ano):
            vf = row.get("valor_total_fob")
            try:
                vf_f = float(vf) if vf is not None else None
            except (TypeError, ValueError):
                vf_f = None
            ncm = bqbd.sh4_para_ncm_display(str(row.get("id_sh4") or ""))
            batch.append(
                EmpresaNCMEstado(
                    nome_empresa=str(row.get("nome_empresa") or "")[:255],
                    cnpj=None,
                    tipo="importadora",
                    estado=str(row.get("estado") or "")[:2],
                    ncm=ncm[:20],
                    valor_fob=vf_f,
                    ano=int(row.get("ano") or ano),
                    atualizado_em=now,
                )
            )

        for obj in batch:
            db.add(obj)
        db.commit()
        return {"ok": True, "ano": ano, "inseridos": len(batch)}
    except Exception as e:
        logger.exception("Erro ao popular empresa_ncm_estado: {}", e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
