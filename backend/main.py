"""
Aplicação principal FastAPI.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel
import uvicorn

from loguru import logger

from config import settings
from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte
from data_collector import DataCollector
from api.export import router as export_router

# Inicializar app FastAPI
app = FastAPI(
    title="Comex Analyzer API",
    description="API para análise de dados do comércio exterior brasileiro",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do frontend Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origem do Electron
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(export_router)


# Inicializar banco de dados na startup
@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados na startup."""
    init_db()
    logger.info("Banco de dados inicializado")


# Schemas Pydantic
class OperacaoResponse(BaseModel):
    """Schema de resposta para operação."""
    id: int
    ncm: str
    descricao_produto: str
    tipo_operacao: str
    pais_origem_destino: str
    uf: str
    valor_fob: float
    data_operacao: date
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Estatísticas do dashboard."""
    volume_importacoes: float
    volume_exportacoes: float
    valor_total_usd: float
    principais_ncms: List[dict]
    principais_paises: List[dict]
    registros_por_mes: dict


class BuscaFiltros(BaseModel):
    """Filtros de busca."""
    ncm: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    tipo_operacao: Optional[str] = None
    pais: Optional[str] = None
    uf: Optional[str] = None
    via_transporte: Optional[str] = None
    valor_fob_min: Optional[float] = None
    valor_fob_max: Optional[float] = None
    peso_min: Optional[float] = None
    peso_max: Optional[float] = None
    page: int = 1
    page_size: int = 100


# Endpoints
@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Comex Analyzer API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Verifica saúde da API."""
    try:
        # Testar conexão com banco
        db.execute(text("SELECT 1"))
        db.commit()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/coletar-dados")
async def coletar_dados(db: Session = Depends(get_db)):
    """
    Inicia coleta de dados do Comex Stat.
    """
    try:
        collector = DataCollector()
        stats = await collector.collect_recent_data(db)
        
        return {
            "success": True,
            "message": "Coleta de dados concluída",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados: {str(e)}")


@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    meses: int = Query(default=3, ge=1, le=12),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas para o dashboard.
    """
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    
    # Calcular data inicial
    data_inicio = datetime.now() - timedelta(days=30 * meses)
    
    # Volume de importações e exportações
    volume_imp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
        and_(
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
            OperacaoComex.data_operacao >= data_inicio.date()
        )
    ).scalar() or 0.0
    
    volume_exp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
        and_(
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
            OperacaoComex.data_operacao >= data_inicio.date()
        )
    ).scalar() or 0.0
    
    # Valor total movimentado
    valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
        OperacaoComex.data_operacao >= data_inicio.date()
    ).scalar() or 0.0
    
    # Principais NCMs
    principais_ncms = db.query(
        OperacaoComex.ncm,
        OperacaoComex.descricao_produto,
        func.sum(OperacaoComex.valor_fob).label('total_valor'),
        func.count(OperacaoComex.id).label('total_operacoes')
    ).filter(
        OperacaoComex.data_operacao >= data_inicio.date()
    ).group_by(
        OperacaoComex.ncm,
        OperacaoComex.descricao_produto
    ).order_by(
        func.sum(OperacaoComex.valor_fob).desc()
    ).limit(10).all()
    
    principais_ncms_list = [
        {
            "ncm": ncm,
            "descricao": desc[:100] if desc else "",
            "valor_total": float(total_valor),
            "total_operacoes": total_operacoes
        }
        for ncm, desc, total_valor, total_operacoes in principais_ncms
    ]
    
    # Principais países
    principais_paises = db.query(
        OperacaoComex.pais_origem_destino,
        func.sum(OperacaoComex.valor_fob).label('total_valor'),
        func.count(OperacaoComex.id).label('total_operacoes')
    ).filter(
        OperacaoComex.data_operacao >= data_inicio.date()
    ).group_by(
        OperacaoComex.pais_origem_destino
    ).order_by(
        func.sum(OperacaoComex.valor_fob).desc()
    ).limit(10).all()
    
    principais_paises_list = [
        {
            "pais": pais,
            "valor_total": float(total_valor),
            "total_operacoes": total_operacoes
        }
        for pais, total_valor, total_operacoes in principais_paises
    ]
    
    # Registros por mês
    registros_por_mes = db.query(
        OperacaoComex.mes_referencia,
        func.count(OperacaoComex.id).label('count')
    ).filter(
        OperacaoComex.data_operacao >= data_inicio.date()
    ).group_by(
        OperacaoComex.mes_referencia
    ).order_by(
        OperacaoComex.mes_referencia
    ).all()
    
    registros_dict = {
        mes: count for mes, count in registros_por_mes
    }
    
    return DashboardStats(
        volume_importacoes=float(volume_imp),
        volume_exportacoes=float(volume_exp),
        valor_total_usd=float(valor_total),
        principais_ncms=principais_ncms_list,
        principais_paises=principais_paises_list,
        registros_por_mes=registros_dict
    )


@app.post("/buscar")
async def buscar_operacoes(
    filtros: BuscaFiltros,
    db: Session = Depends(get_db)
):
    """
    Busca operações com filtros avançados.
    """
    from sqlalchemy import and_, or_
    
    query = db.query(OperacaoComex)
    
    # Aplicar filtros
    conditions = []
    
    if filtros.ncm:
        conditions.append(OperacaoComex.ncm == filtros.ncm)
    
    if filtros.data_inicio:
        conditions.append(OperacaoComex.data_operacao >= filtros.data_inicio)
    
    if filtros.data_fim:
        conditions.append(OperacaoComex.data_operacao <= filtros.data_fim)
    
    if filtros.tipo_operacao:
        tipo = TipoOperacao.IMPORTACAO if filtros.tipo_operacao == "Importação" else TipoOperacao.EXPORTACAO
        conditions.append(OperacaoComex.tipo_operacao == tipo)
    
    if filtros.pais:
        conditions.append(OperacaoComex.pais_origem_destino.ilike(f"%{filtros.pais}%"))
    
    if filtros.uf:
        conditions.append(OperacaoComex.uf == filtros.uf.upper())
    
    if filtros.via_transporte:
        via = ViaTransporte[filtros.via_transporte.upper()]
        conditions.append(OperacaoComex.via_transporte == via)
    
    if filtros.valor_fob_min:
        conditions.append(OperacaoComex.valor_fob >= filtros.valor_fob_min)
    
    if filtros.valor_fob_max:
        conditions.append(OperacaoComex.valor_fob <= filtros.valor_fob_max)
    
    if filtros.peso_min:
        conditions.append(OperacaoComex.peso_liquido_kg >= filtros.peso_min)
    
    if filtros.peso_max:
        conditions.append(OperacaoComex.peso_liquido_kg <= filtros.peso_max)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    # Contar total
    total = query.count()
    
    # Paginação
    offset = (filtros.page - 1) * filtros.page_size
    operacoes = query.order_by(
        OperacaoComex.data_operacao.desc()
    ).offset(offset).limit(filtros.page_size).all()
    
    return {
        "total": total,
        "page": filtros.page,
        "page_size": filtros.page_size,
        "total_pages": (total + filtros.page_size - 1) // filtros.page_size,
        "results": [
            {
                "id": op.id,
                "ncm": op.ncm,
                "descricao_produto": op.descricao_produto,
                "tipo_operacao": op.tipo_operacao.value,
                "pais_origem_destino": op.pais_origem_destino,
                "uf": op.uf,
                "valor_fob": op.valor_fob,
                "data_operacao": op.data_operacao.isoformat(),
            }
            for op in operacoes
        ]
    }


@app.get("/ncm/{ncm}/analise")
async def analise_ncm(
    ncm: str,
    db: Session = Depends(get_db)
):
    """
    Análise detalhada de um NCM específico.
    """
    from sqlalchemy import func
    
    # Validar NCM
    if len(ncm) != 8 or not ncm.isdigit():
        raise HTTPException(status_code=400, detail="NCM inválido")
    
    # Estatísticas gerais
    stats = db.query(
        func.count(OperacaoComex.id).label('total_operacoes'),
        func.sum(OperacaoComex.valor_fob).label('valor_total'),
        func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
        func.avg(OperacaoComex.valor_fob).label('valor_medio')
    ).filter(
        OperacaoComex.ncm == ncm
    ).first()
    
    # Principais países
    principais_paises = db.query(
        OperacaoComex.pais_origem_destino,
        OperacaoComex.tipo_operacao,
        func.sum(OperacaoComex.valor_fob).label('valor_total')
    ).filter(
        OperacaoComex.ncm == ncm
    ).group_by(
        OperacaoComex.pais_origem_destino,
        OperacaoComex.tipo_operacao
    ).order_by(
        func.sum(OperacaoComex.valor_fob).desc()
    ).limit(10).all()
    
    # Evolução temporal
    evolucao = db.query(
        OperacaoComex.mes_referencia,
        OperacaoComex.tipo_operacao,
        func.sum(OperacaoComex.valor_fob).label('valor_total'),
        func.count(OperacaoComex.id).label('quantidade')
    ).filter(
        OperacaoComex.ncm == ncm
    ).group_by(
        OperacaoComex.mes_referencia,
        OperacaoComex.tipo_operacao
    ).order_by(
        OperacaoComex.mes_referencia
    ).all()
    
    return {
        "ncm": ncm,
        "estatisticas": {
            "total_operacoes": stats.total_operacoes or 0,
            "valor_total": float(stats.valor_total or 0),
            "peso_total": float(stats.peso_total or 0),
            "valor_medio": float(stats.valor_medio or 0),
        },
        "principais_paises": [
            {
                "pais": pais,
                "tipo_operacao": tipo.value,
                "valor_total": float(valor_total)
            }
            for pais, tipo, valor_total in principais_paises
        ],
        "evolucao_temporal": [
            {
                "mes": mes,
                "tipo_operacao": tipo.value,
                "valor_total": float(valor_total),
                "quantidade": quantidade
            }
            for mes, tipo, valor_total, quantidade in evolucao
        ]
    }


if __name__ == "__main__":
    from loguru import logger
    
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

