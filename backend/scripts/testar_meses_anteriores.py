"""
Script para testar download de dados de meses anteriores.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.mdic_csv_collector import MDICCSVCollector
from loguru import logger

async def testar_meses():
    """Testa download de meses anteriores."""
    print("="*60)
    print("TESTE DE DOWNLOAD - MESES ANTERIORES")
    print("="*60)
    print()
    
    collector = MDICCSVCollector()
    
    # Testar últimos 6 meses
    hoje = datetime.now()
    meses_testados = []
    meses_com_sucesso = []
    
    print("Testando download dos últimos 6 meses...\n")
    
    for i in range(6):
        data = hoje - timedelta(days=30 * i)
        ano = data.year
        mes = data.month
        
        print(f"{i+1}. Testando {ano}-{mes:02d}...")
        meses_testados.append((ano, mes))
        
        try:
            arquivos = await collector.download_monthly_data(ano, mes, "both")
            
            if arquivos:
                # Verificar se são CSV válidos
                arquivos_validos = []
                for arquivo in arquivos:
                    try:
                        with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                            primeira_linha = f.read(200).strip().lower()
                            if primeira_linha.startswith('<!doctype') or primeira_linha.startswith('<html'):
                                print(f"   ❌ {arquivo.name} - HTML inválido")
                                # Remover arquivo HTML
                                arquivo.unlink()
                            else:
                                print(f"   ✅ {arquivo.name} - CSV válido!")
                                arquivos_validos.append(arquivo)
                    except Exception as e:
                        print(f"   ⚠️ Erro ao verificar {arquivo.name}: {e}")
                
                if arquivos_validos:
                    meses_com_sucesso.append((ano, mes, arquivos_validos))
                    print(f"   ✅ Sucesso: {len(arquivos_validos)} arquivo(s) válido(s)")
                else:
                    print(f"   ❌ Nenhum arquivo válido")
            else:
                print(f"   ❌ Nenhum arquivo baixado")
        
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print()
        await asyncio.sleep(1)  # Delay entre tentativas
    
    print("="*60)
    print("RESULTADO")
    print("="*60)
    print(f"Meses testados: {len(meses_testados)}")
    print(f"Meses com sucesso: {len(meses_com_sucesso)}")
    
    if meses_com_sucesso:
        print("\n✅ Meses com dados válidos encontrados:")
        for ano, mes, arquivos in meses_com_sucesso:
            print(f"   - {ano}-{mes:02d}: {len(arquivos)} arquivo(s)")
            for arquivo in arquivos:
                print(f"     • {arquivo.name}")
        
        print("\n💡 Você pode usar esses meses para testar a coleta!")
    else:
        print("\n⚠️ Nenhum mês com dados válidos foi encontrado.")
        print("   Isso pode indicar que:")
        print("   - As URLs do MDIC mudaram")
        print("   - É necessário autenticação ou headers diferentes")
        print("   - Os dados estão em outro formato/local")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(testar_meses())


