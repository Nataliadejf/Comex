#!/usr/bin/env python3
"""
Verifica se VALE e HIDRAU aparecem no arquivo Excel original com dados válidos
"""
import os
import pandas as pd

# Caminho do arquivo Excel
EXCEL_PATH = r'C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx'

print("="*100)
print(f"Procurando VALE e HIDRAU no arquivo: {os.path.basename(EXCEL_PATH)}")
print("="*100)

if not os.path.exists(EXCEL_PATH):
    print(f"\n❌ Arquivo NÃO ENCONTRADO: {EXCEL_PATH}")
    print("\nProcurando alternativas...")
    
    # Procurar por arquivos Excel/CSV no diretório
    import glob
    excel_dir = os.path.dirname(EXCEL_PATH)
    
    if os.path.exists(excel_dir):
        print(f"\nArquivos encontrados em {excel_dir}:")
        for f in glob.glob(os.path.join(excel_dir, "*.*")):
            if f.endswith(('.xlsx', '.csv', '.xls')):
                print(f"  - {os.path.basename(f)}")
    else:
        print(f"Diretório {excel_dir} também não existe.")
    
    exit(1)

try:
    print(f"\n📂 Carregando arquivo... {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    print(f"✓ Arquivo carregado com {len(df):,} linhas e {len(df.columns)} colunas")
    print(f"  Colunas: {list(df.columns)}")
    
    # Procurar VALE
    print("\n" + "="*100)
    print("🔍 VALE")
    print("="*100)
    vale_rows = df[
        (df.apply(lambda row: row.astype(str).str.contains('VALE', case=False).any(), axis=1))
    ]
    print(f"\nRegistros contendo 'VALE': {len(vale_rows)}")
    if not vale_rows.empty:
        print("\nAmostra (primeiras 5):")
        print(vale_rows.head().to_string())
        
        # Tentar sumarizar por coluna
        for col in ['Importação - 2025 - Valor US$ FOB', 'Exportação - 2025 - Valor US$ FOB', 'UF do Produto']:
            if col in vale_rows.columns:
                print(f"\n{col}:")
                print(vale_rows[col].value_counts().head(10))
    else:
        print("❌ Nenhum registro para VALE no arquivo")
    
    # Procurar HIDRAU
    print("\n" + "="*100)
    print("🔍 HIDRAU")
    print("="*100)
    hidrau_rows = df[
        (df.apply(lambda row: row.astype(str).str.contains('HIDRAU', case=False).any(), axis=1))
    ]
    print(f"\nRegistros contendo 'HIDRAU': {len(hidrau_rows)}")
    if not hidrau_rows.empty:
        print("\nAmostra (primeiras 5):")
        print(hidrau_rows.head().to_string())
        
        # Tentar sumarizar por coluna
        for col in ['Importação - 2025 - Valor US$ FOB', 'Exportação - 2025 - Valor US$ FOB', 'UF do Produto']:
            if col in hidrau_rows.columns:
                print(f"\n{col}:")
                print(hidrau_rows[col].value_counts().head(10))
    else:
        print("❌ Nenhum registro para HIDRAU no arquivo")

except Exception as e:
    print(f"\n❌ Erro ao processar arquivo: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*100)
