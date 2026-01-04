"""
Script automatizado para download de dados do portal Comex Stat.
Mapeia os botões da tela e faz download mensalmente.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import time

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium não instalado. Instale com: pip install selenium")

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright não instalado. Instale com: pip install playwright && playwright install")


class ComexStatDownloader:
    """Classe para download automático de dados do portal Comex Stat."""
    
    BASE_URL = "https://comexstat.mdic.gov.br"
    DOWNLOAD_DIR = settings.data_dir / "raw"
    
    def __init__(self, use_playwright: bool = True):
        """
        Inicializa o downloader.
        
        Args:
            use_playwright: Se True, usa Playwright; caso contrário, usa Selenium
        """
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        self.driver = None
        self.browser = None
        self.page = None
        
        # Criar diretório de download
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloader inicializado. Método: {'Playwright' if self.use_playwright else 'Selenium'}")
    
    def _init_selenium(self):
        """Inicializa o driver Selenium."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium não está instalado")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Modo headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Configurar diretório de download
        prefs = {
            "download.default_directory": str(self.DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Driver Selenium inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar Selenium: {e}")
            raise
    
    def _init_playwright(self):
        """Inicializa o Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright não está instalado")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Criar contexto com download configurado
        context = self.browser.new_context(
            accept_downloads=True
        )
        
        self.page = context.new_page()
        
        # Configurar download
        self.page.on("download", self._handle_download)
        
        logger.info("Playwright inicializado")
    
    def _handle_download(self, download):
        """Manipula downloads do Playwright."""
        try:
            # Obter nome do arquivo
            suggested_filename = download.suggested_filename
            
            # Salvar no diretório de download
            filepath = self.DOWNLOAD_DIR / suggested_filename
            download.save_as(filepath)
            
            logger.info(f"Arquivo baixado: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao salvar download: {e}")
    
    def _get_months_to_download(self, months: int = 3) -> List[str]:
        """
        Retorna lista de meses para download (formato YYYY-MM).
        
        Args:
            months: Número de meses para trás a partir de hoje
        """
        months_list = []
        today = datetime.now()
        
        for i in range(months):
            date = today - timedelta(days=30 * i)
            month_str = date.strftime("%Y-%m")
            months_list.append(month_str)
        
        return months_list
    
    def download_exportacao(self, mes: str) -> Optional[Path]:
        """
        Faz download do arquivo de exportação para um mês específico.
        
        Args:
            mes: Mês no formato YYYY-MM (ex: "2025-01")
        
        Returns:
            Caminho do arquivo baixado ou None se falhar
        """
        logger.info(f"Iniciando download de exportação para {mes}")
        
        try:
            if self.use_playwright:
                return self._download_with_playwright(mes, "Exportação")
            else:
                return self._download_with_selenium(mes, "Exportação")
        except Exception as e:
            logger.error(f"Erro ao baixar exportação {mes}: {e}")
            return None
    
    def download_importacao(self, mes: str) -> Optional[Path]:
        """
        Faz download do arquivo de importação para um mês específico.
        
        Args:
            mes: Mês no formato YYYY-MM (ex: "2025-01")
        
        Returns:
            Caminho do arquivo baixado ou None se falhar
        """
        logger.info(f"Iniciando download de importação para {mes}")
        
        try:
            if self.use_playwright:
                return self._download_with_playwright(mes, "Importação")
            else:
                return self._download_with_selenium(mes, "Importação")
        except Exception as e:
            logger.error(f"Erro ao baixar importação {mes}: {e}")
            return None
    
    def _download_with_playwright(self, mes: str, tipo: str) -> Optional[Path]:
        """Faz download usando Playwright."""
        try:
            # Navegar para a página principal
            self.page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)
            logger.info(f"Página carregada: {self.BASE_URL}")
            
            # Aguardar página carregar
            time.sleep(2)
            
            # Mapear botões/interações necessárias
            # NOTA: Os seletores abaixo precisam ser ajustados conforme a estrutura real do site
            
            # Exemplo de mapeamento (ajustar conforme necessário):
            # 1. Clicar em "Dados" ou menu principal
            # 2. Selecionar tipo (Exportação/Importação)
            # 3. Selecionar período/mês
            # 4. Clicar em "Download" ou "Exportar"
            
            # Tentar encontrar e clicar no botão de download
            # Este é um exemplo genérico - precisa ser ajustado para o site real
            try:
                # Aguardar elemento aparecer (ajustar seletor)
                # Exemplo: self.page.wait_for_selector("button.download", timeout=10000)
                
                # Clicar no botão (ajustar seletor)
                # Exemplo: self.page.click("button.download")
                
                logger.warning("Mapeamento de botões precisa ser ajustado para o site real")
                logger.info("Por enquanto, usando método alternativo de download direto")
                
                # Método alternativo: tentar URL direta de download
                return self._try_direct_download(mes, tipo)
                
            except PlaywrightTimeout:
                logger.error("Timeout ao aguardar elementos da página")
                return None
                
        except Exception as e:
            logger.error(f"Erro no download com Playwright: {e}")
            return None
    
    def _download_with_selenium(self, mes: str, tipo: str) -> Optional[Path]:
        """Faz download usando Selenium."""
        try:
            self.driver.get(self.BASE_URL)
            logger.info(f"Página carregada: {self.BASE_URL}")
            
            # Aguardar página carregar
            time.sleep(3)
            
            # Mapear botões/interações (mesmo processo do Playwright)
            # Ajustar seletores conforme necessário
            
            logger.warning("Mapeamento de botões precisa ser ajustado para o site real")
            return self._try_direct_download(mes, tipo)
            
        except Exception as e:
            logger.error(f"Erro no download com Selenium: {e}")
            return None
    
    def _try_direct_download(self, mes: str, tipo: str) -> Optional[Path]:
        """
        Tenta fazer download direto via URL (método alternativo).
        
        Args:
            mes: Mês no formato YYYY-MM
            tipo: "Exportação" ou "Importação"
        """
        import requests
        
        # Padrões de URL comuns do Comex Stat
        ano, mes_num = mes.split("-")
        
        # Tentar diferentes padrões de URL
        url_patterns = [
            f"{self.BASE_URL}/download/{tipo.lower()}_{ano}_{mes_num}.csv",
            f"{self.BASE_URL}/api/download/{tipo.lower()}/{ano}/{mes_num}",
            f"{self.BASE_URL}/files/{tipo[0:3].upper()}_{ano}_{mes_num}.csv",
        ]
        
        for url in url_patterns:
            try:
                logger.info(f"Tentando URL: {url}")
                response = requests.get(url, timeout=30, verify=False)
                
                if response.status_code == 200 and len(response.content) > 1000:
                    # Salvar arquivo
                    filename = f"{tipo[0:3].upper()}_{ano}_{mes_num}.csv"
                    filepath = self.DOWNLOAD_DIR / filename
                    
                    filepath.write_bytes(response.content)
                    logger.info(f"✅ Arquivo baixado: {filepath}")
                    return filepath
                    
            except Exception as e:
                logger.debug(f"URL não funcionou: {url} - {e}")
                continue
        
        logger.warning(f"Não foi possível baixar {tipo} para {mes} via URL direta")
        return None
    
    def download_all_months(self, months: int = 3, tipos: List[str] = None) -> List[Path]:
        """
        Faz download de todos os meses especificados.
        
        Args:
            months: Número de meses para trás
            tipos: Lista de tipos ["Exportação", "Importação"] ou None para ambos
        
        Returns:
            Lista de arquivos baixados
        """
        if tipos is None:
            tipos = ["Exportação", "Importação"]
        
        months_list = self._get_months_to_download(months)
        downloaded_files = []
        
        logger.info(f"Iniciando download de {len(months_list)} meses")
        
        for mes in months_list:
            for tipo in tipos:
                try:
                    if tipo == "Exportação":
                        filepath = self.download_exportacao(mes)
                    else:
                        filepath = self.download_importacao(mes)
                    
                    if filepath:
                        downloaded_files.append(filepath)
                    
                    # Aguardar entre downloads para não sobrecarregar o servidor
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao baixar {tipo} {mes}: {e}")
                    continue
        
        logger.info(f"✅ Total de arquivos baixados: {len(downloaded_files)}")
        return downloaded_files
    
    def close(self):
        """Fecha o navegador/driver."""
        try:
            if self.use_playwright:
                if self.browser:
                    self.browser.close()
                if hasattr(self, 'playwright'):
                    self.playwright.stop()
            else:
                if self.driver:
                    self.driver.quit()
            logger.info("Navegador fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar navegador: {e}")


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download automático de dados do Comex Stat")
    parser.add_argument("--months", type=int, default=3, help="Número de meses para baixar")
    parser.add_argument("--tipo", choices=["Exportação", "Importação", "Ambos"], default="Ambos")
    parser.add_argument("--use-playwright", action="store_true", help="Usar Playwright ao invés de Selenium")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("DOWNLOAD AUTOMÁTICO - COMEX STAT")
    logger.info("=" * 60)
    
    # Verificar espaço em disco
    try:
        import shutil
        free_space = shutil.disk_usage("D:/").free / (1024**3)  # GB
        logger.info(f"Espaço livre em D:: {free_space:.2f} GB")
        
        if free_space < 1:
            logger.warning("⚠️  Pouco espaço em disco disponível!")
    except Exception as e:
        logger.warning(f"Não foi possível verificar espaço em disco: {e}")
    
    # Inicializar downloader
    downloader = None
    try:
        downloader = ComexStatDownloader(use_playwright=args.use_playwright)
        
        # Determinar tipos
        tipos = None
        if args.tipo != "Ambos":
            tipos = [args.tipo]
        
        # Fazer downloads
        downloaded_files = downloader.download_all_months(
            months=args.months,
            tipos=tipos
        )
        
        logger.info("=" * 60)
        logger.info("DOWNLOAD CONCLUÍDO!")
        logger.info(f"Arquivos baixados: {len(downloaded_files)}")
        logger.info("=" * 60)
        
        # Processar arquivos baixados
        if downloaded_files:
            logger.info("Iniciando processamento dos arquivos...")
            from process_files import main_async
            import asyncio
            asyncio.run(main_async())
        
    except Exception as e:
        logger.error(f"Erro no processo de download: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if downloader:
            downloader.close()


if __name__ == "__main__":
    main()



