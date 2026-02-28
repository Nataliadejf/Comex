#!/usr/bin/env python3
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

companies = [
    ('VALE S.A.', 'VALE'),
    ('HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA', 'HIDRAU')
]

for full_name, short in companies:
    print('\n' + '='*80)
    print(f"Checking company exact name: {full_name} and pattern '{short}'")
    print('='*80)
    with engine.connect() as conn:
        # exact matches
        q1 = text("SELECT COUNT(*) as cnt FROM operacoes_comex WHERE razao_social_importador = :name OR razao_social_exportador = :name")
        r1 = conn.execute(q1, {'name': full_name}).scalar()
        print(f"Exact name matches (importador/exportador) for '{full_name}': {r1}")

        # LIKE pattern
        q2 = text("SELECT COUNT(*) as cnt FROM operacoes_comex WHERE razao_social_importador LIKE :pat OR razao_social_exportador LIKE :pat")
        r2 = conn.execute(q2, {'pat': f"%{short}%"}).scalar()
        print(f"LIKE '%{short}%' matches: {r2}")

        # distinct importer names with pattern
        q3 = text("SELECT razao_social_importador as nome, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE razao_social_importador LIKE :pat GROUP BY razao_social_importador ORDER BY cnt DESC LIMIT 20")
        df3 = pd.read_sql(q3, conn, params={'pat': f"%{short}%"})
        if not df3.empty:
            print('\nTop importer names matching pattern:')
            print(df3.to_string(index=False))
        else:
            print('\nNo importer names matching pattern found')

        # group by cnpj_importador
        q4 = text("SELECT cnpj_importador as cnpj, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE razao_social_importador LIKE :pat GROUP BY cnpj_importador ORDER BY cnt DESC LIMIT 20")
        df4 = pd.read_sql(q4, conn, params={'pat': f"%{short}%"})
        if not df4.empty:
            print('\nTop cnpjs for importer names matching pattern:')
            print(df4.to_string(index=False))
        else:
            print('\nNo cnpj data for these importer names')

print('\nDone')
