# ================================================================
# DATABASE.PY - CONFIGURAÇÃO SQLALCHEMY
# ================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usar DATABASE_URL ou montar a partir de variáveis individuais
database_url = os.getenv("DATABASE_URL")
if not database_url:
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_name = os.getenv("DATABASE_NAME", "comex_db")
    db_user = os.getenv("DATABASE_USER", "user")
    db_password = os.getenv("DATABASE_PASSWORD", "password")
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

engine = create_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
