"""
Sincronização BigQuery (Base dos Dados) → PostgreSQL.
Usa o schema atual das tabelas comex_stat (valor_fob_dolar, sigla_uf, id_ncm, etc.).
Ano padrão: 2021 (última base comum em muitos ambientes).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from database.models import EmpresaComex, OperacaoNCMEstado
from services import basedosdados_bigquery as bqbd


def verificar_municipio_exportacao() -> Dict[str, Any]:
    """
    Executa consultas de verificação no BigQuery (anos disponíveis + colunas da tabela).
    """
    client = bqbd.get_bigquery_client()
    if not client:
        return {"erro": "Cliente BigQuery indisponível"}

    sql_anos = """
    SELECT DISTINCT ano
    FROM `basedosdados.br_me_comex_stat.municipio_exportacao`
    ORDER BY ano DESC
    LIMIT 20
    """
    sql_cols = """
    SELECT column_name, data_type
    FROM `basedosdados.br_me_comex_stat.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'municipio_exportacao'
    ORDER BY ordinal_position
    """
    try:
        anos = bqbd._run_query(client, sql_anos, None)
    except Exception as e:
        logger.warning("verificar anos: {}", e)
        anos = []
    try:
        cols = bqbd._run_query(client, sql_cols, None)
    except Exception as e:
        logger.warning("verificar colunas: {}", e)
        cols = []
    return {"anos_disponiveis": anos, "colunas_municipio_exportacao": cols}


def _norm_uf(val: Optional[str]) -> str:
    if not val or str(val).strip().upper() in ("ND", "NULL", "NONE"):
        return "NA"
    return str(val).strip().upper()[:2]


def _norm_ncm(val: Optional[str]) -> str:
    d = "".join(c for c in str(val or "") if c.isdigit())
    return (d + "00000000")[:8]


def sincronizar_empresas_exportadoras(db: Session, ano: int = 2021) -> Dict[str, Any]:
    """Agrega município × UF (comex_stat) como proxy de 'empresa' e grava em empresas_comex."""
    client = bqbd.get_bigquery_client()
    if not client:
        return {"ok": False, "erro": "BigQuery indisponível", "inseridos": 0}

    sql = """
    SELECT
        COALESCE(mun.nome, CAST(e.id_municipio AS STRING)) AS razao_social,
        e.sigla_uf AS uf,
        COALESCE(mun.nome, CAST(e.id_municipio AS STRING)) AS municipio,
        CAST(SUM(e.valor_fob_dolar) AS FLOAT64) AS valor_fob_total,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_exportacao` AS e
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON e.id_municipio = mun.id_municipio
    WHERE e.ano = @ano
    GROUP BY COALESCE(mun.nome, CAST(e.id_municipio AS STRING)), e.sigla_uf
    """
    now = datetime.utcnow()
    try:
        rows = bqbd._run_query(client, sql, {"ano": int(ano)})
    except Exception as e:
        logger.exception("sync exportadoras BQ: {}", e)
        return {"ok": False, "erro": str(e), "inseridos": 0}

    deleted = db.query(EmpresaComex).filter(
        EmpresaComex.ano_referencia == ano,
        EmpresaComex.tipo == "exportadora",
    ).delete(synchronize_session=False)
    n = 0
    for r in rows:
        mun = (r.get("municipio") or r.get("razao_social") or "")[:255]
        rz = (r.get("razao_social") or "")[:512]
        uf = _norm_uf(r.get("uf"))
        try:
            vf = float(r.get("valor_fob_total") or 0)
        except (TypeError, ValueError):
            vf = 0.0
        try:
            tot = int(r.get("total_operacoes") or 0)
        except (TypeError, ValueError):
            tot = 0
        db.add(
            EmpresaComex(
                cnpj=None,
                razao_social=rz,
                uf=uf,
                municipio=mun or "",
                tipo="exportadora",
                valor_fob_total=vf,
                total_operacoes=tot,
                ano_referencia=ano,
                atualizado_em=now,
            )
        )
        n += 1
    db.commit()
    return {"ok": True, "ano": ano, "removidos": deleted, "inseridos": n}


def sincronizar_empresas_importadoras(db: Session, ano: int = 2021) -> Dict[str, Any]:
    client = bqbd.get_bigquery_client()
    if not client:
        return {"ok": False, "erro": "BigQuery indisponível", "inseridos": 0}

    sql = """
    SELECT
        COALESCE(mun.nome, CAST(i.id_municipio AS STRING)) AS razao_social,
        i.sigla_uf AS uf,
        COALESCE(mun.nome, CAST(i.id_municipio AS STRING)) AS municipio,
        CAST(SUM(i.valor_fob_dolar) AS FLOAT64) AS valor_fob_total,
        COUNT(*) AS total_operacoes
    FROM `basedosdados.br_me_comex_stat.municipio_importacao` AS i
    LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS mun
        ON i.id_municipio = mun.id_municipio
    WHERE i.ano = @ano
    GROUP BY COALESCE(mun.nome, CAST(i.id_municipio AS STRING)), i.sigla_uf
    """
    now = datetime.utcnow()
    try:
        rows = bqbd._run_query(client, sql, {"ano": int(ano)})
    except Exception as e:
        logger.exception("sync importadoras BQ: {}", e)
        return {"ok": False, "erro": str(e), "inseridos": 0}

    deleted = db.query(EmpresaComex).filter(
        EmpresaComex.ano_referencia == ano,
        EmpresaComex.tipo == "importadora",
    ).delete(synchronize_session=False)
    n = 0
    for r in rows:
        mun = (r.get("municipio") or r.get("razao_social") or "")[:255]
        rz = (r.get("razao_social") or "")[:512]
        uf = _norm_uf(r.get("uf"))
        try:
            vf = float(r.get("valor_fob_total") or 0)
        except (TypeError, ValueError):
            vf = 0.0
        try:
            tot = int(r.get("total_operacoes") or 0)
        except (TypeError, ValueError):
            tot = 0
        db.add(
            EmpresaComex(
                cnpj=None,
                razao_social=rz,
                uf=uf,
                municipio=mun or "",
                tipo="importadora",
                valor_fob_total=vf,
                total_operacoes=tot,
                ano_referencia=ano,
                atualizado_em=now,
            )
        )
        n += 1
    db.commit()
    return {"ok": True, "ano": ano, "removidos": deleted, "inseridos": n}


def sincronizar_operacoes_ncm_estado(db: Session, ano: int = 2021) -> Dict[str, Any]:
    """Agrega tabelas ncm_exportacao e ncm_importacao (schema Base dos Dados atual)."""
    client = bqbd.get_bigquery_client()
    if not client:
        return {"ok": False, "erro": "BigQuery indisponível", "inseridos": 0}

    sql = """
    SELECT
        ano,
        mes,
        id_ncm AS ncm,
        sigla_uf_ncm AS uf_raw,
        'exportacao' AS tipo_operacao,
        CAST(SUM(valor_fob_dolar) AS FLOAT64) AS valor_fob_usd,
        CAST(SUM(quantidade_estatistica) AS FLOAT64) AS quantidade_estatistica,
        CAST(SUM(peso_liquido_kg) AS FLOAT64) AS peso_kg
    FROM `basedosdados.br_me_comex_stat.ncm_exportacao`
    WHERE ano = @ano
    GROUP BY ano, mes, id_ncm, sigla_uf_ncm

    UNION ALL

    SELECT
        ano,
        mes,
        id_ncm AS ncm,
        sigla_uf_ncm AS uf_raw,
        'importacao' AS tipo_operacao,
        CAST(SUM(valor_fob_dolar) AS FLOAT64) AS valor_fob_usd,
        CAST(SUM(quantidade_estatistica) AS FLOAT64) AS quantidade_estatistica,
        CAST(SUM(peso_liquido_kg) AS FLOAT64) AS peso_kg
    FROM `basedosdados.br_me_comex_stat.ncm_importacao`
    WHERE ano = @ano
    GROUP BY ano, mes, id_ncm, sigla_uf_ncm
    """
    now = datetime.utcnow()
    try:
        rows = bqbd._run_query(client, sql, {"ano": int(ano)})
    except Exception as e:
        logger.exception("sync ncm_estado BQ: {}", e)
        return {"ok": False, "erro": str(e), "inseridos": 0}

    deleted = db.query(OperacaoNCMEstado).filter(OperacaoNCMEstado.ano == ano).delete(synchronize_session=False)
    n = 0
    for r in rows:
        uf = _norm_uf(r.get("uf_raw"))
        ncm = _norm_ncm(r.get("ncm"))
        try:
            mes = int(r.get("mes")) if r.get("mes") is not None else None
        except (TypeError, ValueError):
            mes = None
        try:
            vf = float(r.get("valor_fob_usd") or 0)
        except (TypeError, ValueError):
            vf = 0.0
        qe = r.get("quantidade_estatistica")
        pk = r.get("peso_kg")
        try:
            qe_f = float(qe) if qe is not None else None
        except (TypeError, ValueError):
            qe_f = None
        try:
            pk_f = float(pk) if pk is not None else None
        except (TypeError, ValueError):
            pk_f = None
        db.add(
            OperacaoNCMEstado(
                ano=int(r.get("ano") or ano),
                mes=mes,
                ncm=ncm,
                descricao_ncm=None,
                uf=uf,
                tipo_operacao=str(r.get("tipo_operacao") or "")[:20],
                valor_fob_usd=vf,
                quantidade_estatistica=qe_f,
                peso_kg=pk_f,
                razao_social=None,
                atualizado_em=now,
            )
        )
        n += 1
    db.commit()
    return {"ok": True, "ano": ano, "removidos": deleted, "inseridos": n}


def sincronizar_tudo(db: Session, ano: int = 2021) -> Dict[str, Any]:
    r1 = sincronizar_empresas_exportadoras(db, ano)
    r2 = sincronizar_empresas_importadoras(db, ano)
    r3 = sincronizar_operacoes_ncm_estado(db, ano)
    return {
        "ano": ano,
        "ok": bool(r1.get("ok") and r2.get("ok") and r3.get("ok")),
        "exportadoras": r1,
        "importadoras": r2,
        "ncm_estado": r3,
    }
