"""
Script para testar login diretamente, sem passar pelo frontend.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy.orm import Session
from database import get_db, Usuario
from auth import verify_password, authenticate_user

def testar_login_direto():
    """Testa login diretamente no banco."""
    logger.info("=" * 60)
    logger.info("TESTANDO LOGIN DIRETO")
    logger.info("=" * 60)
    
    db: Session = next(get_db())
    
    try:
        email = "nataliadejesus2@hotmail.com"
        senha = "senha123"
        
        logger.info(f"\n📧 Email: {email}")
        logger.info(f"🔒 Senha: {senha}")
        
        # Buscar usuário
        user = db.query(Usuario).filter(Usuario.email == email).first()
        
        if not user:
            logger.error(f"❌ Usuário não encontrado: {email}")
            return False
        
        logger.info(f"\n✅ Usuário encontrado:")
        logger.info(f"   ID: {user.id}")
        logger.info(f"   Email: {user.email}")
        logger.info(f"   Status: {user.status_aprovacao}")
        logger.info(f"   Ativo: {user.ativo}")
        logger.info(f"   Hash (primeiros 50 chars): {user.senha_hash[:50]}...")
        
        # Verificar se hash parece ser bcrypt válido
        if not user.senha_hash.startswith('$2'):
            logger.error(f"❌ Hash não parece ser bcrypt válido!")
            logger.error(f"   Hash começa com: {user.senha_hash[:10]}...")
            logger.error("   Execute CORRIGIR_TODOS_USUARIOS.bat novamente")
            return False
        
        logger.info(f"   ✅ Hash parece ser bcrypt válido")
        
        # Testar verificação de senha
        logger.info(f"\n🧪 Testando verificação de senha...")
        logger.info(f"   Tamanho da senha: {len(senha)} caracteres, {len(senha.encode('utf-8'))} bytes")
        
        try:
            resultado = verify_password(senha, user.senha_hash)
            logger.info(f"   ✅ Resultado da verificação: {resultado}")
            
            if resultado:
                logger.info(f"\n✅ LOGIN FUNCIONA DIRETAMENTE!")
            else:
                logger.error(f"\n❌ VERIFICAÇÃO FALHOU!")
                logger.error("   A senha não confere com o hash")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao verificar senha: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        # Testar authenticate_user completo
        logger.info(f"\n🧪 Testando authenticate_user completo...")
        try:
            user_auth = authenticate_user(db, email, senha)
            if user_auth:
                logger.info(f"   ✅ authenticate_user retornou usuário: {user_auth.email}")
            else:
                logger.error(f"   ❌ authenticate_user retornou False")
                logger.error("   Verifique se usuário está ativo e aprovado")
                return False
        except Exception as e:
            logger.error(f"❌ Erro em authenticate_user: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        logger.info("O problema pode estar no frontend ou na comunicação.")
        logger.info("Verifique os logs do backend quando tentar fazer login.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    testar_login_direto()


