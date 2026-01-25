"""
Endpoint para coletar dados públicos de empresas importadoras/exportadoras.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from database import get_db, SessionLocal

try:
    from data_collector.public_company_collector import PublicCompanyCollector
    COLLECTOR_AVAILABLE = True
except ImportError as e:
    COLLECTOR_AVAILABLE = False
    logger.error(f"❌ Erro ao importar PublicCompanyCollector: {e}")
    logger.error(f"   Traceback completo: {__import__('traceback').format_exc()}")
except Exception as e:
    COLLECTOR_AVAILABLE = False
    logger.error(f"❌ Erro inesperado ao importar PublicCompanyCollector: {e}")

router = APIRouter(prefix="/api", tags=["coleta-publica"])


class ColetaRequest(BaseModel):
    """Modelo de requisição para coleta."""
    limite_por_fonte: int = 100
    termos_busca: Optional[List[str]] = None
    salvar_csv: bool = False
    salvar_json: bool = False
    integrar_banco: bool = True


@router.post("/coletar-dados-publicos")
async def coletar_dados_publicos(
    request: ColetaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Coleta dados públicos de empresas importadoras/exportadoras."""
    if not COLLECTOR_AVAILABLE:
        import traceback
        error_detail = f"PublicCompanyCollector não está disponível. Verifique os logs do servidor para mais detalhes."
        logger.error(f"❌ {error_detail}")
        raise HTTPException(
            status_code=503,
            detail=error_detail
        )
    
    try:
        collector = PublicCompanyCollector()
        
        def executar_coleta():
            # Criar nova sessão para background task
            db_bg = SessionLocal()
            try:
                logger.info("🔄 Iniciando coleta de dados públicos...")
                dados = collector.coletar_todos(limite_por_fonte=request.limite_por_fonte)
                
                if request.salvar_csv:
                    collector.salvar_csv()
                
                if request.salvar_json:
                    collector.salvar_json()
                
                if request.integrar_banco:
                    stats = collector.integrar_banco_dados(db_bg)
                    logger.info(f"✅ Coleta concluída: {stats['registros_inseridos']} registros inseridos")
                
                logger.success("✅ Coleta de dados públicos concluída")
            except Exception as e:
                logger.error(f"❌ Erro na coleta: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                db_bg.close()
        
        background_tasks.add_task(executar_coleta)
        
        return {
            "message": "Coleta de dados públicos iniciada em background",
            "status": "started",
            "limite_por_fonte": request.limite_por_fonte,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar coleta: {str(e)}")


@router.get("/coletar-dados-publicos/status")
async def status_coleta_publica() -> Dict[str, Any]:
    """Verifica o status do coletor de dados públicos."""
    import traceback
    error_info = None
    if not COLLECTOR_AVAILABLE:
        try:
            # Tentar importar novamente para capturar o erro
            from data_collector.public_company_collector import PublicCompanyCollector
        except Exception as e:
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
    
    return {
        "collector_available": COLLECTOR_AVAILABLE,
        "status": "ok" if COLLECTOR_AVAILABLE else "unavailable",
        "error_info": error_info
    }
