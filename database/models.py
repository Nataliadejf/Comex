# ================================================================
# MODELS.PY - MODELOS SQLALCHEMY PARA COMEX
# ================================================================

from enum import Enum
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, Enum as SQLEnum
from database.database import Base


class TipoOperacao(str, Enum):
    """Enum para tipos de operação comercial"""
    EXPORTACAO = "exportacao"
    IMPORTACAO = "importacao"


class OperacaoComex(Base):
    """Modelo para operações de comércio exterior (import/export)"""
    __tablename__ = "operacao_comex"

    id = Column(Integer, primary_key=True, index=True)
    ncm = Column(String(8), index=True, nullable=False)
    descricao_produto = Column(String(500))
    tipo_operacao = Column(SQLEnum(TipoOperacao), nullable=False)
    uf = Column(String(2))
    pais_origem_destino = Column(String(100))
    valor_fob = Column(Float)
    peso_liquido_kg = Column(Float)
    data_operacao = Column(Date, index=True)
    mes_referencia = Column(String(7), index=True)  # formato YYYY-MM
    arquivo_origem = Column(String(255))


class CNAEHierarquia(Base):
    """Modelo para classificação CNAE (hierarquia)"""
    __tablename__ = "cnae_hierarquia"

    id = Column(Integer, primary_key=True, index=True)
    cnae = Column(String(10), unique=True, index=True, nullable=False)
    descricao = Column(String(500))
    classe = Column(String(100))
    grupo = Column(String(100))
    divisao = Column(String(100))
    secao = Column(String(100))
