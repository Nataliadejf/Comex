#!/usr/bin/env python3
"""
Script de diagnóstico para SQLite - compatível com sintaxe SQLite
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
import pandas as pd

# Importar configurações do projeto
sys.path.insert(0, str(Path(__file__).parent))
from config import settings

# Determinando DB URL
db_url = os.getenv("DATABASE_URL")
if not db_url or db_url == "":
    db_path = settings.data_dir / "database" / "comex.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    path_str = str(db_path.absolute()).replace("\\", "/")
    db_url = f"sqlite:///{path_str}"

print(f"📊 Conectando ao banco: {db_url[:80]}...")

engine = create_engine(db_url)

# Step 1: Verificar quais tabelas existem
print("\n" + "=" * 80)
print("1️⃣  TABELAS DISPONÍVEIS NO BANCO")
print("=" * 80)

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nTotal de tabelas: {len(tables)}\n")

for table in tables:
    with engine.connect() as conn:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            cols = inspector.get_columns(table)
            col_names = ", ".join([c['name'] for c in cols])
            print(f"✓ {table}: {count:,} registros")
            print(f"  Colunas: {col_names[:100]}...")
        except Exception as e:
            print(f"✗ {table}: Erro - {str(e)[:50]}")

# Step 2: Verificar se operacao_comex existe
op_comex_exists = 'operacao_comex' in tables

if op_comex_exists:
    print("\n" + "=" * 80)
    print("2️⃣  ANÁLISE: Dados de Importação/Exportação")
    print("=" * 80)
    
    # Query compatível com SQLite
    query = """
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT id_empresa) as total_empresas,
        COUNT(DISTINCT ncm) as total_ncms,
        MIN(data_operacao) as primeira_data,
        MAX(data_operacao) as ultima_data
    FROM operacao_comex
    """
    
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query), conn)
        print("\n" + result.to_string())
    
    # Query para empresas com mais operações
    query2 = """
    SELECT 
        ec.razao_social,
        COUNT(*) as total_ops,
        COUNT(DISTINCT o.tipo_operacao) as tipos_operacao,
        COUNT(DISTINCT o.ncm) as ncms_unicos
    FROM operacao_comex o
    LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
    GROUP BY o.id_empresa, ec.razao_social
    ORDER BY total_ops DESC
    LIMIT 20
    """
    
    print("\n\n3️⃣ TOP 20 EMPRESAS (por número de operações)\n")
    try:
        with engine.connect() as conn:
            result = pd.read_sql_query(text(query2), conn)
            print(result.to_string())
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Query específica para VALE e HIDRAU
    query3 = """
    SELECT 
        ec.razao_social,
        o.tipo_operacao,
        COUNT(*) as qtd,
        ROUND(SUM(CAST(o.valor_fob AS REAL)) / 1000000, 2) as valor_milhoes
    FROM operacao_comex o
    LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
    WHERE ec.razao_social LIKE '%VALE%' OR ec.razao_social LIKE '%HIDRAU%'
    GROUP BY o.id_empresa, ec.razao_social, o.tipo_operacao
    ORDER BY ec.razao_social, o.tipo_operacao
    """
    
    print("\n\n4️⃣  COMPARAÇÃO: VALE vs HIDRAU\n")
    try:
        with engine.connect() as conn:
            result = pd.read_sql_query(text(query3), conn)
            if len(result) > 0:
                print(result.to_string())
            else:
                print("❌ Nenhum registro encontrado para VALE ou HIDRAU")
    except Exception as e:
        print(f"❌ Erro: {e}")

else:
    print("\n⚠️  A tabela 'operacao_comex' NÃO EXISTE no banco de dados!")
    print("\nIsso explica por que os valores são iguais - não há dados de importação/exportação carregados!")
    print("\n📋 PRÓXIMAS AÇÕES NECESSÁRIAS:")
    print("1. Importar arquivo Excel com dados de importação/exportação")
    print("2. Relacionar com tabela de empresas (empresa_comex)")
    print("3. Validar se NCMs de importação estão catalogados por empresa")
    print("4. Verificar se há dados para VALE e HIDRAU no período de 01/01/2024 a 22/02/2026")

print("\n" + "=" * 80)
print("✅ Diagnóstico concluído")
print("=" * 80)
