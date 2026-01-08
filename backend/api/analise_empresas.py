"""
Endpoint para executar análise de empresas recomendadas via API.
Permite executar a análise sem precisar do Shell do Render.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, Any
import sys
from pathlib import Path

from database import get_db
from database.models import EmpresasRecomendadas
from sqlalchemy import func

router = APIRouter(prefix="/api/analise", tags=["análise"])


@router.post("/executar-analise-empresas")
async def executar_analise_empresas(db: Session = Depends(get_db)):
    """
    Executa a análise de empresas recomendadas e cria a tabela consolidada.
    Pode ser chamado via HTTP sem precisar do Shell do Render.
    
    Exemplo de uso:
        POST https://comex-backend-wjco.onrender.com/api/analise/executar-analise-empresas
    """
    try:
        logger.info("="*80)
        logger.info("INICIANDO ANÁLISE DE EMPRESAS RECOMENDADAS VIA API")
        logger.info("="*80)
        
        # Adicionar backend ao path
        backend_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_dir))
        
        # Importar função de análise diretamente
        from scripts.analisar_empresas_recomendadas import consolidar_empresas
        
        # Executar análise
        consolidar_empresas(db)
        
        # Verificar resultado
        total_empresas = db.query(func.count(EmpresasRecomendadas.id)).scalar() or 0
        
        provaveis_imp = db.query(func.count(EmpresasRecomendadas.id)).filter(
            EmpresasRecomendadas.provavel_importador == 1
        ).scalar() or 0
        
        provaveis_exp = db.query(func.count(EmpresasRecomendadas.id)).filter(
            EmpresasRecomendadas.provavel_exportador == 1
        ).scalar() or 0
        
        return {
            "success": True,
            "message": "Análise executada com sucesso",
            "total_empresas": total_empresas,
            "provaveis_importadoras": provaveis_imp,
            "provaveis_exportadoras": provaveis_exp,
        }
        
    except Exception as e:
        logger.error(f"Erro ao executar análise: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar análise: {str(e)}"
        )


@router.get("/status-analise")
async def status_analise(db: Session = Depends(get_db)):
    """
    Retorna o status da análise de empresas recomendadas.
    
    Exemplo de uso:
        GET https://comex-backend-wjco.onrender.com/api/analise/status-analise
    """
    try:
        total_empresas = db.query(func.count(EmpresasRecomendadas.id)).scalar() or 0
        
        if total_empresas == 0:
            return {
                "status": "nao_executada",
                "message": "Análise ainda não foi executada",
                "total_empresas": 0
            }
        
        provaveis_imp = db.query(func.count(EmpresasRecomendadas.id)).filter(
            EmpresasRecomendadas.provavel_importador == 1
        ).scalar() or 0
        
        provaveis_exp = db.query(func.count(EmpresasRecomendadas.id)).filter(
            EmpresasRecomendadas.provavel_exportador == 1
        ).scalar() or 0
        
        # Última atualização
        ultima_analise = db.query(func.max(EmpresasRecomendadas.data_analise)).scalar()
        
        return {
            "status": "executada",
            "message": "Análise já foi executada",
            "total_empresas": total_empresas,
            "provaveis_importadoras": provaveis_imp,
            "provaveis_exportadoras": provaveis_exp,
            "ultima_analise": ultima_analise.isoformat() if ultima_analise else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return {
            "status": "erro",
            "message": f"Erro ao verificar status: {str(e)}",
            "total_empresas": 0
        }


@router.get("/verificar-dados")
async def verificar_dados(db: Session = Depends(get_db)):
    """
    Verifica dados em todas as tabelas.
    
    Exemplo de uso:
        GET https://comex-backend-wjco.onrender.com/api/analise/verificar-dados
    """
    try:
        from database.models import ComercioExterior, Empresa, OperacaoComex, TipoOperacao
        
        resultado = {
            "operacoes_comex": {
                "total": db.query(func.count(OperacaoComex.id)).scalar() or 0,
                "importacoes": db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
                ).scalar() or 0,
                "exportacoes": db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
                ).scalar() or 0,
            },
            "comercio_exterior": {
                "total": db.query(func.count(ComercioExterior.id)).scalar() or 0,
                "importacoes": db.query(func.count(ComercioExterior.id)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar() or 0,
                "exportacoes": db.query(func.count(ComercioExterior.id)).filter(
                    ComercioExterior.tipo == 'exportacao'
                ).scalar() or 0,
            },
            "empresas": {
                "total": db.query(func.count(Empresa.id)).scalar() or 0,
            },
            "empresas_recomendadas": {
                "total": db.query(func.count(EmpresasRecomendadas.id)).scalar() or 0,
                "provaveis_importadoras": db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.provavel_importador == 1
                ).scalar() or 0,
                "provaveis_exportadoras": db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.provavel_exportador == 1
                ).scalar() or 0,
            }
        }
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao verificar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar dados: {str(e)}"
        )
