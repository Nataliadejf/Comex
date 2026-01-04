"""
Script para testar o cadastro manualmente.
"""
import sys
from pathlib import Path
import requests
import json

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def testar_cadastro():
    """Testa o endpoint de cadastro."""
    url = "http://localhost:8000/register"
    
    payload = {
        "email": "teste@exemplo.com",
        "password": "senha123",
        "nome_completo": "Teste Usuario",
        "data_nascimento": "1987-08-24",
        "nome_empresa": "GHT",
        "cpf": "12220210723",
        "cnpj": None
    }
    
    print("=" * 60)
    print("TESTANDO CADASTRO")
    print("=" * 60)
    print()
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Cadastro realizado com sucesso!")
        else:
            print(f"\n❌ Erro: {response.json().get('detail', 'Erro desconhecido')}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao backend.")
        print("   Certifique-se de que o backend está rodando em http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_cadastro()


