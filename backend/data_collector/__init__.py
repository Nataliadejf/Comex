"""
Módulo de coleta de dados do Comex Stat.
"""
from .api_client import ComexStatAPIClient
from .collector import DataCollector

# Importar scraper apenas se disponível
try:
    from .scraper import ComexStatScraper
    __all__ = [
        "ComexStatAPIClient",
        "ComexStatScraper",
        "DataCollector",
    ]
except ImportError:
    ComexStatScraper = None
    __all__ = [
        "ComexStatAPIClient",
        "DataCollector",
    ]

