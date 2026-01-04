"""
Cliente para API real do Comex Stat (MDIC).
Integração oficial com endpoints documentados.
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path

from config import settings


class ComexStatAPIReal:
    """
    Cliente para a API oficial do Comex Stat.
    Baseado na documentação oficial do MDIC.
    """
    
    # URLs oficiais conhecidas
    BASE_URL_PORTAL = "https://comexstat.mdic.gov.br"
    BASE_URL_API = "https://api-comexstat.mdic.gov.br"  # Se existir
    
    def __init__(self):
        self.api_url = settings.comex_stat_api_url or self.BASE_URL_API
        self.api_key = settings.comex_stat_api_key
        self.timeout = 30.0
        self.download_dir = settings.data_dir / "raw"
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    async def test_connection(self) -> bool:
        """Testa conexão com o portal."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=True) as client:
                response = await client.get(self.BASE_URL_PORTAL, follow_redirects=True)
                if response.status_code == 200:
                    logger.info(f"✅ Portal acessível: {self.BASE_URL_PORTAL}")
                    return True
        except Exception as e:
            logger.error(f"Erro ao acessar portal: {e}")
        return False
    
    async def buscar_url_download(self, tipo: str, ano: int, mes: int) -> Optional[str]:
        """
        Busca URL de download direto do portal.
        
        Args:
            tipo: 'exportacao' ou 'importacao'
            ano: Ano (ex: 2025)
            mes: Mês (1-12)
        """
        logger.info(f"Buscando URL de download para {tipo} - {ano}/{mes:02d}")
        
        # Padrões de URL conhecidos
        urls_tentativas = [
            f"{self.BASE_URL_PORTAL}/pt/download?tipo={tipo}&ano={ano}&mes={mes}",
            f"{self.BASE_URL_PORTAL}/download/{tipo.upper()}_{ano}_{mes:02d}.csv",
            f"{self.BASE_URL_PORTAL}/api/download/{tipo}/{ano}/{mes:02d}",
            f"https://www.mdic.gov.br/comexstat/download/{tipo.upper()}_{ano}_{mes:02d}.csv",
        ]
        
        for url in urls_tentativas:
            try:
                async with httpx.AsyncClient(timeout=15.0, verify=True, follow_redirects=True) as client:
                    response = await client.head(url)  # HEAD primeiro para verificar
                    
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "csv" in content_type or "text" in content_type:
                            logger.info(f"✅ URL encontrada: {url}")
                            return url
                            
            except Exception as e:
                logger.debug(f"URL {url} não funcionou: {e}")
                continue
        
        return None
    
    async def baixar_arquivo_csv(self, tipo: str, ano: int, mes: int) -> Optional[Path]:
        """
        Baixa arquivo CSV do portal.
        
        Args:
            tipo: 'exportacao' ou 'importacao'
            ano: Ano
            mes: Mês
        
        Returns:
            Caminho do arquivo baixado ou None
        """
        url = await self.buscar_url_download(tipo, ano, mes)
        
        if not url:
            logger.warning(f"Não foi possível encontrar URL para {tipo} {ano}/{mes:02d}")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60.0, verify=True, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Verificar se é CSV válido
                    content_preview = response.text[:1000]
                    if "," in content_preview or ";" in content_preview:
                        # Salvar arquivo
                        filename = f"{tipo.upper()}_{ano}_{mes:02d}.csv"
                        filepath = self.download_dir / filename
                        
                        # Tentar diferentes encodings
                        try:
                            filepath.write_text(response.text, encoding='utf-8')
                        except:
                            filepath.write_bytes(response.content)
                        
                        logger.info(f"✅ Arquivo baixado: {filepath} ({len(response.content)} bytes)")
                        return filepath
                    else:
                        logger.warning(f"Resposta não parece ser CSV válido")
                        return None
                else:
                    logger.warning(f"Status {response.status_code} ao baixar {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {e}")
            return None
    
    async def baixar_ultimos_meses(self, meses: int = 3, tipos: List[str] = None) -> List[Path]:
        """
        Baixa dados dos últimos N meses.
        
        Args:
            meses: Número de meses para trás
            tipos: Lista de tipos ['exportacao', 'importacao'] ou None para ambos
        """
        if tipos is None:
            tipos = ['exportacao', 'importacao']
        
        hoje = datetime.now()
        arquivos_baixados = []
        
        for i in range(meses):
            data = hoje - timedelta(days=30 * i)
            ano = data.year
            mes = data.month
            
            for tipo in tipos:
                try:
                    arquivo = await self.baixar_arquivo_csv(tipo, ano, mes)
                    if arquivo:
                        arquivos_baixados.append(arquivo)
                    
                    # Delay entre downloads
                    import asyncio
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao baixar {tipo} {ano}/{mes:02d}: {e}")
                    continue
        
        logger.info(f"✅ Total de arquivos baixados: {len(arquivos_baixados)}")
        return arquivos_baixados
    
    async def buscar_dados_api(self, mes_inicio: str, mes_fim: str, tipo: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Busca dados via API (se disponível).
        
        Args:
            mes_inicio: Mês inicial (YYYY-MM)
            mes_fim: Mês final (YYYY-MM)
            tipo: 'exportacao' ou 'importacao' (opcional)
        """
        if not self.api_key:
            logger.warning("API key não configurada")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "mes_inicio": mes_inicio,
                "mes_fim": mes_fim,
            }
            
            if tipo:
                params["tipo"] = tipo
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=True) as client:
                response = await client.get(
                    f"{self.api_url}/dados",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Dados obtidos da API: {len(data.get('registros', []))} registros")
                    return data.get("registros", [])
                else:
                    logger.warning(f"API retornou status {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao buscar dados da API: {e}")
            return None



