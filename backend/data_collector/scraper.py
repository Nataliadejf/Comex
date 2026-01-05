"""
Scraper para download de dados do Portal Comex Stat (fallback).
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import requests

# Imports opcionais - não disponíveis no Render
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas não disponível - funcionalidade de scraping limitada")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("selenium não disponível - scraping não funcionará")

from config import settings


class ComexStatScraper:
    """
    Scraper para baixar dados do Portal Comex Stat quando API não está disponível.
    """
    
    BASE_URL = "http://comexstat.mdic.gov.br/"
    
    def __init__(self):
        self.data_dir = settings.data_dir / "raw"
        self.driver: Optional[Any] = None
        
    def _init_driver(self):
        """Inicializa o driver do Selenium."""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium não está disponível")
        
        if self.driver is not None:
            return
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Driver do Selenium inicializado")
        except WebDriverException as e:
            logger.error(f"Erro ao inicializar driver do Selenium: {e}")
            raise
    
    def _close_driver(self):
        """Fecha o driver do Selenium."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Driver do Selenium fechado")
            except Exception as e:
                logger.error(f"Erro ao fechar driver: {e}")
    
    def _get_months_to_fetch(self) -> List[str]:
        """
        Retorna lista de meses dos últimos N meses.
        Formato: ['YYYY-MM', ...]
        """
        months = []
        today = datetime.now()
        
        for i in range(settings.months_to_fetch):
            month_date = today - timedelta(days=30 * i)
            months.append(month_date.strftime("%Y-%m"))
        
        return sorted(months)
    
    def _download_file(self, url: str, destination: Path) -> bool:
        """
        Baixa um arquivo da URL especificada.
        
        Args:
            url: URL do arquivo
            destination: Caminho de destino
        
        Returns:
            True se o download foi bem-sucedido
        """
        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Arquivo baixado: {destination}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo {url}: {e}")
            return False
    
    def _navigate_to_download_page(self, mes: str, tipo_operacao: str) -> Optional[str]:
        """
        Navega até a página de download e retorna URL do arquivo.
        
        Args:
            mes: Mês no formato YYYY-MM
            tipo_operacao: 'Importação' ou 'Exportação'
        
        Returns:
            URL do arquivo para download ou None
        """
        self._init_driver()
        
        try:
            # Navegar para a página principal
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            
            # Aqui você precisaria navegar pela interface do site
            # e encontrar o link de download apropriado
            # Como não temos acesso real ao site, isso é um placeholder
            
            logger.warning(
                "Navegação no site requer implementação específica "
                "baseada na estrutura atual do Portal Comex Stat"
            )
            
            # Placeholder: retornar None indica que precisa implementação
            return None
        
        except TimeoutException:
            logger.error(f"Timeout ao navegar para página de download")
            return None
        except Exception as e:
            logger.error(f"Erro ao navegar para página de download: {e}")
            return None
    
    def download_month_data(
        self,
        mes: str,
        tipo_operacao: str
    ) -> Optional[Path]:
        """
        Baixa dados de um mês específico.
        
        Args:
            mes: Mês no formato YYYY-MM
            tipo_operacao: 'Importação' ou 'Exportação'
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        # Criar diretório do mês
        month_dir = self.data_dir / mes
        month_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        filename = f"{tipo_operacao.lower()}_{mes}.csv"
        filepath = month_dir / filename
        
        # Se já existe, não baixar novamente
        if filepath.exists():
            logger.info(f"Arquivo já existe: {filepath}")
            return filepath
        
        # Tentar baixar
        url = self._navigate_to_download_page(mes, tipo_operacao)
        
        if url:
            if self._download_file(url, filepath):
                return filepath
        
        return None
    
    def download_recent_data(self) -> List[Path]:
        """
        Baixa dados dos últimos N meses.
        
        Returns:
            Lista de caminhos dos arquivos baixados
        """
        months = self._get_months_to_fetch()
        downloaded_files = []
        
        tipos = ["Importação", "Exportação"]
        
        for mes in months:
            for tipo in tipos:
                try:
                    filepath = self.download_month_data(mes, tipo)
                    if filepath:
                        downloaded_files.append(filepath)
                    time.sleep(2)  # Delay entre downloads
                except Exception as e:
                    logger.error(f"Erro ao baixar dados de {mes} - {tipo}: {e}")
        
        self._close_driver()
        return downloaded_files
    
    def parse_csv_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Parse de arquivo CSV baixado.
        
        Args:
            filepath: Caminho do arquivo CSV
        
        Returns:
            Lista de dicionários com os dados
        """
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                    logger.info(f"Arquivo lido com encoding {encoding}: {filepath}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError(f"Não foi possível ler o arquivo: {filepath}")
            
            # Converter para lista de dicionários
            records = df.to_dict('records')
            logger.info(f"{len(records)} registros parseados de {filepath}")
            
            return records
        
        except Exception as e:
            logger.error(f"Erro ao fazer parse do arquivo {filepath}: {e}")
            return []

