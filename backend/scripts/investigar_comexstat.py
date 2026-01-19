"""
Script para investigar a estrutura do ComexStat e encontrar endpoints de download.
"""
import asyncio
import aiohttp
from pathlib import Path
import sys
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from loguru import logger

async def investigar_comexstat():
    """Investiga a estrutura do ComexStat."""
    print("="*60)
    print("INVESTIGAÇÃO DO COMEXSTAT")
    print("="*60)
    print()
    
    base_url = "https://comexstat.mdic.gov.br"
    
    # URLs para testar
    urls_para_testar = [
        f"{base_url}/pt/home",
        f"{base_url}/api",
        f"{base_url}/api/dados",
        f"{base_url}/api/geral",
        f"{base_url}/pt/dados-gerais",
        f"{base_url}/api/export",
        f"{base_url}/api/download",
        "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm",
        "https://balanca.economia.gov.br/balanca/bd/comexstat-bd",
    ]
    
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        print("1. Testando URLs principais...\n")
        
        for url in urls_para_testar:
            try:
                print(f"   Testando: {url}")
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    status = response.status
                    
                    if status == 200:
                        content = await response.text()
                        content_preview = content[:500].replace('\n', ' ').strip()
                        
                        if 'html' in content_type.lower():
                            # Procurar por links ou endpoints interessantes
                            if 'api' in content.lower() or 'download' in content.lower() or 'csv' in content.lower():
                                print(f"      ✅ Status: {status} | Content-Type: {content_type}")
                                print(f"      📄 Preview: {content_preview[:200]}...")
                                print(f"      💡 Possíveis endpoints encontrados!")
                            else:
                                print(f"      ⚠️ Status: {status} | HTML (página normal)")
                        elif 'json' in content_type.lower():
                            print(f"      ✅ Status: {status} | JSON API encontrada!")
                            print(f"      📄 Preview: {content_preview[:200]}...")
                        elif 'csv' in content_type.lower() or 'text/csv' in content_type.lower():
                            print(f"      ✅ Status: {status} | CSV encontrado!")
                        else:
                            print(f"      ✅ Status: {status} | Content-Type: {content_type}")
                    else:
                        print(f"      ❌ Status: {status}")
            except Exception as e:
                print(f"      ❌ Erro: {str(e)[:100]}")
            
            print()
            await asyncio.sleep(0.5)
        
        # Tentar encontrar endpoints de download específicos
        print("\n2. Testando endpoints de download específicos...\n")
        
        # Padrões comuns de URLs de download
        padroes_download = [
            f"{base_url}/api/export/csv",
            f"{base_url}/api/download/csv",
            f"{base_url}/export/csv",
            f"{base_url}/download/csv",
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_2025_12.csv",
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_2025_12.csv",
        ]
        
        for url in padroes_download:
            try:
                print(f"   Testando: {url}")
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                ) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')
                    
                    if status == 200:
                        if 'csv' in content_type.lower() or 'text/csv' in content_type.lower():
                            print(f"      ✅ CSV válido encontrado!")
                            # Verificar conteúdo
                            content = await response.read()
                            if len(content) > 100 and not content[:100].decode('utf-8', errors='ignore').lower().startswith('<!doctype'):
                                print(f"      ✅ Arquivo CSV válido ({len(content)} bytes)")
                            else:
                                print(f"      ⚠️ Parece ser HTML disfarçado")
                        else:
                            print(f"      ⚠️ Status: {status} | Content-Type: {content_type}")
                    else:
                        print(f"      ❌ Status: {status}")
            except Exception as e:
                print(f"      ❌ Erro: {str(e)[:100]}")
            
            print()
            await asyncio.sleep(0.5)
    
    print("="*60)
    print("INVESTIGAÇÃO CONCLUÍDA")
    print("="*60)
    print("\n💡 Próximos passos:")
    print("   1. Verificar manualmente o site: https://comexstat.mdic.gov.br/pt/home")
    print("   2. Usar o módulo 'Dados Gerais' para entender a estrutura")
    print("   3. Verificar se há uma API REST disponível")
    print("   4. Considerar usar web scraping se necessário")

if __name__ == "__main__":
    asyncio.run(investigar_comexstat())


