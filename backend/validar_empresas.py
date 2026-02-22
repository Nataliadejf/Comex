#!/usr/bin/env python3
"""
Validar se VALE e HIDRAU existem em operacoes_comex
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import settings
import os

# Conectar ao banco
db_url = os.getenv("DATABASE_URL")
if not db_url or db_url == "":
    db_path = settings.data_dir / "database" / "comex.db"
    path_str = str(db_path.absolute()).replace("\\", "/")
    db_url = f"sqlite:///{path_str}"

engine = create_engine(db_url)

print("=" * 100)
print("🔍 VALIDAÇÃO: VALE e HIDRAU em operacoes_comex")
print("=" * 100)

# Query 1: Procurar VALE
query_vale = """
SELECT 
    'Importador' as tipo,
    COUNT(*) as qtd_registros,
    MIN(data_operacao) as primeira_data,
    MAX(data_operacao) as ultima_data,
    ROUND(SUM(CAST(valor_fob AS REAL)) / 1000000, 2) as valor_milhoes
FROM operacoes_comex
WHERE razao_social_importador LIKE '%VALE%'
UNION ALL
SELECT 
    'Exportador' as tipo,
    COUNT(*) as qtd_registros,
    MIN(data_operacao) as primeira_data,
    MAX(data_operacao) as ultima_data,
    ROUND(SUM(CAST(valor_fob AS REAL)) / 1000000, 2) as valor_milhoes
FROM operacoes_comex
WHERE razao_social_exportador LIKE '%VALE%'
"""

print("\n📊 VALE - Registros Encontrados:\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query_vale), conn)
        if len(result) > 0:
            print(result.to_string())
        else:
            print("❌ Nenhum registro encontrado com VALE")
except Exception as e:
    print(f"❌ Erro: {e}")

# Query 2: Procurar HIDRAU
query_hidrau = """
SELECT 
    'Importador' as tipo,
    COUNT(*) as qtd_registros,
    MIN(data_operacao) as primeira_data,
    MAX(data_operacao) as ultima_data,
    ROUND(SUM(CAST(valor_fob AS REAL)) / 1000000, 2) as valor_milhoes
FROM operacoes_comex
WHERE razao_social_importador LIKE '%HIDRAU%'
UNION ALL
SELECT 
    'Exportador' as tipo,
    COUNT(*) as qtd_registros,
    MIN(data_operacao) as primeira_data,
    MAX(data_operacao) as ultima_data,
    ROUND(SUM(CAST(valor_fob AS REAL)) / 1000000, 2) as valor_milhoes
FROM operacoes_comex
WHERE razao_social_exportador LIKE '%HIDRAU%'
"""

print("\n\n📊 HIDRAU - Registros Encontrados:\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query_hidrau), conn)
        if len(result) > 0:
            print(result.to_string())
        else:
            print("❌ Nenhum registro encontrado com HIDRAU")
except Exception as e:
    print(f"❌ Erro: {e}")

# Query 3: Nomes únicos que contêm VALE
query_nomes_vale = """
SELECT DISTINCT razao_social_importador as empresas
FROM operacoes_comex
WHERE razao_social_importador LIKE '%VALE%'
LIMIT 10
"""

print("\n\n📋 Nomes com 'VALE' como IMPORTADOR:\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query_nomes_vale), conn)
        if len(result) > 0:
            for idx, row in result.iterrows():
                print(f"  - {row['empresas']}")
        else:
            print("❌ Nenhum encontrado")
except Exception as e:
    print(f"❌ Erro: {e}")

# Query 4: Nomes únicos que contêm HIDRAU
query_nomes_hidrau = """
SELECT DISTINCT razao_social_importador as empresas
FROM operacoes_comex
WHERE razao_social_importador LIKE '%HIDRAU%'
LIMIT 10
"""

print("\n\n📋 Nomes com 'HIDRAU' como IMPORTADOR:\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query_nomes_hidrau), conn)
        if len(result) > 0:
            for idx, row in result.iterrows():
                print(f"  - {row['empresas']}")
        else:
            print("❌ Nenhum encontrado")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "=" * 100)
print("✅ Validação concluída")
print("=" * 100)
