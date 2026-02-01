"""Converte bigquery_queries.json (JSON inválido com strings multilinha) para formato ---QUERY---."""
from pathlib import Path

p = Path(__file__).parent / "bigquery_queries.json"
raw = p.read_text(encoding="utf-8")
raw2 = raw.replace('",\n"', "---QUERY---")
parts = raw2.split("---QUERY---")
prefix = '{\n  "queries": [ "'
if parts[0].strip().startswith(prefix):
    parts[0] = parts[0].strip()[len(prefix) :]
else:
    idx = parts[0].find('"WITH ')
    if idx >= 0:
        parts[0] = parts[0][idx + 1 :]
parts[-1] = parts[-1].strip()
if parts[-1].endswith('"]}'):
    parts[-1] = parts[-1][:-3]
queries = [x.strip() for x in parts if x.strip()]
out = "---QUERY---\n" + "\n---QUERY---\n".join(queries) + "\n"
p.write_text(out, encoding="utf-8")
print("Convertido:", len(queries), "consultas. Arquivo agora usa delimitador ---QUERY---.")
