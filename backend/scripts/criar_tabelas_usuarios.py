"""
Script para criar tabelas de usuários no banco de dados.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import init_db, Base
from database.models import Usuario, AprovacaoCadastro
from sqlalchemy import create_engine
from config import settings
from loguru import logger

def criar_tabelas():
    """Cria as tabelas de usuários no banco de dados."""
    try:
        logger.info("Criando tabelas de usuários...")
        
        # Criar engine
        engine = create_engine(settings.database_url)
        
        # Criar todas as tabelas
        Base.metadata.create_all(engine, tables=[Usuario.__table__, AprovacaoCadastro.__table__])
        
        logger.info("✅ Tabelas de usuários criadas com sucesso!")
        logger.info(f"   - usuarios")
        logger.info(f"   - aprovacoes_cadastro")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    criar_tabelas()

