"""
Teste rápido para verificar se o Selenium está funcionando corretamente.
"""
import sys
from pathlib import Path
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

print("="*60)
print("TESTE RÁPIDO DO SELENIUM")
print("="*60)
print()

try:
    print("1. Verificando importações...")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    print("   ✅ Selenium importado com sucesso")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("   ✅ webdriver-manager importado com sucesso")
        webdriver_manager_available = True
    except ImportError:
        print("   ⚠️ webdriver-manager não disponível")
        webdriver_manager_available = False
    
    print("\n2. Testando inicialização do ChromeDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        if webdriver_manager_available:
            print("   Usando webdriver-manager para ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            print("   Usando ChromeDriver do PATH...")
            driver = webdriver.Chrome(options=chrome_options)
        
        print("   ✅ ChromeDriver inicializado com sucesso!")
        
        print("\n3. Testando navegação...")
        driver.get("https://www.google.com")
        print(f"   ✅ Navegação funcionando! Título: {driver.title[:50]}")
        
        print("\n4. Fechando driver...")
        driver.quit()
        print("   ✅ Driver fechado com sucesso")
        
        print("\n" + "="*60)
        print("✅ TUDO FUNCIONANDO PERFEITAMENTE!")
        print("="*60)
        print("\nO web scraping está pronto para uso.")
        print("Você pode executar:")
        print("  python backend/scripts/testar_scraper_automatico.py")
        
    except Exception as e:
        print(f"\n❌ Erro ao inicializar ChromeDriver: {e}")
        print("\n💡 Possíveis soluções:")
        print("   1. Verifique se o Chrome está instalado")
        print("   2. Instale o ChromeDriver manualmente")
        print("   3. Ou use webdriver-manager: pip install webdriver-manager")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"\n❌ Erro ao importar Selenium: {e}")
    print("\n💡 Instale com: pip install selenium")
    
except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()


