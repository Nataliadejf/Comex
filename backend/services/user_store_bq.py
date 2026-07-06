"""
Armazenamento de usuários (auth) no BigQuery — substitui o Postgres.
Usa DML (INSERT/UPDATE) para leitura imediata após escrita.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

_DEFAULT_TBL = "liquid-receiver-483923-n6.Projeto_Comex.usuarios"


def _tbl() -> str:
    return (os.getenv("COMEX_BQ_TABLE_USUARIOS") or _DEFAULT_TBL).strip().strip("`")


def _client():
    from services.bq_client import get_bigquery_client
    return get_bigquery_client()


def _q(sql: str, params: Optional[list] = None) -> List[dict]:
    from services.bq_client import run_query
    return run_query(_client(), sql, params)


def get_user_by_email(email: str) -> Optional[Dict]:
    from google.cloud import bigquery
    e = (email or "").strip().lower()
    if not e:
        return None
    rows = _q(
        f"SELECT * FROM `{_tbl()}` WHERE LOWER(email) = @e LIMIT 1",
        [bigquery.ScalarQueryParameter("e", "STRING", e)],
    )
    return rows[0] if rows else None


def count_field(field: str, value: str) -> int:
    from google.cloud import bigquery
    if field not in {"email", "cpf", "cnpj"}:
        return 0
    v = (value or "").strip()
    if not v:
        return 0
    col = "LOWER(email)" if field == "email" else field
    val = v.lower() if field == "email" else v
    rows = _q(
        f"SELECT COUNT(*) n FROM `{_tbl()}` WHERE {col} = @v",
        [bigquery.ScalarQueryParameter("v", "STRING", val)],
    )
    return int(rows[0].get("n") or 0) if rows else 0


def create_user(email: str, senha_hash: str, nome_completo: str,
                nome_empresa: Optional[str] = None, cpf: Optional[str] = None,
                cnpj: Optional[str] = None, data_nascimento=None,
                status_aprovacao: str = "aprovado", ativo: int = 1) -> Dict:
    """Insere um usuário (DML). Retorna o dict do usuário."""
    from google.cloud import bigquery
    uid = str(uuid.uuid4())
    params = [
        bigquery.ScalarQueryParameter("id", "STRING", uid),
        bigquery.ScalarQueryParameter("email", "STRING", (email or "").strip().lower()),
        bigquery.ScalarQueryParameter("senha_hash", "STRING", senha_hash),
        bigquery.ScalarQueryParameter("nome_completo", "STRING", nome_completo or ""),
        bigquery.ScalarQueryParameter("nome_empresa", "STRING", nome_empresa),
        bigquery.ScalarQueryParameter("cpf", "STRING", cpf),
        bigquery.ScalarQueryParameter("cnpj", "STRING", cnpj),
        bigquery.ScalarQueryParameter("data_nascimento", "DATE", data_nascimento),
        bigquery.ScalarQueryParameter("status", "STRING", status_aprovacao),
        bigquery.ScalarQueryParameter("ativo", "INT64", int(ativo)),
    ]
    _q(
        f"""INSERT INTO `{_tbl()}`
            (id,email,senha_hash,nome_completo,nome_empresa,cpf,cnpj,data_nascimento,
             status_aprovacao,ativo,criado_em)
            VALUES (@id,@email,@senha_hash,@nome_completo,@nome_empresa,@cpf,@cnpj,
                    @data_nascimento,@status,@ativo,CURRENT_TIMESTAMP())""",
        params,
    )
    return {
        "id": uid, "email": (email or "").strip().lower(),
        "nome_completo": nome_completo, "nome_empresa": nome_empresa,
        "status_aprovacao": status_aprovacao, "ativo": ativo,
    }


def update_last_login(email: str) -> None:
    from google.cloud import bigquery
    try:
        _q(
            f"UPDATE `{_tbl()}` SET ultimo_login = CURRENT_TIMESTAMP() WHERE LOWER(email) = @e",
            [bigquery.ScalarQueryParameter("e", "STRING", (email or "").strip().lower())],
        )
    except Exception as exc:
        logger.warning(f"update_last_login falhou: {exc}")


def authenticate(email: str, senha: str) -> Optional[Dict]:
    """Valida email+senha. Retorna o usuário (dict) se ativo e senha correta."""
    from auth import verify_password
    u = get_user_by_email(email)
    if not u:
        return None
    if not int(u.get("ativo") or 0):
        logger.warning(f"Login negado (inativo/pendente): {email}")
        return None
    if not verify_password(senha, u.get("senha_hash") or ""):
        return None
    return u


def listar_pendentes(limit: int = 100) -> List[Dict]:
    rows = _q(
        f"""SELECT id,email,nome_completo,nome_empresa,criado_em
            FROM `{_tbl()}` WHERE status_aprovacao='pendente' OR ativo=0
            ORDER BY criado_em DESC LIMIT {int(limit)}"""
    )
    return rows


def aprovar(email: str) -> bool:
    from google.cloud import bigquery
    try:
        _q(
            f"UPDATE `{_tbl()}` SET status_aprovacao='aprovado', ativo=1 WHERE LOWER(email)=@e",
            [bigquery.ScalarQueryParameter("e", "STRING", (email or "").strip().lower())],
        )
        return True
    except Exception as exc:
        logger.warning(f"aprovar falhou: {exc}")
        return False
