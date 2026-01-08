"""
Script para verificar dados no PostgreSQL e importar se necessário.

USO:
    python backend/scripts/verificar_e_importar_dados.py
"""
import sys
from pathlib import Path
import os
from loguru import logger
from sqlalchemy import func

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal, init_db
from database.models import ComercioExterior, Empresa, OperacaoComex

logger.info("="*80)
logger.info("VERIFICAÇÃO E IMPORTAÇÃO DE DADOS")
logger.info("="*80)

def verificar_dados():
    """Verifica se há dados no banco."""
    db = SessionLocal()
    
    try:
        # Verificar tabelas
        logger.info("\n🔍 Verificando dados no banco...")
        
        # ComercioExterior
        total_comex = db.query(func.count(ComercioExterior.id)).scalar() or 0
        logger.info(f"📊 ComercioExterior: {total_comex:,} registros")
        
        if total_comex > 0:
            # Totais
            total_imp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'importacao'
            ).scalar() or 0.0
            
            total_exp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'exportacao'
            ).scalar() or 0.0
            
            logger.info(f"💰 Total Importação: ${total_imp:,.2f}")
            logger.info(f"💰 Total Exportação: ${total_exp:,.2f}")
            logger.info(f"💰 Valor Total: ${total_imp + total_exp:,.2f}")
        
        # Empresas
        total_empresas = db.query(func.count(Empresa.id)).scalar() or 0
        logger.info(f"🏢 Empresas: {total_empresas:,} registros")
        
        # OperacaoComex (tabela antiga)
        total_ops = db.query(func.count(OperacaoComex.id)).scalar() or 0
        logger.info(f"📋 OperacaoComex: {total_ops:,} registros")
        
        logger.info("\n" + "="*80)
        
        if total_comex == 0 and total_empresas == 0 and total_ops == 0:
            logger.warning("⚠️ NENHUM DADO ENCONTRADO NO BANCO!")
            logger.info("\n💡 PRÓXIMOS PASSOS:")
            logger.info("1. Execute: python backend/scripts/importar_excel_local.py")
            logger.info("2. Depois: python backend/scripts/migrar_para_postgresql.py")
            return False
        else:
            logger.success("✅ DADOS ENCONTRADOS NO BANCO!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

def importar_dados_se_necessario():
    """Importa dados se não houver nenhum."""
    db = SessionLocal()
    
    try:
        total_comex = db.query(func.count(ComercioExterior.id)).scalar() or 0
        
        if total_comex > 0:
            logger.info("✅ Dados já existem no banco. Pulando importação.")
            return
        
        logger.info("\n📥 Iniciando importação de dados...")
        
        # Importar usando o script existente
        from scripts.importar_excel_local import main as importar_local
        
        logger.info("Executando importação local primeiro...")
        importar_local()
        
        logger.info("\n✅ Importação local concluída!")
        logger.info("💡 Execute 'python backend/scripts/migrar_para_postgresql.py' para enviar para PostgreSQL")
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    # Verificar dados primeiro
    tem_dados = verificar_dados()
    
    if not tem_dados:
        resposta = input("\n❓ Deseja importar dados agora? (s/n): ")
        if resposta.lower() == 's':
            importar_dados_se_necessario()
        else:
            logger.info("💡 Execute manualmente quando estiver pronto:")
            logger.info("   python backend/scripts/importar_excel_local.py")
            logger.info("   python backend/scripts/migrar_para_postgresql.py")
