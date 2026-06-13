"""
Serviço CNAE: carrega a tabela proprietária (NOVO CNAE.xlsx) em memória no startup
e fornece enriquecimento de códigos CNAE com hierarquia Setor→Segmento→Ramo→Categoria→Produto.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

# Caminho padrão — pode ser sobrescrito via env CNAE_XLSX_PATH
_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "NOVO_CNAE.xlsx"

# Dicionário global carregado no startup
_cnae_map: Dict[str, dict] = {}
_loaded = False


def _normalizar_cnae(codigo) -> str:
    """Converte CNAE para string de 7 dígitos sem formatação."""
    return str(codigo).strip().replace(".", "").replace("-", "").replace("/", "").lstrip("0").zfill(7)


def carregar_cnae(path: Optional[str] = None) -> int:
    """
    Lê o arquivo XLSX e popula o mapa global.
    Retorna o número de códigos carregados.
    Seguro para chamar múltiplas vezes (idempotente).
    """
    global _cnae_map, _loaded

    xlsx_path = Path(path or os.getenv("CNAE_XLSX_PATH") or _DEFAULT_PATH)
    if not xlsx_path.exists():
        logger.warning(f"⚠️  Arquivo CNAE não encontrado em {xlsx_path} — enriquecimento desabilitado.")
        _loaded = True
        return 0

    try:
        import pandas as pd

        df = pd.read_excel(xlsx_path, dtype={"CNAE": str})
        mapa: Dict[str, dict] = {}
        for _, row in df.iterrows():
            codigo = _normalizar_cnae(row.get("CNAE") or "")
            if not codigo or codigo == "0000000":
                continue
            produto = row.get("PRODUTO")
            mapa[codigo] = {
                "descricao": str(row.get("DESCRIÇÃO") or "").strip() or None,
                "setor": str(row.get("SETOR") or "").strip() or None,
                "segmento": str(row.get("SEGMENTO") or "").strip() or None,
                "ramo": str(row.get("RAMO") or "").strip() or None,
                "categoria": str(row.get("CATEGORIA") or "").strip() or None,
                "produto": str(produto).strip() if produto and str(produto).strip() not in ("nan", "None", "") else None,
            }

        _cnae_map = mapa
        _loaded = True
        logger.info(f"✅ CNAE carregado: {len(mapa)} códigos de {xlsx_path.name}")
        return len(mapa)

    except Exception as exc:
        logger.error(f"❌ Erro ao carregar CNAE: {exc}")
        _loaded = True
        return 0


def enriquecer(cnae_codigo) -> Optional[dict]:
    """
    Retorna o dict de hierarquia para o código CNAE ou None se não encontrado.
    Tenta variações com zeros à esquerda (6 e 7 dígitos).
    """
    if not _loaded:
        carregar_cnae()

    if not cnae_codigo:
        return None

    # Tentar normalização padrão (7 dígitos)
    chave7 = _normalizar_cnae(cnae_codigo)
    if chave7 in _cnae_map:
        return _cnae_map[chave7]

    # Tentar 6 dígitos (alguns CNAEs da RF têm 6 dígitos sem o dígito verificador)
    chave6 = chave7.lstrip("0").zfill(6)
    for k in (chave6, chave6.lstrip("0")):
        if k in _cnae_map:
            return _cnae_map[k]

    # Busca prefixo (primeiros 4 dígitos) como fallback
    prefixo = chave7[:4]
    for k, v in _cnae_map.items():
        if k.startswith(prefixo):
            return v

    return None


def listar_setores() -> list[str]:
    return sorted({v["setor"] for v in _cnae_map.values() if v.get("setor")})


def listar_segmentos(setor: Optional[str] = None) -> list[str]:
    return sorted({
        v["segmento"] for v in _cnae_map.values()
        if v.get("segmento") and (not setor or v.get("setor") == setor)
    })


def cnae_map() -> Dict[str, dict]:
    if not _loaded:
        carregar_cnae()
    return _cnae_map
