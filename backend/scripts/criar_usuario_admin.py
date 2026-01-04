"""
Script para criar usuário administrador inicial.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, Usuario
from auth import get_password_hash

def criar_admin():
    """Cria usuário administrador."""
    init_db()
    db = next(get_db())
    
    try:
        # Verificar se já existe admin
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin:
            logger.warning("Usuário admin já existe!")
            return
        
        # Criar admin
        admin = Usuario(
            username="admin",
            email="admin@comexanalyzer.com",
            senha_hash=get_password_hash("admin123"),  # MUDAR EM PRODUÇÃO!
            nome_completo="Administrador",
            ativo=1
        )
        db.add(admin)
        db.commit()
        
        logger.info("=" * 60)
        logger.info("✅ USUÁRIO ADMIN CRIADO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"Username: admin")
        logger.info(f"Senha: admin123")
        logger.info("⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro ao criar admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    criar_admin()


