#!/usr/bin/env python3
"""
Script para validar conexão BigQuery e verificar todas as tabelas disponíveis.
"""
import sys
import os
from pathlib import Path

# Carregar .env
_env = Path(__file__).parent / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

# Adicionar backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from loguru import logger
import json

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

def validar_bigquery():
    """Valida conexão BigQuery e lista todas as tabelas."""
    logger.info("="*70)
    logger.info("VALIDAÇÃO BIGQUERY")
    logger.info("="*70)
    
    try:
        from google.cloud import bigquery
        
        # Obter credenciais
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not creds_env:
            logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada")
            logger.info("")
            logger.info("💡 Para configurar:")
            logger.info("   1. PowerShell: $env:GOOGLE_APPLICATION_CREDENTIALS_JSON = '{\"type\":\"service_account\",...}'")
            logger.info("   2. Ou crie arquivo .env na raiz do projeto")
            logger.info("   3. Veja CONFIGURAR_BIGQUERY.md para mais detalhes")
            logger.info("")
            logger.info("⚠️  Sem credenciais, você pode usar apenas --apenas-dou no coletor")
            return False
        
        # Carregar credenciais
        if creds_env.startswith('{'):
            creds_dict = json.loads(creds_env)
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            client = bigquery.Client(credentials=credentials)
        else:
            client = bigquery.Client()
        
        logger.info("✅ Conectado ao BigQuery")
        
        # Listar datasets do projeto
        project_id = "liquid-receiver-483923-n6"
        dataset_id = "Projeto_Comex"
        
        logger.info(f"📊 Projeto: {project_id}")
        logger.info(f"📊 Dataset: {dataset_id}")
        logger.info("")
        
        # Tabelas esperadas (baseado na imagem do usuário)
        tabelas_esperadas = [
            "NCMExportacao",
            "EmpresasImEx",
            "EmpresasMes7_2025",
            "Estabelecimentoscnpj",
            "municipio_exportacao",
            "municipio_importacao",
            "NCMImportacao",
        ]
        
        logger.info("🔍 Verificando tabelas disponíveis...")
        logger.info("")
        
        dataset_ref = client.dataset(dataset_id, project=project_id)
        tabelas_encontradas = []
        
        try:
            tables = list(client.list_tables(dataset_ref))
            
            for table in tables:
                tabela_id = table.table_id
                tabelas_encontradas.append(tabela_id)
                
                # Verificar se é uma das tabelas esperadas
                status = "✅" if tabela_id in tabelas_esperadas else "⚠️"
                logger.info(f"{status} {tabela_id}")
            
            logger.info("")
            logger.info("="*70)
            logger.info("RESUMO")
            logger.info("="*70)
            
            # Verificar tabelas faltando
            tabelas_faltando = [t for t in tabelas_esperadas if t not in tabelas_encontradas]
            
            if tabelas_faltando:
                logger.warning(f"⚠️ Tabelas esperadas mas não encontradas: {', '.join(tabelas_faltando)}")
            else:
                logger.info("✅ Todas as tabelas esperadas foram encontradas!")
            
            logger.info(f"📊 Total de tabelas encontradas: {len(tabelas_encontradas)}")
            logger.info(f"📊 Total de tabelas esperadas: {len(tabelas_esperadas)}")
            
            # Testar query em uma tabela
            logger.info("")
            logger.info("🧪 Testando query em NCMImportacao...")
            try:
                query = f"""
                SELECT COUNT(*) as total
                FROM `{project_id}.{dataset_id}.NCMImportacao`
                LIMIT 1
                """
                result = client.query(query).result()
                for row in result:
                    logger.info(f"✅ NCMImportacao: {row.total:,} registros")
            except Exception as e:
                logger.error(f"❌ Erro ao consultar NCMImportacao: {e}")
            
            logger.info("")
            logger.info("🧪 Testando query em NCMExportacao...")
            try:
                query = f"""
                SELECT COUNT(*) as total
                FROM `{project_id}.{dataset_id}.NCMExportacao`
                LIMIT 1
                """
                result = client.query(query).result()
                for row in result:
                    logger.info(f"✅ NCMExportacao: {row.total:,} registros")
            except Exception as e:
                logger.error(f"❌ Erro ao consultar NCMExportacao: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar tabelas: {e}")
            return False
        
    except ImportError:
        logger.error("❌ google-cloud-bigquery não instalado")
        logger.info("💡 Execute: pip install google-cloud-bigquery")
        return False
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    sucesso = validar_bigquery()
    sys.exit(0 if sucesso else 1)
