"""
Script para carregar dados do arquivo Excel para o banco de dados e preparar para o dashboard.
"""
import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime
from loguru import logger

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db
from database.models import OperacaoComex
from sqlalchemy import func


def processar_arquivo_excel():
    """Processa arquivo Excel e retorna dados estruturados."""
    arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
    
    if not arquivo_excel.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_excel}")
        return None
    
    logger.info(f"Processando arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
    
    return df


def gerar_resumo_dados(df):
    """Gera resumo dos dados para o dashboard."""
    logger.info("Gerando resumo dos dados...")
    
    resumo = {
        'total_registros': len(df),
        'importacoes': {},
        'exportacoes': {},
        'por_estado': {},
        'por_ncm': {}
    }
    
    # Processar importações
    if 'Importação - 2025 - Valor US$ FOB' in df.columns:
        df_imp = df[df['Importação - 2025 - Valor US$ FOB'].notna() & (df['Importação - 2025 - Valor US$ FOB'] > 0)]
        resumo['importacoes'] = {
            'total_registros': len(df_imp),
            'valor_total_usd': float(df_imp['Importação - 2025 - Valor US$ FOB'].sum()),
            'valor_total_brl': float(df_imp['Importação - 2025 - Valor US$ FOB'].sum() * 5.0),
            'por_estado': df_imp.groupby('UF do Produto')['Importação - 2025 - Valor US$ FOB'].sum().to_dict(),
            'top_ncms': df_imp.groupby('Código NCM').agg({
                'Importação - 2025 - Valor US$ FOB': 'sum',
                'Descrição NCM': 'first'
            }).sort_values('Importação - 2025 - Valor US$ FOB', ascending=False).head(10).to_dict('index')
        }
    
    # Processar exportações
    if 'Exportação - 2025 - Valor US$ FOB' in df.columns:
        df_exp = df[df['Exportação - 2025 - Valor US$ FOB'].notna() & (df['Exportação - 2025 - Valor US$ FOB'] > 0)]
        resumo['exportacoes'] = {
            'total_registros': len(df_exp),
            'valor_total_usd': float(df_exp['Exportação - 2025 - Valor US$ FOB'].sum()),
            'valor_total_brl': float(df_exp['Exportação - 2025 - Valor US$ FOB'].sum() * 5.0),
            'por_estado': df_exp.groupby('UF do Produto')['Exportação - 2025 - Valor US$ FOB'].sum().to_dict(),
            'top_ncms': df_exp.groupby('Código NCM').agg({
                'Exportação - 2025 - Valor US$ FOB': 'sum',
                'Descrição NCM': 'first'
            }).sort_values('Exportação - 2025 - Valor US$ FOB', ascending=False).head(10).to_dict('index')
        }
    
    logger.info("✅ Resumo gerado")
    return resumo


def salvar_resumo_json(resumo, df):
    """Salva resumo em arquivo JSON para o dashboard."""
    import json
    
    output_dir = backend_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar resumo
    arquivo_resumo = output_dir / "resumo_dados_comexstat.json"
    with open(arquivo_resumo, 'w', encoding='utf-8') as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2, default=str)
    
    logger.success(f"✅ Resumo salvo: {arquivo_resumo}")
    
    # Salvar dados agregados por NCM
    dados_ncm = []
    if 'Código NCM' in df.columns:
        df_ncm = df.groupby(['Código NCM', 'Descrição NCM', 'UF do Produto']).agg({
            'Importação - 2025 - Valor US$ FOB': 'sum',
            'Exportação - 2025 - Valor US$ FOB': 'sum',
            'Importação - 2025 - Quilograma Líquido': 'sum',
            'Exportação - 2025 - Quilograma Líquido': 'sum'
        }).reset_index()
        
        for _, row in df_ncm.iterrows():
            dados_ncm.append({
                'ncm': str(row['Código NCM']),
                'descricao': str(row['Descrição NCM']),
                'uf': str(row['UF do Produto']),
                'valor_importacao_usd': float(row['Importação - 2025 - Valor US$ FOB']) if pd.notna(row['Importação - 2025 - Valor US$ FOB']) else 0,
                'valor_exportacao_usd': float(row['Exportação - 2025 - Valor US$ FOB']) if pd.notna(row['Exportação - 2025 - Valor US$ FOB']) else 0,
                'peso_importacao_kg': float(row['Importação - 2025 - Quilograma Líquido']) if pd.notna(row['Importação - 2025 - Quilograma Líquido']) else 0,
                'peso_exportacao_kg': float(row['Exportação - 2025 - Quilograma Líquido']) if pd.notna(row['Exportação - 2025 - Quilograma Líquido']) else 0
            })
    
    arquivo_ncm = output_dir / "dados_ncm_comexstat.json"
    with open(arquivo_ncm, 'w', encoding='utf-8') as f:
        json.dump(dados_ncm, f, ensure_ascii=False, indent=2, default=str)
    
    logger.success(f"✅ Dados NCM salvos: {arquivo_ncm}")
    
    return arquivo_resumo, arquivo_ncm


def main():
    """Função principal."""
    logger.info("="*80)
    logger.info("CARREGAMENTO DE DADOS EXCEL PARA DASHBOARD")
    logger.info("="*80)
    
    # Processar arquivo Excel
    df = processar_arquivo_excel()
    if df is None:
        return
    
    # Gerar resumo
    resumo = gerar_resumo_dados(df)
    
    # Salvar arquivos JSON
    arquivo_resumo, arquivo_ncm = salvar_resumo_json(resumo, df)
    
    # Estatísticas
    logger.info("\n" + "="*80)
    logger.info("ESTATÍSTICAS")
    logger.info("="*80)
    logger.info(f"Total de registros: {resumo['total_registros']}")
    logger.info(f"\nImportações:")
    logger.info(f"  - Registros: {resumo['importacoes'].get('total_registros', 0)}")
    logger.info(f"  - Valor total (USD): ${resumo['importacoes'].get('valor_total_usd', 0):,.2f}")
    logger.info(f"  - Valor total (BRL): R$ {resumo['importacoes'].get('valor_total_brl', 0):,.2f}")
    logger.info(f"\nExportações:")
    logger.info(f"  - Registros: {resumo['exportacoes'].get('total_registros', 0)}")
    logger.info(f"  - Valor total (USD): ${resumo['exportacoes'].get('valor_total_usd', 0):,.2f}")
    logger.info(f"  - Valor total (BRL): R$ {resumo['exportacoes'].get('valor_total_brl', 0):,.2f}")
    
    logger.success("\n✅ Processamento concluído!")


if __name__ == "__main__":
    main()


