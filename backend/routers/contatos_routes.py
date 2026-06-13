"""
Rotas /api/contatos — Empresas & Contatos
Integra: empresas_base (BQ) + Estabelecimentos_Ativos_UltimoMes (BQ) + CNAE proprietário + comex BQ.
"""
from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from services.bq_client import get_bigquery_client, run_query
from services import cnae_service

router = APIRouter(prefix="/api/contatos", tags=["contatos"])

# ── Configuração das tabelas BQ (sobrescrevíveis via env) ─────────────────────
_PROJECT = os.getenv("BQ_PROJECT", "liquid-receiver-483923-n6")
_DATASET = os.getenv("BQ_DATASET", "Projeto_Comex")

def _tbl(nome: str) -> str:
    return f"`{_PROJECT}.{_DATASET}.{nome}`"

TBL_EMPRESAS_BASE    = _tbl(os.getenv("BQ_TABLE_EMPRESAS_BASE",    "empresas_base"))
TBL_ESTAB            = _tbl(os.getenv("BQ_TABLE_ESTAB",            "Estabelecimentos_Ativos_UltimoMes"))
TBL_EMPRESAS_NCM     = _tbl(os.getenv("BQ_TABLE_EMPRESAS_NCM",     "empresas_ncm_import_export_uf"))
TBL_IMP_UF_NCM       = _tbl(os.getenv("BQ_TABLE_IMP_UF_NCM",       "importacao_uf_ncm"))
TBL_EXP_UF_NCM       = _tbl(os.getenv("BQ_TABLE_EXP_UF_NCM",       "exportacao_uf_ncm"))
TBL_NCM_TB           = _tbl(os.getenv("BQ_TABLE_NCM_TB",            "NCMImportacao_TB"))


def _apenas_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _cnpj_raiz(cnpj: str) -> str:
    """Retorna os 8 primeiros dígitos do CNPJ (raiz da matriz)."""
    return _apenas_digitos(cnpj)[:8]


def _fmt_telefone(ddd, num) -> Optional[str]:
    ddd = str(ddd or "").strip().replace(".0", "")
    num = str(num or "").strip().replace(".0", "")
    if not num or num in ("0", ""):
        return None
    num_clean = re.sub(r"\D", "", num)
    ddd_clean = re.sub(r"\D", "", ddd)
    if ddd_clean:
        return f"({ddd_clean}) {num_clean}"
    return num_clean


# ── Helpers BigQuery ──────────────────────────────────────────────────────────

def _query_autocomplete(q: str, limit: int) -> List[dict]:
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    termo = q.strip()
    apenas_num = _apenas_digitos(termo)

    # Detectar se é busca por CNPJ (8-14 dígitos)
    if len(apenas_num) >= 8:
        sql = f"""
            SELECT
                CAST(cnpj_basico AS STRING) AS cnpj,
                razao_social,
                uf_sede AS uf,
                CAST(cnae_fiscal_principal AS STRING) AS cnae_fiscal,
                NULL AS cnae_descricao
            FROM {TBL_EMPRESAS_BASE}
            WHERE CAST(cnpj_basico AS STRING) LIKE @cnpj_prefix
            ORDER BY razao_social
            LIMIT @limit
        """
        params = [
            bq_lib.ScalarQueryParameter("cnpj_prefix", "STRING", f"{apenas_num}%"),
            bq_lib.ScalarQueryParameter("limit", "INT64", limit),
        ]
    else:
        sql = f"""
            SELECT
                CAST(cnpj_basico AS STRING) AS cnpj,
                razao_social,
                uf_sede AS uf,
                CAST(cnae_fiscal_principal AS STRING) AS cnae_fiscal,
                NULL AS cnae_descricao
            FROM {TBL_EMPRESAS_BASE}
            WHERE LOWER(razao_social) LIKE LOWER(@termo)
            ORDER BY razao_social
            LIMIT @limit
        """
        params = [
            bq_lib.ScalarQueryParameter("termo", "STRING", f"%{termo}%"),
            bq_lib.ScalarQueryParameter("limit", "INT64", limit),
        ]

    rows = run_query(client, sql, params)

    # Enriquecer com descrição do CNAE proprietário
    for r in rows:
        cnae_info = cnae_service.enriquecer(r.get("cnae_fiscal"))
        if cnae_info:
            r["cnae_descricao"] = cnae_info.get("descricao") or cnae_info.get("ramo")
            r["setor"] = cnae_info.get("setor")
    return rows


def _query_perfil(cnpj_raiz: str) -> Optional[dict]:
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    sql = f"""
        SELECT
            CAST(cnpj_basico AS STRING)           AS cnpj,
            razao_social,
            natureza_juridica,
            porte,
            uf_sede,
            municipio_sede,
            situacao_cadastral                    AS situacao,
            data_abertura,
            CAST(cnae_fiscal_principal AS STRING) AS cnae_fiscal
        FROM {TBL_EMPRESAS_BASE}
        WHERE CAST(cnpj_basico AS STRING) = @cnpj_raiz
        LIMIT 1
    """
    rows = run_query(client, sql, [
        bq_lib.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz),
    ])
    return rows[0] if rows else None


def _query_estabelecimentos(cnpj_raiz: str) -> List[dict]:
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    # Tentar coluna cnpj_basico; fallback para substring do CNPJ completo
    sql = f"""
        SELECT
            CAST(cnpj AS STRING)              AS cnpj_completo,
            uf,
            municipio,
            CAST(cnae_fiscal AS STRING)       AS cnae_fiscal,
            ddd_telefone_1,
            telefone_1,
            ddd_telefone_2,
            telefone_2,
            email,
            situacao_cadastral
        FROM {TBL_ESTAB}
        WHERE CAST(cnpj_basico AS STRING) = @cnpj_raiz
           OR SUBSTR(CAST(cnpj AS STRING), 1, 8) = @cnpj_raiz
        ORDER BY uf, municipio
        LIMIT 200
    """
    try:
        rows = run_query(client, sql, [
            bq_lib.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz),
        ])
    except Exception as exc:
        logger.warning(f"Estabelecimentos BQ erro: {exc}")
        return []

    result = []
    for r in rows:
        telefone = _fmt_telefone(r.get("ddd_telefone_1"), r.get("telefone_1"))
        telefone2 = _fmt_telefone(r.get("ddd_telefone_2"), r.get("telefone_2"))
        cnae_info = cnae_service.enriquecer(r.get("cnae_fiscal"))
        result.append({
            "cnpj_completo": r.get("cnpj_completo"),
            "uf": r.get("uf"),
            "municipio": str(r.get("municipio") or "").title(),
            "cnae_fiscal": r.get("cnae_fiscal"),
            "cnae_info": cnae_info,
            "telefone1": telefone,
            "telefone2": telefone2,
            "email": str(r.get("email") or "").lower().strip() or None,
            "situacao_cadastral": str(r.get("situacao_cadastral") or "").upper(),
        })
    return result


def _query_ncms_empresa(cnpj14: str) -> List[dict]:
    """NCMs da empresa via tabela empresas_ncm_import_export_uf."""
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    sql = f"""
        SELECT
            CAST(ncm AS STRING)       AS ncm,
            tipo,
            SUM(CAST(valor_fob AS FLOAT64))  AS valor_usd,
            SUM(CAST(peso_kg   AS FLOAT64))  AS peso_kg
        FROM {TBL_EMPRESAS_NCM}
        WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') = @cnpj14
        GROUP BY ncm, tipo
        ORDER BY valor_usd DESC
        LIMIT 50
    """
    try:
        rows = run_query(client, sql, [
            bq_lib.ScalarQueryParameter("cnpj14", "STRING", cnpj14),
        ])
    except Exception as exc:
        logger.warning(f"NCMs empresa BQ erro: {exc}")
        return []

    # Enriquecer com descrição NCM se disponível
    for r in rows:
        r["valor_usd"] = float(r.get("valor_usd") or 0)
        r["peso_kg"]   = float(r.get("peso_kg") or 0)
        r["descricao"] = None  # preenchido abaixo se TBL_NCM_TB disponível
    return rows


def _query_ncm_descricoes(ncms: List[str]) -> Dict[str, str]:
    if not ncms:
        return {}
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    placeholders = ", ".join(f"'{n}'" for n in ncms[:50])
    sql = f"""
        SELECT CAST(NCM AS STRING) AS ncm, NO_NCM_POR AS descricao
        FROM {TBL_NCM_TB}
        WHERE CAST(NCM AS STRING) IN ({placeholders})
        LIMIT 50
    """
    try:
        rows = run_query(client, sql)
        return {r["ncm"]: r["descricao"] for r in rows if r.get("ncm")}
    except Exception:
        return {}


def _query_comex_por_ano(cnpj14: str) -> List[dict]:
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    sql = f"""
        SELECT
            EXTRACT(YEAR FROM PARSE_DATE('%Y-%m', CAST(ano_mes AS STRING))) AS ano,
            tipo,
            SUM(CAST(valor_fob AS FLOAT64)) AS valor
        FROM {TBL_EMPRESAS_NCM}
        WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') = @cnpj14
        GROUP BY ano, tipo
        ORDER BY ano
    """
    try:
        rows = run_query(client, sql, [
            bq_lib.ScalarQueryParameter("cnpj14", "STRING", cnpj14),
        ])
    except Exception as exc:
        logger.warning(f"Comex por ano BQ erro: {exc}")
        return []

    # Pivotar: lista de {ano, valor_importacao, valor_exportacao}
    pivot: Dict[int, dict] = {}
    for r in rows:
        ano = int(r.get("ano") or 0)
        if not ano:
            continue
        if ano not in pivot:
            pivot[ano] = {"ano": ano, "valor_importacao": 0.0, "valor_exportacao": 0.0}
        tipo = str(r.get("tipo") or "").upper()
        valor = float(r.get("valor") or 0)
        if tipo in ("IMP", "IMPORTAÇÃO", "IMPORTACAO"):
            pivot[ano]["valor_importacao"] += valor
        else:
            pivot[ano]["valor_exportacao"] += valor

    return sorted(pivot.values(), key=lambda x: x["ano"])


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/autocomplete")
async def autocomplete_empresa(
    q: str = Query(..., min_length=2, description="Razão social ou CNPJ"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Autocomplete de empresas por razão social ou CNPJ.
    Fonte: BigQuery empresas_base + enriquecimento CNAE proprietário.
    """
    try:
        items = await asyncio.to_thread(_query_autocomplete, q, limit)
        return {"items": items, "total": len(items), "fonte": "bigquery"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Autocomplete erro: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/empresa/{cnpj}")
async def perfil_empresa(cnpj: str):
    """
    Perfil completo de uma empresa:
    - Dados cadastrais (empresas_base)
    - Estabelecimentos ativos com contato (Estabelecimentos_Ativos_UltimoMes)
    - Classificação CNAE com hierarquia proprietária (SETOR→SEGMENTO→RAMO→CATEGORIA)
    - NCMs importados/exportados (empresas_ncm_import_export_uf)
    - Evolução anual comex + KPIs
    """
    digitos = _apenas_digitos(cnpj)
    if len(digitos) < 8:
        raise HTTPException(status_code=400, detail="CNPJ deve ter ao menos 8 dígitos.")

    cnpj_raiz = digitos[:8]
    cnpj14 = digitos.zfill(14)[:14]

    # ── Queries em paralelo ──────────────────────────────────────────────────
    try:
        perfil, estabelecimentos, ncms_raw, comex_por_ano = await asyncio.gather(
            asyncio.to_thread(_query_perfil, cnpj_raiz),
            asyncio.to_thread(_query_estabelecimentos, cnpj_raiz),
            asyncio.to_thread(_query_ncms_empresa, cnpj14),
            asyncio.to_thread(_query_comex_por_ano, cnpj14),
            return_exceptions=False,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Perfil empresa erro: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    if not perfil:
        raise HTTPException(
            status_code=404,
            detail=f"Empresa com CNPJ raiz {cnpj_raiz} não encontrada em empresas_base."
        )

    # ── Enriquecimento CNAE ──────────────────────────────────────────────────
    cnae_principal = str(perfil.get("cnae_fiscal") or "").strip()
    cnae_info = cnae_service.enriquecer(cnae_principal)

    # Enriquecer CNAE de cada estabelecimento
    for estab in estabelecimentos:
        if not estab.get("cnae_info"):
            estab["cnae_info"] = cnae_service.enriquecer(estab.get("cnae_fiscal"))

    # ── Descrições NCM ───────────────────────────────────────────────────────
    ncm_codigos = [str(r.get("ncm") or "") for r in ncms_raw if r.get("ncm")]
    ncm_desc_map = await asyncio.to_thread(_query_ncm_descricoes, ncm_codigos)
    for r in ncms_raw:
        r["descricao"] = ncm_desc_map.get(str(r.get("ncm") or ""), None)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_imp = sum(r["valor_usd"] for r in ncms_raw if str(r.get("tipo") or "").upper() in ("IMP", "IMPORTAÇÃO", "IMPORTACAO"))
    total_exp = sum(r["valor_usd"] for r in ncms_raw if str(r.get("tipo") or "").upper() not in ("IMP", "IMPORTAÇÃO", "IMPORTACAO"))
    paises_set = set()  # número de países — indisponível sem tabela específica
    ncms_distintos = len({str(r.get("ncm")) for r in ncms_raw if r.get("ncm")})

    # Aviso se não há dados comex
    aviso = None
    aviso_tipo = "info"
    if not ncms_raw:
        aviso = (
            "Nenhuma operação de comércio exterior encontrada para este CNPJ "
            "na tabela empresas_ncm_import_export_uf. "
            "Configure BQ_TABLE_EMPRESAS_NCM ou verifique se o CNPJ está na tabela."
        )
        aviso_tipo = "warning"

    return {
        "perfil": {
            **perfil,
            "cnae_descricao": cnae_info.get("descricao") if cnae_info else None,
        },
        "cnae_info": cnae_info,
        "estabelecimentos": estabelecimentos,
        "ncms": ncms_raw,
        "comex_por_ano": comex_por_ano,
        "kpis": {
            "valor_importacao_usd": total_imp,
            "valor_exportacao_usd": total_exp,
            "num_ncms": ncms_distintos,
            "num_paises": len(paises_set) or None,
        },
        "aviso": aviso,
        "aviso_tipo": aviso_tipo,
        "fonte": "bigquery",
    }


@router.get("/empresas")
async def listar_empresas_contatos(
    setor: Optional[str] = Query(None, description="Filtro por SETOR do CNAE (ex: INDÚSTRIA)"),
    segmento: Optional[str] = Query(None, description="Filtro por SEGMENTO"),
    uf: Optional[str] = Query(None, description="UF sede"),
    q: Optional[str] = Query(None, description="Busca por razão social"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    Lista empresas filtrada por CNAE (setor/segmento) e/ou UF.
    Útil para prospecção por segmento de mercado.
    """
    try:
        client = get_bigquery_client()
        from google.cloud import bigquery as bq_lib

        # Montar CNAEs válidos para o filtro
        cnae_filtrados: Optional[List[str]] = None
        if setor or segmento:
            mapa = cnae_service.cnae_map()
            cnae_filtrados = [
                codigo for codigo, info in mapa.items()
                if (not setor or info.get("setor") == setor.upper())
                and (not segmento or info.get("segmento") == segmento.upper())
            ]
            if not cnae_filtrados:
                return {"page": page, "size": size, "total": 0, "items": [], "filtros": {"setor": setor, "segmento": segmento}}

        conditions = []
        params = []

        if q:
            conditions.append("LOWER(e.razao_social) LIKE LOWER(@busca)")
            params.append(bq_lib.ScalarQueryParameter("busca", "STRING", f"%{q.strip()}%"))

        if uf:
            conditions.append("e.uf_sede = @uf")
            params.append(bq_lib.ScalarQueryParameter("uf", "STRING", uf.upper()))

        if cnae_filtrados:
            lista_cnae = ", ".join(f"'{c}'" for c in cnae_filtrados[:500])
            conditions.append(f"CAST(e.cnae_fiscal_principal AS STRING) IN ({lista_cnae})")

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        offset = (page - 1) * size
        params += [
            bq_lib.ScalarQueryParameter("limite", "INT64", size),
            bq_lib.ScalarQueryParameter("offset", "INT64", offset),
        ]

        sql = f"""
            SELECT
                CAST(e.cnpj_basico AS STRING)            AS cnpj,
                e.razao_social,
                e.uf_sede                                AS uf,
                CAST(e.cnae_fiscal_principal AS STRING)  AS cnae_fiscal,
                e.porte,
                e.situacao_cadastral                     AS situacao
            FROM {TBL_EMPRESAS_BASE} e
            {where_clause}
            ORDER BY e.razao_social
            LIMIT @limite OFFSET @offset
        """

        rows = await asyncio.to_thread(run_query, client, sql, params)

        # Enriquecer com CNAE proprietário
        for r in rows:
            info = cnae_service.enriquecer(r.get("cnae_fiscal"))
            r["cnae_info"] = info

        return {
            "page": page,
            "size": size,
            "total": len(rows),  # BQ não tem COUNT sem subquery extra; retorna o que veio
            "items": rows,
            "filtros": {"setor": setor, "segmento": segmento, "uf": uf, "q": q},
            "fonte": "bigquery",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Listar empresas erro: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/setores")
def listar_setores():
    """Retorna os setores disponíveis na tabela CNAE proprietária."""
    return {"setores": cnae_service.listar_setores()}


@router.get("/segmentos")
def listar_segmentos(setor: Optional[str] = Query(None)):
    """Retorna segmentos, opcionalmente filtrados por setor."""
    return {"segmentos": cnae_service.listar_segmentos(setor=setor)}
