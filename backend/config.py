"""
Configurações da aplicação.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from loguru import logger


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Ambiente
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Diretório de dados
    data_dir: Path = Field(default=Path("D:/NatFranca"), alias="DATA_DIR")
    
    # Database
    database_url: str = Field(
        default="sqlite:///D:/NatFranca/database/comex.db",
        alias="DATABASE_URL"
    )
    
    # API Comex Stat
    comex_stat_api_url: Optional[str] = Field(
        default=None,
        alias="COMEX_STAT_API_URL"
    )
    comex_stat_api_key: Optional[str] = Field(
        default=None,
        alias="COMEX_STAT_API_KEY"
    )
    
    # Configurações de coleta
    update_interval_hours: int = Field(default=24, alias="UPDATE_INTERVAL_HOURS")
    months_to_fetch: int = Field(default=3, alias="MONTHS_TO_FETCH")
    retry_attempts: int = Field(default=3, alias="RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=5, alias="RETRY_DELAY_SECONDS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=Path("D:/comex_data/logs"), alias="LOG_DIR")
    
    # Email Configuration
    email_smtp_server: str = Field(default="smtp.gmail.com", alias="EMAIL_SMTP_SERVER")
    email_smtp_port: int = Field(default=587, alias="EMAIL_SMTP_PORT")
    email_sender: str = Field(default="nataliadejesus2@gmail.com", alias="EMAIL_SENDER")
    email_sender_password: str = Field(default="", alias="EMAIL_SENDER_PASSWORD")
    email_admin: str = Field(default="nataliadejesus2@gmail.com", alias="EMAIL_ADMIN")
    app_url: str = Field(default="http://localhost:3000", alias="APP_URL")
    
    # SSL Configuration
    ssl_verify: bool = Field(default=True, alias="SSL_VERIFY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extras no .env
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Criar diretórios necessários
        self._create_directories()
    
    def _create_directories(self):
        """Cria os diretórios necessários se não existirem."""
        # Verificar se o diretório base existe, senão usar fallback
        if not Path(self.data_dir.parts[0]).exists():
            # Se o drive não existe, usar diretório do projeto
            project_dir = Path(__file__).parent.parent.parent / "data"
            self.data_dir = project_dir
            self.database_url = f"sqlite:///{project_dir / 'database' / 'comex.db'}"
            self.log_dir = project_dir / "logs"
            logger.warning(f"Drive {self.data_dir.parts[0]} não encontrado. Usando: {self.data_dir}")
        
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "database",
            self.data_dir / "exports",
            self.log_dir,
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Erro ao criar diretório {directory}: {e}")
                # Tentar criar em local alternativo
                if "D:" in str(directory):
                    alt_dir = Path(__file__).parent.parent.parent / "data" / directory.name
                    alt_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Diretório alternativo criado: {alt_dir}")


# Instância global de configurações
settings = Settings()

