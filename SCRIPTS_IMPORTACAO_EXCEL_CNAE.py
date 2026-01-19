"""
Scripts de Importação de Arquivos Excel e CNAE
===============================================

Este arquivo contém os endpoints completos para importação de:
1. Arquivos Excel com dados de importação/exportação (Comex)
2. Arquivos CNAE Excel

Endpoints:
- POST /upload-e-importar-excel
- POST /upload-e-importar-cnae

Características:
- Processamento em background para evitar timeout
- Bulk inserts otimizados
- Processamento em batches
- Logs detalhados de progresso
"""

import threading
import tempfile
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database.models import OperacaoComex, TipoOperacao, CNAEHierarquia
from database.database import SessionLocal
from loguru import logger


# ============================================================================
# ENDPOINT 1: Upload e Importar Excel (Importação/Exportação)
# ============================================================================

@app.post("/upload-e-importar-excel", tags=["importacao"])
async def upload_e_importar_excel(
    arquivo: UploadFile = File(..., description="Arquivo Excel (.xlsx ou .xls) para importar"),
    db: Session = Depends(get_db)
):
    """
    Faz upload de um arquivo Excel e importa automaticamente para o banco de dados.
    
    Aceita arquivos .xlsx e .xls via upload direto.
    OTIMIZADO: Usa bulk inserts e processamento em background para evitar timeout.
    
    IMPORTANTE: Retorna resposta imediata. O processamento continua em background.
    Verifique os logs do Render para acompanhar o progresso.
    
    Colunas esperadas no Excel:
    - Código NCM
    - Descrição NCM
    - UF do Produto
    - Países
    - Mês
    - Exportação - 2025 - Valor US$ FOB (ou Exportação - Valor US$ FOB)
    - Exportação - 2025 - Quilograma Líquido (ou Exportação - Quilograma Líquido)
    - Importação - 2025 - Valor US$ FOB (ou Importação - Valor US$ FOB)
    - Importação - 2025 - Quilograma Líquido (ou Importação - Quilograma Líquido)
    """
    import threading
    
    try:
        # Validar extensão do arquivo
        nome_arquivo = arquivo.filename.lower()
        if not (nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls')):
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ser Excel (.xlsx ou .xls)"
            )
        
        logger.info(f"📤 Recebendo upload do arquivo: {arquivo.filename}")
        
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx' if nome_arquivo.endswith('.xlsx') else '.xls') as tmp_file:
            conteudo = await arquivo.read()
            tmp_file.write(conteudo)
            caminho_temp = tmp_file.name
        
        logger.info(f"✅ Arquivo salvo temporariamente: {caminho_temp}")
        
        # Processar em background para evitar timeout do Render (30s)
        def processar_em_background():
            db_bg = SessionLocal()
            try:
                logger.info(f"🔄 Processamento em background iniciado para: {arquivo.filename}")
                
                # Ler Excel
                logger.info("📖 Lendo arquivo Excel...")
                df = pd.read_excel(caminho_temp)
                logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
                
                # Detectar ano do nome do arquivo
                ano = 2025  # Default
                ano_match = re.search(r'20\d{2}', arquivo.filename)
                if ano_match:
                    ano = int(ano_match.group())
                
                stats = {
                    "arquivo": arquivo.filename,
                    "total_registros": 0,
                    "importacoes": 0,
                    "exportacoes": 0,
                    "erros": []
                }
                
                # Preparar lista para bulk insert
                operacoes_para_inserir = []
                meses_map = {
                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
                    'abril': 4, 'maio': 5, 'junho': 6,
                    'julho': 7, 'agosto': 8, 'setembro': 9,
                    'outubro': 10, 'novembro': 11, 'dezembro': 12
                }
                
                # Processar em batches para melhor performance
                batch_size = 500
                total_rows = len(df)
                
                logger.info(f"🔄 Processando {total_rows} linhas em batches de {batch_size}...")
                
                for batch_start in range(0, total_rows, batch_size):
                    batch_end = min(batch_start + batch_size, total_rows)
                    batch_df = df.iloc[batch_start:batch_end]
                    
                    for idx, row in batch_df.iterrows():
                        try:
                            # Extrair dados básicos
                            ncm = str(row.get('Código NCM', '')).strip() if pd.notna(row.get('Código NCM')) else None
                            if not ncm or len(ncm) < 4:
                                continue
                            
                            ncm_normalizado = ncm[:8] if len(ncm) >= 8 else ncm.zfill(8)
                            descricao = str(row.get('Descrição NCM', '')).strip()[:500] if pd.notna(row.get('Descrição NCM')) else ''
                            uf = str(row.get('UF do Produto', '')).strip()[:2] if pd.notna(row.get('UF do Produto')) else None
                            pais = str(row.get('Países', '')).strip() if pd.notna(row.get('Países')) else None
                            
                            # Processar mês
                            mes_str = str(row.get('Mês', '')).strip() if pd.notna(row.get('Mês')) else ''
                            mes = None
                            if mes_str:
                                match = re.search(r'(\d{1,2})', mes_str)
                                if match:
                                    mes = int(match.group(1))
                                else:
                                    for nome, num in meses_map.items():
                                        if nome in mes_str.lower():
                                            mes = num
                                            break
                            
                            if not mes or mes < 1 or mes > 12:
                                mes = 1  # Default
                            
                            data_operacao = date(ano, mes, 1)
                            mes_referencia = f"{ano}-{mes:02d}"
                            
                            # Processar EXPORTAÇÃO
                            valor_exp = row.get('Exportação - 2025 - Valor US$ FOB', 0) or row.get('Exportação - Valor US$ FOB', 0) or row.get('Valor Exportação', 0)
                            peso_exp = row.get('Exportação - 2025 - Quilograma Líquido', 0) or row.get('Exportação - Quilograma Líquido', 0) or row.get('Peso Exportação', 0)
                            
                            if pd.notna(valor_exp) and float(valor_exp) > 0:
                                operacoes_para_inserir.append({
                                    'ncm': ncm_normalizado,
                                    'descricao_produto': descricao,
                                    'tipo_operacao': TipoOperacao.EXPORTACAO,
                                    'uf': uf,
                                    'pais_origem_destino': pais,
                                    'valor_fob': float(valor_exp),
                                    'peso_liquido_kg': float(peso_exp) if pd.notna(peso_exp) else 0,
                                    'data_operacao': data_operacao,
                                    'mes_referencia': mes_referencia,
                                    'arquivo_origem': arquivo.filename
                                })
                                stats["exportacoes"] += 1
                                stats["total_registros"] += 1
                            
                            # Processar IMPORTAÇÃO
                            valor_imp = row.get('Importação - 2025 - Valor US$ FOB', 0) or row.get('Importação - Valor US$ FOB', 0) or row.get('Valor Importação', 0)
                            peso_imp = row.get('Importação - 2025 - Quilograma Líquido', 0) or row.get('Importação - Quilograma Líquido', 0) or row.get('Peso Importação', 0)
                            
                            if pd.notna(valor_imp) and float(valor_imp) > 0:
                                operacoes_para_inserir.append({
                                    'ncm': ncm_normalizado,
                                    'descricao_produto': descricao,
                                    'tipo_operacao': TipoOperacao.IMPORTACAO,
                                    'uf': uf,
                                    'pais_origem_destino': pais,
                                    'valor_fob': float(valor_imp),
                                    'peso_liquido_kg': float(peso_imp) if pd.notna(peso_imp) else 0,
                                    'data_operacao': data_operacao,
                                    'mes_referencia': mes_referencia,
                                    'arquivo_origem': arquivo.filename
                                })
                                stats["importacoes"] += 1
                                stats["total_registros"] += 1
                        
                        except Exception as e:
                            logger.error(f"Erro ao processar linha {idx}: {e}")
                            stats["erros"].append(f"Linha {idx}: {str(e)}")
                            continue
                    
                    # Log de progresso
                    if batch_end % 1000 == 0 or batch_end == total_rows:
                        logger.info(f"  📊 Processadas {batch_end}/{total_rows} linhas... ({len(operacoes_para_inserir)} operações preparadas)")
                
                # Bulk insert otimizado - inserir em chunks
                logger.info(f"💾 Inserindo {len(operacoes_para_inserir)} operações no banco...")
                insert_chunk_size = 1000
                
                for i in range(0, len(operacoes_para_inserir), insert_chunk_size):
                    chunk = operacoes_para_inserir[i:i + insert_chunk_size]
                    
                    # Usar bulk_insert_mappings para melhor performance
                    db_bg.bulk_insert_mappings(OperacaoComex, chunk)
                    db_bg.commit()
                    
                    logger.info(f"  ✅ Inseridos {min(i + insert_chunk_size, len(operacoes_para_inserir))}/{len(operacoes_para_inserir)} registros...")
                
                logger.success(f"✅ Importação concluída: {stats['total_registros']} registros ({stats['importacoes']} importações, {stats['exportacoes']} exportações)")
                
            except Exception as e:
                logger.error(f"Erro no processamento em background: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                db_bg.close()
                # Remover arquivo temporário
                try:
                    os.unlink(caminho_temp)
                    logger.info(f"🗑️ Arquivo temporário removido: {caminho_temp}")
                except:
                    pass
        
        # Iniciar processamento em thread separada
        thread = threading.Thread(target=processar_em_background, daemon=True)
        thread.start()
        
        # Retornar resposta imediata
        return {
            "success": True,
            "message": "Upload recebido. Processamento iniciado em background.",
            "arquivo": arquivo.filename,
            "status": "processando",
            "instrucoes": "Verifique os logs do Render para acompanhar o progresso. O processamento pode levar vários minutos para arquivos grandes."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


# ============================================================================
# ENDPOINT 2: Upload e Importar CNAE
# ============================================================================

@app.post("/upload-e-importar-cnae", tags=["importacao"])
async def upload_e_importar_cnae(
    arquivo: UploadFile = File(..., description="Arquivo CNAE Excel (.xlsx ou .xls) para importar"),
    db: Session = Depends(get_db)
):
    """
    Faz upload de um arquivo CNAE Excel e importa automaticamente para o banco de dados.
    
    Aceita arquivos .xlsx e .xls via upload direto.
    OTIMIZADO: Usa bulk inserts para melhor performance.
    
    Colunas esperadas no Excel (aceita variações):
    - CNAE (ou Código CNAE, CNAE 2.0, Subclasse)
    - Descrição (ou Descrição Subclasse, Descrição CNAE)
    - Classe (opcional)
    - Grupo (opcional)
    - Divisão (opcional)
    - Seção (opcional)
    """
    try:
        # Validar extensão do arquivo
        nome_arquivo = arquivo.filename.lower()
        if not (nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls')):
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ser Excel (.xlsx ou .xls)"
            )
        
        logger.info(f"📤 Iniciando upload e importação do arquivo CNAE: {arquivo.filename}")
        
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx' if nome_arquivo.endswith('.xlsx') else '.xls') as tmp_file:
            conteudo = await arquivo.read()
            tmp_file.write(conteudo)
            caminho_temp = tmp_file.name
        
        try:
            # Ler Excel
            logger.info("📖 Lendo arquivo Excel...")
            df = pd.read_excel(caminho_temp)
            logger.info(f"✅ Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")
            logger.info(f"Colunas disponíveis: {list(df.columns)}")
            
            stats = {
                "arquivo": arquivo.filename,
                "total_registros": 0,
                "inseridos": 0,
                "atualizados": 0,
                "erros": []
            }
            
            # Preparar lista para bulk insert
            cnae_para_inserir = []
            cnae_existentes = set()
            
            # Buscar CNAEs existentes uma única vez
            logger.info("🔍 Verificando CNAEs existentes...")
            existentes_db = db.query(CNAEHierarquia.cnae).all()
            cnae_existentes = {row[0] for row in existentes_db}
            logger.info(f"  Encontrados {len(cnae_existentes)} CNAEs existentes")
            
            # Processar em batches
            batch_size = 500
            total_rows = len(df)
            
            logger.info(f"🔄 Processando {total_rows} linhas em batches de {batch_size}...")
            
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                batch_df = df.iloc[batch_start:batch_end]
                
                for idx, row in batch_df.iterrows():
                    try:
                        # Tentar diferentes nomes de colunas para CNAE
                        cnae = (
                            str(row.get('CNAE', '')) or
                            str(row.get('Código CNAE', '')) or
                            str(row.get('CNAE 2.0', '')) or
                            str(row.get('Subclasse', ''))
                        ).strip()
                        
                        if not cnae or cnae == 'nan' or len(cnae) < 4:
                            continue
                        
                        # Limpar CNAE (remover pontos, traços, etc)
                        cnae_limpo = cnae.replace('.', '').replace('-', '').strip()
                        
                        # Extrair informações adicionais
                        descricao = (
                            str(row.get('Descrição', '')) or
                            str(row.get('Descrição Subclasse', '')) or
                            str(row.get('Descrição CNAE', ''))
                        ).strip()[:500]
                        
                        classe = str(row.get('Classe', '')).strip()[:10] if pd.notna(row.get('Classe')) else None
                        grupo = str(row.get('Grupo', '')).strip()[:10] if pd.notna(row.get('Grupo')) else None
                        divisao = str(row.get('Divisão', '')).strip()[:10] if pd.notna(row.get('Divisão')) else None
                        secao = str(row.get('Seção', '')).strip()[:10] if pd.notna(row.get('Seção')) else None
                        
                        # Verificar se já existe (usando set em memória)
                        if cnae_limpo in cnae_existentes:
                            stats["atualizados"] += 1
                            # Para atualizações, precisamos fazer individualmente
                            existente = db.query(CNAEHierarquia).filter(
                                CNAEHierarquia.cnae == cnae_limpo
                            ).first()
                            if existente:
                                if descricao:
                                    existente.descricao = descricao
                                if classe:
                                    existente.classe = classe
                                if grupo:
                                    existente.grupo = grupo
                                if divisao:
                                    existente.divisao = divisao
                                if secao:
                                    existente.secao = secao
                        else:
                            # Adicionar à lista para bulk insert
                            cnae_para_inserir.append({
                                'cnae': cnae_limpo,
                                'descricao': descricao,
                                'classe': classe,
                                'grupo': grupo,
                                'divisao': divisao,
                                'secao': secao
                            })
                            cnae_existentes.add(cnae_limpo)  # Adicionar ao set para evitar duplicatas
                            stats["inseridos"] += 1
                        
                        stats["total_registros"] += 1
                    
                    except Exception as e:
                        logger.error(f"Erro ao processar linha {idx}: {e}")
                        stats["erros"].append(f"Linha {idx}: {str(e)}")
                        continue
                
                # Log de progresso
                if batch_end % 1000 == 0 or batch_end == total_rows:
                    logger.info(f"  📊 Processadas {batch_end}/{total_rows} linhas... ({len(cnae_para_inserir)} novos, {stats['atualizados']} atualizados)")
            
            # Commit atualizações primeiro
            if stats["atualizados"] > 0:
                db.commit()
                logger.info(f"✅ {stats['atualizados']} registros atualizados")
            
            # Bulk insert para novos registros
            if cnae_para_inserir:
                logger.info(f"💾 Inserindo {len(cnae_para_inserir)} novos CNAEs no banco...")
                insert_chunk_size = 1000
                
                for i in range(0, len(cnae_para_inserir), insert_chunk_size):
                    chunk = cnae_para_inserir[i:i + insert_chunk_size]
                    db.bulk_insert_mappings(CNAEHierarquia, chunk)
                    db.commit()
                    logger.info(f"  ✅ Inseridos {min(i + insert_chunk_size, len(cnae_para_inserir))}/{len(cnae_para_inserir)} registros...")
            
            logger.success(f"✅ Importação de CNAE concluída: {stats['inseridos']} inseridos, {stats['atualizados']} atualizados")
            
            return {
                "success": True,
                "message": "Upload e importação de CNAE concluídos",
                "stats": stats
            }
        
        finally:
            # Remover arquivo temporário
            try:
                os.unlink(caminho_temp)
            except:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload e importação de CNAE: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro no upload e importação de CNAE: {str(e)}")


# ============================================================================
# INFORMAÇÕES ADICIONAIS
# ============================================================================

"""
COMO USAR OS ENDPOINTS:

1. Via Swagger UI:
   - Acesse: https://comex-backend-gecp.onrender.com/docs
   - Procure: POST /upload-e-importar-excel ou POST /upload-e-importar-cnae
   - Clique em "Try it out"
   - Selecione o arquivo
   - Clique em "Execute"

2. Via curl (PowerShell):
   # Excel
   $filePath = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\H_EXPORTACAO_E IMPORTACAO_GERAL_2025-01_2025-12_DT20260107.xlsx"
   curl.exe -X POST "https://comex-backend-gecp.onrender.com/upload-e-importar-excel" -H "accept: application/json" -F "arquivo=@$filePath"
   
   # CNAE
   $filePath = "C:\Users\User\Desktop\Cursor\Projetos\projeto_comex\comex_data\comexstat_csv\CNAE.xlsx"
   curl.exe -X POST "https://comex-backend-gecp.onrender.com/upload-e-importar-cnae" -H "accept: application/json" -F "arquivo=@$filePath"

3. Via Python requests:
   import requests
   
   # Excel
   url = "https://comex-backend-gecp.onrender.com/upload-e-importar-excel"
   with open("arquivo.xlsx", "rb") as f:
       files = {"arquivo": f}
       response = requests.post(url, files=files)
   print(response.json())
   
   # CNAE
   url = "https://comex-backend-gecp.onrender.com/upload-e-importar-cnae"
   with open("CNAE.xlsx", "rb") as f:
       files = {"arquivo": f}
       response = requests.post(url, files=files)
   print(response.json())


FORMATO ESPERADO DOS ARQUIVOS:

Excel (Importação/Exportação):
- Código NCM (obrigatório)
- Descrição NCM (opcional)
- UF do Produto (opcional)
- Países (opcional)
- Mês (opcional, pode ser número ou nome do mês)
- Exportação - 2025 - Valor US$ FOB (ou Exportação - Valor US$ FOB)
- Exportação - 2025 - Quilograma Líquido (ou Exportação - Quilograma Líquido)
- Importação - 2025 - Valor US$ FOB (ou Importação - Valor US$ FOB)
- Importação - 2025 - Quilograma Líquido (ou Importação - Quilograma Líquido)

CNAE:
- CNAE (ou Código CNAE, CNAE 2.0, Subclasse) - obrigatório
- Descrição (ou Descrição Subclasse, Descrição CNAE) - opcional
- Classe (opcional)
- Grupo (opcional)
- Divisão (opcional)
- Seção (opcional)


OTIMIZAÇÕES IMPLEMENTADAS:

1. Processamento em Background (Excel):
   - Retorna resposta imediata para evitar timeout do Render (30s)
   - Processamento continua em thread separada
   - Logs detalhados para acompanhar progresso

2. Bulk Inserts:
   - Usa bulk_insert_mappings() em vez de inserções individuais
   - Processa em chunks de 1000 registros
   - Reduz tempo de processamento em 50-100x

3. Processamento em Batches:
   - Processa arquivos grandes em batches de 500 linhas
   - Evita consumo excessivo de memória
   - Logs de progresso a cada 1000 linhas

4. Verificação de Duplicatas Otimizada (CNAE):
   - Busca CNAEs existentes uma única vez
   - Usa set em memória para verificação rápida
   - Atualizações feitas individualmente apenas quando necessário
"""
