"""
Endpoints de exportação de relatórios.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path

from database import get_db, OperacaoComex
from utils.export import ReportExporter

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/excel")
async def export_to_excel(
    filtros: dict,
    db: Session = Depends(get_db)
):
    """
    Exporta resultados de busca para Excel.
    """
    try:
        # Aplicar filtros (mesma lógica da busca)
        query = db.query(OperacaoComex)
        
        # TODO: Aplicar filtros aqui (reutilizar lógica de busca)
        
        # Limitar a 10000 registros para exportação
        operacoes = query.limit(10000).all()
        
        # Converter para dicionários
        data = [
            {
                "id": op.id,
                "ncm": op.ncm,
                "descricao_produto": op.descricao_produto,
                "tipo_operacao": op.tipo_operacao.value,
                "pais_origem_destino": op.pais_origem_destino,
                "uf": op.uf,
                "valor_fob": op.valor_fob,
                "peso_liquido_kg": op.peso_liquido_kg,
                "data_operacao": op.data_operacao.isoformat(),
            }
            for op in operacoes
        ]
        
        exporter = ReportExporter()
        filepath = exporter.export_to_excel(data)
        
        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filepath.name,
            "records": len(data),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")


@router.post("/csv")
async def export_to_csv(
    filtros: dict,
    db: Session = Depends(get_db)
):
    """
    Exporta resultados de busca para CSV.
    """
    try:
        query = db.query(OperacaoComex)
        operacoes = query.limit(10000).all()
        
        data = [
            {
                "id": op.id,
                "ncm": op.ncm,
                "descricao_produto": op.descricao_produto,
                "tipo_operacao": op.tipo_operacao.value,
                "pais_origem_destino": op.pais_origem_destino,
                "uf": op.uf,
                "valor_fob": op.valor_fob,
                "peso_liquido_kg": op.peso_liquido_kg,
                "data_operacao": op.data_operacao.isoformat(),
            }
            for op in operacoes
        ]
        
        exporter = ReportExporter()
        filepath = exporter.export_to_csv(data)
        
        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filepath.name,
            "records": len(data),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")

