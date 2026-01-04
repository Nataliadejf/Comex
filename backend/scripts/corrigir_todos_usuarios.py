"""
Script para corrigir TODOS os usuários no banco, recriando seus hashes com bcrypt direto.
"""
import sys
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy.orm import Session
from database import get_db, Usuario, init_db
import bcrypt

def corrigir_todos_usuarios():
    """Recria hashes de todos os usuários usando bcrypt direto."""
    logger.info("=" * 60)
    logger.info("CORRIGINDO TODOS OS USUÁRIOS")
    logger.info("=" * 60)

    db: Session = next(get_db())

    try:
        # Garantir que as tabelas existam
        init_db()
        logger.info("✅ Tabelas verificadas/criadas.")

        # Buscar todos os usuários
        usuarios = db.query(Usuario).all()
        logger.info(f"📋 Encontrados {len(usuarios)} usuário(s) no banco.")

        if len(usuarios) == 0:
            logger.warning("⚠️ Nenhum usuário encontrado no banco.")
            logger.info("Execute RECRIAR_USUARIO.bat para criar um usuário.")
            return

        for user in usuarios:
            logger.info(f"\n🔧 Corrigindo usuário: {user.email}")
            
            # Se o usuário tem senha antiga (hash de passlib), vamos recriar
            # Para isso, vamos usar uma senha padrão temporária
            # IMPORTANTE: Isso só funciona se você souber a senha original
            # Ou vamos criar uma nova senha padrão
            
            # Vamos criar um hash novo com senha padrão "senha123"
            senha_padrao = "senha123"
            logger.info(f"   Criando novo hash com senha padrão...")
            
            senha_bytes = senha_padrao.encode('utf-8')
            if len(senha_bytes) > 72:
                senha_bytes = senha_bytes[:72]
            
            hash_bytes = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
            novo_hash = hash_bytes.decode('utf-8')
            
            user.senha_hash = novo_hash
            user.status_aprovacao = "aprovado"
            user.ativo = 1
            
            logger.info(f"   ✅ Hash atualizado para {user.email}")
            
            # Testar o novo hash
            verificacao = bcrypt.checkpw(senha_bytes, hash_bytes)
            logger.info(f"   ✅ Verificação: {verificacao}")

        db.commit()
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODOS OS USUÁRIOS CORRIGIDOS!")
        logger.info("=" * 60)
        logger.info("📋 SENHA PADRÃO PARA TODOS OS USUÁRIOS:")
        logger.info("   senha123")
        logger.info("\nAgora você pode fazer login com qualquer email do banco")
        logger.info("usando a senha: senha123")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Erro ao corrigir usuários: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    corrigir_todos_usuarios()


