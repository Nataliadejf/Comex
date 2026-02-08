"""
Configuração e inicialização do banco de dados.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import settings
from .models import Base


# Obter DATABASE_URL do ambiente ou usar configuração padrão
database_url = os.getenv("DATABASE_URL") or settings.database_url

# Validar formato da URL antes de usar
def is_valid_database_url(url):
    """Valida se a URL do banco de dados está no formato correto."""
    if not url or url == "":
        return False
    
    # Verificar se é uma URL válida (deve começar com sqlite:// ou postgresql:// ou postgres://)
    if url.startswith("sqlite:///"):
        return True
    
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        # Verificar se tem formato básico: postgresql://user:pass@host:port/db
        if "@" not in url or ":" not in url:
            return False
        # Verificar se não é apenas um hash/ID
        if len(url) < 50:  # URLs válidas têm pelo menos 50 caracteres
            return False
        return True
    
    return False

# Render usa postgres://, mas SQLAlchemy precisa de postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Validar URL antes de usar
if database_url and not is_valid_database_url(database_url):
    import warnings
    warnings.warn(
        f"⚠️ DATABASE_URL inválida detectada: '{database_url[:50]}...' "
        f"(tamanho: {len(database_url)}). "
        f"Usando SQLite local como fallback. "
        f"Configure uma URL válida no formato: postgresql://user:pass@host:port/db",
        UserWarning
    )
    database_url = None

# Se não tiver DATABASE_URL válida, usar SQLite local
if not database_url or database_url == "":
    db_path = settings.data_dir / "database" / "comex.db"
    path_str = str(db_path.absolute()).replace("\\", "/")
    database_url = f"sqlite:///{path_str}"

# Criar engine do SQLAlchemy com tratamento de erro
try:
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        echo=settings.debug,
        pool_pre_ping=True,  # Verifica conexões antes de usar
    )
except (ValueError, Exception) as e:
    import warnings
    # Se for erro de parsing de URL (porta inválida), usar SQLite como fallback
    if "invalid literal" in str(e) or "port" in str(e).lower() or "int()" in str(e):
        warnings.warn(
            f"⚠️ DATABASE_URL inválida detectada (erro ao parsear: {str(e)[:100]}). "
            f"Usando SQLite local como fallback. "
            f"Configure uma URL válida no formato: postgresql://user:pass@host:port/db",
            UserWarning
        )
        # Fallback para SQLite
        db_path = settings.data_dir / "database" / "comex.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        path_str = str(db_path.absolute()).replace("\\", "/")
        database_url = f"sqlite:///{path_str}"
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=settings.debug,
            pool_pre_ping=True,
        )
    else:
        # Re-raise outros erros
        raise

# Criar SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados.
    Usado pelo FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

