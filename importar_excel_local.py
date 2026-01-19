"""
Script para importar arquivo Excel diretamente no banco de dados.
Execute localmente: python importar_excel_local.py

IMPORTANTE: Configure DATABASE_URL antes de executar!
- Opção 1: Variável de ambiente: $env:DATABASE_URL = "postgresql://..."
- Opção 2: Arquivo .env na raiz do projeto com: DATABASE_URL=postgresql://...
"""
import os
import sys
import re
from datetime import date
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Adicionar o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Carregar variáveis de ambiente do .env se existir
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Arquivo .env carregado: {env_path}")
except ImportError:
    pass

# Verificar DATABASE_URL antes de importar
database_url = os.getenv("DATABASE_URL", "")
if database_url:
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        print(f"✅ Usando PostgreSQL: {database_url[:30]}...")
    elif database_url.startswith("sqlite:///"):
        print(f"⚠️ Usando SQLite local: {database_url}")
        print("   Para importar no Render, configure DATABASE_URL com a URL do PostgreSQL!")
else:
    print("⚠️ DATABASE_URL não configurada. Usando SQLite local como padrão.")
    print("   Para importar no Render, configure DATABASE_URL com a URL do PostgreSQL!")

from database.database import SessionLocal
from database.models import OperacaoComex, TipoOperacao, ViaTransporte
from loguru import logger

# Configurar logger
logger.add("importacao_local.log", rotation="10 MB", level="INFO")


def importar_excel_comex(caminho_arquivo: str):
    """
    Importa arquivo Excel diretamente no banco de dados.
    """
    db = SessionLocal()
    
    try:
        logger.info(f"🔄 Iniciando importação de: {caminho_arquivo}")
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        # Ler Excel
        logger.info("📖 Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
        
        # Detectar ano pelo nome do arquivo
        nome_arquivo = os.path.basename(caminho_arquivo)
        ano_match = re.search(r'20\d{2}', nome_arquivo)
        ano = int(ano_match.group()) if ano_match else date.today().year
        logger.info(f"📅 Ano detectado: {ano}")
        
        operacoes_para_inserir = []
        
        meses_map = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        stats = {
            "total_registros": 0,
            "importacoes": 0,
            "exportacoes": 0,
            "erros": 0,
            "linhas_processadas": 0
        }
        
        # Processar linhas
        logger.info("🔄 Processando linhas...")
        for idx, row in df.iterrows():
            stats["linhas_processadas"] += 1
            
            try:
                # Extrair NCM
                ncm = str(row.get('Código NCM', '')).strip() if pd.notna(row.get('Código NCM')) else None
                if not ncm or len(ncm) < 4:
                    continue
                
                ncm_normalizado = ncm[:8] if len(ncm) >= 8 else ncm.zfill(8)
                descricao = str(row.get('Descrição NCM', '')).strip()[:500] if pd.notna(row.get('Descrição NCM')) else ''
                uf = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
                pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
                
                # Extrair via de transporte (sempre definir um valor padrão)
                via_str = str(row.get('Via', '')).strip() if pd.notna(row.get('Via')) else ''
                via_transporte = ViaTransporte.MARITIMA  # Default sempre MARITIMA
                
                if via_str and via_str != '' and via_str.lower() != 'nan':
                    via_upper = via_str.upper()
                    if 'MAR' in via_upper or 'MARÍTIMA' in via_upper or 'MARITIMA' in via_upper:
                        via_transporte = ViaTransporte.MARITIMA
                    elif 'AÉR' in via_upper or 'AEREO' in via_upper or 'AEREO' in via_upper:
                        via_transporte = ViaTransporte.AEREA
                    elif 'ROD' in via_upper or 'RODOVIÁRIA' in via_upper or 'RODOVIARIA' in via_upper:
                        via_transporte = ViaTransporte.RODOVIARIA
                    elif 'FER' in via_upper or 'FERROVIÁRIA' in via_upper or 'FERROVIARIA' in via_upper:
                        via_transporte = ViaTransporte.FERROVIARIA
                    elif 'FLU' in via_upper or 'FLUVIAL' in via_upper:
                        via_transporte = ViaTransporte.FLUVIA
                    elif 'DUT' in via_upper or 'DUTOVIÁRIA' in via_upper or 'DUTOVIARIA' in via_upper:
                        via_transporte = ViaTransporte.DUTOVIARIA
                    elif 'POST' in via_upper:
                        via_transporte = ViaTransporte.POSTAL
                # Se não encontrar ou estiver vazio, mantém o default MARITIMA
                
                # Processar mês
                mes_str = str(row.get('Mês', '')).strip() if pd.notna(row.get('Mês')) else ''
                mes = None
                
                if mes_str:
                    match = re.search(r'(\d{1,2})', mes_str)
                    if match:
                        mes = int(match.group(1))
                    else:
                        for nome, num in meses_map.items():
                            if nome in mes_str.lower():
                                mes = num
                                break
                
                if not mes or mes < 1 or mes > 12:
                    mes = 1
                
                data_operacao = date(ano, mes, 1)
                mes_referencia = f"{ano}-{mes:02d}"
                
                # Processar EXPORTAÇÃO
                valor_exp = (
                    row.get('Exportação - 2025 - Valor US$ FOB', 0) or 
                    row.get('Exportação - Valor US$ FOB', 0) or 
                    row.get('Valor Exportação', 0) or
                    row.get('Exportação Valor', 0)
                )
                peso_exp = (
                    row.get('Exportação - 2025 - Quilograma Líquido', 0) or 
                    row.get('Exportação - Quilograma Líquido', 0) or 
                    row.get('Peso Exportação', 0) or
                    row.get('Exportação Peso', 0)
                )
                
                if pd.notna(valor_exp) and float(valor_exp) > 0:
                    operacoes_para_inserir.append({
                        'ncm': ncm_normalizado,
                        'descricao_produto': descricao,
                        'tipo_operacao': TipoOperacao.EXPORTACAO,
                        'uf': uf,
                        'pais_origem_destino': pais,
                        'via_transporte': via_transporte,  # Sempre incluir via_transporte
                        'valor_fob': float(valor_exp),
                        'peso_liquido_kg': float(peso_exp) if pd.notna(peso_exp) else 0,
                        'data_operacao': data_operacao,
                        'mes_referencia': mes_referencia,
                        'arquivo_origem': nome_arquivo
                    })
                    stats["exportacoes"] += 1
                    stats["total_registros"] += 1
                
                # Processar IMPORTAÇÃO
                valor_imp = (
                    row.get('Importação - 2025 - Valor US$ FOB', 0) or 
                    row.get('Importação - Valor US$ FOB', 0) or 
                    row.get('Valor Importação', 0) or
                    row.get('Importação Valor', 0)
                )
                peso_imp = (
                    row.get('Importação - 2025 - Quilograma Líquido', 0) or 
                    row.get('Importação - Quilograma Líquido', 0) or 
                    row.get('Peso Importação', 0) or
                    row.get('Importação Peso', 0)
                )
                
                if pd.notna(valor_imp) and float(valor_imp) > 0:
                    operacoes_para_inserir.append({
                        'ncm': ncm_normalizado,
                        'descricao_produto': descricao,
                        'tipo_operacao': TipoOperacao.IMPORTACAO,
                        'uf': uf,
                        'pais_origem_destino': pais,
                        'via_transporte': via_transporte,  # Sempre incluir via_transporte
                        'valor_fob': float(valor_imp),
                        'peso_liquido_kg': float(peso_imp) if pd.notna(peso_imp) else 0,
                        'data_operacao': data_operacao,
                        'mes_referencia': mes_referencia,
                        'arquivo_origem': nome_arquivo
                    })
                    stats["importacoes"] += 1
                    stats["total_registros"] += 1
            
            except Exception as e:
                logger.warning(f"Erro na linha {idx}: {e}")
                stats["erros"] += 1
                continue
            
            # Log de progresso a cada 1000 linhas
            if stats["linhas_processadas"] % 1000 == 0:
                logger.info(f"  📊 Processadas {stats['linhas_processadas']} linhas... ({len(operacoes_para_inserir)} operações preparadas)")
        
        # Bulk Insert em chunks de 1000
        logger.info(f"💾 Inserindo {len(operacoes_para_inserir)} operações no banco...")
        
        for i in range(0, len(operacoes_para_inserir), 1000):
            chunk = operacoes_para_inserir[i:i + 1000]
            
            try:
                db.bulk_insert_mappings(OperacaoComex, chunk)
                db.commit()
                logger.info(f"  ✅ Inseridos {min(i + 1000, len(operacoes_para_inserir))}/{len(operacoes_para_inserir)} registros")
            
            except SQLAlchemyError as e:
                logger.error(f"❌ Erro no chunk {i}-{i+1000}: {e}")
                db.rollback()
                
                # Tentar inserir um por um apenas se o chunk falhar
                logger.info(f"  Tentando inserir individualmente...")
                inseridos_individuais = 0
                for item in chunk:
                    try:
                        db.bulk_insert_mappings(OperacaoComex, [item])
                        db.commit()
                        inseridos_individuais += 1
                    except Exception as e2:
                        logger.error(f"Registro inválido: {item.get('ncm', 'N/A')} - {e2}")
                        db.rollback()
                
                logger.info(f"  ✅ Inseridos {inseridos_individuais}/{len(chunk)} registros individualmente")
        
        logger.success(f"✅ Importação concluída!")
        logger.info(f"📊 Estatísticas:")
        logger.info(f"  - Linhas processadas: {stats['linhas_processadas']}")
        logger.info(f"  - Total de registros inseridos: {stats['total_registros']}")
        logger.info(f"  - Importações: {stats['importacoes']}")
        logger.info(f"  - Exportações: {stats['exportacoes']}")
        logger.info(f"  - Erros: {stats['erros']}")
        
        return stats
    
    except Exception as e:
        logger.error(f"❌ Falha crítica na importação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    
    finally:
        db.close()


def importar_cnae(caminho_arquivo: str):
    """
    Importa arquivo CNAE diretamente no banco de dados.
    """
    db = SessionLocal()
    
    try:
        logger.info(f"🔄 Iniciando importação CNAE de: {caminho_arquivo}")
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        # Ler Excel
        logger.info("📖 Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo)
        logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
        
        from database.models import CNAEHierarquia
        
        stats = {
            "total_registros": 0,
            "inseridos": 0,
            "atualizados": 0,
            "erros": 0
        }
        
        # Buscar CNAEs existentes
        logger.info("🔍 Verificando CNAEs existentes...")
        existentes_db = db.query(CNAEHierarquia.cnae).all()
        cnae_existentes = {row[0] for row in existentes_db}
        logger.info(f"  Encontrados {len(cnae_existentes)} CNAEs existentes")
        
        cnae_para_inserir = []
        
        for idx, row in df.iterrows():
            try:
                # Extrair CNAE
                cnae = (
                    str(row.get('CNAE', '')) or
                    str(row.get('Código CNAE', '')) or
                    str(row.get('CNAE 2.0', '')) or
                    str(row.get('Subclasse', ''))
                ).strip()
                
                if not cnae or cnae == 'nan' or len(cnae) < 4:
                    continue
                
                cnae_limpo = cnae.replace('.', '').replace('-', '').strip()
                
                descricao = (
                    str(row.get('Descrição', '')) or
                    str(row.get('Descrição Subclasse', '')) or
                    str(row.get('Descrição CNAE', ''))
                ).strip()[:500]
                
                classe = str(row.get('Classe', '')).strip()[:10] if pd.notna(row.get('Classe')) else None
                grupo = str(row.get('Grupo', '')).strip()[:10] if pd.notna(row.get('Grupo')) else None
                divisao = str(row.get('Divisão', '')).strip()[:10] if pd.notna(row.get('Divisão')) else None
                secao = str(row.get('Seção', '')).strip()[:10] if pd.notna(row.get('Seção')) else None
                
                # Verificar se existe
                if cnae_limpo in cnae_existentes:
                    stats["atualizados"] += 1
                    existente = db.query(CNAEHierarquia).filter(
                        CNAEHierarquia.cnae == cnae_limpo
                    ).first()
                    
                    if existente:
                        if descricao:
                            existente.descricao = descricao
                        if classe:
                            existente.classe = classe
                        if grupo:
                            existente.grupo = grupo
                        if divisao:
                            existente.divisao = divisao
                        if secao:
                            existente.secao = secao
                else:
                    cnae_para_inserir.append({
                        'cnae': cnae_limpo,
                        'descricao': descricao,
                        'classe': classe,
                        'grupo': grupo,
                        'divisao': divisao,
                        'secao': secao
                    })
                    cnae_existentes.add(cnae_limpo)
                    stats["inseridos"] += 1
                
                stats["total_registros"] += 1
            
            except Exception as e:
                logger.warning(f"Erro na linha {idx}: {e}")
                stats["erros"] += 1
                continue
        
        # Commit atualizações
        if stats["atualizados"] > 0:
            try:
                db.commit()
                logger.info(f"✅ {stats['atualizados']} registros atualizados")
            except SQLAlchemyError as e:
                logger.error(f"Erro ao commitar atualizações: {e}")
                db.rollback()
        
        # Bulk insert novos
        if cnae_para_inserir:
            logger.info(f"💾 Inserindo {len(cnae_para_inserir)} novos CNAEs...")
            
            for i in range(0, len(cnae_para_inserir), 1000):
                chunk = cnae_para_inserir[i:i + 1000]
                try:
                    db.bulk_insert_mappings(CNAEHierarquia, chunk)
                    db.commit()
                    logger.info(f"  ✅ Inseridos {min(i + 1000, len(cnae_para_inserir))}/{len(cnae_para_inserir)} registros")
                except SQLAlchemyError as e:
                    logger.error(f"Erro ao inserir chunk: {e}")
                    db.rollback()
        
        logger.success(f"✅ Importação CNAE concluída!")
        logger.info(f"📊 Estatísticas:")
        logger.info(f"  - Total de registros: {stats['total_registros']}")
        logger.info(f"  - Inseridos: {stats['inseridos']}")
        logger.info(f"  - Atualizados: {stats['atualizados']}")
        logger.info(f"  - Erros: {stats['erros']}")
        
        return stats
    
    except Exception as e:
        logger.error(f"❌ Falha crítica na importação CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Importar arquivos Excel diretamente no banco de dados")
    parser.add_argument("arquivo", help="Caminho do arquivo Excel para importar")
    parser.add_argument("--tipo", choices=["comex", "cnae"], default="comex", help="Tipo de arquivo (comex ou cnae)")
    
    args = parser.parse_args()
    
    try:
        if args.tipo == "comex":
            importar_excel_comex(args.arquivo)
        else:
            importar_cnae(args.arquivo)
        
        logger.success("✅ Importação concluída com sucesso!")
    
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        sys.exit(1)
