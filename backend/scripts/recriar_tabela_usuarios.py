"""
Script para recriar a tabela usuarios com todas as colunas necessárias.
ATENÇÃO: Isso apagará todos os usuários existentes!
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect
from database import get_db, init_db, engine, Base
from database.models import Usuario, AprovacaoCadastro
from config import settings

def recriar_tabela_usuarios():
    """Recria a tabela usuarios com todas as colunas necessárias."""
    logger.info("=" * 60)
    logger.info("RECRIANDO TABELA USUARIOS")
    logger.info("=" * 60)
    logger.warning("⚠️  ATENÇÃO: Isso apagará todos os usuários existentes!")
    logger.info("=" * 60)
    
    try:
        # Fechar todas as conexões existentes
        engine.dispose()
        
        db = next(get_db())
        inspector = inspect(engine)
        
        # Verificar se a tabela existe
        tabelas_existentes = inspector.get_table_names()
        logger.info(f"Tabelas existentes: {tabelas_existentes}")
        
        if 'usuarios' in tabelas_existentes:
            logger.warning("Tabela usuarios existe. Removendo...")
            # Remover foreign keys primeiro se existirem
            try:
                db.execute(text("DROP TABLE IF EXISTS aprovacoes_cadastro"))
                logger.info("✅ Tabela aprovacoes_cadastro removida")
            except:
                pass
            
            db.execute(text("DROP TABLE IF EXISTS usuarios"))
            db.commit()
            logger.info("✅ Tabela usuarios removida")
        
        # Remover também a tabela de aprovações se existir
        if 'aprovacoes_cadastro' in tabelas_existentes:
            try:
                db.execute(text("DROP TABLE IF EXISTS aprovacoes_cadastro"))
                db.commit()
                logger.info("✅ Tabela aprovacoes_cadastro removida")
            except:
                pass
        
        # Recriar todas as tabelas usando SQLAlchemy
        logger.info("Criando tabelas com estrutura atualizada...")
        Base.metadata.create_all(bind=engine)
        
        # Verificar se foi criado corretamente
        inspector = inspect(engine)
        tabelas_criadas = inspector.get_table_names()
        logger.info(f"Tabelas criadas: {tabelas_criadas}")
        
        if 'usuarios' in tabelas_criadas:
            colunas = [col['name'] for col in inspector.get_columns('usuarios')]
            logger.info(f"Colunas na tabela usuarios: {colunas}")
            
            # Verificar se data_nascimento existe
            if 'data_nascimento' in colunas:
                logger.info("✅ Coluna data_nascimento existe!")
            else:
                logger.error("❌ Coluna data_nascimento NÃO existe!")
        
        logger.info("=" * 60)
        logger.info("✅ TABELAS RECRIADAS COM SUCESSO!")
        logger.info("=" * 60)
        logger.info("Agora você pode cadastrar novos usuários.")
        
    except Exception as e:
        logger.error(f"❌ Erro ao recriar tabela: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
        engine.dispose()

if __name__ == "__main__":
    recriar_tabela_usuarios()

