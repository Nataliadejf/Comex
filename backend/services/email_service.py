"""
Serviço de envio de emails.
"""
from loguru import logger
from config import settings

# Email do administrador para receber solicitações de aprovação
ADMIN_EMAIL = "nataliadejesus2@gmail.com"


def enviar_email_aprovacao(email_usuario: str, nome: str, token: str):
    """
    Envia email de solicitação de aprovação para o administrador.
    """
    try:
        logger.info("=" * 60)
        logger.info("📧 SOLICITAÇÃO DE APROVAÇÃO DE CADASTRO")
        logger.info("=" * 60)
        logger.info(f"Para: {ADMIN_EMAIL}")
        logger.info(f"Assunto: Nova solicitação de cadastro - {nome}")
        logger.info("")
        logger.info(f"Novo usuário solicitou cadastro:")
        logger.info(f"  Nome: {nome}")
        logger.info(f"  Email: {email_usuario}")
        logger.info(f"  Token de aprovação: {token}")
        logger.info("")
        logger.info(f"Link de aprovação: https://comex-4.onrender.com/aprovar?token={token}")
        logger.info(f"Ou acesse: https://comex-backend-wjco.onrender.com/docs e use o endpoint /aprovar-cadastro")
        logger.info(f"Ou use o endpoint: POST https://comex-backend-wjco.onrender.com/aprovar-cadastro")
        logger.info(f"Com body JSON: {{\"token\": \"{token}\"}}")
        logger.info("")
        logger.info("=" * 60)
        
        # TODO: Implementar envio real de email usando SMTP
        # Exemplo com smtplib:
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(f"Novo cadastro aguardando aprovação...\n\nNome: {nome}\nEmail: {email_usuario}\nToken: {token}")
        # msg['Subject'] = f'Nova solicitação de cadastro - {nome}'
        # msg['From'] = 'sistema@comex.com'
        # msg['To'] = ADMIN_EMAIL
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login('seu_email@gmail.com', 'sua_senha')
        # server.send_message(msg)
        # server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de aprovação: {e}")
        return False


def enviar_email_cadastro_aprovado(email: str, nome: str):
    """
    Envia email de cadastro aprovado para o usuário.
    """
    try:
        logger.info("=" * 60)
        logger.info("📧 CADASTRO APROVADO")
        logger.info("=" * 60)
        logger.info(f"Para: {email}")
        logger.info(f"Assunto: Seu cadastro foi aprovado!")
        logger.info("")
        logger.info(f"Olá {nome},")
        logger.info("")
        logger.info("Seu cadastro no Comex Analyzer foi aprovado!")
        logger.info("Agora você já pode fazer login e usar o sistema.")
        logger.info("")
        logger.info(f"Acesse: https://comex-4.onrender.com/login")
        logger.info("")
        logger.info("=" * 60)
        
        # TODO: Implementar envio real de email usando SMTP
        
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de cadastro aprovado: {e}")
        return False

