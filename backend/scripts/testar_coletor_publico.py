"""
Script para testar o coletor de dados públicos.
Execute: python backend/scripts/testar_coletor_publico.py
"""
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db
from data_collector.public_company_collector import PublicCompanyCollector
from loguru import logger

def main():
    """Testa o coletor de dados públicos."""
    logger.info("=" * 60)
    logger.info("TESTE DO COLETOR DE DADOS PÚBLICOS")
    logger.info("=" * 60)
    
    # Inicializar banco de dados
    try:
        init_db()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao inicializar banco: {e}")
    
    # Obter sessão do banco
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Criar coletor
        collector = PublicCompanyCollector()
        logger.info("✅ Coletor criado")
        
        # Testar coleta (limite pequeno para teste)
        logger.info("🔄 Iniciando coleta de teste (limite: 10)...")
        dados = collector.coletar_todos(limite_por_fonte=10)
        
        logger.info("=" * 60)
        logger.info("RESULTADOS DA COLETA")
        logger.info("=" * 60)
        logger.info(f"Total de registros coletados: {len(dados)}")
        
        if dados:
            logger.info("\n📋 Primeiros 3 registros:")
            for i, registro in enumerate(dados[:3], 1):
                logger.info(f"\n{i}. Empresa: {registro.get('empresa_nome', 'N/A')}")
                logger.info(f"   NCM: {registro.get('ncm', 'N/A')}")
                logger.info(f"   Tipo: {registro.get('tipo_operacao', 'N/A')}")
                logger.info(f"   Fonte: {registro.get('fonte', 'N/A')}")
            
            # Salvar em CSV
            caminho_csv = collector.salvar_csv()
            logger.info(f"\n💾 Dados salvos em CSV: {caminho_csv}")
        else:
            logger.warning("⚠️ Nenhum dado coletado")
        
        # Testar integração com banco (opcional)
        logger.info("\n🔄 Testando integração com banco de dados...")
        try:
            stats = collector.integrar_banco_dados(db)
            logger.info(f"✅ Integração concluída: {stats['registros_inseridos']} inseridos")
        except Exception as e:
            logger.error(f"❌ Erro na integração: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ TESTE CONCLUÍDO!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
