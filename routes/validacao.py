# ================================================================
# ROUTES - VALIDAÇÃO DE SISTEMA
# ================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger
from database.database import SessionLocal
from database.models import OperacaoComex, CNAEHierarquia

router = APIRouter(tags=["sistema"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/validar-sistema")
def validar_sistema(db: Session = Depends(get_db)):
    """
    Endpoint que valida a conexão ao banco de dados e retorna estatísticas.
    Útil para health checks e debugging.
    """
    try:
        # Testar conexão
        db.execute("SELECT 1")
        
        # Contar registros nas tabelas principais
        total_operacoes = db.query(func.count(OperacaoComex.id)).scalar() or 0
        total_cnae = db.query(func.count(CNAEHierarquia.id)).scalar() or 0
        
        # Estatísticas por tipo de operação (se houver)
        try:
            from database.models import TipoOperacao
            total_exportacoes = db.query(func.count(OperacaoComex.id)).filter(
                OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
            ).scalar() or 0
            total_importacoes = db.query(func.count(OperacaoComex.id)).filter(
                OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
            ).scalar() or 0
        except Exception as e:
            logger.warning(f"Erro ao contar por tipo: {e}")
            total_exportacoes = 0
            total_importacoes = 0
        
        return {
            "status": "ok",
            "banco_dados": {
                "conectado": True,
                "total_registros": {
                    "operacoes": total_operacoes,
                    "cnae": total_cnae,
                    "exportacoes": total_exportacoes,
                    "importacoes": total_importacoes,
                },
            },
            "timestamp": str(__import__("datetime").datetime.now()),
        }
    
    except Exception as e:
        logger.error(f"Erro ao validar sistema: {e}")
        return {
            "status": "erro",
            "banco_dados": {
                "conectado": False,
                "erro": str(e),
            },
            "timestamp": str(__import__("datetime").datetime.now()),
        }
