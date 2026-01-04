"""
Script para deletar e recriar as tabelas de login e aprovação.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect
from database import get_db, engine, Base
from database.models import Usuario, AprovacaoCadastro

def deletar_e_recriar_tabelas():
    """Deleta e recria as tabelas de login e aprovação."""
    logger.info("=" * 60)
    logger.info("DELETANDO E RECRIANDO TABELAS DE LOGIN E APROVAÇÃO")
    logger.info("=" * 60)
    
    try:
        # Fechar todas as conexões existentes
        engine.dispose()
        
        db = next(get_db())
        inspector = inspect(engine)
        
        # Listar tabelas existentes
        tabelas_existentes = inspector.get_table_names()
        logger.info(f"Tabelas existentes: {tabelas_existentes}")
        
        # Deletar tabela de aprovações primeiro (tem foreign key)
        if 'aprovacoes_cadastro' in tabelas_existentes:
            logger.info("🗑️  Deletando tabela aprovacoes_cadastro...")
            try:
                db.execute(text("DROP TABLE IF EXISTS aprovacoes_cadastro"))
                db.commit()
                logger.info("✅ Tabela aprovacoes_cadastro deletada")
            except Exception as e:
                logger.warning(f"⚠️  Erro ao deletar aprovacoes_cadastro: {e}")
                db.rollback()
        
        # Deletar tabela de usuários
        if 'usuarios' in tabelas_existentes:
            logger.info("🗑️  Deletando tabela usuarios...")
            try:
                db.execute(text("DROP TABLE IF EXISTS usuarios"))
                db.commit()
                logger.info("✅ Tabela usuarios deletada")
            except Exception as e:
                logger.warning(f"⚠️  Erro ao deletar usuarios: {e}")
                db.rollback()
        
        # Aguardar um pouco para garantir que as tabelas foram deletadas
        import time
        time.sleep(1)
        
        # Recriar tabelas usando SQLAlchemy
        logger.info("")
        logger.info("🔨 Recriando tabelas...")
        logger.info("")
        
        # Criar apenas as tabelas de login e aprovação
        Usuario.__table__.create(bind=engine, checkfirst=True)
        logger.info("✅ Tabela usuarios criada")
        
        AprovacaoCadastro.__table__.create(bind=engine, checkfirst=True)
        logger.info("✅ Tabela aprovacoes_cadastro criada")
        
        # Verificar se foram criadas corretamente
        inspector = inspect(engine)
        tabelas_criadas = inspector.get_table_names()
        logger.info(f"Tabelas criadas: {tabelas_criadas}")
        
        if 'usuarios' in tabelas_criadas:
            colunas = [col['name'] for col in inspector.get_columns('usuarios')]
            logger.info("")
            logger.info("Colunas na tabela usuarios:")
            for col in colunas:
                logger.info(f"  ✅ {col}")
            
            # Verificar colunas críticas
            colunas_necessarias = [
                'id', 'email', 'senha_hash', 'nome_completo', 
                'data_nascimento', 'nome_empresa', 'cpf', 'cnpj',
                'status_aprovacao', 'ativo', 'data_criacao',
                'data_aprovacao', 'aprovado_por', 'ultimo_login'
            ]
            
            faltando = [c for c in colunas_necessarias if c not in colunas]
            if faltando:
                logger.error(f"❌ Colunas faltando: {faltando}")
            else:
                logger.info("")
                logger.info("✅ Todas as colunas necessárias estão presentes!")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ TABELAS RECRIADAS COM SUCESSO!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Agora você pode:")
        logger.info("1. Reiniciar o backend")
        logger.info("2. Cadastrar novos usuários")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Erro ao recriar tabelas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
        engine.dispose()

if __name__ == "__main__":
    deletar_e_recriar_tabelas()


