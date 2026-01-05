"""
Script para diagnosticar o status do backend.
Verifica se o backend está acessível e funcionando.
"""
import sys
import requests
from pathlib import Path
from datetime import datetime

def verificar_backend(base_url: str, timeout: int = 10) -> dict:
    """
    Verifica o status do backend.
    
    Args:
        base_url: URL do backend
        timeout: Timeout em segundos
    
    Returns:
        Dicionário com status e informações
    """
    resultado = {
        "url": base_url,
        "acessivel": False,
        "status_code": None,
        "health_check": False,
        "erro": None,
        "recomendacoes": []
    }
    
    print(f"🔍 Verificando backend: {base_url}")
    print("-" * 80)
    
    # Teste 1: Verificar se o servidor responde
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        resultado["status_code"] = response.status_code
        resultado["acessivel"] = response.status_code < 500
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                resultado["health_check"] = True
                print(f"✅ Backend está respondendo (Status: {response.status_code})")
                print(f"   Health check: {health_data}")
            except:
                print(f"⚠️  Backend respondeu mas não retornou JSON válido")
                resultado["health_check"] = False
        elif response.status_code == 502:
            resultado["erro"] = "502 Bad Gateway - Backend pode estar iniciando ou offline"
            resultado["recomendacoes"].append("O backend pode estar iniciando. Aguarde alguns minutos.")
            resultado["recomendacoes"].append("Verifique os logs do Render para mais detalhes.")
            print(f"❌ Erro 502: Backend pode estar iniciando ou offline")
        elif response.status_code == 503:
            resultado["erro"] = "503 Service Unavailable - Backend pode estar sobrecarregado"
            resultado["recomendacoes"].append("Backend pode estar sobrecarregado. Tente novamente em alguns minutos.")
            print(f"⚠️  Erro 503: Backend pode estar sobrecarregado")
        else:
            resultado["erro"] = f"Status {response.status_code}"
            print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
    
    except requests.exceptions.Timeout:
        resultado["erro"] = "Timeout - Backend não respondeu a tempo"
        resultado["recomendacoes"].append("Backend pode estar offline ou muito lento.")
        resultado["recomendacoes"].append("Verifique se o serviço está rodando no Render.")
        print(f"❌ Timeout: Backend não respondeu em {timeout} segundos")
    
    except requests.exceptions.ConnectionError:
        resultado["erro"] = "Connection Error - Não foi possível conectar"
        resultado["recomendacoes"].append("Verifique sua conexão com a internet.")
        resultado["recomendacoes"].append("Verifique se a URL está correta.")
        print(f"❌ Erro de conexão: Não foi possível conectar ao backend")
    
    except Exception as e:
        resultado["erro"] = str(e)
        resultado["recomendacoes"].append(f"Erro inesperado: {e}")
        print(f"❌ Erro inesperado: {e}")
    
    return resultado


def diagnosticar_completo(base_url: str = "https://comex-backend-wjco.onrender.com"):
    """
    Executa diagnóstico completo do backend.
    """
    print("=" * 80)
    print("DIAGNÓSTICO DO BACKEND")
    print("=" * 80)
    print()
    
    # Verificar backend principal
    resultado = verificar_backend(base_url)
    
    print()
    print("=" * 80)
    print("RESULTADO DO DIAGNÓSTICO")
    print("=" * 80)
    print()
    
    if resultado["acessivel"] and resultado["health_check"]:
        print("✅ BACKEND ESTÁ FUNCIONANDO CORRETAMENTE")
        print()
        print("Você pode executar a coleta agora:")
        print("  python backend/scripts/executar_coleta.py")
        print()
    else:
        print("❌ BACKEND NÃO ESTÁ ACESSÍVEL")
        print()
        print(f"URL testada: {resultado['url']}")
        if resultado["erro"]:
            print(f"Erro: {resultado['erro']}")
        print()
        
        print("💡 RECOMENDAÇÕES:")
        for i, rec in enumerate(resultado["recomendacoes"], 1):
            print(f"   {i}. {rec}")
        
        print()
        print("🔧 AÇÕES SUGERIDAS:")
        print("   1. Verifique o status do serviço no Render:")
        print("      https://dashboard.render.com")
        print("   2. Verifique os logs do backend no Render")
        print("   3. Aguarde alguns minutos se o backend estiver iniciando")
        print("   4. Tente usar o backend local:")
        print("      python backend/scripts/executar_coleta.py --local")
        print()
        
        # Verificar backend local como alternativa
        print("🔍 Verificando backend local...")
        resultado_local = verificar_backend("http://localhost:8000", timeout=5)
        
        if resultado_local["acessivel"] and resultado_local["health_check"]:
            print()
            print("✅ BACKEND LOCAL ESTÁ FUNCIONANDO!")
            print("   Use: python backend/scripts/executar_coleta.py --local")
        else:
            print("   ⚠️  Backend local também não está acessível")
            print("   Para iniciar o backend local:")
            print("   INICIAR_BACKEND.bat")
    
    print()
    print("=" * 80)
    
    return resultado


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnosticar status do backend")
    parser.add_argument(
        "--url",
        default="https://comex-backend-wjco.onrender.com",
        help="URL do backend para verificar"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Verificar apenas backend local"
    )
    
    args = parser.parse_args()
    
    if args.local:
        diagnosticar_completo("http://localhost:8000")
    else:
        diagnosticar_completo(args.url)


if __name__ == "__main__":
    main()

