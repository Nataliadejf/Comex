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
        
        # Última atualização (usar data_atualizacao se disponível)
        try:
            ultima_analise = db.query(func.max(EmpresasRecomendadas.data_atualizacao)).scalar()
        except:
            ultima_analise = None
        
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


@router.post("/correlacionar-empresas-operacoes")
async def executar_correlacao_empresas_operacoes(db: Session = Depends(get_db)):
    """
    Correlaciona empresas da tabela 'empresas' com operações de 'comercio_exterior' e 'operacoes_comex'.
    Atualiza valores de importação/exportação nas empresas baseado nas operações.
    
    Exemplo de uso:
        POST https://comex-backend-wjco.onrender.com/api/analise/correlacionar-empresas-operacoes
    """
    try:
        logger.info("="*80)
        logger.info("INICIANDO CORRELAÇÃO DE EMPRESAS COM OPERAÇÕES VIA API")
        logger.info("="*80)
        
        # Adicionar backend ao path
        backend_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_dir))
        
        # Importar função de correlação
        from scripts.correlacionar_empresas_operacoes import correlacionar_empresas_operacoes
        
        # Executar correlação
        correlacionar_empresas_operacoes()
        
        # Verificar resultado
        from database.models import Empresa
        total_empresas = db.query(func.count(Empresa.id)).scalar() or 0
        empresas_com_valor_imp = db.query(func.count(Empresa.id)).filter(
            Empresa.valor_importacao > 0
        ).scalar() or 0
        empresas_com_valor_exp = db.query(func.count(Empresa.id)).filter(
            Empresa.valor_exportacao > 0
        ).scalar() or 0
        
        total_valor_imp = db.query(func.sum(Empresa.valor_importacao)).scalar() or 0.0
        total_valor_exp = db.query(func.sum(Empresa.valor_exportacao)).scalar() or 0.0
        
        return {
            "success": True,
            "message": "Correlação executada com sucesso",
            "total_empresas": total_empresas,
            "empresas_com_importacao": empresas_com_valor_imp,
            "empresas_com_exportacao": empresas_com_valor_exp,
            "total_valor_importacao_usd": float(total_valor_imp),
            "total_valor_exportacao_usd": float(total_valor_exp),
        }
        
    except Exception as e:
        logger.error(f"Erro ao executar correlação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar correlação: {str(e)}"
        )
