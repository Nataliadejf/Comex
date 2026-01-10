"""
Endpoint para coletar dados da Base dos Dados (BigQuery) e salvar no PostgreSQL.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, Any
import pandas as pd
from datetime import datetime

from database import get_db
from database.models import Empresa
from sqlalchemy import func

router = APIRouter(prefix="/api", tags=["coleta"])

# Query SQL para executar no BigQuery (apenas 2021)
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


def coletar_dados_bigquery():
    """Coleta dados do BigQuery usando a query SQL."""
    try:
        from google.cloud import bigquery
        
        logger.info("🔌 Conectando ao BigQuery...")
        
        # Inicializar cliente BigQuery
        client = bigquery.Client()
        
        logger.info("📊 Executando query no BigQuery (ano 2021)...")
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
        raise HTTPException(
            status_code=500,
            detail="Biblioteca google-cloud-bigquery não instalada. Configure GOOGLE_APPLICATION_CREDENTIALS no Render."
        )
    except Exception as e:
        logger.error(f"❌ Erro ao executar query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar query no BigQuery: {str(e)}"
        )


def importar_para_postgresql(df: pd.DataFrame, db: Session):
    """Importa dados para PostgreSQL."""
    try:
        logger.info("🗄️ Importando dados para PostgreSQL...")
        
        registros_inseridos = 0
        registros_atualizados = 0
        
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
                
                # Verificar se empresa já existe
                empresa_existente = None
                if cnpj and len(cnpj) == 14:
                    empresa_existente = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
                
                # Se não encontrar por CNPJ, tentar por nome
                if not empresa_existente:
                    razao_social = str(row.get('razao_social', '')).strip()
                    if razao_social:
                        empresa_existente = db.query(Empresa).filter(
                            Empresa.nome.ilike(f"%{razao_social}%")
                        ).first()
                
                if empresa_existente:
                    # Atualizar empresa existente
                    empresa_existente.nome = str(row.get('razao_social', '')).strip() or empresa_existente.nome
                    empresa_existente.cnpj = cnpj if cnpj and len(cnpj) == 14 else empresa_existente.cnpj
                    empresa_existente.cnae = str(row.get('cnae_2_primaria', '')).strip()[:10] if pd.notna(row.get('cnae_2_primaria')) else empresa_existente.cnae
                    empresa_existente.estado = str(row.get('sigla_uf', '')).strip()[:2] if pd.notna(row.get('sigla_uf')) else empresa_existente.estado
                    empresa_existente.tipo = tipo
                    empresa_existente.arquivo_origem = 'base_dos_dados_2021'
                    registros_atualizados += 1
                else:
                    # Criar nova empresa
                    empresa = Empresa(
                        nome=str(row.get('razao_social', '')).strip(),
                        cnpj=cnpj if cnpj and len(cnpj) == 14 else None,
                        cnae=str(row.get('cnae_2_primaria', '')).strip()[:10] if pd.notna(row.get('cnae_2_primaria')) else None,
                        estado=str(row.get('sigla_uf', '')).strip()[:2] if pd.notna(row.get('sigla_uf')) else None,
                        tipo=tipo,
                        valor_importacao=0.0,
                        valor_exportacao=0.0,
                        arquivo_origem='base_dos_dados_2021'
                    )
                    db.add(empresa)
                    registros_inseridos += 1
                
                # Commit a cada 1000 registros
                if (registros_inseridos + registros_atualizados) % 1000 == 0:
                    db.commit()
                    logger.info(f"  ⏳ Processadas {registros_inseridos + registros_atualizados:,} empresas...")
            
            except Exception as e:
                logger.error(f"❌ Erro ao processar linha {idx}: {e}")
                continue
        
        db.commit()
        logger.success(f"✅ {registros_inseridos:,} empresas inseridas")
        logger.success(f"✅ {registros_atualizados:,} empresas atualizadas")
        
        return registros_inseridos, registros_atualizados
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar para PostgreSQL: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao importar para PostgreSQL: {str(e)}"
        )


@router.post("/coletar-empresas-base-dados")
async def coletar_empresas_base_dados(db: Session = Depends(get_db)):
    """
    Coleta dados de empresas exportadoras/importadoras da Base dos Dados (BigQuery)
    e importa automaticamente para PostgreSQL.
    
    Requer:
    - GOOGLE_APPLICATION_CREDENTIALS configurado no Render Dashboard
    - BigQuery API habilitada no projeto Google Cloud
    
    Retorna:
    - Total de registros coletados
    - Total de empresas inseridas/atualizadas
    """
    try:
        logger.info("="*80)
        logger.info("INICIANDO COLETA DE EMPRESAS DA BASE DOS DADOS - ANO 2021")
        logger.info("="*80)
        
        # Coletar dados do BigQuery
        df = coletar_dados_bigquery()
        
        if df.empty:
            return {
                "success": False,
                "message": "Nenhum dado retornado da query",
                "total_registros": 0,
                "empresas_inseridas": 0,
                "empresas_atualizadas": 0
            }
        
        # Estatísticas
        total_registros = len(df)
        
        # Estatísticas por tipo
        tipos_stats = {}
        if 'id_exportacao_importacao' in df.columns:
            tipos_stats = df['id_exportacao_importacao'].value_counts().to_dict()
        
        # Estatísticas por estado
        estados_stats = {}
        if 'sigla_uf' in df.columns:
            estados_stats = df['sigla_uf'].value_counts().head(10).to_dict()
        
        # Importar para PostgreSQL
        empresas_inseridas, empresas_atualizadas = importar_para_postgresql(df, db)
        
        # Verificar total no banco após importação
        total_no_banco = db.query(func.count(Empresa.id)).scalar() or 0
        
        logger.success("="*80)
        logger.success("✅ COLETA E IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.success("="*80)
        
        return {
            "success": True,
            "message": "Dados coletados e importados com sucesso",
            "total_registros_coletados": total_registros,
            "empresas_inseridas": empresas_inseridas,
            "empresas_atualizadas": empresas_atualizadas,
            "total_empresas_no_banco": total_no_banco,
            "estatisticas": {
                "por_tipo": tipos_stats,
                "top_10_estados": estados_stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro durante coleta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante coleta: {str(e)}"
        )
