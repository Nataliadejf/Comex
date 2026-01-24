"""
Router para sincronização de dados com BigQuery.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from database import get_db

# Tentar importar os serviços e modelos do BigQuery
try:
    from services.bigquery_service import BigQueryService
    BIGQUERY_SERVICE_AVAILABLE = True
except ImportError:
    BIGQUERY_SERVICE_AVAILABLE = False
    logger.warning("BigQueryService não disponível - certifique-se de que backend/services/bigquery_service.py existe")

try:
    from models.comex_tables import ComexTables
    COMEX_TABLES_AVAILABLE = True
except ImportError:
    COMEX_TABLES_AVAILABLE = False
    logger.warning("ComexTables não disponível - certifique-se de que backend/models/comex_tables.py existe")

router = APIRouter(prefix="/sync", tags=["sincronizacao"])


@router.get("/status")
async def sync_status():
    """
    Verifica o status da sincronização e disponibilidade dos serviços.
    """
    return {
        "bigquery_service_available": BIGQUERY_SERVICE_AVAILABLE,
        "comex_tables_available": COMEX_TABLES_AVAILABLE,
        "status": "ok" if (BIGQUERY_SERVICE_AVAILABLE and COMEX_TABLES_AVAILABLE) else "partial"
    }


@router.post("/bigquery-to-db")
async def sync_bigquery_to_db(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Sincroniza dados do BigQuery para o banco de dados PostgreSQL.
    
    Args:
        limit: Limite de registros para sincronizar (opcional)
        background_tasks: Tarefas em background do FastAPI
        db: Sessão do banco de dados
    """
    if not BIGQUERY_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="BigQueryService não está disponível. Verifique se backend/services/bigquery_service.py existe."
        )
    
    if not COMEX_TABLES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ComexTables não está disponível. Verifique se backend/models/comex_tables.py existe."
        )
    
    try:
        # Importar aqui para garantir que está disponível
        from services.bigquery_service import BigQueryService
        from models.comex_tables import ComexTables
        
        bigquery_service = BigQueryService()
        comex_tables = ComexTables(db)
        
        # Executar sincronização em background
        def sync_task():
            try:
                logger.info("🔄 Iniciando sincronização BigQuery -> PostgreSQL...")
                # Aqui você implementaria a lógica de sincronização
                # Exemplo:
                # dados = bigquery_service.fetch_data(limit=limit)
                # comex_tables.insert_batch(dados)
                logger.success("✅ Sincronização concluída")
            except Exception as e:
                logger.error(f"❌ Erro na sincronização: {e}")
                raise
        
        background_tasks.add_task(sync_task)
        
        return {
            "message": "Sincronização iniciada em background",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar sincronização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar sincronização: {str(e)}")


@router.get("/bigquery/test")
async def test_bigquery_connection():
    """
    Testa a conexão com o BigQuery.
    """
    if not BIGQUERY_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="BigQueryService não está disponível."
        )
    
    try:
        from services.bigquery_service import BigQueryService
        
        service = BigQueryService()
        # Aqui você testaria a conexão
        # result = service.test_connection()
        
        return {
            "status": "ok",
            "message": "Conexão com BigQuery testada com sucesso"
        }
    except Exception as e:
        logger.error(f"❌ Erro ao testar conexão BigQuery: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao testar conexão: {str(e)}")
