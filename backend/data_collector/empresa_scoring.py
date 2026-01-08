"""
Módulo de cálculo de score (PESO_PARTICIPACAO) para empresas.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from loguru import logger


class EmpresaScoring:
    """
    Calcula PESO_PARTICIPACAO para empresas baseado em:
    - 50% volume financeiro importado
    - 40% volume financeiro exportado  
    - 10% quantidade de NCM movimentados
    """
    
    def __init__(self):
        self.peso_importacao = 0.50
        self.peso_exportacao = 0.40
        self.peso_ncms = 0.10
    
    def calcular_peso_participacao(self, empresas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calcula PESO_PARTICIPACAO para cada empresa.
        
        Args:
            empresas: Lista de empresas com dados financeiros e NCMs
            
        Returns:
            Lista de empresas com campo peso_participacao adicionado
        """
        logger.info("Calculando PESO_PARTICIPACAO para empresas...")
        
        if not empresas:
            return empresas
        
        # Converter para DataFrame para facilitar cálculos
        df = pd.DataFrame(empresas)
        
        # Normalizar valores de importação (0-100)
        if df['valor_importacao_usd'].max() > 0:
            df['score_importacao'] = (df['valor_importacao_usd'] / df['valor_importacao_usd'].max()) * 100
        else:
            df['score_importacao'] = 0
        
        # Normalizar valores de exportação (0-100)
        if df['valor_exportacao_usd'].max() > 0:
            df['score_exportacao'] = (df['valor_exportacao_usd'] / df['valor_exportacao_usd'].max()) * 100
        else:
            df['score_exportacao'] = 0
        
        # Calcular quantidade de NCMs únicos
        def contar_ncms_unicos(ncms_str):
            if pd.isna(ncms_str) or not ncms_str:
                return 0
            ncms_list = [n.strip() for n in str(ncms_str).split(',') if n.strip()]
            return len(set(ncms_list))
        
        df['qtd_ncms_unicos'] = df['ncms_importacao'].apply(contar_ncms_unicos) + \
                                df['ncms_exportacao'].apply(contar_ncms_unicos)
        
        # Normalizar quantidade de NCMs (0-100)
        if df['qtd_ncms_unicos'].max() > 0:
            df['score_ncms'] = (df['qtd_ncms_unicos'] / df['qtd_ncms_unicos'].max()) * 100
        else:
            df['score_ncms'] = 0
        
        # Calcular PESO_PARTICIPACAO final
        df['peso_participacao'] = (
            df['score_importacao'] * self.peso_importacao +
            df['score_exportacao'] * self.peso_exportacao +
            df['score_ncms'] * self.peso_ncms
        )
        
        # Garantir que está entre 0 e 100
        df['peso_participacao'] = df['peso_participacao'].clip(0, 100)
        
        # Converter de volta para lista de dicionários
        empresas_com_score = df.to_dict('records')
        
        logger.info(f"✅ PESO_PARTICIPACAO calculado para {len(empresas_com_score)} empresas")
        logger.info(f"   - Score médio: {df['peso_participacao'].mean():.2f}")
        logger.info(f"   - Score máximo: {df['peso_participacao'].max():.2f}")
        logger.info(f"   - Score mínimo: {df['peso_participacao'].min():.2f}")
        
        return empresas_com_score


