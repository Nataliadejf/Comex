"""
Script completo para análise detalhada de empresas importadoras e exportadoras brasileiras em 2024.
Busca dados reais, integra com CNAE e gera sugestões de importação/exportação.
"""
import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any, Optional

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db
from database.models import OperacaoComex
from sqlalchemy import func, and_, or_, extract
from data_collector.cnae_analyzer import CNAEAnalyzer
from data_collector.empresas_mdic_scraper import EmpresasMDICScraper

def buscar_empresas_banco_2024():
    """Busca empresas reais do banco de dados para 2024."""
    logger.info("="*60)
    logger.info("BUSCANDO EMPRESAS NO BANCO DE DADOS - 2024")
    logger.info("="*60)
    
    db = next(get_db())
    
    try:
        # Buscar empresas importadoras de 2024
        logger.info("Buscando empresas importadoras de 2024...")
        empresas_imp = db.query(
            OperacaoComex.razao_social_importador,
            OperacaoComex.cnpj_importador,
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label('faturamento_total'),
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.group_concat(OperacaoComex.ncm.distinct()).label('ncms'),
            func.group_concat(OperacaoComex.descricao_produto.distinct()).label('produtos'),
            func.sum(OperacaoComex.peso_liquido_kg).label('peso_total_kg')
        ).filter(
            OperacaoComex.tipo_operacao == 'IMPORTACAO',
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.cnpj_importador.isnot(None),
            extract('year', OperacaoComex.data_operacao) == 2024
        ).group_by(
            OperacaoComex.cnpj_importador,
            OperacaoComex.razao_social_importador,
            OperacaoComex.uf
        ).all()
        
        logger.info(f"✅ Encontradas {len(empresas_imp)} empresas importadoras")
        
        # Buscar empresas exportadoras de 2024
        logger.info("Buscando empresas exportadoras de 2024...")
        empresas_exp = db.query(
            OperacaoComex.razao_social_exportador,
            OperacaoComex.cnpj_exportador,
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label('faturamento_total'),
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.group_concat(OperacaoComex.ncm.distinct()).label('ncms'),
            func.group_concat(OperacaoComex.descricao_produto.distinct()).label('produtos'),
            func.sum(OperacaoComex.peso_liquido_kg).label('peso_total_kg')
        ).filter(
            OperacaoComex.tipo_operacao == 'EXPORTACAO',
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.cnpj_exportador.isnot(None),
            extract('year', OperacaoComex.data_operacao) == 2024
        ).group_by(
            OperacaoComex.cnpj_exportador,
            OperacaoComex.razao_social_exportador,
            OperacaoComex.uf
        ).all()
        
        logger.info(f"✅ Encontradas {len(empresas_exp)} empresas exportadoras")
        
        return empresas_imp, empresas_exp
        
    except Exception as e:
        logger.error(f"Erro ao buscar empresas no banco: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return [], []


async def buscar_empresas_mdic_2024():
    """Busca empresas do MDIC para 2024."""
    logger.info("="*60)
    logger.info("BUSCANDO EMPRESAS DO MDIC - 2024")
    logger.info("="*60)
    
    try:
        scraper = EmpresasMDICScraper()
        empresas_mdic = await scraper.coletar_empresas(ano=2024)
        
        logger.info(f"✅ Encontradas {len(empresas_mdic)} empresas no MDIC")
        return empresas_mdic
        
    except Exception as e:
        logger.warning(f"Erro ao buscar empresas do MDIC: {e}")
        return []


def processar_empresas_detalhado(empresas_imp, empresas_exp, empresas_mdic=None):
    """Processa empresas e cria análise detalhada."""
    logger.info("="*60)
    logger.info("PROCESSANDO EMPRESAS DETALHADO")
    logger.info("="*60)
    
    # Carregar CNAE
    cnae_analyzer = None
    try:
        arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
        if arquivo_cnae.exists():
            cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
            cnae_analyzer.carregar_cnae_excel()
            logger.info("✅ CNAE carregado")
    except Exception as e:
        logger.warning(f"Não foi possível carregar CNAE: {e}")
    
    # Criar dicionário de empresas do MDIC por CNPJ
    empresas_mdic_dict = {}
    if empresas_mdic:
        for emp in empresas_mdic:
            cnpj = str(emp.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '')
            if cnpj:
                empresas_mdic_dict[cnpj] = emp
    
    # Processar empresas importadoras
    empresas_list = []
    
    for emp in empresas_imp:
        cnpj = str(emp.cnpj_importador).replace('.', '').replace('/', '').replace('-', '')
        
        # Buscar dados do MDIC
        dados_mdic = empresas_mdic_dict.get(cnpj, {})
        
        # Buscar CNAE
        dados_cnae = None
        if cnae_analyzer:
            dados_cnae = cnae_analyzer.buscar_cnae_empresa(cnpj)
        
        empresas_list.append({
            'nome_empresa': emp.razao_social_importador or dados_mdic.get('razao_social', ''),
            'razao_social': emp.razao_social_importador or dados_mdic.get('razao_social', ''),
            'cnpj': cnpj,
            'tipo': 'IMPORTADORA',
            'uf': emp.uf or dados_mdic.get('uf', ''),
            'faturamento_total_usd': float(emp.faturamento_total) if emp.faturamento_total else 0,
            'total_operacoes': emp.total_operacoes,
            'peso_total_kg': float(emp.peso_total_kg) if emp.peso_total_kg else 0,
            'ncms': emp.ncms or '',
            'produtos': emp.produtos or '',
            'cnae': dados_cnae.get('cnae', '') if dados_cnae else dados_mdic.get('cnae', ''),
            'classificacao_cnae': dados_cnae.get('classificacao', '') if dados_cnae else '',
            'endereco': dados_mdic.get('endereco', '') or (dados_cnae.get('endereco', '') if dados_cnae else ''),
            'municipio': dados_mdic.get('municipio', ''),
            'cep': dados_mdic.get('cep', '')
        })
    
    # Processar empresas exportadoras
    for emp in empresas_exp:
        cnpj = str(emp.cnpj_exportador).replace('.', '').replace('/', '').replace('-', '')
        
        # Buscar dados do MDIC
        dados_mdic = empresas_mdic_dict.get(cnpj, {})
        
        # Buscar CNAE
        dados_cnae = None
        if cnae_analyzer:
            dados_cnae = cnae_analyzer.buscar_cnae_empresa(cnpj)
        
        empresas_list.append({
            'nome_empresa': emp.razao_social_exportador or dados_mdic.get('razao_social', ''),
            'razao_social': emp.razao_social_exportador or dados_mdic.get('razao_social', ''),
            'cnpj': cnpj,
            'tipo': 'EXPORTADORA',
            'uf': emp.uf or dados_mdic.get('uf', ''),
            'faturamento_total_usd': float(emp.faturamento_total) if emp.faturamento_total else 0,
            'total_operacoes': emp.total_operacoes,
            'peso_total_kg': float(emp.peso_total_kg) if emp.peso_total_kg else 0,
            'ncms': emp.ncms or '',
            'produtos': emp.produtos or '',
            'cnae': dados_cnae.get('cnae', '') if dados_cnae else dados_mdic.get('cnae', ''),
            'classificacao_cnae': dados_cnae.get('classificacao', '') if dados_cnae else '',
            'endereco': dados_mdic.get('endereco', '') or (dados_cnae.get('endereco', '') if dados_cnae else ''),
            'municipio': dados_mdic.get('municipio', ''),
            'cep': dados_mdic.get('cep', '')
        })
    
    df_empresas = pd.DataFrame(empresas_list)
    
    # Agrupar empresas que são tanto importadoras quanto exportadoras
    if len(df_empresas) > 0:
        df_empresas_agrupadas = df_empresas.groupby('cnpj').agg({
            'nome_empresa': 'first',
            'razao_social': 'first',
            'tipo': lambda x: ', '.join(x.unique()),
            'uf': 'first',
            'faturamento_total_usd': 'sum',
            'total_operacoes': 'sum',
            'peso_total_kg': 'sum',
            'ncms': lambda x: ', '.join(set(','.join(x).split(','))),
            'produtos': lambda x: ', '.join(set(','.join(x).split(','))),
            'cnae': 'first',
            'classificacao_cnae': 'first',
            'endereco': 'first',
            'municipio': 'first',
            'cep': 'first'
        }).reset_index()
        
        df_empresas = df_empresas_agrupadas
    
    # Ordenar por faturamento (se houver dados)
    if len(df_empresas) > 0 and 'faturamento_total_usd' in df_empresas.columns:
        df_empresas = df_empresas.sort_values('faturamento_total_usd', ascending=False)
    
    logger.info(f"✅ Total de empresas únicas processadas: {len(df_empresas)}")
    
    return df_empresas


def criar_analise_ncm_por_empresa(df_empresas):
    """Cria análise detalhada de NCM por empresa com peso do faturamento."""
    logger.info("="*60)
    logger.info("CRIANDO ANÁLISE NCM POR EMPRESA")
    logger.info("="*60)
    
    db = next(get_db())
    
    analise_list = []
    
    for idx, empresa in df_empresas.iterrows():
        cnpj = empresa['cnpj']
        tipo_empresa = empresa['tipo']
        
        # Buscar operações detalhadas por NCM
        if 'IMPORTADORA' in tipo_empresa:
            operacoes = db.query(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                func.sum(OperacaoComex.valor_fob).label('valor_total'),
                func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
                func.count(OperacaoComex.id).label('qtd_operacoes'),
                OperacaoComex.pais_origem_destino
            ).filter(
                OperacaoComex.cnpj_importador == cnpj,
                OperacaoComex.tipo_operacao == 'IMPORTACAO',
                extract('year', OperacaoComex.data_operacao) == 2024
            ).group_by(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                OperacaoComex.pais_origem_destino
            ).all()
        
        if 'EXPORTADORA' in tipo_empresa:
            operacoes = db.query(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                func.sum(OperacaoComex.valor_fob).label('valor_total'),
                func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
                func.count(OperacaoComex.id).label('qtd_operacoes'),
                OperacaoComex.pais_origem_destino
            ).filter(
                OperacaoComex.cnpj_exportador == cnpj,
                OperacaoComex.tipo_operacao == 'EXPORTACAO',
                extract('year', OperacaoComex.data_operacao) == 2024
            ).group_by(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                OperacaoComex.pais_origem_destino
            ).all()
        
        faturamento_total = empresa['faturamento_total_usd']
        
        for op in operacoes:
            valor_ncm = float(op.valor_total) if op.valor_total else 0
            peso_percentual = (valor_ncm / faturamento_total * 100) if faturamento_total > 0 else 0
            
            analise_list.append({
                'cnpj': cnpj,
                'nome_empresa': empresa['nome_empresa'],
                'tipo': tipo_empresa,
                'uf': empresa['uf'],
                'ncm': op.ncm,
                'descricao_produto': op.descricao_produto,
                'pais': op.pais_origem_destino,
                'valor_fob_usd': valor_ncm,
                'peso_percentual_faturamento': peso_percentual,
                'peso_total_kg': float(op.peso_total) if op.peso_total else 0,
                'quantidade_operacoes': op.qtd_operacoes,
                'faturamento_total_empresa': faturamento_total
            })
    
    df_analise = pd.DataFrame(analise_list)
    logger.info(f"✅ Análise NCM criada: {len(df_analise)} registros")
    
    return df_analise


def criar_sugestoes_inteligentes(df_empresas, df_analise_ncm, df_excel=None):
    """Cria sugestões inteligentes de importação/exportação por empresa."""
    logger.info("="*60)
    logger.info("CRIANDO SUGESTÕES INTELIGENTES")
    logger.info("="*60)
    
    db = next(get_db())
    sugestoes_list = []
    
    # Carregar dados do Excel se disponível
    if df_excel is None:
        arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
        if arquivo_excel.exists():
            df_excel = pd.read_excel(arquivo_excel)
            logger.info(f"✅ Arquivo Excel carregado para análise: {len(df_excel)} linhas")
    
    # Para cada empresa, analisar padrões de mercado
    for idx, empresa in df_empresas.iterrows():
        cnpj = empresa['cnpj']
        tipo_empresa = empresa['tipo']
        uf = empresa['uf']
        
        # Buscar NCMs da empresa
        ncms_empresa = str(empresa['ncms']).split(',') if pd.notna(empresa['ncms']) else []
        ncms_empresa = [n.strip() for n in ncms_empresa if n.strip() and len(n.strip()) >= 4]
        
        # Para cada NCM que a empresa trabalha, buscar produtos similares no mercado
        for ncm in ncms_empresa[:10]:  # Limitar a 10 NCMs principais
            if not ncm or len(ncm) < 4:
                continue
            
            # Buscar produtos similares (mesmo prefixo de 4 dígitos) no mercado
            prefixo_ncm = ncm[:4]
            
            # Tentar buscar no banco primeiro
            try:
                produtos_similares = db.query(
                    OperacaoComex.ncm,
                    OperacaoComex.descricao_produto,
                    OperacaoComex.tipo_operacao,
                    func.sum(OperacaoComex.valor_fob).label('valor_total'),
                    func.count(OperacaoComex.id).label('qtd_operacoes')
                ).filter(
                    OperacaoComex.ncm.like(f'{prefixo_ncm}%'),
                    extract('year', OperacaoComex.data_operacao) == 2024
                ).group_by(
                    OperacaoComex.ncm,
                    OperacaoComex.descricao_produto,
                    OperacaoComex.tipo_operacao
                ).all()
            except:
                produtos_similares = []
            
            # Se não encontrou no banco, buscar no Excel
            if len(produtos_similares) == 0 and df_excel is not None:
                produtos_excel = df_excel[df_excel['Código NCM'].astype(str).str.startswith(prefixo_ncm, na=False)]
                
                # Agrupar por NCM e tipo
                if 'Exportação - 2025 - Valor US$ FOB' in produtos_excel.columns:
                    produtos_exp = produtos_excel[produtos_excel['Exportação - 2025 - Valor US$ FOB'].notna() & 
                                                 (produtos_excel['Exportação - 2025 - Valor US$ FOB'] > 0)]
                    produtos_exp_agrupado = produtos_exp.groupby(['Código NCM', 'Descrição NCM']).agg({
                        'Exportação - 2025 - Valor US$ FOB': 'sum'
                    }).reset_index()
                    
                    for _, row in produtos_exp_agrupado.head(5).iterrows():
                        produtos_similares.append(type('obj', (object,), {
                            'ncm': str(row['Código NCM']),
                            'descricao_produto': row['Descrição NCM'],
                            'tipo_operacao': 'EXPORTACAO',
                            'valor_total': row['Exportação - 2025 - Valor US$ FOB'],
                            'qtd_operacoes': 1
                        })())
                
                if 'Importação - 2025 - Valor US$ FOB' in produtos_excel.columns:
                    produtos_imp = produtos_excel[produtos_excel['Importação - 2025 - Valor US$ FOB'].notna() & 
                                                 (produtos_excel['Importação - 2025 - Valor US$ FOB'] > 0)]
                    produtos_imp_agrupado = produtos_imp.groupby(['Código NCM', 'Descrição NCM']).agg({
                        'Importação - 2025 - Valor US$ FOB': 'sum'
                    }).reset_index()
                    
                    for _, row in produtos_imp_agrupado.head(5).iterrows():
                        produtos_similares.append(type('obj', (object,), {
                            'ncm': str(row['Código NCM']),
                            'descricao_produto': row['Descrição NCM'],
                            'tipo_operacao': 'IMPORTACAO',
                            'valor_total': row['Importação - 2025 - Valor US$ FOB'],
                            'qtd_operacoes': 1
                        })())
            
            for produto in produtos_similares[:5]:  # Top 5 produtos similares
                # Se empresa é importadora, sugerir exportação de produtos similares
                if 'IMPORTADORA' in tipo_empresa and produto.tipo_operacao == 'EXPORTACAO':
                    sugestoes_list.append({
                        'cnpj': cnpj,
                        'nome_empresa': empresa['nome_empresa'],
                        'tipo_empresa_atual': 'IMPORTADORA',
                        'sugestao_tipo': 'EXPORTACAO',
                        'ncm_atual': ncm,
                        'ncm_sugerido': produto.ncm,
                        'descricao_produto_sugerido': produto.descricao_produto,
                        'valor_potencial_usd': float(produto.valor_total) if produto.valor_total else 0,
                        'qtd_operacoes_mercado': produto.qtd_operacoes,
                        'razao_sugestao': f'Produto similar ao NCM {ncm} que você já importa - mercado exporta produtos similares',
                        'uf': uf
                    })
                
                # Se empresa é exportadora, sugerir importação de produtos similares
                if 'EXPORTADORA' in tipo_empresa and produto.tipo_operacao == 'IMPORTACAO':
                    sugestoes_list.append({
                        'cnpj': cnpj,
                        'nome_empresa': empresa['nome_empresa'],
                        'tipo_empresa_atual': 'EXPORTADORA',
                        'sugestao_tipo': 'IMPORTACAO',
                        'ncm_atual': ncm,
                        'ncm_sugerido': produto.ncm,
                        'descricao_produto_sugerido': produto.descricao_produto,
                        'valor_potencial_usd': float(produto.valor_total) if produto.valor_total else 0,
                        'qtd_operacoes_mercado': produto.qtd_operacoes,
                        'razao_sugestao': f'Produto similar ao NCM {ncm} que você já exporta - mercado importa produtos similares',
                        'uf': uf
                    })
        
        # Sugerir diversificação baseado no Excel se disponível
        if df_excel is not None and uf:
            # Buscar produtos mais exportados no mesmo estado
            produtos_uf_exp = df_excel[
                (df_excel['UF do Produto'] == uf) & 
                (df_excel['Exportação - 2025 - Valor US$ FOB'].notna()) &
                (df_excel['Exportação - 2025 - Valor US$ FOB'] > 0)
            ].groupby(['Código NCM', 'Descrição NCM']).agg({
                'Exportação - 2025 - Valor US$ FOB': 'sum'
            }).reset_index().sort_values('Exportação - 2025 - Valor US$ FOB', ascending=False).head(10)
            
            # Buscar produtos mais importados no mesmo estado
            produtos_uf_imp = df_excel[
                (df_excel['UF do Produto'] == uf) & 
                (df_excel['Importação - 2025 - Valor US$ FOB'].notna()) &
                (df_excel['Importação - 2025 - Valor US$ FOB'] > 0)
            ].groupby(['Código NCM', 'Descrição NCM']).agg({
                'Importação - 2025 - Valor US$ FOB': 'sum'
            }).reset_index().sort_values('Importação - 2025 - Valor US$ FOB', ascending=False).head(10)
            
            # Se empresa é importadora, sugerir exportação
            if 'IMPORTADORA' in tipo_empresa:
                for _, row in produtos_uf_exp.iterrows():
                    sugestoes_list.append({
                        'cnpj': cnpj,
                        'nome_empresa': empresa['nome_empresa'],
                        'tipo_empresa_atual': 'IMPORTADORA',
                        'sugestao_tipo': 'EXPORTACAO',
                        'ncm_atual': '',
                        'ncm_sugerido': str(row['Código NCM']),
                        'descricao_produto_sugerido': row['Descrição NCM'],
                        'valor_potencial_usd': float(row['Exportação - 2025 - Valor US$ FOB']),
                        'qtd_operacoes_mercado': 1,
                        'razao_sugestao': f'Produto mais exportado no seu estado ({uf}) - oportunidade de diversificação',
                        'uf': uf
                    })
            
            # Se empresa é exportadora, sugerir importação
            if 'EXPORTADORA' in tipo_empresa:
                for _, row in produtos_uf_imp.iterrows():
                    sugestoes_list.append({
                        'cnpj': cnpj,
                        'nome_empresa': empresa['nome_empresa'],
                        'tipo_empresa_atual': 'EXPORTADORA',
                        'sugestao_tipo': 'IMPORTACAO',
                        'ncm_atual': '',
                        'ncm_sugerido': str(row['Código NCM']),
                        'descricao_produto_sugerido': row['Descrição NCM'],
                        'valor_potencial_usd': float(row['Importação - 2025 - Valor US$ FOB']),
                        'qtd_operacoes_mercado': 1,
                        'razao_sugestao': f'Produto mais importado no seu estado ({uf}) - oportunidade de diversificação',
                        'uf': uf
                    })
    
    df_sugestoes = pd.DataFrame(sugestoes_list)
    # Remover duplicatas
    if len(df_sugestoes) > 0:
        df_sugestoes = df_sugestoes.drop_duplicates(subset=['cnpj', 'ncm_sugerido'])
    
    logger.info(f"✅ Sugestões criadas: {len(df_sugestoes)}")
    
    return df_sugestoes


def processar_arquivo_excel_como_fonte():
    """Processa arquivo Excel baixado como fonte de dados."""
    logger.info("="*60)
    logger.info("PROCESSANDO ARQUIVO EXCEL COMO FONTE DE DADOS")
    logger.info("="*60)
    
    arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
    
    if not arquivo_excel.exists():
        logger.error(f"Arquivo Excel não encontrado: {arquivo_excel}")
        return None
    
    logger.info(f"Lendo arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas")
    
    # Processar dados agregados e criar estrutura de empresas
    empresas_list = []
    
    # Agrupar por UF, NCM e tipo de operação
    if 'UF do Produto' in df.columns and 'Código NCM' in df.columns:
        # Processar exportações
        df_exp = df[df['Exportação - 2025 - Valor US$ FOB'].notna() & (df['Exportação - 2025 - Valor US$ FOB'] > 0)]
        df_exp_agrupado = df_exp.groupby(['UF do Produto', 'Código NCM', 'Descrição NCM']).agg({
            'Exportação - 2025 - Valor US$ FOB': 'sum',
            'Exportação - 2025 - Quilograma Líquido': 'sum'
        }).reset_index()
        
        for idx, row in df_exp_agrupado.iterrows():
            empresas_list.append({
                'nome_empresa': f'Empresa Exportadora - {row["UF do Produto"]}',
                'razao_social': f'Empresa Exportadora - {row["UF do Produto"]}',
                'cnpj': f'EXP{idx:08d}',
                'tipo': 'EXPORTADORA',
                'uf': str(row['UF do Produto']),
                'faturamento_total_usd': float(row['Exportação - 2025 - Valor US$ FOB']),
                'peso_total_kg': float(row['Exportação - 2025 - Quilograma Líquido']) if pd.notna(row['Exportação - 2025 - Quilograma Líquido']) else 0,
                'ncms': str(row['Código NCM']),
                'produtos': str(row['Descrição NCM'])[:200],
                'cnae': '',
                'classificacao_cnae': '',
                'endereco': '',
                'municipio': '',
                'cep': '',
                'total_operacoes': 1
            })
        
        # Processar importações
        df_imp = df[df['Importação - 2025 - Valor US$ FOB'].notna() & (df['Importação - 2025 - Valor US$ FOB'] > 0)]
        df_imp_agrupado = df_imp.groupby(['UF do Produto', 'Código NCM', 'Descrição NCM']).agg({
            'Importação - 2025 - Valor US$ FOB': 'sum',
            'Importação - 2025 - Quilograma Líquido': 'sum'
        }).reset_index()
        
        for idx, row in df_imp_agrupado.iterrows():
            empresas_list.append({
                'nome_empresa': f'Empresa Importadora - {row["UF do Produto"]}',
                'razao_social': f'Empresa Importadora - {row["UF do Produto"]}',
                'cnpj': f'IMP{idx:08d}',
                'tipo': 'IMPORTADORA',
                'uf': str(row['UF do Produto']),
                'faturamento_total_usd': float(row['Importação - 2025 - Valor US$ FOB']),
                'peso_total_kg': float(row['Importação - 2025 - Quilograma Líquido']) if pd.notna(row['Importação - 2025 - Quilograma Líquido']) else 0,
                'ncms': str(row['Código NCM']),
                'produtos': str(row['Descrição NCM'])[:200],
                'cnae': '',
                'classificacao_cnae': '',
                'endereco': '',
                'municipio': '',
                'cep': '',
                'total_operacoes': 1
            })
    
    df_empresas = pd.DataFrame(empresas_list)
    
    # Agrupar por CNPJ (se houver duplicatas)
    if len(df_empresas) > 0:
        df_empresas = df_empresas.groupby('cnpj').agg({
            'nome_empresa': 'first',
            'razao_social': 'first',
            'tipo': lambda x: ', '.join(x.unique()),
            'uf': 'first',
            'faturamento_total_usd': 'sum',
            'peso_total_kg': 'sum',
            'ncms': lambda x: ', '.join(set(str(v) for v in x if pd.notna(v))),
            'produtos': lambda x: ', '.join(set(str(v) for v in x if pd.notna(v) and str(v))),
            'cnae': 'first',
            'classificacao_cnae': 'first',
            'endereco': 'first',
            'municipio': 'first',
            'cep': 'first',
            'total_operacoes': 'sum'
        }).reset_index()
        
        df_empresas = df_empresas.sort_values('faturamento_total_usd', ascending=False)
    
    logger.info(f"✅ Empresas processadas do Excel: {len(df_empresas)}")
    return df_empresas


def main():
    """Função principal."""
    logger.info("="*60)
    logger.info("ANÁLISE COMPLETA DE EMPRESAS 2024")
    logger.info("="*60)
    
    # 1. Buscar empresas do banco
    empresas_imp, empresas_exp = buscar_empresas_banco_2024()
    
    # 2. Se não houver empresas no banco, processar arquivo Excel
    df_empresas = None
    if len(empresas_imp) == 0 and len(empresas_exp) == 0:
        logger.info("Nenhuma empresa no banco, processando arquivo Excel...")
        df_empresas = processar_arquivo_excel_como_fonte()
        
        if df_empresas is None or len(df_empresas) == 0:
            logger.error("❌ Nenhuma empresa encontrada para processar")
            logger.info("💡 Dica: Execute primeiro a coleta de dados ou verifique o arquivo Excel")
            return
    else:
        # 3. Processar empresas detalhado do banco
        empresas_mdic = []
        df_empresas = processar_empresas_detalhado(empresas_imp, empresas_exp, empresas_mdic)
        
        if len(df_empresas) == 0:
            logger.error("❌ Nenhuma empresa encontrada para processar")
            return
    
    # 4. Criar análise NCM por empresa (apenas se houver dados no banco)
    df_analise_ncm = pd.DataFrame()
    if len(empresas_imp) > 0 or len(empresas_exp) > 0:
        df_analise_ncm = criar_analise_ncm_por_empresa(df_empresas)
    else:
        logger.info("Criando análise NCM a partir do arquivo Excel...")
        # Criar análise a partir do Excel
        analise_list = []
        for idx, empresa in df_empresas.iterrows():
            ncms = str(empresa['ncms']).split(',') if pd.notna(empresa['ncms']) else []
            faturamento_total = empresa['faturamento_total_usd']
            
            for ncm in ncms[:10]:  # Limitar a 10 NCMs
                ncm = ncm.strip()
                if not ncm:
                    continue
                
                # Calcular peso percentual (estimado)
                peso_percentual = 100 / len(ncms) if len(ncms) > 0 else 0
                
                analise_list.append({
                    'cnpj': empresa['cnpj'],
                    'nome_empresa': empresa['nome_empresa'],
                    'tipo': empresa['tipo'],
                    'uf': empresa['uf'],
                    'ncm': ncm,
                    'descricao_produto': empresa['produtos'][:100] if pd.notna(empresa['produtos']) else '',
                    'pais': '',
                    'valor_fob_usd': faturamento_total * (peso_percentual / 100),
                    'peso_percentual_faturamento': peso_percentual,
                    'peso_total_kg': empresa['peso_total_kg'] * (peso_percentual / 100) if pd.notna(empresa['peso_total_kg']) else 0,
                    'quantidade_operacoes': empresa['total_operacoes'],
                    'faturamento_total_empresa': faturamento_total
                })
        
        df_analise_ncm = pd.DataFrame(analise_list)
        logger.info(f"✅ Análise NCM criada: {len(df_analise_ncm)} registros")
    
    # 5. Criar sugestões inteligentes
    # Carregar Excel para análise se não foi carregado antes
    df_excel_para_sugestoes = None
    if len(empresas_imp) == 0 and len(empresas_exp) == 0:
        arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
        if arquivo_excel.exists():
            df_excel_para_sugestoes = pd.read_excel(arquivo_excel)
    
    df_sugestoes = criar_sugestoes_inteligentes(df_empresas, df_analise_ncm, df_excel_para_sugestoes)
    
    # 6. Salvar arquivos
    output_dir = backend_dir.parent / "comex_data" / "comexstat_csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar empresas
    arquivo_empresas = output_dir / f"empresas_completas_2024_{timestamp}.csv"
    df_empresas.to_csv(arquivo_empresas, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_empresas.name}")
    
    # Salvar análise NCM
    arquivo_analise = output_dir / f"analise_ncm_por_empresa_2024_{timestamp}.csv"
    df_analise_ncm.to_csv(arquivo_analise, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_analise.name}")
    
    # Salvar sugestões
    arquivo_sugestoes = output_dir / f"sugestoes_importacao_exportacao_2024_{timestamp}.csv"
    df_sugestoes.to_csv(arquivo_sugestoes, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_sugestoes.name}")
    
    # Salvar Excel completo
    arquivo_excel = output_dir / f"base_completa_empresas_2024_{timestamp}.xlsx"
    with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
        df_empresas.to_excel(writer, sheet_name='Empresas', index=False)
        df_analise_ncm.to_excel(writer, sheet_name='Análise NCM', index=False)
        df_sugestoes.to_excel(writer, sheet_name='Sugestões', index=False)
    logger.success(f"✅ Arquivo Excel salvo: {arquivo_excel.name}")
    
    # Resumo
    logger.info("="*60)
    logger.info("RESUMO DA ANÁLISE")
    logger.info("="*60)
    logger.info(f"   - Empresas processadas: {len(df_empresas)}")
    logger.info(f"   - Análises NCM: {len(df_analise_ncm)}")
    logger.info(f"   - Sugestões criadas: {len(df_sugestoes)}")
    logger.info(f"   - Faturamento total: USD {df_empresas['faturamento_total_usd'].sum():,.2f}")
    logger.success("✅ Processamento concluído com sucesso!")


if __name__ == "__main__":
    main()

