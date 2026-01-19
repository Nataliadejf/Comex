"""
Script completo de validação do sistema Comex Analyzer.
Verifica:
1. Conexão com BigQuery
2. Dados no banco de dados PostgreSQL
3. Dados CSV em comex_data/comexstat_csv
4. Relacionamentos entre bases (recomendações)
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from database import get_db, init_db, engine
from database.models import (
    OperacaoComex, Empresa, EmpresasRecomendadas,
    ComercioExterior, CNAEHierarquia
)
from loguru import logger
import os
import json

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")

class ValidacaoSistema:
    """Classe para validação completa do sistema."""
    
    def __init__(self, db: Session):
        self.db = db
        self.resultados = {
            "bigquery": {},
            "banco_dados": {},
            "arquivos_csv": {},
            "relacionamentos": {},
            "resumo": {}
        }
    
    def validar_bigquery(self) -> Dict[str, Any]:
        """Valida conexão e acesso ao BigQuery."""
        logger.info("=" * 80)
        logger.info("🔍 VALIDAÇÃO 1: BigQuery")
        logger.info("=" * 80)
        
        resultado = {
            "conectado": False,
            "credenciais_configuradas": False,
            "teste_query": False,
            "erro": None
        }
        
        try:
            # Verificar credenciais
            creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            if creds_env:
                resultado["credenciais_configuradas"] = True
                logger.info("✅ Credenciais do Google Cloud encontradas")
                
                # Tentar parsear se for JSON string
                if creds_env.startswith('{'):
                    try:
                        creds_dict = json.loads(creds_env)
                        logger.info("✅ Credenciais em formato JSON válido")
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Erro ao parsear JSON: {e}")
                else:
                    logger.info(f"✅ Credenciais como caminho: {creds_env[:50]}...")
            else:
                logger.warning("⚠️ Credenciais do Google Cloud NÃO encontradas")
                logger.info("💡 Configure GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            # Tentar conectar ao BigQuery
            try:
                from google.cloud import bigquery
                
                if creds_env and creds_env.startswith('{'):
                    try:
                        creds_dict = json.loads(creds_env)
                        from google.oauth2 import service_account
                        credentials = service_account.Credentials.from_service_account_info(creds_dict)
                        client = bigquery.Client(credentials=credentials)
                        logger.info("✅ Cliente BigQuery criado com credenciais JSON")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao criar credenciais: {e}")
                        client = bigquery.Client()
                else:
                    client = bigquery.Client()
                
                resultado["conectado"] = True
                logger.info("✅ Conectado ao BigQuery com sucesso")
                
                # Testar query simples
                try:
                    query = "SELECT 1 as test"
                    query_job = client.query(query)
                    results = query_job.result()
                    resultado["teste_query"] = True
                    logger.info("✅ Query de teste executada com sucesso")
                except Exception as e:
                    logger.error(f"❌ Erro ao executar query de teste: {e}")
                    resultado["erro"] = str(e)
                    
            except ImportError:
                logger.error("❌ Biblioteca google-cloud-bigquery não instalada")
                logger.info("💡 Instale com: pip install google-cloud-bigquery")
                resultado["erro"] = "Biblioteca não instalada"
            except Exception as e:
                logger.error(f"❌ Erro ao conectar ao BigQuery: {e}")
                resultado["erro"] = str(e)
                
        except Exception as e:
            logger.error(f"❌ Erro inesperado na validação BigQuery: {e}")
            resultado["erro"] = str(e)
        
        self.resultados["bigquery"] = resultado
        return resultado
    
    def validar_banco_dados(self) -> Dict[str, Any]:
        """Valida dados no banco de dados PostgreSQL."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDAÇÃO 2: Banco de Dados PostgreSQL")
        logger.info("=" * 80)
        
        resultado = {
            "conectado": False,
            "tabelas": {},
            "total_registros": {},
            "erro": None
        }
        
        try:
            # Testar conexão
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                resultado["conectado"] = True
                logger.info("✅ Conexão com PostgreSQL OK")
            
            # Verificar tabelas principais
            tabelas_verificar = [
                ("operacoes_comex", OperacaoComex),
                ("empresas", Empresa),
                ("empresas_recomendadas", EmpresasRecomendadas),
                ("comercio_exterior", ComercioExterior),
                ("cnae_hierarquia", CNAEHierarquia)
            ]
            
            for nome_tabela, modelo in tabelas_verificar:
                try:
                    count = self.db.query(func.count(modelo.id)).scalar()
                    resultado["tabelas"][nome_tabela] = {
                        "existe": True,
                        "total_registros": count
                    }
                    resultado["total_registros"][nome_tabela] = count
                    
                    if count > 0:
                        logger.info(f"✅ {nome_tabela}: {count:,} registros")
                    else:
                        logger.warning(f"⚠️ {nome_tabela}: VAZIA (0 registros)")
                        
                except Exception as e:
                    resultado["tabelas"][nome_tabela] = {
                        "existe": False,
                        "erro": str(e)
                    }
                    logger.error(f"❌ Erro ao verificar {nome_tabela}: {e}")
            
            # Verificar dados específicos de operacoes_comex
            if resultado["total_registros"].get("operacoes_comex", 0) > 0:
                try:
                    # Contar por tipo de operação
                    importacao = self.db.query(func.count(OperacaoComex.id)).filter(
                        OperacaoComex.tipo_operacao == "Importação"
                    ).scalar()
                    exportacao = self.db.query(func.count(OperacaoComex.id)).filter(
                        OperacaoComex.tipo_operacao == "Exportação"
                    ).scalar()
                    
                    resultado["operacoes_detalhes"] = {
                        "importacao": importacao,
                        "exportacao": exportacao
                    }
                    
                    logger.info(f"  📊 Importações: {importacao:,}")
                    logger.info(f"  📊 Exportações: {exportacao:,}")
                    
                    # Verificar CNPJs únicos
                    cnpjs_importadores = self.db.query(func.count(func.distinct(OperacaoComex.cnpj_importador))).scalar()
                    cnpjs_exportadores = self.db.query(func.count(func.distinct(OperacaoComex.cnpj_exportador))).scalar()
                    
                    resultado["cnpjs_unicos"] = {
                        "importadores": cnpjs_importadores,
                        "exportadores": cnpjs_exportadores
                    }
                    
                    logger.info(f"  📊 CNPJs Importadores únicos: {cnpjs_importadores:,}")
                    logger.info(f"  📊 CNPJs Exportadores únicos: {cnpjs_exportadores:,}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao obter detalhes: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do banco: {e}")
            resultado["erro"] = str(e)
        
        self.resultados["banco_dados"] = resultado
        return resultado
    
    def validar_arquivos_csv(self) -> Dict[str, Any]:
        """Valida arquivos CSV em comex_data/comexstat_csv."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDAÇÃO 3: Arquivos CSV")
        logger.info("=" * 80)
        
        resultado = {
            "diretorio_existe": False,
            "arquivos_encontrados": [],
            "total_arquivos": 0,
            "tamanho_total": 0,
            "erro": None
        }
        
        try:
            # Caminho do diretório
            base_dir = Path(__file__).parent.parent.parent
            csv_dir = base_dir / "comex_data" / "comexstat_csv"
            csv_downloads_dir = base_dir / "comex_data" / "csv_downloads"
            
            # Verificar diretório principal
            if csv_dir.exists():
                resultado["diretorio_existe"] = True
                logger.info(f"✅ Diretório encontrado: {csv_dir}")
                
                # Listar arquivos CSV
                arquivos_csv = list(csv_dir.glob("*.csv")) + list(csv_dir.glob("*.xlsx"))
                resultado["total_arquivos"] = len(arquivos_csv)
                
                for arquivo in arquivos_csv:
                    tamanho = arquivo.stat().st_size
                    resultado["arquivos_encontrados"].append({
                        "nome": arquivo.name,
                        "tamanho": tamanho,
                        "caminho": str(arquivo)
                    })
                    resultado["tamanho_total"] += tamanho
                    logger.info(f"  📄 {arquivo.name} ({tamanho:,} bytes)")
            else:
                logger.warning(f"⚠️ Diretório não encontrado: {csv_dir}")
            
            # Verificar diretório de downloads
            if csv_downloads_dir.exists():
                arquivos_downloads = list(csv_downloads_dir.glob("*.csv"))
                logger.info(f"\n✅ Diretório csv_downloads encontrado: {len(arquivos_downloads)} arquivos")
                
                # Contar por tipo
                importacoes = [f for f in arquivos_downloads if "importacao" in f.name]
                exportacoes = [f for f in arquivos_downloads if "exportacao" in f.name]
                
                logger.info(f"  📊 Importações: {len(importacoes)} arquivos")
                logger.info(f"  📊 Exportações: {len(exportacoes)} arquivos")
                
                resultado["csv_downloads"] = {
                    "total": len(arquivos_downloads),
                    "importacoes": len(importacoes),
                    "exportacoes": len(exportacoes)
                }
            else:
                logger.warning(f"⚠️ Diretório csv_downloads não encontrado: {csv_downloads_dir}")
                
        except Exception as e:
            logger.error(f"❌ Erro na validação de arquivos: {e}")
            resultado["erro"] = str(e)
        
        self.resultados["arquivos_csv"] = resultado
        return resultado
    
    def validar_relacionamentos(self) -> Dict[str, Any]:
        """Valida relacionamentos entre bases e recomendações."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDAÇÃO 4: Relacionamentos e Recomendações")
        logger.info("=" * 80)
        
        resultado = {
            "empresas_recomendadas": {},
            "relacionamento_operacoes_empresas": {},
            "erro": None
        }
        
        try:
            # Verificar empresas_recomendadas
            total_recomendadas = self.db.query(func.count(EmpresasRecomendadas.id)).scalar()
            resultado["empresas_recomendadas"]["total"] = total_recomendadas
            
            if total_recomendadas > 0:
                logger.info(f"✅ Empresas Recomendadas: {total_recomendadas:,} registros")
                
                # Verificar por tipo
                importadoras = self.db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.tipo == "importadora"
                ).scalar()
                exportadoras = self.db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.tipo == "exportadora"
                ).scalar()
                
                resultado["empresas_recomendadas"]["importadoras"] = importadoras
                resultado["empresas_recomendadas"]["exportadoras"] = exportadoras
                
                logger.info(f"  📊 Importadoras prováveis: {importadoras:,}")
                logger.info(f"  📊 Exportadoras prováveis: {exportadoras:,}")
                
                # Verificar se tem dados de relacionamento
                com_cnpj = self.db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.cnpj.isnot(None)
                ).scalar()
                
                resultado["empresas_recomendadas"]["com_cnpj"] = com_cnpj
                logger.info(f"  📊 Com CNPJ: {com_cnpj:,}")
                
            else:
                logger.warning("⚠️ Tabela empresas_recomendadas está VAZIA")
                logger.info("💡 Execute o script de análise de sinergias para popular")
            
            # Verificar relacionamento entre operacoes_comex e empresas
            try:
                # CNPJs em operacoes_comex que também estão em empresas
                cnpjs_operacoes = self.db.query(func.distinct(OperacaoComex.cnpj_importador)).filter(
                    OperacaoComex.cnpj_importador.isnot(None)
                ).all()
                cnpjs_operacoes = [c[0] for c in cnpjs_operacoes if c[0]]
                
                cnpjs_empresas = self.db.query(func.distinct(Empresa.cnpj)).filter(
                    Empresa.cnpj.isnot(None)
                ).all()
                cnpjs_empresas = [c[0] for c in cnpjs_empresas if c[0]]
                
                # Intersecção
                cnpjs_relacionados = set(cnpjs_operacoes) & set(cnpjs_empresas)
                
                resultado["relacionamento_operacoes_empresas"] = {
                    "cnpjs_operacoes": len(cnpjs_operacoes),
                    "cnpjs_empresas": len(cnpjs_empresas),
                    "cnpjs_relacionados": len(cnpjs_relacionados)
                }
                
                logger.info(f"\n📊 Relacionamento Operações ↔ Empresas:")
                logger.info(f"  CNPJs em operacoes_comex: {len(cnpjs_operacoes):,}")
                logger.info(f"  CNPJs em empresas: {len(cnpjs_empresas):,}")
                logger.info(f"  CNPJs relacionados: {len(cnpjs_relacionados):,}")
                
                if len(cnpjs_relacionados) == 0:
                    logger.warning("⚠️ NENHUM relacionamento encontrado entre operacoes_comex e empresas")
                    logger.info("💡 Execute script de análise de sinergias para criar relacionamentos")
                else:
                    percentual = (len(cnpjs_relacionados) / len(cnpjs_operacoes) * 100) if cnpjs_operacoes else 0
                    logger.info(f"  Percentual relacionado: {percentual:.1f}%")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao verificar relacionamento: {e}")
                resultado["relacionamento_operacoes_empresas"]["erro"] = str(e)
                
        except Exception as e:
            logger.error(f"❌ Erro na validação de relacionamentos: {e}")
            resultado["erro"] = str(e)
        
        self.resultados["relacionamentos"] = resultado
        return resultado
    
    def gerar_resumo(self) -> Dict[str, Any]:
        """Gera resumo final da validação."""
        logger.info("\n" + "=" * 80)
        logger.info("📋 RESUMO DA VALIDAÇÃO")
        logger.info("=" * 80)
        
        resumo = {
            "data_validacao": datetime.now().isoformat(),
            "status_geral": "OK",
            "problemas": [],
            "recomendacoes": []
        }
        
        # BigQuery
        if not self.resultados["bigquery"].get("conectado"):
            resumo["status_geral"] = "ATENÇÃO"
            resumo["problemas"].append("BigQuery não conectado")
            resumo["recomendacoes"].append("Configure GOOGLE_APPLICATION_CREDENTIALS_JSON no Render")
        
        # Banco de dados
        total_operacoes = self.resultados["banco_dados"].get("total_registros", {}).get("operacoes_comex", 0)
        if total_operacoes == 0:
            resumo["status_geral"] = "ATENÇÃO"
            resumo["problemas"].append("Tabela operacoes_comex está vazia")
            resumo["recomendacoes"].append("Execute coleta de dados do Comex Stat")
        
        total_empresas = self.resultados["banco_dados"].get("total_registros", {}).get("empresas", 0)
        if total_empresas == 0:
            resumo["problemas"].append("Tabela empresas está vazia")
            resumo["recomendacoes"].append("Execute coleta de dados do BigQuery (Base dos Dados)")
        
        total_recomendadas = self.resultados["relacionamentos"].get("empresas_recomendadas", {}).get("total", 0)
        if total_recomendadas == 0:
            resumo["problemas"].append("Tabela empresas_recomendadas está vazia")
            resumo["recomendacoes"].append("Execute script de análise de sinergias")
        
        # Relacionamentos
        cnpjs_relacionados = self.resultados["relacionamentos"].get("relacionamento_operacoes_empresas", {}).get("cnpjs_relacionados", 0)
        if cnpjs_relacionados == 0:
            resumo["problemas"].append("Nenhum relacionamento entre operacoes_comex e empresas")
            resumo["recomendacoes"].append("Execute script de análise de sinergias para criar relacionamentos")
        
        # Imprimir resumo
        logger.info(f"\n✅ Status Geral: {resumo['status_geral']}")
        
        if resumo["problemas"]:
            logger.warning("\n⚠️ Problemas Encontrados:")
            for problema in resumo["problemas"]:
                logger.warning(f"  - {problema}")
        
        if resumo["recomendacoes"]:
            logger.info("\n💡 Recomendações:")
            for recomendacao in resumo["recomendacoes"]:
                logger.info(f"  - {recomendacao}")
        
        self.resultados["resumo"] = resumo
        return resumo

def main():
    """Função principal."""
    logger.info("=" * 80)
    logger.info("🔍 VALIDAÇÃO COMPLETA DO SISTEMA COMEX ANALYZER")
    logger.info("=" * 80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Inicializar banco
    init_db()
    db = next(get_db())
    
    try:
        # Criar validador
        validador = ValidacaoSistema(db)
        
        # Executar validações
        validador.validar_bigquery()
        validador.validar_banco_dados()
        validador.validar_arquivos_csv()
        validador.validar_relacionamentos()
        validador.gerar_resumo()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ VALIDAÇÃO CONCLUÍDA")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    main()
