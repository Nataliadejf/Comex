"""
Script para correlacionar empresas da tabela 'empresas' com operações da tabela 'comercio_exterior'.
Atualiza valores de importação e exportação nas empresas baseado nas operações agregadas.
"""
import sys
from pathlib import Path
from loguru import logger
from collections import defaultdict

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal
from database.models import Empresa, ComercioExterior
from sqlalchemy import func

logger.remove()
logger.add(sys.stderr, level="INFO")


def correlacionar_empresas_operacoes():
    """
    Correlaciona empresas com operações de comércio exterior.
    Atualiza valores de importação/exportação nas empresas.
    """
    logger.info("="*80)
    logger.info("CORRELAÇÃO DE EMPRESAS COM OPERAÇÕES DE COMÉRCIO EXTERIOR")
    logger.info("="*80)
    
    db = SessionLocal()
    try:
        # 1. Agregar operações por estado/NCM
        logger.info("\n📊 Agregando operações de comércio exterior por estado...")
        
        # Importações por estado
        imp_por_estado = db.query(
            ComercioExterior.estado,
            func.sum(ComercioExterior.valor_usd).label('valor_total'),
            func.sum(ComercioExterior.peso_kg).label('peso_total'),
            func.count(ComercioExterior.id).label('qtd_operacoes')
        ).filter(
            ComercioExterior.tipo == 'importacao',
            ComercioExterior.estado.isnot(None)
        ).group_by(
            ComercioExterior.estado
        ).all()
        
        logger.info(f"  ✅ Encontradas importações em {len(imp_por_estado)} estados")
        
        # Exportações por estado
        exp_por_estado = db.query(
            ComercioExterior.estado,
            func.sum(ComercioExterior.valor_usd).label('valor_total'),
            func.sum(ComercioExterior.peso_kg).label('peso_total'),
            func.count(ComercioExterior.id).label('qtd_operacoes')
        ).filter(
            ComercioExterior.tipo == 'exportacao',
            ComercioExterior.estado.isnot(None)
        ).group_by(
            ComercioExterior.estado
        ).all()
        
        logger.info(f"  ✅ Encontradas exportações em {len(exp_por_estado)} estados")
        
        # 2. Criar dicionário de valores por estado
        valores_por_estado = defaultdict(lambda: {
            'importacao': {'valor': 0.0, 'peso': 0.0, 'qtd': 0},
            'exportacao': {'valor': 0.0, 'peso': 0.0, 'qtd': 0}
        })
        
        for estado, valor, peso, qtd in imp_por_estado:
            if estado:
                valores_por_estado[estado]['importacao'] = {
                    'valor': float(valor or 0),
                    'peso': float(peso or 0),
                    'qtd': int(qtd or 0)
                }
        
        for estado, valor, peso, qtd in exp_por_estado:
            if estado:
                valores_por_estado[estado]['exportacao'] = {
                    'valor': float(valor or 0),
                    'peso': float(peso or 0),
                    'qtd': int(qtd or 0)
                }
        
        # 3. Buscar todas as empresas
        logger.info("\n🏢 Buscando empresas para atualizar...")
        empresas = db.query(Empresa).all()
        logger.info(f"  ✅ Encontradas {len(empresas)} empresas")
        
        # 4. Calcular distribuição proporcional por estado
        # Se uma empresa está em um estado, ela recebe uma parte proporcional dos valores
        empresas_atualizadas = 0
        
        for empresa in empresas:
            if not empresa.estado:
                continue
            
            estado = empresa.estado.upper()
            valores_estado = valores_por_estado.get(estado, {})
            
            # Contar quantas empresas do mesmo tipo existem no estado
            empresas_mesmo_estado = db.query(func.count(Empresa.id)).filter(
                Empresa.estado == estado
            ).scalar() or 1
            
            # Distribuir valores proporcionalmente
            # (Simplificado: dividir igualmente entre empresas do estado)
            # Em produção, poderia usar CNAE ou outros critérios
            
            valor_imp_estado = valores_estado.get('importacao', {}).get('valor', 0.0)
            valor_exp_estado = valores_estado.get('exportacao', {}).get('valor', 0.0)
            
            # Atualizar empresa apenas se houver valores no estado
            if valor_imp_estado > 0 or valor_exp_estado > 0:
                # Distribuir proporcionalmente (simplificado)
                # Em produção, usar critérios mais sofisticados (CNAE, histórico, etc.)
                empresa.valor_importacao = valor_imp_estado / empresas_mesmo_estado
                empresa.valor_exportacao = valor_exp_estado / empresas_mesmo_estado
                empresas_atualizadas += 1
        
        db.commit()
        logger.success(f"\n✅ {empresas_atualizadas} empresas atualizadas com valores de importação/exportação")
        
        # 5. Estatísticas finais
        logger.info("\n📊 Estatísticas finais:")
        total_empresas = db.query(func.count(Empresa.id)).scalar() or 0
        empresas_com_valor_imp = db.query(func.count(Empresa.id)).filter(
            Empresa.valor_importacao > 0
        ).scalar() or 0
        empresas_com_valor_exp = db.query(func.count(Empresa.id)).filter(
            Empresa.valor_exportacao > 0
        ).scalar() or 0
        
        total_valor_imp = db.query(func.sum(Empresa.valor_importacao)).scalar() or 0.0
        total_valor_exp = db.query(func.sum(Empresa.valor_exportacao)).scalar() or 0.0
        
        logger.info(f"  Total de empresas: {total_empresas:,}")
        logger.info(f"  Empresas com importação: {empresas_com_valor_imp:,}")
        logger.info(f"  Empresas com exportação: {empresas_com_valor_exp:,}")
        logger.info(f"  Valor total importação: ${total_valor_imp:,.2f}")
        logger.info(f"  Valor total exportação: ${total_valor_exp:,.2f}")
        
        logger.success("\n" + "="*80)
        logger.success("✅ CORRELAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.success("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro durante correlação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    correlacionar_empresas_operacoes()
