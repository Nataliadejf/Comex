"""
Script para buscar dados automaticamente e popular o dashboard.
Tenta múltiplas fontes: API pública, download direto, ou dados de exemplo.
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
from sqlalchemy import func
import httpx


async def tentar_api_publica_comex():
    """Tenta buscar dados da API pública do Comex Stat."""
    logger.info("Tentando buscar dados da API pública do Comex Stat...")
    
    # URLs conhecidas da API pública do Comex Stat
    urls_tentativas = [
        "https://api-comexstat.mdic.gov.br/api/v1/dados",
        "https://comexstat.mdic.gov.br/api/dados",
        "http://api.comexstat.mdic.gov.br/dados",
    ]
    
    mes_atual = datetime.now().strftime("%Y-%m")
    mes_anterior = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
    
    for url_base in urls_tentativas:
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                # Tentar buscar dados de exportação
                params = {
                    "mes": mes_atual,
                    "tipo": "exportacao"
                }
                response = await client.get(url_base, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Dados encontrados na API: {url_base}")
                    return data
        except Exception as e:
            logger.debug(f"URL {url_base} não funcionou: {e}")
            continue
    
    logger.warning("Nenhuma API pública funcionou")
    return None


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
    ]
    
    # Países de exemplo
    paises = ["CHINA", "ESTADOS UNIDOS", "ARGENTINA", "ALEMANHA", "JAPÃO"]
    
    # UFs de exemplo
    ufs = ["SP", "RJ", "RS", "MG", "PR"]
    
    # Criar dados para últimos 3 meses
    for mes_offset in range(3):
        mes_data = hoje - timedelta(days=30 * mes_offset)
        mes_ref = mes_data.strftime("%Y-%m")
        
        # Criar dados de importação e exportação
        for tipo_idx, tipo_op in enumerate([TipoOperacao.IMPORTACAO, TipoOperacao.EXPORTACAO]):
            # Criar ~50 registros por tipo por mês
            for i in range(50):
                ncm, descricao = ncms_exemplo[i % len(ncms_exemplo)]
                pais = paises[i % len(paises)]
                uf = ufs[i % len(ufs)]
                
                # Valores variados
                valor_fob = (100000 + i * 5000) * (1 + tipo_idx * 0.5)
                peso_kg = valor_fob * 0.1
                
                registro = {
                    "ncm": ncm,
                    "descricao_produto": descricao,
                    "tipo_operacao": tipo_op,
                    "is_importacao": "S" if tipo_op == TipoOperacao.IMPORTACAO else "N",
                    "is_exportacao": "S" if tipo_op == TipoOperacao.EXPORTACAO else "N",
                    "pais_origem_destino": pais,
                    "uf": uf,
                    "porto_aeroporto": f"Porto {uf}",
                    "via_transporte": ViaTransporte.MARITIMA if i % 3 == 0 else ViaTransporte.RODOVIARIA,
                    "valor_fob": valor_fob,
                    "valor_frete": valor_fob * 0.05,
                    "valor_seguro": valor_fob * 0.001,
                    "peso_liquido_kg": peso_kg,
                    "peso_bruto_kg": peso_kg * 1.1,
                    "quantidade_estatistica": peso_kg / 1000,
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
    
    for registro in dados:
        try:
            # Verificar se já existe (evitar duplicatas)
            from sqlalchemy import and_
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
    
    try:
        db.commit()
        logger.info(f"✅ {total_salvos} novos registros salvos no banco")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao commitar transação: {e}")
        raise
    
    return total_salvos


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("BUSCAR DADOS AUTOMÁTICO - POPULAR DASHBOARD")
    logger.info("=" * 60)
    logger.info("")
    
    # Inicializar banco
    init_db()
    
    # Verificar se já há dados
    db = next(get_db())
    total_atual = db.query(func.count(OperacaoComex.id)).scalar() or 0
    
    if total_atual > 0:
        logger.info(f"⚠️  Já existem {total_atual:,} registros no banco")
        resposta = input("Deseja adicionar mais dados? (s/n): ").strip().lower()
        if resposta != 's':
            logger.info("Operação cancelada")
            return
    
    logger.info("")
    logger.info("Tentando buscar dados de múltiplas fontes...")
    logger.info("")
    
    dados_encontrados = None
    
    # 1. Tentar API pública
    logger.info("1️⃣  Tentando API pública do Comex Stat...")
    dados_api = await tentar_api_publica_comex()
    if dados_api:
        dados_encontrados = dados_api
        logger.info("✅ Dados encontrados na API pública")
    else:
        logger.info("❌ API pública não disponível")
    
    logger.info("")
    
    # 2. Se não encontrou, criar dados de exemplo
    if not dados_encontrados:
        logger.info("2️⃣  Criando dados de exemplo...")
        resposta = input("Deseja criar dados de exemplo para testar o dashboard? (s/n): ").strip().lower()
        
        if resposta == 's':
            dados_encontrados = criar_dados_exemplo()
        else:
            logger.info("Operação cancelada")
            logger.info("")
            logger.info("💡 Para popular o dashboard:")
            logger.info("   1. Baixe arquivos CSV do portal Comex Stat")
            logger.info("   2. Salve em: C:\\Users\\User\\Desktop\\Cursor\\Projetos\\data\\raw\\")
            logger.info("   3. Execute: python scripts/process_files.py")
            return
    
    # 3. Salvar dados no banco
    if dados_encontrados:
        logger.info("")
        logger.info("3️⃣  Salvando dados no banco...")
        total_salvos = await salvar_dados_no_banco(dados_encontrados)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("PROCESSO CONCLUÍDO!")
        logger.info("=" * 60)
        logger.info(f"Total de registros salvos: {total_salvos:,}")
        
        # Verificar resultado final
        db = next(get_db())
        total_final = db.query(func.count(OperacaoComex.id)).scalar() or 0
        logger.info(f"Total de registros no banco: {total_final:,}")
        logger.info("")
        logger.info("✅ Dashboard pode ser acessado agora!")
        logger.info("   Acesse: http://localhost:3000")
    else:
        logger.error("❌ Nenhum dado foi encontrado ou criado")


if __name__ == "__main__":
    asyncio.run(main())

