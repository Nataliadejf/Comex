"""
Serviço de envio de emails (stub - não envia emails reais por padrão).
"""
from loguru import logger


def enviar_email_aprovacao(email: str, nome: str, token: str):
    """
    Envia email de solicitação de aprovação (stub).
    Em produção, implementar envio real de email.
    """
    logger.info(f"📧 [STUB] Email de aprovação seria enviado para: {email}")
    logger.info(f"   Nome: {nome}")
    logger.info(f"   Token: {token}")
    logger.info(f"   Link de aprovação: http://localhost:3000/aprovar?token={token}")
    # TODO: Implementar envio real de email usando SMTP ou serviço de email
    return True


def enviar_email_cadastro_aprovado(email: str, nome: str):
    """
    Envia email de cadastro aprovado (stub).
    Em produção, implementar envio real de email.
    """
    logger.info(f"📧 [STUB] Email de cadastro aprovado seria enviado para: {email}")
    logger.info(f"   Nome: {nome}")
    logger.info(f"   Mensagem: Seu cadastro foi aprovado! Você já pode fazer login.")
    # TODO: Implementar envio real de email usando SMTP ou serviço de email
    return True

