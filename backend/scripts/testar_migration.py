"""
Script para testar se as migrations estão funcionando corretamente.
Execute: python scripts/testar_migration.py
"""
import sys
from pathlib import Path

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.database import engine, init_db
from sqlalchemy import inspect, text
from loguru import logger

def verificar_tabelas():
    """Verifica quais tabelas existem no banco."""
    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    return tabelas

def verificar_indices(tabela):
    """Verifica quais índices existem em uma tabela."""
    inspector = inspect(engine)
    indexes = inspector.get_indexes(tabela)
    return [idx['name'] for idx in indexes]

def verificar_alembic_version():
    """Verifica se a tabela alembic_version existe e qual versão está registrada."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            if version:
                return version[0]
            return None
    except Exception as e:
        logger.warning(f"Tabela alembic_version não existe: {e}")
        return None

def main():
    """Testa o estado atual do banco e migrations."""
    logger.info("🔍 Verificando estado do banco de dados...")
    
    # Verificar tabelas
    tabelas = verificar_tabelas()
    logger.info(f"📊 Tabelas encontradas: {len(tabelas)}")
    for tabela in tabelas:
        logger.info(f"  - {tabela}")
        indices = verificar_indices(tabela)
        if indices:
            logger.info(f"    Índices: {', '.join(indices[:5])}{'...' if len(indices) > 5 else ''}")
    
    # Verificar versão do Alembic
    version = verificar_alembic_version()
    if version:
        logger.info(f"✅ Versão do Alembic registrada: {version}")
    else:
        logger.warning("⚠️ Nenhuma versão do Alembic registrada")
    
    # Verificar tabelas esperadas
    tabelas_esperadas = [
        'operacoes_comex',
        'ncm_info',
        'coleta_log',
        'usuarios',
        'aprovacao_cadastro',
        'comercio_exterior',
        'empresas',
        'cnae_hierarquia',
        'empresas_recomendadas'
    ]
    
    logger.info("\n📋 Verificando tabelas esperadas:")
    for tabela in tabelas_esperadas:
        if tabela in tabelas:
            logger.info(f"  ✅ {tabela} - existe")
        else:
            logger.warning(f"  ❌ {tabela} - NÃO existe")
    
    # Testar conexão
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("\n✅ Conexão com banco de dados OK")
    except Exception as e:
        logger.error(f"\n❌ Erro ao conectar: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
