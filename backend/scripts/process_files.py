"""
Script para processar arquivos CSV baixados manualmente do portal Comex Stat.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
import pandas as pd
from database import get_db, init_db, OperacaoComex
from data_collector.transformer import DataTransformer
from config import settings
from sqlalchemy import and_
import re
from datetime import datetime

def identificar_tipo_e_mes(nome_arquivo: str) -> tuple:
    """
    Identifica tipo (Importação/Exportação) e mês do nome do arquivo.
    
    Exemplos:
    - EXP_2025.csv -> ('Exportação', '2025-01')
    - IMP_2025.csv -> ('Importação', '2025-01')
    - EXP_2025_01.csv -> ('Exportação', '2025-01')
    """
    nome = nome_arquivo.upper()
    
    # Identificar tipo
    if nome.startswith('EXP'):
        tipo = 'Exportação'
    elif nome.startswith('IMP'):
        tipo = 'Importação'
    else:
        return None, None
    
    # Extrair ano e mês
    # Padrão: EXP_YYYY.csv ou EXP_YYYY_MM.csv
    match = re.search(r'(\d{4})(?:_(\d{2}))?', nome)
    if match:
        ano = match.group(1)
        mes = match.group(2) or '01'  # Se não tiver mês, assume janeiro
        mes_ref = f"{ano}-{mes}"
        return tipo, mes_ref
    
    return tipo, None

def processar_arquivo_csv(caminho_arquivo: Path) -> int:
    """
    Processa um arquivo CSV e importa para o banco de dados.
    
    Returns:
        Número de registros importados
    """
    logger.info(f"Processando arquivo: {caminho_arquivo.name}")
    
    # Identificar tipo e mês
    tipo, mes_ref = identificar_tipo_e_mes(caminho_arquivo.name)
    
    if not tipo:
        logger.warning(f"Não foi possível identificar tipo do arquivo: {caminho_arquivo.name}")
        return 0
    
    if not mes_ref:
        logger.warning(f"Não foi possível identificar mês do arquivo: {caminho_arquivo.name}")
        mes_ref = datetime.now().strftime("%Y-%m")
    
    logger.info(f"Tipo identificado: {tipo}")
    logger.info(f"Mês identificado: {mes_ref}")
    
    # Ler CSV
    try:
        # Tentar diferentes encodings e separadores
        try:
            df = pd.read_csv(
                caminho_arquivo,
                encoding='utf-8',
                sep=';',
                decimal=',',
                thousands='.',
                on_bad_lines='skip',
                low_memory=False
            )
        except Exception:
            df = pd.read_csv(
                caminho_arquivo,
                encoding='latin1',
                sep=';',
                decimal=',',
                thousands='.',
                on_bad_lines='skip',
                low_memory=False
            )
        
        logger.info(f"Arquivo lido: {len(df)} linhas")
        
        if df.empty:
            logger.warning("Arquivo está vazio")
            return 0
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo CSV: {e}")
        return 0
    
    # Transformar dados
    transformer = DataTransformer()
    
    # Converter DataFrame para lista de dicionários
    df['arquivo_origem'] = str(caminho_arquivo)
    dados_dict = df.to_dict('records')
    
    # Transformar
    dados_transformados = transformer.transform_dataframe(
        df,
        mes_ref,
        tipo,
        str(caminho_arquivo)
    )
    
    if not dados_transformados:
        logger.warning("Nenhum dado válido após transformação")
        return 0
    
    # Salvar no banco
    db = next(get_db())
    from sqlalchemy import and_
    
    saved_count = 0
    
    for record in dados_transformados:
        try:
            # Verificar se já existe (evitar duplicatas)
            existing = db.query(OperacaoComex).filter(
                and_(
                    OperacaoComex.ncm == record.get("ncm"),
                    OperacaoComex.tipo_operacao == record.get("tipo_operacao"),
                    OperacaoComex.data_operacao == record.get("data_operacao"),
                    OperacaoComex.pais_origem_destino == record.get("pais_origem_destino"),
                    OperacaoComex.uf == record.get("uf"),
                )
            ).first()
            
            if existing:
                continue  # Já existe, pular
            
            # Criar novo registro
            operacao = OperacaoComex(**record)
            db.add(operacao)
            saved_count += 1
        
        except Exception as e:
            logger.error(f"Erro ao salvar registro: {e}")
            continue
    
    try:
        db.commit()
        logger.info(f"✅ {saved_count} registros salvos no banco")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao commitar transação: {e}")
        raise
    
    return saved_count

def main():
    """
    Processa todos os arquivos CSV encontrados nas pastas configuradas.
    """
    logger.info("=" * 60)
    logger.info("PROCESSAMENTO DE ARQUIVOS CSV")
    logger.info("=" * 60)
    
    # Inicializar banco
    init_db()
    
    # Pastas para procurar arquivos
    pastas_busca = [
        Path("D:/comex"),
        Path("D:/NatFranca/raw"),
        settings.data_dir / "raw",
    ]
    
    arquivos_encontrados = []
    
    # Procurar arquivos CSV
    for pasta in pastas_busca:
        if pasta.exists():
            logger.info(f"Procurando arquivos em: {pasta}")
            csv_files = list(pasta.rglob("*.csv"))
            arquivos_encontrados.extend(csv_files)
            logger.info(f"  Encontrados {len(csv_files)} arquivos CSV")
    
    if not arquivos_encontrados:
        logger.warning("Nenhum arquivo CSV encontrado!")
        logger.info("Pastas verificadas:")
        for pasta in pastas_busca:
            logger.info(f"  - {pasta} (existe: {pasta.exists()})")
        logger.info("\n💡 Dica: Baixe arquivos CSV do portal Comex Stat e salve em uma dessas pastas")
        return
    
    logger.info(f"\nTotal de arquivos encontrados: {len(arquivos_encontrados)}")
    
    # Processar cada arquivo
    total_registros = 0
    arquivos_processados = 0
    
    for arquivo in arquivos_encontrados:
        try:
            registros = processar_arquivo_csv(arquivo)
            if registros > 0:
                total_registros += registros
                arquivos_processados += 1
        except Exception as e:
            logger.error(f"Erro ao processar {arquivo.name}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("=" * 60)
    logger.info("PROCESSAMENTO CONCLUÍDO!")
    logger.info("=" * 60)
    logger.info(f"Arquivos processados: {arquivos_processados}/{len(arquivos_encontrados)}")
    logger.info(f"Total de registros importados: {total_registros:,}")
    logger.info("=" * 60)
    
    # Verificar total no banco
    db = next(get_db())
    from sqlalchemy import func
    total_banco = db.query(func.count(OperacaoComex.id)).scalar()
    logger.info(f"Total de registros no banco: {total_banco:,}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

