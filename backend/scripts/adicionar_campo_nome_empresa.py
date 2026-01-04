"""
Script para adicionar campo nome_empresa à tabela operacoes_comex.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text
from database import get_db

def main():
    """Adiciona campo nome_empresa se não existir."""
    logger.info("=" * 60)
    logger.info("ADICIONANDO CAMPO nome_empresa")
    logger.info("=" * 60)
    
    db = next(get_db())
    
    try:
        # Verificar se a coluna já existe
        try:
            db.execute(text("SELECT nome_empresa FROM operacoes_comex LIMIT 1"))
            logger.info("✅ Campo nome_empresa já existe!")
        except Exception:
            logger.info("Adicionando coluna nome_empresa...")
            # Adicionar coluna
            db.execute(text("ALTER TABLE operacoes_comex ADD COLUMN nome_empresa VARCHAR(255)"))
            logger.info("✅ Coluna nome_empresa adicionada")
            
            # Criar índice
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_operacoes_comex_nome_empresa ON operacoes_comex(nome_empresa)"))
                logger.info("✅ Índice criado")
            except Exception as e:
                logger.warning(f"Erro ao criar índice (pode já existir): {e}")
        
        db.commit()
        logger.info("=" * 60)
        logger.info("✅ PROCESSO CONCLUÍDO!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        db.rollback()
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    main()

