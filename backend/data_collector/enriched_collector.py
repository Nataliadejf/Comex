"""
Coletor enriquecido que integra dados CSV do MDIC com CNAE para sugestões inteligentes.
"""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database import OperacaoComex
from .mdic_csv_collector import MDICCSVCollector
from .transformer import DataTransformer
from .cnae_analyzer import CNAEAnalyzer
from .empresas_mdic_scraper import EmpresasMDICScraper


class EnrichedDataCollector:
    """
    Coletor que integra dados CSV do MDIC com CNAE e empresas para sugestões inteligentes.
    """
    
    def __init__(self):
        self.csv_collector = MDICCSVCollector()
        self.transformer = DataTransformer()
        self.cnae_analyzer = None
        self.empresas_scraper = EmpresasMDICScraper()
        
        # Tentar carregar CNAE
        try:
            arquivo_cnae = Path("C:/Users/User/Desktop/Cursor/NOVO CNAE.xlsx")
            if arquivo_cnae.exists():
                self.cnae_analyzer = CNAEAnalyzer(arquivo_cnae)
                self.cnae_analyzer.carregar_cnae_excel()
                logger.info("✅ CNAE carregado para enriquecimento")
        except Exception as e:
            logger.warning(f"CNAE não disponível: {e}")
    
    async def collect_and_enrich(
        self,
        db: Session,
        meses: int = 24
    ) -> Dict[str, Any]:
        """
        Coleta dados CSV do MDIC e enriquece com informações de empresas e CNAE.
        
        Args:
            db: Sessão do banco de dados
            meses: Número de meses para coletar
        
        Returns:
            Estatísticas da coleta
        """
        logger.info("Iniciando coleta enriquecida de dados do MDIC...")
        
        stats = {
            "total_registros": 0,
            "registros_novos": 0,
            "registros_atualizados": 0,
            "meses_processados": [],
            "erros": [],
            "tabelas_correlacao": {},
            "empresas_enriquecidas": 0
        }
        
        try:
            # 1. Baixar tabelas de correlação
            logger.info("Baixando tabelas de correlação...")
            tabelas = await self.csv_collector.download_correlation_tables()
            stats["tabelas_correlacao"] = {k: str(v) for k, v in tabelas.items()}
            
            # 2. Baixar dados mensais
            logger.info(f"Baixando dados dos últimos {meses} meses...")
            arquivos = await self.csv_collector.download_recent_months(meses)
            
            # 3. Processar cada arquivo
            for filepath in arquivos:
                try:
                    # Extrair informações do nome do arquivo
                    nome_parts = filepath.stem.split('_')
                    if len(nome_parts) >= 3:
                        tipo_op = nome_parts[0]  # IMP ou EXP
                        ano = int(nome_parts[1])
                        mes = int(nome_parts[2])
                        
                        tipo_operacao = "Importação" if tipo_op == "IMP" else "Exportação"
                        mes_str = f"{ano}-{mes:02d}"
                        
                        # Processar CSV
                        try:
                            registros_raw = self.csv_collector.parse_csv_file(filepath)
                            
                            if registros_raw:
                                # Transformar para formato do banco
                                registros_transformados = self.transformer.transform_csv_data(
                                    registros_raw,
                                    mes_str,
                                    tipo_operacao
                                )
                                
                                if registros_transformados:
                                    # Salvar no banco
                                    salvos = self._save_to_database(db, registros_transformados, mes_str, tipo_operacao)
                                    stats["total_registros"] += len(registros_transformados)
                                    stats["registros_novos"] += salvos["novos"]
                                    stats["registros_atualizados"] += salvos["atualizados"]
                                    
                                    if mes_str not in stats["meses_processados"]:
                                        stats["meses_processados"].append(mes_str)
                                    
                                    logger.info(
                                        f"✅ {tipo_operacao} {mes_str}: "
                                        f"{len(registros_transformados)} registros "
                                        f"({salvos['novos']} novos, {salvos['atualizados']} atualizados)"
                                    )
                                else:
                                    logger.warning(f"⚠️ Nenhum registro transformado de {filepath.name}")
                            else:
                                logger.warning(f"⚠️ Arquivo vazio ou inválido: {filepath.name}")
                        except Exception as e:
                            logger.error(f"Erro ao processar {filepath.name}: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            stats["erros"].append(f"Erro ao processar {filepath.name}: {str(e)}")
                
                except Exception as e:
                    error_msg = f"Erro ao processar {filepath.name}: {e}"
                    logger.error(error_msg)
                    stats["erros"].append(error_msg)
            
            # 4. Enriquecer com empresas do MDIC
            logger.info("Enriquecendo com empresas do MDIC...")
            empresas_enriquecidas = await self._enrich_with_companies(db)
            stats["empresas_enriquecidas"] = empresas_enriquecidas
            
            logger.success(
                f"✅ Coleta concluída: {stats['total_registros']} registros, "
                f"{stats['registros_novos']} novos, "
                f"{stats['empresas_enriquecidas']} empresas enriquecidas"
            )
            
        except Exception as e:
            logger.error(f"Erro na coleta enriquecida: {e}")
            import traceback
            logger.error(traceback.format_exc())
            stats["erros"].append(str(e))
        
        return stats
    
    def _save_to_database(
        self,
        db: Session,
        registros: List[Dict[str, Any]],
        mes: str,
        tipo_operacao: str
    ) -> Dict[str, int]:
        """
        Salva registros no banco de dados, evitando duplicatas.
        
        Returns:
            Dicionário com contagem de novos e atualizados
        """
        novos = 0
        atualizados = 0
        
        for registro in registros:
            try:
                        # Verificar se já existe (usar chave única: NCM + Data + Tipo + País + UF)
                        existing = db.query(OperacaoComex).filter(
                            and_(
                                OperacaoComex.ncm == registro.get("ncm"),
                                OperacaoComex.data_operacao == registro.get("data_operacao"),
                                OperacaoComex.tipo_operacao == registro.get("tipo_operacao"),
                                OperacaoComex.pais_origem_destino == registro.get("pais_origem_destino"),
                                OperacaoComex.uf == registro.get("uf")
                            )
                        ).first()
                
                if existing:
                    # Atualizar registro existente
                    for key, value in registro.items():
                        if value is not None:
                            setattr(existing, key, value)
                    atualizados += 1
                else:
                    # Criar novo registro
                    nova_operacao = OperacaoComex(**registro)
                    db.add(nova_operacao)
                    novos += 1
                
            except Exception as e:
                logger.error(f"Erro ao salvar registro: {e}")
                continue
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Erro ao commitar: {e}")
            db.rollback()
        
        return {"novos": novos, "atualizados": atualizados}
    
    async def _enrich_with_companies(self, db: Session) -> int:
        """
        Enriquece operações com informações de empresas do MDIC.
        
        Returns:
            Número de operações enriquecidas
        """
        try:
            # Carregar empresas do MDIC
            empresas_mdic = await self.empresas_scraper.coletar_empresas()
            
            # Criar índice por CNPJ e Razão Social
            empresas_index = {}
            for emp in empresas_mdic:
                cnpj = emp.get("cnpj", "").replace(".", "").replace("/", "").replace("-", "")
                razao_social = emp.get("razao_social", "").upper().strip()
                
                if cnpj:
                    empresas_index[cnpj] = emp
                if razao_social:
                    empresas_index[razao_social] = emp
            
            # Buscar operações sem empresa identificada
            operacoes_sem_empresa = db.query(OperacaoComex).filter(
                or_(
                    OperacaoComex.razao_social_importador.is_(None),
                    OperacaoComex.razao_social_exportador.is_(None)
                )
            ).limit(10000).all()
            
            enriquecidas = 0
            
            for op in operacoes_sem_empresa:
                atualizada = False
                
                # Tentar identificar importador
                if not op.razao_social_importador and op.cnpj_importador:
                    cnpj_limpo = str(op.cnpj_importador).replace(".", "").replace("/", "").replace("-", "")
                    if cnpj_limpo in empresas_index:
                        emp = empresas_index[cnpj_limpo]
                        op.razao_social_importador = emp.get("razao_social")
                        atualizada = True
                
                # Tentar identificar exportador
                if not op.razao_social_exportador and op.cnpj_exportador:
                    cnpj_limpo = str(op.cnpj_exportador).replace(".", "").replace("/", "").replace("-", "")
                    if cnpj_limpo in empresas_index:
                        emp = empresas_index[cnpj_limpo]
                        op.razao_social_exportador = emp.get("razao_social")
                        atualizada = True
                
                if atualizada:
                    enriquecidas += 1
            
            if enriquecidas > 0:
                db.commit()
                logger.info(f"✅ {enriquecidas} operações enriquecidas com empresas do MDIC")
            
            return enriquecidas
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer com empresas: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    async def get_suggested_companies(
        self,
        db: Session,
        ncm: Optional[str] = None,
        tipo: Optional[str] = None,  # "importacao" ou "exportacao"
        uf: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Gera sugestões de empresas prováveis baseadas em NCM, CNAE e histórico.
        
        Args:
            db: Sessão do banco
            ncm: Código NCM (opcional)
            tipo: Tipo de operação (opcional)
            uf: UF (opcional)
            limit: Limite de resultados
        
        Returns:
            Lista de empresas sugeridas
        """
        sugestoes = []
        
        try:
            # 1. Buscar empresas do MDIC que operam com esse NCM
            empresas_mdic = await self.empresas_scraper.coletar_empresas()
            
            # 2. Buscar operações no banco para identificar padrões
            query = db.query(OperacaoComex)
            
            if ncm:
                query = query.filter(OperacaoComex.ncm == ncm)
            if tipo == "importacao":
                query = query.filter(OperacaoComex.tipo_operacao == "Importação")
            elif tipo == "exportacao":
                query = query.filter(OperacaoComex.tipo_operacao == "Exportação")
            if uf:
                query = query.filter(OperacaoComex.uf == uf)
            
            # Agrupar por empresa
            if tipo == "importacao":
                empresas_operacoes = query.with_entities(
                    OperacaoComex.razao_social_importador,
                    func.count(OperacaoComex.id).label('total'),
                    func.sum(OperacaoComex.valor_fob).label('valor_total')
                ).filter(
                    OperacaoComex.razao_social_importador.isnot(None)
                ).group_by(
                    OperacaoComex.razao_social_importador
                ).order_by(
                    func.sum(OperacaoComex.valor_fob).desc()
                ).limit(limit).all()
            else:
                empresas_operacoes = query.with_entities(
                    OperacaoComex.razao_social_exportador,
                    func.count(OperacaoComex.id).label('total'),
                    func.sum(OperacaoComex.valor_fob).label('valor_total')
                ).filter(
                    OperacaoComex.razao_social_exportador.isnot(None)
                ).group_by(
                    OperacaoComex.razao_social_exportador
                ).order_by(
                    func.sum(OperacaoComex.valor_fob).desc()
                ).limit(limit).all()
            
            # 3. Enriquecer com informações do MDIC e CNAE
            for empresa_nome, total, valor_total in empresas_operacoes:
                if not empresa_nome:
                    continue
                
                sugestao = {
                    "nome": empresa_nome,
                    "total_operacoes": int(total),
                    "valor_total": float(valor_total or 0),
                    "fonte": "operacoes_reais",
                    "confianca": "alta"
                }
                
                # Buscar empresa no MDIC
                for emp in empresas_mdic:
                    if emp.get("razao_social", "").upper() == empresa_nome.upper():
                        sugestao.update({
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf"),
                            "municipio": emp.get("municipio"),
                            "faixa_valor": emp.get("faixa_valor")
                        })
                        break
                
                # Buscar CNAE se disponível
                if self.cnae_analyzer and sugestao.get("cnpj"):
                    cnae_info = self.cnae_analyzer.buscar_por_cnpj(sugestao["cnpj"])
                    if cnae_info:
                        sugestao.update({
                            "cnae": cnae_info.get("cnae"),
                            "classificacao_cnae": cnae_info.get("classificacao")
                        })
                
                sugestoes.append(sugestao)
            
            # 4. Se não encontrou muitas, complementar com empresas do MDIC
            if len(sugestoes) < limit:
                for emp in empresas_mdic[:limit - len(sugestoes)]:
                    nome = emp.get("razao_social") or emp.get("nome_fantasia", "")
                    if nome and nome not in [s["nome"] for s in sugestoes]:
                        sugestao = {
                            "nome": nome,
                            "total_operacoes": 0,
                            "valor_total": 0.0,
                            "fonte": "mdic",
                            "confianca": "media",
                            "cnpj": emp.get("cnpj"),
                            "uf": emp.get("uf"),
                            "faixa_valor": emp.get("faixa_valor")
                        }
                        
                        # Buscar CNAE
                        if self.cnae_analyzer and sugestao.get("cnpj"):
                            cnae_info = self.cnae_analyzer.buscar_por_cnpj(sugestao["cnpj"])
                            if cnae_info:
                                sugestao.update({
                                    "cnae": cnae_info.get("cnae"),
                                    "classificacao_cnae": cnae_info.get("classificacao")
                                })
                        
                        sugestoes.append(sugestao)
            
            return sugestoes[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

