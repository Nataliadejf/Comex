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
from services import sugestao_comex
from services import dou_scraper as _dou

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


# ── Detecção de schema BQ (cache em memória) ──────────────────────────────────
_schema_cache: Dict[str, list] = {}

def _get_columns(client, full_table_id: str) -> list:
    """Retorna lista de nomes de colunas via INFORMATION_SCHEMA (cacheado)."""
    if full_table_id in _schema_cache:
        return _schema_cache[full_table_id]
    # full_table_id ex: `project.dataset.table`
    clean = full_table_id.strip("`")
    parts = clean.split(".")
    if len(parts) != 3:
        return []
    project, dataset, table = parts
    sql = f"""
        SELECT column_name
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """
    try:
        rows = run_query(client, sql)
        cols = [r["column_name"] for r in rows]
        _schema_cache[full_table_id] = cols
        return cols
    except Exception as exc:
        logger.warning(f"Schema BQ {full_table_id}: {exc}")
        return []


def _col(cols: list, *candidates: str, default: str = "NULL") -> str:
    """Retorna o primeiro candidato presente na lista de colunas, ou default."""
    for c in candidates:
        if c in cols:
            return c
    return default


def _build_empresa_select(cols: list, alias_prefix: str = "") -> str:
    """
    Monta SELECT adaptativo baseado nas colunas disponíveis.
    Suporta variações de nome nas tabelas empresas_base e empresasimportexport.
    """
    p = alias_prefix  # ex: "e." ou ""

    cnpj_col     = _col(cols, "cnpj", "CNPJ", "cnpj_basico")
    nome_col     = _col(cols, "razao_social", "RAZAO_SOCIAL", "nome_empresa", "nome")
    uf_col       = _col(cols, "sigla_uf", "UF", "uf", "uf_sede")
    cnae_col     = _col(cols, "cnae_fiscal_principal", "cnae_fiscal", "CNAE_FISCAL")

    cnpj_expr = f"REGEXP_REPLACE(CAST({p}{cnpj_col} AS STRING), r'[^0-9]', '')" if cnpj_col != "NULL" else "NULL"
    nome_expr = f"CAST({p}{nome_col} AS STRING)" if nome_col != "NULL" else "NULL"
    uf_expr   = f"UPPER(TRIM(CAST({p}{uf_col} AS STRING)))" if uf_col != "NULL" else "NULL"
    cnae_expr = f"CAST({p}{cnae_col} AS STRING)" if cnae_col != "NULL" else "NULL"

    return f"""
        {cnpj_expr} AS cnpj,
        {nome_expr} AS razao_social,
        {uf_expr}   AS uf,
        {cnae_expr} AS cnae_fiscal
    """


# ── Helpers BigQuery ──────────────────────────────────────────────────────────

def _query_autocomplete(q: str, limit: int) -> List[dict]:
    """
    Busca em empresas_base (colunas reais: cnpj, razao_social, sigla_uf).
    Fallback para empresasimportexport se empresas_base falhar.
    """
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    termo = q.strip()
    apenas_num = _apenas_digitos(termo)

    # Descobrir colunas reais da tabela
    tbl_clean = TBL_EMPRESAS_BASE.strip("`")
    cols = _get_columns(client, tbl_clean)
    if not cols:
        # fallback sem schema: usar empresasimportexport
        cols = []

    sel = _build_empresa_select(cols)

    if len(apenas_num) >= 8:
        where = f"WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') LIKE @cnpj_prefix" if "cnpj" in cols or not cols else "WHERE TRUE"
        sql = f"SELECT {sel} FROM {TBL_EMPRESAS_BASE} {where} ORDER BY razao_social LIMIT @limit"
        params = [
            bq_lib.ScalarQueryParameter("cnpj_prefix", "STRING", f"{apenas_num}%"),
            bq_lib.ScalarQueryParameter("limit", "INT64", limit),
        ]
    else:
        sql = f"""
            SELECT {sel}
            FROM {TBL_EMPRESAS_BASE}
            WHERE LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@termo)
            ORDER BY razao_social
            LIMIT @limit
        """
        params = [
            bq_lib.ScalarQueryParameter("termo", "STRING", f"%{termo}%"),
            bq_lib.ScalarQueryParameter("limit", "INT64", limit),
        ]

    try:
        rows = run_query(client, sql, params)
    except Exception as exc:
        logger.warning(f"Autocomplete empresas_base erro ({exc}), tentando empresasimportexport")
        tbl_fallback = _tbl("empresasimportexport")
        cols_fb = _get_columns(client, tbl_fallback.strip("`"))
        sel_fb = _build_empresa_select(cols_fb)
        sql_fb = f"""
            SELECT DISTINCT {sel_fb}
            FROM {tbl_fallback}
            WHERE LOWER(CAST(razao_social AS STRING)) LIKE LOWER(@termo)
            LIMIT @limit
        """
        try:
            rows = run_query(client, sql_fb, [
                bq_lib.ScalarQueryParameter("termo", "STRING", f"%{termo}%"),
                bq_lib.ScalarQueryParameter("limit", "INT64", limit),
            ])
        except Exception as exc2:
            logger.error(f"Autocomplete fallback erro: {exc2}")
            return []

    # Normalizar chave e enriquecer com CNAE proprietário
    result = []
    for r in rows:
        r["nome"] = str(r.get("razao_social") or "").strip()
        cnae_info = cnae_service.enriquecer(r.get("cnae_fiscal"))
        if cnae_info:
            r["cnae_descricao"] = cnae_info.get("descricao") or cnae_info.get("ramo")
            r["setor"] = cnae_info.get("setor")
        result.append(r)
    return result


def _query_perfil(cnpj_raiz: str) -> Optional[dict]:
    """
    Busca perfil em empresas_base.
    Colunas reais: cnpj (14 dígitos), razao_social, sigla_uf.
    Campos opcionais tentados graciosamente.
    """
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    tbl_clean = TBL_EMPRESAS_BASE.strip("`")
    cols = _get_columns(client, tbl_clean)
    sel = _build_empresa_select(cols)

    sql = f"""
        SELECT {sel},
            NULL AS municipio_sede,
            NULL AS natureza_juridica,
            NULL AS porte,
            NULL AS situacao,
            NULL AS data_abertura
        FROM {TBL_EMPRESAS_BASE}
        WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') LIKE @cnpj_prefix
        LIMIT 1
    """
    try:
        rows = run_query(client, sql, [
            bq_lib.ScalarQueryParameter("cnpj_prefix", "STRING", f"{cnpj_raiz}%"),
        ])
        if rows:
            r = rows[0]
            return {
                "cnpj": r.get("cnpj"), "razao_social": r.get("razao_social"),
                "uf_sede": r.get("uf"), "cnae_fiscal": r.get("cnae_fiscal"),
                "municipio_sede": None, "natureza_juridica": None,
                "porte": None, "situacao": None, "data_abertura": None,
            }
    except Exception as exc:
        logger.warning(f"Perfil empresas_base erro ({exc}), tentando empresasimportexport")

    # Fallback: empresasimportexport
    tbl_fb = _tbl("empresasimportexport")
    cols_fb = _get_columns(client, tbl_fb.strip("`"))
    sel_fb = _build_empresa_select(cols_fb)
    sql_fb = f"""
        SELECT DISTINCT {sel_fb}, NULL AS municipio_sede, NULL AS natureza_juridica,
            NULL AS porte, NULL AS situacao, NULL AS data_abertura
        FROM {tbl_fb}
        WHERE REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') LIKE @cnpj_prefix
        LIMIT 1
    """
    try:
        rows = run_query(client, sql_fb, [
            bq_lib.ScalarQueryParameter("cnpj_prefix", "STRING", f"{cnpj_raiz}%"),
        ])
        if rows:
            r = rows[0]
            return {
                "cnpj": r.get("cnpj"), "razao_social": r.get("razao_social"),
                "uf_sede": r.get("uf"), "cnae_fiscal": r.get("cnae_fiscal"),
                "municipio_sede": None, "natureza_juridica": None,
                "porte": None, "situacao": None, "data_abertura": None,
            }
        return None
    except Exception as exc2:
        logger.error(f"Perfil fallback erro: {exc2}")
        return None


def _query_estabelecimentos(cnpj_raiz: str) -> List[dict]:
    """
    Busca estabelecimentos ativos.
    Layout RF: cnpj (14 dígitos completo), sigla_uf, nome_municipio,
               cnae_fiscal_principal, ddd_1, telefone_1, email, situacao_cadastral.
    Tenta múltiplas variações de nomes de colunas.
    """
    client = get_bigquery_client()
    from google.cloud import bigquery as bq_lib

    sql = f"""
        SELECT
            REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '')       AS cnpj_completo,
            COALESCE(CAST(sigla_uf AS STRING), CAST(uf AS STRING))     AS uf,
            COALESCE(
                CAST(nome_municipio AS STRING),
                CAST(municipio AS STRING)
            )                                                           AS municipio,
            COALESCE(
                CAST(cnae_fiscal_principal AS STRING),
                CAST(cnae_fiscal AS STRING)
            )                                                           AS cnae_fiscal,
            CAST(ddd_1 AS STRING)         AS ddd_telefone_1,
            CAST(telefone_1 AS STRING)    AS telefone_1,
            CAST(ddd_2 AS STRING)         AS ddd_telefone_2,
            CAST(telefone_2 AS STRING)    AS telefone_2,
            LOWER(CAST(email AS STRING))  AS email,
            UPPER(CAST(situacao_cadastral AS STRING)) AS situacao_cadastral
        FROM {TBL_ESTAB}
        WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 8) = @cnpj_raiz
        ORDER BY uf, municipio
        LIMIT 200
    """
    try:
        rows = run_query(client, sql, [
            bq_lib.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz),
        ])
    except Exception as exc:
        logger.warning(f"Estabelecimentos BQ erro (layout v1): {exc}")
        # Fallback minimalista — apenas colunas garantidas
        sql2 = f"""
            SELECT
                REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', '') AS cnpj_completo,
                NULL AS uf, NULL AS municipio, NULL AS cnae_fiscal,
                NULL AS ddd_telefone_1, NULL AS telefone_1,
                NULL AS ddd_telefone_2, NULL AS telefone_2,
                NULL AS email, NULL AS situacao_cadastral
            FROM {TBL_ESTAB}
            WHERE SUBSTR(REGEXP_REPLACE(CAST(cnpj AS STRING), r'[^0-9]', ''), 1, 8) = @cnpj_raiz
            LIMIT 200
        """
        try:
            rows = run_query(client, sql2, [
                bq_lib.ScalarQueryParameter("cnpj_raiz", "STRING", cnpj_raiz),
            ])
        except Exception as exc2:
            logger.error(f"Estabelecimentos fallback erro: {exc2}")
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extrair_contato_matriz(estabelecimentos: List[dict], cnpj_raiz: str) -> Optional[dict]:
    """
    Retorna o contato da matriz (CNPJ terminado em 0001 ou o primeiro da lista).
    Prioriza estabelecimento com CNPJ XX.XXX.XXX/0001-XX.
    """
    if not estabelecimentos:
        return None
    # Tentar encontrar a matriz (ordem 0001)
    for e in estabelecimentos:
        cnpj_full = str(e.get("cnpj_completo") or "").replace(".", "").replace("/", "").replace("-", "")
        if len(cnpj_full) == 14 and cnpj_full[8:12] == "0001":
            return _montar_contato(e)
    # Fallback: primeiro estabelecimento
    return _montar_contato(estabelecimentos[0])


def _montar_contato(e: dict) -> dict:
    return {
        "cnpj_completo": e.get("cnpj_completo"),
        "uf": e.get("uf"),
        "municipio": e.get("municipio"),
        "cnae_fiscal": e.get("cnae_fiscal"),
        "telefone1": e.get("telefone1"),
        "telefone2": e.get("telefone2"),
        "email": e.get("email"),
        "situacao_cadastral": e.get("situacao_cadastral"),
        "cnae_info": e.get("cnae_info"),
    }


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

    if not perfil and not estabelecimentos:
        raise HTTPException(
            status_code=404,
            detail=f"Empresa com CNPJ raiz {cnpj_raiz} não encontrada."
        )

    # ── Enriquecimento CNAE ──────────────────────────────────────────────────
    cnae_principal = str((perfil or {}).get("cnae_fiscal") or "").strip()
    # Complementar CNAE a partir do estabelecimento matriz se não veio do perfil
    if not cnae_principal and estabelecimentos:
        cnae_principal = str(estabelecimentos[0].get("cnae_fiscal") or "").strip()

    cnae_info = cnae_service.enriquecer(cnae_principal) if cnae_principal else None

    # Enriquecer CNAE de cada estabelecimento
    for estab in estabelecimentos:
        if not estab.get("cnae_info"):
            estab["cnae_info"] = cnae_service.enriquecer(estab.get("cnae_fiscal"))

    # ── Contato Receita Federal — extrair da matriz (estabelecimento 0001) ───
    contato_rf = _extrair_contato_matriz(estabelecimentos, cnpj_raiz)

    # ── Descrições NCM ───────────────────────────────────────────────────────
    ncm_codigos = [str(r.get("ncm") or "") for r in ncms_raw if r.get("ncm")]
    ncm_desc_map = await asyncio.to_thread(_query_ncm_descricoes, ncm_codigos)
    for r in ncms_raw:
        r["descricao"] = ncm_desc_map.get(str(r.get("ncm") or ""), None)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_imp = sum(r["valor_usd"] for r in ncms_raw if str(r.get("tipo") or "").upper() in ("IMP", "IMPORTAÇÃO", "IMPORTACAO"))
    total_exp = sum(r["valor_usd"] for r in ncms_raw if str(r.get("tipo") or "").upper() not in ("IMP", "IMPORTAÇÃO", "IMPORTACAO"))
    ncms_distintos = len({str(r.get("ncm")) for r in ncms_raw if r.get("ncm")})
    ufs_atuacao = sorted({str(e.get("uf") or "") for e in estabelecimentos if e.get("uf")})

    # Aviso se não há dados comex
    aviso = None
    aviso_tipo = "info"
    tem_comex = bool(ncms_raw)
    if not tem_comex:
        aviso = (
            "Nenhuma operação de comércio exterior encontrada para este CNPJ "
            "na base disponível. Você pode verificar a potencial viabilidade "
            "na aba Sugestão Comex."
        )
        aviso_tipo = "warning"

    perfil_out = {**(perfil or {})}
    perfil_out["cnae_descricao"] = cnae_info.get("descricao") if cnae_info else None
    # Complementar dados do perfil a partir dos estabelecimentos quando empresas_base não os tem
    if not perfil_out.get("uf_sede") and estabelecimentos:
        perfil_out["uf_sede"] = estabelecimentos[0].get("uf")
    if not perfil_out.get("municipio_sede") and estabelecimentos:
        perfil_out["municipio_sede"] = estabelecimentos[0].get("municipio")
    if not perfil_out.get("situacao") and estabelecimentos:
        perfil_out["situacao"] = estabelecimentos[0].get("situacao_cadastral")

    return {
        "perfil": perfil_out,
        "cnae_info": cnae_info,
        "contato_rf": contato_rf,
        "estabelecimentos": estabelecimentos,
        "ncms": ncms_raw,
        "comex_por_ano": comex_por_ano,
        "kpis": {
            "valor_importacao_usd": total_imp,
            "valor_exportacao_usd": total_exp,
            "num_ncms": ncms_distintos,
            "num_paises": None,
            "num_estabelecimentos": len(estabelecimentos),
            "ufs_atuacao": ufs_atuacao,
        },
        "tem_comex": tem_comex,
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
            conditions.append("UPPER(TRIM(CAST(e.sigla_uf AS STRING))) = @uf")
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
                REGEXP_REPLACE(CAST(e.cnpj AS STRING), r'[^0-9]', '') AS cnpj,
                CAST(e.razao_social AS STRING)                          AS razao_social,
                UPPER(TRIM(CAST(e.sigla_uf AS STRING)))                 AS uf,
                NULL AS cnae_fiscal,
                NULL AS porte,
                NULL AS situacao
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


@router.get("/empresa/{cnpj}/sugestao")
async def sugestao_comex_empresa(cnpj: str):
    """
    Sugestão estatística de potencial comex para uma empresa.
    Baseado em empresas do mesmo CNAE/segmento que já operam no comércio exterior.
    Útil para empresas sem histórico na base, como análise de viabilidade.
    """
    digitos = _apenas_digitos(cnpj)
    if len(digitos) < 8:
        raise HTTPException(status_code=400, detail="CNPJ deve ter ao menos 8 dígitos.")

    cnpj_raiz = digitos[:8]

    # Buscar CNAE e UF da empresa
    try:
        perfil = await asyncio.to_thread(_query_perfil, cnpj_raiz)
        estabelecimentos = await asyncio.to_thread(_query_estabelecimentos, cnpj_raiz)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    cnae = None
    uf = None
    if perfil:
        cnae = str(perfil.get("cnae_fiscal") or "").strip()
        uf = str(perfil.get("uf_sede") or "").strip() or None
    if not cnae and estabelecimentos:
        cnae = str(estabelecimentos[0].get("cnae_fiscal") or "").strip()
        uf = str(estabelecimentos[0].get("uf") or "").strip() or None

    if not cnae:
        return {"tem_sugestao": False, "motivo": "CNAE não encontrado para esta empresa."}

    cnae_info = cnae_service.enriquecer(cnae)
    try:
        client = get_bigquery_client()
        sugestao = await asyncio.to_thread(
            sugestao_comex.sugerir_por_cnae,
            client, run_query, cnae, uf, 3, 50
        )
    except Exception as exc:
        logger.warning(f"Sugestão comex erro: {exc}")
        sugestao = {"tem_sugestao": False, "motivo": str(exc)}

    # Enriquecer NCMs típicos com descrição
    ncms_tipicos = sugestao.get("ncms_tipicos", [])
    if ncms_tipicos:
        codigos = [r["ncm"] for r in ncms_tipicos if r.get("ncm")]
        desc_map = await asyncio.to_thread(_query_ncm_descricoes, codigos)
        for r in ncms_tipicos:
            r["descricao"] = desc_map.get(str(r.get("ncm") or ""), None)

    return {
        **sugestao,
        "cnpj_raiz": cnpj_raiz,
        "cnae": cnae,
        "cnae_info": cnae_info,
        "uf_referencia": uf,
    }


@router.get("/empresa/{cnpj}/dou")
async def publicacoes_dou_empresa(
    cnpj: str,
    dias: int = Query(365, ge=7, le=1825, description="Período em dias para busca no DOU"),
):
    """
    Busca publicações do Diário Oficial da União (DOU) mencionando este CNPJ.
    Usa a API pública do Querido Diário.
    """
    digitos = _apenas_digitos(cnpj)
    if len(digitos) < 8:
        raise HTTPException(status_code=400, detail="CNPJ inválido.")

    cnpj14 = digitos.zfill(14)[:14]
    cnpj_raiz = digitos[:8]

    # Buscar razão social para enriquecer a busca
    try:
        perfil = await asyncio.to_thread(_query_perfil, cnpj_raiz)
        razao = str((perfil or {}).get("razao_social") or "").strip()
    except Exception:
        razao = ""

    try:
        resultados = await _dou.scrape_empresa(cnpj14, razao)
        return {
            "cnpj": cnpj14,
            "razao_social": razao,
            "total": len(resultados),
            "publicacoes": resultados[:50],
            "fonte": "Querido Diário / DOU",
            "periodo_dias": dias,
        }
    except Exception as exc:
        logger.warning(f"DOU scraper empresa erro: {exc}")
        return {
            "cnpj": cnpj14,
            "razao_social": razao,
            "total": 0,
            "publicacoes": [],
            "erro": str(exc),
            "fonte": "Querido Diário / DOU",
        }


@router.get("/dou/novas-habilitacoes")
async def novas_habilitacoes_dou(
    dias: int = Query(30, ge=1, le=365, description="Período em dias"),
):
    """
    Lista empresas recentemente habilitadas para importação/exportação
    conforme publicações no DOU (RADAR Receita Federal).
    """
    try:
        termo = "RADAR habilitado importação exportação CNPJ"
        resultados = await _dou.scrape_empresa("", termo)
        return {
            "total": len(resultados),
            "periodo_dias": dias,
            "publicacoes": resultados[:50],
            "fonte": "Querido Diário / DOU",
            "nota": (
                "Resultados extraídos do Diário Oficial via Querido Diário (queridodiario.ok.org.br). "
                "CNPJs e razões sociais são extraídos automaticamente do texto e podem conter imprecisões."
            ),
        }
    except Exception as exc:
        logger.warning(f"Novas habilitações DOU erro: {exc}")
        return {"total": 0, "publicacoes": [], "erro": str(exc)}


@router.get("/setores")
async def listar_setores():
    """Lista os setores CNAE disponíveis."""
    return {"setores": cnae_service.listar_setores()}


@router.get("/segmentos")
async def listar_segmentos(setor: Optional[str] = Query(None)):
    """Lista os segmentos CNAE, opcionalmente filtrados por setor."""
    return {"segmentos": cnae_service.listar_segmentos(setor)}


@router.get("/diagnostico/teste-autocomplete")
async def teste_autocomplete(q: str = Query("Vale")):
    """Teste do autocomplete retornando erro como 200 para diagnóstico."""
    try:
        items = await asyncio.to_thread(_query_autocomplete, q, 2)
        return {"ok": True, "items": items}
    except Exception as exc:
        return {"ok": False, "erro": str(exc), "tipo": type(exc).__name__}


@router.get("/diagnostico/colunas")
async def diagnostico_colunas(tabela: str = Query("empresas_base")):
    """Retorna as colunas reais de uma tabela BQ (diagnóstico)."""
    nomes_permitidos = {
        "empresas_base": TBL_EMPRESAS_BASE,
        "estabelecimentos": TBL_ESTAB,
        "empresas_ncm": TBL_EMPRESAS_NCM,
        "empresasimportexport": _tbl("empresasimportexport"),
    }
    tbl_ref = nomes_permitidos.get(tabela)
    if not tbl_ref:
        raise HTTPException(status_code=400, detail=f"Tabela inválida. Use: {list(nomes_permitidos)}")
    try:
        client = get_bigquery_client()
        from google.cloud import bigquery as bq_lib
        sql = f"SELECT * FROM {tbl_ref} LIMIT 1"
        job = client.query(sql)
        result = job.result()
        schema = [{"nome": f.name, "tipo": f.field_type} for f in result.schema]
        row_sample = [dict(row.items()) for row in result]
        return {"tabela": tabela, "colunas": schema, "amostra": row_sample}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

