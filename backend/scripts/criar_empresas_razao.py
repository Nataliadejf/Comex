"""
Cria/atualiza a tabela local `empresas_razao` com a razão social (e porte,
capital social) de TODAS as empresas do Brasil, a partir do snapshot mais
recente do cadastro RF na Base dos Dados (basedosdados.br_me_cnpj.empresas).

Usada para preencher o nome das empresas SEM histórico de comex no Painel de
Empresas (a base de Estabelecimentos só tem nome fantasia, muitas vezes vazio).

Uso:
    set GOOGLE_APPLICATION_CREDENTIALS=<chave>
    python criar_empresas_razao.py
"""
from google.cloud import bigquery

PROJ = "liquid-receiver-483923-n6.Projeto_Comex"
SRC = "basedosdados.br_me_cnpj.empresas"


def main():
    c = bigquery.Client()
    print(f"Projeto: {c.project} | fonte: {SRC}")
    ddl = f"""
    CREATE OR REPLACE TABLE `{PROJ}.empresas_razao` AS
    WITH snap AS (
      SELECT MAX(ano) ano FROM `{SRC}`
    ), snap_mes AS (
      SELECT ano, (SELECT MAX(mes) FROM `{SRC}` e WHERE e.ano = s.ano) AS mes FROM snap s
    )
    SELECT
      CAST(cnpj_basico AS STRING) AS cnpj_raiz,
      ANY_VALUE(razao_social) AS razao_social,
      ANY_VALUE(CAST(capital_social AS FLOAT64)) AS capital_social,
      ANY_VALUE(CAST(porte AS STRING)) AS porte
    FROM `{SRC}`
    WHERE ano = (SELECT ano FROM snap_mes)
      AND mes = (SELECT mes FROM snap_mes)
    GROUP BY cnpj_raiz
    """
    print("Criando empresas_razao (pode levar 1-2 min)...")
    c.query(ddl).result()
    n = list(c.query(f"SELECT COUNT(*) n FROM `{PROJ}.empresas_razao`").result())[0].n
    print(f"OK - empresas_razao: {n:,} empresas")
    for r in c.query(f"SELECT cnpj_raiz, razao_social FROM `{PROJ}.empresas_razao` WHERE cnpj_raiz IN ('07969673','33592510') LIMIT 5").result():
        print("  ", r.cnpj_raiz, "|", r.razao_social)


if __name__ == "__main__":
    main()
