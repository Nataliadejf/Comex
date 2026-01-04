"""
Script para configurar credenciais de email.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
import os

def configurar_email():
    """Guia para configurar email."""
    print("=" * 60)
    print("CONFIGURAÇÃO DE EMAIL")
    print("=" * 60)
    print()
    print("Para enviar emails de aprovação, configure as variáveis de ambiente:")
    print()
    print("1. Crie ou edite o arquivo .env na pasta backend/")
    print()
    print("2. Adicione as seguintes variáveis:")
    print()
    print("   EMAIL_SENDER=nataliadejesus2@gmail.com")
    print("   EMAIL_SENDER_PASSWORD=sua_senha_de_app")
    print("   EMAIL_ADMIN=nataliadejesus2@gmail.com")
    print("   APP_URL=http://localhost:3000")
    print()
    print("3. Para Gmail, você precisa criar uma 'Senha de App':")
    print("   - Acesse: https://myaccount.google.com/apppasswords")
    print("   - Gere uma senha de app")
    print("   - Use essa senha em EMAIL_SENDER_PASSWORD")
    print()
    print("4. Alternativamente, use outro provedor de email:")
    print("   - Outlook: smtp-mail.outlook.com:587")
    print("   - Yahoo: smtp.mail.yahoo.com:587")
    print()
    print("=" * 60)
    print()
    print("⚠️  IMPORTANTE:")
    print("   - NUNCA commite o arquivo .env no Git!")
    print("   - A senha deve ser uma 'Senha de App' do Gmail")
    print("   - Em produção, use variáveis de ambiente do servidor")
    print()

if __name__ == "__main__":
    configurar_email()


