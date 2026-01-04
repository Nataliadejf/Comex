"""
Script para recriar usuário usando bcrypt diretamente (sem passlib).
"""
import sys
from pathlib import Path
from datetime import datetime, date

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy.orm import Session
from database import get_db, Usuario, AprovacaoCadastro, init_db
import bcrypt

def recriar_usuario_com_bcrypt_direto(
    email: str = "nataliadejesus2@hotmail.com",
    password: str = "senha123",
    nome_completo: str = "Natalia de Jesus",
    data_nascimento: date = date(1987, 8, 24),
    nome_empresa: str = "GHT",
    cpf: str = "12220210723",
    cnpj: str = None
):
    logger.info("=" * 60)
    logger.info("RECRIANDO USUÁRIO COM BCRYPT DIRETO")
    logger.info("=" * 60)

    db: Session = next(get_db())

    try:
        # Garantir que as tabelas existam
        init_db()
        logger.info("✅ Tabelas verificadas/criadas.")

        # Verificar se o usuário já existe
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_user:
            logger.warning(f"⚠️ Usuário com email {email} já existe. Atualizando...")
            user = existing_user
        else:
            user = Usuario()
            logger.info(f"Criando novo usuário: {email}")

        # Hash da senha usando bcrypt DIRETAMENTE (sem passlib)
        logger.info(f"🔐 Criando hash da senha usando bcrypt direto...")
        senha_bytes = password.encode('utf-8')
        logger.info(f"   Tamanho da senha: {len(senha_bytes)} bytes")
        
        # Truncar se necessário
        if len(senha_bytes) > 72:
            senha_bytes = senha_bytes[:72]
            logger.warning(f"   ⚠️ Senha truncada para 72 bytes")
        
        hash_bytes = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
        hashed_password = hash_bytes.decode('utf-8')
        logger.info(f"   ✅ Hash criado com sucesso!")

        # Preencher dados do usuário
        user.email = email
        user.senha_hash = hashed_password
        user.nome_completo = nome_completo
        user.data_nascimento = data_nascimento
        user.nome_empresa = nome_empresa
        user.cpf = cpf
        user.cnpj = cnpj
        user.status_aprovacao = "aprovado"  # Aprovado automaticamente
        user.ativo = 1  # Ativo automaticamente
        user.data_criacao = datetime.utcnow()
        user.ultimo_login = datetime.utcnow()

        if not existing_user:
            db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Usuário '{email}' criado/atualizado com sucesso (ID: {user.id}).")

        # Testar login
        logger.info(f"\n🧪 Testando verificação de senha...")
        senha_test_bytes = password.encode('utf-8')
        if len(senha_test_bytes) > 72:
            senha_test_bytes = senha_test_bytes[:72]
        verificacao = bcrypt.checkpw(senha_test_bytes, hashed_password.encode('utf-8'))
        logger.info(f"   ✅ Verificação de senha: {verificacao}")

        # Remover aprovações pendentes antigas para este usuário
        db.query(AprovacaoCadastro).filter(AprovacaoCadastro.usuario_id == user.id).delete()
        db.commit()
        logger.info(f"✅ Aprovações de cadastro antigas para {email} removidas.")

        logger.info("=" * 60)
        logger.info("✅ USUÁRIO CRIADO E ATIVADO COM SUCESSO!")
        logger.info("=" * 60)
        logger.info(f"Email: {email}")
        logger.info(f"Senha: {password}")
        logger.info("Agora você pode fazer login no frontend.")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recriar_usuario_com_bcrypt_direto()


