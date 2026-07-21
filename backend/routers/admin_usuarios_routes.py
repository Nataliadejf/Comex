"""Administração de usuários (BigQuery): listar pendentes, aprovar, recusar.

Autorização por e-mail admin (JWT). A lista de admins vem da env ADMIN_EMAILS
(separada por vírgula); se vazia, usa um default seguro com a conta da Natália.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/admin/usuarios", tags=["admin-usuarios"])

_bearer = HTTPBearer(auto_error=False)

_DEFAULT_ADMINS = "nataliadejesus2@hotmail.com,nataliadejesus2@gmail.com"


def _admin_emails() -> set:
    raw = os.getenv("ADMIN_EMAILS", _DEFAULT_ADMINS)
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _email_do_token(cred: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if not cred or not cred.credentials:
        return None
    from auth import decode_token_email
    return decode_token_email(cred.credentials)


def require_admin(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    email = _email_do_token(cred)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido ou ausente")
    if email.strip().lower() not in _admin_emails():
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return email


class EmailBody(BaseModel):
    email: str


@router.get("/me")
def me(cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Retorna se o usuário logado é admin (para o frontend mostrar o menu)."""
    email = _email_do_token(cred)
    return {"email": email, "is_admin": bool(email and email.strip().lower() in _admin_emails())}


@router.get("/pendentes")
def pendentes(_admin: str = Depends(require_admin)):
    from services import user_store_bq
    return {"pendentes": user_store_bq.listar_pendentes(200)}


@router.post("/aprovar")
def aprovar(body: EmailBody, admin: str = Depends(require_admin)):
    from services import user_store_bq
    u = user_store_bq.get_user_by_email(body.email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    ok = user_store_bq.aprovar(body.email)
    if not ok:
        raise HTTPException(status_code=500, detail="Falha ao aprovar")
    logger.info(f"Admin {admin} aprovou {body.email}")
    try:
        from services.email_service import enviar_email_cadastro_aprovado
        enviar_email_cadastro_aprovado(body.email, u.get("nome_completo") or "")
    except Exception as exc:
        logger.warning(f"E-mail de aprovação não enviado: {exc}")
    return {"ok": True, "email": body.email, "status": "aprovado"}


@router.post("/recusar")
def recusar(body: EmailBody, admin: str = Depends(require_admin)):
    from services import user_store_bq
    u = user_store_bq.get_user_by_email(body.email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    ok = user_store_bq.recusar(body.email)
    if not ok:
        raise HTTPException(status_code=500, detail="Falha ao recusar")
    logger.info(f"Admin {admin} recusou {body.email}")
    return {"ok": True, "email": body.email, "status": "recusado"}
