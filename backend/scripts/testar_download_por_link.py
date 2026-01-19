"""
Script para testar o download usando um link de consulta direto do ComexStat.
"""
import sys
from pathlib import Path
import os
import time

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.comexstat_scraper import ComexStatScraper
from loguru import logger

def testar_download_por_link():
    """Testa o download usando um link direto."""
    print("="*60)
    print("TESTE DE DOWNLOAD POR LINK DIRETO - COMEXSTAT")
    print("="*60)
    print()
    
    scraper = ComexStatScraper()
    
    # Link fornecido pelo usuário
    link_consulta = "https://comexstat.mdic.gov.br/pt/geral/142608"
    
    try:
        print(f"1. Testando download usando link direto:")
        print(f"   {link_consulta}")
        print()
        print("   Modo: VISÍVEL (você verá o navegador)")
        print("   Iniciando em 3 segundos...")
        time.sleep(3)
        
        # Testar com modo VISÍVEL (headless=False)
        # IMPORTANTE: CSV não está funcionando, então usar Excel
        arquivo = scraper.baixar_dados_por_link(
            link_consulta=link_consulta,
            headless=False,  # MODO VISÍVEL (você verá o navegador)
            preferir_csv=False  # Usar Excel pois CSV não está funcionando
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
                        # Contar linhas
                        f.seek(0)
                        linhas = sum(1 for _ in f)
                        print(f"   📊 Total de linhas: {linhas:,}")
            except Exception as e:
                print(f"   ⚠️ Erro ao verificar arquivo: {e}")
        else:
            print("\n❌ Download não foi concluído")
            print("\n💡 Verifique:")
            print("   - Se o link está correto e acessível")
            print("   - Se há algum popup bloqueando o download")
            print("   - Se o arquivo foi baixado em outro local")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("="*60)
        print("\n⚠️ O navegador será fechado em 10 segundos...")
        print("   (Você pode fechar manualmente se quiser)")
        time.sleep(10)
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️ O navegador será fechado em 10 segundos...")
        time.sleep(10)
    
    finally:
        scraper._close_driver()

if __name__ == "__main__":
    testar_download_por_link()

