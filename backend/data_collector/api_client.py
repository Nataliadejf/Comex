"""
Cliente para API do Comex Stat (se disponível).
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from config import settings


class ComexStatAPIClient:
    """
    Cliente para consumir a API oficial do Comex Stat.
    """
    
    def __init__(self):
        self.base_url = settings.comex_stat_api_url
        self.api_key = settings.comex_stat_api_key
        self.timeout = 30.0
        
    def is_available(self) -> bool:
        """Verifica se a API está disponível."""
        return self.base_url is not None and self.api_key is not None
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão com a API.
        Retorna True se a API estiver disponível.
        """
        if not self.is_available():
            logger.warning("API do Comex Stat não configurada")
            return False
        
        try:
            # Desabilitar verificação SSL para desenvolvimento (pode ser necessário)
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Tentar endpoint de health check ou similar
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info("API do Comex Stat disponível")
                    return True
        except Exception as e:
            logger.error(f"Erro ao testar conexão com API: {e}")
        
        return False
    
    async def fetch_data(
        self,
        mes_inicio: str,
        mes_fim: str,
        tipo_operacao: Optional[str] = None,
        ncm: Optional[str] = None,
        pais: Optional[str] = None,
        uf: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca dados da API.
        
        Args:
            mes_inicio: Mês inicial no formato YYYY-MM
            mes_fim: Mês final no formato YYYY-MM
            tipo_operacao: 'Importação' ou 'Exportação' (opcional)
            ncm: Código NCM (opcional)
            pais: País (opcional)
            uf: Unidade Federativa (opcional)
        
        Returns:
            Lista de registros de operações
        """
        if not self.is_available():
            raise ValueError("API do Comex Stat não configurada")
        
        params = {
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim,
        }
        
        if tipo_operacao:
            params["tipo_operacao"] = tipo_operacao
        if ncm:
            params["ncm"] = ncm
        if pais:
            params["pais"] = pais
        if uf:
            params["uf"] = uf
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/dados",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(
                    f"Dados coletados via API: {len(data.get('registros', []))} registros"
                )
                
                return data.get("registros", [])
        
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao buscar dados da API: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar dados da API: {e}")
            raise
    
    async def get_available_months(self) -> List[str]:
        """
        Retorna lista de meses disponíveis na API.
        Formato: ['YYYY-MM', ...]
        """
        if not self.is_available():
            return []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.get(
                    f"{self.base_url}/meses-disponiveis",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                return data.get("meses", [])
        
        except Exception as e:
            logger.error(f"Erro ao buscar meses disponíveis: {e}")
            return []

