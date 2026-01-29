"""
Auth API Endpoints - Login, Register, Profile
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

# POST - Kullanıcı kaydı (Register)
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı kaydı (Register)
    
    - **username**: Kullanıcı adı (en az 3 karakter)
    - **email**: E-posta
    - **password**: Parola (en az 6 karakter)
    - **password_confirm**: Parola doğrulama
    """
    try:
        return AuthService.register(db, user_in)
    except ValueError as e:
        logger.warning(f"Register validasyon hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Register sırasında hata: {e}")
        raise HTTPException(status_code=500, detail="Kayıt başarısız")

# POST - Kullanıcı girişi (Login)
@router.post("/login", response_model=TokenResponse)
async def login(
    login_in: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı girişi (Login)
    
    - **username**: Kullanıcı adı veya E-posta
    - **password**: Parola
    
    Başarılı girişte JWT token döndürülür.
    """
    try:
        return AuthService.login(db, login_in)
    except ValueError as e:
        logger.warning(f"Login hatası: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login sırasında hata: {e}")
        raise HTTPException(status_code=500, detail="Giriş başarısız")

# GET - Mevcut kullanıcı profili
@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Mevcut kullanıcının profilini getir
    
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header gerekli"
        )
    
    # Bearer token'ı ayıkla
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz Authorization header"
        )
    
    # Token'dan kullanıcı bilgisini al
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz token veya kullanıcı bulunamadı"
        )
    
    return user

# GET - Token test (veya health check for auth)
@router.get("/verify-token", response_model=dict)
async def verify_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Token'ı doğrula
    
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header gerekli"
        )
    
    # Bearer token'ı ayıkla
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz Authorization header"
        )
    
    # Token'ı doğrula
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz token"
        )
    
    return {
        "valid": True,
        "user": user,
        "message": "Token geçerli"
    }
