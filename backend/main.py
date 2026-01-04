"""
Aplicação principal FastAPI.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel
import uvicorn

from loguru import logger

from config import settings
from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte, Usuario, AprovacaoCadastro
from data_collector import DataCollector, ComexStatAPIClient
from api.export import router as export_router
from auth import authenticate_user, create_access_token, get_current_user, get_password_hash, validate_password
from fastapi import Form
from services.email_service import enviar_email_aprovacao, enviar_email_cadastro_aprovado
import secrets
from datetime import timedelta
from fastapi import BackgroundTasks

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
    principais_empresas: Optional[List[dict]] = []
    registros_por_mes: dict
    valores_por_mes_com_peso: Optional[List[dict]] = []


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
    empresa: Optional[str] = None
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
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
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
    meses: int = Query(default=3, ge=1, le=24, description="Número de meses (1-24)"),
    tipo_operacao: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None),
    empresa: Optional[str] = Query(default=None),
    ncms: Optional[str] = Query(default=None, description="Lista de até 3 NCMs separados por vírgula"),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas para o dashboard.
    """
    from sqlalchemy import func, and_, or_, text
    from datetime import datetime, timedelta
    
    logger.info(f"=== Dashboard Stats Request ===")
    logger.info(f"Parâmetros: meses={meses}, tipo_operacao={tipo_operacao}, ncm={ncm}, ncms={ncms}, empresa={empresa}")
    
    # Calcular data inicial
    data_inicio = datetime.now() - timedelta(days=30 * meses)
    data_fim = datetime.now()
    
    # Se há filtro de NCM específico, verificar se há dados no período padrão
    # Se não houver, expandir para até 2 anos
    if ncms_list:
        # Verificar se há dados no período padrão
        total_no_periodo = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.ncm.in_(ncms_list),
            OperacaoComex.data_operacao >= data_inicio.date(),
            OperacaoComex.data_operacao <= data_fim.date()
        ).scalar() or 0
        
        if total_no_periodo == 0:
            # Expandir período para até 2 anos
            logger.info(f"Nenhum dado encontrado no período padrão ({meses} meses)")
            logger.info("Expandindo busca para até 2 anos...")
            data_inicio = datetime.now() - timedelta(days=730)  # 2 anos
            logger.info(f"Novo período: {data_inicio.date()} até {data_fim.date()}")
    
    logger.info(f"Data inicial calculada: {data_inicio.date()}")
    
    # Construir filtros base
    base_filters = [
        OperacaoComex.data_operacao >= data_inicio.date(),
        OperacaoComex.data_operacao <= data_fim.date()
    ]
    
    # Verificar quantos registros existem no período
    total_registros = db.query(func.count(OperacaoComex.id)).filter(
        OperacaoComex.data_operacao >= data_inicio.date()
    ).scalar() or 0
    logger.info(f"Total de registros no período: {total_registros}")
    
    # Aplicar filtro de NCM(s) se fornecido
    # Priorizar 'ncms' (múltiplos) sobre 'ncm' (único)
    ncms_list = []
    if ncms:
        # Separar por vírgula e limpar
        ncms_list = [n.strip().replace('.', '').replace(' ', '') for n in ncms.split(',')]
        ncms_list = [n for n in ncms_list if len(n) == 8]
        logger.info(f"NCMs processados: {ncms_list}")
        # Limitar a 3 NCMs
        if len(ncms_list) > 3:
            ncms_list = ncms_list[:3]
            logger.warning(f"Múltiplos NCMs fornecidos, usando apenas os 3 primeiros: {ncms_list}")
    elif ncm:
        # Fallback para ncm único
        ncm_limpo = ncm.replace('.', '').replace(' ', '')
        if len(ncm_limpo) == 8:
            ncms_list = [ncm_limpo]
    
    if ncms_list:
        base_filters.append(OperacaoComex.ncm.in_(ncms_list))
        logger.info(f"Filtro de NCMs aplicado: {ncms_list}")
        
        # Verificar quantos registros existem para cada NCM
        for ncm_item in ncms_list:
            count = db.query(func.count(OperacaoComex.id)).filter(
                OperacaoComex.ncm == ncm_item,
                OperacaoComex.data_operacao >= data_inicio.date()
            ).scalar() or 0
            logger.info(f"NCM {ncm_item}: {count} registros no período")
    
    # Aplicar filtro de empresa se fornecido
    if empresa:
        base_filters.append(OperacaoComex.nome_empresa.ilike(f"%{empresa}%"))
    
    # Aplicar filtro de tipo de operação se fornecido
    tipo_filtro = None
    if tipo_operacao:
        if tipo_operacao == "Importação":
            tipo_filtro = TipoOperacao.IMPORTACAO
        elif tipo_operacao == "Exportação":
            tipo_filtro = TipoOperacao.EXPORTACAO
    
    # Volume de importações e exportações
    filtros_imp = base_filters.copy()
    if tipo_filtro:
        filtros_imp.append(OperacaoComex.tipo_operacao == tipo_filtro)
    else:
        filtros_imp.append(OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO)
    
    volume_imp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
        and_(*filtros_imp)
    ).scalar() or 0.0
    
    filtros_exp = base_filters.copy()
    if tipo_filtro:
        filtros_exp.append(OperacaoComex.tipo_operacao == tipo_filtro)
    else:
        filtros_exp.append(OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO)
    
    volume_exp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
        and_(*filtros_exp)
    ).scalar() or 0.0
    
    # Valor total movimentado
    valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
        and_(*base_filters)
    ).scalar() or 0.0
    logger.info(f"Valor total USD: {valor_total}")
    logger.info(f"Volume importações: {volume_imp}, Volume exportações: {volume_exp}")
    
    # Verificar se há dados suficientes no banco para os NCMs específicos
    # Contar registros específicos para os NCMs filtrados
    # IMPORTANTE: Verificar por contagem de registros, não apenas por valor total
    # pois pode haver registros com valor zero que ainda são válidos
    tem_dados_no_banco = False
    total_registros_ncms = 0
    
    if ncms_list:
        total_registros_ncms = db.query(func.count(OperacaoComex.id)).filter(
            and_(*base_filters)
        ).scalar() or 0
        tem_dados_no_banco = total_registros_ncms > 0
        logger.info(f"Registros encontrados no banco para NCMs filtrados: {total_registros_ncms}")
        logger.info(f"Valor total encontrado: ${valor_total:,.2f}")
        
        # Se há registros mas valor total é zero, ainda considerar que há dados
        if total_registros_ncms > 0:
            tem_dados_no_banco = True
            logger.info(f"✅ Há {total_registros_ncms} registros no banco para os NCMs filtrados")
    else:
        # Sem filtro de NCM, verificar por valor total
        tem_dados_no_banco = valor_total > 0 or volume_imp > 0 or volume_exp > 0
        total_registros_ncms = db.query(func.count(OperacaoComex.id)).filter(
            and_(*base_filters)
        ).scalar() or 0
        logger.info(f"Total de registros no período: {total_registros_ncms}")
    
        # NOTA: A API do Comex Stat não funciona como REST API pública simples
        # Ela requer autenticação ou funciona através de scraping/download CSV
        # Por enquanto, vamos apenas usar dados do banco local
        # Se não houver dados no banco, retornar estrutura vazia mas informativa
        
        if not tem_dados_no_banco and ncms_list:
            logger.info("=" * 60)
            logger.info("NENHUM DADO ENCONTRADO NO BANCO LOCAL PARA OS NCMs FILTRADOS")
            logger.info(f"NCMs filtrados: {ncms_list}")
            logger.info(f"Total de registros encontrados: {total_registros_ncms}")
            logger.info("=" * 60)
            logger.warning("⚠️ API externa não disponível como REST API pública")
            logger.info("Para obter dados de outros NCMs, é necessário:")
            logger.info("1. Importar dados via CSV no banco local")
            logger.info("2. Ou usar scraping do portal Comex Stat (requer implementação)")
            logger.info("3. Ou configurar API privada se disponível")
    
    # Principais NCMs
    # Se há filtro de NCM específico, mostrar apenas esses NCMs
    if ncms_list:
        # Quando há filtro de NCM, mostrar apenas os NCMs filtrados
        query_ncms = db.query(
            OperacaoComex.ncm,
            OperacaoComex.descricao_produto,
            func.sum(OperacaoComex.valor_fob).label('total_valor'),
            func.count(OperacaoComex.id).label('total_operacoes')
        ).filter(
            and_(*base_filters)
        )
        
        if tipo_filtro:
            query_ncms = query_ncms.filter(OperacaoComex.tipo_operacao == tipo_filtro)
        
        principais_ncms = query_ncms.group_by(
            OperacaoComex.ncm,
            OperacaoComex.descricao_produto
        ).order_by(
            func.sum(OperacaoComex.valor_fob).desc()
        ).all()  # Remover limit para mostrar todos os NCMs filtrados
        
        logger.info(f"Encontrados {len(principais_ncms)} NCMs com dados")
    else:
        # Sem filtro de NCM, mostrar top 10
        query_ncms = db.query(
            OperacaoComex.ncm,
            OperacaoComex.descricao_produto,
            func.sum(OperacaoComex.valor_fob).label('total_valor'),
            func.count(OperacaoComex.id).label('total_operacoes')
        ).filter(
            and_(*base_filters)
        )
        
        if tipo_filtro:
            query_ncms = query_ncms.filter(OperacaoComex.tipo_operacao == tipo_filtro)
        
        principais_ncms = query_ncms.group_by(
            OperacaoComex.ncm,
            OperacaoComex.descricao_produto
        ).order_by(
            func.sum(OperacaoComex.valor_fob).desc()
        ).limit(10).all()
    
    principais_ncms_list = [
        {
            "ncm": ncm,
            "descricao": desc[:100] if desc else "",
            "valor_total": float(total_valor or 0),
            "total_operacoes": total_operacoes
        }
        for ncm, desc, total_valor, total_operacoes in principais_ncms
    ]
    
    logger.info(f"Principais NCMs retornados: {len(principais_ncms_list)}")
    
    # Principais países
    query_paises = db.query(
        OperacaoComex.pais_origem_destino,
        func.sum(OperacaoComex.valor_fob).label('total_valor'),
        func.count(OperacaoComex.id).label('total_operacoes')
    ).filter(
        and_(*base_filters)
    )
    
    if tipo_filtro:
        query_paises = query_paises.filter(OperacaoComex.tipo_operacao == tipo_filtro)
    
    principais_paises = query_paises.group_by(
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
        and_(*base_filters)
    ).group_by(
        OperacaoComex.mes_referencia
    ).order_by(
        OperacaoComex.mes_referencia
    ).all()
    
    registros_dict = {
        mes: count for mes, count in registros_por_mes
    }
    
    # Principais empresas (importadoras/exportadoras) com NCM
    principais_empresas_list = []
    try:
        # Verificar se a coluna nome_empresa existe
        try:
            db.execute(text("SELECT nome_empresa FROM operacoes_comex LIMIT 1"))
        except Exception as col_error:
            logger.warning(f"Coluna nome_empresa não existe: {col_error}")
            logger.info("Execute ADICIONAR_CAMPO_EMPRESA.bat para adicionar a coluna")
            principais_empresas_list = []
        else:
            # Se há filtro de NCM, mostrar empresas agrupadas por NCM
            # Se não há filtro de NCM, mostrar empresas com seus principais NCMs
            if ncms_list:
                # Agrupar por empresa E NCM quando há filtro de NCM
                query_empresas = db.query(
                    OperacaoComex.nome_empresa,
                    OperacaoComex.ncm,
                    func.sum(OperacaoComex.valor_fob).label('total_valor'),
                    func.sum(OperacaoComex.peso_liquido_kg).label('total_peso'),
                    func.count(OperacaoComex.id).label('total_operacoes')
                ).filter(
                    and_(*base_filters),
                    OperacaoComex.nome_empresa.isnot(None),
                    OperacaoComex.nome_empresa != ''
                )
                
                if tipo_filtro:
                    query_empresas = query_empresas.filter(OperacaoComex.tipo_operacao == tipo_filtro)
                
                principais_empresas = query_empresas.group_by(
                    OperacaoComex.nome_empresa,
                    OperacaoComex.ncm
                ).order_by(
                    func.sum(OperacaoComex.valor_fob).desc()
                ).limit(100).all()  # Aumentar limite
                
                logger.info(f"Encontradas {len(principais_empresas)} empresas com filtro de NCM")
                
                # Log detalhado
                if principais_empresas:
                    logger.info(f"Primeiras 3 empresas: {[(e[0], e[2]) for e in principais_empresas[:3]]}")
                else:
                    # Verificar se há registros mas sem nome_empresa
                    total_sem_empresa = db.query(func.count(OperacaoComex.id)).filter(
                        and_(*base_filters),
                        (OperacaoComex.nome_empresa.is_(None) | (OperacaoComex.nome_empresa == ''))
                    ).scalar() or 0
                    if total_sem_empresa > 0:
                        logger.warning(f"⚠️ {total_sem_empresa} registros sem nome_empresa preenchido")
                
                principais_empresas_list = [
                    {
                        "nome": nome,
                        "ncm": ncm,
                        "valor_total": float(total_valor or 0),
                        "peso_total": float(total_peso or 0),
                        "total_operacoes": total_operacoes
                    }
                    for nome, ncm, total_valor, total_peso, total_operacoes in principais_empresas
                    if nome  # Filtrar apenas empresas com nome
                ]
                
                logger.info(f"Principais empresas retornadas (com nome): {len(principais_empresas_list)}")
                
                # Se não há empresas mas há registros, criar entrada genérica
                if not principais_empresas_list and total_registros_ncms > 0:
                    logger.warning("⚠️ Há registros mas nenhuma empresa com nome. Criando entrada genérica...")
                    # Buscar dados agregados sem nome de empresa
                    dados_agregados = db.query(
                        func.sum(OperacaoComex.valor_fob).label('total_valor'),
                        func.sum(OperacaoComex.peso_liquido_kg).label('total_peso'),
                        func.count(OperacaoComex.id).label('total_operacoes')
                    ).filter(
                        and_(*base_filters)
                    ).first()
                    
                    if dados_agregados and dados_agregados.total_operacoes > 0:
                        principais_empresas_list = [{
                            "nome": "Dados disponíveis (nome da empresa não preenchido)",
                            "ncm": ncms_list[0] if ncms_list else None,
                            "valor_total": float(dados_agregados.total_valor or 0),
                            "peso_total": float(dados_agregados.total_peso or 0),
                            "total_operacoes": dados_agregados.total_operacoes
                        }]
                        logger.info("Entrada genérica criada para mostrar que há dados")
            else:
                # Sem filtro de NCM: agrupar apenas por empresa e incluir principais NCMs
                query_empresas = db.query(
                    OperacaoComex.nome_empresa,
                    func.sum(OperacaoComex.valor_fob).label('total_valor'),
                    func.sum(OperacaoComex.peso_liquido_kg).label('total_peso'),
                    func.count(OperacaoComex.id).label('total_operacoes')
                ).filter(
                    and_(*base_filters),
                    OperacaoComex.nome_empresa.isnot(None),
                    OperacaoComex.nome_empresa != ''
                )
                
                if tipo_filtro:
                    query_empresas = query_empresas.filter(OperacaoComex.tipo_operacao == tipo_filtro)
                
                principais_empresas = query_empresas.group_by(
                    OperacaoComex.nome_empresa
                ).order_by(
                    func.sum(OperacaoComex.valor_fob).desc()
                ).limit(20).all()
                
                # Para cada empresa, buscar seus principais NCMs
                principais_empresas_list = []
                for nome, total_valor, total_peso, total_operacoes in principais_empresas:
                    if nome:
                        # Buscar principais NCMs desta empresa
                        query_ncms_empresa = db.query(
                            OperacaoComex.ncm,
                            func.sum(OperacaoComex.valor_fob).label('valor_ncm')
                        ).filter(
                            and_(*base_filters),
                            OperacaoComex.nome_empresa == nome
                        )
                        
                        if tipo_filtro:
                            query_ncms_empresa = query_ncms_empresa.filter(OperacaoComex.tipo_operacao == tipo_filtro)
                        
                        ncms_empresa = query_ncms_empresa.group_by(
                            OperacaoComex.ncm
                        ).order_by(
                            func.sum(OperacaoComex.valor_fob).desc()
                        ).limit(3).all()
                        
                        # Criar uma entrada para cada NCM principal da empresa
                        if ncms_empresa:
                            for ncm_emp, _ in ncms_empresa:
                                principais_empresas_list.append({
                                    "nome": nome,
                                    "ncm": ncm_emp,
                                    "valor_total": float(total_valor or 0),
                                    "peso_total": float(total_peso or 0),
                                    "total_operacoes": total_operacoes
                                })
                        else:
                            # Se não há NCMs, adicionar sem NCM
                            principais_empresas_list.append({
                                "nome": nome,
                                "ncm": None,
                                "valor_total": float(total_valor or 0),
                                "peso_total": float(total_peso or 0),
                                "total_operacoes": total_operacoes
                            })
    except Exception as e:
        logger.warning(f"Erro ao buscar principais empresas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        principais_empresas_list = []
    
    # Valores FOB por mês (para gráfico de evolução)
    query_valores_mes = db.query(
        OperacaoComex.mes_referencia,
        func.sum(OperacaoComex.valor_fob).label('valor_fob'),
        func.sum(OperacaoComex.peso_liquido_kg).label('peso_kg')
    ).filter(
        and_(*base_filters)
    )
    
    if tipo_filtro:
        query_valores_mes = query_valores_mes.filter(OperacaoComex.tipo_operacao == tipo_filtro)
    
    valores_por_mes = query_valores_mes.group_by(
        OperacaoComex.mes_referencia
    ).order_by(
        OperacaoComex.mes_referencia
    ).all()
    
    valores_por_mes_list = [
        {
            "mes": mes,
            "valor_fob": float(valor_fob or 0),
            "peso_kg": float(peso_kg or 0)
        }
        for mes, valor_fob, peso_kg in valores_por_mes
    ]
    
    logger.info(f"Retornando: {len(principais_ncms_list)} NCMs, {len(principais_paises_list)} países, {len(principais_empresas_list)} empresas")
    
    # Log detalhado sobre empresas
    if principais_empresas_list:
        logger.info(f"Primeiras 3 empresas: {principais_empresas_list[:3]}")
    else:
        logger.warning("Nenhuma empresa encontrada! Verificando possíveis causas...")
        # Verificar se há registros com nome_empresa
        total_com_empresa = db.query(func.count(OperacaoComex.id)).filter(
            and_(*base_filters),
            OperacaoComex.nome_empresa.isnot(None),
            OperacaoComex.nome_empresa != ''
        ).scalar() or 0
        logger.info(f"Total de registros com nome_empresa preenchido: {total_com_empresa}")
        
        # Verificar se há registros sem filtro de empresa
        total_sem_filtro_empresa = db.query(func.count(OperacaoComex.id)).filter(
            and_(*[f for f in base_filters if 'nome_empresa' not in str(f)])
        ).scalar() or 0
        logger.info(f"Total de registros sem filtro de empresa: {total_sem_filtro_empresa}")
    
    logger.info(f"=== Fim Dashboard Stats ===")
    
    return DashboardStats(
        volume_importacoes=float(volume_imp),
        volume_exportacoes=float(volume_exp),
        valor_total_usd=float(valor_total),
        principais_ncms=principais_ncms_list,
        principais_paises=principais_paises_list,
        principais_empresas=principais_empresas_list,
        registros_por_mes=registros_dict,
        valores_por_mes_com_peso=valores_por_mes_list
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
    
    if filtros.empresa:
        conditions.append(OperacaoComex.nome_empresa.ilike(f"%{filtros.empresa}%"))
    
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


@app.get("/ncms/verificar")
async def verificar_ncms(
    ncms: str = Query(..., description="Lista de NCMs separados por vírgula"),
    db: Session = Depends(get_db)
):
    """
    Verifica quais NCMs têm dados disponíveis no banco.
    Retorna informações sobre cada NCM: se tem dados, quantos registros, valor total, etc.
    """
    from sqlalchemy import func
    
    # Separar e limpar NCMs
    ncms_list = [n.strip().replace('.', '').replace(' ', '') for n in ncms.split(',')]
    ncms_list = [n for n in ncms_list if len(n) == 8]
    
    if not ncms_list:
        return {"ncms": []}
    
    resultados = []
    
    for ncm in ncms_list:
        # Contar registros
        total_registros = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.ncm == ncm
        ).scalar() or 0
        
        # Valor total
        valor_total = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            OperacaoComex.ncm == ncm
        ).scalar() or 0.0
        
        # Peso total
        peso_total = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
            OperacaoComex.ncm == ncm
        ).scalar() or 0.0
        
        # Período de dados
        periodo = db.query(
            func.min(OperacaoComex.data_operacao).label('data_inicio'),
            func.max(OperacaoComex.data_operacao).label('data_fim')
        ).filter(
            OperacaoComex.ncm == ncm
        ).first()
        
        # Descrição do produto (primeira encontrada)
        descricao = db.query(OperacaoComex.descricao_produto).filter(
            OperacaoComex.ncm == ncm
        ).first()
        
        resultados.append({
            "ncm": ncm,
            "tem_dados": total_registros > 0,
            "total_registros": total_registros,
            "valor_total": float(valor_total),
            "peso_total": float(peso_total),
            "data_inicio": periodo.data_inicio.isoformat() if periodo and periodo.data_inicio else None,
            "data_fim": periodo.data_fim.isoformat() if periodo and periodo.data_fim else None,
            "descricao": descricao[0] if descricao else None
        })
    
    return {"ncms": resultados}


@app.get("/empresas/autocomplete")
async def autocomplete_empresas(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retorna lista de empresas que correspondem ao termo de busca.
    Usado para autocomplete no campo de empresa.
    """
    from sqlalchemy import func, distinct, text
    
    try:
        # Primeiro verificar se a coluna existe
        try:
            # Tentar fazer uma query simples para verificar se a coluna existe
            db.execute(text("SELECT nome_empresa FROM operacoes_comex LIMIT 1"))
        except Exception as col_error:
            logger.warning(f"Coluna nome_empresa não existe: {col_error}")
            logger.info("Execute ADICIONAR_CAMPO_EMPRESA.bat para adicionar a coluna")
            return {
                "empresas": []
            }
        
        # Se chegou aqui, a coluna existe - fazer a query
        empresas = db.query(
            distinct(OperacaoComex.nome_empresa).label('nome')
        ).filter(
            OperacaoComex.nome_empresa.ilike(f"%{q}%"),
            OperacaoComex.nome_empresa.isnot(None),
            OperacaoComex.nome_empresa != ''
        ).order_by(
            OperacaoComex.nome_empresa
        ).limit(limit).all()
        
        empresas_list = [empresa.nome for empresa in empresas if empresa.nome]
        
        logger.info(f"Autocomplete empresas: encontradas {len(empresas_list)} empresas para '{q}'")
        
        return {
            "empresas": empresas_list
        }
    except Exception as e:
        logger.error(f"Erro no autocomplete de empresas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "empresas": []
        }


# Endpoints de Autenticação
@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Endpoint de login usando email."""
    try:
        logger.info(f"Tentativa de login recebida: {username}")
        logger.info(f"Tamanho da senha recebida: {len(password)} caracteres, {len(password.encode('utf-8'))} bytes")
        
        # TRUNCAR SENHA IMEDIATAMENTE - ANTES DE QUALQUER OPERAÇÃO
        senha_original = password
        senha_bytes_original = senha_original.encode('utf-8')
        tamanho_bytes = len(senha_bytes_original)
        
        logger.info(f"🔍 Senha original: {tamanho_bytes} bytes")
        
        # Truncar para exatamente 72 bytes se necessário
        if tamanho_bytes > 72:
            senha_bytes_truncada = senha_bytes_original[:72]
            senha_final = senha_bytes_truncada.decode('utf-8', errors='ignore')
            logger.warning(f"⚠️ Senha truncada de {tamanho_bytes} para 72 bytes no login")
        else:
            senha_final = senha_original
        
        # VERIFICAÇÃO FINAL antes de usar
        senha_bytes_final = senha_final.encode('utf-8')
        if len(senha_bytes_final) > 72:
            logger.error(f"❌ ERRO CRÍTICO: Senha ainda tem {len(senha_bytes_final)} bytes após truncamento!")
            senha_bytes_final = senha_bytes_final[:72]
            senha_final = senha_bytes_final.decode('utf-8', errors='ignore')
        
        logger.info(f"✅ Senha final para autenticação: {len(senha_final)} caracteres, {len(senha_final.encode('utf-8'))} bytes")
        
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
            # Não falhar o login por causa disso
        
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
        import traceback
        logger.error(traceback.format_exc())
        # Se o erro for sobre 72 bytes, dar mensagem mais clara
        if "72 bytes" in str(e).lower() or "truncate" in str(e).lower():
            raise HTTPException(status_code=500, detail="Erro ao processar senha. Tente uma senha mais curta.")
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
            logger.warning(f"Senha inválida para {cadastro.email}: {mensagem_erro}")
            raise HTTPException(status_code=400, detail=mensagem_erro)
        
        # Verificar se email já existe
        usuario_existente = db.query(Usuario).filter(Usuario.email == cadastro.email).first()
        if usuario_existente:
            logger.warning(f"Email já cadastrado: {cadastro.email}")
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Verificar CPF/CNPJ se fornecido
        if cadastro.cpf:
            cpf_existente = db.query(Usuario).filter(Usuario.cpf == cadastro.cpf).first()
            if cpf_existente:
                logger.warning(f"CPF já cadastrado: {cadastro.cpf}")
                raise HTTPException(status_code=400, detail="CPF já cadastrado")
        
        if cadastro.cnpj:
            cnpj_existente = db.query(Usuario).filter(Usuario.cnpj == cadastro.cnpj).first()
            if cnpj_existente:
                logger.warning(f"CNPJ já cadastrado: {cadastro.cnpj}")
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
        
        # Criar novo usuário (inativo até aprovação)
        novo_usuario = None
        token_aprovacao = None
        try:
            # Senha já foi validada, mas garantir truncamento antes do hash
            senha_para_hash = cadastro.password
            senha_bytes = len(senha_para_hash.encode('utf-8'))
            logger.info(f"Tamanho da senha: {len(senha_para_hash)} caracteres, {senha_bytes} bytes")
            
            # Proteção extra: truncar se exceder 72 bytes
            if senha_bytes > 72:
                senha_bytes_truncated = senha_para_hash.encode('utf-8')[:72]
                senha_para_hash = senha_bytes_truncated.decode('utf-8', errors='ignore')
                logger.warning(f"⚠️ Senha truncada de {senha_bytes} para 72 bytes antes do hash")
            
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
            db.flush()  # Flush para obter o ID sem fazer commit ainda
            
            # Criar token de aprovação
            token_aprovacao = secrets.token_urlsafe(32)
            data_expiracao = datetime.utcnow() + timedelta(days=7)  # Token válido por 7 dias
            
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
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao criar usuário: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")
        
        # Enviar email em background (não bloqueia a resposta)
        background_tasks.add_task(
            enviar_email_aprovacao,
            cadastro.email,
            cadastro.nome_completo,
            token_aprovacao
        )
        
        return {
            "message": "Cadastro realizado com sucesso! Aguarde aprovação por email.",
            "email": cadastro.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro inesperado no cadastro: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        
        # Salvar token no banco (usar campo token_aprovacao temporariamente)
        try:
            usuario.token_aprovacao = token_redefinicao
            db.commit()
            logger.info(f"✅ Token de redefinição salvo para {request.email}")
        except Exception as e:
            logger.error(f"Erro ao salvar token de redefinição: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao processar solicitação: {str(e)}")
        
        # TODO: Enviar email com link de redefinição
        logger.info(f"Token de redefinição gerado para {request.email}: {token_redefinicao}")
        
        return {"message": "Se o email existir, você receberá instruções para redefinir a senha"}
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


async def _processar_dados_api_para_dashboard(
    dados_api: List[Dict[str, Any]],
    ncms_list: List[str],
    tipo_operacao: Optional[str],
    empresa: Optional[str],
    meses: int
) -> DashboardStats:
    """
    Processa dados da API externa e retorna no formato DashboardStats.
    """
    from collections import defaultdict
    
    logger.info(f"Processando {len(dados_api)} registros da API para dashboard")
    
    # Log dos primeiros registros para debug
    if dados_api:
        logger.info(f"Primeiro registro da API: {list(dados_api[0].keys()) if dados_api else 'N/A'}")
        logger.info(f"Exemplo de dados: {str(dados_api[0])[:200] if dados_api else 'N/A'}")
    
    # Filtrar dados conforme critérios
    dados_filtrados = dados_api
    
    # Filtrar apenas pelos NCMs solicitados
    if ncms_list:
        dados_filtrados = [
            d for d in dados_filtrados
            if str(d.get('ncm', '')).replace('.', '').replace(' ', '') in ncms_list
        ]
        logger.info(f"Após filtrar por NCMs {ncms_list}: {len(dados_filtrados)} registros")
    
    # Filtrar por empresa se fornecido
    if empresa:
        dados_filtrados = [
            d for d in dados_filtrados
            if empresa.lower() in str(d.get('nome_empresa', '')).lower()
        ]
    
    # Calcular estatísticas
    valor_total = sum(float(d.get('valor_fob', 0) or 0) for d in dados_filtrados)
    volume_imp = sum(
        float(d.get('peso_liquido_kg', 0) or 0) for d in dados_filtrados
        if d.get('tipo_operacao') == 'Importação'
    )
    volume_exp = sum(
        float(d.get('peso_liquido_kg', 0) or 0) for d in dados_filtrados
        if d.get('tipo_operacao') == 'Exportação'
    )
    
    # Agrupar por NCM
    ncms_dict = defaultdict(lambda: {'valor': 0, 'operacoes': 0, 'descricao': ''})
    for d in dados_filtrados:
        ncm = d.get('ncm', '')
        if ncm:
            ncms_dict[ncm]['valor'] += float(d.get('valor_fob', 0) or 0)
            ncms_dict[ncm]['operacoes'] += 1
            if not ncms_dict[ncm]['descricao']:
                ncms_dict[ncm]['descricao'] = d.get('descricao_produto', '')[:100]
    
    principais_ncms_list = [
        {
            "ncm": ncm,
            "descricao": info['descricao'],
            "valor_total": info['valor'],
            "total_operacoes": info['operacoes']
        }
        for ncm, info in sorted(ncms_dict.items(), key=lambda x: x[1]['valor'], reverse=True)[:10]
    ]
    
    # Agrupar por país
    paises_dict = defaultdict(lambda: {'valor': 0, 'operacoes': 0})
    for d in dados_filtrados:
        pais = d.get('pais_origem_destino', '')
        if pais:
            paises_dict[pais]['valor'] += float(d.get('valor_fob', 0) or 0)
            paises_dict[pais]['operacoes'] += 1
    
    principais_paises_list = [
        {
            "pais": pais,
            "valor_total": info['valor'],
            "total_operacoes": info['operacoes']
        }
        for pais, info in sorted(paises_dict.items(), key=lambda x: x[1]['valor'], reverse=True)[:10]
    ]
    
    # Agrupar por empresa
    empresas_dict = defaultdict(lambda: {'valor': 0, 'peso': 0, 'operacoes': 0, 'ncms': set()})
    for d in dados_filtrados:
        nome_emp = d.get('nome_empresa', '')
        ncm_emp = d.get('ncm', '')
        if nome_emp:
            empresas_dict[nome_emp]['valor'] += float(d.get('valor_fob', 0) or 0)
            empresas_dict[nome_emp]['peso'] += float(d.get('peso_liquido_kg', 0) or 0)
            empresas_dict[nome_emp]['operacoes'] += 1
            if ncm_emp:
                empresas_dict[nome_emp]['ncms'].add(ncm_emp)
    
    principais_empresas_list = []
    for nome, info in sorted(empresas_dict.items(), key=lambda x: x[1]['valor'], reverse=True)[:20]:
        # Pegar primeiro NCM da empresa (ou dos NCMs filtrados)
        ncm_emp = None
        if ncms_list:
            for ncm_filtro in ncms_list:
                if ncm_filtro in info['ncms']:
                    ncm_emp = ncm_filtro
                    break
        if not ncm_emp and info['ncms']:
            ncm_emp = list(info['ncms'])[0]
        
        principais_empresas_list.append({
            "nome": nome,
            "ncm": ncm_emp,
            "valor_total": info['valor'],
            "peso_total": info['peso'],
            "total_operacoes": info['operacoes']
        })
    
    # Agrupar por mês
    meses_dict = defaultdict(lambda: {'registros': 0, 'valor': 0, 'peso': 0})
    for d in dados_filtrados:
        mes_ref = d.get('mes_referencia', '')
        if mes_ref:
            meses_dict[mes_ref]['registros'] += 1
            meses_dict[mes_ref]['valor'] += float(d.get('valor_fob', 0) or 0)
            meses_dict[mes_ref]['peso'] += float(d.get('peso_liquido_kg', 0) or 0)
    
    registros_dict = {mes: info['registros'] for mes, info in meses_dict.items()}
    valores_por_mes_list = [
        {
            "mes": mes,
            "valor_fob": info['valor'],
            "peso_kg": info['peso']
        }
        for mes, info in sorted(meses_dict.items())
    ]
    
    logger.info(f"Dados da API processados: {len(principais_ncms_list)} NCMs, {len(principais_paises_list)} países, {len(principais_empresas_list)} empresas")
    
    return DashboardStats(
        volume_importacoes=float(volume_imp),
        volume_exportacoes=float(volume_exp),
        valor_total_usd=float(valor_total),
        principais_ncms=principais_ncms_list,
        principais_paises=principais_paises_list,
        principais_empresas=principais_empresas_list,
        registros_por_mes=registros_dict,
        valores_por_mes_com_peso=valores_por_mes_list
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

