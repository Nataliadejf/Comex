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


def _carregar_credenciais_bigquery():
    """
    Carrega GOOGLE_APPLICATION_CREDENTIALS_JSON (variável ou .env).
    Suporta JSON multilinha no .env (dotenv pode truncar).
    Retorna dict das credenciais ou None.
    """
    import os
    creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    # Arquivo JSON no disco
    if creds_path and not creds_env:
        try:
            p = Path(creds_path).expanduser()
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    creds_env = f.read()
        except Exception:
            pass
    if not creds_env or not creds_env.strip().startswith("{"):
        creds_env = None
    # JSON truncado (ex.: só "{" da primeira linha do .env)?
    if creds_env and (not creds_env.strip().endswith("}") or len(creds_env.strip()) < 10):
        creds_env = None
    if creds_env:
        try:
            return json.loads(creds_env)
        except json.JSONDecodeError:
            creds_env = None
    # Ler do .env (JSON multilinha)
    for _env_path in [backend_dir / ".env", backend_dir.parent / ".env"]:
        if not _env_path.exists():
            continue
        try:
            with open(_env_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        key = "GOOGLE_APPLICATION_CREDENTIALS_JSON"
        if key not in content:
            continue
        start = content.find(key)
        start = content.find("=", start) + 1
        brace = content.find("{", start)
        if brace == -1:
            continue
        depth = 0
        end = brace
        for i, c in enumerate(content[brace:], start=brace):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            if depth == 0:
                end = i
                break
        json_str = content[brace : end + 1]
        if not json_str.strip():
            continue
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            continue
    return None


def _carregar_queries_bigquery() -> List[str]:
    """
    Carrega a lista de SQL das consultas BigQuery a executar (consultas salvas).
    Ordem: 1) arquivo bigquery_queries.json (ao lado deste módulo), 2) env BIGQUERY_QUERIES_JSON, 3) lista vazia (usa query embutida).
    Retorna lista de strings SQL; vazia = usar query embutida no código.
    """
    import os
    # 1) Arquivo bigquery_queries.json
    queries_file = Path(__file__).resolve().parent / "bigquery_queries.json"
    logger.info(f"   Arquivo de consultas: {queries_file} (existe: {queries_file.exists()})")
    if queries_file.exists():
        try:
            with open(queries_file, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
            if isinstance(data, list) and data:
                out = [q.strip() for q in data if q and str(q).strip()]
                logger.info(f"   Carregadas {len(out)} consulta(s) do JSON (formato array)")
                return out
            if isinstance(data, dict) and data.get("queries"):
                out = [q.strip() for q in data["queries"] if q and str(q).strip()]
                logger.info(f"   Carregadas {len(out)} consulta(s) do JSON (chave 'queries')")
                return out
            logger.warning("   Arquivo bigquery_queries.json: 'queries' vazio ou formato inválido.")
        except json.JSONDecodeError as e:
            logger.warning(f"   bigquery_queries.json: JSON inválido ({e}). Tentando formato com delimitador ---QUERY---")
            # Fallback: arquivo com consultas separadas por ---QUERY--- (permite SQL multilinha)
            try:
                parts = [p.strip() for p in raw.split("---QUERY---") if p.strip()]
                if parts:
                    logger.info(f"   Carregadas {len(parts)} consulta(s) do arquivo (formato ---QUERY---)")
                    return parts
            except Exception:
                pass
            logger.error(f"   Erro ao ler bigquery_queries.json (JSON inválido): {e}")
            logger.error("   Em JSON, strings não podem ter quebra de linha literal; use \\n ou use delimitador ---QUERY--- entre cada consulta.")
        except Exception as e:
            logger.error(f"   Erro ao carregar bigquery_queries.json: {e}")
    else:
        logger.warning("   Arquivo bigquery_queries.json não encontrado.")
    # 2) Variável de ambiente (JSON array de strings)
    env_queries = os.getenv("BIGQUERY_QUERIES_JSON")
    if env_queries and env_queries.strip().startswith("["):
        try:
            arr = json.loads(env_queries)
            if isinstance(arr, list) and arr:
                out = [str(q).strip() for q in arr if q]
                logger.info(f"   Carregadas {len(out)} consulta(s) de BIGQUERY_QUERIES_JSON")
                return out
        except Exception as e:
            logger.error(f"   Erro ao ler BIGQUERY_QUERIES_JSON: {e}")
    return []


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
    
    def coletar_dou(self, termos_busca: List[str] = None, limite: int = 500000) -> List[Dict[str, Any]]:
        """
        Coleta dados do Diário Oficial da União (DOU).
        Usa a API de busca do DOU para encontrar licenças de importação/exportação.
        """
        if not BS4_AVAILABLE:
            logger.warning("⚠️ BeautifulSoup4 não disponível - pulando coleta DOU")
            return []
        if limite is None or limite <= 0:
            limite = 500000
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
    
    def coletar_bigquery_empresas_ncm(self, limite: int = 500000) -> List[Dict[str, Any]]:
        """
        Coleta dados do BigQuery relacionando empresas com NCM e município.
        Usa as tabelas já disponíveis no BigQuery.
        """
        dados = []
        if limite is None or limite <= 0:
            limite = 500000
        logger.info(f"🔍 Iniciando coleta no BigQuery - Meta: {limite:,} registros")
        
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account

            # Obter credenciais (suporta .env multilinha e arquivo JSON)
            creds_dict = _carregar_credenciais_bigquery()
            if not creds_dict:
                logger.warning("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON não configurada ou inválida. Verifique o .env em backend/")
                return dados

            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            project_id = (creds_dict.get("project_id") or "").strip() or "liquid-receiver-483923-n6"
            # Usar project explicitamente para o job ser criado neste projeto (evita 403 por projeto incorreto)
            client = bigquery.Client(credentials=credentials, project=project_id)
            client_email = (creds_dict.get("client_email") or "").strip()
            logger.info("✅ Conectado ao BigQuery")
            logger.info(f"   Conta em uso: {client_email or '(não informada)'} | Projeto: {project_id}")
            
            # Usar apenas as CONSULTAS (SQL das consultas salvas). O dataset Projeto_Comex não tem as tabelas;
            # os dados estão nas consultas salvas no BigQuery (EmpresasImEx, NCMExportacao, NCMImportacao, etc.).
            queries_sql = _carregar_queries_bigquery()
            if not queries_sql:
                logger.warning(
                    "⚠️ Nenhuma consulta configurada. O script não usa tabelas do dataset; usa o SQL das CONSULTAS salvas no BigQuery."
                )
                logger.warning(
                    "   → Edite backend/data_collector/bigquery_queries.json e cole o SQL de cada consulta salva (EmpresasImEx, NCMExportacao, NCMImportacao)."
                )
                logger.warning(
                    "   → Ou defina BIGQUERY_QUERIES_JSON (array JSON de strings SQL). Alternativa: salve as consultas como views/tabelas no dataset."
                )
                return dados
            
            logger.info(f"📋 Executando {len(queries_sql)} consulta(s) (bigquery_queries.json / BIGQUERY_QUERIES_JSON)")
            all_rows = []
            for idx, sql in enumerate(queries_sql):
                if len(all_rows) >= limite:
                    break
                job_config = bigquery.QueryJobConfig()
                if "@limite" in sql:
                    job_config.query_parameters = [bigquery.ScalarQueryParameter("limite", "INT64", limite)]
                try:
                    query_job = client.query(sql.strip(), job_config=job_config)
                    rows = query_job.result()
                    for row in rows:
                        all_rows.append(row)
                        if len(all_rows) >= limite:
                            break
                except Exception as e_query:
                    logger.warning(f"⚠️ Erro ao executar consulta {idx + 1}/{len(queries_sql)}: {e_query}")
                    raise
            
            rows = all_rows
            logger.info("📊 Processando resultados do BigQuery (consultas)...")
            
            def _val(row, *keys, default=None):
                """Lê valor da linha BigQuery (Row ou dict) tentando várias chaves."""
                for k in keys:
                    try:
                        v = row.get(k, default) if hasattr(row, "get") else default
                        if v is default and hasattr(row, "__getitem__"):
                            v = row[k]
                        if v is not None and (v != "" if isinstance(v, str) else True):
                            return v
                    except (KeyError, TypeError, IndexError, AttributeError):
                        pass
                return default
            
            for row in rows:
                # Mapear colunas das consultas (estabelecimentos: razao_social, id_exportacao_importacao; NCM: id_ncm, valor_fob_dolar, etc.)
                empresa_nome = _val(row, "empresa_nome", "razao_social")
                cnpj = _val(row, "cnpj")
                ncm = _val(row, "ncm", "id_ncm")
                estado = _val(row, "estado", "sigla_uf", "sigla_uf_nome", "sigla_uf_ncm_nome")
                municipio = _val(row, "municipio", "id_municipio_nome")
                tipo_raw = _val(row, "tipo_operacao", "id_exportacao_importacao", "descricao_id_exportacao_importacao")
                tipo_operacao = None
                if tipo_raw is not None and tipo_raw != "":
                    s = str(tipo_raw).lower().strip()
                    if "export" in s or "exportador" in s:
                        tipo_operacao = "Exportação"
                    elif "import" in s or "importador" in s:
                        tipo_operacao = "Importação"
                    elif s in ("1", "2"):  # códigos comuns: 1=Importador, 2=Exportador
                        tipo_operacao = "Exportação" if s == "2" else "Importação"
                    else:
                        tipo_operacao = str(tipo_raw)
                if not tipo_operacao and empresa_nome:
                    tipo_operacao = "Importação"  # fallback para não descartar linha
                ano = _val(row, "ano")
                mes = _val(row, "mes")
                data_operacao = _val(row, "data_operacao")
                valor_fob = _val(row, "valor_fob", "valor_fob_dolar")
                quantidade = _val(row, "quantidade", "quantidade_estatistica")
                peso_kg = _val(row, "peso_kg", "peso_liquido_kg")
                
                if not empresa_nome:
                    continue
                # NCM: id_ncm pode ser string ou número; quando ausente (ex.: query estabelecimentos), usar placeholder para não descartar a linha
                ncm_str = (str(ncm).replace(".0", "").strip()[:8].zfill(8)) if ncm else "00000000"
                
                if not data_operacao and (ano or mes):
                    try:
                        y, m = int(ano or 0), int(mes or 1)
                        if y:
                            data_operacao = f"{y}-{m:02d}-01"
                    except (TypeError, ValueError):
                        pass
                
                registro = {
                    "empresa_nome": empresa_nome,
                    "cnpj": str(cnpj).zfill(14) if cnpj else None,
                    "tipo_operacao": tipo_operacao,
                    "ncm": ncm_str,
                    "valor_fob": float(valor_fob) if valor_fob is not None else None,
                    "quantidade": float(quantidade) if quantidade is not None else None,
                    "data_operacao": data_operacao.isoformat()[:10] if hasattr(data_operacao, "isoformat") else str(data_operacao)[:10] if data_operacao else None,
                    "municipio": municipio,
                    "estado": (str(estado or "").strip()[:2].upper())[:2] if estado else "",
                    "fonte": "BigQuery",
                    "peso_liquido_kg": float(peso_kg) if peso_kg is not None else None,
                }
                
                dados.append(registro)
                
                if len(dados) % 10000 == 0:
                    logger.info(f"📊 Progresso BigQuery: {len(dados):,}/{limite:,} registros coletados")
            
            logger.info(f"✅ Coletados {len(dados)} registros do BigQuery")
            
        except ImportError:
            logger.warning("⚠️ google-cloud-bigquery não instalado - pulando coleta BigQuery")
        except Exception as e:
            err_msg = str(e)
            # Sempre logar o erro completo para diagnóstico (billing, permissão, recurso, etc.)
            logger.error(f"   Detalhe do erro: {e}")
            if getattr(e, "errors", None):
                logger.error(f"   Erros (e.errors): {e.errors}")
            if getattr(e, "response", None):
                logger.error(f"   Response: {e.response}")
            if "403" in err_msg or "Access Denied" in err_msg:
                _creds = _carregar_credenciais_bigquery()
                _email = (_creds.get("client_email") or "").strip() if _creds else ""
                _proj = (_creds.get("project_id") or "").strip() if _creds else "liquid-receiver-483923-n6"
                if "permission to query table" in err_msg or "does not have permission to query" in err_msg:
                    logger.error("❌ BigQuery: conta sem permissão para LER os dados (tabela/dataset).")
                    logger.error("   Conceda a role 'BigQuery Data Viewer' no dataset Projeto_Comex:")
                    logger.error("   BigQuery → Explorador → Projeto_Comex → Compartilhar → Adicionar principal:")
                    logger.error(f"   → E-mail: {_email or '(verifique .env)'}")
                    logger.error("   → Função: BigQuery Data Viewer (Visualizador de dados do BigQuery)")
                else:
                    logger.error("❌ BigQuery: conta de serviço sem permissão para criar jobs.")
                    logger.error("   Conceda a role 'BigQuery Job User' (ou 'BigQuery User') a ESTE e-mail no Google Cloud:")
                if _email:
                    logger.error(f"   → E-mail da conta em uso: {_email}")
                else:
                    logger.error("   → E-mail da conta em uso: (verifique o client_email no .env)")
                logger.error(f"   → Projeto: {_proj}")
                logger.error("   https://console.cloud.google.com/iam-admin/iam?project=" + _proj)
                logger.error("   Veja CONFIGURAR_BIGQUERY.md seção 'Erro 403 - Permissão'.")
            else:
                logger.error(f"❌ Erro ao coletar BigQuery: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return dados
    
    def coletar_todos(self, limite_por_fonte: int = 500000) -> List[Dict[str, Any]]:
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
        skip_sem_ncm = skip_sem_tipo = skip_sem_empresa = 0
        for registro in self.dados_coletados:
            try:
                ncm = registro.get("ncm")
                tipo_operacao = registro.get("tipo_operacao")
                empresa_nome = registro.get("empresa_nome")
                data_operacao = registro.get("data_operacao")
                if not empresa_nome:
                    skip_sem_empresa += 1
                    continue
                if not tipo_operacao:
                    tipo_operacao = "Importação"  # fallback para registro com empresa
                    skip_sem_tipo += 1
                if not ncm:
                    skip_sem_ncm += 1
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
                
                # valor_fob e pais_origem_destino são NOT NULL no modelo; usar 0.0 e "" quando ausentes
                valor_fob = registro.get("valor_fob")
                valor_fob = 0.0 if valor_fob is None else float(valor_fob)
                operacao = OperacaoComex(
                    ncm=ncm,
                    descricao_produto=registro.get("descricao_ncm") or "",
                    tipo_operacao=tipo_enum,
                    razao_social_importador=empresa_nome if tipo_enum == TipoOperacao.IMPORTACAO else None,
                    razao_social_exportador=empresa_nome if tipo_enum == TipoOperacao.EXPORTACAO else None,
                    cnpj_importador=registro.get("cnpj") if tipo_enum == TipoOperacao.IMPORTACAO else None,
                    cnpj_exportador=registro.get("cnpj") if tipo_enum == TipoOperacao.EXPORTACAO else None,
                    uf=uf or "  ",
                    pais_origem_destino=(registro.get("pais_origem_destino") or "").strip() or "",
                    valor_fob=valor_fob,
                    quantidade_estatistica=registro.get("quantidade"),
                    peso_liquido_kg=registro.get("peso_liquido_kg"),
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
        
        if skip_sem_empresa or skip_sem_ncm or skip_sem_tipo:
            logger.info(f"   Pulados: sem empresa={skip_sem_empresa}, sem NCM={skip_sem_ncm}, tipo preenchido por fallback={skip_sem_tipo}")
        try:
            db.commit()
            logger.info(f"✅ Integração concluída: {stats['registros_inseridos']} inseridos")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao commitar: {e}")
            stats["erros"] += stats["registros_inseridos"]
            stats["registros_inseridos"] = 0
        
        return stats
