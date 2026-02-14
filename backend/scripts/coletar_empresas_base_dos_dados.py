"""
Script para coletar dados de empresas exportadoras/importadoras da Base dos Dados (BigQuery)
e salvar em arquivo Excel e/ou importar para PostgreSQL.

CREDENCIAIS (obrigatório para acessar o BigQuery):
    OPÇÃO 1 - No PC (PowerShell): aponte para o arquivo JSON da Service Account
        $env:GOOGLE_APPLICATION_CREDENTIALS="C:\\caminho\\para\\sua-conta-servico.json"
    OPÇÃO 2 - No Render: crie a variável GOOGLE_APPLICATION_CREDENTIALS_JSON com o
        conteúdo completo do JSON da Service Account.
    OPÇÃO 3 - Login local: gcloud auth application-default login

USO:
    cd backend
    python scripts/coletar_empresas_base_dos_dados.py
"""
import sys
from pathlib import Path
import os
from datetime import datetime
from loguru import logger
import pandas as pd

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# Carregar .env do backend para ter GOOGLE_APPLICATION_CREDENTIALS_JSON (e outras variáveis)
_env_file = backend_dir / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
        # Se o JSON no .env for multilinha, load_dotenv pode não carregar tudo; tentar ler manualmente
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip() == "{":
            raw = _env_file.read_text(encoding="utf-8", errors="replace")
            if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in raw:
                start = raw.find("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                start = raw.find("{", start)
                if start != -1:
                    depth = 0
                    end = start
                    for i, c in enumerate(raw[start:], start):
                        if c == "{": depth += 1
                        elif c == "}": depth -= 1
                        if depth == 0:
                            end = i
                            break
                    if end > start:
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = raw[start:end + 1]
    except Exception:
        pass

logger.info("="*80)
logger.info("COLETA DE EMPRESAS DA BASE DOS DADOS - ANO 2021")
logger.info("="*80)

# Query SQL para executar no BigQuery
QUERY_SQL = """
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
    dados.id_natureza_juridica AS id_natureza_juridica,
    diretorio_id_natureza_juridica.descricao AS id_natureza_juridica_descricao,
    dados.cnae_2_primaria AS cnae_2_primaria,
    diretorio_cnae_2_primaria.descricao_subclasse AS cnae_2_primaria_descricao_subclasse,
    diretorio_cnae_2_primaria.descricao_classe AS cnae_2_primaria_descricao_classe,
    diretorio_cnae_2_primaria.descricao_grupo AS cnae_2_primaria_descricao_grupo,
    diretorio_cnae_2_primaria.descricao_divisao AS cnae_2_primaria_descricao_divisao,
    diretorio_cnae_2_primaria.descricao_secao AS cnae_2_primaria_descricao_secao,
    dados.id_municipio AS id_municipio,
    diretorio_id_municipio.nome AS id_municipio_nome,
    dados.sigla_uf AS sigla_uf,
    diretorio_sigla_uf.nome AS sigla_uf_nome,
    dados.cep as cep,
    dados.bairro as bairro,
    dados.endereco as endereco,
    dados.numero as numero
FROM `basedosdados.br_me_exportadoras_importadoras.estabelecimentos` AS dados
LEFT JOIN `dicionario_id_exportacao_importacao`
    ON dados.id_exportacao_importacao = chave_id_exportacao_importacao
LEFT JOIN (SELECT DISTINCT id_natureza_juridica,descricao  FROM `basedosdados.br_bd_diretorios_brasil.natureza_juridica`) AS diretorio_id_natureza_juridica
    ON dados.id_natureza_juridica = diretorio_id_natureza_juridica.id_natureza_juridica
LEFT JOIN (SELECT DISTINCT subclasse,descricao_subclasse,descricao_classe,descricao_grupo,descricao_divisao,descricao_secao  FROM `basedosdados.br_bd_diretorios_brasil.cnae_2`) AS diretorio_cnae_2_primaria
    ON dados.cnae_2_primaria = diretorio_cnae_2_primaria.subclasse
LEFT JOIN (SELECT DISTINCT id_municipio,nome  FROM `basedosdados.br_bd_diretorios_brasil.municipio`) AS diretorio_id_municipio
    ON dados.id_municipio = diretorio_id_municipio.id_municipio
LEFT JOIN (SELECT DISTINCT sigla,nome  FROM `basedosdados.br_bd_diretorios_brasil.uf`) AS diretorio_sigla_uf
    ON dados.sigla_uf = diretorio_sigla_uf.sigla
WHERE dados.ano = 2021
"""


def _get_bigquery_client():
    """Cria cliente BigQuery usando credenciais de GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_CREDENTIALS_JSON."""
    from google.cloud import bigquery
    from google.oauth2 import service_account
    import json

    # 1) Credenciais via JSON em variável de ambiente (útil para Render/CI)
    json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if json_str and json_str.strip():
        try:
            info = json.loads(json_str)
            creds = service_account.Credentials.from_service_account_info(info)
            return bigquery.Client(credentials=creds, project=info.get("project_id"))
        except Exception as e:
            logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS_JSON inválido: {e}. Tentando outras opções.")

    # 2) Caminho para arquivo JSON (padrão)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.isfile(creds_path):
        return bigquery.Client.from_service_account_json(creds_path)

    # 3) Sem credenciais configuradas
    return None


def coletar_dados_bigquery():
    """Coleta dados do BigQuery usando a query SQL."""
    try:
        from google.cloud import bigquery
        from google.auth.exceptions import DefaultCredentialsError

        logger.info("🔌 Conectando ao BigQuery...")

        # Tentar obter cliente com credenciais configuradas
        client = _get_bigquery_client()
        if client is None:
            try:
                client = bigquery.Client()
            except DefaultCredentialsError:
                logger.error("❌ Credenciais do Google Cloud não encontradas.")
                logger.info("")
                logger.info("Configure de uma das formas abaixo:")
                logger.info("")
                logger.info("  OPÇÃO 1 - Arquivo JSON (recomendado no PC):")
                logger.info("    1. No Google Cloud Console, crie uma Service Account e baixe o JSON.")
                logger.info("    2. No PowerShell:")
                logger.info('       $env:GOOGLE_APPLICATION_CREDENTIALS="C:\\caminho\\para\\sua-conta-servico.json"')
                logger.info("    3. Rode o script de novo.")
                logger.info("")
                logger.info("  OPÇÃO 2 - Variável com JSON (útil no Render):")
                logger.info('    No Render, crie a variável GOOGLE_APPLICATION_CREDENTIALS_JSON')
                logger.info("    com o conteúdo do arquivo JSON da Service Account.")
                logger.info("")
                logger.info("  OPÇÃO 3 - Login local (gcloud):")
                logger.info("    Execute: gcloud auth application-default login")
                logger.info("")
                raise DefaultCredentialsError(
                    "Configure GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_CREDENTIALS_JSON. "
                    "Veja https://cloud.google.com/docs/authentication"
                )
        
        logger.info("📊 Executando query no BigQuery...")
        logger.info("⚠️ Esta operação pode demorar alguns minutos...")
        
        # Executar query
        query_job = client.query(QUERY_SQL)
        
        # Aguardar conclusão e obter resultados
        logger.info("⏳ Aguardando resultados...")
        results = query_job.result()
        
        # Converter para DataFrame
        logger.info("📋 Convertendo resultados para DataFrame...")
        df = results.to_dataframe()
        
        logger.success(f"✅ Query executada com sucesso!")
        logger.info(f"📊 Total de registros: {len(df):,}")
        
        return df
        
    except ImportError:
        logger.error("❌ Biblioteca google-cloud-bigquery não instalada!")
        logger.info("💡 Instale com: pip install google-cloud-bigquery")
        logger.info("💡 Configure credenciais: export GOOGLE_APPLICATION_CREDENTIALS='caminho/credenciais.json'")
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao executar query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def salvar_dados_excel(df, caminho_arquivo):
    """Salva dados em arquivo Excel."""
    try:
        logger.info(f"💾 Salvando dados em Excel: {caminho_arquivo}")
        
        # Criar diretório se não existir
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar em Excel
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        
        logger.success(f"✅ Dados salvos em: {caminho_arquivo}")
        logger.info(f"📊 Total de linhas: {len(df):,}")
        logger.info(f"📋 Total de colunas: {len(df.columns)}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar Excel: {e}")
        raise


def salvar_dados_csv(df, caminho_arquivo):
    """Salva dados em arquivo CSV."""
    try:
        logger.info(f"💾 Salvando dados em CSV: {caminho_arquivo}")
        
        # Criar diretório se não existir
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar em CSV
        df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
        
        logger.success(f"✅ Dados salvos em: {caminho_arquivo}")
        logger.info(f"📊 Total de linhas: {len(df):,}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar CSV: {e}")
        raise


def importar_para_postgresql(df):
    """Importa dados para PostgreSQL."""
    try:
        from database.database import SessionLocal
        from database.models import Empresa
        
        logger.info("🗄️ Importando dados para PostgreSQL...")
        
        db = SessionLocal()
        
        try:
            registros_inseridos = 0
            
            for idx, row in df.iterrows():
                try:
                    # Determinar tipo baseado em id_exportacao_importacao
                    id_exp_imp = str(row.get('id_exportacao_importacao', '')).lower()
                    
                    if 'exportadora' in id_exp_imp and 'importadora' in id_exp_imp:
                        tipo = 'ambos'
                    elif 'exportadora' in id_exp_imp:
                        tipo = 'exportadora'
                    elif 'importadora' in id_exp_imp:
                        tipo = 'importadora'
                    else:
                        tipo = 'ambos'  # Default
                    
                    # Limpar CNPJ (remover caracteres especiais)
                    cnpj = str(row.get('cnpj', '')).strip().replace('.', '').replace('/', '').replace('-', '')
                    
                    # Criar ou atualizar empresa
                    empresa = Empresa(
                        nome=str(row.get('razao_social', '')).strip(),
                        cnpj=cnpj if cnpj and len(cnpj) == 14 else None,
                        cnae=str(row.get('cnae_2_primaria', '')).strip()[:10] if pd.notna(row.get('cnae_2_primaria')) else None,
                        estado=str(row.get('sigla_uf', '')).strip()[:2] if pd.notna(row.get('sigla_uf')) else None,
                        tipo=tipo,
                        valor_importacao=0.0,  # Será preenchido depois com dados de comércio exterior
                        valor_exportacao=0.0,
                        arquivo_origem='base_dos_dados'
                    )
                    
                    db.add(empresa)
                    registros_inseridos += 1
                    
                    # Commit a cada 1000 registros
                    if registros_inseridos % 1000 == 0:
                        db.commit()
                        logger.info(f"  ⏳ Processadas {registros_inseridos:,} empresas...")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao processar linha {idx}: {e}")
                    continue
            
            db.commit()
            logger.success(f"✅ {registros_inseridos:,} empresas importadas para PostgreSQL")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao importar para PostgreSQL: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def main():
    """Função principal."""
    try:
        # Coletar dados do BigQuery
        df = coletar_dados_bigquery()
        
        if df.empty:
            logger.warning("⚠️ Nenhum dado retornado da query!")
            return
        
        # Mostrar estatísticas
        logger.info("\n" + "="*80)
        logger.info("📊 ESTATÍSTICAS DOS DADOS")
        logger.info("="*80)
        logger.info(f"Total de registros: {len(df):,}")
        logger.info(f"Total de colunas: {len(df.columns)}")
        logger.info(f"\nColunas disponíveis:")
        for col in df.columns:
            logger.info(f"  - {col}")
        
        # Estatísticas por tipo
        if 'id_exportacao_importacao' in df.columns:
            tipos = df['id_exportacao_importacao'].value_counts()
            logger.info(f"\nDistribuição por tipo:")
            for tipo, count in tipos.items():
                logger.info(f"  - {tipo}: {count:,}")
        
        # Estatísticas por estado
        if 'sigla_uf' in df.columns:
            estados = df['sigla_uf'].value_counts().head(10)
            logger.info(f"\nTop 10 estados:")
            for estado, count in estados.items():
                logger.info(f"  - {estado}: {count:,}")
        
        logger.info("="*80)
        
        # Salvar em Excel
        data_dir = backend_dir / "data"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_excel = data_dir / f"empresas_base_dos_dados_2021_{timestamp}.xlsx"
        salvar_dados_excel(df, arquivo_excel)
        
        # Salvar em CSV também
        arquivo_csv = data_dir / f"empresas_base_dos_dados_2021_{timestamp}.csv"
        salvar_dados_csv(df, arquivo_csv)
        
        # Importar automaticamente para PostgreSQL (dados de 2021)
        logger.info("\n" + "="*80)
        logger.info("🗄️ Importando dados de 2021 para PostgreSQL...")
        importar_para_postgresql(df)
        
        logger.success("\n" + "="*80)
        logger.success("✅ COLETA CONCLUÍDA COM SUCESSO!")
        logger.success("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro durante coleta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
