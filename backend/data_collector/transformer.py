"""
Transformador de dados brutos para formato do banco de dados.
"""
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from database import TipoOperacao, ViaTransporte


class DataTransformer:
    """
    Transforma dados brutos (API ou CSV) para formato do banco de dados.
    """
    
    @staticmethod
    def _safe_str(value: Any, default: str = "") -> str:
        """
        Converte valor para string de forma segura, tratando None, NaN e outros tipos.
        
        Args:
            value: Valor a ser convertido
            default: Valor padrão se conversão falhar ou for inválida
        
        Returns:
            String segura para usar com métodos como .upper() ou .lower()
        """
        if value is None:
            return default
        
        # Tratar NaN (float)
        if isinstance(value, float):
            if math.isnan(value):
                return default
            # Converter float para string (ex: 123.0 -> "123")
            if value.is_integer():
                return str(int(value))
            return str(value)
        
        # Para outros tipos, converter para string
        try:
            result = str(value).strip()
            return result if result else default
        except (ValueError, TypeError, AttributeError):
            return default
    
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
    
    def transform_csv_data(
        self,
        data: List[Dict[str, Any]],
        mes: str,
        tipo: str
    ) -> List[Dict[str, Any]]:
        """
        Transforma dados CSV das bases de dados brutas para formato do banco.
        Similar ao transform_scraper_data mas otimizado para formato do MDIC.
        
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
                logger.error(f"Erro ao transformar registro CSV: {e}")
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
            # Mapear campos (ajustar conforme estrutura real dos dados)
            # Extrair UF de forma segura - SEMPRE converter para string antes de .upper()
            uf_raw = self._extract_string(record, "uf", "estado", "")
            uf_value = self._safe_str(uf_raw, "").upper()[:2] if uf_raw else ""
            
            # Extrair CNPJ de forma segura - SEMPRE converter para string antes de operações
            cnpj_imp_value = ""
            if tipo == "Importação":
                cnpj_imp_raw = self._extract_string(
                    record, 
                    "cnpj_importador", "cnpj_imp", "cnpj_importador", ""
                )
                cnpj_imp_str = self._safe_str(cnpj_imp_raw, "")
                cnpj_imp_value = cnpj_imp_str.replace('.', '').replace('/', '').replace('-', '')[:14]
            
            cnpj_exp_value = ""
            if tipo == "Exportação":
                cnpj_exp_raw = self._extract_string(
                    record, 
                    "cnpj_exportador", "cnpj_exp", "cnpj_exportador", ""
                )
                cnpj_exp_str = self._safe_str(cnpj_exp_raw, "")
                cnpj_exp_value = cnpj_exp_str.replace('.', '').replace('/', '').replace('-', '')[:14]
            
            # Extrair arquivo_origem de forma segura
            arquivo_origem_raw = record.get("arquivo_origem") or ""
            arquivo_origem_value = self._safe_str(arquivo_origem_raw, "")
            
            transformed = {
                "ncm": self._extract_ncm(record),
                "descricao_produto": self._extract_string(record, "descricao", "produto", ""),
                "tipo_operacao": TipoOperacao.IMPORTACAO if tipo == "Importação" else TipoOperacao.EXPORTACAO,
                "pais_origem_destino": self._extract_string(record, "pais", "pais_origem", "pais_destino", ""),
                "uf": uf_value,
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
                "arquivo_origem": arquivo_origem_value,
                # Campos de empresa
                "razao_social_importador": self._extract_string(
                    record, 
                    "razao_social_importador", "razao_social_imp", "importador", 
                    "nome_importador", "empresa_importadora", ""
                ) if tipo == "Importação" else None,
                "razao_social_exportador": self._extract_string(
                    record, 
                    "razao_social_exportador", "razao_social_exp", "exportador", 
                    "nome_exportador", "empresa_exportadora", ""
                ) if tipo == "Exportação" else None,
                "cnpj_importador": cnpj_imp_value if tipo == "Importação" else None,
                "cnpj_exportador": cnpj_exp_value if tipo == "Exportação" else None,
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
        ncm_value = (
            record.get("ncm") or
            record.get("NCM") or
            record.get("codigo_ncm") or
            ""
        )
        
        # Converter para string, tratando floats especialmente
        if isinstance(ncm_value, float):
            if math.isnan(ncm_value):
                ncm_value = ""
            else:
                # Converter float para int primeiro para evitar decimais
                ncm_value = str(int(ncm_value)) if ncm_value.is_integer() else str(int(ncm_value))
        else:
            ncm_value = str(ncm_value)
        
        # Garantir 8 dígitos
        ncm = ncm_value.replace(".", "").replace("-", "").strip()
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
            # Tentar diferentes variações da chave
            value = None
            for key_variant in [key, key.upper(), key.lower(), key.capitalize()]:
                if key_variant in record:
                    value = record[key_variant]
                    break
            
            if value is None:
                continue
                
            # Usar função auxiliar para conversão segura
            result = self._safe_str(value, "")
            if result:  # Só retornar se não estiver vazio
                return result
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
        via_value = None
        
        # Tentar diferentes chaves
        for key in ["via", "via_transporte", "modal", "VIA", "VIA_TRANSPORTE", "MODAL"]:
            if key in record:
                via_value = record[key]
                break
        
        # Se não encontrou, tentar com variações
        if via_value is None:
            for key in ["via", "via_transporte", "modal"]:
                value = record.get(key) or record.get(key.upper()) or record.get(key.lower())
                if value is not None and value != "":
                    via_value = value
                    break
        
        # Converter para string de forma segura ANTES de usar .lower()
        via = self._safe_str(via_value, "").lower()
        
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

