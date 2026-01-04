"""
Script para verificar capacidade local antes de popular banco.
"""
import sys
import os
import shutil
from pathlib import Path

def verificar_capacidade():
    """Verifica capacidade do sistema."""
    print("=" * 60)
    print("VERIFICANDO CAPACIDADE LOCAL")
    print("=" * 60)
    print()
    
    # Verificar espaço em disco
    print("📦 ESPAÇO EM DISCO:")
    try:
        stat = shutil.disk_usage(".")
        total_gb = stat.total / (1024**3)
        usado_gb = stat.used / (1024**3)
        livre_gb = stat.free / (1024**3)
        
        print(f"   Total: {total_gb:.2f} GB")
        print(f"   Usado: {usado_gb:.2f} GB")
        print(f"   Livre: {livre_gb:.2f} GB")
        
        if livre_gb >= 5:
            print("   ✅ Espaço suficiente (recomendado: 5GB+)")
        elif livre_gb >= 1:
            print("   ⚠️  Espaço mínimo disponível (recomendado: 5GB+)")
        else:
            print("   ❌ Espaço insuficiente! Libere espaço antes de continuar.")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar espaço: {e}")
    
    print()
    
    # Verificar memória (aproximado)
    print("💾 MEMÓRIA RAM:")
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        disponivel_gb = mem.available / (1024**3)
        usado_gb = mem.used / (1024**3)
        
        print(f"   Total: {total_gb:.2f} GB")
        print(f"   Usado: {usado_gb:.2f} GB")
        print(f"   Disponível: {disponivel_gb:.2f} GB")
        
        if disponivel_gb >= 2:
            print("   ✅ Memória suficiente (recomendado: 2GB+ livre)")
        elif disponivel_gb >= 1:
            print("   ⚠️  Memória mínima disponível")
        else:
            print("   ❌ Memória insuficiente!")
    except ImportError:
        print("   ⚠️  psutil não instalado. Instale com: pip install psutil")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar memória: {e}")
    
    print()
    
    # Verificar tamanho do banco atual
    print("🗄️  BANCO DE DADOS:")
    try:
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / "comex_analyzer.db"
        if db_path.exists():
            tamanho_mb = db_path.stat().st_size / (1024**2)
            print(f"   Tamanho atual: {tamanho_mb:.2f} MB")
        else:
            print("   Banco ainda não existe")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar banco: {e}")
    
    print()
    print("=" * 60)
    print("RECOMENDAÇÕES:")
    print("=" * 60)
    print()
    print("✅ Se tudo estiver OK, execute: POPULAR_BANCO.bat")
    print("⚠️  Se houver problemas, veja: OPCOES_HOSPEDAGEM.md")
    print()

if __name__ == "__main__":
    verificar_capacidade()


