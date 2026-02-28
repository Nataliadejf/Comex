from pathlib import Path
import os
from sqlalchemy import create_engine, text
from config import settings

# DB URL
db_url = os.getenv('DATABASE_URL')
if not db_url or db_url=='':
    db_path = settings.data_dir / 'database' / 'comex.db'
    db_url = f"sqlite:///{str(db_path.absolute()).replace('\\','/')}"
engine = create_engine(db_url)

with engine.connect() as conn:
    print('Samples valor_fob for VALE S.A. importador')
    rows = conn.execute(text("SELECT valor_fob, typeof(valor_fob) as typ, data_operacao, cnpj_importador FROM operacoes_comex WHERE razao_social_importador = 'VALE S.A.' LIMIT 10")).fetchall()
    for r in rows:
        print(r)
    
    print('\nSamples valor_fob for HIDRAU-like importador')
    rows2 = conn.execute(text("SELECT valor_fob, typeof(valor_fob) as typ, data_operacao, razao_social_importador, cnpj_importador FROM operacoes_comex WHERE razao_social_importador LIKE '%HIDRAU%' LIMIT 10")).fetchall()
    for r in rows2:
        print(r)
print('\nDone')
