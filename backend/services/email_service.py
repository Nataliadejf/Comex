"""
Serviço de envio de e-mails via SMTP (configurável por variáveis de ambiente).

Variáveis (definir no Render):
  SMTP_HOST      ex.: smtp-relay.brevo.com | smtp.gmail.com | smtp-mail.outlook.com
  SMTP_PORT      ex.: 587
  SMTP_USER      usuário/login SMTP
  SMTP_PASSWORD  senha/app-password/chave SMTP
  SMTP_FROM      remetente (ex.: "Comex Analyzer <no-reply@seudominio.com>")
  FRONTEND_URL   ex.: https://comex-bs9w.onrender.com  (para montar o link de reset)

Se SMTP não estiver configurado, as mensagens são apenas registradas no log.
"""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "nataliadejesus2@hotmail.com")


def _smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from": (os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "").strip(),
    }


def smtp_configurado() -> bool:
    c = _smtp_config()
    return bool(c["host"] and c["user"] and c["password"] and c["from"])


def frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or "https://comex-bs9w.onrender.com").rstrip("/")


def enviar_email(destino: str, assunto: str, html: str, texto: str = "") -> bool:
    """Envia um e-mail HTML via SMTP. Retorna True se enviado."""
    cfg = _smtp_config()
    if not smtp_configurado():
        logger.warning("SMTP não configurado — e-mail apenas registrado no log.")
        logger.info(f"[EMAIL não enviado] Para: {destino} | Assunto: {assunto}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = cfg["from"]
        msg["To"] = destino
        if texto:
            msg.attach(MIMEText(texto, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        contexto = ssl.create_default_context()
        if cfg["port"] == 465:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=contexto, timeout=30) as s:
                s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as s:
                s.ehlo()
                s.starttls(context=contexto)
                s.login(cfg["user"], cfg["password"])
                s.send_message(msg)
        logger.info(f"✅ E-mail enviado para {destino} — {assunto}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {destino}: {e}")
        return False


def enviar_email_redefinicao(email: str, nome: str, token: str) -> bool:
    """Envia o link de redefinição de senha para o usuário."""
    link = f"{frontend_url()}/login?reset_token={token}"
    assunto = "Redefinição de senha — Comex Analyzer"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto">
      <h2 style="color:#722ed1">Comex Analyzer</h2>
      <p>Olá{(' ' + nome) if nome else ''},</p>
      <p>Recebemos uma solicitação para redefinir sua senha. Clique no botão abaixo
         (válido por 2 horas):</p>
      <p style="text-align:center;margin:28px 0">
        <a href="{link}" style="background:#722ed1;color:#fff;padding:12px 24px;
           border-radius:6px;text-decoration:none;font-weight:bold">Redefinir senha</a>
      </p>
      <p style="font-size:12px;color:#888">Se você não solicitou, ignore este e-mail.
         Link: <a href="{link}">{link}</a></p>
    </div>
    """
    texto = f"Redefinição de senha — Comex Analyzer\n\nAcesse (válido 2h): {link}\n\nSe não solicitou, ignore."
    return enviar_email(email, assunto, html, texto)


def enviar_email_aprovacao(email_usuario: str, nome: str, token: str) -> bool:
    """Notifica o administrador sobre novo cadastro pendente."""
    assunto = f"Novo cadastro aguardando aprovação — {nome}"
    html = f"""
    <div style="font-family:Arial,sans-serif">
      <h3>Novo cadastro no Comex Analyzer</h3>
      <p><b>Nome:</b> {nome}<br><b>E-mail:</b> {email_usuario}</p>
      <p>Aprove pela ferramenta admin:
         <code>python gerenciar_usuarios.py aprovar {email_usuario}</code></p>
    </div>
    """
    ok = enviar_email(ADMIN_EMAIL, assunto, html)
    if not ok:
        logger.info(f"[Aprovação pendente] {nome} <{email_usuario}> — aprovar via CLI.")
    return ok


def enviar_email_cadastro_aprovado(email: str, nome: str) -> bool:
    """Avisa o usuário que o cadastro foi aprovado."""
    assunto = "Seu cadastro foi aprovado — Comex Analyzer"
    html = f"""
    <div style="font-family:Arial,sans-serif">
      <h3>Cadastro aprovado!</h3>
      <p>Olá {nome}, seu acesso ao Comex Analyzer foi liberado.</p>
      <p><a href="{frontend_url()}/login">Fazer login</a></p>
    </div>
    """
    return enviar_email(email, assunto, html)
