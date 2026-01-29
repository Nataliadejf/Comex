#!/usr/bin/env python3
"""
Script para validar conexão BigQuery e verificar todas as tabelas disponíveis.
"""
import sys
import os
from pathlib import Path

# Carregar .env de vários locais (incl. backend/.env)
_raiz = Path(__file__).resolve().parent
_backend_env = _raiz / "backend" / ".env"
for _env_path in [_backend_env, _raiz / ".env", Path(os.getcwd()) / ".env", _raiz.parent / ".env"]:
    if _env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_env_path)
            break
        except ImportError:
            break

# Adicionar backend ao path
backend_dir = _raiz / "backend"
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
        
        # Obter credenciais: variável JSON ou caminho do arquivo
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # caminho para arquivo .json
        
        # Se veio vazio ou não é JSON válido (ex.: dotenv truncou valor multilinha), tentar ler do .env
        if creds_env and not creds_env.strip().startswith("{"):
            creds_env = None
        if not creds_env or (creds_env.strip().startswith("{") and not creds_env.strip().endswith("}")):
            for _env_path in [_backend_env, _raiz / ".env"]:
                if _env_path.exists():
                    try:
                        with open(_env_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        key = "GOOGLE_APPLICATION_CREDENTIALS_JSON"
                        if key in content:
                            start = content.find(key)
                            start = content.find("=", start) + 1
                            # Valor pode ser multilinha: do primeiro { ao último }
                            brace = content.find("{", start)
                            if brace != -1:
                                depth = 0
                                end = brace
                                for i, c in enumerate(content[brace:], start=brace):
                                    if c == "{": depth += 1
                                    elif c == "}": depth -= 1
                                    if depth == 0:
                                        end = i
                                        break
                                creds_env = content[brace:end + 1]
                                if creds_env.strip():
                                    break
                    except Exception:
                        pass
        
        if creds_path and not creds_env:
            # Tentar carregar do arquivo
            try:
                p = Path(creds_path)
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        creds_env = f.read()
                    logger.info("✅ Credenciais carregadas do arquivo: " + str(p))
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível ler arquivo de credenciais: {e}")
        
        if not creds_env:
            logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada")
            logger.info("")
            logger.info("📁 Procurou .env em: " + str(_raiz) + ", backend/, " + os.getcwd())
            _env_check = _raiz / ".env"
            _backend_check = _raiz / "backend" / ".env"
            logger.info("   .env na raiz? " + ("Sim" if _env_check.exists() else "Não") + "  |  backend/.env? " + ("Sim" if _backend_check.exists() else "Não"))
            logger.info("")
            logger.info("💡 OPÇÕES PARA CONFIGURAR:")
            logger.info("")
            logger.info("   OPÇÃO 1 - Arquivo .env (recomendado)")
            logger.info("   Crie/edite .env na raiz do projeto ou em backend/ (JSON em uma ou várias linhas).")
            logger.info("   Nunca commite .env no GitHub (credenciais devem ficar só local/Render).")
            logger.info("")
            logger.info("   OPÇÃO 2 - PowerShell (sessão atual)")
            logger.info("   $env:GOOGLE_APPLICATION_CREDENTIALS_JSON = Get-Content -Raw caminho\\arquivo.json")
            logger.info("   Depois: python validar_bigquery.py")
            logger.info("")
            logger.info("   OPÇÃO 3 - Arquivo JSON no disco")
            logger.info("   No .env: GOOGLE_APPLICATION_CREDENTIALS=C:\\caminho\\sua-chave.json")
            logger.info("   (o script tenta ler o conteúdo desse arquivo)")
            logger.info("")
            logger.info("   Veja CONFIGURAR_BIGQUERY.md para mais detalhes.")
            logger.info("")
            logger.info("="*70)
            logger.info("OPÇÕES DE SAÍDA (o que fazer agora)")
            logger.info("="*70)
            logger.info("")
            logger.info("  A) Configurar credenciais e testar de novo")
            logger.info("     → Crie .env com GOOGLE_APPLICATION_CREDENTIALS_JSON ou use OPÇÃO 2/3 acima.")
            logger.info("     → Depois: python validar_bigquery.py")
            logger.info("")
            logger.info("  B) Rodar o coletor SEM BigQuery (apenas DOU)")
            logger.info("     → python coletar_dados_publicos_standalone.py --apenas-dou")
            logger.info("     → Útil para testar integração/cruzamento sem acesso ao BigQuery.")
            logger.info("")
            logger.info("  C) Ignorar validação local e usar só no Render")
            logger.info("     → Configure GOOGLE_APPLICATION_CREDENTIALS_JSON nas variáveis do Render.")
            logger.info("     → A coleta com BigQuery funcionará no deploy; localmente use --apenas-dou.")
            logger.info("")
            logger.info("  D) Sair e configurar depois")
            logger.info("     → Este script retorna código de saída 1 (falha).")
            logger.info("     → Scripts que checam 'validar_bigquery' podem pular BigQuery se falhar.")
            logger.info("")
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
            
            logger.info("")
            logger.info("🧪 Testando query em EmpresasImEx...")
            try:
                query = f"""
                SELECT COUNT(*) as total
                FROM `{project_id}.{dataset_id}.EmpresasImEx`
                WHERE razao_social IS NOT NULL AND cnpj IS NOT NULL
                LIMIT 1
                """
                result = client.query(query).result()
                for row in result:
                    logger.info(f"✅ EmpresasImEx (com cnpj/razao_social): {row.total:,} registros")
            except Exception as e:
                logger.error(f"❌ Erro ao consultar EmpresasImEx: {e}")
            
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
