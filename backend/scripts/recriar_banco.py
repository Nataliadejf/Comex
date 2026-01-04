"""
Script para recriar o banco de dados corrompido.
"""
import sys
from pathlib import Path
import shutil

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings
from database import init_db

def main():
    """Recria o banco de dados."""
    logger.info("=" * 60)
    logger.info("RECRIANDO BANCO DE DADOS")
    logger.info("=" * 60)
    
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    db_dir = db_path.parent
    
    # Criar diretório se não existir
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Fazer backup do banco corrompido se existir
    if db_path.exists():
        backup_path = db_path.with_suffix('.db.backup')
        logger.info(f"Fazendo backup do banco corrompido: {backup_path}")
        try:
            shutil.copy2(db_path, backup_path)
            logger.info("✅ Backup criado")
        except Exception as e:
            logger.warning(f"Erro ao criar backup: {e}")
        
        # Remover banco corrompido
        try:
            db_path.unlink()
            logger.info("✅ Banco corrompido removido")
        except Exception as e:
            logger.error(f"Erro ao remover banco: {e}")
    
    # Recriar banco
    logger.info("Criando novo banco de dados...")
    init_db()
    logger.info("✅ Banco de dados recriado com sucesso!")
    
    logger.info("=" * 60)
    logger.info("PRÓXIMOS PASSOS:")
    logger.info("1. Execute: python scripts/process_files.py")
    logger.info("2. Ou execute: python scripts/sistema_completo.py")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()



