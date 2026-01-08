"""
Scraper para baixar arquivos CSV das bases de dados brutas do MDIC.
Acessa https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta
e baixa os arquivos CSV disponíveis.
"""
import aiohttp
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import csv
import io

from config import settings


class CSVDataScraper:
    """
    Scraper para baixar e processar arquivos CSV das bases de dados brutas do MDIC.
    """
    
    BASE_URL = "https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta"
    
    # URLs conhecidas dos arquivos CSV (podem ser atualizadas)
    CSV_BASE_URLS = {
        "importacao": "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_{ano}_{mes}.csv",
        "exportacao": "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_{ano}_{mes}.csv",
    }
    
    def __init__(self):
        self.data_dir = settings.data_dir / "csv_downloads"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutos para downloads grandes
        
    async def download_month_csv(
        self,
        ano: int,
        mes: int,
        tipo_operacao: str
    ) -> Optional[Path]:
        """
        Baixa arquivo CSV de um mês específico.
        
        Args:
            ano: Ano (ex: 2024)
            mes: Mês (1-12)
            tipo_operacao: 'Importação' ou 'Exportação'
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        tipo = "importacao" if tipo_operacao.lower() == "importação" else "exportacao"
        mes_str = f"{mes:02d}"
        
        # Tentar diferentes formatos de URL
        urls_to_try = [
            f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/{tipo.upper()}_{ano}_{mes_str}.csv",
            f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/{tipo.upper()}_{ano}{mes_str}.csv",
            f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/{tipo}_{ano}_{mes_str}.csv",
            f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/{tipo}_{ano}{mes_str}.csv",
        ]
        
        filename = f"{tipo}_{ano}_{mes_str}.csv"
        filepath = self.data_dir / filename
        
        # Se já existe, retornar
        if filepath.exists() and filepath.stat().st_size > 0:
            logger.info(f"Arquivo já existe: {filepath}")
            return filepath
        
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            for url in urls_to_try:
                try:
                    logger.info(f"Tentando baixar: {url}")
                    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                        if response.status == 200:
                            content_type = response.headers.get("content-type", "").lower()
                            if "csv" in content_type or "text" in content_type:
                                # Baixar arquivo
                                content = await response.read()
                                if len(content) > 100:  # Arquivo válido deve ter mais de 100 bytes
                                    filepath.write_bytes(content)
                                    logger.success(f"✅ Arquivo baixado: {filepath} ({len(content)} bytes)")
                                    return filepath
                                else:
                                    logger.warning(f"Arquivo muito pequeno: {len(content)} bytes")
                        else:
                            logger.debug(f"Status {response.status} para {url}")
                except Exception as e:
                    logger.debug(f"Erro ao baixar {url}: {e}")
                    continue
        
        logger.warning(f"⚠️ Não foi possível baixar CSV para {tipo} {ano}-{mes_str}")
        return None
    
    async def download_recent_months(
        self,
        meses: int = 24
    ) -> List[Path]:
        """
        Baixa arquivos CSV dos últimos N meses.
        
        Args:
            meses: Número de meses para baixar (padrão: 24)
        
        Returns:
            Lista de caminhos dos arquivos baixados
        """
        downloaded_files = []
        hoje = datetime.now()
        
        tipos = ["Importação", "Exportação"]
        
        for i in range(meses):
            data = hoje - timedelta(days=30 * i)
            ano = data.year
            mes = data.month
            
            for tipo in tipos:
                try:
                    filepath = await self.download_month_csv(ano, mes, tipo)
                    if filepath:
                        downloaded_files.append(filepath)
                    # Pequeno delay entre downloads
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Erro ao baixar {tipo} {ano}-{mes:02d}: {e}")
        
        logger.info(f"✅ Total de arquivos baixados: {len(downloaded_files)}")
        return downloaded_files
    
    def parse_csv_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Processa um arquivo CSV e retorna lista de registros.
        
        Args:
            filepath: Caminho do arquivo CSV
        
        Returns:
            Lista de dicionários com os dados
        """
        registros = []
        
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
                logger.error(f"Não foi possível ler {filepath} com nenhum encoding")
                return []
            
            # Ler CSV
            reader = csv.DictReader(io.StringIO(content), delimiter=';')
            
            for row in reader:
                # Normalizar nomes das colunas (remover espaços, converter para minúsculas)
                registro = {}
                for key, value in row.items():
                    # Normalizar chave
                    key_normalized = key.strip().lower().replace(' ', '_')
                    registro[key_normalized] = value.strip() if value else None
                
                registros.append(registro)
            
            logger.info(f"✅ Processados {len(registros)} registros de {filepath.name}")
            return registros
            
        except Exception as e:
            logger.error(f"Erro ao processar CSV {filepath}: {e}")
            return []
    
    async def get_available_files(self) -> List[Dict[str, Any]]:
        """
        Tenta descobrir quais arquivos CSV estão disponíveis.
        Faz requisições para verificar quais URLs retornam arquivos válidos.
        
        Returns:
            Lista de dicionários com informações dos arquivos disponíveis
        """
        available_files = []
        hoje = datetime.now()
        
        # Verificar últimos 24 meses
        for i in range(24):
            data = hoje - timedelta(days=30 * i)
            ano = data.year
            mes = data.month
            
            for tipo in ["importacao", "exportacao"]:
                url = f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/{tipo.upper()}_{ano}_{mes:02d}.csv"
                
                try:
                    connector = aiohttp.TCPConnector(ssl=False)
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), connector=connector) as session:
                        async with session.head(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                            if response.status == 200:
                                size = response.headers.get("content-length", "unknown")
                                available_files.append({
                                    "url": url,
                                    "tipo": tipo,
                                    "ano": ano,
                                    "mes": mes,
                                    "size": size
                                })
                except:
                    pass
        
        return available_files



