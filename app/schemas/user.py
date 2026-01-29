"""
User Schema - Request/Response modelleri
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    """
    User temel bilgileri
    """
    username: str = Field(..., min_length=3, max_length=50, description="Kullanıcı adı")
    email: EmailStr = Field(..., description="E-posta")
    full_name: Optional[str] = Field(None, max_length=100, description="Adı Soyadı")

class UserRegister(UserBase):
    """
    Kullanıcı kaydı (register)
    """
    password: str = Field(..., min_length=6, max_length=72, description="Parola (min 6 karakter)")
    password_confirm: str = Field(..., description="Parola Doğrulama")

class UserLogin(BaseModel):
    """
    Kullanıcı girişi (login)
    """
    username: str = Field(..., description="Kullanıcı adı veya E-posta")
    password: str = Field(..., description="Parola")

class UserResponse(UserBase):
    """
    Kullanıcı cevap modeli
    """
    id: UUID
    is_active: bool
    is_admin: bool
    created_date: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """
    Token cevap modeli
    """
    access_token: str = Field(..., description="JWT Access Token")
    token_type: str = Field(default="bearer", description="Token Tipi")
    expires_in: int = Field(..., description="Geçerlilik Süresi (saniye)")
    user: UserResponse = Field(..., description="Kullanıcı Bilgileri")

class TokenPayload(BaseModel):
    """
    JWT Token Payload
    """
    user_id: str
    username: str
    email: str
    is_admin: bool
    exp: int  # Expiration time
