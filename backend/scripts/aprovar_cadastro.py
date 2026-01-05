"""
Script para aprovar cadastros pendentes.
Pode ser usado localmente ou no Render via Shell.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from database import get_db, init_db
from database.models import Usuario, AprovacaoCadastro
from loguru import logger
from datetime import datetime

def listar_cadastros_pendentes(db: Session):
    """Lista todos os cadastros pendentes."""
    usuarios = db.query(Usuario).filter(
        Usuario.status_aprovacao == "pendente"
    ).all()
    
    if not usuarios:
        print("✅ Nenhum cadastro pendente encontrado.")
        return []
    
    print(f"\n📋 Cadastros Pendentes ({len(usuarios)}):")
    print("=" * 80)
    for i, usuario in enumerate(usuarios, 1):
        print(f"\n{i}. Email: {usuario.email}")
        print(f"   Nome: {usuario.nome_completo}")
        print(f"   Empresa: {usuario.nome_empresa or 'N/A'}")
        print(f"   CPF/CNPJ: {usuario.cpf or usuario.cnpj or 'N/A'}")
        print(f"   Data Cadastro: {usuario.data_criacao}")
        print(f"   Token Aprovação: {usuario.token_aprovacao}")
    
    return usuarios

def aprovar_por_email(db: Session, email: str):
    """Aprova cadastro por email."""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario:
        print(f"❌ Usuário com email {email} não encontrado.")
        return False
    
    if usuario.status_aprovacao == "aprovado":
        print(f"✅ Usuário {email} já está aprovado.")
        return True
    
    try:
        # Atualizar usuário
        usuario.status_aprovacao = "aprovado"
        usuario.ativo = 1
        usuario.token_aprovacao = None
        
        # Atualizar aprovação se existir
        aprovacao = db.query(AprovacaoCadastro).filter(
            AprovacaoCadastro.usuario_id == usuario.id
        ).first()
        
        if aprovacao:
            aprovacao.status = "aprovado"
            aprovacao.data_aprovacao = datetime.utcnow()
        
        db.commit()
        print(f"✅ Cadastro de {email} aprovado com sucesso!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao aprovar cadastro: {e}")
        return False

def aprovar_por_token(db: Session, token: str):
    """Aprova cadastro por token."""
    aprovacao = db.query(AprovacaoCadastro).filter(
        AprovacaoCadastro.token_aprovacao == token
    ).first()
    
    if not aprovacao:
        print(f"❌ Token de aprovação {token} não encontrado.")
        return False
    
    if aprovacao.status == "aprovado":
        print(f"✅ Cadastro já está aprovado.")
        return True
    
    usuario = db.query(Usuario).filter(Usuario.id == aprovacao.usuario_id).first()
    
    if not usuario:
        print(f"❌ Usuário associado ao token não encontrado.")
        return False
    
    try:
        # Atualizar usuário
        usuario.status_aprovacao = "aprovado"
        usuario.ativo = 1
        usuario.token_aprovacao = None
        
        # Atualizar aprovação
        aprovacao.status = "aprovado"
        aprovacao.data_aprovacao = datetime.utcnow()
        
        db.commit()
        print(f"✅ Cadastro de {usuario.email} aprovado com sucesso!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao aprovar cadastro: {e}")
        return False

def aprovar_todos(db: Session):
    """Aprova todos os cadastros pendentes."""
    usuarios = db.query(Usuario).filter(
        Usuario.status_aprovacao == "pendente"
    ).all()
    
    if not usuarios:
        print("✅ Nenhum cadastro pendente para aprovar.")
        return
    
    print(f"\n⚠️  ATENÇÃO: Você está prestes a aprovar {len(usuarios)} cadastro(s).")
    confirmacao = input("Deseja continuar? (s/N): ")
    
    if confirmacao.lower() != 's':
        print("❌ Operação cancelada.")
        return
    
    aprovados = 0
    for usuario in usuarios:
        if aprovar_por_email(db, usuario.email):
            aprovados += 1
    
    print(f"\n✅ {aprovados} de {len(usuarios)} cadastros aprovados com sucesso!")

def main():
    """Função principal."""
    print("=" * 80)
    print("🔐 Script de Aprovação de Cadastros")
    print("=" * 80)
    
    # Inicializar banco
    init_db()
    
    # Obter sessão do banco
    db = next(get_db())
    
    try:
        if len(sys.argv) > 1:
            comando = sys.argv[1]
            
            if comando == "listar" or comando == "ls":
                listar_cadastros_pendentes(db)
            
            elif comando == "aprovar" or comando == "ap":
                if len(sys.argv) < 3:
                    print("❌ Uso: python aprovar_cadastro.py aprovar <email>")
                    print("   ou: python aprovar_cadastro.py aprovar --token <token>")
                    return
                
                if sys.argv[2] == "--token" or sys.argv[2] == "-t":
                    if len(sys.argv) < 4:
                        print("❌ Token não fornecido.")
                        return
                    aprovar_por_token(db, sys.argv[3])
                else:
                    aprovar_por_email(db, sys.argv[2])
            
            elif comando == "todos" or comando == "all":
                aprovar_todos(db)
            
            else:
                print(f"❌ Comando desconhecido: {comando}")
                print("\nComandos disponíveis:")
                print("  listar, ls          - Lista cadastros pendentes")
                print("  aprovar <email>     - Aprova cadastro por email")
                print("  aprovar --token <t>  - Aprova cadastro por token")
                print("  todos, all          - Aprova todos os cadastros pendentes")
        else:
            # Modo interativo
            print("\nEscolha uma opção:")
            print("1. Listar cadastros pendentes")
            print("2. Aprovar por email")
            print("3. Aprovar por token")
            print("4. Aprovar todos")
            print("0. Sair")
            
            opcao = input("\nOpção: ")
            
            if opcao == "1":
                listar_cadastros_pendentes(db)
            elif opcao == "2":
                email = input("Digite o email: ")
                aprovar_por_email(db, email)
            elif opcao == "3":
                token = input("Digite o token: ")
                aprovar_por_token(db, token)
            elif opcao == "4":
                aprovar_todos(db)
            else:
                print("Saindo...")
    
    except Exception as e:
        logger.error(f"Erro: {e}")
        print(f"❌ Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

