"""
Script para testar o banco de dados e diagnosticar problemas.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, init_db, OperacaoComex, TipoOperacao
from sqlalchemy import func, distinct
from loguru import logger

def testar_banco():
    """Testa o banco de dados e mostra estatísticas."""
    logger.info("=" * 80)
    logger.info("TESTE DO BANCO DE DADOS - DIAGNÓSTICO COMPLETO")
    logger.info("=" * 80)
    
    try:
        # Inicializar banco
        init_db()
        db = next(get_db())
        
        # 1. Contar total de registros
        logger.info("\n📊 1. CONTAGEM DE REGISTROS")
        logger.info("-" * 80)
        total_registros = db.query(OperacaoComex).count()
        logger.info(f"Total de registros: {total_registros}")
        
        if total_registros == 0:
            logger.warning("⚠️ BANCO ESTÁ VAZIO! Não há dados para exibir.")
            logger.info("💡 Solução: Execute o endpoint /popular-dados-exemplo ou /coletar-dados")
            db.close()
            return
        
        # 2. Contar por tipo de operação
        logger.info("\n📊 2. REGISTROS POR TIPO DE OPERAÇÃO")
        logger.info("-" * 80)
        importacoes = db.query(OperacaoComex).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
        ).count()
        exportacoes = db.query(OperacaoComex).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
        ).count()
        logger.info(f"Importações: {importacoes}")
        logger.info(f"Exportações: {exportacoes}")
        
        # 3. Verificar empresas importadoras
        logger.info("\n📊 3. EMPRESAS IMPORTADORAS")
        logger.info("-" * 80)
        empresas_imp = db.query(
            distinct(OperacaoComex.razao_social_importador)
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != ''
        ).limit(10).all()
        
        total_imp_distintas = db.query(
            func.count(distinct(OperacaoComex.razao_social_importador))
        ).filter(
            OperacaoComex.razao_social_importador.isnot(None),
            OperacaoComex.razao_social_importador != ''
        ).scalar() or 0
        
        logger.info(f"Total de empresas importadoras distintas: {total_imp_distintas}")
        logger.info("Exemplos de empresas importadoras:")
        for i, (empresa,) in enumerate(empresas_imp[:10], 1):
            if empresa:
                logger.info(f"  {i}. {empresa}")
        
        if total_imp_distintas == 0:
            logger.warning("⚠️ Nenhuma empresa importadora encontrada!")
        
        # 4. Verificar empresas exportadoras
        logger.info("\n📊 4. EMPRESAS EXPORTADORAS")
        logger.info("-" * 80)
        empresas_exp = db.query(
            distinct(OperacaoComex.razao_social_exportador)
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != ''
        ).limit(10).all()
        
        total_exp_distintas = db.query(
            func.count(distinct(OperacaoComex.razao_social_exportador))
        ).filter(
            OperacaoComex.razao_social_exportador.isnot(None),
            OperacaoComex.razao_social_exportador != ''
        ).scalar() or 0
        
        logger.info(f"Total de empresas exportadoras distintas: {total_exp_distintas}")
        logger.info("Exemplos de empresas exportadoras:")
        for i, (empresa,) in enumerate(empresas_exp[:10], 1):
            if empresa:
                logger.info(f"  {i}. {empresa}")
        
        if total_exp_distintas == 0:
            logger.warning("⚠️ Nenhuma empresa exportadora encontrada!")
        
        # 5. Testar autocomplete de importadoras
        logger.info("\n📊 5. TESTE DE AUTOCOMPLETE - IMPORTADORAS")
        logger.info("-" * 80)
        termos_teste = ["Importadora", "ABC", "Comércio", "Vale"]
        for termo in termos_teste:
            empresas = db.query(
                OperacaoComex.razao_social_importador.label('empresa'),
                func.count(OperacaoComex.id).label('total_operacoes'),
                func.sum(OperacaoComex.valor_fob).label('valor_total')
            ).filter(
                OperacaoComex.razao_social_importador.isnot(None),
                OperacaoComex.razao_social_importador != '',
                OperacaoComex.razao_social_importador.ilike(f"%{termo}%")
            ).group_by(
                OperacaoComex.razao_social_importador
            ).limit(5).all()
            
            logger.info(f"Busca por '{termo}': {len(empresas)} resultados")
            for empresa, total_op, valor_total in empresas[:3]:
                logger.info(f"  - {empresa} ({total_op} operações, US$ {valor_total:,.2f})")
        
        # 6. Testar autocomplete de exportadoras
        logger.info("\n📊 6. TESTE DE AUTOCOMPLETE - EXPORTADORAS")
        logger.info("-" * 80)
        termos_teste = ["Exportadora", "Brasil", "Comércio", "Vale"]
        for termo in termos_teste:
            empresas = db.query(
                OperacaoComex.razao_social_exportador.label('empresa'),
                func.count(OperacaoComex.id).label('total_operacoes'),
                func.sum(OperacaoComex.valor_fob).label('valor_total')
            ).filter(
                OperacaoComex.razao_social_exportador.isnot(None),
                OperacaoComex.razao_social_exportador != '',
                OperacaoComex.razao_social_exportador.ilike(f"%{termo}%")
            ).group_by(
                OperacaoComex.razao_social_exportador
            ).limit(5).all()
            
            logger.info(f"Busca por '{termo}': {len(empresas)} resultados")
            for empresa, total_op, valor_total in empresas[:3]:
                logger.info(f"  - {empresa} ({total_op} operações, US$ {valor_total:,.2f})")
        
        # 7. Verificar dados por mês
        logger.info("\n📊 7. REGISTROS POR MÊS (Últimos 12 meses)")
        logger.info("-" * 80)
        hoje = datetime.now()
        meses_dados = {}
        for i in range(12):
            mes = (hoje - timedelta(days=30 * i)).strftime("%Y-%m")
            count = db.query(OperacaoComex).filter(
                OperacaoComex.mes_referencia == mes
            ).count()
            meses_dados[mes] = count
        
        for mes, count in sorted(meses_dados.items(), reverse=True):
            if count > 0:
                logger.info(f"{mes}: {count} registros")
        
        # 8. Verificar valores totais
        logger.info("\n📊 8. VALORES TOTAIS")
        logger.info("-" * 80)
        valor_total_imp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
        ).scalar() or 0
        
        valor_total_exp = db.query(func.sum(OperacaoComex.valor_fob)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
        ).scalar() or 0
        
        peso_total_imp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
        ).scalar() or 0
        
        peso_total_exp = db.query(func.sum(OperacaoComex.peso_liquido_kg)).filter(
            OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
        ).scalar() or 0
        
        logger.info(f"Valor total importações: US$ {valor_total_imp:,.2f}")
        logger.info(f"Valor total exportações: US$ {valor_total_exp:,.2f}")
        logger.info(f"Peso total importações: {peso_total_imp:,.2f} KG")
        logger.info(f"Peso total exportações: {peso_total_exp:,.2f} KG")
        
        # 9. Verificar alguns registros de exemplo
        logger.info("\n📊 9. REGISTROS DE EXEMPLO")
        logger.info("-" * 80)
        exemplos = db.query(OperacaoComex).limit(5).all()
        for i, op in enumerate(exemplos, 1):
            logger.info(f"\nRegistro {i}:")
            logger.info(f"  NCM: {op.ncm}")
            logger.info(f"  Tipo: {op.tipo_operacao.value}")
            logger.info(f"  Valor FOB: US$ {op.valor_fob:,.2f}")
            logger.info(f"  Peso: {op.peso_liquido_kg:,.2f} KG")
            logger.info(f"  Data: {op.data_operacao}")
            logger.info(f"  Importador: {op.razao_social_importador or 'N/A'}")
            logger.info(f"  Exportador: {op.razao_social_exportador or 'N/A'}")
        
        # 10. Resumo e recomendações
        logger.info("\n" + "=" * 80)
        logger.info("📋 RESUMO E RECOMENDAÇÕES")
        logger.info("=" * 80)
        
        problemas = []
        if total_registros == 0:
            problemas.append("❌ Banco está vazio - nenhum dado encontrado")
        if total_imp_distintas == 0:
            problemas.append("⚠️ Nenhuma empresa importadora encontrada")
        if total_exp_distintas == 0:
            problemas.append("⚠️ Nenhuma empresa exportadora encontrada")
        if valor_total_imp == 0 and valor_total_exp == 0:
            problemas.append("⚠️ Valores totais estão zerados")
        
        if problemas:
            logger.warning("\nPROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                logger.warning(f"  {problema}")
            
            logger.info("\n💡 SOLUÇÕES SUGERIDAS:")
            if total_registros == 0:
                logger.info("  1. Execute: POST /popular-dados-exemplo com quantidade: 1000")
                logger.info("  2. Ou execute: POST /coletar-dados para buscar dados reais")
            if total_imp_distintas == 0 or total_exp_distintas == 0:
                logger.info("  3. Verifique se os dados têm campos razao_social_importador/exportador preenchidos")
                logger.info("  4. Se usar dados de exemplo, eles devem ter empresas preenchidas")
        else:
            logger.success("\n✅ Banco de dados está funcionando corretamente!")
            logger.info(f"  - {total_registros} registros")
            logger.info(f"  - {total_imp_distintas} empresas importadoras")
            logger.info(f"  - {total_exp_distintas} empresas exportadoras")
            logger.info(f"  - Valores totais: US$ {valor_total_imp + valor_total_exp:,.2f}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar banco: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    testar_banco()

