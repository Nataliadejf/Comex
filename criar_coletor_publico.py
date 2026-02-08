"""
Script para criar todos os arquivos do coletor de dados públicos.
Execute: python criar_coletor_publico.py
"""
from pathlib import Path
import os

# Caminhos
projeto_dir = Path(__file__).parent
backend_dir = projeto_dir / "backend"
data_collector_dir = backend_dir / "data_collector"
api_dir = backend_dir / "api"

# Criar diretórios se não existirem
data_collector_dir.mkdir(parents=True, exist_ok=True)
api_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ARQUIVO 1: backend/data_collector/public_company_collector.py
# ============================================================================
arquivo1 = data_collector_dir / "public_company_collector.py"
conteudo1 = '''"""
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
from bs4 import BeautifulSoup
import json

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.models import OperacaoComex


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
        cnpj_limpo = re.sub(r'[^\\d]', '', str(cnpj))
        return len(cnpj_limpo) == 14
    
    def limpar_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return re.sub(r'[^\\d]', '', str(cnpj))
    
    def extrair_ncm(self, texto: str) -> Optional[str]:
        """Extrai código NCM de um texto."""
        padroes = [
            r'NCM[:\\s]*(\\d{4}\\.?\\d{2}\\.?\\d{2})',
            r'(\\d{4}\\.\\d{2}\\.\\d{2})',
            r'(\\d{8})',
            r'Código[:\\s]*(\\d{4}\\.?\\d{2}\\.?\\d{2})',
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
            r'CNPJ[:\\s]*(\\d{2}\\.?\\d{3}\\.?\\d{3}\\/?\\d{4}-?\\d{2})',
            r'(\\d{2}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2})',
            r'(\\d{14})',
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
            r'Razão Social[:\\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\\s&.,-]+(?:LTDA|S\\.A\\.|EIRELI|ME|EPP))',
            r'Empresa[:\\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\\s&.,-]+(?:LTDA|S\\.A\\.|EIRELI|ME|EPP))',
            r'Importador[:\\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\\s&.,-]+(?:LTDA|S\\.A\\.|EIRELI|ME|EPP))',
            r'Exportador[:\\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][A-ZÁÉÍÓÚÇÃÊÔÀ\\s&.,-]+(?:LTDA|S\\.A\\.|EIRELI|ME|EPP))',
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
            r'(\\d{2})/(\\d{2})/(\\d{4})',
            r'(\\d{4})-(\\d{2})-(\\d{2})',
            r'(\\d{2})\\.(\\d{2})\\.(\\d{4})',
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
            r'Valor FOB[:\\s]*USD[:\\s]*([\\d.,]+)',
            r'FOB[:\\s]*([\\d.,]+)',
            r'USD[:\\s]*([\\d.,]+)',
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
        match = re.search(r'Quantidade[:\\s]*([\\d.,]+)', texto, re.IGNORECASE)
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
            r'Município[:\\s]*([A-ZÁÉÍÓÚÇÃÊÔÀ][a-záéíóúçãêôà\\s]+)[/\\-]?([A-Z]{2})',
            r'([A-ZÁÉÍÓÚÇÃÊÔÀ][a-záéíóúçãêôà\\s]+)[/\\-]\\s*([A-Z]{2})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                municipio = match.group(1).strip()
                estado = match.group(2).strip()
                return municipio, estado
        return None, None
    
    def coletar_dou(self, termos_busca: List[str] = None, limite: int = 100) -> List[Dict[str, Any]]:
        """Coleta dados do Diário Oficial da União (DOU)."""
        if termos_busca is None:
            termos_busca = [
                "licença de importação deferida",
                "licença de exportação deferida",
                "empresa habilitada radar",
                "exportação autorizada",
                "importação autorizada",
            ]
        
        dados = []
        logger.info(f"🔍 Iniciando coleta no DOU com {len(termos_busca)} termos de busca...")
        
        base_url = "https://www.in.gov.br/en/web/dou"
        
        for termo in termos_busca:
            try:
                logger.info(f"Buscando: {termo}")
                url = f"{base_url}/-/extrato-de-licenca-de-importacao"
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                textos = soup.find_all("div", class_="texto-dou")
                if not textos:
                    textos = soup.find_all("p")
                
                for texto_elem in textos[:limite]:
                    texto = texto_elem.get_text()
                    
                    if any(t.lower() in texto.lower() for t in ["importação", "exportação", "ncm"]):
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
                            logger.debug(f"✅ Coletado: {empresa_nome} - {ncm}")
                
                time.sleep(self.delay_between_requests)
                
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
    
    def coletar_todos(self, limite_por_fonte: int = 100) -> List[Dict[str, Any]]:
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
                
                if isinstance(data_operacao, str):
                    try:
                        data_operacao = datetime.fromisoformat(data_operacao).date()
                    except:
                        data_operacao = date.today()
                elif not isinstance(data_operacao, date):
                    data_operacao = date.today()
                
                operacao = OperacaoComex(
                    ncm=ncm,
                    descricao_produto=registro.get("descricao_ncm", ""),
                    tipo_operacao=tipo_operacao,
                    razao_social_importador=empresa_nome if tipo_operacao == "Importação" else None,
                    razao_social_exportador=empresa_nome if tipo_operacao == "Exportação" else None,
                    cnpj_importador=registro.get("cnpj") if tipo_operacao == "Importação" else None,
                    cnpj_exportador=registro.get("cnpj") if tipo_operacao == "Exportação" else None,
                    uf=registro.get("estado", ""),
                    pais_origem_destino=registro.get("pais_origem_destino", ""),
                    valor_fob=registro.get("valor_fob", 0.0),
                    quantidade_estatistica=registro.get("quantidade"),
                    data_operacao=data_operacao,
                    mes_referencia=data_operacao.strftime("%Y-%m"),
                    arquivo_origem=registro.get("fonte", "public_collector"),
                    via_transporte="Outras",
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
'''

# ============================================================================
# ARQUIVO 2: backend/api/coletar_dados_publicos.py
# ============================================================================
arquivo2 = api_dir / "coletar_dados_publicos.py"
conteudo2 = '''"""
Endpoint para coletar dados públicos de empresas importadoras/exportadoras.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from database import get_db

try:
    from data_collector.public_company_collector import PublicCompanyCollector
    COLLECTOR_AVAILABLE = True
except ImportError:
    COLLECTOR_AVAILABLE = False
    logger.warning("PublicCompanyCollector não disponível")

router = APIRouter(prefix="/api", tags=["coleta-publica"])


class ColetaRequest(BaseModel):
    """Modelo de requisição para coleta."""
    limite_por_fonte: int = 100
    termos_busca: Optional[List[str]] = None
    salvar_csv: bool = False
    salvar_json: bool = False
    integrar_banco: bool = True


@router.post("/coletar-dados-publicos")
async def coletar_dados_publicos(
    request: ColetaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Coleta dados públicos de empresas importadoras/exportadoras."""
    if not COLLECTOR_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PublicCompanyCollector não está disponível."
        )
    
    try:
        collector = PublicCompanyCollector()
        
        def executar_coleta():
            try:
                logger.info("🔄 Iniciando coleta de dados públicos...")
                dados = collector.coletar_todos(limite_por_fonte=request.limite_por_fonte)
                
                if request.salvar_csv:
                    collector.salvar_csv()
                
                if request.salvar_json:
                    collector.salvar_json()
                
                if request.integrar_banco:
                    stats = collector.integrar_banco_dados(db)
                    logger.info(f"✅ Coleta concluída: {stats['registros_inseridos']} registros inseridos")
                
                logger.success("✅ Coleta de dados públicos concluída")
            except Exception as e:
                logger.error(f"❌ Erro na coleta: {e}")
                raise
        
        background_tasks.add_task(executar_coleta)
        
        return {
            "message": "Coleta de dados públicos iniciada em background",
            "status": "started",
            "limite_por_fonte": request.limite_por_fonte,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar coleta: {str(e)}")


@router.get("/coletar-dados-publicos/status")
async def status_coleta_publica() -> Dict[str, Any]:
    """Verifica o status do coletor de dados públicos."""
    return {
        "collector_available": COLLECTOR_AVAILABLE,
        "status": "ok" if COLLECTOR_AVAILABLE else "unavailable"
    }
'''

# Escrever arquivos
print("📝 Criando arquivos do coletor de dados públicos...")

with open(arquivo1, 'w', encoding='utf-8') as f:
    f.write(conteudo1)
print(f"✅ Criado: {arquivo1}")

with open(arquivo2, 'w', encoding='utf-8') as f:
    f.write(conteudo2)
print(f"✅ Criado: {arquivo2}")

print("\n✅ Todos os arquivos foram criados com sucesso!")
print("\n📋 Próximos passos:")
print("1. Integrar o router no main.py (adicionar após linha 186)")
print("2. Testar o endpoint: POST /api/coletar-dados-publicos")