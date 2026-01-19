"""
Aplicação principal FastAPI.
"""
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from datetime import date, datetime
from threading import Lock
import time
import json
import os
from pydantic import BaseModel
from pathlib import Path
import uvicorn

from loguru import logger

from config import settings
from database import get_db, init_db, SessionLocal
from database.models import (
    OperacaoComex, TipoOperacao, ViaTransporte,
    ComercioExterior, Empresa, CNAEHierarquia, EmpresasRecomendadas
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
    version="1.0.0",
    openapi_tags=[
        {
            "name": "importacao",
            "description": "Endpoints para importação de arquivos Excel e CNAE",
        },
    ]
)

# Configurar CORS para permitir requisições do frontend Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origem do Electron
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importação automática opcional do Excel no startup
def _start_auto_import_excel_if_configured() -> None:
    flag = os.getenv("AUTO_IMPORT_EXCEL_ON_START", "").strip().lower()
    if flag not in {"1", "true", "yes", "y"}:
        return

    filename = os.getenv(
        "AUTO_IMPORT_EXCEL_FILENAME",
        "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx",
    ).strip()
    if not filename:
        logger.warning("AUTO_IMPORT_EXCEL_FILENAME vazio; importação ignorada.")
        return

    base_dir = Path(__file__).parent
    possible_paths = [
        base_dir / "data" / filename,
        base_dir.parent / "comex_data" / "comexstat_csv" / filename,
        Path("/opt/render/project/src/backend/data") / filename,
        Path("/opt/render/project/src/comex_data/comexstat_csv") / filename,
    ]

    source_path = next((p for p in possible_paths if p.exists()), None)
    if not source_path:
        logger.warning(
            "Arquivo para importação automática não encontrado. Procurado em: "
            f"{[str(p) for p in possible_paths]}"
        )
        return

    only_if_empty = os.getenv("AUTO_IMPORT_EXCEL_ONLY_IF_EMPTY", "true").strip().lower()
    only_if_empty = only_if_empty not in {"0", "false", "no", "n"}

    def run_import() -> None:
        db = SessionLocal()
        try:
            total_existente = db.query(OperacaoComex.id).count()
            if only_if_empty and total_existente > 0:
                logger.info(
                    f"Importação automática ignorada: {total_existente} registros já existem."
                )
                return

            clear_by_file = os.getenv("AUTO_IMPORT_EXCEL_CLEAR_BY_FILE", "false").strip().lower()
            clear_by_file = clear_by_file in {"1", "true", "yes", "y"}
            if clear_by_file:
                removidos = (
                    db.query(OperacaoComex)
                    .filter(OperacaoComex.arquivo_origem == source_path.name)
                    .delete(synchronize_session=False)
                )
                db.commit()
                logger.info(f"Registros removidos para reimportação: {removidos}")
        except Exception as e:
            logger.warning(f"Falha ao verificar registros existentes: {e}")
            db.rollback()
        finally:
            db.close()

        import tempfile
        import shutil

        fd, tmp_path = tempfile.mkstemp(suffix=source_path.suffix)
        os.close(fd)
        shutil.copy2(source_path, tmp_path)
        logger.info(f"Iniciando importação automática do arquivo {source_path.name}...")
        processar_excel_comex_task(tmp_path, source_path.name)

    import threading

    threading.Thread(target=run_import, daemon=True).start()

# Incluir routers
if EXPORT_ROUTER_AVAILABLE:
    app.include_router(export_router)

# Router de análise de empresas
try:
    from api.analise_empresas import router as analise_router
    app.include_router(analise_router)
    logger.info("✅ Router de análise de empresas incluído")
except ImportError as e:
    logger.warning(f"Router de análise de empresas não disponível: {e}")

# Router de coleta da Base dos Dados
try:
    from api.coletar_base_dados import router as coletar_router
    app.include_router(coletar_router)
    logger.info("✅ Router de coleta Base dos Dados incluído")
except ImportError as e:
    logger.warning(f"Router de coleta Base dos Dados não disponível: {e}")


# Inicializar banco de dados na startup
@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados na startup."""
    try:
        # Executar migrations do Alembic antes de inicializar
        import subprocess
        import sys
        logger.info("🔄 Executando migrations do Alembic...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("✅ Migrations executadas com sucesso")
            else:
                logger.warning(f"⚠️ Migration retornou código {result.returncode}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Migration timeout, continuando...")
        except Exception as migration_error:
            logger.warning(f"⚠️ Erro ao executar migrations: {migration_error}, continuando...")
        
        # Inicializar banco (cria tabelas se não existirem)
        init_db()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        # Não interrompe a aplicação, mas loga o erro

    _start_auto_import_excel_if_configured()
    
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
    quantidade_estatistica_importacoes: Optional[float] = None
    quantidade_estatistica_exportacoes: Optional[float] = None
    quantidade_estatistica_total: Optional[float] = None
    principais_ncms: List[dict]
    principais_paises: List[dict]
    registros_por_mes: dict
    valores_por_mes: Optional[dict] = None  # Valores FOB por mês
    pesos_por_mes: Optional[dict] = None  # Pesos por mês


# Cache simples em memória para aliviar o /dashboard/stats
_DASHBOARD_CACHE = {}
_DASHBOARD_CACHE_LOCK = Lock()
_DASHBOARD_CACHE_TTL_SECONDS = 300


def _make_dashboard_cache_key(
    meses: int,
    tipo_operacao: Optional[str],
    ncm: Optional[str],
    ncms: Optional[List[str]],
    empresa_importadora: Optional[str],
    empresa_exportadora: Optional[str],
) -> str:
    ncms_key = ",".join(sorted(ncms)) if ncms else ""
    parts = [
        f"meses={meses}",
        f"tipo={tipo_operacao or ''}",
        f"ncm={ncm or ''}",
        f"ncms={ncms_key}",
        f"imp={empresa_importadora or ''}",
        f"exp={empresa_exportadora or ''}",
    ]
    return "|".join(parts)


def _get_cached_dashboard_stats(cache_key: str) -> Optional[dict]:
    now = time.time()
    with _DASHBOARD_CACHE_LOCK:
        cached = _DASHBOARD_CACHE.get(cache_key)
        if not cached:
            return None
        expires_at, payload = cached
        if expires_at <= now:
            _DASHBOARD_CACHE.pop(cache_key, None)
            return None
        return payload


def _set_cached_dashboard_stats(cache_key: str, payload: dict) -> None:
    expires_at = time.time() + _DASHBOARD_CACHE_TTL_SECONDS
    with _DASHBOARD_CACHE_LOCK:
        _DASHBOARD_CACHE[cache_key] = (expires_at, payload)


_BIGQUERY_COMEX_TABLE = os.getenv(
    "BIGQUERY_COMEX_TABLE",
    "liquid-receiver-483923-n6.Projeto_Comex.Comex",
)


def _get_bigquery_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except ImportError:
        return None

    creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_env and creds_env.strip().startswith("{"):
        try:
            creds_dict = json.loads(creds_env)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            project_id = creds_dict.get("project_id")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception:
            return bigquery.Client()

    return bigquery.Client()


def _buscar_empresas_bigquery(q: str, tipo: Optional[str], limit: int) -> List[dict]:
    if not q or limit <= 0:
        return []

    client = _get_bigquery_client()
    if not client:
        return []

    tipo_filter = None
    if tipo:
        tipo_lower = tipo.lower()
        if "import" in tipo_lower:
            tipo_filter = "%import%"
        elif "export" in tipo_lower:
            tipo_filter = "%export%"

    where_clauses = [
        "razao_social IS NOT NULL",
        "LOWER(razao_social) LIKE CONCAT('%', @q, '%')",
    ]
    if tipo_filter:
        where_clauses.append("LOWER(id_exportacao_importacao) LIKE @tipo_filter")

    query = f"""
        SELECT razao_social, sigla_uf, id_exportacao_importacao
        FROM `{_BIGQUERY_COMEX_TABLE}`
        WHERE {" AND ".join(where_clauses)}
        LIMIT @limit
    """

    try:
        from google.cloud import bigquery

        query_params = [
            bigquery.ScalarQueryParameter("q", "STRING", q),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        if tipo_filter:
            query_params.append(
                bigquery.ScalarQueryParameter("tipo_filter", "STRING", tipo_filter)
            )

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        rows = query_job.result()
    except Exception:
        return []

    resultados = []
    for row in rows:
        resultados.append({
            "nome": row.get("razao_social"),
            "total_operacoes": 0,
            "valor_total": 0.0,
            "fonte": "bigquery",
            "uf": row.get("sigla_uf"),
            "tipo_operacao": row.get("id_exportacao_importacao"),
        })

    return resultados


def _buscar_empresas_bigquery_sugestoes(
    uf: Optional[str],
    tipo: Optional[str],
    limit: int,
) -> List[dict]:
    if limit <= 0:
        return []

    client = _get_bigquery_client()
    if not client:
        return []

    tipo_filter = None
    if tipo:
        tipo_lower = tipo.lower()
        if "import" in tipo_lower:
            tipo_filter = "%import%"
        elif "export" in tipo_lower:
            tipo_filter = "%export%"

    where_clauses = ["razao_social IS NOT NULL"]
    if uf:
        where_clauses.append("sigla_uf = @uf")
    if tipo_filter:
        where_clauses.append("LOWER(id_exportacao_importacao) LIKE @tipo_filter")

    query = f"""
        SELECT razao_social, sigla_uf, id_exportacao_importacao
        FROM `{_BIGQUERY_COMEX_TABLE}`
        WHERE {" AND ".join(where_clauses)}
        LIMIT @limit
    """

    try:
        from google.cloud import bigquery

        query_params = [
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        if uf:
            query_params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf))
        if tipo_filter:
            query_params.append(
                bigquery.ScalarQueryParameter("tipo_filter", "STRING", tipo_filter)
            )

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        query_job = client.query(query, job_config=job_config)
        rows = query_job.result()
    except Exception:
        return []

    resultados = []
    for row in rows:
        resultados.append({
            "nome": row.get("razao_social"),
            "valor_total": 0.0,
            "peso": 0.0,
            "tipo_operacao": row.get("id_exportacao_importacao"),
            "uf": row.get("sigla_uf"),
            "fonte": "bigquery",
        })

    return resultados


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
    page_size: int = 50


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


@app.get("/validar-sistema")
async def validar_sistema_completo(db: Session = Depends(get_db)):
    """
    Validação completa do sistema.
    Verifica:
    - Conexão com BigQuery
    - Dados no banco de dados PostgreSQL
    - Arquivos CSV disponíveis
    - Relacionamentos entre bases
    """
    from sqlalchemy import func
    from database.models import (
        OperacaoComex, Empresa, EmpresasRecomendadas,
        ComercioExterior, CNAEHierarquia
    )
    from pathlib import Path
    import os
    import json
    
    resultados = {
        "data_validacao": datetime.now().isoformat(),
        "bigquery": {},
        "banco_dados": {},
        "arquivos_csv": {},
        "relacionamentos": {},
        "resumo": {}
    }
    
    try:
        # 1. Validar BigQuery
        logger.info("🔍 Validando BigQuery...")
        bigquery_result = {"conectado": False, "credenciais_configuradas": False, "teste_query": False, "erro": None}
        
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if creds_env:
            bigquery_result["credenciais_configuradas"] = True
            if creds_env.startswith('{'):
                try:
                    json.loads(creds_env)
                    bigquery_result["credenciais_validas"] = True
                except:
                    bigquery_result["credenciais_validas"] = False
        
        try:
            from google.cloud import bigquery
            if creds_env and creds_env.startswith('{'):
                try:
                    creds_dict = json.loads(creds_env)
                    from google.oauth2 import service_account
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    client = bigquery.Client(credentials=credentials)
                except:
                    client = bigquery.Client()
            else:
                client = bigquery.Client()
            
            bigquery_result["conectado"] = True
            query_job = client.query("SELECT 1 as test")
            query_job.result()
            bigquery_result["teste_query"] = True
        except ImportError:
            bigquery_result["erro"] = "Biblioteca google-cloud-bigquery não instalada"
        except Exception as e:
            bigquery_result["erro"] = str(e)
        
        resultados["bigquery"] = bigquery_result
        
        # 2. Validar Banco de Dados
        logger.info("🔍 Validando banco de dados...")
        banco_result = {"conectado": False, "tabelas": {}, "total_registros": {}}
        
        try:
            db.execute(text("SELECT 1"))
            banco_result["conectado"] = True
            
            tabelas_verificar = [
                ("operacoes_comex", OperacaoComex),
                ("empresas", Empresa),
                ("empresas_recomendadas", EmpresasRecomendadas),
                ("comercio_exterior", ComercioExterior),
                ("cnae_hierarquia", CNAEHierarquia)
            ]
            
            for nome_tabela, modelo in tabelas_verificar:
                try:
                    count = db.query(func.count(modelo.id)).scalar()
                    banco_result["tabelas"][nome_tabela] = {"existe": True, "total_registros": count}
                    banco_result["total_registros"][nome_tabela] = count
                except Exception as e:
                    banco_result["tabelas"][nome_tabela] = {"existe": False, "erro": str(e)}
            
            # Detalhes de operacoes_comex
            if banco_result["total_registros"].get("operacoes_comex", 0) > 0:
                importacao = db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == "Importação"
                ).scalar()
                exportacao = db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == "Exportação"
                ).scalar()
                
                banco_result["operacoes_detalhes"] = {
                    "importacao": importacao,
                    "exportacao": exportacao
                }
                
                cnpjs_importadores = db.query(func.count(func.distinct(OperacaoComex.cnpj_importador))).scalar()
                cnpjs_exportadores = db.query(func.count(func.distinct(OperacaoComex.cnpj_exportador))).scalar()
                
                banco_result["cnpjs_unicos"] = {
                    "importadores": cnpjs_importadores,
                    "exportadores": cnpjs_exportadores
                }
        except Exception as e:
            banco_result["erro"] = str(e)
        
        resultados["banco_dados"] = banco_result
        
        # 3. Validar Arquivos CSV
        logger.info("🔍 Validando arquivos CSV...")
        csv_result = {"diretorio_existe": False, "arquivos_encontrados": [], "total_arquivos": 0}
        
        try:
            base_dir = Path(__file__).parent.parent
            csv_dir = base_dir / "comex_data" / "comexstat_csv"
            csv_downloads_dir = base_dir / "comex_data" / "csv_downloads"
            
            if csv_dir.exists():
                csv_result["diretorio_existe"] = True
                arquivos_csv = list(csv_dir.glob("*.csv")) + list(csv_dir.glob("*.xlsx"))
                csv_result["total_arquivos"] = len(arquivos_csv)
                
                for arquivo in arquivos_csv[:10]:  # Limitar a 10 para não sobrecarregar resposta
                    tamanho = arquivo.stat().st_size
                    csv_result["arquivos_encontrados"].append({
                        "nome": arquivo.name,
                        "tamanho": tamanho
                    })
            
            if csv_downloads_dir.exists():
                arquivos_downloads = list(csv_downloads_dir.glob("*.csv"))
                importacoes = [f for f in arquivos_downloads if "importacao" in f.name]
                exportacoes = [f for f in arquivos_downloads if "exportacao" in f.name]
                
                csv_result["csv_downloads"] = {
                    "total": len(arquivos_downloads),
                    "importacoes": len(importacoes),
                    "exportacoes": len(exportacoes)
                }
        except Exception as e:
            csv_result["erro"] = str(e)
        
        resultados["arquivos_csv"] = csv_result
        
        # 4. Validar Relacionamentos
        logger.info("🔍 Validando relacionamentos...")
        rel_result = {"empresas_recomendadas": {}, "relacionamento_operacoes_empresas": {}}
        
        try:
            total_recomendadas = db.query(func.count(EmpresasRecomendadas.id)).scalar()
            rel_result["empresas_recomendadas"]["total"] = total_recomendadas
            
            if total_recomendadas > 0:
                importadoras = db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.tipo_principal == "importadora"
                ).scalar()
                exportadoras = db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.tipo_principal == "exportadora"
                ).scalar()
                
                rel_result["empresas_recomendadas"]["importadoras"] = importadoras
                rel_result["empresas_recomendadas"]["exportadoras"] = exportadoras
                
                com_cnpj = db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.cnpj.isnot(None)
                ).scalar()
                rel_result["empresas_recomendadas"]["com_cnpj"] = com_cnpj
            
            # Relacionamento operacoes_comex ↔ empresas
            cnpjs_operacoes = db.query(func.distinct(OperacaoComex.cnpj_importador)).filter(
                OperacaoComex.cnpj_importador.isnot(None)
            ).all()
            cnpjs_operacoes = [c[0] for c in cnpjs_operacoes if c[0]]
            
            cnpjs_empresas = db.query(func.distinct(Empresa.cnpj)).filter(
                Empresa.cnpj.isnot(None)
            ).all()
            cnpjs_empresas = [c[0] for c in cnpjs_empresas if c[0]]
            
            cnpjs_relacionados = len(set(cnpjs_operacoes) & set(cnpjs_empresas))
            
            rel_result["relacionamento_operacoes_empresas"] = {
                "cnpjs_operacoes": len(cnpjs_operacoes),
                "cnpjs_empresas": len(cnpjs_empresas),
                "cnpjs_relacionados": cnpjs_relacionados,
                "percentual_relacionado": round((cnpjs_relacionados / len(cnpjs_operacoes) * 100) if cnpjs_operacoes else 0, 2)
            }
        except Exception as e:
            rel_result["erro"] = str(e)
        
        resultados["relacionamentos"] = rel_result
        
        # 5. Gerar Resumo
        resumo = {
            "status_geral": "OK",
            "problemas": [],
            "recomendacoes": []
        }
        
        if not bigquery_result.get("conectado"):
            resumo["status_geral"] = "ATENÇÃO"
            resumo["problemas"].append("BigQuery não conectado")
            resumo["recomendacoes"].append("Configure GOOGLE_APPLICATION_CREDENTIALS_JSON no Render")
        
        if banco_result["total_registros"].get("operacoes_comex", 0) == 0:
            resumo["status_geral"] = "ATENÇÃO"
            resumo["problemas"].append("Tabela operacoes_comex está vazia")
            resumo["recomendacoes"].append("Execute coleta de dados do Comex Stat")
        
        if banco_result["total_registros"].get("empresas", 0) == 0:
            resumo["problemas"].append("Tabela empresas está vazia")
            resumo["recomendacoes"].append("Execute coleta de dados do BigQuery (Base dos Dados)")
        
        if rel_result["empresas_recomendadas"].get("total", 0) == 0:
            resumo["problemas"].append("Tabela empresas_recomendadas está vazia")
            resumo["recomendacoes"].append("Execute script de análise de sinergias")
        
        if rel_result["relacionamento_operacoes_empresas"].get("cnpjs_relacionados", 0) == 0:
            resumo["problemas"].append("Nenhum relacionamento entre operacoes_comex e empresas")
            resumo["recomendacoes"].append("Execute script de análise de sinergias para criar relacionamentos")
        
        resultados["resumo"] = resumo
        
        return resultados
        
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")


@app.post("/coletar-dados")
async def coletar_dados(db: Session = Depends(get_db)):
    """
    Inicia coleta de dados do Comex Stat.
    Tenta múltiplos métodos: API → CSV Scraper → Scraper tradicional
    """
    try:
        collector = DataCollector()
        stats = await collector.collect_recent_data(db)
        
        # Se não coletou nada, tentar CSV scraper diretamente
        if stats.get("total_registros", 0) == 0:
            logger.warning("⚠️ Coleta inicial retornou 0 registros. Tentando CSV scraper diretamente...")
            try:
                from data_collector.csv_scraper import CSVDataScraper
                csv_scraper = CSVDataScraper()
                
                # Baixar últimos 12 meses
                logger.info("📥 Baixando arquivos CSV do MDIC...")
                downloaded_files = await csv_scraper.download_recent_months(meses=12)
                
                if downloaded_files:
                    logger.info(f"✅ {len(downloaded_files)} arquivos baixados. Processando...")
                    from data_collector.transformer import DataTransformer
                    transformer = DataTransformer()
                    
                    total_saved = 0
                    for filepath in downloaded_files:
                        try:
                            # Parse CSV
                            raw_data = csv_scraper.parse_csv_file(filepath)
                            if not raw_data:
                                continue
                            
                            # Extrair mês e tipo do nome do arquivo
                            nome = filepath.stem
                            if "importacao" in nome.lower():
                                tipo = "Importação"
                            elif "exportacao" in nome.lower():
                                tipo = "Exportação"
                            else:
                                continue
                            
                            # Extrair mês (formato: tipo_YYYY_MM)
                            partes = nome.split('_')
                            if len(partes) >= 3:
                                ano = partes[-2]
                                mes = partes[-1]
                                mes_str = f"{ano}-{mes}"
                            else:
                                mes_str = datetime.now().strftime("%Y-%m")
                            
                            # Transformar dados
                            transformed = transformer.transform_csv_data(raw_data, mes_str, tipo)
                            
                            # Salvar no banco
                            saved = collector._save_to_database(db, transformed, mes_str, tipo)
                            total_saved += saved
                            
                            if mes_str not in stats["meses_processados"]:
                                stats["meses_processados"].append(mes_str)
                                
                        except Exception as e:
                            logger.error(f"Erro ao processar {filepath.name}: {e}")
                            stats["erros"].append(f"Erro ao processar {filepath.name}: {str(e)}")
                    
                    stats["total_registros"] = total_saved
                    logger.info(f"✅ CSV scraper salvou {total_saved} registros")
                else:
                    logger.warning("⚠️ Nenhum arquivo CSV foi baixado")
                    stats["erros"].append("CSV scraper não conseguiu baixar arquivos")
                    
            except Exception as e:
                logger.error(f"Erro no CSV scraper direto: {e}")
                stats["erros"].append(f"CSV scraper direto: {str(e)}")
        
        return {
            "success": True,
            "message": "Coleta de dados concluída",
            "stats": stats,
            "recomendacao": "Se total_registros = 0, tente usar POST /coletar-dados-enriquecidos" if stats.get("total_registros", 0) == 0 else None
        }
    except Exception as e:
        logger.error(f"Erro ao coletar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao coletar dados: {str(e)}")


# ============================================================================
# FUNÇÕES DE PROCESSAMENTO EM BACKGROUND
# ============================================================================

def processar_excel_comex_task(caminho_temp: str, nome_original: str):
    """
    Processa arquivo Excel de Comex em background.
    Usa sessão própria e garante limpeza de recursos.
    """
    import os
    db = SessionLocal()
    
    try:
        logger.info(f"🔄 Iniciando processamento de: {nome_original}")
        import pandas as pd
        from datetime import date
        import re
        from database.models import OperacaoComex, TipoOperacao, ViaTransporte
        
        df = pd.read_excel(caminho_temp)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas")
        
        # Detectar ano pelo nome do arquivo
        ano_match = re.search(r'20\d{2}', nome_original)
        ano = int(ano_match.group()) if ano_match else date.today().year
        
        operacoes_para_inserir = []
        
        meses_map = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        stats = {
            "total_registros": 0,
            "importacoes": 0,
            "exportacoes": 0,
            "erros": 0
        }
        
        # Processar linhas
        for idx, row in df.iterrows():
            try:
                # Extrair NCM
                ncm = str(row.get('Código NCM', '')).strip() if pd.notna(row.get('Código NCM')) else None
                if not ncm or len(ncm) < 4:
                    continue
                
                ncm_normalizado = ncm[:8] if len(ncm) >= 8 else ncm.zfill(8)
                descricao = str(row.get('Descrição NCM', '')).strip()[:500] if pd.notna(row.get('Descrição NCM')) else ''
                uf = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
                pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
                
                # Processar mês
                mes_str = str(row.get('Mês', '')).strip() if pd.notna(row.get('Mês')) else ''
                mes = None
                
                if mes_str:
                    match = re.search(r'(\d{1,2})', mes_str)
                    if match:
                        mes = int(match.group(1))
                    else:
                        for nome, num in meses_map.items():
                            if nome in mes_str.lower():
                                mes = num
                                break
                
                if not mes or mes < 1 or mes > 12:
                    mes = 1
                
                data_operacao = date(ano, mes, 1)
                mes_referencia = f"{ano}-{mes:02d}"
                
                # Processar EXPORTAÇÃO
                def _parse_number(value) -> float:
                    if pd.isna(value):
                        return 0.0
                    if isinstance(value, (int, float)):
                        return float(value)
                    text = str(value).strip()
                    if not text:
                        return 0.0
                    if "," in text and "." in text:
                        text = text.replace(".", "").replace(",", ".")
                    elif "," in text:
                        text = text.replace(",", ".")
                    try:
                        return float(text)
                    except ValueError:
                        return 0.0

                valor_exp = _parse_number(
                    row.get('Exportação - 2025 - Valor US$ FOB', 0) or
                    row.get('Exportação - Valor US$ FOB', 0) or
                    row.get('Valor Exportação', 0)
                )
                peso_exp = _parse_number(
                    row.get('Exportação - 2025 - Quilograma Líquido', 0) or
                    row.get('Exportação - Quilograma Líquido', 0) or
                    row.get('Peso Exportação', 0)
                )
                quantidade_exp = _parse_number(
                    row.get('Exportação - 2025 - Quantidade Estatística', 0) or
                    row.get('Exportação - Quantidade Estatística', 0) or
                    row.get('Quantidade Exportação', 0)
                )
                
                if valor_exp > 0:
                    operacoes_para_inserir.append({
                        'ncm': ncm_normalizado,
                        'descricao_produto': descricao,
                        'tipo_operacao': TipoOperacao.EXPORTACAO,
                        'via_transporte': ViaTransporte.OUTRAS,
                        'uf': uf,
                        'pais_origem_destino': pais,
                        'valor_fob': float(valor_exp),
                        'peso_liquido_kg': float(peso_exp),
                        'quantidade_estatistica': float(quantidade_exp),
                        'data_operacao': data_operacao,
                        'mes_referencia': mes_referencia,
                        'arquivo_origem': nome_original
                    })
                    stats["exportacoes"] += 1
                    stats["total_registros"] += 1
                
                # Processar IMPORTAÇÃO
                valor_imp = _parse_number(
                    row.get('Importação - 2025 - Valor US$ FOB', 0) or
                    row.get('Importação - Valor US$ FOB', 0) or
                    row.get('Valor Importação', 0)
                )
                peso_imp = _parse_number(
                    row.get('Importação - 2025 - Quilograma Líquido', 0) or
                    row.get('Importação - Quilograma Líquido', 0) or
                    row.get('Peso Importação', 0)
                )
                quantidade_imp = _parse_number(
                    row.get('Importação - 2025 - Quantidade Estatística', 0) or
                    row.get('Importação - Quantidade Estatística', 0) or
                    row.get('Quantidade Importação', 0)
                )
                
                if valor_imp > 0:
                    operacoes_para_inserir.append({
                        'ncm': ncm_normalizado,
                        'descricao_produto': descricao,
                        'tipo_operacao': TipoOperacao.IMPORTACAO,
                        'via_transporte': ViaTransporte.OUTRAS,
                        'uf': uf,
                        'pais_origem_destino': pais,
                        'valor_fob': float(valor_imp),
                        'peso_liquido_kg': float(peso_imp),
                        'quantidade_estatistica': float(quantidade_imp),
                        'data_operacao': data_operacao,
                        'mes_referencia': mes_referencia,
                        'arquivo_origem': nome_original
                    })
                    stats["importacoes"] += 1
                    stats["total_registros"] += 1
            
            except Exception as e:
                logger.warning(f"Erro na linha {idx}: {e}")
                stats["erros"] += 1
                continue
        
        # Bulk Insert em chunks de 1000
        logger.info(f"💾 Inserindo {len(operacoes_para_inserir)} operações no banco...")
        
        for i in range(0, len(operacoes_para_inserir), 1000):
            chunk = operacoes_para_inserir[i:i + 1000]
            
            try:
                db.bulk_insert_mappings(OperacaoComex, chunk)
                db.commit()
                logger.info(f"  ✅ Inseridos {min(i + 1000, len(operacoes_para_inserir))}/{len(operacoes_para_inserir)} registros")
            
            except SQLAlchemyError as e:
                logger.error(f"❌ Erro no chunk {i}-{i+1000}: {e}")
                db.rollback()
                
                # Tentar inserir um por um apenas se o chunk falhar
                for item in chunk:
                    try:
                        db.bulk_insert_mappings(OperacaoComex, [item])
                        db.commit()
                    except Exception as e2:
                        logger.error(f"Registro inválido: {item.get('ncm', 'N/A')} - {e2}")
                        db.rollback()
        
        logger.success(f"✅ Importação concluída: {stats['total_registros']} registros ({stats['importacoes']} importações, {stats['exportacoes']} exportações, {stats['erros']} erros)")
    
    except Exception as e:
        logger.error(f"❌ Falha crítica no processamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    
    finally:
        db.close()
        # Remover arquivo temporário
        if os.path.exists(caminho_temp):
            try:
                os.unlink(caminho_temp)
                logger.info(f"🗑️ Arquivo temporário removido: {caminho_temp}")
            except:
                pass


def processar_cnae_task(caminho_temp: str, nome_original: str):
    """
    Processa arquivo CNAE em background.
    """
    import os
    db = SessionLocal()
    
    try:
        logger.info(f"🔄 Iniciando processamento CNAE: {nome_original}")
        import pandas as pd
        from database.models import CNAEHierarquia
        
        df = pd.read_excel(caminho_temp)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas")
        
        stats = {
            "total_registros": 0,
            "inseridos": 0,
            "atualizados": 0,
            "erros": 0
        }
        
        # Buscar CNAEs existentes
        logger.info("🔍 Verificando CNAEs existentes...")
        existentes_db = db.query(CNAEHierarquia.cnae).all()
        cnae_existentes = {row[0] for row in existentes_db}
        logger.info(f"  Encontrados {len(cnae_existentes)} CNAEs existentes")
        
        cnae_para_inserir = []
        
        for idx, row in df.iterrows():
            try:
                # Extrair CNAE
                cnae = (
                    str(row.get('CNAE', '')) or
                    str(row.get('Código CNAE', '')) or
                    str(row.get('CNAE 2.0', '')) or
                    str(row.get('Subclasse', ''))
                ).strip()
                
                if not cnae or cnae == 'nan' or len(cnae) < 4:
                    continue
                
                cnae_limpo = cnae.replace('.', '').replace('-', '').strip()
                
                descricao = (
                    str(row.get('Descrição', '')) or
                    str(row.get('Descrição Subclasse', '')) or
                    str(row.get('Descrição CNAE', ''))
                ).strip()[:500]
                
                classe = str(row.get('Classe', '')).strip()[:10] if pd.notna(row.get('Classe')) else None
                grupo = str(row.get('Grupo', '')).strip()[:10] if pd.notna(row.get('Grupo')) else None
                divisao = str(row.get('Divisão', '')).strip()[:10] if pd.notna(row.get('Divisão')) else None
                secao = str(row.get('Seção', '')).strip()[:10] if pd.notna(row.get('Seção')) else None
                
                # Verificar se existe
                if cnae_limpo in cnae_existentes:
                    stats["atualizados"] += 1
                    existente = db.query(CNAEHierarquia).filter(
                        CNAEHierarquia.cnae == cnae_limpo
                    ).first()
                    
                    if existente:
                        if descricao:
                            existente.descricao = descricao
                        if classe:
                            existente.classe = classe
                        if grupo:
                            existente.grupo = grupo
                        if divisao:
                            existente.divisao = divisao
                        if secao:
                            existente.secao = secao
                else:
                    cnae_para_inserir.append({
                        'cnae': cnae_limpo,
                        'descricao': descricao,
                        'classe': classe,
                        'grupo': grupo,
                        'divisao': divisao,
                        'secao': secao
                    })
                    cnae_existentes.add(cnae_limpo)
                    stats["inseridos"] += 1
                
                stats["total_registros"] += 1
            
            except Exception as e:
                logger.warning(f"Erro na linha {idx}: {e}")
                stats["erros"] += 1
                continue
        
        # Commit atualizações
        if stats["atualizados"] > 0:
            try:
                db.commit()
                logger.info(f"✅ {stats['atualizados']} registros atualizados")
            except SQLAlchemyError as e:
                logger.error(f"Erro ao commitar atualizações: {e}")
                db.rollback()
        
        # Bulk insert novos
        if cnae_para_inserir:
            logger.info(f"💾 Inserindo {len(cnae_para_inserir)} novos CNAEs...")
            
            for i in range(0, len(cnae_para_inserir), 1000):
                chunk = cnae_para_inserir[i:i + 1000]
                try:
                    db.bulk_insert_mappings(CNAEHierarquia, chunk)
                    db.commit()
                    logger.info(f"  ✅ Inseridos {min(i + 1000, len(cnae_para_inserir))}/{len(cnae_para_inserir)} registros")
                except SQLAlchemyError as e:
                    logger.error(f"Erro ao inserir chunk: {e}")
                    db.rollback()
        
        logger.success(f"✅ Importação CNAE concluída: {stats['inseridos']} inseridos, {stats['atualizados']} atualizados, {stats['erros']} erros")
    
    except Exception as e:
        logger.error(f"❌ Falha crítica no processamento CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    
    finally:
        db.close()
        if os.path.exists(caminho_temp):
            try:
                os.unlink(caminho_temp)
                logger.info(f"🗑️ Arquivo temporário removido")
            except:
                pass


@app.post("/upload-e-importar-excel", tags=["importacao"])
async def upload_e_importar_excel(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(..., description="Arquivo Excel (.xlsx ou .xls) para importar")
):
    """
    Faz upload de um arquivo Excel e importa automaticamente para o banco de dados.
    OTIMIZADO: Usa BackgroundTasks do FastAPI para processamento assíncrono seguro.
    """
    import tempfile
    import os
    
    # Validar extensão
    if not (arquivo.filename.endswith('.xlsx') or arquivo.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    logger.info(f"📤 Recebendo upload do arquivo: {arquivo.filename}")
    
    # Criar arquivo temporário de forma segura
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    
    try:
        with os.fdopen(fd, 'wb') as tmp:
            conteudo = await arquivo.read()
            tmp.write(conteudo)
        
        logger.info(f"✅ Arquivo salvo temporariamente: {path}")
        
        # Adicionar à fila de tarefas do FastAPI
        background_tasks.add_task(processar_excel_comex_task, path, arquivo.filename)
        
        return {
            "success": True,
            "message": "Upload recebido. Processamento iniciado em background.",
            "arquivo": arquivo.filename,
            "status": "processando",
            "instrucoes": "Verifique os logs do Render para acompanhar o progresso."
        }
    
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        # Limpar arquivo se houver erro
        try:
            os.unlink(path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@app.post("/importar-excel-automatico")
async def importar_excel_automatico(
    db: Session = Depends(get_db)
):
    """
    Importa automaticamente todos os arquivos Excel encontrados na pasta comex_data/comexstat_csv.
    
    Procura por arquivos .xlsx e .xls e importa todos encontrados.
    """
    try:
        from pathlib import Path
        import pandas as pd
        from datetime import date
        from database.models import OperacaoComex, TipoOperacao, ViaTransporte
        
        logger.info("Iniciando importação automática de arquivos Excel...")
        
        # Procurar arquivos em múltiplos locais
        base_dir = Path(__file__).parent.parent
        diretorios_procurar = [
            base_dir / "comex_data" / "comexstat_csv",
            Path("/opt/render/project/src/comex_data/comexstat_csv"),
        ]
        
        arquivos_encontrados = []
        for diretorio in diretorios_procurar:
            if diretorio.exists():
                # Procurar arquivos Excel
                arquivos_xlsx = list(diretorio.glob("*.xlsx"))
                arquivos_xls = list(diretorio.glob("*.xls"))
                arquivos_encontrados.extend(arquivos_xlsx + arquivos_xls)
                logger.info(f"Encontrados {len(arquivos_xlsx + arquivos_xls)} arquivos em {diretorio}")
        
        # Filtrar apenas arquivos de dados (não arquivos temporários ou outros)
        arquivos_validos = []
        for arquivo in arquivos_encontrados:
            nome = arquivo.name.lower()
            # Ignorar arquivos temporários e outros
            if nome.startswith('~$') or nome.startswith('.~'):
                continue
            # Incluir arquivos que parecem ser de dados
            if 'exportacao' in nome or 'importacao' in nome or 'comex' in nome or 'geral' in nome:
                arquivos_validos.append(arquivo)
        
        if not arquivos_validos:
            logger.warning("⚠️ Nenhum arquivo Excel válido encontrado")
            return {
                "success": False,
                "message": "Nenhum arquivo Excel válido encontrado",
                "diretorios_procurados": [str(d) for d in diretorios_procurar],
                "arquivos_encontrados": 0
            }
        
        logger.info(f"✅ {len(arquivos_validos)} arquivo(s) válido(s) encontrado(s)")
        
        stats_geral = {
            "total_arquivos": len(arquivos_validos),
            "arquivos_processados": 0,
            "arquivos_com_erro": 0,
            "total_registros": 0,
            "importacoes": 0,
            "exportacoes": 0,
            "erros": [],
            "detalhes_por_arquivo": []
        }
        
        # Processar cada arquivo
        for arquivo_excel in arquivos_validos:
            try:
                logger.info(f"📄 Processando arquivo: {arquivo_excel.name}")
                
                # Ler Excel
                df = pd.read_excel(arquivo_excel)
                logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
                
                stats_arquivo = {
                    "arquivo": arquivo_excel.name,
                    "total_registros": 0,
                    "importacoes": 0,
                    "exportacoes": 0,
                    "erros": []
                }
                
                # Processar cada linha
                for idx, row in df.iterrows():
                    try:
                        # Extrair dados básicos
                        ncm = str(row.get('Código NCM', '')).strip() if pd.notna(row.get('Código NCM')) else None
                        if not ncm or len(ncm) < 4:
                            continue
                        
                        descricao = str(row.get('Descrição NCM', '')).strip()[:500] if pd.notna(row.get('Descrição NCM')) else ''
                        uf = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
                        pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
                        
                        # Processar mês
                        mes_str = str(row.get('Mês', '')).strip() if pd.notna(row.get('Mês')) else ''
                        mes = None
                        if mes_str:
                            import re
                            match = re.search(r'(\d{1,2})', mes_str)
                            if match:
                                mes = int(match.group(1))
                            else:
                                meses_map = {
                                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
                                    'abril': 4, 'maio': 5, 'junho': 6,
                                    'julho': 7, 'agosto': 8, 'setembro': 9,
                                    'outubro': 10, 'novembro': 11, 'dezembro': 12
                                }
                                for nome, num in meses_map.items():
                                    if nome in mes_str.lower():
                                        mes = num
                                        break
                        
                        if not mes:
                            mes = 1  # Default
                        
                        # Tentar detectar ano do nome do arquivo ou usar padrão
                        ano = 2025  # Default
                        nome_arquivo_lower = arquivo_excel.name.lower()
                        ano_match = re.search(r'20\d{2}', arquivo_excel.name)
                        if ano_match:
                            ano = int(ano_match.group())
                        
                        data_operacao = date(ano, mes, 1)
                        mes_referencia = f"{ano}-{mes:02d}"
                        
                        # Processar EXPORTAÇÃO
                        valor_exp = row.get('Exportação - 2025 - Valor US$ FOB', 0) or row.get('Exportação - Valor US$ FOB', 0) or row.get('Valor Exportação', 0)
                        peso_exp = row.get('Exportação - 2025 - Quilograma Líquido', 0) or row.get('Exportação - Quilograma Líquido', 0) or row.get('Peso Exportação', 0)
                        quantidade_exp = (
                            row.get('Exportação - 2025 - Quantidade Estatística', 0)
                            or row.get('Exportação - Quantidade Estatística', 0)
                            or row.get('Quantidade Exportação', 0)
                        )
                        
                        if pd.notna(valor_exp) and float(valor_exp) > 0:
                            # Verificar se já existe
                            existing = db.query(OperacaoComex).filter(
                                and_(
                                    OperacaoComex.ncm == ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                                    OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
                                    OperacaoComex.data_operacao == data_operacao,
                                    OperacaoComex.pais_origem_destino == pais,
                                    OperacaoComex.uf == uf
                                )
                            ).first()
                            
                            if not existing:
                                operacao = OperacaoComex(
                                    ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                                    descricao_produto=descricao,
                                    tipo_operacao=TipoOperacao.EXPORTACAO,
                                    via_transporte=ViaTransporte.OUTRAS,
                                    uf=uf,
                                    pais_origem_destino=pais,
                                    valor_fob=float(valor_exp),
                                    peso_liquido_kg=float(peso_exp) if pd.notna(peso_exp) else 0,
                                    quantidade_estatistica=float(quantidade_exp) if pd.notna(quantidade_exp) else 0,
                                    data_operacao=data_operacao,
                                    mes_referencia=mes_referencia,
                                    arquivo_origem=arquivo_excel.name
                                )
                                db.add(operacao)
                                stats_arquivo["exportacoes"] += 1
                                stats_arquivo["total_registros"] += 1
                                stats_geral["exportacoes"] += 1
                                stats_geral["total_registros"] += 1
                        
                        # Processar IMPORTAÇÃO
                        valor_imp = row.get('Importação - 2025 - Valor US$ FOB', 0) or row.get('Importação - Valor US$ FOB', 0) or row.get('Valor Importação', 0)
                        peso_imp = row.get('Importação - 2025 - Quilograma Líquido', 0) or row.get('Importação - Quilograma Líquido', 0) or row.get('Peso Importação', 0)
                        quantidade_imp = (
                            row.get('Importação - 2025 - Quantidade Estatística', 0)
                            or row.get('Importação - Quantidade Estatística', 0)
                            or row.get('Quantidade Importação', 0)
                        )
                        
                        if pd.notna(valor_imp) and float(valor_imp) > 0:
                            # Verificar se já existe
                            existing = db.query(OperacaoComex).filter(
                                and_(
                                    OperacaoComex.ncm == ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                                    OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
                                    OperacaoComex.data_operacao == data_operacao,
                                    OperacaoComex.pais_origem_destino == pais,
                                    OperacaoComex.uf == uf
                                )
                            ).first()
                            
                            if not existing:
                                operacao = OperacaoComex(
                                    ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                                    descricao_produto=descricao,
                                    tipo_operacao=TipoOperacao.IMPORTACAO,
                                    via_transporte=ViaTransporte.OUTRAS,
                                    uf=uf,
                                    pais_origem_destino=pais,
                                    valor_fob=float(valor_imp),
                                    peso_liquido_kg=float(peso_imp) if pd.notna(peso_imp) else 0,
                                    quantidade_estatistica=float(quantidade_imp) if pd.notna(quantidade_imp) else 0,
                                    data_operacao=data_operacao,
                                    mes_referencia=mes_referencia,
                                    arquivo_origem=arquivo_excel.name
                                )
                                db.add(operacao)
                                stats_arquivo["importacoes"] += 1
                                stats_arquivo["total_registros"] += 1
                                stats_geral["importacoes"] += 1
                                stats_geral["total_registros"] += 1
                        
                        # Commit a cada 1000 registros
                        if stats_geral["total_registros"] % 1000 == 0:
                            db.commit()
                            logger.info(f"  Processados {stats_geral['total_registros']} registros...")
                    
                    except Exception as e:
                        logger.error(f"Erro ao processar linha {idx} do arquivo {arquivo_excel.name}: {e}")
                        stats_arquivo["erros"].append(f"Linha {idx}: {str(e)}")
                        continue
                
                # Commit final do arquivo
                db.commit()
                stats_geral["arquivos_processados"] += 1
                stats_geral["detalhes_por_arquivo"].append(stats_arquivo)
                logger.success(f"✅ Arquivo {arquivo_excel.name} processado: {stats_arquivo['total_registros']} registros ({stats_arquivo['importacoes']} importações, {stats_arquivo['exportacoes']} exportações)")
            
            except Exception as e:
                logger.error(f"Erro ao processar arquivo {arquivo_excel.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                stats_geral["arquivos_com_erro"] += 1
                stats_geral["erros"].append(f"Arquivo {arquivo_excel.name}: {str(e)}")
                continue
        
        logger.success(
            f"✅ Importação automática concluída: {stats_geral['arquivos_processados']} arquivo(s) processado(s), "
            f"{stats_geral['total_registros']} registros ({stats_geral['importacoes']} importações, {stats_geral['exportacoes']} exportações)"
        )
        
        return {
            "success": True,
            "message": "Importação automática concluída",
            "stats": stats_geral
        }
        
    except Exception as e:
        logger.error(f"Erro na importação automática: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na importação automática: {str(e)}")


@app.post("/importar-excel-manual")
async def importar_excel_manual(
    nome_arquivo: str = Query(..., description="Nome do arquivo Excel (ex: H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx)"),
    db: Session = Depends(get_db)
):
    """
    Importa arquivo Excel manualmente do diretório comex_data/comexstat_csv.
    
    O arquivo deve estar em: comex_data/comexstat_csv/
    """
    try:
        from pathlib import Path
        import pandas as pd
        from datetime import date
        from database.models import OperacaoComex, TipoOperacao
        
        logger.info(f"Iniciando importação manual do arquivo: {nome_arquivo}")
        
        # Procurar arquivo em múltiplos locais
        base_dir = Path(__file__).parent.parent
        caminhos_possiveis = [
            base_dir / "comex_data" / "comexstat_csv" / nome_arquivo,
            base_dir / "comex_data" / "comexstat_csv" / f"{nome_arquivo}.xlsx",
            Path("/opt/render/project/src/comex_data/comexstat_csv") / nome_arquivo,
            Path("/opt/render/project/src/comex_data/comexstat_csv") / f"{nome_arquivo}.xlsx",
        ]
        
        arquivo_excel = None
        for caminho in caminhos_possiveis:
            if caminho.exists():
                arquivo_excel = caminho
                break
        
        if not arquivo_excel:
            raise HTTPException(
                status_code=404,
                detail=f"Arquivo não encontrado. Procurado em: {[str(c) for c in caminhos_possiveis]}"
            )
        
        logger.info(f"✅ Arquivo encontrado: {arquivo_excel}")
        
        # Ler Excel
        df = pd.read_excel(arquivo_excel)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        
        stats = {
            "total_registros": 0,
            "importacoes": 0,
            "exportacoes": 0,
            "erros": []
        }
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                # Extrair dados básicos
                ncm = str(row.get('Código NCM', '')).strip() if pd.notna(row.get('Código NCM')) else None
                if not ncm or len(ncm) < 4:
                    continue
                
                descricao = str(row.get('Descrição NCM', '')).strip()[:500] if pd.notna(row.get('Descrição NCM')) else ''
                uf = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
                pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
                
                # Processar mês
                mes_str = str(row.get('Mês', '')).strip() if pd.notna(row.get('Mês')) else ''
                mes = None
                if mes_str:
                    # Tentar extrair número do mês
                    import re
                    match = re.search(r'(\d{1,2})', mes_str)
                    if match:
                        mes = int(match.group(1))
                    else:
                        meses_map = {
                            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
                            'abril': 4, 'maio': 5, 'junho': 6,
                            'julho': 7, 'agosto': 8, 'setembro': 9,
                            'outubro': 10, 'novembro': 11, 'dezembro': 12
                        }
                        for nome, num in meses_map.items():
                            if nome in mes_str.lower():
                                mes = num
                                break
                
                if not mes:
                    mes = 1  # Default
                
                ano = 2025  # Ano do arquivo
                data_operacao = date(ano, mes, 1)
                mes_referencia = f"{ano}-{mes:02d}"
                
                # Processar EXPORTAÇÃO
                valor_exp = row.get('Exportação - 2025 - Valor US$ FOB', 0)
                peso_exp = row.get('Exportação - 2025 - Quilograma Líquido', 0)
                quantidade_exp = row.get('Exportação - 2025 - Quantidade Estatística', 0)
                
                if pd.notna(valor_exp) and float(valor_exp) > 0:
                    # Verificar se já existe
                    existing = db.query(OperacaoComex).filter(
                        and_(
                            OperacaoComex.ncm == ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
                            OperacaoComex.data_operacao == data_operacao,
                            OperacaoComex.pais_origem_destino == pais,
                            OperacaoComex.uf == uf
                        )
                    ).first()
                    
                    if not existing:
                        operacao = OperacaoComex(
                            ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                            descricao_produto=descricao,
                            tipo_operacao=TipoOperacao.EXPORTACAO,
                            via_transporte=ViaTransporte.OUTRAS,
                            uf=uf,
                            pais_origem_destino=pais,
                            valor_fob=float(valor_exp),
                            peso_liquido_kg=float(peso_exp) if pd.notna(peso_exp) else 0,
                            quantidade_estatistica=float(quantidade_exp) if pd.notna(quantidade_exp) else 0,
                            data_operacao=data_operacao,
                            mes_referencia=mes_referencia,
                            arquivo_origem=nome_arquivo
                        )
                        db.add(operacao)
                        stats["exportacoes"] += 1
                        stats["total_registros"] += 1
                
                # Processar IMPORTAÇÃO
                valor_imp = row.get('Importação - 2025 - Valor US$ FOB', 0)
                peso_imp = row.get('Importação - 2025 - Quilograma Líquido', 0)
                quantidade_imp = row.get('Importação - 2025 - Quantidade Estatística', 0)
                
                if pd.notna(valor_imp) and float(valor_imp) > 0:
                    # Verificar se já existe
                    existing = db.query(OperacaoComex).filter(
                        and_(
                            OperacaoComex.ncm == ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
                            OperacaoComex.data_operacao == data_operacao,
                            OperacaoComex.pais_origem_destino == pais,
                            OperacaoComex.uf == uf
                        )
                    ).first()
                    
                    if not existing:
                        operacao = OperacaoComex(
                            ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                            descricao_produto=descricao,
                            tipo_operacao=TipoOperacao.IMPORTACAO,
                            via_transporte=ViaTransporte.OUTRAS,
                            uf=uf,
                            pais_origem_destino=pais,
                            valor_fob=float(valor_imp),
                            peso_liquido_kg=float(peso_imp) if pd.notna(peso_imp) else 0,
                            quantidade_estatistica=float(quantidade_imp) if pd.notna(quantidade_imp) else 0,
                            data_operacao=data_operacao,
                            mes_referencia=mes_referencia,
                            arquivo_origem=nome_arquivo
                        )
                        db.add(operacao)
                        stats["importacoes"] += 1
                        stats["total_registros"] += 1
                
                # Commit a cada 1000 registros
                if stats["total_registros"] % 1000 == 0:
                    db.commit()
                    logger.info(f"  Processados {stats['total_registros']} registros...")
            
            except Exception as e:
                logger.error(f"Erro ao processar linha {idx}: {e}")
                stats["erros"].append(f"Linha {idx}: {str(e)}")
                continue
        
        db.commit()
        logger.success(f"✅ Importação concluída: {stats['total_registros']} registros ({stats['importacoes']} importações, {stats['exportacoes']} exportações)")
        
        return {
            "success": True,
            "message": "Importação manual concluída",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na importação manual: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na importação manual: {str(e)}")


@app.post("/upload-e-importar-cnae", tags=["importacao"])
async def upload_e_importar_cnae(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(..., description="Arquivo CNAE Excel (.xlsx ou .xls) para importar")
):
    """
    Faz upload de um arquivo CNAE Excel e importa automaticamente.
    OTIMIZADO: Usa BackgroundTasks do FastAPI para processamento assíncrono seguro.
    """
    import tempfile
    import os
    
    # Validar extensão
    if not (arquivo.filename.endswith('.xlsx') or arquivo.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    logger.info(f"📤 Recebendo upload do arquivo CNAE: {arquivo.filename}")
    
    # Criar arquivo temporário de forma segura
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    
    try:
        with os.fdopen(fd, 'wb') as tmp:
            conteudo = await arquivo.read()
            tmp.write(conteudo)
        
        logger.info(f"✅ Arquivo salvo temporariamente: {path}")
        
        # Adicionar à fila de tarefas do FastAPI
        background_tasks.add_task(processar_cnae_task, path, arquivo.filename)
        
        return {
            "success": True,
            "message": "Upload recebido. Processamento iniciado em background.",
            "arquivo": arquivo.filename,
            "status": "processando",
            "instrucoes": "Verifique os logs do Render para acompanhar o progresso."
        }
    
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        # Limpar arquivo se houver erro
        try:
            os.unlink(path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


# ============================================================================
# ENDPOINTS DE TESTE E INVESTIGAÇÃO
# ============================================================================

@app.post("/testar-upload-banco", tags=["teste"])
async def testar_upload_banco():
    """
    Endpoint de teste para verificar conexão com banco e inserir registro de teste.
    """
    try:
        db = SessionLocal()
        
        try:
            # Testar conexão
            result = db.execute(text("SELECT 1"))
            logger.info("✅ Conexão com banco OK")
            
            # Verificar tabela existe
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'operacoes_comex'
                )
            """))
            tabela_existe = result.scalar()
            
            if not tabela_existe:
                return {
                    "success": False,
                    "erro": "Tabela operacoes_comex não existe"
                }
            
            # Contar registros existentes
            total = db.query(OperacaoComex).count()
            
            # Inserir registro de teste
            from datetime import date
            registro_teste = OperacaoComex(
                ncm="00000000",
                descricao_produto="TESTE DE UPLOAD",
                tipo_operacao=TipoOperacao.EXPORTACAO,
                valor_fob=1.0,
                peso_liquido_kg=1.0,
                data_operacao=date.today(),
                mes_referencia=date.today().strftime("%Y-%m"),
                arquivo_origem="teste_upload"
            )
            
            db.add(registro_teste)
            db.commit()
            
            novo_total = db.query(OperacaoComex).count()
            
            return {
                "success": True,
                "mensagem": "Teste de upload bem-sucedido",
                "tabela_existe": True,
                "registros_antes": total,
                "registros_depois": novo_total,
                "registro_teste_inserido": True
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Erro no teste: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "erro": str(e),
                "traceback": traceback.format_exc()
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Erro crítico no teste: {e}")
        import traceback
        return {
            "success": False,
            "erro": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/testar-upload-automatico", tags=["teste"])
async def testar_upload_automatico():
    """
    Endpoint de teste para verificar se o processamento automático funciona.
    Cria um arquivo Excel de teste em memória e tenta processá-lo.
    """
    import tempfile
    import os
    import pandas as pd
    from datetime import date
    
    try:
        # Criar DataFrame de teste
        df_teste = pd.DataFrame({
            'Código NCM': ['01010101', '02020202'],
            'Descrição NCM': ['Produto Teste 1', 'Produto Teste 2'],
            'UF do Produto': ['SP', 'RJ'],
            'Países': ['EUA', 'China'],
            'Mês': ['1', '2'],
            'Exportação - 2025 - Valor US$ FOB': [100.0, 200.0],
            'Exportação - 2025 - Quilograma Líquido': [10.0, 20.0],
            'Importação - 2025 - Valor US$ FOB': [50.0, 75.0],
            'Importação - 2025 - Quilograma Líquido': [5.0, 7.5]
        })
        
        # Criar arquivo temporário
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        
        try:
            with os.fdopen(fd, 'wb') as tmp:
                df_teste.to_excel(tmp, index=False, engine='openpyxl')
            
            logger.info(f"✅ Arquivo de teste criado: {path}")
            
            # Testar processamento
            processar_excel_comex_task(path, "teste_automatico.xlsx")
            
            # Verificar se registros foram inseridos
            db = SessionLocal()
            try:
                registros_teste = db.query(OperacaoComex).filter(
                    OperacaoComex.arquivo_origem == "teste_automatico.xlsx"
                ).count()
                
                return {
                    "success": True,
                    "mensagem": "Teste de upload automático bem-sucedido",
                    "arquivo_teste_criado": True,
                    "processamento_executado": True,
                    "registros_inseridos": registros_teste
                }
            
            finally:
                db.close()
        
        finally:
            # Remover arquivo temporário
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Erro no teste automático: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "erro": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/diagnostico-sistema", tags=["teste"])
async def diagnostico_sistema():
    """
    Endpoint de diagnóstico completo do sistema.
    """
    import os
    from pathlib import Path
    
    diagnostico = {
        "timestamp": datetime.now().isoformat(),
        "banco_dados": {},
        "arquivos": {},
        "ambiente": {}
    }
    
    try:
        # Testar banco de dados
        db = SessionLocal()
        try:
            # Conexão
            result = db.execute(text("SELECT version()"))
            versao_pg = result.scalar()
            diagnostico["banco_dados"]["conectado"] = True
            diagnostico["banco_dados"]["versao"] = versao_pg
            
            # Tabelas
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tabelas = [row[0] for row in result]
            diagnostico["banco_dados"]["tabelas"] = tabelas
            
            # Contar registros
            if 'operacoes_comex' in tabelas:
                total = db.query(OperacaoComex).count()
                diagnostico["banco_dados"]["total_operacoes_comex"] = total
            
            if 'cnae_hierarquia' in tabelas:
                from database.models import CNAEHierarquia
                total_cnae = db.query(CNAEHierarquia).count()
                diagnostico["banco_dados"]["total_cnae"] = total_cnae
        
        except Exception as e:
            diagnostico["banco_dados"]["erro"] = str(e)
        
        finally:
            db.close()
        
        # Verificar diretórios de arquivos
        diretorios_verificar = [
            "/opt/render/project/src/comex_data/comexstat_csv",
            "/opt/render/project/src/comex_data/mdic_csv",
            str(Path(__file__).parent.parent / "comex_data" / "comexstat_csv")
        ]
        
        arquivos_encontrados = []
        for diretorio in diretorios_verificar:
            if os.path.exists(diretorio):
                arquivos = [f for f in os.listdir(diretorio) if f.endswith(('.xlsx', '.xls'))]
                arquivos_encontrados.extend([os.path.join(diretorio, f) for f in arquivos])
        
        diagnostico["arquivos"]["diretorios_verificados"] = diretorios_verificar
        diagnostico["arquivos"]["arquivos_excel_encontrados"] = arquivos_encontrados
        diagnostico["arquivos"]["total_arquivos"] = len(arquivos_encontrados)
        
        # Variáveis de ambiente
        diagnostico["ambiente"]["DATABASE_URL_configurado"] = bool(os.getenv("DATABASE_URL"))
        diagnostico["ambiente"]["PYTHON_VERSION"] = os.getenv("PYTHON_VERSION", "não configurado")
        diagnostico["ambiente"]["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "não configurado")
        
        return diagnostico
    
    except Exception as e:
        logger.error(f"Erro no diagnóstico: {e}")
        import traceback
        diagnostico["erro"] = str(e)
        diagnostico["traceback"] = traceback.format_exc()
        return diagnostico


@app.post("/importar-cnae-automatico")
async def importar_cnae_automatico(
    db: Session = Depends(get_db)
):
    """
    Importa automaticamente todos os arquivos CNAE encontrados na pasta comex_data/comexstat_csv.
    
    Procura por arquivos CNAE.xlsx, NOVO CNAE.xlsx ou arquivos na pasta cnae/.
    """
    try:
        from pathlib import Path
        import pandas as pd
        from database.models import CNAEHierarquia
        
        logger.info("Iniciando importação automática de arquivos CNAE...")
        
        # Procurar arquivos em múltiplos locais
        base_dir = Path(__file__).parent.parent
        diretorios_procurar = [
            base_dir / "comex_data" / "comexstat_csv",
            base_dir / "comex_data" / "comexstat_csv" / "cnae",
            Path("/opt/render/project/src/comex_data/comexstat_csv"),
            Path("/opt/render/project/src/comex_data/comexstat_csv/cnae"),
        ]
        
        arquivos_encontrados = []
        for diretorio in diretorios_procurar:
            if diretorio.exists():
                # Procurar arquivos CNAE
                arquivos_cnae = list(diretorio.glob("*CNAE*.xlsx")) + list(diretorio.glob("*CNAE*.xls"))
                arquivos_encontrados.extend(arquivos_cnae)
                logger.info(f"Encontrados {len(arquivos_cnae)} arquivos CNAE em {diretorio}")
        
        # Filtrar apenas arquivos válidos (não temporários)
        arquivos_validos = [a for a in arquivos_encontrados if not a.name.startswith('~$')]
        
        if not arquivos_validos:
            logger.warning("⚠️ Nenhum arquivo CNAE encontrado")
            return {
                "success": False,
                "message": "Nenhum arquivo CNAE encontrado",
                "diretorios_procurados": [str(d) for d in diretorios_procurar],
                "arquivos_encontrados": 0
            }
        
        logger.info(f"✅ {len(arquivos_validos)} arquivo(s) CNAE encontrado(s)")
        
        stats_geral = {
            "total_arquivos": len(arquivos_validos),
            "arquivos_processados": 0,
            "total_registros": 0,
            "inseridos": 0,
            "atualizados": 0,
            "erros": [],
            "detalhes_por_arquivo": []
        }
        
        # Processar cada arquivo
        for arquivo_excel in arquivos_validos:
            try:
                logger.info(f"📄 Processando arquivo CNAE: {arquivo_excel.name}")
                
                # Ler Excel
                df = pd.read_excel(arquivo_excel)
                logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
                
                stats_arquivo = {
                    "arquivo": arquivo_excel.name,
                    "total_registros": 0,
                    "inseridos": 0,
                    "atualizados": 0,
                    "erros": []
                }
                
                # Processar cada linha
                for idx, row in df.iterrows():
                    try:
                        # Tentar diferentes nomes de colunas para CNAE
                        cnae = (
                            str(row.get('CNAE', '')) or
                            str(row.get('Código CNAE', '')) or
                            str(row.get('CNAE 2.0', '')) or
                            str(row.get('Subclasse', ''))
                        ).strip()
                        
                        if not cnae or cnae == 'nan' or len(cnae) < 4:
                            continue
                        
                        # Limpar CNAE (remover pontos, traços, etc)
                        cnae_limpo = cnae.replace('.', '').replace('-', '').strip()
                        
                        # Extrair informações adicionais
                        descricao = (
                            str(row.get('Descrição', '')) or
                            str(row.get('Descrição Subclasse', '')) or
                            str(row.get('Descrição CNAE', ''))
                        ).strip()[:500]
                        
                        classe = str(row.get('Classe', '')).strip()[:10] if pd.notna(row.get('Classe')) else None
                        grupo = str(row.get('Grupo', '')).strip()[:10] if pd.notna(row.get('Grupo')) else None
                        divisao = str(row.get('Divisão', '')).strip()[:10] if pd.notna(row.get('Divisão')) else None
                        secao = str(row.get('Seção', '')).strip()[:10] if pd.notna(row.get('Seção')) else None
                        
                        # Verificar se já existe
                        existente = db.query(CNAEHierarquia).filter(
                            CNAEHierarquia.cnae == cnae_limpo
                        ).first()
                        
                        if existente:
                            # Atualizar
                            if descricao:
                                existente.descricao = descricao
                            if classe:
                                existente.classe = classe
                            if grupo:
                                existente.grupo = grupo
                            if divisao:
                                existente.divisao = divisao
                            if secao:
                                existente.secao = secao
                            stats_arquivo["atualizados"] += 1
                            stats_geral["atualizados"] += 1
                        else:
                            # Criar novo
                            cnae_hierarquia = CNAEHierarquia(
                                cnae=cnae_limpo,
                                descricao=descricao,
                                classe=classe,
                                grupo=grupo,
                                divisao=divisao,
                                secao=secao
                            )
                            db.add(cnae_hierarquia)
                            stats_arquivo["inseridos"] += 1
                            stats_geral["inseridos"] += 1
                        
                        stats_arquivo["total_registros"] += 1
                        stats_geral["total_registros"] += 1
                        
                        # Commit a cada 100 registros
                        if stats_geral["total_registros"] % 100 == 0:
                            db.commit()
                            logger.info(f"  Processados {stats_geral['total_registros']} registros...")
                    
                    except Exception as e:
                        logger.error(f"Erro ao processar linha {idx} do arquivo {arquivo_excel.name}: {e}")
                        stats_arquivo["erros"].append(f"Linha {idx}: {str(e)}")
                        continue
                
                # Commit final do arquivo
                db.commit()
                stats_geral["arquivos_processados"] += 1
                stats_geral["detalhes_por_arquivo"].append(stats_arquivo)
                logger.success(f"✅ Arquivo CNAE {arquivo_excel.name} processado: {stats_arquivo['inseridos']} inseridos, {stats_arquivo['atualizados']} atualizados")
            
            except Exception as e:
                logger.error(f"Erro ao processar arquivo CNAE {arquivo_excel.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                stats_geral["erros"].append(f"Arquivo {arquivo_excel.name}: {str(e)}")
                continue
        
        logger.success(
            f"✅ Importação automática de CNAE concluída: {stats_geral['arquivos_processados']} arquivo(s) processado(s), "
            f"{stats_geral['inseridos']} inseridos, {stats_geral['atualizados']} atualizados"
        )
        
        return {
            "success": True,
            "message": "Importação automática de CNAE concluída",
            "stats": stats_geral
        }
        
    except Exception as e:
        logger.error(f"Erro na importação automática de CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na importação automática de CNAE: {str(e)}")


@app.post("/importar-cnae")
async def importar_cnae(
    nome_arquivo: str = Query("CNAE.xlsx", description="Nome do arquivo CNAE (ex: CNAE.xlsx)"),
    db: Session = Depends(get_db)
):
    """
    Importa dados de CNAE do arquivo Excel para o banco de dados.
    
    O arquivo deve estar em: comex_data/comexstat_csv/cnae/
    """
    try:
        from pathlib import Path
        import pandas as pd
        from database.models import CNAEHierarquia
        
        logger.info(f"Iniciando importação de CNAE do arquivo: {nome_arquivo}")
        
        # Procurar arquivo em múltiplos locais
        base_dir = Path(__file__).parent.parent
        caminhos_possiveis = [
            base_dir / "comex_data" / "comexstat_csv" / nome_arquivo,
            base_dir / "comex_data" / "comexstat_csv" / "cnae" / nome_arquivo,
            base_dir / "comex_data" / "comexstat_csv" / f"{nome_arquivo}.xlsx",
            Path("/opt/render/project/src/comex_data/comexstat_csv") / nome_arquivo,
            Path("/opt/render/project/src/comex_data/comexstat_csv/cnae") / nome_arquivo,
        ]
        
        arquivo_excel = None
        for caminho in caminhos_possiveis:
            if caminho.exists():
                arquivo_excel = caminho
                break
        
        if not arquivo_excel:
            raise HTTPException(
                status_code=404,
                detail=f"Arquivo CNAE não encontrado. Procurado em: {[str(c) for c in caminhos_possiveis]}"
            )
        
        logger.info(f"✅ Arquivo encontrado: {arquivo_excel}")
        
        # Ler Excel
        df = pd.read_excel(arquivo_excel)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
        
        stats = {
            "total_registros": 0,
            "inseridos": 0,
            "atualizados": 0,
            "erros": []
        }
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                # Tentar diferentes nomes de colunas para CNAE
                cnae = (
                    str(row.get('CNAE', '')) or
                    str(row.get('Código CNAE', '')) or
                    str(row.get('CNAE 2.0', '')) or
                    str(row.get('Subclasse', ''))
                ).strip()
                
                if not cnae or cnae == 'nan' or len(cnae) < 4:
                    continue
                
                # Limpar CNAE (remover pontos, traços, etc)
                cnae_limpo = cnae.replace('.', '').replace('-', '').strip()
                
                # Extrair informações adicionais
                descricao = (
                    str(row.get('Descrição', '')) or
                    str(row.get('Descrição Subclasse', '')) or
                    str(row.get('Descrição CNAE', ''))
                ).strip()[:500]
                
                classe = str(row.get('Classe', '')).strip()[:10] if pd.notna(row.get('Classe')) else None
                grupo = str(row.get('Grupo', '')).strip()[:10] if pd.notna(row.get('Grupo')) else None
                divisao = str(row.get('Divisão', '')).strip()[:10] if pd.notna(row.get('Divisão')) else None
                secao = str(row.get('Seção', '')).strip()[:10] if pd.notna(row.get('Seção')) else None
                
                # Verificar se já existe
                existente = db.query(CNAEHierarquia).filter(
                    CNAEHierarquia.cnae == cnae_limpo
                ).first()
                
                if existente:
                    # Atualizar
                    if descricao:
                        existente.descricao = descricao
                    if classe:
                        existente.classe = classe
                    if grupo:
                        existente.grupo = grupo
                    if divisao:
                        existente.divisao = divisao
                    if secao:
                        existente.secao = secao
                    stats["atualizados"] += 1
                else:
                    # Criar novo
                    cnae_hierarquia = CNAEHierarquia(
                        cnae=cnae_limpo,
                        descricao=descricao,
                        classe=classe,
                        grupo=grupo,
                        divisao=divisao,
                        secao=secao
                    )
                    db.add(cnae_hierarquia)
                    stats["inseridos"] += 1
                
                stats["total_registros"] += 1
                
                # Commit a cada 100 registros
                if stats["total_registros"] % 100 == 0:
                    db.commit()
                    logger.info(f"  Processados {stats['total_registros']} registros...")
            
            except Exception as e:
                logger.error(f"Erro ao processar linha {idx}: {e}")
                stats["erros"].append(f"Linha {idx}: {str(e)}")
                continue
        
        db.commit()
        logger.success(f"✅ Importação de CNAE concluída: {stats['inseridos']} inseridos, {stats['atualizados']} atualizados")
        
        return {
            "success": True,
            "message": "Importação de CNAE concluída",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na importação de CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na importação de CNAE: {str(e)}")


@app.post("/coletar-empresas-bigquery-ultimos-anos")
async def coletar_empresas_bigquery_ultimos_anos(
    db: Session = Depends(get_db)
):
    """
    Coleta empresas do BigQuery (Base dos Dados) dos últimos 3 anos (2019, 2020, 2021).
    
    Requer BigQuery configurado no Render.
    """
    try:
        from api.coletar_base_dados import coletar_dados_bigquery, importar_para_postgresql
        from database.models import Empresa
        from sqlalchemy import func
        
        logger.info("Iniciando coleta de empresas do BigQuery (anos 2019, 2020, 2021)...")
        
        # Coletar dados do BigQuery
        df = coletar_dados_bigquery()
        
        if df.empty:
            return {
                "success": False,
                "message": "Nenhum dado retornado da query",
                "total_registros": 0,
                "empresas_inseridas": 0,
                "empresas_atualizadas": 0
            }
        
        # Estatísticas
        total_registros = len(df)
        
        # Estatísticas por ano
        anos_stats = {}
        if 'ano' in df.columns:
            anos_stats = df['ano'].value_counts().to_dict()
        
        # Estatísticas por tipo
        tipos_stats = {}
        if 'id_exportacao_importacao' in df.columns:
            tipos_stats = df['id_exportacao_importacao'].value_counts().to_dict()
        
        # Estatísticas por estado
        estados_stats = {}
        if 'sigla_uf' in df.columns:
            estados_stats = df['sigla_uf'].value_counts().head(10).to_dict()
        
        # Importar para PostgreSQL
        empresas_inseridas, empresas_atualizadas = importar_para_postgresql(df, db)
        
        # Verificar total no banco após importação
        total_no_banco = db.query(func.count(Empresa.id)).scalar() or 0
        
        logger.success(
            f"✅ Coleta concluída: {total_registros} registros coletados, "
            f"{empresas_inseridas} empresas inseridas, {empresas_atualizadas} atualizadas"
        )
        
        return {
            "success": True,
            "message": "Coleta de empresas do BigQuery concluída",
            "total_registros": total_registros,
            "empresas_inseridas": empresas_inseridas,
            "empresas_atualizadas": empresas_atualizadas,
            "total_no_banco": total_no_banco,
            "estatisticas": {
                "por_ano": anos_stats,
                "por_tipo": tipos_stats,
                "por_estado": estados_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta de empresas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na coleta: {str(e)}")


@app.get("/validar-bigquery")
async def validar_bigquery():
    """
    Valida conexão e configuração do BigQuery.
    Verifica se as credenciais estão configuradas e se é possível conectar.
    """
    try:
        import os
        import json
        from google.cloud import bigquery
        from google.oauth2 import service_account
        
        resultado = {
            "conectado": False,
            "credenciais_configuradas": False,
            "credenciais_validas": False,
            "teste_query": False,
            "erro": None,
            "detalhes": {}
        }
        
        # Verificar variável de ambiente
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        
        if creds_env:
            resultado["credenciais_configuradas"] = True
            
            # Tentar validar JSON
            if creds_env.startswith('{'):
                try:
                    creds_dict = json.loads(creds_env)
                    resultado["credenciais_validas"] = True
                    resultado["detalhes"]["tipo"] = "JSON string"
                    resultado["detalhes"]["project_id"] = creds_dict.get("project_id", "não encontrado")
                except json.JSONDecodeError:
                    resultado["credenciais_validas"] = False
                    resultado["erro"] = "JSON inválido em GOOGLE_APPLICATION_CREDENTIALS_JSON"
            else:
                resultado["detalhes"]["tipo"] = "Caminho de arquivo"
                resultado["detalhes"]["caminho"] = creds_env
        
        # Tentar conectar
        try:
            if creds_env and creds_env.startswith('{'):
                try:
                    creds_dict = json.loads(creds_env)
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    client = bigquery.Client(credentials=credentials, project=creds_dict.get("project_id"))
                except Exception as e:
                    resultado["erro"] = f"Erro ao criar credenciais: {str(e)}"
                    return resultado
            else:
                client = bigquery.Client()
            
            # Testar query simples
            query_job = client.query("SELECT 1 as test")
            query_job.result()
            
            resultado["conectado"] = True
            resultado["teste_query"] = True
            resultado["detalhes"]["project_id"] = client.project
            
            logger.success("✅ BigQuery conectado e funcionando")
            
        except ImportError:
            resultado["erro"] = "Biblioteca google-cloud-bigquery não instalada"
        except Exception as e:
            resultado["erro"] = str(e)
            logger.error(f"Erro ao conectar BigQuery: {e}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro na validação do BigQuery: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")


@app.post("/enriquecer-com-cnae-relacionamentos")
async def enriquecer_com_cnae_relacionamentos(
    db: Session = Depends(get_db)
):
    """
    Enriquece dados com CNAE e cria relacionamentos entre empresas importadoras e exportadoras.
    
    Este endpoint:
    1. Valida BigQuery
    2. Coleta empresas do BigQuery (Base dos Dados)
    3. Enriquece com dados de CNAE
    4. Cria relacionamentos entre importadoras e exportadoras
    5. Gera recomendações de sinergias
    """
    try:
        from pathlib import Path
        from data_collector.cnae_analyzer import CNAEAnalyzer
        from data_collector.sinergia_analyzer import SinergiaAnalyzer
        from data_collector.empresas_mdic_scraper import EmpresasMDICScraper
        from database.models import Empresa, EmpresasRecomendadas
        from sqlalchemy import func
        
        logger.info("Iniciando enriquecimento com CNAE e relacionamentos...")
        
        resultado = {
            "bigquery_validado": False,
            "empresas_coletadas": 0,
            "empresas_enriquecidas_cnae": 0,
            "relacionamentos_criados": 0,
            "recomendacoes_geradas": 0,
            "erros": []
        }
        
        # 1. Validar BigQuery
        logger.info("1️⃣ Validando BigQuery...")
        try:
            import os
            import json
            from google.cloud import bigquery
            from google.oauth2 import service_account
            
            creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            if creds_env:
                try:
                    if creds_env.startswith('{'):
                        creds_dict = json.loads(creds_env)
                        credentials = service_account.Credentials.from_service_account_info(creds_dict)
                        client = bigquery.Client(credentials=credentials, project=creds_dict.get("project_id"))
                    else:
                        client = bigquery.Client()
                    
                    # Testar query
                    query_job = client.query("SELECT 1 as test")
                    query_job.result()
                    
                    resultado["bigquery_validado"] = True
                    resultado["bigquery_detalhes"] = {"conectado": True, "project_id": client.project}
                    logger.success("✅ BigQuery conectado")
                except Exception as e:
                    resultado["bigquery_validado"] = False
                    resultado["bigquery_detalhes"] = {"conectado": False, "erro": str(e)}
                    logger.warning(f"⚠️ BigQuery não conectado: {e}")
                    resultado["erros"].append(f"BigQuery não conectado: {str(e)}")
            else:
                resultado["bigquery_validado"] = False
                resultado["bigquery_detalhes"] = {"conectado": False, "erro": "Credenciais não configuradas"}
                logger.warning("⚠️ BigQuery não configurado. Continuando sem BigQuery...")
                resultado["erros"].append("BigQuery não configurado - usando apenas dados locais")
        except ImportError:
            resultado["bigquery_validado"] = False
            resultado["bigquery_detalhes"] = {"conectado": False, "erro": "Biblioteca google-cloud-bigquery não instalada"}
            logger.warning("⚠️ Biblioteca BigQuery não instalada")
            resultado["erros"].append("Biblioteca BigQuery não instalada")
        except Exception as e:
            logger.warning(f"Erro ao validar BigQuery: {e}")
            resultado["erros"].append(f"Erro ao validar BigQuery: {str(e)}")
        
        # 2. Coletar empresas do BigQuery (se disponível)
        empresas_mdic = {}
        if resultado["bigquery_validado"]:
            logger.info("2️⃣ Coletando empresas do BigQuery...")
            try:
                scraper = EmpresasMDICScraper()
                empresas_lista = await scraper.coletar_empresas()
                for empresa in empresas_lista:
                    cnpj = empresa.get("cnpj")
                    if cnpj:
                        empresas_mdic[cnpj] = empresa
                resultado["empresas_coletadas"] = len(empresas_mdic)
                logger.success(f"✅ {len(empresas_mdic)} empresas coletadas do BigQuery")
            except Exception as e:
                logger.warning(f"Erro ao coletar empresas do BigQuery: {e}")
                resultado["erros"].append(f"Erro ao coletar empresas: {str(e)}")
        
        # 3. Carregar CNAE
        logger.info("3️⃣ Carregando dados de CNAE...")
        cnae_analyzer = None
        try:
            # Tentar múltiplos caminhos
            caminhos_cnae = [
                Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx"),
                Path(__file__).parent.parent / "NOVO CNAE.xlsx",
                Path("/opt/render/project/src/NOVO CNAE.xlsx"),
            ]
            
            arquivo_cnae = None
            for caminho in caminhos_cnae:
                if caminho.exists():
                    arquivo_cnae = caminho
                    break
            
            if arquivo_cnae:
                cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                cnae_analyzer.carregar_cnae_excel()
                logger.success("✅ CNAE carregado")
            else:
                logger.warning("⚠️ Arquivo CNAE não encontrado")
                resultado["erros"].append("Arquivo CNAE não encontrado")
        except Exception as e:
            logger.warning(f"Erro ao carregar CNAE: {e}")
            resultado["erros"].append(f"Erro ao carregar CNAE: {str(e)}")
        
        # 4. Enriquecer operações com empresas e CNAE
        logger.info("4️⃣ Enriquecendo operações com empresas e CNAE...")
        try:
            from database.models import OperacaoComex
            
            # Buscar operações sem empresa identificada
            operacoes_sem_empresa = db.query(OperacaoComex).filter(
                OperacaoComex.cnpj_importador.is_(None) | OperacaoComex.cnpj_exportador.is_(None)
            ).limit(10000).all()
            
            enriquecidas = 0
            for op in operacoes_sem_empresa:
                atualizada = False
                
                # Tentar identificar importador
                if not op.cnpj_importador and op.razao_social_importador:
                    # Buscar por razão social no MDIC
                    razao_limpa = str(op.razao_social_importador).upper().strip()
                    for cnpj, emp in empresas_mdic.items():
                        if str(emp.get("razao_social", "")).upper().strip() == razao_limpa:
                            op.cnpj_importador = cnpj
                            atualizada = True
                            break
                
                # Tentar identificar exportador
                if not op.cnpj_exportador and op.razao_social_exportador:
                    razao_limpa = str(op.razao_social_exportador).upper().strip()
                    for cnpj, emp in empresas_mdic.items():
                        if str(emp.get("razao_social", "")).upper().strip() == razao_limpa:
                            op.cnpj_exportador = cnpj
                            atualizada = True
                            break
                
                if atualizada:
                    enriquecidas += 1
                
                # Enriquecer com CNAE se disponível
                if cnae_analyzer:
                    if op.cnpj_importador:
                        cnae_info = cnae_analyzer.buscar_por_cnpj(op.cnpj_importador)
                        if cnae_info:
                            op.cnae_importador = cnae_info.get("cnae")
                    
                    if op.cnpj_exportador:
                        cnae_info = cnae_analyzer.buscar_por_cnpj(op.cnpj_exportador)
                        if cnae_info:
                            op.cnae_exportador = cnae_info.get("cnae")
            
            if enriquecidas > 0:
                db.commit()
                resultado["empresas_enriquecidas_cnae"] = enriquecidas
                logger.success(f"✅ {enriquecidas} operações enriquecidas")
        except Exception as e:
            logger.error(f"Erro ao enriquecer operações: {e}")
            resultado["erros"].append(f"Erro ao enriquecer operações: {str(e)}")
        
        # 5. Criar recomendações baseadas em estado, NCM e volume
        logger.info("5️⃣ Criando recomendações baseadas em estado, NCM e volume...")
        try:
            from database.models import OperacaoComex, TipoOperacao
            
            # Buscar empresas do banco (do BigQuery)
            empresas_banco = db.query(Empresa).all()
            empresas_dict = {emp.cnpj: emp for emp in empresas_banco if emp.cnpj}
            
            # Analisar operações por estado, NCM e volume
            logger.info("Analisando operações para criar recomendações...")
            
            # Agrupar operações por estado, NCM e tipo
            query_importacoes = db.query(
                OperacaoComex.uf,
                OperacaoComex.ncm,
                OperacaoComex.cnpj_importador,
                func.sum(OperacaoComex.valor_fob).label('volume_total'),
                func.count(OperacaoComex.id).label('qtd_operacoes')
            ).filter(
                OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
                OperacaoComex.uf.isnot(None),
                OperacaoComex.ncm.isnot(None),
                OperacaoComex.valor_fob > 0
            ).group_by(
                OperacaoComex.uf,
                OperacaoComex.ncm,
                OperacaoComex.cnpj_importador
            ).having(
                func.sum(OperacaoComex.valor_fob) > 10000  # Mínimo de volume
            ).all()
            
            query_exportacoes = db.query(
                OperacaoComex.uf,
                OperacaoComex.ncm,
                OperacaoComex.cnpj_exportador,
                func.sum(OperacaoComex.valor_fob).label('volume_total'),
                func.count(OperacaoComex.id).label('qtd_operacoes')
            ).filter(
                OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
                OperacaoComex.uf.isnot(None),
                OperacaoComex.ncm.isnot(None),
                OperacaoComex.valor_fob > 0
            ).group_by(
                OperacaoComex.uf,
                OperacaoComex.ncm,
                OperacaoComex.cnpj_exportador
            ).having(
                func.sum(OperacaoComex.valor_fob) > 10000  # Mínimo de volume
            ).all()
            
            # Criar índice de operações por estado+NCM
            importacoes_por_estado_ncm = {}
            exportacoes_por_estado_ncm = {}
            
            for uf, ncm, cnpj, volume, qtd in query_importacoes:
                chave = f"{uf}_{ncm}"
                if chave not in importacoes_por_estado_ncm:
                    importacoes_por_estado_ncm[chave] = []
                importacoes_por_estado_ncm[chave].append({
                    "cnpj": cnpj,
                    "volume": float(volume),
                    "qtd": int(qtd)
                })
            
            for uf, ncm, cnpj, volume, qtd in query_exportacoes:
                chave = f"{uf}_{ncm}"
                if chave not in exportacoes_por_estado_ncm:
                    exportacoes_por_estado_ncm[chave] = []
                exportacoes_por_estado_ncm[chave].append({
                    "cnpj": cnpj,
                    "volume": float(volume),
                    "qtd": int(qtd)
                })
            
            # Criar recomendações: para cada exportador, encontrar importadores prováveis
            relacionamentos_criados = 0
            recomendacoes_geradas = 0
            
            # Processar exportadores
            for chave, exportadores in exportacoes_por_estado_ncm.items():
                uf, ncm = chave.split('_', 1)
                
                # Buscar importadores do mesmo estado e NCM
                importadores_provaveis = importacoes_por_estado_ncm.get(chave, [])
                
                if not importadores_provaveis:
                    # Tentar mesmo estado, NCM diferente (complementaridade)
                    for chave_imp, importadores in importacoes_por_estado_ncm.items():
                        uf_imp, ncm_imp = chave_imp.split('_', 1)
                        if uf_imp == uf:
                            importadores_provaveis.extend(importadores)
                
                # Criar recomendações para cada exportador
                for exp in exportadores:
                    cnpj_exp = exp["cnpj"]
                    if not cnpj_exp:
                        continue
                    
                    empresa_exp = empresas_dict.get(cnpj_exp)
                    if not empresa_exp:
                        continue
                    
                    # Ordenar importadores por volume (maior volume = maior probabilidade)
                    importadores_provaveis_ordenados = sorted(
                        importadores_provaveis,
                        key=lambda x: x["volume"],
                        reverse=True
                    )[:5]  # Top 5 importadores prováveis
                    
                    for imp in importadores_provaveis_ordenados:
                        cnpj_imp = imp["cnpj"]
                        if not cnpj_imp or cnpj_imp == cnpj_exp:
                            continue
                        
                        empresa_imp = empresas_dict.get(cnpj_imp)
                        if not empresa_imp:
                            continue
                        
                        # Calcular score de recomendação
                        score = (
                            (imp["volume"] / 1000000) * 0.4 +  # Volume (peso 40%)
                            (imp["qtd"] / 100) * 0.3 +  # Quantidade de operações (peso 30%)
                            0.3 if uf == empresa_imp.estado else 0.1  # Mesmo estado (peso 30%)
                        )
                        
                        # Criar recomendação para exportador
                        recomendacao_exp = db.query(EmpresasRecomendadas).filter(
                            EmpresasRecomendadas.cnpj == cnpj_exp,
                            EmpresasRecomendadas.tipo_principal == "exportadora"
                        ).first()
                        
                        if not recomendacao_exp:
                            recomendacao_exp = EmpresasRecomendadas(
                                cnpj=cnpj_exp,
                                nome=empresa_exp.nome,
                                tipo_principal="exportadora",
                                estado=uf,
                                cnae=empresa_exp.cnae,
                                provavel_exportador=1,
                                peso_participacao=score * 100,  # Converter para 0-100
                                total_operacoes_exportacao=exp["qtd"],
                                valor_total_exportacao_usd=exp["volume"],
                                ncms_exportacao=ncm
                            )
                            db.add(recomendacao_exp)
                            recomendacoes_geradas += 1
                        else:
                            recomendacao_exp.peso_participacao = max(
                                recomendacao_exp.peso_participacao or 0,
                                score * 100
                            )
                            recomendacao_exp.total_operacoes_exportacao = max(
                                recomendacao_exp.total_operacoes_exportacao or 0,
                                exp["qtd"]
                            )
                            recomendacao_exp.valor_total_exportacao_usd = max(
                                recomendacao_exp.valor_total_exportacao_usd or 0,
                                exp["volume"]
                            )
                            if recomendacao_exp.ncms_exportacao:
                                if ncm not in recomendacao_exp.ncms_exportacao:
                                    recomendacao_exp.ncms_exportacao += f",{ncm}"
                            else:
                                recomendacao_exp.ncms_exportacao = ncm
                        
                        # Criar recomendação para importador
                        recomendacao_imp = db.query(EmpresasRecomendadas).filter(
                            EmpresasRecomendadas.cnpj == cnpj_imp,
                            EmpresasRecomendadas.tipo_principal == "importadora"
                        ).first()
                        
                        if not recomendacao_imp:
                            recomendacao_imp = EmpresasRecomendadas(
                                cnpj=cnpj_imp,
                                nome=empresa_imp.nome,
                                tipo_principal="importadora",
                                estado=uf,
                                cnae=empresa_imp.cnae,
                                provavel_importador=1,
                                peso_participacao=score * 100,  # Converter para 0-100
                                total_operacoes_importacao=imp["qtd"],
                                valor_total_importacao_usd=imp["volume"],
                                ncms_importacao=ncm
                            )
                            db.add(recomendacao_imp)
                            recomendacoes_geradas += 1
                        else:
                            recomendacao_imp.peso_participacao = max(
                                recomendacao_imp.peso_participacao or 0,
                                score * 100
                            )
                            recomendacao_imp.total_operacoes_importacao = max(
                                recomendacao_imp.total_operacoes_importacao or 0,
                                imp["qtd"]
                            )
                            recomendacao_imp.valor_total_importacao_usd = max(
                                recomendacao_imp.valor_total_importacao_usd or 0,
                                imp["volume"]
                            )
                            if recomendacao_imp.ncms_importacao:
                                if ncm not in recomendacao_imp.ncms_importacao:
                                    recomendacao_imp.ncms_importacao += f",{ncm}"
                            else:
                                recomendacao_imp.ncms_importacao = ncm
                        
                        relacionamentos_criados += 1
            
            db.commit()
            resultado["relacionamentos_criados"] = relacionamentos_criados
            resultado["recomendacoes_geradas"] = recomendacoes_geradas
            logger.success(f"✅ {relacionamentos_criados} relacionamentos criados, {recomendacoes_geradas} recomendações geradas")
        
        except Exception as e:
            logger.error(f"Erro ao analisar sinergias: {e}")
            import traceback
            logger.error(traceback.format_exc())
            resultado["erros"].append(f"Erro ao analisar sinergias: {str(e)}")
        
        logger.success("✅ Enriquecimento concluído")
        
        return {
            "success": True,
            "message": "Enriquecimento com CNAE e relacionamentos concluído",
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"Erro no enriquecimento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro no enriquecimento: {str(e)}")


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


@app.post("/coletar-dados-csv-direto")
async def coletar_dados_csv_direto(
    meses: int = Query(12, description="Número de meses para coletar"),
    db: Session = Depends(get_db)
):
    """
    Coleta dados CSV diretamente do MDIC usando CSVDataScraper (método mais confiável).
    Este endpoint força o download dos arquivos CSV e processa diretamente.
    
    Use este endpoint se /coletar-dados-enriquecidos não estiver coletando dados.
    """
    try:
        from data_collector.csv_scraper import CSVDataScraper
        from data_collector.transformer import DataTransformer
        from data_collector.collector import DataCollector
        from datetime import datetime
        
        logger.info(f"Iniciando coleta direta de CSV do MDIC ({meses} meses)...")
        
        stats = {
            "total_registros": 0,
            "meses_processados": [],
            "erros": [],
            "arquivos_baixados": 0
        }
        
        # Inicializar scrapers
        csv_scraper = CSVDataScraper()
        transformer = DataTransformer()
        collector = DataCollector()
        
        # Baixar arquivos CSV
        logger.info("📥 Baixando arquivos CSV do MDIC...")
        downloaded_files = await csv_scraper.download_recent_months(meses)
        
        if not downloaded_files:
            logger.warning("⚠️ Nenhum arquivo CSV foi baixado")
            stats["erros"].append("Nenhum arquivo CSV foi baixado do MDIC")
            return {
                "success": False,
                "message": "Não foi possível baixar arquivos CSV",
                "stats": stats,
                "recomendacao": "Verifique se as URLs do MDIC estão acessíveis ou tente novamente mais tarde"
            }
        
        stats["arquivos_baixados"] = len(downloaded_files)
        logger.info(f"✅ {len(downloaded_files)} arquivos baixados. Processando...")
        
        # Processar cada arquivo
        total_saved = 0
        for filepath in downloaded_files:
            try:
                # Parse CSV
                raw_data = csv_scraper.parse_csv_file(filepath)
                if not raw_data:
                    logger.warning(f"⚠️ Arquivo vazio ou inválido: {filepath.name}")
                    continue
                
                # Extrair mês e tipo do nome do arquivo
                nome = filepath.stem
                if "importacao" in nome.lower() or "imp" in nome.lower():
                    tipo = "Importação"
                elif "exportacao" in nome.lower() or "exp" in nome.lower():
                    tipo = "Exportação"
                else:
                    logger.warning(f"⚠️ Não foi possível determinar tipo do arquivo: {nome}")
                    continue
                
                # Extrair mês (formato: tipo_YYYY_MM ou tipo_YYYYMM)
                partes = nome.split('_')
                mes_str = None
                if len(partes) >= 3:
                    try:
                        ano = partes[-2]
                        mes = partes[-1]
                        mes_str = f"{ano}-{mes.zfill(2)}"
                    except:
                        pass
                
                if not mes_str:
                    # Tentar formato alternativo
                    import re
                    match = re.search(r'(\d{4})[_-]?(\d{2})', nome)
                    if match:
                        ano, mes = match.groups()
                        mes_str = f"{ano}-{mes}"
                    else:
                        mes_str = datetime.now().strftime("%Y-%m")
                        logger.warning(f"⚠️ Não foi possível extrair mês de {nome}, usando mês atual")
                
                # Transformar dados
                transformed = transformer.transform_csv_data(raw_data, mes_str, tipo)
                
                if not transformed:
                    logger.warning(f"⚠️ Nenhum registro transformado de {filepath.name}")
                    continue
                
                # Salvar no banco
                saved = collector._save_to_database(db, transformed, mes_str, tipo)
                total_saved += saved
                
                if mes_str not in stats["meses_processados"]:
                    stats["meses_processados"].append(mes_str)
                
                logger.info(
                    f"✅ {tipo} {mes_str}: {len(transformed)} registros processados, "
                    f"{saved} salvos no banco"
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar {filepath.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                stats["erros"].append(f"Erro ao processar {filepath.name}: {str(e)}")
        
        stats["total_registros"] = total_saved
        
        logger.success(
            f"✅ Coleta direta concluída: {total_saved} registros salvos, "
            f"{len(stats['meses_processados'])} meses processados"
        )
        
        return {
            "success": True,
            "message": "Coleta direta de CSV concluída",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta direta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro na coleta direta: {str(e)}")


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

    cache_key = _make_dashboard_cache_key(
        meses,
        tipo_operacao,
        ncm,
        ncms,
        empresa_importadora,
        empresa_exportadora,
    )
    cached = _get_cached_dashboard_stats(cache_key)
    if cached:
        return cached
    
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

    # Quantidade estatística total
    quantidade_total = db.query(func.sum(OperacaoComex.quantidade_estatistica)).filter(
        and_(*filtros_valor)
    ).scalar() or 0.0
    
    # Valores e quantidade separados por tipo de operação (se não houver filtro de tipo)
    valor_total_imp = 0.0
    valor_total_exp = 0.0
    quantidade_imp = 0.0
    quantidade_exp = 0.0
    if tipo_filtro is None:
        # Calcular valores separados apenas se não houver filtro de tipo
        filtros_valor_imp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO]
        valor_total_imp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            and_(*filtros_valor_imp)
        ).scalar() or 0.0

        quantidade_imp = db.query(func.sum(OperacaoComex.quantidade_estatistica)).filter(
            and_(*filtros_valor_imp)
        ).scalar() or 0.0
        
        filtros_valor_exp = base_filters + [OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO]
        valor_total_exp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            and_(*filtros_valor_exp)
        ).scalar() or 0.0
        quantidade_exp = db.query(func.sum(OperacaoComex.quantidade_estatistica)).filter(
            and_(*filtros_valor_exp)
        ).scalar() or 0.0
    elif tipo_filtro == TipoOperacao.IMPORTACAO:
        valor_total_imp = valor_total
        quantidade_imp = quantidade_total
    elif tipo_filtro == TipoOperacao.EXPORTACAO:
        valor_total_exp = valor_total
        quantidade_exp = quantidade_total
    
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
        total_emp_rec = db.query(func.count(EmpresasRecomendadas.id)).scalar() or 0
        if total_emp_rec > 0 and valor_total == 0 and not principais_ncms_list:
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

            quantidade_imp = db.query(func.sum(ComercioExterior.quantidade)).filter(
                ComercioExterior.tipo == 'importacao',
                ComercioExterior.data >= data_corte.date()
            ).scalar() or 0.0

            quantidade_exp = db.query(func.sum(ComercioExterior.quantidade)).filter(
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

                quantidade_imp = db.query(func.sum(ComercioExterior.quantidade)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar() or 0.0

                quantidade_exp = db.query(func.sum(ComercioExterior.quantidade)).filter(
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
                quantidade_total = float((quantidade_imp or 0) + (quantidade_exp or 0))
                
                logger.info("="*80)
                logger.info("📊 TOTAIS DE COMÉRCIO EXTERIOR")
                logger.info("="*80)
                logger.info(f"💰 Total Importação (USD): ${valor_total_imp:,.2f}")
                logger.info(f"💰 Total Exportação (USD): ${valor_total_exp:,.2f}")
                logger.info(f"💰 Valor Total (USD): ${valor_total:,.2f}")
                logger.info(f"📦 Volume Importação (kg): {volume_imp:,.2f}")
                logger.info(f"📦 Volume Exportação (kg): {volume_exp:,.2f}")
                logger.info(f"📊 Total de NCMs: {len(principais_ncms_list)}")
                logger.info("="*80)
                
                logger.info(f"✅ Dados carregados das novas tabelas: {len(principais_ncms_list)} NCMs, {valor_total:.2f} USD total")
        except Exception as e:
            logger.debug(f"Erro ao buscar dados das novas tabelas: {e}")
    
    # Garantir que valores sempre sejam calculados (mesmo que zero)
    if valor_total_imp is None:
        valor_total_imp = 0.0
    if valor_total_exp is None:
        valor_total_exp = 0.0
    
    # Log dos totais finais
    logger.info("="*80)
    logger.info("📊 RESUMO FINAL DO DASHBOARD")
    logger.info("="*80)
    logger.info(f"💰 Total Importação (USD): ${valor_total_imp:,.2f}")
    logger.info(f"💰 Total Exportação (USD): ${valor_total_exp:,.2f}")
    logger.info(f"💰 Valor Total (USD): ${valor_total:,.2f}")
    logger.info(f"📦 Volume Importação (kg): {volume_imp:,.2f}")
    logger.info(f"📦 Volume Exportação (kg): {volume_exp:,.2f}")
    logger.info(f"📊 Total de NCMs: {len(principais_ncms_list)}")
    logger.info(f"📊 Total de Países/Estados: {len(principais_paises_list)}")
    logger.info("="*80)
    
    # Se não houver dados, retornar resposta vazia rapidamente (não travar)
    if valor_total == 0 and not principais_ncms_list and not principais_paises_list:
        logger.warning("⚠️ Nenhum dado encontrado, retornando resposta vazia")
        return DashboardStats(
            volume_importacoes=0.0,
            volume_exportacoes=0.0,
            valor_total_usd=0.0,
            valor_total_importacoes=0.0,
            valor_total_exportacoes=0.0,
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
        valor_total_importacoes=float(valor_total_imp) if valor_total_imp > 0 else 0.0,
        valor_total_exportacoes=float(valor_total_exp) if valor_total_exp > 0 else 0.0,
        quantidade_estatistica_importacoes=float(quantidade_imp) if quantidade_imp > 0 else 0.0,
        quantidade_estatistica_exportacoes=float(quantidade_exp) if quantidade_exp > 0 else 0.0,
        quantidade_estatistica_total=float(quantidade_total) if quantidade_total > 0 else 0.0,
        principais_ncms=principais_ncms_list if principais_ncms_list else [],
        principais_paises=principais_paises_list if principais_paises_list else [],
        registros_por_mes=registros_dict if registros_dict else {},
        valores_por_mes=valores_por_mes_dict if valores_por_mes_dict else {},
        pesos_por_mes=pesos_por_mes_dict if pesos_por_mes_dict else {}
    )

    payload = stats_response.model_dump() if hasattr(stats_response, "model_dump") else stats_response.dict()
    _set_cached_dashboard_stats(cache_key, payload)
    return payload


def _read_json_file(relative_path: str) -> Optional[dict]:
    try:
        file_path = Path(__file__).parent.parent / relative_path
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


@app.get("/dashboard/dados-comexstat")
async def dashboard_dados_comexstat():
    dados = _read_json_file("data/resumo_dados_comexstat.json")
    if not dados:
        return {"success": False, "data": None, "message": "Arquivo não encontrado"}
    return {"success": True, "data": dados}


@app.get("/dashboard/dados-ncm-comexstat")
async def dashboard_dados_ncm_comexstat(
    limite: int = Query(default=100, ge=1, le=1000),
    uf: Optional[str] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
):
    dados = _read_json_file("data/dados_ncm_comexstat.json")
    if not dados:
        return {"success": False, "data": [], "message": "Arquivo não encontrado"}

    resultados = dados
    if uf:
        resultados = [item for item in resultados if str(item.get("uf", "")).upper() == uf.upper()]
    if tipo:
        tipo_lower = tipo.lower()
        if "import" in tipo_lower:
            resultados = [item for item in resultados if item.get("valor_importacao_usd", 0) > 0]
        elif "export" in tipo_lower:
            resultados = [item for item in resultados if item.get("valor_exportacao_usd", 0) > 0]

    return {"success": True, "data": resultados[:limite]}


@app.get("/dashboard/empresas-recomendadas")
async def dashboard_empresas_recomendadas(
    limite: int = Query(default=100, ge=1, le=500),
    tipo: Optional[str] = Query(default=None),
    uf: Optional[str] = Query(default=None),
    ncm: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        from sqlalchemy import or_

        query = db.query(EmpresasRecomendadas)
        if uf:
            query = query.filter(EmpresasRecomendadas.estado == uf.upper())
        if tipo:
            tipo_lower = tipo.lower()
            if "import" in tipo_lower:
                query = query.filter(EmpresasRecomendadas.provavel_importador == 1)
            elif "export" in tipo_lower:
                query = query.filter(EmpresasRecomendadas.provavel_exportador == 1)
        if ncm:
            ncm_limpo = ncm.replace(".", "").replace(" ", "").strip()
            query = query.filter(
                or_(
                    EmpresasRecomendadas.ncms_importacao.ilike(f"%{ncm_limpo}%"),
                    EmpresasRecomendadas.ncms_exportacao.ilike(f"%{ncm_limpo}%"),
                )
            )

        resultados = query.order_by(EmpresasRecomendadas.peso_participacao.desc()).limit(limite).all()
        data = [
            {
                "nome": emp.nome,
                "cnpj": emp.cnpj,
                "uf": emp.estado,
                "tipo": emp.tipo_principal,
                "peso_participacao": float(emp.peso_participacao or 0),
                "valor_total": float((emp.valor_total_importacao_usd or 0) + (emp.valor_total_exportacao_usd or 0)),
                "valor_importacao_usd": float(emp.valor_total_importacao_usd or 0),
                "valor_exportacao_usd": float(emp.valor_total_exportacao_usd or 0),
            }
            for emp in resultados
        ]
        return {"success": True, "data": data}
    except Exception:
        return {"success": False, "data": [], "message": "Erro ao consultar empresas recomendadas"}


@app.get("/dashboard/empresas-importadoras")
async def dashboard_empresas_importadoras(
    limite: int = Query(default=10, ge=1, le=100),
    uf: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(EmpresasRecomendadas).filter(
            EmpresasRecomendadas.provavel_importador == 1
        )
        if uf:
            query = query.filter(EmpresasRecomendadas.estado == uf.upper())
        resultados = query.order_by(EmpresasRecomendadas.peso_participacao.desc()).limit(limite).all()
        data = [
            {
                "nome": emp.nome,
                "cnpj": emp.cnpj,
                "uf": emp.estado,
                "valor_total": float(emp.valor_total_importacao_usd or 0),
                "peso_participacao": float(emp.peso_participacao or 0),
            }
            for emp in resultados
        ]
        if data:
            return {"success": True, "data": data}
    except Exception:
        pass

    fallback = _buscar_empresas_bigquery_sugestoes(uf=uf, tipo="importacao", limit=limite)
    return {"success": True, "data": fallback}


@app.get("/dashboard/empresas-exportadoras")
async def dashboard_empresas_exportadoras(
    limite: int = Query(default=10, ge=1, le=100),
    uf: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(EmpresasRecomendadas).filter(
            EmpresasRecomendadas.provavel_exportador == 1
        )
        if uf:
            query = query.filter(EmpresasRecomendadas.estado == uf.upper())
        resultados = query.order_by(EmpresasRecomendadas.peso_participacao.desc()).limit(limite).all()
        data = [
            {
                "nome": emp.nome,
                "cnpj": emp.cnpj,
                "uf": emp.estado,
                "valor_total": float(emp.valor_total_exportacao_usd or 0),
                "peso_participacao": float(emp.peso_participacao or 0),
            }
            for emp in resultados
        ]
        if data:
            return {"success": True, "data": data}
    except Exception:
        pass

    fallback = _buscar_empresas_bigquery_sugestoes(uf=uf, tipo="exportacao", limit=limite)
    return {"success": True, "data": fallback}


@app.get("/dashboard/sinergias-estado")
async def dashboard_sinergias_estado(
    uf: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    if SINERGIA_AVAILABLE and SinergiaAnalyzer is not None:
        analyzer = SinergiaAnalyzer()
        return analyzer.analisar_sinergias_por_estado(db, uf)

    try:
        from sqlalchemy import func

        filtros_imp = [OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO]
        filtros_exp = [OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO]
        if uf:
            filtros_imp.append(OperacaoComex.uf == uf.upper())
            filtros_exp.append(OperacaoComex.uf == uf.upper())

        importacoes = db.query(
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label("valor_total"),
            func.sum(OperacaoComex.peso_liquido_kg).label("peso_total"),
        ).filter(and_(*filtros_imp)).group_by(OperacaoComex.uf).all()

        exportacoes = db.query(
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label("valor_total"),
            func.sum(OperacaoComex.peso_liquido_kg).label("peso_total"),
        ).filter(and_(*filtros_exp)).group_by(OperacaoComex.uf).all()

        resultado = {}
        for uf_row, valor, peso in importacoes:
            resultado.setdefault(uf_row, {}).update({
                "uf": uf_row,
                "importacao_valor": float(valor or 0),
                "importacao_peso": float(peso or 0),
            })
        for uf_row, valor, peso in exportacoes:
            resultado.setdefault(uf_row, {}).update({
                "uf": uf_row,
                "exportacao_valor": float(valor or 0),
                "exportacao_peso": float(peso or 0),
            })

        return {"success": True, "data": list(resultado.values())}
    except Exception:
        return {"success": False, "data": []}


@app.get("/dashboard/sugestoes-empresas")
async def dashboard_sugestoes_empresas(
    limite: int = Query(default=20, ge=1, le=100),
    tipo: Optional[str] = Query(default=None),
    uf: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(EmpresasRecomendadas)
        if uf:
            query = query.filter(EmpresasRecomendadas.estado == uf.upper())
        if tipo:
            tipo_lower = tipo.lower()
            if "import" in tipo_lower:
                query = query.filter(EmpresasRecomendadas.provavel_importador == 1)
            elif "export" in tipo_lower:
                query = query.filter(EmpresasRecomendadas.provavel_exportador == 1)

        resultados = query.order_by(EmpresasRecomendadas.peso_participacao.desc()).limit(limite).all()
        sugestoes = [
            {
                "nome": emp.nome,
                "cnpj": emp.cnpj,
                "uf": emp.estado,
                "peso_participacao": float(emp.peso_participacao or 0),
                "valor_total": float((emp.valor_total_importacao_usd or 0) + (emp.valor_total_exportacao_usd or 0)),
                "tipo": emp.tipo_principal,
                "fonte": "empresas_recomendadas",
            }
            for emp in resultados
        ]
        if sugestoes:
            return {"success": True, "sugestoes": sugestoes}
    except Exception:
        pass

    sugestoes = _buscar_empresas_bigquery_sugestoes(uf=uf, tipo=tipo, limit=limite)
    return {"success": True, "sugestoes": sugestoes}


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
        
        # 2. Complementar com BigQuery (cadastro histórico)
        if len(resultado) < limit:
            try:
                resultados_bq = _buscar_empresas_bigquery(
                    q=q,
                    tipo="importacao",
                    limit=limit - len(resultado)
                )
                for item in resultados_bq:
                    nome = item.get("nome")
                    if not nome:
                        continue
                    if nome.lower() not in {r["nome"].lower() for r in resultado}:
                        resultado.append(item)
            except Exception as e:
                logger.debug(f"Erro ao buscar BigQuery (importadoras): {e}")

        # 3. Se não encontrou resultados ou quer incluir sugestões, buscar no MDIC
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
        
        # 4. Se ainda não tem resultados suficientes, buscar sugestões de sinergias
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
        
        # 2. Complementar com BigQuery (cadastro histórico)
        if len(resultado) < limit:
            try:
                resultados_bq = _buscar_empresas_bigquery(
                    q=q,
                    tipo="exportacao",
                    limit=limit - len(resultado)
                )
                for item in resultados_bq:
                    nome = item.get("nome")
                    if not nome:
                        continue
                    if nome.lower() not in {r["nome"].lower() for r in resultado}:
                        resultado.append(item)
            except Exception as e:
                logger.debug(f"Erro ao buscar BigQuery (exportadoras): {e}")

        # 3. Se não encontrou resultados ou query vazia, buscar no MDIC
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
        
        # 4. Se ainda não tem resultados suficientes, buscar sugestões de sinergias
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


@app.get("/api/validar-dados-banco")
async def validar_dados_banco(db: Session = Depends(get_db)):
    """
    Valida dados no banco e retorna estatísticas detalhadas.
    """
    from sqlalchemy import func
    from database.models import ComercioExterior, Empresa, OperacaoComex
    
    try:
        # ComercioExterior
        total_comex = db.query(func.count(ComercioExterior.id)).scalar() or 0
        
        total_valor_imp = 0.0
        total_valor_exp = 0.0
        total_peso_imp = 0.0
        total_peso_exp = 0.0
        
        if total_comex > 0:
            total_valor_imp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'importacao'
            ).scalar() or 0.0
            
            total_valor_exp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                ComercioExterior.tipo == 'exportacao'
            ).scalar() or 0.0
            
            total_peso_imp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                ComercioExterior.tipo == 'importacao'
            ).scalar() or 0.0
            
            total_peso_exp = db.query(func.sum(ComercioExterior.peso_kg)).filter(
                ComercioExterior.tipo == 'exportacao'
            ).scalar() or 0.0
        
        # Empresas
        total_empresas = db.query(func.count(Empresa.id)).scalar() or 0
        
        # OperacaoComex (tabela antiga)
        total_ops = db.query(func.count(OperacaoComex.id)).scalar() or 0
        
        logger.info("="*80)
        logger.info("📊 VALIDAÇÃO DE DADOS NO BANCO")
        logger.info("="*80)
        logger.info(f"📊 ComercioExterior: {total_comex:,} registros")
        logger.info(f"💰 Total Importação (USD): ${total_valor_imp:,.2f}")
        logger.info(f"💰 Total Exportação (USD): ${total_valor_exp:,.2f}")
        logger.info(f"📦 Total Peso Importação (kg): {total_peso_imp:,.2f}")
        logger.info(f"📦 Total Peso Exportação (kg): {total_peso_exp:,.2f}")
        logger.info(f"🏢 Empresas: {total_empresas:,} registros")
        logger.info(f"📋 OperacaoComex: {total_ops:,} registros")
        logger.info("="*80)
        
        return {
            "status": "ok",
            "comercio_exterior": {
                "total_registros": total_comex,
                "total_valor_importacao_usd": float(total_valor_imp),
                "total_valor_exportacao_usd": float(total_valor_exp),
                "total_peso_importacao_kg": float(total_peso_imp),
                "total_peso_exportacao_kg": float(total_peso_exp),
            },
            "empresas": {
                "total": total_empresas
            },
            "operacoes_comex": {
                "total": total_ops
            },
            "tem_dados": total_comex > 0 or total_empresas > 0 or total_ops > 0
        }
    except Exception as e:
        logger.error(f"Erro ao validar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao validar dados: {str(e)}")


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

