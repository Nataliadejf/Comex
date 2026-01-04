"""
Script para configurar e preparar o banco de dados.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import init_db, get_db, OperacaoComex
from sqlalchemy import func, inspect
from config import settings


def verificar_estrutura_banco():
    """Verifica se a estrutura do banco está correta."""
    logger.info("Verificando estrutura do banco de dados...")
    
    db = next(get_db())
    inspector = inspect(db.bind)
    
    # Verificar tabelas
    tabelas = inspector.get_table_names()
    logger.info(f"Tabelas encontradas: {', '.join(tabelas)}")
    
    # Verificar colunas da tabela principal
    if 'operacoes_comex' in tabelas:
        colunas = [col['name'] for col in inspector.get_columns('operacoes_comex')]
        logger.info(f"Colunas em operacoes_comex: {len(colunas)}")
        
        # Verificar campos importantes
        campos_importantes = ['ncm', 'tipo_operacao', 'is_importacao', 'is_exportacao']
        for campo in campos_importantes:
            if campo in colunas:
                logger.info(f"  ✅ Campo '{campo}' existe")
            else:
                logger.warning(f"  ⚠️  Campo '{campo}' não encontrado")
    
    return True


def contar_registros():
    """Conta registros no banco."""
    db = next(get_db())
    
    total = db.query(func.count(OperacaoComex.id)).scalar() or 0
    
    if total > 0:
        # Contar por tipo
        importacao = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.tipo_operacao == 'Importação'
        ).scalar() or 0
        
        exportacao = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.tipo_operacao == 'Exportação'
        ).scalar() or 0
        
        logger.info(f"Total de registros: {total:,}")
        logger.info(f"  Importações: {importacao:,}")
        logger.info(f"  Exportações: {exportacao:,}")
    else:
        logger.info("Banco de dados está vazio")
    
    return total


def configurar_banco():
    """Configura e prepara o banco de dados."""
    logger.info("=" * 60)
    logger.info("CONFIGURAÇÃO DO BANCO DE DADOS")
    logger.info("=" * 60)
    
    # Inicializar banco
    logger.info("Inicializando banco de dados...")
    init_db()
    logger.info("✅ Banco de dados inicializado")
    
    # Verificar estrutura
    verificar_estrutura_banco()
    
    # Contar registros
    total = contar_registros()
    
    logger.info("=" * 60)
    logger.info("CONFIGURAÇÃO CONCLUÍDA!")
    logger.info("=" * 60)
    
    return total


if __name__ == "__main__":
    configurar_banco()



