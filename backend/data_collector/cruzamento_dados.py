"""
Sistema de cruzamento de dados entre diferentes fontes.
Cruza dados do Comex Stat com lista de empresas do MDIC e outras fontes.
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import OperacaoComex
from .empresas_mdic_scraper import EmpresasMDICScraper


class CruzamentoDados:
    """
    Classe para cruzar dados de diferentes fontes.
    """
    
    def __init__(self):
        self.empresas_scraper = EmpresasMDICScraper()
        self.cache_empresas: Dict[str, Dict[str, Any]] = {}
    
    async def carregar_empresas_mdic(self, ano: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Carrega lista de empresas do MDIC e cria índice por CNPJ.
        
        Args:
            ano: Ano específico (None = ano atual)
        
        Returns:
            Dicionário indexado por CNPJ
        """
        empresas = await self.empresas_scraper.coletar_empresas(ano)
        
        # Criar índice por CNPJ
        indice = {}
        for empresa in empresas:
            cnpj = empresa.get("cnpj")
            if cnpj:
                # Pode haver múltiplas empresas com mesmo CNPJ (exportadora e importadora)
                if cnpj not in indice:
                    indice[cnpj] = []
                indice[cnpj].append(empresa)
        
        self.cache_empresas = indice
        logger.info(f"✅ {len(indice)} CNPJs únicos carregados do MDIC")
        return indice
    
    def cruzar_operacao_com_empresa(
        self,
        operacao: OperacaoComex,
        empresas_mdic: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Cruza uma operação com dados de empresa do MDIC.
        
        Args:
            operacao: Operação do banco de dados
            empresas_mdic: Índice de empresas (se None, usa cache)
        
        Returns:
            Dicionário com operação enriquecida
        """
        if empresas_mdic is None:
            empresas_mdic = self.cache_empresas
        
        resultado = {
            "operacao": {
                "id": operacao.id,
                "ncm": operacao.ncm,
                "tipo_operacao": operacao.tipo_operacao.value if operacao.tipo_operacao else None,
                "valor_fob": float(operacao.valor_fob) if operacao.valor_fob else 0.0,
                "peso_liquido_kg": float(operacao.peso_liquido_kg) if operacao.peso_liquido_kg else 0.0,
                "pais": operacao.pais_origem_destino,
                "uf": operacao.uf,
                "data": operacao.data_operacao.isoformat() if operacao.data_operacao else None,
            },
            "empresa_identificada": False,
            "empresa_dados": None,
            "confianca": "baixa"
        }
        
        # Tentar identificar empresa pelo CNPJ
        cnpj_importador = operacao.cnpj_importador
        cnpj_exportador = operacao.cnpj_exportador
        
        empresa_encontrada = None
        
        if operacao.tipo_operacao == "Importação" and cnpj_importador:
            empresa_encontrada = empresas_mdic.get(cnpj_importador)
            resultado["confianca"] = "alta"  # CNPJ direto = alta confiança
        elif operacao.tipo_operacao == "Exportação" and cnpj_exportador:
            empresa_encontrada = empresas_mdic.get(cnpj_exportador)
            resultado["confianca"] = "alta"
        
        # Se não encontrou por CNPJ, tentar por razão social
        if not empresa_encontrada:
            razao_social = None
            if operacao.tipo_operacao == "Importação":
                razao_social = operacao.razao_social_importador
            elif operacao.tipo_operacao == "Exportação":
                razao_social = operacao.razao_social_exportador
            
            if razao_social:
                # Buscar por nome (busca parcial)
                for cnpj, empresas_lista in empresas_mdic.items():
                    for empresa in empresas_lista:
                        if razao_social.lower() in empresa.get("razao_social", "").lower():
                            empresa_encontrada = empresas_lista
                            resultado["confianca"] = "media"  # Nome = confiança média
                            break
                    if empresa_encontrada:
                        break
        
        if empresa_encontrada:
            resultado["empresa_identificada"] = True
            # Pegar primeira empresa (ou consolidar se houver múltiplas)
            empresa_principal = empresa_encontrada[0] if isinstance(empresa_encontrada, list) else empresa_encontrada
            resultado["empresa_dados"] = {
                "cnpj": empresa_principal.get("cnpj"),
                "razao_social": empresa_principal.get("razao_social"),
                "nome_fantasia": empresa_principal.get("nome_fantasia"),
                "uf": empresa_principal.get("uf"),
                "municipio": empresa_principal.get("municipio"),
                "faixa_valor": empresa_principal.get("faixa_valor"),
            }
        
        return resultado
    
    async def cruzar_operacoes_bulk(
        self,
        db: Session,
        filtros: Optional[Dict[str, Any]] = None,
        limite: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Cruza múltiplas operações com dados de empresas.
        
        Args:
            db: Sessão do banco de dados
            filtros: Filtros para operações (NCM, tipo, etc.)
            limite: Limite de operações a processar
        
        Returns:
            Lista de operações cruzadas
        """
        # Carregar empresas do MDIC
        await self.carregar_empresas_mdic()
        
        # Buscar operações
        query = db.query(OperacaoComex)
        
        if filtros:
            if filtros.get("ncm"):
                query = query.filter(OperacaoComex.ncm == filtros["ncm"])
            if filtros.get("tipo_operacao"):
                query = query.filter(OperacaoComex.tipo_operacao == filtros["tipo_operacao"])
            if filtros.get("uf"):
                query = query.filter(OperacaoComex.uf == filtros["uf"])
        
        operacoes = query.limit(limite).all()
        
        logger.info(f"Cruzando {len(operacoes)} operações com dados de empresas...")
        
        resultados = []
        identificadas = 0
        
        for operacao in operacoes:
            resultado = self.cruzar_operacao_com_empresa(operacao)
            resultados.append(resultado)
            
            if resultado["empresa_identificada"]:
                identificadas += 1
        
        if len(operacoes) > 0:
            logger.info(f"✅ {identificadas}/{len(operacoes)} operações identificadas com empresas ({identificadas/len(operacoes)*100:.1f}%)")
        else:
            logger.info(f"✅ {identificadas} operações identificadas (nenhuma operação para processar)")
        
        return resultados
    
    def estatisticas_cruzamento(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera estatísticas do cruzamento.
        
        Args:
            resultados: Lista de resultados do cruzamento
        
        Returns:
            Dicionário com estatísticas
        """
        total = len(resultados)
        identificadas = sum(1 for r in resultados if r["empresa_identificada"])
        
        por_confianca = {
            "alta": sum(1 for r in resultados if r.get("confianca") == "alta"),
            "media": sum(1 for r in resultados if r.get("confianca") == "media"),
            "baixa": sum(1 for r in resultados if r.get("confianca") == "baixa"),
        }
        
        empresas_unicas = set()
        for r in resultados:
            if r["empresa_identificada"]:
                cnpj = r["empresa_dados"].get("cnpj")
                if cnpj:
                    empresas_unicas.add(cnpj)
        
        return {
            "total_operacoes": total,
            "operacoes_identificadas": identificadas,
            "taxa_identificacao": identificadas / total * 100 if total > 0 else 0,
            "por_confianca": por_confianca,
            "empresas_unicas": len(empresas_unicas),
        }



