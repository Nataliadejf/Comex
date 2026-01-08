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

# Render usa postgres://, mas SQLAlchemy precisa de postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Se não tiver DATABASE_URL, usar SQLite local
if not database_url or database_url == "":
    db_path = settings.data_dir / "database" / "comex.db"
    database_url = f"sqlite:///{db_path.absolute()}"

# Criar engine do SQLAlchemy
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.debug,
    pool_pre_ping=True,  # Verifica conexões antes de usar
)

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

