"""
Script para verificar se há dados no banco para os NCMs monitorados.
"""
import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from database import get_db, OperacaoComex

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def verificar_ncms_monitorados():
    """
    Verifica quais NCMs têm dados no banco de dados.
    """
    logger.info("=" * 60)
    logger.info("VERIFICANDO DADOS DOS NCMs NO BANCO")
    logger.info("=" * 60)

    db: Session = next(get_db())

    try:
        # Buscar todos os NCMs únicos no banco
        logger.info("Buscando NCMs únicos no banco de dados...")
        
        ncms_no_banco = db.query(
            OperacaoComex.ncm,
            func.count(OperacaoComex.id).label('total_registros'),
            func.sum(OperacaoComex.valor_fob).label('valor_total'),
            func.min(OperacaoComex.data_referencia).label('data_inicio'),
            func.max(OperacaoComex.data_referencia).label('data_fim')
        ).group_by(
            OperacaoComex.ncm
        ).order_by(
            func.count(OperacaoComex.id).desc()
        ).limit(100).all()

        logger.info(f"\n{'='*60}")
        logger.info(f"TOP 100 NCMs COM MAIS DADOS:")
        logger.info(f"{'='*60}\n")

        for ncm, total_registros, valor_total, data_inicio, data_fim in ncms_no_banco:
            if ncm:
                valor_formatado = f"${float(valor_total or 0):,.2f}" if valor_total else "$0.00"
                logger.info(f"NCM: {ncm}")
                logger.info(f"  Total de registros: {total_registros:,}")
                logger.info(f"  Valor total (FOB): {valor_formatado}")
                logger.info(f"  Período: {data_inicio} até {data_fim}")
                logger.info("")

        # Estatísticas gerais
        total_registros = db.query(func.count(OperacaoComex.id)).scalar()
        total_ncms_unicos = db.query(func.count(func.distinct(OperacaoComex.ncm))).scalar()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"ESTATÍSTICAS GERAIS:")
        logger.info(f"{'='*60}")
        logger.info(f"Total de registros no banco: {total_registros:,}")
        logger.info(f"Total de NCMs únicos: {total_ncms_unicos:,}")
        logger.info(f"{'='*60}\n")

        # Verificar NCMs específicos se fornecidos
        import json
        import os
        
        # Tentar ler NCMs monitorados do localStorage (via arquivo temporário se necessário)
        # Por enquanto, vamos verificar alguns NCMs comuns
        ncms_comuns = ['87083090', '87089900', '87084090', '87085090', '87086090']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"VERIFICANDO NCMs ESPECÍFICOS:")
        logger.info(f"{'='*60}\n")

        for ncm_test in ncms_comuns:
            registros = db.query(OperacaoComex).filter(
                OperacaoComex.ncm == ncm_test
            ).count()
            
            if registros > 0:
                valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
                    OperacaoComex.ncm == ncm_test
                ).scalar()
                
                logger.info(f"✅ NCM {ncm_test}: {registros:,} registros - Valor total: ${float(valor_total or 0):,.2f}")
            else:
                logger.info(f"❌ NCM {ncm_test}: Nenhum registro encontrado")

        logger.info(f"\n{'='*60}\n")

    except Exception as e:
        logger.error(f"❌ Erro ao verificar NCMs: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    verificar_ncms_monitorados()

