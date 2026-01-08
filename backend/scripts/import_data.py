"""
Script para importar dados dos arquivos Excel para PostgreSQL.

USO:
    Localmente:
        python backend/scripts/import_data.py
    
    No Render Shell:
        cd /opt/render/project/src/backend
        python scripts/import_data.py
"""
import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime, date
from loguru import logger
from sqlalchemy import func, text

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal, init_db, engine
from database.models import (
    ComercioExterior, Empresa, CNAEHierarquia,
    Base
)


def parse_mes(mes_str):
    """Converte string de mês (ex: '12. Dezembro') para número."""
    if pd.isna(mes_str):
        return None
    
    mes_str = str(mes_str).strip()
    # Extrair número do início (ex: "12. Dezembro" -> 12)
    try:
        mes_num = int(mes_str.split('.')[0])
        if 1 <= mes_num <= 12:
            return mes_num
    except:
        pass
    
    # Mapeamento de nomes
    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
        'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9,
        'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    for nome, num in meses_map.items():
        if nome in mes_str.lower():
            return num
    
    return None


def importar_dados_comex(db, arquivo_excel):
    """Importa dados de comércio exterior do Excel para PostgreSQL."""
    logger.info("="*80)
    logger.info("IMPORTANDO DADOS DE COMÉRCIO EXTERIOR")
    logger.info("="*80)
    
    if not arquivo_excel.exists():
        logger.error(f"Arquivo não encontrado: {arquivo_excel}")
        return 0
    
    logger.info(f"Lendo arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Verificar colunas esperadas
    colunas_esperadas = [
        'Mês', 'Código NCM', 'Descrição NCM', 'UF do Produto', 'Países',
        'Exportação - 2025 - Valor US$ FOB', 'Exportação - 2025 - Quilograma Líquido',
        'Importação - 2025 - Valor US$ FOB', 'Importação - 2025 - Quilograma Líquido'
    ]
    
    colunas_faltando = [c for c in colunas_esperadas if c not in df.columns]
    if colunas_faltando:
        logger.warning(f"Colunas faltando: {colunas_faltando}")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
    
    registros_inseridos = 0
    ano = 2025  # Ano fixo do arquivo
    
    # Processar linha por linha
    for idx, row in df.iterrows():
        try:
            # Parse do mês
            mes_str = row.get('Mês', '')
            mes = parse_mes(mes_str)
            if not mes:
                continue
            
            # Dados básicos
            ncm = str(row.get('Código NCM', '')).strip()
            descricao_ncm = str(row.get('Descrição NCM', '')).strip()
            estado = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
            pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
            
            # Criar data (usar primeiro dia do mês)
            try:
                data_operacao = date(ano, mes, 1)
            except:
                continue
            
            mes_referencia = f"{ano}-{mes:02d}"
            
            # Processar EXPORTAÇÃO
            valor_exp = row.get('Exportação - 2025 - Valor US$ FOB', 0)
            peso_exp = row.get('Exportação - 2025 - Quilograma Líquido', 0)
            qtd_exp = row.get('Exportação - 2025 - Quantidade Estatística', 0)
            
            if pd.notna(valor_exp) and float(valor_exp) > 0:
                registro_exp = ComercioExterior(
                    tipo='exportacao',
                    ncm=ncm,
                    descricao_ncm=descricao_ncm,
                    estado=estado,
                    pais=pais,
                    valor_usd=float(valor_exp),
                    peso_kg=float(peso_exp) if pd.notna(peso_exp) else None,
                    quantidade=float(qtd_exp) if pd.notna(qtd_exp) else None,
                    data=data_operacao,
                    mes=mes,
                    ano=ano,
                    mes_referencia=mes_referencia,
                    arquivo_origem=arquivo_excel.name
                )
                db.add(registro_exp)
                registros_inseridos += 1
            
            # Processar IMPORTAÇÃO
            valor_imp = row.get('Importação - 2025 - Valor US$ FOB', 0)
            peso_imp = row.get('Importação - 2025 - Quilograma Líquido', 0)
            qtd_imp = row.get('Importação - 2025 - Quantidade Estatística', 0)
            
            if pd.notna(valor_imp) and float(valor_imp) > 0:
                registro_imp = ComercioExterior(
                    tipo='importacao',
                    ncm=ncm,
                    descricao_ncm=descricao_ncm,
                    estado=estado,
                    pais=pais,
                    valor_usd=float(valor_imp),
                    peso_kg=float(peso_imp) if pd.notna(peso_imp) else None,
                    quantidade=float(qtd_imp) if pd.notna(qtd_imp) else None,
                    data=data_operacao,
                    mes=mes,
                    ano=ano,
                    mes_referencia=mes_referencia,
                    arquivo_origem=arquivo_excel.name
                )
                db.add(registro_imp)
                registros_inseridos += 1
            
            # Commit a cada 1000 registros
            if registros_inseridos % 1000 == 0:
                db.commit()
                logger.info(f"  Processados {registros_inseridos} registros...")
        
        except Exception as e:
            logger.error(f"Erro ao processar linha {idx}: {e}")
            continue
    
    db.commit()
    logger.success(f"✅ Importação concluída: {registros_inseridos} registros inseridos")
    return registros_inseridos


def importar_empresas(db, arquivo_excel):
    """Importa dados de empresas do Excel para PostgreSQL."""
    logger.info("="*80)
    logger.info("IMPORTANDO DADOS DE EMPRESAS")
    logger.info("="*80)
    
    if not arquivo_excel.exists():
        logger.warning(f"Arquivo não encontrado: {arquivo_excel}")
        return 0
    
    logger.info(f"Lendo arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
    logger.info(f"Colunas disponíveis: {list(df.columns)}")
    
    registros_inseridos = 0
    
    for idx, row in df.iterrows():
        try:
            # Tentar diferentes nomes de colunas
            nome = (
                str(row.get('Razão Social', '')) or
                str(row.get('Nome', '')) or
                str(row.get('Empresa', '')) or
                str(row.get('Nome Fantasia', ''))
            ).strip()
            
            if not nome or nome == 'nan':
                continue
            
            cnpj = str(row.get('CNPJ', '')).strip() if pd.notna(row.get('CNPJ')) else None
            cnae = str(row.get('CNAE', '')).strip() if pd.notna(row.get('CNAE')) else None
            estado = str(row.get('Estado', '')).strip()[:2] if pd.notna(row.get('Estado')) else None
            
            # Determinar tipo (importadora, exportadora, ambos)
            valor_imp = float(row.get('Valor Importação', 0) or row.get('Importado (R$)', 0) or 0)
            valor_exp = float(row.get('Valor Exportação', 0) or row.get('Exportado (R$)', 0) or 0)
            
            if valor_imp > 0 and valor_exp > 0:
                tipo = 'ambos'
            elif valor_imp > 0:
                tipo = 'importadora'
            elif valor_exp > 0:
                tipo = 'exportadora'
            else:
                tipo = 'importadora'  # Default
            
            # Verificar se empresa já existe (por CNPJ ou nome)
            empresa_existente = None
            if cnpj:
                empresa_existente = db.query(Empresa).filter(Empresa.cnpj == cnpj).first()
            
            if not empresa_existente:
                empresa_existente = db.query(Empresa).filter(Empresa.nome == nome).first()
            
            if empresa_existente:
                # Atualizar valores
                empresa_existente.valor_importacao = max(empresa_existente.valor_importacao or 0, valor_imp)
                empresa_existente.valor_exportacao = max(empresa_existente.valor_exportacao or 0, valor_exp)
                if cnae and not empresa_existente.cnae:
                    empresa_existente.cnae = cnae
                if estado and not empresa_existente.estado:
                    empresa_existente.estado = estado
            else:
                # Criar nova empresa
                empresa = Empresa(
                    nome=nome,
                    cnpj=cnpj if cnpj and cnpj != 'nan' else None,
                    cnae=cnae if cnae and cnae != 'nan' else None,
                    estado=estado,
                    tipo=tipo,
                    valor_importacao=valor_imp,
                    valor_exportacao=valor_exp,
                    arquivo_origem=arquivo_excel.name
                )
                db.add(empresa)
                registros_inseridos += 1
            
            # Commit a cada 100 registros
            if registros_inseridos % 100 == 0:
                db.commit()
                logger.info(f"  Processadas {registros_inseridos} empresas...")
        
        except Exception as e:
            logger.error(f"Erro ao processar empresa linha {idx}: {e}")
            continue
    
    db.commit()
    logger.success(f"✅ Importação de empresas concluída: {registros_inseridos} empresas inseridas/atualizadas")
    return registros_inseridos


def importar_cnae(db, arquivo_cnae=None):
    """Importa hierarquia CNAE (opcional)."""
    logger.info("="*80)
    logger.info("IMPORTANDO HIERARQUIA CNAE")
    logger.info("="*80)
    
    if not arquivo_cnae or not arquivo_cnae.exists():
        logger.warning("Arquivo CNAE não fornecido ou não encontrado. Pulando importação de CNAE.")
        logger.info("💡 Dica: Você pode criar manualmente a hierarquia CNAE ou usar uma API externa.")
        return 0
    
    logger.info(f"Lendo arquivo CNAE: {arquivo_cnae.name}")
    # Implementar leitura do arquivo CNAE se necessário
    logger.warning("Importação de CNAE ainda não implementada completamente.")
    return 0


def main():
    """Função principal de importação."""
    logger.info("="*80)
    logger.info("INICIANDO IMPORTAÇÃO DE DADOS PARA POSTGRESQL")
    logger.info("="*80)
    
    # Criar todas as tabelas
    logger.info("Criando/verificando tabelas no banco de dados...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("✅ Tabelas criadas/verificadas")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        # Tentar executar schema.sql diretamente
        try:
            schema_file = backend_dir / "database" / "schema.sql"
            if schema_file.exists():
                logger.info("Tentando executar schema.sql diretamente...")
                with engine.connect() as conn:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        conn.execute(text(f.read()))
                    conn.commit()
                logger.success("✅ Tabelas criadas via schema.sql")
        except Exception as e2:
            logger.error(f"Erro ao executar schema.sql: {e2}")
            raise
    
    # Caminhos dos arquivos (tentar múltiplos locais)
    base_dir = backend_dir.parent
    arquivo_comex = None
    arquivo_empresas = None
    
    # Tentar caminhos locais primeiro
    caminhos_comex = [
        base_dir / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx",
        backend_dir / "data" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx",
        Path("/opt/render/project/src/comex_data/comexstat_csv/H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"),
        Path("/opt/render/project/src/backend/data/H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"),
    ]
    
    caminhos_empresas = [
        base_dir / "comex_data" / "comexstat_csv" / "Empresas Importadoras e Exportadoras.xlsx",
        backend_dir / "data" / "Empresas Importadoras e Exportadoras.xlsx",
        Path("/opt/render/project/src/comex_data/comexstat_csv/Empresas Importadoras e Exportadoras.xlsx"),
        Path("/opt/render/project/src/backend/data/Empresas Importadoras e Exportadoras.xlsx"),
    ]
    
    for caminho in caminhos_comex:
        if caminho.exists():
            arquivo_comex = caminho
            logger.info(f"✅ Arquivo Comex encontrado: {arquivo_comex}")
            break
    
    for caminho in caminhos_empresas:
        if caminho.exists():
            arquivo_empresas = caminho
            logger.info(f"✅ Arquivo Empresas encontrado: {arquivo_empresas}")
            break
    
    if not arquivo_comex:
        logger.warning("⚠️ Arquivo de comércio exterior não encontrado. Pulando importação...")
        logger.info("Caminhos tentados:")
        for caminho in caminhos_comex:
            logger.info(f"  - {caminho}")
    
    if not arquivo_empresas:
        logger.warning("⚠️ Arquivo de empresas não encontrado. Pulando importação...")
        logger.info("Caminhos tentados:")
        for caminho in caminhos_empresas:
            logger.info(f"  - {caminho}")
    
    db = SessionLocal()
    
    try:
        total_comex = 0
        total_empresas = 0
        
        # 1. Importar dados de comércio exterior
        if arquivo_comex:
            total_comex = importar_dados_comex(db, arquivo_comex)
        else:
            logger.warning("⚠️ Pulando importação de comércio exterior (arquivo não encontrado)")
        
        # 2. Importar empresas
        if arquivo_empresas:
            total_empresas = importar_empresas(db, arquivo_empresas)
        else:
            logger.warning("⚠️ Pulando importação de empresas (arquivo não encontrado)")
        
        # 3. Importar CNAE (opcional)
        # total_cnae = importar_cnae(db, arquivo_cnae)
        
        logger.info("="*80)
        logger.success("✅ IMPORTAÇÃO CONCLUÍDA!")
        logger.info(f"   - Registros de comércio exterior: {total_comex}")
        logger.info(f"   - Empresas: {total_empresas}")
        logger.info("="*80)
        
        if total_comex == 0 and total_empresas == 0:
            logger.warning("⚠️ Nenhum dado foi importado. Verifique se os arquivos Excel estão nos caminhos corretos.")
            logger.info("💡 Dica: Copie os arquivos Excel para backend/data/ ou comex_data/comexstat_csv/")
        
    except Exception as e:
        logger.error(f"❌ Erro durante importação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
