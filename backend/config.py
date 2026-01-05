"""
Configurações da aplicação.
"""
import os
from pathlib import Path
from typing import Optional
try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
except ImportError:
    # Pydantic v1 (fallback para Render)
    from pydantic import BaseSettings

from pydantic import Field


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Ambiente
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Diretório de dados (relativo ao projeto)
    data_dir: Path = Field(
        default=Path(__file__).parent.parent / "comex_data",
        alias="DATA_DIR"
    )
    
    # Database (será construído dinamicamente se não definido)
    database_url: Optional[str] = Field(
        default="",  # Será construído dinamicamente
        alias="DATABASE_URL"
    )
    
    # API Comex Stat
    comex_stat_api_url: Optional[str] = Field(
        default="https://api-comexstat.mdic.gov.br",
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
    log_dir: Optional[Path] = Field(
        default=Path(__file__).parent.parent / "comex_data" / "logs",
        alias="LOG_DIR"
    )
    
    # Autenticação
    secret_key: str = Field(
        default="sua-chave-secreta-aqui-mude-em-producao",
        alias="SECRET_KEY"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configurar caminhos relativos se não foram definidos via env
        if str(self.data_dir) == "D:/comex_data" or "D:/" in str(self.data_dir):
            self.data_dir = Path(__file__).parent.parent / "comex_data"
        
        # Configurar database_url se não foi definido ou contém D:/
        if not self.database_url or "D:/comex_data" in str(self.database_url) or "D:/" in str(self.database_url):
            db_path = self.data_dir / "database" / "comex.db"
            self.database_url = f"sqlite:///{db_path.absolute()}"
        
        # Configurar log_dir se contém D:/
        if "D:/comex_data" in str(self.log_dir) or "D:/" in str(self.log_dir):
            self.log_dir = self.data_dir / "logs"
        
        # Criar diretórios necessários
        self._create_directories()
    
    def _create_directories(self):
        """Cria os diretórios necessários se não existirem."""
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "database",
            self.data_dir / "exports",
            self.log_dir,
        ]
        
        # Tenta criar todos os diretórios
        failed = False
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                failed = True
                print(f"⚠️ Aviso: Não foi possível criar {directory}: {e}")
        
        # Se falhou, tenta usar diretório temporário como fallback
        if failed:
            try:
                import tempfile
                fallback_dir = Path(tempfile.gettempdir()) / "comex_data"
                fallback_dir.mkdir(parents=True, exist_ok=True)
                
                # Atualiza os caminhos para o fallback
                self.data_dir = fallback_dir
                db_path = fallback_dir / "database" / "comex.db"
                self.database_url = f"sqlite:///{db_path.absolute()}"
                self.log_dir = fallback_dir / "logs"
                
                # Cria todos os diretórios no fallback
                fallback_dirs = [
                    self.data_dir,
                    self.data_dir / "raw",
                    self.data_dir / "processed",
                    self.data_dir / "database",
                    self.data_dir / "exports",
                    self.log_dir,
                ]
                for d in fallback_dirs:
                    d.mkdir(parents=True, exist_ok=True)
                
                print(f"✅ Usando diretório alternativo: {fallback_dir}")
            except Exception as e2:
                print(f"❌ Erro crítico: Não foi possível criar diretórios nem usar fallback: {e2}")
                raise


# Instância global de configurações
settings = Settings()

