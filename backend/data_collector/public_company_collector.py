"""
Coletor de dados públicos de empresas importadoras/exportadoras.
Relaciona empresas com NCM e município.
"""
import sys
from pathlib import Path
import re
import requests
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
import time
from datetime import datetime, date
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("⚠️ BeautifulSoup4 (bs4) não disponível - funcionalidade DOU limitada")
import json

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.models import OperacaoComex, TipoOperacao, ViaTransporte


class PublicCompanyCollector:
    """Coletor de dados públicos de empresas importadoras/exportadoras."""
    
    def __init__(self):
        self.dados_coletados: List[Dict[str, Any]] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 30
        self.delay_between_requests = 1
    
    def validar_cnpj(self, cnpj: str) -> bool:
        """Valida formato de CNPJ."""
        cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
        return len(cnpj_limpo) == 14
    
    def limpar_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return re.sub(r'[^\d]', '', str(cnpj))
    
    def extrair_ncm(self, texto: str) -> Optional[str]:
        """Extrai código NCM de um texto."""
        padroes = [
            r'NCM[:\s]*(\d{4}\.?\d{2}\.?\d{2})',
            r'(\d{4}\.\d{2}\.\d{2})',
            r'(\d{8})',
            r'Código[:\s]*(\d{4}\.?\d{2}\.?\d{2})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                ncm = match.group(1).replace('.', '')
                if len(ncm) == 8:
                    return ncm
        return None
    
    def extrair_cnpj(self, texto: str) -> Optional[str]:
        """Extrai CNPJ de um texto."""
        padroes = [
            r'CNPJ[:\s]*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})',
            r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
            r'(\d{14})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                cnpj = self.limpar_cnpj(match.group(1))
                if self.validar_cnpj(cnpj):
                    return cnpj
        return None
    
    def extrair_nome_empresa(self, texto: str) -> Optional[str]:
        """Extrai nome da empresa de um texto."""
        padroes = [
            r'Razão Social[:\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\s&.,-]+(?:LTDA|S\.A\.|EIRELI|ME|EPP))',
            r'Empresa[:\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\s&.,-]+(?:LTDA|S\.A\.|EIRELI|ME|EPP))',
            r'Importador[:\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\s&.,-]+(?:LTDA|S\.A\.|EIRELI|ME|EPP))',
            r'Exportador[:\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\s&.,-]+(?:LTDA|S\.A\.|EIRELI|ME|EPP))',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Filtrar MEI, microempresa, EPP
                if not any(x in nome.upper() for x in ['MEI', 'MICROEMPRESA', 'EPP']):
                    return nome
        return None
    
    def extrair_data(self, texto: str) -> Optional[date]:
        """Extrai data de um texto."""
        padroes = [
            r'(\d{2})/(\d{2})/(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{2})\.(\d{2})\.(\d{4})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                try:
                    if '/' in match.group(0):
                        dia, mes, ano = match.groups()
                    elif '-' in match.group(0):
                        ano, mes, dia = match.groups()
                    else:
                        dia, mes, ano = match.groups()
                    return date(int(ano), int(mes), int(dia))
                except:
                    continue
        return None
    
    def extrair_valor_fob(self, texto: str) -> Optional[float]:
        """Extrai valor FOB de um texto."""
        padroes = [
            r'Valor FOB[:\s]*USD[:\s]*([\d.,]+)',
            r'FOB[:\s]*([\d.,]+)',
            r'USD[:\s]*([\d.,]+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                try:
                    valor_str = match.group(1).replace('.', '').replace(',', '.')
                    return float(valor_str)
                except:
                    continue
        return None
    
    def extrair_quantidade(self, texto: str) -> Optional[float]:
        """Extrai quantidade de um texto."""
        match = re.search(r'Quantidade[:\s]*([\d.,]+)', texto, re.IGNORECASE)
        if match:
            try:
                qtd_str = match.group(1).replace('.', '').replace(',', '.')
                return float(qtd_str)
            except:
                pass
        return None
    
    def extrair_municipio_estado(self, texto: str) -> Tuple[Optional[str], Optional[str]]:
        """Extrai município e estado de um texto."""
        padroes = [
            r'Município[:\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][a-záéíóúçãêôà\s]+)[/\-]?([A-Z]{2})',
            r'([A-ZÁÉÍÓÚÇÃÊÔÀ][a-záéíóúçãêôà\s]+)[/\-]\s*([A-Z]{2})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                municipio = match.group(1).strip()
                estado = match.group(2).strip()
                return municipio, estado
        return None, None
    
    def coletar_dou(self, termos_busca: List[str] = None, limite: int = 50000) -> List[Dict[str, Any]]:
        """
        Coleta dados do Diário Oficial da União (DOU).
        Usa a API de busca do DOU para encontrar licenças de importação/exportação.
        """
        if not BS4_AVAILABLE:
            logger.warning("⚠️ BeautifulSoup4 não disponível - pulando coleta DOU")
            return []
        
        if termos_busca is None:
            termos_busca = [
                "licença de importação",
                "licença de exportação",
                "importação deferida",
                "exportação deferida",
                "empresa habilitada radar",
                "exportação autorizada",
                "importação autorizada",
                "comércio exterior",
                "NCM",
            ]
        
        dados = []
        logger.info(f"🔍 Iniciando coleta no DOU - Meta: {limite} registros")
        
        # API do DOU - buscar por termos e datas
        base_url = "https://www.in.gov.br/consulta/-/buscar/dou"
        
        # Buscar nos últimos 2 anos
        from datetime import timedelta
        data_fim = datetime.now().date()
        data_inicio = data_fim - timedelta(days=730)  # 2 anos
        
        total_coletado = 0
        
        for termo in termos_busca:
            if total_coletado >= limite:
                break
                
            try:
                logger.info(f"🔍 Buscando DOU: '{termo}' ({total_coletado}/{limite})")
                
                # Parâmetros da busca DOU
                params = {
                    "q": termo,
                    "s": "do1",  # Seção 1 do DOU
                    "sd": data_inicio.strftime("%d-%m-%Y"),
                    "ed": data_fim.strftime("%d-%m-%Y"),
                    "p": 1,  # Página
                }
                
                pagina = 1
                max_paginas = 100  # Limitar páginas para não sobrecarregar
                
                while pagina <= max_paginas and total_coletado < limite:
                    params["p"] = pagina
                    
                    try:
                        response = self.session.get(base_url, params=params, timeout=self.timeout)
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar resultados na página
                        resultados = soup.find_all("div", class_="resultado")
                        if not resultados:
                            resultados = soup.find_all("article")
                        if not resultados:
                            resultados = soup.find_all("div", class_="texto-dou")
                        
                        if not resultados:
                            logger.debug(f"   Nenhum resultado encontrado na página {pagina}")
                            break
                        
                        logger.info(f"   📄 Página {pagina}: {len(resultados)} resultados encontrados")
                        
                        for resultado in resultados:
                            if total_coletado >= limite:
                                break
                                
                            texto = resultado.get_text()
                            
                            # Verificar se contém termos relevantes
                            if any(t.lower() in texto.lower() for t in ["importação", "exportação", "ncm", "comércio exterior"]):
                                empresa_nome = self.extrair_nome_empresa(texto)
                                cnpj = self.extrair_cnpj(texto)
                                ncm = self.extrair_ncm(texto)
                                data_operacao = self.extrair_data(texto)
                                valor_fob = self.extrair_valor_fob(texto)
                                quantidade = self.extrair_quantidade(texto)
                                municipio, estado = self.extrair_municipio_estado(texto)
                                
                                tipo_operacao = None
                                if "importação" in texto.lower() or "importacao" in texto.lower():
                                    tipo_operacao = "Importação"
                                elif "exportação" in texto.lower() or "exportacao" in texto.lower():
                                    tipo_operacao = "Exportação"
                                
                                if empresa_nome and (ncm or tipo_operacao):
                                    registro = {
                                        "empresa_nome": empresa_nome,
                                        "cnpj": cnpj,
                                        "tipo_operacao": tipo_operacao,
                                        "ncm": ncm,
                                        "valor_fob": valor_fob,
                                        "quantidade": quantidade,
                                        "data_operacao": data_operacao.isoformat() if data_operacao else None,
                                        "municipio": municipio,
                                        "estado": estado,
                                        "fonte": "DOU",
                                        "texto_origem": texto[:500],
                                    }
                                    dados.append(registro)
                                    total_coletado += 1
                                    
                                    if total_coletado % 1000 == 0:
                                        logger.info(f"📊 Progresso DOU: {total_coletado}/{limite} registros coletados")
                        
                        pagina += 1
                        time.sleep(self.delay_between_requests)
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar página {pagina} do termo '{termo}': {e}")
                        break
                
            except Exception as e:
                logger.error(f"❌ Erro ao coletar DOU para termo '{termo}': {e}")
                continue
        
        logger.info(f"✅ Coletados {len(dados)} registros do DOU")
        return dados
    
    def coletar_portal_transparencia(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Coleta dados do Portal da Transparência."""
        dados = []
        logger.info("🔍 Iniciando coleta no Portal da Transparência...")
        # Implementação futura
        return dados
    
    def coletar_dados_gov_br(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Coleta dados do dados.gov.br."""
        dados = []
        logger.info("🔍 Iniciando coleta no dados.gov.br...")
        # Implementação futura
        return dados
    
    def coletar_bigquery_empresas_ncm(self, limite: int = 50000) -> List[Dict[str, Any]]:
        """
        Coleta dados do BigQuery relacionando empresas com NCM e município.
        Usa as tabelas já disponíveis no BigQuery.
        """
        dados = []
        logger.info(f"🔍 Iniciando coleta no BigQuery - Meta: {limite} registros")
        
        try:
            from google.cloud import bigquery
            import os
            import json
            
            # Obter credenciais
            creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if not creds_env:
                logger.warning("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada")
                return dados
            
            # Carregar credenciais
            if creds_env.startswith('{'):
                creds_dict = json.loads(creds_env)
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                client = bigquery.Client(credentials=credentials)
            else:
                client = bigquery.Client()
            
            logger.info("✅ Conectado ao BigQuery")
            
            # Query para relacionar empresas com NCM usando tabela de estabelecimentos
            # e cruzando com dados de município/NCM se disponíveis
            import os
            bigquery_table = os.getenv("BIGQUERY_COMEX_TABLE", "basedosdados.br_me_exportadoras_importadoras.estabelecimentos")
            
            # Query para buscar empresas e cruzar com dados de NCM por município
            # Usar tabelas NCMImportacao e NCMExportacao que já relacionam NCM com empresas
            query = """
            WITH empresas_ncm AS (
                -- Importações
                SELECT DISTINCT
                    imp.razao_social_importador as empresa_nome,
                    imp.cnpj_importador as cnpj,
                    imp.ncm,
                    imp.uf as estado,
                    imp.municipio,
                    'Importação' as tipo_operacao,
                    imp.data_operacao,
                    imp.valor_fob
                FROM `liquid-receiver-483923-n6.Projeto_Comex.NCMImportacao` imp
                WHERE imp.razao_social_importador IS NOT NULL
                    AND imp.cnpj_importador IS NOT NULL
                    AND imp.ncm IS NOT NULL
                    AND imp.uf IS NOT NULL
                
                UNION ALL
                
                -- Exportações
                SELECT DISTINCT
                    exp.razao_social_exportador as empresa_nome,
                    exp.cnpj_exportador as cnpj,
                    exp.ncm,
                    exp.uf as estado,
                    exp.municipio,
                    'Exportação' as tipo_operacao,
                    exp.data_operacao,
                    exp.valor_fob
                FROM `liquid-receiver-483923-n6.Projeto_Comex.NCMExportacao` exp
                WHERE exp.razao_social_exportador IS NOT NULL
                    AND exp.cnpj_exportador IS NOT NULL
                    AND exp.ncm IS NOT NULL
                    AND exp.uf IS NOT NULL
            )
            SELECT * FROM empresas_ncm
            LIMIT @limite
            """
            
            # Executar query
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limite", "INT64", limite)
                ]
            )
            
            query_job = client.query(query, job_config=job_config)
            rows = query_job.result()
            
            logger.info(f"📊 Processando resultados do BigQuery...")
            
            for row in rows:
                empresa_nome = row.get("empresa_nome")
                cnpj = row.get("cnpj")
                ncm = row.get("ncm")
                estado = row.get("estado")
                municipio = row.get("municipio")
                tipo_operacao = row.get("tipo_operacao")
                data_operacao = row.get("data_operacao")
                valor_fob = row.get("valor_fob")
                
                if not empresa_nome or not ncm:
                    continue
                
                registro = {
                    "empresa_nome": empresa_nome,
                    "cnpj": str(cnpj).zfill(14) if cnpj else None,
                    "tipo_operacao": tipo_operacao,
                    "ncm": str(ncm)[:8] if ncm else None,  # Garantir 8 dígitos
                    "valor_fob": float(valor_fob) if valor_fob else None,
                    "quantidade": None,
                    "data_operacao": data_operacao.isoformat() if data_operacao else None,
                    "municipio": municipio,
                    "estado": estado,
                    "fonte": "BigQuery",
                }
                
                dados.append(registro)
                
                if len(dados) % 10000 == 0:
                    logger.info(f"📊 Progresso BigQuery: {len(dados)}/{limite} registros coletados")
            
            logger.info(f"✅ Coletados {len(dados)} registros do BigQuery")
            
        except ImportError:
            logger.warning("⚠️ google-cloud-bigquery não instalado - pulando coleta BigQuery")
        except Exception as e:
            logger.error(f"❌ Erro ao coletar BigQuery: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return dados
    
    def coletar_todos(self, limite_por_fonte: int = 50000) -> List[Dict[str, Any]]:
        """Coleta dados de todas as fontes disponíveis."""
        logger.info("="*60)
        logger.info("COLETA DE DADOS PÚBLICOS - INÍCIO")
        logger.info("="*60)
        
        todos_dados = []
        
        try:
            dados_dou = self.coletar_dou(limite=limite_por_fonte)
            todos_dados.extend(dados_dou)
        except Exception as e:
            logger.error(f"❌ Erro ao coletar DOU: {e}")
        
        try:
            dados_transparencia = self.coletar_portal_transparencia(limite=limite_por_fonte)
            todos_dados.extend(dados_transparencia)
        except Exception as e:
            logger.error(f"❌ Erro ao coletar Portal da Transparência: {e}")
        
        try:
            dados_gov = self.coletar_dados_gov_br(limite=limite_por_fonte)
            todos_dados.extend(dados_gov)
        except Exception as e:
            logger.error(f"❌ Erro ao coletar dados.gov.br: {e}")
        
        # 4. BigQuery (fonte principal para grandes volumes)
        try:
            dados_bigquery = self.coletar_bigquery_empresas_ncm(limite=limite_por_fonte)
            todos_dados.extend(dados_bigquery)
            logger.info(f"✅ BigQuery: {len(dados_bigquery)} registros coletados")
        except Exception as e:
            logger.error(f"❌ Erro ao coletar BigQuery: {e}")
        
        # Remover duplicatas
        dados_unicos = {}
        for registro in todos_dados:
            chave = (
                registro.get("empresa_nome"),
                registro.get("ncm"),
                registro.get("data_operacao")
            )
            if chave not in dados_unicos:
                dados_unicos[chave] = registro
        
        dados_finais = list(dados_unicos.values())
        
        logger.info("="*60)
        logger.info(f"✅ COLETA CONCLUÍDA: {len(dados_finais)} registros únicos")
        logger.info("="*60)
        
        self.dados_coletados = dados_finais
        return dados_finais
    
    def salvar_csv(self, caminho: str = None) -> str:
        """Salva dados coletados em CSV."""
        if not self.dados_coletados:
            logger.warning("⚠️ Nenhum dado coletado para salvar")
            return None
        
        if caminho is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"empresas_publicas_{timestamp}.csv"
        
        df = pd.DataFrame(self.dados_coletados)
        df.to_csv(caminho, index=False, encoding='utf-8-sig')
        
        logger.info(f"✅ Dados salvos em: {caminho}")
        return caminho
    
    def salvar_json(self, caminho: str = None) -> str:
        """Salva dados coletados em JSON."""
        if not self.dados_coletados:
            logger.warning("⚠️ Nenhum dado coletado para salvar")
            return None
        
        if caminho is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"empresas_publicas_{timestamp}.json"
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(self.dados_coletados, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Dados salvos em: {caminho}")
        return caminho
    
    def integrar_banco_dados(self, db) -> Dict[str, int]:
        """Integra dados coletados com o banco de dados PostgreSQL."""
        stats = {
            "total_registros": len(self.dados_coletados),
            "registros_inseridos": 0,
            "registros_atualizados": 0,
            "erros": 0,
        }
        
        logger.info(f"🔄 Integrando {stats['total_registros']} registros no banco de dados...")
        
        for registro in self.dados_coletados:
            try:
                ncm = registro.get("ncm")
                tipo_operacao = registro.get("tipo_operacao")
                empresa_nome = registro.get("empresa_nome")
                data_operacao = registro.get("data_operacao")
                
                if not ncm or not tipo_operacao or not empresa_nome:
                    continue
                
                # Normalizar tipo para enum
                tipo_enum = TipoOperacao.IMPORTACAO if str(tipo_operacao).lower().startswith("import") else TipoOperacao.EXPORTACAO
                
                # Normalizar UF para 2 caracteres (sigla)
                uf_raw = (registro.get("estado") or "").strip().upper()
                uf = uf_raw[:2] if len(uf_raw) >= 2 else uf_raw
                if len(uf) != 2 and uf_raw:
                    # Mapeamento nome completo -> sigla (principais)
                    siglas = {"SAO PAULO": "SP", "RIO DE JANEIRO": "RJ", "MINAS GERAIS": "MG", "BAHIA": "BA", "PARANA": "PR", "RIO GRANDE DO SUL": "RS", "PERNAMBUCO": "PE", "CEARA": "CE", "SANTA CATARINA": "SC", "GOIAS": "GO", "DISTRITO FEDERAL": "DF"}
                    uf = siglas.get(uf_raw.replace("Ã", "A").replace("Á", "A")[:20], uf_raw[:2] or "  ")
                
                if isinstance(data_operacao, str):
                    try:
                        data_operacao = datetime.fromisoformat(data_operacao.replace("Z", "")).date()
                    except Exception:
                        data_operacao = date.today()
                elif not isinstance(data_operacao, date):
                    data_operacao = date.today()
                
                operacao = OperacaoComex(
                    ncm=ncm,
                    descricao_produto=registro.get("descricao_ncm", ""),
                    tipo_operacao=tipo_enum,
                    razao_social_importador=empresa_nome if tipo_enum == TipoOperacao.IMPORTACAO else None,
                    razao_social_exportador=empresa_nome if tipo_enum == TipoOperacao.EXPORTACAO else None,
                    cnpj_importador=registro.get("cnpj") if tipo_enum == TipoOperacao.IMPORTACAO else None,
                    cnpj_exportador=registro.get("cnpj") if tipo_enum == TipoOperacao.EXPORTACAO else None,
                    uf=uf or "  ",
                    pais_origem_destino=registro.get("pais_origem_destino", ""),
                    valor_fob=registro.get("valor_fob", 0.0),
                    quantidade_estatistica=registro.get("quantidade"),
                    data_operacao=data_operacao,
                    mes_referencia=data_operacao.strftime("%Y-%m"),
                    arquivo_origem=registro.get("fonte", "public_collector"),
                    via_transporte=ViaTransporte.OUTRAS,
                )
                
                db.add(operacao)
                stats["registros_inseridos"] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao integrar registro: {e}")
                stats["erros"] += 1
                continue
        
        try:
            db.commit()
            logger.info(f"✅ Integração concluída: {stats['registros_inseridos']} inseridos")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao commitar: {e}")
            stats["erros"] += stats["registros_inseridos"]
            stats["registros_inseridos"] = 0
        
        return stats
