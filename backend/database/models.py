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
        comment="Tipo de operação: Importação ou Exportação"
    )
    
    # Identificação clara de importador/exportador
    is_importacao = Column(
        String(1),
        nullable=False,
        default='N',
        index=True,
        comment="S=Sim, N=Não - Identifica se é importação"
    )
    
    is_exportacao = Column(
        String(1),
        nullable=False,
        default='N',
        index=True,
        comment="S=Sim, N=Não - Identifica se é exportação"
    )
    
    # Localização
    pais_origem_destino = Column(String(100), nullable=False, index=True)
    uf = Column(String(2), nullable=False, index=True, comment="Unidade Federativa")
    porto_aeroporto = Column(String(100), nullable=True, comment="Porto/Aeroporto")
    
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
    
    # Empresa (Importador/Exportador)
    nome_empresa = Column(String(255), nullable=True, index=True, comment="Nome da empresa importadora/exportadora")
    
    # Metadados
    mes_referencia = Column(String(7), nullable=False, index=True, comment="YYYY-MM")
    arquivo_origem = Column(String(255), nullable=True, comment="Arquivo de origem")
    
    # Índices compostos para consultas frequentes
    __table_args__ = (
        Index('idx_ncm_tipo_data', 'ncm', 'tipo_operacao', 'data_operacao'),
        Index('idx_pais_tipo_data', 'pais_origem_destino', 'tipo_operacao', 'data_operacao'),
        Index('idx_uf_tipo_data', 'uf', 'tipo_operacao', 'data_operacao'),
        Index('idx_mes_tipo', 'mes_referencia', 'tipo_operacao'),
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
    Modelo de usuário para autenticação.
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)  # Email é o login
    senha_hash = Column(String(255), nullable=False)  # Hash da senha (bcrypt)
    nome_completo = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    nome_empresa = Column(String(255), nullable=True)
    cpf = Column(String(14), nullable=True, index=True)  # CPF formatado: 000.000.000-00
    cnpj = Column(String(18), nullable=True, index=True)  # CNPJ formatado: 00.000.000/0000-00
    status_aprovacao = Column(String(20), default="pendente", nullable=False)  # pendente, aprovado, rejeitado
    ativo = Column(Integer, default=0, nullable=False)  # 0=inativo (aguardando aprovação), 1=ativo
    data_criacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_aprovacao = Column(DateTime, nullable=True)
    aprovado_por = Column(String(255), nullable=True)  # Email do admin que aprovou
    ultimo_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email}, status={self.status_aprovacao})>"


class AprovacaoCadastro(Base):
    """
    Log de aprovações de cadastro.
    """
    __tablename__ = "aprovacoes_cadastro"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    token_aprovacao = Column(String(255), unique=True, nullable=False, index=True)
    email_destino = Column(String(255), nullable=False)
    status = Column(String(20), default="pendente", nullable=False)  # pendente, aprovado, rejeitado, expirado
    data_solicitacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_aprovacao = Column(DateTime, nullable=True)
    data_expiracao = Column(DateTime, nullable=False)
    aprovado_por = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<AprovacaoCadastro(id={self.id}, usuario_id={self.usuario_id}, status={self.status})>"

