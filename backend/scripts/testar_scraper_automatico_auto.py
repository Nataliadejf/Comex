"""
Script para testar o scraper automático do ComexStat (versão automática).
Executa automaticamente sem pedir confirmação.
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
        print("1. Testando download de um mês específico...")
        print("   (Ano: 2025, Mês: 12, Tipo: Ambos)")
        print("   Modo: Headless (sem interface gráfica)")
        print()
        
        # Testar com modo headless primeiro
        arquivo = scraper.baixar_dados(
            ano=2025,
            mes=12,
            tipo_operacao="Ambos",
            headless=True
        )
        
        if arquivo:
            print(f"\n✅ Sucesso! Arquivo baixado: {arquivo.name}")
            print(f"   Localização: {arquivo}")
            print(f"   Tamanho: {arquivo.stat().st_size:,} bytes")
            
            # Verificar se é CSV válido
            try:
                with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira_linha = f.read(200).strip().lower()
                    if primeira_linha.startswith('<!doctype') or primeira_linha.startswith('<html'):
                        print("   ⚠️ ATENÇÃO: Arquivo parece ser HTML, não CSV!")
                    else:
                        print("   ✅ Arquivo parece ser CSV válido")
            except Exception as e:
                print(f"   ⚠️ Erro ao verificar arquivo: {e}")
        else:
            print("\n❌ Download não foi concluído")
            print("\n💡 Possíveis causas:")
            print("   - A página não carregou corretamente")
            print("   - Os filtros não foram preenchidos")
            print("   - O botão de download não foi encontrado")
            print("   - O site pode ter mudado sua estrutura")
            print("\n💡 Tente executar em modo visível para debug:")
            print("   python backend/scripts/testar_scraper_automatico.py")
            print("   (e escolha 'n' quando perguntar sobre headless)")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Verifique:")
        print("   - Se o Chrome está instalado")
        print("   - Se há conexão com a internet")
        print("   - Se o site está acessível: https://comexstat.mdic.gov.br/pt/dados-gerais")
    
    finally:
        scraper._close_driver()

if __name__ == "__main__":
    testar_scraper()


