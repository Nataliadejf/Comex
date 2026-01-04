"""
Gera dados realistas baseados na estrutura real do Comex Stat.
Usa NCMs, países e produtos reais para simular dados oficiais.
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, OperacaoComex, TipoOperacao, ViaTransporte
from data_collector.collector import DataCollector
from config import settings


# NCMs reais do Comex Stat
NCMs_REAIS = [
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
    ("87083090", "Outros freios e partes, para tratores/veículos automóveis"),
    ("87346890", "Outras partes para veículos automóveis"),
    ("27101921", "Querosene para aviação"),
    ("10063000", "Arroz semi-beneficiado ou beneficiado"),
    ("02071400", "Carnes de peru, congeladas"),
]

# Países reais
PAISES_REAIS = [
    "CHINA", "ESTADOS UNIDOS", "ARGENTINA", "ALEMANHA", "JAPÃO",
    "CORÉIA DO SUL", "MÉXICO", "CHILE", "FRANÇA", "REINO UNIDO",
    "ESPANHA", "ITÁLIA", "ÍNDIA", "RÚSSIA", "CANADÁ",
    "ÁFRICA DO SUL", "AUSTRÁLIA", "BRASIL", "PARAGUAI", "URUGUAI"
]

# UFs brasileiras
UFS = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "PE", "CE", "PA", "AM"]

# Portos/Aeroportos
PORTOS = [
    "Porto de Santos", "Porto do Rio de Janeiro", "Porto de Paranaguá",
    "Porto de Itajaí", "Porto de Suape", "Porto de Manaus",
    "Aeroporto de Guarulhos", "Aeroporto do Galeão", "Aeroporto de Viracopos",
    "Aeroporto de Confins", "Aeroporto de Brasília"
]

# Vias de transporte
VIAS = [ViaTransporte.MARITIMA, ViaTransporte.AEREA, ViaTransporte.RODOVIARIA]


def gerar_dados_realistas(num_registros: int = 1000, meses: int = 3) -> List[Dict[str, Any]]:
    """
    Gera dados realistas baseados na estrutura do Comex Stat.
    """
    dados = []
    hoje = datetime.now()
    
    for i in range(num_registros):
        # Escolher tipo de operação
        tipo_op = random.choice([TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO])
        is_imp = "S" if tipo_op == TipoOperacao.IMPORTACAO else "N"
        is_exp = "S" if tipo_op == TipoOperacao.EXPORTACAO else "N"
        
        # Escolher NCM e descrição
        ncm, descricao = random.choice(NCMs_REAIS)
        
        # Escolher país
        pais = random.choice(PAISES_REAIS)
        
        # Escolher UF
        uf = random.choice(UFS)
        
        # Escolher porto/aeroporto
        porto = random.choice(PORTOS)
        
        # Escolher via de transporte
        via = random.choice(VIAS)
        
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
            "arquivo_origem": "dados_realistas_gerados",
        })
    
    return dados


async def salvar_dados_no_banco(db, dados: List[Dict[str, Any]]) -> int:
    """Salva dados diretamente no banco."""
    from sqlalchemy import and_
    
    saved_count = 0
    batch_size = 500
    
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
                            OperacaoComex.valor_fob == record.get("valor_fob"),
                        )
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Criar novo registro
                    operacao = OperacaoComex(**record)
                    db.add(operacao)
                    saved_count += 1
                except Exception as e:
                    logger.debug(f"Erro ao salvar registro: {e}")
                    continue
            
            db.commit()
            logger.info(f"  Batch {i//batch_size + 1}: {saved_count - (i//batch_size * batch_size)} registros salvos")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar batch: {e}")
            continue
    
    return saved_count


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("GERAR DADOS REALISTAS - COMEX STAT")
    logger.info("=" * 60)
    logger.info("")
    
    # 1. Inicializar banco
    logger.info("1️⃣  Inicializando banco de dados...")
    init_db()
    
    # Verificar estado atual
    db = next(get_db())
    total_atual = db.query(OperacaoComex).count()
    db.close()
    
    logger.info(f"   Registros atuais no banco: {total_atual:,}")
    logger.info("")
    
    # 2. Gerar dados
    logger.info("2️⃣  Gerando dados realistas...")
    logger.info("   Baseado em NCMs, países e produtos reais do Comex Stat")
    logger.info("")
    
    num_registros = 2000  # Gerar 2000 registros
    meses = 3
    
    dados = gerar_dados_realistas(num_registros, meses)
    logger.info(f"✅ {len(dados)} registros gerados")
    logger.info("")
    
    # 3. Salvar no banco
    logger.info("3️⃣  Salvando dados no banco...")
    db = next(get_db())
    
    try:
        saved_count = await salvar_dados_no_banco(db, dados)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar dados: {e}")
        raise
    finally:
        db.close()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTADO FINAL")
    logger.info("=" * 60)
    logger.info("")
    
    # Verificar resultado
    db = next(get_db())
    total_final = db.query(OperacaoComex).count()
    total_importacoes = db.query(OperacaoComex).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
    ).count()
    total_exportacoes = db.query(OperacaoComex).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
    ).count()
    db.close()
    
    logger.info(f"✅ Registros salvos nesta execução: {saved_count:,}")
    logger.info("")
    logger.info(f"📊 Total no banco: {total_final:,}")
    logger.info(f"   • Importações: {total_importacoes:,}")
    logger.info(f"   • Exportações: {total_exportacoes:,}")
    logger.info("")
    logger.info("✅ Banco populado com dados realistas!")
    logger.info("   Acesse o dashboard: http://localhost:3000")
    logger.info("")
    logger.info("💡 NOTA:")
    logger.info("   Estes são dados simulados baseados em estrutura real.")
    logger.info("   Para dados oficiais, baixe CSV do portal Comex Stat.")
    logger.info("")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

