"""
Busca publicações no Diário Oficial da União (consulta in.gov.br) e extrai códigos NCM
mencionados no HTML (padrão ####.##.##).
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import quote_plus

from loguru import logger

NCM_PATTERN = re.compile(r"\b\d{4}\.\d{2}\.\d{2}\b")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def buscar_ncms_dou_por_empresa(termo: str, timeout: int = 25) -> List[str]:
    """
    Consulta o site do DOU com o termo (CNPJ ou razão social) e retorna NCMs únicos
    encontrados no HTML retornado.
    """
    termo = (termo or "").strip()
    if not termo:
        return []

    q = quote_plus(termo)
    url = (
        f"https://www.in.gov.br/consulta/-/buscar/dou?q={q}"
        f"&s=todos&exactDate=personalizado"
    )

    try:
        import requests
    except ImportError:
        logger.warning("requests não instalado — DOU indisponível")
        return []

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Falha ao consultar DOU: {}", e)
        return []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)
    except Exception:
        text = resp.text

    found = NCM_PATTERN.findall(text)
    # únicos preservando ordem
    seen = set()
    out: List[str] = []
    for n in found:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
