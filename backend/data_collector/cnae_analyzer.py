"""
Analisador de CNAE e integração com empresas do MDIC.
Lê arquivo Excel com classificação CNAE e relaciona com empresas.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

# Tentar importar pandas/openpyxl
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas não disponível - análise CNAE limitada")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl não disponível - leitura Excel limitada")


class CNAEAnalyzer:
    """
    Analisador de CNAE para empresas do comércio exterior.
    """
    
    def __init__(self, arquivo_cnae: Optional[Path] = None):
        """
        Inicializa o analisador.
        
        Args:
            arquivo_cnae: Caminho para arquivo Excel com CNAE
        """
        if arquivo_cnae is None:
            # Tentar caminho padrão
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
        
        self.arquivo_cnae = Path(arquivo_cnae)
        self.cnae_data: Dict[str, Dict[str, Any]] = {}
        self.empresas_cnae: Dict[str, Dict[str, Any]] = {}
        
    def carregar_cnae_excel(self) -> bool:
        """
        Carrega dados do arquivo Excel CNAE.
        
        Returns:
            True se carregou com sucesso
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas não disponível - não é possível ler Excel")
            return False
        
        if not self.arquivo_cnae.exists():
            logger.warning(f"Arquivo CNAE não encontrado: {self.arquivo_cnae}")
            return False
        
        try:
            # Ler Excel - tentar diferentes sheets
            excel_file = pd.ExcelFile(self.arquivo_cnae)
            
            logger.info(f"Planilhas encontradas: {excel_file.sheet_names}")
            
            # Ler primeira planilha ou todas
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                logger.info(f"Lendo planilha '{sheet_name}': {len(df)} linhas, {len(df.columns)} colunas")
                logger.info(f"Colunas: {list(df.columns)}")
                
                # Processar dados
                self._processar_dataframe_cnae(df, sheet_name)
            
            logger.success(f"✅ CNAE carregado: {len(self.cnae_data)} registros")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar CNAE Excel: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _processar_dataframe_cnae(self, df: pd.DataFrame, sheet_name: str):
        """
        Processa DataFrame do CNAE.
        
        Args:
            df: DataFrame do pandas
            sheet_name: Nome da planilha
        """
        # Normalizar nomes das colunas
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Procurar colunas relevantes
        colunas_cnae = [col for col in df.columns if 'cnae' in col.lower()]
        colunas_cnpj = [col for col in df.columns if 'cnpj' in col.lower()]
        colunas_empresa = [col for col in df.columns if any(x in col.lower() for x in ['empresa', 'razao', 'nome', 'fantasia'])]
        colunas_classificacao = [col for col in df.columns if any(x in col.lower() for x in ['classificacao', 'categoria', 'tipo', 'setor'])]
        
        logger.info(f"Colunas CNAE: {colunas_cnae}")
        logger.info(f"Colunas CNPJ: {colunas_cnpj}")
        logger.info(f"Colunas Empresa: {colunas_empresa}")
        logger.info(f"Colunas Classificação: {colunas_classificacao}")
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                # Extrair CNAE
                cnae = None
                for col in colunas_cnae:
                    valor = row.get(col)
                    if pd.notna(valor):
                        cnae = str(valor).strip().replace('.', '').replace('-', '')
                        if len(cnae) >= 4:  # CNAE tem pelo menos 4 dígitos
                            break
                
                # Extrair CNPJ
                cnpj = None
                for col in colunas_cnpj:
                    valor = row.get(col)
                    if pd.notna(valor):
                        cnpj = str(valor).strip().replace('.', '').replace('/', '').replace('-', '')
                        if len(cnpj) == 14:
                            break
                
                # Extrair nome da empresa
                razao_social = None
                for col in colunas_empresa:
                    valor = row.get(col)
                    if pd.notna(valor):
                        razao_social = str(valor).strip()
                        if razao_social:
                            break
                
                # Extrair classificação
                classificacao = None
                for col in colunas_classificacao:
                    valor = row.get(col)
                    if pd.notna(valor):
                        classificacao = str(valor).strip()
                        if classificacao:
                            break
                
                # Criar registro
                registro = {
                    "cnae": cnae,
                    "cnpj": cnpj,
                    "razao_social": razao_social,
                    "classificacao": classificacao,
                    "planilha": sheet_name,
                    "linha": idx + 2  # +2 porque começa em 0 e tem header
                }
                
                # Adicionar dados adicionais da linha
                for col, valor in row.items():
                    if pd.notna(valor) and col not in ['cnae', 'cnpj', 'razao_social', 'classificacao']:
                        registro[col] = str(valor).strip()
                
                # Indexar por CNAE
                if cnae:
                    if cnae not in self.cnae_data:
                        self.cnae_data[cnae] = []
                    self.cnae_data[cnae].append(registro)
                
                # Indexar por CNPJ
                if cnpj:
                    self.empresas_cnae[cnpj] = registro
                    
            except Exception as e:
                logger.debug(f"Erro ao processar linha {idx}: {e}")
                continue
    
    def buscar_cnae_empresa(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Busca CNAE de uma empresa por CNPJ.
        
        Args:
            cnpj: CNPJ da empresa (com ou sem formatação)
        
        Returns:
            Dados do CNAE ou None
        """
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
        return self.empresas_cnae.get(cnpj_limpo)
    
    def buscar_empresas_por_cnae(self, cnae: str) -> List[Dict[str, Any]]:
        """
        Busca empresas por CNAE.
        
        Args:
            cnae: Código CNAE (pode ser parcial)
        
        Returns:
            Lista de empresas com esse CNAE
        """
        cnae_limpo = cnae.replace('.', '').replace('-', '')
        
        # Busca exata
        if cnae_limpo in self.cnae_data:
            return self.cnae_data[cnae_limpo]
        
        # Busca parcial (prefixo)
        resultados = []
        for cnae_key, empresas in self.cnae_data.items():
            if cnae_key.startswith(cnae_limpo[:4]):  # Primeiros 4 dígitos
                resultados.extend(empresas)
        
        return resultados
    
    def obter_classificacao_cnae(self, cnae: str) -> Optional[str]:
        """
        Obtém classificação de um CNAE.
        
        Args:
            cnae: Código CNAE
        
        Returns:
            Classificação ou None
        """
        empresas = self.buscar_empresas_por_cnae(cnae)
        if empresas:
            return empresas[0].get("classificacao")
        return None
    
    def listar_todos_cnaes(self) -> List[str]:
        """Retorna lista de todos os CNAEs encontrados."""
        return list(self.cnae_data.keys())
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do CNAE."""
        total_empresas = len(self.empresas_cnae)
        total_cnaes = len(self.cnae_data)
        
        classificacoes = {}
        for empresas in self.cnae_data.values():
            for empresa in empresas:
                classificacao = empresa.get("classificacao")
                if classificacao:
                    classificacoes[classificacao] = classificacoes.get(classificacao, 0) + 1
        
        return {
            "total_empresas": total_empresas,
            "total_cnaes_unicos": total_cnaes,
            "classificacoes": classificacoes,
            "arquivo": str(self.arquivo_cnae)
        }

