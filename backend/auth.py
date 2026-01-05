"""
Módulo de autenticação e autorização.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from loguru import logger

# Tentar importar bcrypt, usar passlib como fallback
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt não disponível, usando passlib")

try:
    from jose import JWTError, jwt as jose_jwt
    JWT_AVAILABLE = True
    JWT_LIB = "jose"
except ImportError:
    try:
        import jwt as pyjwt
        JWT_AVAILABLE = True
        JWT_LIB = "pyjwt"
    except ImportError:
        JWT_AVAILABLE = False
        JWT_LIB = None
        logger.warning("JWT não disponível")

from config import settings

# Configuração de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração JWT
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta."""
    try:
        if BCRYPT_AVAILABLE:
            # Usar bcrypt diretamente
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        else:
            # Usar passlib
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Gera hash da senha."""
    try:
        # Truncar senha se necessário (bcrypt limite: 72 bytes)
        senha_bytes = password.encode('utf-8')
        if len(senha_bytes) > 72:
            senha_bytes = senha_bytes[:72]
            password = senha_bytes.decode('utf-8', errors='ignore')
            logger.warning(f"Senha truncada para 72 bytes antes do hash")
        
        if BCRYPT_AVAILABLE:
            # Usar bcrypt diretamente
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        else:
            # Usar passlib
            return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Erro ao gerar hash da senha: {e}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT."""
    if not JWT_AVAILABLE:
        raise Exception("JWT não disponível")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    if JWT_LIB == "jose":
        encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    elif JWT_LIB == "pyjwt":
        import jwt as pyjwt
        encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    else:
        raise Exception("JWT não disponível")
    
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str):
    """Autentica usuário."""
    try:
        from database.models import Usuario
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            return None
        
        # Verificar se usuário está ativo
        if not user.ativo:
            logger.warning(f"Usuário {email} tentou fazer login mas está inativo")
            return None
        
        # Verificar senha
        if not verify_password(password, user.senha_hash):
            return None
        
        return user
    except ImportError:
        logger.error("Modelo Usuario não encontrado")
        return None
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário: {e}")
        return None


def get_current_user(db: Session, token: str):
    """Obtém usuário atual a partir do token."""
    try:
        from database.models import Usuario
        
        if not JWT_AVAILABLE:
            raise Exception("JWT não disponível")
        
        if JWT_LIB == "jose":
            payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        elif JWT_LIB == "pyjwt":
            import jwt as pyjwt
            payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        else:
            raise Exception("JWT não disponível")
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        return user
    except Exception as e:
        logger.error(f"Erro ao obter usuário atual: {e}")
        return None


def validate_password(password: str) -> tuple[bool, str]:
    """Valida senha."""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if len(password) > 72:
        return False, "Senha muito longa (máximo 72 bytes)"
    
    return True, ""

