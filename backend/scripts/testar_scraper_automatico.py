"""
Script para testar o scraper automático do ComexStat.
"""
import sys
from pathlib import Path
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.comexstat_scraper import ComexStatScraper
from loguru import logger

def testar_scraper():
    """Testa o scraper automático."""
    print("="*60)
    print("TESTE DO SCRAPER AUTOMÁTICO COMEXSTAT")
    print("="*60)
    print()
    
    scraper = ComexStatScraper()
    
    try:
        print("⚠️ IMPORTANTE:")
        print("   - Este script requer Selenium e ChromeDriver instalados")
        print("   - O ChromeDriver deve estar no PATH ou no mesmo diretório")
        print("   - O download será feito automaticamente via interface web")
        print()
        
        resposta = input("Deseja continuar? (s/n): ").lower()
        if resposta != 's':
            print("Teste cancelado.")
            return
        
        print("\n1. Testando download de um mês específico...")
        print("   (Ano: 2025, Mês: 12, Tipo: Ambos)")
        print()
        
        # Testar com modo não-headless primeiro para debug
        headless_input = input("Executar em modo headless (sem interface)? (s/n): ").lower()
        headless = headless_input == 's'
        
        arquivo = scraper.baixar_dados(
            ano=2025,
            mes=12,
            tipo_operacao="Ambos",
            headless=headless
        )
        
        if arquivo:
            print(f"\n✅ Sucesso! Arquivo baixado: {arquivo.name}")
            print(f"   Localização: {arquivo}")
            print(f"   Tamanho: {arquivo.stat().st_size:,} bytes")
        else:
            print("\n❌ Download não foi concluído")
            print("💡 Verifique:")
            print("   - Se o ChromeDriver está instalado")
            print("   - Se a página carregou corretamente")
            print("   - Se os filtros foram preenchidos")
            print("   - Se o botão de download foi encontrado")
        
        print("\n" + "="*60)
        
        # Perguntar se quer baixar mais meses
        resposta = input("\nDeseja baixar mais meses? (s/n): ").lower()
        if resposta == 's':
            meses_input = input("Quantos meses deseja baixar? (padrão: 3): ")
            meses = int(meses_input) if meses_input.isdigit() else 3
            
            print(f"\n2. Baixando últimos {meses} meses...")
            print("   (Isso pode levar alguns minutos)")
            print()
            
            arquivos = scraper.baixar_meses_recentes(
                meses=meses,
                tipo_operacao="Ambos",
                headless=headless
            )
            
            if arquivos:
                print(f"\n✅ Total de {len(arquivos)} arquivo(s) baixado(s):")
                for arquivo in arquivos:
                    print(f"   - {arquivo.name} ({arquivo.stat().st_size:,} bytes)")
            else:
                print("\n❌ Nenhum arquivo foi baixado")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper._close_driver()
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    testar_scraper()


