"""
Modelos do banco de dados.
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    Index, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TipoOperacao(str, enum.Enum):
    """Tipo de operação de comércio exterior."""
    IMPORTACAO = "Importação"
    EXPORTACAO = "Exportação"


class ViaTransporte(str, enum.Enum):
    """Via de transporte."""
    MARITIMA = "Marítima"
    AEREA = "Aérea"
    RODOVIARIA = "Rodoviária"
    FERROVIARIA = "Ferroviária"
    DUTOVIARIA = "Dutoviária"
    POSTAL = "Postal"
    OUTRAS = "Outras"


class OperacaoComex(Base):
    """
    Modelo principal para operações de comércio exterior.
    """
    __tablename__ = "operacoes_comex"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    ncm = Column(String(8), nullable=False, index=True, comment="NCM - 8 dígitos")
    descricao_produto = Column(Text, nullable=False, comment="Descrição do produto")
    
    # Operação
    tipo_operacao = Column(
        SQLEnum(TipoOperacao),
        nullable=False,
        index=True,
        comment="Tipo de operação"
    )
    
    # Localização
    pais_origem_destino = Column(String(100), nullable=False, index=True)
    uf = Column(String(2), nullable=False, index=True, comment="Unidade Federativa")
    porto_aeroporto = Column(String(100), nullable=True, comment="Porto/Aeroporto")
    
    # Empresa (Importador/Exportador)
    razao_social_importador = Column(String(255), nullable=True, index=True, comment="Razão social do importador")
    razao_social_exportador = Column(String(255), nullable=True, index=True, comment="Razão social do exportador")
    cnpj_importador = Column(String(14), nullable=True, index=True, comment="CNPJ do importador")
    cnpj_exportador = Column(String(14), nullable=True, index=True, comment="CNPJ do exportador")
    
    # Transporte
    via_transporte = Column(
        SQLEnum(ViaTransporte),
        nullable=False,
        index=True
    )
    
    # Valores monetários (USD)
    valor_fob = Column(Float, nullable=False, comment="Valor FOB em USD")
    valor_frete = Column(Float, nullable=True, comment="Valor do frete em USD")
    valor_seguro = Column(Float, nullable=True, comment="Valor do seguro em USD")
    
    # Quantidades
    peso_liquido_kg = Column(Float, nullable=True, comment="Peso líquido em kg")
    peso_bruto_kg = Column(Float, nullable=True, comment="Peso bruto em kg")
    quantidade_estatistica = Column(Float, nullable=True)
    unidade_medida_estatistica = Column(String(50), nullable=True)
    
    # Datas
    data_operacao = Column(Date, nullable=False, index=True)
    data_importacao = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Data de importação dos dados"
    )
    
    # Metadados
    mes_referencia = Column(String(7), nullable=False, index=True, comment="YYYY-MM")
    arquivo_origem = Column(String(255), nullable=True, comment="Arquivo de origem")
    
    # Índices compostos para consultas frequentes
    __table_args__ = (
        Index('idx_ncm_tipo_data', 'ncm', 'tipo_operacao', 'data_operacao'),
        Index('idx_pais_tipo_data', 'pais_origem_destino', 'tipo_operacao', 'data_operacao'),
        Index('idx_uf_tipo_data', 'uf', 'tipo_operacao', 'data_operacao'),
        Index('idx_mes_tipo', 'mes_referencia', 'tipo_operacao'),
        Index('idx_importador', 'razao_social_importador', 'tipo_operacao'),
        Index('idx_exportador', 'razao_social_exportador', 'tipo_operacao'),
    )
    
    def __repr__(self):
        return (
            f"<OperacaoComex(id={self.id}, ncm={self.ncm}, "
            f"tipo={self.tipo_operacao.value}, data={self.data_operacao})>"
        )


class NCMInfo(Base):
    """
    Informações adicionais sobre NCMs.
    """
    __tablename__ = "ncm_info"
    
    id = Column(Integer, primary_key=True, index=True)
    ncm = Column(String(8), unique=True, nullable=False, index=True)
    descricao_completa = Column(Text, nullable=True)
    categoria = Column(String(100), nullable=True)
    data_atualizacao = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NCMInfo(ncm={self.ncm}, descricao={self.descricao_completa[:50]}...)>"


class ColetaLog(Base):
    """
    Log de coletas de dados realizadas.
    """
    __tablename__ = "coleta_log"
    
    id = Column(Integer, primary_key=True, index=True)
    mes_referencia = Column(String(7), nullable=False, index=True)
    tipo_operacao = Column(SQLEnum(TipoOperacao), nullable=True)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="em_andamento")
    registros_coletados = Column(Integer, default=0)
    erro = Column(Text, nullable=True)
    arquivo_origem = Column(String(255), nullable=True)
    
    def __repr__(self):
        return (
            f"<ColetaLog(id={self.id}, mes={self.mes_referencia}, "
            f"status={self.status}, registros={self.registros_coletados})>"
        )


class Usuario(Base):
    """
    Modelo de usuário do sistema.
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    nome_empresa = Column(String(255), nullable=True)
    cpf = Column(String(11), nullable=True, unique=True)
    cnpj = Column(String(14), nullable=True, unique=True)
    status_aprovacao = Column(String(20), nullable=False, default="pendente")  # pendente, aprovado, rejeitado
    ativo = Column(Integer, nullable=False, default=0)  # 0 = inativo, 1 = ativo
    token_aprovacao = Column(String(255), nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email}, status={self.status_aprovacao})>"


class AprovacaoCadastro(Base):
    """
    Modelo para controle de aprovação de cadastros.
    """
    __tablename__ = "aprovacoes_cadastro"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    token_aprovacao = Column(String(255), unique=True, nullable=False, index=True)
    email_destino = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pendente")  # pendente, aprovado, rejeitado
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_expiracao = Column(DateTime, nullable=False)
    data_aprovacao = Column(DateTime, nullable=True)
    
    usuario = relationship("Usuario", backref="aprovacoes")
    
    def __repr__(self):
        return f"<AprovacaoCadastro(id={self.id}, usuario_id={self.usuario_id}, status={self.status})>"

