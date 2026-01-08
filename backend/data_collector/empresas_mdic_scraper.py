"""
Scraper para baixar e processar a Lista de Empresas Exportadoras e Importadoras do MDIC.
Esta lista contém CNPJ e nome das empresas, mas sem detalhamento por NCM.
"""
import aiohttp
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import csv
import io
import re

from config import settings


class EmpresasMDICScraper:
    """
    Scraper para a lista de empresas exportadoras e importadoras do MDIC.
    """
    
    BASE_URL = "https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas"
    
    # URLs conhecidas dos arquivos (podem variar)
    LISTA_EMPRESAS_URLS = [
        "https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/empresas-exportadoras-e-importadoras",
        "https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta",
    ]
    
    def __init__(self):
        self.data_dir = settings.data_dir / "empresas_mdic"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = aiohttp.ClientTimeout(total=300)
        
    async def buscar_urls_arquivos(self, ano: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Busca URLs dos arquivos de lista de empresas.
        
        Args:
            ano: Ano específico (None = ano atual)
        
        Returns:
            Lista de dicionários com informações dos arquivos
        """
        if ano is None:
            ano = datetime.now().year
        
        arquivos_encontrados = []
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            for base_url in self.LISTA_EMPRESAS_URLS:
                try:
                    async with session.get(base_url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Procurar links para arquivos CSV/XLSX
                            # Padrões comuns: empresas_exportadoras_2024.csv, lista_empresas_2024.xlsx
                            patterns = [
                                rf'href=["\']([^"\']*empresas?[^"\']*{ano}[^"\']*\.(csv|xlsx|xls))["\']',
                                rf'href=["\']([^"\']*lista[^"\']*empresas?[^"\']*{ano}[^"\']*\.(csv|xlsx|xls))["\']',
                                rf'href=["\']([^"\']*exportadoras?[^"\']*{ano}[^"\']*\.(csv|xlsx|xls))["\']',
                                rf'href=["\']([^"\']*importadoras?[^"\']*{ano}[^"\']*\.(csv|xlsx|xls))["\']',
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, html, re.IGNORECASE)
                                for match in matches:
                                    url = match[0] if isinstance(match, tuple) else match
                                    # Converter URL relativa para absoluta
                                    if url.startswith('/'):
                                        from urllib.parse import urljoin
                                        url = urljoin(base_url, url)
                                    elif not url.startswith('http'):
                                        url = f"{base_url}/{url}"
                                    
                                    arquivos_encontrados.append({
                                        "url": url,
                                        "ano": ano,
                                        "tipo": "empresas_mdic",
                                        "fonte": base_url
                                    })
                except Exception as e:
                    logger.debug(f"Erro ao buscar em {base_url}: {e}")
        
        return arquivos_encontrados
    
    async def download_arquivo(self, url: str, tipo: str = "exportadoras") -> Optional[Path]:
        """
        Baixa um arquivo de lista de empresas.
        
        Args:
            url: URL do arquivo
            tipo: Tipo ('exportadoras' ou 'importadoras')
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        filename = url.split('/')[-1]
        if not filename.endswith(('.csv', '.xlsx', '.xls')):
            filename = f"empresas_{tipo}_{datetime.now().year}.csv"
        
        filepath = self.data_dir / filename
        
        # Se já existe, retornar
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.info(f"Arquivo já existe: {filepath}")
            return filepath
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status == 200:
                        content = await response.read()
                        filepath.write_bytes(content)
                        logger.success(f"✅ Arquivo baixado: {filepath} ({len(content)} bytes)")
                        return filepath
                    else:
                        logger.warning(f"Status {response.status} para {url}")
        except Exception as e:
            logger.error(f"Erro ao baixar {url}: {e}")
        
        return None
    
    def parse_csv_empresas(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Processa arquivo CSV de empresas.
        
        Args:
            filepath: Caminho do arquivo CSV
        
        Returns:
            Lista de dicionários com dados das empresas
        """
        empresas = []
        
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    content = filepath.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.error(f"Não foi possível ler {filepath}")
                return []
            
            # Ler CSV
            reader = csv.DictReader(io.StringIO(content), delimiter=';')
            
            for row in reader:
                # Normalizar campos
                empresa = {}
                for key, value in row.items():
                    key_normalized = key.strip().lower().replace(' ', '_')
                    empresa[key_normalized] = value.strip() if value else None
                
                # Extrair campos importantes
                empresa_normalizada = {
                    "cnpj": self._normalizar_cnpj(empresa.get("cnpj") or empresa.get("cnpj_empresa") or ""),
                    "razao_social": empresa.get("razao_social") or empresa.get("nome_empresa") or empresa.get("empresa") or "",
                    "nome_fantasia": empresa.get("nome_fantasia") or empresa.get("fantasia") or "",
                    "uf": empresa.get("uf") or empresa.get("estado") or "",
                    "municipio": empresa.get("municipio") or empresa.get("cidade") or "",
                    "tipo_operacao": empresa.get("tipo") or empresa.get("tipo_operacao") or "",
                    "faixa_valor": empresa.get("faixa_valor") or empresa.get("valor_faixa") or "",
                    "ano": empresa.get("ano") or str(datetime.now().year),
                }
                
                # Validar CNPJ
                if empresa_normalizada["cnpj"] and len(empresa_normalizada["cnpj"]) == 14:
                    empresas.append(empresa_normalizada)
            
            logger.info(f"✅ Processadas {len(empresas)} empresas de {filepath.name}")
            return empresas
            
        except Exception as e:
            logger.error(f"Erro ao processar CSV {filepath}: {e}")
            return []
    
    def _normalizar_cnpj(self, cnpj: str) -> str:
        """Normaliza CNPJ removendo formatação."""
        if not cnpj:
            return ""
        cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
        return cnpj_limpo[:14]  # CNPJ tem 14 dígitos
    
    async def coletar_empresas(self, ano: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Coleta lista completa de empresas.
        
        Args:
            ano: Ano específico (None = ano atual)
        
        Returns:
            Lista de empresas
        """
        logger.info(f"Coletando lista de empresas do MDIC para {ano or 'ano atual'}")
        
        # Buscar URLs
        arquivos = await self.buscar_urls_arquivos(ano)
        
        if not arquivos:
            logger.warning("Nenhum arquivo encontrado. Tentando URLs conhecidas...")
            # Tentar URLs conhecidas diretamente
            ano_atual = ano or datetime.now().year
            urls_tentativas = [
                f"https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/empresas-exportadoras-e-importadoras/arquivos/empresas_exportadoras_{ano_atual}.csv",
                f"https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/empresas-exportadoras-e-importadoras/arquivos/empresas_importadoras_{ano_atual}.csv",
            ]
            
            for url in urls_tentativas:
                arquivos.append({
                    "url": url,
                    "ano": ano_atual,
                    "tipo": "empresas_mdic",
                    "fonte": "url_conhecida"
                })
        
        todas_empresas = []
        
        for arquivo_info in arquivos:
            url = arquivo_info["url"]
            tipo = "exportadoras" if "exportadora" in url.lower() else "importadoras"
            
            filepath = await self.download_arquivo(url, tipo)
            if filepath:
                empresas = self.parse_csv_empresas(filepath)
                todas_empresas.extend(empresas)
        
        logger.info(f"✅ Total de empresas coletadas: {len(todas_empresas)}")
        return todas_empresas



