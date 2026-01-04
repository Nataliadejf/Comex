"""
Script para buscar dados diretamente do portal Comex Stat.
Tenta múltiplas estratégias de download.
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import httpx
import ssl

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings


async def baixar_arquivo_com_ssl_desabilitado(url: str, destino: Path) -> bool:
    """
    Baixa arquivo com SSL verificação desabilitada (para ambientes corporativos).
    """
    try:
        # Criar contexto SSL que não verifica certificados
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with httpx.AsyncClient(
            timeout=60.0,
            verify=False,  # Desabilitar verificação SSL
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            logger.info(f"Baixando: {url}")
            response = await client.get(url)
            
            if response.status_code == 200:
                # Verificar se é CSV válido
                content_preview = response.text[:1000]
                if "," in content_preview or ";" in content_preview:
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Tentar diferentes encodings
                    try:
                        destino.write_text(response.text, encoding='utf-8')
                    except:
                        try:
                            destino.write_text(response.text, encoding='latin1')
                        except:
                            destino.write_bytes(response.content)
                    
                    tamanho_mb = len(response.content) / (1024 * 1024)
                    logger.info(f"✅ Arquivo baixado: {destino} ({tamanho_mb:.2f} MB)")
                    return True
                else:
                    logger.warning(f"Resposta não parece ser CSV válido")
                    return False
            else:
                logger.debug(f"Status {response.status_code} para {url}")
                return False
                
    except Exception as e:
        logger.debug(f"Erro ao baixar {url}: {e}")
        return False


async def buscar_urls_download():
    """
    Busca URLs de download conhecidas do portal Comex Stat.
    """
    BASE_URL = "https://comexstat.mdic.gov.br"
    
    hoje = datetime.now()
    arquivos_baixados = []
    download_dir = settings.data_dir / "raw"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Tentar últimos 3 meses
    for i in range(3):
        data = hoje - timedelta(days=30 * i)
        ano = data.year
        mes = data.month
        
        for tipo in ['exportacao', 'importacao']:
            tipo_upper = tipo.upper()
            tipo_short = tipo[:3].upper()  # EXP ou IMP
            
            # Padrões de URL conhecidos
            urls = [
                # Padrão 1: EXP_YYYY_MM.csv
                f"{BASE_URL}/download/{tipo_short}_{ano}_{mes:02d}.csv",
                # Padrão 2: EXP_YYYYMM.csv
                f"{BASE_URL}/download/{tipo_short}_{ano}{mes:02d}.csv",
                # Padrão 3: Com query string
                f"{BASE_URL}/pt/download?tipo={tipo}&ano={ano}&mes={mes}",
                # Padrão 4: MDIC
                f"https://www.mdic.gov.br/comexstat/download/{tipo_short}_{ano}_{mes:02d}.csv",
                # Padrão 5: API endpoint
                f"{BASE_URL}/api/download/{tipo}/{ano}/{mes:02d}",
            ]
            
            filename = f"{tipo_short}_{ano}_{mes:02d}.csv"
            destino = download_dir / filename
            
            # Se já existe, pular
            if destino.exists():
                logger.info(f"Arquivo já existe: {destino}")
                arquivos_baixados.append(destino)
                continue
            
            # Tentar cada URL
            for url in urls:
                sucesso = await baixar_arquivo_com_ssl_desabilitado(url, destino)
                if sucesso:
                    arquivos_baixados.append(destino)
                    break
            
            # Delay entre downloads
            await asyncio.sleep(1)
    
    return arquivos_baixados


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("BUSCAR DADOS DO PORTAL COMEX STAT")
    logger.info("=" * 60)
    logger.info("")
    
    logger.info("Tentando baixar arquivos CSV do portal...")
    logger.info("")
    
    arquivos = await buscar_urls_download()
    
    logger.info("")
    logger.info("=" * 60)
    
    if arquivos:
        logger.info(f"✅ {len(arquivos)} arquivo(s) baixado(s)!")
        logger.info("")
        logger.info("Arquivos baixados:")
        for arquivo in arquivos:
            logger.info(f"  • {arquivo.name}")
        logger.info("")
        logger.info("Próximo passo: Processar os arquivos")
        logger.info("  Execute: python scripts/process_files.py")
    else:
        logger.warning("⚠️  Nenhum arquivo foi baixado automaticamente")
        logger.info("")
        logger.info("INSTRUÇÕES PARA DOWNLOAD MANUAL:")
        logger.info("=" * 60)
        logger.info("")
        logger.info("1. Acesse: https://comexstat.mdic.gov.br")
        logger.info("2. Navegue até: Dados Abertos > Download")
        logger.info("3. Baixe arquivos CSV de Exportação e Importação")
        logger.info("4. Salve em:")
        logger.info(f"   {download_dir}")
        logger.info("")
        logger.info("5. Execute: python scripts/process_files.py")
        logger.info("")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())



