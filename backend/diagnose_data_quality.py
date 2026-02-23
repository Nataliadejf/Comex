#!/usr/bin/env python3
"""
Diagnóstico: Verificar por que valor_fob está 0.0 para registros de VALE/HIDRAU
"""
from pathlib import Path
import os
from sqlalchemy import create_engine, text
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import settings

# DB URL
db_url = os.getenv('DATABASE_URL')
if not db_url or db_url == '':
    db_path = settings.data_dir / 'database' / 'comex.db'
    db_url = f"sqlite:///{str(db_path.absolute()).replace('\\','/')}"

engine = create_engine(db_url)

print("="*100)
print("DIAGNÓSTICO: Analisando dados em operacoes_comex")
print("="*100)

with engine.connect() as conn:
    # 1. Contagem total de registros
    q_total = text("SELECT COUNT(*) as total FROM operacoes_comex")
    total = conn.execute(q_total).scalar()
    print(f"\n1. TOTAL DE REGISTROS: {total:,}")
    
    # 2. Distribuição de valor_fob
    q_dist = text("""
    SELECT 
        CASE 
            WHEN valor_fob = 0 THEN '0.0 (ZERO)'
            WHEN valor_fob > 0 AND valor_fob < 100 THEN '0.01 a 99.99'
            WHEN valor_fob >= 100 AND valor_fob < 1000 THEN '100 a 999.99'
            WHEN valor_fob >= 1000 AND valor_fob < 10000 THEN '1k a 9.9k'
            ELSE 'Acima de 10k'
        END as faixa,
        COUNT(*) as qtd,
        ROUND(SUM(valor_fob)/1000000, 2) as valor_milhoes
    FROM operacoes_comex
    GROUP BY faixa
    ORDER BY qtd DESC
    """)
    result = conn.execute(q_dist)
    print("\n2. DISTRIBUIÇÃO DE valor_fob:")
    for row in result:
        print(f"   {row[0]}: {row[1]:,} registros ({row[2]:.2f} mi)")
    
    # 3. Registros com valor_fob = 0 vs resumir por arquivo_origem
    q_origem = text("""
    SELECT 
        arquivo_origem,
        COUNT(*) as total,
        SUM(CASE WHEN valor_fob = 0 THEN 1 ELSE 0 END) as qtd_zero,
        SUM(CASE WHEN valor_fob > 0 THEN 1 ELSE 0 END) as qtd_nao_zero,
        ROUND(SUM(valor_fob)/1000000, 2) as valor_total_milhoes
    FROM operacoes_comex
    GROUP BY arquivo_origem
    ORDER BY total DESC
    """)
    result = conn.execute(q_origem)
    print("\n3. REGISTROS POR ARQUIVO DE ORIGEM:")
    for row in result:
        origem = row[0] or 'NULL'
        print(f"   {origem:50} | Total: {row[1]:,} | Zeros: {row[2]:,} | Não-zeros: {row[3]:,} | Valor: {row[4]:.2f}Mi")
    
    # 4. Para VALE e HIDRAU especificamente
    print("\n4. VALE - Distribuição de valor_fob:")
    q_vale = text("""
    SELECT 
        CASE 
            WHEN valor_fob = 0 THEN '0.0'
            WHEN valor_fob > 0 THEN '>0'
        END as faixa,
        COUNT(*) as qtd
    FROM operacoes_comex
    WHERE razao_social_importador LIKE '%VALE%' OR razao_social_exportador LIKE '%VALE%'
    GROUP BY faixa
    """)
    result = conn.execute(q_vale)
    for row in result:
        print(f"   {row[0]}: {row[1]:,}")
    
    print("\n5. HIDRAU - Distribuição de valor_fob:")
    q_hidrau = text("""
    SELECT 
        CASE 
            WHEN valor_fob = 0 THEN '0.0'
            WHEN valor_fob > 0 THEN '>0'
        END as faixa,
        COUNT(*) as qtd
    FROM operacoes_comex
    WHERE razao_social_importador LIKE '%HIDRAU%' OR razao_social_exportador LIKE '%HIDRAU%'
    GROUP BY faixa
    """)
    result = conn.execute(q_hidrau)
    for row in result:
        print(f"   {row[0]}: {row[1]:,}")
    
    # 6. NCM Reais vs 00000000
    print("\n6. DISTRIBUIÇÃO DE NCM (primeiras 10 linhas por arquivo_origem):")
    q_ncm = text("""
    SELECT 
        arquivo_origem,
        CASE WHEN ncm = '00000000' THEN 'NULL/00000000' ELSE ncm END as ncm_status,
        COUNT(*) as qtd
    FROM operacoes_comex
    GROUP BY arquivo_origem, ncm_status
    ORDER BY arquivo_origem, qtd DESC
    LIMIT 15
    """)
    result = conn.execute(q_ncm)
    for row in result:
        origem = row[0] or 'NULL'
        print(f"   {origem:50} | {row[1]:20} | {row[2]:,}")

print("\n" + "="*100)
print("CONCLUSÃO: Verifique acima:")
print("- Se há registros de 'BigQuery' com valor_fob=0 e ncm=00000000")
print("- Se esses dados são duvidosos (importação desatualizada ou teste)")
print("- Considere limpar registros com ncm='00000000' ou valor_fob=0")
print("="*100)
