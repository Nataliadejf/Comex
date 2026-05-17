#!/usr/bin/env python3
"""
Carga inicial: operacoes_comex → empresas + operacoes_empresa.
Uso: cd backend && python scripts/importar_empresas.py [--limit N]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import SessionLocal, init_db
from database.models import Empresa, OperacaoComex, OperacaoEmpresa, TipoOperacao


def _cnpj14(s: str | None) -> str | None:
    if not s:
        return None
    d = re.sub(r"\D", "", s)[:14]
    return d if len(d) == 14 else None


def run(limit: int | None = None) -> dict:
    init_db()
    db = SessionLocal()
    stats = {"empresas": 0, "operacoes": 0, "skipped": 0}
    try:
        q = db.query(OperacaoComex)
        if limit:
            q = q.limit(limit)
        rows = q.all()
        emp_cache: dict[str, Empresa] = {}

        for op in rows:
            if op.tipo_operacao == TipoOperacao.IMPORTACAO:
                cnpj = _cnpj14(op.cnpj_importador)
                nome = (op.razao_social_importador or "").strip() or "Importador"
                tipo_op = "IMP"
            else:
                cnpj = _cnpj14(op.cnpj_exportador)
                nome = (op.razao_social_exportador or "").strip() or "Exportador"
                tipo_op = "EXP"

            if not cnpj:
                stats["skipped"] += 1
                continue

            emp = emp_cache.get(cnpj)
            if not emp:
                emp = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
                if not emp:
                    emp = Empresa(
                        cnpj=cnpj,
                        nome=nome[:255],
                        estado=(op.uf or "")[:2] or None,
                        tipo="importadora" if tipo_op == "IMP" else "exportadora",
                        valor_importacao=0.0,
                        valor_exportacao=0.0,
                    )
                    db.add(emp)
                    db.flush()
                    stats["empresas"] += 1
                emp_cache[cnpj] = emp

            ncm8 = re.sub(r"\D", "", str(op.ncm or ""))[:8]
            if len(ncm8) != 8:
                stats["skipped"] += 1
                continue

            db.add(
                OperacaoEmpresa(
                    empresa_id=emp.id,
                    tipo=tipo_op,
                    ncm=ncm8,
                    ncm_descricao=(op.descricao_produto or "")[:2000] or None,
                    uf_origem=op.uf,
                    uf_destino=op.uf,
                    pais=op.pais_origem_destino,
                    ano=op.data_operacao.year if op.data_operacao else None,
                    mes=op.data_operacao.month if op.data_operacao else None,
                    valor_usd=op.valor_fob,
                    peso_kg=op.peso_liquido_kg,
                    quantidade=int(op.quantidade_estatistica or 0) or None,
                )
            )
            stats["operacoes"] += 1

        db.commit()
    finally:
        db.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    print(run(limit=args.limit))
