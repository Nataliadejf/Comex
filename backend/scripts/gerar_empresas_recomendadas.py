"""
Script principal end-to-end para gerar tabela de empresas recomendadas.
Orquestra todo o fluxo: coleta -> scoring -> cruzamento -> geração de tabela.
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

from data_collector.empresa_data_collector import EmpresaDataCollector
from data_collector.empresa_scoring import EmpresaScoring
from data_collector.empresa_cruzamento import EmpresaCruzamento


def gerar_tabela_final(relacionamentos: list, sugestoes: list) -> pd.DataFrame:
    """
    Gera tabela final padronizada empresas_recomendadas_comex.
    
    Args:
        relacionamentos: Lista de relacionamentos empresa-NCM
        sugestoes: Lista de sugestões geradas
        
    Returns:
        DataFrame com tabela final padronizada
    """
    logger.info("Gerando tabela final padronizada...")
    
    # Combinar relacionamentos e sugestões
    df_rel = pd.DataFrame(relacionamentos)
    df_sug = pd.DataFrame(sugestoes)
    
    # Criar tabela consolidada
    tabela_final = []
    
    # Processar relacionamentos
    for _, row in df_rel.iterrows():
        # Converter USD para BRL (taxa aproximada 5.0)
        valor_imp_brl = row.get('valor_importacao_usd', 0) * 5.0
        valor_exp_brl = row.get('valor_exportacao_usd', 0) * 5.0
        
        # Determinar sugestão baseado no tipo de operação
        if row['tipo_operacao'] == 'IMPORTACAO':
            sugestao = 'FORNECEDOR_POTENCIAL'
        else:
            sugestao = 'CLIENTE_POTENCIAL'
        
        tabela_final.append({
            'CNPJ': row['cnpj'],
            'Razão Social': row['razao_social'],
            'Nome Fantasia': row.get('nome_fantasia', ''),
            'CNAE': row.get('cnae', ''),
            'Estado': row.get('estado', ''),
            'Endereço': row.get('endereco', ''),
            'NCM Relacionado': row['ncm'],
            'Descrição NCM': row.get('descricao_ncm', ''),
            'Importado (R$)': valor_imp_brl,
            'Exportado (R$)': valor_exp_brl,
            'Capital Social': row.get('capital_social'),
            'Funcionários (Estimado)': row.get('funcionarios_estimado'),
            'Peso Participação (0-100)': row.get('peso_participacao', 0),
            'Sugestão': sugestao,
            'Dados Estimados': 'SIM' if row.get('dados_estimados', True) else 'NÃO'
        })
    
    # Adicionar sugestões específicas
    for _, row in df_sug.iterrows():
        valor_imp_brl = row.get('valor_importacao_usd', 0) * 5.0
        valor_exp_brl = row.get('valor_exportacao_usd', 0) * 5.0
        
        tabela_final.append({
            'CNPJ': row['cnpj'],
            'Razão Social': row['razao_social'],
            'Nome Fantasia': row.get('nome_fantasia', ''),
            'CNAE': row.get('cnae', ''),
            'Estado': row.get('estado', ''),
            'Endereço': row.get('endereco', ''),
            'NCM Relacionado': row['ncm'],
            'Descrição NCM': row.get('descricao_ncm', ''),
            'Importado (R$)': valor_imp_brl,
            'Exportado (R$)': valor_exp_brl,
            'Capital Social': row.get('capital_social'),
            'Funcionários (Estimado)': row.get('funcionarios_estimado'),
            'Peso Participação (0-100)': row.get('peso_participacao', 0),
            'Sugestão': row.get('sugestao', ''),
            'Dados Estimados': 'SIM' if row.get('dados_estimados', True) else 'NÃO'
        })
    
    df_final = pd.DataFrame(tabela_final)
    
    # Remover duplicatas (mesmo CNPJ + NCM)
    df_final = df_final.drop_duplicates(subset=['CNPJ', 'NCM Relacionado'])
    
    # Ordenar por Peso Participação (maior primeiro)
    df_final = df_final.sort_values('Peso Participação (0-100)', ascending=False)
    
    logger.info(f"✅ Tabela final gerada: {len(df_final)} registros")
    
    return df_final


def main():
    """Função principal end-to-end."""
    logger.info("="*80)
    logger.info("GERAÇÃO DE EMPRESAS RECOMENDADAS - FLUXO COMPLETO")
    logger.info("="*80)
    
    # ETAPA 1: COLETA DE DADOS
    logger.info("\n" + "="*80)
    logger.info("ETAPA 1: COLETA DE DADOS")
    logger.info("="*80)
    
    coletor = EmpresaDataCollector()
    empresas = coletor.coletar_empresas(limite=5000)
    
    if not empresas:
        logger.error("❌ Nenhuma empresa coletada. Verifique a base de dados.")
        return
    
    logger.info(f"✅ {len(empresas)} empresas coletadas")
    
    # ETAPA 2: SCORING (PESO_PARTICIPACAO)
    logger.info("\n" + "="*80)
    logger.info("ETAPA 2: CÁLCULO DE SCORE (PESO_PARTICIPACAO)")
    logger.info("="*80)
    
    scoring = EmpresaScoring()
    empresas_com_score = scoring.calcular_peso_participacao(empresas)
    
    # ETAPA 3: CRUZAMENTO COM BASE INTERNA
    logger.info("\n" + "="*80)
    logger.info("ETAPA 3: CRUZAMENTO COM BASE INTERNA COMEX")
    logger.info("="*80)
    
    cruzamento = EmpresaCruzamento()
    relacionamentos = cruzamento.relacionar_empresas_ncms(empresas_com_score)
    
    # ETAPA 4: GERAÇÃO DE SUGESTÕES
    logger.info("\n" + "="*80)
    logger.info("ETAPA 4: GERAÇÃO DE SUGESTÕES")
    logger.info("="*80)
    
    sugestoes = cruzamento.gerar_sugestoes(relacionamentos)
    
    # ETAPA 5: GERAÇÃO DA TABELA FINAL
    logger.info("\n" + "="*80)
    logger.info("ETAPA 5: GERAÇÃO DA TABELA FINAL")
    logger.info("="*80)
    
    df_tabela_final = gerar_tabela_final(relacionamentos, sugestoes)
    
    # ETAPA 6: SALVAR ARQUIVO
    logger.info("\n" + "="*80)
    logger.info("ETAPA 6: SALVANDO ARQUIVO")
    logger.info("="*80)
    
    # Criar diretório se não existir
    output_dir = backend_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    arquivo_excel = output_dir / "empresas_recomendadas.xlsx"
    
    # Salvar em Excel com formatação
    with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
        df_tabela_final.to_excel(writer, sheet_name='Empresas Recomendadas', index=False)
        
        # Ajustar largura das colunas
        worksheet = writer.sheets['Empresas Recomendadas']
        for idx, col in enumerate(df_tabela_final.columns):
            max_length = max(
                df_tabela_final[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    logger.success(f"✅ Arquivo salvo: {arquivo_excel.absolute()}")
    
    # Salvar também em CSV
    arquivo_csv = output_dir / "empresas_recomendadas.csv"
    df_tabela_final.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
    logger.success(f"✅ Arquivo CSV salvo: {arquivo_csv.absolute()}")
    
    # RESUMO FINAL
    logger.info("\n" + "="*80)
    logger.info("RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"   - Empresas coletadas: {len(empresas)}")
    logger.info(f"   - Relacionamentos empresa-NCM: {len(relacionamentos)}")
    logger.info(f"   - Sugestões geradas: {len(sugestoes)}")
    logger.info(f"   - Registros na tabela final: {len(df_tabela_final)}")
    logger.info(f"   - Arquivo Excel: {arquivo_excel.name}")
    logger.info(f"   - Arquivo CSV: {arquivo_csv.name}")
    
    # Estatísticas
    logger.info("\nEstatísticas:")
    logger.info(f"   - Empresas com dados completos: {len(df_tabela_final[df_tabela_final['Dados Estimados'] == 'NÃO'])}")
    logger.info(f"   - Empresas com dados estimados: {len(df_tabela_final[df_tabela_final['Dados Estimados'] == 'SIM'])}")
    logger.info(f"   - Valor total importado (R$): {df_tabela_final['Importado (R$)'].sum():,.2f}")
    logger.info(f"   - Valor total exportado (R$): {df_tabela_final['Exportado (R$)'].sum():,.2f}")
    logger.info(f"   - Peso participação médio: {df_tabela_final['Peso Participação (0-100)'].mean():.2f}")
    
    logger.success("\n✅ Processamento concluído com sucesso!")


if __name__ == "__main__":
    main()


