"""Carrega os valores REAIS de importacao (Logcomex) no BigQuery, deduplicados.

Fonte: 4 planilhas exportadas da Logcomex (Clientes, Fornecedores, Concorrentes,
Clientes e Concorrentes). Todas sao registros de IMPORTACAO brasileira.

Saida: tabela liquid-receiver-483923-n6.Projeto_Comex.comex_real_import_logcomex
Colunas: cnpj_raiz, importador_nome, ano, mes, sigla_uf, id_ncm, pais_origem,
         exportador_nome, fob_import, qtd_estatistica, peso_liquido, n_operacoes
"""
import os
import re
import sys
import unicodedata

import pandas as pd
from google.cloud import bigquery

DOWNLOADS = os.environ.get("LOGCOMEX_DIR", r"C:\Users\User\Downloads")
FILES = {
    "Clientes": "Clientes.xlsx",
    "Fornecedores": "Fornecedores.xlsx",
    "Concorrentes": "Concorrentes.xlsx",
    "ClientesEConcorrentes": "Clientes e Concorrentes.xlsx",
}
DEST = "liquid-receiver-483923-n6.Projeto_Comex.comex_real_import_logcomex"
HAB = "liquid-receiver-483923-n6.Projeto_Comex.empresas_habilitacao"

_STOP = {"ltda", "sa", "s.a", "s/a", "me", "epp", "eireli", "cia", "e", "de",
         "do", "da", "dos", "das", "&", "-", "ind", "com", "comercio",
         "importacao", "exportacao", "industria"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def _tokens(s: str):
    return [t for t in re.findall(r"[0-9a-z]+", _norm(s)) if len(t) >= 3 and t not in _STOP]


def carregar_planilhas() -> pd.DataFrame:
    frames = []
    for base, fname in FILES.items():
        path = os.path.join(DOWNLOADS, fname)
        df = pd.read_excel(path, sheet_name="Sheet1")
        df["__base"] = base
        frames.append(df)
    big = pd.concat(frames, ignore_index=True)

    # deduplicacao por operacao (ignora a base de origem)
    keycols = ["ANO/MÊS", "PROVÁVEL IMPORTADOR", "PROVÁVEL EXPORTADOR", "NCM",
               "VALOR FOB ESTIMADO TOTAL", "QTD Estatística", "Peso líquido",
               "PAIS DE ORIGEM"]
    antes = len(big)
    big = big.drop_duplicates(subset=keycols)
    print(f"Linhas: {antes} -> {len(big)} apos deduplicar ({antes - len(big)} removidas)")

    big = big.copy()
    big["ano"] = (pd.to_numeric(big["ANO/MÊS"], errors="coerce") // 100).astype("Int64")
    big["mes"] = (pd.to_numeric(big["ANO/MÊS"], errors="coerce") % 100).astype("Int64")
    big["id_ncm"] = pd.to_numeric(big["NCM"], errors="coerce").astype("Int64").astype(str)
    big["fob_import"] = pd.to_numeric(big["VALOR FOB ESTIMADO TOTAL"], errors="coerce").fillna(0.0)
    big["qtd_estatistica"] = pd.to_numeric(big["QTD Estatística"], errors="coerce").fillna(0.0)
    big["peso_liquido"] = pd.to_numeric(big["Peso líquido"], errors="coerce").fillna(0.0)

    agg = (big.groupby(
        ["PROVÁVEL IMPORTADOR", "ano", "mes", "UF IMPORTADOR", "id_ncm",
         "PAIS DE ORIGEM", "PROVÁVEL EXPORTADOR"], dropna=False)
        .agg(fob_import=("fob_import", "sum"),
             qtd_estatistica=("qtd_estatistica", "sum"),
             peso_liquido=("peso_liquido", "sum"),
             n_operacoes=("fob_import", "size"))
        .reset_index()
        .rename(columns={"PROVÁVEL IMPORTADOR": "importador_nome",
                         "UF IMPORTADOR": "sigla_uf",
                         "PAIS DE ORIGEM": "pais_origem",
                         "PROVÁVEL EXPORTADOR": "exportador_nome"}))
    return agg


def resolver_cnpjs(client: bigquery.Client, nomes) -> dict:
    """Casa cada importador (nome) com cnpj_raiz de empresas_habilitacao por tokens."""
    hab = client.query(
        f"SELECT cnpj_raiz, razao_social, anos_ativos FROM {HAB}"
    ).to_dataframe()
    hab["_norm"] = hab["razao_social"].map(_norm)
    hab["_toks"] = hab["razao_social"].map(lambda s: set(_tokens(s)))

    resolvido = {}
    for nome in nomes:
        toks = set(_tokens(nome))
        if not toks:
            resolvido[nome] = None
            continue
        n = _norm(nome)
        # candidatos: contem todos os tokens do nome
        mask = hab["_toks"].map(lambda ht: toks.issubset(ht))
        cand = hab[mask]
        if cand.empty:
            # relaxa: pelo menos 2 tokens em comum (nomes longos)
            cand = hab[hab["_toks"].map(lambda ht: len(toks & ht) >= max(2, len(toks) - 1))]
        if cand.empty:
            resolvido[nome] = None
            continue
        # rank: match exato > prefixo > menor razao (mais especifica) > mais anos
        cand = cand.assign(
            _exact=(cand["_norm"] == n).astype(int),
            _pref=cand["_norm"].str.startswith(n[:12]).astype(int),
            _len=cand["razao_social"].str.len(),
        ).sort_values(["_exact", "_pref", "anos_ativos", "_len"],
                      ascending=[False, False, False, True])
        resolvido[nome] = str(cand.iloc[0]["cnpj_raiz"])
    return resolvido


def main():
    client = bigquery.Client()
    df = carregar_planilhas()
    nomes = df["importador_nome"].dropna().unique().tolist()
    print(f"Resolvendo {len(nomes)} importadores para cnpj_raiz...")
    mapa = resolver_cnpjs(client, nomes)
    df["cnpj_raiz"] = df["importador_nome"].map(mapa)
    resolvidos = df["cnpj_raiz"].notna().sum()
    print(f"CNPJ resolvido em {resolvidos}/{len(df)} linhas "
          f"({df.loc[df['cnpj_raiz'].notna(), 'importador_nome'].nunique()}/"
          f"{len(nomes)} importadores)")

    df = df.dropna(subset=["ano", "mes"])
    df = df[["cnpj_raiz", "importador_nome", "ano", "mes", "sigla_uf", "id_ncm",
             "pais_origem", "exportador_nome", "fob_import", "qtd_estatistica",
             "peso_liquido", "n_operacoes"]]
    df["ano"] = df["ano"].astype("int64")
    df["mes"] = df["mes"].astype("int64")

    schema = [
        bigquery.SchemaField("cnpj_raiz", "STRING"),
        bigquery.SchemaField("importador_nome", "STRING"),
        bigquery.SchemaField("ano", "INT64"),
        bigquery.SchemaField("mes", "INT64"),
        bigquery.SchemaField("sigla_uf", "STRING"),
        bigquery.SchemaField("id_ncm", "STRING"),
        bigquery.SchemaField("pais_origem", "STRING"),
        bigquery.SchemaField("exportador_nome", "STRING"),
        bigquery.SchemaField("fob_import", "FLOAT64"),
        bigquery.SchemaField("qtd_estatistica", "FLOAT64"),
        bigquery.SchemaField("peso_liquido", "FLOAT64"),
        bigquery.SchemaField("n_operacoes", "INT64"),
    ]
    job = client.load_table_from_dataframe(
        df, DEST,
        job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    t = client.get_table(DEST)
    print(f"OK: {t.num_rows} linhas em {DEST}")
    print(f"FOB real total: US$ {df['fob_import'].sum():,.0f}")


if __name__ == "__main__":
    main()
