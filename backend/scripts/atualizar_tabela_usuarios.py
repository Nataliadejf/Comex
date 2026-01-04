"""
Script para atualizar a tabela usuarios adicionando colunas que faltam.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect
from database import get_db, init_db, engine
from config import settings

def atualizar_tabela_usuarios():
    """Atualiza a tabela usuarios adicionando colunas que faltam."""
    logger.info("=" * 60)
    logger.info("ATUALIZANDO TABELA USUARIOS")
    logger.info("=" * 60)
    
    db = next(get_db())
    
    try:
        inspector = inspect(engine)
        
        # Verificar se a tabela existe
        if 'usuarios' not in inspector.get_table_names():
            logger.info("Tabela usuarios não existe. Criando...")
            init_db()
            logger.info("✅ Tabela usuarios criada")
            return
        
        # Obter colunas existentes
        colunas_existentes = [col['name'] for col in inspector.get_columns('usuarios')]
        logger.info(f"Colunas existentes: {colunas_existentes}")
        
        # Colunas que devem existir
        colunas_necessarias = {
            'email': 'VARCHAR(255) NOT NULL',
            'senha_hash': 'VARCHAR(255) NOT NULL',
            'nome_completo': 'VARCHAR(255) NOT NULL',
            'data_nascimento': 'DATE',
            'nome_empresa': 'VARCHAR(255)',
            'cpf': 'VARCHAR(14)',
            'cnpj': 'VARCHAR(18)',
            'status_aprovacao': 'VARCHAR(20) DEFAULT "pendente" NOT NULL',
            'ativo': 'INTEGER DEFAULT 0 NOT NULL',
            'data_criacao': 'DATETIME',
            'data_aprovacao': 'DATETIME',
            'aprovado_por': 'VARCHAR(255)',
            'ultimo_login': 'DATETIME'
        }
        
        # Adicionar colunas que faltam
        colunas_adicionadas = []
        for coluna, tipo in colunas_necessarias.items():
            if coluna not in colunas_existentes:
                try:
                    if 'sqlite' in str(engine.url):
                        # SQLite - ALTER TABLE ADD COLUMN (SQLite não suporta DEFAULT em ALTER TABLE)
                        # Remover DEFAULT se presente para SQLite
                        tipo_sqlite = tipo.replace(' DEFAULT "pendente"', '').replace(' DEFAULT 0', '')
                        db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo_sqlite}"))
                        logger.info(f"✅ Coluna {coluna} adicionada")
                        colunas_adicionadas.append(coluna)
                        
                        # Se for status_aprovacao ou ativo, atualizar valores padrão
                        if coluna == 'status_aprovacao':
                            db.execute(text("UPDATE usuarios SET status_aprovacao = 'pendente' WHERE status_aprovacao IS NULL"))
                        elif coluna == 'ativo':
                            db.execute(text("UPDATE usuarios SET ativo = 0 WHERE ativo IS NULL"))
                    else:
                        # PostgreSQL/MySQL
                        db.execute(text(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}"))
                        logger.info(f"✅ Coluna {coluna} adicionada")
                        colunas_adicionadas.append(coluna)
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao adicionar coluna {coluna}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        db.commit()
        
        if colunas_adicionadas:
            logger.info(f"✅ {len(colunas_adicionadas)} colunas adicionadas: {', '.join(colunas_adicionadas)}")
        else:
            logger.info("✅ Todas as colunas já existem")
        
        # Verificar se tabela de aprovações existe
        if 'aprovacoes_cadastro' not in inspector.get_table_names():
            logger.info("Criando tabela aprovacoes_cadastro...")
            init_db()
            logger.info("✅ Tabela aprovacoes_cadastro criada")
        
        logger.info("=" * 60)
        logger.info("✅ TABELA ATUALIZADA COM SUCESSO!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar tabela: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    atualizar_tabela_usuarios()

