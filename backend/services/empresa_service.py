"""Lógica de negócio do painel de empresas importadoras/exportadoras."""
from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database.models import Empresa, OperacaoComex, OperacaoEmpresa, TipoOperacao


def normalize_cnpj(cnpj: str) -> str:
    d = re.sub(r"\D", "", cnpj or "")
    return d.zfill(14)[-14:] if d else ""


def get_empresa_by_cnpj(db: Session, cnpj: str) -> Optional[Empresa]:
    c14 = normalize_cnpj(cnpj)
    if not c14:
        return None
    return (
        db.query(Empresa)
        .filter(
            or_(
                Empresa.cnpj == c14,
                Empresa.cnpj == cnpj.strip(),
            )
        )
        .first()
    )


def list_empresas(
    db: Session,
    *,
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    uf: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    query = db.query(Empresa)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(Empresa.nome.ilike(like), Empresa.cnpj.ilike(like))
        )
    if uf:
        query = query.filter(Empresa.estado == uf.strip().upper()[:2])
    if tipo:
        t = tipo.strip().lower()
        if t in ("importador", "importadora"):
            query = query.filter(Empresa.tipo.in_(["importadora", "ambos"]))
        elif t in ("exportador", "exportadora"):
            query = query.filter(Empresa.tipo.in_(["exportadora", "ambos"]))

    total = query.count()
    rows = (
        query.order_by(Empresa.nome.asc())
        .offset((max(1, page) - 1) * size)
        .limit(min(size, 100))
        .all()
    )
    items = [
        {
            "cnpj": r.cnpj,
            "razao_social": r.nome,
            "uf_sede": r.estado,
            "tipo": r.tipo,
            "valor_importacao_usd": float(r.valor_importacao or 0),
            "valor_exportacao_usd": float(r.valor_exportacao or 0),
        }
        for r in rows
    ]
    return items, total


def perfil_empresa(db: Session, cnpj: str) -> Optional[Dict[str, Any]]:
    emp = get_empresa_by_cnpj(db, cnpj)
    if not emp:
        return None
    ops_q = db.query(OperacaoEmpresa).filter(OperacaoEmpresa.empresa_id == emp.id)
    if ops_q.count() == 0:
        return _perfil_from_operacoes_comex(db, emp)
    imp = (
        db.query(func.coalesce(func.sum(OperacaoEmpresa.valor_usd), 0))
        .filter(OperacaoEmpresa.empresa_id == emp.id, OperacaoEmpresa.tipo == "IMP")
        .scalar()
    )
    exp = (
        db.query(func.coalesce(func.sum(OperacaoEmpresa.valor_usd), 0))
        .filter(OperacaoEmpresa.empresa_id == emp.id, OperacaoEmpresa.tipo == "EXP")
        .scalar()
    )
    n_ncm = (
        db.query(func.count(func.distinct(OperacaoEmpresa.ncm)))
        .filter(OperacaoEmpresa.empresa_id == emp.id)
        .scalar()
    )
    n_paises = (
        db.query(func.count(func.distinct(OperacaoEmpresa.pais)))
        .filter(OperacaoEmpresa.empresa_id == emp.id, OperacaoEmpresa.pais.isnot(None))
        .scalar()
    )
    return {
        "cnpj": emp.cnpj,
        "razao_social": emp.nome,
        "uf_sede": emp.estado,
        "tipo": emp.tipo,
        "habilitada": True,
        "kpis": {
            "valor_importacao_usd": float(imp or 0),
            "valor_exportacao_usd": float(exp or 0),
            "num_ncms": int(n_ncm or 0),
            "num_paises": int(n_paises or 0),
        },
        "fonte": "operacoes_empresa",
    }


def _perfil_from_operacoes_comex(db: Session, emp: Empresa) -> Dict[str, Any]:
    c14 = normalize_cnpj(emp.cnpj or "")
    q = db.query(OperacaoComex).filter(
        or_(
            OperacaoComex.cnpj_importador == c14,
            OperacaoComex.cnpj_exportador == c14,
        )
    )
    imp = (
        db.query(func.coalesce(func.sum(OperacaoComex.valor_fob), 0))
        .filter(
            OperacaoComex.cnpj_importador == c14,
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
        )
        .scalar()
    )
    exp = (
        db.query(func.coalesce(func.sum(OperacaoComex.valor_fob), 0))
        .filter(
            OperacaoComex.cnpj_exportador == c14,
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
        )
        .scalar()
    )
    ncms = {r.ncm for r in q.with_entities(OperacaoComex.ncm).distinct().all() if r.ncm}
    paises = {
        r.pais_origem_destino
        for r in q.with_entities(OperacaoComex.pais_origem_destino).distinct().all()
        if r.pais_origem_destino
    }
    return {
        "cnpj": emp.cnpj,
        "razao_social": emp.nome,
        "uf_sede": emp.estado,
        "tipo": emp.tipo,
        "habilitada": True,
        "kpis": {
            "valor_importacao_usd": float(imp or 0),
            "valor_exportacao_usd": float(exp or 0),
            "num_ncms": len(ncms),
            "num_paises": len(paises),
        },
        "fonte": "operacoes_comex",
    }


def ncm_por_empresa(
    db: Session,
    cnpj: str,
    *,
    tipo: Optional[str] = None,
    ano: Optional[int] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    emp = get_empresa_by_cnpj(db, cnpj)
    if not emp:
        return [], 0
    q = db.query(OperacaoEmpresa).filter(OperacaoEmpresa.empresa_id == emp.id)
    if tipo and tipo.upper() in ("IMP", "EXP"):
        q = q.filter(OperacaoEmpresa.tipo == tipo.upper())
    if ano:
        q = q.filter(OperacaoEmpresa.ano == ano)
    total = q.count()
    if total == 0:
        return _ncm_from_comex(db, emp, tipo=tipo, ano=ano, page=page, size=size)
    rows = (
        q.order_by(OperacaoEmpresa.valor_usd.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return [_op_to_dict(r) for r in rows], total


def _op_to_dict(r: OperacaoEmpresa) -> Dict[str, Any]:
    return {
        "ncm": r.ncm,
        "descricao": r.ncm_descricao,
        "tipo": r.tipo,
        "valor_usd": float(r.valor_usd or 0),
        "peso_kg": float(r.peso_kg or 0),
        "ano": r.ano,
        "mes": r.mes,
    }


def _ncm_from_comex(
    db: Session,
    emp: Empresa,
    *,
    tipo: Optional[str],
    ano: Optional[int],
    page: int,
    size: int,
) -> Tuple[List[Dict[str, Any]], int]:
    c14 = normalize_cnpj(emp.cnpj or "")
    q = db.query(OperacaoComex).filter(
        or_(
            OperacaoComex.cnpj_importador == c14,
            OperacaoComex.cnpj_exportador == c14,
        )
    )
    if tipo == "IMP":
        q = q.filter(
            OperacaoComex.cnpj_importador == c14,
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
        )
    elif tipo == "EXP":
        q = q.filter(
            OperacaoComex.cnpj_exportador == c14,
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
        )
    if ano:
        q = q.filter(func.extract("year", OperacaoComex.data_operacao) == ano)
    total = q.count()
    rows = q.order_by(OperacaoComex.valor_fob.desc()).offset((page - 1) * size).limit(size).all()
    out = []
    for r in rows:
        t = "IMP" if r.tipo_operacao == TipoOperacao.IMPORTACAO else "EXP"
        out.append(
            {
                "ncm": re.sub(r"\D", "", str(r.ncm or ""))[:8],
                "descricao": r.descricao_produto,
                "tipo": t,
                "valor_usd": float(r.valor_fob or 0),
                "peso_kg": float(r.peso_liquido_kg or 0),
                "ano": r.data_operacao.year if r.data_operacao else None,
                "mes": r.data_operacao.month if r.data_operacao else None,
            }
        )
    return out, total


def estados_por_empresa(db: Session, cnpj: str, tipo: Optional[str] = None) -> Dict[str, Any]:
    emp = get_empresa_by_cnpj(db, cnpj)
    if not emp:
        return {"ufs": [], "total_usd": 0}
    q = db.query(OperacaoEmpresa).filter(OperacaoEmpresa.empresa_id == emp.id)
    if tipo and tipo.upper() in ("IMP", "EXP"):
        q = q.filter(OperacaoEmpresa.tipo == tipo.upper())
    agg: Dict[str, float] = defaultdict(float)
    for r in q.all():
        uf = r.uf_destino or r.uf_origem or emp.estado or "NA"
        agg[uf] += float(r.valor_usd or 0)
    if not agg:
        c14 = normalize_cnpj(emp.cnpj or "")
        q2 = db.query(OperacaoComex).filter(
            or_(
                OperacaoComex.cnpj_importador == c14,
                OperacaoComex.cnpj_exportador == c14,
            )
        )
        for r in q2.all():
            uf = r.uf or emp.estado or "NA"
            agg[uf] += float(r.valor_fob or 0)
    total = sum(agg.values()) or 1.0
    ufs = [
        {
            "uf": uf,
            "valor_usd": v,
            "percentual": round(100.0 * v / total, 2),
        }
        for uf, v in sorted(agg.items(), key=lambda x: -x[1])
    ]
    return {"ufs": ufs, "total_usd": total}


def timeline_empresa(db: Session, cnpj: str) -> List[Dict[str, Any]]:
    emp = get_empresa_by_cnpj(db, cnpj)
    if not emp:
        return []
    buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {"IMP": 0.0, "EXP": 0.0})
    rows = db.query(OperacaoEmpresa).filter(OperacaoEmpresa.empresa_id == emp.id).all()
    for r in rows:
        if r.ano and r.mes:
            key = f"{r.ano:04d}-{r.mes:02d}"
            buckets[key][r.tipo] += float(r.valor_usd or 0)
    if not rows:
        c14 = normalize_cnpj(emp.cnpj or "")
        for r in db.query(OperacaoComex).filter(
            or_(
                OperacaoComex.cnpj_importador == c14,
                OperacaoComex.cnpj_exportador == c14,
            )
        ).all():
            if not r.data_operacao:
                continue
            key = r.data_operacao.strftime("%Y-%m")
            t = "IMP" if r.tipo_operacao == TipoOperacao.IMPORTACAO else "EXP"
            buckets[key][t] += float(r.valor_fob or 0)
    return [
        {"periodo": k, "importacao_usd": v["IMP"], "exportacao_usd": v["EXP"]}
        for k, v in sorted(buckets.items())
    ]


def ranking_empresas(
    db: Session,
    *,
    tipo: str = "IMP",
    ano: Optional[int] = None,
    uf: Optional[str] = None,
    n: int = 10,
) -> List[Dict[str, Any]]:
    t = (tipo or "IMP").upper()
    q = (
        db.query(
            Empresa.cnpj,
            Empresa.nome,
            Empresa.estado,
            func.coalesce(func.sum(OperacaoEmpresa.valor_usd), 0).label("total"),
        )
        .join(OperacaoEmpresa, OperacaoEmpresa.empresa_id == Empresa.id)
        .filter(OperacaoEmpresa.tipo == t)
    )
    if ano:
        q = q.filter(OperacaoEmpresa.ano == ano)
    if uf:
        q = q.filter(Empresa.estado == uf.upper()[:2])
    q = q.group_by(Empresa.id, Empresa.cnpj, Empresa.nome, Empresa.estado)
    q = q.order_by(func.sum(OperacaoEmpresa.valor_usd).desc()).limit(n)
    rows = q.all()
    if rows:
        return [
            {
                "cnpj": r.cnpj,
                "razao_social": r.nome,
                "uf": r.estado,
                "valor_usd": float(r.total or 0),
            }
            for r in rows
        ]
    col = Empresa.valor_importacao if t == "IMP" else Empresa.valor_exportacao
    q2 = db.query(Empresa).order_by(col.desc()).limit(n)
    return [
        {
            "cnpj": e.cnpj,
            "razao_social": e.nome,
            "uf": e.estado,
            "valor_usd": float(e.valor_importacao if t == "IMP" else e.valor_exportacao),
        }
        for e in q2.all()
    ]
