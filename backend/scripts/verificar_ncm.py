"""
Script para verificar se um NCM existe no banco de dados.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, OperacaoComex
from sqlalchemy import func

def verificar_ncm(ncm: str):
    """Verifica se o NCM existe no banco e mostra estatísticas."""
    db = next(get_db())
    
    try:
        # Remover pontos e espaços
        ncm_limpo = ncm.replace('.', '').replace(' ', '').strip()
        
        if len(ncm_limpo) != 8:
            print(f"❌ NCM inválido: {ncm} (deve ter 8 dígitos)")
            return
        
        print(f"\n🔍 Verificando NCM: {ncm_limpo}\n")
        
        # Contar registros
        total = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.ncm == ncm_limpo
        ).scalar() or 0
        
        if total == 0:
            print(f"❌ NCM {ncm_limpo} não encontrado no banco de dados")
            
            # Verificar NCMs similares (primeiros 4 dígitos)
            prefixo = ncm_limpo[:4]
            similares = db.query(
                OperacaoComex.ncm,
                func.count(OperacaoComex.id).label('count')
            ).filter(
                OperacaoComex.ncm.like(f"{prefixo}%")
            ).group_by(
                OperacaoComex.ncm
            ).limit(10).all()
            
            if similares:
                print(f"\n📋 NCMs similares encontrados (começando com {prefixo}):")
                for ncm_sim, count in similares:
                    print(f"   • {ncm_sim}: {count} registros")
        else:
            # Estatísticas do NCM
            stats = db.query(
                func.sum(OperacaoComex.valor_fob).label('valor_total'),
                func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
                func.count(OperacaoComex.id).label('total_operacoes'),
                func.min(OperacaoComex.data_operacao).label('data_inicio'),
                func.max(OperacaoComex.data_operacao).label('data_fim')
            ).filter(
                OperacaoComex.ncm == ncm_limpo
            ).first()
            
            print(f"✅ NCM {ncm_limpo} encontrado!")
            print(f"\n📊 Estatísticas:")
            print(f"   • Total de operações: {stats.total_operacoes or 0}")
            print(f"   • Valor total FOB: ${(stats.valor_total or 0):,.2f} USD")
            print(f"   • Peso total: {(stats.peso_total or 0):,.2f} KG")
            print(f"   • Período: {stats.data_inicio} até {stats.data_fim}")
            
            # Tipos de operação
            tipos = db.query(
                OperacaoComex.tipo_operacao,
                func.count(OperacaoComex.id).label('count')
            ).filter(
                OperacaoComex.ncm == ncm_limpo
            ).group_by(
                OperacaoComex.tipo_operacao
            ).all()
            
            print(f"\n📋 Tipos de operação:")
            for tipo, count in tipos:
                print(f"   • {tipo.value}: {count} operações")
        
        # Listar todos os NCMs disponíveis
        print(f"\n📋 Todos os NCMs disponíveis no banco:")
        todos_ncms = db.query(
            OperacaoComex.ncm,
            func.count(OperacaoComex.id).label('count')
        ).group_by(
            OperacaoComex.ncm
        ).order_by(
            func.count(OperacaoComex.id).desc()
        ).limit(20).all()
        
        for ncm_val, count in todos_ncms:
            print(f"   • {ncm_val}: {count} registros")
        
    except Exception as e:
        print(f"❌ Erro ao verificar NCM: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    ncm = sys.argv[1] if len(sys.argv) > 1 else "87083090"
    verificar_ncm(ncm)


