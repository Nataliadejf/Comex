"""
Script para avaliar qual método foi usado na coleta e verificar resultados.
Analisa logs e estatísticas da coleta.
"""
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def buscar_ultima_coleta(base_url: str = "https://comex-backend-wjco.onrender.com") -> Optional[Dict[str, Any]]:
    """
    Busca informações sobre a última coleta executada.
    Verifica logs do backend ou arquivos locais.
    """
    # Tentar buscar via endpoint de estatísticas
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.ok:
            # Se tiver endpoint de estatísticas de coleta, usar aqui
            pass
    except:
        pass
    
    # Buscar arquivos de log locais
    logs_dir = Path(__file__).parent.parent / "comex_data" / "logs"
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("coleta_*.json"), reverse=True)
        if log_files:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
    
    return None


def avaliar_metodo_usado(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Avalia qual método foi usado e fornece recomendações.
    
    Args:
        stats: Estatísticas da coleta
    
    Returns:
        Dicionário com avaliação detalhada
    """
    avaliacao = {
        "metodo_detectado": stats.get("metodo_usado", "desconhecido"),
        "usou_api": stats.get("usou_api", False),
        "total_registros": stats.get("total_registros", 0),
        "meses_processados": len(stats.get("meses_processados", [])),
        "erros": len(stats.get("erros", [])),
        "status": "desconhecido",
        "recomendacoes": []
    }
    
    metodo = avaliacao["metodo_detectado"].lower()
    registros = avaliacao["total_registros"]
    erros = avaliacao["erros"]
    
    # Determinar status
    if registros > 0 and erros == 0:
        avaliacao["status"] = "sucesso_total"
    elif registros > 0 and erros < 5:
        avaliacao["status"] = "sucesso_parcial"
    elif registros == 0 and erros > 0:
        avaliacao["status"] = "falha"
    else:
        avaliacao["status"] = "indeterminado"
    
    # Análise por método
    if "api" in metodo:
        avaliacao["recomendacoes"].append("✅ API REST funcionando corretamente")
        if registros == 0:
            avaliacao["recomendacoes"].append("⚠️  API retornou mas sem dados - verifique parâmetros")
    elif "csv" in metodo:
        avaliacao["recomendacoes"].append("✅ CSV Scraper funcionando - usando bases de dados brutas")
        avaliacao["recomendacoes"].append("💡 Este método é mais confiável para dados históricos")
        if registros == 0:
            avaliacao["recomendacoes"].append("⚠️  CSV Scraper não encontrou arquivos - verifique URLs")
    elif "scraper" in metodo:
        avaliacao["recomendacoes"].append("✅ Scraper tradicional funcionando")
        avaliacao["recomendacoes"].append("💡 Este método requer Selenium e pode ser mais lento")
    else:
        avaliacao["recomendacoes"].append("⚠️  Método desconhecido - verifique logs")
    
    # Recomendações gerais
    if registros == 0:
        avaliacao["recomendacoes"].append("❌ Nenhum registro coletado - verifique:")
        avaliacao["recomendacoes"].append("   1. Conexão com backend")
        avaliacao["recomendacoes"].append("   2. Disponibilidade da API/CSV")
        avaliacao["recomendacoes"].append("   3. Parâmetros da requisição")
    elif registros < 100:
        avaliacao["recomendacoes"].append("⚠️  Poucos registros coletados - pode ser normal para:")
        avaliacao["recomendacoes"].append("   - Períodos específicos")
        avaliacao["recomendacoes"].append("   - NCMs específicos")
        avaliacao["recomendacoes"].append("   - Filtros muito restritivos")
    else:
        avaliacao["recomendacoes"].append(f"✅ {registros} registros coletados com sucesso!")
    
    if erros > 0:
        avaliacao["recomendacoes"].append(f"⚠️  {erros} erros encontrados - verifique logs detalhados")
    
    return avaliacao


def verificar_banco_dados(base_url: str = "https://comex-backend-wjco.onrender.com") -> Dict[str, Any]:
    """
    Verifica estatísticas do banco de dados.
    """
    try:
        # Tentar buscar estatísticas do dashboard
        response = requests.get(
            f"{base_url}/dashboard/stats?meses=24",
            timeout=30
        )
        
        if response.ok:
            stats = response.json()
            return {
                "total_registros": stats.get("registros_por_mes", {}),
                "valor_total": stats.get("valor_total_usd", 0),
                "volume_importacoes": stats.get("volume_importacoes", 0),
                "volume_exportacoes": stats.get("volume_exportacoes", 0),
                "disponivel": True
            }
    except Exception as e:
        return {
            "disponivel": False,
            "erro": str(e)
        }
    
    return {"disponivel": False}


def imprimir_relatorio(avaliacao: Dict[str, Any], stats: Dict[str, Any], banco_stats: Dict[str, Any]):
    """Imprime relatório formatado."""
    print("=" * 80)
    print("RELATÓRIO DE AVALIAÇÃO - MÉTODO DE COLETA")
    print("=" * 80)
    print()
    
    # Método usado
    print("📡 MÉTODO USADO:")
    print(f"   {avaliacao['metodo_detectado']}")
    print(f"   Usou API: {'Sim' if avaliacao['usou_api'] else 'Não'}")
    print()
    
    # Estatísticas
    print("📊 ESTATÍSTICAS DA COLETA:")
    print(f"   Total de registros: {avaliacao['total_registros']:,}")
    print(f"   Meses processados: {avaliacao['meses_processados']}")
    print(f"   Erros encontrados: {avaliacao['erros']}")
    print()
    
    # Status
    status_emoji = {
        "sucesso_total": "✅",
        "sucesso_parcial": "⚠️",
        "falha": "❌",
        "indeterminado": "❓"
    }
    emoji = status_emoji.get(avaliacao['status'], "❓")
    print(f"{emoji} STATUS: {avaliacao['status'].upper().replace('_', ' ')}")
    print()
    
    # Banco de dados
    if banco_stats.get("disponivel"):
        print("💾 BANCO DE DADOS:")
        print(f"   Valor total: US$ {banco_stats.get('valor_total', 0):,.2f}")
        print(f"   Volume importações: {banco_stats.get('volume_importacoes', 0):,.2f} KG")
        print(f"   Volume exportações: {banco_stats.get('volume_exportacoes', 0):,.2f} KG")
        
        meses_com_dados = len(banco_stats.get('total_registros', {}))
        if meses_com_dados > 0:
            print(f"   Meses com dados: {meses_com_dados}")
    else:
        print("💾 BANCO DE DADOS:")
        print("   ⚠️  Não foi possível verificar o banco de dados")
        if banco_stats.get("erro"):
            print(f"   Erro: {banco_stats['erro']}")
    print()
    
    # Recomendações
    print("💡 RECOMENDAÇÕES:")
    for rec in avaliacao['recomendacoes']:
        print(f"   {rec}")
    print()
    
    # Erros detalhados (se houver)
    erros = stats.get('erros', [])
    if erros:
        print("⚠️  ERROS DETALHADOS:")
        for i, erro in enumerate(erros[:10], 1):
            print(f"   {i}. {erro}")
        if len(erros) > 10:
            print(f"   ... e mais {len(erros) - 10} erros")
        print()
    
    print("=" * 80)


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Avaliar método usado na coleta de dados")
    parser.add_argument(
        "--url",
        default="https://comex-backend-wjco.onrender.com",
        help="URL do backend (padrão: https://comex-backend-wjco.onrender.com)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Usar backend local (http://localhost:8000)"
    )
    parser.add_argument(
        "--arquivo",
        help="Caminho para arquivo JSON com resultado da coleta"
    )
    
    args = parser.parse_args()
    
    base_url = "http://localhost:8000" if args.local else args.url
    
    # Carregar dados da coleta
    if args.arquivo:
        with open(args.arquivo, 'r', encoding='utf-8') as f:
            resultado = json.load(f)
    else:
        resultado = buscar_ultima_coleta(base_url)
    
    if not resultado:
        print("❌ Não foi possível encontrar dados da coleta.")
        print("   Execute primeiro: python scripts/executar_coleta.py")
        return
    
    stats = resultado.get("stats", {})
    
    # Avaliar método
    avaliacao = avaliar_metodo_usado(stats)
    
    # Verificar banco de dados
    banco_stats = verificar_banco_dados(base_url)
    
    # Imprimir relatório
    imprimir_relatorio(avaliacao, stats, banco_stats)
    
    # Salvar relatório
    output_file = Path(__file__).parent.parent / "comex_data" / "logs" / f"avaliacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    relatorio_completo = {
        "timestamp": datetime.now().isoformat(),
        "avaliacao": avaliacao,
        "stats": stats,
        "banco_stats": banco_stats
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relatorio_completo, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Relatório salvo em: {output_file}")


if __name__ == "__main__":
    main()

