"""
Script para analisar e consolidar dados de empresas, relacionando tabelas
e criando uma tabela única com prováveis importadores e exportadores.

USO:
    Localmente:
        python backend/scripts/analisar_empresas_recomendadas.py
    
    No Render Shell:
        cd /opt/render/project/src/backend
        python scripts/analisar_empresas_recomendadas.py
"""
import sys
from pathlib import Path
import os
from datetime import datetime
from loguru import logger
from sqlalchemy import func, distinct, and_, or_
from collections import defaultdict

# Mudar para o diretório backend
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database.database import SessionLocal, init_db, engine
from database.models import (
    ComercioExterior, Empresa, OperacaoComex, EmpresasRecomendadas,
    Base, TipoOperacao
)

def calcular_peso_participacao(valor_imp, valor_exp, qtd_ncms):
    """
    Calcula o peso de participação (0-100) baseado em:
    - 50% = volume financeiro importado
    - 40% = volume financeiro exportado
    - 10% = quantidade de NCMs movimentados
    """
    # Normalizar valores (assumindo máximo de 1 bilhão USD)
    max_valor = 1_000_000_000
    
    peso_imp = min((valor_imp / max_valor) * 50, 50) if valor_imp > 0 else 0
    peso_exp = min((valor_exp / max_valor) * 40, 40) if valor_exp > 0 else 0
    peso_ncm = min((qtd_ncms / 100) * 10, 10) if qtd_ncms > 0 else 0
    
    peso_total = peso_imp + peso_exp + peso_ncm
    
    # Normalizar para 0-100
    return min(peso_total, 100.0)


def analisar_empresas_operacoes_comex(db):
    """Analisa empresas da tabela OperacaoComex."""
    logger.info("Analisando empresas da tabela OperacaoComex...")
    
    empresas_dict = defaultdict(lambda: {
        'nome': None,
        'cnpj': None,
        'estado': None,
        'valor_imp': 0.0,
        'valor_exp': 0.0,
        'peso_imp': 0.0,
        'peso_exp': 0.0,
        'ncms_imp': set(),
        'ncms_exp': set(),
        'qtd_ops_imp': 0,
        'qtd_ops_exp': 0,
        'cnae': None,
    })
    
    # Buscar empresas importadoras
    logger.info("  Buscando empresas importadoras...")
    importadoras = db.query(
        OperacaoComex.razao_social_importador,
        OperacaoComex.cnpj_importador,
        OperacaoComex.uf,
        OperacaoComex.ncm,
        func.sum(OperacaoComex.valor_fob).label('valor_total'),
        func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
        func.count(OperacaoComex.id).label('qtd_ops')
    ).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
        OperacaoComex.razao_social_importador.isnot(None)
    ).group_by(
        OperacaoComex.cnpj_importador,
        OperacaoComex.razao_social_importador,
        OperacaoComex.uf,
        OperacaoComex.ncm
    ).all()
    
    for nome, cnpj, uf, ncm, valor, peso, qtd in importadoras:
        key = cnpj or nome
        empresas_dict[key]['nome'] = nome
        empresas_dict[key]['cnpj'] = cnpj
        empresas_dict[key]['estado'] = uf
        empresas_dict[key]['valor_imp'] += float(valor or 0)
        empresas_dict[key]['peso_imp'] += float(peso or 0)
        empresas_dict[key]['ncms_imp'].add(str(ncm))
        empresas_dict[key]['qtd_ops_imp'] += int(qtd or 0)
    
    # Buscar empresas exportadoras
    logger.info("  Buscando empresas exportadoras...")
    exportadoras = db.query(
        OperacaoComex.razao_social_exportador,
        OperacaoComex.cnpj_exportador,
        OperacaoComex.uf,
        OperacaoComex.ncm,
        func.sum(OperacaoComex.valor_fob).label('valor_total'),
        func.sum(OperacaoComex.peso_liquido_kg).label('peso_total'),
        func.count(OperacaoComex.id).label('qtd_ops')
    ).filter(
        OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
        OperacaoComex.razao_social_exportador.isnot(None)
    ).group_by(
        OperacaoComex.cnpj_exportador,
        OperacaoComex.razao_social_exportador,
        OperacaoComex.uf,
        OperacaoComex.ncm
    ).all()
    
    for nome, cnpj, uf, ncm, valor, peso, qtd in exportadoras:
        key = cnpj or nome
        empresas_dict[key]['nome'] = nome
        empresas_dict[key]['cnpj'] = cnpj
        empresas_dict[key]['estado'] = uf
        empresas_dict[key]['valor_exp'] += float(valor or 0)
        empresas_dict[key]['peso_exp'] += float(peso or 0)
        empresas_dict[key]['ncms_exp'].add(str(ncm))
        empresas_dict[key]['qtd_ops_exp'] += int(qtd or 0)
    
    logger.info(f"  ✅ Encontradas {len(empresas_dict)} empresas em OperacaoComex")
    return empresas_dict


def analisar_empresas_comercio_exterior(db):
    """Analisa empresas relacionadas através de ComercioExterior e Empresa."""
    logger.info("Analisando empresas das tabelas ComercioExterior e Empresa...")
    
    empresas_dict = defaultdict(lambda: {
        'nome': None,
        'cnpj': None,
        'estado': None,
        'valor_imp': 0.0,
        'valor_exp': 0.0,
        'peso_imp': 0.0,
        'peso_exp': 0.0,
        'ncms_imp': set(),
        'ncms_exp': set(),
        'qtd_ops_imp': 0,
        'qtd_ops_exp': 0,
        'cnae': None,
    })
    
    # Buscar empresas da tabela Empresa
    empresas = db.query(Empresa).all()
    logger.info(f"  Encontradas {len(empresas)} empresas na tabela Empresa")
    
    for emp in empresas:
        key = emp.cnpj or emp.nome
        empresas_dict[key]['nome'] = emp.nome
        empresas_dict[key]['cnpj'] = emp.cnpj
        empresas_dict[key]['estado'] = emp.estado
        empresas_dict[key]['cnae'] = emp.cnae
        empresas_dict[key]['valor_imp'] = float(emp.valor_importacao or 0)
        empresas_dict[key]['valor_exp'] = float(emp.valor_exportacao or 0)
    
    # Buscar dados de ComercioExterior por estado/NCM (agregação)
    logger.info("  Agregando dados de ComercioExterior por estado...")
    
    # Importações por estado
    imp_por_estado = db.query(
        ComercioExterior.estado,
        ComercioExterior.ncm,
        func.sum(ComercioExterior.valor_usd).label('valor_total'),
        func.sum(ComercioExterior.peso_kg).label('peso_total'),
        func.count(ComercioExterior.id).label('qtd')
    ).filter(
        ComercioExterior.tipo == 'importacao',
        ComercioExterior.estado.isnot(None)
    ).group_by(
        ComercioExterior.estado,
        ComercioExterior.ncm
    ).all()
    
    for estado, ncm, valor, peso, qtd in imp_por_estado:
        # Associar a empresas do mesmo estado
        for key, dados in empresas_dict.items():
            if dados['estado'] == estado:
                dados['valor_imp'] += float(valor or 0)
                dados['peso_imp'] += float(peso or 0)
                dados['ncms_imp'].add(str(ncm))
                dados['qtd_ops_imp'] += int(qtd or 0)
    
    # Exportações por estado
    exp_por_estado = db.query(
        ComercioExterior.estado,
        ComercioExterior.ncm,
        func.sum(ComercioExterior.valor_usd).label('valor_total'),
        func.sum(ComercioExterior.peso_kg).label('peso_total'),
        func.count(ComercioExterior.id).label('qtd')
    ).filter(
        ComercioExterior.tipo == 'exportacao',
        ComercioExterior.estado.isnot(None)
    ).group_by(
        ComercioExterior.estado,
        ComercioExterior.ncm
    ).all()
    
    for estado, ncm, valor, peso, qtd in exp_por_estado:
        # Associar a empresas do mesmo estado
        for key, dados in empresas_dict.items():
            if dados['estado'] == estado:
                dados['valor_exp'] += float(valor or 0)
                dados['peso_exp'] += float(peso or 0)
                dados['ncms_exp'].add(str(ncm))
                dados['qtd_ops_exp'] += int(qtd or 0)
    
    logger.info(f"  ✅ Processadas {len(empresas_dict)} empresas")
    return empresas_dict


def consolidar_empresas(db):
    """Consolida dados de todas as fontes e cria tabela EmpresasRecomendadas."""
    logger.info("="*80)
    logger.info("ANÁLISE E CONSOLIDAÇÃO DE EMPRESAS RECOMENDADAS")
    logger.info("="*80)
    
    # Criar tabela se não existir
    Base.metadata.create_all(bind=engine, tables=[EmpresasRecomendadas.__table__])
    
    # Limpar tabela existente
    logger.info("Limpando tabela empresas_recomendadas...")
    db.query(EmpresasRecomendadas).delete()
    db.commit()
    
    # Analisar empresas de diferentes fontes
    empresas_op = analisar_empresas_operacoes_comex(db)
    empresas_ce = analisar_empresas_comercio_exterior(db)
    
    # Consolidar dados
    logger.info("Consolidando dados de todas as fontes...")
    empresas_consolidadas = defaultdict(lambda: {
        'nome': None,
        'cnpj': None,
        'estado': None,
        'cnae': None,
        'valor_imp': 0.0,
        'valor_exp': 0.0,
        'peso_imp': 0.0,
        'peso_exp': 0.0,
        'ncms_imp': set(),
        'ncms_exp': set(),
        'qtd_ops_imp': 0,
        'qtd_ops_exp': 0,
    })
    
    # Mesclar dados de OperacaoComex
    for key, dados in empresas_op.items():
        empresas_consolidadas[key]['nome'] = dados['nome'] or empresas_consolidadas[key]['nome']
        empresas_consolidadas[key]['cnpj'] = dados['cnpj'] or empresas_consolidadas[key]['cnpj']
        empresas_consolidadas[key]['estado'] = dados['estado'] or empresas_consolidadas[key]['estado']
        empresas_consolidadas[key]['valor_imp'] += dados['valor_imp']
        empresas_consolidadas[key]['valor_exp'] += dados['valor_exp']
        empresas_consolidadas[key]['peso_imp'] += dados['peso_imp']
        empresas_consolidadas[key]['peso_exp'] += dados['peso_exp']
        empresas_consolidadas[key]['ncms_imp'].update(dados['ncms_imp'])
        empresas_consolidadas[key]['ncms_exp'].update(dados['ncms_exp'])
        empresas_consolidadas[key]['qtd_ops_imp'] += dados['qtd_ops_imp']
        empresas_consolidadas[key]['qtd_ops_exp'] += dados['qtd_ops_exp']
    
    # Mesclar dados de ComercioExterior/Empresa
    for key, dados in empresas_ce.items():
        empresas_consolidadas[key]['nome'] = dados['nome'] or empresas_consolidadas[key]['nome']
        empresas_consolidadas[key]['cnpj'] = dados['cnpj'] or empresas_consolidadas[key]['cnpj']
        empresas_consolidadas[key]['estado'] = dados['estado'] or empresas_consolidadas[key]['estado']
        empresas_consolidadas[key]['cnae'] = dados['cnae'] or empresas_consolidadas[key]['cnae']
        empresas_consolidadas[key]['valor_imp'] += dados['valor_imp']
        empresas_consolidadas[key]['valor_exp'] += dados['valor_exp']
        empresas_consolidadas[key]['peso_imp'] += dados['peso_imp']
        empresas_consolidadas[key]['peso_exp'] += dados['peso_exp']
        empresas_consolidadas[key]['ncms_imp'].update(dados['ncms_imp'])
        empresas_consolidadas[key]['ncms_exp'].update(dados['ncms_exp'])
        empresas_consolidadas[key]['qtd_ops_imp'] += dados['qtd_ops_imp']
        empresas_consolidadas[key]['qtd_ops_exp'] += dados['qtd_ops_exp']
    
    logger.info(f"✅ Total de empresas consolidadas: {len(empresas_consolidadas)}")
    
    # Inserir na tabela
    logger.info("Inserindo empresas na tabela empresas_recomendadas...")
    registros_inseridos = 0
    
    for key, dados in empresas_consolidadas.items():
        if not dados['nome']:
            continue
        
        # Determinar tipo principal
        if dados['valor_imp'] > 0 and dados['valor_exp'] > 0:
            tipo_principal = 'ambos'
            provavel_imp = 1
            provavel_exp = 1
        elif dados['valor_imp'] > dados['valor_exp']:
            tipo_principal = 'importadora'
            provavel_imp = 1
            provavel_exp = 0
        else:
            tipo_principal = 'exportadora'
            provavel_imp = 0
            provavel_exp = 1
        
        # Calcular peso de participação
        qtd_ncms_total = len(dados['ncms_imp']) + len(dados['ncms_exp'])
        peso_participacao = calcular_peso_participacao(
            dados['valor_imp'],
            dados['valor_exp'],
            qtd_ncms_total
        )
        
        # Criar registro
        empresa_rec = EmpresasRecomendadas(
            cnpj=dados['cnpj'],
            nome=dados['nome'],
            cnae=dados['cnae'],
            estado=dados['estado'],
            tipo_principal=tipo_principal,
            provavel_importador=provavel_imp,
            provavel_exportador=provavel_exp,
            valor_total_importacao_usd=dados['valor_imp'],
            valor_total_exportacao_usd=dados['valor_exp'],
            volume_total_importacao_kg=dados['peso_imp'],
            volume_total_exportacao_kg=dados['peso_exp'],
            ncms_importacao=','.join(sorted(dados['ncms_imp'])) if dados['ncms_imp'] else None,
            ncms_exportacao=','.join(sorted(dados['ncms_exp'])) if dados['ncms_exp'] else None,
            total_operacoes_importacao=dados['qtd_ops_imp'],
            total_operacoes_exportacao=dados['qtd_ops_exp'],
            peso_participacao=peso_participacao
        )
        
        db.add(empresa_rec)
        registros_inseridos += 1
        
        # Commit a cada 100 registros
        if registros_inseridos % 100 == 0:
            db.commit()
            logger.info(f"  Processados {registros_inseridos} registros...")
    
    db.commit()
    logger.success(f"✅ {registros_inseridos} empresas inseridas na tabela empresas_recomendadas")
    
    # Estatísticas finais
    total_imp = db.query(func.count(EmpresasRecomendadas.id)).filter(
        EmpresasRecomendadas.provavel_importador == 1
    ).scalar()
    
    total_exp = db.query(func.count(EmpresasRecomendadas.id)).filter(
        EmpresasRecomendadas.provavel_exportador == 1
    ).scalar()
    
    total_ambos = db.query(func.count(EmpresasRecomendadas.id)).filter(
        EmpresasRecomendadas.tipo_principal == 'ambos'
    ).scalar()
    
    logger.info("\n" + "="*80)
    logger.info("RESUMO DA ANÁLISE:")
    logger.info(f"  - Total de empresas: {registros_inseridos}")
    logger.info(f"  - Prováveis importadoras: {total_imp}")
    logger.info(f"  - Prováveis exportadoras: {total_exp}")
    logger.info(f"  - Ambos (importadora e exportadora): {total_ambos}")
    logger.info("="*80)


def main():
    """Função principal."""
    db = SessionLocal()
    
    try:
        consolidar_empresas(db)
    except Exception as e:
        logger.error(f"❌ Erro durante análise: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
