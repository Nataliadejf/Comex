"""
Script para criar um usuário de teste diretamente no banco de dados.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db
from database.models import Usuario
from auth import get_password_hash
from loguru import logger

def criar_usuario_teste():
    """Cria um usuário de teste aprovado."""
    try:
        init_db()
        db = next(get_db())
        
        email = "nataliadejesus2@hotmail.com"
        senha = "senha123"
        
        # Verificar se usuário já existe
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        
        if usuario_existente:
            logger.info(f"Usuário {email} já existe. Atualizando...")
            # Atualizar senha e ativar
            usuario_existente.senha_hash = get_password_hash(senha)
            usuario_existente.ativo = 1
            usuario_existente.status_aprovacao = "aprovado"
            db.commit()
            logger.info(f"✅ Usuário {email} atualizado e ativado!")
        else:
            logger.info(f"Criando novo usuário: {email}")
            novo_usuario = Usuario(
                email=email,
                senha_hash=get_password_hash(senha),
                nome_completo="Natalia de Jesus",
                nome_empresa="Teste",
                status_aprovacao="aprovado",
                ativo=1  # Ativo desde o início
            )
            db.add(novo_usuario)
            db.commit()
            logger.info(f"✅ Usuário {email} criado e ativado!")
        
        logger.info(f"   Email: {email}")
        logger.info(f"   Senha: {senha}")
        logger.info(f"   Status: Aprovado e Ativo")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    criar_usuario_teste()

