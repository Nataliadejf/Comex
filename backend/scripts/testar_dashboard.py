"""Script para testar o endpoint do dashboard."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db, OperacaoComex
from sqlalchemy import func

def testar_dados():
    """Testa se há dados no banco."""
    db = next(get_db())
    
    try:
        # Total de registros
        total = db.query(func.count(OperacaoComex.id)).scalar()
        print(f"✅ Total de registros no banco: {total}")
        
        # Verificar NCM 84295200
        ncm_count = db.query(func.count(OperacaoComex.id)).filter(
            OperacaoComex.ncm == '84295200'
        ).scalar()
        print(f"✅ Registros com NCM 84295200: {ncm_count}")
        
        if ncm_count == 0:
            print("\n⚠️  Não há dados para NCM 84295200!")
            print("   Vamos verificar quais NCMs existem...\n")
            ncms = db.query(
                OperacaoComex.ncm,
                func.count(OperacaoComex.id).label('count')
            ).group_by(
                OperacaoComex.ncm
            ).order_by(
                func.count(OperacaoComex.id).desc()
            ).limit(10).all()
            
            print("Top 10 NCMs no banco:")
            for ncm, count in ncms:
                print(f"  {ncm}: {count} registros")
        
        # Verificar valores
        valor_total = db.query(func.sum(OperacaoComex.valor_fob)).scalar()
        print(f"\n✅ Valor total no banco: ${valor_total:,.2f}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    testar_dados()



