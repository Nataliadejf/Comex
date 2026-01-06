"""
Agendador de tarefas para atualização automática de dados.
"""
import schedule
import time
import asyncio
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from data_collector import DataCollector

# Import opcional do atualizador de dados
try:
    from utils.data_updater import DataUpdater
    DATA_UPDATER_AVAILABLE = True
except ImportError:
    DATA_UPDATER_AVAILABLE = False
    logger.warning("DataUpdater não disponível - atualizações limitadas")


class DataScheduler:
    """Agendador para atualização automática de dados."""
    
    def __init__(self):
        self.collector = DataCollector()
        self.updater = DataUpdater() if DATA_UPDATER_AVAILABLE else None
        self.running = False
    
    async def _collect_data_task(self):
        """Tarefa assíncrona de coleta de dados."""
        logger.info("Iniciando coleta automática de dados")
        
        # Obter sessão do banco
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Tentar coletor enriquecido primeiro (dados reais do MDIC)
            try:
                from data_collector.enriched_collector import EnrichedDataCollector
                enriched_collector = EnrichedDataCollector()
                stats = await enriched_collector.collect_and_enrich(db, meses=1)  # Último mês apenas
                logger.info(
                    f"✅ Coleta enriquecida concluída: {stats['total_registros']} registros, "
                    f"{stats['empresas_enriquecidas']} empresas enriquecidas"
                )
            except Exception as e:
                logger.warning(f"Coletor enriquecido não disponível, usando coletor padrão: {e}")
                # Fallback para coletor padrão
                stats = await self.collector.collect_recent_data(db)
                logger.info(
                    f"Coleta automática concluída: {stats['total_registros']} registros"
                )
        except Exception as e:
            logger.error(f"Erro na coleta automática: {e}")
        finally:
            db.close()
    
    async def _update_empresas_task(self):
        """Tarefa assíncrona de atualização de empresas MDIC."""
        if not self.updater:
            return
        
        logger.info("Iniciando atualização de empresas MDIC")
        try:
            resultado = await self.updater.atualizar_empresas_mdic()
            if resultado.get("success"):
                logger.info(f"✅ Empresas MDIC atualizadas: {resultado['total_empresas']} empresas")
            else:
                logger.warning(f"⚠️ Erro ao atualizar empresas MDIC: {resultado.get('error')}")
        except Exception as e:
            logger.error(f"Erro na atualização de empresas: {e}")
    
    async def _update_relacionamentos_task(self):
        """Tarefa assíncrona de atualização de relacionamentos."""
        if not self.updater:
            return
        
        logger.info("Iniciando atualização de relacionamentos")
        try:
            resultado = await self.updater.atualizar_relacionamentos()
            if resultado.get("success"):
                logger.info(f"✅ Relacionamentos atualizados: {resultado['operacoes_identificadas']}/{resultado['total_operacoes']}")
            else:
                logger.warning(f"⚠️ Erro ao atualizar relacionamentos: {resultado.get('error')}")
        except Exception as e:
            logger.error(f"Erro na atualização de relacionamentos: {e}")
    
    async def _update_sinergias_task(self):
        """Tarefa assíncrona de atualização de sinergias."""
        if not self.updater:
            return
        
        logger.info("Iniciando atualização de sinergias")
        try:
            resultado = await self.updater.atualizar_sinergias()
            if resultado.get("success"):
                logger.info(f"✅ Sinergias atualizadas: {resultado['empresas_analisadas']} empresas")
            else:
                logger.warning(f"⚠️ Erro ao atualizar sinergias: {resultado.get('error')}")
        except Exception as e:
            logger.error(f"Erro na atualização de sinergias: {e}")
    
    def start(self):
        """Inicia o agendador."""
        if self.running:
            logger.warning("Agendador já está em execução")
            return
        
        # Agendar coleta diária às 02:00 da manhã
        schedule.every().day.at("02:00").do(
            lambda: asyncio.run(self._collect_data_task())
        )
        
        # Agendar atualização de empresas MDIC semanalmente (domingo às 03:00)
        if self.updater:
            schedule.every().sunday.at("03:00").do(
                lambda: asyncio.run(self._update_empresas_task())
            )
            
            # Agendar atualização de relacionamentos diariamente às 03:30
            schedule.every().day.at("03:30").do(
                lambda: asyncio.run(self._update_relacionamentos_task())
            )
            
            # Agendar atualização de sinergias diariamente às 04:00
            schedule.every().day.at("04:00").do(
                lambda: asyncio.run(self._update_sinergias_task())
            )
        
        self.running = True
        logger.info("Agendador iniciado: coleta diária às 02:00")
        if self.updater:
            logger.info("Atualizações agendadas: empresas (domingo 03:00), relacionamentos (03:30), sinergias (04:00)")
        
        # Executar loop do agendador em thread separada
        import threading
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def stop(self):
        """Para o agendador."""
        self.running = False
        schedule.clear()
        logger.info("Agendador parado")

