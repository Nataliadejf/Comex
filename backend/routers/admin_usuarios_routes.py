"""Administração de usuários (BigQuery): listar pendentes, aprovar, recusar.

Autorização por e-mail admin (JWT). A lista de admins vem da env ADMIN_EMAILS
(separada por vírgula); se vazia, usa um default seguro com a conta da Natália.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/admin/usuarios", tags=["admin-usuarios"])


def gerar_token_acao(email: str, acao: str, dias: int = 7) -> str:
    """Gera um token assinado para aprovar/recusar por link (expira em `dias`)."""
    from datetime import timedelta
    from auth import create_access_token
    return create_access_token(
        data={"sub": (email or "").strip().lower(), "act": acao},
        expires_delta=timedelta(days=dias),
    )


def _pagina(titulo: str, msg: str, cor: str = "#1890ff") -> HTMLResponse:
    html = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{titulo}</title></head>
    <body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:40px;text-align:center">
      <div style="max-width:460px;margin:40px auto;background:#fff;border-radius:12px;padding:32px 24px;box-shadow:0 4px 16px rgba(0,0,0,.08)">
        <div style="font-size:44px;color:{cor}">&#10003;</div>
        <h2 style="color:#222;margin:8px 0">{titulo}</h2>
        <p style="color:#555">{msg}</p>
        <a href="https://comex-bs9w.onrender.com/usuarios"
           style="display:inline-block;margin-top:12px;background:{cor};color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none">
          Abrir gerenciamento</a>
      </div></body></html>"""
    return HTMLResponse(content=html)

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


@router.get("/uso")
def uso(_admin: str = Depends(require_admin), dias: int = 90):
    """Painel de uso por usuário: nº de sessões (acessos), tempo de permanência
    e telas mais visitadas — a partir do log de atividade (heartbeat)."""
    from services.bq_client import get_bigquery_client, run_query
    t = "liquid-receiver-483923-n6.Projeto_Comex.acessos_log"
    client = get_bigquery_client()
    # Por sessão: início, fim e duração (min); depois agrega por usuário.
    sql = f"""
    WITH sess AS (
      SELECT email, session_id,
             MIN(criado_em) ini, MAX(criado_em) fim,
             TIMESTAMP_DIFF(MAX(criado_em), MIN(criado_em), SECOND) dur_s
      FROM `{t}`
      WHERE criado_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(dias)} DAY)
        AND session_id != ''
        AND email NOT LIKE '%@example.com'
      GROUP BY email, session_id
    )
    SELECT email,
           COUNT(*) AS acessos,
           MAX(fim) AS ultimo_acesso,
           ROUND(SUM(dur_s)/60.0, 1) AS tempo_total_min,
           ROUND(AVG(dur_s)/60.0, 1) AS tempo_medio_min
    FROM sess GROUP BY email ORDER BY acessos DESC
    """
    usuarios = [dict(r) for r in run_query(client, sql, None)]

    # Telas mais usadas por usuário (top 5 por nº de pings)
    sql_t = f"""
    SELECT email, tela, COUNT(*) n FROM `{t}`
    WHERE criado_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(dias)} DAY)
      AND tela != '' AND tela IS NOT NULL
      AND email NOT LIKE '%@example.com'
    GROUP BY email, tela ORDER BY email, n DESC
    """
    # Nome amigável de cada tela (rota → nome)
    nomes_tela = {
        "/": "Dashboard", "/dashboard": "Dashboard",
        "/dashboard-comex-bq": "Comex BigQuery", "/busca": "Busca Avançada",
        "/ncm": "Análise por NCM", "/panorama-global": "Panorama Global",
        "/empresas": "Empresas por Segmento", "/contatos": "Empresas & Contatos",
        "/habilitadas": "Habilitadas Comex", "/usuarios": "Gerenciar Usuários",
    }

    def _nome(rota):
        r = (rota or "").rstrip("/") or "/"
        if r.startswith("/ncm/"):
            r = "/ncm"
        return nomes_tela.get(r, r)

    telas_por_user = {}
    ranking_global = {}
    for r in run_query(client, sql_t, None):
        nome = _nome(r["tela"])
        telas_por_user.setdefault(r["email"], {})
        telas_por_user[r["email"]][nome] = telas_por_user[r["email"]].get(nome, 0) + int(r["n"])
        ranking_global[nome] = ranking_global.get(nome, 0) + int(r["n"])

    for u in usuarios:
        tp = telas_por_user.get(u["email"], {})
        u["telas"] = [{"tela": k, "visitas": v}
                      for k, v in sorted(tp.items(), key=lambda x: x[1], reverse=True)][:5]
        u["ultimo_acesso"] = u["ultimo_acesso"].isoformat() if u.get("ultimo_acesso") else None

    telas_ranking = [{"tela": k, "visitas": v}
                     for k, v in sorted(ranking_global.items(), key=lambda x: x[1], reverse=True)]
    resumo = {
        "usuarios_ativos": len(usuarios),
        "total_acessos": sum(int(u.get("acessos") or 0) for u in usuarios),
        "tempo_total_min": round(sum(float(u.get("tempo_total_min") or 0) for u in usuarios), 1),
        "tela_mais_acessada": telas_ranking[0]["tela"] if telas_ranking else None,
    }
    return {"dias": dias, "resumo": resumo, "telas_ranking": telas_ranking, "usuarios": usuarios}


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


@router.get("/acao-link", response_class=HTMLResponse)
def acao_por_link(token: str = Query(...)):
    """Aprova/recusa por link do e-mail (token assinado, sem exigir login)."""
    from auth import decode_token
    from services import user_store_bq

    payload = decode_token(token)
    if not payload or not payload.get("sub") or payload.get("act") not in ("approve", "reject"):
        return _pagina("Link inválido ou expirado",
                       "Este link não é mais válido. Abra o gerenciamento para aprovar manualmente.",
                       "#f5222d")
    email = payload["sub"]
    u = user_store_bq.get_user_by_email(email)
    if not u:
        return _pagina("Usuário não encontrado", f"O cadastro «{email}» não existe mais.", "#faad14")

    if payload["act"] == "approve":
        user_store_bq.aprovar(email)
        logger.info(f"Aprovação por link: {email}")
        try:
            from services.email_service import enviar_email_cadastro_aprovado
            enviar_email_cadastro_aprovado(email, u.get("nome_completo") or "")
        except Exception:
            pass
        return _pagina("Cadastro aprovado", f"«{email}» agora pode acessar o Comex Analyzer.", "#52c41a")
    else:
        user_store_bq.recusar(email)
        logger.info(f"Recusa por link: {email}")
        return _pagina("Cadastro recusado", f"«{email}» foi recusado e não terá acesso.", "#f5222d")
