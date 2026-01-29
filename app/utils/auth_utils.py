"""
Auth Utils - Şifre ve JWT işlemleri
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Şifre konteksti
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthUtils:
    """
    Authentication utilities
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Parolayı hashle
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Parolayı doğrula
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        user_id: str,
        username: str,
        email: str,
        is_admin: bool = False,
        expires_delta: Optional[timedelta] = None
    ) -> dict:
        """
        JWT access token oluştur
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)  # 24 saat geçerli
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "is_admin": is_admin,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        try:
            encoded_jwt = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            logger.info(f"Token oluşturuldu: {username}")
            return {
                "access_token": encoded_jwt,
                "token_type": "bearer",
                "expires_in": int(expires_delta.total_seconds()),
                "exp": expire
            }
        except Exception as e:
            logger.error(f"Token oluşturmada hata: {e}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        JWT token'ı doğrula ve payload'ı getir
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            logger.info(f"Token doğrulandı: {payload.get('username')}")
            return payload
        except JWTError as e:
            logger.error(f"Token doğrulama hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Token işleminde hata: {e}")
            return None
