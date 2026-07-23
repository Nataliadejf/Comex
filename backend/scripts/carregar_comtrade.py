"""Ingestão CURADA do UN Comtrade (camada macro global) no BigQuery.

Estratégia p/ não estourar consumo:
- Só os HS6 mais relevantes (top-N por valor na base real Logcomex = produtos
  dos clientes), parceiro = Mundo (agregado por país), anual, poucos anos.
- Endpoint público de preview (sem chave), 1 chamada por (HS6, ano, fluxo) com
  filtro de agregado (partner2Code=0, customsCode=C00, motCode=0) → ~166 países.

Saída: liquid-receiver-483923-n6.Projeto_Comex.comtrade_global
Colunas: hs6, ano, fluxo, reporter_code, pais, iso3, valor_usd, fob_usd, peso_kg, qtd
"""
import os
import time

import requests
from google.cloud import bigquery

DEST = "liquid-receiver-483923-n6.Projeto_Comex.comtrade_global"
LOGCOMEX = "liquid-receiver-483923-n6.Projeto_Comex.comex_real_import_logcomex"
BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

TOP_HS6 = int(os.getenv("COMTRADE_TOP_HS6", "50"))
ANOS = [int(a) for a in os.getenv("COMTRADE_ANOS", "2021,2022,2023,2024").split(",")]
THROTTLE = float(os.getenv("COMTRADE_THROTTLE", "0.5"))


def _reporters():
    r = requests.get("https://comtradeapi.un.org/files/v1/app/reference/Reporters.json", timeout=40)
    m = {}
    for x in (r.json().get("results") or r.json()):
        code = x.get("reporterCode") or x.get("id")
        m[int(code)] = (x.get("text") or x.get("reporterDesc") or "", x.get("reporterCodeIsoAlpha3") or "")
    return m


def _top_hs6(client, n):
    q = f"""SELECT SUBSTR(id_ncm,1,6) hs6, SUM(fob_import) fob
            FROM `{LOGCOMEX}` WHERE id_ncm IS NOT NULL AND LENGTH(id_ncm)>=6
            GROUP BY hs6 ORDER BY fob DESC LIMIT {int(n)}"""
    return [r["hs6"] for r in client.query(q).result()]


def _fetch(hs6, ano, flow):
    params = {
        "period": ano, "partnerCode": 0, "cmdCode": hs6, "flowCode": flow,
        "partner2Code": 0, "customsCode": "C00", "motCode": 0,
    }
    for tentativa in range(3):
        try:
            r = requests.get(BASE, params=params, timeout=60)
            if r.status_code == 200:
                return r.json().get("data") or []
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 + tentativa * 3)
                continue
            return []
        except Exception:
            time.sleep(2 + tentativa * 2)
    return []


def main():
    client = bigquery.Client()
    reps = _reporters()
    hs6_list = _top_hs6(client, TOP_HS6)
    print(f"HS6 curados: {len(hs6_list)} | anos: {ANOS} | ~{len(hs6_list)*len(ANOS)*2} chamadas")

    linhas = []
    chamadas = 0
    for i, hs6 in enumerate(hs6_list, 1):
        for ano in ANOS:
            for flow, rotulo in (("M", "Importação"), ("X", "Exportação")):
                dados = _fetch(hs6, ano, flow)
                chamadas += 1
                for d in dados:
                    code = int(d.get("reporterCode") or 0)
                    if code == 0:
                        continue
                    nome, iso = reps.get(code, ("", ""))
                    linhas.append({
                        "hs6": hs6, "ano": ano, "fluxo": rotulo,
                        "reporter_code": code, "pais": nome, "iso3": iso,
                        "valor_usd": float(d.get("primaryValue") or 0),
                        "fob_usd": float(d.get("fobvalue") or 0),
                        "peso_kg": float(d.get("netWgt") or 0),
                        "qtd": float(d.get("qty") or 0),
                    })
                time.sleep(THROTTLE)
        if i % 10 == 0:
            print(f"  {i}/{len(hs6_list)} HS6 | {chamadas} chamadas | {len(linhas)} linhas")

    print(f"Total: {len(linhas)} linhas de {chamadas} chamadas")
    if not linhas:
        print("Nada coletado — abortando.")
        return

    schema = [
        bigquery.SchemaField("hs6", "STRING"),
        bigquery.SchemaField("ano", "INT64"),
        bigquery.SchemaField("fluxo", "STRING"),
        bigquery.SchemaField("reporter_code", "INT64"),
        bigquery.SchemaField("pais", "STRING"),
        bigquery.SchemaField("iso3", "STRING"),
        bigquery.SchemaField("valor_usd", "FLOAT64"),
        bigquery.SchemaField("fob_usd", "FLOAT64"),
        bigquery.SchemaField("peso_kg", "FLOAT64"),
        bigquery.SchemaField("qtd", "FLOAT64"),
    ]
    client.load_table_from_json(
        linhas, DEST,
        job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"),
    ).result()
    print(f"OK: {client.get_table(DEST).num_rows} linhas em {DEST}")


if __name__ == "__main__":
    main()
