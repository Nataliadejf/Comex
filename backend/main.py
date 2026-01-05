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

# Import opcional do router de exportação
try:
    from api.export import router as export_router
    EXPORT_ROUTER_AVAILABLE = True
except ImportError:
    EXPORT_ROUTER_AVAILABLE = False
    logger.warning("Router de exportação não disponível")

# Imports opcionais para funcionalidades de autenticação
try:
    from database.models import Usuario, AprovacaoCadastro
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logger.warning("Modelos de autenticação não disponíveis")

try:
    from auth import authenticate_user, create_access_token, get_current_user, get_password_hash, validate_password
    AUTH_FUNCTIONS_AVAILABLE = True
except ImportError:
    AUTH_FUNCTIONS_AVAILABLE = False
    logger.warning("Funções de autenticação não disponíveis")

try:
    from services.email_service import enviar_email_aprovacao, enviar_email_cadastro_aprovado
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    logger.warning("Serviço de email não disponível")

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
if EXPORT_ROUTER_AVAILABLE:
    app.include_router(export_router)


# Inicializar banco de dados na startup
@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados na startup."""
    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        # Não interrompe a aplicação, mas loga o erro
    
    # Iniciar scheduler para atualização diária
    try:
        from utils.scheduler import DataScheduler
        scheduler = DataScheduler()
        scheduler.start()
        logger.info("Scheduler de atualização diária iniciado")
    except Exception as e:
        logger.warning(f"Não foi possível iniciar scheduler: {e}")
        # Não interrompe a aplicação se o scheduler falhar


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
    valor_total_importacoes: Optional[float] = None  # Valor total de importações
    valor_total_exportacoes: Optional[float] = None  # Valor total de exportações
    principais_ncms: List[dict]
    principais_paises: List[dict]
    registros_por_mes: dict
    valores_por_mes: Optional[dict] = None  # Valores FOB por mês
    pesos_por_mes: Optional[dict] = None  # Pesos por mês


class BuscaFiltros(BaseModel):
    """Filtros de busca."""
    ncms: Optional[List[str]] = None  # Lista de NCMs
    ncm: Optional[str] = None  # Mantido para compatibilidade
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
    empresa_importadora: Optional[str] = None
    empresa_exportadora: Optional[str] = None
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
    meses: int = Query(default=24, ge=1, le=24),  # Padrão: 2 anos
    tipo_operacao: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None),
    ncms: Optional[List[str]] = Query(default=None),  # Múltiplos NCMs
    empresa_importadora: Optional[str] = Query(default=None),
    empresa_exportadora: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas para o dashboard.
    Por padrão busca últimos 2 anos (24 meses).
    """
    from sqlalchemy import func, and_, or_
    from datetime import datetime, timedelta
    
    # Calcular data inicial (padrão: 2 anos)
    data_inicio = datetime.now() - timedelta(days=30 * meses)
    
    # Construir filtros base
    base_filters = [OperacaoComex.data_operacao >= data_inicio.date()]
    
    # Aplicar filtro de NCMs (múltiplos ou único)
    ncms_filtro = []
    if ncms:
        for ncm_item in ncms:
            ncm_limpo = ncm_item.replace('.', '').replace(' ', '').strip()
            if len(ncm_limpo) == 8 and ncm_limpo.isdigit():
                ncms_filtro.append(ncm_limpo)
    elif ncm:
        ncm_limpo = ncm.replace('.', '').replace(' ', '').strip()
        if len(ncm_limpo) == 8 and ncm_limpo.isdigit():
            ncms_filtro.append(ncm_limpo)
    
    if ncms_filtro:
        if len(ncms_filtro) == 1:
            base_filters.append(OperacaoComex.ncm == ncms_filtro[0])
        else:
            base_filters.append(OperacaoComex.ncm.in_(ncms_filtro))
    
    # Aplicar filtros de empresa
    if empresa_importadora:
        base_filters.append(
            OperacaoComex.razao_social_importador.ilike(f"%{empresa_importadora}%")
        )
    
    if empresa_exportadora:
        base_filters.append(
            OperacaoComex.razao_social_exportador.ilike(f"%{empresa_exportadora}%")
        )
    
    # Aplicar filtro de tipo de operação se fornecido
    tipo_filtro = None
    if tipo_operacao:
        if tipo_operacao.lower() == "importação" or tipo_operacao.lower() == "importacao":
            tipo_filtro = TipoOperacao.IMPORTACAO
        elif tipo_operacao.lower() == "exportação" or tipo_operacao.lower() == "exportacao":
            tipo_filtro = TipoOperacao.EXPORTACAO
    
    # Volume de importações e exportações
    filtros_imp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO]
    if tipo_filtro == TipoOperacao.IMPORTACAO or tipo_filtro is None:
        volume_imp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
            and_(*filtros_imp)
        ).scalar() or 0.0
    else:
        volume_imp = 0.0
    
    filtros_exp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO]
    if tipo_filtro == TipoOperacao.EXPORTACAO or tipo_filtro is None:
        volume_exp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
            and_(*filtros_exp)
        ).scalar() or 0.0
    else:
        volume_exp = 0.0
    
    # Valor total movimentado
    if tipo_filtro:
        filtros_valor = base_filters + [OperacaoComex.tipo_operacao == tipo_filtro]
    else:
        filtros_valor = base_filters
    
    valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
        and_(*filtros_valor)
    ).scalar() or 0.0
    
    # Valores separados por tipo de operação (se não houver filtro de tipo)
    valor_total_imp = 0.0
    valor_total_exp = 0.0
    if tipo_filtro is None:
        # Calcular valores separados apenas se não houver filtro de tipo
        filtros_valor_imp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO]
        valor_total_imp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            and_(*filtros_valor_imp)
        ).scalar() or 0.0
        
        filtros_valor_exp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO]
        valor_total_exp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            and_(*filtros_valor_exp)
        ).scalar() or 0.0
    elif tipo_filtro == TipoOperacao.IMPORTACAO:
        valor_total_imp = valor_total
    elif tipo_filtro == TipoOperacao.EXPORTACAO:
        valor_total_exp = valor_total
    
    # Principais NCMs
    principais_ncms = db.query(
        OperacaoComex.ncm,
        OperacaoComex.descricao_produto,
        func.sum(OperacaoComex.valor_fob).label('total_valor'),
        func.count(OperacaoComex.id).label('total_operacoes')
    ).filter(
        and_(*filtros_valor)
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
        and_(*filtros_valor)
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
    
    # Registros por mês com valores FOB e peso
    registros_por_mes_query = db.query(
        OperacaoComex.mes_referencia,
        func.count(OperacaoComex.id).label('count'),
        func.sum(OperacaoComex.valor_fob).label('valor_total'),
        func.sum(OperacaoComex.peso_liquido_kg).label('peso_total')
    ).filter(
        and_(*filtros_valor)
    ).group_by(
        OperacaoComex.mes_referencia
    ).order_by(
        OperacaoComex.mes_referencia
    ).all()
    
    registros_dict = {
        mes: count for mes, count, _, _ in registros_por_mes_query
    }
    
    valores_por_mes_dict = {
        mes: float(valor_total) if valor_total else 0.0
        for mes, _, valor_total, _ in registros_por_mes_query
    }
    
    pesos_por_mes_dict = {
        mes: float(peso_total) if peso_total else 0.0
        for mes, _, _, peso_total in registros_por_mes_query
    }
    
    stats_response = DashboardStats(
        volume_importacoes=float(volume_imp),
        volume_exportacoes=float(volume_exp),
        valor_total_usd=float(valor_total),
        valor_total_importacoes=float(valor_total_imp) if valor_total_imp else None,
        valor_total_exportacoes=float(valor_total_exp) if valor_total_exp else None,
        principais_ncms=principais_ncms_list,
        principais_paises=principais_paises_list,
        registros_por_mes=registros_dict,
        valores_por_mes=valores_por_mes_dict if valores_por_mes_dict else {},
        pesos_por_mes=pesos_por_mes_dict if pesos_por_mes_dict else {}
    )
    
    return stats_response


@app.post("/buscar")
async def buscar_operacoes(
    filtros: BuscaFiltros,
    db: Session = Depends(get_db)
):
    """
    Busca operações com filtros avançados.
    Por padrão, busca dados dos últimos 2 anos se não especificar datas.
    """
    from sqlalchemy import and_, or_
    from datetime import datetime, timedelta
    
    query = db.query(OperacaoComex)
    
    # Aplicar filtros
    conditions = []
    
    # Filtro de NCMs (múltiplos)
    ncms_filtro = []
    if filtros.ncms:
        # Limpar e validar NCMs
        for ncm in filtros.ncms:
            ncm_limpo = ncm.replace('.', '').replace(' ', '').strip()
            if len(ncm_limpo) == 8 and ncm_limpo.isdigit():
                ncms_filtro.append(ncm_limpo)
    elif filtros.ncm:
        # Compatibilidade: aceitar NCM único também
        ncm_limpo = filtros.ncm.replace('.', '').replace(' ', '').strip()
        if len(ncm_limpo) == 8 and ncm_limpo.isdigit():
            ncms_filtro.append(ncm_limpo)
    
    if ncms_filtro:
        conditions.append(OperacaoComex.ncm.in_(ncms_filtro))
    
    # Por padrão, buscar últimos 2 anos se não especificar datas
    if not filtros.data_inicio:
        filtros.data_inicio = (datetime.now() - timedelta(days=730)).date()
    if not filtros.data_fim:
        filtros.data_fim = datetime.now().date()
    
    conditions.append(OperacaoComex.data_operacao >= filtros.data_inicio)
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
    
    # Filtros de empresa
    if filtros.empresa_importadora:
        conditions.append(
            OperacaoComex.razao_social_importador.ilike(f"%{filtros.empresa_importadora}%")
        )
    
    if filtros.empresa_exportadora:
        conditions.append(
            OperacaoComex.razao_social_exportador.ilike(f"%{filtros.empresa_exportadora}%")
        )
    
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
                "peso_liquido_kg": op.peso_liquido_kg,
                "data_operacao": op.data_operacao.isoformat(),
                "razao_social_importador": op.razao_social_importador,
                "razao_social_exportador": op.razao_social_exportador,
            }
            for op in operacoes
        ]
    }


@app.get("/empresas/autocomplete/importadoras")
async def autocomplete_importadoras(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas importadoras.
    """
    from sqlalchemy import func, distinct
    
    empresas = db.query(
        distinct(OperacaoComex.razao_social_importador).label('empresa'),
        func.count(OperacaoComex.id).label('total_operacoes'),
        func.sum(OperacaoComex.valor_fob).label('valor_total')
    ).filter(
        OperacaoComex.razao_social_importador.isnot(None),
        OperacaoComex.razao_social_importador != '',
        OperacaoComex.razao_social_importador.ilike(f"%{q}%"),
        OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
    ).group_by(
        OperacaoComex.razao_social_importador
    ).order_by(
        func.sum(OperacaoComex.valor_fob).desc()
    ).limit(limit).all()
    
    return [
        {
            "nome": empresa,
            "total_operacoes": total_operacoes,
            "valor_total": float(valor_total or 0)
        }
        for empresa, total_operacoes, valor_total in empresas
    ]


@app.get("/empresas/autocomplete/exportadoras")
async def autocomplete_exportadoras(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas exportadoras.
    """
    from sqlalchemy import func, distinct
    
    empresas = db.query(
        distinct(OperacaoComex.razao_social_exportador).label('empresa'),
        func.count(OperacaoComex.id).label('total_operacoes'),
        func.sum(OperacaoComex.valor_fob).label('valor_total')
    ).filter(
        OperacaoComex.razao_social_exportador.isnot(None),
        OperacaoComex.razao_social_exportador != '',
        OperacaoComex.razao_social_exportador.ilike(f"%{q}%"),
        OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
    ).group_by(
        OperacaoComex.razao_social_exportador
    ).order_by(
        func.sum(OperacaoComex.valor_fob).desc()
    ).limit(limit).all()
    
    return [
        {
            "nome": empresa,
            "total_operacoes": total_operacoes,
            "valor_total": float(valor_total or 0)
        }
        for empresa, total_operacoes, valor_total in empresas
    ]


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

