"""
Atualiza as tabelas de comércio exterior UF×NCM no BigQuery com os dados
oficiais mais recentes do MDIC (Comex Stat — base bruta).

O MDIC publica, todo mês, o arquivo do ANO CORRENTE completo (com os meses já
disponíveis). Este script baixa IMP_<ano>.csv e EXP_<ano>.csv, agrega por
ano × mês × UF × NCM (somando VL_FOB) e SUBSTITUI aquele ano nas tabelas:
  - importacao_uf_ncm (ano, mes, sigla_uf, id_ncm, total_importacao_fob)
  - exportacao_uf_ncm (ano, mes, sigla_uf, id_ncm, total_exportacao_fob)

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<caminho da chave>
    python atualizar_comex_uf_ncm.py 2025          # atualiza 2025
    python atualizar_comex_uf_ncm.py 2025 2026      # atualiza 2025 e 2026

Requisitos: pandas, requests, google-cloud-bigquery (já no projeto).
"""
import os
import sys
import tempfile
import requests
import urllib3
import pandas as pd
from google.cloud import bigquery

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
BASE_URL = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm"
CHUNK = 500_000

CONFIG = {
    "IMP": {"tabela": f"{PROJ}.importacao_uf_ncm", "col_fob": "total_importacao_fob"},
    "EXP": {"tabela": f"{PROJ}.exportacao_uf_ncm", "col_fob": "total_exportacao_fob"},
}


def _baixar_arquivo(url: str, destino: str):
    """Baixa (streaming) para arquivo. Tenta com verificação SSL; se falhar
    (cadeia de certificado gov.br), refaz sem verificação (fonte oficial pública)."""
    for verify in (True, False):
        try:
            if not verify:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                print("  [aviso] verificação SSL desabilitada (cadeia gov.br) — fonte oficial MDIC")
            with requests.get(url, timeout=900, stream=True, verify=verify) as r:
                r.raise_for_status()
                with open(destino, "wb") as f:
                    for bloco in r.iter_content(chunk_size=1024 * 1024):
                        if bloco:
                            f.write(bloco)
            return
        except requests.exceptions.SSLError:
            if verify:
                continue  # tenta de novo sem verificação
            raise


def baixar_e_agregar(fluxo: str, ano: int) -> pd.DataFrame:
    """Baixa IMP_<ano>.csv ou EXP_<ano>.csv e agrega por ano×mês×UF×NCM."""
    url = f"{BASE_URL}/{fluxo}_{ano}.csv"
    print(f"  Baixando {url} ...")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.close()
    try:
        _baixar_arquivo(url, tmp.name)
        agregado = None
        usecols = ["CO_ANO", "CO_MES", "SG_UF_NCM", "CO_NCM", "VL_FOB"]
        for chunk in pd.read_csv(tmp.name, sep=";", usecols=usecols, chunksize=CHUNK,
                                 dtype={"CO_ANO": int, "CO_MES": int, "SG_UF_NCM": str,
                                        "CO_NCM": str, "VL_FOB": float}):
            g = (chunk.groupby(["CO_ANO", "CO_MES", "SG_UF_NCM", "CO_NCM"], as_index=False)["VL_FOB"]
                      .sum())
            agregado = g if agregado is None else (
                pd.concat([agregado, g]).groupby(["CO_ANO", "CO_MES", "SG_UF_NCM", "CO_NCM"],
                                                 as_index=False)["VL_FOB"].sum())
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    if agregado is None:
        return pd.DataFrame()
    return agregado.rename(columns={
        "CO_ANO": "ano", "CO_MES": "mes", "SG_UF_NCM": "sigla_uf", "CO_NCM": "id_ncm",
    })


def atualizar(client: bigquery.Client, fluxo: str, ano: int):
    cfg = CONFIG[fluxo]
    df = baixar_e_agregar(fluxo, ano)
    if df.empty:
        print(f"  [!] Sem dados para {fluxo} {ano}")
        return
    df = df.rename(columns={"VL_FOB": cfg["col_fob"]})
    df = df[["ano", "mes", "sigla_uf", "id_ncm", cfg["col_fob"]]]
    meses = sorted(df["mes"].unique().tolist())
    print(f"  {fluxo} {ano}: {len(df):,} linhas agregadas | meses={meses}")

    # 1) Remove o ano existente (evita duplicidade)
    client.query(f"DELETE FROM `{cfg['tabela']}` WHERE ano = {ano}").result()
    # 2) Carrega o ano atualizado (append)
    job = client.load_table_from_dataframe(
        df, cfg["tabela"],
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
    )
    job.result()
    print(f"  ✅ {cfg['tabela']} atualizada com {ano}")


def main():
    anos = [int(a) for a in sys.argv[1:]] or [2025]
    client = bigquery.Client()
    print(f"Projeto: {client.project} | anos: {anos}")
    for ano in anos:
        for fluxo in ("IMP", "EXP"):
            print(f"\n=== {fluxo} {ano} ===")
            try:
                atualizar(client, fluxo, ano)
            except Exception as e:
                print(f"  [ERRO] {fluxo} {ano}: {str(e)[:300]}")
    print("\nConcluído. As demais tabelas (empresas_comex_estimado, etc.) podem ser")
    print("regeneradas com: python criar_tabela_estimativa.py")


if __name__ == "__main__":
    main()
