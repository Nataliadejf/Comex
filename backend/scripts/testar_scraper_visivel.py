"""
Script para testar o scraper automático do ComexStat em modo VISÍVEL.
Este script abre o navegador para que você possa ver o que está acontecendo.
"""
import sys
from pathlib import Path
import os
from datetime import datetime, timedelta

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.comexstat_scraper import ComexStatScraper
from loguru import logger

def testar_scraper_visivel():
    """Testa o scraper em modo visível."""
    print("="*60)
    print("TESTE DO SCRAPER AUTOMÁTICO COMEXSTAT - MODO VISÍVEL")
    print("="*60)
    print()
    print("⚠️ IMPORTANTE:")
    print("   - O navegador será aberto e você poderá ver o que está acontecendo")
    print("   - Não feche o navegador durante o teste")
    print("   - Observe se há popups ou confirmações que precisam ser aceitas")
    print()
    
    scraper = ComexStatScraper()
    
    try:
        print("1. Testando download de um mês específico...")
        print("   (Ano: 2025, Mês: 12, Tipo: Ambos)")
        print("   Modo: VISÍVEL (você verá o navegador)")
        print()
        print("   Pressione ENTER para iniciar o teste...")
        input()
        
        # Testar com modo VISÍVEL (headless=False)
        arquivo = scraper.baixar_dados(
            ano=2025,
            mes=12,
            tipo_operacao="Ambos",
            headless=False  # MODO VISÍVEL
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
            print("\n💡 O que você observou no navegador?")
            print("   - O botão CSV foi clicado?")
            print("   - Apareceu algum popup ou confirmação?")
            print("   - O download iniciou mas não foi detectado?")
            print("   - Algum erro apareceu na página?")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("="*60)
        print("\n💡 Se o download não funcionou, verifique:")
        print("   1. Se há algum popup bloqueando o download")
        print("   2. Se o Chrome está pedindo confirmação")
        print("   3. Se o arquivo foi baixado em outro local")
        print("   4. Se há algum erro na página após clicar em CSV")
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Verifique:")
        print("   - Se o Chrome está instalado")
        print("   - Se há conexão com a internet")
        print("   - Se o site está acessível: https://comexstat.mdic.gov.br/pt/dados-gerais")
    
    finally:
        print("\n⚠️ Pressione ENTER para fechar o navegador...")
        input()
        scraper._close_driver()

if __name__ == "__main__":
    testar_scraper_visivel()


