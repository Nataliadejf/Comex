"""
Script para testar a API do Comex Stat de forma detalhada.
Testa diferentes URLs, métodos e formatos para entender o que está disponível.
"""
import sys
import os
import asyncio
import aiohttp
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

async def test_url(session, url, method="GET", params=None, headers=None):
    """Testa uma URL e retorna informações detalhadas."""
    try:
        if method == "GET":
            async with session.get(url, params=params, headers=headers) as response:
                content_type = response.headers.get("content-type", "").lower()
                status = response.status
                text = await response.text()
                
                return {
                    "url": str(response.url),
                    "status": status,
                    "content_type": content_type,
                    "is_json": "application/json" in content_type,
                    "is_html": "text/html" in content_type,
                    "is_xml": "xml" in content_type,
                    "size": len(text),
                    "preview": text[:500] if len(text) > 0 else "",
                    "success": status == 200
                }
        else:
            async with session.post(url, json=params, headers=headers) as response:
                content_type = response.headers.get("content-type", "").lower()
                status = response.status
                text = await response.text()
                
                return {
                    "url": str(response.url),
                    "status": status,
                    "content_type": content_type,
                    "is_json": "application/json" in content_type,
                    "is_html": "text/html" in content_type,
                    "is_xml": "xml" in content_type,
                    "size": len(text),
                    "preview": text[:500] if len(text) > 0 else "",
                    "success": status == 200
                }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

async def main():
    """Executa testes detalhados na API do Comex Stat."""
    base_urls = [
        "https://comexstat.mdic.gov.br",
        "http://comexstat.mdic.gov.br",  # Tentar HTTP também
    ]
    
    endpoints_to_test = [
        "/dados",
        "/api/dados",
        "/api/v1/dados",
        "/api/comex/dados",
        "/dados/export",
        "/api/export",
        "/api",
        "/",
    ]
    
    # Parâmetros de teste
    test_params = {
        "mes_inicio": "2024-01",
        "mes_fim": "2024-01",
        "tipo_operacao": "Importação"
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("=" * 80)
    print("TESTE DETALHADO DA API COMEX STAT")
    print("=" * 80)
    print()
    
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        results = []
        
        for base_url in base_urls:
            print(f"\n🔍 Testando base URL: {base_url}")
            print("-" * 80)
            
            for endpoint in endpoints_to_test:
                url = f"{base_url}{endpoint}"
                print(f"\n📡 Testando: {url}")
                
                # Teste GET
                result = await test_url(session, url, method="GET", params=test_params, headers=headers)
                results.append(result)
                
                if result.get("success"):
                    print(f"   ✅ Status: {result['status']}")
                    print(f"   📄 Content-Type: {result.get('content_type', 'N/A')}")
                    print(f"   📊 Tamanho: {result.get('size', 0)} bytes")
                    
                    if result.get("is_json"):
                        print(f"   🎉 JSON detectado!")
                    elif result.get("is_html"):
                        print(f"   ⚠️  HTML detectado")
                        # Tentar encontrar informações úteis no HTML
                        preview = result.get("preview", "")
                        if "api" in preview.lower() or "json" in preview.lower():
                            print(f"   💡 HTML pode conter referências à API")
                    elif result.get("is_xml"):
                        print(f"   📋 XML detectado")
                    
                    if result.get("preview"):
                        print(f"   👀 Preview: {result['preview'][:200]}...")
                else:
                    if "error" in result:
                        print(f"   ❌ Erro: {result['error']}")
                    else:
                        print(f"   ⚠️  Status: {result.get('status', 'N/A')}")
                        print(f"   📄 Content-Type: {result.get('content_type', 'N/A')}")
                
                # Pequeno delay para não sobrecarregar
                await asyncio.sleep(0.5)
        
        # Resumo
        print("\n" + "=" * 80)
        print("RESUMO DOS TESTES")
        print("=" * 80)
        
        successful = [r for r in results if r.get("success")]
        json_responses = [r for r in results if r.get("is_json")]
        html_responses = [r for r in results if r.get("is_html")]
        
        print(f"\n✅ Respostas bem-sucedidas (200): {len(successful)}")
        print(f"📄 Respostas JSON: {len(json_responses)}")
        print(f"🌐 Respostas HTML: {len(html_responses)}")
        
        if json_responses:
            print("\n🎉 ENDPOINTS QUE RETORNARAM JSON:")
            for r in json_responses:
                print(f"   - {r['url']}")
        
        if html_responses:
            print("\n⚠️  ENDPOINTS QUE RETORNARAM HTML:")
            for r in html_responses[:5]:  # Mostrar apenas os primeiros 5
                print(f"   - {r['url']}")
                print(f"     Preview: {r.get('preview', '')[:100]}...")
        
        if not json_responses:
            print("\n❌ CONCLUSÃO:")
            print("   A API do Comex Stat não parece ter uma API REST pública disponível.")
            print("   Todos os endpoints testados retornaram HTML ao invés de JSON.")
            print("\n💡 RECOMENDAÇÕES:")
            print("   1. Use dados de exemplo para testes: /popular-dados-exemplo")
            print("   2. Verifique se há documentação oficial da API do MDIC")
            print("   3. Entre em contato com o MDIC para acesso à API")
            print("   4. Considere usar o scraper se necessário")

if __name__ == "__main__":
    asyncio.run(main())



