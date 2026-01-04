"""
Script para criar usuário diretamente no banco de dados.
Contorna problemas de frontend/backend criando o usuário diretamente.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from datetime import datetime
from database import get_db
from database.models import Usuario, AprovacaoCadastro
from auth import get_password_hash
import secrets
from datetime import timedelta

def criar_usuario_direto():
    """Cria usuário diretamente no banco."""
    logger.info("=" * 60)
    logger.info("CRIANDO USUÁRIO DIRETAMENTE NO BANCO")
    logger.info("=" * 60)
    
    db = next(get_db())
    
    try:
        email = "nataliadejesus2@hotmail.com"
        senha_plana = "senha123"  # Senha curta para garantir que funciona
        
        logger.info(f"Email: {email}")
        logger.info(f"Senha: {senha_plana} (será hasheada)")
        
        # Verificar se usuário já existe
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            logger.warning(f"⚠️  Usuário {email} já existe!")
            logger.info("Deletando usuário existente...")
            # Deletar aprovações relacionadas
            db.query(AprovacaoCadastro).filter(AprovacaoCadastro.usuario_id == usuario_existente.id).delete()
            # Deletar usuário
            db.delete(usuario_existente)
            db.commit()
            logger.info("✅ Usuário antigo deletado")
        
        # Criar hash da senha
        logger.info("Criando hash da senha...")
        senha_bytes = len(senha_plana.encode('utf-8'))
        logger.info(f"Tamanho da senha em bytes: {senha_bytes}")
        
        senha_hash = get_password_hash(senha_plana)
        logger.info("✅ Hash criado com sucesso")
        
        # Criar novo usuário
        logger.info("Criando usuário no banco...")
        novo_usuario = Usuario(
            email=email,
            senha_hash=senha_hash,
            nome_completo="Natalia de Jesus",
            data_nascimento=None,
            nome_empresa=None,
            cpf=None,
            cnpj=None,
            status_aprovacao="aprovado",  # Aprovar automaticamente
            ativo=1  # Ativar automaticamente
        )
        
        db.add(novo_usuario)
        db.flush()  # Para obter o ID
        
        # Criar token de aprovação (mesmo que já esteja aprovado)
        token_aprovacao = secrets.token_urlsafe(32)
        data_expiracao = datetime.utcnow() + timedelta(days=7)
        
        aprovacao = AprovacaoCadastro(
            usuario_id=novo_usuario.id,
            token_aprovacao=token_aprovacao,
            email_destino=email,
            status="aprovado",
            data_aprovacao=datetime.utcnow(),
            data_expiracao=data_expiracao
        )
        
        db.add(aprovacao)
        db.commit()
        db.refresh(novo_usuario)
        
        logger.info("=" * 60)
        logger.info("✅ USUÁRIO CRIADO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"Email: {novo_usuario.email}")
        logger.info(f"ID: {novo_usuario.id}")
        logger.info(f"Status: {novo_usuario.status_aprovacao}")
        logger.info(f"Ativo: {novo_usuario.ativo}")
        logger.info("")
        logger.info("✅ Usuário está APROVADO e ATIVO")
        logger.info("✅ Você pode fazer login agora!")
        logger.info("")
        logger.info("Credenciais:")
        logger.info(f"  Email: {email}")
        logger.info(f"  Senha: {senha_plana}")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    criar_usuario_direto()


