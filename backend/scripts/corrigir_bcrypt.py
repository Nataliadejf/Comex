"""
Script para corrigir problemas com bcrypt.
Remove passlib e instala apenas bcrypt diretamente.
"""
import sys
from pathlib import Path
import subprocess

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger

def corrigir_bcrypt():
    """Remove passlib e instala apenas bcrypt."""
    logger.info("=" * 60)
    logger.info("CORRIGINDO BCRYPT (REMOVENDO PASSLIB)")
    logger.info("=" * 60)
    
    try:
        logger.info("Desinstalando passlib (não vamos mais usar)...")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "passlib"], 
                      cwd=str(backend_dir))
        
        logger.info("Instalando bcrypt 4.0.1...")
        subprocess.run([sys.executable, "-m", "pip", "install", "bcrypt==4.0.1"], 
                      cwd=str(backend_dir))
        
        logger.info("=" * 60)
        logger.info("✅ BCRYPT CORRIGIDO!")
        logger.info("=" * 60)
        logger.info("Agora usamos bcrypt diretamente (sem passlib)")
        logger.info("Execute: RECRIAR_USUARIO.bat")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    corrigir_bcrypt()

