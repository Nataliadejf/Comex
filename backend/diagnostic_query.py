#!/usr/bin/env python3
"""
Script de diagnóstico para validar valores de importação/exportação por empresa e NCM
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

# Importar configurações do projeto
sys.path.insert(0, str(Path(__file__).parent))
from config import settings
from database import SessionLocal

# Determinando DB URL (mesma lógica do database.py)
db_url = os.getenv("DATABASE_URL")
if not db_url or db_url == "":
    db_path = settings.data_dir / "database" / "comex.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    path_str = str(db_path.absolute()).replace("\\", "/")
    db_url = f"sqlite:///{path_str}"

print(f"📊 Conectando ao banco: {db_url[:60]}...")

if not db_url:
    print("❌ DATABASE_URL não configurada")
    sys.exit(1)

engine = create_engine(db_url)

print("=" * 80)
print("DIAGNÓSTICO: Validação de Valores por Empresa e NCM")
print("=" * 80)

# Query 1: Verificar estrutura de dados
query1 = """
SELECT 
    ec.razao_social,
    COUNT(o.id) as total_operacoes,
    COUNT(DISTINCT o.ncm) as total_ncms,
    COUNT(DISTINCT DATE_TRUNC('month', o.data_operacao)) as total_periodos,
    o.tipo_operacao,
    MIN(o.data_operacao)::date as primeira_data,
    MAX(o.data_operacao)::date as ultima_data,
    ROUND(SUM(o.valor_fob::numeric) / 1000000, 2) as valor_total_milhoes
FROM operacao_comex o
LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
WHERE ec.razao_social IN ('VALE S.A.', 'HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA')
GROUP BY ec.razao_social, o.tipo_operacao
ORDER BY ec.razao_social, o.tipo_operacao;
"""

print("\n1️⃣  VISÃO GERAL: Operações por Empresa\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query1), conn)
        print(result.to_string())
except Exception as e:
    print(f"❌ Erro na query 1: {e}")

# Query 2: Comparação de importações VALE vs HIDRAU
query2 = """
SELECT 
    ec.razao_social,
    DATE_TRUNC('year', o.data_operacao)::date as ano,
    o.tipo_operacao,
    COUNT(DISTINCT o.ncm) as ncms_distintos,
    COUNT(*) as qtd_registros,
    ROUND(SUM(o.valor_fob::numeric) / 1000000, 2) as valor_milhoes
FROM operacao_comex o
LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
WHERE ec.razao_social IN ('VALE S.A.', 'HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA')
GROUP BY ec.razao_social, ano, o.tipo_operacao
ORDER BY ec.razao_social, ano DESC, o.tipo_operacao;
"""

print("\n\n2️⃣  COMPARAÇÃO: Importações/Exportações por Ano\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query2), conn)
        print(result.to_string())
except Exception as e:
    print(f"❌ Erro na query 2: {e}")

# Query 3: Amostra de NCMs para cada empresa
query3 = """
SELECT 
    ec.razao_social,
    o.tipo_operacao,
    COUNT(DISTINCT o.ncm) as total_ncms,
    STRING_AGG(DISTINCT o.ncm::text, ', ' ORDER BY o.ncm::text) as ncms_amostra
FROM operacao_comex o
LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
WHERE ec.razao_social IN ('VALE S.A.', 'HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA')
GROUP BY ec.razao_social, o.tipo_operacao
ORDER BY ec.razao_social, o.tipo_operacao;
"""

print("\n\n3️⃣  NCMs UTILIZADOS: Amostra de Códigos\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query3), conn)
        for idx, row in result.iterrows():
            print(f"\n{row['razao_social']} - {row['tipo_operacao']}")
            print(f"  Total de NCMs: {row['total_ncms']}")
            ncms = row['ncms_amostra'].split(', ')
            print(f"  Amostra (primeiros 5): {', '.join(ncms[:5])}")
except Exception as e:
    print(f"❌ Erro na query 3: {e}")

# Query 4: Verificar se há dados vazios/NULL
query4 = """
SELECT 
    ec.razao_social,
    COUNT(*) as total,
    COUNT(CASE WHEN o.valor_fob IS NULL THEN 1 END) as valor_fob_nulo,
    COUNT(CASE WHEN o.ncm IS NULL THEN 1 END) as ncm_nulo,
    COUNT(CASE WHEN o.tipo_operacao IS NULL THEN 1 END) as tipo_op_nulo
FROM operacao_comex o
LEFT JOIN empresa_comex ec ON o.id_empresa = ec.id
WHERE ec.razao_social IN ('VALE S.A.', 'HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA')
GROUP BY ec.razao_social;
"""

print("\n\n4️⃣  VALIDAÇÃO: Dados NULL/Vazios\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query4), conn)
        print(result.to_string())
except Exception as e:
    print(f"❌ Erro na query 4: {e}")

# Query 5: Teste do filtro aplicado no dashboard
query5 = """
SELECT 'Teste: Filtro VALE como IMPORTADORA' as teste;

SELECT 
    COUNT(*) as total,
    ROUND(SUM(CASE WHEN tipo_operacao = 'IMPORTACAO' THEN valor_fob::numeric ELSE 0 END) / 1000000, 2) as imp_milhoes,
    ROUND(SUM(CASE WHEN tipo_operacao = 'EXPORTACAO' THEN valor_fob::numeric ELSE 0 END) / 1000000, 2) as exp_milhoes
FROM operacao_comex
WHERE id_empresa IN (
    SELECT id FROM empresa_comex 
    WHERE razao_social = 'VALE S.A.' 
    AND tipo_operacao = 'IMPORTACAO'
);

SELECT 'Teste: Filtro HIDRAU como IMPORTADORA' as teste;

SELECT 
    COUNT(*) as total,
    ROUND(SUM(CASE WHEN tipo_operacao = 'IMPORTACAO' THEN valor_fob::numeric ELSE 0 END) / 1000000, 2) as imp_milhoes,
    ROUND(SUM(CASE WHEN tipo_operacao = 'EXPORTACAO' THEN valor_fob::numeric ELSE 0 END) / 1000000, 2) as exp_milhoes
FROM operacao_comex
WHERE id_empresa IN (
    SELECT id FROM empresa_comex 
    WHERE razao_social = 'HIDRAU TORQUE INDUSTRIA COMERCIO IMPORTACAO E EXPORTACAO LTDA'
    AND tipo_operacao = 'IMPORTACAO'
);
"""

print("\n\n5️⃣  TESTE: Filtros Simulados no Dashboard\n")
try:
    with engine.connect() as conn:
        result = pd.read_sql_query(text(query5), conn)
        print(result.to_string())
except Exception as e:
    print(f"❌ Erro na query 5: {e}")

print("\n" + "=" * 80)
print("✅ Diagnóstico concluído")
print("=" * 80)
