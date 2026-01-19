"""
Script para testar o novo scraper do ComexStat.
"""
import asyncio
import sys
from pathlib import Path
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.comexstat_scraper import ComexStatScraper
from loguru import logger

async def testar():
    """Testa o scraper do ComexStat."""
    print("="*60)
    print("TESTE DO SCRAPER COMEXSTAT")
    print("="*60)
    print()
    
    scraper = ComexStatScraper()
    
    try:
        print("1. Tentando descobrir endpoints da API...")
        print("   (Isso pode levar alguns minutos - precisa do Selenium)")
        print()
        
        endpoints = await scraper.encontrar_endpoints_api()
        
        if endpoints:
            print(f"   ✅ {len(endpoints)} endpoint(s) encontrado(s):")
            for nome, url in endpoints.items():
                print(f"      - {nome}: {url}")
        else:
            print("   ⚠️ Nenhum endpoint encontrado automaticamente")
            print("   💡 Isso pode significar que:")
            print("      - O site usa uma estrutura diferente")
            print("      - É necessário interagir com a interface web")
            print("      - Os endpoints estão protegidos/autenticados")
        
        print()
        print("2. Tentando baixar dados usando endpoints descobertos...")
        print()
        
        arquivos = await scraper.baixar_via_api_descoberta(2025, 12, "both")
        
        if arquivos:
            print(f"   ✅ {len(arquivos)} arquivo(s) baixado(s):")
            for arquivo in arquivos:
                print(f"      - {arquivo.name}")
        else:
            print("   ⚠️ Nenhum arquivo foi baixado")
            print()
            print("   💡 Próximos passos:")
            print("      1. Verificar manualmente o site:")
            print("         https://comexstat.mdic.gov.br/pt/dados-gerais")
            print("      2. Usar o módulo 'Dados Gerais' para fazer um download manual")
            print("      3. Verificar a URL do download no navegador (F12 > Network)")
            print("      4. Compartilhar a URL encontrada para atualizar o código")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper._close_driver()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(testar())


