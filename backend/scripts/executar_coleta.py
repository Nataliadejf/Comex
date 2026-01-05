"""
Script para executar a coleta de dados via endpoint.
Testa o sistema de fallback automático (API → CSV Scraper → Scraper tradicional).
"""
import sys
import requests
import json
from pathlib import Path
from datetime import datetime

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def executar_coleta(
    base_url: str = "https://comex-backend-wjco.onrender.com",
    meses: int = 24,
    ncms: list = None,
    tipo_operacao: str = None
):
    """
    Executa a coleta de dados via endpoint.
    
    Args:
        base_url: URL do backend
        meses: Número de meses para coletar (padrão: 24)
        ncms: Lista de NCMs específicos (None = todos os NCMs)
        tipo_operacao: 'Importação' ou 'Exportação' (None = ambos)
    
    Returns:
        Dicionário com resultado da coleta
    """
    url = f"{base_url}/coletar-dados-ncms"
    
    payload = {
        "meses": meses,
        "ncms": ncms or None,
        "tipo_operacao": tipo_operacao
    }
    
    print("=" * 80)
    print("EXECUTANDO COLETA DE DADOS")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Meses: {meses}")
    print(f"NCMs: {ncms if ncms else 'Todos (geral)'}")
    print(f"Tipo Operação: {tipo_operacao or 'Ambos'}")
    print("-" * 80)
    print("Enviando requisição...")
    print()
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutos
        )
        
        response.raise_for_status()
        result = response.json()
        
        print("✅ COLETA INICIADA COM SUCESSO!")
        print("-" * 80)
        print(f"Mensagem: {result.get('message', 'N/A')}")
        print()
        
        stats = result.get("stats", {})
        print("📊 ESTATÍSTICAS:")
        print(f"  Total de registros: {stats.get('total_registros', 0)}")
        print(f"  Método usado: {stats.get('metodo_usado', 'desconhecido')}")
        print(f"  Usou API: {stats.get('usou_api', False)}")
        print(f"  Meses processados: {len(stats.get('meses_processados', []))}")
        
        if stats.get('meses_processados'):
            print(f"  Primeiros meses: {', '.join(stats['meses_processados'][:5])}")
            if len(stats['meses_processados']) > 5:
                print(f"  ... e mais {len(stats['meses_processados']) - 5} meses")
        
        if stats.get('ncms_processados'):
            print(f"  NCMs processados: {len(stats['ncms_processados'])}")
            print(f"  Primeiros NCMs: {', '.join(stats['ncms_processados'][:5])}")
        
        erros = stats.get('erros', [])
        if erros:
            print()
            print("⚠️  ERROS ENCONTRADOS:")
            for i, erro in enumerate(erros[:10], 1):  # Mostrar até 10 erros
                print(f"  {i}. {erro}")
            if len(erros) > 10:
                print(f"  ... e mais {len(erros) - 10} erros")
        else:
            print()
            print("✅ Nenhum erro encontrado!")
        
        print()
        print("=" * 80)
        print("COLETA CONCLUÍDA")
        print("=" * 80)
        
        return result
        
    except requests.exceptions.Timeout:
        print("❌ ERRO: Timeout - A coleta está demorando muito.")
        print("   Isso é normal para coletas grandes. Verifique os logs do Render.")
        print()
        print("💡 Tente:")
        print("   1. Aguardar alguns minutos e verificar logs do Render")
        print("   2. Coletar menos meses: --meses 6")
        print("   3. Usar backend local: --local")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO na requisição: {e}")
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            print(f"   Status: {status_code}")
            
            if status_code == 502:
                print()
                print("⚠️  ERRO 502: Bad Gateway")
                print("   O backend pode estar:")
                print("   - Iniciando (aguarde alguns minutos)")
                print("   - Offline (verifique o Render)")
                print("   - Sobrecarregado")
                print()
                print("💡 SOLUÇÕES:")
                print("   1. Execute diagnóstico: python backend/scripts/diagnosticar_backend.py")
                print("   2. Verifique logs do Render")
                print("   3. Aguarde 2-3 minutos e tente novamente")
                print("   4. Use backend local: --local")
            elif status_code == 503:
                print()
                print("⚠️  ERRO 503: Service Unavailable")
                print("   Backend pode estar sobrecarregado.")
                print("   Aguarde alguns minutos e tente novamente.")
            else:
                try:
                    error_detail = e.response.json()
                    print(f"   Detalhes: {error_detail}")
                except:
                    resposta_texto = e.response.text[:500]
                    if resposta_texto:
                        print(f"   Resposta: {resposta_texto}")
        else:
            print()
            print("💡 Verifique:")
            print("   1. Conexão com internet")
            print("   2. URL do backend está correta")
            print("   3. Backend está rodando")
            print("   4. Execute diagnóstico: python backend/scripts/diagnosticar_backend.py")
        return None
    except Exception as e:
        print(f"❌ ERRO inesperado: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Executar coleta de dados do Comex Stat")
    parser.add_argument(
        "--url",
        default="https://comex-backend-wjco.onrender.com",
        help="URL do backend (padrão: https://comex-backend-wjco.onrender.com)"
    )
    parser.add_argument(
        "--meses",
        type=int,
        default=24,
        help="Número de meses para coletar (padrão: 24)"
    )
    parser.add_argument(
        "--ncms",
        nargs="+",
        help="NCMs específicos para coletar (ex: --ncms 86079900 73182200)"
    )
    parser.add_argument(
        "--tipo",
        choices=["Importação", "Exportação"],
        help="Tipo de operação (Importação ou Exportação)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Usar backend local (http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    base_url = "http://localhost:8000" if args.local else args.url
    
    resultado = executar_coleta(
        base_url=base_url,
        meses=args.meses,
        ncms=args.ncms,
        tipo_operacao=args.tipo
    )
    
    if resultado:
        # Salvar resultado em arquivo JSON
        output_file = Path(__file__).parent.parent / "comex_data" / "logs" / f"coleta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultado salvo em: {output_file}")
        print()
        print("💡 Dica: Execute 'python scripts/avaliar_metodo.py' para ver detalhes do método usado")


if __name__ == "__main__":
    main()

