#!/usr/bin/env python3
"""
Script para limpar registros de baixa qualidade (BigQuery com valor=0 e ncm=00000000)
ANTES DE EXECUTAR: Fazer backup do banco!
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
print("⚠️  LIMPEZA DE REGISTROS DE BAIXA QUALIDADE")
print("="*100)

with engine.connect() as conn:
    # Contar antes
    q_before = text("SELECT COUNT(*) FROM operacoes_comex WHERE arquivo_origem='BigQuery' AND valor_fob=0 AND ncm='00000000'")
    count_before = conn.execute(q_before).scalar()
    print(f"\n📊 ANTES: {count_before:,} registros a limpar")
    
    # Simulação (não deleta)
    print("\n⏸️  SIMULAÇÃO (não deleta ainda):")
    q_check = text("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN arquivo_origem='BigQuery' THEN 1 ELSE 0 END) as bq_count,
        SUM(CASE WHEN valor_fob=0 THEN 1 ELSE 0 END) as zero_value,
        SUM(CASE WHEN ncm='00000000' THEN 1 ELSE 0 END) as null_ncm
    FROM operacoes_comex
    """)
    result = conn.execute(q_check).fetchone()
    print(f"  - Total de registros: {result[0]:,}")
    print(f"  - BigQuery: {result[1]:,}")
    print(f"  - valor_fob=0: {result[2]:,}")
    print(f"  - ncm=00000000: {result[3]:,}")
    print(f"  - 🔴 A DELETAR (BigQuery + valor=0 + ncm=00000000): {count_before:,}")

print("\n" + "="*100)
print("❌ REGISTROS A DELETAR:")
print("="*100)

with engine.connect() as conn:
    q_sample = text("""
    SELECT 
        razao_social_importador,
        COUNT(*) as qtd,
        SUM(valor_fob) as valor_total
    FROM operacoes_comex 
    WHERE arquivo_origem='BigQuery' AND valor_fob=0 AND ncm='00000000'
    GROUP BY razao_social_importador
    ORDER BY qtd DESC
    LIMIT 20
    """)
    results = conn.execute(q_sample)
    print("\nTop 20 razões sociais que serão removidas:")
    for row in results:
        empresa = row[0] or 'NULL'
        print(f"  {empresa:50} | {row[1]:6,} registros | valor: ${row[2]}")

print("\n" + "="*100)
print("💾 EXECUTANDO LIMPEZA...")
print("="*100)

# EXECUTAR DELETE
with engine.begin() as conn:  # begin() = transação automática
    q_delete = text('''
        DELETE FROM operacoes_comex 
        WHERE arquivo_origem='BigQuery' 
        AND valor_fob=0 
        AND ncm='00000000'
    ''')
    result = conn.execute(q_delete)
    print(f'✅ Deletados {result.rowcount:,} registros')

# Verificar resultado
print("\n" + "="*100)
print("📊 APÓS LIMPEZA:")
print("="*100)

with engine.connect() as conn:
    q_after = text("SELECT COUNT(*) FROM operacoes_comex")
    count_after = conn.execute(q_after).scalar()
    print(f"\n✅ Total agora: {count_after:,} registros (era 643.701)")
    
    # Distribuição nova
    q_dist = text("""
    SELECT 
        arquivo_origem,
        COUNT(*) as total,
        ROUND(SUM(valor_fob)/1000000, 2) as valor_milhoes
    FROM operacoes_comex
    GROUP BY arquivo_origem
    ORDER BY total DESC
    """)
    result = conn.execute(q_dist)
    print("\nRegistros por arquivo:")
    for row in result:
        origem = row[0] or 'NULL'
        print(f"  {origem:50} | {row[1]:,} | ${row[2]:.2f} Mi")

print("\n" + "="*100)
print("⚠️  ADVERTÊNCIAS:")
print("="*100)
print("""
1. BACKUP: Faça backup do banco antes de deletar
2. VALE/HIDRAU: Essas empresas desaparecerão da base (só tinham registros BigQuery zerados)
3. DADOS: Arquivo Excel 2025 não contém VALE nem HIDRAU - precisam ser adicionados manualmente
4. RESTAURAÇÃO: Se precisar deshacer, restaurar do backup
""")
