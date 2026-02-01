#!/usr/bin/env python3
"""
Mostra qual service account (e-mail) e projeto estão sendo usados pelo BigQuery.
Use para conferir no Google Cloud IAM se a permissão foi dada à conta certa.

Rode na pasta projeto_comex:  python verificar_conta_bigquery.py
"""
import sys
from pathlib import Path

# Garantir que o backend está no path (para importar o coletor)
raiz = Path(__file__).resolve().parent
backend_dir = raiz / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from data_collector.public_company_collector import _carregar_credenciais_bigquery

def main():
    creds = _carregar_credenciais_bigquery()
    if not creds:
        print("GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada ou inválida.")
        print("Verifique o .env em projeto_comex/ ou projeto_comex/backend/")
        sys.exit(1)
    email = (creds.get("client_email") or "").strip()
    proj = (creds.get("project_id") or "").strip()
    print("Conta em uso (client_email):", email or "(não encontrado)")
    print("Projeto (project_id):", proj or "(não encontrado)")
    print()
    print("No Google Cloud IAM, a role 'BigQuery Job User' ou 'BigQuery User'")
    print("deve estar nesse e-mail. Projeto no console:", proj or "liquid-receiver-483923-n6")

if __name__ == "__main__":
    main()
