"""
Script para validar se a DATABASE_URL está configurada corretamente.

USO:
    python backend/scripts/validar_database_url.py
"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def validar_database_url():
    """Valida a DATABASE_URL configurada."""
    print("="*80)
    print("VALIDAÇÃO DA DATABASE_URL")
    print("="*80)
    
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        print("❌ DATABASE_URL não configurada!")
        print("\n💡 Configure a variável DATABASE_URL com a URL do PostgreSQL")
        print("   Exemplo: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        return False
    
    print(f"\n📋 DATABASE_URL encontrada:")
    print(f"   Tamanho: {len(database_url)} caracteres")
    
    # Mostrar primeiros e últimos caracteres (sem mostrar senha completa)
    if len(database_url) > 100:
        print(f"   Início: {database_url[:30]}...")
        print(f"   Fim: ...{database_url[-30:]}")
    else:
        print(f"   Valor: {database_url[:50]}..." if len(database_url) > 50 else f"   Valor: {database_url}")
    
    # Validar formato
    print("\n🔍 Validando formato...")
    
    erros = []
    
    # Verificar se começa com protocolo válido
    if not (database_url.startswith("postgresql://") or 
            database_url.startswith("postgres://") or 
            database_url.startswith("sqlite:///")):
        erros.append("❌ URL deve começar com 'postgresql://', 'postgres://' ou 'sqlite:///'")
    
    # Verificar tamanho mínimo para PostgreSQL
    if database_url.startswith(("postgresql://", "postgres://")):
        if len(database_url) < 50:
            erros.append("❌ URL muito curta (menos de 50 caracteres). URLs PostgreSQL válidas são maiores.")
        
        # Verificar formato básico
        if "@" not in database_url:
            erros.append("❌ URL deve conter '@' separando credenciais do host")
        
        if ":" not in database_url:
            erros.append("❌ URL deve conter ':' separando usuário da senha e host da porta")
        
        # Tentar parsear componentes básicos
        try:
            # Remover protocolo
            sem_protocolo = database_url.split("://", 1)[1]
            
            # Separar credenciais e host
            if "@" in sem_protocolo:
                credenciais, resto = sem_protocolo.split("@", 1)
                if ":" in credenciais:
                    usuario, senha = credenciais.split(":", 1)
                    print(f"   ✅ Usuário encontrado: {usuario}")
                    print(f"   ✅ Senha encontrada: {'*' * len(senha)}")
                
                # Separar host e porta
                if ":" in resto:
                    host, porta_db = resto.split(":", 1)
                    print(f"   ✅ Host encontrado: {host}")
                    
                    # Separar porta e database
                    if "/" in porta_db:
                        porta, database = porta_db.split("/", 1)
                        try:
                            porta_int = int(porta)
                            print(f"   ✅ Porta válida: {porta_int}")
                        except ValueError:
                            erros.append(f"❌ Porta inválida: '{porta}' (deve ser um número)")
                        print(f"   ✅ Database: {database}")
                    else:
                        erros.append("❌ URL deve conter '/' separando porta do nome do banco")
                else:
                    erros.append("❌ URL deve conter ':' separando host da porta")
            else:
                erros.append("❌ URL deve conter '@' separando credenciais do host")
        except Exception as e:
            erros.append(f"❌ Erro ao parsear URL: {e}")
    
    # Verificar se parece ser apenas um hash/ID
    if len(database_url) < 50 and not database_url.startswith("sqlite:///"):
        erros.append("⚠️ URL muito curta - pode ser apenas um hash/ID, não uma URL completa")
    
    # Mostrar resultado
    print("\n" + "="*80)
    if erros:
        print("❌ ERROS ENCONTRADOS:")
        for erro in erros:
            print(f"   {erro}")
        print("\n💡 SOLUÇÃO:")
        print("   1. No Render Dashboard, vá em PostgreSQL → Seu banco → Connections")
        print("   2. Copie a 'Internal Database URL'")
        print("   3. Cole no campo DATABASE_URL do backend")
        print("   4. Formato esperado: postgresql://user:pass@host:port/dbname")
        print("\n" + "="*80)
        return False
    else:
        print("✅ DATABASE_URL válida!")
        print("\n" + "="*80)
        return True

if __name__ == "__main__":
    sucesso = validar_database_url()
    sys.exit(0 if sucesso else 1)
