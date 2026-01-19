"""
Script para carregar dados do arquivo Excel ComexStat para o banco de dados.
"""
import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime, date
from loguru import logger

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db
from database.models import OperacaoComex, TipoOperacao


def processar_e_carregar_excel():
    """Processa arquivo Excel e carrega no banco de dados."""
    logger.info("="*80)
    logger.info("CARREGAMENTO DE DADOS EXCEL PARA BANCO DE DADOS")
    logger.info("="*80)
    
    arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
    
    if not arquivo_excel.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_excel}")
        return
    
    logger.info(f"Processando arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas")
    
    db = next(get_db())
    
    try:
        # Verificar se já há dados no banco
        total_existente = db.query(OperacaoComex).count()
        if total_existente > 0:
            logger.warning(f"⚠️ Já existem {total_existente} registros no banco")
            resposta = input("Deseja continuar e adicionar mais dados? (s/n): ")
            if resposta.lower() != 's':
                logger.info("Operação cancelada pelo usuário")
                return
        
        logger.info("Processando importações...")
        registros_adicionados = 0
        
        # Processar importações
        if 'Importação - 2025 - Valor US$ FOB' in df.columns:
            df_imp = df[
                df['Importação - 2025 - Valor US$ FOB'].notna() & 
                (df['Importação - 2025 - Valor US$ FOB'] > 0)
            ]
            
            logger.info(f"Processando {len(df_imp)} registros de importação...")
            
            for idx, row in df_imp.iterrows():
                try:
                    ncm = str(row['Código NCM']).strip() if pd.notna(row['Código NCM']) else None
                    if not ncm or len(ncm) < 4:
                        continue
                    
                    # Criar registro de importação
                    operacao = OperacaoComex(
                        ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                        descricao_produto=str(row.get('Descrição NCM', ''))[:500] if pd.notna(row.get('Descrição NCM')) else '',
                        tipo_operacao=TipoOperacao.IMPORTACAO,
                        uf=str(row.get('UF do Produto', '')) if pd.notna(row.get('UF do Produto')) else None,
                        valor_fob=float(row['Importação - 2025 - Valor US$ FOB']),
                        peso_liquido_kg=float(row['Importação - 2025 - Quilograma Líquido']) if pd.notna(row.get('Importação - 2025 - Quilograma Líquido')) else 0,
                        data_operacao=date(2025, 1, 1),  # Data padrão
                        mes_referencia='2025-01',
                        arquivo_origem=arquivo_excel.name
                    )
                    
                    db.add(operacao)
                    registros_adicionados += 1
                    
                    # Commit em lotes de 1000
                    if registros_adicionados % 1000 == 0:
                        db.commit()
                        logger.info(f"   Processados {registros_adicionados} registros...")
                
                except Exception as e:
                    logger.debug(f"Erro ao processar linha {idx}: {e}")
                    continue
        
        # Processar exportações
        logger.info("Processando exportações...")
        if 'Exportação - 2025 - Valor US$ FOB' in df.columns:
            df_exp = df[
                df['Exportação - 2025 - Valor US$ FOB'].notna() & 
                (df['Exportação - 2025 - Valor US$ FOB'] > 0)
            ]
            
            logger.info(f"Processando {len(df_exp)} registros de exportação...")
            
            for idx, row in df_exp.iterrows():
                try:
                    ncm = str(row['Código NCM']).strip() if pd.notna(row['Código NCM']) else None
                    if not ncm or len(ncm) < 4:
                        continue
                    
                    # Criar registro de exportação
                    operacao = OperacaoComex(
                        ncm=ncm[:8] if len(ncm) >= 8 else ncm.zfill(8),
                        descricao_produto=str(row.get('Descrição NCM', ''))[:500] if pd.notna(row.get('Descrição NCM')) else '',
                        tipo_operacao=TipoOperacao.EXPORTACAO,
                        uf=str(row.get('UF do Produto', '')) if pd.notna(row.get('UF do Produto')) else None,
                        valor_fob=float(row['Exportação - 2025 - Valor US$ FOB']),
                        peso_liquido_kg=float(row['Exportação - 2025 - Quilograma Líquido']) if pd.notna(row.get('Exportação - 2025 - Quilograma Líquido')) else 0,
                        data_operacao=date(2025, 1, 1),  # Data padrão
                        mes_referencia='2025-01',
                        arquivo_origem=arquivo_excel.name
                    )
                    
                    db.add(operacao)
                    registros_adicionados += 1
                    
                    # Commit em lotes de 1000
                    if registros_adicionados % 1000 == 0:
                        db.commit()
                        logger.info(f"   Processados {registros_adicionados} registros...")
                
                except Exception as e:
                    logger.debug(f"Erro ao processar linha {idx}: {e}")
                    continue
        
        # Commit final
        db.commit()
        logger.success(f"✅ Total de {registros_adicionados} registros adicionados ao banco!")
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    processar_e_carregar_excel()


