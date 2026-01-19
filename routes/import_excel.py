# ================================================================
# IMPORTAR EXCEL E CNAE - VERSÃO CORRIGIDA COM ROLLBACK
# ================================================================

import threading
import tempfile
import os
import re
from datetime import date
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import OperacaoComex, TipoOperacao, CNAEHierarquia
from database.database import SessionLocal
from loguru import logger


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================================================================
# ENDPOINT 1 — IMPORTAÇÃO DO EXCEL (CORRIGIDO)
# ================================================================
@app.post("/upload-e-importar-excel")
async def upload_e_importar_excel(
    arquivo: UploadFile = File(...),
):
    nome_arquivo = arquivo.filename.lower()

    if not (nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Arquivo precisa ser XLSX ou XLS")

    # salvar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        conteudo = await arquivo.read()
        tmp.write(conteudo)
        caminho_temp = tmp.name

    # processamento em background
    def processar():
        db = SessionLocal()

        try:
            logger.info("Lendo planilha…")
            df = pd.read_excel(caminho_temp)

            ano = 2025
            match = re.search(r"20\d{2}", arquivo.filename)
            if match:
                ano = int(match.group())

            meses_map = {
                'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
                'abril': 4, 'maio': 5, 'junho': 6,
                'julho': 7, 'agosto': 8, 'setembro': 9,
                'outubro': 10, 'novembro': 11, 'dezembro': 12
            }

            operacoes = []

            # PROCESSAMENTO EM BATCHES
            for idx, row in df.iterrows():

                try:
                    ncm = str(row.get("Código NCM", "")).strip()
                    if not ncm or len(ncm) < 4:
                        continue

                    ncm_normalizado = ncm[:8] if len(ncm) >= 8 else ncm.zfill(8)
                    descricao = str(row.get("Descrição NCM", "")).strip()[:500]
                    uf = str(row.get("UF do Produto", "")).strip()[:2]
                    pais = str(row.get("Países", "")).strip()

                    mes_str = str(row.get("Mês", "")).strip()
                    mes = None

                    if mes_str:
                        if mes_str.isdigit():
                            mes = int(mes_str)
                        else:
                            for nome, numero in meses_map.items():
                                if nome in mes_str.lower():
                                    mes = numero
                                    break

                    if not mes or mes < 1 or mes > 12:
                        mes = 1

                    data_operacao = date(ano, mes, 1)
                    mes_referencia = f"{ano}-{mes:02d}"

                    # EXPORTAÇÃO
                    valor_exp = (
                        row.get("Exportação - 2025 - Valor US$ FOB", 0)
                        or row.get("Exportação - Valor US$ FOB", 0)
                    )
                    peso_exp = (
                        row.get("Exportação - 2025 - Quilograma Líquido", 0)
                        or row.get("Exportação - Quilograma Líquido", 0)
                    )

                    if pd.notna(valor_exp) and float(valor_exp) > 0:
                        operacoes.append({
                            "ncm": ncm_normalizado,
                            "descricao_produto": descricao,
                            "tipo_operacao": TipoOperacao.EXPORTACAO,
                            "uf": uf,
                            "pais_origem_destino": pais,
                            "valor_fob": float(valor_exp),
                            "peso_liquido_kg": float(peso_exp) if pd.notna(peso_exp) else 0,
                            "data_operacao": data_operacao,
                            "mes_referencia": mes_referencia,
                            "arquivo_origem": arquivo.filename,
                        })

                    # IMPORTAÇÃO
                    valor_imp = (
                        row.get("Importação - 2025 - Valor US$ FOB", 0)
                        or row.get("Importação - Valor US$ FOB", 0)
                    )
                    peso_imp = (
                        row.get("Importação - 2025 - Quilograma Líquido", 0)
                        or row.get("Importação - Quilograma Líquido", 0)
                    )

                    if pd.notna(valor_imp) and float(valor_imp) > 0:
                        operacoes.append({
                            "ncm": ncm_normalizado,
                            "descricao_produto": descricao,
                            "tipo_operacao": TipoOperacao.IMPORTACAO,
                            "uf": uf,
                            "pais_origem_destino": pais,
                            "valor_fob": float(valor_imp),
                            "peso_liquido_kg": float(peso_imp) if pd.notna(peso_imp) else 0,
                            "data_operacao": data_operacao,
                            "mes_referencia": mes_referencia,
                            "arquivo_origem": arquivo.filename,
                        })

                except Exception as e:
                    logger.error(f"Erro linha {idx}: {e}")
                    continue

            # =============================
            #      INSERÇÃO EM CHUNKS
            # =============================
            logger.info("Inserindo dados em chunks…")
            chunk_size = 1000

            for i in range(0, len(operacoes), chunk_size):
                chunk = operacoes[i:i + chunk_size]

                try:
                    db.bulk_insert_mappings(OperacaoComex, chunk)
                    db.commit()

                except Exception as erro_chunk:

                    logger.error(f"Chunk falhou, tentando item por item… ERRO: {erro_chunk}")
                    db.rollback()

                    # inserir individualmente
                    for item in chunk:
                        try:
                            db.bulk_insert_mappings(OperacaoComex, [item])
                            db.commit()
                        except Exception as erro_individual:
                            logger.error(f"Registro inválido: {item}")
                            logger.error(f"Motivo: {erro_individual}")
                            db.rollback()

        except Exception as e:
            logger.error(f"Erro no processamento background: {e}")
        finally:
            db.close()
            os.unlink(caminho_temp)

    threading.Thread(target=processar, daemon=True).start()

    return {
        "ok": True,
        "msg": "Arquivo recebido. Processamento iniciado.",
    }


# ================================================================
# ENDPOINT 2 — IMPORTAÇÃO CNAE (CORRIGIDO)
# ================================================================
@app.post("/upload-e-importar-cnae")
async def upload_e_importar_cnae(arquivo: UploadFile = File(...), db: Session = Depends(get_db)):
    nome = arquivo.filename.lower()

    if not (nome.endswith(".xlsx") or nome.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Arquivo precisa ser XLSX ou XLS")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await arquivo.read())
        caminho_temp = tmp.name

    try:
        df = pd.read_excel(caminho_temp)

        existentes = {x[0] for x in db.query(CNAEHierarquia.cnae).all()}
        novos = []

        for idx, row in df.iterrows():
            try:
                cnae = (
                    str(row.get("CNAE", "")) or
                    str(row.get("Código CNAE", "")) or
                    str(row.get("Subclasse", ""))
                ).strip()

                if not cnae or len(cnae) < 4:
                    continue

                cnae_limpo = cnae.replace(".", "").replace("-", "").strip()

                descricao = str(row.get("Descrição", "")).strip()
                classe = str(row.get("Classe", "")).strip()
                grupo = str(row.get("Grupo", "")).strip()
                divisao = str(row.get("Divisão", "")).strip()
                secao = str(row.get("Seção", "")).strip()

                if cnae_limpo in existentes:
                    reg = db.query(CNAEHierarquia).filter(CNAEHierarquia.cnae == cnae_limpo).first()
                    if reg:
                        reg.descricao = descricao
                        reg.classe = classe
                        reg.grupo = grupo
                        reg.divisao = divisao
                        reg.secao = secao
                else:
                    novos.append({
                        "cnae": cnae_limpo,
                        "descricao": descricao,
                        "classe": classe,
                        "grupo": grupo,
                        "divisao": divisao,
                        "secao": secao,
                    })
                    existentes.add(cnae_limpo)

            except Exception as e:
                logger.error(f"Erro linha {idx}: {e}")
                continue

        db.commit()

        # inserir novos
        for i in range(0, len(novos), 500):
            chunk = novos[i:i + 500]

            try:
                db.bulk_insert_mappings(CNAEHierarquia, chunk)
                db.commit()
            except Exception as e:
                logger.error(f"Erro chunk CNAE: {e}")
                db.rollback()

    finally:
        os.unlink(caminho_temp)

    return {"ok": True, "inseridos": len(novos)}
