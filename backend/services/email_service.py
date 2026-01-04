"""
Serviço de envio de emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from config import settings


def enviar_email_aprovacao(
    email_destino: str,
    nome_usuario: str,
    token_aprovacao: str,
    link_aprovacao: str
) -> bool:
    """
    Envia email de solicitação de aprovação de cadastro.
    """
    try:
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Solicitação de Aprovação - Comex Analyzer'
        msg['From'] = settings.email_sender
        msg['To'] = settings.email_admin
        
        # Corpo do email em HTML
        html_body = f"""
        <html>
          <head></head>
          <body>
            <h2>Nova Solicitação de Cadastro - Comex Analyzer</h2>
            <p>Olá,</p>
            <p>Uma nova solicitação de cadastro foi recebida:</p>
            <ul>
              <li><strong>Nome:</strong> {nome_usuario}</li>
              <li><strong>Email:</strong> {email_destino}</li>
              <li><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</li>
            </ul>
            <p>Para aprovar este cadastro, clique no link abaixo:</p>
            <p><a href="{link_aprovacao}" style="background-color: #722ed1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Aprovar Cadastro</a></p>
            <p>Ou copie e cole este link no navegador:</p>
            <p>{link_aprovacao}</p>
            <p><strong>Token de aprovação:</strong> {token_aprovacao}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">Este é um email automático do sistema Comex Analyzer.</p>
          </body>
        </html>
        """
        
        # Corpo em texto simples
        text_body = f"""
        Nova Solicitação de Cadastro - Comex Analyzer
        
        Nome: {nome_usuario}
        Email: {email_destino}
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        
        Para aprovar este cadastro, acesse:
        {link_aprovacao}
        
        Token de aprovação: {token_aprovacao}
        """
        
        # Adicionar partes ao email
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Enviar email
        if settings.email_sender_password:
            # Usar SMTP com autenticação
            server = smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port)
            server.starttls()
            server.login(settings.email_sender, settings.email_sender_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email de aprovação enviado para {settings.email_admin}")
            return True
        else:
            # Modo desenvolvimento - apenas logar
            logger.warning("EMAIL_SENDER_PASSWORD não configurado. Email não será enviado.")
            logger.info(f"Email que seria enviado para {settings.email_admin}:")
            logger.info(f"Assunto: {msg['Subject']}")
            logger.info(f"Link de aprovação: {link_aprovacao}")
            logger.info(f"Token: {token_aprovacao}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar email de aprovação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def enviar_email_cadastro_aprovado(email_destino: str, nome_usuario: str) -> bool:
    """
    Envia email informando que o cadastro foi aprovado.
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Cadastro Aprovado - Comex Analyzer'
        msg['From'] = settings.email_sender
        msg['To'] = email_destino
        
        html_body = f"""
        <html>
          <head></head>
          <body>
            <h2>Cadastro Aprovado!</h2>
            <p>Olá {nome_usuario},</p>
            <p>Seu cadastro no <strong>Comex Analyzer</strong> foi aprovado com sucesso!</p>
            <p>Agora você pode acessar o sistema usando seu email e senha.</p>
            <p><a href="{settings.app_url}/login" style="background-color: #722ed1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Sistema</a></p>
            <hr>
            <p style="color: #666; font-size: 12px;">Este é um email automático do sistema Comex Analyzer.</p>
          </body>
        </html>
        """
        
        text_body = f"""
        Cadastro Aprovado!
        
        Olá {nome_usuario},
        
        Seu cadastro no Comex Analyzer foi aprovado com sucesso!
        Agora você pode acessar o sistema usando seu email e senha.
        
        Acesse: {settings.app_url}/login
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        if settings.email_sender_password:
            server = smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port)
            server.starttls()
            server.login(settings.email_sender, settings.email_sender_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email de aprovação enviado para {email_destino}")
            return True
        else:
            logger.warning("EMAIL_SENDER_PASSWORD não configurado. Email não será enviado.")
            logger.info(f"Email que seria enviado para {email_destino}: Cadastro aprovado!")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar email de cadastro aprovado: {e}")
        return False


