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


class ColetarDadosNCMsRequest(BaseModel):
    """Schema para coletar dados de múltiplos NCMs."""
    ncms: Optional[List[str]] = None  # Lista de NCMs específicos (None = todos)
    meses: Optional[int] = 24  # Quantos meses buscar (padrão: 24)
    tipo_operacao: Optional[str] = None  # "Importação" ou "Exportação" (None = ambos)


@app.post("/coletar-dados-ncms")
async def coletar_dados_ncms(
    request: ColetarDadosNCMsRequest,
    db: Session = Depends(get_db)
):
    """
    Coleta dados reais da API Comex Stat para múltiplos NCMs.
    Se ncms não for fornecido, coleta dados gerais (todos os NCMs).
    """
    try:
        from datetime import datetime, timedelta
        from data_collector import DataCollector
        
        collector = DataCollector()
        stats = {
            "total_registros": 0,
            "meses_processados": [],
            "erros": [],
            "ncms_processados": [],
            "usou_api": False
        }
        
        # Calcular meses a buscar
        hoje = datetime.now()
        meses_lista = []
        for i in range(request.meses or 24):
            mes_date = hoje - timedelta(days=30 * i)
            meses_lista.append(mes_date.strftime("%Y-%m"))
        meses_lista = sorted(meses_lista)
        
        # Verificar se API está disponível
        if await collector.api_client.test_connection():
            stats["usou_api"] = True
            
            # Se não especificar NCMs, coletar dados gerais
            if not request.ncms or len(request.ncms) == 0:
                logger.info("Coletando dados gerais (todos os NCMs)...")
                for mes in meses_lista:
                    try:
                        tipos = ["Importação", "Exportação"]
                        if request.tipo_operacao:
                            tipos = [request.tipo_operacao]
                        
                        for tipo in tipos:
                            logger.info(f"Coletando {mes} - {tipo}...")
                            data = await collector.api_client.fetch_data(
                                mes_inicio=mes,
                                mes_fim=mes,
                                tipo_operacao=tipo
                            )
                            
                            if data:
                                transformed = collector.transformer.transform_api_data(data, mes, tipo)
                                saved = collector._save_to_database(db, transformed, mes, tipo)
                                stats["total_registros"] += saved
                                logger.info(f"✓ {saved} registros salvos para {mes} - {tipo}")
                        
                        if mes not in stats["meses_processados"]:
                            stats["meses_processados"].append(mes)
                    except Exception as e:
                        error_msg = f"Erro ao coletar {mes}: {e}"
                        logger.error(error_msg)
                        stats["erros"].append(error_msg)
            else:
                # Coletar dados específicos de cada NCM
                logger.info(f"Coletando dados para {len(request.ncms)} NCMs...")
                for ncm in request.ncms:
                    ncm_limpo = ncm.replace('.', '').replace(' ', '').strip()
                    if len(ncm_limpo) != 8 or not ncm_limpo.isdigit():
                        logger.warning(f"NCM inválido ignorado: {ncm}")
                        continue
                    
                    try:
                        tipos = ["Importação", "Exportação"]
                        if request.tipo_operacao:
                            tipos = [request.tipo_operacao]
                        
                        for tipo in tipos:
                            logger.info(f"Coletando NCM {ncm_limpo} - {tipo}...")
                            for mes in meses_lista:
                                try:
                                    data = await collector.api_client.fetch_data(
                                        mes_inicio=mes,
                                        mes_fim=mes,
                                        tipo_operacao=tipo,
                                        ncm=ncm_limpo
                                    )
                                    
                                    if data:
                                        transformed = collector.transformer.transform_api_data(data, mes, tipo)
                                        saved = collector._save_to_database(db, transformed, mes, tipo)
                                        stats["total_registros"] += saved
                                
                                except Exception as e:
                                    logger.warning(f"Erro ao coletar {ncm_limpo} - {mes}: {e}")
                                    continue
                        
                        stats["ncms_processados"].append(ncm_limpo)
                        logger.info(f"✓ NCM {ncm_limpo} processado")
                    except Exception as e:
                        error_msg = f"Erro ao coletar NCM {ncm}: {e}"
                        logger.error(error_msg)
                        stats["erros"].append(error_msg)
        else:
            stats["erros"].append("API do Comex Stat não está disponível")
            raise HTTPException(status_code=503, detail="API do Comex Stat não está disponível")
        
        return {
            "success": True,
            "message": f"Coleta concluída: {stats['total_registros']} registros",
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao coletar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados: {str(e)}")


class PopularDadosRequest(BaseModel):
    """Schema para popular dados de exemplo."""
    quantidade: int = 1000
    meses: int = 24


@app.post("/popular-dados-exemplo")
async def popular_dados_exemplo(
    request: PopularDadosRequest,
    db: Session = Depends(get_db)
):
    """
    Popula o banco de dados com dados de exemplo.
    Útil para testes quando não há acesso ao Shell.
    """
    try:
        from scripts.popular_dados_exemplo import gerar_dados_exemplo
        
        logger.info(f"Iniciando população de {request.quantidade} registros...")
        
        registros_criados = gerar_dados_exemplo(request.quantidade)
        
        # Verificar quantas empresas foram criadas
        from sqlalchemy import func, distinct
        total_importadoras = db.query(func.count(distinct(OperacaoComex.razao_social_importador))).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != ''
        ).scalar() or 0
        
        total_exportadoras = db.query(func.count(distinct(OperacaoComex.razao_social_exportador))).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != ''
        ).scalar() or 0
        
        return {
            "success": True,
            "message": f"Banco populado com {registros_criados} registros",
            "registros_criados": registros_criados,
            "quantidade_solicitada": request.quantidade,
            "empresas_importadoras": total_importadoras or 0,
            "empresas_exportadoras": total_exportadoras or 0
        }
    except Exception as e:
        logger.error(f"Erro ao popular dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao popular dados: {str(e)}")


@app.get("/test/empresas")
async def test_empresas(db: Session = Depends(get_db)):
    """
    Endpoint de teste para verificar empresas no banco.
    """
    from sqlalchemy import func, distinct
    
    try:
        # Contar total de registros
        total_registros = db.query(OperacaoComex).count()
        
        # Contar empresas importadoras distintas
        importadoras = db.query(
            distinct(OperacaoComex.razao_social_importador)
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != ''
        ).limit(10).all()
        
        # Contar empresas exportadoras distintas
        exportadoras = db.query(
            distinct(OperacaoComex.razao_social_exportador)
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != ''
        ).limit(10).all()
        
        # Contar totais distintos
        total_imp_distintas = db.query(
            func.count(distinct(OperacaoComex.razao_social_importador))
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != ''
        ).scalar() or 0
        
        total_exp_distintas = db.query(
            func.count(distinct(OperacaoComex.razao_social_exportador))
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != ''
        ).scalar() or 0
        
        # Valores totais
        valor_total_imp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
        ).scalar() or 0
        
        valor_total_exp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
        ).scalar() or 0
        
        # Testar autocomplete
        teste_autocomplete_imp = db.query(
            OperacaoComex.razao_social_importador.label('empresa'),
            func.count(OperacaoComex.id).label('total_operacoes')
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != '',
            OperacaoComex.razao_social_importador.ilike("%Importadora%")
        ).group_by(
            OperacaoComex.razao_social_importador
        ).limit(5).all()
        
        teste_autocomplete_exp = db.query(
            OperacaoComex.razao_social_exportador.label('empresa'),
            func.count(OperacaoComex.id).label('total_operacoes')
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != '',
            OperacaoComex.razao_social_exportador.ilike("%Exportadora%")
        ).group_by(
            OperacaoComex.razao_social_exportador
        ).limit(5).all()
        
        return {
            "total_registros": total_registros,
            "exemplo_importadoras": [imp[0] for imp in importadoras if imp[0]],
            "exemplo_exportadoras": [exp[0] for exp in exportadoras if exp[0]],
            "total_importadoras_distintas": total_imp_distintas,
            "total_exportadoras_distintas": total_exp_distintas,
            "valor_total_importacoes": float(valor_total_imp),
            "valor_total_exportacoes": float(valor_total_exp),
            "teste_autocomplete_importadoras": [
                {"nome": emp, "total_operacoes": int(total)} 
                for emp, total in teste_autocomplete_imp
            ],
            "teste_autocomplete_exportadoras": [
                {"nome": emp, "total_operacoes": int(total)} 
                for emp, total in teste_autocomplete_exp
            ],
            "status": "ok" if total_registros > 0 else "vazio",
            "problemas": [
                "Banco está vazio" if total_registros == 0 else None,
                "Nenhuma empresa importadora" if total_imp_distintas == 0 else None,
                "Nenhuma empresa exportadora" if total_exp_distintas == 0 else None,
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao testar empresas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"erro": str(e), "traceback": traceback.format_exc()}


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
    q: str = Query(..., min_length=1, description="Termo de busca"),  # Reduzido para min_length=1
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas importadoras.
    Retorna empresas que contêm o termo de busca no nome.
    """
    from sqlalchemy import func, distinct
    
    try:
        # Buscar empresas importadoras que contêm o termo
        empresas = db.query(
            OperacaoComex.razao_social_importador.label('empresa'),
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.sum(OperacaoComex.valor_fob).label('valor_total')
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != '',
            OperacaoComex.razao_social_importador.ilike(f"%{q}%")
        ).group_by(
            OperacaoComex.razao_social_importador
        ).order_by(
            func.sum(OperacaoComex.valor_fob).desc()
        ).limit(limit).all()
        
        return [
            {
                "nome": empresa,
                "total_operacoes": int(total_operacoes),
                "valor_total": float(valor_total or 0)
            }
            for empresa, total_operacoes, valor_total in empresas
        ]
    except Exception as e:
        logger.error(f"Erro ao buscar importadoras: {e}")
        return []


@app.get("/empresas/autocomplete/exportadoras")
async def autocomplete_exportadoras(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas exportadoras.
    Retorna empresas que contêm o termo de busca no nome.
    """
    from sqlalchemy import func
    
    try:
        logger.info(f"🔍 Buscando exportadoras com termo: '{q}'")
        
        # Primeiro, verificar se há dados
        total_registros = db.query(OperacaoComex).count()
        logger.info(f"Total de registros no banco: {total_registros}")
        
        # Buscar empresas exportadoras que contêm o termo
        empresas_query = db.query(
            OperacaoComex.razao_social_exportador,
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.sum(OperacaoComex.valor_fob).label('valor_total')
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != '',
            OperacaoComex.razao_social_exportador.ilike(f"%{q}%")
        ).group_by(
            OperacaoComex.razao_social_exportador
        ).order_by(
            func.sum(OperacaoComex.valor_fob).desc()
        ).limit(limit)
        
        empresas = empresas_query.all()
        
        resultado = []
        for empresa, total_operacoes, valor_total in empresas:
            if empresa:  # Garantir que empresa não é None
                resultado.append({
                    "nome": str(empresa),
                    "total_operacoes": int(total_operacoes) if total_operacoes else 0,
                    "valor_total": float(valor_total or 0)
                })
        
        logger.info(f"✅ Encontradas {len(resultado)} exportadoras para '{q}'")
        if len(resultado) == 0:
            # Debug: verificar quantas empresas existem sem filtro
            total_empresas = db.query(func.count(func.distinct(OperacaoComex.razao_social_exportador))).filter(
                OperacaoComex.razao_social_exportador.isnot(None),
                OperacaoComex.razao_social_exportador != ''
            ).scalar() or 0
            logger.warning(f"⚠️ Nenhuma exportadora encontrada. Total de empresas no banco: {total_empresas}")
        
        return resultado
    except Exception as e:
        logger.error(f"❌ Erro ao buscar exportadoras: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


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


# Endpoints de Autenticação (opcionais - só funcionam se módulos estiverem disponíveis)
if AUTH_FUNCTIONS_AVAILABLE and AUTH_AVAILABLE:
    from fastapi import Form
    from fastapi import BackgroundTasks
    import secrets
    from datetime import timedelta
    
    @app.post("/login")
    async def login(
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """Endpoint de login usando email."""
        try:
            logger.info(f"Tentativa de login recebida: {username}")
            
            # Truncar senha se necessário (bcrypt limite: 72 bytes)
            senha_original = password
            senha_bytes_original = senha_original.encode('utf-8')
            if len(senha_bytes_original) > 72:
                senha_bytes_truncada = senha_bytes_original[:72]
                senha_final = senha_bytes_truncada.decode('utf-8', errors='ignore')
                logger.warning(f"⚠️ Senha truncada de {len(senha_bytes_original)} para 72 bytes")
            else:
                senha_final = senha_original
            
            # username é o email
            user = authenticate_user(db, username, senha_final)
            
            if not user:
                logger.warning(f"Login falhou para: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="Email ou senha incorretos, ou cadastro aguardando aprovação",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Atualizar último login
            try:
                user.ultimo_login = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Login bem-sucedido para: {user.email}")
            except Exception as e:
                logger.error(f"Erro ao atualizar último login: {e}")
                db.rollback()
            
            access_token = create_access_token(data={"sub": user.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "nome_completo": user.nome_completo,
                    "nome_empresa": user.nome_empresa
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado no login: {e}")
            raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
    
    class CadastroRequest(BaseModel):
        """Schema para cadastro de usuário."""
        email: str
        password: str
        nome_completo: str
        data_nascimento: Optional[date] = None
        nome_empresa: Optional[str] = None
        cpf: Optional[str] = None
        cnpj: Optional[str] = None
    
    @app.post("/register")
    async def register(
        cadastro: CadastroRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
    ):
        """Endpoint de registro de usuário com aprovação."""
        try:
            logger.info(f"Tentativa de cadastro recebida: {cadastro.email}")
            
            # Validar senha
            senha_valida, mensagem_erro = validate_password(cadastro.password)
            if not senha_valida:
                raise HTTPException(status_code=400, detail=mensagem_erro)
            
            # Verificar se email já existe
            usuario_existente = db.query(Usuario).filter(Usuario.email == cadastro.email).first()
            if usuario_existente:
                raise HTTPException(status_code=400, detail="Email já cadastrado")
            
            # Truncar senha antes do hash
            senha_para_hash = cadastro.password
            senha_bytes = len(senha_para_hash.encode('utf-8'))
            if senha_bytes > 72:
                senha_bytes_truncated = senha_para_hash.encode('utf-8')[:72]
                senha_para_hash = senha_bytes_truncated.decode('utf-8', errors='ignore')
                logger.warning(f"⚠️ Senha truncada de {senha_bytes} para 72 bytes")
            
            # Todos os cadastros precisam de aprovação manual
            novo_usuario = Usuario(
                email=cadastro.email,
                senha_hash=get_password_hash(senha_para_hash),
                nome_completo=cadastro.nome_completo,
                data_nascimento=cadastro.data_nascimento,
                nome_empresa=cadastro.nome_empresa,
                cpf=cadastro.cpf,
                cnpj=cadastro.cnpj,
                status_aprovacao="pendente",
                ativo=0  # Inativo até aprovação
            )
            db.add(novo_usuario)
            db.flush()
            
            # Criar token de aprovação
            token_aprovacao = secrets.token_urlsafe(32)
            data_expiracao = datetime.utcnow() + timedelta(days=7)
            
            aprovacao = AprovacaoCadastro(
                usuario_id=novo_usuario.id,
                token_aprovacao=token_aprovacao,
                email_destino=cadastro.email,
                status="pendente",
                data_expiracao=data_expiracao
            )
            db.add(aprovacao)
            db.commit()
            
            logger.info(f"✅ Usuário criado: {cadastro.email} (ID: {novo_usuario.id})")
            
            # Enviar email em background
            if EMAIL_SERVICE_AVAILABLE:
                background_tasks.add_task(
                    enviar_email_aprovacao,
                    cadastro.email,
                    cadastro.nome_completo,
                    token_aprovacao
                )
            
            return {
                "message": "Cadastro realizado com sucesso! Aguarde aprovação por email.",
                "email": cadastro.email,
                "aprovado": False
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado no cadastro: {e}")
            raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
    
    class RedefinirSenhaRequest(BaseModel):
        """Schema para solicitar redefinição de senha."""
        email: str
    
    class NovaSenhaRequest(BaseModel):
        """Schema para definir nova senha."""
        token: str
        nova_senha: str
    
    @app.post("/solicitar-redefinicao-senha")
    async def solicitar_redefinicao_senha(
        request: RedefinirSenhaRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
    ):
        """Endpoint para solicitar redefinição de senha."""
        try:
            usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
            if not usuario:
                # Por segurança, não revelar se o email existe ou não
                logger.info(f"Solicitação de redefinição para email não encontrado: {request.email}")
                return {"message": "Se o email existir, você receberá instruções para redefinir a senha"}
            
            # Gerar token de redefinição
            token_redefinicao = secrets.token_urlsafe(32)
            
            # Salvar token no banco
            try:
                usuario.token_aprovacao = token_redefinicao
                db.commit()
                logger.info(f"✅ Token de redefinição salvo para {request.email}")
            except Exception as e:
                logger.error(f"Erro ao salvar token de redefinição: {e}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Erro ao processar solicitação: {str(e)}")
            
            # Log do token (em produção, enviar por email)
            logger.info(f"📧 Token de redefinição gerado para {request.email}: {token_redefinicao}")
            logger.info(f"   Link: http://localhost:3000/redefinir-senha?token={token_redefinicao}")
            
            return {"message": "Se o email existir, você receberá instruções para redefinir a senha"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao solicitar redefinição: {e}")
            raise HTTPException(status_code=500, detail="Erro ao processar solicitação")
    
    @app.post("/redefinir-senha")
    async def redefinir_senha(
        request: NovaSenhaRequest,
        db: Session = Depends(get_db)
    ):
        """Endpoint para redefinir senha usando token."""
        try:
            # Validar nova senha
            senha_valida, mensagem_erro = validate_password(request.nova_senha)
            if not senha_valida:
                raise HTTPException(status_code=400, detail=mensagem_erro)
            
            # Buscar usuário pelo token
            usuario = db.query(Usuario).filter(Usuario.token_aprovacao == request.token).first()
            if not usuario:
                raise HTTPException(status_code=400, detail="Token inválido ou expirado")
            
            # Truncar senha antes de criar hash
            senha_para_hash = request.nova_senha
            senha_bytes = len(senha_para_hash.encode('utf-8'))
            if senha_bytes > 72:
                senha_bytes_truncated = senha_para_hash.encode('utf-8')[:72]
                senha_para_hash = senha_bytes_truncated.decode('utf-8', errors='ignore')
                logger.warning(f"⚠️ Senha truncada de {senha_bytes} para 72 bytes na redefinição")
            
            # Atualizar senha
            usuario.senha_hash = get_password_hash(senha_para_hash)
            usuario.token_aprovacao = None  # Limpar token após uso
            db.commit()
            
            logger.info(f"✅ Senha redefinida para: {usuario.email}")
            return {"message": "Senha redefinida com sucesso"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {e}")
            raise HTTPException(status_code=500, detail="Erro ao redefinir senha")
    
    class AprovarCadastroRequest(BaseModel):
        """Schema para aprovar cadastro."""
        token: str
    
    @app.post("/aprovar-cadastro")
    async def aprovar_cadastro(
        request: AprovarCadastroRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
    ):
        """Endpoint para aprovar cadastro usando token."""
        try:
            # Buscar aprovação pelo token
            aprovacao = db.query(AprovacaoCadastro).filter(
                AprovacaoCadastro.token_aprovacao == request.token,
                AprovacaoCadastro.status == "pendente"
            ).first()
            
            if not aprovacao:
                raise HTTPException(status_code=400, detail="Token inválido ou cadastro já processado")
            
            # Verificar se token não expirou
            if aprovacao.data_expiracao < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Token expirado")
            
            # Buscar usuário
            usuario = db.query(Usuario).filter(Usuario.id == aprovacao.usuario_id).first()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Aprovar usuário
            usuario.status_aprovacao = "aprovado"
            usuario.ativo = 1
            aprovacao.status = "aprovado"
            aprovacao.data_aprovacao = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Cadastro aprovado para: {usuario.email}")
            
            # Enviar email de confirmação para o usuário
            if EMAIL_SERVICE_AVAILABLE:
                background_tasks.add_task(
                    enviar_email_cadastro_aprovado,
                    usuario.email,
                    usuario.nome_completo
                )
            
            return {
                "message": "Cadastro aprovado com sucesso!",
                "email": usuario.email,
                "nome": usuario.nome_completo
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao aprovar cadastro: {e}")
            raise HTTPException(status_code=500, detail="Erro ao aprovar cadastro")
    
    @app.get("/cadastros-pendentes")
    async def listar_cadastros_pendentes(
        db: Session = Depends(get_db)
    ):
        """Lista todos os cadastros pendentes de aprovação."""
        try:
            cadastros = db.query(Usuario).filter(
                Usuario.status_aprovacao == "pendente"
            ).all()
            
            cadastros_list = []
            for c in cadastros:
                # Buscar token de aprovação
                aprovacao = db.query(AprovacaoCadastro).filter(
                    AprovacaoCadastro.usuario_id == c.id,
                    AprovacaoCadastro.status == "pendente"
                ).first()
                
                cadastros_list.append({
                    "id": c.id,
                    "email": c.email,
                    "nome_completo": c.nome_completo,
                    "nome_empresa": c.nome_empresa,
                    "cpf": c.cpf,
                    "cnpj": c.cnpj,
                    "data_criacao": c.data_criacao.isoformat() if c.data_criacao else None,
                    "token_aprovacao": aprovacao.token_aprovacao if aprovacao else None,
                    "link_aprovacao": f"http://localhost:8000/docs#/default/aprovar_cadastro_aprovar_cadastro_post" if aprovacao else None
                })
            
            return {
                "total": len(cadastros_list),
                "cadastros": cadastros_list
            }
        except Exception as e:
            logger.error(f"Erro ao listar cadastros pendentes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Erro ao listar cadastros pendentes")
    
    @app.post("/criar-usuario-teste")
    async def criar_usuario_teste(
        email: str = Form(...),
        senha: str = Form(...),
        nome_completo: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """
        Endpoint para criar usuário já aprovado (apenas para desenvolvimento/teste).
        ATENÇÃO: Em produção, considere proteger este endpoint com autenticação admin.
        """
        try:
            # Verificar se usuário já existe
            usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
            
            if usuario_existente:
                # Atualizar usuário existente
                usuario_existente.senha_hash = get_password_hash(senha)
                usuario_existente.nome_completo = nome_completo
                usuario_existente.status_aprovacao = "aprovado"
                usuario_existente.ativo = 1
                usuario_existente.token_aprovacao = None
                
                db.commit()
                logger.info(f"✅ Usuário {email} atualizado e aprovado")
                return {
                    "message": "Usuário atualizado e aprovado com sucesso",
                    "email": email,
                    "status": "aprovado"
                }
            
            # Criar novo usuário
            senha_hash = get_password_hash(senha)
            
            novo_usuario = Usuario(
                email=email,
                senha_hash=senha_hash,
                nome_completo=nome_completo,
                status_aprovacao="aprovado",
                ativo=1,
                token_aprovacao=None,
                data_criacao=datetime.utcnow()
            )
            
            db.add(novo_usuario)
            db.commit()
            
            logger.info(f"✅ Usuário {email} criado e aprovado")
            return {
                "message": "Usuário criado e aprovado com sucesso",
                "email": email,
                "status": "aprovado"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao criar usuário teste: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")
else:
    # Endpoints stub quando autenticação não está disponível
    @app.post("/login")
    async def login_stub():
        """Endpoint de login não disponível - módulos de autenticação não instalados."""
        raise HTTPException(
            status_code=501,
            detail="Autenticação não disponível. Módulos de autenticação não estão instalados."
        )
    
    @app.post("/register")
    async def register_stub():
        """Endpoint de registro não disponível - módulos de autenticação não instalados."""
        raise HTTPException(
            status_code=501,
            detail="Cadastro não disponível. Módulos de autenticação não estão instalados."
        )


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

