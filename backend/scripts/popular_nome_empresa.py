"""
Script para popular o campo nome_empresa a partir de outras colunas ou dados existentes.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect
from database import get_db

def verificar_colunas_empresa():
    """Verifica quais colunas relacionadas a empresa existem."""
    db = next(get_db())
    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('operacoes_comex')]
        
        logger.info("Colunas na tabela operacoes_comex:")
        for col in sorted(columns):
            logger.info(f"  - {col}")
        
        # Procurar colunas relacionadas a empresa
        empresa_cols = [
            col for col in columns 
            if any(termo in col.lower() for termo in ['empresa', 'importador', 'exportador', 'razao', 'social', 'nome'])
        ]
        
        logger.info("\nColunas relacionadas a empresa encontradas:")
        if empresa_cols:
            for col in empresa_cols:
                logger.info(f"  ✓ {col}")
        else:
            logger.warning("  ❌ Nenhuma coluna de empresa encontrada")
        
        return empresa_cols, columns
    finally:
        db.close()

def popular_nome_empresa():
    """Tenta popular nome_empresa a partir de outras colunas."""
    logger.info("=" * 60)
    logger.info("POPULANDO CAMPO nome_empresa")
    logger.info("=" * 60)
    
    empresa_cols, all_cols = verificar_colunas_empresa()
    
    db = next(get_db())
    try:
        # Verificar se nome_empresa existe
        try:
            db.execute(text("SELECT nome_empresa FROM operacoes_comex LIMIT 1"))
            logger.info("✅ Coluna nome_empresa existe")
        except Exception:
            logger.error("❌ Coluna nome_empresa não existe!")
            logger.info("Execute ADICIONAR_CAMPO_EMPRESA.bat primeiro")
            return False
        
        # Contar registros sem nome_empresa
        result = db.execute(text("SELECT COUNT(*) FROM operacoes_comex WHERE nome_empresa IS NULL OR nome_empresa = ''"))
        total_sem_empresa = result.scalar()
        logger.info(f"Registros sem nome_empresa: {total_sem_empresa}")
        
        if total_sem_empresa == 0:
            logger.info("✅ Todos os registros já têm nome_empresa preenchido!")
            return True
        
        # Tentar popular a partir de outras colunas
        # Exemplo: se houver uma coluna 'importador' ou similar
        for col in empresa_cols:
            if col != 'nome_empresa':
                logger.info(f"\nTentando popular nome_empresa a partir de {col}...")
                try:
                    # Atualizar apenas registros onde nome_empresa está vazio
                    query = f"""
                        UPDATE operacoes_comex 
                        SET nome_empresa = {col}
                        WHERE (nome_empresa IS NULL OR nome_empresa = '')
                        AND {col} IS NOT NULL 
                        AND {col} != ''
                    """
                    result = db.execute(text(query))
                    updated = result.rowcount
                    db.commit()
                    logger.info(f"✅ Atualizados {updated} registros a partir de {col}")
                except Exception as e:
                    logger.warning(f"❌ Erro ao popular de {col}: {e}")
                    db.rollback()
        
        # Verificar resultado final
        result = db.execute(text("SELECT COUNT(*) FROM operacoes_comex WHERE nome_empresa IS NOT NULL AND nome_empresa != ''"))
        total_com_empresa = result.scalar()
        logger.info(f"\n✅ Total de registros com nome_empresa: {total_com_empresa}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    popular_nome_empresa()
