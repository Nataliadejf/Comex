"""
Módulo de coleta de dados do Comex Stat.
"""
from .api_client import ComexStatAPIClient
from .collector import DataCollector

# Import opcional do scraper
try:
    from .scraper import ComexStatScraper
    __all__ = [
        "ComexStatAPIClient",
        "ComexStatScraper",
        "DataCollector",
    ]
except ImportError:
    __all__ = [
        "ComexStatAPIClient",
        "DataCollector",
    ]

