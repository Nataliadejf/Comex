#!/usr/bin/env python3
"""
Script para instalar todas as dependências necessárias para o coletor público.
"""
import subprocess
import sys
from pathlib import Path

def instalar_dependencias():
    """Instala todas as dependências do projeto."""
    print("="*70)
    print("INSTALAÇÃO DE DEPENDÊNCIAS")
    print("="*70)
    print()
    
    requirements_file = Path(__file__).parent / "backend" / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Arquivo não encontrado: {requirements_file}")
        return False
    
    print(f"📦 Instalando dependências de: {requirements_file}")
    print()
    
    try:
        # Instalar do requirements.txt
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Dependências instaladas com sucesso!")
        print()
        print("📋 Dependências principais instaladas:")
        print("   - fastapi, uvicorn")
        print("   - sqlalchemy")
        print("   - pandas, numpy")
        print("   - beautifulsoup4 (bs4)")
        print("   - requests")
        print("   - google-cloud-bigquery")
        print("   - loguru")
        print()
        print("="*70)
        print("✅ INSTALAÇÃO CONCLUÍDA!")
        print("="*70)
        print()
        print("💡 Próximos passos:")
        print("   1. Execute: python validar_bigquery.py")
        print("   2. Execute: python coletar_dados_publicos_standalone.py --limite 1000")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    sucesso = instalar_dependencias()
    sys.exit(0 if sucesso else 1)
