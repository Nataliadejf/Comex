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
from database import get_db, init_db
from database.models import (
    OperacaoComex, TipoOperacao, ViaTransporte,
    ComercioExterior, Empresa, CNAEHierarquia
)
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
        
        # Executar atualização inicial de empresas e sinergias em background
        async def atualizacao_inicial():
            try:
                from utils.data_updater import DataUpdater
                updater = DataUpdater()
                logger.info("Iniciando atualização inicial de empresas MDIC e sinergias...")
                await updater.atualizar_empresas_mdic()
                await updater.atualizar_relacionamentos(limite=500)  # Limite menor na inicialização
                await updater.atualizar_sinergias(limite_empresas=50)  # Limite menor na inicialização
                logger.info("✅ Atualização inicial concluída")
            except Exception as e:
                logger.warning(f"Atualização inicial não executada: {e}")
        
        # Executar após 30 segundos (dar tempo para o servidor inicializar)
        import asyncio
        import threading
        def run_initial_update():
            import time
            time.sleep(30)
            asyncio.run(atualizacao_inicial())
        
        update_thread = threading.Thread(target=run_initial_update, daemon=True)
        update_thread.start()
        
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


@app.post("/coletar-dados-enriquecidos")
async def coletar_dados_enriquecidos(
    meses: int = Query(24, description="Número de meses para coletar"),
    db: Session = Depends(get_db)
):
    """
    Coleta dados CSV do portal oficial do MDIC e enriquece com empresas e CNAE.
    Este endpoint:
    1. Baixa tabelas de correlação do MDIC
    2. Baixa dados mensais de importação/exportação dos últimos N meses
    3. Processa e salva no banco de dados
    4. Enriquece com informações de empresas do MDIC
    5. Integra com CNAE para sugestões inteligentes
    
    Fonte: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta
    """
    try:
        from data_collector.enriched_collector import EnrichedDataCollector
        
        logger.info(f"Iniciando coleta enriquecida de dados do MDIC ({meses} meses)...")
        
        collector = EnrichedDataCollector()
        stats = await collector.collect_and_enrich(db, meses)
        
        return {
            "success": True,
            "message": "Coleta enriquecida concluída",
            "stats": stats,
            "tabelas_baixadas": list(stats.get("tabelas_correlacao", {}).keys()),
            "empresas_enriquecidas": stats.get("empresas_enriquecidas", 0)
        }
    except Exception as e:
        logger.error(f"Erro na coleta enriquecida: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na coleta enriquecida: {str(e)}")


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
    Coleta dados reais da API Comex Stat ou CSV scraper para múltiplos NCMs.
    Sistema de fallback automático:
    1. Tenta API REST primeiro
    2. Se falhar, usa CSV scraper (bases de dados brutas)
    3. Se falhar, usa scraper tradicional (se disponível)
    
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
            "usou_api": False,
            "metodo_usado": "desconhecido"
        }
        
        # Calcular meses a buscar
        meses = request.meses or 24
        hoje = datetime.now()
        meses_lista = []
        for i in range(meses):
            mes_date = hoje - timedelta(days=30 * i)
            meses_lista.append(mes_date.strftime("%Y-%m"))
        meses_lista = sorted(meses_lista)
        
        # Se não especificar NCMs, usar método coletivo (mais eficiente)
        if not request.ncms or len(request.ncms) == 0:
            logger.info(f"Coletando dados gerais (todos os NCMs) para {meses} meses...")
            logger.info("Sistema tentará: API → CSV Scraper → Scraper tradicional")
            
            # Usar o método coletivo do DataCollector que tem fallback automático
            try:
                # Ajustar meses no collector temporariamente
                original_months = settings.months_to_fetch
                settings.months_to_fetch = meses
                
                # Coletar dados (com fallback automático)
                collection_stats = await collector.collect_recent_data(db)
                
                # Restaurar configuração
                settings.months_to_fetch = original_months
                
                stats.update(collection_stats)
                stats["metodo_usado"] = "API" if collection_stats.get("usou_api") else "CSV Scraper ou Scraper"
                
            except Exception as e:
                logger.error(f"Erro na coleta coletiva: {e}")
                stats["erros"].append(f"Coleta coletiva: {str(e)}")
        else:
            # Coletar dados específicos de cada NCM (via API apenas por enquanto)
            logger.info(f"Coletando dados para {len(request.ncms)} NCMs específicos...")
            
            # Verificar se API está disponível
            if await collector.api_client.test_connection():
                stats["usou_api"] = True
                stats["metodo_usado"] = "API"
                
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
                # Se API não disponível e NCMs específicos, sugerir coleta geral
                stats["erros"].append(
                    "API não disponível para NCMs específicos. "
                    "Use coleta geral (sem especificar NCMs) para usar CSV scraper."
                )
        
        return {
            "success": True,
            "message": f"Coleta concluída: {stats['total_registros']} registros usando {stats.get('metodo_usado', 'desconhecido')}",
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
    
    # Se não houver países no banco, tentar usar empresas recomendadas
    if not principais_paises_list:
        try:
            # Buscar empresas importadoras e exportadoras recomendadas
            empresas_imp = _buscar_empresas_importadoras_recomendadas(5)
            empresas_exp = _buscar_empresas_exportadoras_recomendadas(5)
            
            principais_paises_list.extend(empresas_imp)
            principais_paises_list.extend(empresas_exp)
            
            # Ordenar por valor total e limitar
            principais_paises_list.sort(key=lambda x: x.get("valor_total", 0), reverse=True)
            principais_paises_list = principais_paises_list[:10]
        except Exception as e:
            logger.debug(f"Erro ao buscar empresas recomendadas para países: {e}")
    
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
    
    # Se não houver dados no banco, tentar usar dados do Excel
    if valor_total == 0 and not principais_ncms_list:
        try:
            import json
            from pathlib import Path
            
            arquivo_resumo = Path(__file__).parent.parent / "data" / "resumo_dados_comexstat.json"
            if arquivo_resumo.exists():
                with open(arquivo_resumo, 'r', encoding='utf-8') as f:
                    resumo_excel = json.load(f)
                
                # Usar dados do Excel para popular o dashboard
                if resumo_excel.get('importacoes'):
                    valor_total_imp = resumo_excel['importacoes'].get('valor_total_usd', 0)
                    volume_imp = resumo_excel['importacoes'].get('total_registros', 0) * 1000  # Estimativa
                
                if resumo_excel.get('exportacoes'):
                    valor_total_exp = resumo_excel['exportacoes'].get('valor_total_usd', 0)
                    volume_exp = resumo_excel['exportacoes'].get('total_registros', 0) * 1000  # Estimativa
                
                valor_total = valor_total_imp + valor_total_exp
                
                # Criar registros por mês baseado no Excel (distribuir ao longo de 12 meses)
                registros_dict = {}
                valores_por_mes_dict = {}
                pesos_por_mes_dict = {}
                
                meses_2025 = [f"2025-{str(i).zfill(2)}" for i in range(1, 13)]
                total_registros_imp = resumo_excel.get('importacoes', {}).get('total_registros', 0)
                total_registros_exp = resumo_excel.get('exportacoes', {}).get('total_registros', 0)
                
                for mes in meses_2025:
                    registros_dict[mes] = int((total_registros_imp + total_registros_exp) / 12)
                    valores_por_mes_dict[mes] = float((valor_total_imp + valor_total_exp) / 12)
                    pesos_por_mes_dict[mes] = float((volume_imp + volume_exp) / 12)
                
                # Top NCMs do Excel
                arquivo_ncm = Path(__file__).parent.parent / "data" / "dados_ncm_comexstat.json"
                if arquivo_ncm.exists():
                    with open(arquivo_ncm, 'r', encoding='utf-8') as f:
                        dados_ncm = json.load(f)
                    
                    # Agrupar por NCM e ordenar
                    ncms_agrupados = {}
                    for item in dados_ncm:
                        ncm = item.get('ncm', '')
                        if ncm:
                            if ncm not in ncms_agrupados:
                                ncms_agrupados[ncm] = {
                                    'ncm': ncm,
                                    'descricao': item.get('descricao', ''),
                                    'valor_total': 0,
                                    'total_operacoes': 0
                                }
                            ncms_agrupados[ncm]['valor_total'] += item.get('valor_importacao_usd', 0) + item.get('valor_exportacao_usd', 0)
                            ncms_agrupados[ncm]['total_operacoes'] += 1
                    
                    principais_ncms_list = sorted(
                        ncms_agrupados.values(),
                        key=lambda x: x['valor_total'],
                        reverse=True
                    )[:10]
        except Exception as e:
            logger.debug(f"Erro ao carregar dados do Excel: {e}")
    
    # PRIMEIRO: Tentar usar tabela consolidada EmpresasRecomendadas (mais eficiente)
    try:
        from database.models import EmpresasRecomendadas
        
        total_emp_rec = db.query(func.count(EmpresasRecomendadas.id)).scalar() or 0
        if total_emp_rec > 0:
            logger.info(f"Usando tabela consolidada EmpresasRecomendadas ({total_emp_rec} empresas)")
            
            # Buscar empresas prováveis importadoras e exportadoras
            empresas_imp_rec = db.query(
                EmpresasRecomendadas.nome,
                EmpresasRecomendadas.valor_total_importacao_usd,
                EmpresasRecomendadas.volume_total_importacao_kg,
                EmpresasRecomendadas.peso_participacao
            ).filter(
                EmpresasRecomendadas.provavel_importador == 1
            ).order_by(
                EmpresasRecomendadas.peso_participacao.desc()
            ).limit(10).all()
            
            empresas_exp_rec = db.query(
                EmpresasRecomendadas.nome,
                EmpresasRecomendadas.valor_total_exportacao_usd,
                EmpresasRecomendadas.volume_total_exportacao_kg,
                EmpresasRecomendadas.peso_participacao
            ).filter(
                EmpresasRecomendadas.provavel_exportador == 1
            ).order_by(
                EmpresasRecomendadas.peso_participacao.desc()
            ).limit(10).all()
            
            # Calcular totais
            valor_total_imp = sum(float(emp.valor_total_importacao_usd or 0) for emp in empresas_imp_rec)
            valor_total_exp = sum(float(emp.valor_total_exportacao_usd or 0) for emp in empresas_exp_rec)
            volume_imp = sum(float(emp.volume_total_importacao_kg or 0) for emp in empresas_imp_rec)
            volume_exp = sum(float(emp.volume_total_exportacao_kg or 0) for emp in empresas_exp_rec)
            
            if valor_total_imp > 0 or valor_total_exp > 0:
                valor_total = valor_total_imp + valor_total_exp
                
                # Usar empresas recomendadas como principais países (temporário)
                principais_paises_list = [
                    {
                        "pais": emp.nome[:50],
                        "valor_total": float(emp.valor_total_importacao_usd or 0),
                        "total_operacoes": 0,
                        "tipo": "IMPORTADORA"
                    }
                    for emp in empresas_imp_rec[:5]
                ] + [
                    {
                        "pais": emp.nome[:50],
                        "valor_total": float(emp.valor_total_exportacao_usd or 0),
                        "total_operacoes": 0,
                        "tipo": "EXPORTADORA"
                    }
                    for emp in empresas_exp_rec[:5]
                ]
                
                principais_paises_list.sort(key=lambda x: x.get("valor_total", 0), reverse=True)
                principais_paises_list = principais_paises_list[:10]
                
                logger.info(f"✅ Dados carregados da tabela consolidada: {len(empresas_imp_rec)} importadoras, {len(empresas_exp_rec)} exportadoras")
    except Exception as e:
        logger.debug(f"Erro ao buscar EmpresasRecomendadas: {e}")
    
    # Se ainda não houver dados, tentar usar as novas tabelas (ComercioExterior e Empresa)
    if valor_total == 0 and not principais_ncms_list:
        try:
            logger.info("Tentando buscar dados das novas tabelas (ComercioExterior e Empresa)")
            data_corte = datetime.now() - timedelta(days=30 * meses)
            
            # Primeiro tentar com filtro de data
            importacoes = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'importacao',
                ComercioExterior.data >= data_corte.date()
            ).scalar() or 0.0
            
            exportacoes = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'exportacao',
                ComercioExterior.data >= data_corte.date()
            ).scalar() or 0.0
            
            peso_imp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                ComercioExterior.tipo == 'importacao',
                ComercioExterior.data >= data_corte.date()
            ).scalar() or 0.0
            
            peso_exp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                ComercioExterior.tipo == 'exportacao',
                ComercioExterior.data >= data_corte.date()
            ).scalar() or 0.0
            
            # Se não encontrou com filtro de data, tentar SEM filtro (buscar todos os dados)
            if importacoes == 0 and exportacoes == 0:
                logger.info("Nenhum dado encontrado com filtro de data, buscando todos os dados disponíveis...")
                importacoes = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar() or 0.0
                
                exportacoes = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                    ComercioExterior.tipo == 'exportacao'
                ).scalar() or 0.0
                
                peso_imp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar() or 0.0
                
                peso_exp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                    ComercioExterior.tipo == 'exportacao'
                ).scalar() or 0.0
                
                # Se encontrou dados sem filtro, usar todos os dados (sem filtro de data)
                if importacoes > 0 or exportacoes > 0:
                    data_corte = None  # Remover filtro de data
            
            if importacoes > 0 or exportacoes > 0:
                # Top NCMs
                query_ncms = db.query(
                    ComercioExterior.ncm,
                    ComercioExterior.descricao_ncm,
                    func.sum(ComercioExterior.valor_usd).label('valor_total')
                )
                
                if data_corte:
                    query_ncms = query_ncms.filter(ComercioExterior.data >= data_corte.date())
                
                top_ncms_novo = query_ncms.group_by(
                    ComercioExterior.ncm,
                    ComercioExterior.descricao_ncm
                ).order_by(
                    func.sum(ComercioExterior.valor_usd).desc()
                ).limit(10).all()
                
                principais_ncms_list = [
                    {
                        "ncm": ncm,
                        "descricao": desc or "",
                        "valor_total": float(valor)
                    }
                    for ncm, desc, valor in top_ncms_novo
                ]
                
                # Top Estados
                query_estados = db.query(
                    ComercioExterior.estado,
                    func.sum(ComercioExterior.valor_usd).label('valor_total')
                ).filter(
                    ComercioExterior.estado.isnot(None)
                )
                
                if data_corte:
                    query_estados = query_estados.filter(ComercioExterior.data >= data_corte.date())
                
                top_estados_novo = query_estados.group_by(
                    ComercioExterior.estado
                ).order_by(
                    func.sum(ComercioExterior.valor_usd).desc()
                ).limit(10).all()
                
                principais_paises_list = [
                    {
                        "pais": estado or "N/A",
                        "valor_total": float(valor),
                        "total_operacoes": 0,
                        "tipo": "GERAL"
                    }
                    for estado, valor in top_estados_novo
                ]
                
                # Valores por mês
                query_valores_mes = db.query(
                    ComercioExterior.mes,
                    ComercioExterior.ano,
                    func.sum(ComercioExterior.valor_usd).label('valor_total')
                )
                
                if data_corte:
                    query_valores_mes = query_valores_mes.filter(ComercioExterior.data >= data_corte.date())
                
                valores_por_mes_novo = query_valores_mes.group_by(
                    ComercioExterior.mes,
                    ComercioExterior.ano
                ).order_by(
                    ComercioExterior.ano,
                    ComercioExterior.mes
                ).all()
                
                valores_por_mes_dict = {
                    f"{ano}-{mes:02d}": float(valor)
                    for mes, ano, valor in valores_por_mes_novo
                }
                
                # Pesos por mês
                query_pesos_mes = db.query(
                    ComercioExterior.mes,
                    ComercioExterior.ano,
                    func.sum(ComercioExterior.peso_kg).label('peso_total')
                )
                
                if data_corte:
                    query_pesos_mes = query_pesos_mes.filter(ComercioExterior.data >= data_corte.date())
                
                pesos_por_mes_novo = query_pesos_mes.group_by(
                    ComercioExterior.mes,
                    ComercioExterior.ano
                ).order_by(
                    ComercioExterior.ano,
                    ComercioExterior.mes
                ).all()
                
                pesos_por_mes_dict = {
                    f"{ano}-{mes:02d}": float(peso) if peso else 0.0
                    for mes, ano, peso in pesos_por_mes_novo
                }
                
                # Registros por mês
                query_registros_mes = db.query(
                    ComercioExterior.mes,
                    ComercioExterior.ano,
                    func.count(ComercioExterior.id).label('count')
                )
                
                if data_corte:
                    query_registros_mes = query_registros_mes.filter(ComercioExterior.data >= data_corte.date())
                
                registros_por_mes_novo = query_registros_mes.group_by(
                    ComercioExterior.mes,
                    ComercioExterior.ano
                ).order_by(
                    ComercioExterior.ano,
                    ComercioExterior.mes
                ).all()
                
                registros_dict = {
                    f"{ano}-{mes:02d}": int(count)
                    for mes, ano, count in registros_por_mes_novo
                }
                
                # Atualizar valores
                valor_total_imp = float(importacoes)
                valor_total_exp = float(exportacoes)
                volume_imp = float(peso_imp)
                volume_exp = float(peso_exp)
                valor_total = float(importacoes + exportacoes)
                
                logger.info(f"✅ Dados carregados das novas tabelas: {len(principais_ncms_list)} NCMs, {valor_total:.2f} USD total")
        except Exception as e:
            logger.debug(f"Erro ao buscar dados das novas tabelas: {e}")
    
    # Se não houver dados, retornar resposta vazia rapidamente (não travar)
    if valor_total == 0 and not principais_ncms_list and not principais_paises_list:
        logger.info("Nenhum dado encontrado, retornando resposta vazia")
        return DashboardStats(
            volume_importacoes=0.0,
            volume_exportacoes=0.0,
            valor_total_usd=0.0,
            valor_total_importacoes=None,
            valor_total_exportacoes=None,
            principais_ncms=[],
            principais_paises=[],
            registros_por_mes={},
            valores_por_mes={},
            pesos_por_mes={}
        )
    
    stats_response = DashboardStats(
        volume_importacoes=float(volume_imp),
        volume_exportacoes=float(volume_exp),
        valor_total_usd=float(valor_total),
        valor_total_importacoes=float(valor_total_imp) if valor_total_imp else None,
        valor_total_exportacoes=float(valor_total_exp) if valor_total_exp else None,
        principais_ncms=principais_ncms_list if principais_ncms_list else [],
        principais_paises=principais_paises_list if principais_paises_list else [],
        registros_por_mes=registros_dict if registros_dict else {},
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
    q: str = Query("", description="Termo de busca (vazio retorna sugestões)"),
    limit: int = Query(default=20, ge=1, le=100),
    incluir_sugestoes: bool = Query(default=True, description="Incluir empresas sugeridas do MDIC"),
    ncm: Optional[str] = Query(None, description="Filtrar por NCM específico"),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas importadoras.
    Retorna empresas que contêm o termo de busca no nome.
    Se não encontrar resultados, inclui empresas sugeridas do MDIC.
    """
    from sqlalchemy import func, distinct
    
    try:
        resultado = []
        
        # 1. Buscar empresas importadoras que contêm o termo nas operações
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
        
        resultado = [
            {
                "nome": empresa,
                "total_operacoes": int(total_operacoes),
                "valor_total": float(valor_total or 0),
                "fonte": "operacoes"
            }
            for empresa, total_operacoes, valor_total in empresas
        ]
        
        # 2. Se não encontrou resultados ou quer incluir sugestões, buscar no MDIC
        if (len(resultado) < limit and incluir_sugestoes) or len(resultado) == 0:
            try:
                from data_collector.empresas_mdic_scraper import EmpresasMDICScraper
                # Importação condicional - apenas quando necessário
                
                scraper = EmpresasMDICScraper()
                empresas_mdic = await scraper.coletar_empresas()
                
                # Filtrar empresas do MDIC que são importadoras e contêm o termo
                empresas_mdic_filtradas = [
                    emp for emp in empresas_mdic
                    if emp.get("tipo_operacao", "").lower() in ["importação", "importacao", ""] and
                    q.lower() in emp.get("razao_social", "").lower()
                ]
                
                # Adicionar empresas do MDIC que não estão no resultado
                empresas_ja_adicionadas = {r["nome"].lower() for r in resultado}
                
                for emp in empresas_mdic_filtradas[:limit - len(resultado)]:
                    nome = emp.get("razao_social") or emp.get("nome_fantasia", "")
                    if nome.lower() not in empresas_ja_adicionadas:
                        resultado.append({
                            "nome": nome,
                            "total_operacoes": 0,  # Não temos dados de operações do MDIC
                            "valor_total": 0.0,
                            "fonte": "mdic",
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf"),
                            "faixa_valor": emp.get("faixa_valor")
                        })
                        empresas_ja_adicionadas.add(nome.lower())
                
            except Exception as e:
                logger.debug(f"Erro ao buscar empresas MDIC para autocomplete: {e}")
        
        # 3. Se ainda não tem resultados suficientes, buscar sugestões de sinergias
        if len(resultado) < limit and incluir_sugestoes:
            try:
                # Importação condicional - apenas quando necessário
                if not SINERGIA_AVAILABLE or SinergiaAnalyzer is None:
                    raise ImportError("SinergiaAnalyzer não disponível")
                from data_collector.cnae_analyzer import CNAEAnalyzer
                
                # Carregar CNAE se disponível
                cnae_analyzer = None
                try:
                    arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
                    if arquivo_cnae.exists():
                        cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                        cnae_analyzer.carregar_cnae_excel()
                except:
                    pass
                
                analyzer = SinergiaAnalyzer(cnae_analyzer)
                
                # Buscar empresas com sinergia que são importadoras
                empresas_com_sinergia = analyzer.analisar_sinergias_por_empresa(db, {}, limit * 2)
                
                # Filtrar empresas que contêm o termo e são importadoras
                empresas_ja_adicionadas = {r["nome"].lower() for r in resultado}
                
                for emp in empresas_com_sinergia:
                    nome = emp.get("razao_social", "")
                    if (nome.lower() not in empresas_ja_adicionadas and
                        q.lower() in nome.lower() and
                        emp.get("importacoes", {}).get("total_operacoes", 0) > 0):
                        resultado.append({
                            "nome": nome,
                            "total_operacoes": emp.get("importacoes", {}).get("total_operacoes", 0),
                            "valor_total": emp.get("importacoes", {}).get("valor_total", 0.0),
                            "fonte": "sinergia",
                            "potencial_sinergia": emp.get("potencial_sinergia", 0),
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf")
                        })
                        empresas_ja_adicionadas.add(nome.lower())
                        
                        if len(resultado) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Erro ao buscar sugestões de sinergia: {e}")
        
        return resultado[:limit]
        
    except Exception as e:
        logger.error(f"Erro ao buscar importadoras: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


@app.get("/empresas/autocomplete/exportadoras")
async def autocomplete_exportadoras(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    limit: int = Query(default=20, ge=1, le=100),
    incluir_sugestoes: bool = Query(default=True, description="Incluir empresas sugeridas do MDIC"),
    db: Session = Depends(get_db)
):
    """
    Autocomplete para empresas exportadoras.
    Retorna empresas que contêm o termo de busca no nome.
    Se não encontrar resultados, inclui empresas sugeridas do MDIC e sinergias.
    """
    from sqlalchemy import func
    
    try:
        logger.info(f"🔍 Buscando exportadoras com termo: '{q}'")
        
        resultado = []
        query_lower = q.lower() if q else ""
        
        # 1. Se tem query, buscar nas operações primeiro
        if q:
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
                        "valor_total": float(valor_total or 0),
                        "fonte": "operacoes"
                    })
        
        logger.info(f"✅ Encontradas {len(resultado)} exportadoras nas operações para '{q}'")
        
        # 2. Se não encontrou resultados ou query vazia, buscar no MDIC
        if (len(resultado) < limit and incluir_sugestoes) or not q:
            try:
                from data_collector.empresas_mdic_scraper import EmpresasMDICScraper
                
                scraper = EmpresasMDICScraper()
                empresas_mdic = await scraper.coletar_empresas()
                
                # Filtrar empresas do MDIC que são exportadoras e contêm o termo
                empresas_mdic_filtradas = [
                    emp for emp in empresas_mdic
                    if emp.get("tipo_operacao", "").lower() in ["exportação", "exportacao", ""] and
                    q.lower() in emp.get("razao_social", "").lower()
                ]
                
                # Adicionar empresas do MDIC que não estão no resultado
                empresas_ja_adicionadas = {r["nome"].lower() for r in resultado}
                
                for emp in empresas_mdic_filtradas[:limit - len(resultado)]:
                    nome = emp.get("razao_social") or emp.get("nome_fantasia", "")
                    if nome.lower() not in empresas_ja_adicionadas:
                        resultado.append({
                            "nome": nome,
                            "total_operacoes": 0,
                            "valor_total": 0.0,
                            "fonte": "mdic",
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf"),
                            "faixa_valor": emp.get("faixa_valor")
                        })
                        empresas_ja_adicionadas.add(nome.lower())
                
            except Exception as e:
                logger.debug(f"Erro ao buscar empresas MDIC: {e}")
        
        # 3. Se ainda não tem resultados suficientes, buscar sugestões de sinergias
        if len(resultado) < limit and incluir_sugestoes:
            try:
                # Importação condicional - apenas quando necessário
                if not SINERGIA_AVAILABLE or SinergiaAnalyzer is None:
                    raise ImportError("SinergiaAnalyzer não disponível")
                from data_collector.cnae_analyzer import CNAEAnalyzer
                
                # Carregar CNAE se disponível
                cnae_analyzer = None
                try:
                    arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
                    if arquivo_cnae.exists():
                        cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                        cnae_analyzer.carregar_cnae_excel()
                except:
                    pass
                
                analyzer = SinergiaAnalyzer(cnae_analyzer)
                
                # Buscar empresas com sinergia que são exportadoras
                empresas_com_sinergia = analyzer.analisar_sinergias_por_empresa(db, {}, limit * 2)
                
                # Filtrar empresas que contêm o termo e são exportadoras
                empresas_ja_adicionadas = {r["nome"].lower() for r in resultado}
                
                for emp in empresas_com_sinergia:
                    nome = emp.get("razao_social", "")
                    if (nome.lower() not in empresas_ja_adicionadas and
                        q.lower() in nome.lower() and
                        emp.get("exportacoes", {}).get("total_operacoes", 0) > 0):
                        resultado.append({
                            "nome": nome,
                            "total_operacoes": emp.get("exportacoes", {}).get("total_operacoes", 0),
                            "valor_total": emp.get("exportacoes", {}).get("valor_total", 0.0),
                            "fonte": "sinergia",
                            "potencial_sinergia": emp.get("potencial_sinergia", 0),
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf")
                        })
                        empresas_ja_adicionadas.add(nome.lower())
                        
                        if len(resultado) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Erro ao buscar sugestões de sinergia: {e}")
        
        return resultado[:limit]
        
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


# Endpoints para cruzamento de dados com empresas do MDIC
try:
    from data_collector.cruzamento_dados import CruzamentoDados
    from data_collector.empresas_mdic_scraper import EmpresasMDICScraper
    CRUZAMENTO_AVAILABLE = True
except ImportError:
    CRUZAMENTO_AVAILABLE = False
    logger.warning("Módulos de cruzamento não disponíveis")

# Endpoints para análise de sinergias e CNAE
try:
    from data_collector.sinergia_analyzer import SinergiaAnalyzer
    from data_collector.cnae_analyzer import CNAEAnalyzer
    SINERGIA_AVAILABLE = True
except (ImportError, NameError) as e:
    SINERGIA_AVAILABLE = False
    SinergiaAnalyzer = None
    CNAEAnalyzer = None
    logger.warning(f"Módulos de sinergia não disponíveis: {e}")


@app.post("/coletar-empresas-mdic")
async def coletar_empresas_mdic(
    ano: Optional[int] = Query(None, description="Ano específico (None = ano atual)"),
    db: Session = Depends(get_db)
):
    """
    Coleta lista de empresas exportadoras e importadoras do MDIC.
    Esta lista contém CNPJ e nome das empresas, mas sem detalhamento por NCM.
    """
    if not CRUZAMENTO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de cruzamento não disponível")
    
    try:
        scraper = EmpresasMDICScraper()
        empresas = await scraper.coletar_empresas(ano)
        
        return {
            "success": True,
            "message": f"Coletadas {len(empresas)} empresas do MDIC",
            "total_empresas": len(empresas),
            "ano": ano or datetime.now().year,
            "empresas": empresas[:100]  # Retornar primeiras 100 como exemplo
        }
    except Exception as e:
        logger.error(f"Erro ao coletar empresas do MDIC: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao coletar empresas: {str(e)}")


class CruzamentoFiltros(BaseModel):
    """Filtros para cruzamento de dados."""
    ncm: Optional[str] = None
    tipo_operacao: Optional[str] = None
    uf: Optional[str] = None
    limite: int = 1000


@app.post("/cruzar-dados-empresas")
async def cruzar_dados_empresas(
    filtros: CruzamentoFiltros,
    db: Session = Depends(get_db)
):
    """
    Cruza dados de operações com lista de empresas do MDIC.
    Tenta identificar empresas por CNPJ ou razão social.
    """
    if not CRUZAMENTO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de cruzamento não disponível")
    
    try:
        cruzamento = CruzamentoDados()
        
        filtros_dict = {}
        if filtros.ncm:
            filtros_dict["ncm"] = filtros.ncm
        if filtros.tipo_operacao:
            filtros_dict["tipo_operacao"] = filtros.tipo_operacao
        if filtros.uf:
            filtros_dict["uf"] = filtros.uf
        
        resultados = await cruzamento.cruzar_operacoes_bulk(
            db,
            filtros=filtros_dict if filtros_dict else None,
            limite=filtros.limite
        )
        
        estatisticas = cruzamento.estatisticas_cruzamento(resultados)
        
        return {
            "success": True,
            "message": f"Cruzamento concluído: {estatisticas['operacoes_identificadas']}/{estatisticas['total_operacoes']} operações identificadas",
            "estatisticas": estatisticas,
            "resultados": resultados[:100]  # Retornar primeiras 100 como exemplo
        }
    except Exception as e:
        logger.error(f"Erro ao cruzar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao cruzar dados: {str(e)}")


@app.get("/estatisticas-cruzamento")
async def estatisticas_cruzamento(
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas sobre cruzamento de dados.
    """
    if not CRUZAMENTO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de cruzamento não disponível")
    
    try:
        # Contar operações com CNPJ
        from sqlalchemy import func, or_
        
        total_operacoes = db.query(func.count(OperacaoComex.id)).scalar() or 0
        
        operacoes_com_cnpj = db.query(func.count(OperacaoComex.id)).filter(
            or_(
                OperacaoComex.cnpj_importador.isnot(None),
                OperacaoComex.cnpj_exportador.isnot(None)
            )
        ).scalar() or 0
        
        operacoes_com_razao_social = db.query(func.count(OperacaoComex.id)).filter(
            or_(
                OperacaoComex.razao_social_importador.isnot(None),
                OperacaoComex.razao_social_exportador.isnot(None)
            )
        ).scalar() or 0
        
        return {
            "total_operacoes": total_operacoes,
            "operacoes_com_cnpj": operacoes_com_cnpj,
            "operacoes_com_razao_social": operacoes_com_razao_social,
            "taxa_cnpj": (operacoes_com_cnpj / total_operacoes * 100) if total_operacoes > 0 else 0,
            "taxa_razao_social": (operacoes_com_razao_social / total_operacoes * 100) if total_operacoes > 0 else 0,
            "nota": "Dados públicos são anonimizados. CNPJ/razão social podem não estar disponíveis em todas as operações."
        }
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@app.post("/carregar-cnae")
async def carregar_cnae(
    arquivo_path: Optional[str] = Query(None, description="Caminho do arquivo Excel CNAE")
):
    """
    Carrega arquivo Excel com classificação CNAE.
    """
    if not SINERGIA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de sinergia não disponível")
    
    try:
        from pathlib import Path
        
        if arquivo_path:
            arquivo = Path(arquivo_path)
        else:
            # Tentar caminho padrão
            arquivo = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
        
        analyzer = CNAEAnalyzer(arquivo)
        sucesso = analyzer.carregar_cnae_excel()
        
        if sucesso:
            stats = analyzer.estatisticas()
            return {
                "success": True,
                "message": f"CNAE carregado com sucesso",
                "estatisticas": stats
            }
        else:
            raise HTTPException(status_code=400, detail="Não foi possível carregar arquivo CNAE")
    except Exception as e:
        logger.error(f"Erro ao carregar CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao carregar CNAE: {str(e)}")


@app.get("/analisar-sinergias-estado")
async def analisar_sinergias_estado(
    uf: Optional[str] = Query(None, description="UF específica (None = todos)"),
    db: Session = Depends(get_db)
):
    """
    Analisa sinergias de importação/exportação por estado.
    """
    if not SINERGIA_AVAILABLE or SinergiaAnalyzer is None:
        raise HTTPException(status_code=501, detail="Módulo de sinergia não disponível")
    
    try:
        analyzer = SinergiaAnalyzer()
        resultado = analyzer.analisar_sinergias_por_estado(db, uf)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao analisar sinergias: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao analisar sinergias: {str(e)}")


@app.post("/analisar-sinergias-empresas")
async def analisar_sinergias_empresas(
    limite: int = Query(100, description="Limite de empresas a analisar"),
    ano: Optional[int] = Query(None, description="Ano para coletar empresas do MDIC"),
    db: Session = Depends(get_db)
):
    """
    Analisa sinergias por empresa, integrando com CNAE.
    """
    if not SINERGIA_AVAILABLE or not CRUZAMENTO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulos necessários não disponíveis")
    
    try:
        # Carregar empresas do MDIC
        scraper = EmpresasMDICScraper()
        empresas_lista = await scraper.coletar_empresas(ano)
        
        # Criar índice por CNPJ
        empresas_mdic = {}
        for empresa in empresas_lista:
            cnpj = empresa.get("cnpj")
            if cnpj:
                empresas_mdic[cnpj] = empresa
        
        # Carregar CNAE se disponível
        cnae_analyzer = None
        try:
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
            if arquivo_cnae.exists():
                cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                cnae_analyzer.carregar_cnae_excel()
        except Exception as e:
            logger.warning(f"Não foi possível carregar CNAE: {e}")
        
        # Analisar sinergias
        analyzer = SinergiaAnalyzer(cnae_analyzer)
        resultados = analyzer.analisar_sinergias_por_empresa(db, empresas_mdic, limite)
        
        return {
            "success": True,
            "message": f"Análise de sinergias concluída para {len(resultados)} empresas",
            "total_empresas_mdic": len(empresas_mdic),
            "empresas_analisadas": len(resultados),
            "cnae_carregado": cnae_analyzer is not None,
            "resultados": resultados
        }
    except Exception as e:
        logger.error(f"Erro ao analisar sinergias de empresas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao analisar sinergias: {str(e)}")


@app.get("/sugestoes-empresa/{cnpj}")
async def sugestoes_empresa(
    cnpj: str,
    db: Session = Depends(get_db)
):
    """
    Gera sugestões de importação/exportação para uma empresa específica.
    """
    if not SINERGIA_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulo de sinergia não disponível")
    
    try:
        # Buscar empresa no MDIC
        scraper = EmpresasMDICScraper()
        empresas_lista = await scraper.coletar_empresas()
        
        empresa_mdic = None
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
        for empresa in empresas_lista:
            if empresa.get("cnpj") == cnpj_limpo:
                empresa_mdic = empresa
                break
        
        if not empresa_mdic:
            raise HTTPException(status_code=404, detail="Empresa não encontrada no MDIC")
        
        # Carregar CNAE
        cnae_analyzer = None
        try:
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
            if arquivo_cnae.exists():
                cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                cnae_analyzer.carregar_cnae_excel()
        except Exception as e:
            logger.warning(f"Não foi possível carregar CNAE: {e}")
        
        # Analisar empresa
        analyzer = SinergiaAnalyzer(cnae_analyzer)
        sinergia = analyzer._analisar_empresa_individual(
            db,
            cnpj_limpo,
            empresa_mdic,
            empresa_mdic.get("uf")
        )
        
        if not sinergia:
            raise HTTPException(status_code=404, detail="Não foi possível analisar empresa")
        
        return {
            "success": True,
            "empresa": sinergia,
            "sugestoes": {
                "importacao": sinergia.get("sugestao", ""),
                "exportacao": sinergia.get("sugestao", ""),
                "cnae": sinergia.get("cnae"),
                "classificacao_cnae": sinergia.get("classificacao_cnae")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar sugestões: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao gerar sugestões: {str(e)}")


@app.post("/atualizar-dados-completos")
async def atualizar_dados_completos():
    """
    Executa atualização completa de todos os dados (empresas MDIC, relacionamentos, sinergias).
    Útil para atualização manual ou via scheduler.
    """
    try:
        from utils.data_updater import DataUpdater
        
        updater = DataUpdater()
        resultado = await updater.atualizar_completo()
        
        return resultado
    except Exception as e:
        logger.error(f"Erro na atualização completa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na atualização: {str(e)}")


@app.get("/dashboard/sinergias-estado")
async def dashboard_sinergias_estado(
    uf: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint otimizado para dashboard - sinergias por estado.
    """
    if not SINERGIA_AVAILABLE or SinergiaAnalyzer is None:
        raise HTTPException(status_code=501, detail="Módulo de sinergia não disponível")
    
    try:
        analyzer = SinergiaAnalyzer()
        resultado = analyzer.analisar_sinergias_por_estado(db, uf)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao buscar sinergias: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar sinergias: {str(e)}")


@app.get("/dashboard/sugestoes-empresas")
async def dashboard_sugestoes_empresas(
    limite: int = Query(20, description="Número de sugestões"),
    tipo: Optional[str] = Query(None, description="Tipo: 'importacao', 'exportacao', ou None para ambos"),
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    db: Session = Depends(get_db)
):
    """
    Endpoint otimizado para dashboard - sugestões de empresas.
    Retorna empresas com maior potencial de sinergia.
    """
    if not SINERGIA_AVAILABLE or not CRUZAMENTO_AVAILABLE:
        raise HTTPException(status_code=501, detail="Módulos necessários não disponíveis")
    
    try:
        # Carregar empresas
        scraper = EmpresasMDICScraper()
        empresas_lista = await scraper.coletar_empresas()
        empresas_mdic = {}
        for empresa in empresas_lista:
            cnpj = empresa.get("cnpj")
            if cnpj:
                empresas_mdic[cnpj] = empresa
        
        # Carregar CNAE
        cnae_analyzer = None
        try:
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
            if arquivo_cnae.exists():
                cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                cnae_analyzer.carregar_cnae_excel()
        except Exception as e:
            logger.warning(f"Não foi possível carregar CNAE: {e}")
        
        # Analisar sinergias
        analyzer = SinergiaAnalyzer(cnae_analyzer)
        resultados = analyzer.analisar_sinergias_por_empresa(db, empresas_mdic, limite * 2)
        
        # Filtrar por tipo se especificado
        if tipo == "importacao":
            resultados = [r for r in resultados if r["importacoes"]["total_operacoes"] > 0 and r["exportacoes"]["total_operacoes"] == 0]
        elif tipo == "exportacao":
            resultados = [r for r in resultados if r["exportacoes"]["total_operacoes"] > 0 and r["importacoes"]["total_operacoes"] == 0]
        
        # Filtrar por UF se especificado
        if uf:
            resultados = [r for r in resultados if r.get("uf") == uf]
        
        # Ordenar por potencial e limitar
        resultados.sort(key=lambda x: x.get("potencial_sinergia", 0), reverse=True)
        resultados = resultados[:limite]
        
        return {
            "success": True,
            "total": len(resultados),
            "sugestoes": resultados
        }
    except Exception as e:
        logger.error(f"Erro ao buscar sugestões: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao buscar sugestões: {str(e)}")


@app.get("/dashboard/empresas-recomendadas")
async def get_empresas_recomendadas(
    limite: int = Query(default=100, ge=1, le=5000),
    tipo: Optional[str] = Query(default=None, description="Filtrar por tipo: CLIENTE_POTENCIAL ou FORNECEDOR_POTENCIAL"),
    uf: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None)
):
    """
    Retorna lista de empresas recomendadas para o dashboard.
    """
    try:
        import json
        from pathlib import Path
        
        arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.xlsx"
        
        if not arquivo_empresas.exists():
            # Tentar CSV como fallback
            arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.csv"
            if not arquivo_empresas.exists():
                return {
                    "success": False,
                    "message": "Arquivo de empresas recomendadas não encontrado",
                    "data": []
                }
        
        import pandas as pd
        
        if arquivo_empresas.suffix == '.xlsx':
            df = pd.read_excel(arquivo_empresas)
        else:
            df = pd.read_csv(arquivo_empresas, encoding='utf-8-sig')
        
        # Aplicar filtros
        if tipo:
            df = df[df['Sugestão'] == tipo]
        if uf:
            df = df[df['Estado'] == uf]
        if ncm:
            df = df[df['NCM Relacionado'] == ncm]
        
        # Limitar resultados
        df = df.head(limite)
        
        # Converter para dict
        empresas = df.to_dict('records')
        
        return {
            "success": True,
            "total": len(empresas),
            "data": empresas
        }
    except Exception as e:
        logger.error(f"Erro ao buscar empresas recomendadas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao buscar empresas recomendadas: {str(e)}")


def _buscar_empresas_importadoras_recomendadas(limite: int = 10):
    """
    Função auxiliar síncrona para buscar empresas importadoras recomendadas.
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.xlsx"
        
        if not arquivo_empresas.exists():
            arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.csv"
            if not arquivo_empresas.exists():
                return []
        
        if arquivo_empresas.suffix == '.xlsx':
            df = pd.read_excel(arquivo_empresas)
        else:
            df = pd.read_csv(arquivo_empresas, encoding='utf-8-sig')
        
        # Filtrar empresas que importam (têm valor de importação > 0)
        df_importadoras = df[
            (df['Importado (R$)'].notna()) & 
            (df['Importado (R$)'] > 0)
        ].copy()
        
        # Agrupar por empresa (CNPJ) e somar valores
        df_agrupado = df_importadoras.groupby('CNPJ').agg({
            'Razão Social': 'first',
            'Nome Fantasia': 'first',
            'Estado': 'first',
            'Importado (R$)': 'sum',
            'Peso Participação (0-100)': 'max'
        }).reset_index()
        
        # Ordenar por valor de importação
        df_agrupado = df_agrupado.sort_values('Importado (R$)', ascending=False).head(limite)
        
        # Converter para formato esperado pelo dashboard
        empresas = []
        for _, row in df_agrupado.iterrows():
            empresas.append({
                "pais": row['Razão Social'] or row['Nome Fantasia'],
                "valor_total": float(row['Importado (R$)']) / 5.0,  # Converter BRL para USD
                "total_operacoes": 1,
                "uf": row.get('Estado', ''),
                "peso_participacao": float(row.get('Peso Participação (0-100)', 0))
            })
        
        return empresas
    except Exception as e:
        logger.debug(f"Erro ao buscar empresas importadoras: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def _buscar_empresas_exportadoras_recomendadas(limite: int = 10):
    """
    Função auxiliar síncrona para buscar empresas exportadoras recomendadas.
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.xlsx"
        
        if not arquivo_empresas.exists():
            arquivo_empresas = Path(__file__).parent.parent / "data" / "empresas_recomendadas.csv"
            if not arquivo_empresas.exists():
                return []
        
        if arquivo_empresas.suffix == '.xlsx':
            df = pd.read_excel(arquivo_empresas)
        else:
            df = pd.read_csv(arquivo_empresas, encoding='utf-8-sig')
        
        # Filtrar empresas que exportam (têm valor de exportação > 0)
        df_exportadoras = df[
            (df['Exportado (R$)'].notna()) & 
            (df['Exportado (R$)'] > 0)
        ].copy()
        
        # Agrupar por empresa (CNPJ) e somar valores
        df_agrupado = df_exportadoras.groupby('CNPJ').agg({
            'Razão Social': 'first',
            'Nome Fantasia': 'first',
            'Estado': 'first',
            'Exportado (R$)': 'sum',
            'Peso Participação (0-100)': 'max'
        }).reset_index()
        
        # Ordenar por valor de exportação
        df_agrupado = df_agrupado.sort_values('Exportado (R$)', ascending=False).head(limite)
        
        # Converter para formato esperado pelo dashboard
        empresas = []
        for _, row in df_agrupado.iterrows():
            empresas.append({
                "pais": row['Razão Social'] or row['Nome Fantasia'],
                "valor_total": float(row['Exportado (R$)']) / 5.0,  # Converter BRL para USD
                "total_operacoes": 1,
                "uf": row.get('Estado', ''),
                "peso_participacao": float(row.get('Peso Participação (0-100)', 0))
            })
        
        return empresas
    except Exception as e:
        logger.debug(f"Erro ao buscar empresas exportadoras: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


@app.get("/dashboard/empresas-importadoras")
async def get_empresas_importadoras_recomendadas(
    limite: int = Query(default=10, ge=1, le=100)
):
    """
    Retorna empresas recomendadas que são importadoras (para seção "Prováveis Importadores").
    """
    empresas = _buscar_empresas_importadoras_recomendadas(limite)
    return {
        "success": True,
        "data": empresas
    }


@app.get("/dashboard/empresas-exportadoras")
async def get_empresas_exportadoras_recomendadas(
    limite: int = Query(default=10, ge=1, le=100)
):
    """
    Retorna empresas recomendadas que são exportadoras (para seção "Prováveis Exportadores").
    """
    empresas = _buscar_empresas_exportadoras_recomendadas(limite)
    return {
        "success": True,
        "data": empresas
    }


@app.get("/dashboard/dados-comexstat")
async def get_dados_comexstat():
    """
    Retorna resumo dos dados do arquivo Excel ComexStat.
    """
    try:
        import json
        from pathlib import Path
        
        arquivo_resumo = Path(__file__).parent.parent / "data" / "resumo_dados_comexstat.json"
        
        if not arquivo_resumo.exists():
            return {
                "success": False,
                "message": "Arquivo de resumo não encontrado. Execute o script de processamento primeiro.",
                "data": None
            }
        
        with open(arquivo_resumo, 'r', encoding='utf-8') as f:
            resumo = json.load(f)
        
        return {
            "success": True,
            "data": resumo
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados ComexStat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")


@app.get("/dashboard/dados-ncm-comexstat")
async def get_dados_ncm_comexstat(
    limite: int = Query(default=100, ge=1, le=1000),
    uf: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None, description="importacao ou exportacao")
):
    """
    Retorna dados agregados por NCM do arquivo Excel ComexStat.
    """
    try:
        import json
        from pathlib import Path
        
        arquivo_ncm = Path(__file__).parent.parent / "data" / "dados_ncm_comexstat.json"
        
        if not arquivo_ncm.exists():
            return {
                "success": False,
                "message": "Arquivo de dados NCM não encontrado. Execute o script de processamento primeiro.",
                "data": []
            }
        
        with open(arquivo_ncm, 'r', encoding='utf-8') as f:
            dados_ncm = json.load(f)
        
        # Aplicar filtros
        if uf:
            dados_ncm = [d for d in dados_ncm if d.get('uf') == uf]
        
        if tipo == 'importacao':
            dados_ncm = [d for d in dados_ncm if d.get('valor_importacao_usd', 0) > 0]
        elif tipo == 'exportacao':
            dados_ncm = [d for d in dados_ncm if d.get('valor_exportacao_usd', 0) > 0]
        
        # Ordenar por valor total e limitar
        dados_ncm.sort(
            key=lambda x: x.get('valor_importacao_usd', 0) + x.get('valor_exportacao_usd', 0),
            reverse=True
        )
        dados_ncm = dados_ncm[:limite]
        
        return {
            "success": True,
            "total": len(dados_ncm),
            "data": dados_ncm
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados NCM: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados NCM: {str(e)}")


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

