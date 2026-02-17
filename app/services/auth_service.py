"""
Auth Service - Business logic
"""

from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.utils.auth_utils import AuthUtils
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """
    Authentication işlemleri
    """
    
    @staticmethod
    def register(db: Session, user_in: UserRegister) -> UserResponse:
        """
        Yeni kullanıcı kaydı (register)
        """
        # Parola doğrulama
        if user_in.password != user_in.password_confirm:
            raise ValueError("Parolalar eşleşmiyor")
        
        # Username zaten var mı?
        existing_user = UserRepository.get_by_username(db, user_in.username)
        if existing_user:
            raise ValueError(f"Kullanıcı adı '{user_in.username}' zaten kullanılıyor")
        
        # Email zaten var mı?
        existing_email = UserRepository.get_by_email(db, user_in.email)
        if existing_email:
            raise ValueError(f"E-posta '{user_in.email}' zaten kullanılıyor")
        
        # Parolayı hashle
        hashed_password = AuthUtils.hash_password(user_in.password)
        
        # Kullanıcıyı oluştur
        logger.info(f"Yeni kullanıcı kaydediliyor: {user_in.username}")
        user = UserRepository.create(db, user_in, hashed_password)
        logger.info(f"Kullanıcı başarıyla kaydedildi: {user.id}")
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    def login(db: Session, login_in: UserLogin) -> TokenResponse:
        """
        Kullanıcı girişi (login) ve token oluştur
        """
        # Username veya email ile kullanıcı bul
        user = UserRepository.get_by_username(db, login_in.username)
        if not user:
            user = UserRepository.get_by_email(db, login_in.username)
        
        if not user:
            logger.warning(f"Kullanıcı bulunamadı: {login_in.username}")
            raise ValueError("Kullanıcı adı veya parola yanlış")
        
        # Kullanıcı aktif mi?
        if not user.is_active:
            logger.warning(f"Deaktif kullanıcı giriş denemesi: {user.username}")
            raise ValueError("Kullanıcı hesabı deaktif")
        
        # Parolayı doğrula
        if not AuthUtils.verify_password(login_in.password, user.hashed_password):
            logger.warning(f"Yanlış parola: {user.username}")
            raise ValueError("Kullanıcı adı veya parola yanlış")
        
        # Son giriş tarihini güncelle
        UserRepository.update_last_login(db, user.id)
        
        # Token oluştur
        logger.info(f"Token oluşturuluyor: {user.username}")
        token_data = AuthUtils.create_access_token(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            is_admin=user.is_admin
        )
        
        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=UserResponse.model_validate(user)
        )
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[UserResponse]:
        """
        Token'dan kullanıcı bilgisini al
        """
        payload = AuthUtils.verify_token(token)
        if not payload:
            logger.warning("Token doğrulama başarısız")
            return None
        user_id = payload.get("user_id")
        # Safely convert user_id to UUID - handle malformed values
        try:
            user_uuid = UUID(user_id)
        except Exception as e:
            logger.warning(f"Geçersiz user_id in token payload: {user_id} - {e}")
            return None

        user = UserRepository.get_by_id(db, user_uuid)
        
        if not user:
            logger.warning(f"Kullanıcı bulunamadı: {user_id}")
            return None
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[UserResponse]:
        """
        ID'ye göre kullanıcı getir
        """
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            logger.warning(f"Kullanıcı bulunamadı: {user_id}")
            return None
        return UserResponse.model_validate(user)
