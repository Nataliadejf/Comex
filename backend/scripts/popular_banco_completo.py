"""
Script completo para popular o banco com dados do Comex Stat.
Faz download, verifica arquivos e processa tudo automaticamente.
"""
import sys
from pathlib import Path
import asyncio

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, OperacaoComex
from sqlalchemy import func
from config import settings
import pandas as pd
from data_collector.transformer import DataTransformer
from data_collector.collector import DataCollector
import re
from datetime import datetime


def verificar_arquivo_csv(arquivo: Path) -> bool:
    """Verifica se o arquivo é CSV válido ou HTML."""
    try:
        conteudo = arquivo.read_text(encoding='utf-8', errors='ignore')[:1000]
        if '<html' in conteudo.lower() or '<!doctype' in conteudo.lower():
            logger.warning(f"Arquivo {arquivo.name} parece ser HTML, não CSV")
            return False
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar arquivo {arquivo.name}: {e}")
        return False


def identificar_tipo_e_mes(nome_arquivo: str) -> tuple:
    """Identifica tipo e mês do nome do arquivo."""
    nome = nome_arquivo.upper()
    
    if nome.startswith('EXP'):
        tipo = 'Exportação'
    elif nome.startswith('IMP'):
        tipo = 'Importação'
    else:
        return None, None
    
    match = re.search(r'(\d{4})(?:_(\d{2}))?', nome)
    if match:
        ano = match.group(1)
        mes = match.group(2) or '01'
        mes_ref = f"{ano}-{mes}"
        return tipo, mes_ref
    
    return tipo, None


def processar_arquivo_csv(arquivo: Path) -> int:
    """Processa um arquivo CSV e importa no banco."""
    logger.info(f"Processando: {arquivo.name}")
    
    # Verificar se é CSV válido
    if not verificar_arquivo_csv(arquivo):
        logger.warning(f"Pulando arquivo inválido: {arquivo.name}")
        return 0
    
    tipo, mes_ref = identificar_tipo_e_mes(arquivo.name)
    if not tipo or not mes_ref:
        logger.warning(f"Não foi possível identificar tipo/mês de {arquivo.name}")
        return 0
    
    logger.info(f"  Tipo: {tipo}, Mês: {mes_ref}")
    
    try:
        # Ler CSV com diferentes encodings e separadores
        df = None
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        separators = [';', ',', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(
                        arquivo,
                        encoding=encoding,
                        sep=sep,
                        decimal=',',
                        thousands='.',
                        on_bad_lines='skip',
                        low_memory=False,
                        dtype=str  # Ler tudo como string primeiro
                    )
                    if len(df.columns) > 1:  # CSV válido tem múltiplas colunas
                        logger.info(f"  Arquivo lido com encoding={encoding}, sep='{sep}': {len(df)} linhas")
                        break
                except Exception as e:
                    continue
            if df is not None and len(df.columns) > 1:
                break
        
        if df is None or len(df.columns) <= 1:
            logger.error(f"Não foi possível ler {arquivo.name} como CSV válido")
            return 0
        
        logger.info(f"  Colunas encontradas: {list(df.columns)[:10]}")
        
        # Transformar dados
        transformer = DataTransformer()
        dados_transformados = transformer.transform_dataframe(df, mes_ref, tipo)
        
        if not dados_transformados:
            logger.warning(f"Nenhum dado válido após transformação em {arquivo.name}")
            return 0
        
        logger.info(f"  {len(dados_transformados)} registros transformados")
        
        # Salvar no banco
        db = next(get_db())
        collector = DataCollector()
        
        saved_count = 0
        batch_size = 1000
        
        for i in range(0, len(dados_transformados), batch_size):
            batch = dados_transformados[i:i + batch_size]
            try:
                count = collector._save_to_database(db, batch)
                saved_count += count
                logger.info(f"  Batch {i//batch_size + 1}: {count} registros salvos")
            except Exception as e:
                logger.error(f"Erro ao salvar batch: {e}")
                continue
        
        db.close()
        
        logger.info(f"✅ {arquivo.name}: {saved_count} registros importados")
        return saved_count
        
    except Exception as e:
        logger.error(f"Erro ao processar {arquivo.name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("POPULAR BANCO COM DADOS DO COMEX STAT")
    logger.info("=" * 60)
    logger.info("")
    
    # 1. Inicializar banco
    logger.info("1️⃣  Inicializando banco de dados...")
    init_db()
    
    # Verificar estado atual
    db = next(get_db())
    total_atual = db.query(func.count(OperacaoComex.id)).scalar() or 0
    db.close()
    
    logger.info(f"   Registros atuais no banco: {total_atual:,}")
    logger.info("")
    
    # 2. Verificar arquivos CSV
    logger.info("2️⃣  Verificando arquivos CSV...")
    raw_dir = settings.data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    arquivos_csv = list(raw_dir.glob("*.csv"))
    
    if not arquivos_csv:
        logger.warning("Nenhum arquivo CSV encontrado!")
        logger.info(f"   Diretório: {raw_dir}")
        logger.info("")
        logger.info("💡 Baixe arquivos CSV do portal Comex Stat e salve neste diretório")
        return
    
    logger.info(f"   Encontrados {len(arquivos_csv)} arquivo(s) CSV")
    logger.info("")
    
    # 3. Processar arquivos
    logger.info("3️⃣  Processando arquivos...")
    logger.info("")
    
    total_importado = 0
    arquivos_processados = 0
    
    for arquivo in sorted(arquivos_csv):
        try:
            count = processar_arquivo_csv(arquivo)
            if count > 0:
                total_importado += count
                arquivos_processados += 1
            logger.info("")
        except Exception as e:
            logger.error(f"Erro ao processar {arquivo.name}: {e}")
            logger.info("")
    
    # 4. Verificar resultado final
    logger.info("=" * 60)
    logger.info("RESULTADO FINAL")
    logger.info("=" * 60)
    logger.info("")
    
    db = next(get_db())
    total_final = db.query(func.count(OperacaoComex.id)).scalar() or 0
    total_importacoes = db.query(func.count(OperacaoComex.id)).filter(
        OperacaoComex.tipo_operacao == 'IMPORTACAO'
    ).scalar() or 0
    total_exportacoes = db.query(func.count(OperacaoComex.id)).filter(
        OperacaoComex.tipo_operacao == 'EXPORTACAO'
    ).scalar() or 0
    db.close()
    
    logger.info(f"✅ Arquivos processados: {arquivos_processados}/{len(arquivos_csv)}")
    logger.info(f"✅ Registros importados nesta execução: {total_importado:,}")
    logger.info("")
    logger.info(f"📊 Total no banco: {total_final:,}")
    logger.info(f"   • Importações: {total_importacoes:,}")
    logger.info(f"   • Exportações: {total_exportacoes:,}")
    logger.info("")
    
    if total_final > 0:
        logger.info("✅ Banco populado com sucesso!")
        logger.info("   Acesse o dashboard: http://localhost:3000")
    else:
        logger.warning("⚠️  Nenhum registro foi importado")
        logger.info("   Verifique os logs acima para identificar problemas")
    
    logger.info("")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())



