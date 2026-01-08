"""
Coletor de dados de empresas brasileiras importadoras e exportadoras.
Busca dados em fontes públicas, APIs governamentais e agregadores.
"""
import sys
from pathlib import Path
import os
import re
import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger
import time
from datetime import datetime

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_db
from database.models import OperacaoComex
from sqlalchemy import func, extract


class EmpresaDataCollector:
    """
    Coletor de dados de empresas para análise de comércio exterior.
    """
    
    def __init__(self):
        self.empresas_coletadas: List[Dict[str, Any]] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def validar_cnpj(self, cnpj: str) -> bool:
        """
        Valida formato de CNPJ brasileiro.
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            True se válido, False caso contrário
        """
        # Remover formatação
        cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
        
        # Verificar tamanho
        if len(cnpj_limpo) != 14:
            return False
        
        # Verificar se todos os dígitos são iguais (CNPJ inválido)
        if len(set(cnpj_limpo)) == 1:
            return False
        
        # Validar dígitos verificadores
        def calcular_digito(cnpj: str, posicoes: List[int]) -> int:
            soma = sum(int(cnpj[i]) * posicoes[i] for i in range(len(posicoes)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        # Validar primeiro dígito
        posicoes_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        digito_1 = calcular_digito(cnpj_limpo, posicoes_1)
        if digito_1 != int(cnpj_limpo[12]):
            return False
        
        # Validar segundo dígito
        posicoes_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        digito_2 = calcular_digito(cnpj_limpo, posicoes_2)
        if digito_2 != int(cnpj_limpo[13]):
            return False
        
        return True
    
    def formatar_cnpj(self, cnpj: str) -> str:
        """Formata CNPJ para padrão XX.XXX.XXX/XXXX-XX"""
        cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
        if len(cnpj_limpo) == 14:
            return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"
        return cnpj_limpo
    
    def buscar_empresas_banco_dados(self, limite: int = 5000) -> List[Dict[str, Any]]:
        """
        Busca empresas do banco de dados interno.
        
        Args:
            limite: Número máximo de empresas a retornar
            
        Returns:
            Lista de empresas com dados completos
        """
        logger.info(f"Buscando até {limite} empresas no banco de dados...")
        db = next(get_db())
        
        empresas_list = []
        
        try:
            # Buscar empresas importadoras (todos os anos)
            empresas_imp = db.query(
                OperacaoComex.razao_social_importador,
                OperacaoComex.cnpj_importador,
                OperacaoComex.uf,
                func.sum(OperacaoComex.valor_fob).label('valor_importacao'),
                func.count(OperacaoComex.id).label('qtd_operacoes_imp'),
                func.group_concat(OperacaoComex.ncm.distinct()).label('ncms_importacao'),
                func.sum(OperacaoComex.peso_liquido_kg).label('peso_importacao_kg')
            ).filter(
                OperacaoComex.tipo_operacao == 'IMPORTACAO',
                OperacaoComex.razao_social_importador.isnot(None),
                OperacaoComex.cnpj_importador.isnot(None)
            ).group_by(
                OperacaoComex.cnpj_importador,
                OperacaoComex.razao_social_importador,
                OperacaoComex.uf
            ).order_by(func.sum(OperacaoComex.valor_fob).desc()).limit(limite // 2).all()
            
            # Buscar empresas exportadoras (todos os anos)
            empresas_exp = db.query(
                OperacaoComex.razao_social_exportador,
                OperacaoComex.cnpj_exportador,
                OperacaoComex.uf,
                func.sum(OperacaoComex.valor_fob).label('valor_exportacao'),
                func.count(OperacaoComex.id).label('qtd_operacoes_exp'),
                func.group_concat(OperacaoComex.ncm.distinct()).label('ncms_exportacao'),
                func.sum(OperacaoComex.peso_liquido_kg).label('peso_exportacao_kg')
            ).filter(
                OperacaoComex.tipo_operacao == 'EXPORTACAO',
                OperacaoComex.razao_social_exportador.isnot(None),
                OperacaoComex.cnpj_exportador.isnot(None)
            ).group_by(
                OperacaoComex.cnpj_exportador,
                OperacaoComex.razao_social_exportador,
                OperacaoComex.uf
            ).order_by(func.sum(OperacaoComex.valor_fob).desc()).limit(limite // 2).all()
            
            # Processar importadoras
            for emp in empresas_imp:
                cnpj = str(emp.cnpj_importador).replace('.', '').replace('/', '').replace('-', '')
                if self.validar_cnpj(cnpj):
                    empresas_list.append({
                        'cnpj': self.formatar_cnpj(cnpj),
                        'razao_social': emp.razao_social_importador,
                        'nome_fantasia': emp.razao_social_importador,  # Será preenchido depois se disponível
                        'cnae': '',  # Será preenchido depois
                        'estado': emp.uf or '',
                        'endereco': '',  # Será preenchido depois
                        'ncms_importacao': emp.ncms_importacao or '',
                        'ncms_exportacao': '',
                        'valor_importacao_usd': float(emp.valor_importacao) if emp.valor_importacao else 0,
                        'valor_exportacao_usd': 0,
                        'qtd_operacoes_imp': emp.qtd_operacoes_imp,
                        'qtd_operacoes_exp': 0,
                        'peso_importacao_kg': float(emp.peso_importacao_kg) if emp.peso_importacao_kg else 0,
                        'peso_exportacao_kg': 0,
                        'capital_social': None,  # Será preenchido depois
                        'funcionarios_estimado': None,  # Será preenchido depois
                        'dados_estimados': True,  # Flag para dados que precisam ser buscados
                        'fonte': 'banco_dados_interno'
                    })
            
            # Processar exportadoras
            for emp in empresas_exp:
                cnpj = str(emp.cnpj_exportador).replace('.', '').replace('/', '').replace('-', '')
                if self.validar_cnpj(cnpj):
                    # Verificar se já existe na lista
                    empresa_existente = next((e for e in empresas_list if e['cnpj'] == self.formatar_cnpj(cnpj)), None)
                    
                    if empresa_existente:
                        # Atualizar dados existentes
                        empresa_existente['ncms_exportacao'] = emp.ncms_exportacao or ''
                        empresa_existente['valor_exportacao_usd'] = float(emp.valor_exportacao) if emp.valor_exportacao else 0
                        empresa_existente['qtd_operacoes_exp'] = emp.qtd_operacoes_exp
                        empresa_existente['peso_exportacao_kg'] = float(emp.peso_exportacao_kg) if emp.peso_exportacao_kg else 0
                    else:
                        # Criar nova entrada
                        empresas_list.append({
                            'cnpj': self.formatar_cnpj(cnpj),
                            'razao_social': emp.razao_social_exportador,
                            'nome_fantasia': emp.razao_social_exportador,
                            'cnae': '',
                            'estado': emp.uf or '',
                            'endereco': '',
                            'ncms_importacao': '',
                            'ncms_exportacao': emp.ncms_exportacao or '',
                            'valor_importacao_usd': 0,
                            'valor_exportacao_usd': float(emp.valor_exportacao) if emp.valor_exportacao else 0,
                            'qtd_operacoes_imp': 0,
                            'qtd_operacoes_exp': emp.qtd_operacoes_exp,
                            'peso_importacao_kg': 0,
                            'peso_exportacao_kg': float(emp.peso_exportacao_kg) if emp.peso_exportacao_kg else 0,
                            'capital_social': None,
                            'funcionarios_estimado': None,
                            'dados_estimados': True,
                            'fonte': 'banco_dados_interno'
                        })
            
            logger.info(f"✅ Encontradas {len(empresas_list)} empresas no banco de dados")
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresas no banco: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return empresas_list
    
    def buscar_dados_receita_ws(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados da ReceitaWS (API pública gratuita).
        
        Args:
            cnpj: CNPJ sem formatação
            
        Returns:
            Dados da empresa ou None
        """
        try:
            cnpj_limpo = re.sub(r'[^\d]', '', cnpj)
            url = f"https://www.receitaws.com.br/v1/{cnpj_limpo}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK':
                    return {
                        'nome_fantasia': data.get('fantasia', ''),
                        'endereco': self._formatar_endereco_receita_ws(data),
                        'cnae': data.get('atividade_principal', [{}])[0].get('code', '') if data.get('atividade_principal') else '',
                        'capital_social': self._extrair_capital_social(data),
                        'situacao': data.get('situacao', ''),
                        'abertura': data.get('abertura', ''),
                        'municipio': data.get('municipio', ''),
                        'uf': data.get('uf', ''),
                        'telefone': data.get('telefone', ''),
                        'email': data.get('email', '')
                    }
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            logger.debug(f"Erro ao buscar dados ReceitaWS para {cnpj}: {e}")
        
        return None
    
    def _formatar_endereco_receita_ws(self, data: Dict) -> str:
        """Formata endereço completo a partir dos dados da ReceitaWS."""
        partes = []
        if data.get('logradouro'):
            partes.append(data['logradouro'])
        if data.get('numero'):
            partes.append(data['numero'])
        if data.get('bairro'):
            partes.append(data['bairro'])
        if data.get('municipio'):
            partes.append(data['municipio'])
        if data.get('uf'):
            partes.append(data['uf'])
        if data.get('cep'):
            partes.append(f"CEP: {data['cep']}")
        
        return ', '.join(partes)
    
    def _extrair_capital_social(self, data: Dict) -> Optional[float]:
        """Extrai capital social dos dados da ReceitaWS."""
        capital_str = data.get('capital_social', '')
        if capital_str:
            # Remover formatação e converter
            capital_limpo = re.sub(r'[^\d,]', '', str(capital_str))
            capital_limpo = capital_limpo.replace(',', '.')
            try:
                return float(capital_limpo)
            except:
                pass
        return None
    
    def estimar_funcionarios(self, valor_total_usd: float, cnae: str = '') -> Optional[int]:
        """
        Estima número de funcionários baseado em heurísticas.
        
        Args:
            valor_total_usd: Valor total de importação + exportação em USD
            cnae: CNAE da empresa (opcional)
            
        Returns:
            Número estimado de funcionários
        """
        # Converter USD para BRL (aproximadamente 5.0)
        valor_total_brl = valor_total_usd * 5.0
        
        # Heurística básica: empresas com maior faturamento tendem a ter mais funcionários
        # Mas isso varia muito por setor, então é uma estimativa grosseira
        if valor_total_brl < 1_000_000:  # < 1M BRL
            return 10
        elif valor_total_brl < 10_000_000:  # < 10M BRL
            return 50
        elif valor_total_brl < 50_000_000:  # < 50M BRL
            return 200
        elif valor_total_brl < 200_000_000:  # < 200M BRL
            return 500
        else:  # >= 200M BRL
            return 1000
    
    def enriquecer_dados_empresas(self, empresas: List[Dict[str, Any]], limite_api: int = 100) -> List[Dict[str, Any]]:
        """
        Enriquece dados das empresas buscando informações adicionais.
        
        Args:
            empresas: Lista de empresas para enriquecer
            limite_api: Limite de chamadas à API (para evitar rate limiting)
            
        Returns:
            Lista de empresas enriquecidas
        """
        logger.info(f"Enriquecendo dados de {len(empresas)} empresas...")
        
        empresas_enriquecidas = []
        chamadas_api = 0
        
        for empresa in empresas:
            empresa_enriquecida = empresa.copy()
            cnpj_limpo = re.sub(r'[^\d]', '', empresa['cnpj'])
            
            # Buscar dados da ReceitaWS se ainda não tiver dados completos
            if empresa.get('dados_estimados', True) and chamadas_api < limite_api:
                dados_receita = self.buscar_dados_receita_ws(cnpj_limpo)
                if dados_receita:
                    empresa_enriquecida['nome_fantasia'] = dados_receita.get('nome_fantasia') or empresa_enriquecida.get('nome_fantasia', '')
                    empresa_enriquecida['endereco'] = dados_receita.get('endereco') or empresa_enriquecida.get('endereco', '')
                    empresa_enriquecida['cnae'] = dados_receita.get('cnae') or empresa_enriquecida.get('cnae', '')
                    empresa_enriquecida['estado'] = dados_receita.get('uf') or empresa_enriquecida.get('estado', '')
                    empresa_enriquecida['capital_social'] = dados_receita.get('capital_social') or empresa_enriquecida.get('capital_social')
                    empresa_enriquecida['dados_estimados'] = False  # Dados reais encontrados
                    chamadas_api += 1
            
            # Estimar funcionários se não tiver
            if empresa_enriquecida.get('funcionarios_estimado') is None:
                valor_total = empresa_enriquecida.get('valor_importacao_usd', 0) + empresa_enriquecida.get('valor_exportacao_usd', 0)
                empresa_enriquecida['funcionarios_estimado'] = self.estimar_funcionarios(valor_total, empresa_enriquecida.get('cnae', ''))
                if empresa_enriquecida.get('dados_estimados', True):
                    empresa_enriquecida['funcionarios_estimado_flag'] = 'estimado'
            
            empresas_enriquecidas.append(empresa_enriquecida)
        
        logger.info(f"✅ Dados enriquecidos para {len(empresas_enriquecidas)} empresas")
        return empresas_enriquecidas
    
    def buscar_empresas_excel(self, limite: int = 5000) -> List[Dict[str, Any]]:
        """
        Busca empresas do arquivo Excel como fonte alternativa.
        
        Args:
            limite: Número máximo de empresas a retornar
            
        Returns:
            Lista de empresas
        """
        logger.info("Buscando empresas no arquivo Excel...")
        
        arquivo_excel = backend_dir.parent / "comex_data" / "comexstat_csv" / "H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
        
        if not arquivo_excel.exists():
            logger.warning(f"Arquivo Excel não encontrado: {arquivo_excel}")
            return []
        
        try:
            df = pd.read_excel(arquivo_excel)
            logger.info(f"✅ Arquivo Excel lido: {len(df)} linhas")
            
            empresas_list = []
            empresas_dict = {}
            
            # Processar exportações
            df_exp = df[df['Exportação - 2025 - Valor US$ FOB'].notna() & (df['Exportação - 2025 - Valor US$ FOB'] > 0)]
            df_exp_agrupado = df_exp.groupby(['UF do Produto', 'Código NCM']).agg({
                'Exportação - 2025 - Valor US$ FOB': 'sum',
                'Descrição NCM': 'first'
            }).reset_index()
            
            for idx, row in df_exp_agrupado.head(limite // 2).iterrows():
                uf = str(row['UF do Produto'])
                ncm = str(row['Código NCM'])
                chave = f"EXP_{uf}_{idx}"
                
                empresas_dict[chave] = {
                    'cnpj': f"EXP{idx:010d}",  # CNPJ fictício
                    'razao_social': f'Empresa Exportadora - {uf}',
                    'nome_fantasia': f'Empresa Exportadora - {uf}',
                    'cnae': '',
                    'estado': uf,
                    'endereco': f'{uf}, Brasil',
                    'ncms_importacao': '',
                    'ncms_exportacao': ncm,
                    'valor_importacao_usd': 0,
                    'valor_exportacao_usd': float(row['Exportação - 2025 - Valor US$ FOB']),
                    'qtd_operacoes_imp': 0,
                    'qtd_operacoes_exp': 1,
                    'peso_importacao_kg': 0,
                    'peso_exportacao_kg': 0,
                    'capital_social': None,
                    'funcionarios_estimado': None,
                    'dados_estimados': True,
                    'fonte': 'arquivo_excel'
                }
            
            # Processar importações
            df_imp = df[df['Importação - 2025 - Valor US$ FOB'].notna() & (df['Importação - 2025 - Valor US$ FOB'] > 0)]
            df_imp_agrupado = df_imp.groupby(['UF do Produto', 'Código NCM']).agg({
                'Importação - 2025 - Valor US$ FOB': 'sum',
                'Descrição NCM': 'first'
            }).reset_index()
            
            for idx, row in df_imp_agrupado.head(limite // 2).iterrows():
                uf = str(row['UF do Produto'])
                ncm = str(row['Código NCM'])
                chave = f"IMP_{uf}_{idx}"
                
                empresas_dict[chave] = {
                    'cnpj': f"IMP{idx:010d}",  # CNPJ fictício
                    'razao_social': f'Empresa Importadora - {uf}',
                    'nome_fantasia': f'Empresa Importadora - {uf}',
                    'cnae': '',
                    'estado': uf,
                    'endereco': f'{uf}, Brasil',
                    'ncms_importacao': ncm,
                    'ncms_exportacao': '',
                    'valor_importacao_usd': float(row['Importação - 2025 - Valor US$ FOB']),
                    'valor_exportacao_usd': 0,
                    'qtd_operacoes_imp': 1,
                    'qtd_operacoes_exp': 0,
                    'peso_importacao_kg': 0,
                    'peso_exportacao_kg': 0,
                    'capital_social': None,
                    'funcionarios_estimado': None,
                    'dados_estimados': True,
                    'fonte': 'arquivo_excel'
                }
            
            empresas_list = list(empresas_dict.values())
            logger.info(f"✅ Encontradas {len(empresas_list)} empresas no arquivo Excel")
            
            return empresas_list
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo Excel: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def coletar_empresas(self, limite: int = 5000) -> List[Dict[str, Any]]:
        """
        Método principal para coletar empresas.
        
        Args:
            limite: Número máximo de empresas a coletar
            
        Returns:
            Lista de empresas coletadas e enriquecidas
        """
        logger.info("="*60)
        logger.info("COLETA DE EMPRESAS - INÍCIO")
        logger.info("="*60)
        
        # 1. Buscar empresas do banco de dados
        empresas = self.buscar_empresas_banco_dados(limite=limite)
        
        # 2. Se não encontrou no banco, buscar no Excel
        if len(empresas) == 0:
            logger.info("Nenhuma empresa no banco, buscando no arquivo Excel...")
            empresas = self.buscar_empresas_excel(limite=limite)
        
        # 3. Enriquecer dados
        empresas = self.enriquecer_dados_empresas(empresas, limite_api=min(100, len(empresas)))
        
        # 4. Remover duplicatas (por CNPJ)
        empresas_unicas = {}
        for emp in empresas:
            cnpj = emp['cnpj']
            if cnpj not in empresas_unicas:
                empresas_unicas[cnpj] = emp
            else:
                # Mesclar dados se houver duplicata
                existente = empresas_unicas[cnpj]
                existente['ncms_importacao'] = f"{existente.get('ncms_importacao', '')},{emp.get('ncms_importacao', '')}"
                existente['ncms_exportacao'] = f"{existente.get('ncms_exportacao', '')},{emp.get('ncms_exportacao', '')}"
                existente['valor_importacao_usd'] += emp.get('valor_importacao_usd', 0)
                existente['valor_exportacao_usd'] += emp.get('valor_exportacao_usd', 0)
        
        empresas_finais = list(empresas_unicas.values())
        logger.info(f"✅ Total de empresas únicas coletadas: {len(empresas_finais)}")
        
        self.empresas_coletadas = empresas_finais
        return empresas_finais

