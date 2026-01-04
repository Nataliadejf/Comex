"""
Script para verificar se há dados no banco para um NCM específico.
"""
import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import func, and_
from datetime import datetime, timedelta

# Adicionar o diretório backend ao path ANTES de importar
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Agora importar os módulos
from database import get_db, OperacaoComex, TipoOperacao

def verificar_ncm_banco(ncm: str):
    """
    Verifica se há dados no banco para um NCM específico.
    """
    logger.info("=" * 60)
    logger.info(f"VERIFICANDO NCM {ncm} NO BANCO DE DADOS")
    logger.info("=" * 60)
    
    db = next(get_db())
    
    try:
        # Verificar diferentes períodos
        periodos = [
            ("últimos 3 meses", 90),
            ("últimos 6 meses", 180),
            ("último ano", 365),
            ("últimos 2 anos", 730),
            ("todos os dados", None)  # Sem filtro de data
        ]
        
        logger.info(f"\nVerificando diferentes períodos...")
        
        total_registros = 0
        periodo_encontrado = None
        
        for nome_periodo, dias in periodos:
            if dias:
                data_inicio = datetime.now() - timedelta(days=dias)
                filtro_data = OperacaoComex.data_operacao >= data_inicio.date()
            else:
                filtro_data = True  # Sem filtro de data
            
            registros_periodo = db.query(func.count(OperacaoComex.id)).filter(
                OperacaoComex.ncm == ncm,
                filtro_data
            ).scalar() or 0
            
            logger.info(f"  {nome_periodo}: {registros_periodo} registros")
            
            if registros_periodo > 0 and total_registros == 0:
                total_registros = registros_periodo
                periodo_encontrado = nome_periodo
                data_inicio = datetime.now() - timedelta(days=dias) if dias else None
                break
        
        if total_registros == 0:
            logger.warning(f"\n❌ NENHUM REGISTRO ENCONTRADO NO BANCO para NCM {ncm}")
            logger.info("O sistema tentará buscar na API externa quando você fizer uma busca.")
            return
        
        logger.info(f"\n✅ Dados encontrados no período: {periodo_encontrado}")
        logger.info(f"Total de registros: {total_registros}")
        
        if total_registros > 0:
            # Valor total
            valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
                OperacaoComex.ncm == ncm,
                OperacaoComex.data_operacao >= data_inicio.date()
            ).scalar() or 0
            
            # Peso total
            peso_total = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
                OperacaoComex.ncm == ncm,
                OperacaoComex.data_operacao >= data_inicio.date()
            ).scalar() or 0
            
            # Por tipo de operação
            por_tipo = db.query(
                OperacaoComex.tipo_operacao,
                func.count(OperacaoComex.id).label('total'),
                func.sum(OperacaoComex.valor_fob).label('valor')
            ).filter(
                OperacaoComex.ncm == ncm,
                OperacaoComex.data_operacao >= data_inicio.date()
            ).group_by(OperacaoComex.tipo_operacao).all()
            
            logger.info(f"\nValor total: ${valor_total:,.2f}")
            logger.info(f"Peso total: {peso_total:,.2f} KG")
            logger.info(f"\nPor tipo de operação:")
            for tipo, total, valor in por_tipo:
                logger.info(f"  {tipo.value}: {total} registros - ${valor or 0:,.2f}")
            
            # Empresas
            empresas = db.query(
                OperacaoComex.nome_empresa,
                func.count(OperacaoComex.id).label('total'),
                func.sum(OperacaoComex.valor_fob).label('valor')
            ).filter(
                OperacaoComex.ncm == ncm,
                OperacaoComex.data_operacao >= data_inicio.date(),
                OperacaoComex.nome_empresa.isnot(None),
                OperacaoComex.nome_empresa != ''
            ).group_by(OperacaoComex.nome_empresa).order_by(
                func.sum(OperacaoComex.valor_fob).desc()
            ).limit(10).all()
            
            if empresas:
                logger.info(f"\nTop 10 empresas:")
                for nome, total, valor in empresas:
                    logger.info(f"  {nome}: {total} registros - ${valor or 0:,.2f}")
            else:
                logger.warning("\n⚠️ Nenhuma empresa encontrada (campo nome_empresa pode estar vazio)")
            
            # Por mês
            por_mes = db.query(
                OperacaoComex.mes_referencia,
                func.count(OperacaoComex.id).label('total'),
                func.sum(OperacaoComex.valor_fob).label('valor')
            ).filter(
                OperacaoComex.ncm == ncm,
                OperacaoComex.data_operacao >= data_inicio.date()
            ).group_by(OperacaoComex.mes_referencia).order_by(
                OperacaoComex.mes_referencia
            ).all()
            
            logger.info(f"\nPor mês:")
            for mes, total, valor in por_mes:
                logger.info(f"  {mes}: {total} registros - ${valor or 0:,.2f}")
            
            logger.info(f"\n✅ DADOS ENCONTRADOS NO BANCO!")
        else:
            logger.warning(f"\n❌ NENHUM REGISTRO ENCONTRADO NO BANCO para NCM {ncm}")
            logger.info("O sistema tentará buscar na API externa quando você fizer uma busca.")
        
    except Exception as e:
        logger.error(f"Erro ao verificar NCM: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    # Permitir passar NCM como argumento ou usar padrão
    ncm = sys.argv[1] if len(sys.argv) > 1 else "73182200"
    logger.info(f"\nNCM a verificar: {ncm}\n")
    verificar_ncm_banco(ncm)

