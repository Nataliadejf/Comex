"""Rastreamento de uso: registra pings de sessão (heartbeat) e expõe um
painel de uso por usuário (nº de acessos, tempo de permanência, telas)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/atividade", tags=["atividade"])
_bearer = HTTPBearer(auto_error=False)

_TABELA = "liquid-receiver-483923-n6.Projeto_Comex.acessos_log"


def _email(cred: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if not cred or not cred.credentials:
        return None
    from auth import decode_token_email
    return decode_token_email(cred.credentials)


class PingBody(BaseModel):
    session_id: str
    tela: Optional[str] = None
    evento: Optional[str] = "ping"


@router.post("/ping")
def ping(body: PingBody, request: Request, cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Heartbeat: registra atividade do usuário (streaming insert, barato)."""
    email = _email(cred)
    if not email:
        return {"ok": False}
    try:
        from services.bq_client import get_bigquery_client
        client = get_bigquery_client()
        ip = request.client.host if request.client else None
        row = {
            "email": email.strip().lower(),
            "evento": (body.evento or "ping")[:20],
            "tela": (body.tela or "")[:120],
            "session_id": (body.session_id or "")[:64],
            "ip": ip,
            "criado_em": datetime.now(timezone.utc).isoformat(),
        }
        errs = client.insert_rows_json(_TABELA, [row])
        if errs:
            logger.warning(f"ping insert erro: {errs}")
    except Exception as exc:
        logger.warning(f"ping falhou: {exc}")
    return {"ok": True}
