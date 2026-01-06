"""
Sistema de atualização automática de dados.
Atualiza empresas do MDIC, CNAE e cruza com operações.
"""
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session

from database import get_db
from data_collector.empresas_mdic_scraper import EmpresasMDICScraper
from data_collector.cruzamento_dados import CruzamentoDados
from data_collector.cnae_analyzer import CNAEAnalyzer
from data_collector.sinergia_analyzer import SinergiaAnalyzer
from pathlib import Path


class DataUpdater:
    """
    Gerencia atualizações automáticas de dados.
    """
    
    def __init__(self):
        self.empresas_scraper = EmpresasMDICScraper()
        self.cruzamento = CruzamentoDados()
        self.cnae_analyzer = None
        self.sinergia_analyzer = None
        
        # Tentar carregar CNAE
        try:
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
            if arquivo_cnae.exists():
                self.cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                self.cnae_analyzer.carregar_cnae_excel()
                logger.info("✅ CNAE carregado para atualizações")
        except Exception as e:
            logger.warning(f"Não foi possível carregar CNAE: {e}")
        
        if self.cnae_analyzer:
            self.sinergia_analyzer = SinergiaAnalyzer(self.cnae_analyzer)
    
    async def atualizar_empresas_mdic(self, ano: int = None) -> dict:
        """
        Atualiza lista de empresas do MDIC.
        
        Args:
            ano: Ano específico (None = ano atual)
        
        Returns:
            Estatísticas da atualização
        """
        logger.info(f"Iniciando atualização de empresas do MDIC (ano: {ano or 'atual'})")
        
        try:
            empresas = await self.empresas_scraper.coletar_empresas(ano)
            
            return {
                "success": True,
                "total_empresas": len(empresas),
                "ano": ano or datetime.now().year,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar empresas MDIC: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def atualizar_relacionamentos(self, limite: int = 1000) -> dict:
        """
        Atualiza relacionamentos entre operações e empresas.
        
        Args:
            limite: Limite de operações a processar
        
        Returns:
            Estatísticas da atualização
        """
        logger.info(f"Iniciando atualização de relacionamentos (limite: {limite})")
        
        try:
            db = next(get_db())
            
            # Carregar empresas do MDIC
            empresas_lista = await self.empresas_scraper.coletar_empresas()
            empresas_mdic = {}
            for empresa in empresas_lista:
                cnpj = empresa.get("cnpj")
                if cnpj:
                    empresas_mdic[cnpj] = empresa
            
            # Cruzar dados
            resultados = await self.cruzamento.cruzar_operacoes_bulk(
                db,
                filtros=None,
                limite=limite
            )
            
            stats = self.cruzamento.estatisticas_cruzamento(resultados)
            
            return {
                "success": True,
                "total_operacoes": stats["total_operacoes"],
                "operacoes_identificadas": stats["operacoes_identificadas"],
                "taxa_identificacao": stats["taxa_identificacao"],
                "empresas_unicas": stats["empresas_unicas"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar relacionamentos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def atualizar_sinergias(self, limite_empresas: int = 100) -> dict:
        """
        Atualiza análise de sinergias.
        
        Args:
            limite_empresas: Limite de empresas a analisar
        
        Returns:
            Estatísticas da atualização
        """
        logger.info(f"Iniciando atualização de sinergias (limite: {limite_empresas})")
        
        try:
            db = next(get_db())
            
            # Carregar empresas
            empresas_lista = await self.empresas_scraper.coletar_empresas()
            empresas_mdic = {}
            for empresa in empresas_lista:
                cnpj = empresa.get("cnpj")
                if cnpj:
                    empresas_mdic[cnpj] = empresa
            
            if not self.sinergia_analyzer:
                self.sinergia_analyzer = SinergiaAnalyzer(self.cnae_analyzer)
            
            # Analisar sinergias por estado
            sinergias_estado = self.sinergia_analyzer.analisar_sinergias_por_estado(db)
            
            # Analisar sinergias por empresa
            sinergias_empresas = self.sinergia_analyzer.analisar_sinergias_por_empresa(
                db,
                empresas_mdic,
                limite_empresas
            )
            
            return {
                "success": True,
                "estados_analisados": sinergias_estado["total_estados"],
                "estados_com_sinergia": sinergias_estado["estados_com_sinergia"],
                "empresas_analisadas": len(sinergias_empresas),
                "sinergias_estado": sinergias_estado["sinergias"][:10],  # Top 10
                "sinergias_empresas": sinergias_empresas[:20],  # Top 20
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar sinergias: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def atualizar_completo(self) -> dict:
        """
        Executa atualização completa de todos os dados.
        
        Returns:
            Estatísticas completas
        """
        logger.info("Iniciando atualização completa de dados")
        
        resultados = {
            "inicio": datetime.now().isoformat(),
            "empresas_mdic": {},
            "relacionamentos": {},
            "sinergias": {},
            "fim": None,
            "sucesso": False
        }
        
        try:
            # 1. Atualizar empresas MDIC
            resultados["empresas_mdic"] = await self.atualizar_empresas_mdic()
            
            # 2. Atualizar relacionamentos
            resultados["relacionamentos"] = await self.atualizar_relacionamentos()
            
            # 3. Atualizar sinergias
            resultados["sinergias"] = await self.atualizar_sinergias()
            
            resultados["fim"] = datetime.now().isoformat()
            resultados["sucesso"] = (
                resultados["empresas_mdic"].get("success") and
                resultados["relacionamentos"].get("success") and
                resultados["sinergias"].get("success")
            )
            
            logger.success("✅ Atualização completa concluída")
            
        except Exception as e:
            logger.error(f"Erro na atualização completa: {e}")
            resultados["erro"] = str(e)
        
        return resultados

