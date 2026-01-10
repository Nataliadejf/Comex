"""
Script para verificar registros no banco de dados PostgreSQL.
"""
import os
import sys
from pathlib import Path

# Adicionar backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal
from database.models import Empresa, ComercioExterior
from sqlalchemy import func

def verificar_banco():
    """Verifica dados no banco."""
    db = SessionLocal()
    
    try:
        print("="*80)
        print("VERIFICAÇÃO DO BANCO DE DADOS")
        print("="*80)
        
        # Total de empresas
        total_empresas = db.query(func.count(Empresa.id)).scalar() or 0
        print(f"\n📊 Total de Empresas: {total_empresas:,}")
        
        if total_empresas > 0:
            # Por tipo
            empresas_por_tipo = db.query(
                Empresa.tipo,
                func.count(Empresa.id).label('total')
            ).group_by(Empresa.tipo).all()
            
            print("\n📋 Distribuição por tipo:")
            for tipo, total in empresas_por_tipo:
                print(f"  - {tipo}: {total:,}")
            
            # Por estado (top 10)
            empresas_por_estado = db.query(
                Empresa.estado,
                func.count(Empresa.id).label('total')
            ).filter(
                Empresa.estado.isnot(None)
            ).group_by(Empresa.estado).order_by(
                func.count(Empresa.id).desc()
            ).limit(10).all()
            
            print("\n📍 Top 10 Estados:")
            for estado, total in empresas_por_estado:
                print(f"  - {estado}: {total:,}")
        
        # Total de registros de comércio exterior
        total_comex = db.query(func.count(ComercioExterior.id)).scalar() or 0
        print(f"\n📊 Total de Registros Comércio Exterior: {total_comex:,}")
        
        if total_comex > 0:
            # Por tipo
            comex_por_tipo = db.query(
                ComercioExterior.tipo,
                func.count(ComercioExterior.id).label('total'),
                func.sum(ComercioExterior.valor_usd).label('valor_total')
            ).group_by(ComercioExterior.tipo).all()
            
            print("\n💰 Valores por tipo:")
            for tipo, total, valor in comex_por_tipo:
                print(f"  - {tipo}: {total:,} registros | ${valor:,.2f}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    verificar_banco()
