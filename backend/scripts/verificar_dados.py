"""
Script para verificar se há dados nas tabelas do PostgreSQL.

USO:
    Localmente:
        python backend/scripts/verificar_dados.py
    
    No Render Shell:
        cd /opt/render/project/src/backend
        python scripts/verificar_dados.py
"""
import sys
from pathlib import Path
import os
from loguru import logger
from sqlalchemy import func, text

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal, engine
from database.models import (
    ComercioExterior, Empresa, CNAEHierarquia, 
    OperacaoComex, EmpresasRecomendadas, TipoOperacao
)

def verificar_tabelas():
    """Verifica se as tabelas existem e quantos registros têm."""
    logger.info("="*80)
    logger.info("VERIFICANDO DADOS NO POSTGRESQL")
    logger.info("="*80)
    
    db = SessionLocal()
    
    try:
        # Verificar se as tabelas existem
        logger.info("\n📊 Verificando existência das tabelas...")
        
        with engine.connect() as conn:
            # Verificar tabela comex_registros (ou comercio_exterior)
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('comercio_exterior', 'comex_registros')
                """))
                tabelas_existem = result.fetchone()[0] > 0
                logger.info(f"✅ Tabelas encontradas: {tabelas_existem}")
            except Exception as e:
                logger.error(f"❌ Erro ao verificar tabelas: {e}")
                tabelas_existem = False
        
        if not tabelas_existem:
            logger.warning("⚠️ Tabelas não encontradas! Execute o schema.sql primeiro.")
            return
        
        # Contar registros em ComercioExterior
        try:
            total_comex = db.query(func.count(ComercioExterior.id)).scalar()
            logger.info(f"\n📦 Tabela ComercioExterior:")
            logger.info(f"   Total de registros: {total_comex}")
            
            if total_comex > 0:
                # Estatísticas por tipo
                importacoes = db.query(func.count(ComercioExterior.id)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar()
                exportacoes = db.query(func.count(ComercioExterior.id)).filter(
                    ComercioExterior.tipo == 'exportacao'
                ).scalar()
                
                logger.info(f"   - Importações: {importacoes}")
                logger.info(f"   - Exportações: {exportacoes}")
                
                # Valores totais
                valor_imp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                    ComercioExterior.tipo == 'importacao'
                ).scalar() or 0.0
                valor_exp = db.query(func.sum(ComercioExterior.valor_usd)).filter(
                    ComercioExterior.tipo == 'exportacao'
                ).scalar() or 0.0
                
                logger.info(f"   - Valor total importações (USD): ${valor_imp:,.2f}")
                logger.info(f"   - Valor total exportações (USD): ${valor_exp:,.2f}")
                
                # Período dos dados
                data_min = db.query(func.min(ComercioExterior.data)).scalar()
                data_max = db.query(func.max(ComercioExterior.data)).scalar()
                logger.info(f"   - Período: {data_min} até {data_max}")
                
                # Top 5 NCMs
                top_ncms = db.query(
                    ComercioExterior.ncm,
                    ComercioExterior.descricao_ncm,
                    func.sum(ComercioExterior.valor_usd).label('total')
                ).group_by(
                    ComercioExterior.ncm,
                    ComercioExterior.descricao_ncm
                ).order_by(
                    func.sum(ComercioExterior.valor_usd).desc()
                ).limit(5).all()
                
                logger.info(f"\n   Top 5 NCMs:")
                for ncm, desc, valor in top_ncms:
                    logger.info(f"   - {ncm}: ${valor:,.2f} - {desc[:50]}")
            else:
                logger.warning("   ⚠️ Tabela vazia! Execute o script de importação.")
        except Exception as e:
            logger.error(f"❌ Erro ao consultar ComercioExterior: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Contar registros em Empresa
        try:
            total_empresas = db.query(func.count(Empresa.id)).scalar()
            logger.info(f"\n🏢 Tabela Empresa:")
            logger.info(f"   Total de empresas: {total_empresas}")
            
            if total_empresas > 0:
                # Estatísticas por tipo
                importadoras = db.query(func.count(Empresa.id)).filter(
                    Empresa.tipo.in_(['importadora', 'ambos'])
                ).scalar()
                exportadoras = db.query(func.count(Empresa.id)).filter(
                    Empresa.tipo.in_(['exportadora', 'ambos'])
                ).scalar()
                
                logger.info(f"   - Importadoras: {importadoras}")
                logger.info(f"   - Exportadoras: {exportadoras}")
                
                # Valores totais
                valor_imp = db.query(func.sum(Empresa.valor_importacao)).scalar() or 0.0
                valor_exp = db.query(func.sum(Empresa.valor_exportacao)).scalar() or 0.0
                
                logger.info(f"   - Valor total importações: R$ {valor_imp:,.2f}")
                logger.info(f"   - Valor total exportações: R$ {valor_exp:,.2f}")
                
                # Top 5 empresas
                top_empresas = db.query(
                    Empresa.nome,
                    Empresa.cnpj,
                    Empresa.valor_importacao,
                    Empresa.valor_exportacao
                ).order_by(
                    (Empresa.valor_importacao + Empresa.valor_exportacao).desc()
                ).limit(5).all()
                
                logger.info(f"\n   Top 5 Empresas:")
                for nome, cnpj, imp, exp in top_empresas:
                    total = (imp or 0) + (exp or 0)
                    logger.info(f"   - {nome[:40]}: R$ {total:,.2f}")
            else:
                logger.warning("   ⚠️ Tabela vazia! Execute o script de importação.")
        except Exception as e:
            logger.error(f"❌ Erro ao consultar Empresa: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Contar registros em CNAEHierarquia
        try:
            total_cnae = db.query(func.count(CNAEHierarquia.id)).scalar()
            logger.info(f"\n📋 Tabela CNAEHierarquia:")
            logger.info(f"   Total de registros: {total_cnae}")
        except Exception as e:
            logger.error(f"❌ Erro ao consultar CNAEHierarquia: {e}")
        
        # Contar registros em OperacaoComex (tabela antiga)
        try:
            total_op = db.query(func.count(OperacaoComex.id)).scalar()
            logger.info(f"\n📊 Tabela OperacaoComex:")
            logger.info(f"   Total de registros: {total_op}")
            
            if total_op > 0:
                imp_op = db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
                ).scalar()
                exp_op = db.query(func.count(OperacaoComex.id)).filter(
                    OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
                ).scalar()
                logger.info(f"   - Importações: {imp_op}")
                logger.info(f"   - Exportações: {exp_op}")
        except Exception as e:
            logger.debug(f"Tabela OperacaoComex não encontrada ou erro: {e}")
        
        # Contar registros em EmpresasRecomendadas
        try:
            total_rec = db.query(func.count(EmpresasRecomendadas.id)).scalar()
            logger.info(f"\n⭐ Tabela EmpresasRecomendadas:")
            logger.info(f"   Total de empresas: {total_rec}")
            
            if total_rec > 0:
                imp_rec = db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.provavel_importador == 1
                ).scalar()
                exp_rec = db.query(func.count(EmpresasRecomendadas.id)).filter(
                    EmpresasRecomendadas.provavel_exportador == 1
                ).scalar()
                logger.info(f"   - Prováveis importadoras: {imp_rec}")
                logger.info(f"   - Prováveis exportadoras: {exp_rec}")
        except Exception as e:
            logger.debug(f"Tabela EmpresasRecomendadas não encontrada ou erro: {e}")
        
        logger.info("\n" + "="*80)
        
        # Resumo final
        if total_comex == 0 and total_empresas == 0:
            logger.warning("⚠️ NENHUM DADO ENCONTRADO!")
            logger.info("\n💡 PRÓXIMOS PASSOS:")
            logger.info("1. Verifique se os arquivos Excel estão em backend/data/")
            logger.info("2. Execute: python backend/scripts/import_data.py")
            logger.info("3. Aguarde a importação completar")
        else:
            logger.success("✅ DADOS ENCONTRADOS NO BANCO!")
            logger.info(f"   - Registros de comércio: {total_comex}")
            logger.info(f"   - Empresas: {total_empresas}")
            logger.info("\n💡 Se o dashboard ainda estiver vazio:")
            logger.info("   - Verifique o endpoint /dashboard/stats")
            logger.info("   - Verifique os logs do backend")
            logger.info("   - Verifique se há filtros de data aplicados")
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    verificar_tabelas()
