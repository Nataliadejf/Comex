"""
Módulo de banco de dados.
"""
from .models import Base, OperacaoComex, NCMInfo, ColetaLog, TipoOperacao, ViaTransporte
from .database import get_db, init_db

# Imports opcionais para modelos de autenticação
try:
    from .models import Usuario, AprovacaoCadastro
except ImportError:
    Usuario = None
    AprovacaoCadastro = None

__all__ = [
    "Base",
    "OperacaoComex",
    "NCMInfo",
    "ColetaLog",
    "TipoOperacao",
    "ViaTransporte",
    "get_db",
    "init_db",
]

# Adicionar modelos opcionais ao __all__ se disponíveis
if Usuario is not None:
    __all__.append("Usuario")
if AprovacaoCadastro is not None:
    __all__.append("AprovacaoCadastro")

