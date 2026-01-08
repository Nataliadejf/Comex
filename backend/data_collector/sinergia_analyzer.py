"""
Analisador de sinergias entre importações e exportações.
Identifica oportunidades de negócio baseado em padrões de dados.
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from database import OperacaoComex, TipoOperacao
from .cnae_analyzer import CNAEAnalyzer


class SinergiaAnalyzer:
    """
    Analisa sinergias entre importações e exportações por empresa e estado.
    """
    
    def __init__(self, cnae_analyzer: Optional[CNAEAnalyzer] = None):
        """
        Inicializa o analisador de sinergias.
        
        Args:
            cnae_analyzer: Analisador de CNAE (opcional)
        """
        self.cnae_analyzer = cnae_analyzer
    
    def analisar_sinergias_por_estado(
        self,
        db: Session,
        uf: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analisa sinergias de importação/exportação por estado.
        
        Args:
            db: Sessão do banco de dados
            uf: UF específica (None = todos)
        
        Returns:
            Dicionário com análise de sinergias
        """
        logger.info(f"Analisando sinergias por estado: {uf or 'Todos'}")
        
        # Filtros
        filtros = []
        if uf:
            filtros.append(OperacaoComex.uf == uf)
        
        # Importações por estado
        importacoes = db.query(
            OperacaoComex.uf,
            func.count(OperacaoComex.id).label('total'),
            func.sum(OperacaoComex.valor_fob).label('valor_total'),
            func.sum(OperacaoComex.peso_liquido_kg).label('peso_total')
        ).filter(
            and_(
                OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO,
                *filtros
            )
        ).group_by(OperacaoComex.uf).all()
        
        # Exportações por estado
        exportacoes = db.query(
            OperacaoComex.uf,
            func.count(OperacaoComex.id).label('total'),
            func.sum(OperacaoComex.valor_fob).label('valor_total'),
            func.sum(OperacaoComex.peso_liquido_kg).label('peso_total')
        ).filter(
            and_(
                OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO,
                *filtros
            )
        ).group_by(OperacaoComex.uf).all()
        
        # Criar dicionários
        imp_por_uf = {
            uf: {
                "total": int(total),
                "valor_total": float(valor_total) if valor_total else 0.0,
                "peso_total": float(peso_total) if peso_total else 0.0
            }
            for uf, total, valor_total, peso_total in importacoes
        }
        
        exp_por_uf = {
            uf: {
                "total": int(total),
                "valor_total": float(valor_total) if valor_total else 0.0,
                "peso_total": float(peso_total) if peso_total else 0.0
            }
            for uf, total, valor_total, peso_total in exportacoes
        }
        
        # Calcular sinergias
        sinergias = []
        todos_ufs = set(list(imp_por_uf.keys()) + list(exp_por_uf.keys()))
        
        for estado in todos_ufs:
            imp = imp_por_uf.get(estado, {"total": 0, "valor_total": 0.0, "peso_total": 0.0})
            exp = exp_por_uf.get(estado, {"total": 0, "valor_total": 0.0, "peso_total": 0.0})
            
            # Calcular índice de sinergia
            # Estados que fazem ambos têm maior sinergia
            if imp["total"] > 0 and exp["total"] > 0:
                indice_sinergia = min(imp["valor_total"], exp["valor_total"]) / max(imp["valor_total"], exp["valor_total"]) if max(imp["valor_total"], exp["valor_total"]) > 0 else 0
                
                sinergias.append({
                    "uf": estado,
                    "importacoes": imp,
                    "exportacoes": exp,
                    "indice_sinergia": indice_sinergia,
                    "sugestao": self._gerar_sugestao_estado(imp, exp, indice_sinergia)
                })
        
        # Ordenar por índice de sinergia
        sinergias.sort(key=lambda x: x["indice_sinergia"], reverse=True)
        
        return {
            "uf_filtrada": uf,
            "total_estados": len(todos_ufs),
            "estados_com_sinergia": len(sinergias),
            "sinergias": sinergias[:20]  # Top 20
        }
    
    def analisar_sinergias_por_empresa(
        self,
        db: Session,
        empresas_mdic: Dict[str, Dict[str, Any]],
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Analisa sinergias por empresa usando dados do MDIC.
        
        Args:
            db: Sessão do banco de dados
            empresas_mdic: Dicionário de empresas do MDIC indexado por CNPJ
            limite: Limite de empresas a analisar
        
        Returns:
            Lista de empresas com análise de sinergia
        """
        logger.info(f"Analisando sinergias por empresa (limite: {limite})")
        
        resultados = []
        
        # Buscar empresas que têm CNPJ nas operações
        empresas_com_cnpj = db.query(
            OperacaoComex.cnpj_importador,
            OperacaoComex.cnpj_exportador,
            OperacaoComex.uf
        ).filter(
            or_(
                OperacaoComex.cnpj_importador.isnot(None),
                OperacaoComex.cnpj_exportador.isnot(None)
            )
        ).distinct().limit(limite).all()
        
        cnpjs_processados = set()
        
        for cnpj_imp, cnpj_exp, uf in empresas_com_cnpj:
            # Processar importador
            if cnpj_imp and cnpj_imp not in cnpjs_processados:
                cnpj_limpo = cnpj_imp.replace('.', '').replace('/', '').replace('-', '')
                empresa_mdic = empresas_mdic.get(cnpj_limpo)
                
                if empresa_mdic:
                    sinergia = self._analisar_empresa_individual(db, cnpj_limpo, empresa_mdic, uf)
                    if sinergia:
                        resultados.append(sinergia)
                        cnpjs_processados.add(cnpj_imp)
            
            # Processar exportador
            if cnpj_exp and cnpj_exp not in cnpjs_processados:
                cnpj_limpo = cnpj_exp.replace('.', '').replace('/', '').replace('-', '')
                empresa_mdic = empresas_mdic.get(cnpj_limpo)
                
                if empresa_mdic:
                    sinergia = self._analisar_empresa_individual(db, cnpj_limpo, empresa_mdic, uf)
                    if sinergia:
                        resultados.append(sinergia)
                        cnpjs_processados.add(cnpj_exp)
        
        # Ordenar por potencial de sinergia
        resultados.sort(key=lambda x: x.get("potencial_sinergia", 0), reverse=True)
        
        return resultados
    
    def _analisar_empresa_individual(
        self,
        db: Session,
        cnpj: str,
        empresa_mdic: Dict[str, Any],
        uf: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Analisa sinergia de uma empresa individual.
        """
        # Buscar operações da empresa
        importacoes = db.query(
            func.count(OperacaoComex.id).label('total'),
            func.sum(OperacaoComex.valor_fob).label('valor_total')
        ).filter(
            and_(
                OperacaoComex.cnpj_importador == cnpj,
                OperacaoComex.tipo_operacao == TipoOperacao.IMPORTACAO
            )
        ).first()
        
        exportacoes = db.query(
            func.count(OperacaoComex.id).label('total'),
            func.sum(OperacaoComex.valor_fob).label('valor_total')
        ).filter(
            and_(
                OperacaoComex.cnpj_exportador == cnpj,
                OperacaoComex.tipo_operacao == TipoOperacao.EXPORTACAO
            )
        ).first()
        
        imp_total = importacoes.total or 0
        imp_valor = float(importacoes.valor_total) if importacoes.valor_total else 0.0
        
        exp_total = exportacoes.total or 0
        exp_valor = float(exportacoes.valor_total) if exportacoes.valor_total else 0.0
        
        # Buscar CNAE se disponível
        cnae_info = None
        if self.cnae_analyzer:
            cnae_info = self.cnae_analyzer.buscar_cnae_empresa(cnpj)
        
        # Calcular potencial
        potencial = 0.0
        if imp_total > 0 and exp_total > 0:
            potencial = 1.0  # Já faz ambos
        elif imp_total > 0:
            potencial = 0.5  # Só importa - pode exportar
        elif exp_total > 0:
            potencial = 0.5  # Só exporta - pode importar
        
        return {
            "cnpj": cnpj,
            "razao_social": empresa_mdic.get("razao_social"),
            "nome_fantasia": empresa_mdic.get("nome_fantasia"),
            "uf": empresa_mdic.get("uf") or uf,
            "municipio": empresa_mdic.get("municipio"),
            "importacoes": {
                "total_operacoes": imp_total,
                "valor_total": imp_valor
            },
            "exportacoes": {
                "total_operacoes": exp_total,
                "valor_total": exp_valor
            },
            "potencial_sinergia": potencial,
            "cnae": cnae_info.get("cnae") if cnae_info else None,
            "classificacao_cnae": cnae_info.get("classificacao") if cnae_info else None,
            "sugestao": self._gerar_sugestao_empresa(imp_total, exp_total, imp_valor, exp_valor, cnae_info)
        }
    
    def _gerar_sugestao_estado(
        self,
        imp: Dict[str, Any],
        exp: Dict[str, Any],
        indice: float
    ) -> str:
        """Gera sugestão baseada em análise de estado."""
        if indice > 0.7:
            return "Estado com alta sinergia - empresas podem diversificar operações"
        elif indice > 0.3:
            return "Estado com sinergia moderada - oportunidades de crescimento"
        elif imp["valor_total"] > exp["valor_total"] * 2:
            return "Estado importador - oportunidades de exportação"
        elif exp["valor_total"] > imp["valor_total"] * 2:
            return "Estado exportador - oportunidades de importação"
        else:
            return "Estado equilibrado - potencial para ambas operações"
    
    def _gerar_sugestao_empresa(
        self,
        imp_total: int,
        exp_total: int,
        imp_valor: float,
        exp_valor: float,
        cnae_info: Optional[Dict[str, Any]]
    ) -> str:
        """Gera sugestão para empresa específica."""
        if imp_total > 0 and exp_total > 0:
            return "Empresa já opera em ambos os sentidos - manter diversificação"
        elif imp_total > 0:
            sugestao = f"Empresa importadora - considere exportar produtos relacionados ao CNAE {cnae_info.get('cnae') if cnae_info else 'N/A'}"
            if cnae_info and cnae_info.get("classificacao"):
                sugestao += f" ({cnae_info['classificacao']})"
            return sugestao
        elif exp_total > 0:
            sugestao = f"Empresa exportadora - considere importar insumos relacionados ao CNAE {cnae_info.get('cnae') if cnae_info else 'N/A'}"
            if cnae_info and cnae_info.get("classificacao"):
                sugestao += f" ({cnae_info['classificacao']})"
            return sugestao
        else:
            return "Empresa sem operações registradas - potencial para iniciar comércio exterior"



