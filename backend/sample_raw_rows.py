#!/usr/bin/env python3
"""
Amostra de linhas brutas para um CNPJ específico
"""
from pathlib import Path
import os
from sqlalchemy import create_engine, text
import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import settings

# DB URL
db_url = os.getenv('DATABASE_URL')
if not db_url or db_url == '':
    db_path = settings.data_dir / 'database' / 'comex.db'
    db_url = f"sqlite:///{str(db_path.absolute()).replace('\\','/')}"

engine = create_engine(db_url)

# CNPJs exemplo (de VALE e HIDRAU)
cnpjs_teste = [
    ('33592510037821', 'VALE'),
    ('19502657000185', 'HIDRAU')
]

with engine.connect() as conn:
    for cnpj, empresa in cnpjs_teste:
        print('\n' + '='*100)
        print(f"Amostra para CNPJ {cnpj} ({empresa})")
        print('='*100)
        
        # Pegando as primeiras 5 linhas
        q = text("SELECT * FROM operacoes_comex WHERE cnpj_importador = :cnpj LIMIT 5")
        df = pd.read_sql(q, conn, params={'cnpj': cnpj})
        
        if df.empty:
            print(f"Nenhum registro para CNPJ {cnpj}")
            continue
        
        print(f"\nTotal de colunas: {len(df.columns)}")
        print(f"Nomes das colunas: {list(df.columns)}\n")
        
        # Mostrar cada coluna em detalhe para cada linha
        for idx, row in df.iterrows():
            print(f"\n--- Linha {idx + 1} ---")
            for col in df.columns:
                val = row[col]
                val_type = type(val).__name__
                print(f"  {col}: {repr(val)} (tipo: {val_type})")

print('\n' + '='*100)
print("Conclusão: Inspecione acima tipo de dado e conteúdo real de ncm, valor_fob, etc.")
print('='*100)
