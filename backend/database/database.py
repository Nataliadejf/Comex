"""
Configuração e inicialização do banco de dados.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import settings
from .models import Base


# Criar engine do SQLAlchemy
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
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

