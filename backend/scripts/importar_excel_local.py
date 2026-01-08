"""
Script para importar dados dos arquivos Excel para SQLite LOCAL.
Depois use o script migrar_para_postgresql.py para enviar para PostgreSQL.

USO:
    python backend/scripts/importar_excel_local.py
"""
import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime, date
from loguru import logger

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# FORÇAR SQLite local (sem DATABASE_URL)
os.environ.pop("DATABASE_URL", None)

from database.database import SessionLocal, init_db, engine
from database.models import (
    ComercioExterior, Empresa, CNAEHierarquia,
    Base
)

# Garantir que está usando SQLite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_path = backend_dir.parent / "comex_data" / "database" / "comex.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
sqlite_url = f"sqlite:///{db_path.absolute()}"

# Recriar engine com SQLite
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas
Base.metadata.create_all(bind=engine)

logger.info("="*80)
logger.info("IMPORTAÇÃO PARA SQLITE LOCAL")
logger.info(f"Banco de dados: {db_path}")
logger.info("="*80)


def parse_mes(mes_str):
    """Converte string de mês (ex: '12. Dezembro') para número."""
    if pd.isna(mes_str):
        return None
    
    mes_str = str(mes_str).strip()
    try:
        mes_num = int(mes_str.split('.')[0])
        if 1 <= mes_num <= 12:
            return mes_num
    except:
        pass
    
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
    """Importa dados de comércio exterior do Excel para SQLite."""
    logger.info("="*80)
    logger.info("IMPORTANDO DADOS DE COMÉRCIO EXTERIOR")
    logger.info("="*80)
    
    if not arquivo_excel.exists():
        logger.error(f"❌ Arquivo não encontrado: {arquivo_excel}")
        return 0, 0, 0, 0
    
    logger.info(f"📄 Lendo arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Verificar colunas
    colunas_esperadas = [
        'Mês', 'Código NCM', 'Descrição NCM', 'UF do Produto', 'Países',
        'Exportação - 2025 - Valor US$ FOB', 'Exportação - 2025 - Quilograma Líquido',
        'Importação - 2025 - Valor US$ FOB', 'Importação - 2025 - Quilograma Líquido'
    ]
    
    colunas_faltando = [c for c in colunas_esperadas if c not in df.columns]
    if colunas_faltando:
        logger.warning(f"⚠️ Colunas faltando: {colunas_faltando}")
        logger.info(f"📋 Colunas disponíveis: {list(df.columns)}")
    
    registros_inseridos = 0
    total_valor_importacao = 0.0
    total_valor_exportacao = 0.0
    total_peso_importacao = 0.0
    total_peso_exportacao = 0.0
    ano = 2025
    
    # Limpar tabela antes de importar (opcional)
    db.query(ComercioExterior).delete()
    db.commit()
    logger.info("🗑️ Tabela limpa antes da importação")
    
    # Processar linha por linha
    for idx, row in df.iterrows():
        try:
            mes_str = row.get('Mês', '')
            mes = parse_mes(mes_str)
            if not mes:
                continue
            
            ncm = str(row.get('Código NCM', '')).strip()
            descricao_ncm = str(row.get('Descrição NCM', '')).strip()
            estado = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
            pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
            
            # Valores de exportação
            valor_exp = row.get('Exportação - 2025 - Valor US$ FOB', 0)
            peso_exp = row.get('Exportação - 2025 - Quilograma Líquido', 0)
            
            # Valores de importação
            valor_imp = row.get('Importação - 2025 - Valor US$ FOB', 0)
            peso_imp = row.get('Importação - 2025 - Quilograma Líquido', 0)
            
            # Converter para float
            try:
                valor_exp = float(valor_exp) if pd.notna(valor_exp) else 0.0
                peso_exp = float(peso_exp) if pd.notna(peso_exp) else 0.0
                valor_imp = float(valor_imp) if pd.notna(valor_imp) else 0.0
                peso_imp = float(peso_imp) if pd.notna(peso_imp) else 0.0
            except:
                continue
            
            # Criar data
            try:
                data_operacao = date(ano, mes, 1)
            except:
                continue
            
            mes_referencia = f"{ano}-{mes:02d}"
            
            # Inserir exportação
            if valor_exp > 0:
                registro_exp = ComercioExterior(
                    tipo='exportacao',
                    ncm=ncm,
                    descricao_ncm=descricao_ncm,
                    estado=estado,
                    pais=pais,
                    valor_usd=valor_exp,
                    peso_kg=peso_exp if peso_exp > 0 else None,
                    data=data_operacao,
                    mes=mes,
                    ano=ano,
                    mes_referencia=mes_referencia,
                    arquivo_origem=arquivo_excel.name
                )
                db.add(registro_exp)
                registros_inseridos += 1
                total_valor_exportacao += valor_exp
                total_peso_exportacao += peso_exp if peso_exp > 0 else 0
            
            # Inserir importação
            if valor_imp > 0:
                registro_imp = ComercioExterior(
                    tipo='importacao',
                    ncm=ncm,
                    descricao_ncm=descricao_ncm,
                    estado=estado,
                    pais=pais,
                    valor_usd=valor_imp,
                    peso_kg=peso_imp if peso_imp > 0 else None,
                    data=data_operacao,
                    mes=mes,
                    ano=ano,
                    mes_referencia=mes_referencia,
                    arquivo_origem=arquivo_excel.name
                )
                db.add(registro_imp)
                registros_inseridos += 1
                total_valor_importacao += valor_imp
                total_peso_importacao += peso_imp if peso_imp > 0 else 0
            
            # Commit a cada 1000 registros
            if registros_inseridos % 1000 == 0:
                db.commit()
                logger.info(f"  ⏳ Processados {registros_inseridos} registros...")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar linha {idx}: {e}")
            continue
    
    db.commit()
    
    logger.success("="*80)
    logger.success("✅ IMPORTAÇÃO DE COMÉRCIO EXTERIOR CONCLUÍDA")
    logger.success("="*80)
    logger.info(f"📊 Total de registros inseridos: {registros_inseridos:,}")
    logger.info(f"💰 Total Importação (USD): ${total_valor_importacao:,.2f}")
    logger.info(f"💰 Total Exportação (USD): ${total_valor_exportacao:,.2f}")
    logger.info(f"📦 Total Peso Importação (kg): {total_peso_importacao:,.2f}")
    logger.info(f"📦 Total Peso Exportação (kg): {total_peso_exportacao:,.2f}")
    logger.success("="*80)
    
    return registros_inseridos, total_valor_importacao, total_valor_exportacao, total_peso_importacao + total_peso_exportacao


def importar_dados_empresas(db, arquivo_excel):
    """Importa dados de empresas do Excel para SQLite."""
    logger.info("="*80)
    logger.info("IMPORTANDO DADOS DE EMPRESAS")
    logger.info("="*80)
    
    if not arquivo_excel.exists():
        logger.error(f"❌ Arquivo não encontrado: {arquivo_excel}")
        return 0
    
    logger.info(f"📄 Lendo arquivo Excel: {arquivo_excel.name}")
    df = pd.read_excel(arquivo_excel)
    logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Limpar tabela antes de importar (opcional)
    db.query(Empresa).delete()
    db.commit()
    logger.info("🗑️ Tabela limpa antes da importação")
    
    registros_inseridos = 0
    
    for idx, row in df.iterrows():
        try:
            nome = str(row.get('Nome', '') or row.get('Razão Social', '') or '').strip()
            cnpj = str(row.get('CNPJ', '') or '').strip()
            cnae = str(row.get('CNAE', '') or '').strip()
            estado = str(row.get('Estado', '') or row.get('UF', '') or '').strip()[:2]
            
            valor_imp = float(row.get('Valor Importação', 0) or row.get('Importação', 0) or 0)
            valor_exp = float(row.get('Valor Exportação', 0) or row.get('Exportação', 0) or 0)
            
            if not nome:
                continue
            
            # Determinar tipo
            if valor_imp > 0 and valor_exp > 0:
                tipo = 'ambos'
            elif valor_imp > 0:
                tipo = 'importadora'
            elif valor_exp > 0:
                tipo = 'exportadora'
            else:
                continue
            
            empresa = Empresa(
                nome=nome,
                cnpj=cnpj if cnpj else None,
                cnae=cnae if cnae else None,
                estado=estado if estado else None,
                tipo=tipo,
                valor_importacao=valor_imp,
                valor_exportacao=valor_exp,
                arquivo_origem=arquivo_excel.name
            )
            
            db.add(empresa)
            registros_inseridos += 1
            
            if registros_inseridos % 100 == 0:
                db.commit()
                logger.info(f"  ⏳ Processadas {registros_inseridos} empresas...")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar linha {idx}: {e}")
            continue
    
    db.commit()
    
    logger.success("="*80)
    logger.success("✅ IMPORTAÇÃO DE EMPRESAS CONCLUÍDA")
    logger.success("="*80)
    logger.info(f"📊 Total de empresas inseridas: {registros_inseridos:,}")
    logger.success("="*80)
    
    return registros_inseridos


def main():
    """Função principal."""
    db = SessionLocal()
    
    try:
        # Inicializar banco
        init_db()
        logger.info("✅ Banco de dados inicializado")
        
        # Caminhos dos arquivos Excel
        data_dir = backend_dir / "data"
        
        arquivo_comex = data_dir / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
        arquivo_empresas = data_dir / "Empresas Importadoras e Exportadoras.xlsx"
        
        # Verificar arquivos
        logger.info("\n🔍 Verificando arquivos...")
        logger.info(f"  📄 Comércio Exterior: {arquivo_comex.exists()}")
        logger.info(f"  📄 Empresas: {arquivo_empresas.exists()}")
        
        if not arquivo_comex.exists() and not arquivo_empresas.exists():
            logger.error("❌ Nenhum arquivo Excel encontrado!")
            logger.info(f"📁 Procurando em: {data_dir}")
            if data_dir.exists():
                arquivos = list(data_dir.glob("*.xlsx"))
                logger.info(f"📋 Arquivos encontrados: {[f.name for f in arquivos]}")
            return
        
        # Importar dados
        total_registros = 0
        total_valor_imp = 0.0
        total_valor_exp = 0.0
        total_peso = 0.0
        
        if arquivo_comex.exists():
            regs, val_imp, val_exp, peso = importar_dados_comex(db, arquivo_comex)
            total_registros += regs
            total_valor_imp += val_imp
            total_valor_exp += val_exp
            total_peso += peso
        
        if arquivo_empresas.exists():
            regs_emp = importar_dados_empresas(db, arquivo_empresas)
            total_registros += regs_emp
        
        # Resumo final
        logger.info("\n" + "="*80)
        logger.info("📊 RESUMO FINAL DA IMPORTAÇÃO")
        logger.info("="*80)
        logger.info(f"📁 Banco de dados: {db_path}")
        logger.info(f"📊 Total de registros: {total_registros:,}")
        logger.info(f"💰 Total Importação (USD): ${total_valor_imp:,.2f}")
        logger.info(f"💰 Total Exportação (USD): ${total_valor_exp:,.2f}")
        logger.info(f"💰 Valor Total (USD): ${total_valor_imp + total_valor_exp:,.2f}")
        logger.info(f"📦 Total Peso (kg): {total_peso:,.2f}")
        logger.success("="*80)
        logger.success("✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("\n💡 Próximo passo: Execute 'python backend/scripts/migrar_para_postgresql.py'")
        logger.info("   para enviar os dados para PostgreSQL no Render.")
        logger.success("="*80)
        
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
