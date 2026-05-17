"""Lookup NCM (TEC/SISCOMEX) com cache local e sugestão opcional via IA."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from database.models import NCMDescricao, OperacaoEmpresa

NCM_JSON_URL = "https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json"

PROMPT_SUGESTAO = """
Código NCM: {ncm}
Descrição técnica oficial: {descricao_tec}
Em 2 frases, explique de forma simples e comercial qual produto
ou categoria de produto esse NCM representa, como se estivesse
descrevendo para um comprador de e-commerce. Responda em português.
"""


def normalize_ncm(code: str) -> Optional[str]:
    d = re.sub(r"\D", "", code or "")[:8]
    return d if len(d) == 8 else None


def _load_ncm_json_remote() -> Optional[dict]:
    try:
        import httpx

        with httpx.Client(timeout=60.0) as client:
            r = client.get(NCM_JSON_URL)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.warning("Falha ao baixar NCM SISCOMEX: {}", e)
    return None


def _find_in_json(data: Any, ncm8: str) -> Optional[str]:
    """Busca heurística em estrutura JSON do Siscomex."""
    if isinstance(data, dict):
        for k, v in data.items():
            if re.sub(r"\D", "", str(k)) == ncm8 and isinstance(v, str):
                return v
            found = _find_in_json(v, ncm8)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                cod = re.sub(r"\D", "", str(item.get("codigo") or item.get("Codigo") or ""))
                if cod == ncm8:
                    return (
                        item.get("descricao")
                        or item.get("Descricao")
                        or item.get("nome")
                    )
            found = _find_in_json(item, ncm8)
            if found:
                return found
    return None


def _sugestao_ia(descricao_tec: str, ncm8: str) -> Optional[str]:
    api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if not api_key or not descricao_tec:
        return None
    prompt = PROMPT_SUGESTAO.format(ncm=ncm8, descricao_tec=descricao_tec[:2000])
    try:
        if os.getenv("OPENAI_API_KEY"):
            import httpx

            with httpx.Client(timeout=45.0) as client:
                r = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                    },
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("Sugestão IA NCM indisponível: {}", e)
    return None


def lookup(db: Session, code: str, use_ia: bool = True) -> Dict[str, Any]:
    ncm8 = normalize_ncm(code)
    if not ncm8:
        return {"ncm": code, "erro": "NCM inválido (8 dígitos)"}

    cached = db.query(NCMDescricao).filter(NCMDescricao.ncm == ncm8).first()
    if cached and cached.descricao_tec:
        return {
            "ncm": ncm8,
            "descricao_tec": cached.descricao_tec,
            "sugestao_produto": cached.sugestao_produto,
            "fonte": "cache",
        }

    descricao = None
    data = _load_ncm_json_remote()
    if data:
        descricao = _find_in_json(data, ncm8)

    if not descricao:
        row = (
            db.query(OperacaoEmpresa.ncm_descricao)
            .filter(OperacaoEmpresa.ncm == ncm8, OperacaoEmpresa.ncm_descricao.isnot(None))
            .first()
        )
        if row and row[0]:
            descricao = str(row[0])

    sugestao = _sugestao_ia(descricao or "", ncm8) if use_ia else None

    if descricao or sugestao:
        rec = db.query(NCMDescricao).filter(NCMDescricao.ncm == ncm8).first()
        if not rec:
            rec = NCMDescricao(ncm=ncm8)
            db.add(rec)
        rec.descricao_tec = descricao or rec.descricao_tec
        if sugestao:
            rec.sugestao_produto = sugestao
        rec.atualizado_em = datetime.utcnow()
        db.commit()

    return {
        "ncm": ncm8,
        "descricao_tec": descricao,
        "sugestao_produto": sugestao,
        "fonte": "siscomex" if data else "operacoes_empresa",
    }


def buscar_texto(db: Session, q: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = (q or "").strip()
    if not q:
        return []
    ncm8 = normalize_ncm(q)
    if ncm8:
        return [lookup(db, ncm8, use_ia=False)]
    like = f"%{q.upper()}%"
    rows = (
        db.query(NCMDescricao)
        .filter(NCMDescricao.descricao_tec.ilike(like))
        .limit(limit)
        .all()
    )
    return [
        {
            "ncm": r.ncm,
            "descricao_tec": r.descricao_tec,
            "sugestao_produto": r.sugestao_produto,
        }
        for r in rows
    ]
