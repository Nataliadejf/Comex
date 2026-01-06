"""
Script para testar a coleta enriquecida de dados do MDIC.
Útil para diagnosticar problemas.
"""
import asyncio
import sys
from pathlib import Path
import os

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# Agora importar módulos relativos
from database import get_db
from data_collector.enriched_collector import EnrichedDataCollector
from loguru import logger

async def testar_coleta():
    """Testa a coleta enriquecida."""
    print("="*60)
    print("TESTE DE COLETA ENRIQUECIDA")
    print("="*60)
    print()
    
    try:
        # Obter sessão do banco
        db = next(get_db())
        
        # Criar coletor
        print("1. Criando coletor...")
        collector = EnrichedDataCollector()
        print("   ✅ Coletor criado")
        print()
        
        # Testar download de tabelas
        print("2. Testando download de tabelas de correlação...")
        try:
            tabelas = await collector.csv_collector.download_correlation_tables()
            print(f"   ✅ {len(tabelas)} tabelas baixadas")
            for nome, caminho in tabelas.items():
                print(f"      - {nome}: {caminho}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        print()
        
        # Testar download de um mês apenas
        print("3. Testando download de dados mensais (1 mês)...")
        try:
            from datetime import datetime
            hoje = datetime.now()
            arquivos = await collector.csv_collector.download_monthly_data(
                hoje.year, hoje.month, "both"
            )
            print(f"   ✅ {len(arquivos)} arquivos baixados")
            for arquivo in arquivos:
                print(f"      - {arquivo.name}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        print()
        
        # Testar processamento de um arquivo
        if arquivos:
            print("4. Testando processamento de arquivo CSV...")
            try:
                registros = collector.csv_collector.parse_csv_file(arquivos[0])
                print(f"   ✅ {len(registros)} registros processados")
                if registros:
                    print(f"   Exemplo de registro:")
                    for key, value in list(registros[0].items())[:5]:
                        print(f"      {key}: {value}")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                import traceback
                traceback.print_exc()
            print()
        
        # Testar coleta completa (apenas 1 mês para teste)
        print("5. Testando coleta completa (1 mês)...")
        try:
            stats = await collector.collect_and_enrich(db, meses=1)
            print()
            print("="*60)
            print("RESULTADO DA COLETA")
            print("="*60)
            print(f"Total de registros: {stats['total_registros']:,}")
            print(f"Registros novos: {stats['registros_novos']:,}")
            print(f"Registros atualizados: {stats['registros_atualizados']:,}")
            print(f"Empresas enriquecidas: {stats['empresas_enriquecidas']:,}")
            print(f"Meses processados: {len(stats['meses_processados'])}")
            if stats['erros']:
                print(f"\n⚠️ Erros encontrados: {len(stats['erros'])}")
                for erro in stats['erros'][:5]:
                    print(f"   - {erro}")
            print("="*60)
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    resultado = asyncio.run(testar_coleta())
    sys.exit(resultado)

