"""
Módulo de cruzamento de dados de empresas com base interna comex.
Relaciona empresas aos NCMs e gera sugestões de clientes/fornecedores potenciais.
"""
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
from loguru import logger

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db
from database.models import OperacaoComex
from sqlalchemy import func, extract


class EmpresaCruzamento:
    """
    Cruza dados de empresas com base interna comex.
    """
    
    def __init__(self):
        self.base_comex_ncms: Dict[str, Dict[str, Any]] = {}
    
    def carregar_base_comex(self):
        """Carrega base interna comex para cruzamento."""
        logger.info("Carregando base interna comex...")
        db = next(get_db())
        
        try:
            # Buscar todos os NCMs da base com seus valores
            operacoes = db.query(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                OperacaoComex.tipo_operacao,
                func.sum(OperacaoComex.valor_fob).label('valor_total'),
                func.count(OperacaoComex.id).label('qtd_operacoes')
            ).group_by(
                OperacaoComex.ncm,
                OperacaoComex.descricao_produto,
                OperacaoComex.tipo_operacao
            ).all()
            
            for op in operacoes:
                ncm = op.ncm
                if ncm not in self.base_comex_ncms:
                    self.base_comex_ncms[ncm] = {
                        'descricao': op.descricao_produto,
                        'valor_importacao': 0,
                        'valor_exportacao': 0,
                        'qtd_operacoes_imp': 0,
                        'qtd_operacoes_exp': 0
                    }
                
                if op.tipo_operacao == 'IMPORTACAO':
                    self.base_comex_ncms[ncm]['valor_importacao'] += float(op.valor_total) if op.valor_total else 0
                    self.base_comex_ncms[ncm]['qtd_operacoes_imp'] += op.qtd_operacoes
                else:
                    self.base_comex_ncms[ncm]['valor_exportacao'] += float(op.valor_total) if op.valor_total else 0
                    self.base_comex_ncms[ncm]['qtd_operacoes_exp'] += op.qtd_operacoes
            
            logger.info(f"✅ Base comex carregada: {len(self.base_comex_ncms)} NCMs únicos")
            
        except Exception as e:
            logger.error(f"Erro ao carregar base comex: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def relacionar_empresas_ncms(self, empresas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Relaciona empresas aos NCMs da base interna.
        
        Args:
            empresas: Lista de empresas
            
        Returns:
            Lista expandida com relacionamento empresa-NCM
        """
        logger.info("Relacionando empresas aos NCMs da base interna...")
        
        if not self.base_comex_ncms:
            self.carregar_base_comex()
        
        relacionamentos = []
        
        for empresa in empresas:
            # Processar NCMs de importação
            ncms_imp = str(empresa.get('ncms_importacao', '')).split(',')
            for ncm in ncms_imp:
                ncm = ncm.strip()
                if ncm and ncm in self.base_comex_ncms:
                    relacionamentos.append({
                        'cnpj': empresa['cnpj'],
                        'razao_social': empresa['razao_social'],
                        'nome_fantasia': empresa.get('nome_fantasia', ''),
                        'cnae': empresa.get('cnae', ''),
                        'estado': empresa.get('estado', ''),
                        'endereco': empresa.get('endereco', ''),
                        'ncm': ncm,
                        'descricao_ncm': self.base_comex_ncms[ncm]['descricao'],
                        'tipo_operacao': 'IMPORTACAO',
                        'valor_importacao_usd': empresa.get('valor_importacao_usd', 0),
                        'valor_exportacao_usd': empresa.get('valor_exportacao_usd', 0),
                        'capital_social': empresa.get('capital_social'),
                        'funcionarios_estimado': empresa.get('funcionarios_estimado'),
                        'peso_participacao': empresa.get('peso_participacao', 0),
                        'dados_estimados': empresa.get('dados_estimados', True)
                    })
            
            # Processar NCMs de exportação
            ncms_exp = str(empresa.get('ncms_exportacao', '')).split(',')
            for ncm in ncms_exp:
                ncm = ncm.strip()
                if ncm and ncm in self.base_comex_ncms:
                    relacionamentos.append({
                        'cnpj': empresa['cnpj'],
                        'razao_social': empresa['razao_social'],
                        'nome_fantasia': empresa.get('nome_fantasia', ''),
                        'cnae': empresa.get('cnae', ''),
                        'estado': empresa.get('estado', ''),
                        'endereco': empresa.get('endereco', ''),
                        'ncm': ncm,
                        'descricao_ncm': self.base_comex_ncms[ncm]['descricao'],
                        'tipo_operacao': 'EXPORTACAO',
                        'valor_importacao_usd': empresa.get('valor_importacao_usd', 0),
                        'valor_exportacao_usd': empresa.get('valor_exportacao_usd', 0),
                        'capital_social': empresa.get('capital_social'),
                        'funcionarios_estimado': empresa.get('funcionarios_estimado'),
                        'peso_participacao': empresa.get('peso_participacao', 0),
                        'dados_estimados': empresa.get('dados_estimados', True)
                    })
        
        logger.info(f"✅ Relacionamentos criados: {len(relacionamentos)} empresa-NCM")
        return relacionamentos
    
    def gerar_sugestoes(self, relacionamentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gera sugestões de clientes/fornecedores potenciais.
        
        Args:
            relacionamentos: Lista de relacionamentos empresa-NCM
            
        Returns:
            Lista com sugestões adicionadas
        """
        logger.info("Gerando sugestões de clientes/fornecedores potenciais...")
        
        df = pd.DataFrame(relacionamentos)
        
        if len(df) == 0:
            return relacionamentos
        
        # Para cada NCM, identificar empresas que mais compram/vendem
        sugestoes_list = []
        
        for ncm in df['ncm'].unique():
            df_ncm = df[df['ncm'] == ncm]
            
            # Empresas que importam este NCM = potenciais fornecedores para quem exporta
            empresas_importadoras = df_ncm[df_ncm['tipo_operacao'] == 'IMPORTACAO'].sort_values(
                'valor_importacao_usd', ascending=False
            )
            
            # Empresas que exportam este NCM = potenciais clientes para quem importa
            empresas_exportadoras = df_ncm[df_ncm['tipo_operacao'] == 'EXPORTACAO'].sort_values(
                'valor_exportacao_usd', ascending=False
            )
            
            # Adicionar sugestões
            for _, empresa_imp in empresas_importadoras.head(10).iterrows():
                sugestoes_list.append({
                    'cnpj': empresa_imp['cnpj'],
                    'razao_social': empresa_imp['razao_social'],
                    'nome_fantasia': empresa_imp['nome_fantasia'],
                    'cnae': empresa_imp['cnae'],
                    'estado': empresa_imp['estado'],
                    'endereco': empresa_imp['endereco'],
                    'ncm': ncm,
                    'descricao_ncm': empresa_imp['descricao_ncm'],
                    'valor_importacao_usd': empresa_imp['valor_importacao_usd'],
                    'valor_exportacao_usd': empresa_imp['valor_exportacao_usd'],
                    'capital_social': empresa_imp.get('capital_social'),
                    'funcionarios_estimado': empresa_imp.get('funcionarios_estimado'),
                    'peso_participacao': empresa_imp['peso_participacao'],
                    'sugestao': 'FORNECEDOR_POTENCIAL',  # Empresa que importa pode fornecer para quem exporta
                    'dados_estimados': empresa_imp.get('dados_estimados', True)
                })
            
            for _, empresa_exp in empresas_exportadoras.head(10).iterrows():
                sugestoes_list.append({
                    'cnpj': empresa_exp['cnpj'],
                    'razao_social': empresa_exp['razao_social'],
                    'nome_fantasia': empresa_exp['nome_fantasia'],
                    'cnae': empresa_exp['cnae'],
                    'estado': empresa_exp['estado'],
                    'endereco': empresa_exp['endereco'],
                    'ncm': ncm,
                    'descricao_ncm': empresa_exp['descricao_ncm'],
                    'valor_importacao_usd': empresa_exp['valor_importacao_usd'],
                    'valor_exportacao_usd': empresa_exp['valor_exportacao_usd'],
                    'capital_social': empresa_exp.get('capital_social'),
                    'funcionarios_estimado': empresa_exp.get('funcionarios_estimado'),
                    'peso_participacao': empresa_exp['peso_participacao'],
                    'sugestao': 'CLIENTE_POTENCIAL',  # Empresa que exporta pode ser cliente de quem importa
                    'dados_estimados': empresa_exp.get('dados_estimados', True)
                })
        
        logger.info(f"✅ Sugestões geradas: {len(sugestoes_list)}")
        return sugestoes_list


