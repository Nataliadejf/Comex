"""
Modelos do banco de dados.
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, Numeric,
    Index, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint,
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


class ComercioExterior(Base):
    """
    Modelo para dados de comércio exterior (importação/exportação).
    """
    __tablename__ = "comercio_exterior"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False, index=True, comment="importacao ou exportacao")
    ncm = Column(String(8), nullable=False, index=True)
    descricao_ncm = Column(Text, nullable=True)
    estado = Column(String(2), nullable=True, index=True)
    pais = Column(String(100), nullable=True, index=True)
    valor_usd = Column(Float, nullable=False)
    peso_kg = Column(Float, nullable=True)
    quantidade = Column(Float, nullable=True)
    data = Column(Date, nullable=False, index=True)
    mes = Column(Integer, nullable=False, index=True, comment="1-12")
    ano = Column(Integer, nullable=False, index=True)
    mes_referencia = Column(String(7), nullable=False, index=True, comment="YYYY-MM")
    
    # Metadados
    data_importacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    arquivo_origem = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_comercio_tipo_data', 'tipo', 'data'),
        Index('idx_comercio_ncm_tipo', 'ncm', 'tipo'),
        Index('idx_comercio_estado_tipo', 'estado', 'tipo'),
        Index('idx_comercio_mes_ano', 'mes', 'ano'),
    )
    
    def __repr__(self):
        return f"<ComercioExterior(id={self.id}, tipo={self.tipo}, ncm={self.ncm}, data={self.data})>"


class Empresa(Base):
    """
    Modelo para empresas importadoras e exportadoras.
    """
    __tablename__ = "empresas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False, index=True)
    cnpj = Column(String(14), nullable=True, unique=True, index=True)
    cnae = Column(String(10), nullable=True, index=True)
    estado = Column(String(2), nullable=True, index=True)
    tipo = Column(String(20), nullable=False, index=True, comment="importadora, exportadora, ambos")
    valor_importacao = Column(Float, default=0.0, nullable=False)
    valor_exportacao = Column(Float, default=0.0, nullable=False)
    
    # Metadados
    data_importacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    arquivo_origem = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_empresa_tipo', 'tipo'),
        Index('idx_empresa_cnae', 'cnae'),
        Index('idx_empresa_estado', 'estado'),
    )
    
    def __repr__(self):
        return f"<Empresa(id={self.id}, nome={self.nome}, tipo={self.tipo})>"


class CNAEHierarquia(Base):
    """
    Modelo para hierarquia CNAE (Setor → Segmento → Ramo → Categoria).
    """
    __tablename__ = "cnae_hierarquia"
    
    id = Column(Integer, primary_key=True, index=True)
    cnae = Column(String(10), unique=True, nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    setor = Column(String(100), nullable=True, index=True)
    segmento = Column(String(100), nullable=True, index=True)
    ramo = Column(String(100), nullable=True, index=True)
    categoria = Column(String(100), nullable=True, index=True)
    
    # Metadados
    data_importacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_cnae_setor', 'setor'),
        Index('idx_cnae_segmento', 'segmento'),
        Index('idx_cnae_ramo', 'ramo'),
    )
    
    def __repr__(self):
        return f"<CNAEHierarquia(id={self.id}, cnae={self.cnae}, setor={self.setor})>"


class EmpresasRecomendadas(Base):
    """
    Tabela consolidada com análise de empresas prováveis importadoras e exportadoras.
    Relaciona dados de ComercioExterior, Empresa e OperacaoComex.
    """
    __tablename__ = "empresas_recomendadas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação da empresa
    cnpj = Column(String(14), nullable=True, index=True)
    nome = Column(String(255), nullable=False, index=True)
    cnae = Column(String(10), nullable=True, index=True)
    estado = Column(String(2), nullable=True, index=True)
    
    # Classificação
    tipo_principal = Column(String(20), nullable=False, index=True, comment="importadora, exportadora, ambos")
    provavel_importador = Column(Integer, default=0, nullable=False, comment="1=sim, 0=não")
    provavel_exportador = Column(Integer, default=0, nullable=False, comment="1=sim, 0=não")
    
    # Dados financeiros consolidados
    valor_total_importacao_usd = Column(Float, default=0.0, nullable=False)
    valor_total_exportacao_usd = Column(Float, default=0.0, nullable=False)
    volume_total_importacao_kg = Column(Float, default=0.0, nullable=False)
    volume_total_exportacao_kg = Column(Float, default=0.0, nullable=False)
    
    # NCMs relacionados (separados por vírgula)
    ncms_importacao = Column(Text, nullable=True, comment="NCMs importados separados por vírgula")
    ncms_exportacao = Column(Text, nullable=True, comment="NCMs exportados separados por vírgula")
    
    # Contadores
    total_operacoes_importacao = Column(Integer, default=0, nullable=False)
    total_operacoes_exportacao = Column(Integer, default=0, nullable=False)
    
    # Score de participação (0-100)
    peso_participacao = Column(Float, default=0.0, nullable=False, index=True)
    
    # Metadados
    data_analise = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_emp_rec_tipo', 'tipo_principal'),
        Index('idx_emp_rec_prov_imp', 'provavel_importador'),
        Index('idx_emp_rec_prov_exp', 'provavel_exportador'),
        Index('idx_emp_rec_peso', 'peso_participacao'),
        Index('idx_emp_rec_cnpj', 'cnpj'),
    )
    
    def __repr__(self):
        return f"<EmpresasRecomendadas(id={self.id}, nome={self.nome}, tipo={self.tipo_principal}, peso={self.peso_participacao})>"


class EmpresaNCMEstado(Base):
    """
    Consolidação estado × NCM × empresa (ex.: após sync BigQuery → PostgreSQL).
    """

    __tablename__ = "empresa_ncm_estado"

    id = Column(Integer, primary_key=True, index=True)
    nome_empresa = Column(String(255), nullable=False, index=True)
    cnpj = Column(String(14), nullable=True, index=True)
    tipo = Column(String(20), nullable=False, comment="importadora ou exportadora")
    estado = Column(String(2), nullable=False, index=True)
    ncm = Column(String(20), nullable=False, index=True)
    valor_fob = Column(Float, nullable=True)
    ano = Column(Integer, nullable=False, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_enc_estado_ncm", "estado", "ncm"),
        Index("idx_enc_ano_tipo", "ano", "tipo"),
    )

    def __repr__(self):
        return f"<EmpresaNCMEstado(id={self.id}, nome={self.nome_empresa[:20]!r}, uf={self.estado}, ncm={self.ncm})>"


class EmpresaComex(Base):
    """
    Empresas agregadas a partir do comex_stat (sincronização BigQuery → PostgreSQL).
    """

    __tablename__ = "empresas_comex"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(14), nullable=True, index=True)
    razao_social = Column(String(512), nullable=False, index=True)
    uf = Column(String(2), nullable=False, index=True)
    municipio = Column(String(255), nullable=True)
    tipo = Column(String(20), nullable=False, index=True)
    valor_fob_total = Column(Float, nullable=False, default=0)
    total_operacoes = Column(Integer, nullable=False, default=0)
    ano_referencia = Column(Integer, nullable=False, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ano_referencia",
            "tipo",
            "razao_social",
            "uf",
            "municipio",
            name="uq_empresas_comex_natural",
        ),
    )

    def __repr__(self):
        return f"<EmpresaComex(id={self.id}, razao={self.razao_social[:30]!r}, uf={self.uf}, tipo={self.tipo})>"


class OperacaoNCMEstado(Base):
    """
    Operações agregadas por NCM × UF × mês (ncm_exportacao / ncm_importacao).
    """

    __tablename__ = "operacao_ncm_estado"

    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, nullable=False, index=True)
    mes = Column(Integer, nullable=True, index=True)
    ncm = Column(String(8), nullable=False, index=True)
    descricao_ncm = Column(String(512), nullable=True)
    uf = Column(String(2), nullable=False, index=True)
    tipo_operacao = Column(String(20), nullable=False, index=True)
    valor_fob_usd = Column(Float, nullable=False)
    quantidade_estatistica = Column(Float, nullable=True)
    peso_kg = Column(Float, nullable=True)
    razao_social = Column(String(512), nullable=True, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ano",
            "mes",
            "ncm",
            "uf",
            "tipo_operacao",
            name="uq_operacao_ncm_estado_key",
        ),
        Index("idx_one_ncm_uf_tipo", "ncm", "uf", "tipo_operacao"),
    )

    def __repr__(self):
        return f"<OperacaoNCMEstado(ano={self.ano}, ncm={self.ncm}, uf={self.uf}, tipo={self.tipo_operacao})>"


class OperacaoEmpresa(Base):
    """Operação de importação/exportação por empresa × NCM (painel empresas)."""

    __tablename__ = "operacoes_empresa"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    tipo = Column(String(3), nullable=False, index=True, comment="IMP ou EXP")
    ncm = Column(String(8), nullable=False, index=True)
    ncm_descricao = Column(Text, nullable=True)
    uf_origem = Column(String(2), nullable=True, index=True)
    uf_destino = Column(String(2), nullable=True, index=True)
    pais = Column(String(60), nullable=True)
    ano = Column(Integer, nullable=True, index=True)
    mes = Column(Integer, nullable=True, index=True)
    valor_usd = Column(Numeric(18, 2), nullable=True)
    peso_kg = Column(Numeric(18, 3), nullable=True)
    quantidade = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    empresa = relationship("Empresa", backref="operacoes_detalhe")

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "tipo",
            "ncm",
            "uf_destino",
            "ano",
            "mes",
            name="uq_operacao_empresa_periodo",
        ),
        Index("idx_op_emp_empresa_tipo", "empresa_id", "tipo"),
        Index("idx_op_emp_ncm_ano", "ncm", "ano"),
    )


class DOURegistro(Base):
    """Registros do Diário Oficial relacionados a empresas."""

    __tablename__ = "dou_registros"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), nullable=True, index=True)
    razao_social = Column(String(255), nullable=True)
    data_pub = Column(Date, nullable=True, index=True)
    secao = Column(String(10), nullable=True)
    tipo_ato = Column(String(100), nullable=True, index=True)
    resumo = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_dou_cnpj_data", "cnpj", "data_pub"),)


class NCMDescricao(Base):
    """Cache de descrição oficial TEC e sugestão IA por NCM."""

    __tablename__ = "ncm_descricao"

    ncm = Column(String(8), primary_key=True)
    descricao_tec = Column(Text, nullable=True)
    sugestao_produto = Column(Text, nullable=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

