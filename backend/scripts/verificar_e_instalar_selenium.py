"""
Script para verificar e instalar dependências do web scraping.
Verifica antes de instalar para não sobrecarregar a máquina.
"""
import sys
import subprocess

def verificar_import(module_name):
    """Verifica se um módulo pode ser importado."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def instalar_pacote(package_name):
    """Instala um pacote usando pip."""
    try:
        print(f"   Instalando {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erro ao instalar {package_name}: {e}")
        return False

def main():
    print("="*60)
    print("VERIFICAÇÃO E INSTALAÇÃO DE DEPENDÊNCIAS")
    print("="*60)
    print()
    
    # Dicionário de pacotes e seus nomes de importação
    pacotes = {
        "selenium": "selenium",
        "webdriver-manager": "webdriver_manager"
    }
    
    instalados = []
    ja_instalados = []
    
    for package_name, import_name in pacotes.items():
        print(f"Verificando {package_name}...")
        
        if verificar_import(import_name):
            print(f"   ✅ {package_name} já está instalado")
            ja_instalados.append(package_name)
            
            # Verificar versão se possível
            try:
                if import_name == "selenium":
                    import selenium
                    print(f"      Versão: {selenium.__version__}")
                elif import_name == "webdriver_manager":
                    import webdriver_manager
                    print(f"      Versão: {webdriver_manager.__version__}")
            except:
                pass
        else:
            print(f"   ⚠️ {package_name} não está instalado")
            resposta = input(f"   Deseja instalar {package_name}? (s/n): ").lower()
            
            if resposta == 's':
                if instalar_pacote(package_name):
                    # Verificar se foi instalado corretamente
                    if verificar_import(import_name):
                        print(f"   ✅ {package_name} instalado com sucesso!")
                        instalados.append(package_name)
                    else:
                        print(f"   ⚠️ {package_name} foi instalado mas não pode ser importado")
                else:
                    print(f"   ❌ Falha ao instalar {package_name}")
            else:
                print(f"   ⏭️ Pulando instalação de {package_name}")
        
        print()
    
    # Resumo
    print("="*60)
    print("RESUMO")
    print("="*60)
    
    if ja_instalados:
        print(f"✅ Já instalados ({len(ja_instalados)}):")
        for pkg in ja_instalados:
            print(f"   - {pkg}")
    
    if instalados:
        print(f"\n✅ Instalados agora ({len(instalados)}):")
        for pkg in instalados:
            print(f"   - {pkg}")
    
    if not ja_instalados and not instalados:
        print("⚠️ Nenhuma dependência está disponível")
        print("   Execute novamente e escolha 's' para instalar")
    
    # Verificar se tudo está pronto
    print("\n" + "="*60)
    tudo_pronto = verificar_import("selenium")
    
    if tudo_pronto:
        print("✅ TUDO PRONTO!")
        print("   O web scraping está pronto para uso.")
        print("\n   Você pode testar com:")
        print("   python backend/scripts/testar_scraper_automatico.py")
    else:
        print("⚠️ SELENIUM NÃO ESTÁ DISPONÍVEL")
        print("   Instale manualmente com:")
        print("   pip install selenium")
    
    print("="*60)

if __name__ == "__main__":
    main()


