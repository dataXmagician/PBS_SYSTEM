"""
Meta Entity Model - Anaveri Tipi Tanımları

Kullanıcının oluşturduğu anaveri tiplerini tutar.
Örnek: Müşteri, Ürün, Bölge, Kanal, Maliyet Merkezi...
"""

from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import uuid


class MetaEntity(BaseModel):
    """
    Anaveri tipi tanımı.
    
    Örnek:
        - code: "CUSTOMER"
        - default_name: "Müşteri"
        - icon: "users"
    """
    __tablename__ = "meta_entities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tekil tanımlayıcı kod (CUSTOMER, PRODUCT, REGION...)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Varsayılan isim (çeviri yoksa kullanılır)
    default_name = Column(String(100), nullable=False)
    
    # Açıklama
    description = Column(Text, nullable=True)
    
    # UI için ikon (lucide-react ikon adı)
    icon = Column(String(50), default="database")
    
    # UI için renk
    color = Column(String(20), default="blue")
    
    # Aktif mi?
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Sistem tarafından oluşturulmuş mu? (silinemez)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Sıralama
    sort_order = Column(Integer, default=0)
    
    # İlişkiler
    attributes = relationship("MetaAttribute", foreign_keys="[MetaAttribute.entity_id]", back_populates="entity", cascade="all, delete-orphan")
    translations = relationship("MetaTranslation", back_populates="entity", cascade="all, delete-orphan")
    master_data = relationship("MasterData", back_populates="entity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaEntity(code='{self.code}', name='{self.default_name}')>"
