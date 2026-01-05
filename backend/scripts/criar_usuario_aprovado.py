"""
Script para criar usuário já aprovado diretamente no banco.
Útil para criar usuário de teste no Render.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from database import get_db, init_db
from database.models import Usuario
from auth import get_password_hash
from loguru import logger
from datetime import datetime

def criar_usuario_aprovado(
    db: Session,
    email: str,
    senha: str,
    nome_completo: str,
    nome_empresa: str = None,
    cpf: str = None,
    cnpj: str = None
):
    """Cria um usuário já aprovado."""
    # Verificar se usuário já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    
    if usuario_existente:
        print(f"⚠️  Usuário com email {email} já existe.")
        resposta = input("Deseja atualizar? (s/N): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada.")
            return False
        
        # Atualizar usuário existente
        usuario_existente.senha_hash = get_password_hash(senha)
        usuario_existente.nome_completo = nome_completo
        usuario_existente.nome_empresa = nome_empresa
        usuario_existente.cpf = cpf
        usuario_existente.cnpj = cnpj
        usuario_existente.status_aprovacao = "aprovado"
        usuario_existente.ativo = 1
        usuario_existente.token_aprovacao = None
        
        try:
            db.commit()
            print(f"✅ Usuário {email} atualizado e aprovado com sucesso!")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Erro ao atualizar usuário: {e}")
            return False
    
    # Criar novo usuário
    try:
        senha_hash = get_password_hash(senha)
        
        novo_usuario = Usuario(
            email=email,
            senha_hash=senha_hash,
            nome_completo=nome_completo,
            nome_empresa=nome_empresa,
            cpf=cpf,
            cnpj=cnpj,
            status_aprovacao="aprovado",
            ativo=1,
            token_aprovacao=None,
            data_criacao=datetime.utcnow()
        )
        
        db.add(novo_usuario)
        db.commit()
        
        print(f"✅ Usuário {email} criado e aprovado com sucesso!")
        print(f"   Nome: {nome_completo}")
        print(f"   Email: {email}")
        print(f"   Status: Aprovado e Ativo")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário: {e}")
        logger.error(f"Erro ao criar usuário: {e}")
        return False

def main():
    """Função principal."""
    print("=" * 80)
    print("👤 Criar Usuário Aprovado")
    print("=" * 80)
    
    # Inicializar banco
    init_db()
    
    # Obter sessão do banco
    db = next(get_db())
    
    try:
        if len(sys.argv) >= 4:
            # Modo linha de comando
            email = sys.argv[1]
            senha = sys.argv[2]
            nome_completo = sys.argv[3]
            nome_empresa = sys.argv[4] if len(sys.argv) > 4 else None
            cpf = sys.argv[5] if len(sys.argv) > 5 else None
            cnpj = sys.argv[6] if len(sys.argv) > 6 else None
            
            criar_usuario_aprovado(
                db, email, senha, nome_completo, nome_empresa, cpf, cnpj
            )
        else:
            # Modo interativo
            print("\nPreencha os dados do usuário:")
            email = input("Email: ")
            senha = input("Senha: ")
            nome_completo = input("Nome Completo: ")
            nome_empresa = input("Nome da Empresa (opcional): ") or None
            cpf = input("CPF (opcional): ") or None
            cnpj = input("CNPJ (opcional): ") or None
            
            criar_usuario_aprovado(
                db, email, senha, nome_completo, nome_empresa, cpf, cnpj
            )
    
    except Exception as e:
        logger.error(f"Erro: {e}")
        print(f"❌ Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

