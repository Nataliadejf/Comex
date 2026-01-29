#!/usr/bin/env python3
"""
Script standalone para coletar dados públicos de empresas importadoras/exportadoras.
Pode ser executado diretamente no terminal ou via Git.

Uso:
    python coletar_dados_publicos_standalone.py
    python coletar_dados_publicos_standalone.py --limite 10000
    python coletar_dados_publicos_standalone.py --salvar-csv
"""
import sys
import os
from pathlib import Path

# Carregar .env (raiz do projeto ou backend/)
_root = Path(__file__).resolve().parent
for _env in [_root / "backend" / ".env", _root / ".env"]:
    if _env.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_env)
            break
        except ImportError:
            break

# Adicionar backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

import argparse
from loguru import logger
from datetime import datetime

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "coleta_publica_{time:YYYYMMDD_HHMMSS}.log",
    rotation="100 MB",
    level="DEBUG"
)

def main():
    parser = argparse.ArgumentParser(description="Coletor de dados públicos de empresas")
    parser.add_argument("--limite", type=int, default=50000, help="Limite de registros por fonte (padrão: 50000)")
    parser.add_argument("--salvar-csv", action="store_true", help="Salvar dados em CSV")
    parser.add_argument("--salvar-json", action="store_true", help="Salvar dados em JSON")
    parser.add_argument("--integrar-banco", action="store_true", default=True, help="Integrar com banco PostgreSQL")
    parser.add_argument("--apenas-dou", action="store_true", help="Coletar apenas do DOU")
    parser.add_argument("--apenas-bigquery", action="store_true", help="Coletar apenas do BigQuery")
    parser.add_argument("--executar-cruzamento", action="store_true", help="Após integrar, executar cruzamento NCM+UF")
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("COLETOR DE DADOS PÚBLICOS - EXECUÇÃO STANDALONE")
    logger.info("="*70)
    logger.info(f"Limite por fonte: {args.limite:,}")
    logger.info(f"Salvar CSV: {args.salvar_csv}")
    logger.info(f"Salvar JSON: {args.salvar_json}")
    logger.info(f"Integrar banco: {args.integrar_banco}")
    logger.info("")
    
    try:
        from data_collector.public_company_collector import PublicCompanyCollector
        
        collector = PublicCompanyCollector()
        
        # Coletar dados
        if args.apenas_dou:
            logger.info("🔍 Coletando apenas do DOU...")
            dados = collector.coletar_dou(limite=args.limite)
            collector.dados_coletados = dados
        elif args.apenas_bigquery:
            logger.info("🔍 Coletando apenas do BigQuery...")
            dados = collector.coletar_bigquery_empresas_ncm(limite=args.limite)
            collector.dados_coletados = dados
        else:
            logger.info("🔍 Coletando de todas as fontes...")
            dados = collector.coletar_todos(limite_por_fonte=args.limite)
        
        logger.info(f"✅ Total coletado: {len(dados):,} registros")
        
        # Salvar arquivos
        if args.salvar_csv:
            caminho_csv = collector.salvar_csv()
            logger.info(f"📄 CSV salvo em: {caminho_csv}")
        
        if args.salvar_json:
            caminho_json = collector.salvar_json()
            logger.info(f"📄 JSON salvo em: {caminho_json}")
        
        # Integrar banco
        if args.integrar_banco:
            try:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    stats = collector.integrar_banco_dados(db)
                    logger.info(f"✅ Integração concluída:")
                    logger.info(f"   - Total: {stats['total_registros']:,}")
                    logger.info(f"   - Inseridos: {stats['registros_inseridos']:,}")
                    logger.info(f"   - Erros: {stats['erros']:,}")
                    # Cruzamento NCM + UF (importadores x exportadores)
                    if args.executar_cruzamento and stats.get("registros_inseridos", 0) > 0:
                        try:
                            from services.cruzamento_ncm_uf import executar_cruzamento_ncm_uf
                            cruzamento_stats = executar_cruzamento_ncm_uf(db, limite_grupos=5000)
                            logger.info(f"✅ Cruzamento: {cruzamento_stats.get('grupos_ncm_uf', 0)} grupos NCM/UF")
                        except Exception as cx:
                            logger.error(f"❌ Erro no cruzamento: {cx}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"❌ Erro ao integrar banco: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info("="*70)
        logger.info("✅ COLETA CONCLUÍDA COM SUCESSO!")
        logger.info("="*70)
        
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulos: {e}")
        logger.error("💡 Certifique-se de que está executando do diretório raiz do projeto")
        logger.error("💡 E que todas as dependências estão instaladas: pip install -r backend/requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro durante coleta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
