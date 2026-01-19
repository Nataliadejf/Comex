"""
Script para processar dados do ComexStat e criar base de empresas com análises e sugestões.
"""
import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db
from database.models import OperacaoComex
from sqlalchemy import func, and_, or_
from data_collector.cnae_analyzer import CNAEAnalyzer
from pathlib import Path

def processar_arquivo_comexstat():
    """Processa o arquivo Excel do ComexStat e cria base de empresas."""
    
    # Caminho do arquivo Excel
    arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
    
    if not arquivo_excel.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_excel}")
        return None
    
    logger.info(f"Lendo arquivo Excel: {arquivo_excel.name}")
    
    # Ler arquivo Excel
    try:
        df = pd.read_excel(arquivo_excel)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        logger.info(f"Colunas: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Erro ao ler arquivo Excel: {e}")
        return None
    
    # Buscar dados de empresas no banco de dados
    logger.info("Buscando dados de empresas no banco de dados...")
    db = next(get_db())
    
    try:
        # Buscar empresas importadoras
        empresas_importadoras = db.query(
            OperacaoComex.razao_social_importador,
            OperacaoComex.cnpj_importador,
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label('total_valor_fob'),
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.group_concat(OperacaoComex.ncm.distinct()).label('ncms'),
            func.group_concat(OperacaoComex.descricao_produto.distinct()).label('produtos')
        ).filter(
            OperacaoComex.tipo_operacao == 'IMPORTACAO',
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.cnpj_importador.isnot(None)
        ).group_by(
            OperacaoComex.cnpj_importador,
            OperacaoComex.razao_social_importador,
            OperacaoComex.uf
        ).all()
        
        # Buscar empresas exportadoras
        empresas_exportadoras = db.query(
            OperacaoComex.razao_social_exportador,
            OperacaoComex.cnpj_exportador,
            OperacaoComex.uf,
            func.sum(OperacaoComex.valor_fob).label('total_valor_fob'),
            func.count(OperacaoComex.id).label('total_operacoes'),
            func.group_concat(OperacaoComex.ncm.distinct()).label('ncms'),
            func.group_concat(OperacaoComex.descricao_produto.distinct()).label('produtos')
        ).filter(
            OperacaoComex.tipo_operacao == 'EXPORTACAO',
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.cnpj_exportador.isnot(None)
        ).group_by(
            OperacaoComex.cnpj_exportador,
            OperacaoComex.razao_social_exportador,
            OperacaoComex.uf
        ).all()
        
        logger.info(f"✅ Encontradas {len(empresas_importadoras)} empresas importadoras")
        logger.info(f"✅ Encontradas {len(empresas_exportadoras)} empresas exportadoras")
        
    except Exception as e:
        logger.error(f"Erro ao buscar empresas no banco: {e}")
        empresas_importadoras = []
        empresas_exportadoras = []
    
    # Criar DataFrame de empresas importadoras
    empresas_imp_list = []
    for emp in empresas_importadoras:
        empresas_imp_list.append({
            'nome_empresa': emp.razao_social_importador,
            'razao_social': emp.razao_social_importador,
            'cnpj': emp.cnpj_importador,
            'tipo': 'IMPORTADORA',
            'uf': emp.uf,
            'valor_fob_total': float(emp.total_valor_fob) if emp.total_valor_fob else 0,
            'total_operacoes': emp.total_operacoes,
            'ncms': emp.ncms if emp.ncms else '',
            'produtos': emp.produtos if emp.produtos else ''
        })
    
    # Criar DataFrame de empresas exportadoras
    empresas_exp_list = []
    for emp in empresas_exportadoras:
        empresas_exp_list.append({
            'nome_empresa': emp.razao_social_exportador,
            'razao_social': emp.razao_social_exportador,
            'cnpj': emp.cnpj_exportador,
            'tipo': 'EXPORTADORA',
            'uf': emp.uf,
            'valor_fob_total': float(emp.total_valor_fob) if emp.total_valor_fob else 0,
            'total_operacoes': emp.total_operacoes,
            'ncms': emp.ncms if emp.ncms else '',
            'produtos': emp.produtos if emp.produtos else ''
        })
    
    # Combinar empresas importadoras e exportadoras
    todas_empresas = empresas_imp_list + empresas_exp_list
    
    if not todas_empresas:
        logger.warning("⚠️ Nenhuma empresa encontrada no banco de dados")
        logger.info("Criando base a partir do arquivo Excel agregado...")
        
        # Processar dados agregados do Excel
        df_empresas = processar_dados_agregados_excel(df)
    else:
        # Criar DataFrame de empresas
        df_empresas = pd.DataFrame(todas_empresas)
        
        # Agrupar por CNPJ (empresas que são tanto importadoras quanto exportadoras)
        df_empresas_agrupadas = df_empresas.groupby('cnpj').agg({
            'nome_empresa': 'first',
            'razao_social': 'first',
            'tipo': lambda x: ', '.join(x.unique()),
            'uf': 'first',
            'valor_fob_total': 'sum',
            'total_operacoes': 'sum',
            'ncms': lambda x: ', '.join(set(','.join(x).split(','))),
            'produtos': lambda x: ', '.join(set(','.join(x).split(',')))
        }).reset_index()
        
        df_empresas = df_empresas_agrupadas
    
    # Ordenar por valor FOB total (maiores primeiro)
    df_empresas = df_empresas.sort_values('valor_fob_total', ascending=False)
    
    # Selecionar top 5000 empresas
    df_empresas_top = df_empresas.head(5000).copy()
    logger.info(f"✅ Top 5000 empresas selecionadas")
    
    # Adicionar informações adicionais - buscar CNAE se disponível
    logger.info("Buscando informações de CNAE...")
    cnae_analyzer = None
    try:
        arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
        if arquivo_cnae.exists():
            cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
            cnae_analyzer.carregar_cnae_excel()
            logger.info("✅ CNAE carregado")
    except Exception as e:
        logger.warning(f"Não foi possível carregar CNAE: {e}")
    
    # Preencher CNAE e endereço
    df_empresas_top['cnae'] = ''
    df_empresas_top['endereco'] = ''
    df_empresas_top['classificacao_cnae'] = ''
    
    if cnae_analyzer:
        for idx, empresa in df_empresas_top.iterrows():
            cnpj = str(empresa['cnpj']).replace('.', '').replace('/', '').replace('-', '')
            dados_cnae = cnae_analyzer.buscar_cnae_empresa(cnpj)
            if dados_cnae:
                df_empresas_top.at[idx, 'cnae'] = dados_cnae.get('cnae', '')
                df_empresas_top.at[idx, 'classificacao_cnae'] = dados_cnae.get('classificacao', '')
                df_empresas_top.at[idx, 'endereco'] = dados_cnae.get('endereco', '')
    
    # Processar NCMs mais frequentes por empresa
    logger.info("Processando NCMs mais frequentes por empresa...")
    df_empresas_top['ncms_principais'] = df_empresas_top['ncms'].apply(
        lambda x: ', '.join(str(x).split(',')[:10]) if pd.notna(x) and x else ''
    )
    
    # Criar análise de produtos mais importados/exportados
    logger.info("Criando análise de produtos...")
    df_produtos_analise = criar_analise_produtos(df, df_empresas_top)
    
    # Criar base de sugestões
    logger.info("Criando base de sugestões...")
    df_sugestoes = criar_base_sugestoes(df_empresas_top, df_produtos_analise)
    
    # Criar tabela de relacionamento
    logger.info("Criando tabela de relacionamento...")
    df_relacionamento = criar_tabela_relacionamento(df_empresas_top, df_produtos_analise, df)
    
    # Salvar arquivos
    output_dir = backend_dir.parent / "comex_data" / "comexstat_csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar empresas principais
    arquivo_empresas = output_dir / f"empresas_principais_top5000_{timestamp}.csv"
    df_empresas_top.to_csv(arquivo_empresas, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_empresas.name}")
    
    # Salvar análise de produtos
    arquivo_produtos = output_dir / f"analise_produtos_{timestamp}.csv"
    df_produtos_analise.to_csv(arquivo_produtos, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_produtos.name}")
    
    # Salvar sugestões
    arquivo_sugestoes = output_dir / f"sugestoes_empresas_{timestamp}.csv"
    df_sugestoes.to_csv(arquivo_sugestoes, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_sugestoes.name}")
    
    # Salvar relacionamento
    arquivo_relacionamento = output_dir / f"relacionamento_empresas_produtos_{timestamp}.csv"
    df_relacionamento.to_csv(arquivo_relacionamento, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo salvo: {arquivo_relacionamento.name}")
    
    # Salvar também em Excel
    arquivo_excel_completo = output_dir / f"base_empresas_completa_{timestamp}.xlsx"
    with pd.ExcelWriter(arquivo_excel_completo, engine='openpyxl') as writer:
        df_empresas_top.to_excel(writer, sheet_name='Empresas Top 5000', index=False)
        df_produtos_analise.to_excel(writer, sheet_name='Análise Produtos', index=False)
        df_sugestoes.to_excel(writer, sheet_name='Sugestões', index=False)
        df_relacionamento.to_excel(writer, sheet_name='Relacionamento', index=False)
    logger.success(f"✅ Arquivo Excel completo salvo: {arquivo_excel_completo.name}")
    
    return {
        'empresas': df_empresas_top,
        'produtos': df_produtos_analise,
        'sugestoes': df_sugestoes,
        'relacionamento': df_relacionamento
    }


def processar_dados_agregados_excel(df):
    """Processa dados agregados do Excel quando não há dados de empresas no banco."""
    logger.info("Processando dados agregados do Excel...")
    
    # Criar empresas fictícias baseadas nos dados agregados
    empresas_list = []
    
    # Agrupar por UF, NCM e outros campos para criar empresas representativas mais detalhadas
    if 'UF do Produto' in df.columns and 'Código NCM' in df.columns:
        # Agrupar por múltiplos campos para criar empresas mais realistas
        campos_agrupamento = ['UF do Produto', 'Código NCM', 'Países', 'Via']
        df_agrupado = df.groupby(campos_agrupamento).agg({
            'Exportação - 2025 - Valor US$ FOB': 'sum',
            'Importação - 2025 - Valor US$ FOB': 'sum',
            'Descrição NCM': 'first'
        }).reset_index()
        
        contador_exp = 0
        contador_imp = 0
        
        for idx, row in df_agrupado.iterrows():
            uf = str(row['UF do Produto']) if pd.notna(row['UF do Produto']) else 'BR'
            ncm = str(row['Código NCM'])
            pais = str(row['Países']) if pd.notna(row['Países']) else 'Vários'
            via = str(row['Via']) if pd.notna(row['Via']) else 'Várias'
            descricao = str(row['Descrição NCM']) if pd.notna(row['Descrição NCM']) else ''
            
            valor_exp = float(row['Exportação - 2025 - Valor US$ FOB']) if pd.notna(row['Exportação - 2025 - Valor US$ FOB']) else 0
            valor_imp = float(row['Importação - 2025 - Valor US$ FOB']) if pd.notna(row['Importação - 2025 - Valor US$ FOB']) else 0
            
            if valor_exp > 1000:  # Filtrar apenas valores significativos
                empresas_list.append({
                    'nome_empresa': f'Empresa Exportadora - {uf}',
                    'razao_social': f'Empresa Exportadora - {uf} - {descricao[:50]}',
                    'cnpj': f'0000000000000{contador_exp:05d}',
                    'tipo': 'EXPORTADORA',
                    'uf': uf,
                    'valor_fob_total': valor_exp,
                    'total_operacoes': 1,
                    'ncms': ncm,
                    'produtos': descricao[:200]
                })
                contador_exp += 1
            
            if valor_imp > 1000:  # Filtrar apenas valores significativos
                empresas_list.append({
                    'nome_empresa': f'Empresa Importadora - {uf}',
                    'razao_social': f'Empresa Importadora - {uf} - {descricao[:50]}',
                    'cnpj': f'0000000000001{contador_imp:05d}',
                    'tipo': 'IMPORTADORA',
                    'uf': uf,
                    'valor_fob_total': valor_imp,
                    'total_operacoes': 1,
                    'ncms': ncm,
                    'produtos': descricao[:200]
                })
                contador_imp += 1
    
    return pd.DataFrame(empresas_list)


def criar_analise_produtos(df_excel, df_empresas):
    """Cria análise de produtos mais importados/exportados."""
    produtos_list = []
    
    # Analisar produtos do Excel
    if 'Código NCM' in df_excel.columns:
        df_produtos = df_excel.groupby('Código NCM').agg({
            'Descrição NCM': 'first',
            'Exportação - 2025 - Valor US$ FOB': 'sum',
            'Importação - 2025 - Valor US$ FOB': 'sum',
            'UF do Produto': lambda x: ', '.join(x.unique()[:5])
        }).reset_index()
        
        for idx, row in df_produtos.iterrows():
            valor_exp = float(row['Exportação - 2025 - Valor US$ FOB']) if pd.notna(row['Exportação - 2025 - Valor US$ FOB']) else 0
            valor_imp = float(row['Importação - 2025 - Valor US$ FOB']) if pd.notna(row['Importação - 2025 - Valor US$ FOB']) else 0
            
            produtos_list.append({
                'ncm': str(row['Código NCM']),
                'descricao': row['Descrição NCM'] if pd.notna(row['Descrição NCM']) else '',
                'valor_exportacao': valor_exp,
                'valor_importacao': valor_imp,
                'valor_total': valor_exp + valor_imp,
                'ufs_principais': row['UF do Produto'] if pd.notna(row['UF do Produto']) else ''
            })
    
    df_produtos_analise = pd.DataFrame(produtos_list)
    df_produtos_analise = df_produtos_analise.sort_values('valor_total', ascending=False)
    
    return df_produtos_analise


def criar_base_sugestoes(df_empresas, df_produtos):
    """Cria base de sugestões do que empresas podem importar/exportar."""
    sugestoes_list = []
    
    # Para cada empresa, sugerir produtos similares aos que já trabalha
    for idx, empresa in df_empresas.iterrows():
        ncms_empresa = str(empresa['ncms']).split(',') if pd.notna(empresa['ncms']) else []
        tipo_empresa = empresa['tipo']
        
        # Buscar produtos similares (mesmo código NCM inicial de 4 dígitos)
        ncms_principais = [ncm[:4] for ncm in ncms_empresa if len(ncm) >= 4][:5]
        
        for ncm_prefixo in ncms_principais:
            produtos_similares = df_produtos[df_produtos['ncm'].str.startswith(ncm_prefixo, na=False)]
            
            for _, produto in produtos_similares.head(5).iterrows():
                sugestoes_list.append({
                    'cnpj': empresa['cnpj'],
                    'nome_empresa': empresa['nome_empresa'],
                    'tipo_empresa': tipo_empresa,
                    'ncm_sugerido': produto['ncm'],
                    'descricao_produto': produto['descricao'],
                    'valor_potencial_exportacao': produto['valor_exportacao'] if tipo_empresa == 'EXPORTADORA' else 0,
                    'valor_potencial_importacao': produto['valor_importacao'] if tipo_empresa == 'IMPORTADORA' else 0,
                    'razao_sugestao': f'Produto similar ao NCM {ncm_prefixo} que a empresa já trabalha'
                })
    
    return pd.DataFrame(sugestoes_list)


def criar_tabela_relacionamento(df_empresas, df_produtos, df_excel):
    """Cria tabela relacionando empresas, produtos e dados do Excel."""
    relacionamento_list = []
    
    # Relacionar empresas com produtos do Excel
    for idx, empresa in df_empresas.head(100).iterrows():  # Limitar para não ficar muito grande
        ncms_empresa = str(empresa['ncms']).split(',') if pd.notna(empresa['ncms']) else []
        
        for ncm in ncms_empresa[:10]:  # Limitar a 10 NCMs por empresa
            ncm_clean = str(ncm).strip()
            if not ncm_clean:
                continue
            
            # Buscar no Excel
            produtos_excel = df_excel[df_excel['Código NCM'].astype(str) == ncm_clean]
            
            for _, produto_excel in produtos_excel.head(5).iterrows():
                relacionamento_list.append({
                    'cnpj': empresa['cnpj'],
                    'nome_empresa': empresa['nome_empresa'],
                    'tipo_empresa': empresa['tipo'],
                    'uf': empresa['uf'],
                    'ncm': ncm_clean,
                    'descricao_ncm': produto_excel.get('Descrição NCM', ''),
                    'pais': produto_excel.get('Países', ''),
                    'bloco_economico': produto_excel.get('Bloco Econômico', ''),
                    'via': produto_excel.get('Via', ''),
                    'valor_exportacao': produto_excel.get('Exportação - 2025 - Valor US$ FOB', 0),
                    'valor_importacao': produto_excel.get('Importação - 2025 - Valor US$ FOB', 0),
                    'valor_fob_empresa': empresa['valor_fob_total']
                })
    
    return pd.DataFrame(relacionamento_list)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("PROCESSAMENTO DE EMPRESAS COMEXSTAT")
    logger.info("="*60)
    
    resultado = processar_arquivo_comexstat()
    
    if resultado:
        logger.success("✅ Processamento concluído com sucesso!")
        logger.info(f"   - Empresas processadas: {len(resultado['empresas'])}")
        logger.info(f"   - Produtos analisados: {len(resultado['produtos'])}")
        logger.info(f"   - Sugestões criadas: {len(resultado['sugestoes'])}")
        logger.info(f"   - Relacionamentos: {len(resultado['relacionamento'])}")
    else:
        logger.error("❌ Erro no processamento")

