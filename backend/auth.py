"""
Sistema de autenticação e autorização.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, Usuario
from loguru import logger

# Configuração de segurança
SECRET_KEY = "comex_analyzer_secret_key_change_in_production"  # MUDAR EM PRODUÇÃO!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 dias

# Usar bcrypt diretamente (sem passlib para evitar problemas)
logger.info("✅ Usando bcrypt diretamente (sem passlib)")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta usando bcrypt diretamente."""
    try:
        # Truncar senha se necessário antes de verificar (bcrypt limite: 72 bytes)
        password_bytes = plain_password.encode('utf-8')
        tamanho_original = len(password_bytes)
        
        # TRUNCAR PARA EXATAMENTE 72 BYTES (não menos, não mais)
        if tamanho_original > 72:
            password_bytes = password_bytes[:72]
            logger.warning(f"⚠️ Senha truncada de {tamanho_original} para 72 bytes na verificação")
        
        # VERIFICAÇÃO FINAL: garantir que não excede 72 bytes
        if len(password_bytes) > 72:
            logger.error(f"❌ ERRO CRÍTICO: Senha ainda tem {len(password_bytes)} bytes após truncamento!")
            password_bytes = password_bytes[:72]
        
        # Usar bcrypt diretamente
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        
        # Verificar se o hash parece ser válido (começa com $2b$ ou $2a$)
        if isinstance(hash_bytes, bytes):
            hash_str = hash_bytes.decode('utf-8', errors='ignore')
        else:
            hash_str = hashed_password
        
        if not hash_str.startswith('$2'):
            logger.error(f"❌ Hash inválido (não é bcrypt): {hash_str[:20]}...")
            logger.error("Hash pode ter sido criado com passlib. Execute CORRIGIR_TODOS_USUARIOS.bat")
            return False
        
        # GARANTIR que password_bytes não excede 72 bytes antes de chamar bcrypt
        # ÚLTIMA VERIFICAÇÃO antes de chamar bcrypt.checkpw
        if len(password_bytes) > 72:
            logger.error(f"❌ ERRO CRÍTICO: Senha tem {len(password_bytes)} bytes antes de bcrypt.checkpw!")
            password_bytes = password_bytes[:72]
            logger.warning(f"⚠️ Truncado para {len(password_bytes)} bytes")
        
        # Chamar bcrypt.checkpw com try/except para capturar QUALQUER erro
        try:
            resultado = bcrypt.checkpw(password_bytes, hash_bytes)
            return resultado
        except ValueError as e:
            # Se o erro for sobre 72 bytes, tentar truncar novamente
            if "72 bytes" in str(e).lower() or "truncate" in str(e).lower():
                logger.error(f"❌ Erro de 72 bytes capturado: {e}")
                logger.error(f"Tamanho atual: {len(password_bytes)} bytes")
                # Forçar truncamento para exatamente 72 bytes
                password_bytes = password_bytes[:72]
                logger.warning(f"⚠️ Tentando novamente com {len(password_bytes)} bytes")
                try:
                    return bcrypt.checkpw(password_bytes, hash_bytes)
                except Exception as e2:
                    logger.error(f"❌ Erro mesmo após truncamento: {e2}")
                    return False
            raise
    except AssertionError as e:
        logger.error(f"❌ AssertionError na verificação: {e}")
        # Última tentativa: forçar truncamento
        password_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        try:
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e2:
            logger.error(f"❌ Erro mesmo após truncamento: {e2}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar senha: {e}")
        logger.error(f"Tamanho da senha: {len(plain_password)} caracteres, {len(plain_password.encode('utf-8'))} bytes")
        logger.error(f"Hash (primeiros 30 chars): {hashed_password[:30] if hashed_password else 'None'}...")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_password_hash(password: str) -> str:
    """Gera hash da senha usando bcrypt diretamente.
    
    Bcrypt tem limite físico de 72 bytes que não pode ser alterado.
    Esta função garante que a senha nunca exceda esse limite.
    """
    if not password:
        raise ValueError("Senha não pode ser vazia")
    
    # Converter para bytes primeiro
    password_bytes = password.encode('utf-8')
    tamanho_original = len(password_bytes)
    
    logger.info(f"🔍 Processando senha: {tamanho_original} bytes")
    
    # TRUNCAR PARA EXATAMENTE 72 BYTES (não menos, não mais)
    # IMPORTANTE: Truncar ANTES de qualquer operação
    if tamanho_original > 72:
        password_bytes = password_bytes[:72]
        logger.warning(f"⚠️ Senha truncada de {tamanho_original} para 72 bytes")
    
    # VERIFICAÇÃO FINAL: garantir que não excede 72 bytes
    tamanho_final = len(password_bytes)
    if tamanho_final > 72:
        logger.error(f"❌ ERRO CRÍTICO: Senha ainda tem {tamanho_final} bytes após truncamento!")
        password_bytes = password_bytes[:72]
        tamanho_final = 72
    
    # Fazer o hash usando bcrypt diretamente
    try:
        # Garantir que password_bytes é exatamente <= 72 bytes
        assert len(password_bytes) <= 72, f"Senha ainda excede 72 bytes: {len(password_bytes)}"
        
        hash_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        hash_result = hash_bytes.decode('utf-8')
        logger.info(f"✅ Hash criado com sucesso usando bcrypt direto! ({tamanho_final} bytes)")
        return hash_result
    except AssertionError as e:
        logger.error(f"❌ AssertionError: {e}")
        # Última tentativa: forçar truncamento
        password_bytes = password_bytes[:72]
        hash_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        hash_result = hash_bytes.decode('utf-8')
        logger.warning(f"⚠️ Hash criado após truncamento forçado")
        return hash_result
    except Exception as e:
        logger.error(f"❌ Erro ao criar hash: {e}")
        logger.error(f"Tamanho da senha: {tamanho_original} bytes")
        logger.error(f"Senha (primeiros 20 chars): {password[:20]}")
        import traceback
        logger.error(traceback.format_exc())
        raise ValueError(f"Erro ao criar hash da senha: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str):
    """Autentica usuário usando email."""
    try:
        # TRUNCAR SENHA ANTES DE QUALQUER OPERAÇÃO
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
            logger.warning(f"⚠️ Senha truncada em authenticate_user: {len(password_bytes)} bytes")
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            return False
        if user.ativo != 1:
            return False
        if user.status_aprovacao != "aprovado":
            return False
        
        # Verificar senha com proteção extra
        try:
            resultado = verify_password(password, user.senha_hash)
            return user if resultado else False
        except Exception as e:
            logger.error(f"❌ Erro em verify_password: {e}")
            # Tentar novamente com senha truncada
            password_bytes = password.encode('utf-8')[:72]
            password_truncada = password_bytes.decode('utf-8', errors='ignore')
            resultado = verify_password(password_truncada, user.senha_hash)
            return user if resultado else False
    except Exception as e:
        logger.error(f"❌ Erro em authenticate_user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def validate_password(password: str) -> tuple[bool, str]:
    """
    Valida se a senha contém letras e números.
    Retorna (valido, mensagem_erro)
    
    IMPORTANTE: Bcrypt tem limite físico de 72 bytes que não pode ser alterado.
    Validamos por bytes, não por caracteres, para garantir segurança.
    """
    if len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    
    # Verificar tamanho em bytes (não caracteres!)
    password_bytes = len(password.encode('utf-8'))
    if password_bytes > 72:
        return False, f"Senha muito longa ({password_bytes} bytes). Máximo: 72 bytes. Use uma senha mais curta."
    
    # Limitar a aproximadamente 60 caracteres para dar margem de segurança
    # (caracteres especiais podem ocupar mais bytes)
    if len(password) > 60:
        return False, "Senha deve ter no máximo 60 caracteres"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not has_letter:
        return False, "Senha deve conter pelo menos uma letra"
    
    if not has_digit:
        return False, "Senha deve conter pelo menos um número"
    
    return True, ""


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtém usuário atual a partir do token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise credentials_exception
    if user.ativo != 1:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    if user.status_aprovacao != "aprovado":
        raise HTTPException(status_code=403, detail="Cadastro aguardando aprovação")
    return user

