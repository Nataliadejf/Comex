"""
Script para coletar dados do Comex Stat e popular o banco de dados.
"""
import sys
import asyncio
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db
from data_collector import DataCollector
from loguru import logger

async def main():
    """Função principal para coletar dados."""
    logger.info("=" * 60)
    logger.info("INICIANDO COLETA DE DADOS DO COMEX STAT")
    logger.info("=" * 60)
    
    # Inicializar banco de dados
    init_db()
    logger.info("Banco de dados inicializado")
    
    # Obter sessão do banco
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Criar coletor
        collector = DataCollector()
        
        # Coletar dados
        logger.info("Iniciando coleta...")
        stats = await collector.collect_recent_data(db)
        
        # Exibir resultados
        logger.info("=" * 60)
        logger.info("COLETA CONCLUÍDA!")
        logger.info("=" * 60)
        logger.info(f"Total de registros coletados: {stats.get('total_registros', 0)}")
        logger.info(f"Meses processados: {len(stats.get('meses_processados', []))}")
        logger.info(f"Usou API: {stats.get('usou_api', False)}")
        
        if stats.get('meses_processados'):
            logger.info(f"Meses: {', '.join(stats['meses_processados'])}")
        
        if stats.get('erros'):
            logger.warning(f"Erros encontrados: {len(stats['erros'])}")
            for erro in stats['erros']:
                logger.error(f"  - {erro}")
        else:
            logger.success("Nenhum erro encontrado!")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro durante a coleta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

