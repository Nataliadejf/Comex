"""
Executa as queries de auditoria em operacoes_comex.
Uso: na pasta backend: python run_audit_queries.py
"""
import sqlite3
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings

# sqlite:///C:\...\comex.db -> C:\...\comex.db
db_path = settings.database_url.replace("sqlite:///", "").strip()
if not Path(db_path).exists():
    print(f"Banco não encontrado: {db_path}")
    sys.exit(1)

def _nome(s):
    """Remove quebras de linha e limita tamanho para alinhar tabela."""
    if s is None:
        return ""
    return " ".join(str(s).replace("\r", " ").replace("\n", " ").split())[:55]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

queries = [
    ("Total de registros em operacoes_comex", "SELECT COUNT(*) AS total_registros FROM operacoes_comex"),
    ("Empresas importadoras distintas (com nome preenchido)", 
     "SELECT COUNT(DISTINCT razao_social_importador) AS total_importadoras FROM operacoes_comex WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> ''"),
    ("Empresas exportadoras distintas (com nome preenchido)",
     "SELECT COUNT(DISTINCT razao_social_exportador) AS total_exportadoras FROM operacoes_comex WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> ''"),
    ("Registros sem importador",
     "SELECT COUNT(*) AS registros_sem_importador FROM operacoes_comex WHERE razao_social_importador IS NULL OR TRIM(razao_social_importador) = ''"),
    ("Registros sem exportador",
     "SELECT COUNT(*) AS registros_sem_exportador FROM operacoes_comex WHERE razao_social_exportador IS NULL OR TRIM(razao_social_exportador) = ''"),
]

print("=" * 60)
print("AUDITORIA operacoes_comex")
print("=" * 60)

for label, sql in queries:
    try:
        cur.execute(sql)
        row = cur.fetchone()
        key = row.keys()[0]
        val = row[0]
        print(f"{label}: {val}")
    except Exception as e:
        print(f"{label}: ERRO - {e}")

# Top 10 importadoras
print("\n--- Top 10 importadoras por quantidade de operações ---")
try:
    cur.execute("""
        SELECT razao_social_importador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_importador IS NOT NULL AND TRIM(razao_social_importador) <> ''
        GROUP BY razao_social_importador
        ORDER BY total_operacoes DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
except Exception as e:
    print(f"  ERRO: {e}")

# Top 10 exportadoras
print("\n--- Top 10 exportadoras por quantidade de operações ---")
try:
    cur.execute("""
        SELECT razao_social_exportador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_exportador IS NOT NULL AND TRIM(razao_social_exportador) <> ''
        GROUP BY razao_social_exportador
        ORDER BY total_operacoes DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
except Exception as e:
    print(f"  ERRO: {e}")

# Busca Vale e Hidrau torque (importador e exportador)
LIMITE_VALE = 25  # top N para não encher o terminal
print(f"\n--- Busca: Vale (importador) - top {LIMITE_VALE} ---")
try:
    cur.execute("""
        SELECT razao_social_importador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_importador IS NOT NULL AND razao_social_importador LIKE ?
        GROUP BY razao_social_importador
        ORDER BY total_operacoes DESC
    """, ("%Vale%",))
    rows = cur.fetchall()
    if not rows:
        print("  Nenhum resultado.")
    else:
        for row in rows[:LIMITE_VALE]:
            print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
        if len(rows) > LIMITE_VALE:
            print(f"  ... e mais {len(rows) - LIMITE_VALE} empresas com 'Vale' no nome.")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n--- Busca: Vale (exportador) ---")
try:
    cur.execute("""
        SELECT razao_social_exportador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_exportador IS NOT NULL AND razao_social_exportador LIKE ?
        GROUP BY razao_social_exportador
        ORDER BY total_operacoes DESC
    """, ("%Vale%",))
    rows = cur.fetchall()
    if not rows:
        print("  Nenhum resultado.")
    for row in rows:
        print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n--- Busca: Hidrau torque / Hidru torque (importador) ---")
try:
    cur.execute("""
        SELECT razao_social_importador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_importador IS NOT NULL AND (razao_social_importador LIKE ? OR razao_social_importador LIKE ?)
        GROUP BY razao_social_importador
        ORDER BY total_operacoes DESC
    """, ("%Hidrau%torque%", "%Hidru%torque%"))
    rows = cur.fetchall()
    if not rows:
        print("  Nenhum resultado.")
    for row in rows:
        print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n--- Busca: Hidrau torque / Hidru torque (exportador) ---")
try:
    cur.execute("""
        SELECT razao_social_exportador AS nome, COUNT(*) AS total_operacoes, SUM(valor_fob) AS valor_total_fob
        FROM operacoes_comex
        WHERE razao_social_exportador IS NOT NULL AND (razao_social_exportador LIKE ? OR razao_social_exportador LIKE ?)
        GROUP BY razao_social_exportador
        ORDER BY total_operacoes DESC
    """, ("%Hidrau%torque%", "%Hidru%torque%"))
    rows = cur.fetchall()
    if not rows:
        print("  Nenhum resultado.")
    for row in rows:
        print(f"  {_nome(row['nome']):55} | ops: {row['total_operacoes']:>8} | FOB: {row['valor_total_fob'] or 0:,.0f}")
except Exception as e:
    print(f"  ERRO: {e}")

# Teste filtro por empresa (VALE) - equivalente ao ILIKE do dashboard
print("\n--- Teste filtro por empresa: importador contém 'VALE' (case-insensitive) ---")
try:
    # SQLite: usar LOWER() para case-insensitive (equivalente a ILIKE)
    cur.execute("""
        SELECT COUNT(*) AS total_operacoes, COALESCE(SUM(valor_fob), 0) AS valor_total
        FROM operacoes_comex
        WHERE LOWER(razao_social_importador) LIKE '%vale%'
    """)
    row = cur.fetchone()
    print(f"  Total operações: {row['total_operacoes']}")
    print(f"  Soma valor_fob:  {row['valor_total']:,.2f}")
    print("  (Compare com GET /dashboard/stats?empresa_importadora=Vale)")
except Exception as e:
    print(f"  ERRO: {e}")

# Resumo: destaques Vale S.A. e Hidrau Torque
print("\n--- Resumo (Vale S.A. e Hidrau Torque) ---")
try:
    for label, like in [("VALE S.A. (importador)", "VALE S.A.%"), ("Hidrau Torque (importador)", "%Hidrau%torque%")]:
        cur.execute("""
            SELECT COUNT(*) AS total_operacoes
            FROM operacoes_comex
            WHERE razao_social_importador IS NOT NULL AND razao_social_importador LIKE ?
        """, (like,))
        n = cur.fetchone()[0]
        print(f"  {label}: {n} operações")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n" + "=" * 60)
conn.close()
