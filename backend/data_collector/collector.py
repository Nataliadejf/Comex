"""
Coletor principal de dados do Comex Stat.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_

from config import settings
from database import get_db, OperacaoComex, ColetaLog, TipoOperacao
from .api_client import ComexStatAPIClient
from .transformer import DataTransformer

# Import opcional - scraper não disponível no Render
try:
    from .scraper import ComexStatScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    logger.warning("scraper não disponível - apenas API será usada")

# Import CSV scraper (sempre disponível - não requer Selenium)
try:
    from .csv_scraper import CSVDataScraper
    CSV_SCRAPER_AVAILABLE = True
except ImportError:
    CSV_SCRAPER_AVAILABLE = False
    logger.warning("CSV scraper não disponível")


class DataCollector:
    """
    Classe principal para coleta de dados do Comex Stat.
    Tenta usar API primeiro, depois fallback para scraper.
    """
    
    def __init__(self):
        self.api_client = ComexStatAPIClient()
        self.scraper = ComexStatScraper() if SCRAPER_AVAILABLE else None
        self.csv_scraper = CSVDataScraper() if CSV_SCRAPER_AVAILABLE else None
        self.transformer = DataTransformer()
    
    async def collect_recent_data(self, db: Session) -> Dict[str, Any]:
        """
        Coleta dados dos últimos N meses.
        
        Args:
            db: Sessão do banco de dados
        
        Returns:
            Dicionário com estatísticas da coleta
        """
        logger.info("Iniciando coleta de dados do Comex Stat")
        
        stats = {
            "total_registros": 0,
            "meses_processados": [],
            "erros": [],
            "usou_api": False,
        }
        
        # Tentar usar API primeiro
        if await self.api_client.test_connection():
            stats["usou_api"] = True
            try:
                await self._collect_via_api(db, stats)
                # Se coletou dados com sucesso, retornar
                if stats["total_registros"] > 0:
                    return stats
            except Exception as e:
                logger.error(f"Erro ao coletar via API: {e}")
                stats["erros"].append(f"API: {str(e)}")
        
        # Fallback 1: Tentar CSV scraper (mais confiável, não requer Selenium)
        if CSV_SCRAPER_AVAILABLE and self.csv_scraper:
            logger.info("Tentando coletar dados via CSV scraper (bases de dados brutas)")
            try:
                await self._collect_via_csv_scraper(db, stats)
                if stats["total_registros"] > 0:
                    return stats
            except Exception as e:
                logger.error(f"Erro ao coletar via CSV scraper: {e}")
                stats["erros"].append(f"CSV Scraper: {str(e)}")
        
        # Fallback 2: Tentar scraper tradicional (se disponível)
        if SCRAPER_AVAILABLE and self.scraper:
            logger.info("Tentando coletar dados via scraper tradicional")
            stats["usou_api"] = False
            try:
                await self._collect_via_scraper(db, stats)
            except Exception as e:
                logger.error(f"Erro ao coletar via scraper: {e}")
                stats["erros"].append(f"Scraper: {str(e)}")
        else:
            logger.warning("Nenhum método de coleta disponível - API não disponível e scrapers não instalados")
            stats["erros"].append("Nenhum método de coleta disponível")
        
        logger.info(
            f"Coleta concluída: {stats['total_registros']} registros, "
            f"{len(stats['meses_processados'])} meses processados"
        )
        
        return stats
    
    async def _collect_via_api(
        self,
        db: Session,
        stats: Dict[str, Any]
    ):
        """Coleta dados via API."""
        logger.info("Coletando dados via API")
        
        months = self._get_months_to_fetch()
        
        for mes in months:
            try:
                # Buscar dados de importação e exportação
                for tipo in ["Importação", "Exportação"]:
                    data = await self.api_client.fetch_data(
                        mes_inicio=mes,
                        mes_fim=mes,
                        tipo_operacao=tipo
                    )
                    
                    if data:
                        transformed = self.transformer.transform_api_data(data, mes, tipo)
                        saved = self._save_to_database(db, transformed, mes, tipo)
                        stats["total_registros"] += saved
                
                if mes not in stats["meses_processados"]:
                    stats["meses_processados"].append(mes)
            
            except Exception as e:
                error_msg = f"Erro ao coletar {mes}: {e}"
                logger.error(error_msg)
                stats["erros"].append(error_msg)
    
    async def _collect_via_csv_scraper(
        self,
        db: Session,
        stats: Dict[str, Any]
    ):
        """Coleta dados via CSV scraper (bases de dados brutas do MDIC)."""
        if not CSV_SCRAPER_AVAILABLE or not self.csv_scraper:
            logger.error("CSV scraper não disponível")
            stats["erros"].append("CSV scraper não disponível")
            return
        
        logger.info("Coletando dados via CSV scraper (bases de dados brutas)")
        
        # Baixar arquivos CSV dos últimos 24 meses
        months = self._get_months_to_fetch()
        
        for mes_str in months:
            try:
                # Extrair ano e mês
                ano, mes = map(int, mes_str.split('-'))
                
                # Baixar importação e exportação
                for tipo in ["Importação", "Exportação"]:
                    filepath = await self.csv_scraper.download_month_csv(ano, mes, tipo)
                    
                    if filepath:
                        # Parse do arquivo CSV
                        raw_data = self.csv_scraper.parse_csv_file(filepath)
                        
                        if raw_data:
                            # Transformar dados
                            transformed = self.transformer.transform_csv_data(
                                raw_data,
                                mes_str,
                                tipo
                            )
                            
                            # Salvar no banco
                            saved = self._save_to_database(db, transformed, mes_str, tipo)
                            stats["total_registros"] += saved
                
                if mes_str not in stats["meses_processados"]:
                    stats["meses_processados"].append(mes_str)
            
            except Exception as e:
                error_msg = f"Erro ao coletar {mes_str}: {e}"
                logger.error(error_msg)
                stats["erros"].append(error_msg)
    
    async def _collect_via_scraper(
        self,
        db: Session,
        stats: Dict[str, Any]
    ):
        """Coleta dados via scraper tradicional (fallback)."""
        if not SCRAPER_AVAILABLE or not self.scraper:
            logger.error("Scraper não disponível")
            stats["erros"].append("Scraper não disponível (dependências não instaladas)")
            return
        
        logger.info("Coletando dados via scraper tradicional")
        
        # Baixar arquivos
        files = self.scraper.download_recent_data()
        
        for filepath in files:
            try:
                # Parse do arquivo
                raw_data = self.scraper.parse_csv_file(filepath)
                
                if not raw_data:
                    continue
                
                # Extrair mês e tipo do nome do arquivo
                mes = self._extract_month_from_filename(filepath)
                tipo = self._extract_type_from_filename(filepath)
                
                # Transformar dados
                transformed = self.transformer.transform_scraper_data(
                    raw_data,
                    mes,
                    tipo
                )
                
                # Salvar no banco
                saved = self._save_to_database(db, transformed, mes, tipo)
                stats["total_registros"] += saved
                
                if mes and mes not in stats["meses_processados"]:
                    stats["meses_processados"].append(mes)
            
            except Exception as e:
                error_msg = f"Erro ao processar {filepath}: {e}"
                logger.error(error_msg)
                stats["erros"].append(error_msg)
    
    def _get_months_to_fetch(self) -> List[str]:
        """Retorna lista de meses dos últimos 2 anos (24 meses)."""
        months = []
        today = datetime.now()
        
        # Buscar últimos 24 meses (2 anos)
        for i in range(24):
            month_date = today - timedelta(days=30 * i)
            months.append(month_date.strftime("%Y-%m"))
        
        return sorted(months)
    
    def _extract_month_from_filename(self, filepath: Path) -> Optional[str]:
        """Extrai mês do nome do arquivo."""
        # Formato esperado: tipo_YYYY-MM.csv
        parts = filepath.stem.split('_')
        if len(parts) >= 2:
            return parts[-1]
        return None
    
    def _extract_type_from_filename(self, filepath: Path) -> str:
        """Extrai tipo de operação do nome do arquivo."""
        # Formato esperado: tipo_YYYY-MM.csv
        parts = filepath.stem.split('_')
        if len(parts) >= 1:
            tipo = parts[0].capitalize()
            if tipo.lower() == "importacao":
                return "Importação"
            elif tipo.lower() == "exportacao":
                return "Exportação"
        return "Importação"  # Default
    
    def _save_to_database(
        self,
        db: Session,
        records: List[Dict[str, Any]],
        mes: str,
        tipo: str
    ) -> int:
        """
        Salva registros no banco de dados.
        Implementa atualização incremental (não duplica dados).
        
        Returns:
            Número de registros salvos
        """
        saved_count = 0
        
        for record in records:
            try:
                # Verificar se já existe (evitar duplicatas)
                existing = db.query(OperacaoComex).filter(
                    and_(
                        OperacaoComex.ncm == record.get("ncm"),
                        OperacaoComex.tipo_operacao == record.get("tipo_operacao"),
                        OperacaoComex.data_operacao == record.get("data_operacao"),
                        OperacaoComex.pais_origem_destino == record.get("pais_origem_destino"),
                        OperacaoComex.uf == record.get("uf"),
                    )
                ).first()
                
                if existing:
                    continue  # Já existe, pular
                
                # Criar novo registro
                operacao = OperacaoComex(**record)
                db.add(operacao)
                saved_count += 1
            
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {e}")
                continue
        
        try:
            db.commit()
            logger.info(f"{saved_count} novos registros salvos para {mes} - {tipo}")
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao commitar transação: {e}")
            raise
        
        return saved_count
    
    def check_data_freshness(self, db: Session) -> Dict[str, Any]:
        """
        Verifica a "frescura" dos dados no banco.
        
        Returns:
            Dicionário com informações sobre os dados
        """
        # Última data de operação no banco
        last_date = db.query(OperacaoComex.data_operacao).order_by(
            OperacaoComex.data_operacao.desc()
        ).first()
        
        # Contagem por mês
        from sqlalchemy import func
        counts_by_month = db.query(
            OperacaoComex.mes_referencia,
            func.count(OperacaoComex.id).label('count')
        ).group_by(OperacaoComex.mes_referencia).all()
        
        return {
            "ultima_data": last_date[0].isoformat() if last_date else None,
            "registros_por_mes": {
                mes: count for mes, count in counts_by_month
            },
            "total_registros": db.query(OperacaoComex).count(),
        }

