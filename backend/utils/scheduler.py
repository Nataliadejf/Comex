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


class DataScheduler:
    """Agendador para atualização automática de dados."""
    
    def __init__(self):
        self.collector = DataCollector()
        self.running = False
    
    async def _collect_data_task(self):
        """Tarefa assíncrona de coleta de dados."""
        logger.info("Iniciando coleta automática de dados")
        
        # Obter sessão do banco
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            stats = await self.collector.collect_recent_data(db)
            logger.info(
                f"Coleta automática concluída: {stats['total_registros']} registros"
            )
        except Exception as e:
            logger.error(f"Erro na coleta automática: {e}")
        finally:
            db.close()
    
    def start(self):
        """Inicia o agendador."""
        if self.running:
            logger.warning("Agendador já está em execução")
            return
        
        # Agendar coleta diária às 02:00 da manhã
        schedule.every().day.at("02:00").do(
            lambda: asyncio.run(self._collect_data_task())
        )
        
        self.running = True
        logger.info("Agendador iniciado: coleta diária às 02:00")
        
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

