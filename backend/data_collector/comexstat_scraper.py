"""
Scraper automático para o ComexStat (comexstat.mdic.gov.br).
Interage com o módulo "Dados Gerais" para baixar dados automaticamente.
"""
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import re

from config import settings

# Imports para web scraping
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import (
        TimeoutException, 
        WebDriverException,
        NoSuchElementException,
        ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
    
    # Tentar importar webdriver-manager para instalação automática do ChromeDriver
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
        logger.info("webdriver-manager não disponível - ChromeDriver precisa estar no PATH")
        
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False
    logger.warning("selenium não disponível - instale com: pip install selenium")


class ComexStatScraper:
    """
    Scraper automático para o ComexStat usando Selenium.
    Interage com a interface web para fazer downloads automáticos.
    """
    
    BASE_URL = "https://comexstat.mdic.gov.br"
    DADOS_GERAIS_URL = f"{BASE_URL}/pt/dados-gerais"
    
    def __init__(self):
        self.data_dir = settings.data_dir / "comexstat_csv"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.driver: Optional[Any] = None
        self.wait_timeout = 30
        
    def _init_driver(self, headless: bool = True):
        """Inicializa o driver do Selenium."""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError(
                "Selenium não está disponível. Instale com: pip install selenium\n"
                "Também é necessário ter o ChromeDriver instalado."
            )
        
        if self.driver is not None:
            return
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Configurar download automático
        prefs = {
            "download.default_directory": str(self.data_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.notifications": 2,  # Desabilitar notificações
            "profile.default_content_settings.popups": 0,  # Permitir popups (pode ser necessário para download)
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Tentar usar webdriver-manager se disponível
            if WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("Baixando/verificando ChromeDriver via webdriver-manager...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Usar ChromeDriver do PATH
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Driver do Selenium inicializado")
        except WebDriverException as e:
            logger.error(f"❌ Erro ao inicializar driver do Selenium: {e}")
            logger.error("💡 Soluções:")
            logger.error("   1. Instale webdriver-manager: pip install webdriver-manager")
            logger.error("   2. Ou instale ChromeDriver manualmente e adicione ao PATH")
            logger.error("   3. Verifique se o Chrome está instalado")
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
    
    def _wait_for_element(self, by: By, value: str, timeout: int = None):
        """Aguarda elemento aparecer na página."""
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = None):
        """Aguarda elemento ficar clicável."""
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, value)))
    
    def _navigate_to_dados_gerais(self):
        """Navega para a página de Dados Gerais."""
        try:
            logger.info(f"Navegando para {self.DADOS_GERAIS_URL}...")
            self.driver.get(self.DADOS_GERAIS_URL)
            
            # Aguardar página carregar completamente (SPA pode demorar)
            logger.info("Aguardando aplicação carregar...")
            time.sleep(5)
            
            # Aguardar JavaScript executar completamente
            try:
                # Aguardar até que o documento esteja pronto
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logger.info("✅ Documento carregado")
            except:
                logger.warning("⚠️ Timeout aguardando documento carregar")
            
            # Aguardar um pouco mais para JavaScript executar
            time.sleep(3)
            
            # Verificar se a página carregou corretamente
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                logger.info(f"✅ Página carregada - Título: {self.driver.title[:50]}")
                
                # Tentar encontrar elementos comuns de aplicações SPA
                try:
                    # Procurar por inputs, divs clicáveis, etc.
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    divs = self.driver.find_elements(By.TAG_NAME, "div")
                    logger.info(f"   Elementos encontrados: {len(inputs)} inputs, {len(buttons)} buttons, {len(divs)} divs")
                    
                    # Se estamos na página inicial, tentar clicar no botão "Acessar" ou "Acesse os Dados"
                    page_title = self.driver.title.lower()
                    if "dados gerais" not in page_title and "dados-gerais" not in self.driver.current_url.lower():
                        logger.info("   Parece ser a página inicial - tentando acessar Dados Gerais...")
                        
                        # Procurar botão "Acessar" ou link para Dados Gerais
                        try:
                            # Tentar encontrar link ou botão com texto relacionado a "Dados Gerais"
                            dados_gerais_links = self.driver.find_elements(
                                By.XPATH,
                                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dados gerais')] | "
                                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dados gerais')] | "
                                "//a[contains(@href, 'dados-gerais')]"
                            )
                            
                            if dados_gerais_links:
                                logger.info(f"   Encontrado {len(dados_gerais_links)} link(s) para Dados Gerais")
                                dados_gerais_links[0].click()
                                time.sleep(5)  # Aguardar navegação
                                logger.info("   ✅ Navegado para Dados Gerais")
                            else:
                                # Tentar clicar em qualquer botão "Acessar" próximo a texto sobre dados
                                acessar_buttons = self.driver.find_elements(
                                    By.XPATH,
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acessar')]"
                                )
                                if acessar_buttons:
                                    logger.info(f"   Encontrado {len(acessar_buttons)} botão(ões) 'Acessar'")
                                    # Clicar no primeiro que estiver visível
                                    for btn in acessar_buttons:
                                        try:
                                            if btn.is_displayed():
                                                btn.click()
                                                time.sleep(5)
                                                logger.info("   ✅ Clicado em botão 'Acessar'")
                                                break
                                        except:
                                            continue
                        except Exception as e:
                            logger.debug(f"Erro ao tentar navegar: {e}")
                except:
                    pass
                
                return True
            except NoSuchElementException:
                logger.warning("⚠️ Página pode não ter carregado completamente")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao navegar para Dados Gerais: {e}")
            return False
    
    def _preencher_filtros(
        self,
        ano: int,
        mes: int,
        tipo_operacao: str = "Ambos"  # "Importação", "Exportação", "Ambos"
    ) -> bool:
        """
        Preenche os filtros na página de Dados Gerais.
        
        Args:
            ano: Ano dos dados
            mes: Mês dos dados (1-12)
            tipo_operacao: Tipo de operação ("Importação", "Exportação", "Ambos")
        
        Returns:
            True se os filtros foram preenchidos com sucesso
        """
        try:
            logger.info(f"Preenchendo filtros: Ano={ano}, Mês={mes}, Tipo={tipo_operacao}")
            
            # Primeiro, preencher o tipo de Fluxo (Exportação/Importação/Ambos)
            logger.info("Preenchendo filtro de Fluxo...")
            fluxo_preenchido = False
            try:
                # Procurar radio buttons ou selects para Fluxo
                fluxo_selectors = [
                    "//input[@type='radio' and contains(@value, 'Exportação')]",
                    "//input[@type='radio' and contains(@value, 'Importação')]",
                    "//input[@type='radio' and contains(@value, 'Ambos')]",
                    "//label[contains(text(), 'Exportação')]/preceding-sibling::input[@type='radio']",
                    "//label[contains(text(), 'Importação')]/preceding-sibling::input[@type='radio']",
                    "//label[contains(text(), 'Exportação e Importação')]/preceding-sibling::input[@type='radio']",
                ]
                
                # Mapear tipo_operacao para o texto esperado
                tipo_map = {
                    "Exportação": ["Exportação", "exportação"],
                    "Importação": ["Importação", "importação"],
                    "Ambos": ["Ambos", "Exportação e Importação", "Exportação e importação"]
                }
                
                tipos_procurar = tipo_map.get(tipo_operacao, tipo_map["Ambos"])
                
                for tipo_texto in tipos_procurar:
                    try:
                        # Procurar por label com o texto e depois o input associado
                        labels = self.driver.find_elements(By.XPATH, f"//label[contains(text(), '{tipo_texto}')]")
                        for label in labels:
                            try:
                                # Tentar encontrar o input associado
                                input_id = label.get_attribute("for")
                                if input_id:
                                    input_elem = self.driver.find_element(By.ID, input_id)
                                    if input_elem.get_attribute("type") == "radio":
                                        self.driver.execute_script("arguments[0].click();", input_elem)
                                        logger.info(f"✅ Fluxo selecionado: {tipo_texto}")
                                        fluxo_preenchido = True
                                        break
                                else:
                                    # Tentar clicar no label diretamente (pode acionar o radio)
                                    self.driver.execute_script("arguments[0].click();", label)
                                    logger.info(f"✅ Fluxo selecionado via label: {tipo_texto}")
                                    fluxo_preenchido = True
                                    break
                            except:
                                continue
                        
                        if fluxo_preenchido:
                            break
                            
                        # Tentar encontrar radio buttons diretamente
                        radios = self.driver.find_elements(By.XPATH, f"//input[@type='radio']")
                        for radio in radios:
                            try:
                                value = radio.get_attribute("value") or ""
                                # Verificar se o valor ou o label próximo contém o texto
                                if any(t in value.lower() for t in [t.lower() for t in tipos_procurar]):
                                    self.driver.execute_script("arguments[0].click();", radio)
                                    logger.info(f"✅ Fluxo selecionado via radio: {value}")
                                    fluxo_preenchido = True
                                    break
                            except:
                                continue
                        
                        if fluxo_preenchido:
                            break
                    except:
                        continue
                
                if not fluxo_preenchido:
                    logger.warning("⚠️ Não foi possível preencher o filtro de Fluxo")
            except Exception as e:
                logger.debug(f"Erro ao preencher Fluxo: {e}")
            
            time.sleep(1)  # Aguardar após selecionar Fluxo
            
            # Aguardar página carregar completamente (aplicações Angular/React podem demorar)
            logger.info("Aguardando elementos da página aparecerem...")
            time.sleep(5)
            
            # Para aplicações SPA, tentar aguardar elementos aparecerem
            try:
                # Aguardar qualquer input ou elemento interativo aparecer
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                logger.info("✅ Inputs encontrados na página")
            except:
                logger.warning("⚠️ Nenhum input encontrado - pode ser uma aplicação SPA com elementos customizados")
            
            # Tentar aguardar selects também
            try:
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                if selects:
                    logger.info(f"✅ {len(selects)} select(s) encontrado(s)")
            except:
                pass
            
            # Estratégia expandida: Procurar por campos de formulário comuns
            # Procurar por "Ano inicial" e "Ano final" separadamente
            selectors_ano_inicial = [
                "//label[contains(text(), 'Ano inicial')]/following::select[1]",
                "//label[contains(text(), 'Ano inicial')]/following::input[1]",
                "select[name*='ano_inicial']",
                "select[id*='ano_inicial']",
                "select[name*='anoInicial']",
                "select[id*='anoInicial']",
                "select[name*='ano_inicio']",
                "select[id*='ano_inicio']",
            ]
            
            selectors_ano_final = [
                "//label[contains(text(), 'Ano final')]/following::select[1]",
                "//label[contains(text(), 'Ano final')]/following::input[1]",
                "select[name*='ano_final']",
                "select[id*='ano_final']",
                "select[name*='anoFinal']",
                "select[id*='anoFinal']",
            ]
            
            # Seletores genéricos para ano (fallback)
            selectors_ano = [
                # Por atributo
                "select[name*='ano']",
                "select[id*='ano']",
                "select[class*='ano']",
                "select[name*='year']",
                "select[id*='year']",
                # Por XPath
                "//select[contains(@name, 'ano')]",
                "//select[contains(@id, 'ano')]",
                "//select[contains(@name, 'year')]",
                "//select[contains(@id, 'year')]",
                # Por texto do label
                "//label[contains(text(), 'Ano')]/following::select[1]",
                "//label[contains(text(), 'Year')]/following::select[1]",
                # Inputs também podem ser usados
                "input[name*='ano']",
                "input[id*='ano']",
                "input[type='number'][name*='ano']",
            ]
            
            # Procurar por "Mês inicial" e "Mês final" separadamente
            selectors_mes_inicial = [
                "//label[contains(text(), 'Mês inicial')]/following::select[1]",
                "//label[contains(text(), 'Mês inicial')]/following::input[1]",
                "select[name*='mes_inicial']",
                "select[id*='mes_inicial']",
                "select[name*='mesInicial']",
                "select[id*='mesInicial']",
                "select[name*='mes_inicio']",
                "select[id*='mes_inicio']",
            ]
            
            selectors_mes_final = [
                "//label[contains(text(), 'Mês final')]/following::select[1]",
                "//label[contains(text(), 'Mês final')]/following::input[1]",
                "select[name*='mes_final']",
                "select[id*='mes_final']",
                "select[name*='mesFinal']",
                "select[id*='mesFinal']",
            ]
            
            # Seletores genéricos para mês (fallback)
            selectors_mes = [
                # Por atributo
                "select[name*='mes']",
                "select[id*='mes']",
                "select[class*='mes']",
                "select[name*='month']",
                "select[id*='month']",
                # Por XPath
                "//select[contains(@name, 'mes')]",
                "//select[contains(@id, 'mes')]",
                "//select[contains(@name, 'month')]",
                "//select[contains(@id, 'month')]",
                # Por texto do label
                "//label[contains(text(), 'Mês')]/following::select[1]",
                "//label[contains(text(), 'Month')]/following::select[1]",
                # Inputs também podem ser usados
                "input[name*='mes']",
                "input[id*='mes']",
                "input[type='number'][name*='mes']",
            ]
            
            selectors_tipo = [
                # Por atributo
                "select[name*='tipo']",
                "select[name*='operacao']",
                "select[id*='tipo']",
                "select[id*='operacao']",
                "select[name*='type']",
                "select[id*='type']",
                # Por XPath
                "//select[contains(@name, 'tipo')]",
                "//select[contains(@name, 'operacao')]",
                "//select[contains(@name, 'type')]",
                "//select[contains(@id, 'tipo')]",
                "//select[contains(@id, 'operacao')]",
            ]
            
            # Tentar encontrar e preencher campo de ano INICIAL
            ano_inicial_preenchido = False
            for selector in selectors_ano_inicial:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Verificar se é select ou input
                    if element.tag_name == "select":
                        select = Select(element)
                        # Tentar diferentes formas de seleção
                        try:
                            select.select_by_value(str(ano))
                        except:
                            try:
                                select.select_by_visible_text(str(ano))
                            except:
                                select.select_by_index(0)
                        logger.info(f"✅ Ano inicial selecionado: {ano}")
                        ano_inicial_preenchido = True
                        break
                    elif element.tag_name == "input":
                        element.clear()
                        element.send_keys(str(ano))
                        logger.info(f"✅ Ano inicial preenchido: {ano}")
                        ano_inicial_preenchido = True
                        break
                except (NoSuchElementException, ElementNotInteractableException) as e:
                    continue
            
            # Tentar encontrar e preencher campo de ano FINAL
            ano_final_preenchido = False
            for selector in selectors_ano_final:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element.tag_name == "select":
                        select = Select(element)
                        try:
                            select.select_by_value(str(ano))
                        except:
                            try:
                                select.select_by_visible_text(str(ano))
                            except:
                                select.select_by_index(0)
                        logger.info(f"✅ Ano final selecionado: {ano}")
                        ano_final_preenchido = True
                        break
                    elif element.tag_name == "input":
                        element.clear()
                        element.send_keys(str(ano))
                        logger.info(f"✅ Ano final preenchido: {ano}")
                        ano_final_preenchido = True
                        break
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
            
            # Se não encontrou campos específicos, tentar método genérico
            ano_preenchido = ano_inicial_preenchido and ano_final_preenchido
            if not ano_preenchido:
                for selector in selectors_ano:
                    try:
                        if selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        # Verificar se é select ou input
                        if element.tag_name == "select":
                            select = Select(element)
                            # Tentar diferentes formas de seleção
                            try:
                                select.select_by_value(str(ano))
                            except:
                                try:
                                    select.select_by_visible_text(str(ano))
                                except:
                                    select.select_by_index(0)  # Selecionar primeiro item
                            logger.info(f"✅ Ano selecionado: {ano}")
                            ano_preenchido = True
                            break
                        elif element.tag_name == "input":
                            element.clear()
                            element.send_keys(str(ano))
                            logger.info(f"✅ Ano preenchido: {ano}")
                            ano_preenchido = True
                            break
                    except (NoSuchElementException, ElementNotInteractableException) as e:
                        continue
            
            if not ano_preenchido:
                logger.warning("⚠️ Campo de ano não encontrado - tentando método alternativo")
                # Tentar encontrar todos os selects e tentar preencher
                try:
                    selects = self.driver.find_elements(By.TAG_NAME, "select")
                    logger.info(f"   Encontrados {len(selects)} selects na página")
                    for i, select_elem in enumerate(selects):
                        try:
                            select = Select(select_elem)
                            options = [opt.text for opt in select.options]
                            logger.debug(f"   Select {i}: {options[:5]}...")
                            # Tentar encontrar opção com o ano
                            for opt in select.options:
                                if str(ano) in opt.text or str(ano) in opt.get_attribute("value"):
                                    select.select_by_visible_text(opt.text)
                                    logger.info(f"✅ Ano selecionado via busca: {ano}")
                                    ano_preenchido = True
                                    break
                            if ano_preenchido:
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Erro ao buscar selects: {e}")
            
            # Tentar encontrar e preencher campo de mês INICIAL
            mes_inicial_preenchido = False
            meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome = meses_pt[mes - 1] if 1 <= mes <= 12 else str(mes)
            
            for selector in selectors_mes_inicial:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element.tag_name == "select":
                        select = Select(element)
                        try:
                            select.select_by_value(str(mes))
                        except:
                            try:
                                select.select_by_value(f"{mes:02d}")
                            except:
                                try:
                                    select.select_by_visible_text(mes_nome)
                                except:
                                    try:
                                        select.select_by_visible_text(str(mes))
                                    except:
                                        select.select_by_index(mes - 1)
                        logger.info(f"✅ Mês inicial selecionado: {mes_nome} ({mes})")
                        mes_inicial_preenchido = True
                        break
                    elif element.tag_name == "input":
                        element.clear()
                        element.send_keys(str(mes))
                        logger.info(f"✅ Mês inicial preenchido: {mes}")
                        mes_inicial_preenchido = True
                        break
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
            
            # Tentar encontrar e preencher campo de mês FINAL (mesmo mês)
            mes_final_preenchido = False
            for selector in selectors_mes_final:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element.tag_name == "select":
                        select = Select(element)
                        try:
                            select.select_by_value(str(mes))
                        except:
                            try:
                                select.select_by_value(f"{mes:02d}")
                            except:
                                try:
                                    select.select_by_visible_text(mes_nome)
                                except:
                                    try:
                                        select.select_by_visible_text(str(mes))
                                    except:
                                        select.select_by_index(mes - 1)
                        logger.info(f"✅ Mês final selecionado: {mes_nome} ({mes})")
                        mes_final_preenchido = True
                        break
                    elif element.tag_name == "input":
                        element.clear()
                        element.send_keys(str(mes))
                        logger.info(f"✅ Mês final preenchido: {mes}")
                        mes_final_preenchido = True
                        break
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
            
            # Se não encontrou campos específicos, tentar método genérico
            mes_preenchido = mes_inicial_preenchido and mes_final_preenchido
            if not mes_preenchido:
                for selector in selectors_mes:
                    try:
                        if selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        # Verificar se é select ou input
                        if element.tag_name == "select":
                            select = Select(element)
                            # Tentar diferentes formas de seleção
                            try:
                                select.select_by_value(str(mes))
                            except:
                                try:
                                    select.select_by_value(f"{mes:02d}")
                                except:
                                    try:
                                        select.select_by_visible_text(str(mes))
                                    except:
                                        select.select_by_index(0)
                            logger.info(f"✅ Mês selecionado: {mes}")
                            mes_preenchido = True
                            break
                        elif element.tag_name == "input":
                            element.clear()
                            element.send_keys(str(mes))
                            logger.info(f"✅ Mês preenchido: {mes}")
                            mes_preenchido = True
                            break
                    except (NoSuchElementException, ElementNotInteractableException):
                        continue
            
            if not mes_preenchido:
                logger.warning("⚠️ Campo de mês não encontrado - tentando método alternativo")
                # Tentar encontrar selects restantes
                try:
                    selects = self.driver.find_elements(By.TAG_NAME, "select")
                    for select_elem in selects:
                        try:
                            select = Select(select_elem)
                            # Tentar encontrar opção com o mês
                            for opt in select.options:
                                if str(mes) in opt.text or f"{mes:02d}" in opt.text:
                                    select.select_by_visible_text(opt.text)
                                    logger.info(f"✅ Mês selecionado via busca: {mes}")
                                    mes_preenchido = True
                                    break
                            if mes_preenchido:
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Erro ao buscar selects para mês: {e}")
            
            # Se ainda não encontrou, tentar salvar HTML para análise
            if not ano_preenchido or not mes_preenchido:
                logger.info("💡 Salvando HTML da página para análise...")
                try:
                    html_path = self.data_dir / "pagina_html_debug.html"
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info(f"   HTML salvo em: {html_path}")
                    
                    # Listar elementos interativos encontrados
                    logger.info("   Elementos interativos encontrados:")
                    try:
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        logger.info(f"      - {len(inputs)} inputs")
                        for i, inp in enumerate(inputs[:5]):  # Mostrar apenas os 5 primeiros
                            try:
                                logger.info(f"        Input {i+1}: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")
                            except:
                                pass
                    except:
                        pass
                    
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        logger.info(f"      - {len(buttons)} buttons")
                        for i, btn in enumerate(buttons[:5]):
                            try:
                                logger.info(f"        Button {i+1}: text={btn.text[:30]}, class={btn.get_attribute('class')}")
                            except:
                                pass
                    except:
                        pass
                except Exception as e:
                    logger.debug(f"Erro ao salvar HTML: {e}")
            
            # Tentar encontrar e preencher campo de tipo de operação
            tipo_preenchido = False
            if tipo_operacao != "Ambos":
                for selector in selectors_tipo:
                    try:
                        if selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        select = Select(element)
                        # Tentar diferentes valores
                        for value in [tipo_operacao, tipo_operacao.upper(), tipo_operacao.lower()]:
                            try:
                                select.select_by_visible_text(value)
                                logger.info(f"✅ Tipo de operação selecionado: {tipo_operacao}")
                                tipo_preenchido = True
                                break
                            except:
                                continue
                        
                        if tipo_preenchido:
                            break
                    except (NoSuchElementException, ElementNotInteractableException):
                        continue
            
            # Tentar marcar o checkbox "Detalhar por mês" se existir
            try:
                checkbox_selectors = [
                    "//label[contains(text(), 'Detalhar por mês')]/preceding-sibling::input[@type='checkbox']",
                    "//label[contains(text(), 'Detalhar por mês')]/following::input[@type='checkbox'][1]",
                    "//input[@type='checkbox' and contains(@name, 'detalhar')]",
                    "//input[@type='checkbox' and contains(@id, 'detalhar')]",
                ]
                
                for selector in checkbox_selectors:
                    try:
                        checkbox = self.driver.find_element(By.XPATH, selector)
                        if not checkbox.is_selected():
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            logger.info("✅ Checkbox 'Detalhar por mês' marcado")
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Erro ao marcar checkbox: {e}")
            
            # Preencher a seção "Filtros" - selecionar TODAS as opções
            logger.info("Preenchendo seção de Filtros com todas as opções...")
            try:
                # Procurar pelo campo de filtros
                filtros_selectors = [
                    "//label[contains(text(), 'Filtros')]/following::input[1]",
                    "//input[contains(@placeholder, 'filtros') or contains(@placeholder, 'Filtros')]",
                    "//input[contains(@placeholder, 'Selecione os filtros')]",
                    "//div[contains(@class, 'filtros')]//input",
                    "//button[contains(text(), 'Filtros')]",
                ]
                
                filtros_preenchidos = False
                for selector in filtros_selectors:
                    try:
                        filtro_element = self.driver.find_element(By.XPATH, selector)
                        if filtro_element.is_displayed():
                            # Clicar no campo para abrir seletor/modal
                            self.driver.execute_script("arguments[0].click();", filtro_element)
                            logger.info("✅ Campo de Filtros clicado")
                            time.sleep(3)  # Aguardar modal/seletor abrir
                            
                            # Tentar selecionar TODAS as opções disponíveis
                            try:
                                # Aguardar modal/seletor aparecer completamente
                                time.sleep(2)
                                
                                # Procurar por diferentes tipos de elementos selecionáveis
                                # 1. Checkboxes
                                checkboxes = self.driver.find_elements(By.XPATH, 
                                    "//input[@type='checkbox']"
                                )
                                
                                opcoes_selecionadas = 0
                                for checkbox in checkboxes:
                                    try:
                                        if checkbox.is_displayed():
                                            # Verificar se já está selecionado
                                            is_selected = checkbox.is_selected() or checkbox.get_attribute("checked") == "true"
                                            if not is_selected:
                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                                                time.sleep(0.3)
                                                # Tentar clicar de várias formas
                                                try:
                                                    checkbox.click()
                                                except:
                                                    try:
                                                        self.driver.execute_script("arguments[0].click();", checkbox)
                                                    except:
                                                        # Tentar clicar no label associado
                                                        try:
                                                            checkbox_id = checkbox.get_attribute("id")
                                                            if checkbox_id:
                                                                label = self.driver.find_element(By.XPATH, f"//label[@for='{checkbox_id}']")
                                                                label.click()
                                                        except:
                                                            continue
                                                
                                                # Verificar se foi selecionado
                                                time.sleep(0.2)
                                                if checkbox.is_selected() or checkbox.get_attribute("checked") == "true":
                                                    try:
                                                        label = self.driver.find_element(By.XPATH, f"//label[@for='{checkbox.get_attribute('id')}']")
                                                        logger.debug(f"   Selecionado: {label.text[:50]}")
                                                    except:
                                                        pass
                                                    opcoes_selecionadas += 1
                                    except Exception as e:
                                        logger.debug(f"Erro ao selecionar checkbox: {e}")
                                        continue
                                
                                # 2. Tentar também selecionar via botões ou links se houver
                                try:
                                    # Procurar botões "Selecionar todos" ou "Marcar todos"
                                    selecionar_todos_buttons = self.driver.find_elements(By.XPATH,
                                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar todos')] | "
                                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'marcar todos')] | "
                                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar todos')]"
                                    )
                                    
                                    for btn in selecionar_todos_buttons:
                                        if btn.is_displayed():
                                            self.driver.execute_script("arguments[0].click();", btn)
                                            logger.info("✅ Botão 'Selecionar todos' clicado")
                                            time.sleep(1)
                                            break
                                except:
                                    pass
                                
                                if opcoes_selecionadas > 0:
                                    logger.info(f"✅ {opcoes_selecionadas} opção(ões) de Filtros selecionada(s)")
                                else:
                                    logger.warning("⚠️ Nenhuma opção de Filtros foi selecionada - pode estar vazio ou já selecionado")
                                
                                # Procurar botão de confirmar/aplicar
                                confirmar_buttons = self.driver.find_elements(By.XPATH,
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirmar')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aplicar')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar')] | "
                                    "//button[@type='submit']"
                                )
                                
                                if confirmar_buttons:
                                    for btn in confirmar_buttons:
                                        if btn.is_displayed():
                                            self.driver.execute_script("arguments[0].click();", btn)
                                            logger.info("✅ Botão de confirmar Filtros clicado")
                                            time.sleep(2)
                                            break
                                else:
                                    # Se não houver botão de confirmar, tentar fechar com ESC ou clicar fora
                                    try:
                                        from selenium.webdriver.common.keys import Keys
                                        filtro_element.send_keys(Keys.ESCAPE)
                                        time.sleep(1)
                                    except:
                                        # Tentar clicar fora do modal
                                        try:
                                            body = self.driver.find_element(By.TAG_NAME, "body")
                                            body.click()
                                            time.sleep(1)
                                        except:
                                            pass
                                
                            except Exception as e:
                                logger.debug(f"Erro ao selecionar opções de Filtros: {e}")
                                import traceback
                                logger.debug(traceback.format_exc())
                                # Tentar fechar modal
                                try:
                                    from selenium.webdriver.common.keys import Keys
                                    filtro_element.send_keys(Keys.ESCAPE)
                                except:
                                    pass
                            
                            filtros_preenchidos = True
                            break
                    except:
                        continue
                
                if not filtros_preenchidos:
                    logger.warning("⚠️ Campo de Filtros não encontrado")
            except Exception as e:
                logger.debug(f"Erro ao preencher Filtros: {e}")
            
            # Preencher a seção "Detalhamento" - selecionar TODAS as opções
            logger.info("Preenchendo seção de Detalhamento com todas as opções...")
            try:
                detalhamento_selectors = [
                    "//label[contains(text(), 'Detalhamento')]/following::input[1]",
                    "//input[contains(@placeholder, 'Detalhamento')]",
                    "//input[contains(@placeholder, 'colunas')]",
                    "//div[contains(@class, 'detalhamento')]//input",
                ]
                
                detalhamento_preenchido = False
                for selector in detalhamento_selectors:
                    try:
                        detalhamento_element = self.driver.find_element(By.XPATH, selector)
                        if detalhamento_element.is_displayed():
                            # Clicar no campo para abrir seletor/modal
                            self.driver.execute_script("arguments[0].click();", detalhamento_element)
                            logger.info("✅ Campo de Detalhamento clicado")
                            time.sleep(3)  # Aguardar modal/seletor abrir
                            
                            # Tentar selecionar TODAS as opções disponíveis
                            try:
                                # Aguardar modal/seletor aparecer completamente
                                time.sleep(2)
                                
                                # Procurar por diferentes tipos de elementos selecionáveis
                                # 1. Checkboxes
                                checkboxes = self.driver.find_elements(By.XPATH, 
                                    "//input[@type='checkbox']"
                                )
                                
                                opcoes_selecionadas = 0
                                for checkbox in checkboxes:
                                    try:
                                        if checkbox.is_displayed():
                                            # Verificar se já está selecionado
                                            is_selected = checkbox.is_selected() or checkbox.get_attribute("checked") == "true"
                                            if not is_selected:
                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                                                time.sleep(0.3)
                                                # Tentar clicar de várias formas
                                                try:
                                                    checkbox.click()
                                                except:
                                                    try:
                                                        self.driver.execute_script("arguments[0].click();", checkbox)
                                                    except:
                                                        # Tentar clicar no label associado
                                                        try:
                                                            checkbox_id = checkbox.get_attribute("id")
                                                            if checkbox_id:
                                                                label = self.driver.find_element(By.XPATH, f"//label[@for='{checkbox_id}']")
                                                                label.click()
                                                        except:
                                                            continue
                                                
                                                # Verificar se foi selecionado
                                                time.sleep(0.2)
                                                if checkbox.is_selected() or checkbox.get_attribute("checked") == "true":
                                                    try:
                                                        label = self.driver.find_element(By.XPATH, f"//label[@for='{checkbox.get_attribute('id')}']")
                                                        logger.debug(f"   Selecionado: {label.text[:50]}")
                                                    except:
                                                        pass
                                                    opcoes_selecionadas += 1
                                    except Exception as e:
                                        logger.debug(f"Erro ao selecionar checkbox: {e}")
                                        continue
                                
                                # 2. Tentar também selecionar via botões ou links se houver
                                try:
                                    # Procurar botões "Selecionar todos" ou "Marcar todos"
                                    selecionar_todos_buttons = self.driver.find_elements(By.XPATH,
                                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar todos')] | "
                                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'marcar todos')] | "
                                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar todos')]"
                                    )
                                    
                                    for btn in selecionar_todos_buttons:
                                        if btn.is_displayed():
                                            self.driver.execute_script("arguments[0].click();", btn)
                                            logger.info("✅ Botão 'Selecionar todos' clicado")
                                            time.sleep(1)
                                            break
                                except:
                                    pass
                                
                                if opcoes_selecionadas > 0:
                                    logger.info(f"✅ {opcoes_selecionadas} opção(ões) de Detalhamento selecionada(s)")
                                else:
                                    logger.warning("⚠️ Nenhuma opção de Detalhamento foi selecionada - pode estar vazio ou já selecionado")
                                
                                # Procurar botão de confirmar/aplicar
                                confirmar_buttons = self.driver.find_elements(By.XPATH,
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirmar')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aplicar')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | "
                                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'selecionar')] | "
                                    "//button[@type='submit']"
                                )
                                
                                if confirmar_buttons:
                                    for btn in confirmar_buttons:
                                        if btn.is_displayed():
                                            self.driver.execute_script("arguments[0].click();", btn)
                                            logger.info("✅ Botão de confirmar Detalhamento clicado")
                                            time.sleep(2)
                                            break
                                else:
                                    # Se não houver botão de confirmar, tentar fechar com ESC ou clicar fora
                                    try:
                                        from selenium.webdriver.common.keys import Keys
                                        detalhamento_element.send_keys(Keys.ESCAPE)
                                        time.sleep(1)
                                    except:
                                        # Tentar clicar fora do modal
                                        try:
                                            body = self.driver.find_element(By.TAG_NAME, "body")
                                            body.click()
                                            time.sleep(1)
                                        except:
                                            pass
                                
                            except Exception as e:
                                logger.debug(f"Erro ao selecionar opções de Detalhamento: {e}")
                                import traceback
                                logger.debug(traceback.format_exc())
                                # Tentar fechar modal
                                try:
                                    from selenium.webdriver.common.keys import Keys
                                    detalhamento_element.send_keys(Keys.ESCAPE)
                                except:
                                    pass
                            
                            detalhamento_preenchido = True
                            break
                    except:
                        continue
                
                if not detalhamento_preenchido:
                    logger.warning("⚠️ Campo de Detalhamento não encontrado")
            except Exception as e:
                logger.debug(f"Erro ao preencher Detalhamento: {e}")
            
            # Verificar seção "$ Valores" - marcar TODAS as opções disponíveis
            logger.info("Preenchendo seção de Valores com todas as opções...")
            try:
                # Procurar todos os checkboxes na seção de Valores
                valores_checkboxes = self.driver.find_elements(By.XPATH,
                    "//div[contains(., 'Valores')]//input[@type='checkbox'] | "
                    "//label[contains(text(), 'Valor')]/preceding-sibling::input[@type='checkbox'] | "
                    "//label[contains(text(), 'Valor')]/following::input[@type='checkbox'][1] | "
                    "//label[contains(text(), 'Quilograma')]/preceding-sibling::input[@type='checkbox'] | "
                    "//label[contains(text(), 'Quilograma')]/following::input[@type='checkbox'][1]"
                )
                
                opcoes_marcadas = 0
                for checkbox in valores_checkboxes:
                    try:
                        if checkbox.is_displayed() and not checkbox.is_selected():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                            time.sleep(0.2)
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            # Tentar obter o label associado
                            try:
                                label = self.driver.find_element(By.XPATH, f"//label[@for='{checkbox.get_attribute('id')}']")
                                logger.info(f"✅ Checkbox marcado: {label.text}")
                            except:
                                logger.info("✅ Checkbox de Valores marcado")
                            opcoes_marcadas += 1
                    except:
                        continue
                
                if opcoes_marcadas > 0:
                    logger.info(f"✅ Total de {opcoes_marcadas} opção(ões) de Valores marcada(s)")
                else:
                    logger.info("ℹ️ Nenhuma opção adicional de Valores encontrada para marcar")
            except Exception as e:
                logger.debug(f"Erro ao preencher Valores: {e}")
            
            time.sleep(2)  # Aguardar filtros serem aplicados
            
            # Após preencher filtros, pode ser necessário clicar em "Buscar" ou "Consultar"
            logger.info("Procurando botão 'Buscar' ou 'Consultar'...")
            buscar_clicado = False
            try:
                # Primeiro, tentar encontrar o botão "Consultar" diretamente pela lista de botões
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in all_buttons:
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.strip().lower()
                                if "consultar" in btn_text or "buscar" in btn_text or "pesquisar" in btn_text:
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                    time.sleep(0.5)
                                    try:
                                        btn.click()
                                    except:
                                        self.driver.execute_script("arguments[0].click();", btn)
                                    logger.info(f"✅ Botão '{btn.text.strip()}' clicado")
                                    buscar_clicado = True
                                    logger.info("Aguardando resultados carregarem...")
                                    time.sleep(8)  # Aguardar resultados carregarem (pode demorar)
                                    break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Erro ao procurar botão na lista: {e}")
                
                # Se não encontrou, tentar seletores
                if not buscar_clicado:
                    buscar_selectors = [
                        "//button[contains(text(), 'Consultar')]",
                        "//button[normalize-space(text())='Consultar']",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consultar')]",
                        "//button[contains(text(), 'Buscar')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buscar')]",
                        "button[class*='primary']",
                    ]
                    
                    for selector in buscar_selectors:
                        try:
                            if selector.startswith("//"):
                                btn = self.driver.find_element(By.XPATH, selector)
                            else:
                                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            if btn.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(0.5)
                                try:
                                    btn.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                logger.info(f"✅ Botão '{btn.text.strip()}' clicado (via seletor)")
                                buscar_clicado = True
                                logger.info("Aguardando resultados carregarem...")
                                time.sleep(8)  # Aguardar resultados carregarem (pode demorar)
                                break
                        except:
                            continue
                
                if not buscar_clicado:
                    logger.warning("⚠️ Botão 'Buscar' não encontrado - pode não ser necessário")
            except Exception as e:
                logger.debug(f"Erro ao procurar botão buscar: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao preencher filtros: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def _clicar_botao_download(self, preferir_csv: bool = True) -> bool:
        """
        Clica no botão de download/exportar CSV.
        
        Args:
            preferir_csv: Se True, tenta encontrar botão CSV antes de Excel
        
        Returns:
            True se o botão foi clicado com sucesso
        """
        try:
            logger.info("Procurando botão de download...")
            
            # Aguardar um pouco para garantir que a página está pronta
            # Se foi clicado em "Buscar", aguardar mais tempo para resultados aparecerem
            time.sleep(3)
            
            # Estratégias expandidas para encontrar o botão de download
            selectors_download = [
                # Por texto (case insensitive)
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'exportar')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'csv')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'exportar')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'csv')]",
                # Por texto simples
                "//button[contains(text(), 'Download')]",
                "//button[contains(text(), 'Baixar')]",
                "//button[contains(text(), 'Exportar')]",
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'Download')]",
                "//a[contains(text(), 'Baixar')]",
                "//a[contains(text(), 'Exportar')]",
                "//a[contains(text(), 'CSV')]",
                # Por atributos
                "button[class*='download']",
                "button[id*='download']",
                "a[class*='download']",
                "a[id*='download']",
                "button[class*='export']",
                "a[class*='export']",
                "button[class*='csv']",
                "a[class*='csv']",
                # Por ícones ou classes comuns
                "button.btn-download",
                "a.btn-download",
                "button.export-btn",
                "a.export-btn",
                "button.btn-export",
                "a.btn-export",
                # Por tipo ou role
                "button[type='button']",
                "a[role='button']",
                # Qualquer elemento clicável que contenha texto relacionado
                "//*[@role='button' and (contains(text(), 'Download') or contains(text(), 'Baixar') or contains(text(), 'Exportar'))]",
                # Após buscar, pode aparecer um botão de exportar
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'exportar')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'exportar')]",
                # Botões Excel e CSV
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'csv')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'csv')]",
                "//button[contains(text(), 'Excel')]",
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'Excel')]",
                "//a[contains(text(), 'CSV')]",
                # Ícones de download
                "//*[contains(@class, 'download')]",
                "//*[contains(@class, 'export')]",
                "//*[contains(@aria-label, 'download')]",
                "//*[contains(@aria-label, 'Download')]",
                "//*[contains(@aria-label, 'baixar')]",
                "//*[contains(@aria-label, 'Baixar')]",
            ]
            
            for selector in selectors_download:
                try:
                    if selector.startswith("//"):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Verificar se está visível e clicável
                    if button.is_displayed():
                        # Scroll até o botão
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        
                        # Log do botão encontrado
                        try:
                            btn_text = button.text[:50] if button.text else "sem texto"
                            logger.info(f"   Botão encontrado: '{btn_text}'")
                            
                            # Se preferir CSV e encontrar Excel primeiro, continuar procurando CSV
                            if "excel" in btn_text.lower() and preferir_csv:
                                logger.info("   Botão Excel encontrado, mas procurando CSV primeiro...")
                                continue
                        except:
                            pass
                        
                        # Tentar clicar
                        try:
                            button.click()
                            logger.info("✅ Botão de download clicado")
                            # Aguardar um pouco após clicar para garantir que o download iniciou
                            time.sleep(2)
                            return True
                        except Exception as e:
                            # Tentar via JavaScript se clique normal falhar
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                logger.info("✅ Botão de download clicado (via JavaScript)")
                                # Aguardar um pouco após clicar
                                time.sleep(2)
                                return True
                            except Exception as e2:
                                logger.debug(f"Erro ao clicar: {e2}")
                                continue
                        
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
                except Exception as e:
                    logger.debug(f"Erro ao tentar seletor {selector}: {e}")
                    continue
            
            logger.warning("⚠️ Botão de download não encontrado")
            
            # Listar todos os botões visíveis para debug
            try:
                logger.info("💡 Listando todos os botões visíveis na página...")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                visible_buttons = [btn for btn in all_buttons if btn.is_displayed()]
                logger.info(f"   Total de {len(visible_buttons)} botão(ões) visível(is):")
                for i, btn in enumerate(visible_buttons[:10], 1):  # Mostrar até 10
                    try:
                        btn_text = btn.text.strip()[:40] if btn.text else "sem texto"
                        btn_class = btn.get_attribute("class")[:40] if btn.get_attribute("class") else "sem classe"
                        logger.info(f"      {i}. Texto: '{btn_text}' | Classe: {btn_class}")
                    except:
                        pass
                
                # Também procurar por links que possam ser de download
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                download_links = []
                for link in all_links:
                    try:
                        if link.is_displayed():
                            href = link.get_attribute("href") or ""
                            text = link.text.strip()[:40] if link.text else ""
                            if "csv" in href.lower() or "download" in href.lower() or "export" in href.lower():
                                download_links.append((text, href))
                    except:
                        continue
                
                if download_links:
                    logger.info(f"   Encontrado(s) {len(download_links)} link(s) que podem ser de download:")
                    for text, href in download_links[:5]:
                        logger.info(f"      - '{text}': {href[:80]}")
            except Exception as e:
                logger.debug(f"Erro ao listar botões: {e}")
            
            logger.info("💡 Tentando capturar screenshot para debug...")
            try:
                screenshot_path = self.data_dir / "screenshot.png"
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"   Screenshot salvo em: {screenshot_path}")
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao clicar no botão de download: {e}")
            return False
    
    def _aguardar_download(self, timeout: int = 120) -> Optional[Path]:
        """
        Aguarda o download ser concluído.
        
        Args:
            timeout: Tempo máximo de espera em segundos
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        try:
            logger.info("Aguardando download...")
            
            # Obter diretório de Downloads padrão do usuário
            downloads_dir = Path.home() / "Downloads"
            
            # Listar arquivos antes do download (CSV e XLSX) em ambos os diretórios
            arquivos_antes_csv = set(self.data_dir.glob("*.csv"))
            arquivos_antes_xlsx = set(self.data_dir.glob("*.xlsx"))
            arquivos_antes_xls = set(self.data_dir.glob("*.xls"))
            
            # Também verificar Downloads padrão
            if downloads_dir.exists():
                arquivos_antes_csv.update(downloads_dir.glob("*.csv"))
                arquivos_antes_xlsx.update(downloads_dir.glob("*.xlsx"))
                arquivos_antes_xls.update(downloads_dir.glob("*.xls"))
            
            # Registrar timestamp de início
            timestamp_inicio = time.time()
            
            # Aguardar novo arquivo aparecer
            inicio = time.time()
            tentativas = 0
            while time.time() - inicio < timeout:
                # Verificar CSV no diretório configurado
                arquivos_depois_csv = set(self.data_dir.glob("*.csv"))
                novos_csv = arquivos_depois_csv - arquivos_antes_csv
                
                # Verificar XLSX no diretório configurado
                arquivos_depois_xlsx = set(self.data_dir.glob("*.xlsx"))
                novos_xlsx = arquivos_depois_xlsx - arquivos_antes_xlsx
                
                # Verificar XLS no diretório configurado
                arquivos_depois_xls = set(self.data_dir.glob("*.xls"))
                novos_xls = arquivos_depois_xls - arquivos_antes_xls
                
                todos_novos = list(novos_csv) + list(novos_xlsx) + list(novos_xls)
                
                # Também verificar Downloads padrão durante o loop
                if downloads_dir.exists():
                    try:
                        novos_csv_downloads = set(downloads_dir.glob("*.csv")) - arquivos_antes_csv
                        novos_xlsx_downloads = set(downloads_dir.glob("*.xlsx")) - arquivos_antes_xlsx
                        novos_xls_downloads = set(downloads_dir.glob("*.xls")) - arquivos_antes_xls
                        todos_novos.extend(list(novos_csv_downloads) + list(novos_xlsx_downloads) + list(novos_xls_downloads))
                    except Exception as e:
                        logger.debug(f"Erro ao verificar Downloads durante loop: {e}")
                
                # Também verificar arquivos modificados recentemente (últimos 30 segundos)
                try:
                    arquivos_recentes = []
                    for ext in ['*.csv', '*.xlsx', '*.xls']:
                        for arquivo in self.data_dir.glob(ext):
                            try:
                                # Verificar se foi modificado nos últimos 30 segundos
                                tempo_modificacao = arquivo.stat().st_mtime
                                if tempo_modificacao > timestamp_inicio - 5:  # 5 segundos antes do início
                                    if arquivo not in todos_novos:
                                        arquivos_recentes.append(arquivo)
                            except:
                                continue
                    
                    if arquivos_recentes:
                        todos_novos.extend(arquivos_recentes)
                        logger.info(f"   Encontrado(s) {len(arquivos_recentes)} arquivo(s) modificado(s) recentemente")
                except Exception as e:
                    logger.debug(f"Erro ao verificar arquivos recentes: {e}")
                
                if todos_novos:
                    # Verificar se o arquivo está completo (não está sendo escrito)
                    for arquivo in todos_novos:
                        try:
                            tamanho_antes = arquivo.stat().st_size
                            time.sleep(2)  # Aguardar mais tempo
                            tamanho_depois = arquivo.stat().st_size
                            
                            if tamanho_antes == tamanho_depois and tamanho_antes > 100:  # Mínimo 100 bytes
                                logger.success(f"✅ Download concluído: {arquivo.name} ({tamanho_antes:,} bytes)")
                                
                                # Se for XLSX, tentar converter para CSV ou manter como está
                                if arquivo.suffix.lower() in ['.xlsx', '.xls']:
                                    logger.info(f"   Arquivo Excel baixado - pode ser convertido para CSV depois")
                                
                                return arquivo
                        except Exception as e:
                            logger.debug(f"Erro ao verificar arquivo {arquivo}: {e}")
                            continue
                
                tentativas += 1
                if tentativas % 10 == 0:
                    logger.info(f"   Aguardando... ({int(time.time() - inicio)}s)")
                
                time.sleep(2)  # Verificar a cada 2 segundos
            
            logger.warning("⚠️ Timeout aguardando download")
            logger.info("💡 Verificando se algum arquivo foi baixado mesmo assim...")
            
            # Verificar novamente todos os arquivos no diretório configurado
            todos_arquivos = list(self.data_dir.glob("*.*"))
            if todos_arquivos:
                logger.info(f"   Arquivos encontrados no diretório: {len(todos_arquivos)}")
                # Ordenar por data de modificação (mais recente primeiro)
                todos_arquivos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for arquivo in todos_arquivos[:10]:  # Mostrar últimos 10
                    try:
                        tamanho = arquivo.stat().st_size
                        tempo_mod = time.time() - arquivo.stat().st_mtime
                        logger.info(f"      - {arquivo.name} ({tamanho:,} bytes, modificado há {int(tempo_mod)}s)")
                        
                        # Se foi modificado recentemente (últimos 2 minutos) e é CSV/XLSX, considerar como download
                        if tempo_mod < 120 and arquivo.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                            if tamanho > 100:  # Mínimo 100 bytes
                                logger.info(f"   ✅ Arquivo recente encontrado: {arquivo.name}")
                                return arquivo
                    except:
                        pass
            
            # Verificar também diretório de Downloads padrão do Windows
            try:
                downloads_dir = Path.home() / "Downloads"
                if downloads_dir.exists():
                    logger.info(f"   Verificando diretório de Downloads: {downloads_dir}")
                    arquivos_downloads = []
                    for ext in ['*.csv', '*.xlsx', '*.xls']:
                        for arquivo in downloads_dir.glob(ext):
                            try:
                                tempo_mod = time.time() - arquivo.stat().st_mtime
                                # Verificar se foi modificado após o início do download (últimos 5 minutos)
                                if tempo_mod < 300 and arquivo.stat().st_mtime > timestamp_inicio - 10:
                                    tamanho = arquivo.stat().st_size
                                    if tamanho > 100:  # Mínimo 100 bytes
                                        arquivos_downloads.append((arquivo, tempo_mod, tamanho))
                                        logger.info(f"      📥 Arquivo candidato: {arquivo.name} ({tamanho:,} bytes, há {int(tempo_mod)}s)")
                            except Exception as e:
                                logger.debug(f"Erro ao verificar {arquivo}: {e}")
                                continue
                    
                    if arquivos_downloads:
                        # Ordenar por tempo de modificação (mais recente primeiro)
                        arquivos_downloads.sort(key=lambda x: x[1])
                        arquivo_mais_recente, tempo_mod, tamanho = arquivos_downloads[0]
                        logger.success(f"   ✅ Arquivo encontrado em Downloads: {arquivo_mais_recente.name} ({tamanho:,} bytes)")
                        # Mover para o diretório de destino
                        try:
                            arquivo_destino = self.data_dir / arquivo_mais_recente.name
                            # Se já existe, adicionar timestamp
                            if arquivo_destino.exists():
                                timestamp = int(time.time())
                                arquivo_destino = self.data_dir / f"{arquivo_mais_recente.stem}_{timestamp}{arquivo_mais_recente.suffix}"
                            arquivo_mais_recente.rename(arquivo_destino)
                            logger.success(f"   ✅ Arquivo movido para: {arquivo_destino}")
                            return arquivo_destino
                        except Exception as e:
                            logger.warning(f"   ⚠️ Erro ao mover arquivo: {e}")
                            logger.info(f"   ℹ️ Retornando arquivo do diretório Downloads: {arquivo_mais_recente}")
                            return arquivo_mais_recente
                    else:
                        logger.info(f"   ℹ️ Nenhum arquivo CSV/XLSX recente encontrado em Downloads")
            except Exception as e:
                logger.debug(f"Erro ao verificar Downloads: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao aguardar download: {e}")
            return None
    
    def _converter_excel_para_csv(self, arquivo_excel: Path) -> Optional[Path]:
        """
        Converte arquivo Excel para CSV.
        
        Args:
            arquivo_excel: Caminho do arquivo Excel
        
        Returns:
            Caminho do arquivo CSV ou None se falhar
        """
        try:
            import pandas as pd
            
            logger.info(f"Convertendo {arquivo_excel.name} para CSV...")
            
            # Ler Excel
            df = pd.read_excel(arquivo_excel)
            
            # Criar nome do arquivo CSV
            arquivo_csv = arquivo_excel.with_suffix('.csv')
            
            # Salvar como CSV
            df.to_csv(arquivo_csv, index=False, encoding='utf-8', sep=';')
            
            logger.success(f"✅ Convertido para CSV: {arquivo_csv.name}")
            return arquivo_csv
            
        except ImportError:
            logger.warning("⚠️ pandas não disponível - não é possível converter Excel para CSV")
            logger.info("   Instale com: pip install pandas openpyxl")
            return None
        except Exception as e:
            logger.error(f"Erro ao converter Excel para CSV: {e}")
            return None
    
    def baixar_dados_por_link(
        self,
        link_consulta: str,
        headless: bool = True,
        preferir_csv: bool = True
    ) -> Optional[Path]:
        """
        Baixa dados do ComexStat usando um link de consulta direto.
        
        Args:
            link_consulta: URL completa da consulta (ex: https://comexstat.mdic.gov.br/pt/geral/142608)
            headless: Executar em modo headless (sem interface gráfica)
            preferir_csv: Se True, tenta baixar CSV antes de Excel
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        try:
            logger.info(f"Baixando dados usando link direto: {link_consulta}")
            
            # Inicializar driver
            self._init_driver(headless=headless)
            
            # Navegar diretamente para o link de consulta
            logger.info(f"Navegando para {link_consulta}...")
            self.driver.get(link_consulta)
            
            # Aguardar página carregar
            logger.info("Aguardando página carregar...")
            time.sleep(5)
            
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logger.info("✅ Página carregada")
            except:
                logger.warning("⚠️ Timeout aguardando página carregar")
            
            time.sleep(3)  # Aguardar um pouco mais para JavaScript executar
            
            # PASSO 1: Clicar em "Consultar" para gerar a tabela
            logger.info("PASSO 1: Clicando em 'Consultar' para gerar a tabela...")
            consultar_clicado = False
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = btn.text.strip().lower()
                            if "consultar" in btn_text or "buscar" in btn_text or "pesquisar" in btn_text:
                                logger.info(f"✅ Botão '{btn.text.strip()}' encontrado. Clicando...")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(0.5)
                                try:
                                    btn.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                consultar_clicado = True
                                logger.info("Aguardando tabela aparecer na tela...")
                                break
                    except Exception as e:
                        logger.debug(f"Erro ao verificar botão: {e}")
                        continue
                
                if not consultar_clicado:
                    logger.warning("⚠️ Botão 'Consultar' não encontrado - pode já estar carregado")
            except Exception as e:
                logger.error(f"Erro ao procurar botão Consultar: {e}")
            
            # PASSO 2: Aguardar a tabela aparecer na tela
            if consultar_clicado:
                logger.info("PASSO 2: Aguardando tabela aparecer na tela...")
                try:
                    # Aguardar até que uma tabela apareça na página
                    WebDriverWait(self.driver, 30).until(
                        lambda d: len(d.find_elements(By.TAG_NAME, "table")) > 0 or
                                 len(d.find_elements(By.CSS_SELECTOR, "[class*='table']")) > 0 or
                                 len(d.find_elements(By.CSS_SELECTOR, "[class*='result']")) > 0 or
                                 len(d.find_elements(By.CSS_SELECTOR, "[class*='data']")) > 0
                    )
                    logger.success("✅ Tabela apareceu na tela")
                    time.sleep(3)  # Aguardar um pouco mais para garantir que está totalmente carregada
                except TimeoutException:
                    logger.warning("⚠️ Timeout aguardando tabela - continuando mesmo assim")
                    time.sleep(5)  # Aguardar um tempo fixo mesmo se não detectar tabela
            
            # PASSO 3: Procurar e clicar no botão "Gerar link da consulta"
            logger.info("PASSO 3: Procurando botão 'Gerar link da consulta'...")
            link_gerado = None
            try:
                # Aguardar um pouco mais para garantir que todos os botões apareceram após a tabela
                time.sleep(2)
                
                # Procurar por botões que possam gerar o link - expandir busca
                link_button_selectors = [
                    # Por texto completo
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gerar link')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'link da consulta')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copiar link')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'compartilhar')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'link')]",
                    # Links também podem ser clicáveis
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gerar link')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'link da consulta')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copiar link')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'link')]",
                    # Por texto simples (case sensitive também)
                    "//button[contains(text(), 'Gerar link')]",
                    "//button[contains(text(), 'Link da consulta')]",
                    "//button[contains(text(), 'Copiar link')]",
                    "//button[contains(text(), 'Compartilhar')]",
                    "//a[contains(text(), 'Gerar link')]",
                    "//a[contains(text(), 'Link da consulta')]",
                    # Por atributos
                    "//button[@title='Gerar link']",
                    "//button[@aria-label='Gerar link']",
                    "//a[@title='Gerar link']",
                    "//a[@aria-label='Gerar link']",
                    # Por classes comuns
                    "//button[contains(@class, 'link')]",
                    "//a[contains(@class, 'link')]",
                    "//button[contains(@class, 'share')]",
                    "//a[contains(@class, 'share')]",
                ]
                
                link_button_encontrado = False
                for selector in link_button_selectors:
                    try:
                        btn_link = self.driver.find_element(By.XPATH, selector)
                        if btn_link.is_displayed() and btn_link.is_enabled():
                            btn_text = btn_link.text.strip()
                            logger.info(f"✅ Botão encontrado: '{btn_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn_link)
                            time.sleep(0.5)
                            try:
                                btn_link.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", btn_link)
                            link_button_encontrado = True
                            logger.info("Aguardando link ser gerado...")
                            time.sleep(1)  # Aguardar 1 segundo como solicitado
                            
                            # Usar sequência de teclas para navegar pelo popup de permissão
                            logger.info("   Navegando pelo popup de permissão usando teclado (TAB+TAB+ENTER)...")
                            try:
                                from selenium.webdriver.common.keys import Keys
                                
                                # Garantir que o foco está na página
                                body = self.driver.find_element(By.TAG_NAME, "body")
                                body.click()  # Clicar no body para garantir foco
                                time.sleep(0.2)
                                
                                # Pressionar TAB duas vezes para navegar até o botão "Permitir"
                                logger.info("   Pressionando TAB (1/2)...")
                                body.send_keys(Keys.TAB)
                                time.sleep(0.5)  # Aguardar um pouco mais entre as teclas
                                
                                logger.info("   Pressionando TAB (2/2)...")
                                body.send_keys(Keys.TAB)
                                time.sleep(0.5)
                                
                                # Pressionar ENTER para confirmar "Permitir"
                                logger.info("   Pressionando ENTER para confirmar...")
                                body.send_keys(Keys.ENTER)
                                logger.success("   ✅ Sequência de teclas executada (TAB+TAB+ENTER)")
                                time.sleep(3)  # Aguardar popup fechar e link ser copiado
                            except Exception as e:
                                logger.warning(f"   ⚠️ Erro ao executar sequência de teclas: {e}")
                                import traceback
                                logger.debug(traceback.format_exc())
                            
                            # Verificar se apareceu algum modal ou popup
                            try:
                                modals = self.driver.find_elements(By.CSS_SELECTOR, "[class*='modal'], [class*='dialog'], [class*='popup']")
                                if modals:
                                    logger.info(f"   Modal/popup detectado após clicar no botão")
                            except:
                                pass
                            
                            break
                    except:
                        continue
                
                if not link_button_encontrado:
                    # Tentar método alternativo: procurar todos os botões e links visíveis
                    logger.info("💡 Tentando método alternativo: procurar todos os botões e links visíveis...")
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    all_elements = list(all_buttons) + list(all_links)
                    
                    # Listar todos os botões visíveis para debug
                    logger.info("   Listando todos os botões/links visíveis:")
                    elementos_candidatos = []
                    for elem in all_elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                elem_text = elem.text.strip()
                                if not elem_text:  # Ignorar elementos sem texto
                                    continue
                                
                                elem_text_lower = elem_text.lower()
                                logger.info(f"      - '{elem_text}' (tag: {elem.tag_name})")
                                
                                # PRIMEIRO: Verificar palavras de exclusão - se contém qualquer uma, IGNORAR completamente
                                palavras_excluir = ["contraste", "acessibilidade", "menu", "voltar", "limpar", "consultar", "mudar", "alto", "modo"]
                                if any(palavra_excluir in elem_text_lower for palavra_excluir in palavras_excluir):
                                    logger.debug(f"      ❌ Ignorado (contém palavra de exclusão): '{elem_text}'")
                                    continue
                                
                                # SEGUNDO: OBRIGATÓRIO que contenha "link"
                                if "link" not in elem_text_lower:
                                    continue
                                
                                # TERCEIRO: Verificar palavras complementares
                                palavras_complementares = ["gerar", "consult", "copiar", "compartilhar"]
                                if any(palavra_comp in elem_text_lower for palavra_comp in palavras_complementares):
                                    # Prioridade máxima: contém "link" + palavra complementar
                                    elementos_candidatos.insert(0, (elem, elem_text))
                                    logger.info(f"      ✅ Candidato de ALTA PRIORIDADE: '{elem_text}'")
                                elif "link" in elem_text_lower:
                                    # Prioridade menor: só contém "link"
                                    elementos_candidatos.append((elem, elem_text))
                                    logger.info(f"      ✅ Candidato de BAIXA PRIORIDADE: '{elem_text}'")
                        except Exception as e:
                            logger.debug(f"Erro ao verificar elemento: {e}")
                            continue
                    
                    # Tentar clicar nos candidatos
                    for elem, elem_text in elementos_candidatos:
                        try:
                            logger.info(f"   Tentando clicar em: '{elem_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                            time.sleep(0.5)
                            try:
                                elem.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", elem)
                            logger.info("   Clicado! Aguardando link ser gerado...")
                            time.sleep(1)  # Aguardar 1 segundo como solicitado
                            
                            # Usar sequência de teclas para navegar pelo popup de permissão
                            logger.info("   Navegando pelo popup de permissão usando teclado (TAB+TAB+ENTER)...")
                            try:
                                from selenium.webdriver.common.keys import Keys
                                
                                # Garantir que o foco está na página
                                body = self.driver.find_element(By.TAG_NAME, "body")
                                body.click()  # Clicar no body para garantir foco
                                time.sleep(0.2)
                                
                                # Pressionar TAB duas vezes para navegar até o botão "Permitir"
                                logger.info("   Pressionando TAB (1/2)...")
                                body.send_keys(Keys.TAB)
                                time.sleep(0.5)  # Aguardar um pouco mais entre as teclas
                                
                                logger.info("   Pressionando TAB (2/2)...")
                                body.send_keys(Keys.TAB)
                                time.sleep(0.5)
                                
                                # Pressionar ENTER para confirmar "Permitir"
                                logger.info("   Pressionando ENTER para confirmar...")
                                body.send_keys(Keys.ENTER)
                                logger.success("   ✅ Sequência de teclas executada (TAB+TAB+ENTER)")
                                time.sleep(3)  # Aguardar popup fechar e link ser copiado
                            except Exception as e:
                                logger.warning(f"   ⚠️ Erro ao executar sequência de teclas: {e}")
                                import traceback
                                logger.debug(traceback.format_exc())
                                # Tentar método alternativo de detecção do popup
                                logger.info("   Tentando método alternativo de detecção do popup...")
                            
                            # Verificar se apareceu solicitação de permissão do Google/Chrome (método alternativo)
                            logger.info("   Verificando se há solicitação de permissão do Chrome...")
                            
                            # Aguardar um pouco para o popup aparecer (se ainda não foi fechado)
                            time.sleep(1)
                            
                            for tentativa in range(5):  # Tentar até 5 vezes com intervalos maiores
                                try:
                                    # Procurar por popup de permissão do Chrome
                                    # Primeiro, procurar por todos os botões visíveis na página
                                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                                    btn_permitir_encontrado = False
                                    
                                    for btn in all_buttons:
                                        try:
                                            if btn.is_displayed():
                                                btn_text = btn.text.strip().lower()
                                                # Procurar especificamente pelo botão "Permitir"
                                                if btn_text == "permitir" or btn_text == "allow":
                                                    logger.info(f"   ✅ Botão de permissão encontrado: '{btn.text.strip()}'")
                                                    # Scroll até o botão
                                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                    time.sleep(0.5)
                                                    
                                                    # Tentar múltiplos métodos de clique
                                                    try:
                                                        btn.click()
                                                        logger.success("   ✅ Permissão concedida (método 1: click normal)")
                                                    except:
                                                        try:
                                                            self.driver.execute_script("arguments[0].click();", btn)
                                                            logger.success("   ✅ Permissão concedida (método 2: JavaScript click)")
                                                        except:
                                                            # Tentar via ActionChains
                                                            try:
                                                                from selenium.webdriver.common.action_chains import ActionChains
                                                                ActionChains(self.driver).move_to_element(btn).click().perform()
                                                                logger.success("   ✅ Permissão concedida (método 3: ActionChains)")
                                                            except Exception as e3:
                                                                logger.warning(f"   ⚠️ Erro ao clicar no botão: {e3}")
                                                    
                                                    btn_permitir_encontrado = True
                                                    time.sleep(2)  # Aguardar popup fechar
                                                    break
                                        except Exception as e:
                                            logger.debug(f"Erro ao verificar botão: {e}")
                                            continue
                                    
                                    if btn_permitir_encontrado:
                                        break
                                    
                                    # Se não encontrou, tentar procurar por XPath mais específicos
                                    permissoes_selectors = [
                                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permitir')]",
                                        "//button[contains(text(), 'Permitir')]",
                                        "//button[normalize-space(text())='Permitir']",
                                        "//button[normalize-space(text())='Permitir' and contains(@class, 'button')]",
                                    ]
                                    
                                    for perm_selector in permissoes_selectors:
                                        try:
                                            btn_permitir = self.driver.find_element(By.XPATH, perm_selector)
                                            if btn_permitir.is_displayed():
                                                logger.info(f"   ✅ Botão de permissão encontrado via XPath: '{btn_permitir.text.strip()}'")
                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_permitir)
                                                time.sleep(0.5)
                                                try:
                                                    btn_permitir.click()
                                                except:
                                                    self.driver.execute_script("arguments[0].click();", btn_permitir)
                                                logger.success("   ✅ Permissão concedida!")
                                                time.sleep(2)
                                                btn_permitir_encontrado = True
                                                break
                                        except:
                                            continue
                                    
                                    if btn_permitir_encontrado:
                                        break
                                    
                                    # Se não encontrou, aguardar mais um pouco e tentar novamente
                                    if tentativa < 4:
                                        logger.debug(f"   Tentativa {tentativa+1}/5: Popup não encontrado, aguardando...")
                                        time.sleep(2)
                                    
                                except Exception as e:
                                    logger.debug(f"Erro ao procurar botão de permissão (tentativa {tentativa+1}): {e}")
                                    if tentativa < 4:
                                        time.sleep(2)
                            
                            time.sleep(3)  # Aguardar mais um pouco após clicar
                            link_button_encontrado = True
                            break
                        except Exception as e:
                            logger.debug(f"Erro ao clicar em '{elem_text}': {e}")
                            continue
                
                # Verificar novamente se há popup de permissão após aguardar
                logger.info("   Verificando se há popup de permissão do Chrome...")
                time.sleep(1)  # Aguardar popup aparecer
                
                for tentativa_permissao in range(10):  # Tentar até 10 vezes (popup pode demorar para aparecer)
                    try:
                        # Procurar por todos os botões visíveis
                        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        btn_permitir_encontrado = False
                        
                        for btn in all_buttons:
                            try:
                                if btn.is_displayed():
                                    btn_text = btn.text.strip()
                                    btn_text_lower = btn_text.lower()
                                    
                                    # Procurar especificamente pelo botão "Permitir"
                                    if btn_text_lower == "permitir" or btn_text_lower == "allow":
                                        logger.info(f"   ✅ Popup de permissão encontrado! Botão: '{btn_text}'")
                                        
                                        # Scroll até o botão para garantir que está visível
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn)
                                        time.sleep(0.5)
                                        
                                        # Tentar múltiplos métodos de clique
                                        clicado = False
                                        try:
                                            btn.click()
                                            logger.success("   ✅ Permissão concedida (método 1: click normal)")
                                            clicado = True
                                        except Exception as e1:
                                            try:
                                                self.driver.execute_script("arguments[0].click();", btn)
                                                logger.success("   ✅ Permissão concedida (método 2: JavaScript click)")
                                                clicado = True
                                            except Exception as e2:
                                                try:
                                                    from selenium.webdriver.common.action_chains import ActionChains
                                                    ActionChains(self.driver).move_to_element(btn).click().perform()
                                                    logger.success("   ✅ Permissão concedida (método 3: ActionChains)")
                                                    clicado = True
                                                except Exception as e3:
                                                    logger.warning(f"   ⚠️ Erro ao clicar (tentativa {tentativa_permissao+1}): {e3}")
                                        
                                        if clicado:
                                            btn_permitir_encontrado = True
                                            time.sleep(3)  # Aguardar popup fechar e link ser copiado
                                            break
                            except Exception as e:
                                logger.debug(f"Erro ao verificar botão: {e}")
                                continue
                        
                        if btn_permitir_encontrado:
                            break
                        
                        # Se não encontrou, aguardar um pouco e tentar novamente
                        if tentativa_permissao < 9:
                            time.sleep(1)
                    except Exception as e:
                        logger.debug(f"Erro ao verificar popup (tentativa {tentativa_permissao+1}): {e}")
                        if tentativa_permissao < 9:
                            time.sleep(1)
                
                # PASSO 4: Capturar o link gerado
                logger.info("PASSO 4: Capturando o link gerado...")
                time.sleep(2)  # Aguardar um pouco mais para modal/popup aparecer
                
                # Capturar screenshot para debug
                try:
                    screenshot_path = self.data_dir / "screenshot_apos_gerar_link.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    logger.info(f"   Screenshot salvo: {screenshot_path}")
                except:
                    pass
                
                # Tentar várias formas de capturar o link:
                # 1. Procurar por input ou textarea com o link (pode estar em um modal)
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    logger.info(f"   Verificando {len(inputs)} inputs...")
                    for inp in inputs:
                        try:
                            if inp.is_displayed():
                                value = inp.get_attribute("value") or ""
                                if "comexstat.mdic.gov.br" in value and "/pt/geral/" in value:
                                    link_gerado = value.strip()
                                    logger.success(f"✅ Link encontrado em input: {link_gerado}")
                                    break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"Erro ao verificar inputs: {e}")
                
                # 2. Procurar por textarea
                if not link_gerado:
                    try:
                        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                        logger.info(f"   Verificando {len(textareas)} textareas...")
                        for ta in textareas:
                            try:
                                if ta.is_displayed():
                                    value = ta.get_attribute("value") or ta.text or ""
                                    if "comexstat.mdic.gov.br" in value and "/pt/geral/" in value:
                                        link_gerado = value.strip()
                                        logger.success(f"✅ Link encontrado em textarea: {link_gerado}")
                                        break
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Erro ao verificar textareas: {e}")
                
                # 3. Procurar por elementos com texto que contenha o link
                if not link_gerado:
                    try:
                        logger.info("   Procurando elementos com texto contendo link...")
                        # Procurar por divs, spans, etc. que possam conter o link
                        all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'comexstat.mdic.gov.br')]")
                        for elem in all_elements:
                            try:
                                if elem.is_displayed():
                                    text = elem.text or elem.get_attribute("textContent") or ""
                                    # Extrair URL do texto
                                    import re
                                    urls = re.findall(r'https?://[^\s]+comexstat\.mdic\.gov\.br[^\s]*', text)
                                    if urls:
                                        link_gerado = urls[0].strip()
                                        logger.success(f"✅ Link encontrado em elemento de texto: {link_gerado}")
                                        break
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Erro ao procurar elementos com texto: {e}")
                
                # 4. Verificar se o link foi copiado para a área de transferência (via JavaScript)
                if not link_gerado:
                    try:
                        logger.info("   Tentando ler da área de transferência...")
                        # Tentar ler da área de transferência usando JavaScript
                        link_clipboard = self.driver.execute_script("""
                            return navigator.clipboard.readText().catch(() => {
                                // Se falhar, tentar método alternativo
                                return null;
                            });
                        """)
                        if link_clipboard and "comexstat.mdic.gov.br" in link_clipboard:
                            link_gerado = link_clipboard.strip()
                            # Verificar se o link está completo (deve conter /pt/geral/)
                            if "/pt/geral/" in link_gerado:
                                logger.success(f"✅ Link completo encontrado na área de transferência: {link_gerado}")
                            else:
                                logger.warning(f"⚠️ Link incompleto na área de transferência: {link_gerado}")
                                # Tentar usar a URL atual se o link da área de transferência estiver incompleto
                                current_url = self.driver.current_url
                                if "/pt/geral/" in current_url:
                                    link_gerado = current_url
                                    logger.info(f"   Usando URL atual completa: {link_gerado}")
                                else:
                                    logger.warning(f"   URL atual também não contém /pt/geral/: {current_url}")
                    except Exception as e:
                        logger.debug(f"Erro ao ler área de transferência: {e}")
                
                # 5. Verificar URL atual (pode ter mudado após clicar)
                if not link_gerado:
                    current_url = self.driver.current_url
                    if "comexstat.mdic.gov.br" in current_url and "/pt/geral/" in current_url:
                        link_gerado = current_url
                        logger.info(f"ℹ️ Usando URL atual: {link_gerado}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar/capturar link: {e}")
                import traceback
                logger.debug(traceback.format_exc())
            
            # Se não conseguiu gerar o link, retornar None
            if not link_gerado:
                logger.error("❌ Não foi possível gerar ou capturar o link da consulta")
                return None
            
            # PASSO 5: Procurar e clicar no botão "Excel" na tela
            logger.info("PASSO 5: Procurando botão 'Excel' na tela...")
            time.sleep(2)  # Aguardar um pouco para a página estabilizar
            
            # Procurar especificamente pela palavra "Excel" na tela
            excel_encontrado = False
            try:
                # Procurar por botões/links que contenham "Excel"
                excel_selectors = [
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')]",
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'excel')]",
                    "//button[contains(text(), 'Excel')]",
                    "//a[contains(text(), 'Excel')]",
                ]
                
                for selector in excel_selectors:
                    try:
                        elementos_excel = self.driver.find_elements(By.XPATH, selector)
                        for elem in elementos_excel:
                            try:
                                if elem.is_displayed() and elem.is_enabled():
                                    elem_text = elem.text.strip()
                                    if "excel" in elem_text.lower():
                                        logger.info(f"   ✅ Botão 'Excel' encontrado: '{elem_text}'")
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                        time.sleep(0.5)
                                        try:
                                            elem.click()
                                        except:
                                            self.driver.execute_script("arguments[0].click();", elem)
                                        logger.success("   ✅ Botão Excel clicado!")
                                        excel_encontrado = True
                                        time.sleep(2)
                                        break
                            except Exception as e:
                                logger.debug(f"Erro ao clicar em elemento Excel: {e}")
                                continue
                        if excel_encontrado:
                            break
                    except Exception as e:
                        logger.debug(f"Erro ao procurar Excel com seletor '{selector}': {e}")
                        continue
                
                if not excel_encontrado:
                    logger.warning("   ⚠️ Botão Excel não encontrado, tentando método alternativo...")
                    # Método alternativo: usar _clicar_botao_download
                    if not self._clicar_botao_download(preferir_csv=False):
                        logger.error("   ❌ Não foi possível encontrar ou clicar no botão Excel")
                        return None
            except Exception as e:
                logger.error(f"   ❌ Erro ao procurar botão Excel: {e}")
                return None
                logger.warning("⚠️ Não foi possível clicar no botão de download")
                return None
            
            # Aguardar download
            arquivo = self._aguardar_download()
            
            # Se não encontrou arquivo, aguardar mais um pouco e verificar novamente
            if not arquivo:
                logger.info("Aguardando mais 30 segundos para download aparecer...")
                time.sleep(30)
                arquivo = self._aguardar_download(timeout=10)  # Verificação rápida
            
            # Se baixou Excel e preferir CSV, tentar converter
            if arquivo and arquivo.suffix.lower() in ['.xlsx', '.xls']:
                if preferir_csv:
                    arquivo_csv = self._converter_excel_para_csv(arquivo)
                    if arquivo_csv:
                        return arquivo_csv
                else:
                    logger.info(f"Arquivo Excel mantido: {arquivo.name}")
            
            return arquivo
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados por link: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def baixar_dados(
        self,
        ano: int,
        mes: int,
        tipo_operacao: str = "Ambos",
        headless: bool = True,
        preferir_csv: bool = True
    ) -> Optional[Path]:
        """
        Baixa dados do ComexStat para um mês específico.
        
        Args:
            ano: Ano dos dados
            mes: Mês dos dados (1-12)
            tipo_operacao: "Importação", "Exportação" ou "Ambos"
            headless: Executar em modo headless (sem interface gráfica)
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        try:
            # Inicializar driver
            self._init_driver(headless=headless)
            
            # Navegar para Dados Gerais
            if not self._navigate_to_dados_gerais():
                return None
            
            # Preencher filtros
            if not self._preencher_filtros(ano, mes, tipo_operacao):
                logger.warning("⚠️ Filtros podem não ter sido preenchidos corretamente")
            
            # Clicar em download
            if not self._clicar_botao_download(preferir_csv=preferir_csv):
                return None
            
            # Aguardar download
            arquivo = self._aguardar_download()
            
            # Se não encontrou arquivo, aguardar mais um pouco e verificar novamente
            if not arquivo:
                logger.info("Aguardando mais 30 segundos para download aparecer...")
                time.sleep(30)
                arquivo = self._aguardar_download(timeout=10)  # Verificação rápida
            
            # Se baixou Excel e preferir CSV, tentar converter
            if arquivo and arquivo.suffix.lower() in ['.xlsx', '.xls']:
                if preferir_csv:
                    arquivo_csv = self._converter_excel_para_csv(arquivo)
                    if arquivo_csv:
                        # Opcional: remover arquivo Excel original
                        # arquivo.unlink()
                        return arquivo_csv
                else:
                    logger.info(f"Arquivo Excel mantido: {arquivo.name}")
            
            return arquivo
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def baixar_meses_recentes(
        self,
        meses: int = 6,
        tipo_operacao: str = "Ambos",
        headless: bool = True
    ) -> List[Path]:
        """
        Baixa dados dos últimos N meses.
        
        Args:
            meses: Número de meses para baixar
            tipo_operacao: "Importação", "Exportação" ou "Ambos"
            headless: Executar em modo headless
        
        Returns:
            Lista de arquivos baixados
        """
        logger.info(f"Baixando dados dos últimos {meses} meses...")
        
        downloaded = []
        hoje = datetime.now()
        
        try:
            self._init_driver(headless=headless)
            
            for i in range(meses):
                data = hoje - timedelta(days=30 * i)
                ano = data.year
                mes = data.month
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Baixando {ano}-{mes:02d}...")
                logger.info(f"{'='*60}")
                
                # Navegar para a página (só na primeira vez)
                if i == 0:
                    if not self._navigate_to_dados_gerais():
                        continue
                else:
                    # Recarregar página para próximo mês
                    self.driver.refresh()
                    time.sleep(2)
                
                # Preencher filtros
                if not self._preencher_filtros(ano, mes, tipo_operacao):
                    logger.warning(f"⚠️ Pulando {ano}-{mes:02d} - erro ao preencher filtros")
                    continue
                
                # Clicar em download
                if not self._clicar_botao_download():
                    logger.warning(f"⚠️ Pulando {ano}-{mes:02d} - erro ao clicar em download")
                    continue
                
                # Aguardar download
                arquivo = self._aguardar_download()
                if arquivo:
                    downloaded.append(arquivo)
                    logger.success(f"✅ {ano}-{mes:02d} baixado com sucesso")
                else:
                    logger.warning(f"⚠️ Download de {ano}-{mes:02d} não concluído")
                
                # Delay entre downloads
                if i < meses - 1:
                    time.sleep(3)
        
        except Exception as e:
            logger.error(f"Erro durante download: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        finally:
            self._close_driver()
        
        logger.success(f"\n✅ Total de {len(downloaded)} arquivo(s) baixado(s)")
        return downloaded
    
    def __del__(self):
        """Garantir que o driver seja fechado."""
        self._close_driver()
