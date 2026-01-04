"""
Script para testar a busca de dados na API do Comex Stat diretamente.
"""
import sys
from pathlib import Path
import asyncio
import httpx
from datetime import datetime, timedelta
from loguru import logger

# Adicionar o diretório backend ao path ANTES de importar
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Agora importar os módulos
from config import settings

async def testar_api_ncm(ncm: str):
    """
    Testa a busca de dados na API para um NCM específico.
    """
    logger.info("=" * 60)
    logger.info(f"TESTANDO API COM NCM: {ncm}")
    logger.info("=" * 60)
    
    # Calcular período (últimos 3 meses)
    data_fim = datetime.now()
    data_inicio = datetime.now() - timedelta(days=90)
    mes_inicio = data_inicio.strftime("%Y-%m")
    mes_fim = data_fim.strftime("%Y-%m")
    
    logger.info(f"Período: {mes_inicio} até {mes_fim}")
    logger.info(f"API URL configurada: {settings.comex_stat_api_url}")
    
    # Tentar diferentes URLs e formatos de API
    urls_tentativas = []
    
    if settings.comex_stat_api_url:
        base_url = settings.comex_stat_api_url.rstrip('/')
        urls_tentativas.extend([
            f"{base_url}/api/dados",
            f"{base_url}/api/v1/dados",
            f"{base_url}/dados",
            f"{base_url}/api/operacoes",
        ])
    
    # URLs conhecidas do portal Comex Stat
    urls_tentativas.extend([
        "https://comexstat.mdic.gov.br/api/dados",
        "https://comexstat.mdic.gov.br/api/v1/dados",
        "https://api-comexstat.mdic.gov.br/dados",
        "https://api-comexstat.mdic.gov.br/api/v1/dados",
    ])
    
    headers = {}
    if settings.comex_stat_api_key:
        headers["Authorization"] = f"Bearer {settings.comex_stat_api_key}"
    
    # Diferentes formatos de parâmetros
    formatos_params = [
        # Formato 1: padrão
        {
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim,
            "ncm": ncm,
            "tipo_operacao": "Importação"
        },
        # Formato 2: sem tipo
        {
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim,
            "ncm": ncm
        },
        # Formato 3: com ano/mês separados
        {
            "ano_inicio": data_inicio.year,
            "mes_inicio": data_inicio.month,
            "ano_fim": data_fim.year,
            "mes_fim": data_fim.month,
            "ncm": ncm
        },
        # Formato 4: apenas NCM
        {
            "ncm": ncm
        },
    ]
    
    resultados_encontrados = False
    
    for url in urls_tentativas:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testando URL: {url}")
        logger.info(f"{'='*60}")
        
        for i, params in enumerate(formatos_params, 1):
            logger.info(f"\nFormato {i}: {params}")
            
            try:
                async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
                    response = await client.get(url, params=params, headers=headers)
                    
                    logger.info(f"Status: {response.status_code}")
                    logger.info(f"Headers resposta: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"✅ Resposta JSON recebida!")
                            logger.info(f"Tipo de dados: {type(data)}")
                            
                            if isinstance(data, dict):
                                logger.info(f"Chaves no JSON: {list(data.keys())}")
                                registros = data.get('registros', data.get('data', data.get('resultado', [])))
                                if isinstance(data, list):
                                    registros = data
                            elif isinstance(data, list):
                                registros = data
                            else:
                                registros = []
                            
                            if registros:
                                logger.info(f"✅ {len(registros)} registros encontrados!")
                                logger.info(f"Primeiro registro: {str(registros[0])[:300]}")
                                resultados_encontrados = True
                                
                                # Mostrar alguns dados
                                for j, reg in enumerate(registros[:3], 1):
                                    logger.info(f"\nRegistro {j}:")
                                    if isinstance(reg, dict):
                                        for key, value in list(reg.items())[:10]:
                                            logger.info(f"  {key}: {value}")
                                    else:
                                        logger.info(f"  {reg}")
                                
                                return registros
                            else:
                                logger.warning("⚠️ Resposta vazia ou sem registros")
                                logger.info(f"Resposta completa: {str(data)[:500]}")
                        except Exception as e:
                            logger.error(f"Erro ao processar JSON: {e}")
                            logger.info(f"Resposta texto: {response.text[:500]}")
                    elif response.status_code == 404:
                        logger.warning(f"⚠️ Endpoint não encontrado (404)")
                    elif response.status_code == 401:
                        logger.warning(f"⚠️ Não autorizado (401) - pode precisar de API key")
                    else:
                        logger.warning(f"⚠️ Status {response.status_code}")
                        logger.info(f"Resposta: {response.text[:300]}")
                        
            except httpx.TimeoutException:
                logger.error(f"❌ Timeout ao acessar {url}")
            except httpx.ConnectError:
                logger.warning(f"⚠️ Não foi possível conectar a {url}")
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    if not resultados_encontrados:
        logger.warning("\n" + "="*60)
        logger.warning("NENHUM DADO ENCONTRADO NA API")
        logger.warning("="*60)
        logger.info("\nPossíveis causas:")
        logger.info("1. A API do Comex Stat pode não ter endpoint REST direto")
        logger.info("2. Pode ser necessário usar download de arquivos CSV")
        logger.info("3. A URL da API pode estar incorreta")
        logger.info("4. Pode ser necessário autenticação diferente")
    
    return None

async def main():
    ncm = "73182200"
    logger.info(f"Iniciando teste com NCM: {ncm}")
    resultado = await testar_api_ncm(ncm)
    
    if resultado:
        logger.info(f"\n✅ Teste concluído com sucesso!")
        logger.info(f"Total de registros: {len(resultado)}")
    else:
        logger.warning(f"\n⚠️ Nenhum dado encontrado na API")

if __name__ == "__main__":
    asyncio.run(main())

