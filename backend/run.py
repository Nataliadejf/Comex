"""
Script de inicialização do backend.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings
import uvicorn

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8000"))
    # No Windows, reload do Uvicorn causa PermissionError no multiprocessing; desabilitar.
    use_reload = settings.debug and os.name != "nt"

    logger.info("=" * 50)
    logger.info("Comex Analyzer - Backend")
    logger.info("=" * 50)
    logger.info(f"Ambiente: {settings.environment}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"Diretório de dados: {settings.data_dir}")
    logger.info(f"Banco de dados: {settings.database_url}")
    logger.info(f"URL: http://0.0.0.0:{port}")
    logger.info("=" * 50)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=use_reload,
        log_level=settings.log_level.lower(),
    )

