"""
Script para adicionar campos de empresa (importador/exportador) ao banco de dados.
"""
import sys
from pathlib import Path

# Adicionar diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from database import get_db, init_db
from loguru import logger

def adicionar_campos_empresas():
    """Adiciona campos de empresa à tabela operacoes_comex."""
    db = next(get_db())
    
    try:
        # Verificar se os campos já existem
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='operacoes_comex'
        """))
        
        if not result.fetchone():
            logger.error("Tabela operacoes_comex não encontrada")
            return False
        
        # Verificar se os campos já existem
        result = db.execute(text("PRAGMA table_info(operacoes_comex)"))
        columns = [row[1] for row in result.fetchall()]
        
        campos_para_adicionar = []
        
        if 'razao_social_importador' not in columns:
            campos_para_adicionar.append('razao_social_importador TEXT')
        
        if 'razao_social_exportador' not in columns:
            campos_para_adicionar.append('razao_social_exportador TEXT')
        
        if 'cnpj_importador' not in columns:
            campos_para_adicionar.append('cnpj_importador VARCHAR(14)')
        
        if 'cnpj_exportador' not in columns:
            campos_para_adicionar.append('cnpj_exportador VARCHAR(14)')
        
        if not campos_para_adicionar:
            logger.info("Todos os campos de empresa já existem")
            return True
        
        # Adicionar campos
        for campo in campos_para_adicionar:
            try:
                db.execute(text(f"ALTER TABLE operacoes_comex ADD COLUMN {campo}"))
                logger.info(f"Campo adicionado: {campo}")
            except Exception as e:
                logger.warning(f"Erro ao adicionar campo {campo}: {e}")
        
        # Criar índices
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_importador 
                ON operacoes_comex(razao_social_importador, tipo_operacao)
            """))
            logger.info("Índice idx_importador criado")
        except Exception as e:
            logger.warning(f"Erro ao criar índice idx_importador: {e}")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exportador 
                ON operacoes_comex(razao_social_exportador, tipo_operacao)
            """))
            logger.info("Índice idx_exportador criado")
        except Exception as e:
            logger.warning(f"Erro ao criar índice idx_exportador: {e}")
        
        db.commit()
        logger.info("✅ Campos de empresa adicionados com sucesso!")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao adicionar campos: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Iniciando migração: adicionar campos de empresa")
    init_db()  # Garantir que o banco existe
    sucesso = adicionar_campos_empresas()
    
    if sucesso:
        logger.info("✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Migração falhou")
        sys.exit(1)

