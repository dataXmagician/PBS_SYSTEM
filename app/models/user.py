"""
User Model - Sistem Kullanıcıları
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class User(Base):
    """
    Sistem kullanıcısı - Login için
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="Kullanıcı adı")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="E-posta")
    full_name = Column(String(100), comment="Adı Soyadı")
    hashed_password = Column(String(255), nullable=False, comment="Şifreli Parola")
    is_active = Column(Boolean, default=True, nullable=False, comment="Aktif mi?")
    is_admin = Column(Boolean, default=False, nullable=False, comment="Admin mi?")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True, comment="Son giriş tarihi")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
