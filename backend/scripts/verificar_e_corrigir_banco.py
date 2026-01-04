"""
Script para verificar e corrigir o banco de dados de forma definitiva.
"""
import sys
from pathlib import Path
import sqlite3
import os

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text, inspect, create_engine
from database import get_db, Base
from database.database import engine
from database.models import Usuario, AprovacaoCadastro
from config import settings

def verificar_e_corrigir():
    """Verifica e corrige o banco de dados."""
    logger.info("=" * 60)
    logger.info("VERIFICANDO E CORRIGINDO BANCO DE DADOS")
    logger.info("=" * 60)
    
    # Mostrar caminho do banco
    db_path = settings.database_url
    logger.info(f"Caminho do banco: {db_path}")
    
    # Se for SQLite, extrair o caminho do arquivo
    if 'sqlite' in db_path:
        if db_path.startswith('sqlite:///'):
            file_path = db_path.replace('sqlite:///', '')
            logger.info(f"Arquivo do banco: {file_path}")
            
            # Criar diretório se não existir
            db_dir = Path(file_path).parent
            if not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Diretório criado: {db_dir}")
    
    try:
        # Fechar todas as conexões
        engine.dispose()
        
        # Conectar diretamente ao SQLite para verificar
        if 'sqlite' in db_path:
            file_path = db_path.replace('sqlite:///', '')
            if os.path.exists(file_path):
                logger.info(f"Banco existe em: {file_path}")
                
                # Conectar diretamente ao SQLite
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                
                # Verificar tabelas existentes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas = [row[0] for row in cursor.fetchall()]
                logger.info(f"Tabelas no banco: {tabelas}")
                
                # Se usuarios existe, verificar colunas
                if 'usuarios' in tabelas:
                    cursor.execute("PRAGMA table_info(usuarios)")
                    colunas = cursor.fetchall()
                    logger.info("Colunas na tabela usuarios:")
                    for col in colunas:
                        logger.info(f"  - {col[1]} ({col[2]})")
                    
                    # Verificar se data_nascimento existe
                    colunas_nomes = [col[1] for col in colunas]
                    if 'data_nascimento' not in colunas_nomes:
                        logger.warning("❌ Coluna data_nascimento NÃO existe!")
                        logger.info("Deletando tabela usuarios...")
                        cursor.execute("DROP TABLE IF EXISTS usuarios")
                        conn.commit()
                        logger.info("✅ Tabela usuarios deletada")
                    else:
                        logger.info("✅ Coluna data_nascimento existe")
                
                # Deletar aprovacoes_cadastro também
                if 'aprovacoes_cadastro' in tabelas:
                    logger.info("Deletando tabela aprovacoes_cadastro...")
                    cursor.execute("DROP TABLE IF EXISTS aprovacoes_cadastro")
                    conn.commit()
                    logger.info("✅ Tabela aprovacoes_cadastro deletada")
                
                conn.close()
        
        # Recriar usando SQLAlchemy
        logger.info("")
        logger.info("Recriando tabelas com SQLAlchemy...")
        
        # Criar engine novo para garantir
        new_engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
            echo=False
        )
        
        # Criar tabelas
        Base.metadata.create_all(bind=new_engine)
        logger.info("✅ Tabelas criadas")
        
        # Verificar novamente
        inspector = inspect(new_engine)
        tabelas_criadas = inspector.get_table_names()
        logger.info(f"Tabelas criadas: {tabelas_criadas}")
        
        if 'usuarios' in tabelas_criadas:
            colunas = [col['name'] for col in inspector.get_columns('usuarios')]
            logger.info("")
            logger.info("Colunas na tabela usuarios:")
            for col in colunas:
                logger.info(f"  ✅ {col}")
            
            if 'data_nascimento' in colunas:
                logger.info("")
                logger.info("✅ SUCESSO! Coluna data_nascimento existe!")
            else:
                logger.error("")
                logger.error("❌ ERRO! Coluna data_nascimento ainda não existe!")
        
        new_engine.dispose()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ PROCESSO CONCLUÍDO!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    verificar_e_corrigir()

