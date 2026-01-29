"""
Dependencies - Request bağımlılıkları ve token kontrol
"""

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Mevcut kullanıcıyı al (token doğrula)
    
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        logger.warning("Authorization header gerekli")
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
        logger.warning("Geçersiz Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Geçersiz Authorization header (format: Bearer <token>)"
        )
    
    # Token'dan kullanıcı bilgisini al
    user = AuthService.get_current_user(db, token)
    if not user:
        logger.warning("Geçersiz token veya kullanıcı bulunamadı")
        raise HTTPException(
            status_code=401,
            detail="Geçersiz token veya kullanıcı bulunamadı"
        )
    
    return user

async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Mevcut admin kullanıcıyı al
    """
    if not current_user.is_admin:
        logger.warning(f"Admin yetkisi gerekli: {current_user.username}")
        raise HTTPException(
            status_code=403,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    return current_user
