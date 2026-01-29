"""
Cruzamento de dados: empresas importadoras, exportadoras, NCM e município/UF.
Agrupa operações por NCM e UF e gera relacionamentos importador-exportador por NCM/UF.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from database.models import OperacaoComex, TipoOperacao, EmpresasRecomendadas


def executar_cruzamento_ncm_uf(db: Session, limite_grupos: int = 5000) -> Dict[str, Any]:
    """
    Cruza dados de operacoes_comex: agrupa por NCM e UF,
    lista importadores e exportadores por grupo e opcionalmente atualiza EmpresasRecomendadas.
    
    Returns:
        Estatísticas do cruzamento e lista de grupos (ncm, uf) com empresas.
    """
    stats = {
        "grupos_ncm_uf": 0,
        "importadores_unicos": 0,
        "exportadores_unicos": 0,
        "registros_empresas_recomendadas": 0,
        "erros": 0,
    }
    
    logger.info("🔄 Iniciando cruzamento NCM + UF (importadores x exportadores)...")
    
    try:
        # Agrupar por NCM e UF: listar CNPJ/razão social de importadores e exportadores
        q_imp = (
            db.query(
                OperacaoComex.ncm,
                OperacaoComex.uf,
                OperacaoComex.razao_social_importador,
                OperacaoComex.cnpj_importador,
                func.sum(OperacaoComex.valor_fob).label("valor_total"),
                func.count(OperacaoComex.id).label("qtd"),
            )
            .filter(
                OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
                OperacaoComex.ncm.isnot(None),
                OperacaoComex.uf.isnot(None),
                OperacaoComex.razao_social_importador.isnot(None),
            )
            .group_by(
                OperacaoComex.ncm,
                OperacaoComex.uf,
                OperacaoComex.razao_social_importador,
                OperacaoComex.cnpj_importador,
            )
            .limit(limite_grupos * 10)
        )
        
        q_exp = (
            db.query(
                OperacaoComex.ncm,
                OperacaoComex.uf,
                OperacaoComex.razao_social_exportador,
                OperacaoComex.cnpj_exportador,
                func.sum(OperacaoComex.valor_fob).label("valor_total"),
                func.count(OperacaoComex.id).label("qtd"),
            )
            .filter(
                OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
                OperacaoComex.ncm.isnot(None),
                OperacaoComex.uf.isnot(None),
                OperacaoComex.razao_social_exportador.isnot(None),
            )
            .group_by(
                OperacaoComex.ncm,
                OperacaoComex.uf,
                OperacaoComex.razao_social_exportador,
                OperacaoComex.cnpj_exportador,
            )
            .limit(limite_grupos * 10)
        )
        
        importadores_por_ncm_uf: Dict[tuple, List[Dict[str, Any]]] = {}
        exportadores_por_ncm_uf: Dict[tuple, List[Dict[str, Any]]] = {}
        
        for row in q_imp.all():
            chave = (row.ncm or "", (row.uf or "").strip()[:2] or "  ")
            if chave not in importadores_por_ncm_uf:
                importadores_por_ncm_uf[chave] = []
            importadores_por_ncm_uf[chave].append({
                "razao_social": row.razao_social_importador,
                "cnpj": row.cnpj_importador,
                "valor_total": float(row.valor_total or 0),
                "qtd_operacoes": row.qtd or 0,
            })
        
        for row in q_exp.all():
            chave = (row.ncm or "", (row.uf or "").strip()[:2] or "  ")
            if chave not in exportadores_por_ncm_uf:
                exportadores_por_ncm_uf[chave] = []
            exportadores_por_ncm_uf[chave].append({
                "razao_social": row.razao_social_exportador,
                "cnpj": row.cnpj_exportador,
                "valor_total": float(row.valor_total or 0),
                "qtd_operacoes": row.qtd or 0,
            })
        
        todos_chaves = set(importadores_por_ncm_uf.keys()) | set(exportadores_por_ncm_uf.keys())
        stats["grupos_ncm_uf"] = len(todos_chaves)
        
        importadores_unicos = set()
        exportadores_unicos = set()
        for chave, lista in importadores_por_ncm_uf.items():
            for item in lista:
                if item.get("cnpj"):
                    importadores_unicos.add(item["cnpj"])
                if item.get("razao_social"):
                    importadores_unicos.add(item["razao_social"])
        for chave, lista in exportadores_por_ncm_uf.items():
            for item in lista:
                if item.get("cnpj"):
                    exportadores_unicos.add(item["cnpj"])
                if item.get("razao_social"):
                    exportadores_unicos.add(item["razao_social"])
        
        stats["importadores_unicos"] = len(importadores_unicos)
        stats["exportadores_unicos"] = len(exportadores_unicos)
        
        # Opcional: consolidar em EmpresasRecomendadas (por CNPJ/nome, agregando NCMs e UFs)
        try:
            # Inserir/atualizar empresas recomendadas a partir dos importadores
            for chave, lista in importadores_por_ncm_uf.items():
                ncm, uf = chave
                for item in lista[:50]:  # Limitar por grupo
                    cnpj = (item.get("cnpj") or "").strip()
                    nome = (item.get("razao_social") or "").strip()
                    if not nome:
                        continue
                    q_rec = db.query(EmpresasRecomendadas)
                    if cnpj:
                        q_rec = q_rec.filter(EmpresasRecomendadas.cnpj == cnpj)
                    else:
                        q_rec = q_rec.filter(EmpresasRecomendadas.nome == nome)
                    rec = q_rec.first()
                    if rec:
                        rec.valor_total_importacao_usd = (rec.valor_total_importacao_usd or 0) + item.get("valor_total", 0)
                        rec.total_operacoes_importacao = (rec.total_operacoes_importacao or 0) + item.get("qtd_operacoes", 0)
                        rec.ncms_importacao = (rec.ncms_importacao or "") + ("," + ncm if ncm and (not rec.ncms_importacao or ncm not in (rec.ncms_importacao or "")) else "")
                    else:
                        rec = EmpresasRecomendadas(
                            cnpj=cnpj or None,
                            nome=nome,
                            estado=uf,
                            tipo_principal="importadora",
                            provavel_importador=1,
                            provavel_exportador=0,
                            valor_total_importacao_usd=item.get("valor_total", 0),
                            valor_total_exportacao_usd=0,
                            total_operacoes_importacao=item.get("qtd_operacoes", 0),
                            total_operacoes_exportacao=0,
                            ncms_importacao=ncm or "",
                        )
                        db.add(rec)
                        stats["registros_empresas_recomendadas"] += 1
            
            # Exportadores
            for chave, lista in exportadores_por_ncm_uf.items():
                ncm, uf = chave
                for item in lista[:50]:
                    cnpj = (item.get("cnpj") or "").strip()
                    nome = (item.get("razao_social") or "").strip()
                    if not nome:
                        continue
                    q_rec = db.query(EmpresasRecomendadas)
                    if cnpj:
                        q_rec = q_rec.filter(EmpresasRecomendadas.cnpj == cnpj)
                    else:
                        q_rec = q_rec.filter(EmpresasRecomendadas.nome == nome)
                    rec = q_rec.first()
                    if rec:
                        rec.valor_total_exportacao_usd = (rec.valor_total_exportacao_usd or 0) + item.get("valor_total", 0)
                        rec.total_operacoes_exportacao = (rec.total_operacoes_exportacao or 0) + item.get("qtd_operacoes", 0)
                        rec.ncms_exportacao = (rec.ncms_exportacao or "") + ("," + ncm if ncm and (not rec.ncms_exportacao or ncm not in (rec.ncms_exportacao or "")) else "")
                        if rec.tipo_principal == "importadora":
                            rec.tipo_principal = "ambos"
                        rec.provavel_exportador = 1
                    else:
                        rec = EmpresasRecomendadas(
                            cnpj=cnpj or None,
                            nome=nome,
                            estado=uf,
                            tipo_principal="exportadora",
                            provavel_importador=0,
                            provavel_exportador=1,
                            valor_total_importacao_usd=0,
                            valor_total_exportacao_usd=item.get("valor_total", 0),
                            total_operacoes_importacao=0,
                            total_operacoes_exportacao=item.get("qtd_operacoes", 0),
                            ncms_exportacao=ncm or "",
                        )
                        db.add(rec)
                        stats["registros_empresas_recomendadas"] += 1
            
            db.commit()
            logger.info(f"✅ Cruzamento concluído: {stats['grupos_ncm_uf']} grupos NCM/UF, "
                        f"{stats['importadores_unicos']} importadores, {stats['exportadores_unicos']} exportadores, "
                        f"{stats['registros_empresas_recomendadas']} registros em empresas_recomendadas")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao salvar cruzamento em empresas_recomendadas: {e}")
            stats["erros"] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro no cruzamento NCM/UF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        stats["erros"] += 1
        return stats
