"""
Script para adicionar campos is_importacao e is_exportacao ao banco existente.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text
from database import get_db, OperacaoComex, TipoOperacao

def main():
    """Adiciona campos e atualiza dados existentes."""
    logger.info("=" * 60)
    logger.info("ADICIONANDO CAMPOS DE IDENTIFICAÇÃO")
    logger.info("=" * 60)
    
    db = next(get_db())
    
    try:
        # Verificar se as colunas já existem
        try:
            db.execute(text("SELECT is_importacao FROM operacoes_comex LIMIT 1"))
            logger.info("Campos já existem, atualizando dados...")
        except Exception:
            logger.info("Adicionando novas colunas...")
            # Adicionar colunas
            db.execute(text("ALTER TABLE operacoes_comex ADD COLUMN is_importacao VARCHAR(1) DEFAULT 'N'"))
            db.execute(text("ALTER TABLE operacoes_comex ADD COLUMN is_exportacao VARCHAR(1) DEFAULT 'N'"))
            logger.info("✅ Colunas adicionadas")
        
        # Criar índices
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_operacoes_comex_is_importacao ON operacoes_comex(is_importacao)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_operacoes_comex_is_exportacao ON operacoes_comex(is_exportacao)"))
            logger.info("✅ Índices criados")
        except Exception as e:
            logger.warning(f"Erro ao criar índices (podem já existir): {e}")
        
        # Atualizar dados existentes
        logger.info("Atualizando registros existentes...")
        
        # Importações
        result_imp = db.execute(text("""
            UPDATE operacoes_comex 
            SET is_importacao = 'S', is_exportacao = 'N'
            WHERE tipo_operacao = 'Importação'
        """))
        logger.info(f"✅ {result_imp.rowcount} registros de importação atualizados")
        
        # Exportações
        result_exp = db.execute(text("""
            UPDATE operacoes_comex 
            SET is_importacao = 'N', is_exportacao = 'S'
            WHERE tipo_operacao = 'Exportação'
        """))
        logger.info(f"✅ {result_exp.rowcount} registros de exportação atualizados")
        
        db.commit()
        
        logger.info("=" * 60)
        logger.info("✅ PROCESSO CONCLUÍDO!")
        logger.info("=" * 60)
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



