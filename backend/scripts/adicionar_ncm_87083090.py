"""
Script para adicionar dados do NCM 87083090 ao banco de dados.
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
from data_collector.collector import DataCollector
from config import settings


# Dados específicos para NCM 87083090
NCM_87083090 = {
    "ncm": "87083090",
    "descricao": "Outros freios e partes, para tratores/veículos automóveis",
    "paises": ["CHINA", "JAPÃO", "ALEMANHA", "ESTADOS UNIDOS", "CORÉIA DO SUL"],
    "ufs": ["SP", "GO", "PR", "SC", "RS", "PE", "RJ", "BA"],
    "portos": [
        "PORTO DE SANTOS",
        "PORTO DE PARANAGUA",
        "ITAJAI",
        "PORTO DO RIO DE JANEIRO",
        "PORTO DE RIO GRANDE",
        "PORTO DE SAO FRANCISCO DO SUL",
        "ALF - SALVADOR",
        "IRF - PORTO DE SUAPE",
        "SAO PAULO"
    ],
    "cidades": {
        "GO": ["ANÁPOLIS", "GOIÂNIA"],
        "SP": ["SOROCABA", "LIMEIRA", "SÃO BERNARDO DO CAMPO", "PIRACICABA", "PAULÍNIA"],
        "PR": ["SÃO JOSÉ DOS PINHAIS", "CURITIBA"],
        "SC": ["ITAJAÍ", "FLORIANÓPOLIS"],
        "PE": ["GOIANA", "RECIFE"],
        "RS": ["PORTO ALEGRE", "RIO GRANDE"]
    }
}


def gerar_dados_ncm_87083090(num_registros: int = 500, meses: int = 3):
    """Gera dados realistas para o NCM 87083090."""
    dados = []
    hoje = datetime.now()
    
    empresas_importadoras = [
        "TOYOTA DO BRASIL LTDA",
        "STELLANTIS AUTOMOVEIS BRASIL LTDA.",
        "CAOA MONTADORA DE VEICULOS LTDA",
        "HYUNDAI MOTOR BRASIL MONTADORA DE AUTOMOVEIS LTDA",
        "HONDA AUTOMOVEIS DO BRASIL LTDA",
        "VOLKSWAGEN DO BRASIL LTDA",
        "FORD MOTOR COMPANY BRASIL LTDA",
        "GENERAL MOTORS DO BRASIL LTDA",
        "NISSAN DO BRASIL AUTOMOVEIS LTDA",
        "FIAT AUTOMOVEIS S.A."
    ]
    
    empresas_exportadoras = [
        "CHERY AUTOMOBILE CHINA",
        "HYUNDAI GLOVIS SOUTH KOREA",
        "TOYOTA MOTOR SINGAPORE",
        "SCANIA CV SWEDEN",
        "RENAULT FRANCE",
        "BMW GERMANY",
        "MERCEDES-BENZ GERMANY",
        "AUDI GERMANY",
        "VOLVO SWEDEN",
        "MAZDA JAPAN"
    ]
    
    for i in range(num_registros):
        # Escolher tipo de operação (70% importação, 30% exportação)
        tipo_op = random.choices(
            [TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO],
            weights=[70, 30]
        )[0]
        is_imp = "S" if tipo_op == TipoOperacao.IMPORTACAO else "N"
        is_exp = "S" if tipo_op == TipoOperacao.EXPORTACAO else "N"
        
        # Escolher país
        pais = random.choice(NCM_87083090["paises"])
        
        # Escolher UF
        uf = random.choice(NCM_87083090["ufs"])
        
        # Escolher porto/aeroporto
        porto = random.choice(NCM_87083090["portos"])
        
        # Escolher via de transporte (80% marítima, 15% aérea, 5% rodoviária)
        via = random.choices(
            [ViaTransporte.MARITIMA, ViaTransporte.AEREA, ViaTransporte.RODOVIARIA],
            weights=[80, 15, 5]
        )[0]
        
        # Gerar valores realistas para freios de veículos
        valor_fob = random.uniform(50000, 800000)
        valor_frete = valor_fob * random.uniform(0.04, 0.10)
        valor_seguro = valor_fob * random.uniform(0.001, 0.003)
        
        # Gerar pesos (freios são relativamente leves)
        peso_liquido = random.uniform(500, 15000)
        peso_bruto = peso_liquido * random.uniform(1.05, 1.12)
        
        # Quantidade estatística
        quantidade = random.uniform(50, 500)
        unidade = random.choice(["UN", "KG", "TON"])
        
        # Data aleatória nos últimos N meses
        dias_aleatorios = random.randint(0, meses * 30)
        data_operacao = (hoje - timedelta(days=dias_aleatorios)).date()
        mes_referencia = data_operacao.strftime("%Y-%m")
        
        dados.append({
            "ncm": NCM_87083090["ncm"],
            "descricao_produto": NCM_87083090["descricao"],
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
            "arquivo_origem": "dados_ncm_87083090_gerados",
        })
    
    return dados


async def salvar_dados_no_banco(db, dados):
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
                            OperacaoComex.pais_origem_destino == record.get("pais_origem_destino")
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
            logger.info(f"✅ Lote {i//batch_size + 1}: {saved_count} registros salvos")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar lote: {e}")
    
    return saved_count


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("ADICIONANDO DADOS DO NCM 87083090")
    logger.info("=" * 60)
    
    init_db()
    db = next(get_db())
    
    try:
        # Verificar quantos registros já existem
        from sqlalchemy import func
        total_existente = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.ncm == "87083090"
        ).scalar() or 0
        
        logger.info(f"📊 Registros existentes do NCM 87083090: {total_existente}")
        
        if total_existente > 0:
            logger.info("⚠️  Já existem registros deste NCM. Deseja adicionar mais?")
            logger.info("   (Execute novamente para adicionar mais dados)")
        
        # Gerar dados
        logger.info("🔄 Gerando dados realistas...")
        dados = gerar_dados_ncm_87083090(num_registros=500, meses=6)
        logger.info(f"✅ {len(dados)} registros gerados")
        
        # Salvar no banco
        logger.info("💾 Salvando no banco de dados...")
        total_salvos = await salvar_dados_no_banco(db, dados)
        
        logger.info("=" * 60)
        logger.info(f"✅ CONCLUÍDO!")
        logger.info(f"   • Total de registros salvos: {total_salvos}")
        logger.info(f"   • NCM: 87083090")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())


