"""
Script para limpar arquivos HTML inválidos e tentar baixar CSVs válidos.
"""
import asyncio
import sys
from pathlib import Path
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from data_collector.mdic_csv_collector import MDICCSVCollector
from loguru import logger

async def limpar_e_baixar():
    """Remove arquivos HTML e tenta baixar CSVs válidos."""
    print("="*60)
    print("LIMPEZA E DOWNLOAD DE ARQUIVOS CSV")
    print("="*60)
    print()
    
    collector = MDICCSVCollector()
    
    # 1. Listar e remover arquivos HTML
    print("1. Procurando arquivos HTML inválidos...")
    arquivos_html = []
    
    # Verificar em mdic_csv
    for arquivo in collector.data_dir.glob("*.csv"):
        try:
            with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                primeira_linha = f.read(200).strip().lower()
                if primeira_linha.startswith('<!doctype') or primeira_linha.startswith('<html'):
                    arquivos_html.append(arquivo)
                    print(f"   ❌ HTML encontrado: {arquivo.name}")
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar {arquivo.name}: {e}")
    
    # Verificar em data/raw (se existir)
    data_raw = Path(__file__).parent.parent.parent / "data" / "raw"
    if data_raw.exists():
        for arquivo in data_raw.glob("*.csv"):
            try:
                with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira_linha = f.read(200).strip().lower()
                    if primeira_linha.startswith('<!doctype') or primeira_linha.startswith('<html'):
                        arquivos_html.append(arquivo)
                        print(f"   ❌ HTML encontrado: {arquivo.name}")
            except Exception as e:
                print(f"   ⚠️ Erro ao verificar {arquivo.name}: {e}")
    
    print(f"\n   Total de arquivos HTML encontrados: {len(arquivos_html)}")
    
    # 2. Remover arquivos HTML
    if arquivos_html:
        print("\n2. Removendo arquivos HTML...")
        for arquivo in arquivos_html:
            try:
                arquivo.unlink()
                print(f"   ✅ Removido: {arquivo.name}")
            except Exception as e:
                print(f"   ❌ Erro ao remover {arquivo.name}: {e}")
    else:
        print("\n2. Nenhum arquivo HTML encontrado para remover.")
    
    # 3. Tentar baixar arquivos válidos
    print("\n3. Tentando baixar arquivos CSV válidos...")
    print("   (Isso pode levar alguns minutos)")
    
    try:
        # Baixar apenas o mês atual para teste
        from datetime import datetime
        hoje = datetime.now()
        
        print(f"\n   Baixando dados de {hoje.year}-{hoje.month:02d}...")
        arquivos = await collector.download_monthly_data(
            hoje.year, hoje.month, "both"
        )
        
        if arquivos:
            print(f"\n   ✅ {len(arquivos)} arquivos baixados:")
            for arquivo in arquivos:
                # Verificar se é válido
                try:
                    with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                        primeira_linha = f.read(200).strip().lower()
                        if primeira_linha.startswith('<!doctype') or primeira_linha.startswith('<html'):
                            print(f"      ❌ {arquivo.name} - AINDA É HTML!")
                        else:
                            print(f"      ✅ {arquivo.name} - CSV válido")
                except Exception as e:
                    print(f"      ⚠️ {arquivo.name} - Erro ao verificar: {e}")
        else:
            print("\n   ⚠️ Nenhum arquivo foi baixado.")
            print("   Isso pode indicar que:")
            print("   - As URLs do MDIC mudaram")
            print("   - Os dados ainda não estão disponíveis para este mês")
            print("   - Há problemas de conexão")
    
    except Exception as e:
        print(f"\n   ❌ Erro ao baixar: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("PROCESSO CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(limpar_e_baixar())


