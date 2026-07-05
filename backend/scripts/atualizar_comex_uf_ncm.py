"""
Atualiza as tabelas de comércio exterior UF×NCM no BigQuery a partir da
BASE DOS DADOS (dataset público basedosdados.br_me_comex_stat), que espelha
os dados oficiais do MDIC (Comex Stat) já dentro do BigQuery.

Vantagens vs. baixar CSV do MDIC: sem download, sem problema de SSL, tudo
BigQuery→BigQuery (rápido e barato quando limitado aos anos recentes).

Para cada ano da janela, agrega por ano × mês × UF × NCM (soma valor_fob_dolar)
e SUBSTITUI aquele ano nas tabelas:
  - importacao_uf_ncm (ano, mes, sigla_uf, id_ncm, total_importacao_fob)
  - exportacao_uf_ncm (ano, mes, sigla_uf, id_ncm, total_exportacao_fob)

Só substitui anos que a Base dos Dados realmente possui — anos mais recentes
não presentes na fonte (ex.: já carregados de outra origem) são preservados.

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<caminho da chave>
    python atualizar_comex_uf_ncm.py            # janela automática (últimos 3 anos)
    python atualizar_comex_uf_ncm.py 2024 2025  # anos específicos
"""
import sys
from datetime import date
from google.cloud import bigquery

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
BD = "basedosdados.br_me_comex_stat"
JANELA_ANOS = 3  # quantos anos recentes atualizar por padrão

CONFIG = {
    "importacao": {
        "origem": f"{BD}.ncm_importacao",
        "destino": f"{PROJ}.importacao_uf_ncm",
        "col_fob": "total_importacao_fob",
        "tipo_fob": "FLOAT64",
    },
    "exportacao": {
        "origem": f"{BD}.ncm_exportacao",
        "destino": f"{PROJ}.exportacao_uf_ncm",
        "col_fob": "total_exportacao_fob",
        "tipo_fob": "INT64",  # a tabela de destino usa INT64 para exportação
    },
}


def anos_disponiveis_bd(client) -> set:
    r = client.query(f"SELECT DISTINCT ano FROM `{BD}.ncm_exportacao`").result()
    return {int(x.ano) for x in r}


def atualizar_ano(client, fluxo: str, ano: int):
    cfg = CONFIG[fluxo]
    # Agrega o ano na Base dos Dados
    sql_ins = f"""
    INSERT INTO `{cfg['destino']}` (ano, mes, sigla_uf, id_ncm, {cfg['col_fob']})
    SELECT
      CAST(ano AS INT64) AS ano,
      CAST(mes AS INT64) AS mes,
      UPPER(TRIM(CAST(sigla_uf_ncm AS STRING))) AS sigla_uf,
      CAST(id_ncm AS STRING) AS id_ncm,
      CAST(SUM(CAST(valor_fob_dolar AS FLOAT64)) AS {cfg['tipo_fob']}) AS {cfg['col_fob']}
    FROM `{cfg['origem']}`
    WHERE ano = {ano}
    GROUP BY ano, mes, sigla_uf, id_ncm
    """
    # 1) apaga o ano existente; 2) insere agregado da Base dos Dados
    client.query(f"DELETE FROM `{cfg['destino']}` WHERE ano = {ano}").result()
    job = client.query(sql_ins)
    job.result()
    n = client.query(f"SELECT COUNT(*) n FROM `{cfg['destino']}` WHERE ano = {ano}").result()
    linhas = list(n)[0].n
    print(f"  ✅ {cfg['destino']} — {ano}: {linhas:,} linhas")


def main():
    client = bigquery.Client()
    disp = anos_disponiveis_bd(client)
    bd_max = max(disp) if disp else date.today().year

    if len(sys.argv) > 1:
        anos = [int(a) for a in sys.argv[1:]]
    else:
        ano_atual = date.today().year
        # janela dos últimos anos, limitada ao que a Base dos Dados possui
        anos = [a for a in range(ano_atual - JANELA_ANOS + 1, ano_atual + 1)]

    anos = [a for a in anos if a in disp]
    ignorados = sorted(set([int(a) for a in sys.argv[1:]]) - set(anos)) if len(sys.argv) > 1 else []

    print(f"Projeto: {client.project} | fonte: Base dos Dados ({BD})")
    print(f"Base dos Dados vai até {bd_max}. Atualizando anos: {anos}")
    if ignorados:
        print(f"Ignorados (não presentes na Base dos Dados, preservados): {ignorados}")

    for ano in anos:
        for fluxo in ("importacao", "exportacao"):
            try:
                atualizar_ano(client, fluxo, ano)
            except Exception as e:
                print(f"  [ERRO] {fluxo} {ano}: {str(e)[:300]}")

    print("\nConcluído. Regenerar tabelas derivadas com: python criar_tabela_estimativa.py")


if __name__ == "__main__":
    main()
