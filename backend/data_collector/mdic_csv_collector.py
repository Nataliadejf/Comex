"""
Coletor completo de dados CSV do portal oficial do MDIC.
Baixa e processa todas as tabelas disponíveis em:
https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta
"""
import aiohttp
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import io
import csv

from config import settings


class MDICCSVCollector:
    """
    Coletor completo de dados CSV do portal oficial do MDIC.
    Baixa arquivos de importação/exportação e tabelas de correlação.
    """
    
    BASE_URL = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd"
    
    # URLs das tabelas de correlação
    CORRELATION_TABLES = {
        "ncm_sh": "https://balanca.economia.gov.br/balanca/bd/tabelas/NCM_SH.csv",
        "ncm_cgce": "https://balanca.economia.gov.br/balanca/bd/tabelas/NCM_CGCE.csv",
        "ncm_cuci": "https://balanca.economia.gov.br/balanca/bd/tabelas/NCM_CUCI.csv",
        "ncm_isic": "https://balanca.economia.gov.br/balanca/bd/tabelas/NCM_ISIC.csv",
        "paises": "https://balanca.economia.gov.br/balanca/bd/tabelas/PAIS.csv",
        "uf": "https://balanca.economia.gov.br/balanca/bd/tabelas/UF.csv",
        "via": "https://balanca.economia.gov.br/balanca/bd/tabelas/VIA.csv",
        "urf": "https://balanca.economia.gov.br/balanca/bd/tabelas/URF.csv",
    }
    
    def __init__(self):
        self.data_dir = settings.data_dir / "mdic_csv"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir = self.data_dir / "tabelas"
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = aiohttp.ClientTimeout(total=600)  # 10 minutos para downloads grandes
        
    async def download_file(
        self,
        url: str,
        filepath: Path,
        session: Optional[aiohttp.ClientSession] = None
    ) -> bool:
        """
        Baixa um arquivo da URL especificada.
        
        Args:
            url: URL do arquivo
            filepath: Caminho onde salvar
            session: Sessão HTTP (opcional)
        
        Returns:
            True se baixou com sucesso
        """
        close_session = False
        if session is None:
            connector = aiohttp.TCPConnector(ssl=False, limit=10)
            session = aiohttp.ClientSession(timeout=self.timeout, connector=connector)
            close_session = True
        
        try:
            # Se arquivo já existe e tem tamanho válido, não baixar novamente
            if filepath.exists() and filepath.stat().st_size > 1000:
                logger.debug(f"Arquivo já existe: {filepath}")
                return True
            
            logger.info(f"Baixando: {url}")
            async with session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as response:
                if response.status == 200:
                    content = await response.read()
                    if len(content) > 100:  # Arquivo válido
                        filepath.write_bytes(content)
                        logger.success(f"✅ Baixado: {filepath.name} ({len(content):,} bytes)")
                        return True
                    else:
                        logger.warning(f"Arquivo muito pequeno: {len(content)} bytes")
                else:
                    logger.warning(f"Status {response.status} para {url}")
        except Exception as e:
            logger.error(f"Erro ao baixar {url}: {e}")
        finally:
            if close_session:
                await session.close()
        
        return False
    
    async def download_correlation_tables(self) -> Dict[str, Path]:
        """
        Baixa todas as tabelas de correlação do MDIC.
        
        Returns:
            Dicionário com nome da tabela e caminho do arquivo
        """
        logger.info("Baixando tabelas de correlação do MDIC...")
        
        downloaded = {}
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            tasks = []
            for nome, url in self.CORRELATION_TABLES.items():
                filepath = self.tables_dir / f"{nome}.csv"
                task = self.download_file(url, filepath, session)
                tasks.append((nome, task))
            
            # Executar downloads em paralelo
            for nome, task in tasks:
                success = await task
                if success:
                    downloaded[nome] = self.tables_dir / f"{nome}.csv"
                    await asyncio.sleep(0.5)  # Pequeno delay entre downloads
        
        logger.info(f"✅ Baixadas {len(downloaded)} tabelas de correlação")
        return downloaded
    
    async def download_monthly_data(
        self,
        ano: int,
        mes: int,
        tipo: str = "both"  # "importacao", "exportacao", ou "both"
    ) -> List[Path]:
        """
        Baixa dados mensais de importação/exportação.
        
        Args:
            ano: Ano (ex: 2024)
            mes: Mês (1-12)
            tipo: Tipo de operação
        
        Returns:
            Lista de arquivos baixados
        """
        downloaded = []
        mes_str = f"{mes:02d}"
        
        tipos = []
        if tipo == "both":
            tipos = ["IMP", "EXP"]
        elif tipo == "importacao":
            tipos = ["IMP"]
        elif tipo == "exportacao":
            tipos = ["EXP"]
        
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            for tipo_op in tipos:
                # Tentar diferentes formatos de URL
                urls = [
                    f"{self.BASE_URL}/ncm/{tipo_op}_{ano}_{mes_str}.csv",
                    f"{self.BASE_URL}/ncm/{tipo_op}_{ano}{mes_str}.csv",
                ]
                
                filename = f"{tipo_op}_{ano}_{mes_str}.csv"
                filepath = self.data_dir / filename
                
                for url in urls:
                    if await self.download_file(url, filepath, session):
                        downloaded.append(filepath)
                        break
                
                await asyncio.sleep(1)  # Delay entre downloads
        
        return downloaded
    
    async def download_recent_months(
        self,
        meses: int = 24
    ) -> List[Path]:
        """
        Baixa dados dos últimos N meses.
        
        Args:
            meses: Número de meses para baixar
        
        Returns:
            Lista de arquivos baixados
        """
        logger.info(f"Baixando dados dos últimos {meses} meses...")
        
        downloaded = []
        hoje = datetime.now()
        
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            for i in range(meses):
                data = hoje - timedelta(days=30 * i)
                ano = data.year
                mes = data.month
                
                files = await self.download_monthly_data(ano, mes, "both")
                downloaded.extend(files)
                
                # Delay progressivo para não sobrecarregar servidor
                await asyncio.sleep(2)
        
        logger.info(f"✅ Total de arquivos baixados: {len(downloaded)}")
        return downloaded
    
    def parse_csv_file(
        self,
        filepath: Path,
        delimiter: str = ";"
    ) -> List[Dict[str, Any]]:
        """
        Processa um arquivo CSV e retorna lista de registros.
        
        Args:
            filepath: Caminho do arquivo CSV
            delimiter: Delimitador (padrão: ;)
        
        Returns:
            Lista de dicionários com os dados
        """
        registros = []
        
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
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
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            for row in reader:
                # Normalizar nomes das colunas
                registro = {}
                for key, value in row.items():
                    if key:
                        key_normalized = key.strip().lower().replace(' ', '_').replace('-', '_')
                        registro[key_normalized] = value.strip() if value else None
                
                if registro:  # Só adicionar se não estiver vazio
                    registros.append(registro)
            
            logger.info(f"✅ Processados {len(registros)} registros de {filepath.name}")
            return registros
            
        except Exception as e:
            logger.error(f"Erro ao processar CSV {filepath}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def load_correlation_table(self, table_name: str) -> pd.DataFrame:
        """
        Carrega uma tabela de correlação como DataFrame.
        
        Args:
            table_name: Nome da tabela
        
        Returns:
            DataFrame com os dados
        """
        filepath = self.tables_dir / f"{table_name}.csv"
        
        if not filepath.exists():
            logger.warning(f"Tabela {table_name} não encontrada")
            return pd.DataFrame()
        
        try:
            # Tentar diferentes encodings e delimitadores
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            delimiters = [';', ',']
            
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, delimiter=delimiter, low_memory=False)
                        if len(df) > 0:
                            logger.info(f"✅ Carregada tabela {table_name}: {len(df)} registros")
                            return df
                    except:
                        continue
            
            logger.error(f"Não foi possível carregar {table_name}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erro ao carregar tabela {table_name}: {e}")
            return pd.DataFrame()
    
    async def get_available_files(self) -> List[Dict[str, Any]]:
        """
        Descobre quais arquivos CSV estão disponíveis.
        
        Returns:
            Lista de dicionários com informações dos arquivos
        """
        available = []
        hoje = datetime.now()
        
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Verificar últimos 24 meses
            for i in range(24):
                data = hoje - timedelta(days=30 * i)
                ano = data.year
                mes = data.month
                mes_str = f"{mes:02d}"
                
                for tipo in ["IMP", "EXP"]:
                    url = f"{self.BASE_URL}/ncm/{tipo}_{ano}_{mes_str}.csv"
                    
                    try:
                        async with session.head(
                            url,
                            headers={"User-Agent": "Mozilla/5.0"}
                        ) as response:
                            if response.status == 200:
                                size = response.headers.get("content-length", "unknown")
                                available.append({
                                    "url": url,
                                    "tipo": tipo,
                                    "ano": ano,
                                    "mes": mes,
                                    "size": size
                                })
                    except:
                        pass
                
                await asyncio.sleep(0.1)  # Pequeno delay
        
        return available

