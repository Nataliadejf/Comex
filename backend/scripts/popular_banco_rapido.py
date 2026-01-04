"""
Script rápido para popular o banco de dados com dados realistas.
Inclui vários NCMs incluindo 87083900 e 87083090.
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import random

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte
from config import settings


# NCMs para popular
NCMs_PARA_POPULAR = [
    ("87083900", "Outras partes e acessórios para veículos automóveis"),
    ("87083090", "Outros freios e partes, para tratores/veículos automóveis"),
    ("84295200", "Máquinas e aparelhos para elevação, carga, descarga ou movimentação"),
    ("87032300", "Automóveis de passageiros, com motor de pistão alternativo"),
    ("27101259", "Gasolina, exceto para aviação"),
    ("10019000", "Trigo e mistura de trigo com centeio"),
    ("02071200", "Carnes de aves, congeladas"),
    ("84713000", "Computadores portáteis"),
    ("30049099", "Medicamentos"),
    ("85171200", "Telefones celulares"),
    ("27090000", "Petróleo bruto"),
    ("52010000", "Algodão não cardado nem penteado"),
    ("87089990", "Partes e acessórios para veículos automóveis"),
    ("27101921", "Querosene para aviação"),
    ("10063000", "Arroz semi-beneficiado ou beneficiado"),
]

PAISES = [
    "CHINA", "ESTADOS UNIDOS", "ARGENTINA", "ALEMANHA", "JAPÃO",
    "CORÉIA DO SUL", "MÉXICO", "CHILE", "FRANÇA", "REINO UNIDO",
    "ESPANHA", "ITÁLIA", "ÍNDIA", "RÚSSIA", "CANADÁ",
    "ÁFRICA DO SUL", "AUSTRÁLIA", "BRASIL", "PARAGUAI", "URUGUAI"
]

UFS = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "PE", "CE", "PA", "AM"]

PORTOS = [
    "PORTO DE SANTOS",
    "PORTO DE PARANAGUA",
    "ITAJAI",
    "PORTO DO RIO DE JANEIRO",
    "PORTO DE RIO GRANDE",
    "PORTO DE SAO FRANCISCO DO SUL",
    "ALF - SALVADOR",
    "IRF - PORTO DE SUAPE",
    "SAO PAULO",
    "Aeroporto de Guarulhos",
    "Aeroporto do Galeão",
    "Aeroporto de Viracopos",
]

VIAS = [ViaTransporte.MARITIMA, ViaTransporte.AEREA, ViaTransporte.RODOVIARIA]


def gerar_dados(num_registros_por_ncm: int = 200, meses: int = 6):
    """Gera dados realistas para todos os NCMs."""
    dados = []
    hoje = datetime.now()
    
    for ncm, descricao in NCMs_PARA_POPULAR:
        logger.info(f"Gerando dados para NCM {ncm}...")
        
        for i in range(num_registros_por_ncm):
            # Escolher tipo de operação (70% importação, 30% exportação)
            tipo_op = random.choices(
                [TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO],
                weights=[70, 30]
            )[0]
            is_imp = "S" if tipo_op == TipoOperacao.IMPORTACAO else "N"
            is_exp = "S" if tipo_op == TipoOperacao.EXPORTACAO else "N"
            
            # Escolher país
            pais = random.choice(PAISES)
            
            # Escolher UF
            uf = random.choice(UFS)
            
            # Escolher porto/aeroporto
            porto = random.choice(PORTOS)
            
            # Escolher via de transporte (80% marítima, 15% aérea, 5% rodoviária)
            via = random.choices(
                [ViaTransporte.MARITIMA, ViaTransporte.AEREA, ViaTransporte.RODOVIARIA],
                weights=[80, 15, 5]
            )[0]
            
            # Gerar valores realistas
            valor_fob = random.uniform(10000, 500000)
            valor_frete = valor_fob * random.uniform(0.03, 0.08)
            valor_seguro = valor_fob * random.uniform(0.001, 0.003)
            
            # Gerar pesos
            peso_liquido = random.uniform(1000, 50000)
            peso_bruto = peso_liquido * random.uniform(1.05, 1.15)
            
            # Quantidade estatística
            quantidade = random.uniform(10, 1000)
            unidade = random.choice(["TON", "UN", "M3", "KG"])
            
            # Data aleatória nos últimos N meses
            dias_aleatorios = random.randint(0, meses * 30)
            data_operacao = (hoje - timedelta(days=dias_aleatorios)).date()
            mes_referencia = data_operacao.strftime("%Y-%m")
            
            dados.append({
                "ncm": ncm,
                "descricao_produto": descricao,
                "tipo_operacao": tipo_op,
                "is_importacao": is_imp,
                "is_exportacao": is_exp,
                "pais_origem_destino": pais,
                "uf": uf,
                "porto_aeroporto": porto,
                "via_transporte": via,
                "valor_fob": round(valor_fob, 2),
                "valor_frete": round(valor_frete, 2),
                "valor_seguro": round(valor_seguro, 2),
                "peso_liquido_kg": round(peso_liquido, 2),
                "peso_bruto_kg": round(peso_bruto, 2),
                "quantidade_estatistica": round(quantidade, 3),
                "unidade_medida_estatistica": unidade,
                "data_operacao": data_operacao,
                "mes_referencia": mes_referencia,
                "arquivo_origem": "dados_popular_banco_rapido",
            })
    
    return dados


async def salvar_dados_no_banco(db, dados):
    """Salva dados diretamente no banco."""
    from sqlalchemy import and_
    
    saved_count = 0
    batch_size = 500
    
    logger.info(f"💾 Salvando {len(dados)} registros no banco...")
    
    for i in range(0, len(dados), batch_size):
        batch = dados[i:i + batch_size]
        try:
            for record in batch:
                try:
                    # Verificar se já existe (evitar duplicatas)
                    existing = db.query(OperacaoComex).filter(
                        and_(
                            OperacaoComex.ncm == record.get("ncm"),
                            OperacaoComex.tipo_operacao == record.get("tipo_operacao"),
                            OperacaoComex.data_operacao == record.get("data_operacao"),
                            OperacaoComex.pais_origem_destino == record.get("pais_origem_destino"),
                            OperacaoComex.valor_fob == record.get("valor_fob")
                        )
                    ).first()
                    
                    if not existing:
                        operacao = OperacaoComex(**record)
                        db.add(operacao)
                        saved_count += 1
                except Exception as e:
                    logger.warning(f"Erro ao salvar registro: {e}")
                    continue
            
            db.commit()
            logger.info(f"✅ Lote {i//batch_size + 1}: {saved_count} registros salvos até agora")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar lote: {e}")
            import traceback
            traceback.print_exc()
    
    return saved_count


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("POPULANDO BANCO DE DADOS COM DADOS REALISTAS")
    logger.info("=" * 60)
    
    init_db()
    db = next(get_db())
    
    try:
        # Verificar quantos registros já existem
        from sqlalchemy import func
        total_existente = db.query(func.count(OperacaoComex.id)).scalar() or 0
        
        logger.info(f"📊 Registros existentes no banco: {total_existente}")
        
        if total_existente > 0:
            logger.info("⚠️  Já existem registros no banco.")
            logger.info("   Os novos registros serão adicionados (sem duplicatas).")
        
        # Gerar dados
        logger.info("🔄 Gerando dados realistas...")
        logger.info(f"   • {len(NCMs_PARA_POPULAR)} NCMs diferentes")
        logger.info(f"   • {200} registros por NCM")
        logger.info(f"   • Total: {len(NCMs_PARA_POPULAR) * 200} registros")
        
        dados = gerar_dados(num_registros_por_ncm=200, meses=6)
        logger.info(f"✅ {len(dados)} registros gerados")
        
        # Salvar no banco
        logger.info("💾 Salvando no banco de dados...")
        total_salvos = await salvar_dados_no_banco(db, dados)
        
        # Verificar total final
        total_final = db.query(func.count(OperacaoComex.id)).scalar() or 0
        
        logger.info("=" * 60)
        logger.info(f"✅ CONCLUÍDO!")
        logger.info(f"   • Registros salvos nesta execução: {total_salvos}")
        logger.info(f"   • Total de registros no banco: {total_final}")
        logger.info(f"   • NCMs incluídos: {len(NCMs_PARA_POPULAR)}")
        logger.info("=" * 60)
        
        # Listar NCMs disponíveis
        logger.info("\n📋 NCMs disponíveis no banco:")
        ncms_disponiveis = db.query(
            OperacaoComex.ncm,
            func.count(OperacaoComex.id).label('count')
        ).group_by(
            OperacaoComex.ncm
        ).order_by(
            func.count(OperacaoComex.id).desc()
        ).all()
        
        for ncm_val, count in ncms_disponiveis:
            logger.info(f"   • {ncm_val}: {count} registros")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())


