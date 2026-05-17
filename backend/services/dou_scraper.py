"""Scraper DOU — Querido Diário + fallback in.gov.br."""
from __future__ import annotations

import asyncio
import os
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from database.models import DOURegistro, Empresa

QUERIDO_DIARIO_URL = "https://queridodiario.ok.org.br/api/gazettes"
DELAY_SEC = float(os.getenv("DOU_SCRAPE_DELAY_SEC", "1.5"))


def inferir_tipo(texto: str) -> str:
    texto = (texto or "").lower()
    if "habilitaç" in texto:
        return "Habilitação"
    if "penalidade" in texto or "suspensão" in texto or "suspensao" in texto:
        return "Penalidade"
    if "portaria" in texto:
        return "Portaria"
    if "despacho" in texto:
        return "Despacho"
    return "Outros"


def inferir_secao(g: dict) -> str:
    return str(g.get("section") or g.get("secao") or "1")[:10]


async def scrape_empresa(cnpj: str, razao: str) -> List[dict]:
    resultados: List[dict] = []
    try:
        import httpx
    except ImportError:
        logger.warning("httpx não instalado — DOU scraper desabilitado")
        return resultados

    headers = {"User-Agent": "comex-dou-scraper/1.0"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for termo in filter(None, [cnpj, razao]):
            if not termo or len(termo.strip()) < 3:
                continue
            try:
                r = await client.get(
                    QUERIDO_DIARIO_URL,
                    params={"querystring": termo.strip(), "size": 50},
                )
                await asyncio.sleep(DELAY_SEC)
                if r.status_code != 200:
                    continue
                payload = r.json()
                for g in payload.get("gazettes", []):
                    excerpt = (g.get("excerpt") or g.get("content") or "")[:500]
                    dp = g.get("date")
                    data_pub = None
                    if dp:
                        try:
                            data_pub = date.fromisoformat(str(dp)[:10])
                        except ValueError:
                            pass
                    resultados.append(
                        {
                            "cnpj": re.sub(r"\D", "", cnpj or "")[:14] or None,
                            "razao_social": razao,
                            "data_pub": data_pub,
                            "secao": inferir_secao(g),
                            "tipo_ato": inferir_tipo(excerpt),
                            "resumo": excerpt,
                            "url": g.get("url") or g.get("pdf_url"),
                        }
                    )
            except Exception as e:
                logger.warning("Querido Diário falhou para {}: {}", termo, e)

    if not resultados and razao:
        try:
            from data_collector.diario_oficial import buscar_ncms_dou_por_empresa

            ncms = buscar_ncms_dou_por_empresa(razao)
            if ncms:
                resultados.append(
                    {
                        "cnpj": re.sub(r"\D", "", cnpj or "")[:14] or None,
                        "razao_social": razao,
                        "data_pub": date.today(),
                        "secao": "1",
                        "tipo_ato": "Outros",
                        "resumo": f"Menções a NCM no DOU: {', '.join(ncms[:10])}",
                        "url": "https://www.in.gov.br/consulta/",
                    }
                )
        except Exception:
            pass

    return resultados


def persistir_registros(db: Session, registros: List[dict]) -> int:
    n = 0
    for r in registros:
        db.add(
            DOURegistro(
                cnpj=r.get("cnpj"),
                razao_social=r.get("razao_social"),
                data_pub=r.get("data_pub"),
                secao=r.get("secao"),
                tipo_ato=r.get("tipo_ato"),
                resumo=r.get("resumo"),
                url=r.get("url"),
                scraped_at=datetime.utcnow(),
            )
        )
        n += 1
    if n:
        db.commit()
    return n


async def scrape_todas_empresas(db: Session) -> Dict[str, int]:
    batch = int(os.getenv("DOU_SCRAPE_BATCH_SIZE", "50"))
    empresas = db.query(Empresa).filter(Empresa.cnpj.isnot(None)).limit(batch).all()
    total = 0
    for emp in empresas:
        cnpj = re.sub(r"\D", "", emp.cnpj or "")
        regs = await scrape_empresa(cnpj, emp.nome or "")
        total += persistir_registros(db, regs)
    return {"empresas_processadas": len(empresas), "registros_inseridos": total}
