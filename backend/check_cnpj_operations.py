#!/usr/bin/env python3
"""
Checa CNPJ/autocomplete, operações por estado (uf) e top NCMs para empresas exemplo (VALE, HIDRAU).
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

print(f"Conectando ao DB: {db_url[:120]}")
engine = create_engine(db_url)

companies = [
    ('VALE S.A.', 'VALE'),
    ('HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA', 'HIDRAU')
]

with engine.connect() as conn:
    for full_name, short in companies:
        print('\n' + '='*80)
        print(f"Empresa: {full_name}  (pattern: %{short}%)")
        print('='*80)

        # Try to find matching empresas table (official registry) by nome
        try:
            q_emp = text("SELECT id, razao_social, cnpj FROM empresas WHERE razao_social LIKE :pat LIMIT 20")
            df_emp = pd.read_sql(q_emp, conn, params={'pat': f"%{short}%"})
            if not df_emp.empty:
                print('\nPossíveis empresas na tabela `empresas` (amostra):')
                print(df_emp.to_string(index=False))
            else:
                print('\nNenhuma correspondência encontrada na tabela `empresas` (ou tabela ausente).')
        except Exception:
            print('\nTabela `empresas` não disponível ou erro ao consultar.')

        # Distinct CNPJs from operacoes_comex matching pattern
        q_cnpj = text("SELECT cnpj_importador as cnpj, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE razao_social_importador LIKE :pat GROUP BY cnpj_importador ORDER BY cnt DESC LIMIT 10")
        df_cnpj = pd.read_sql(q_cnpj, conn, params={'pat': f"%{short}%"})
        if df_cnpj.empty:
            print('\nNenhum CNPJ encontrado em `operacoes_comex` para esse padrão (importador).')
            # try exportador
            q_cnpj2 = text("SELECT cnpj_exportador as cnpj, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE razao_social_exportador LIKE :pat GROUP BY cnpj_exportador ORDER BY cnt DESC LIMIT 10")
            df_cnpj2 = pd.read_sql(q_cnpj2, conn, params={'pat': f"%{short}%"})
            if not df_cnpj2.empty:
                print('\nTop CNPJs como exportador:')
                print(df_cnpj2.to_string(index=False))
            continue

        print('\nTop CNPJs (importador) encontrados:')
        print(df_cnpj.to_string(index=False))

        # Para cada CNPJ top, checar operações por UF e por NCM
        for idx, row in df_cnpj.iterrows():
            cnpj = row['cnpj']
            print('\n' + '-'*60)
            print(f"Detalhes para CNPJ: {cnpj}  (ops: {row['cnt']}, valor_milhoes: {row['valor_milhoes']})")

            # operações por UF
            q_uf = text("SELECT uf, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE cnpj_importador = :cnpj GROUP BY uf ORDER BY cnt DESC")
            df_uf = pd.read_sql(q_uf, conn, params={'cnpj': cnpj})
            if not df_uf.empty:
                print('\nOperações por UF:')
                print(df_uf.to_string(index=False))
            else:
                print('\nNenhuma operação com esse CNPJ por UF encontrada (importador).')

            # top NCMs
            q_ncm = text("SELECT ncm, COUNT(*) as cnt, ROUND(SUM(CAST(valor_fob AS REAL))/1000000,2) as valor_milhoes FROM operacoes_comex WHERE cnpj_importador = :cnpj GROUP BY ncm ORDER BY cnt DESC LIMIT 10")
            df_ncm = pd.read_sql(q_ncm, conn, params={'cnpj': cnpj})
            if not df_ncm.empty:
                print('\nTop NCMs para esse CNPJ:')
                print(df_ncm.to_string(index=False))
            else:
                print('\nNenhum NCM registrado para esse CNPJ.')

print('\nConcluído')
