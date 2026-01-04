"""
Script para criar dados de exemplo e popular o dashboard.
Executa automaticamente sem pedir confirmação.
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte
from config import settings
from sqlalchemy import func, and_


def criar_dados_exemplo():
    """Cria dados de exemplo para popular o dashboard."""
    logger.info("Criando dados de exemplo...")
    
    dados_exemplo = []
    hoje = datetime.now()
    
    # NCMs de exemplo (produtos comuns)
    ncms_exemplo = [
        ("84295200", "Máquinas e aparelhos para elevação"),
        ("87032300", "Automóveis de passageiros"),
        ("27101259", "Gasolina"),
        ("10019000", "Trigo"),
        ("02071200", "Carne de frango"),
        ("84713000", "Computadores portáteis"),
        ("30049099", "Medicamentos"),
        ("85171200", "Telefones celulares"),
        ("27090000", "Petróleo"),
        ("52010000", "Algodão"),
    ]
    
    # Países de exemplo
    paises = ["CHINA", "ESTADOS UNIDOS", "ARGENTINA", "ALEMANHA", "JAPÃO", "CORÉIA DO SUL", "MÉXICO", "CHILE"]
    
    # UFs de exemplo
    ufs = ["SP", "RJ", "RS", "MG", "PR", "SC", "BA", "GO"]
    
    # Criar dados para últimos 3 meses
    for mes_offset in range(3):
        mes_data = hoje - timedelta(days=30 * mes_offset)
        mes_ref = mes_data.strftime("%Y-%m")
        
        # Criar dados de importação e exportação
        for tipo_idx, tipo_op in enumerate([TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO]):
            # Criar ~100 registros por tipo por mês
            for i in range(100):
                ncm, descricao = ncms_exemplo[i % len(ncms_exemplo)]
                pais = paises[i % len(paises)]
                uf = ufs[i % len(ufs)]
                
                # Valores variados e realistas
                valor_base = 50000 + (i * 3000) + (mes_offset * 10000)
                valor_fob = valor_base * (1 + tipo_idx * 0.3)  # Exportação um pouco maior
                peso_kg = valor_fob * 0.15  # Relação peso/valor
                
                # Variar via de transporte
                if i % 3 == 0:
                    via = ViaTransporte.MARITIMA
                elif i % 3 == 1:
                    via = ViaTransporte.RODOVIARIA
                else:
                    via = ViaTransporte.AEREA
                
                registro = {
                    "ncm": ncm,
                    "descricao_produto": descricao,
                    "tipo_operacao": tipo_op,
                    "is_importacao": "S" if tipo_op == TipoOperacao.IMPORTACAO else "N",
                    "is_exportacao": "S" if tipo_op == TipoOperacao.EXPORTACAO else "N",
                    "pais_origem_destino": pais,
                    "uf": uf,
                    "porto_aeroporto": f"Porto {uf}" if via == ViaTransporte.MARITIMA else f"Aeroporto {uf}",
                    "via_transporte": via,
                    "valor_fob": round(valor_fob, 2),
                    "valor_frete": round(valor_fob * 0.05, 2),
                    "valor_seguro": round(valor_fob * 0.001, 2),
                    "peso_liquido_kg": round(peso_kg, 2),
                    "peso_bruto_kg": round(peso_kg * 1.1, 2),
                    "quantidade_estatistica": round(peso_kg / 1000, 3),
                    "unidade_medida_estatistica": "TON",
                    "data_operacao": mes_data.date(),
                    "data_importacao": datetime.now(),
                    "mes_referencia": mes_ref,
                    "arquivo_origem": "dados_exemplo",
                }
                
                dados_exemplo.append(registro)
    
    logger.info(f"✅ {len(dados_exemplo)} registros de exemplo criados")
    return dados_exemplo


async def salvar_dados_no_banco(dados: list):
    """Salva dados no banco de dados."""
    if not dados:
        return 0
    
    logger.info(f"Salvando {len(dados)} registros no banco...")
    
    db = next(get_db())
    
    # Salvar registros diretamente
    total_salvos = 0
    batch_size = 100
    
    for i in range(0, len(dados), batch_size):
        batch = dados[i:i + batch_size]
        
        for registro in batch:
            try:
                # Verificar se já existe (evitar duplicatas)
                existing = db.query(OperacaoComex).filter(
                    and_(
                        OperacaoComex.ncm == registro.get("ncm"),
                        OperacaoComex.tipo_operacao == registro.get("tipo_operacao"),
                        OperacaoComex.data_operacao == registro.get("data_operacao"),
                        OperacaoComex.pais_origem_destino == registro.get("pais_origem_destino"),
                        OperacaoComex.uf == registro.get("uf"),
                    )
                ).first()
                
                if existing:
                    continue  # Já existe, pular
                
                # Criar novo registro
                operacao = OperacaoComex(**registro)
                db.add(operacao)
                total_salvos += 1
                
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {e}")
                continue
        
        # Commit em lotes
        try:
            db.commit()
            logger.info(f"Salvos {min(i + batch_size, len(dados))}/{len(dados)} registros...")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao commitar lote: {e}")
    
    logger.info(f"✅ {total_salvos} novos registros salvos no banco")
    return total_salvos


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("CRIAR DADOS DE EXEMPLO - POPULAR DASHBOARD")
    logger.info("=" * 60)
    logger.info("")
    
    # Inicializar banco
    init_db()
    
    # Verificar se já há dados
    db = next(get_db())
    total_atual = db.query(func.count(OperacaoComex.id)).scalar() or 0
    
    if total_atual > 0:
        logger.info(f"⚠️  Já existem {total_atual:,} registros no banco")
        logger.info("Adicionando mais dados de exemplo...")
    
    logger.info("")
    logger.info("Criando dados de exemplo...")
    
    # Criar dados
    dados = criar_dados_exemplo()
    
    # Salvar no banco
    logger.info("")
    logger.info("Salvando dados no banco...")
    total_salvos = await salvar_dados_no_banco(dados)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("PROCESSO CONCLUÍDO!")
    logger.info("=" * 60)
    
    # Verificar resultado final
    db = next(get_db())
    total_final = db.query(func.count(OperacaoComex.id)).scalar() or 0
    
    # Estatísticas
    importacao = db.query(func.count(OperacaoComex.id)).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
    ).scalar() or 0
    
    exportacao = db.query(func.count(OperacaoComex.id)).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
    ).scalar() or 0
    
    logger.info(f"Total de registros salvos nesta execução: {total_salvos:,}")
    logger.info(f"Total de registros no banco: {total_final:,}")
    logger.info(f"  • Importações: {importacao:,}")
    logger.info(f"  • Exportações: {exportacao:,}")
    logger.info("")
    logger.info("✅ Dashboard pode ser acessado agora!")
    logger.info("   Acesse: http://localhost:3000")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())



