"""
Transformador de dados brutos para formato do banco de dados.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from database import TipoOperacao, ViaTransporte


class DataTransformer:
    """
    Transforma dados brutos (API ou CSV) para formato do banco de dados.
    """
    
    def transform_api_data(
        self,
        data: List[Dict[str, Any]],
        mes: str,
        tipo: str
    ) -> List[Dict[str, Any]]:
        """
        Transforma dados da API para formato do banco.
        
        Args:
            data: Dados brutos da API
            mes: Mês de referência (YYYY-MM)
            tipo: Tipo de operação
        
        Returns:
            Lista de dicionários no formato do banco
        """
        transformed = []
        
        for record in data:
            try:
                transformed_record = self._transform_record(record, mes, tipo)
                if transformed_record:
                    transformed.append(transformed_record)
            except Exception as e:
                logger.error(f"Erro ao transformar registro da API: {e}")
                continue
        
        return transformed
    
    def transform_scraper_data(
        self,
        data: List[Dict[str, Any]],
        mes: str,
        tipo: str
    ) -> List[Dict[str, Any]]:
        """
        Transforma dados do scraper (CSV) para formato do banco.
        
        Args:
            data: Dados brutos do CSV
            mes: Mês de referência (YYYY-MM)
            tipo: Tipo de operação
        
        Returns:
            Lista de dicionários no formato do banco
        """
        transformed = []
        
        for record in data:
            try:
                transformed_record = self._transform_record(record, mes, tipo)
                if transformed_record:
                    transformed.append(transformed_record)
            except Exception as e:
                logger.error(f"Erro ao transformar registro do CSV: {e}")
                continue
        
        return transformed
    
    def _transform_record(
        self,
        record: Dict[str, Any],
        mes: str,
        tipo: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transforma um registro individual.
        
        Args:
            record: Registro bruto
            mes: Mês de referência
            tipo: Tipo de operação
        
        Returns:
            Dicionário transformado ou None se inválido
        """
        try:
            # Determinar tipo de operação
            tipo_op = TipoOperacao.IMPORTACAO if tipo == "Importação" else TipoOperacao.EXPORTACAO
            is_imp = "S" if tipo_op == TipoOperacao.IMPORTACAO else "N"
            is_exp = "S" if tipo_op == TipoOperacao.EXPORTACAO else "N"
            
            # Mapear campos (ajustar conforme estrutura real dos dados)
            transformed = {
                "ncm": self._extract_ncm(record),
                "descricao_produto": self._extract_string(record, "descricao", "produto", ""),
                "tipo_operacao": tipo_op,
                "is_importacao": is_imp,
                "is_exportacao": is_exp,
                "pais_origem_destino": self._extract_string(record, "pais", "pais_origem", "pais_destino", ""),
                "uf": self._extract_string(record, "uf", "estado", "").upper()[:2],
                "porto_aeroporto": self._extract_string(record, "porto", "aeroporto", ""),
                "via_transporte": self._extract_via_transporte(record),
                "valor_fob": self._extract_float(record, "valor_fob", "fob", "valor", 0.0),
                "valor_frete": self._extract_float(record, "frete", "valor_frete", 0.0),
                "valor_seguro": self._extract_float(record, "seguro", "valor_seguro", 0.0),
                "peso_liquido_kg": self._extract_float(record, "peso_liquido", "peso_liq", 0.0),
                "peso_bruto_kg": self._extract_float(record, "peso_bruto", "peso_brt", 0.0),
                "quantidade_estatistica": self._extract_float(record, "quantidade", "qtd", 0.0),
                "unidade_medida_estatistica": self._extract_string(record, "unidade", "unidade_medida", ""),
                "data_operacao": self._extract_date(record, mes),
                "mes_referencia": mes,
                "arquivo_origem": record.get("arquivo_origem", ""),
            }
            
            # Validações básicas
            if not transformed["ncm"] or len(transformed["ncm"]) != 8:
                logger.warning(f"NCM inválido: {transformed['ncm']}")
                return None
            
            if not transformed["data_operacao"]:
                logger.warning("Data de operação inválida")
                return None
            
            return transformed
        
        except Exception as e:
            logger.error(f"Erro ao transformar registro: {e}")
            return None
    
    def _extract_ncm(self, record: Dict[str, Any]) -> str:
        """Extrai NCM do registro."""
        ncm = (
            record.get("ncm") or
            record.get("NCM") or
            record.get("codigo_ncm") or
            ""
        )
        
        # Garantir 8 dígitos
        ncm = str(ncm).replace(".", "").replace("-", "").strip()
        if len(ncm) > 8:
            ncm = ncm[:8]
        elif len(ncm) < 8:
            ncm = ncm.zfill(8)
        
        return ncm
    
    def _extract_string(
        self,
        record: Dict[str, Any],
        *keys: str,
        default: str = ""
    ) -> str:
        """Extrai string do registro usando múltiplas chaves possíveis."""
        for key in keys:
            value = record.get(key) or record.get(key.upper()) or record.get(key.lower())
            if value:
                return str(value).strip()
        return default
    
    def _extract_float(
        self,
        record: Dict[str, Any],
        *keys: str,
        default: float = 0.0
    ) -> float:
        """Extrai float do registro usando múltiplas chaves possíveis."""
        for key in keys:
            value = record.get(key) or record.get(key.upper()) or record.get(key.lower())
            if value:
                try:
                    # Remover separadores e converter
                    value_str = str(value).replace(".", "").replace(",", ".")
                    return float(value_str)
                except (ValueError, TypeError):
                    continue
        return default
    
    def _extract_date(
        self,
        record: Dict[str, Any],
        mes_referencia: str
    ) -> Optional[datetime]:
        """Extrai data do registro."""
        # Tentar campos de data
        date_fields = ["data", "data_operacao", "data_emissao", "data_movimentacao"]
        
        for field in date_fields:
            value = record.get(field) or record.get(field.upper())
            if value:
                try:
                    if isinstance(value, str):
                        # Tentar diferentes formatos
                        formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]
                        for fmt in formats:
                            try:
                                return datetime.strptime(value, fmt).date()
                            except ValueError:
                                continue
                    elif isinstance(value, datetime):
                        return value.date()
                except Exception:
                    continue
        
        # Fallback: usar primeiro dia do mês de referência
        try:
            return datetime.strptime(f"{mes_referencia}-01", "%Y-%m-%d").date()
        except Exception:
            return None
    
    def _extract_via_transporte(self, record: Dict[str, Any]) -> ViaTransporte:
        """Extrai via de transporte do registro."""
        via = (
            record.get("via") or
            record.get("via_transporte") or
            record.get("modal") or
            ""
        ).lower()
        
        via_mapping = {
            "marítima": ViaTransporte.MARITIMA,
            "maritima": ViaTransporte.MARITIMA,
            "mar": ViaTransporte.MARITIMA,
            "aérea": ViaTransporte.AEREA,
            "aerea": ViaTransporte.AEREA,
            "ar": ViaTransporte.AEREA,
            "rodoviária": ViaTransporte.RODOVIARIA,
            "rodoviaria": ViaTransporte.RODOVIARIA,
            "rod": ViaTransporte.RODOVIARIA,
            "ferroviária": ViaTransporte.FERROVIARIA,
            "ferroviaria": ViaTransporte.FERROVIARIA,
            "fer": ViaTransporte.FERROVIARIA,
            "dutoviária": ViaTransporte.DUTOVIARIA,
            "dutoviaria": ViaTransporte.DUTOVIARIA,
            "postal": ViaTransporte.POSTAL,
        }
        
        return via_mapping.get(via, ViaTransporte.OUTRAS)
    
    def transform_dataframe(
        self,
        df: 'pd.DataFrame',
        mes: str,
        tipo: str,
        arquivo_origem: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Transforma um DataFrame do pandas para formato do banco.
        
        Args:
            df: DataFrame do pandas
            mes: Mês de referência (YYYY-MM)
            tipo: Tipo de operação
            arquivo_origem: Caminho do arquivo de origem
        
        Returns:
            Lista de dicionários no formato do banco
        """
        transformed = []
        
        # Converter DataFrame para lista de dicionários
        records = df.to_dict('records')
        
        for record in records:
            try:
                # Adicionar arquivo_origem ao registro
                record['arquivo_origem'] = arquivo_origem
                transformed_record = self._transform_record(record, mes, tipo)
                if transformed_record:
                    transformed.append(transformed_record)
            except Exception as e:
                logger.error(f"Erro ao transformar registro do DataFrame: {e}")
                continue
        
        return transformed

