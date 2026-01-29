"""
Meta Attribute Model - Anaveri Alan Tanımları

Her anaveri tipinin sahip olduğu alanları tanımlar.
Örnek: Müşteri anaverisi için -> Kod, Ad, Sektör, Bölge, Kredi Limiti
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum
import uuid


class AttributeType(enum.Enum):
    """Alan veri tipleri"""
    STRING = "string"           # Metin
    INTEGER = "integer"         # Tam sayı
    DECIMAL = "decimal"         # Ondalıklı sayı
    BOOLEAN = "boolean"         # Evet/Hayır
    DATE = "date"               # Tarih
    DATETIME = "datetime"       # Tarih ve saat
    LIST = "list"               # Seçim listesi (options JSON'da)
    REFERENCE = "reference"     # Başka bir anaveriye referans


class MetaAttribute(BaseModel):
    """
    Anaveri alan tanımı.
    
    Örnek (Müşteri anaverisi için):
        - code: "SECTOR"
        - default_label: "Sektör"
        - data_type: LIST
        - options: ["Otomotiv", "Gıda", "Tekstil"]
    """
    __tablename__ = "meta_attributes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Hangi anaveri tipine ait?
    entity_id = Column(Integer, ForeignKey("meta_entities.id", ondelete="CASCADE"), nullable=False)
    
    # Alan kodu (CODE, NAME, SECTOR...)
    code = Column(String(50), nullable=False, index=True)
    
    # Varsayılan etiket
    default_label = Column(String(100), nullable=False)
    
    # Veri tipi
    data_type = Column(Enum(AttributeType), nullable=False, default=AttributeType.STRING)
    
    # Liste seçenekleri (LIST tipi için JSON array)
    options = Column(Text, nullable=True)  # JSON: ["Opt1", "Opt2"]
    
    # Referans anaverisi (REFERENCE tipi için)
    reference_entity_id = Column(Integer, ForeignKey("meta_entities.id"), nullable=True)
    
    # Varsayılan değer
    default_value = Column(String(255), nullable=True)
    
    # Zorunlu alan mı?
    is_required = Column(Boolean, default=False)
    
    # Tekil mi? (aynı değer başka kayıtta olamaz)
    is_unique = Column(Boolean, default=False)
    
    # Kod alanı mı? (her anaverinin bir kod alanı olmalı)
    is_code_field = Column(Boolean, default=False)
    
    # Ana tanım alanı mı? (listelerde gösterilir)
    is_name_field = Column(Boolean, default=False)
    
    # Aktif mi?
    is_active = Column(Boolean, default=True)
    
    # Sistem alanı mı? (silinemez)
    is_system = Column(Boolean, default=False)
    
    # Sıralama
    sort_order = Column(Integer, default=0)
    
    # Minimum/Maximum değerler (sayısal tipler için)
    min_value = Column(String(50), nullable=True)
    max_value = Column(String(50), nullable=True)
    
    # Minimum/Maximum uzunluk (metin için)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    
    # İlişkiler
    entity = relationship("MetaEntity", back_populates="attributes", foreign_keys=[entity_id])
    reference_entity = relationship("MetaEntity", foreign_keys=[reference_entity_id])
    translations = relationship("MetaTranslation", back_populates="attribute", cascade="all, delete-orphan")
    values = relationship("MasterDataValue", back_populates="attribute", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MetaAttribute(code='{self.code}', type='{self.data_type.value}')>"
