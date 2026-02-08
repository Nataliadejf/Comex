import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, OperacaoComex, TipoOperacao, ViaTransporte
import main as backend_main


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


@pytest.mark.asyncio
async def test_dashboard_stats_sums_import_export():
    db = _make_session()
    backend_main._DASHBOARD_CACHE.clear()

    hoje = date.today()
    db.add_all([
        OperacaoComex(
            ncm="01010101",
            descricao_produto="Produto A",
            tipo_operacao=TipoOperacao.IMPORTACAO,
            pais_origem_destino="China",
            uf="SP",
            via_transporte=ViaTransporte.MARITIMA,
            valor_fob=100.0,
            peso_liquido_kg=10.0,
            quantidade_estatistica=5.0,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
        ),
        OperacaoComex(
            ncm="02020202",
            descricao_produto="Produto B",
            tipo_operacao=TipoOperacao.EXPORTACAO,
            pais_origem_destino="EUA",
            uf="RJ",
            via_transporte=ViaTransporte.AEREA,
            valor_fob=200.0,
            peso_liquido_kg=20.0,
            quantidade_estatistica=8.0,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
        ),
    ])
    db.commit()

    result = await backend_main.get_dashboard_stats(
        meses=24,
        tipo_operacao=None,
        ncm=None,
        ncms=None,
        empresa_importadora=None,
        empresa_exportadora=None,
        db=db,
    )

    assert result["valor_total_importacoes"] == 100.0
    assert result["valor_total_exportacoes"] == 200.0
    assert result["valor_total_usd"] == 300.0
    assert result["volume_importacoes"] == 10.0
    assert result["volume_exportacoes"] == 20.0
    assert result["quantidade_estatistica_importacoes"] == 5.0
    assert result["quantidade_estatistica_exportacoes"] == 8.0
    assert result["quantidade_estatistica_total"] == 13.0


@pytest.mark.asyncio
async def test_dashboard_stats_tipo_operacao_importacao():
    db = _make_session()
    backend_main._DASHBOARD_CACHE.clear()

    hoje = date.today()
    db.add_all([
        OperacaoComex(
            ncm="01010101",
            descricao_produto="Produto A",
            tipo_operacao=TipoOperacao.IMPORTACAO,
            pais_origem_destino="China",
            uf="SP",
            via_transporte=ViaTransporte.MARITIMA,
            valor_fob=100.0,
            peso_liquido_kg=10.0,
            quantidade_estatistica=5.0,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
        ),
        OperacaoComex(
            ncm="02020202",
            descricao_produto="Produto B",
            tipo_operacao=TipoOperacao.EXPORTACAO,
            pais_origem_destino="EUA",
            uf="RJ",
            via_transporte=ViaTransporte.AEREA,
            valor_fob=200.0,
            peso_liquido_kg=20.0,
            quantidade_estatistica=8.0,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
        ),
    ])
    db.commit()

    result = await backend_main.get_dashboard_stats(
        meses=24,
        tipo_operacao="Importação",
        ncm=None,
        ncms=None,
        empresa_importadora=None,
        empresa_exportadora=None,
        db=db,
    )

    assert result["valor_total_importacoes"] == 100.0
    assert result["valor_total_exportacoes"] == 0.0
    assert result["valor_total_usd"] == 100.0
    assert result["quantidade_estatistica_importacoes"] == 5.0
    assert result["quantidade_estatistica_exportacoes"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_stats_filtro_empresa_importadora():
    """Filtro por empresa_importadora deve retornar apenas linhas onde razao_social_importador contém o termo."""
    db = _make_session()
    backend_main._DASHBOARD_CACHE.clear()

    hoje = date.today()
    db.add_all([
        OperacaoComex(
            ncm="01010101",
            descricao_produto="Produto A",
            tipo_operacao=TipoOperacao.IMPORTACAO,
            pais_origem_destino="China",
            uf="SP",
            via_transporte=ViaTransporte.MARITIMA,
            valor_fob=100.0,
            peso_liquido_kg=10.0,
            quantidade_estatistica=None,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
            razao_social_importador="EMPRESA VALE S.A.",
            razao_social_exportador="OUTRO EXPORTADOR",
        ),
        OperacaoComex(
            ncm="02020202",
            descricao_produto="Produto B",
            tipo_operacao=TipoOperacao.IMPORTACAO,
            pais_origem_destino="EUA",
            uf="RJ",
            via_transporte=ViaTransporte.AEREA,
            valor_fob=200.0,
            peso_liquido_kg=20.0,
            quantidade_estatistica=None,
            data_operacao=hoje,
            mes_referencia=f"{hoje.year}-{hoje.month:02d}",
            arquivo_origem="teste",
            razao_social_importador="OUTRA IMPORTADORA LTDA",
            razao_social_exportador="EXPORTADOR Y",
        ),
    ])
    db.commit()

    # Sem filtro: 2 linhas, total 300
    result_todos = await backend_main.get_dashboard_stats(
        meses=24,
        tipo_operacao=None,
        ncm=None,
        ncms=None,
        empresa_importadora=None,
        empresa_exportadora=None,
        db=db,
    )
    assert result_todos["valor_total_usd"] == 300.0
    assert result_todos["quantidade_estatistica_total"] == 2.0  # fallback = contagem

    # Com filtro VALE: só 1 linha (EMPRESA VALE S.A.)
    result_filtrado = await backend_main.get_dashboard_stats(
        meses=24,
        tipo_operacao=None,
        ncm=None,
        ncms=None,
        empresa_importadora="VALE",
        empresa_exportadora=None,
        db=db,
    )
    assert result_filtrado["valor_total_usd"] == 100.0
    assert result_filtrado["quantidade_estatistica_total"] == 1.0
    assert result_filtrado["volume_importacoes"] == 10.0
