"""
Script para migrar dados do SQLite local para PostgreSQL no Render.

USO:
    1. Configure DATABASE_URL com a URL do PostgreSQL do Render
    2. python backend/scripts/migrar_para_postgresql.py
"""
import sys
from pathlib import Path
import os
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database.models import (
    ComercioExterior, Empresa, CNAEHierarquia,
    Base
)

logger.info("="*80)
logger.info("MIGRAÇÃO SQLITE → POSTGRESQL")
logger.info("="*80)


def migrar_dados():
    """Migra dados do SQLite local para PostgreSQL."""
    
    # 1. Conectar ao SQLite local
    db_path = backend_dir.parent / "comex_data" / "database" / "comex.db"
    sqlite_url = f"sqlite:///{db_path.absolute()}"
    
    if not db_path.exists():
        logger.error(f"❌ Banco SQLite não encontrado: {db_path}")
        logger.info("💡 Execute primeiro: python backend/scripts/importar_excel_local.py")
        return
    
    logger.info(f"📁 SQLite local: {db_path}")
    
    sqlite_engine = create_engine(sqlite_url, echo=False)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SqliteSession()
    
    # 2. Conectar ao PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("❌ DATABASE_URL não configurada!")
        logger.info("💡 Configure a variável DATABASE_URL com a URL do PostgreSQL do Render")
        logger.info("   Exemplo: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        sqlite_db.close()
        return
    
    # Converter postgres:// para postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    logger.info(f"📁 PostgreSQL: {database_url[:50]}...")
    
    postgres_engine = create_engine(database_url, echo=False)
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_db = PostgresSession()
    
    try:
        # Criar tabelas no PostgreSQL
        logger.info("🔨 Criando tabelas no PostgreSQL...")
        Base.metadata.create_all(bind=postgres_engine)
        logger.success("✅ Tabelas criadas")
        
        # 3. Migrar ComercioExterior
        logger.info("\n📊 Migrando dados de Comércio Exterior...")
        
        # Limpar tabela no PostgreSQL
        postgres_db.query(ComercioExterior).delete()
        postgres_db.commit()
        
        # Buscar todos do SQLite
        registros_comex = sqlite_db.query(ComercioExterior).all()
        logger.info(f"  📋 Encontrados {len(registros_comex):,} registros no SQLite")
        
        total_valor_imp = 0.0
        total_valor_exp = 0.0
        
        for idx, registro in enumerate(registros_comex):
            # Criar novo registro no PostgreSQL
            novo_registro = ComercioExterior(
                tipo=registro.tipo,
                ncm=registro.ncm,
                descricao_ncm=registro.descricao_ncm,
                estado=registro.estado,
                pais=registro.pais,
                valor_usd=registro.valor_usd,
                peso_kg=registro.peso_kg,
                quantidade=registro.quantidade,
                data=registro.data,
                mes=registro.mes,
                ano=registro.ano,
                mes_referencia=registro.mes_referencia,
                arquivo_origem=registro.arquivo_origem
            )
            postgres_db.add(novo_registro)
            
            # Acumular totais
            if registro.tipo == 'importacao':
                total_valor_imp += registro.valor_usd or 0.0
            else:
                total_valor_exp += registro.valor_usd or 0.0
            
            # Commit a cada 1000 registros
            if (idx + 1) % 1000 == 0:
                postgres_db.commit()
                logger.info(f"  ⏳ Migrados {idx + 1:,} registros...")
        
        postgres_db.commit()
        logger.success(f"✅ {len(registros_comex):,} registros de Comércio Exterior migrados")
        
        # 4. Migrar Empresas
        logger.info("\n🏢 Migrando dados de Empresas...")
        
        # Limpar tabela no PostgreSQL
        postgres_db.query(Empresa).delete()
        postgres_db.commit()
        
        # Buscar todos do SQLite
        empresas = sqlite_db.query(Empresa).all()
        logger.info(f"  📋 Encontradas {len(empresas):,} empresas no SQLite")
        
        for idx, empresa in enumerate(empresas):
            nova_empresa = Empresa(
                nome=empresa.nome,
                cnpj=empresa.cnpj,
                cnae=empresa.cnae,
                estado=empresa.estado,
                tipo=empresa.tipo,
                valor_importacao=empresa.valor_importacao,
                valor_exportacao=empresa.valor_exportacao,
                arquivo_origem=empresa.arquivo_origem
            )
            postgres_db.add(nova_empresa)
            
            if (idx + 1) % 100 == 0:
                postgres_db.commit()
                logger.info(f"  ⏳ Migradas {idx + 1:,} empresas...")
        
        postgres_db.commit()
        logger.success(f"✅ {len(empresas):,} empresas migradas")
        
        # Resumo final
        logger.info("\n" + "="*80)
        logger.info("📊 RESUMO DA MIGRAÇÃO")
        logger.info("="*80)
        logger.info(f"📊 Registros de Comércio Exterior: {len(registros_comex):,}")
        logger.info(f"🏢 Empresas: {len(empresas):,}")
        logger.info(f"💰 Total Importação (USD): ${total_valor_imp:,.2f}")
        logger.info(f"💰 Total Exportação (USD): ${total_valor_exp:,.2f}")
        logger.info(f"💰 Valor Total (USD): ${total_valor_imp + total_valor_exp:,.2f}")
        logger.success("="*80)
        logger.success("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("\n💡 Agora o dashboard deve mostrar os dados!")
        logger.success("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        postgres_db.rollback()
        raise
    finally:
        sqlite_db.close()
        postgres_db.close()


if __name__ == "__main__":
    migrar_dados()
