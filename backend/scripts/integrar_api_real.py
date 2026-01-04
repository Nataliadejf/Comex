"""
Script para integrar com dados REAIS do Comex Stat.
Remove dados de exemplo e busca dados oficiais do portal.
"""
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from database import get_db, init_db, OperacaoComex, TipoOperacao
from config import settings
from sqlalchemy import func, delete
import httpx
import asyncio
from pathlib import Path


async def limpar_dados_exemplo():
    """Remove todos os dados de exemplo do banco."""
    logger.info("Removendo dados de exemplo...")
    
    db = next(get_db())
    
    deleted = db.execute(
        delete(OperacaoComex).where(
            OperacaoComex.arquivo_origem == "dados_exemplo"
        )
    )
    db.commit()
    
    count = deleted.rowcount
    logger.info(f"✅ {count} registros de exemplo removidos")
    return count


async def baixar_dados_reais():
    """Baixa dados reais do portal Comex Stat."""
    logger.info("=" * 60)
    logger.info("BAIXANDO DADOS REAIS DO PORTAL COMEX STAT")
    logger.info("=" * 60)
    
    BASE_URL = "https://comexstat.mdic.gov.br"
    download_dir = settings.data_dir / "raw"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Testar conexão
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=True, follow_redirects=True) as client:
            response = await client.get(BASE_URL)
            if response.status_code == 200:
                logger.info(f"✅ Portal acessível: {BASE_URL}")
            else:
                logger.warning(f"Portal retornou status {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro ao acessar portal: {e}")
        return []
    
    # Tentar baixar arquivos dos últimos 3 meses
    hoje = datetime.now()
    arquivos_baixados = []
    
    for i in range(3):
        data = hoje - timedelta(days=30 * i)
        ano = data.year
        mes = data.month
        
        for tipo in ['exportacao', 'importacao']:
            # Tentar diferentes padrões de URL
            urls = [
                f"{BASE_URL}/pt/download?tipo={tipo}&ano={ano}&mes={mes}",
                f"{BASE_URL}/download/{tipo.upper()}_{ano}_{mes:02d}.csv",
                f"https://www.mdic.gov.br/comexstat/download/{tipo.upper()}_{ano}_{mes:02d}.csv",
            ]
            
            for url in urls:
                try:
                    async with httpx.AsyncClient(timeout=30.0, verify=True, follow_redirects=True) as client:
                        response = await client.get(url)
                        
                        if response.status_code == 200:
                            content_type = response.headers.get("content-type", "")
                            if "csv" in content_type or "text" in content_type:
                                content_preview = response.text[:500]
                                if "," in content_preview or ";" in content_preview:
                                    filename = f"{tipo.upper()}_{ano}_{mes:02d}.csv"
                                    filepath = download_dir / filename
                                    
                                    try:
                                        filepath.write_text(response.text, encoding='utf-8')
                                    except:
                                        filepath.write_bytes(response.content)
                                    
                                    logger.info(f"✅ Arquivo baixado: {filepath}")
                                    arquivos_baixados.append(filepath)
                                    break
                except Exception as e:
                    logger.debug(f"URL {url} não funcionou: {e}")
                    continue
            
            await asyncio.sleep(1)  # Delay entre tentativas
    
    return arquivos_baixados


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("INTEGRAÇÃO COM DADOS REAIS - COMEX STAT")
    logger.info("=" * 60)
    logger.info("")
    
    # 1. Limpar dados de exemplo
    logger.info("1️⃣  Removendo dados de exemplo...")
    await limpar_dados_exemplo()
    logger.info("")
    
    # 2. Baixar dados reais
    logger.info("2️⃣  Baixando dados reais do portal...")
    arquivos = await baixar_dados_reais()
    
    if arquivos:
        logger.info("")
        logger.info(f"✅ {len(arquivos)} arquivo(s) baixado(s)!")
        logger.info("")
        logger.info("3️⃣  Processando arquivos...")
        logger.info("   Execute: python scripts/process_files.py")
        logger.info("")
    else:
        logger.warning("")
        logger.warning("⚠️  Não foi possível baixar dados automaticamente")
        logger.warning("")
        logger.info("=" * 60)
        logger.info("INSTRUÇÕES PARA DADOS REAIS:")
        logger.info("=" * 60)
        logger.info("")
        logger.info("OPÇÃO 1: Download Manual (Recomendado)")
        logger.info("   1. Acesse: https://comexstat.mdic.gov.br")
        logger.info("   2. Vá em: Dados Abertos > Download")
        logger.info("   3. Baixe arquivos CSV de Exportação e Importação")
        logger.info("   4. Salve em: C:\\Users\\User\\Desktop\\Cursor\\Projetos\\data\\raw\\")
        logger.info("   5. Execute: python scripts/process_files.py")
        logger.info("")
        logger.info("OPÇÃO 2: Configurar API (se tiver credenciais)")
        logger.info("   1. Edite: backend/.env")
        logger.info("   2. Adicione:")
        logger.info("      COMEX_STAT_API_URL=https://api-comexstat.mdic.gov.br")
        logger.info("      COMEX_STAT_API_KEY=sua_chave_aqui")
        logger.info("   3. Execute este script novamente")
        logger.info("")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

