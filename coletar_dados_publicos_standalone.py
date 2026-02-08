"""
Script standalone para coletar dados públicos (BigQuery), integrar no PostgreSQL
e executar cruzamento para popular operacoes_comex e empresas_recomendadas.

Coleta por ESCALA DE TEMPO (ano início a ano fim), não por limite de linhas.

Uso:
    cd projeto_comex
    python coletar_dados_publicos_standalone.py --ano-inicio 2024 --ano-fim 2030 --integrar-banco --executar-cruzamento

    # Sem limite de linhas (todos os registros do período):
    python coletar_dados_publicos_standalone.py --integrar-banco --executar-cruzamento

    # Com limite opcional (ex.: teste com 5000 linhas):
    python coletar_dados_publicos_standalone.py --ano-inicio 2024 --ano-fim 2025 --limite 5000 --integrar-banco

Requer:
    - GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_CREDENTIALS_JSON
    - DATABASE_URL (PostgreSQL, ex.: Render)
"""
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import date, datetime

# Garantir que o backend esteja no path
PROJETO_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJETO_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from loguru import logger

# Template da query Base dos Dados - estabelecimentos (empresas importadoras/exportadoras)
# Retorna: ano, cnpj, razao_social, id_exportacao_importacao, sigla_uf
# Filtro por escala de tempo: ano_inicio e ano_fim (não por limite de linhas)
QUERY_ESTABELECIMENTOS_TEMPLATE = """
WITH 
dicionario_id_exportacao_importacao AS (
    SELECT
        chave AS chave_id_exportacao_importacao,
        valor AS descricao_id_exportacao_importacao
    FROM `basedosdados.br_me_exportadoras_importadoras.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'id_exportacao_importacao'
        AND id_tabela = 'estabelecimentos'
)
SELECT
    dados.ano as ano,
    dados.cnpj as cnpj,
    dados.razao_social as razao_social,
    descricao_id_exportacao_importacao AS id_exportacao_importacao,
    dados.sigla_uf AS sigla_uf
FROM `basedosdados.br_me_exportadoras_importadoras.estabelecimentos` AS dados
LEFT JOIN `dicionario_id_exportacao_importacao`
    ON dados.id_exportacao_importacao = chave_id_exportacao_importacao
WHERE dados.ano >= {ano_inicio} AND dados.ano <= {ano_fim}
ORDER BY dados.ano, dados.cnpj
"""


def _get_bigquery_client():
    """Cria cliente BigQuery usando credenciais do ambiente."""
    try:
        from google.cloud import bigquery
        from google.auth import exceptions as auth_exceptions
    except ImportError:
        logger.error("Biblioteca google-cloud-bigquery não instalada. pip install google-cloud-bigquery")
        return None

    creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_env and creds_env.strip().startswith("{"):
        try:
            creds_dict = json.loads(creds_env)
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return bigquery.Client(credentials=credentials)
        except Exception as e:
            logger.warning(f"Erro ao parsear credenciais JSON: {e}")
            return None
    try:
        return bigquery.Client()
    except auth_exceptions.DefaultCredentialsError:
        logger.error(
            "Credenciais do BigQuery não encontradas. Configure GOOGLE_APPLICATION_CREDENTIALS_JSON "
            "(JSON da chave de serviço) no .env ou nas variáveis de ambiente do Render."
        )
    return None


def coletar_bigquery(ano_inicio: int = 2024, ano_fim: int = None, limite_linhas: int = 0):
    """
    Coleta dados do BigQuery (estabelecimentos) por escala de tempo (ano início a ano fim).
    Não usa limite de linhas por padrão; todos os registros do período são coletados.
    Retorna lista de dicts no formato para inserção em operacoes_comex.
    """
    if ano_fim is None:
        ano_fim = date.today().year
    ano_fim = max(ano_inicio, min(ano_fim, 2030))

    client = _get_bigquery_client()
    if not client:
        return []

    sql = QUERY_ESTABELECIMENTOS_TEMPLATE.format(ano_inicio=ano_inicio, ano_fim=ano_fim)
    if limite_linhas and limite_linhas > 0:
        sql = sql.strip() + f"\nLIMIT {int(limite_linhas)}"
        logger.info(f"Executando query no BigQuery (escala {ano_inicio}-{ano_fim}, limite={limite_linhas:,} linhas)...")
    else:
        logger.info(f"Executando query no BigQuery (escala de tempo: {ano_inicio} a {ano_fim}, sem limite de linhas)...")
    try:
        query_job = client.query(sql)
        rows = list(query_job.result())
    except Exception as e:
        logger.error(f"Erro BigQuery: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

    logger.info(f"BigQuery retornou {len(rows):,} linhas (período {ano_inicio}-{ano_fim}).")

    # Transformar em registros para operacoes_comex
    # Cada linha = empresa; criamos 1 ou 2 operações (Importação/Exportação) conforme id_exportacao_importacao
    registros = []
    for row in rows:
        try:
            ano = getattr(row, "ano", None) or (row["ano"] if isinstance(row, dict) else None)
            if ano is None:
                continue
            try:
                ano_int = int(ano)
            except (TypeError, ValueError):
                ano_int = 2021
            data_op = date(ano_int, 1, 1)
            mes_ref = f"{ano_int}-01"

            cnpj_raw = getattr(row, "cnpj", None) or (row.get("cnpj") if hasattr(row, "get") else None)
            cnpj = "".join(filter(str.isdigit, str(cnpj_raw or "")))[:14] or None

            razao = getattr(row, "razao_social", None) or (row.get("razao_social") if hasattr(row, "get") else None)
            razao = (razao or "").strip() or "Não informado"

            uf_raw = getattr(row, "sigla_uf", None) or (row.get("sigla_uf") if hasattr(row, "get") else None)
            uf = (str(uf_raw or "").strip().upper())[:2] or "BR"

            id_exp_imp = getattr(row, "id_exportacao_importacao", None) or (row.get("id_exportacao_importacao") if hasattr(row, "get") else None)
            id_str = (id_exp_imp or "").lower()

            # Uma ou duas operações conforme tipo
            if "exportadora" in id_str and "importadora" in id_str:
                tipos = ["Importação", "Exportação"]
            elif "exportadora" in id_str:
                tipos = ["Exportação"]
            elif "importadora" in id_str:
                tipos = ["Importação"]
            else:
                tipos = ["Importação"]

            for tipo in tipos:
                item = {
                    "ncm": "00000000",
                    "descricao_produto": "Não informado (BigQuery estabelecimentos)",
                    "tipo_operacao": tipo,
                    "pais_origem_destino": "",
                    "uf": uf,
                    "razao_social_importador": razao if tipo == "Importação" else None,
                    "razao_social_exportador": razao if tipo == "Exportação" else None,
                    "cnpj_importador": cnpj if tipo == "Importação" else None,
                    "cnpj_exportador": cnpj if tipo == "Exportação" else None,
                    "valor_fob": 0.0,
                    "data_operacao": data_op,
                    "mes_referencia": mes_ref,
                    "arquivo_origem": "bigquery_estabelecimentos",
                }
                registros.append(item)
        except Exception as e:
            logger.debug(f"Ignorando linha: {e}")
            continue

    logger.info(f"Gerados {len(registros):,} registros para operacoes_comex.")
    return registros


def integrar_banco(registros: list) -> int:
    """Insere registros em operacoes_comex no PostgreSQL."""
    if not registros:
        return 0

    from database.database import SessionLocal
    from database.models import OperacaoComex, TipoOperacao, ViaTransporte

    db = SessionLocal()
    inseridos = 0
    try:
        for reg in registros:
            try:
                tipo = TipoOperacao.IMPORTACAO if reg["tipo_operacao"] == "Importação" else TipoOperacao.EXPORTACAO
                op = OperacaoComex(
                    ncm=reg["ncm"],
                    descricao_produto=reg["descricao_produto"],
                    tipo_operacao=tipo,
                    pais_origem_destino=reg["pais_origem_destino"] or "",
                    uf=reg["uf"] or "BR",
                    razao_social_importador=reg.get("razao_social_importador"),
                    razao_social_exportador=reg.get("razao_social_exportador"),
                    cnpj_importador=reg.get("cnpj_importador"),
                    cnpj_exportador=reg.get("cnpj_exportador"),
                    valor_fob=float(reg.get("valor_fob", 0)),
                    data_operacao=reg["data_operacao"],
                    mes_referencia=reg["mes_referencia"],
                    via_transporte=ViaTransporte.OUTRAS,
                    arquivo_origem=reg.get("arquivo_origem", "bigquery_estabelecimentos"),
                )
                db.add(op)
                inseridos += 1
                if inseridos % 5000 == 0:
                    db.commit()
                    logger.info(f"  Inseridos {inseridos:,} em operacoes_comex...")
            except Exception as e:
                logger.debug(f"Erro ao inserir registro: {e}")
                continue
        db.commit()
        logger.success(f"Integração concluída: {inseridos:,} registros em operacoes_comex.")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao integrar banco: {e}")
        raise
    finally:
        db.close()
    return inseridos


def executar_cruzamento():
    """Popula empresas_recomendadas a partir de operacoes_comex (e outras fontes)."""
    from database.database import SessionLocal
    from scripts.analisar_empresas_recomendadas import consolidar_empresas

    db = SessionLocal()
    try:
        consolidar_empresas(db)
    except Exception as e:
        logger.error(f"Erro no cruzamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Coletor de dados públicos: BigQuery -> operacoes_comex -> empresas_recomendadas"
    )
    parser.add_argument("--apenas-bigquery", action="store_true", help="Apenas rodar coleta BigQuery (não integrar nem cruzamento)")
    parser.add_argument("--ano-inicio", type=int, default=2024, help="Ano inicial da escala de tempo (default: 2024)")
    parser.add_argument("--ano-fim", type=int, default=None, help="Ano final da escala de tempo (default: ano atual, máx. 2030)")
    parser.add_argument("--limite", type=int, default=0, help="Limite opcional de linhas (0 = sem limite, usar escala de tempo)")
    parser.add_argument("--integrar-banco", action="store_true", help="Inserir dados em operacoes_comex (PostgreSQL)")
    parser.add_argument("--executar-cruzamento", action="store_true", help="Popular empresas_recomendadas a partir de operacoes_comex")
    args = parser.parse_args()

    ano_fim = args.ano_fim if args.ano_fim is not None else date.today().year
    ano_fim = min(ano_fim, 2030)

    # Se nenhum passo explícito, assumir fluxo completo quando passar --integrar-banco ou --executar-cruzamento
    run_bq = args.apenas_bigquery or args.integrar_banco or args.executar_cruzamento
    if not run_bq and not args.integrar_banco and not args.executar_cruzamento:
        run_bq = True
        args.integrar_banco = True
        args.executar_cruzamento = True
        logger.info("Nenhum passo especificado; executando fluxo completo (BigQuery + integrar + cruzamento).")

    logger.info("="*60)
    logger.info("COLETOR DE DADOS PÚBLICOS STANDALONE")
    logger.info("="*60)
    logger.info(f"Escala de tempo: {args.ano_inicio} a {ano_fim} (sem limite de linhas)" if not args.limite else f"Escala {args.ano_inicio}-{ano_fim}, limite={args.limite:,} linhas")
    logger.info(f"Integrar banco: {args.integrar_banco}")
    logger.info(f"Executar cruzamento: {args.executar_cruzamento}")

    registros = []
    if run_bq:
        registros = coletar_bigquery(ano_inicio=args.ano_inicio, ano_fim=ano_fim, limite_linhas=args.limite or 0)
        if not registros and args.integrar_banco:
            logger.warning("Nenhum registro do BigQuery; integração ignorada.")

    if args.integrar_banco and registros:
        integrar_banco(registros)

    if args.executar_cruzamento:
        executar_cruzamento()

    logger.info("="*60)
    logger.success("Processo finalizado.")
    logger.info("="*60)


if __name__ == "__main__":
    main()
