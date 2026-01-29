"""
User Repository - Database işlemleri
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.schemas.user import UserRegister
from uuid import UUID
from typing import Optional
from datetime import datetime

class UserRepository:
    """
    User modeli için database işlemleri
    """
    
    @staticmethod
    def create(db: Session, user_in: UserRegister, hashed_password: str) -> User:
        """
        Yeni kullanıcı oluştur
        """
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        ID'ye göre kullanıcı getir
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """
        Kullanıcı adına göre kullanıcı getir
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        E-postaya göre kullanıcı getir
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> tuple:
        """
        Tüm kullanıcıları listele
        """
        query = db.query(User)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total
    
    @staticmethod
    def update_last_login(db: Session, user_id: UUID) -> Optional[User]:
        """
        Son giriş tarihini güncelle
        """
        db_user = UserRepository.get_by_id(db, user_id)
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(db_user)
        return db_user
    
    @staticmethod
    def deactivate(db: Session, user_id: UUID) -> bool:
        """
        Kullanıcıyı deaktif et
        """
        db_user = UserRepository.get_by_id(db, user_id)
        if db_user:
            db_user.is_active = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def activate(db: Session, user_id: UUID) -> bool:
        """
        Kullanıcıyı aktif et
        """
        db_user = UserRepository.get_by_id(db, user_id)
        if db_user:
            db_user.is_active = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """
        Toplam kullanıcı sayısını getir
        """
        return db.query(func.count(User.id)).scalar()
