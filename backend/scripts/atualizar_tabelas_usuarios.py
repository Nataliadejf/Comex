"""
Script para atualizar tabelas de usuários no banco existente.
Adiciona novas colunas se não existirem.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect
from database import get_db, init_db, engine

def atualizar_tabelas():
    """Atualiza tabelas de usuários."""
    logger.info("=" * 60)
    logger.info("ATUALIZANDO TABELAS DE USUÁRIOS")
    logger.info("=" * 60)
    
    # Garantir que todas as tabelas existam
    init_db()
    logger.info("✅ Tabelas base criadas/verificadas")
    
    db = next(get_db())
    
    try:
        inspector = inspect(engine)
        colunas_existentes = [col['name'] for col in inspector.get_columns('usuarios')] if 'usuarios' in inspector.get_table_names() else []
        
        logger.info(f"Colunas existentes na tabela usuarios: {colunas_existentes}")
        
        # Verificar e adicionar colunas que faltam
        colunas_necessarias = {
            'email': 'VARCHAR(255)',
            'senha_hash': 'VARCHAR(255)',
            'nome_completo': 'VARCHAR(255)',
            'data_nascimento': 'DATE',
            'nome_empresa': 'VARCHAR(255)',
            'cpf': 'VARCHAR(14)',
            'cnpj': 'VARCHAR(18)',
            'status_aprovacao': 'VARCHAR(20)',
            'ativo': 'INTEGER',
            'data_criacao': 'DATETIME',
            'data_aprovacao': 'DATETIME',
            'aprovado_por': 'VARCHAR(255)',
            'ultimo_login': 'DATETIME'
        }
        
        for coluna, tipo in colunas_necessarias.items():
            if coluna not in colunas_existentes:
                try:
                    if 'sqlite' in str(engine.url):
                        # SQLite
                        db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}"))
                        logger.info(f"✅ Coluna {coluna} adicionada")
                    else:
                        # PostgreSQL/MySQL
                        db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}"))
                        logger.info(f"✅ Coluna {coluna} adicionada")
                except Exception as e:
                    logger.warning(f"Erro ao adicionar coluna {coluna}: {e}")
        
        db.commit()
        
        # Verificar se tabela de aprovações existe
        if 'aprovacoes_cadastro' not in inspector.get_table_names():
            logger.info("Criando tabela aprovacoes_cadastro...")
            init_db()  # Recriar para garantir que todas as tabelas existam
        
        logger.info("=" * 60)
        logger.info("✅ TABELAS ATUALIZADAS COM SUCESSO!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro ao atualizar tabelas: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    atualizar_tabelas()


