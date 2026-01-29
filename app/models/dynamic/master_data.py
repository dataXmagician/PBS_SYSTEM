"""
Master Data Model - Anaveri Kayıtları

Kullanıcının girdiği anaveri kayıtlarını tutar.
Örnek: M001-Acme Ltd, P001-Laptop...
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import uuid


class MasterData(BaseModel):
    """
    Anaveri kaydı.
    
    Örnek (Müşteri anaverisi):
        - entity_id: 1 (Müşteri tipi)
        - code: "M001"
        - name: "Acme Ltd"
    """
    __tablename__ = "master_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Hangi anaveri tipine ait?
    entity_id = Column(Integer, ForeignKey("meta_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Kayıt kodu (her entity içinde unique)
    code = Column(String(50), nullable=False, index=True)
    
    # Kayıt adı (hızlı erişim için denormalize)
    name = Column(String(200), nullable=False)
    
    # Aktif mi?
    is_active = Column(Boolean, default=True)
    
    # Sıralama
    sort_order = Column(Integer, default=0)
    
    # İlişkiler
    entity = relationship("MetaEntity", back_populates="master_data")
    values = relationship("MasterDataValue", back_populates="master_data", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Entity + Code kombinasyonu unique olmalı
        UniqueConstraint('entity_id', 'code', name='uq_entity_code'),
    )
    
    def __repr__(self):
        return f"<MasterData(code='{self.code}', name='{self.name}')>"
